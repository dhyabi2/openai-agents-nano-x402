"""Laws for the client-side ``exact`` scheme on ``nano:mainnet`` (x402_sdk.py).

Offline and deterministic: no network, no broadcast, no real funds. The wallet
is built from a fixed throwaway seed and the RPC is a stub that reports a funded
account and serves a *genuinely valid* proof of work for the fixed frontier
(precomputed once, so the suite does not spend 35 s per block generating it).

Two of these laws exist because a pass-through payer that looks right cannot buy
anything, and they are the reason this module is not three lines:

* ``link_as_account`` is absent from feeless402's block dict, and the Nano
  facilitator compares ``requirements.payTo`` against that field and nothing
  else -- so without it every payment is refused ``error_payto_link_mismatch``.
* ``amount`` on the wire is an integer string in raw. Reading ``"0.01"`` as XNO
  instead of refusing it pays 10**28 times the quoted price.

The block's field set and the regexes below mirror ``NANO_SEND_BLOCK`` in
``@x402nano/typescript-common`` 0.1.0, which is the schema the facilitator
validates a payload against; measured against that package, not guessed.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nano_pay.wallet import NET, Wallet

from openai_agents_nano.x402_sdk import (
    ASSET_XNO,
    DEFAULT_MAX_XNO,
    NETWORK_NANO_MAINNET,
    ExactNanoClientScheme,
    NanoX402Refused,
    nano_spend_controls,
    normalize_payee,
    parse_raw_amount,
)

RAW_PER_XNO = 10**30

# A throwaway test seed. It holds nothing and is never funded; the balance below
# is reported by the stub RPC, not by any ledger.
TEST_SEED = "11" * 32

# The stub's frontier, and a work value that is genuinely valid for it at the
# mainnet send threshold (fffffff800000000). Serving it keeps the suite fast:
# generating work locally for this root took 35.2 s on the machine that recorded
# it, which is the cost this module's docstring warns a caller about.
FRONTIER = "A" * 64
FRONTIER_WORK = "8861e54f16b2e62a"

REPRESENTATIVE = "nano_1center16ci77qw5w69ww8sy4i4bfmgfhr81ydzpurm91cauj11jn6y3uc5y"
PAYEE = "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3"
PAYEE_PK = "e89208dd038fbb269987689621d52292ae9c35941a7484756ecced92a65093ba"

START_BALANCE = 5 * RAW_PER_XNO  # 5 XNO, as the stub reports it
ONE_HUNDREDTH = RAW_PER_XNO // 100  # 0.01 XNO in raw

# NANO_SEND_BLOCK, as @x402nano/typescript-common 0.1.0 declares it.
HEX_64 = re.compile(r"[0-9A-Fa-f]{64}")
NANO_ACCOUNT = re.compile(r"(?:nano_|xrb_)[13][13456789abcdefghijkmnopqrstuwxyz]{59}")
STRING_INT = re.compile(r"[0-9]+")
BLOCK_FIELDS = {
    "type": re.compile(r"state"),
    "account": NANO_ACCOUNT,
    "previous": HEX_64,
    "representative": NANO_ACCOUNT,
    "balance": STRING_INT,
    "link": HEX_64,
    "link_as_account": NANO_ACCOUNT,
    "work": re.compile(r"[0-9A-Fa-f]+"),
    "signature": re.compile(r"[0-9A-Fa-f]{128}"),
}


class StubRPC:
    """Offline RPC. Reports one opened, funded account and serves known-good work."""

    def __init__(self, balance=START_BALANCE, frontier=FRONTIER, work=FRONTIER_WORK,
                 frontier_after=None):
        self.balance = balance
        self.frontier = frontier
        self.work = work
        self._frontier_after = frontier_after
        self.account_info_calls = 0
        self.processed = []  # stays empty: nothing here may broadcast

    def account_info(self, addr):
        self.account_info_calls += 1
        frontier = self.frontier
        if self._frontier_after is not None and self.account_info_calls > 1:
            frontier = self._frontier_after
        return {
            "frontier": frontier,
            "balance": str(self.balance),
            "representative": REPRESENTATIVE,
        }

    def work_generate(self, root, difficulty):
        return self.work

    def process(self, *a, **k):  # pragma: no cover - a failure if ever reached
        raise AssertionError("the client must never broadcast; the facilitator settles")


class Requirements:
    """The fields of x402 ``PaymentRequirements`` this scheme reads."""

    def __init__(self, pay_to=PAYEE, amount=str(ONE_HUNDREDTH), scheme="exact",
                 network=NETWORK_NANO_MAINNET, asset=ASSET_XNO):
        self.pay_to = pay_to
        self.amount = amount
        self.scheme = scheme
        self.network = network
        self.asset = asset


def _wallet(tmpdir):
    return Wallet(Path(tmpdir) / "wallet.json").create(seed=TEST_SEED)


def _scheme(tmpdir, rpc=None, **kw):
    return ExactNanoClientScheme(_wallet(tmpdir), rpc or StubRPC(), **kw)


# ----------------------------------------------------------------- happy path

def test_payload_is_the_exact_nano_payload_shape():
    """EXACT_NANO_PAYLOAD is ``{block: NANO_SEND_BLOCK}`` -- nothing more."""
    with tempfile.TemporaryDirectory() as td:
        payload = _scheme(td).create_payment_payload(Requirements())
        assert set(payload) == {"block"}
        block = payload["block"]
        assert set(block) == set(BLOCK_FIELDS), sorted(block)
        for field, pattern in BLOCK_FIELDS.items():
            assert pattern.fullmatch(str(block[field])), (field, block[field])


def test_link_as_account_is_present_and_is_the_quoted_payee():
    """Without this field the facilitator refuses every block as payTo-mismatch."""
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements())["block"]
        assert "link_as_account" in block
        assert block["link_as_account"] == PAYEE


def test_link_decodes_to_the_quoted_payee():
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements())["block"]
        assert block["link"].lower() == PAYEE_PK
        assert NET.from_pk(block["link"]) == PAYEE


def test_block_sends_exactly_the_quoted_amount():
    """The facilitator's own test: balance_before - block.balance == amount."""
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements())["block"]
        assert START_BALANCE - int(block["balance"]) == ONE_HUNDREDTH


def test_the_payer_builds_on_the_observed_frontier():
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements())["block"]
        assert block["previous"].upper() == FRONTIER


def test_nothing_is_broadcast():
    """x402 hands the block over; the facilitator calls process. The stub asserts it."""
    with tempfile.TemporaryDirectory() as td:
        rpc = StubRPC()
        _scheme(td, rpc).create_payment_payload(Requirements())
        assert rpc.processed == []


def test_an_xrb_payee_is_normalized_rather_than_crashing_the_signer():
    """The block schema allows xrb_; nanopy rejects it with ValueError."""
    xrb = "xrb_" + PAYEE[len("nano_"):]
    with pytest.raises(ValueError):
        NET.to_pk(xrb)  # the failure this normalization exists to prevent
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements(pay_to=xrb))["block"]
        assert block["link_as_account"] == PAYEE
        assert block["link"].lower() == PAYEE_PK


def test_amounts_are_exact_at_the_top_of_the_supply():
    """Integer raw only: a float would lose digits well below this size."""
    big = 133_248_298 * RAW_PER_XNO  # the whole Nano supply, in raw
    assert parse_raw_amount(str(big)) == big
    assert len(str(big)) == 39
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td, StubRPC(balance=big), max_xno=str(133_248_298))
        block = scheme.create_payment_payload(Requirements(amount=str(big)))["block"]
        assert block["balance"] == "0"
        assert big - int(block["balance"]) == big


# -------------------------------------------------------------------- amounts

def test_a_decimal_amount_is_refused_not_rescaled():
    """'0.01' on the wire is 0.01 raw. Reading it as XNO overpays 10**28-fold."""
    with pytest.raises(NanoX402Refused) as exc:
        parse_raw_amount("0.01")
    assert "integer string in raw" in str(exc.value)
    assert str(ONE_HUNDREDTH) in str(exc.value)  # names what the seller likely meant


@pytest.mark.parametrize("amount", ["0", "-1", "", None, "abc", "1e30", " ", "01"])
def test_malformed_amounts_are_refused(amount):
    with pytest.raises(NanoX402Refused):
        parse_raw_amount(amount)


def test_a_quote_over_the_cap_is_refused_before_signing():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td, max_xno="0.001")
        with pytest.raises(NanoX402Refused) as exc:
            scheme.create_payment_payload(Requirements(amount=str(ONE_HUNDREDTH)))
        assert "cap" in str(exc.value)


def test_the_cap_is_inclusive_at_its_own_value():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td, max_xno="0.01")
        assert scheme.max_amount_raw == ONE_HUNDREDTH
        block = scheme.create_payment_payload(Requirements(amount=str(ONE_HUNDREDTH)))["block"]
        assert START_BALANCE - int(block["balance"]) == ONE_HUNDREDTH


@pytest.mark.parametrize("cap", ["nan", "Infinity", "-Infinity", "0", "-1", "abc", None])
def test_a_non_finite_or_non_positive_cap_is_refused_at_construction(cap):
    """A NaN cap compares false against everything, so it is no cap at all."""
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused):
            _scheme(td, max_xno=cap)


def test_a_cap_finer_than_one_raw_is_refused():
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused):
            _scheme(td, max_xno="0." + "0" * 30 + "1")


def test_insufficient_balance_is_refused_with_both_numbers():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td, StubRPC(balance=ONE_HUNDREDTH - 1))
        with pytest.raises(NanoX402Refused) as exc:
            scheme.create_payment_payload(Requirements(amount=str(ONE_HUNDREDTH)))
        assert "insufficient balance" in str(exc.value)


# --------------------------------------------------------------------- payees

@pytest.mark.parametrize("bad", [
    "nano_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr4",  # checksum
    "nano_bogus", "", None, "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
])
def test_a_malformed_or_tampered_payee_is_refused(bad):
    with pytest.raises(NanoX402Refused):
        normalize_payee(bad)


def test_paying_our_own_address_is_refused():
    with tempfile.TemporaryDirectory() as td:
        wallet = _wallet(td)
        scheme = ExactNanoClientScheme(wallet, StubRPC())
        with pytest.raises(NanoX402Refused) as exc:
            scheme.create_payment_payload(Requirements(pay_to=wallet.address))
        assert "own address" in str(exc.value)


# ------------------------------------------------------- quote-shape refusals

def test_a_non_exact_scheme_is_refused():
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused):
            _scheme(td).create_payment_payload(Requirements(scheme="permit"))


def test_a_quote_for_another_network_is_refused():
    """Registered for nano:mainnet, quoted eip155:8453 -- never pay it in XNO."""
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused) as exc:
            _scheme(td).create_payment_payload(Requirements(network="eip155:8453"))
        assert "eip155:8453" in str(exc.value)


@pytest.mark.parametrize("asset", ["USDC", "", None, "xno "])
def test_a_non_xno_asset_is_refused(asset):
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused):
            _scheme(td).create_payment_payload(Requirements(asset=asset))


def test_a_lowercase_xno_asset_is_accepted():
    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements(asset="xno"))["block"]
        assert block["link_as_account"] == PAYEE


def test_registering_for_a_non_nano_network_is_refused_at_construction():
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(NanoX402Refused):
            _scheme(td, network="eip155:8453")


def test_the_default_cap_matches_the_tool_factory():
    """One ceiling for the package: a reader should not find two defaults."""
    from openai_agents_nano import tool as tool_mod

    assert DEFAULT_MAX_XNO == "0.01"
    assert tool_mod.DEFAULT_MAX_XNO == DEFAULT_MAX_XNO or os.environ.get("X402_MAX_XNO")


# ------------------------------------------------------------- race refusal

def test_a_frontier_that_moves_mid_signing_is_refused_not_paid():
    """The balance checked and the balance spent must be the same balance.

    If a receive lands between the two, the signed block's delta is measured
    against a balance that is no longer current, so it is thrown away. The
    refusal is the safe direction: nothing was broadcast.
    """
    moved = "B" * 64
    with tempfile.TemporaryDirectory() as td:
        rpc = StubRPC(frontier_after=moved)
        with pytest.raises(NanoX402Refused) as exc:
            _scheme(td, rpc).create_payment_payload(Requirements())
        assert "moved while this payment was being signed" in str(exc.value)
        assert rpc.processed == []


# ----------------------- the block the facilitator receives actually verifies

def test_the_handed_over_block_passes_the_checks_the_facilitator_runs():
    """The facilitator verifies the signature against the payer's public key and
    the work against the send threshold, then broadcasts. A block that fails
    either is a payment that silently never happens, so prove both here --
    against the real crypto, not against the field regexes.
    """
    import nanopy

    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td)
        block = scheme.create_payment_payload(Requirements())["block"]

        rebuilt = nanopy.StateBlock(
            acc=nanopy.Account(addr=block["account"]),
            rep=nanopy.Account(addr=block["representative"]),
            bal=int(block["balance"]),
            prev=block["previous"],
            link=block["link"],
            sig=block["signature"],
            work=block["work"],
        )
        assert rebuilt.verify_signature(), "the facilitator would reject this as invalid_block"
        assert rebuilt.work_validate(NET.send_difficulty), (
            "the facilitator would reject this as invalid_work"
        )
        # The send threshold the facilitator uses is the one feeless402 signs for.
        assert NET.send_difficulty == "fffffff800000000"


def test_adding_link_as_account_does_not_change_the_signed_block():
    """link_as_account is a convenience field outside the signed hash. Adding it
    must not disturb the fields the signature covers."""
    import nanopy

    with tempfile.TemporaryDirectory() as td:
        block = _scheme(td).create_payment_payload(Requirements())["block"]
        signed = {k: v for k, v in block.items() if k != "link_as_account"}
        rebuilt = nanopy.StateBlock(
            acc=nanopy.Account(addr=signed["account"]),
            rep=nanopy.Account(addr=signed["representative"]),
            bal=int(signed["balance"]),
            prev=signed["previous"],
            link=signed["link"],
            sig=signed["signature"],
            work=signed["work"],
        )
        assert rebuilt.verify_signature()
        assert set(signed) == set(BLOCK_FIELDS) - {"link_as_account"}


# --------------------------- the signed block is checked before it is handed over

class _TamperingWallet:
    """A wallet whose signer returns a block that does not match the quote.

    The post-signature checks exist for the case where the thing that builds the
    block and the thing that quoted the price disagree. Without a wallet that
    actually misbehaves those checks are unreachable code, so this supplies one.
    """

    def __init__(self, real, **overrides):
        self._real = real
        self._overrides = overrides

    def __getattr__(self, name):
        return getattr(self._real, name)

    def build_payment_block(self, rpc, to_addr, raw_amt):
        block, new_frontier, work_root = self._real.build_payment_block(rpc, to_addr, raw_amt)
        block = dict(block)
        block.update(self._overrides)
        return block, new_frontier, work_root


def _tampered(td, **overrides):
    rpc = StubRPC()
    wallet = _TamperingWallet(_wallet(td), **overrides)
    return ExactNanoClientScheme(wallet, rpc), rpc


def test_a_block_that_sends_more_than_the_quote_is_refused():
    """Never overpay: the refusal is the point, and nothing was broadcast."""
    with tempfile.TemporaryDirectory() as td:
        over = str(START_BALANCE - (ONE_HUNDREDTH * 2))  # leaves less behind => sends more
        scheme, rpc = _tampered(td, balance=over)
        with pytest.raises(NanoX402Refused) as exc:
            scheme.create_payment_payload(Requirements())
        assert "refusing" in str(exc.value)
        assert str(ONE_HUNDREDTH) in str(exc.value)
        assert rpc.processed == []


def test_a_block_that_sends_less_than_the_quote_is_refused():
    """Underpaying is refused too: the facilitator would reject it as amount-mismatch."""
    with tempfile.TemporaryDirectory() as td:
        scheme, _ = _tampered(td, balance=str(START_BALANCE - (ONE_HUNDREDTH // 2)))
        with pytest.raises(NanoX402Refused):
            scheme.create_payment_payload(Requirements())


def test_a_block_that_pays_a_different_account_is_refused():
    """The link must decode to the payee that was quoted, not merely be well formed."""
    other = NET.to_pk("nano_1center16ci77qw5w69ww8sy4i4bfmgfhr81ydzpurm91cauj11jn6y3uc5y")
    with tempfile.TemporaryDirectory() as td:
        scheme, rpc = _tampered(td, link=other)
        with pytest.raises(NanoX402Refused) as exc:
            scheme.create_payment_payload(Requirements())
        assert "wrong account" in str(exc.value)
        assert rpc.processed == []


@pytest.mark.parametrize("overrides", [
    {"type": "send"},
    {"signature": "deadbeef"},
    {"work": "zzzz"},
    {"balance": "-1"},
    {"balance": "1.5"},
    {"link": "nope"},
    {"previous": "short"},
])
def test_a_malformed_signed_block_is_refused(overrides):
    with tempfile.TemporaryDirectory() as td:
        scheme, _ = _tampered(td, **overrides)
        with pytest.raises(NanoX402Refused):
            scheme.create_payment_payload(Requirements())


def test_a_refused_block_is_not_bookable_as_settled():
    """A block that never left must not drop the wallet's cached work."""
    with tempfile.TemporaryDirectory() as td:
        scheme, _ = _tampered(td, link="nope")
        with pytest.raises(NanoX402Refused):
            scheme.create_payment_payload(Requirements())
        booked = []
        scheme._wallet._real.payment_succeeded = lambda *a, **k: booked.append(a)
        scheme.settled()
        assert booked == []


# --------------------------------------------------- settlement bookkeeping

def test_settled_books_the_payment_once_and_only_once():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td)
        scheme.create_payment_payload(Requirements())
        booked = []
        scheme._wallet.payment_succeeded = lambda *a, **k: booked.append((a, k))
        scheme.settled()
        scheme.settled()  # nothing pending now
        assert len(booked) == 1
        assert booked[0][1] == {"prework": False}


def test_not_settled_tells_the_wallet_its_cached_work_still_stands():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td)
        scheme.create_payment_payload(Requirements())
        seen = []
        scheme._wallet.payment_failed = lambda root: seen.append(root)
        scheme.not_settled()
        scheme.not_settled()
        assert seen == [FRONTIER]


def test_a_refused_quote_leaves_nothing_pending():
    with tempfile.TemporaryDirectory() as td:
        scheme = _scheme(td, max_xno="0.001")
        with pytest.raises(NanoX402Refused):
            scheme.create_payment_payload(Requirements(amount=str(ONE_HUNDREDTH)))
        booked = []
        scheme._wallet.payment_succeeded = lambda *a, **k: booked.append(a)
        scheme.settled()
        assert booked == []


# ------------------------------------------- the official SDK actually takes it

def _payment_required(amount=str(ONE_HUNDREDTH), network=NETWORK_NANO_MAINNET):
    from x402.schemas import PaymentRequired, PaymentRequirements

    return PaymentRequired(
        x402Version=2,
        accepts=[
            PaymentRequirements(
                scheme="exact",
                network=network,
                asset=ASSET_XNO,
                amount=amount,
                payTo=PAYEE,
                maxTimeoutSeconds=60,
            )
        ],
    )


def test_the_official_x402_client_produces_a_nano_payment_payload():
    """End to end through the real SDK: register, hand it a 402, get a payload.

    This is the whole point of the module -- an agent that already speaks x402
    pays a nano:mainnet quote -- so it is checked against the published SDK
    rather than against a local idea of its interface.
    """
    x402 = pytest.importorskip("x402", reason="the official x402 SDK is not installed")

    with tempfile.TemporaryDirectory() as td:
        client = x402.x402ClientSync()
        client.register(NETWORK_NANO_MAINNET, _scheme(td))
        client.set_spend_controls(nano_spend_controls(max_xno="0.01"))

        payload = client.create_payment_payload(_payment_required())

        assert payload.x402_version == 2
        assert payload.accepted.network == NETWORK_NANO_MAINNET
        assert payload.accepted.scheme == "exact"
        block = payload.payload["block"]
        assert set(block) == set(BLOCK_FIELDS), sorted(block)
        assert block["link_as_account"] == PAYEE
        assert START_BALANCE - int(block["balance"]) == ONE_HUNDREDTH


def test_the_sdk_default_spend_controls_reject_xno_until_opted_in():
    """Registering the scheme is necessary but not sufficient, and the error says
    nothing about Nano -- which is why nano_spend_controls exists."""
    x402 = pytest.importorskip("x402", reason="the official x402 SDK is not installed")
    from x402.schemas.errors import NoMatchingRequirementsError

    with tempfile.TemporaryDirectory() as td:
        client = x402.x402ClientSync()
        client.register(NETWORK_NANO_MAINNET, _scheme(td))
        with pytest.raises(NoMatchingRequirementsError) as exc:
            client.create_payment_payload(_payment_required())
        assert "spend_controls" in str(exc.value)
        assert "nano" not in str(exc.value).lower()  # the trap: it never names Nano


def test_the_nano_cap_stays_in_raw_and_is_never_a_dollar_figure():
    """The SDK resolves a USD cap against an asset's decimals. At 30 decimals
    "$1" is 10**30 raw -- exactly 1 XNO -- so a dollar limit would silently
    become an XNO limit. The opt-in this module writes is atomic, so it cannot."""
    pytest.importorskip("x402", reason="the official x402 SDK is not installed")

    entry = nano_spend_controls(max_xno="0.01")["allowed_assets"][0]
    assert entry == {
        "network": NETWORK_NANO_MAINNET,
        "asset": ASSET_XNO,
        "max_amount_per_payment": str(ONE_HUNDREDTH),
    }
    assert re.fullmatch(r"[0-9]+", entry["max_amount_per_payment"])
    assert "$" not in entry["max_amount_per_payment"]


def test_the_sdk_enforces_the_raw_cap_this_module_writes():
    """The opt-in is a real ceiling, not decoration: a quote above it is rejected
    by the SDK before the scheme is ever asked to sign."""
    x402 = pytest.importorskip("x402", reason="the official x402 SDK is not installed")
    from x402.schemas.errors import NoMatchingRequirementsError

    with tempfile.TemporaryDirectory() as td:
        client = x402.x402ClientSync()
        client.register(NETWORK_NANO_MAINNET, _scheme(td, max_xno="1"))
        client.set_spend_controls(nano_spend_controls(max_xno="0.01"))
        with pytest.raises(NoMatchingRequirementsError):
            client.create_payment_payload(_payment_required(amount=str(ONE_HUNDREDTH + 1)))


def test_the_scheme_reports_no_default_asset():
    """Deliberate: find_default_asset would make the SDK read "$1" as 1 XNO."""
    with tempfile.TemporaryDirectory() as td:
        assert not hasattr(_scheme(td), "find_default_asset")


@pytest.mark.parametrize("cap", ["nan", "0", "-1", "abc"])
def test_nano_spend_controls_refuses_a_bad_cap(cap):
    with pytest.raises(NanoX402Refused):
        nano_spend_controls(max_xno=cap)
