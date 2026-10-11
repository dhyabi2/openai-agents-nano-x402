# openai-agents-nano-x402 — audit 2026-10-11

Previous audit 2026-10-10. Audited at `892e019` (`main` after #22).
Lens: can an agent PAY in XNO with this today without being hurt — paying more
than it authorised, paying somebody else, being told it paid when it did not, or
being left with an exception it cannot read.

**Nothing found worth changing. No code change in this pull request.**

`python3 -m pip install -e .` from a clean interpreter, then
`python3 -m pytest -q`: **285 passed, 4 skipped** (the four skips are the
`x402_sdk` laws that want the official `x402` SDK installed, which this session
does not carry; they are skips by design and the module's own tests cover the
same shapes).

## What I checked, end to end

- **`tool.py`'s whole redeem path, in order:** the wallet-load guard (an
  unusable wallet is text, not an exception), `_apply_cap`'s refusals of a
  non-finite, non-numeric or negative cap on either side,
  `xno_to_raw(cap_xno)` inside the same `except ValueError`, the spendless dry
  run, the mandate pre-check, the cap check **before** the token is consumed,
  `QuoteTokenStore.reject`'s four refusals (missing, invalid-or-used, expired,
  offer-changed), and then the two pins that matter: `price_raw` as the maximum
  the paying read may charge, and `_PayeePinnedWallet` refusing to sign to any
  address but the one just quoted. Both only narrow, and both sit outside the
  mandate proxy so a moved payee refuses before the ledger reserves anything.
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
  `_verify_signed_block`'s four integer checks on the signed block before it is
  handed over.
- **The first step a new agent takes.** The two install URLs the README puts
  first both answer `200`:
  `.../releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl` and
  the sdist beside it. `pip install -e .` and the suite are what this audit ran.

## Specific things I went looking for and did not find

- **A float on an amount.** None anywhere in `src/`: the only `10 ** 30` is
  `mandate.RAW_PER_XNO`, and `_refuse_float` is wired into `load_signed`'s
  `json.load` so a non-integer number in a mandate file is refused by name.
- **A float reaching the mandate ledger**, which `json.load`s without that hook.
  It cannot widen a cap: `_read` accepts `spent_raw` only when
  `str(...).isdigit()` and additionally requires
  `sum(int(p["amount_raw"])) == spent`, so a float on either side is
  `ledger_corrupt` and refuses every spend. Checked both spellings.
- **A verification that trusts the payer or the merchant.** The amount and payee
  are pinned against this tool's own quote; the merchant's receipt `pay_to` is
  printed as untrusted and named as such when it differs.
- **Input reaching a shell or a path.** No `subprocess`, `os.system`, `eval`,
  `exec` or `shell=` in `src/`. The only paths opened are the wallet, the
  mandate and its ledger, all operator-supplied.
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
- **The four skipped `x402_sdk` laws**, which need the official `x402` SDK
  installed to register the mechanism on a real `x402Client`.
- **Everything the v0.1.0 wheel does not carry** (the mandate guard, the
  official-SDK client, the cap checks) is documented in the README's own
  "What v0.1.0 does not include"; that section still matches the released wheel's
  contents, and the fix for it is a release, which is the owner's to cut.
