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
`python3 -m pytest tests/ -q --tb=short`: **332 passed, 0 skipped** (289 before
this change, plus the 43 tests in `tests/test_journal_replay_payee.py`).
`tests/test_journal_replay_payee.py` also passes, 43 of 43, against feeless402
0.2.9 and 0.2.12; on 0.2.8, which has no journal, the 34 tests that need one
skip. `[dev]`
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
    **refuses before anything is sent** when a live entry that feeless402 could
    re-present for this request holds a block paying another account. "Could
    re-present" is feeless402's own key: same method, URL and request body
    (recomputed with its `_journal_key` and `_request_fingerprint`), and an
    amount no higher than the price authorised. An entry for a higher amount
    does not refuse; from feeless402 0.2.12 an entry for another body does not
    either (older versions leave the body out of the key, so there it refuses). The refusal names the block hash, the journal
    file and the entry key with its expiry, tells the agent not to pay again and
    tells the operator how to clear it.
  - after the payment, counts the blocks the pinned wallet actually built. If it
    built none and a receipt came back, the block was re-presented, whether or
    not the journal held the entry when it was read before the call. Its payee is
    taken only from the signed block in the journal (`link`, or
    `link_as_account`), read before the call, at the send and after the call,
    matched by the block hash feeless402 reports. If that is the authorised
    account the result reads PAID with a `re-sent:` line; another account is
    headed **PAYEE MISMATCH**; a block that cannot be read is headed **PAYEE
    UNVERIFIED**. The receipt's `pay_to` never confirms a payee, because the
    merchant's payment-response can overwrite it; it is shown only as unproven.
    Under a mandate, both say the block was not checked against the allow-list
    in this call. Neither is headed PAID or says "signed to A".
  - on a re-presentation the merchant does not answer (`PaidRequestFailed`),
    prints feeless402's `pay_to` and flags a mismatch the same way.
  - compares payees as accounts, so `xrb_X` and `nano_X` are the same payee.

  Re-presenting the same block to the same payee is the journal doing its job,
  and still reads PAID. `tests/test_journal_replay_payee.py` drives the real
  `request_with_payment` and its real journal; only the network, the node and
  the signature are stubbed.

  Limitation: the tool's lock is per tool instance. Another tool instance in
  the same process, another process, or the `feeless402` CLI sharing the wallet
  file can write a journal entry between the tool's pre-send read and
  feeless402's. That block is then sent; the tool cannot stop it, and reports it
  as PAYEE MISMATCH or PAYEE UNVERIFIED instead of PAID.

  **Correction to the first version of this fix (`96094c4`).** It said the
  result was "never headed PAID" and that only "a second process" was not
  covered. Neither held: the post-payment check ran only when the journal held
  an entry before the call, so an entry written by another tool instance in the
  same process (or another process) during the paying read was reported as PAID
  to the authorised payee; it fell back to the receipt's `pay_to`, which the
  merchant can overwrite; it compared `xrb_`/`nano_` spellings as different
  payees; and its pre-send check matched method and URL only, so an entry for
  another body or an amount above the price refused every request to that URL
  for 24 hours with no way out named. All four are fixed as described above.

  **Review round 3.** Five further findings, all fixed:
  - (MEDIUM) In the NanoGPT dialect (the offer carries `paymentId`) the stored
    header echoes no offer, so the amount was unknown and every live entry for
    the same method and URL to another payee refused, even for another body.
    feeless402 keys that dialect exactly like v2, on the offer's amount, which is
    the amount it signs. The tool now asks the node for the balance of the
    block the journalled block follows and subtracts the block's own signed
    balance, then applies the same amount and key checks. A node that does not
    answer, a missing or failing key function, still refuses.
  - (LOW) The amount check now comes before the missing-helper fallback, as in
    feeless402, which raises `PriceCapExceeded` before it reads the journal.
    The comment saying feeless402 refuses an unreadable journal now says that
    holds from 0.2.12 only.
  - (LOW) A journal time of Infinity or 1e20 crashed the refusal's expiry date
    (`OverflowError`), and a NaN time was live to the tool but dead to
    feeless402. Liveness is now feeless402's own test, `now - t < TTL`, and an
    expiry that cannot be printed reads `unknown`.
  - (LOW) A re-sent block reported PAID under a mandate now says the mandate
    was not charged for it in this call, and that whether it was when it was
    signed is unknown.
  - (INFO) A block whose `link` is present but unreadable was attributed to its
    unsigned `link_as_account`. It is now unreadable (PAYEE UNVERIFIED if
    re-presented); `link_as_account` is used only when there is no `link`.
    `_same_payee` no longer confirms two identical strings that are not valid
    addresses. The end-to-end stub now builds blocks with a signed `link`.

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
