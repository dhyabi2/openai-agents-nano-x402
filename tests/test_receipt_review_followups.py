"""Review follow-ups to the unpaid-receipt and wallet-guard fix. Offline: no
real HTTP, no node, no money.

1. A journalled block re-sent, refused with a 402, not on the ledger in time:
   feeless402 (0.2.13) drops the journal entry and recurses, and the recursive
   call returns `(response, None)` when its first unpaid read is not a 402. A
   signed block DID reach the merchant, so the answer must not say "nothing was
   signed or sent". This runs the REAL `request_with_payment` and journal.
2. Wallet-error path redaction never replaces a bare "." or "/".
3. A structurally bad wallet file names what is wrong, never the seed.
5. A receipt with no block never prints the merchant's pay_to as the payee.
"""
import base64
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import nano_pay.x402 as X

import openai_agents_nano.tool as T
from test_journal_replay_payee import (  # noqa: F401  (env is a fixture)
    A, PREV, RPC, Resp, _buy, _journal, _journal_a_lost_payment_to, _tool, env,
)


class _LedgerWithoutTheBlock(RPC):
    """The node answers that it has no such block for anything but PREV."""

    def call(self, body):
        if body.get("hash") == PREV:
            return super().call(body)
        raise Exception("Block not found")


def test_a_re_sent_journalled_block_then_a_free_read_is_never_nothing_sent(env, monkeypatch):
    seller, built, wallet_path = env
    monkeypatch.setattr(X, "CONFIRM_WAIT_S", 0, raising=False)
    tool = _tool(wallet_path, rpc=_LedgerWithoutTheBlock())
    # The lost-payment setup uses RPC() semantics only for the first redeem's
    # outcome; the ledger-without-the-block view applies from here on.
    old_block = _journal_a_lost_payment_to(seller, tool, A, wallet_path)
    built.clear()

    # Preview + redeem quote + paying read: 402. The journalled block is re-sent
    # and refused with 402; the recursive unpaid read is a 200.
    orig_request = seller.request

    def request(method, url, headers=None, **kw):
        headers = headers or {}
        if seller.paid_headers:
            # The recursive "unpaid" read (feeless402 0.2.13 passes its headers
            # on, the old payment header included) is answered without a 402.
            seller.reads += 1
            return Resp(200, {}, "served after all")
        if "X-PAYMENT" in headers:
            seller.paid_headers.append(headers["X-PAYMENT"])
            return Resp(402, {}, "")
        return orig_request(method, url, headers=headers, **kw)

    monkeypatch.setattr(X.requests, "request", request)
    _, out = _buy(tool)

    assert len(seller.paid_headers) == 1, "the journalled block was re-sent"
    assert built == [], "no new block was signed in this call"
    assert _journal(wallet_path) == {}, "feeless402 dropped the entry and recursed"
    assert "this call signed nothing" not in out, out
    assert out.startswith("UNCONFIRMED"), out
    assert old_block.upper() in out, out
    assert "before paying again" in out
    assert not out.startswith("PAID") and "NOT PAID" not in out


def test_a_free_paying_read_with_no_journal_still_says_nothing_was_sent(env, monkeypatch):
    """Control: with no journalled block for this request, the plain form stays."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    start = seller.reads
    orig_request = seller.request

    def request(method, url, headers=None, **kw):
        if seller.reads - start >= 2:
            seller.reads += 1
            return Resp(200, {}, "free after all")
        return orig_request(method, url, headers=headers, **kw)

    monkeypatch.setattr(X.requests, "request", request)
    _, out = _buy(tool)
    assert out.startswith("NOT PAID - no payment was requested on the paying read"), out
    assert "block:     none - this call signed nothing" in out, out
    assert A not in out


# --- 2. path redaction ------------------------------------------------------------


@pytest.mark.parametrize("path", ["wallet.json", "/wallet.json", "sub/wallet.json"])
def test_redaction_never_replaces_a_bare_dot_or_slash(path):
    msg = f"[Errno 21] Is a directory: '{path}' (see d.json and a/b)"
    out = T._redact_wallet_path(msg, pathlib.Path(path))
    assert "d.json and a/b" in out, out
    assert "<wallet dir>json" not in out and "d<wallet dir>" not in out, out
    assert "wallet.json" in out


def test_redaction_replaces_the_absolute_path(tmp_path):
    p = tmp_path / "w.json"
    out = T._redact_wallet_path(f"bad file {p} in {tmp_path}/x.y", p)
    assert str(tmp_path) not in out, out
    assert "bad file w.json in <wallet dir>/x.y" == out


def test_a_relative_wallet_path_error_is_not_mangled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "rel.json").mkdir()
    tool = T.make_nano_x402_tool(wallet_path="rel.json", rpc=RPC(), default_max_xno="0.01")
    from test_journal_replay_payee import _call
    out = _call(tool, dry_run=True)
    assert out.startswith("ERROR: the wallet at rel.json cannot be used"), out
    assert "<wallet dir>" not in out.split("Nothing was spent")[0], out
    assert str(tmp_path) not in out


# --- 3. structurally bad wallet ------------------------------------------------------


SECRET = "ab" * 32


@pytest.mark.parametrize("content", [
    "{}", "[]", "null", "3",
    json.dumps({"seed": SECRET}),
    json.dumps({"seed": SECRET, "index": -1}),
    json.dumps({"seed": SECRET, "index": "0"}),
    json.dumps({"seed": SECRET, "index": True}),
    json.dumps({"seed": SECRET, "index": 2 ** 32}),
    json.dumps({"seed": SECRET, "index": 1.0}),
    json.dumps({"seed": SECRET[:-2], "index": 0}),
    json.dumps({"seed": SECRET[:-1] + "z", "index": 0}),
])
def test_a_bad_wallet_says_plainly_what_is_wrong_without_the_seed(tmp_path, content):
    p = tmp_path / "bad.json"
    p.write_text(content)
    tool = T.make_nano_x402_tool(wallet_path=str(p), rpc=RPC(), default_max_xno="0.01")
    from test_journal_replay_payee import _call
    out = _call(tool, dry_run=True)
    assert out.startswith("ERROR: the wallet at bad.json cannot be used"), out
    assert ("wallet file is not a wallet: expected a JSON object with a 64-hex "
            "'seed' and a non-negative integer 'index' below 2^32") in out, out
    assert SECRET[:20] not in out, "the seed never goes into model context"
    assert "AssertionError: )" not in out


# --- 5. no block, no payee ------------------------------------------------------------


def test_a_receipt_without_a_block_never_names_the_merchants_pay_to_as_payee():
    class R:
        status_code, text = 200, "ok"
    merchant = "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
    out = T._format_receipt(R(), {"settled": None, "pay_to": merchant, "amount_xno": "0.001"},
                            "0.01", authorised_pay_to=A)
    assert f"pay_to:    {merchant}" not in out, out
    assert f"pay_to:    {A}" not in out, out
    assert "pay_to:    none" in out, out
    assert f"merchant claims pay_to: {merchant} - UNTRUSTED" in out, out
    # And with no authorised payee given at all.
    out2 = T._format_receipt(R(), {"settled": None, "pay_to": merchant}, "0.01")
    assert f"pay_to:    {merchant}" not in out2 and "UNTRUSTED" in out2, out2


@pytest.mark.parametrize("seed", [SECRET + "\n", " " + SECRET,
                                  " ".join(SECRET[i:i + 2] for i in range(0, 64, 2))])
def test_a_seed_with_whitespace_that_signs_is_accepted(tmp_path, seed):
    """feeless402 reads the seed with bytes.fromhex, which ignores whitespace:
    such a wallet pays, and derives the same address, so it is not refused."""
    from nano_pay.wallet import Wallet
    from test_journal_replay_payee import _call
    clean = tmp_path / "clean" / "w.json"
    clean.parent.mkdir()
    clean.write_text(json.dumps({"seed": SECRET, "index": 0}))
    spaced = tmp_path / "spaced" / "w.json"
    spaced.parent.mkdir()
    spaced.write_text(json.dumps({"seed": seed, "index": 0}))
    assert Wallet(spaced).load().address == Wallet(clean).load().address

    class Free:
        status_code, headers, text = 200, {}, "free"
    import requests
    orig = requests.request
    requests.request = lambda *a, **k: Free()
    try:
        out = _call(T.make_nano_x402_tool(wallet_path=str(spaced), rpc=RPC(),
                                          default_max_xno="0.01"), dry_run=True)
    finally:
        requests.request = orig
    assert not out.startswith("ERROR: the wallet"), out


def test_index_at_the_top_of_its_range_is_accepted(tmp_path):
    from test_journal_replay_payee import _call
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"seed": SECRET, "index": 2 ** 32 - 1}))
    out = _call(T.make_nano_x402_tool(wallet_path=str(p), rpc=RPC(), default_max_xno="0.01"),
                dry_run=True, url="http://127.0.0.1:9/never")
    assert not out.startswith("ERROR: the wallet"), out
