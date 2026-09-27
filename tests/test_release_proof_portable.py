"""The release-readiness proof must be runnable by someone who is not this agent.

`tests/release_install_offline.py` is the only thing in this repository that proves the PUBLISHED
wheel installs into a fresh environment and yields a working SDK tool. It resolved its build tool as

    UV = os.environ.get("UV", "/root/.hermes/bin/uv")

-- a path that exists on one agent box and nowhere else. Anywhere else, including a contributor's
laptop and this repository's own CI (whose workflows get uv from `pip install uv`, so it lands on
PATH), the first subprocess raised

    FileNotFoundError: [Errno 2] No such file or directory: '/root/.hermes/bin/uv'

before a single check ran. The proof of the published package was unrunnable by anyone who installs
the published package.

These laws are collected by pytest, unlike the offline script itself, so the property is checked on
every run rather than only when someone remembers to invoke that file.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
SCRIPT = TESTS / "release_install_offline.py"

# Roots that belong to the swarm's own boxes and to nothing a reader of this repository has.
MACHINE_PATHS = ("/root/", "/srv/swarm", "/opt/swarm", "/var/lib/swarm")


def _docstring_nodes(tree):
    """Every string Constant that is a module, class or function docstring."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            yield body[0].value


def load_script():
    """Import the offline script as a module. It is guarded by __main__, so nothing runs."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("release_install_offline", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_no_test_file_hardcodes_an_absolute_machine_path():
    """The root cause, stated as a property of the tree: a published test may not depend on a path
    that exists only on the machine that wrote it.

    Read through the AST and over string LITERALS only, so that a comment or a docstring explaining
    this very defect is not itself a violation -- the property is about what the code uses, not about
    what the prose mentions. This file is excluded because the needles below are its own literals.
    """
    offenders = []
    for path in sorted(TESTS.glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        docstrings = {id(d) for d in _docstring_nodes(tree)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            for bad in MACHINE_PATHS:
                if bad in node.value:
                    offenders.append(f"{path.name}:{node.lineno}: {node.value!r}")
    assert not offenders, (
        "a test uses a path that exists on one machine only:\n" + "\n".join(offenders))


def test_the_release_proof_resolves_uv_rather_than_assuming_it():
    """find_uv() must exist and must find uv where it actually is."""
    mod = load_script()
    assert hasattr(mod, "find_uv"), "release_install_offline has no find_uv(); it assumes a path"
    resolved = mod.find_uv()
    assert os.path.exists(resolved), f"find_uv() returned a path that does not exist: {resolved!r}"


def test_an_explicit_uv_still_wins():
    """$UV is how the agent box, or anyone with uv somewhere unusual, points this at its own copy."""
    mod = load_script()
    before = os.environ.get("UV")
    os.environ["UV"] = "/some/deliberate/path/uv"
    try:
        assert mod.find_uv() == "/some/deliberate/path/uv"
    finally:
        if before is None:
            os.environ.pop("UV", None)
        else:
            os.environ["UV"] = before


def test_a_missing_uv_says_what_is_missing():
    """With no uv anywhere, the failure must name uv and how to get it -- not surface as a
    FileNotFoundError on a path the reader never chose."""
    mod = load_script()
    before_uv, before_path = os.environ.get("UV"), os.environ.get("PATH", "")
    os.environ.pop("UV", None)
    os.environ["PATH"] = ""
    try:
        with pytest.raises(SystemExit) as e:
            mod.find_uv()
        assert "uv" in str(e.value)
        assert "PATH" in str(e.value) or "UV" in str(e.value)
    finally:
        os.environ["PATH"] = before_path
        if before_uv is not None:
            os.environ["UV"] = before_uv


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed here")
def test_the_release_proof_runs_end_to_end_with_nothing_configured():
    """The law that matters most: with no UV set and no arguments, the proof runs and passes. This is
    exactly the invocation that used to die on line 34 before running a check."""
    env = {k: v for k, v in os.environ.items() if k != "UV"}
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True,
                       timeout=900, env=env)
    assert r.returncode == 0, f"the release proof failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}"
    assert "RELEASE_INSTALL_OK" in r.stdout
