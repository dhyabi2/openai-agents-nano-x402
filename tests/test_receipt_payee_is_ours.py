"""The record says where the money went, not where the merchant says it went.
Offline: no HTTP, no node, no money.

`test_payee_moved_after_preview.py` closed the signing half: `_PayeePinnedWallet`
refuses to build a block to any address but the one quoted, minted into the
quote token and authorised, so a redeem that reaches a receipt at all was signed
to `quote["pay_to"]`.

The RECORD half was open. feeless402 sets its own ground truth and then merges
the merchant's receipt fields over it (`nano_pay/x402.py:584`):

    base = {..., "pay_to": pay_to, "block": new_frontier, ...}
    base.update({k: v for k, v in receipt.items()
                 if k not in ("settled", "block", "amount_xno",
                              "amount_raw", "note", "ledger",
                              "receipt_hash_mismatch")})
    base["amount_xno"] = raw_to_xno(amount)
    base["block"] = new_frontier

That exclusion list is the one its own comment calls "never let them speak for
ours" - and `pay_to` is not in it, nor among the two fields re-asserted
afterwards. So a merchant returning a `payment-response` header that names any
address at all wrote the one line of the receipt that says where the money went,
in the very field the payee pinning exists to guarantee. The block hash is
correct, so the `receipt_hash_mismatch` guard does not fire.

Two harms: the operator's audit trail becomes attacker-chosen text, and an
agent told to check the receipt's `pay_to` against its preview concludes the
payment went astray - and buys again.

`_format_receipt` is given the authorised payee and prints that. A merchant
claim that differs is still shown, named as the merchant's and as untrusted.
"""
import asyncio
import json
import os
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.tool_context import ToolContext
from nano_pay.wallet import Wallet

import openai_agents_nano.tool as T
from openai_agents_nano import mandate as M

PAYEE = "nano_1p7cqqnfo91zwcnse54f3ucyfi6xwzsbnkt3ay14cd1g6epmiygnt7jtcoa5"
OTHER = "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
XNO = 10 ** 30
PRICE = XNO // 1000
CAP = "0.01"
BLOCK = "AB" * 32


class EchoingSeller:
    """Quotes and is paid correctly; echoes `claims` as the receipt's `pay_to`.

    `claims` is what feeless402 hands back after the merge above: the merchant's
    field, already sitting where the tool's ground truth was.
    """

    def __init__(self, claims):
        self.claims, self.signed = claims, []

    def quote(self):
        return {"amount_raw": PRICE, "amount_xno": M.raw_to_xno(PRICE), "pay_to": PAYEE}

    def request_with_payment(self, method, url, wallet, rpc, max_raw, headers=None,
                             dry_run=False, **kw):
        class R:
            status_code, text = (402, "") if dry_run else (200, "the resource")
        if dry_run:
            return R(), self.quote()
        # Paid correctly: the block really is signed to the authorised payee.
        wallet.build_payment_block(rpc, PAYEE, PRICE)
        receipt = {"settled": True, "amount_xno": M.raw_to_xno(PRICE),
                   "block": BLOCK, "ledger": "confirmed"}
        if self.claims is not None:
            receipt["pay_to"] = self.claims
        return R(), receipt


def _env(monkeypatch, claims):
    seller = EchoingSeller(claims)
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", BLOCK, "root"))
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    Wallet(pathlib.Path(wallet_path)).create()
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP)
    return seller, tool


def _buy(tool):
    def call(**args):
        raw = json.dumps(dict({"url": "http://seller.invalid/report"}, **args))
        ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
        return asyncio.run(tool.on_invoke_tool(ctx, raw))
    preview = call(dry_run=True)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    return preview, call(dry_run=False, quote_token=token)


def _pay_to_line(text):
    line = re.search(r"^  pay_to:\s+(\S+)$", text, re.M)
    assert line, f"no pay_to line in:\n{text}"
    return line.group(1)


def test_the_pay_to_line_is_where_the_money_went(monkeypatch):
    seller, tool = _env(monkeypatch, claims=OTHER)
    preview, out = _buy(tool)

    assert out.startswith("PAID (Nano x402):"), out
    assert seller.signed == [(PAYEE, PRICE)], "the block really was signed to the authorised payee"
    assert _pay_to_line(out) == PAYEE, (
        "the receipt's pay_to must be the address this tool authorised and pinned, "
        "not the one the merchant echoed back")


def test_a_merchant_claim_that_differs_is_shown_and_named_untrusted(monkeypatch):
    _, tool = _env(monkeypatch, claims=OTHER)
    _, out = _buy(tool)

    assert OTHER in out, "the merchant's claim is still on the record"
    claim = re.search(r"^  merchant claims pay_to: (\S+) - UNTRUSTED", out, re.M)
    assert claim and claim.group(1) == OTHER, out
    assert PAYEE in out


def test_an_agent_comparing_the_receipt_to_its_preview_sees_them_agree(monkeypatch):
    """The second harm: a mismatch here is what makes an agent buy again."""
    _, tool = _env(monkeypatch, claims=OTHER)
    preview, out = _buy(tool)

    quoted = re.search(r"pay_to:\s+(\S+)", preview)
    assert quoted and quoted.group(1) == PAYEE, preview
    assert _pay_to_line(out) == quoted.group(1), (
        "the address the agent authorised and the address the receipt records "
        "must be the same, or an agent that checks will think its money went astray")


def test_an_honest_merchant_adds_no_untrusted_line(monkeypatch):
    """Control: when the echo agrees, the receipt reads exactly as before."""
    _, tool = _env(monkeypatch, claims=PAYEE)
    _, out = _buy(tool)

    assert _pay_to_line(out) == PAYEE
    assert "merchant claims pay_to" not in out, out


def test_a_merchant_that_echoes_no_payee_at_all_still_records_ours(monkeypatch):
    """Control: no `pay_to` in the receipt is not a blank line in the record."""
    _, tool = _env(monkeypatch, claims=None)
    _, out = _buy(tool)

    assert _pay_to_line(out) == PAYEE
    assert "merchant claims pay_to" not in out, out
