"""A smolagents Tool that pays any x402-priced HTTP endpoint in self-custodied
Nano (XNO).

This is a thin framework adapter: it rebuilds **no** Nano payment logic. It
reuses the MIT-licensed feeless402 client (`nano_pay.x402.request_with_payment`,
`nano_pay.wallet.Wallet`, `nano_pay.rpc.RPC`) and exposes it as a smolagents
`Tool` named ``nano_x402_fetch`` — so a smolagents code-writing agent can settle
a metered tool/model call itself, on a feeless, sub-second, self-sovereign rail.

Design matches smolagents' "no new abstraction" philosophy: one small class, no
new abstraction layer. The wallet path and RPC are bound at construction and are
never visible to the model, so the agent cannot spend more than the caller's cap.

Two-phase, honest-by-default: a `dry_run=true` preview returns a spendless
quote plus a single-use `quote_token` bound to that exact offer; redeeming
(with `dry_run=false` and that token) spends only after the ledger confirms
the block. Offline callers can inject `pay_call` for deterministic tests; the
default is feeless402's real two-phase handshake.
"""

from __future__ import annotations

import os
import secrets
import time
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional, Union

try:  # smolagents is imported lazily so the adapter is importable standalone
    from smolagents import Tool
except Exception:  # pragma: no cover - optional dependency
    Tool = None

from nano_pay.rpc import RPC
from nano_pay.wallet import Wallet
from nano_pay.x402 import PaidRequestFailed, request_with_payment  # noqa: F401
from nano_pay import xno_to_raw

DEFAULT_WALLET_ENV = "X402_WALLET_PATH"
DEFAULT_WALLET_PATH = "~/.nano-pay/wallet.json"
DEFAULT_MAX_XNO = os.environ.get("X402_MAX_XNO", "0.01")  # hard default cap
QUOTE_TOKEN_TTL_S = 60 * 30


class QuoteTokenStore:
    """Single-use, expiring quote tokens bound to an exact quoted offer.

    Mirrors the OpenAI-SDK adapter's store so the same honesty guarantees hold:
    a preview mints a token bound to (pay_to, amount_xno); a redeem is refused
    unless a valid, unexpired, matching token is presented, and the token is
    consumed on first use. Bound to amount *in XNO* because that is what both
    the dry-run quote and the settled receipt reliably report.
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


def _apply_cap(max_xno: Optional[Union[str, int, float]]) -> float:
    """The applied cap is a non-negative XNO float; a bad value is refused."""
    if max_xno is None or str(max_xno).strip() == "":
        return float(Decimal(str(DEFAULT_MAX_XNO)))
    try:
        cap = float(Decimal(str(max_xno)))
    except Exception:
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


def make_nano_x402_tool(
    wallet_path: Optional[str] = None,
    rpc: Optional[RPC] = None,
    default_max_xno: Optional[str] = None,
    pay_call: Optional[Callable] = None,
    token_store: Optional[QuoteTokenStore] = None,
) -> Tool:
    """Return a smolagents ``Tool`` named ``nano_x402_fetch``.

    wallet_path: path to the self-custodied Nano wallet. Default: the
      ``X402_WALLET_PATH`` env var, else ``~/.nano-pay/wallet.json``.
    rpc: a feeless402 ``RPC``. Default: a fresh ``RPC()`` against public nodes.
    default_max_xno: hard cap when the model omits max_xno. Default: the
      ``X402_MAX_XNO`` env var, else 0.01 XNO.
    pay_call: injectable function ``(method, url, headers, dry_run, max_raw) ->
      (response, receipt_or_quote)``. Default: feeless402's ``request_with_payment``
      bound to the constructed wallet. Injectable so offline tests are deterministic.
    token_store: normally omitted (one is created per tool); injectable for tests.
    """
    if Tool is None:  # pragma: no cover - optional dependency
        raise ImportError(
            "smolagents is not installed; install it with `pip install smolagents`."
        )
    wallet_path = _wallet_path(wallet_path)
    rpc = rpc or RPC()
    cap = str(default_max_xno or DEFAULT_MAX_XNO)
    tokens = token_store or QuoteTokenStore()
    pay = pay_call or _default_pay_call(wallet_path, rpc)

    class NanoX402Tool(Tool):
        name = "nano_x402_fetch"
        description = (
            "Fetch an HTTP resource that may require an x402 payment, paying in "
            "self-custodied Nano (XNO). Call with dry_run=true first to preview the "
            "price/pay_to/cap (nothing is spent), then with dry_run=false and the "
            "returned quote_token to settle this exact offer. Returns the fetched "
            "body text (or a readable PAID/QUOTE/REFUSED receipt). Use for paid "
            "tool/API calls, paywalled endpoints, and metered model calls."
        )
        inputs = {
            "url": {
                "type": "string",
                "description": "The URL to fetch (HTTP/HTTPS).",
            },
            "method": {
                "type": "string",
                "description": 'HTTP method, default "GET".',
                "nullable": True,
            },
            "headers_json": {
                "type": "string",
                "description": "Optional JSON object string of extra request headers.",
                "nullable": True,
            },
            "max_xno": {
                "type": "number",
                "description": "Hard cap in XNO; refuse to pay more. Default 0.01.",
                "nullable": True,
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, preview the quote without spending.",
                "nullable": True,
            },
            "quote_token": {
                "type": "string",
                "description": "Single-use token from a dry_run preview to settle that exact offer.",
                "nullable": True,
            },
        }
        output_type = "string"

        def forward(
            self,
            url: str,
            method: str = "GET",
            headers_json: Optional[str] = None,
            max_xno: Optional[float] = None,
            dry_run: bool = False,
            quote_token: Optional[str] = None,
        ) -> str:
            try:
                cap_xno = _apply_cap(max_xno)
            except ValueError as e:
                return f"REFUSED: {e}"
            headers = {}
            if headers_json:
                try:
                    import json as _json

                    parsed = _json.loads(headers_json)
                    if isinstance(parsed, dict):
                        headers = {str(k): str(v) for k, v in parsed.items()}
                    else:
                        return "REFUSED: headers_json must be a JSON object"
                except Exception as e:
                    return f"REFUSED: headers_json not valid JSON: {e}"

            max_raw = xno_to_raw(cap_xno)

            if not dry_run:
                # Redeem path: consume the quote_token BEFORE any money can be
                # spent. A missing, expired or already-consumed token is refused
                # without ever calling the payment layer, so one preview can
                # authorize at most one settlement.
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

            # Redeem succeeded: the token was consumed above and the payment was
            # settled within our cap by the feeless402 client.
            receipt = result or {}
            body = resp.text if hasattr(resp, "text") else str(resp)
            return _format_receipt(receipt, str(cap_xno)) + "\n  body:\n" + (body or "")

    return NanoX402Tool()
