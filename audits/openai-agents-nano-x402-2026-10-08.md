# openai-agents-nano-x402 — audit 2026-10-08

Previous audit 2026-10-05. One question: can an agent pay an x402-priced
endpoint in XNO with this today, without being hurt? Audited at `66528af`
(`main` after #18). Python 3.11.

## Checked

- `pip install -e ".[dev]"`, `pytest tests/ -q`: **173 passed** on `main`,
  **175** after this change.
- `src/openai_agents_nano/tool.py` end to end again, with attention to what #17
  and #18 added: `QuoteTokenStore.mint/reject`, `_apply_cap`, the cap-before-token
  ordering, `_PayeePinnedWallet` wrapped outside `_MandatedWallet`, every
  formatter, and `price_raw` (not `cap_raw`) as the ceiling handed to the payer.
- `src/openai_agents_nano/x402_sdk.py`, the newest module and the one the last
  audit read least: `parse_raw_amount` (integer raw only, a decimal refused with
  the number the seller probably meant), `_cap_to_raw`, `normalize_payee`,
  `_check_quote`'s five refusals, and `_verify_signed_block` — which re-checks
  `previous` against the observed frontier, `link` against the quoted `payTo`,
  and `observed_balance - block.balance == amount_raw`, all as integer raw.
- **The `Decimal` context every XNO conversion in this package runs in**, which
  is the open question on three sibling repositories. Established here:
  `nanopy/__init__.py:19` executes `decimal.getcontext().prec = 40` at import,
  and this package imports `nano_pay.wallet` (hence `nanopy`) at module level.
  So `_cap_to_raw`'s `value * RAW_PER_XNO` runs at 40 significant digits, not
  the interpreter default of 28, and every cap a legal XNO amount can express
  converts exactly. Measured on the shipped code: `0.01`,
  `99.99999999999999999999999999999`, `1.00000000000000000000000000006` and
  `1.000000000000000000000000000001` all come back with **delta 0** against the
  value computed from their digits. **Not a defect here** — but it is correct by
  a dependency's import side effect rather than by construction, and a host
  application that lowers `prec` itself would reintroduce it. Recorded, not
  changed: the exact-conversion fix moves an amount in both directions, which
  the merge rule does not cover, and the three open pull requests of ours
  already put that question to the owner.
- No float on any amount in either module. Secrets: none in the tree.

## Found and fixed (this branch)

**`.github/workflows/ci.yml` installed this package from a PEP 503 index on a
deleted account, so the weekly installability check was permanently red.**

```yaml
- name: Install from GitHub Pages PEP 503 index
  run: pip install openai-agents-nano
       --extra-index-url https://pandeveloper001.github.io/openai-agents-nano-x402/simple/
```

The account is gone, and the package is on no other index — `README.md` says so
itself: "Until then `pip install openai-agents-nano` fails with 'No matching
distribution found' — this project is not on PyPI, and the name is not
registered." So the step could only fail; a failing step skips every later step
in the job, so the "Import and smoke-test the installed package" step behind it
could never run. The job the workflow's own cron describes as the weekly check on
what is installable has therefore reported red every Monday across six
`matrix` legs, saying nothing about what is published — the same failure mode
`tests/test_ci_workflow.py` was written for, one step further down.

The 2026-10-05 audit found this and left it for its own branch. This is that
branch.

**The fix** points the weekly step at the install path `README.md` actually
publishes — the v0.1.0 GitHub release wheel — and renames the step and the cron
comment to say what it now does. Verified end to end rather than assumed: in a
clean venv, outside any checkout,

```
$ pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl
$ python3 -c "from openai_agents_nano import make_nano_x402_tool, NanoX402ToolError; ..."
make_nano_x402_tool loaded: <function make_nano_x402_tool at 0x...>
NanoX402ToolError loaded: <class 'openai_agents_nano.tool.NanoX402ToolError'>
```

so both steps of the weekly job now pass. (That wheel predates `mandate.py` and
`x402_sdk.py`, which `README.md` already documents at length; the smoke test
imports only what v0.1.0 ships.)

**Two laws, both failing on the unfixed workflow:**

- `test_no_install_path_references_the_deleted_account` — no file under
  `.github/workflows`, `src/`, `README.md` or `pyproject.toml` may name that
  account. It deliberately does **not** cover `docs/`, `.ledger/`, `scripts/`,
  `audits/`, `funnel.md` or `LICENSE`: those record forks and issues that really
  were created there, and rewriting a record is not the fix. Nothing under the
  covered paths referenced it other than this step.
- `test_the_published_install_the_weekly_check_uses_is_one_the_readme_offers` —
  the artifact URL in the workflow must appear in `README.md`, so the weekly
  check exercises the install a reader is actually given rather than a URL only
  CI knows.

The two existing laws in that file matched the literal string
`--extra-index-url`, so both would have passed **vacuously** once the step
stopped using that flag. They now match any install of the package from outside
the checkout, which is the property they were about; with the new step in place
both still have something to judge.

Failing-then-passing, `.github/workflows/ci.yml` alone reverted to `main` with
the tests kept: **2 failed, 3 passed** in that file. With the fix: **175 passed**
overall.

## Could not verify

- **The dead index itself.** This session's egress proxy answers 403 to CONNECT
  for `pandeveloper001.github.io`, so it is established from the account's
  deletion, `funnel.md:357`'s recorded 404, and the README's own statement that
  the package is on no index — not re-probed. The release URL above *was*
  reached (HTTP 200) and installed, which is the half that matters for the fix.
- **The `uv` leg.** `uv pip install --system <url>` is unchanged in shape from
  the `pip` leg and the matrix expression is untouched, but only `pip` was run
  here.
- A real wallet, node or broadcast: none exist in this session, and the suite
  opens no socket by design.
