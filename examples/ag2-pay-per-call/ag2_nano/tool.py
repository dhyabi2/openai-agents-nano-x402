"""A plain AG2 (formerly AutoGen) tool function that pays any x402-priced HTTP
endpoint in self-custodied Nano (XNO).

This is a thin framework adapter: it rebuilds **no** Nano payment logic. It
reuses the MIT-licensed feeless402 client (`nano_pay.x402.request_with_payment`,
`nano_pay.wallet.Wallet`, `nano_pay.rpc.RPC`) and exposes a completely ordinary
Python function, ``nano_x402_fetch``, that AG2 discovers from its annotated
signature + docstring and wraps into a ``FunctionTool`` (see
``AssistantAgent(tools=[...])``). No new abstraction, no framework-specific
`Tool` class to learn.

The wallet path and RPC are bound once at construction (via
:func:`make_nano_x402_fetch`) and are **never visible to the model**, so an AG2
agent cannot spend more than the caller's cap.

Two-phase, honest-by-default: a ``dry_run=True`` preview returns a spendless
quote plus a single-use ``quote_token`` bound to that exact offer; redeeming
(with ``dry_run=False`` and that token) spends only after the ledger confirms
the block. Offline callers can inject ``pay_call`` for deterministic tests; the
default is feeless402's real two-phase handshake.
"""

from __future__ import annotations

import json as _json
import os
import secrets
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Optional

try:  # feeless402 is optional so the module is importable (and testable) without it
    from nano_pay.rpc import RPC
    from nano_pay.wallet import Wallet
    from nano_pay.x402 import PaidRequestFailed, request_with_payment
    from nano_pay import xno_to_raw
except Exception:  # pragma: no cover - optional dependency
    RPC = Wallet = None
    PaidRequestFailed = None
    request_with_payment = None
    xno_to_raw = None

DEFAULT_WALLET_ENV = "X402_WALLET_PATH"
DEFAULT_WALLET_PATH = "~/.nano-pay/wallet.json"
DEFAULT_MAX_XNO = os.environ.get("X402_MAX_XNO", "0.01")  # hard default cap
QUOTE_TOKEN_TTL_S = 60 * 30


class QuoteTokenStore:
    """Single-use, expiring quote tokens bound to an exact quoted offer.

    Mirrors the OpenAI-SDK / smolagents adapters' store so the same honesty
    guarantees hold: a preview mints a token bound to (pay_to, amount_xno); a
    redeem is refused unless a valid, unexpired, matching token is presented,
    and the token is consumed on first use. Bound to amount *in XNO* because
    that is what both the dry-run quote and the settled receipt reliably report.
    """

    def __init__(self, ttl_s: float = QUOTE_TOKEN_TTL_S, now=None):
        self.ttl_s = ttl_s
        self._now = now or time.time
        self._tokens = {}  # token -> (pay_to, amount_xno, expires)

    def mint(self, pay_to: str, amount_xno) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[token] = (str(pay_to), str(amount_xno), self._now() + self.ttl_s)
        return token

    def consume(self, token: str) -> bool:
        """Reserve `token` for one redemption, before any money is spent.

        Returns False (and leaves the token unused) for a missing, expired or
        already-consumed token. On True the token is single-use: a second
        redeem with the same token is refused *before* the payment call, so a
        consumed preview can never authorize a second spend. The exact-offer
        binding lives in feeless402's live re-quote plus the caller's hard cap;
        this store's job is the "one redemption per preview" gate.
        """
        if not isinstance(token, str) or not token:
            return False
        rec = self._tokens.get(token)
        if rec is None:
            return False
        if self._now() > rec[2]:
            self._tokens.pop(token, None)
            return False
        self._tokens.pop(token, None)  # single-use: consumed here
        return True


def _wallet_path(wallet_path: Optional[str]) -> str:
    if wallet_path is not None:
        return wallet_path
    return os.environ.get(DEFAULT_WALLET_ENV, DEFAULT_WALLET_PATH)


def _apply_cap(max_xno: Optional[str]) -> float:
    """The applied cap is a non-negative XNO float; a bad value is refused."""
    if max_xno is None or str(max_xno).strip() == "":
        return float(Decimal(str(DEFAULT_MAX_XNO)))
    try:
        cap = float(Decimal(str(max_xno)))
    except (InvalidOperation, ValueError):
        raise ValueError(f"max_xno is not a number: {max_xno!r}")
    if cap < 0:
        raise ValueError(f"max_xno must be >= 0: {max_xno!r}")
    return min(cap, float(Decimal(str(DEFAULT_MAX_XNO))))


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


def _format_receipt(receipt: dict, cap_xno: str) -> str:
    """Render a settled result with a truthful head line: only a ledger-confirmed
    payment may read PAID."""
    settled = receipt.get("settled")
    if settled is True:
        headline = "PAID (Nano x402):"
    elif settled is False:
        headline = "NOT PAID (Nano x402) - ledger does not hold the block:"
    else:
        headline = "UNCONFIRMED (Nano x402) - verdict indeterminate; check the block hash before paying again:"
    lines = [
        headline,
        f"  amount: {receipt.get('amount_xno')} XNO  (cap {cap_xno})",
        f"  pay_to: {receipt.get('pay_to')}",
        f"  block:  {receipt.get('block')}",
        f"  settled:{receipt.get('settled')}",
        f"  ledger: {receipt.get('ledger')}",
    ]
    note = receipt.get("note")
    if note:
        lines.append(f"  note:   {note}")
    return "\n".join(lines)


# Default pay_call: feeless402's real two-phase handshake, wallet-bound.
def _default_pay_call(wallet_path: str, rpc: RPC):  # pragma: no cover - live path
    wallet = Wallet(Path(wallet_path).expanduser())

    def pay(method: str, url: str, headers: dict, dry_run: bool, max_raw: float):
        return request_with_payment(
            method, url, wallet, rpc, max_raw=max_raw, headers=headers, dry_run=dry_run
        )

    return pay


def make_nano_x402_fetch(
    wallet_path: Optional[str] = None,
    rpc: Optional[RPC] = None,
    default_max_xno: Optional[str] = None,
    pay_call: Optional[Callable] = None,
    token_store: Optional[QuoteTokenStore] = None,
) -> Callable[..., str]:
    """Return the AG2 tool function ``nano_x402_fetch``.

    wallet_path: path to the self-custodied Nano wallet. Default: the
      ``X402_WALLET_PATH`` env var, else ``~/.nano-pay/wallet.json``.
    rpc: a feeless402 ``RPC``. Default: a fresh ``RPC()`` against public nodes.
    default_max_xno: hard cap when the model omits max_xno. Default: the
      ``X402_MAX_XNO`` env var, else 0.01 XNO.
    pay_call: injectable function ``(method, url, headers, dry_run, max_raw) ->
      (response, receipt_or_quote)``. Default: feeless402's
      ``request_with_payment`` bound to the constructed wallet. Injectable so
      offline tests are deterministic.
    token_store: normally omitted (one is created per tool); injectable for tests.
    """
    wallet_path = _wallet_path(wallet_path)
    rpc = rpc or (RPC() if RPC else None)
    cap = str(default_max_xno or DEFAULT_MAX_XNO)
    tokens = token_store or QuoteTokenStore()
    pay = pay_call or _default_pay_call(wallet_path, rpc)

    def nano_x402_fetch(
        url: str,
        method: str = "GET",
        headers_json: Optional[str] = None,
        max_xno: Optional[float] = None,
        dry_run: bool = False,
        quote_token: Optional[str] = None,
    ) -> str:
        """Fetch an HTTP resource that may require an x402 payment, paying in
        self-custodied Nano (XNO). Call with dry_run=true first to preview the
        price/pay_to/cap (nothing is spent), then with dry_run=false and the
        returned quote_token to settle this exact offer. Returns the fetched
        body text (or a readable PAID/QUOTE/REFUSED receipt). Use for paid
        tool/API calls, paywalled endpoints, and metered model calls. url: the
        URL to fetch (HTTP/HTTPS). method: HTTP method, default GET.
        headers_json: optional JSON object string of extra request headers.
        max_xno: hard cap in XNO; refuse to pay more (default 0.01).
        dry_run: if true, preview the quote without spending. quote_token:
        single-use token from a dry_run preview to settle that exact offer."""
        try:
            cap_xno = _apply_cap(str(max_xno) if max_xno is not None else None)
        except ValueError as e:
            return f"REFUSED: {e}"
        headers: dict = {}
        if headers_json:
            try:
                parsed = _json.loads(headers_json)
                if isinstance(parsed, dict):
                    headers = {str(k): str(v) for k, v in parsed.items()}
                else:
                    return "REFUSED: headers_json must be a JSON object"
            except Exception as e:  # noqa: BLE001
                return f"REFUSED: headers_json not valid JSON: {e}"

        max_raw = xno_to_raw(cap_xno)

        if not dry_run:
            if not quote_token or not tokens.consume(quote_token):
                return (
                    "REFUSED: no valid quote_token. Call dry_run=true first to "
                    "preview the offer and receive a single-use quote_token, "
                    "then redeem with dry_run=false and that token."
                )

        try:
            resp, result = pay(method, url, headers, dry_run, max_raw)
        except PaidRequestFailed as exc:  # pragma: no cover - live failure path
            return _format_receipt(exc.receipt or {}, str(cap_xno))

        if dry_run:
            quote = result or {}
            pay_to = quote.get("pay_to")
            amount_xno = quote.get("amount_xno")
            tok = tokens.mint(pay_to, amount_xno) if pay_to and amount_xno is not None else None
            return _format_quote(quote, str(cap_xno), tok)

        receipt = result or {}
        body = resp.text if hasattr(resp, "text") else str(resp)
        return _format_receipt(receipt, str(cap_xno)) + "\n  body:\n" + (body or "")

    # Bind the closure state onto the function so it is picklable/visible for tests.
    nano_x402_fetch.__ag2_nano_cap__ = str(cap)  # expose for introspection only
    return nano_x402_fetch
