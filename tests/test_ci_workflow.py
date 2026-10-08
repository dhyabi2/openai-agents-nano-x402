"""The test suite must actually run in CI.

A GitHub Actions step that fails skips every later step in the same job. The
`test` job used to install the package from an external GitHub Pages index
*before* running this repository's own suite, so once that index stopped
resolving the job died at the install step and the suite was never reached:

    Looking in indexes: https://pypi.org/simple, https://<...>.github.io/...
    ERROR: Could not find a version that satisfies the requirement
           openai-agents-nano (from versions: none)
    ##[error]Process completed with exit code 1.

CI went red on every push and said nothing whatever about the code, because the
one step that would have judged the code never ran.

This law pins the ordering and the gating that keep that from recurring. It
reads the workflow as text rather than as YAML on purpose: the repository has no
YAML parser among its dependencies, and adding one to assert a property this
simple would cost more than it is worth.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
README = ROOT / "README.md"

SUITE_STEP = "Run project test suite"

#: A step that reaches outside this checkout for the package. It used to be only
#: `--extra-index-url`; the weekly check now installs a release URL directly, and
#: both laws below are about *any* install whose success depends on something
#: published elsewhere, so both spellings count. Matching only the flag would
#: have left those laws passing vacuously the moment the step changed shape.
EXTERNAL_INSTALL = re.compile(
    r"--extra-index-url|--index-url|https://[^\s]*\.(?:whl|tar\.gz)", re.I
)

#: The account every published link used to live under. It is deleted, so a
#: reference to it in an install path is an install that cannot work.
DELETED_ACCOUNT = re.compile(r"pandeveloper001", re.I)

#: Where a reference to that account would be a broken install path rather than a
#: record of something that happened. `docs/` holds outreach studies that name
#: forks and issues created there at the time, `.ledger/`, `scripts/`, `funnel.md`
#: and `x-thread-sep22.md` are operator notes, `audits/` is history, and LICENSE
#: carries a copyright line. None of those is a path anybody installs from.
LIVE_INSTALL_PATHS = (".github/workflows", "pyproject.toml", "README.md", "src")


def _test_job_steps():
    """The `test` job's steps, in order, as (name, body) pairs."""
    text = WORKFLOW.read_text()
    # The jobs are top-level two-space keys; take everything from `test:` up to
    # the next one so a later job's steps cannot be mistaken for this job's.
    start = text.index("\n  test:")
    rest = text[start + 1 :]
    nxt = re.search(r"\n  [a-zA-Z0-9_-]+:\n", rest)
    body = rest[: nxt.start()] if nxt else rest
    chunks = re.split(r"\n      - name: ", body)[1:]
    return [(c.split("\n", 1)[0].strip(), c) for c in chunks]


def test_the_workflow_exists():
    assert WORKFLOW.is_file(), WORKFLOW


def test_the_suite_runs_before_any_external_index_install():
    steps = _test_job_steps()
    names = [n for n, _ in steps]
    suite = next((i for i, (n, _) in enumerate(steps) if SUITE_STEP in n), None)
    assert suite is not None, f"no step runs the suite; steps are {names}"

    for i, (name, body) in enumerate(steps):
        if EXTERNAL_INSTALL.search(body) and i < suite:
            pytest.fail(
                f"step {i} ({name!r}) installs the package from outside this "
                f"checkout "
                f"before step {suite} ({names[suite]!r}) runs the suite. "
                "If that index is unreachable the job stops there and the suite "
                f"never runs. Steps are {names}"
            )


def test_an_external_index_install_cannot_gate_an_ordinary_push():
    """Whether a published mirror resolves is not a fact about this commit."""
    for name, body in _test_job_steps():
        if not EXTERNAL_INSTALL.search(body):
            continue
        assert "if:" in body and "github.event_name" in body, (
            f"step {name!r} installs the package from outside this checkout on "
            "every event. Gate it on the schedule/dispatch events that the "
            "published-artifact check is for, so an outage elsewhere does not "
            "fail this commit."
        )


def test_no_install_path_references_the_deleted_account():
    """An install from a deleted account's host is an install that cannot work.

    `ci.yml` installed `openai-agents-nano` from
    `https://pandeveloper001.github.io/openai-agents-nano-x402/simple/`. That
    account is gone and the package is on no other index -- README.md says so
    itself ("Until then `pip install openai-agents-nano` fails with 'No matching
    distribution found'"). So the weekly step could only fail, the smoke test
    behind it could never run, and the signal this workflow exists to give about
    what is installable was permanently red rather than absent.

    This law covers only paths somebody installs or imports from. A reference in
    `docs/`, `.ledger/`, `scripts/` or `audits/` is a record of a fork or an
    issue that really was created there, and rewriting history is not the fix.
    """
    offenders = []
    for rel in LIVE_INSTALL_PATHS:
        target = ROOT / rel
        files = sorted(target.rglob("*")) if target.is_dir() else [target]
        for f in files:
            if not f.is_file():
                continue
            try:
                text = f.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if DELETED_ACCOUNT.search(line):
                    offenders.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
    assert offenders == [], (
        "these install or import paths point at a deleted account, so they cannot "
        "work:\n  " + "\n  ".join(offenders)
    )


def test_the_published_install_the_weekly_check_uses_is_one_the_readme_offers():
    """The workflow and the README must name the same published artifact.

    The point of the weekly step is to find out whether what this project tells a
    reader to install still installs. A URL only the workflow knows about proves
    nothing about the Install section, and a reader following the README would be
    the one to discover it had rotted.
    """
    readme = README.read_text()
    urls = set()
    for _name, body in _test_job_steps():
        urls.update(re.findall(r"https://\S+?\.(?:whl|tar\.gz)", body))
    assert urls, (
        "no step installs a published artifact, so nothing checks whether the "
        "install path README.md offers still works"
    )
    for url in sorted(urls):
        assert url in readme, (
            f"ci.yml installs {url}, which README.md does not offer. The weekly "
            "check must exercise the install path a reader is actually given."
        )
