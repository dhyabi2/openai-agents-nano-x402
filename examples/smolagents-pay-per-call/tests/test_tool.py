"""Offline, deterministic tests for the smolagents Nano x402 tool.

No real Nano network, no wallet spend, no external calls: the payment core is
injected via `pay_call`, and a fake 402 server exercises the settle flow end to
end is NOT needed because `pay_call` replaces the whole network layer. These
tests prove the smolagents Tool contract and the two-phase honesty semantics.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from smolagents import Tool
from smolagents_nano.tool import make_nano_x402_tool, QuoteTokenStore


def _make(pay_call, default_max_xno="0.01", token_store=None):
    return make_nano_x402_tool(
        wallet_path="/tmp/does-not-exist.json",
        default_max_xno=default_max_xno,
        pay_call=pay_call,
        token_store=token_store,
    )


def test_returns_smolagents_tool():
    tool = _make(lambda *a, **k: (None, None))
    assert isinstance(tool, Tool)
    assert tool.name == "nano_x402_fetch"
    assert callable(tool.forward)


def test_wallet_path_and_rpc_not_exposed_to_model():
    tool = _make(lambda *a, **k: (None, None))
    schema_text = str(tool.inputs)
    assert "wallet" not in schema_text.lower()
    assert "rpc" not in schema_text.lower()
    assert ".json" not in schema_text


class FakeResp:
    def __init__(self, text="hello world", status=200):
        self.text = text
        self.status_code = status


def test_dry_run_returns_quote_with_token_nothing_spent():
    spent = []

    def pay(method, url, headers, dry_run, max_raw):
        assert dry_run is True
        spent.append(True)
        return FakeResp(status=402), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "amount_raw": 10**22,
        }

    tool = _make(pay)
    out = tool.forward("https://x.example/resource", dry_run=True)
    assert out.startswith("QUOTE")
    assert "nano_1abc" in out
    assert "quote_token" in out
    assert spent == [True]  # only a dry run happened, nothing paid


def test_redeem_refused_without_valid_token():
    def pay(method, url, headers, dry_run, max_raw):
        return FakeResp(), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "settled": True,
            "block": "ABCDEF",
            "ledger": "confirmed",
        }

    tool = _make(pay)
    # No token presented -> refuse even though the backend would settle.
    out = tool.forward("https://x.example/resource", dry_run=False)
    assert out.startswith("REFUSED")
    assert "quote_token" in out


def test_redeem_paid_after_valid_token():
    store = QuoteTokenStore()

    def pay(method, url, headers, dry_run, max_raw):
        if dry_run:
            return FakeResp(status=402), {
                "amount_xno": "0.00001",
                "pay_to": "nano_1abc",
                "amount_raw": 10**22,
            }
        return FakeResp(text="paid body here"), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "settled": True,
            "block": "ABCDEF1234",
            "ledger": "confirmed",
        }

    tool = _make(pay, token_store=store)
    preview = tool.forward("https://x.example/resource", dry_run=True)
    assert preview.startswith("QUOTE")
    token = preview.split("quote_token: ")[1].strip()
    out = tool.forward(
        "https://x.example/resource", dry_run=False, quote_token=token
    )
    assert out.startswith("PAID (Nano x402)")
    assert "ABCDEF1234" in out


def test_token_is_single_use():
    store = QuoteTokenStore()
    pay_calls = {"n": 0}

    def pay(method, url, headers, dry_run, max_raw):
        if dry_run:
            return FakeResp(status=402), {
                "amount_xno": "0.00001",
                "pay_to": "nano_1abc",
                "amount_raw": 10**22,
            }
        pay_calls["n"] += 1
        return FakeResp(text="body"), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "settled": True,
            "block": "BLOCK",
            "ledger": "confirmed",
        }

    tool = _make(pay, token_store=store)
    preview = tool.forward("https://x.example/", dry_run=True)
    token = preview.split("quote_token: ")[1].strip()
    assert tool.forward("https://x.example/", dry_run=False, quote_token=token).startswith("PAID")
    # Second redeem with the same consumed token must be refused.
    out = tool.forward("https://x.example/", dry_run=False, quote_token=token)
    assert out.startswith("REFUSED")
    assert pay_calls["n"] == 1  # backend only ever settled once


def test_cap_validation_refuses_bad_max():
    tool = _make(lambda *a, **k: (None, None))
    assert tool.forward("u", max_xno=-5).startswith("REFUSED")
    assert tool.forward("u", max_xno="abc").startswith("REFUSED")


def test_headers_json_must_be_object():
    tool = _make(lambda *a, **k: (None, None))
    assert tool.forward("u", headers_json='["a"]').startswith("REFUSED")
    assert tool.forward("u", headers_json="not json").startswith("REFUSED")


def test_headers_json_passed_to_pay():
    seen = {}

    def pay(method, url, headers, dry_run, max_raw):
        seen.update(headers)
        return FakeResp(status=402), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "amount_raw": 10**22,
        }

    tool = _make(pay)
    # Use dry_run so the header reaches the payment layer without a token gate.
    tool.forward("https://x.example", headers_json='{"X-Test": "1"}', dry_run=True)
    assert seen.get("X-Test") == "1"


def test_import_guard_raises_when_smolagents_absent(monkeypatch):
    # Simulate smolagents being unavailable.
    import smolagents_nano.tool as m

    monkeypatch.setattr(m, "Tool", None, raising=True)
    with pytest.raises(ImportError):
        m.make_nano_x402_tool(
            wallet_path="/tmp/x.json",
            default_max_xno="0.01",
            pay_call=lambda *a, **k: (None, None),
        )
