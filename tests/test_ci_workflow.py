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

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

SUITE_STEP = "Run project test suite"
EXTERNAL_INDEX = "--extra-index-url"


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
        if EXTERNAL_INDEX in body and i < suite:
            pytest.fail(
                f"step {i} ({name!r}) installs from an external package index "
                f"before step {suite} ({names[suite]!r}) runs the suite. "
                "If that index is unreachable the job stops there and the suite "
                f"never runs. Steps are {names}"
            )


def test_an_external_index_install_cannot_gate_an_ordinary_push():
    """Whether a published mirror resolves is not a fact about this commit."""
    for name, body in _test_job_steps():
        if EXTERNAL_INDEX not in body:
            continue
        assert "if:" in body and "github.event_name" in body, (
            f"step {name!r} installs from an external package index on every "
            "event. Gate it on the schedule/dispatch events that the mirror "
            "check is for, so an outage elsewhere does not fail this commit."
        )
