# openai-agents-nano-x402 — audit 2026-10-13

Previous audit 2026-10-11. Audited at `3067e3c` (`main` after #24).
Lens: can an agent PAY in XNO with this today without being hurt — paying more
than it authorised, paying somebody else, being told it paid when it did not, or
being unable to get started at all.

Suite as CI runs it, from a clean venv (`pip install -e '.[dev]'`, then
`python -m pytest tests/ -q`): **419 passed** before this change, **421
passed** after. `ruff check .` (CI's lint step) clean both ways.

## Found and fixed

- **The official-SDK section's install command could not work.** (MEDIUM, the
  first step a new agent takes)
  `README.md:260` opened that section with

      pip install "openai-agents-nano[x402]"

  while the Install section 180 lines above states, correctly, that
  `pip install openai-agents-nano` fails with "No matching distribution found —
  this project is not on PyPI, and the name is not registered". Measured in a
  clean venv this run:

      ERROR: Could not find a version that satisfies the requirement
             openai-agents-nano[x402] (from versions: none)
      ERROR: No matching distribution found for openai-agents-nano[x402]

  `https://pypi.org/pypi/openai-agents-nano/json` answers **404**
  (`x402-nano-exact`, which the same paragraph links, answers 200). That
  section is self-contained — its own install block, its own imports — so a
  reader who starts there, which is the whole point of a section addressed to
  people who already speak x402, gets an error and no payer. It is also the
  section whose module (`x402_sdk.py`) the pinned v0.1.0 wheel does not carry,
  so there was no working install of it named anywhere in that section.

  The command is now the PEP 508 direct reference, which keeps the extra:

      pip install "openai_agents_nano[x402] @ git+https://github.com/dhyabi2/openai-agents-nano-x402"

  Verified by running it in a fresh `python3.13 -m venv`: it resolves, installs
  the `x402` extra (x402 2.25.0), and
  `from openai_agents_nano import ExactNanoClientScheme, nano_spend_controls` —
  the exact import that section shows — succeeds.

  **The law**, appended to `tests/test_readme_release_claims.py`
  (`test_no_readme_command_installs_this_project_by_bare_pypi_name`): no command
  in a README fenced `bash` block may install `project.name` by bare name while
  the name is unregistered. It reads the commands out of the README itself, so a
  section added later is covered, and derives the name from `pyproject.toml`
  rather than a literal. Prose is deliberately not parsed, so the Install
  section can keep saying that the bare-name install fails. A parser guard
  (`test_the_readme_installs_something_so_this_law_can_see_it`) fails if the
  fenced-block shape ever stops matching, so the law cannot silently disarm.
  `PYPI_REGISTERED = False` is the one line to flip, in the commit that
  publishes. Against the README as on `main` the law fails; with the fix it
  passes.

## What I checked, end to end

- **`x402_sdk.py`, the whole client mechanism** (the module the 10-11 audit
  covered in one paragraph): `_check_quote`'s refusals (scheme, network, asset,
  payee checksum via `NET`, amount, the cap, and a payTo equal to the payer's
  own address), `parse_raw_amount` (a decimal is refused with a hint rather
  than scaled — a JSON float `1e30` stringifies to `'1e+30'` and is refused;
  `5.0` and `true` are refused), `_xno_to_raw_exact`'s `adjusted()` magnitude
  check *before* any integer is built, and `_verify_signed_block`'s checks on
  the block before it is handed over: `type`, `previous` against the observed
  frontier, `link` decoding to exactly the quoted `payTo`, and
  `observed_balance - int(balance) == amount_raw`. Every amount comparison is
  integer raw. **All four module regexes (`_RAW_RE`, `_HEX64_RE`,
  `_SIGNATURE_RE`, `_WORK_RE`) are unanchored patterns used only with
  `fullmatch`** — checked each of the six call sites; a `.match()` among them
  would have let `"5abc"` through as an amount, and there is none.
- **The journal re-presentation guard** (#23/#24's subject) against the
  *installed* feeless402 0.2.13 source rather than against its description.
  `_journalled_block`'s `int(accepted[field])` (`tool.py:270`) looked loose
  beside the repo's own strict `_raw_digits` — it is **correct as written**:
  `nano_pay.x402.offer_amount_raw` (0.2.13, line 277) uses the identical field
  order `("amount", "maxAmountRequired", "max_amount_required")` and the
  identical bare `int()`, and `_journal_key` is keyed on exactly that value.
  The tool's job here is to predict what feeless402 will do, so mirroring its
  looseness is what makes the prediction right; tightening it to `_raw_digits`
  would make the tool read a different amount than the one in the entry's key,
  the key comparison would miss, and the refusal would be skipped. Confirmed
  `build_payment_header` echoes the whole offer as `accepted`, so the field the
  tool reads is the field feeless402 keyed. `_could_be_re_presented`'s three
  payee spellings cover `offer_pay_to`'s raw string, and every unreadable case
  falls through `except Exception: return True`, the conservative side.
- **README install paths, every one of them.** The release wheel and the sdist
  both answer 200; `git+...@v0.1.0` and the bare `git+...` forms are the ones
  the suite's own `release_install_offline.py` exercises. Line 260 was the only
  command that could not run.
- **No float on an amount anywhere in `src/`**: the only `10 ** 30` literal is
  `mandate.RAW_PER_XNO`; `_refuse_float` is still wired into `load_signed`.
- **No input reaching a shell or an unchecked path**: no `subprocess`,
  `os.system`, `eval`, `exec` or `shell=` in `src/`. The only paths opened are
  the wallet, the feeless402 journal beside it (read-only), the mandate and its
  ledger — all operator-supplied.
- **No secret in the tree.** `secrets` is the stdlib module (quote token,
  mandate nonce); `_write_private` creates key files `O_EXCL` at `0o600`.

## Still open, unchanged from 2026-10-11

- **A float in the mandate ledger.** `mandate.py` `_read` digit-checks
  `spent_raw` but each `payments[*].amount_raw` goes through `int()`, so `5.0`
  and `true` read as 5 and 1 when the total matches. Reaching it needs write
  access to the operator's ledger file, which already allows resetting the
  ledger outright, so it widens nothing an agent or a merchant can do.
  `mandate.py` is a byte-for-byte vendored copy pinned by `VENDORED_SHA256` in
  `tests/test_mandate.py` and shared with two other repositories; the fix
  belongs in that shared source and must be bumped in all three together.
- The three items #23 left open in `audits/nano-mcp-2026-10-12.md` are that
  repository's, not this one's.

## Could not verify

- **No live payment.** No XNO moved in this run; every case is measured against
  stubs. The README's live proof (block `E67FB894…57FC3`, 2026-09-18) is
  unchanged and was not re-paid.
- **`github.com/feeless402/feeless402`** and **`feeless402.com`**: this
  session's own GitHub proxy answers 403 for any repository not attached to the
  session (`{"message":"GitHub access to this repository is not enabled for this
  session"}`), not a 404 from GitHub, so the README's links to them could not be
  checked either way from here. Not evidence of a broken link.
- **Whether the PyPI name is now registered.** The 404 above is what this run
  measured; registration itself needs a person with a PyPI login, and
  `.github/workflows/publish.yml` still awaits the pending trusted publisher.

## One thing for the cloud worker, not this run

`origin/fix/untrack-build-output` exists with no open pull request. Standing
duty 1 (unmerged branches) is the cloud worker's, not the auditor's; noting it
here rather than acting on it.
