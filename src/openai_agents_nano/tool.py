"""Thin OpenAI Agents SDK adapter reusing feeless402's Nano client.

`make_nano_x402_tool(...)` returns an OpenAI Agents SDK `FunctionTool` named
`nano_x402_fetch`, binding a self-custodied `Wallet` plus an `RPC` at
construction; the model never sees a wallet path, seed, plain RPC URL.

This is two-phase, so an agent only ever pays an offer it has seen: a
dry-run preview returns a spendless quote plus a single-use `quote_token`
bound to that exact offer.  Redeem mode refuses unless a valid,
unspent, matching token returns (missing, stale, replayed, re-offered
tokens get refused prior to signing).  A valid token is consumed, then
feeless402 signs locally, then verifies on the ledger.  The cap is
`min(max_xno, default)`.  Payments sharing one wallet are serialised
behind an `asyncio.Lock` since Nano blocks are stateful, non-replayable.
The return value is always agent-readable text.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import time
from decimal import Decimal
from pathlib import Path
from typing import Optional

try:  # the Agents SDK is imported lazily so the core adapter is importable alone
    from agents import FunctionTool, function_tool
except Exception:  # pragma: no cover - optional dependency
    FunctionTool = None
    function_tool = None

from nano_pay.rpc import RPC
from nano_pay.wallet import Wallet
from nano_pay.x402 import PaidRequestFailed, request_with_payment
from nano_pay import xno_to_raw, raw_to_xno

from .mandate import MandateGuard, MandateRefused, raw_to_xno as _mandate_raw_to_xno

DEFAULT_WALLET_ENV = "X402_WALLET_PATH"
DEFAULT_WALLET_PATH = "~/.nano-pay/wallet.json"
DEFAULT_MAX_XNO = os.environ.get("X402_MAX_XNO", "0.01")  # hard default cap
QUOTE_TOKEN_TTL_S = 60 * 30  # a preview is only good for half an hour
DEFAULT_MANDATE_ENV = "X402_MANDATE_PATH"  # an operator-signed spend cap (mandate.py)
DEFAULT_MANDATE_LEDGER_ENV = "X402_MANDATE_LEDGER"


class NanoX402ToolError(Exception):
    """Raised only for conditions the tool cannot represent as text."""


class QuoteTokenStore:
    """Single-use, expiring quote tokens bound to an exact quoted offer.

    A token is minted on a dry-run preview against the offer the server just
    quoted, then consumed on the first successful redeem. A token is either
    VALID (present, unexpired, pay_to plus amount both match the offer the
    redeem is about to pay) or REFUSED
    (missing-token, stale, already-used, offer-changed).  Thread-safety comes
    from the tool serialising payments behind a single asyncio.Lock, so a
    dict is sufficient here.
    """

    def __init__(self, ttl_s: float = QUOTE_TOKEN_TTL_S, now=None):
        self.ttl_s = ttl_s
        self._now = now or time.time
        self._tokens = {}  # token -> (pay_to, amount_raw, expires)

    def mint(self, pay_to: str, amount_raw: int) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[token] = (
            str(pay_to),
            int(amount_raw),
            self._now() + self.ttl_s,
        )
        return token

    def reject(self, token: str, pay_to: str, amount_raw: int) -> Optional[str]:
        """Return a refusal reason if ``token`` cannot redeem this offer, else None."""
        if not token:
            return "missing"
        rec = self._tokens.get(token)
        if rec is None:
            return "invalid-or-used"
        bound_pay_to, bound_amount, expires = rec
        if self._now() > expires:
            self._tokens.pop(token, None)
            return "expired"
        if str(pay_to) != bound_pay_to or int(amount_raw) != bound_amount:
            return "offer-changed"
        self._tokens.pop(token, None)  # single-use: consumed here
        return None


class _MandatedWallet:
    """The wallet as request_with_payment sees it when an operator mandate is set.

    feeless402 re-reads the 402 before it pays, so the payee and amount it
    signs are the ones that matter. This proxy checks THOSE, at the moment
    the block is built: the mandate guard reserves the amount in its ledger
    and only then lets the real wallet sign. A refusal raises MandateRefused
    before any block exists. Everything else is the real wallet.
    """

    def __init__(self, wallet, guard: MandateGuard, ref: str):
        self._wallet = wallet
        self._guard = guard
        self._ref = ref

    def __getattr__(self, name):
        return getattr(self._wallet, name)

    def build_payment_block(self, rpc, to_addr, raw_amt):
        return self._guard.spend(
            to_addr, int(raw_amt),
            lambda: self._wallet.build_payment_block(rpc, to_addr, raw_amt),
            ref=self._ref[:200],
        )


def _format_mandate_refusal(exc: MandateRefused) -> str:
    return (
        "REFUSED: your operator's mandate does not allow this payment.\n"
        f"  reason: {exc.reason}\n"
        f"  detail: {exc.message}\n"
        "Nothing was signed or paid. Only the operator can widen a mandate."
    )


def _wallet_path(wallet_path: Optional[str]) -> str:
    if wallet_path is not None:
        return wallet_path
    return os.environ.get(DEFAULT_WALLET_ENV, DEFAULT_WALLET_PATH)


def _apply_cap(requested: Optional[str], default: str) -> Decimal:
    """The applied cap is min(requested, default); a bad value either side is refused."""
    # The default is operator-supplied (default_max_xno, else X402_MAX_XNO) and is the
    # hard limit of the two, but it used to reach Decimal() with no check: a typo
    # ("0.01 XNO", an empty export, "nan") raised InvalidOperation straight past the
    # caller's `except ValueError`, and a negative one got through to xno_to_raw, which
    # is not inside any try. Check it exactly as the requested value is checked below,
    # so a misconfigured cap is refused in text that names it.
    try:
        cap = Decimal(str(default))
    except Exception:
        raise ValueError(f"the configured default cap is not a number: {default!r}")
    if not cap.is_finite():
        raise ValueError(f"the configured default cap is not a finite number: {default!r}")
    if cap < 0:
        raise ValueError(f"the configured default cap must be >= 0: {default!r}")
    if requested is not None and str(requested).strip() != "":
        try:
            req = Decimal(str(requested))
        except Exception:
            raise ValueError(f"max_xno is not a number: {requested!r}")
        # Decimal() accepts "nan"/"snan"/"Infinity" happily, and comparing a NaN
        # raises InvalidOperation rather than returning False -- so without this
        # the `min()` below escapes as an unhandled ArithmeticError, past the
        # caller's `except ValueError`. max_xno is model-supplied.
        if not req.is_finite():
            raise ValueError(f"max_xno is not a finite number: {requested!r}")
        if req < 0:
            raise ValueError(f"max_xno must be >= 0: {requested!r}")
        cap = min(cap, req)
    return cap


def _format_quote(quote: dict, cap_xno: str, token: Optional[str]) -> str:
    lines = [
        "QUOTE (dry run, nothing spent):",
        f"  price:  {quote.get('amount_xno')} XNO",
        f"  pay_to: {quote.get('pay_to')}",
        f"  cap:    {cap_xno} XNO (refusing to pay more than this)",
        "Call again with dry_run=false, passing the quote_token below, to pay",
        "this exact offer.",
    ]
    if token:
        lines.append(f"  quote_token: {token}")
    return "\n".join(lines)


_REFUSAL_REASONS = {
    "missing": (
        "REFUSED: no quote token. Call dry_run=true first to preview the offer "
        "and receive a single-use quote_token, then redeem with dry_run=false "
        "and that token."
    ),
    "invalid-or-used": (
        "REFUSED: the quote token is invalid or already used. Call dry_run=true "
        "to mint a fresh quote_token."
    ),
    "expired": (
        "REFUSED: the quote token has expired. Call dry_run=true to re-preview "
        "and mint a fresh quote_token."
    ),
    "offer-changed": (
        "REFUSED: the endpoint changed its price or pay_to since your preview. "
        "Call dry_run=true again to re-preview the new offer and mint a fresh "
        "quote_token."
    ),
}


def _format_refusal(reason: str) -> str:
    return _REFUSAL_REASONS.get(reason, f"REFUSED: {reason}")


def _format_cap_refusal(price_xno: str, cap_xno: str) -> str:
    return (
        "REFUSED: the endpoint's price is above your cap.\n"
        f"  price: {price_xno} XNO\n"
        f"  cap:   {cap_xno} XNO\n"
        "Nothing was paid. Raise max_xno (or the tool's default cap) if you "
        "intend to pay this endpoint."
    )


def _format_receipt(resp, receipt: dict, cap_xno: str) -> str:
    """Render a redeem result with a truthful head line.

    Only a ledger-confirmed payment may be headed PAID. A block the ledger
    does not hold (settled False) or whose verdict is indeterminate must never
    read as paid: the block hash and verdict are always shown so a caller can
    check before ever paying again.
    """
    settled = receipt.get("settled")
    if settled is True:
        headline = "PAID (Nano x402):"
    elif settled is False:
        headline = "NOT PAID (Nano x402) - ledger does not hold the block:"
    else:
        headline = "UNCONFIRMED (Nano x402) - verdict indeterminate; check the block hash before paying again:"
    lines = [
        headline,
        f"  status:    {resp.status_code}",
        f"  amount:    {receipt.get('amount_xno')} XNO  (cap {cap_xno})",
        f"  pay_to:    {receipt.get('pay_to')}",
        f"  block:     {receipt.get('block')}",
        f"  settled:   {receipt.get('settled')}",
        f"  ledger:    {receipt.get('ledger')}",
    ]
    note = receipt.get("note")
    if note:
        lines.append(f"  note:      {note}")
    lines.append("  body:")
    try:
        body = resp.text
    except Exception:
        body = ""
    body = (body or "").strip()
    lines.append(body[:4000] if body else "  (empty response body)")
    return "\n".join(lines)


def _format_failed_payment(exc: "PaidRequestFailed", cap_xno: str) -> str:
    """A signed block was handed to the merchant but no reply came back.

    Never a generic error that hides the block: the money may well have
    moved. Surface the signed block hash and the ledger verdict and tell the
    caller to re-present the SAME block, never to pay again blind.
    """
    rec = exc.receipt or {}
    block = rec.get("block") or "?"
    amount = rec.get("amount_xno") or "?"
    settled = rec.get("settled")
    ledger = rec.get("ledger")
    lines = [
        f"PAYMENT OUTCOME UNKNOWN (Nano x402) - merchant did not reply:",
        f"  block:     {block}",
        f"  amount:    {amount} XNO  (cap {cap_xno})",
        f"  settled:   {settled}",
        f"  ledger:    {ledger}",
    ]
    note = rec.get("note")
    if note:
        lines.append(f"  note:      {note}")
    lines.append(
        "  action:    do NOT pay again; this block may already be on the ledger. "
        f"Re-present the SAME block {block} to collect your resource, or ask the "
        "merchant about it before paying anything else."
    )
    return "\n".join(lines)


def make_nano_x402_tool(
    wallet_path: Optional[str] = None,
    rpc: Optional[RPC] = None,
    default_max_xno: Optional[str] = None,
    token_store: Optional[QuoteTokenStore] = None,
    mandate_path: Optional[str] = None,
    mandate_ledger: Optional[str] = None,
) -> FunctionTool:
    """Return an OpenAI Agents SDK FunctionTool named ``nano_x402_fetch``.

    wallet_path: path to the self-custodied Nano wallet. Default: the
      ``X402_WALLET_PATH`` env var, else ``~/.nano-pay/wallet.json``.
    rpc: a feeless402 ``RPC``. Default: a fresh ``RPC()`` against public nodes.
    default_max_xno: the hard cap when the model does not pass one. Default:
      the ``X402_MAX_XNO`` env var, else 0.01 XNO.
    token_store: normally omitted (one is created per tool). Injectable for tests.
    mandate_path: an operator-signed mandate (see ``mandate.py``). Default: the
      ``X402_MANDATE_PATH`` env var, else none. When set, every payment must
      also fit the mandate's total cap, per-payment max, payee allow-list and
      expiry, checked against the payee and amount actually being signed; a
      mandate that cannot be read or verified refuses every payment.
    mandate_ledger: where the mandate's spend is recorded. Default:
      ``X402_MANDATE_LEDGER``, else ``<mandate_path>.ledger.json``.
    """
    if function_tool is None:  # pragma: no cover - optional dependency
        raise ImportError(
            "openai-agents is not installed; install with `pip install "
            "openai-agents-nano[x402]` or `pip install openai-agents`."
        )
    wallet = Wallet(Path(_wallet_path(wallet_path)).expanduser())
    rpc = rpc or RPC()
    # X402_MAX_XNO is re-read here: DEFAULT_MAX_XNO was bound at import, so a
    # value exported after `import openai_agents_nano` used to be ignored.
    default_cap = str(default_max_xno or os.environ.get("X402_MAX_XNO") or DEFAULT_MAX_XNO)
    lock = asyncio.Lock()
    tokens = token_store or QuoteTokenStore()
    # Read at construction, not import: a variable set after import still binds.
    mandate_file = mandate_path or os.environ.get(DEFAULT_MANDATE_ENV) or None
    mandate_ledger = mandate_ledger or os.environ.get(DEFAULT_MANDATE_LEDGER_ENV) or None

    def _guard() -> MandateGuard:
        return MandateGuard.from_file(mandate_file, mandate_ledger, agent=wallet.address)

    @function_tool(
        name_override="nano_x402_fetch",
        description_override=(
            "Fetch an HTTP resource that requires an x402 payment, paying in "
            "self-custodied Nano (XNO). Two-phase: first call with dry_run=true "
            "to preview the price, pay_to and cap and receive a single-use "
            "quote_token (nothing is spent). Then, only if the price is within "
            "an acceptable cap and you intend to pay, call with dry_run=false, "
            "passing that exact quote_token back — it pays from the configured "
            "wallet and returns the resource body plus the on-ledger receipt. "
            "Never pay more than necessary; keep max_xno small."
        ),
    )
    async def _nano_x402_fetch(
        url: str,
        method: str = "GET",
        json_body: str = "",
        max_xno: Optional[str] = None,
        dry_run: bool = False,
        quote_token: Optional[str] = None,
    ) -> str:
        if not wallet.exists():
            wallet.create()
        else:
            wallet.load()  # an existing funded wallet must be loaded to sign
        try:
            cap_xno = str(_apply_cap(max_xno, default_cap))
            # xno_to_raw sat outside this guard. It refuses an amount finer than
            # one raw (10**-30 XNO) with AmountError, and max_xno is
            # model-supplied: a model told to "keep max_xno small" that answers
            # "1e-40" left the tool as an exception, which the Agents SDK renders
            # to the model as "An error occurred while running the tool. Please
            # try again." -- a retry that cannot ever succeed, with no reason
            # given, while "nan" one line above already refused in plain text.
            # AmountError is a ValueError, so widening the guard to cover the
            # conversion is the whole fix; the cap itself is unchanged.
            cap_raw = xno_to_raw(cap_xno)
        except ValueError as e:
            return f"REFUSED: {e}"

        req_kwargs = {}
        if json_body:
            import json as _json

            try:
                req_kwargs["json"] = _json.loads(json_body)
            except Exception:
                req_kwargs["data"] = json_body

        async with lock:  # one wallet, stateful non-replayable Nano blocks
            try:
                # Spendless quote first: never sign or broadcast on dry_run.
                _resp, quote = await asyncio.to_thread(
                    request_with_payment,
                    method, url, wallet, rpc, cap_raw,
                    headers={"x-x402": "true"},
                    dry_run=True,
                    **req_kwargs,
                )
            except Exception as e:
                return f"ERROR: could not read the x402 quote: {e}"
            if dry_run:
                if quote is None:
                    return f"NOTE: {url} returned {_resp.status_code}, not a 402 x402 quote; nothing spent."
                token = tokens.mint(quote.get("pay_to") or "", quote.get("amount_raw") or 0)
                text = _format_quote(quote, cap_xno, token)
                if mandate_file:
                    try:
                        verdict = _guard().check(quote.get("pay_to") or "", int(quote.get("amount_raw") or 0))
                        text += ("\n  mandate: allows this payment; "
                                 f"{_mandate_raw_to_xno(int(verdict['remaining_after_raw']))} XNO would remain")
                    except MandateRefused as e:
                        text += f"\n  mandate: would REFUSE this payment ({e.reason}: {e.message})"
                return text

            # Not dry_run: two-phase redeem. The agent must hold a single-use
            # quote token minted against the exact offer it is about to pay.
            if quote is None:
                return f"NOTE: {url} returned {_resp.status_code}, not a 402 x402 quote; nothing spent."
            pay_wallet = wallet
            if mandate_file:
                # Checked before the token is consumed, so a refusal costs no preview.
                try:
                    guard = _guard()
                    guard.check(quote.get("pay_to") or "", int(quote.get("amount_raw") or 0))
                except MandateRefused as e:
                    return _format_mandate_refusal(e)
                pay_wallet = _MandatedWallet(wallet, guard, ref=f"{method} {url}")
            reason = tokens.reject(quote_token or "", quote.get("pay_to") or "", quote.get("amount_raw") or 0)
            if reason is not None:
                return _format_refusal(reason)

            # The quoted offer is authorised; enforce the cap before signing.
            price_raw = int(quote.get("amount_raw") or 0)
            if price_raw > cap_raw:
                return _format_cap_refusal(raw_to_xno(price_raw), cap_xno)

            try:
                resp, receipt = await asyncio.to_thread(
                    request_with_payment,
                    method, url, pay_wallet, rpc, cap_raw,
                    headers={"x-x402": "true"},
                    dry_run=False,
                    **req_kwargs,
                )
            except MandateRefused as e:
                # Raised while building the block: nothing was signed.
                return _format_mandate_refusal(e)
            except PaidRequestFailed as e:
                # A signed block is in the merchant's hands with no reply: the
                # money may have moved. Never swallow this into a generic
                # "failed" that invites a blind re-pay.
                return _format_failed_payment(e, cap_xno)
            except Exception as e:
                return f"ERROR: payment or request failed: {e}"
            receipt = receipt or {}
            return _format_receipt(resp, receipt, cap_xno)

    return _nano_x402_fetch


__all__ = ["make_nano_x402_tool", "QuoteTokenStore", "NanoX402ToolError", "MandateGuard", "MandateRefused"]