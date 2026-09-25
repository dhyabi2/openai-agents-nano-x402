# openai-agents-nano-x402 — code audit, 2026-09-25

Scope: the tree at `ca98558` (`main`). Read `src/openai_agents_nano/tool.py` in
full, both collected test modules, `pyproject.toml`, and
`.github/workflows/ci.yml`. The 2026-09-24 audit recorded that CI had never run
this repository's test suite; this run confirmed that from GitHub's own job logs
and fixed it.

## How it was checked

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # clean
.venv/bin/python -m pytest -q          # 10 passed  <- baseline
.venv/bin/ruff check .                 # All checks passed
```

## Found and fixed

**The `test` job never reached the test suite.** A failing step in a GitHub
Actions job skips every later step in that job. The job installed the package
from an external GitHub Pages index first and ran this repository's suite last,
so once that index stopped resolving the job died at the install step. From the
runner's own log for run 16 (`test (3.13, pip)`, 2026-09-25T06:41:18Z):

```
Looking in indexes: https://pypi.org/simple, https://<...>.github.io/openai-agents-nano-x402/simple/
ERROR: Could not find a version that satisfies the requirement openai-agents-nano (from versions: none)
ERROR: No matching distribution found for openai-agents-nano
##[error]Process completed with exit code 1.
```

Every recent CI run is red on this, and none of them says anything at all about
the code — the step that would judge the code never ran.

Fixed by running the suite first and on every event, and gating the mirror
install on the events it is actually for. The workflow's own cron comment
already says what that check is — "Weekly: test install from every mirror" — so
it now runs on `schedule` and `workflow_dispatch` rather than on every push. The
mirror check is not deleted and still fails loudly on its weekly run, which is
the correct place to learn that what is published cannot be installed.

Proved by `tests/test_ci_workflow.py`, which pins the ordering and the gating.
Against the unfixed workflow:

```
FAILED tests/test_ci_workflow.py::test_the_suite_runs_before_any_external_index_install
FAILED tests/test_ci_workflow.py::test_an_external_index_install_cannot_gate_an_ordinary_push
2 failed, 1 passed
```

and with the fix, `3 passed`. Suite: **10 passed before, 13 after.** The PR's own
CI run is the end-to-end evidence: it is the first run in this repository's
history in which the `pytest` step executes.

## Found, not changed — for the owner

**The GitHub Pages package index does not exist under either account.** The
workflow installs from `pandeveloper001.github.io/.../simple/`; that account is
retired, and `dhyabi2.github.io/.../simple/` is not serving one either. Both were
also unreachable from this sandbox, but the sandbox's egress proxy denies plenty
of hosts, so the finding above rests on GitHub's runner log rather than on that.

The honest options are to publish the index under `dhyabi2`, or to delete those
two steps and let PyPI (`publish.yml`) be the only distribution route. Either is
a decision about how this package is distributed, which is the owner's, not a
defect to patch — so the steps are gated here, not removed.

## Checked and clean

- `tool.py`'s two-phase quote/redeem path. A token is minted only on a dry run,
  bound to `pay_to` and the exact `amount_raw`, single-use (popped on the
  redeem that consumes it), and expiring; `reject()` refuses missing, unknown,
  expired and offer-changed tokens before anything is signed. The cap is
  re-checked against the quoted price after the token is accepted and before
  signing.
- The cap parser was probed rather than read. `_apply_cap` already refuses NaN,
  Infinity and negatives as text; this run also pushed model-supplied values
  that make `str(Decimal)` emit scientific notation (`1e-40`, `1E-7`,
  `0.0000000000000000000000000000000001`). `xno_to_raw` accepts every one of
  them, so the exponent form does not escape the tool as an exception — the
  promise that the tool always returns agent-readable text holds on that path.
- `PaidRequestFailed` is handled separately from a generic failure and surfaces
  the signed block hash with an explicit "do NOT pay again" instruction — the
  one outcome where a retry could spend twice.
- `_format_receipt` heads a result `PAID` only for `settled is True`; `False`
  and an indeterminate verdict get distinct, non-paid headlines.
- No secrets in the tree. No `.env`, key or wallet file is tracked; the wallet
  path is taken from the environment and never rendered into tool output.
- The eight `tests/*_offline.py` files are standalone scripts with `__main__`
  and no `def test_`, so pytest not collecting them is deliberate, not a set of
  tests silently skipped.
- `ruff check .` passes under the deliberately narrow rule set pinned in
  `pyproject.toml`.

## Not verified here

- The `build` and `lint` jobs were not re-run locally beyond `ruff`; `uv build`
  was not exercised.
- Nothing was paid, and no live x402 endpoint was called. The payment path is
  verified only by the offline suite and by reading, never against a merchant.
- Whether `publish.yml` would succeed: it was read but not run, and this audit
  does not publish anything.
