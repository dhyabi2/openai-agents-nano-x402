# openai-agents-nano-x402 — audit, 2026-10-14

Lens: can an agent pay in XNO with this, today, without being hurt?

**Result: nothing to fix.** No pull request beyond this note. What follows is
what was checked and how, so the next run does not repeat it.

## Checked

**Suite.** `pip install -e '.[dev]'` then `python -m pytest -q` — **421 passed**
in 53 s, on the current `main` (`0a46f4f`). Nothing skipped for a missing
optional dependency: `x402>=2.22` is in the `dev` extra precisely so the
`x402_sdk` laws run against a real `x402Client` rather than skipping.

**`x402_sdk.py`, all 462 lines.** The client-side `exact` mechanism on
`nano:mainnet`.
- `parse_raw_amount` refuses a decimal rather than scaling it, which is the
  right call: on this network the wire `amount` is raw, and a payer that reads
  `"0.01"` as XNO overpays by 10**30. The refusal names the raw figure the
  seller probably meant, and the hint itself is computed exactly.
- `_xno_to_raw_exact` places digits by integer arithmetic on the decimal tuple
  instead of multiplying, so the ambient `decimal` precision of 28 cannot round
  a 39-digit raw amount. The magnitude is bounded with `adjusted()` *before* any
  integer is built, so a seller-chosen exponent (`1e20000000`) cannot make the
  payer construct a 20-million-digit power of ten. Both are correct and both are
  load-bearing.
- `_verify_signed_block` re-checks the signed block against the quote while it
  can still be thrown away: state type, `previous` equal to the frontier that
  was read (so a receive landing mid-sign refuses rather than spending from an
  unchecked balance), `link` decoding to exactly the quoted `payTo`, and
  `observed_balance - balance == amount_raw`. All integer comparisons on raw.
- Self-payment, cap, scheme, network and asset are all refused in `_check_quote`
  before signing.

**`tool.py`, all 1209 lines.** The two-phase Agents SDK tool.
- The amount the paying read may charge is pinned to `price_raw` (the quoted
  figure), not `cap_raw`. This matters: `request_with_payment` re-reads the 402
  and compares only against the max it is handed, so passing the operator's cap
  would let a seller quote cheap twice and charge up to the cap on the paying
  read.
- The payee is pinned by `_PayeePinnedWallet` at the moment the block is built,
  which is the only moment that is the real one, and outside the mandate proxy
  so a moved payee refuses before the ledger reserves anything.
- feeless402's payment journal is read before, at and after the send, and a
  block it could re-present to a different payee refuses before anything is
  sent. A re-presented block is never headed `PAID` unless the journalled block
  itself pays the authorised account; the merchant's own `pay_to` echo is
  printed only as untrusted, because feeless402 merges the merchant's receipt
  fields over its own and `pay_to` is not on its exclusion list.
- Only a ledger-confirmed payment is headed `PAID`; `settled` False and
  indeterminate each get their own headline, and every one shows the block hash.
- Cap and mandate are both checked *before* the quote token is consumed, so a
  refusal does not cost the agent its preview — and the token is still
  single-use on the path that reaches a signature.
- `_apply_cap` validates both sides (NaN, infinity, negative, non-numeric) and
  the `xno_to_raw` conversion is inside the same guard, so a model-supplied
  `max_xno` of `"1e-40"` refuses in text instead of leaving the tool as an
  exception the SDK renders as an unbounded retry.
- A wallet file that is not a wallet is caught before a quote is ever read, and
  the message carries only the file's name — never the seed, never the path.

**`mandate.py`, all 828 lines.** The operator-signed spend cap.
- `verify_signed` checks shape (exactly `{mandate, hash, signature}`), every
  field, the hash, the operator's signature over a canonical message, the agent,
  `issued_at` and `expires_at`. `validate_fields` refuses unknown fields rather
  than ignoring them.
- The Ed25519-blake2b `verify` is hand-rolled, so it was read line by line
  against RFC 8032: lengths are checked, `_decode_point` rejects a non-residue
  (it tests `x*x == xx` after the `_I` correction) and `y >= _Q`, `s >= _L` is
  rejected so a malleable signature cannot be re-spelled, and the verification
  equation is the strict non-cofactored form. `load_signed` refuses a float or a
  JSON constant anywhere in the file via `parse_float`/`parse_constant`.
- `parse_raw` refuses floats and bools outright and bounds amounts to
  `2**128-1`; the ledger refuses to spend when its totals do not add up, when it
  belongs to another mandate, or when it cannot be read; and `spend` reserves
  *before* calling `send` and marks the entry `unknown` (not rolled back) if
  `send` raises, so a cap cannot be overrun by a payment whose outcome is
  unknown.

**The amount path, probed rather than assumed.** `_apply_cap` returns a
`Decimal` whose `str()` is handed to feeless402's `xno_to_raw`, and `Decimal`
switches to scientific notation below 1e-6 — so `str()` yields `"1E-7"`, not
`"0.0000001"`. I checked whether that is read correctly: for `1E-7`, `1E-8`,
`1e-7`, `0.000001`, `1E+2` and `0.01`, `xno_to_raw(str(cap))` equals
`int(Decimal(s) * 10**30)` exactly in every case. No mismatch, no float.

## Found

Nothing. No defect proved on the XNO path, no secret in the tree, no README
claim the code does not support, no test asserting the wrong thing.

## Could not verify

- **Two README links, because of this session's own network policy — not
  because they are broken.** `https://feeless402.com` is refused by the agent
  proxy at `CONNECT` (`403`), and `https://github.com/feeless402/feeless402`
  returns `403` from this session's GitHub scoping layer, which answers `403`
  for *any* repository not configured here — a repository known not to exist
  returns the same `403`, so the method cannot distinguish existence at all.
  Neither result is evidence of a 404. The four links that could be checked are
  live: both PyPI projects (`x402`, `x402-nano-exact`), this repository, and the
  v0.1.0 wheel asset in its own releases (`200`).
- The live payment path. Nothing here was run against a real node, a funded
  wallet or a real seller; the suite is offline by construction.
- feeless402's own internals are taken as correct where this adapter reuses
  them. What was checked is the adapter's behaviour *around* them — the pins,
  the journal reads and the block re-verification — which is where this package's
  defects would live.

## Left alone deliberately

- `QuoteTokenStore` prunes an expired token only when that token is presented
  again, so a long-lived tool that previews often grows its dict without bound.
  It is a resource matter, not a payment defect, and this role does not optimise.
- `settled()` / `not_settled()` touch `self._pending` outside the instance lock.
  The module docstring already reasons the cost: a lost or crossed
  acknowledgement leaves a stale cached work value, not a wrong payment.
