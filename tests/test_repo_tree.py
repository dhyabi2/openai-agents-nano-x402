"""Build output must not be tracked.

`.gitignore` carried the line `build/.ledger/live-proof.md` -- a path that does
not exist and never has, so it ignored nothing -- where two separate lines were
plainly meant, `build/` and `.ledger/live-proof.md`, merged into one. With
`build/` unignored, an ordinary `python -m build --wheel` left its intermediate
copy in the tree and it was committed:

    $ git ls-files build/
    build/lib/openai_agents_nano/__init__.py
    build/lib/openai_agents_nano/tool.py

    $ git check-ignore -v build/
    (no output, exit 1 -- not ignored)

That copy then went stale, and what it was missing mattered: the `req.is_finite()`
guard in `_apply_cap`, which refuses a model-supplied `max_xno` of `"nan"` or
`"Infinity"`. So a public repository carried a second, weaker copy of a guard on
model-controlled input, which a reader or a scanner could take for live code.
Nothing in the repository references `build/`.

Running the build also rewrites that tracked file, so `python -m build` left a
contributor with a dirty working tree for no reason.

These laws read git itself rather than the `.gitignore` text: the property that
matters is what git actually tracks and ignores, not how the pattern is spelled.
"""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Directories that only ever hold build output. A tracked file under any of them
# is a build artifact somebody committed.
ARTIFACT_DIRS = ("build/", "dist/")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _require_git_checkout() -> None:
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout (installed from a distribution)")
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        pytest.skip("git is not usable here")


def test_no_build_output_is_tracked():
    _require_git_checkout()
    tracked = _git("ls-files").stdout.split("\n")
    offenders = sorted(p for p in tracked if p.startswith(ARTIFACT_DIRS))
    assert offenders == [], (
        "these build artifacts are tracked: "
        + ", ".join(offenders)
        + ". They are a second, silently ageing copy of the package; remove them "
        "with `git rm --cached` and keep the directory ignored."
    )


def test_git_ignores_the_build_directory():
    _require_git_checkout()
    # check-ignore answers for an arbitrary path, so this holds whether or not a
    # build has run in this checkout.
    probe = "build/lib/openai_agents_nano/tool.py"
    result = _git("check-ignore", probe)
    assert result.returncode == 0, (
        f"git does not ignore {probe!r}, so `python -m build` leaves its "
        "intermediate copy of the package in the tree where it can be committed. "
        "Add `build/` to .gitignore."
    )
