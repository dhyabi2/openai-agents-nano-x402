# openai-agents-nano-x402 - audit 2026-10-03

Lens: can an OpenAI Agents SDK agent pay an x402 endpoint in XNO through this tool, today,
without being hurt. Last audited 2026-09-30, so this is the first pass since #9 and #11.

## Checked

- Install and suite from a clean virtualenv (`pytest`, `openai-agents`, `feeless402`):
  **85 passed** on `main`, **89 passed** with this change.
- `tool.py`'s payment path end to end: `_apply_cap`, the dry-run preview, `QuoteTokenStore`
  mint/reject, the cap check, `_MandatedWallet.build_payment_block`, and every refusal
  formatter.
- Amount handling. No float touches an amount anywhere in `src/` - the only `float` in the
  package is `QuoteTokenStore.ttl_s`, a clock value, and `mandate.py:506` is a
  `_refuse_float` guard. Raw is integer throughout.
- `_MandatedWallet`, which is the good pattern in this repository and worth keeping: it wraps
  the wallet rather than the request, so the mandate guard sees the payee and amount
  **at the moment the block is built** - the ones actually being signed - and not the ones the
  tool happened to read. `tests/test_tool_mandate.py::test_payee_switched_after_the_preview_is_refused_at_signing`
  pins it.
- `PaidRequestFailed` is never swallowed into a generic failure, so a signed block with no
  reply is reported as such instead of inviting a blind re-pay. Correct, and the hard case.
- Secret scan of the tree and of `git log --all -p`: no seed, private key or API key. The
  64-hex matches are content hashes in `.ledger/cache.json` (a judge cache) and lockfile
  integrity digests. Clean.
- The README's own honesty about the v0.1.0 wheel, landed by #11, still holds: it says
  plainly that the published wheel carries `__init__.py` and `tool.py` only, so
  `mandate keygen` is not a command after that install and
  `make_nano_x402_tool(mandate_path=...)` raises `TypeError`.

## Found and fixed - the agent could pay nine times what it previewed

`request_with_payment` **re-reads the 402 before it signs** and compares that read against the
`max_raw` it is handed (`nano_pay/x402.py`: `if amount > max_raw: raise PriceCapExceeded`).
The tool handed it `cap_raw` - the operator's whole cap - rather than the amount that had just
been quoted and authorised. So a seller could quote cheap on both dry runs and raise the price
on the paying read, and be paid anything up to the cap.

The `quote_token` looks like the defence against exactly this, and is not: it binds `pay_to`
and `amount_raw`, but `tokens.reject(...)` is checked against **the tool's own second read**,
never against the amount finally signed. Nor does the mandate close it in general - the guard
checks the per-payment max and the remaining cap, not the quoted price - and with no mandate
configured nothing checks it at all.

Reproduced with no mandate, `default_max_xno="0.01"`, a seller quoting 0.001 XNO and asking
0.009 XNO once it was time to pay:

```
preview quoted: 0.001 XNO
   seller now asks 0.009 XNO; max_raw it was handed = 0.01 XNO
result: PAID (Nano x402):
blocks actually signed: [('nano_1p7c...coa5', '0.009')]
```

Nine times the previewed price, signed, settled, and reported as `PAID`.

Fixed by passing `price_raw` - the amount just quoted and authorised - as the payer's ceiling.
**This only narrows what is accepted:** the existing check immediately above guarantees
`price_raw <= cap_raw`, so the new ceiling is never looser than the old one, and no amount,
destination, rounding or key path changes. `PriceCapExceeded` is now caught and rendered as a
refusal that says what happened, rather than falling through to a generic
`ERROR: payment or request failed`. After the fix the same seller gets:

```
REFUSED: the endpoint asked for more than it quoted.
  quoted and authorised: 0.001 XNO
  detail: quote 0.009 XNO exceeds cap 0.001 XNO - refusing to pay
Nothing was signed and nothing was paid.
blocks signed: []
```

`tests/test_price_moved_after_preview.py` has four laws: the raise is refused with nothing
signed; the ceiling handed to the payer is the quoted amount and not the operator cap (so a
later edit cannot quietly widen it back); an unchanged offer still pays; and a price **cut**
after the preview is still paid, because a ceiling is a ceiling. The first two fail on
unmodified `main` and all four pass with the fix.

## Needs the owner

The published **v0.1.0 wheel ships `tool.py`**, and therefore ships this defect. The README
tells readers to install that wheel as "the immutable, public install path (works today)".
Anyone who followed it can be overcharged up to their configured cap by a seller that moves
its price between the preview and the payment. Closing that needs a new release, which is the
owner's: a routine does not publish a package.

## Could not verify

- No live x402 endpoint, no node and no XNO: `request_with_payment` is replaced by a fake
  whose signature and cap check mirror the real one, and the wallet's block builder is
  replaced so every block that would have been signed is counted instead.
- The real `feeless402` behaviour is read from its installed source
  (`nano_pay/x402.py`'s re-read, `PriceCapExceeded`, and the five-positional signature
  `(method, url, wallet, rpc, max_raw, ...)`), not observed against a live seller.
- Whether any endpoint in the wild actually moves its price between reads. The defect is that
  nothing here would stop one, not that one was caught doing it.
