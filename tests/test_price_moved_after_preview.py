"""The agent pays what it previewed, or it pays nothing. Offline: no HTTP, no node, no money.

`request_with_payment` RE-READS the 402 before it signs, and caps that read against the
`max_raw` it is given. The tool used to hand it the operator's whole cap, so a seller could
quote cheap on both dry runs, raise the price on the paying read, and be paid anything up to
the cap. The quote_token binds pay_to and amount, but it is checked against the tool's own
read and never against the amount finally signed, so it did not catch this: previewed
0.001 XNO, signed 0.009 XNO, and the tool reported "PAID".
"""
import asyncio
import json
import os
import pathlib
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.tool_context import ToolContext
from nano_pay.wallet import Wallet
from nano_pay.x402 import PriceCapExceeded

import openai_agents_nano.tool as T
from openai_agents_nano import mandate as M

PAYEE = "nano_1p7cqqnfo91zwcnse54f3ucyfi6xwzsbnkt3ay14cd1g6epmiygnt7jtcoa5"
XNO = 10 ** 30
PRICE = XNO // 1000        # 0.001 XNO, what the seller quotes
RAISED = XNO * 9 // 1000   # 0.009 XNO, what it asks for when it is time to pay
CAP = "0.01"               # the operator's cap, comfortably above both


class MovingSeller:
    """Quotes `PRICE` on every dry run; asks `raise_to` on the paying read."""

    def __init__(self, raise_to=None):
        self.amount, self.raise_to, self.signed = PRICE, raise_to, []

    def quote(self):
        return {"amount_raw": self.amount, "amount_xno": M.raw_to_xno(self.amount), "pay_to": PAYEE}

    def request_with_payment(self, method, url, wallet, rpc, max_raw, headers=None,
                             dry_run=False, **kw):
        class R:
            status_code, text = (402, "") if dry_run else (200, "the resource")
        if dry_run:
            return R(), self.quote()
        if self.raise_to is not None:
            self.amount = self.raise_to      # after both dry runs, as a hostile seller would
        offer = self.quote()
        # feeless402's own check, verbatim in shape: nothing is built if it trips.
        if offer["amount_raw"] > max_raw:
            raise PriceCapExceeded(
                f"quote {M.raw_to_xno(offer['amount_raw'])} XNO exceeds cap "
                f"{M.raw_to_xno(max_raw)} XNO - refusing to pay")
        wallet.build_payment_block(rpc, offer["pay_to"], offer["amount_raw"])
        return R(), {"settled": True, "amount_xno": offer["amount_xno"], "pay_to": offer["pay_to"],
                     "block": "AB" * 32, "ledger": "confirmed"}


def _env(monkeypatch, raise_to):
    seller = MovingSeller(raise_to)
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))
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


def test_a_price_raised_after_the_preview_is_refused_and_nothing_is_signed(monkeypatch):
    seller, tool = _env(monkeypatch, raise_to=RAISED)
    preview, out = _buy(tool)
    assert "0.001" in preview, preview
    assert out.startswith("REFUSED: the endpoint asked for more than it quoted"), out
    assert "0.001" in out, out
    assert seller.signed == [], (
        "the agent previewed 0.001 XNO and must not sign a block for more; "
        f"signed {seller.signed}")


def test_the_cap_handed_to_the_payer_is_the_quoted_amount_not_the_operator_cap(monkeypatch):
    """Pins the mechanism, so a later edit cannot quietly widen it back to the cap."""
    seen = {}
    seller = MovingSeller()
    original = seller.request_with_payment

    def record(method, url, wallet, rpc, max_raw, **kw):
        if not kw.get("dry_run"):
            seen["max_raw"] = int(max_raw)
        return original(method, url, wallet, rpc, max_raw, **kw)

    monkeypatch.setattr(T, "request_with_payment", record)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    Wallet(pathlib.Path(wallet_path)).create()
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seen["max_raw"] == PRICE, (
        f"the payer was handed {M.raw_to_xno(seen['max_raw'])} XNO as its ceiling, "
        f"not the {M.raw_to_xno(PRICE)} XNO that was quoted and authorised")


def test_an_unchanged_offer_still_pays(monkeypatch):
    """The refusal must not be bought by refusing the ordinary case too."""
    seller, tool = _env(monkeypatch, raise_to=None)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE)]


def test_a_price_cut_after_the_preview_is_still_paid(monkeypatch):
    """A lower price is not a reason to refuse: the ceiling is a ceiling."""
    seller, tool = _env(monkeypatch, raise_to=PRICE // 2)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE // 2)]
