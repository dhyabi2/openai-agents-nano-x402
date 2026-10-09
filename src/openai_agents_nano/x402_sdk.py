"""Client side of the x402 v2 ``exact`` scheme on ``nano:mainnet``, for the
official x402 Python SDK.

The official SDK ships client mechanisms for EVM and SVM only, so an agent that
already speaks x402 cannot pay a ``nano:mainnet`` quote: ``x402Client`` raises
``SchemeNotFoundError`` because nothing is registered for that network. The
resource-server half of the pair is published (``x402-nano-exact`` on PyPI,
which ``x402ResourceServer.register("nano:mainnet", ...)`` takes), and the
facilitator settles; the client half was the missing piece. This is it::

    from x402 import x402Client
    from openai_agents_nano.x402_sdk import ExactNanoClientScheme

    client = x402Client()
    client.register("nano:mainnet", ExactNanoClientScheme(wallet, rpc, max_xno="0.01"))
    payload = await client.create_payment_payload(payment_required)

Like the rest of this package it rebuilds no Nano payment logic: the keys, the
work and the signature all come from feeless402's ``Wallet``, whose
``build_payment_block`` signs a send block *without* broadcasting it -- which is
exactly the x402 shape, since the facilitator is what calls ``process``.

What this module adds on top of that block is the part a pass-through gets
wrong, and three of them are refusals rather than conveniences:

* **``link_as_account``.** feeless402's block dict carries ``link`` (the payee's
  public key) but not ``link_as_account``. The Nano facilitator's verify compares
  ``requirements.payTo`` against ``block.link_as_account`` and nothing else, so a
  block handed over without that field is refused as ``error_payto_link_mismatch``
  every single time -- a payer that looks correct and can never buy anything.
  Measured against ``@x402nano/exact`` 0.3.0 and ``@x402nano/typescript-common``
  0.1.0, whose ``NANO_SEND_BLOCK`` is the schema the facilitator validates.
* **``xrb_`` payees.** That same schema accepts ``xrb_`` as well as ``nano_``, and
  the facilitator rewrites the prefix before comparing; ``nanopy`` rejects
  ``xrb_`` outright with ``ValueError: Invalid address``. A quote in the older
  prefix is normalized here instead of failing deep inside the signer.
* **A decimal ``amount`` is refused, not rounded.** On ``nano:mainnet`` the wire
  ``amount`` is an integer string in raw (1 XNO = 10**30 raw). A seller that
  quotes ``"0.01"`` has quoted 0.01 raw, not 0.01 XNO, and a payer that "helpfully"
  reinterprets it pays 10**28 times the price. Raw is read as raw and a decimal is
  refused with the number the seller probably meant.
* **The signed block is checked before it is handed over.** The payee public key
  in ``link`` must decode to exactly the ``payTo`` that was quoted, and the
  balance the block leaves behind must be exactly the observed balance minus the
  quoted amount -- never less. Both are integer comparisons on raw. A block that
  fails either is refused and never returned, so the failure mode is a payment
  that does not happen rather than one that goes to the wrong place or carries
  the wrong amount.

All arithmetic is integer raw. No float ever touches an amount.

**Work, and why this is deliberately synchronous.** The SDK calls
``create_payment_payload`` synchronously, from inside the async client too, so
the proof-of-work for the send block is generated on the calling thread. A local
``work_generate`` is 6-35 s of CPU (35.2 s measured here), which would stall an
event loop for that long. Give the ``rpc`` a working ``work_generate`` endpoint,
or pre-warm the wallet's work cache with ``Wallet.prework``, and this returns in
milliseconds. Payments through one wallet are serialised on a lock, because Nano
blocks build on each other: two blocks signed against one frontier are a fork,
and only one of them can ever confirm.

**The SDK's own spend controls refuse XNO until you opt in.** Registering this
scheme is necessary but not sufficient: ``x402Client`` runs ``spend_controls``
*before* it dispatches, and by default it allows only assets a scheme reports
through ``find_default_asset``, capped at ``DEFAULT_MAX_AMOUNT_PER_PAYMENT``
(``"$1"``). A ``nano:mainnet`` quote is otherwise rejected with
``NoMatchingRequirementsError: All payment requirements were rejected by
spend_controls`` -- which does not mention Nano, so it reads like a missing
registration. Use :func:`nano_spend_controls`::

    client.set_spend_controls(nano_spend_controls(max_xno="0.01"))

This scheme deliberately does **not** implement ``find_default_asset``. That
would make XNO a default asset, and the SDK would then resolve its USD cap
against the asset's decimals -- ``"$1"`` at 30 decimals is 10**30 raw, i.e.
exactly 1 XNO. The SDK would be silently treating one dollar as one XNO, which
is a unit conflation and not a cap anyone chose. An atomic cap in raw, which is
what :func:`nano_spend_controls` writes, is the only unambiguous way to say it,
and the SDK honours an explicit atomic ``max_amount_per_payment`` without ever
consulting the dollar limit.

**Settlement bookkeeping.** This interface gives the scheme no settle callback --
the facilitator settles, and the client learns the outcome from the response. So
the caller tells the wallet how it went, with ``settled()`` or ``not_settled()``
after the paid request returns (``x402Client.on_payment_response`` is the hook
for it). Skipping that is not a correctness bug, only a stale cached work value.
"""
from __future__ import annotations

import re
import threading
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from nano_pay import raw_to_xno
from nano_pay.wallet import NET

SCHEME_EXACT = "exact"
NETWORK_NANO_MAINNET = "nano:mainnet"
ASSET_XNO = "XNO"

DEFAULT_MAX_XNO = "0.01"
"""Same default ceiling as ``make_nano_x402_tool``: a cap is never absent."""

_RAW_EXPONENT = 30
"""``RAW_PER_XNO == 10 ** _RAW_EXPONENT``; pinned by a test so the two cannot desync."""

_MAX_XNO_EXPONENT = 40
"""An XNO amount of ``10 ** _MAX_XNO_EXPONENT`` or more is refused before any
integer is built. The whole supply is about 1.33 * 10**8 XNO, so no real cap or
quote comes near; the bound exists so a seller-chosen exponent cannot make the
payer build a power of ten with millions of digits."""

_RAW_RE = re.compile(r"[1-9][0-9]*")
_HEX64_RE = re.compile(r"[0-9A-Fa-f]{64}")
_SIGNATURE_RE = re.compile(r"[0-9A-Fa-f]{128}")
_WORK_RE = re.compile(r"[0-9A-Fa-f]+")


class NanoX402Refused(Exception):
    """Raised instead of signing, or instead of handing over a signed block.

    Every message names what was quoted and what was expected, because this is
    the exception an agent operator reads when a purchase did not happen.
    """


def normalize_payee(address: Any) -> str:
    """Return ``address`` in canonical ``nano_`` form, checksum verified.

    Accepts the ``xrb_`` prefix, which the x402 Nano block schema allows and
    ``nanopy`` does not. Validation is feeless402's own network object, so no
    address cryptography is reimplemented here.

    Raises:
        NanoX402Refused: If the address is malformed or its checksum fails.
    """
    text = str(address or "").strip()
    if text.startswith("xrb_"):
        text = "nano_" + text[4:]
    try:
        return NET.from_pk(NET.to_pk(text))
    except Exception as exc:  # nanopy raises bare ValueError
        raise NanoX402Refused(f"payTo is not a valid Nano address: {address!r} ({exc})") from exc


def parse_raw_amount(amount: Any) -> int:
    """Read a wire ``amount`` as an integer number of raw.

    On ``nano:mainnet`` the x402 ``amount`` is always an integer string in raw.
    A decimal is refused rather than scaled, because the two readings differ by
    up to 10**30 and guessing wrong overpays by that factor.

    Raises:
        NanoX402Refused: If the amount is not a positive integer string in raw.
    """
    text = str(amount if amount is not None else "").strip()
    if _RAW_RE.fullmatch(text):
        return int(text)
    if "." in text:
        try:
            as_xno = Decimal(text)
        except InvalidOperation:
            as_xno = None
        hint = ""
        if as_xno is not None and as_xno.is_finite() and as_xno > 0:
            # Exactly, for the same reason as _xno_to_raw_exact: a hint that
            # names the wrong number is worse than no hint.
            try:
                as_raw = _xno_to_raw_exact(as_xno)
            except NanoX402Refused:
                as_raw = None  # out of range: refuse below, with no hint
            if as_raw is not None:
                hint = f"; {text} XNO would be '{as_raw}'"
        raise NanoX402Refused(
            f"amount must be an integer string in raw on nano:mainnet, got {amount!r}"
            f"{hint}. Refusing rather than guessing which unit the seller meant."
        )
    raise NanoX402Refused(f"amount must be a positive integer string in raw, got {amount!r}")


def _xno_to_raw_exact(value: Decimal) -> Optional[int]:
    """Scale a finite, positive ``Decimal`` of XNO to integer raw, exactly.

    ``value * RAW_PER_XNO`` would go through the ambient ``decimal`` context,
    whose default precision is 28 while a raw amount reaches 39 digits, so the
    product is rounded before anyone can inspect it -- and the usual
    ``to_integral_value()`` check cannot see it, because a value rounded at the
    28th significant digit is still an integer. This mirrors
    ``nano_pay.raw_to_xno`` in the other direction: the digits are placed by
    integer arithmetic on the decimal tuple and never multiplied.

    The magnitude is checked with ``adjusted()`` (constant time) *before* any
    integer is built, because the exponent can come from a seller: ``1e20000000``
    would otherwise make a 20-million-digit power of ten, and ``1e-20000000``
    the same as a divisor. Trailing zeros are stripped from the digit tuple, so
    the integer built at the end has at most ``_MAX_XNO_EXPONENT + 30`` digits.

    Returns:
        The amount in raw, or ``None`` if ``value`` is finer than one raw.

    Raises:
        NanoX402Refused: If ``value`` is ``10**_MAX_XNO_EXPONENT`` XNO or more.
    """
    magnitude = value.adjusted()
    if magnitude >= _MAX_XNO_EXPONENT:
        raise NanoX402Refused(f"an XNO amount must be below 10**{_MAX_XNO_EXPONENT}")
    if magnitude < -_RAW_EXPONENT:
        return None  # nonzero and below one raw
    _, digits, exponent = value.as_tuple()
    significant = bytes(digits).rstrip(b"\0")
    if not significant:
        return 0
    shift = int(exponent) + (len(digits) - len(significant)) + _RAW_EXPONENT
    if shift < 0:
        return None  # its last nonzero digit is below one raw
    return int("".join(map(str, significant))) * 10 ** shift


def _cap_to_raw(max_xno: Any) -> int:
    """Convert a cap in XNO to raw, refusing the non-finite and the non-positive."""
    try:
        value = Decimal(str(max_xno))
    except (InvalidOperation, ValueError) as exc:
        raise NanoX402Refused(f"max_xno is not a number: {max_xno!r}") from exc
    if not value.is_finite() or value <= 0:
        raise NanoX402Refused(f"max_xno must be a positive, finite number of XNO: {max_xno!r}")
    try:
        raw = _xno_to_raw_exact(value)
    except NanoX402Refused as exc:
        raise NanoX402Refused(f"max_xno is out of range: {exc}") from None
    if raw is None:
        raise NanoX402Refused(f"max_xno is finer than one raw (10**-30 XNO): {max_xno!r}")
    return raw


def nano_spend_controls(
    max_xno: Any = DEFAULT_MAX_XNO,
    network: str = NETWORK_NANO_MAINNET,
) -> dict[str, Any]:
    """Build ``spend_controls`` that let an x402 client pay XNO, capped in raw.

    The SDK's default spend controls reject ``nano:mainnet`` outright; see the
    module docstring. This returns the opt-in that allows it, with the ceiling
    expressed as an integer atomic amount so no dollar figure is ever reinterpreted
    as XNO::

        client.set_spend_controls(nano_spend_controls(max_xno="0.01"))

    Args:
        max_xno: Ceiling for a single payment, in XNO.
        network: The Nano network to allow. ``"nano:*"`` allows every Nano network.

    Returns:
        A ``SpendControls`` dict with one ``allowed_assets`` entry for XNO.

    Raises:
        NanoX402Refused: If ``max_xno`` is not a positive, finite number of XNO.
    """
    return {
        "allowed_assets": [
            {
                "network": str(network),
                "asset": ASSET_XNO,
                "max_amount_per_payment": str(_cap_to_raw(max_xno)),
            }
        ]
    }


class ExactNanoClientScheme:
    """``SchemeNetworkClient`` for the ``exact`` scheme on a Nano network.

    Register it on an ``x402Client`` for the network the seller quotes::

        client.register("nano:mainnet", ExactNanoClientScheme(wallet, rpc))

    Args:
        wallet: A loaded feeless402 ``Wallet``. Holds the seed; never logged.
        rpc: A feeless402 ``RPC``. Supplies the frontier, the balance and --
            ideally -- ``work_generate``; see the module docstring on work.
        max_xno: Ceiling for a single payment, in XNO. Defaults to
            ``DEFAULT_MAX_XNO``. A quote above it is refused before signing.
        network: The x402 network this instance pays on. Must be a ``nano:``
            network, and must match the quote.

    Attributes:
        scheme: ``"exact"``, the scheme identifier the SDK dispatches on.
    """

    scheme = SCHEME_EXACT

    def __init__(
        self,
        wallet: Any,
        rpc: Any,
        *,
        max_xno: Any = DEFAULT_MAX_XNO,
        network: str = NETWORK_NANO_MAINNET,
    ) -> None:
        """Bind a wallet and an RPC, and fix the cap and the network."""
        if not str(network).startswith("nano:"):
            raise NanoX402Refused(
                f"ExactNanoClientScheme pays Nano networks only, got network={network!r}"
            )
        self._wallet = wallet
        self._rpc = rpc
        self._network = str(network)
        self._max_raw = _cap_to_raw(max_xno)
        self._lock = threading.Lock()
        self._pending: Optional[tuple] = None  # (new_frontier, work_root)

    @property
    def network(self) -> str:
        """The x402 network this instance pays on."""
        return self._network

    @property
    def max_amount_raw(self) -> int:
        """The per-payment ceiling, in raw."""
        return self._max_raw

    def create_payment_payload(self, requirements: Any) -> dict[str, Any]:
        """Sign a send block for ``requirements`` and return the inner payload.

        Returns:
            ``{"block": {...}}`` -- the ``EXACT_NANO_PAYLOAD`` shape the Nano
            facilitator verifies. The SDK wraps it into a full ``PaymentPayload``.

        Raises:
            NanoX402Refused: For any quote this cannot pay exactly as asked, and
                for a signed block that does not match the quote. Nothing is
                broadcast either way: the facilitator settles, so a refusal here
                means no payment exists.
        """
        pay_to, amount_raw = self._check_quote(requirements)
        with self._lock:
            block = self._sign(pay_to, amount_raw)
        return {"block": block}

    def settled(self, prework: bool = False) -> None:
        """Tell the wallet the last block was settled, so it re-warms its work.

        ``prework=True`` generates the next block's proof of work now, which is
        the 6-35 s cost described in the module docstring; the default defers it.
        """
        pending, self._pending = self._pending, None
        if pending is not None:
            self._wallet.payment_succeeded(self._rpc, pending[0], pending[1], prework=prework)

    def not_settled(self) -> None:
        """Tell the wallet the last block was not settled; its cached work stands."""
        pending, self._pending = self._pending, None
        if pending is not None:
            self._wallet.payment_failed(pending[1])

    def _check_quote(self, requirements: Any) -> tuple[str, int]:
        """Validate the quote and return ``(canonical payTo, amount in raw)``."""
        scheme = str(getattr(requirements, "scheme", "") or "")
        if scheme != SCHEME_EXACT:
            raise NanoX402Refused(f"this scheme pays {SCHEME_EXACT!r} quotes only, got {scheme!r}")

        network = str(getattr(requirements, "network", "") or "")
        if network != self._network:
            raise NanoX402Refused(
                f"quote is for network {network!r}, this payer is registered for {self._network!r}"
            )

        asset = str(getattr(requirements, "asset", "") or "")
        if asset.upper() != ASSET_XNO:
            raise NanoX402Refused(f"unsupported asset {asset!r} on {network}; only {ASSET_XNO}")

        pay_to = normalize_payee(getattr(requirements, "pay_to", None))
        amount_raw = parse_raw_amount(getattr(requirements, "amount", None))

        if amount_raw > self._max_raw:
            raise NanoX402Refused(
                f"quote of {raw_to_xno(amount_raw)} XNO exceeds this payer's cap of "
                f"{raw_to_xno(self._max_raw)} XNO; refusing to pay"
            )
        if pay_to == self._wallet.address:
            raise NanoX402Refused(
                "payTo is this payer's own address; a self-payment buys nothing and would "
                "still burn the frontier"
            )
        return pay_to, amount_raw

    def _sign(self, pay_to: str, amount_raw: int) -> dict[str, Any]:
        """Sign the send block and refuse it unless it matches the quote exactly."""
        account = self._wallet.synced_account(self._rpc)
        observed_frontier = str(account.frontier)
        observed_balance = int(account.raw_bal)
        if observed_balance < amount_raw:
            raise NanoX402Refused(
                f"insufficient balance: have {raw_to_xno(observed_balance)} XNO, "
                f"the quote is {raw_to_xno(amount_raw)} XNO"
            )

        block, new_frontier, work_root = self._wallet.build_payment_block(
            self._rpc, pay_to, amount_raw
        )
        block = dict(block)
        self._verify_signed_block(block, pay_to, amount_raw, observed_frontier, observed_balance)

        # The one field feeless402 does not emit and the facilitator compares.
        block["link_as_account"] = pay_to
        self._pending = (new_frontier, work_root)
        return block

    def _verify_signed_block(
        self,
        block: dict[str, Any],
        pay_to: str,
        amount_raw: int,
        observed_frontier: str,
        observed_balance: int,
    ) -> None:
        """Refuse a block that does not pay exactly the quoted amount to the quoted payee.

        Checks the same properties the facilitator will, while the block can
        still be thrown away.
        """
        if block.get("type") != "state":
            raise NanoX402Refused(f"signed block is not a state block: {block.get('type')!r}")

        previous = str(block.get("previous") or "")
        if not _HEX64_RE.fullmatch(previous):
            raise NanoX402Refused(f"signed block has a malformed previous: {previous!r}")
        if previous.lower() != observed_frontier.lower():
            # A receive or another send landed between the balance read and the
            # signature, so the balance this block spends from is not the one
            # checked below. Refuse; the next attempt reads the new frontier.
            raise NanoX402Refused(
                "the account moved while this payment was being signed "
                f"(frontier {observed_frontier[:16]}... became {previous[:16]}...); "
                "nothing was paid, try again"
            )

        link = str(block.get("link") or "")
        if not _HEX64_RE.fullmatch(link):
            raise NanoX402Refused(f"signed block has a malformed link: {link!r}")
        if link.lower() != NET.to_pk(pay_to).lower():
            raise NanoX402Refused(
                f"signed block pays the wrong account: link {link} does not decode to "
                f"the quoted payTo {pay_to}"
            )

        balance_text = str(block.get("balance") or "")
        if not re.fullmatch(r"0|[1-9][0-9]*", balance_text):
            raise NanoX402Refused(f"signed block has a malformed balance: {balance_text!r}")
        sent = observed_balance - int(balance_text)
        if sent != amount_raw:
            raise NanoX402Refused(
                f"signed block sends {sent} raw where the quote is {amount_raw} raw; refusing"
            )

        signature = str(block.get("signature") or "")
        if not _SIGNATURE_RE.fullmatch(signature):
            raise NanoX402Refused(f"signed block has a malformed signature: {signature!r}")
        work = str(block.get("work") or "")
        if not _WORK_RE.fullmatch(work):
            raise NanoX402Refused(f"signed block has malformed work: {work!r}")
