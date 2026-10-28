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
from nano_pay.verify import block_hash
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


# feeless402 0.2.12 added the request body to the journal key
# (`_request_fingerprint`); 0.2.9-0.2.11 key on (method, url, pay_to, amount)
# only and so re-present a block for another body too.
KEYS_BODY = hasattr(X, "_request_fingerprint") and hasattr(X, "_journal_key")

# The ledger as the stubbed node sees it: every block built below is signed by
# PAYER and follows PREV, whose balance is PREV_BALANCE, so the block's own
# balance gives its amount. PREV is the real state-block hash of PREV_CONTENTS,
# as on a real ledger: the tool hashes the node's answer and checks it.
PAYER_KEY = M.private_key_from_seed(bytes.fromhex("22" * 32), 0)  # test-fixture
PAYER = M.address_from_public_key(M.public_key_from_private(PAYER_KEY))
PREV_BALANCE = 10 ** 30
PREV_CONTENTS = {"type": "state", "account": PAYER, "previous": "CD" * 32,
                 "representative": PAYER, "balance": str(PREV_BALANCE), "link": "00" * 32,
                 "signature": "00" * 64, "work": "00" * 8}
PREV = block_hash(PREV_CONTENTS)


class Resp:
    def __init__(self, code, headers=None, text="", body=None):
        self.status_code, self.headers, self.text, self._body = code, headers or {}, text, body

    def json(self):
        if self._body is None:
            return {}
        return self._body


def _payment_required(pay_to, amount=PRICE):
    q = {"x402Version": 2, "accepts": [{"scheme": "exact", "network": "nano:mainnet",
                                        "asset": "XNO", "amount": str(amount), "payTo": pay_to}]}
    return {"payment-required": base64.b64encode(json.dumps(q).encode()).decode()}


class Seller:
    """An x402 seller on the wire. `quote_for(n)` names the payee of the n-th
    unpaid read and `amount_for(n)` its price; `reply` is False to drop every
    paid request (no reply); `receipt` is a payment-response the merchant sends
    with a paid reply; `on_read(n)` runs on the n-th unpaid read."""

    def __init__(self):
        self.reads = 0
        self.quote_for = lambda n: A
        self.amount_for = lambda n: PRICE
        self.on_read = lambda n: None
        self.reply = True
        self.receipt = None
        self.paid_headers = []
        self.dialect = "v2"

    def request(self, method, url, headers=None, **kw):
        headers = headers or {}
        if "X-PAYMENT" in headers:
            self.paid_headers.append(headers["X-PAYMENT"])
            if not self.reply:
                raise requests.ConnectionError("merchant did not reply")
            hdrs = {}
            if self.receipt is not None:
                hdrs["payment-response"] = base64.b64encode(json.dumps(self.receipt).encode()).decode()
            return Resp(200, hdrs, "the resource")
        self.reads += 1
        self.on_read(self.reads)
        if self.dialect == "nanogpt":
            # NanoGPT: the offer carries a paymentId, so feeless402 sends a v1
            # payload that does not echo the offer (no `accepted`, no amount).
            body = {"x402Version": 1, "accepts": [{
                "scheme": "nano", "protocolScheme": "exact", "network": "nano:mainnet",
                "maxAmountRequired": str(self.amount_for(self.reads)),
                "payTo": self.quote_for(self.reads), "paymentId": "pid%d" % self.reads,
                "asset": "XNO"}]}
            return Resp(402, {}, json.dumps(body), body)
        return Resp(402, _payment_required(self.quote_for(self.reads), self.amount_for(self.reads)))


class RPC:
    """The ledger holds every block asked about (a payment whose reply was lost).
    PREV, the block every stubbed payment follows, has balance PREV_BALANCE;
    `answers_prev=False` is a node that does not say."""

    answers_prev = True

    def call(self, body):
        if body.get("hash") == PREV and self.answers_prev:
            return {"block_account": PAYER, "balance": str(PREV_BALANCE),
                    "contents": dict(PREV_CONTENTS), "confirmed": "true"}
        return {"contents": {}, "confirmed": "true"}


@pytest.fixture
def env(monkeypatch, tmp_path):
    seller = Seller()
    monkeypatch.setattr(requests, "request", seller.request)
    # feeless402 0.2.8 has no module-level `time` (and no journal).
    if hasattr(X, "time"):
        monkeypatch.setattr(X.time, "sleep", lambda s: None)
    built = []

    def build(self, rpc, to, amt):
        # Shaped like nanopy's send block: the payee is in the signed `link`
        # (the account's public key) and in `link_as_account`, and the balance
        # after the send follows PREV.
        built.append((to, int(amt)))
        block = {"type": "state", "account": PAYER, "representative": PAYER,
                 "previous": PREV, "balance": str(PREV_BALANCE - int(amt)),
                 "link": M.public_key_from_address(to).hex().upper(), "link_as_account": to}
        return block, ("%064X" % (0xB10C + len(built))), "root"

    monkeypatch.setattr(Wallet, "build_payment_block", build)
    wallet_path = tmp_path / "wallet.json"
    Wallet(pathlib.Path(wallet_path)).create()
    return seller, built, wallet_path


def _tool(wallet_path, rpc=None, **kw):
    return T.make_nano_x402_tool(wallet_path=str(wallet_path), rpc=rpc or RPC(), default_max_xno=CAP, **kw)


def _call(tool, **args):
    raw = json.dumps(dict({"url": URL}, **args))
    ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
    return asyncio.run(tool.on_invoke_tool(ctx, raw))


def _buy(tool, **args):
    preview = _call(tool, dry_run=True, **args)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    return preview, _call(tool, dry_run=False, quote_token=token, **args)


def _journal(wallet_path):
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _journal_a_lost_payment_to(seller, tool, payee, wallet_path, amount=PRICE, **args):
    """An earlier, authorised redeem to `payee` whose reply never came back:
    feeless402 keeps the signed block in its journal to re-present it."""
    if not hasattr(X, "_journal_load"):
        pytest.skip("this feeless402 has no payment journal (before 0.2.9)")
    seller.quote_for = lambda n: payee
    seller.amount_for = lambda n: amount
    seller.reply = False
    _, out = _buy(tool, **args)
    assert out.startswith("PAYMENT OUTCOME UNKNOWN"), out
    entries = list(_journal(wallet_path).values())
    assert len(entries) == 1, entries
    seller.reply = True
    seller.amount_for = lambda n: PRICE
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
        payload["payload"]["block"].pop("link", None)
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
    # The operator is told exactly what to clear, and the agent not to pay.
    journal_file = pathlib.Path(wallet_path).parent / "pending-payments.json"
    (key,) = _journal(wallet_path).keys()
    assert f"journal file:        {journal_file}" in out, out
    assert f'journal entry:       "{key}"' in out, out
    assert "do NOT pay again" in out and "remove only the journal entry named above" in out, out
    assert seller.paid_headers == [], "the journalled block to B was re-sent"
    assert built == []


# --- the check after the payment ---------------------------------------------


def test_a_re_presented_block_whose_payee_cannot_be_read_is_unverified_never_paid(env):
    """The pre-send check cannot see the journalled block's payee, so the block
    to B goes out. The receipt's pay_to (B here) is not proof of the payee - a
    merchant can overwrite it - so the result is PAYEE UNVERIFIED."""
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
    assert out.startswith("PAYEE UNVERIFIED"), out
    assert f"authorised pay_to:   {A}" in out, out
    assert "block actually pays: UNKNOWN" in out, out
    assert f"reported pay_to:     {B}" in out and "not proof of the payee" in out, out
    assert old_block in out
    assert f"signed to {A}" not in out, out
    assert "pay_to:    " + A not in out, out


def test_under_a_mandate_an_unverified_block_says_the_allow_list_was_not_checked(env, tmp_path):
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
    assert out.startswith("PAYEE UNVERIFIED"), out
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
    assert "re-sent:" in out, out
    assert len(seller.paid_headers) == 1 and built == []


def test_an_ordinary_payment_through_the_real_client_reads_paid(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]
    assert "re-sent" not in out, out
    assert _journal(wallet_path) == {}


# --- review round 2 ------------------------------------------------------------


def _sent_payee(header):
    return json.loads(base64.b64decode(header))["payload"]["block"]["link_as_account"]


def _move_journal_aside(wallet_path):
    jp = pathlib.Path(wallet_path).parent / "pending-payments.json"
    saved = jp.read_text()
    jp.unlink()
    return jp, saved


def _land_journal_on_paying_read(seller, jp, saved):
    """Another tool instance or process sharing the wallet writes its journal
    entry to B after this tool's pre-send check, during the paying read."""
    start = seller.reads

    def on_read(n):
        if n - start == 3:
            jp.write_text(saved)

    seller.on_read = on_read
    seller.quote_for = lambda n: A if n - start <= 2 else B


def test_an_entry_written_during_the_paying_read_is_a_payee_mismatch_not_paid(env):
    """P2: the journal entry to B appears after the pre-send check. The block to
    B is re-presented; the tool must name B, from the signed block itself."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    jp, saved = _move_journal_aside(wallet_path)
    built.clear()
    _land_journal_on_paying_read(seller, jp, saved)
    _, out = _buy(tool)
    assert built == [] and len(seller.paid_headers) == 1
    assert _sent_payee(seller.paid_headers[0]) == B
    assert not out.startswith("PAID"), out
    assert out.startswith("PAYEE MISMATCH"), out
    assert f"block actually pays: {B}" in out and old_block in out, out
    assert f"signed to {A}" not in out, out


def test_an_unreadable_entry_written_during_the_paying_read_is_unverified(env):
    """P2 with the late entry's payee unreadable: nothing positively confirms
    the payee, so the tool says so instead of PAID."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    jp, saved = _move_journal_aside(wallet_path)
    built.clear()
    _land_journal_on_paying_read(seller, jp, saved)
    seller.receipt = {"pay_to": A, "status": "ok"}
    _, out = _buy(tool)
    assert built == [] and len(seller.paid_headers) == 1
    assert out.startswith("PAYEE UNVERIFIED"), out
    assert f"signed to {A}" not in out, out


def test_a_merchant_receipt_naming_the_authorised_payee_does_not_confirm_it(env):
    """P1: the journalled header's payee is unreadable and the merchant's
    payment-response says pay_to=A while the block sent pays B. The merchant's
    word never confirms the payee."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    built.clear()
    _preview_a_then_pay_read_b(seller)
    seller.receipt = {"pay_to": A, "status": "ok"}
    _, out = _buy(tool)
    assert built == [] and len(seller.paid_headers) == 1
    sent = json.loads(base64.b64decode(seller.paid_headers[0]))
    assert sent["accepted"]["payTo"] == B
    assert not out.startswith("PAID"), out
    assert out.startswith("PAYEE UNVERIFIED"), out
    assert f"signed to {A}" not in out, out
    assert f"reported pay_to:     {A}" in out and "not proof" in out, out


def test_the_payee_is_matched_by_the_block_hash_not_any_entry(env):
    """A live entry for another request that pays A must not vouch for the
    unreadable block to B that was actually re-presented."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _strip_payee_from_journalled_header(wallet_path)
    # An unrelated, readable entry to A for another URL.
    other = T._x402_module._journal_key("GET", URL + "/other", A, PRICE)
    j = _journal(wallet_path)
    (entry,) = j.values()
    payload = json.loads(base64.b64decode(entry["header"]))
    payload["payload"]["block"]["link_as_account"] = A
    payload["payload"]["block"]["link"] = M.public_key_from_address(A).hex().upper()
    j[other] = dict(entry, url=URL + "/other", hash="%064X" % 0xA11CE,
                    header=base64.b64encode(json.dumps(payload).encode()).decode())
    (pathlib.Path(wallet_path).parent / "pending-payments.json").write_text(json.dumps(j))
    built.clear()
    _preview_a_then_pay_read_b(seller)
    _, out = _buy(tool)
    assert built == [] and len(seller.paid_headers) == 1
    assert not out.startswith("PAID"), out
    assert out.startswith("PAYEE UNVERIFIED"), out


def test_xrb_and_nano_spellings_of_the_authorised_payee_are_the_same_account(env):
    """A block journalled to xrb_A is a block to A: no refusal, and when it is
    re-presented it reads PAID."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    xa = "xrb_" + A[len("nano_"):]
    old_block = _journal_a_lost_payment_to(seller, tool, xa, wallet_path)
    built.clear()
    start = seller.reads
    seller.quote_for = lambda n: A if n - start <= 2 else xa
    _, out = _buy(tool)
    assert not out.startswith("REFUSED"), out
    assert built == [] and len(seller.paid_headers) == 1
    assert out.startswith("PAID"), out
    assert old_block in out and "re-sent:" in out, out
    assert "merchant claims pay_to" not in out, out


def test_xrb_spelling_with_no_reply_is_not_a_mismatch(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    xa = "xrb_" + A[len("nano_"):]
    _journal_a_lost_payment_to(seller, tool, xa, wallet_path)
    start = seller.reads
    seller.quote_for = lambda n: A if n - start <= 2 else xa
    seller.reply = False
    _, out = _buy(tool)
    assert out.startswith("PAYMENT OUTCOME UNKNOWN"), out
    assert f"pay_to:    {xa}" in out, out
    assert "PAYEE MISMATCH" not in out, out


def test_an_entry_for_a_different_body_does_not_refuse(env):
    """feeless402 0.2.12+ keys its journal on the request body too: a block for
    another body is never re-presented for this one, so it must not block it.
    Before 0.2.12 the key leaves the body out, the block COULD be re-presented,
    and the tool refuses."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 2}')
    if not KEYS_BODY:
        assert out.startswith("REFUSED: a payment for this same request"), out
        assert seller.paid_headers == [] and built == []
        return
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)] and _sent_payee(seller.paid_headers[0]) == A


def test_an_entry_for_the_same_body_to_another_payee_is_refused(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 1}')
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert old_block in out and seller.paid_headers == [] and built == []


def test_an_entry_above_this_price_does_not_refuse(env):
    """feeless402 refuses an amount above the price authorised before it looks
    in the journal, so a block for more than this redeem's price is never
    re-presented here."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, amount=PRICE + 1)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]


def test_an_entry_at_this_price_to_the_other_payee_is_refused(env):
    """The control for the one above: the same entry at the authorised price
    could be re-presented, so it refuses."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, amount=PRICE)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out


@pytest.fixture
def clock(monkeypatch):
    now = [1_900_000_000.0]
    monkeypatch.setattr(T.time, "time", lambda: now[0])
    return now


def _age_journal(wallet_path, t):
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    j = json.loads(p.read_text())
    for entry in j.values():
        entry["t"] = t
    p.write_text(json.dumps(j))


def test_an_entry_exactly_at_its_ttl_has_expired_and_does_not_refuse(env, clock):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _age_journal(wallet_path, clock[0] - X.JOURNAL_TTL_S)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]


def test_an_entry_just_inside_its_ttl_still_refuses_and_says_when_it_expires(env, clock):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _age_journal(wallet_path, clock[0] - X.JOURNAL_TTL_S + 60)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out
    import time as _time
    expires = _time.strftime("%Y-%m-%d %H:%M:%S UTC", _time.gmtime(clock[0] + 60))
    assert f"(expires {expires})" in out, out


def test_the_pin_counts_the_blocks_it_builds():
    calls = []

    class Inner:
        def build_payment_block(self, rpc, to, amt):
            calls.append(to)
            return {"link_as_account": to}, "H", "root"

    pinned = T._PayeePinnedWallet(Inner(), A)
    assert pinned.built == 0
    pinned.build_payment_block(None, A, PRICE)
    pinned.build_payment_block(None, A, PRICE)
    assert pinned.built == 2
    with pytest.raises(T._PayeeMoved):
        pinned.build_payment_block(None, B, PRICE)
    assert pinned.built == 2 and calls == [A, A]


def test_the_journalled_payee_comes_from_the_signed_link_when_present():
    link_b = M.public_key_from_address(B).hex().upper()
    hdr = lambda block: base64.b64encode(json.dumps({"payload": {"block": block}}).encode()).decode()
    assert T._journalled_block(hdr({"link": link_b}))[0] == B
    assert T._journalled_block(hdr({"link": link_b, "link_as_account": B}))[0] == B
    # A link_as_account that disagrees with the signed link is not believed.
    assert T._journalled_block(hdr({"link": link_b, "link_as_account": A}))[0] is None
    assert T._journalled_block(hdr({}))[0] is None
    assert T._journalled_block("not base64 json") == (None, None)


# --- review round 3 ------------------------------------------------------------


def _nanogpt(seller):
    seller.dialect = "nanogpt"


def test_the_e2e_block_carries_a_signed_link_and_the_payee_is_read_from_it(env):
    """The stubbed block is shaped like a real one: `link` holds the payee's key.
    With `link_as_account` removed from the journalled header, the refusal still
    names B, read from `link` alone."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    j = json.loads(p.read_text())
    (entry,) = j.values()
    payload = json.loads(base64.b64decode(entry["header"]))
    assert payload["payload"]["block"]["link"] == M.public_key_from_address(B).hex().upper()
    payload["payload"]["block"].pop("link_as_account")
    entry["header"] = base64.b64encode(json.dumps(payload).encode()).decode()
    p.write_text(json.dumps(j))
    built.clear()
    _preview_a_then_pay_read_b(seller)
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert f"{old_block} to {B}" in out, out
    assert seller.paid_headers == [] and built == []


def test_nanogpt_an_entry_for_a_different_body_does_not_refuse(env):
    """NanoGPT dialect: the header echoes no amount, so the amount is read from
    the ledger (the block's predecessor's balance minus its own) and the key is
    recomputed with the body. Another body is never re-presented (0.2.12+)."""
    seller, built, wallet_path = env
    _nanogpt(seller)
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    (entry,) = _journal(wallet_path).values()
    assert "accepted" not in json.loads(base64.b64decode(entry["header"]))
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 2}')
    if not KEYS_BODY:
        assert out.startswith("REFUSED: a payment for this same request"), out
        return
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)] and _sent_payee(seller.paid_headers[0]) == A


def test_nanogpt_an_entry_for_the_same_body_to_another_payee_is_refused(env):
    seller, built, wallet_path = env
    _nanogpt(seller)
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 1}')
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert old_block in out and seller.paid_headers == [] and built == []


def test_nanogpt_an_amount_the_ledger_does_not_give_refuses_conservatively(env):
    """When the node does not say what the block pays, a NanoGPT entry for the
    same method and URL cannot be ruled out, even for another body."""
    seller, built, wallet_path = env
    _nanogpt(seller)
    rpc = RPC()
    tool = _tool(wallet_path, rpc=rpc)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    rpc.answers_prev = False
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 2}')
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert seller.paid_headers == [] and built == []


def test_nanogpt_an_entry_above_this_price_does_not_refuse(env):
    seller, built, wallet_path = env
    _nanogpt(seller)
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, amount=PRICE + 1)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]


class _NoKeyHelpers:
    """feeless402 as seen by the tool, without the named helpers (or with them
    raising), the way 0.2.9-0.2.11 lack `_request_fingerprint`."""

    def __init__(self, missing=(), raising=()):
        self._missing, self._raising = set(missing), set(raising)

    def __getattr__(self, name):
        if name in self._missing:
            raise AttributeError(name)
        if name in self._raising:
            def boom(*a, **k):
                raise RuntimeError("key function failed")
            return boom
        return getattr(X, name)


@pytest.mark.parametrize("missing", [("_journal_key",), ("_request_fingerprint",),
                                     ("_journal_key", "_request_fingerprint")])
def test_without_the_key_helpers_another_payee_for_the_same_url_refuses(env, monkeypatch, missing):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    monkeypatch.setattr(T, "_x402_module", _NoKeyHelpers(missing=missing))
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 2}')
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert seller.paid_headers == [] and built == []


@pytest.mark.parametrize("raising", ["_journal_key", "_request_fingerprint"])
def test_a_key_helper_that_raises_refuses(env, monkeypatch, raising):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, method="POST", json_body='{"q": 1}')
    monkeypatch.setattr(T, "_x402_module", _NoKeyHelpers(raising=[raising]))
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool, method="POST", json_body='{"q": 2}')
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert seller.paid_headers == [] and built == []


def test_without_the_key_helpers_an_entry_above_this_price_still_does_not_refuse(env, monkeypatch):
    """feeless402 refuses an amount above the price before it reads the journal,
    in every version with one, so the amount decides before the helpers."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path, amount=PRICE + 1)
    monkeypatch.setattr(T, "_x402_module",
                        _NoKeyHelpers(missing=("_journal_key", "_request_fingerprint")))
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert built == [(A, PRICE)]


def test_same_payee_never_confirms_strings_that_are_not_addresses():
    bad = "nano_" + "1" * 60
    assert T._same_payee(A, A) and T._same_payee(A, "xrb_" + A[5:])
    assert not T._same_payee(bad, bad)
    assert not T._same_payee("not an address", "not an address")
    assert not T._same_payee(A, A[:-1] + ("a" if A[-1] != "a" else "b"))
    assert not T._same_payee(A, "")


@pytest.mark.parametrize("t,live", [(float("inf"), True), (1e20, True), (float("nan"), False)])
def test_a_journal_time_out_of_range_is_judged_like_feeless402_and_never_crashes(env, t, live):
    """feeless402 keeps an entry while `now - t < TTL`: an infinite or far-future
    `t` stays live (and has no expiry date to print), a NaN one is dead."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    _age_journal(wallet_path, t)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    if live:
        assert out.startswith("REFUSED: a payment for this same request"), out
        assert old_block in out and "(expires unknown)" in out, out
        assert seller.paid_headers == [] and built == []
    else:
        assert out.startswith("PAID"), out
        assert built == [(A, PRICE)]


@pytest.mark.parametrize("t", [float("inf"), float("nan"), 1e20, -1e300])
def test_the_refusal_text_never_raises_on_a_strange_time(t):
    out = T._format_journalled_elsewhere_refusal(A, [{"hash": "H", "payee": B, "path": "p", "key": "k", "t": t}])
    assert "(expires " in out


def test_a_re_sent_block_under_a_mandate_says_the_mandate_was_not_charged_now(env, tmp_path):
    seller, built, wallet_path = env
    agent = Wallet(pathlib.Path(wallet_path))
    agent.load()
    mandate = M.build_mandate(agent.address, OPERATOR, PRICE * 5, PRICE,
                              "Buy reports from the seller", "2030-01-01T00:00:00Z",
                              allowed_payees=[A])
    mandate_path = tmp_path / "mandate.json"
    mandate_path.write_text(json.dumps(M.sign_mandate(mandate, OPERATOR_KEY)))
    tool = _tool(wallet_path, mandate_path=str(mandate_path),
                 mandate_ledger=str(tmp_path / "mandate.ledger.json"))
    _journal_a_lost_payment_to(seller, tool, A, wallet_path)
    built.clear()
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert "re-sent:" in out, out
    assert "mandate was NOT charged for this block in this call" in out, out
    assert "signed in an earlier call" in out and "unknown" in out, out


def test_a_re_sent_block_without_a_mandate_has_no_mandate_line(env):
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, A, wallet_path)
    seller.quote_for = lambda n: A
    _, out = _buy(tool)
    assert out.startswith("PAID") and "re-sent:" in out, out
    assert "mandate:" not in out, out


def test_an_unreadable_signed_link_is_never_replaced_by_link_as_account():
    hdr = lambda block: base64.b64encode(json.dumps({"payload": {"block": block}}).encode()).decode()
    assert T._journalled_block(hdr({"link_as_account": B}))[0] == B
    for link in ("zz" * 32, "AB", 7, None, ""):
        assert T._journalled_block(hdr({"link": link, "link_as_account": B}))[0] is None, link


def test_a_journalled_block_with_an_unreadable_link_is_unverified_not_refused_by_its_label(env):
    """The block to B has a corrupt `link` and `link_as_account` B. The unsigned
    label is not believed, so the payee is unreadable: nothing confirms it, and
    the re-presented block is PAYEE UNVERIFIED, never PAID."""
    seller, built, wallet_path = env
    tool = _tool(wallet_path)
    _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    j = json.loads(p.read_text())
    for entry in j.values():
        payload = json.loads(base64.b64decode(entry["header"]))
        payload["payload"]["block"]["link"] = "ZZ" * 32
        entry["header"] = base64.b64encode(json.dumps(payload).encode()).decode()
    p.write_text(json.dumps(j))
    built.clear()
    _preview_a_then_pay_read_b(seller)
    seller.receipt = {"pay_to": A}
    _, out = _buy(tool)
    assert built == [] and len(seller.paid_headers) == 1
    assert out.startswith("PAYEE UNVERIFIED"), out
    assert "block actually pays: UNKNOWN" in out, out


# --- the ledger's answer is authenticated, not trusted -----------------------------
#
# In the NanoGPT dialect the journalled amount is read from the node: the
# balance of the block the journalled one follows. That block's hash, PREV, is
# in the journalled block, signed by this wallet; the node's `contents` must
# hash to it, so a node that answers wrongly cannot change the amount read.


def _ledger_block(amount=PRICE, **over):
    block = {"type": "state", "account": PAYER, "representative": PAYER, "previous": PREV,
             "balance": str(PREV_BALANCE - amount),
             "link": M.public_key_from_address(B).hex().upper(), "link_as_account": B}
    block.update(over)
    return block


class _Answer:
    """A node whose `block_info` reply for PREV is `answer` (or raises it)."""

    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def call(self, body):
        self.calls += 1
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer


def _honest_answer(**top):
    reply = {"block_account": PAYER, "balance": str(PREV_BALANCE),
             "contents": dict(PREV_CONTENTS), "confirmed": "true"}
    reply.update(top)
    return reply


def _altered(**fields):
    reply = _honest_answer()
    reply["contents"].update(fields)
    return reply


def _shifted(d):
    """Contents that hash to PREV but read another balance: the state-block hash
    is taken over the fields' hex concatenated, so moving the boundaries by `d`
    hex digits (into `previous`, out of `link`) keeps the bytes - and the hash -
    while `balance` now reads a different 32 hex digits. Only fixed field widths
    stop it."""
    c = dict(PREV_CONTENTS)
    prev, link = c["previous"], c["link"]
    rep = M.public_key_from_address(c["representative"]).hex().upper()
    bal = "%032X" % int(c["balance"])
    c.update(previous=prev + rep[:d],
             representative=M.address_from_public_key(bytes.fromhex(rep[d:] + bal[:d])),
             balance=str(int(bal[d:] + link[:d], 16)), link=link[d:])
    reply = _honest_answer(balance=c["balance"])
    reply["contents"] = c
    return reply


def test_an_honest_node_gives_the_signed_amount():
    assert T._amount_from_ledger(_ledger_block(), RPC()) == PRICE
    assert T._amount_from_ledger(_ledger_block(), _Answer(_honest_answer())) == PRICE
    # The node may spell the account xrb_ and the hashes in lower case.
    reply = _honest_answer(block_account="xrb_" + PAYER[5:])
    reply["contents"].update(account="xrb_" + PAYER[5:], representative="xrb_" + PAYER[5:],
                             previous=PREV_CONTENTS["previous"].lower())
    assert T._amount_from_ledger(_ledger_block(previous=PREV.lower()), _Answer(reply)) == PRICE


@pytest.mark.parametrize("balance", [PREV_BALANCE + 1, PREV_BALANCE - 1, 2 ** 128 - 1, 10 ** 40])
def test_a_top_level_balance_that_disagrees_with_the_unchanged_contents_is_refused(balance):
    """The reply's `balance` is not where the amount comes from: a node whose
    top-level balance disagrees with its own (authentic) contents is not believed."""
    assert T._amount_from_ledger(_ledger_block(), _Answer(_honest_answer(balance=str(balance)))) is None


@pytest.mark.parametrize("fields", [
    {"balance": str(PREV_BALANCE + 1)}, {"balance": str(PREV_BALANCE - 1)},
    {"balance": str(2 ** 128 - 1)}, {"balance": str(10 ** 40)},
    {"representative": B}, {"link": "11" * 32}, {"previous": "CE" * 32},
    {"account": B}, {"balance": " %d" % PREV_BALANCE}, {"balance": PREV_BALANCE},
    {"balance": "1_" + str(PREV_BALANCE)[1:]}, {"representative": "garbage"},
    {"link": "zz"}, {"previous": None},
])
def test_contents_that_do_not_hash_to_previous_are_refused(fields):
    """A node that alters the contents - and the top-level balance to match - is
    caught by the hash."""
    reply = _altered(**fields)
    reply["balance"] = fields.get("balance", reply["balance"])
    reply.pop("block_account")
    assert T._amount_from_ledger(_ledger_block(), _Answer(reply)) is None, fields


@pytest.mark.parametrize("d", [2, 4, 8])
def test_contents_with_shifted_field_boundaries_are_refused(d):
    """A node that moves hex digits between `previous`, `representative`,
    `balance` and `link` keeps the hash and changes the balance read. Fields of
    the wrong width are not believed, so it gives no amount, not a wrong one."""
    reply = _shifted(d)
    assert T._state_block_hash(reply["contents"]) == PREV  # the forgery does hash to PREV
    assert int(reply["contents"]["balance"]) != PREV_BALANCE
    assert T._amount_from_ledger(_ledger_block(), _Answer(reply)) is None


@pytest.mark.parametrize("fields", [
    {"balance": str(2 ** 128)}, {"balance": str(2 ** 130)}, {"previous": "CD" * 32 + "00"},
    {"link": "00" * 31}, {"previous": "CD" * 31}, {"link": "00" * 33},
])
def test_contents_fields_of_the_wrong_width_are_refused(fields):
    reply = _altered(**fields)
    reply["balance"] = fields.get("balance", reply["balance"])
    assert T._amount_from_ledger(_ledger_block(), _Answer(reply)) is None, fields


@pytest.mark.parametrize("reply", [
    {"balance": str(PREV_BALANCE)}, {"balance": str(PREV_BALANCE), "contents": {"balance": str(PREV_BALANCE)}},
    {"error": "Block not found"}, {}, [], "str", None, {"contents": "x"},
    _honest_answer(block_account=B),
])
def test_a_reply_without_authentic_contents_is_refused(reply):
    assert T._amount_from_ledger(_ledger_block(), _Answer(reply)) is None


@pytest.mark.parametrize("exc", [RuntimeError("every node failed"), TimeoutError("timed out"),
                                 ValueError("bad json")])
def test_an_rpc_that_raises_gives_no_amount(exc):
    assert T._amount_from_ledger(_ledger_block(), _Answer(exc)) is None


@pytest.mark.parametrize("over", [
    {"balance": str(PREV_BALANCE)}, {"balance": str(PREV_BALANCE + 5)},
    {"balance": None}, {"balance": "-5"}, {"account": B}, {"account": None},
    {"previous": "0" * 64}, {"previous": "AB"}, {"previous": "ZZ" * 32},
])
def test_a_journalled_block_that_gives_no_positive_amount_is_refused(over):
    block = _ledger_block(**over)
    if over.get("balance", "") is None:
        block.pop("balance")
    if "account" in over and over["account"] is None:
        block.pop("account")
    assert T._amount_from_ledger(block, RPC()) is None, over


def _rewrite_journalled_block(wallet_path, fn):
    p = pathlib.Path(wallet_path).parent / "pending-payments.json"
    j = json.loads(p.read_text())
    for entry in j.values():
        payload = json.loads(base64.b64decode(entry["header"]))
        fn(payload["payload"]["block"])
        entry["header"] = base64.b64encode(json.dumps(payload).encode()).decode()
    p.write_text(json.dumps(j))


def _nanogpt_lost_to_b_then_paying_read_b(env, rpc):
    seller, built, wallet_path = env
    _nanogpt(seller)
    tool = _tool(wallet_path, rpc=rpc)
    old_block = _journal_a_lost_payment_to(seller, tool, B, wallet_path)
    built.clear()
    _preview_a_then_pay_read_b(seller)
    return seller, built, wallet_path, tool, old_block


class _LiesAboutPrev(RPC):
    """Honest until `lie` is set; then answers `reply` (or raises it) for PREV."""

    def __init__(self, reply):
        self.reply, self.lie = reply, False

    def call(self, body):
        if self.lie and body.get("hash") == PREV:
            if isinstance(self.reply, BaseException):
                raise self.reply
            return self.reply
        return super().call(body)


@pytest.mark.parametrize("reply", [
    # The pre-fix bypass: a top-level balance off by one, or huge, beside unchanged contents.
    _honest_answer(balance=str(PREV_BALANCE + 1)), _honest_answer(balance=str(PREV_BALANCE - 1)),
    _honest_answer(balance=str(10 ** 40)),
    {"balance": str(PREV_BALANCE + 1), "contents": {"balance": str(PREV_BALANCE + 1)}},
    {"balance": str(PREV_BALANCE - 1), "contents": {"balance": str(PREV_BALANCE - 1)}},
    # Altered contents, consistent with themselves.
    dict(_altered(balance=str(PREV_BALANCE + 1)), balance=str(PREV_BALANCE + 1)),
    dict(_altered(balance=str(PREV_BALANCE - 1)), balance=str(PREV_BALANCE - 1)),
    # Contents that hash to PREV with the field boundaries shifted, so they read another balance.
    _shifted(2), _shifted(4),
    # No answer the tool can use.
    {"error": "Block not found"}, RuntimeError("every node failed"), TimeoutError("timed out"),
])
def test_a_node_that_answers_wrongly_cannot_skip_the_refusal(env, reply):
    rpc = _LiesAboutPrev(reply)
    seller, built, wallet_path, tool, old_block = _nanogpt_lost_to_b_then_paying_read_b(env, rpc)
    rpc.lie = True
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert old_block in out and seller.paid_headers == [] and built == []


@pytest.mark.parametrize("balance", [str(PREV_BALANCE), str(PREV_BALANCE + 5), None])
def test_a_journalled_block_with_no_positive_amount_still_refuses(env, balance):
    """A zero or negative difference, or no balance at all, is no amount: the
    entry cannot be ruled out, so it refuses (it is never read as 0, or as the
    whole previous balance)."""
    seller, built, wallet_path, tool, old_block = _nanogpt_lost_to_b_then_paying_read_b(env, RPC())

    def edit(block):
        if balance is None:
            block.pop("balance")
        else:
            block["balance"] = balance

    _rewrite_journalled_block(wallet_path, edit)
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert seller.paid_headers == [] and built == []


def test_an_entry_keyed_under_the_xrb_spelling_with_only_a_link_is_still_matched(env):
    """feeless402 keys the entry on the payee as the merchant spelled it (xrb_
    here); the tool reads the payee from the signed `link` (nano_), so it must
    try both spellings to recompute the key."""
    seller, built, wallet_path = env
    xrb_b = "xrb_" + B[5:]
    tool = _tool(wallet_path)
    old_block = _journal_a_lost_payment_to(seller, tool, xrb_b, wallet_path)
    _rewrite_journalled_block(wallet_path, lambda block: block.pop("link_as_account", None))
    built.clear()
    start = seller.reads
    seller.quote_for = lambda n: A if n - start <= 2 else xrb_b
    _, out = _buy(tool)
    assert out.startswith("REFUSED: a payment for this same request"), out
    assert old_block in out and seller.paid_headers == [] and built == []


def test_a_previous_block_of_another_account_gives_no_amount():
    """`previous` is authentic but belongs to another account (a journalled
    block that does not follow this wallet's own chain): no amount, even when
    the node does not name the account at the top level."""
    reply = _honest_answer()
    reply.pop("block_account")
    assert T._amount_from_ledger(_ledger_block(), _Answer(reply)) == PRICE
    assert T._amount_from_ledger(_ledger_block(account=B), _Answer(reply)) is None
