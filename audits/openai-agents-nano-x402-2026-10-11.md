# openai-agents-nano-x402 — audit 2026-10-11

Previous audit 2026-10-10. Audited at `892e019` (`main` after #22).
Lens: can an agent PAY in XNO with this today without being hurt — paying more
than it authorised, paying somebody else, being told it paid when it did not, or
being left with an exception it cannot read.

**One payee defect found and fixed in `tool.py`; one claim about the mandate
ledger corrected.** The first draft of this audit concluded "nothing to change".
An independent review showed that was wrong; this version says what was found
and what changed.

The suite as CI runs it, from a clean venv: `pip install -e '.[dev]'`, then
`python3 -m pytest tests/ -q --tb=short`: **295 passed, 0 skipped** (289 before
this change, plus the 6 tests in `tests/test_journal_replay_payee.py`). `[dev]`
installs the official `x402` SDK, so the four `x402_sdk` laws that skip under a
bare `pip install -e .` run here. `ruff check .` (CI's lint step) is clean.

## Found and fixed

- **A block feeless402 re-presented from its payment journal bypassed the payee
  pin, and the tool reported it as paid to the authorised payee.** (MEDIUM)
  feeless402 0.2.13 journals every signed block beside the wallet
  (`pending-payments.json`), keyed by (method, url, pay_to, amount, body). When
  the paying read names a (pay_to, amount) that has an entry,
  `request_with_payment` re-sends the stored block **without calling
  `wallet.build_payment_block`** (`nano_pay/x402.py` ~463-472), so neither
  `_PayeePinnedWallet` nor `_MandatedWallet` was consulted. With a block to B
  journalled by an earlier redeem the merchant never answered, a preview quoting
  A and a paying read naming B for the same amount re-presented the block to B,
  and the tool printed `PAID`, `pay_to: A`, and called B an "UNTRUSTED merchant
  claim ... the block above was signed to A" — the opposite of the truth. Under
  a mandate, the allow-list check had run against A only.

  `tool.py` now:
  - reads the journal before the paying request (read-only, as a file:
    feeless402 has no API for it, and nothing in feeless402 is patched) and
    **refuses before anything is sent** when a live entry for the same method and
    URL holds a block whose `link_as_account` is not the authorised payee. The
    refusal names that block hash and payee and tells the agent not to pay again.
  - after the payment, counts the blocks the pinned wallet actually built. If it
    built none and the journal held an entry for this request, the block was
    re-presented. Its payee is taken from the journalled block, or failing that
    from feeless402's reported `pay_to`. If that is not the authorised payee, the
    result is headed **PAYEE MISMATCH**. It names the address actually paid,
    says that address is not the authorised payee, and, under a mandate, says
    the block was not checked against the allow-list in this call. It is never
    headed PAID and never says "signed to A".
  - on a re-presentation the merchant does not answer (`PaidRequestFailed`),
    prints feeless402's `pay_to` and flags a mismatch the same way.

  Re-presenting the same block to the same payee is the journal doing its job,
  and still reads PAID. `tests/test_journal_replay_payee.py` drives the real
  `request_with_payment` and its real journal; only the network, the node and
  the signature are stubbed. Its four mismatch tests fail on the previous
  `tool.py`, and its two controls pass on both versions. Limitation: a second
  process writing the same journal between the tool's read and the send is not
  covered.

## Corrected claims

- **A float in the mandate ledger.** The first draft said a float on either side
  of the ledger total is `ledger_corrupt`. Only `spent_raw` is digit-checked
  (`mandate.py` `_read`). Each `payments[*].amount_raw` goes through `int()`, so
  `5.0`, `5.9` and `true` are accepted as 5, 5 and 1 when `spent_raw` matches.
  Reaching this needs write access to the operator's ledger file, which already
  allows resetting the ledger outright, so it does not widen what an agent or a
  merchant can do. It is not changed here: `mandate.py` is a byte-for-byte
  vendored copy, pinned by SHA-256 (`VENDORED_SHA256` in
  `tests/test_mandate.py`) and shared with two other repositories, to be bumped
  only together. The fix (digit-check `amount_raw` the way `spent_raw` is
  checked) belongs in that shared source.
- **`_verify_signed_block`** makes one integer check, not four: the balance,
  which gives the amount sent, compared exactly with the quote. Its other checks
  are the block type, the `previous` frontier, the `link` payee, and the
  signature and work formats.
- **`10 ** 30`.** The only occurrence of that literal is `mandate.RAW_PER_XNO`.
  `10**30` also appears in docstrings and comments in `mandate.py` and
  `x402_sdk.py`, none of them arithmetic.

## What I checked, end to end

- **`tool.py`'s whole redeem path, in order:** the wallet-load guard (an
  unusable wallet is text, not an exception), `_apply_cap`'s refusals of a
  non-finite, non-numeric or negative cap on either side,
  `xno_to_raw(cap_xno)` inside the same `except ValueError`, the spendless dry
  run, the mandate pre-check, the cap check **before** the token is consumed,
  `QuoteTokenStore.reject`'s four refusals (missing, invalid-or-used, expired,
  offer-changed), and then the two pins: `price_raw` as the maximum the paying
  read may charge, and `_PayeePinnedWallet` refusing to sign to any address but
  the one just quoted. Both only narrow, and both sit outside the mandate proxy,
  so a moved payee refuses before the ledger reserves anything. Neither pin
  applies to a block feeless402 re-presents from its journal, which is the defect
  fixed above.
- **Every exit from that path is agent-readable text**, including
  `PaidRequestFailed` — which surfaces the signed block hash and tells the
  caller to re-present the same block rather than pay again blind — and
  `_format_receipt`, which heads a block the ledger does not hold as **NOT
  PAID**, an indeterminate verdict as **UNCONFIRMED**, and prints the payee this
  tool authorised in preference to the merchant's echo.
- **`mandate.py`:** `parse_raw` (bool and float refused, decimal-integer strings
  only, bounded by `2**128-1`), `xno_to_raw`/`raw_to_xno` (integer arithmetic on
  the digit string, no float), `validate_fields`, `verify_signed`, the ledger's
  `_read`/`_write`/`_check`/`spend`, and `status`.
- **`x402_sdk.py`:** `parse_raw_amount` refusing a decimal rather than scaling it
  (the 10**30 misreading), `_xno_to_raw_exact`'s constant-time magnitude check
  before any integer is built, `normalize_payee`'s `xrb_` handling, and
  `_verify_signed_block`'s checks on the signed block before it is handed over
  (type, frontier, payee link, the one integer check on the balance, and the
  signature and work formats).
- **The first step a new agent takes.** The two install URLs the README puts
  first both answer `200`:
  `.../releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl` and
  the sdist beside it. `pip install -e '.[dev]'` and the full suite are what this
  audit ran.

## Specific things I went looking for and did not find

- **A float on an amount.** None anywhere in `src/`: the only `10 ** 30` literal
  is `mandate.RAW_PER_XNO`, and `_refuse_float` is wired into `load_signed`'s
  `json.load`, so a non-integer number in a mandate file is refused by name. (A
  float in the mandate *ledger* is covered under "Corrected claims" above.)
- **A verification that trusts the payer or the merchant.** The amount and payee
  are pinned against this tool's own quote. The merchant's receipt `pay_to` is
  printed as untrusted and named as such when it differs. The one path that
  skipped the payee pin, a journalled block re-presented by feeless402, is the
  defect fixed above.
- **Input reaching a shell or a path.** No `subprocess`, `os.system`, `eval`,
  `exec` or `shell=` in `src/`. The only paths opened are the wallet, the
  feeless402 journal beside it (read-only), the mandate and its ledger, all
  operator-supplied.
- **A secret in the tree or in history.** None. `secrets` is the stdlib module,
  used for the quote token and the mandate nonce; `_write_private` creates key
  files `O_EXCL` at `0o600`.

## Could not verify

- **No live payment of our own.** No XNO moved in this run; every case is
  measured against stubs. The README's live proof (block `E67FB894…57FC3`,
  0.00001292 XNO to NanoGPT, 2026-09-18) is unchanged and was not re-paid.
- **`feeless402.com`** is unreachable from this session — the egress proxy
  refuses the CONNECT (`403`), not a 404 — so the README's link to it could not
  be checked either way.
- **Everything the v0.1.0 wheel does not carry** (the mandate guard, the
  official-SDK client, the cap checks) is documented in the README's own "What
  v0.1.0 does not include"; that section still matches the released wheel's
  contents, and the fix for it is a release, which is the owner's to cut. The
  journal check added here is not in v0.1.0 either and is not yet listed there.
