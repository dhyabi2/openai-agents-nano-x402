"""The agent pays WHO it previewed, or it pays nothing. Offline: no HTTP, no node, no money.

`test_price_moved_after_preview.py` closed the amount half of this: the tool now
hands `request_with_payment` the quoted amount as its ceiling instead of the
operator's whole cap, so a seller cannot quote cheap and charge more.

The payee half was open. `request_with_payment` RE-READS the 402 before it pays
and signs to `offer_pay_to()` of THAT read:

    if amount > max_raw: raise PriceCapExceeded(...)      # the amount is checked
    block, ... = wallet.build_payment_block(rpc, pay_to, amount)   # pay_to is not

So a seller could quote `nano_A` on both dry runs and answer `nano_B` for the
same amount on the paying read, and the block was signed to `nano_B`. The
quote_token binds `pay_to`, but against the tool's OWN read, never against the
address finally signed - exactly the reason it did not catch the moved price.
`_MandatedWallet` checks the signing-time payee, but only when an operator
mandate is configured, which is not the default.
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
# A different, checksum-shaped address: the one a hostile seller swaps in.
OTHER = "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
XNO = 10 ** 30
PRICE = XNO // 1000        # 0.001 XNO, unchanged throughout
CAP = "0.01"


class SwitchingSeller:
    """Quotes `PAYEE` on every dry run; names `switch_to` on the paying read.

    The amount never moves, so `max_raw` is satisfied and feeless402's own cap
    check passes - which is the point: the amount was the only thing checked.
    """

    def __init__(self, switch_to=None):
        self.pay_to, self.switch_to, self.signed = PAYEE, switch_to, []

    def quote(self):
        return {"amount_raw": PRICE, "amount_xno": M.raw_to_xno(PRICE), "pay_to": self.pay_to}

    def request_with_payment(self, method, url, wallet, rpc, max_raw, headers=None,
                             dry_run=False, **kw):
        class R:
            status_code, text = (402, "") if dry_run else (200, "the resource")
        if dry_run:
            return R(), self.quote()
        if self.switch_to is not None:
            self.pay_to = self.switch_to     # after both dry runs, as a hostile seller would
        offer = self.quote()
        if offer["amount_raw"] > max_raw:    # feeless402's own check, verbatim in shape
            raise PriceCapExceeded(
                f"quote {M.raw_to_xno(offer['amount_raw'])} XNO exceeds cap "
                f"{M.raw_to_xno(max_raw)} XNO - refusing to pay")
        wallet.build_payment_block(rpc, offer["pay_to"], offer["amount_raw"])
        return R(), {"settled": True, "amount_xno": offer["amount_xno"], "pay_to": offer["pay_to"],
                     "block": "AB" * 32, "ledger": "confirmed"}


def _env(monkeypatch, switch_to, mandate_path=None, mandate_ledger=None):
    seller = SwitchingSeller(switch_to)
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    Wallet(pathlib.Path(wallet_path)).create()
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP,
                                 mandate_path=mandate_path, mandate_ledger=mandate_ledger)
    return seller, tool


def _buy(tool):
    def call(**args):
        raw = json.dumps(dict({"url": "http://seller.invalid/report"}, **args))
        ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
        return asyncio.run(tool.on_invoke_tool(ctx, raw))
    preview = call(dry_run=True)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    return preview, call(dry_run=False, quote_token=token)


def test_a_payee_switched_after_the_preview_is_refused_and_nothing_is_signed(monkeypatch):
    seller, tool = _env(monkeypatch, switch_to=OTHER)
    preview, out = _buy(tool)
    assert PAYEE in preview, preview
    assert out.startswith("REFUSED: the endpoint changed where the money goes"), out
    assert seller.signed == [], (
        "the agent previewed and authorised a payment to "
        f"{PAYEE} and must not sign a block to anyone else; signed {seller.signed}")


def test_the_refusal_names_both_addresses_so_the_agent_can_tell_them_apart(monkeypatch):
    seller, tool = _env(monkeypatch, switch_to=OTHER)
    _, out = _buy(tool)
    assert PAYEE in out and OTHER in out, out


def test_the_amount_being_within_the_cap_does_not_excuse_a_switched_payee(monkeypatch):
    """The amount is the only thing feeless402 checks, and here it is correct.
    A block signed to the wrong account for the right amount is still lost money."""
    seller, tool = _env(monkeypatch, switch_to=OTHER)
    _, out = _buy(tool)
    assert "exceeds cap" not in out, (
        "this must not pass as a cap refusal: the price never moved")
    assert seller.signed == []


OPERATOR_SEED = "11" * 32  # test-fixture, same as tests/test_tool_mandate.py
OPERATOR_KEY = M.private_key_from_seed(bytes.fromhex(OPERATOR_SEED), 0)
OPERATOR = M.address_from_public_key(M.public_key_from_private(OPERATOR_KEY))


def _ledger_spent(path):
    """(spent_raw, number of payment entries) in a mandate ledger; (0, 0) if absent."""
    if not os.path.exists(path):
        return (0, 0)
    with open(path) as fh:
        data = json.load(fh)
    return (int(data.get("spent_raw", 0)), len(data.get("payments") or []))


def test_a_payee_switch_refuses_under_a_mandate_before_its_ledger_is_touched(monkeypatch):
    """The pin sits OUTSIDE the mandate proxy, so a moved payee refuses before
    `MandateGuard.spend` reserves anything.

    A mandate whose allow-list already excludes the new address would refuse
    this too - but by reserving and releasing in its ledger first, and only when
    an operator configured a mandate at all. The refusal must come from the pin.
    """
    seller = SwitchingSeller(OTHER)
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    agent = Wallet(pathlib.Path(wallet_path))
    agent.create()
    # Both addresses are allowed by the mandate, so the mandate itself has no
    # objection: the only thing standing between the agent and the wrong payee
    # is the pin.
    mandate = M.build_mandate(agent.address, OPERATOR, PRICE * 3, PRICE,
                              "Buy one report per day from the seller",
                              "2030-01-01T00:00:00Z", allowed_payees=[PAYEE, OTHER])
    mandate_path = os.path.join(td, "mandate.json")
    ledger_path = os.path.join(td, "mandate.ledger.json")
    with open(mandate_path, "w") as fh:
        json.dump(M.sign_mandate(mandate, OPERATOR_KEY), fh)
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP,
                                 mandate_path=mandate_path, mandate_ledger=ledger_path)
    _, out = _buy(tool)
    assert out.startswith("REFUSED: the endpoint changed where the money goes"), out
    assert seller.signed == []
    # Nothing was signed, so the mandate ledger holds no reservation for it.
    # `MandateGuard.spend` appends to `payments` and adds to `spent_raw` BEFORE
    # it calls the block builder, and leaves the entry as "unknown" if that
    # raises - so a pin that fired inside the proxy instead of outside it would
    # show up here as a non-zero spend against a payment that never happened.
    assert _ledger_spent(ledger_path) == (0, 0), (
        f"the mandate ledger recorded {_ledger_spent(ledger_path)} "
        "(spent_raw, payments) for a payment that was never signed")


# --- controls: the pin must not cost a good payment ---------------------------


def test_an_unchanged_payee_still_pays(monkeypatch):
    seller, tool = _env(monkeypatch, switch_to=None)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE)]


def test_the_same_payee_quoted_again_on_the_paying_read_still_pays(monkeypatch):
    """A seller that re-states the same address is not 'changing' anything."""
    seller, tool = _env(monkeypatch, switch_to=PAYEE)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE)]


def test_a_price_cut_with_the_same_payee_is_still_paid(monkeypatch):
    """The payee pin must not interfere with the amount ceiling being a ceiling."""
    seller = SwitchingSeller(None)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))

    def cheaper(method, url, wallet, rpc, max_raw, headers=None, dry_run=False, **kw):
        class R:
            status_code, text = (402, "") if dry_run else (200, "the resource")
        if dry_run:
            return R(), seller.quote()
        wallet.build_payment_block(rpc, PAYEE, PRICE // 2)
        return R(), {"settled": True, "amount_xno": M.raw_to_xno(PRICE // 2),
                     "pay_to": PAYEE, "block": "AB" * 32, "ledger": "confirmed"}

    monkeypatch.setattr(T, "request_with_payment", cheaper)
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    Wallet(pathlib.Path(wallet_path)).create()
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE // 2)]


def test_the_pin_does_not_touch_dry_run_previewing(monkeypatch):
    """Previewing spends nothing, so a preview is never refused for its address."""
    seller, tool = _env(monkeypatch, switch_to=OTHER)

    def call(**args):
        raw = json.dumps(dict({"url": "http://seller.invalid/report"}, **args))
        ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
        return asyncio.run(tool.on_invoke_tool(ctx, raw))

    preview = call(dry_run=True)
    assert preview.startswith("QUOTE") and PAYEE in preview, preview
    assert seller.signed == []


def test_the_mandate_ledger_does_record_a_payment_that_does_happen(monkeypatch):
    """Makes the ledger assertion above non-vacuous: the same mandate, the same
    keys, an unswitched payee - `spent_raw` and `payments` both move."""
    seller = SwitchingSeller(None)
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt)))
                        or ("blk", "front", "root"))
    td = tempfile.mkdtemp()
    wallet_path = os.path.join(td, "wallet.json")
    agent = Wallet(pathlib.Path(wallet_path))
    agent.create()
    mandate = M.build_mandate(agent.address, OPERATOR, PRICE * 3, PRICE,
                              "Buy one report per day from the seller",
                              "2030-01-01T00:00:00Z", allowed_payees=[PAYEE, OTHER])
    mandate_path = os.path.join(td, "mandate.json")
    ledger_path = os.path.join(td, "mandate.ledger.json")
    with open(mandate_path, "w") as fh:
        json.dump(M.sign_mandate(mandate, OPERATOR_KEY), fh)
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno=CAP,
                                 mandate_path=mandate_path, mandate_ledger=ledger_path)
    _, out = _buy(tool)
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE)]
    assert _ledger_spent(ledger_path) == (PRICE, 1), _ledger_spent(ledger_path)
