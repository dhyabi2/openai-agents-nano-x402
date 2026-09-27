# openai-agents-nano-x402 — audit 2026-09-27

Fourth pass. The 2026-09-26 note named `scripts/` as the obvious next target. It is still not the
important thing here: the eight `tests/*_offline.py` scripts were run this time, which the earlier passes
had only read, and two of them do not run at all outside one agent box. One of those two is the
repository's proof that the published wheel works.

## What was checked

- `pytest tests -q` on a clean clone in a fresh venv: **15 passed** before any change.
- `ruff check .` under the narrow rule set pinned in `pyproject.toml`: **All checks passed**.
- **All eight `tests/*_offline.py` scripts actually executed**, not read. Six pass
  (`fail_closed`, `payment_failure_honesty`, `receipt_honesty`, `tunnel_ua_probe` 7/7, `two_phase`,
  `wallet_load`). Two fail — see below.
- `src/openai_agents_nano/tool.py` line by line: the cap, the quote-token store, both refusal paths,
  and the three receipt renderings.
- The tracked tree for build output and for machine-specific paths.

## Fixed

- **`tests/release_install_offline.py:34` — the proof that the published wheel installs could not be
  run by anyone who installs it.** The build tool was resolved as

      UV = os.environ.get("UV", "/root/.hermes/bin/uv")

  an absolute path that exists on one agent box and nowhere else. Everywhere else — a contributor's
  laptop, a reviewer's checkout, and this repository's own CI, whose workflows get uv from
  `pip install uv` and so find it on **PATH** — the first subprocess raised

      FileNotFoundError: [Errno 2] No such file or directory: '/root/.hermes/bin/uv'

  before a single check ran. This is not a minor test: it is the only thing here that builds the wheel,
  installs it into a brand-new venv, and drives the installed tool through the SDK invoker
  (`FunctionTool.on_invoke_tool`) to prove a dry-run quote spends nothing and an over-cap redeem is
  refused before signing. The repository's evidence that the published package works was unrunnable by
  everyone except one machine.

  Shown, then fixed, then shown again: with nothing configured the script died on that line; with
  `UV=$(command -v uv)` the **entire script passed unchanged**, which is what proves the path was the
  only fault. After the fix, `python tests/release_install_offline.py` with no environment at all
  prints `RELEASE_INSTALL_OK` and exits 0.

  Fix: `find_uv()` — `$UV` if set, else `shutil.which("uv")`, else a `SystemExit` naming uv and how to
  get it instead of a raw `FileNotFoundError` on a path the reader never chose. Resolved inside phase 1
  rather than at import, because the `--in-venv` phase needs no uv. Nothing else in the script changed.

  Laws: `tests/test_release_proof_portable.py`, 5 laws, and **collected by pytest** — unlike the offline
  script itself, which has no `def test_` and so was never collected, which is precisely how a
  machine-only path survived three audits. The last of them runs the whole proof end to end with `UV`
  stripped from the environment. One reads the AST of every sibling test and fails on a string literal
  holding `/root/`, `/srv/swarm`, `/opt/swarm` or `/var/lib/swarm`, over literals only so that a comment
  explaining this defect is not itself a violation.

  **Before: 5 failed, 15 passed. After: 20 passed.** `ruff check .` still passes.

## Found, NOT fixed

- **`tests/prepared_pr_doc_offline.py` exits 1 outside the agent box.** It wants a scan report it
  cannot generate here ("no scan report and could not generate one"). It documents outreach state
  rather than the package, so it ranks below the release proof and is not in this change's concern.
  A reader running the test directory will still see it fail.

- **`QuoteTokenStore` never evicts.** `mint` adds; only `reject` removes, and only the token it was
  handed. A long-lived agent that previews far more often than it redeems grows the dict without
  bound. Real but slow — tens of bytes per unredeemed preview — and a fix means choosing an eviction
  policy, which is design, not repair.

- **A quote token is bound to `(pay_to, amount_raw)` and not to the URL.** So a token minted previewing
  one endpoint can redeem at a different endpoint that quotes the same recipient and the same amount.
  The money goes to the same account for the same amount either way, so there is no financial gap, but
  the docstring's "bound to that exact offer" is stronger than what the code checks. Widening the
  binding changes behaviour and belongs to whoever owns the two-phase design, not to an audit.

## Not verified

- **Nothing was paid and no live x402 endpoint was called.** The payment path is verified only by the
  offline suite and by reading, never against a real merchant.
- **The README's external links.** `https://feeless402.com` and `https://github.com/feeless402/feeless402`
  answer 000 and 403 **through this sandbox's egress proxy**, which is the proxy's policy and not
  evidence about the sites. The release-asset URL returns a real 200 and is confirmed good. The other
  two need a check from an unproxied network before anyone calls them dead.
- **`publish.yml` was read, not run.** Nothing was published and no version bumped.
- **`scripts/` (22 files, ~2350 lines)** still not audited: none of it ships in the package or runs in
  CI. Carried forward from 2026-09-26.
