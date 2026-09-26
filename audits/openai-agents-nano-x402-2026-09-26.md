# openai-agents-nano-x402 — code audit, 2026-09-26

Scope: the tree at `ef10114` (`main`). This run went after the repository as a
*distribution* rather than the adapter logic the two previous audits read in
full: what is tracked, what a build produces, and what the artifact the README
tells people to install actually contains. That is where both findings are.

## How it was checked

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # clean
.venv/bin/python -m pytest -q          # 13 passed   <- baseline
.venv/bin/python -m build --wheel      # clean
.venv/bin/ruff check .                 # All checks passed!
```

## Found and fixed

**`.gitignore` carried a line that ignored nothing, and build output was
committed because of it.** Line 9 read

```
build/.ledger/live-proof.md
```

— a path that does not exist and never has in this repository. `git check-ignore`
confirms it matches only itself, while the two paths plainly meant, `build/` and
`.ledger/live-proof.md`, are both *unignored*:

```
$ git check-ignore -v build/                       (no output, exit 1 — NOT ignored)
$ git check-ignore -v .ledger/live-proof.md        (no output, exit 1 — NOT ignored)
$ git check-ignore -v build/.ledger/live-proof.md
.gitignore:9:build/.ledger/live-proof.md	build/.ledger/live-proof.md
```

Two lines merged into one by a missing newline. With `build/` unignored, an
ordinary `python -m build --wheel` left its intermediate copy of the package in
the tree and it was committed:

```
$ git ls-files build/
build/lib/openai_agents_nano/__init__.py
build/lib/openai_agents_nano/tool.py
```

**What that copy had gone on to be missing is the part that matters.** It is 418
bytes shorter than `src/openai_agents_nano/tool.py`, and the difference is one
guard in `_apply_cap`:

```
-        # Decimal() accepts "nan"/"snan"/"Infinity" happily, and comparing a NaN
-        # raises InvalidOperation rather than returning False ...
-        if not req.is_finite():
-            raise ValueError(f"max_xno is not a finite number: {requested!r}")
```

`max_xno` is model-supplied. So a public repository carried a second, weaker copy
of a guard on model-controlled input, which a reader or a scanner could
reasonably take for live code. Nothing in the repository references `build/`.
Running the build also rewrote that tracked file, so `python -m build` left a
contributor with a dirty working tree for no reason.

Fixed by making line 9 `build/` and untracking the two files with
`git rm --cached` — they remain ordinary build output on disk. `.ledger/live-proof.md`
is tracked and its intent belongs to the ledger, not to this fix, so it is left
exactly as it is.

Proved rather than asserted. `tests/test_repo_tree.py` asks git itself — what it
tracks and what it ignores — rather than reading the `.gitignore` text, because
the property that matters is the behaviour, not the spelling. Against the unfixed
tree:

```
FAILED tests/test_repo_tree.py::test_no_build_output_is_tracked
  AssertionError: these build artifacts are tracked:
  build/lib/openai_agents_nano/__init__.py, build/lib/openai_agents_nano/tool.py
FAILED tests/test_repo_tree.py::test_git_ignores_the_build_directory
  AssertionError: git does not ignore 'build/lib/openai_agents_nano/tool.py' ...
2 failed
```

With the fix:

```
$ .venv/bin/python -m pytest -q
15 passed

$ rm -rf build dist && python -m build --wheel
Successfully built openai_agents_nano-0.1.0-py3-none-any.whl
  wheel's tool.py carries the is_finite guard: True
$ git status --porcelain        # only this change; no build artifact dirties the tree

$ ruff check .
All checks passed!
```

Both laws skip when there is no git checkout, so installing from a distribution
does not turn them into failures.

## Urgent, and NOT fixable from this repository

**The published release wheel — the exact artifact the README tells people to
install — is the version without that guard.** `README.md:35` and `:51` both say:

```
pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl
```

That URL resolves (HTTP 200; the only release is `v0.1.0`, carrying the wheel and
the sdist). Its `tool.py` is 13741 bytes — the same as the stale `build/lib` copy,
against 14159 in `src/` — and it has no `is_finite()` call at all. Exercised
directly out of the downloaded wheel:

```
PUBLISHED v0.1.0 wheel (what the README tells users to pip install):
  max_xno='nan'        -> InvalidOperation escapes past `except ValueError`
  max_xno='Infinity'   -> accepted, cap=0.01
  max_xno='-Infinity'  -> ValueError (refused, correct)
  max_xno='snan'       -> InvalidOperation escapes past `except ValueError`

the repository tree (fixed):
  all four              -> ValueError (refused, correct)
```

So on the published artifact a model that answers `max_xno: "nan"` raises
`decimal.InvalidOperation` straight past the caller's `except ValueError`, and
`"Infinity"` is accepted and silently clamped rather than refused. The repository
has been correct since the guard landed; the release asset was built before it
and has never been rebuilt.

Remedying that means a new release built from current `main` — a version bump and
a publish. Publishing goes through the swarm's own rail with its secret scan and
is explicitly not this audit's to perform, so it is reported to the owner
instead. `openai-agents-nano` is still **not on PyPI**
(`pypi.org/pypi/openai-agents-nano/json` → 404), so the GitHub release is the
only published artifact and the only one affected.

## Checked and clean

- No secrets in the tree. No `.env`, key or wallet file is tracked; `.gitignore`
  covers `nano_wallet*.json` and `.wallet.json`, and the wallet path is taken
  from the environment and never rendered into tool output.
- `ruff check .` passes under the deliberately narrow rule set pinned in
  `pyproject.toml` (E9, F63, F7, F82 — real bugs, not style).
- `[tool.setuptools.packages.find] where = ["src"]` means the tracked `build/lib`
  could not have been *selected* as the distribution; the wheel built from this
  tree carries `src/`'s version. The stale copy's harm was to readers of the
  public repository and to a contributor's working tree, not to the wheel this
  tree builds — checked both ways, including with `build/lib` deliberately given
  a newer mtime than `src/`, where setuptools 84 force-copies and the fresh file
  still wins.
- The README's install URL resolves: HTTP 200, and the `v0.1.0` release carries
  both `openai_agents_nano-0.1.0-py3-none-any.whl` and the sdist.
- The eight `tests/*_offline.py` files are standalone scripts with `__main__` and
  no `def test_`, so pytest not collecting them is deliberate, not a set of tests
  silently skipped. Carried from 2026-09-24 and still true.

## Not verified here

- Nothing was paid and no live x402 endpoint was called. The payment path is
  verified only by the offline suite and by reading, never against a merchant.
- `publish.yml` was read, not run. Nothing was published and no version bumped.
- `scripts/` (22 files, ~2350 lines of outreach and measurement tooling) was
  listed but not audited: none of it ships in the package or runs in CI, so it
  ranks below the distribution defects above. It is the obvious target for a
  later run.
