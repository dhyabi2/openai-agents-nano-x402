"""A block feeless402 re-presents from its journal is not a block this tool signed.
Offline: no real HTTP, no node, no money.

feeless402 (0.2.13) journals every signed block beside the wallet before sending
it, keyed by (method, url, pay_to, amount, body). When the paying read names a
(pay_to, amount) that already has an entry, `request_with_payment` re-sends the
stored block and never calls `wallet.build_payment_block`:

    entry = journal.get(jkey)
    if entry:
        pay_header, new_frontier, work_root = entry["header"], entry["hash"], ...
    else:
        block, new_frontier, work_root = wallet.build_payment_block(rpc, pay_to, amount)

So `_PayeePinnedWallet` and `_MandatedWallet` are never consulted for it. With a
block to B journalled by an earlier redeem the merchant never answered, a preview
that quotes A and a paying read that names B for the same amount re-presented the
block to B, and the tool printed "PAID", `pay_to: A`, and called B an untrusted
merchant claim "not where this payment went" - the opposite of the truth.

These tests run the REAL `request_with_payment` and its real journal. Only the
network (`requests.request`), the node (`rpc`) and the signature itself
(`Wallet.build_payment_block`, which needs a funded account) are stubbed.
"""
import asyncio
import base64
import json
import os
import pathlib
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import requests
from agents.tool_context import ToolContext
from nano_pay.wallet import Wallet
import nano_pay.x402 as X

import openai_agents_nano.tool as T
from openai_agents_nano import mandate as M

A = "nano_1p7cqqnfo91zwcnse54f3ucyfi6xwzsbnkt3ay14cd1g6epmiygnt7jtcoa5"
B = "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
PRICE = 10 ** 27          # 0.001 XNO
CAP = "0.01"
URL = "http://seller.invalid/report"

OPERATOR_SEED = "11" * 32  # test-fixture, same as tests/test_tool_mandate.py
OPERATOR_KEY = M.private_key_from_seed(bytes.fromhex(OPERATOR_SEED), 0)
OPERATOR = M.address_from_public_key(M.public_key_from_private(OPERATOR_KEY))


class Resp:
    def __init__(self, code, headers=None, text=""):
        self.status_code, self.headers, self.text = code, headers or {}, text

    def json(self):
        return {}


def _payment_required(pay_to):
    q = {"x402Version": 2, "accepts": [{"scheme": "exact", "network": "nano:mainnet",
                                        "asset": "XNO", "amount": str(PRICE), "payTo": pay_to}]}
    return {"payment-required": base64.b64encode(json.dumps(q).encode()).decode()}


class Seller:
    """An x402 seller on the wire. `quote_for(n)` names the payee of the n-th
    unpaid read; `reply` is False to drop every paid request (no reply)."""

    def __init__(self):
        self.reads = 0
        self.quote_for = lambda n: A
        self.reply = True
        self.paid_headers = []

    def request(self, method, url, headers=None, **kw):
        headers = headers or {}
        if "X-PAYMENT" in headers:
            self.paid_headers.append(headers["X-PAYMENT"])
            if not self.reply:
                raise requests.ConnectionError("merchant did not reply")
            return Resp(200, {}, "the resource")
        self.reads += 1
        return Resp(402, _payment_required(self.quote_for(self.reads)))


class RPC:
    """The ledger holds every block asked about (a payment whose reply was lost)."""

    def call(self, body):
        return {"contents": {}, "confirmed": "true"}


@pytest.fixture
def env(monkeypatch, tmp_path):
    seller = Seller()
    monkeypatch.setattr(requests, "request", seller.request)
    monkeypatch.setattr(X.time, "sleep", lambda s: None)
    built = []

    def build(self, rpc, to, amt):
        built.append((to, int(amt)))
        return {"type": "state", "link_as_account": to}, ("%064X" % (0xB10C + len(built))), "root"

    monkeypatch.setattr(Wallet, "build_payment_block", build)
    wallet_path = tmp_path / "wallet.json"
    Wallet(pathlib.Path(wallet_path)).create()
    return seller, built, wallet_path


def _tool(wallet_path, **kw):
    return T.make_nano_x402_tool(wallet_path=str(wallet_path), rpc=RPC(), default_max_xno=CAP, **kw)


def _call(tool, **args):
    raw = json.dumps(dict({"url": URL}, **args))
    ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
    return asyncio.run(tool.on_invoke_tool(ctx, raw))


def _buy(tool):
    preview = _call(tool, dry_run=True)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    return preview, _call(tool, dry_run=False, quote_token=token)


def _journal(wallet_path):
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _journal_a_lost_payment_to(seller, tool, payee, wallet_path):
    """An earlier, authorised redeem to `payee` whose reply never came back:
    feeless402 keeps the signed block in its journal to re-present it."""
    seller.quote_for = lambda n: payee
    seller.reply = False
    _, out = _buy(tool)
    assert out.startswith("PAYMENT OUTCOME UNKNOWN"), out
    entries = list(_journal(wallet_path).values())
    assert len(entries) == 1, entries
    seller.reply = True
    seller.paid_headers.clear()
    return entries[0]["hash"]


def _strip_payee_from_journalled_header(wallet_path):
    """Leave the journalled block's payee unreadable from its header, so the
    tool cannot see it before sending and only the post-payment check is left."""
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    j = json.loads(p.read_text())
    for entry in j.values():
        payload = json.loads(base64.b64decode(entry["header"]))
        payload["payload"]["block"].pop("link_as_account", None)
        entry["header"] = base64.b64encode(json.dumps(payload).encode()).decode()
    p.write_text(json.dumps(j))


def _preview_a_then_pay_read_b(seller):
    # Reads 1 and 2 are the tool's two dry runs; read 3 is feeless402's paying read.
    start = seller.reads
    seller.quote_for = lambda n: A if n - start <= 2 else B


# --- the refusal before anything is sent ---------------------------------------


def test_a_block_journalled_to_another_payee_is_refused_before_anything_is_sent(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    built.clear()
    _preview_a_then_pay_read_b(seller)
    preview, out = _buy(tool)
    assert A in preview
    assert out.startswith("REFUSED: a payment for this same request is already signed to a DIFFERENT payee"), out
    assert B in out and old_block in out, out
    assert "PAID" not in out
    assert seller.paid_headers == [], "the journalled block to B was re-sent"
    assert built == []


# --- the check after the payment ---------------------------------------------


def test_a_re_presented_block_to_another_payee_is_never_reported_as_paid_to_the_authorised_one(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    built.clear()
    _preview_a_then_pay_read_b(seller)
    _, out = _buy(tool)
    # feeless402 really did re-present the old block to B, without building one.
    assert len(seller.paid_headers) == 1 and built == []
    assert not out.startswith("PAID"), out
    assert out.startswith("PAYEE MISMATCH"), out
    assert f"block actually pays: {B}" in out, out
    assert f"authorised pay_to:   {A}" in out, out
    assert old_block in out
    assert f"signed to {A}" not in out, out
    assert "pay_to:    " + A not in out, out


def test_under_a_mandate_the_mismatch_says_the_allow_list_was_not_checked(env, tmp_path):
    seller, built, wallet_path = env
    agent = Wallet(pathlib.Path(wallet_path))
    agent.load()
    mandate = M.build_mandate(agent.address, OPERATOR, PRICE * 5, PRICE,
                              "Buy reports from the seller", "2030-01-01T00:00:00Z",
                              allowed_payees=[A, B])
    mandate_path = tmp_path / "mandate.json"
    mandate_path.write_text(json.dumps(M.sign_mandate(mandate, OPERATOR_KEY)))
    tool = _tool(wallet_path, mandate_path=str(mandate_path),
                 mandate_ledger=str(tmp_path / "mandate.ledger.json"))
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    built.clear()
    _preview_a_then_pay_read_b(seller)
    _, out = _buy(tool)
    assert out.startswith("PAYEE MISMATCH"), out
    assert "NOT checked against your operator's mandate" in out, out


def test_a_re_presented_block_to_another_payee_with_no_reply_names_the_real_payee(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    _preview_a_then_pay_read_b(seller)
    seller.reply = False
    _, out = _buy(tool)
    assert out.startswith("PAYMENT OUTCOME UNKNOWN"), out
    assert f"PAYEE MISMATCH: this block pays {B}, NOT the payee you authorised ({A})" in out, out


# --- controls --------------------------------------------------------------------


def test_a_re_presented_block_to_the_authorised_payee_still_reads_paid(env):
    """The journal doing its job - re-presenting the SAME block to the SAME payee
    after a lost reply - must not be refused or flagged."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, A, wallet_path)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert f"pay_to:    {A}" in out and old_block in out, out
    assert len(seller.paid_headers) == 1 and built == []


def test_an_ordinary_payment_through_the_real_client_reads_paid(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]
    assert _journal(wallet_path) == {}
