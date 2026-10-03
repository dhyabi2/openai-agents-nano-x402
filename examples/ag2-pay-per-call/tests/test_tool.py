"""Offline, deterministic tests for the AG2 (AutoGen) Nano x402 tool function.

No real Nano network, no wallet spend, no external calls: the payment core is
injected via `pay_call`, which replaces the whole network layer. These tests
prove the AG2 tool contract (a plain annotated function that AG2 discovers as a
``FunctionTool``) and the two-phase honesty semantics (quote_token single-use,
cap validation, header passthrough).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

pytest.importorskip("autogen_agentchat")

from ag2_nano.tool import make_nano_x402_fetch, QuoteTokenStore


def _make(pay_call, default_max_xno="0.01", token_store=None):
    return make_nano_x402_fetch(
        wallet_path="/tmp/does-not-exist.json",
        default_max_xno=default_max_xno,
        pay_call=pay_call,
        token_store=token_store,
    )


def test_returns_plain_callable_function():
    fn = _make(lambda *a, **k: (None, None))
    assert callable(fn)
    assert fn.__name__ == "nano_x402_fetch"
    assert fn.__doc__ and "x402" in fn.__doc__


def test_wallet_path_and_rpc_not_exposed_to_model():
    fn = _make(lambda *a, **k: (None, None))
    schema_text = fn.__doc__ or ""
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

    fn = _make(pay)
    out = fn("https://x.example/resource", dry_run=True)
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

    fn = _make(pay)
    out = fn("https://x.example/resource", dry_run=False)
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

    fn = _make(pay, token_store=store)
    preview = fn("https://x.example/resource", dry_run=True)
    assert preview.startswith("QUOTE")
    token = preview.split("quote_token: ")[1].strip()
    out = fn("https://x.example/resource", dry_run=False, quote_token=token)
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

    fn = _make(pay, token_store=store)
    preview = fn("https://x.example/", dry_run=True)
    token = preview.split("quote_token: ")[1].strip()
    assert fn("https://x.example/", dry_run=False, quote_token=token).startswith("PAID")
    # Second redeem with the same consumed token must be refused.
    out = fn("https://x.example/", dry_run=False, quote_token=token)
    assert out.startswith("REFUSED")
    assert pay_calls["n"] == 1  # backend only ever settled once


def test_cap_validation_refuses_bad_max():
    fn = _make(lambda *a, **k: (None, None))
    # dry_run=True so the cap guard is reached directly (dry_run=False would
    # short-circuit at the quote_token gate and mask a slipped negative cap).
    assert fn("u", max_xno=-5, dry_run=True).startswith("REFUSED: max_xno must be >= 0")
    assert fn("u", max_xno="abc", dry_run=True).startswith("REFUSED: max_xno is not a number")
    # and they must refuse even on the redeem path
    assert fn("u", max_xno=-5).startswith("REFUSED")


def test_headers_json_must_be_object():
    fn = _make(lambda *a, **k: (None, None))
    assert fn("u", headers_json='["a"]').startswith("REFUSED")
    assert fn("u", headers_json="not json").startswith("REFUSED")


def test_headers_json_passed_to_pay():
    seen = {}

    def pay(method, url, headers, dry_run, max_raw):
        seen.update(headers)
        return FakeResp(status=402), {
            "amount_xno": "0.00001",
            "pay_to": "nano_1abc",
            "amount_raw": 10**22,
        }

    fn = _make(pay)
    fn("https://x.example", headers_json='{"X-Test": "1"}', dry_run=True)
    assert seen.get("X-Test") == "1"


def test_ag2_discovers_plain_function_as_functiontool():
    """The whole point: AG2 must auto-wrap our plain annotated function into a
    FunctionTool, so an AG2 agent can call it with no framework-specific Tool
    class."""
    from ag2_nano.tool import make_nano_x402_fetch
    from autogen_core.tools import FunctionTool
    from autogen_agentchat.agents import AssistantAgent
    import inspect

    fn = make_nano_x402_fetch(
        wallet_path="/tmp/does-not-exist.json",
        default_max_xno="0.01",
        pay_call=lambda *a, **k: (FakeResp(text="hi"), {
            "amount_xno": "0.00001", "pay_to": "nano_1abc",
            "settled": True, "block": "B", "ledger": "confirmed",
        }),
    )
    tool = FunctionTool(fn, description=fn.__doc__ or "")
    assert isinstance(tool, FunctionTool)
    # AG2 builds an args model from the annotated signature: url is required str,
    # dry_run optional.
    fields = tool.args_type().model_fields
    assert "url" in fields
    assert fields["url"].is_required() is True
    assert fields["dry_run"].is_required() is False
    # The function schema AG2 advertises to the LLM carries the named params.
    assert set(tool.schema["parameters"]["properties"].keys()) >= {"url", "dry_run", "quote_token"}
    # Function name matches the source function.
    assert tool.name == "nano_x402_fetch"
