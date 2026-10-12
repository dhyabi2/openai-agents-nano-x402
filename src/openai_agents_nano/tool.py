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
`min(max_xno, default)`.  Payments through one tool instance are serialised
behind an `asyncio.Lock` since Nano blocks are stateful, non-replayable.
The return value is always agent-readable text.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
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
from nano_pay.verify import block_hash as _state_block_hash
from nano_pay.wallet import Wallet
from nano_pay.x402 import PaidRequestFailed, PriceCapExceeded, request_with_payment
from nano_pay import xno_to_raw, raw_to_xno
import nano_pay.x402 as _x402_module

from .mandate import MandateGuard, MandateRefused, address_from_public_key, normalise_address
from .mandate import raw_to_xno as _mandate_raw_to_xno

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


class _PayeeMoved(Exception):
    """The paying read asked for a block to an address that was never authorised."""

    def __init__(self, authorised: str, asked: str):
        self.authorised, self.asked = authorised, asked
        super().__init__(f"authorised {authorised}, asked to sign to {asked}")


class _PayeePinnedWallet:
    """The wallet as request_with_payment sees it: it may only sign to the payee
    that was quoted and authorised.

    feeless402 RE-READS the 402 before it pays and signs to `offer_pay_to()` of
    THAT read, comparing only the amount against `max_raw`
    (`nano_pay/x402.py`: `if amount > max_raw: raise PriceCapExceeded`, then
    `wallet.build_payment_block(rpc, pay_to, amount)`). Nothing compared the
    payee. The quote_token binds `pay_to`, but against OUR read, never against
    the address finally signed - the same hole the amount had, one field over:
    preview quotes nano_A, the paying read answers nano_B for the same amount,
    the block is signed to nano_B and the tool reports PAID.

    `_MandatedWallet` already checks the signing-time payee, but only when an
    operator mandate is configured, which is not the default. This proxy is
    applied on every redeem and refuses before any block exists. Everything else
    is the wallet it wraps.
    """

    def __init__(self, wallet, pay_to: str):
        self._wallet = wallet
        self._pay_to = str(pay_to)
        # How many blocks THIS proxy built, all of them to `_pay_to`. Zero after
        # a redeem that returned a receipt means feeless402 did not sign in this
        # call: it re-presented a block from its payment journal, and neither
        # this pin nor the mandate proxy was ever consulted for it. (feeless402
        # builds at most once per call, and only after the last re-presentation
        # it tries, so a non-zero count means the block sent is the one built.)
        self.built = 0
        # Journal entries seen at the moment feeless402 asks for the account to
        # prove the send (`replay_proof`), i.e. after it chose the block it is
        # about to send and before any reply can make it drop that entry.
        self.seen_at_send = []

    def __getattr__(self, name):
        return getattr(self._wallet, name)

    def build_payment_block(self, rpc, to_addr, raw_amt):
        if str(to_addr) != self._pay_to:
            raise _PayeeMoved(self._pay_to, str(to_addr))
        out = self._wallet.build_payment_block(rpc, to_addr, raw_amt)
        self.built += 1
        return out

    def account(self, *args, **kwargs):
        try:
            self.seen_at_send.extend(_journal_live(self))
        except Exception:
            pass
        return self._wallet.account(*args, **kwargs)


# --- feeless402's payment journal ---------------------------------------------
# feeless402 (0.2.13) writes every signed block to `pending-payments.json` beside
# the wallet before sending it, keyed by sha256(METHOD|url|pay_to|amount[|body
# fingerprint]). When a later paying read gives the same key, it re-sends that
# stored block WITHOUT calling `wallet.build_payment_block` - so
# `_PayeePinnedWallet` and `_MandatedWallet` never see it. Preview quotes A, the
# paying read names B, a block to B for the same request from an earlier
# unanswered redeem is journalled: that block to B is re-presented, and nothing
# in this tool was asked.
#
# The journal is read here, read-only, as a file: feeless402 exposes no API for
# it, and this tool does not patch feeless402. A journal that cannot be read
# yields an empty view here. From feeless402 0.2.12 on, feeless402 itself refuses
# to pay on a journal it cannot read, so no replay can follow from that case;
# 0.2.9-0.2.11 treat an unreadable journal as empty and sign a fresh block, which
# reaches the payee pin. The file is the payer's
# own: a merchant cannot write it, so a payee read from a block in it is the
# payer's record, unlike the receipt's `pay_to`, which the merchant's
# payment-response header can overwrite.
_JOURNAL_FILE = "pending-payments.json"
_JOURNAL_TTL_DEFAULT_S = 24 * 3600


def _journal_ttl() -> float:
    return float(getattr(_x402_module, "JOURNAL_TTL_S", _JOURNAL_TTL_DEFAULT_S))


def _journal_path(wallet) -> Path:
    """The file feeless402's `_journal_path` uses for this wallet."""
    base = getattr(wallet, "path", "") or (Path.home() / ".nano-pay" / "wallet.json")
    return Path(base).parent / _JOURNAL_FILE


def _same_payee(a, b) -> bool:
    """True when `a` and `b` name the same Nano account (xrb_X is nano_X).
    Uses the vendored mandate's checksum-verifying normaliser. A string that is
    not a valid address never confirms a match, not even with itself: this is
    only ever asked whether a block pays the authorised account, and a payee
    that cannot be read as an account is not proof of that."""
    if not a or not b:
        return False
    try:
        return normalise_address(str(a)) == normalise_address(str(b))
    except Exception:
        return False


def _journalled_block(header):
    """(payee, amount_raw) of the signed block a stored payment header carries.

    The payee is the block's own `link` (the field that is signed). Only when
    the block has no `link` field at all is its unsigned `link_as_account`
    used; a `link` that is present but cannot be read leaves the payee None, as
    does a `link_as_account` that disagrees with the `link`. The amount is the
    `accepted` offer the header echoes (x402 v2), or None (the NanoGPT dialect
    does not echo it)."""
    block = _header_block(header)
    if block is None:
        return None, None
    try:
        payload = json.loads(base64.b64decode(str(header)).decode())
    except Exception:
        return None, None
    payee = None
    try:
        las = block.get("link_as_account")
        las = las if isinstance(las, str) and las.startswith(("nano_", "xrb_")) else None
        if "link" in block:
            link = block.get("link")
            signed = None
            if isinstance(link, str) and len(link) == 64:
                signed = address_from_public_key(bytes.fromhex(link))
            if signed is not None and (las is None or _same_payee(signed, las)):
                payee = las or signed
        else:
            payee = las
    except Exception:
        payee = None
    amount = None
    try:
        accepted = payload.get("accepted")
        if isinstance(accepted, dict):
            for field in ("amount", "maxAmountRequired", "max_amount_required"):
                if field in accepted:
                    amount = int(accepted[field])
                    break
    except Exception:
        amount = None
    return payee, amount


def _header_block(header):
    """The block dict inside a stored payment header, or None."""
    try:
        payload = json.loads(base64.b64decode(str(header)).decode())
        block = payload["payload"]["block"]
        return block if isinstance(block, dict) else None
    except Exception:
        return None


def _raw_digits(value) -> Optional[int]:
    """A raw amount written as a plain decimal-digit string, else None. Rejects
    what `int()` would also take - signs, spaces, underscores, bools, floats."""
    if not isinstance(value, str) or not value or not value.isascii() or not value.isdigit():
        return None
    return int(value)


def _amount_from_ledger(block, rpc) -> Optional[int]:
    """The amount a journalled send block pays, from the ledger: the balance of
    the block it follows (`previous`, which this wallet signed) minus its own
    signed `balance`. feeless402 keys the journal on the offer's amount, which
    is the amount it signed, so this is that amount. The NanoGPT dialect does
    not echo the offer in the header, so this is the only way to read it.

    The node's answer is not trusted: the previous block's `contents` are
    hashed here, with feeless402's own state-block hash, and must hash to
    `previous` - the hash this wallet signed into the journalled block. The
    balance is read only from those contents (never the reply's top-level
    `balance`, which must agree with them), and their `account` must be the
    journalled block's own. So a node that answers wrongly, by mistake or on
    purpose, gets None, not a wrong amount. None whenever the amount cannot be
    read that way: no `previous`, `account` or `balance` in the journalled
    block, no answer, an RPC error, contents that do not hash to `previous`,
    another account's block, or a non-positive difference.

    The call is one `block_info` per matching entry, made while the instance
    lock is held, and may take up to the RPC's own timeout (per node it fails
    over to) before the tool answers."""
    if rpc is None or not isinstance(block, dict):
        return None
    try:
        prev = str(block.get("previous") or "").upper()
        balance = _raw_digits(block.get("balance"))
        account = block.get("account")
        if balance is None or not account:
            return None
        if len(prev) != 64 or not prev.strip("0"):
            return None
        bytes.fromhex(prev)
        info = rpc.call({"action": "block_info", "json_block": "true", "hash": prev})
        if not isinstance(info, dict):
            return None
        contents = info.get("contents")
        if not isinstance(contents, dict):
            return None
        if not _same_payee(contents.get("account"), account):
            return None
        prev_balance = _raw_digits(contents.get("balance"))
        if prev_balance is None:
            return None
        # A node that contradicts the contents it returns is not believed at all.
        if "balance" in info and _raw_digits(info.get("balance")) != prev_balance:
            return None
        if "block_account" in info and not _same_payee(info.get("block_account"), account):
            return None
        hashed = _state_block_hash({
            "account": normalise_address(str(contents["account"])),
            "representative": normalise_address(str(contents["representative"])),
            "balance": str(prev_balance),
            "previous": str(contents["previous"]),
            "link": str(contents["link"]),
        })
        if str(hashed).upper() != prev:
            return None
        amount = prev_balance - balance
        return amount if amount > 0 else None
    except Exception:
        return None


def _journal_live(wallet) -> list:
    """Every live (unexpired) journal entry, as dicts with the journal key, the
    block hash, the entry's method/url/time and the block's payee and amount.
    Empty when there is no journal or it cannot be read."""
    path = _journal_path(wallet)
    try:
        if not path.is_file():
            return []
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return []
    except Exception:
        return []
    ttl = _journal_ttl()
    now = time.time()
    out = []
    for key, entry in data.items():
        try:
            if not isinstance(entry, dict):
                continue
            t = float(entry.get("t", 0))
            # feeless402's own liveness test, verbatim: `now - t < TTL`. A NaN
            # `t` is dead to it (every comparison with NaN is False) and an
            # infinite or far-future `t` is live, so the same holds here.
            if not (now - t < ttl):
                continue
            payee, amount = _journalled_block(entry.get("header"))
            out.append({
                "block": _header_block(entry.get("header")),
                "key": str(key), "hash": str(entry.get("hash") or "").upper(),
                "method": str(entry.get("method", "")).upper(), "url": str(entry.get("url")),
                "t": t, "payee": payee, "amount": amount, "path": str(path),
            })
        except Exception:
            continue
    return out


def _could_be_re_presented(entry: dict, method: str, url: str, req_kwargs: dict, max_raw: int,
                           rpc=None) -> bool:
    """Could feeless402 re-present `entry` for this request?

    It does when the paying read's key - (METHOD, url, pay_to, amount, body
    fingerprint) - is the entry's key, and only after refusing an amount above
    `max_raw` (it raises PriceCapExceeded before it reads the journal, in every
    version that has one). The pay_to is the block's own; the amount is the one
    the header echoes (x402 v2) or, in the NanoGPT dialect, which echoes none,
    the one the ledger shows the signed block pays (`_amount_from_ledger`); the
    key is recomputed with feeless402's own key functions. An entry whose key
    does not come out (another JSON body, say) is never re-presented for this
    request; one above the price authorised here is refused by feeless402
    before it looks. An entry whose amount or payee cannot be read, or a
    feeless402 without `_journal_key` and `_request_fingerprint` (before
    0.2.12, whose key leaves the body out), cannot be ruled out: it counts.
    """
    if entry["method"] != method.upper() or entry["url"] != url:
        return False
    payee, amount = entry["payee"], entry["amount"]
    if amount is None:
        amount = _amount_from_ledger(entry.get("block"), rpc)
    if amount is not None and amount > max_raw:
        return False
    key_fn = getattr(_x402_module, "_journal_key", None)
    fp_fn = getattr(_x402_module, "_request_fingerprint", None)
    if payee is None or amount is None or key_fn is None or fp_fn is None:
        return True
    try:
        fingerprint = fp_fn(dict(req_kwargs))
        tail = payee[payee.index("_") + 1:]
        spellings = {payee, "nano_" + tail, "xrb_" + tail}
        return any(key_fn(method, url, s, amount, fingerprint) == entry["key"] for s in spellings)
    except Exception:
        return True


def _format_journalled_elsewhere_refusal(authorised: str, pending: list) -> str:
    ttl = _journal_ttl()
    lines = [
        "REFUSED: a payment for this same request is already signed to a DIFFERENT payee.",
        f"  you authorised:        {authorised}",
    ]
    for e in pending:
        try:
            expires = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(e["t"] + ttl))
        except Exception:
            # An infinite or far-future `t` (live to feeless402) has no date.
            expires = "unknown"
        lines.append(f"  pending signed block:  {e['hash']} to {e['payee']}")
        lines.append(f"    journal file:        {e['path']}")
        lines.append(f"    journal entry:       \"{e['key']}\" (expires {expires})")
    lines.append(
        "Nothing new was signed and nothing was sent. feeless402 keeps that earlier "
        "block in its payment journal and would re-present it, unchecked, if the "
        "merchant names that payee again - and it may already be on the ledger."
    )
    lines.append(
        "  agent:     do NOT pay again and do NOT edit the journal; report this to "
        "your operator with the block hash above."
    )
    lines.append(
        "  operator:  look the block hash up on the ledger. If it landed, the money "
        "went to that payee: settle it with the merchant. Either way, to let this "
        "request be paid again, remove only the journal entry named above from the "
        "journal file (a JSON object; delete that one key), or wait until it expires."
    )
    return "\n".join(lines)


def _format_unsigned_block(resp, receipt: dict, cap_xno: str, authorised: str,
                           actual: Optional[str], source: str, mandated: bool) -> str:
    """A receipt for a block this call did not sign, whose payee is either not
    the authorised one (`actual`) or could not be confirmed (`actual` None)."""
    settled = receipt.get("settled")
    state = {True: "the ledger HOLDS this block - money moved",
             False: "the ledger does not hold this block"}.get(
        settled, "verdict indeterminate - check the block hash")
    if actual is not None:
        lines = [
            "PAYEE MISMATCH (Nano x402) - NOT a payment to the payee you authorised:",
            f"  authorised pay_to:   {authorised}",
            f"  block actually pays: {actual}  ({source})",
        ]
    else:
        lines = [
            "PAYEE UNVERIFIED (Nano x402) - this call did not sign the block it sent, "
            "and where it pays could not be confirmed; do NOT treat it as paid to the "
            "payee you authorised:",
            f"  authorised pay_to:   {authorised}",
            "  block actually pays: UNKNOWN - the signed block was not readable in "
            "feeless402's payment journal before, at or after the send",
        ]
        claimed = str(receipt.get("pay_to") or "")
        if claimed:
            lines.append(
                f"  reported pay_to:     {claimed}  (feeless402's record, which the "
                "merchant's payment-response can overwrite - not proof of the payee)"
            )
    lines += [
        f"  block:     {receipt.get('block')}",
        f"  amount:    {receipt.get('amount_xno')} XNO  (cap {cap_xno})",
        f"  settled:   {settled}  ({state})",
        f"  ledger:    {receipt.get('ledger')}",
        f"  status:    {resp.status_code}",
        "  why:       feeless402 re-presented a block signed in an EARLIER call (by "
        "this or another tool instance or process sharing this wallet) from its "
        "payment journal; it was not signed in this call, so this tool's payee pin "
        "never checked it.",
    ]
    if mandated:
        lines.append(
            "  mandate:   this block was NOT checked against your operator's mandate "
            f"allow-list in this call (the check ran against {authorised})."
        )
    lines.append(
        "  action:    do NOT pay again and do NOT treat this as paid to the authorised "
        "payee; look the block hash up on the ledger to see where it paid, and report "
        "it to your operator."
    )
    lines.append("  body:")
    try:
        body = resp.text
    except Exception:
        body = ""
    body = (body or "").strip()
    lines.append(body[:4000] if body else "  (empty response body)")
    return "\n".join(lines)

def _format_mandate_refusal(exc: MandateRefused) -> str:
    return (
        "REFUSED: your operator's mandate does not allow this payment.\n"
        f"  reason: {exc.reason}\n"
        f"  detail: {exc.message}\n"
        "Nothing was signed or paid. Only the operator can widen a mandate."
    )


def _format_mandate_unavailable(exc: BaseException) -> str:
    """A mandate that cannot be checked refuses, in text.

    `MandateGuard` raises `MandateRefused` for everything it can name, but it
    reaches its ledger through a plain `open()`: a ledger path whose directory
    is missing or unwritable raises `OSError` instead. That is still doubt, and
    doubt is a refusal - an unrecordable spend must not be spent. It must also
    not leave the tool as an exception: a refusal an agent cannot read is a
    refusal it cannot act on.
    """
    return (
        "REFUSED: your operator's mandate could not be checked, so nothing was paid.\n"
        "  reason: mandate_unavailable\n"
        f"  detail: {type(exc).__name__}: {exc}\n"
        "A mandate that cannot be read or recorded refuses every payment; it never "
        "falls back to uncapped. Nothing was signed or paid - fix the mandate or its "
        "ledger path, or ask your operator to."
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


def _format_price_moved_refusal(quoted_xno: str, detail: str) -> str:
    return (
        "REFUSED: the endpoint asked for more than it quoted.\n"
        f"  quoted and authorised: {quoted_xno} XNO\n"
        f"  detail: {detail}\n"
        "Nothing was signed and nothing was paid. Call dry_run=true again to "
        "re-preview the new offer and mint a fresh quote_token if you still want it."
    )


def _format_payee_moved_refusal(authorised: str, asked: str) -> str:
    return (
        "REFUSED: the endpoint changed where the money goes after it quoted.\n"
        f"  quoted and authorised: {authorised}\n"
        f"  asked to be paid:      {asked}\n"
        "Nothing was signed and nothing was paid. Call dry_run=true again to "
        "re-preview the new offer and mint a fresh quote_token if you still want it."
    )


def _format_unanswered_earlier_block(resp, cap_xno: str, earlier: list) -> str:
    """No receipt, no block built in this call, but feeless402's journal held a
    live block for this request before the call.

    feeless402 (0.2.13, `request_with_payment`) re-sends a journalled block; if
    the merchant answers 402 and the ledger does not hold the block within its
    wait, it drops the journal entry and recurses, and the recursive call returns
    `(response, None)` when its first unpaid read is not a 402. A signed block
    DID reach the merchant on that path and can still be broadcast, so this must
    never say that nothing was signed or sent.
    """
    hashes = sorted({e.get("hash") for e in earlier if e.get("hash")})
    lines = [
        "UNCONFIRMED (Nano x402) - a block signed in an EARLIER call for this request "
        "may have been re-sent; check it before paying again:",
        f"  status:    {resp.status_code}",
        f"  block:     {', '.join(hashes) if hashes else 'UNKNOWN - the earlier block hash could not be read'}"
        "  (signed in an earlier call, from feeless402's payment journal)",
        f"  cap:       {cap_xno} XNO",
        "  note:      no payment was requested on the final paying read and this call "
        "signed no new block, but feeless402's payment journal held a signed block for "
        "this request before the call; it may have been re-sent to the merchant and can "
        "still reach the ledger. Check that block hash on the ledger before paying again. "
        "The quote_token was used.",
        "  body:",
    ]
    try:
        body = resp.text
    except Exception:
        body = ""
    body = (body or "").strip()
    lines.append(body[:4000] if body else "  (empty response body)")
    return "\n".join(lines)


_HEX64 = re.compile(r"[0-9a-fA-F]{64}")


class _NotAWallet(ValueError):
    """A wallet file that parses as JSON but is not a wallet."""


def _redact_wallet_path(text: str, path) -> str:
    """Replace the wallet's full path spellings in `text` with its file name.

    Only whole path strings are replaced: never a bare "." or "/" (the parent of
    a relative or root-level path), which would mangle every dot and slash in
    the message. An absolute parent directory longer than "/" is replaced with
    "<wallet dir>" after the full paths are.
    """
    path = Path(path)
    name = path.name
    fulls, parents = set(), set()
    for spelling in (path, path.absolute()):
        fulls.add(str(spelling))
        parents.add(str(spelling.parent))
    try:
        resolved = path.resolve()
        fulls.add(str(resolved))
        parents.add(str(resolved.parent))
    except Exception:
        pass
    for full in sorted(fulls, key=len, reverse=True):
        if full and full not in (".", "/", name):
            text = text.replace(full, name)
    for parent in sorted(parents, key=len, reverse=True):
        if Path(parent).is_absolute() and len(parent) > 1:
            text = text.replace(parent, "<wallet dir>")
    return text


def _format_receipt(resp, receipt: dict, cap_xno: str, authorised_pay_to: str = "",
                    re_presented: bool = False, mandated: bool = False) -> str:
    """Render a redeem result with a truthful head line.

    Only a ledger-confirmed payment may be headed PAID. A block the ledger
    does not hold (settled False) or whose verdict is indeterminate must never
    read as paid: the block hash and verdict are always shown so a caller can
    check before ever paying again.

    `authorised_pay_to` is the payee THIS tool quoted, minted a token against
    and pinned `_PayeePinnedWallet` to, so it is the address any block built in
    this call was signed to. A block feeless402 re-presented from its journal is
    not built in this call; the redeem path sends that case through here only
    when the journalled signed block itself pays the authorised account
    (`re_presented=True`), and otherwise reports PAYEE MISMATCH or PAYEE
    UNVERIFIED instead.

    It is printed in preference to the receipt's own `pay_to`, which is the merchant's echo: feeless402 sets
    `base["pay_to"]` from its own ground truth and then merges the merchant's
    receipt fields over it (`nano_pay/x402.py:584`), whose exclusion list - the
    one its comment calls "never let them speak for ours" - lists `settled`,
    `block`, `amount_xno`, `amount_raw`, `note` and `ledger` but not `pay_to`,
    and re-asserts `amount_xno` and `block` afterwards but not `pay_to`. So a
    merchant that returns a `payment-response` header naming any address at all
    decided the one line of the record that says where the money went, in the
    field the payee pinning exists to guarantee. A merchant claim that differs
    is still shown, named as the merchant's and as untrusted.
    """
    if not receipt:
        # feeless402 returns (response, None) when the paying read is not a 402:
        # nothing was asked for, so nothing was signed or sent. There is no block,
        # so no payee may be named - printing the authorised one here read as a
        # payment to it.
        lines = [
            "NOT PAID - no payment was requested on the paying read:",
            f"  status:    {resp.status_code}",
            "  block:     none - nothing was signed or sent",
            "  note:      the endpoint answered without a 402 when the payment was "
            "due; the quote_token was used. Call dry_run=true again if it asks for "
            "payment later.",
            "  body:",
        ]
        try:
            body = resp.text
        except Exception:
            body = ""
        body = (body or "").strip()
        lines.append(body[:4000] if body else "  (empty response body)")
        return "\n".join(lines)
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
        # The authorised payee stands in only for a block this call reports: with
        # no block there is no signed payee to name - and the merchant's own
        # `pay_to` (which its payment-response can overwrite) is never printed
        # here as if it were where the money went.
        (f"  pay_to:    {authorised_pay_to or receipt.get('pay_to')}" if receipt.get("block")
         else "  pay_to:    none - no block was reported, so no payee is confirmed"),
        f"  block:     {receipt.get('block')}",
        f"  settled:   {receipt.get('settled')}",
        f"  ledger:    {receipt.get('ledger')}",
    ]
    claimed = str(receipt.get("pay_to") or "")
    if (authorised_pay_to and receipt.get("block") and claimed
            and not _same_payee(claimed, authorised_pay_to)):
        lines.append(
            f"  merchant claims pay_to: {claimed} - UNTRUSTED, and not where this "
            f"payment went; the block above was signed to {authorised_pay_to}"
        )
    elif claimed and not receipt.get("block"):
        lines.append(
            f"  merchant claims pay_to: {claimed} - UNTRUSTED; with no block there is "
            f"no signed payee to confirm it"
        )
    if re_presented:
        lines.append(
            "  re-sent:   this block was signed in an earlier call and re-presented "
            "from feeless402's payment journal; the signed block there pays the "
            "authorised account"
        )
        if mandated:
            lines.append(
                "  mandate:   your operator's mandate was NOT charged for this block in "
                "this call: it was signed in an earlier call, and whether the mandate "
                "was charged for it then is unknown here."
            )
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


def _format_failed_payment(exc: "PaidRequestFailed", cap_xno: str, authorised_pay_to: str = "") -> str:
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
    # Here `pay_to` is feeless402's own (no merchant receipt was merged in).
    paid_to = str(rec.get("pay_to") or "")
    if paid_to:
        lines.append(f"  pay_to:    {paid_to}")
    if authorised_pay_to and paid_to and not _same_payee(paid_to, authorised_pay_to):
        lines.append(
            f"  PAYEE MISMATCH: this block pays {paid_to}, NOT the payee you "
            f"authorised ({authorised_pay_to}); it was re-presented from an earlier "
            "call and never checked by this tool."
        )
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
        try:
            if not wallet.exists():
                wallet.create()
            else:
                wallet.load()  # an existing funded wallet must be loaded to sign
            # `load()` is only `json.loads`: `{}`, `[]` or a bad seed pass it, and
            # the first thing to read the seed used to be the redeem's signing
            # step - after a quote, a token, and the token consumed - failing as
            # "'seed'". Deriving the address here reads the seed and index now,
            # so such a file is the same configuration error as a corrupt one.
            data = getattr(wallet, "data", None)
            seed = data.get("seed") if isinstance(data, dict) else None
            index = data.get("index") if isinstance(data, dict) else None
            if not (isinstance(seed, str) and _HEX64.fullmatch(seed)
                    and isinstance(index, int) and not isinstance(index, bool) and index >= 0):
                # Never echo the seed: this text goes into the model's context.
                raise _NotAWallet(
                    "wallet file is not a wallet: expected a JSON object with a "
                    "64-hex 'seed' and a non-negative integer 'index'")
            wallet.address
        except Exception as e:
            # These three lines sat outside every guard in this function, and
            # outside the lock. `load()` is `json.loads(path.read_text())` and
            # `create()` is a mkdir plus a write, so a path that exists but is
            # not a usable wallet - a directory, a truncated or hand-edited file,
            # the wrong artefact pointed at by X402_WALLET_PATH - left the tool
            # as an exception. The Agents SDK renders that to the model as "An
            # error occurred while running the tool. Please try again.": an
            # unbounded retry that cannot ever succeed, with no reason given, and
            # the agent cannot even PREVIEW a price. It is the same defect class
            # as the `xno_to_raw` conversion below, one line further out. Nothing
            # is signed or broadcast on this path, so nothing can have been spent.
            # Only the file name: this text goes into the model's context, and the
            # operator who has to fix it knows where their wallet lives.
            name = wallet.path.name
            detail = _redact_wallet_path(str(e), wallet.path)
            return (
                f"ERROR: the wallet at {name} cannot be used "
                f"({type(e).__name__}: {detail}). Nothing was spent and no payment was "
                f"attempted. This is a configuration problem, not something to "
                f"retry: point X402_WALLET_PATH (or wallet_path=) at a wallet JSON "
                f"file, or at a path that does not exist yet so this tool can "
                f"create one."
            )
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
                    except Exception as e:
                        # Nothing is spent on a dry run, so the quote still stands -
                        # but it must not read as if the mandate had allowed anything.
                        text += (f"\n  mandate: could not be checked ({type(e).__name__}: {e});"
                                 " a redeem will refuse until this is fixed")
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
                except Exception as e:
                    # Fail closed: an unreadable mandate or an unusable ledger path
                    # never becomes an uncapped payment, and never an exception.
                    return _format_mandate_unavailable(e)
                pay_wallet = _MandatedWallet(wallet, guard, ref=f"{method} {url}")
            # The cap is checked BEFORE the token is consumed, for the same reason
            # the mandate is: a cap refusal signs nothing, broadcasts nothing and
            # spends nothing, so it must not cost the agent its preview. It used to
            # sit after `tokens.reject`, which consumes the token on success -- so a
            # redeem with too small a max_xno refused with
            #
            #     Nothing was paid. Raise max_xno (or the tool's default cap) if you
            #     intend to pay this endpoint.
            #
            # and doing exactly that, with the same token, answered
            #
            #     REFUSED: the quote token is invalid or already used.
            #
            # The tool's own instruction could not be followed. Single-use still
            # means single-use: the token is consumed only on the path that reaches
            # a signature, and an offer that has not been paid stays redeemable
            # until its TTL, which is what a preview is for.
            price_raw = int(quote.get("amount_raw") or 0)
            if price_raw > cap_raw:
                return _format_cap_refusal(raw_to_xno(price_raw), cap_xno)

            authorised = str(quote.get("pay_to") or "")
            # A block feeless402 could re-present for THIS request (same method,
            # URL and body, an amount within the price authorised here) that pays
            # another account would be sent without ever reaching the pins below.
            # Refuse before anything is sent; like the cap refusal, it costs no
            # token. Entries for another body or above this price are never
            # re-presented here, so they do not refuse (with feeless402 0.2.12 or
            # later; older versions leave the body out of the key, so an entry
            # for another body could be re-presented and still refuses). A
            # NanoGPT-dialect entry's amount is read from the ledger, so this
            # runs off the event loop.
            journal_before = _journal_live(wallet)
            elsewhere = await asyncio.to_thread(
                lambda: [e for e in journal_before
                         if e["payee"] is not None and not _same_payee(e["payee"], authorised)
                         and _could_be_re_presented(e, method, url, req_kwargs, price_raw, rpc)])
            if elsewhere:
                return _format_journalled_elsewhere_refusal(authorised, elsewhere)

            reason = tokens.reject(quote_token or "", quote.get("pay_to") or "", quote.get("amount_raw") or 0)
            if reason is not None:
                return _format_refusal(reason)

            # Pay at most the amount that was just quoted and authorised, not the
            # operator's whole cap. request_with_payment RE-READS the 402 and signs
            # whatever that read says, comparing it against the max_raw given here --
            # so handing it cap_raw let a seller quote cheap on both dry runs, raise
            # the price on the paying read, and be paid anything up to the cap. The
            # quote_token check just above binds pay_to and amount, but against OUR
            # read, never against the amount finally signed, so it did not catch
            # this: previewed 0.001 XNO, signed 0.009 XNO, reported "PAID".
            # price_raw is never looser than cap_raw -- the check above guarantees
            # price_raw <= cap_raw -- so this only narrows what is accepted.
            # The amount the paying read may charge is pinned above (price_raw).
            # The payee is pinned here, at the only moment that is the real one:
            # the block being built. request_with_payment compares the amount of
            # its own read against max_raw and compares the payee against nothing,
            # so a seller could quote one address on both dry runs and name another
            # on the paying read for the same money. This only narrows what is
            # signed - the address allowed is exactly the one just quoted and
            # authorised, and it is checked outside the mandate proxy so a moved
            # payee refuses before the mandate ledger reserves anything.
            pay_wallet = _PayeePinnedWallet(pay_wallet, quote.get("pay_to") or "")
            pinned = pay_wallet
            try:
                resp, receipt = await asyncio.to_thread(
                    request_with_payment,
                    method, url, pay_wallet, rpc, price_raw,
                    headers={"x-x402": "true"},
                    dry_run=False,
                    **req_kwargs,
                )
            except _PayeeMoved as e:
                # Raised while building the block: nothing was signed.
                return _format_payee_moved_refusal(e.authorised, e.asked)
            except MandateRefused as e:
                # Raised while building the block: nothing was signed.
                return _format_mandate_refusal(e)
            except PriceCapExceeded as e:
                # The paying read asked for more than was quoted and authorised.
                # feeless402 refuses before building a block, so nothing was signed.
                return _format_price_moved_refusal(raw_to_xno(price_raw), str(e))
            except PaidRequestFailed as e:
                # A signed block is in the merchant's hands with no reply: the
                # money may have moved. Never swallow this into a generic
                # "failed" that invites a blind re-pay.
                return _format_failed_payment(e, cap_xno, authorised_pay_to=authorised)
            except Exception as e:
                return f"ERROR: payment or request failed: {e}"
            if not receipt and pinned.built == 0:
                # No receipt and no block built here. If feeless402's journal held a
                # live block for THIS request before the call (or at the send), it may
                # have re-sent it, been answered 402, dropped the entry and recursed
                # into an unpaid read that was not a 402: a signed block reached the
                # merchant, so "nothing was signed or sent" would be false.
                seen = list(journal_before) + list(pinned.seen_at_send)
                earlier = await asyncio.to_thread(
                    lambda: [e for e in seen
                             if _could_be_re_presented(e, method, url, req_kwargs, price_raw, rpc)])
                if earlier:
                    return _format_unanswered_earlier_block(resp, cap_xno, earlier)
            receipt = receipt or {}
            block_hash = str(receipt.get("block") or "").upper()
            if pinned.built == 0 and receipt:
                # This call did not sign the block it sent: feeless402 re-presented
                # a stored one, so neither the pin nor the mandate proxy saw it. The
                # journal entry may have been there before the check above, or been
                # written since by another tool instance or process sharing this
                # wallet (the lock above is per tool instance). Its payee is only
                # taken from the payer's own record of the signed block - the
                # journal as read before, at and after the send, matched by the
                # block hash feeless402 reports (which the merchant cannot
                # overwrite). Never from the receipt's `pay_to`, which the
                # merchant's payment-response can overwrite. Unconfirmed is never
                # reported as paid to the authorised payee.
                actual = None
                views = (journal_before, pinned.seen_at_send, _journal_live(wallet))
                for view in views:
                    for e in view:
                        if block_hash and e["hash"] == block_hash and e["payee"] is not None:
                            actual = e["payee"]
                            break
                    if actual is not None:
                        break
                if actual is None or not _same_payee(actual, authorised):
                    return _format_unsigned_block(resp, receipt, cap_xno, authorised, actual,
                                                  "the signed block in this wallet's payment journal",
                                                  bool(mandate_file))
                return _format_receipt(resp, receipt, cap_xno, authorised_pay_to=authorised,
                                       re_presented=True, mandated=bool(mandate_file))
            return _format_receipt(resp, receipt, cap_xno, authorised_pay_to=authorised)

    return _nano_x402_fetch


__all__ = ["make_nano_x402_tool", "QuoteTokenStore", "NanoX402ToolError", "MandateGuard", "MandateRefused"]