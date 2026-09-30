# openai-agents-nano-x402 — code audit, 2026-09-30

Clone of `main` at `f6bd7d1`. Baseline in a clean venv, before any change:

```
$ pip install -e ".[dev]"      # succeeds
$ python3 -m pytest tests/ -q  # 81 passed
$ ruff check .                 # All checks passed!
```

Earlier notes read the adapter's source. This run instead audited **what the published install path
actually delivers**: the release asset was downloaded from the GitHub release and compared against
the tree and against the README's claims. That is where the finding is.

## Found and fixed

**The README documented a feature its own pinned install path cannot provide.** `README.md` presents
the **v0.1.0 GitHub release** as "the immutable, public install path (works today)", and it is the
only published path — there is no PyPI project. The asset was fetched and read:

```
release v0.1.0, openai_agents_nano-0.1.0-py3-none-any.whl
  sha256 70263652da161e896d35059198067e8298f27ac3ba656ccf240363406f6fe3ea
  modules: __init__, tool          (no mandate)
  console scripts: none            (no entry_points.txt in the archive)
```

The tree ships a third module, `mandate.py` (828 lines), and `pyproject.toml` declares a `mandate`
CLI. Both came after the tag, and the project version never left `0.1.0`, so nothing about the
install signals the gap. Installed exactly as the README's Install section says, then used exactly as
the README's operator-mandate section says:

```
$ mandate keygen --out operator.key
  -> no 'mandate' console script is installed
>>> make_nano_x402_tool(mandate_path="mandate.json")
  TypeError: make_nano_x402_tool() got an unexpected keyword argument 'mandate_path'
>>> import openai_agents_nano.mandate
  ModuleNotFoundError: No module named 'openai_agents_nano.mandate'
```

The same wheel also predates the `_apply_cap` hardening. Driving the **published** wheel's own
`_apply_cap`, against today's source for comparison:

| input | published v0.1.0 | `main` today |
|---|---|---|
| `X402_MAX_XNO="nan"` | returns cap `NaN`, no refusal | `ValueError` — refused |
| `X402_MAX_XNO="-1"` | returns cap `-1`, no refusal | `ValueError` — refused |
| `X402_MAX_XNO="abc"` | `decimal.InvalidOperation` escapes the caller's `except ValueError` | `ValueError` — refused |
| model-supplied `max_xno="nan"` | `InvalidOperation` escapes | `ValueError` — refused |
| model-supplied `max_xno="Infinity"` | silently ignored, cap stays `0.01` | `ValueError` — refused |

`max_xno` is model-supplied, so the third and fourth rows are an unhandled exception out of a tool an
agent calls.

**Fixed** in the README, which is the half this audit may change: the Install section now states what
v0.1.0 ships, that it carries neither `mandate.py` nor the `mandate` CLI, that
`make_nano_x402_tool(mandate_path=...)` raises `TypeError` on it, that its cap checks are the older
ones, and it points at the source install for the current code. The code needs no change — `main` is
already correct. **What is not fixed is the release itself**, and only a person can fix that: cutting
a release is a publishing action this audit does not take.

**Law.** `tests/test_readme_release_claims.py` (4 cases) refuses the state where the README documents
a module or console script the pinned release cannot provide and says nothing about it. It is derived
from `pyproject.toml` and from `tests/data/release-v0.1.0-contents.json` — real data read out of the
release asset, not written by hand — so a module added later is covered without touching the law. It
does not dictate which way the gap closes: re-cutting the release and re-recording the fixture
satisfies it too. One case guards the fixture against being hand-emptied, which would disarm the
rest, and one refuses deleting the pinned install block instead of explaining it.

```
before the README change: 2 failed, 2 passed
after:                    4 passed
full suite:               85 passed   (81 before; +4)
ruff check .              All checks passed!
```

## Found, not changed

**Eight of the sixteen test files never run in CI.** `tests/*_offline.py` are standalone proofs with
`__main__` blocks, named so pytest does not collect them (verified: 0 collected even when named
explicitly). CI runs only `python3 -m pytest tests/ -q`, so the fail-closed proof, the two-phase gate,
receipt honesty, payment-failure honesty, wallet load, release install and the tunnel probe are
covered nowhere in CI. They are not dead: seven pass when run by hand, and they check the things that
matter most. Run by hand this run:

```
fail_closed_offline.py              exit 0    two_phase_offline.py                exit 0
receipt_honesty_offline.py          exit 0    wallet_load_offline.py              exit 0
payment_failure_honesty_offline.py  exit 0    release_install_offline.py          exit 0
tunnel_ua_probe_offline.py          exit 0    prepared_pr_doc_offline.py          exit 1
```

Adding them to CI is a workflow change, so it is left for a person to decide.

**`QuoteTokenStore` never evicts.** `mint` adds to `self._tokens` unboundedly; expiry is only checked
when that exact token is presented (`tool.py:78`), and a token nobody redeems is never dropped. A
long-lived agent that previews many endpoints grows the dict for the process's life. Not touched:
`tool.py` gates payment.

## Not verified here

`prepared_pr_doc_offline.py` exits 1 with "no scan report and could not generate one". It reads
`.ledger/tmp/drift_all.json`, which `.gitignore` excludes (`.gitignore:2`), and regenerating it needs
live GitHub access this sandbox does not have. The tracked `.ledger/drift_all.json` is a different
shape — a `{"branches": {...}}` dict, not the list of rows with `branch` keys the proof reads — so it
is not a substitute. **This is a sandbox limit, not evidence of a defect**, and it is not in the
published package or in CI. A future run with GitHub access should settle it.

The weekly scheduled CI job installs from
`https://pandeveloper001.github.io/openai-agents-nano-x402/simple/`. Reachability was not tested: the
sandbox's proxy refuses the tunnel, and reading that as a dead link would be wrong.

## Secrets

Clean. No credential, key or seed in the tree. `.gitignore` covers `nano_wallet*.json`,
`.wallet.json`, `dist/` and `build/`; no build output is tracked (the stale tracked copy an earlier
note recorded is gone). The 64-hex strings in `docs/` and `.ledger/` are Nano block hashes and public
addresses.
