"""nano_x402_fetch under an operator mandate. Offline: no HTTP, no node, no money.

feeless402's request_with_payment is replaced by a fake that behaves like it
where it matters: a dry run returns the quote; a redeem RE-READS the offer
(which the test may change) and asks the wallet to build a block for that
offer's payee and amount. The wallet's block builder is replaced too, so the
test can count every block that would have been signed.
"""
import asyncio
import json
import os
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.tool_context import ToolContext
from nano_pay.wallet import Wallet

import openai_agents_nano.tool as T
from openai_agents_nano import mandate as M

OPERATOR_SEED = "11" * 32  # test-fixture
OPERATOR_KEY = M.private_key_from_seed(bytes.fromhex(OPERATOR_SEED), 0)
OPERATOR = M.address_from_public_key(M.public_key_from_private(OPERATOR_KEY))
PAYEE = "nano_1p7cqqnfo91zwcnse54f3ucyfi6xwzsbnkt3ay14cd1g6epmiygnt7jtcoa5"
STRANGER = "nano_3166w1xhtgg1b46izokwhxq9aist9wagha6eouuce7fy5fyrbb1xjgzwwm3c"
XNO = 10 ** 30
PRICE = XNO // 1000  # 0.001 XNO


class FakeSeller:
    def __init__(self):
        self.pay_to, self.amount = PAYEE, PRICE
        self.signed = []

    def quote(self):
        return {"amount_raw": self.amount, "amount_xno": M.raw_to_xno(self.amount), "pay_to": self.pay_to}

    def request_with_payment(self, method, url, wallet, rpc, max_raw, headers=None, dry_run=False, **kw):
        class R:
            status_code, text = (402, "") if dry_run else (200, "the resource")
        if dry_run:
            return R(), self.quote()
        offer = self.quote()  # re-read, as feeless402 does
        if offer["amount_raw"] > max_raw:
            raise RuntimeError("PriceCapExceeded")
        wallet.build_payment_block(rpc, offer["pay_to"], offer["amount_raw"])
        return R(), {"settled": True, "amount_xno": offer["amount_xno"], "pay_to": offer["pay_to"],
                     "block": "AB" * 32, "ledger": "confirmed"}


@pytest.fixture
def env(monkeypatch):
    seller = FakeSeller()
    monkeypatch.setattr(T, "request_with_payment", seller.request_with_payment)
    monkeypatch.setattr(Wallet, "build_payment_block",
                        lambda self, rpc, to, amt: seller.signed.append((to, int(amt))) or ("blk", "front", "root"))
    with tempfile.TemporaryDirectory() as td:
        wallet_path = os.path.join(td, "wallet.json")
        w = Wallet(__import__("pathlib").Path(wallet_path))
        w.create()
        yield seller, td, wallet_path, w.address


def write_mandate(td, agent, total=PRICE * 3, per=PRICE, payees=(PAYEE,), expires="2030-01-01T00:00:00Z",
                  issued=None):
    mandate = M.build_mandate(agent, OPERATOR, total, per, "Buy one report per day from the seller",
                              expires, allowed_payees=list(payees) or None, issued_at=issued)
    path = os.path.join(td, "mandate.json")
    with open(path, "w") as fh:
        json.dump(M.sign_mandate(mandate, OPERATOR_KEY), fh)
    return path


def call(tool, **args):
    raw = json.dumps(dict({"url": "http://seller.invalid/report"}, **args))
    ctx = ToolContext(context={}, tool_name=tool.name, tool_arguments=raw, tool_call_id="c1")
    return asyncio.run(tool.on_invoke_tool(ctx, raw))


def buy(tool):
    preview = call(tool, dry_run=True)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    return preview, call(tool, dry_run=False, quote_token=token)


def make(wallet_path, mandate_path):
    return T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno="0.01",
                                 mandate_path=mandate_path)


def test_within_the_mandate_pays_and_is_recorded(env):
    seller, td, wallet_path, agent = env
    path = write_mandate(td, agent)
    preview, out = buy(make(wallet_path, path))
    assert "mandate: allows this payment" in preview
    assert out.startswith("PAID"), out
    assert seller.signed == [(PAYEE, PRICE)]
    assert M.MandateGuard.from_file(path, agent=agent).status()["spent_raw"] == str(PRICE)


def test_cap_exhaustion_refuses_before_signing(env):
    seller, td, wallet_path, agent = env
    tool = make(wallet_path, write_mandate(td, agent))
    for _ in range(3):
        assert buy(tool)[1].startswith("PAID")
    preview, out = buy(tool)
    assert "would REFUSE" in preview and "cap_exhausted" in preview
    assert out.startswith("REFUSED: your operator's mandate") and "cap_exhausted" in out
    assert len(seller.signed) == 3


def test_payee_switched_after_the_preview_is_refused_at_signing(env):
    """The seller re-quotes a different payee between the token check and the
    block: the mandate sees the payee actually being signed and refuses."""
    seller, td, wallet_path, agent = env
    tool = make(wallet_path, write_mandate(td, agent))
    preview = call(tool, dry_run=True)
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    original = seller.request_with_payment

    def switch_then_pay(*a, **kw):
        if not kw.get("dry_run"):
            seller.pay_to = STRANGER
        return original(*a, **kw)

    T.request_with_payment = switch_then_pay
    out = call(tool, dry_run=False, quote_token=token)
    assert out.startswith("REFUSED: your operator's mandate") and "payee_not_allowed" in out, out
    assert seller.signed == []


def test_per_payment_max(env):
    seller, td, wallet_path, agent = env
    seller.amount = PRICE + 1
    _, out = buy(make(wallet_path, write_mandate(td, agent)))
    assert "over_per_payment_max" in out and seller.signed == []


def test_expired_mandate(env):
    seller, td, wallet_path, agent = env
    path = write_mandate(td, agent, issued="2026-01-01T00:00:00Z", expires="2026-01-02T00:00:00Z")
    _, out = buy(make(wallet_path, path))
    assert "expired" in out and seller.signed == []


def test_mandate_for_another_agent(env):
    seller, td, wallet_path, agent = env
    _, out = buy(make(wallet_path, write_mandate(td, STRANGER)))
    assert "wrong_agent" in out and seller.signed == []


def test_tampered_mandate(env):
    seller, td, wallet_path, agent = env
    path = write_mandate(td, agent)
    doc = json.load(open(path))
    doc["mandate"]["total_cap_raw"] = str(100 * XNO)
    doc["hash"] = M.mandate_hash(doc["mandate"])
    json.dump(doc, open(path, "w"))
    _, out = buy(make(wallet_path, path))
    assert "bad_signature" in out and seller.signed == []


def test_missing_mandate_file_refuses_rather_than_paying_uncapped(env):
    seller, td, wallet_path, agent = env
    _, out = buy(make(wallet_path, os.path.join(td, "nope.json")))
    assert "unreadable_mandate" in out and seller.signed == []


def test_env_var_is_read_at_construction(env, monkeypatch):
    seller, td, wallet_path, agent = env
    monkeypatch.setenv("X402_MANDATE_PATH", write_mandate(td, agent, payees=(STRANGER,)))
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno="0.01")
    _, out = buy(tool)
    assert "payee_not_allowed" in out and seller.signed == []


def test_without_a_mandate_nothing_changes(env):
    seller, td, wallet_path, agent = env
    _, out = buy(make(wallet_path, None))
    assert out.startswith("PAID") and seller.signed == [(PAYEE, PRICE)]


def test_x402_max_xno_exported_after_import_is_honoured(env, monkeypatch):
    seller, td, wallet_path, agent = env
    monkeypatch.setenv("X402_MAX_XNO", "0.0005")  # below PRICE; the module is already imported
    tool = T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object())
    preview, out = buy(tool)
    assert "cap:    0.0005 XNO" in preview
    assert out.startswith("REFUSED: the endpoint's price is above your cap"), out
    assert seller.signed == []


# --- a mandate the guard cannot read must refuse in text, never raise ---------
# mandate.py's contract: "Any doubt - an unreadable ledger, a ledger for another
# mandate ... is a refusal with a machine-readable reason", and tool.py's: "The
# return value is always agent-readable text." The ledger is opened through
# `_Locked`, which is plain `open()`: a ledger path whose directory does not
# exist, or one on a read-only mount, raises OSError, not MandateRefused.


def make_with_ledger(wallet_path, mandate_path, ledger):
    return T.make_nano_x402_tool(wallet_path=wallet_path, rpc=object(), default_max_xno="0.01",
                                 mandate_path=mandate_path, mandate_ledger=ledger)


def test_an_unusable_ledger_path_refuses_in_text_and_signs_nothing(env):
    seller, td, wallet_path, agent = env
    path = write_mandate(td, agent)
    tool = make_with_ledger(wallet_path, path, os.path.join(td, "no-such-dir", "ledger.json"))

    preview = call(tool, dry_run=True)
    assert preview.startswith("QUOTE"), preview
    assert "mandate: could not be checked" in preview, preview
    assert "allows this payment" not in preview

    token = re.search(r"quote_token: (\S+)", preview).group(1)
    out = call(tool, dry_run=False, quote_token=token)
    assert out.startswith("REFUSED"), out
    assert "mandate_unavailable" in out
    assert seller.signed == [], "a payment was signed while the mandate could not be checked"


def test_a_ledger_path_under_a_regular_file_refuses_in_text(env):
    """A different OSError than the missing directory above (NotADirectoryError),
    and one no amount of privilege turns into a writable path."""
    seller, td, wallet_path, agent = env
    path = write_mandate(td, agent)
    not_a_dir = os.path.join(td, "a-file")
    with open(not_a_dir, "w") as fh:
        fh.write("x")
    tool = make_with_ledger(wallet_path, path, os.path.join(not_a_dir, "ledger.json"))

    preview = call(tool, dry_run=True)
    assert preview.startswith("QUOTE") and "could not be checked" in preview, preview
    token = re.search(r"quote_token: (\S+)", preview).group(1)
    out = call(tool, dry_run=False, quote_token=token)
    assert out.startswith("REFUSED") and "mandate_unavailable" in out, out
    assert seller.signed == []


def test_a_mandate_file_that_is_not_json_still_refuses_in_text(env):
    """load_signed already turns this into MandateRefused; pinned so the
    fail-closed path stays covered for the readable-but-invalid case too."""
    seller, td, wallet_path, agent = env
    path = os.path.join(td, "broken.json")
    with open(path, "w") as fh:
        fh.write("{not json")
    tool = make_with_ledger(wallet_path, path, os.path.join(td, "ledger.json"))
    out = call(tool, dry_run=False, quote_token="anything")
    assert out.startswith("REFUSED"), out
    assert seller.signed == []
