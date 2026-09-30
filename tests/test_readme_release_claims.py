"""The pinned install path the README offers must be able to satisfy what the README documents.

`README.md` presents the **v0.1.0 GitHub release** as "the immutable, public install path
(works today)", and it is the only published install path: there is no PyPI project yet. But the
source tree has moved on since that tag, and the project version never left `0.1.0`, so nothing
about a `pip install` of that wheel signals the gap.

Measured against the real release asset (`tests/data/release-v0.1.0-contents.json`, recorded by
downloading it): the wheel ships `__init__` and `tool` only, and carries no console script. The
tree also ships `mandate`, and `pyproject.toml` declares a `mandate` CLI. So a reader who followed
the Install section and then the operator-mandate section got:

    $ mandate keygen --out operator.key
    mandate: command not found
    >>> make_nano_x402_tool(mandate_path="mandate.json")
    TypeError: make_nano_x402_tool() got an unexpected keyword argument 'mandate_path'
    >>> import openai_agents_nano.mandate
    ModuleNotFoundError: No module named 'openai_agents_nano.mandate'

This law does not judge which way the gap is closed -- re-cutting the release would satisfy it by
making the fixture's module list grow. It only refuses the state where the README documents a
feature the pinned artifact cannot provide and says nothing about it. It is derived from the
fixture and `pyproject.toml`, so a module or CLI added later is covered without editing this file.
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
RELEASE = json.loads((ROOT / "tests/data/release-v0.1.0-contents.json").read_text())
TAG = RELEASE["release_tag"]

# A paragraph that tells the reader the pinned release lacks something.
_NEGATION = re.compile(
    r"does not (?:include|carry|ship|contain)|predates|is not in|absent from|"
    r"not present in|only in the source|newer than",
    re.I,
)


def _src_modules() -> set[str]:
    pkg = ROOT / "src" / "openai_agents_nano"
    return {p.stem for p in pkg.glob("*.py")}


def _declared_scripts() -> set[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return set(data.get("project", {}).get("scripts", {}))


def _paragraphs() -> list[str]:
    return [p for p in re.split(r"\n\s*\n", README)]


def _has_caveat(feature: str) -> bool:
    """A paragraph that names the tag, the feature, and says the tag lacks it."""
    for para in _paragraphs():
        if TAG in para and feature.lower() in para.lower() and _NEGATION.search(para):
            return True
    return False


def _readme_documents(feature: str) -> bool:
    """The README documents the feature as something a reader can use."""
    return bool(
        re.search(rf"\b{re.escape(feature)}_path\s*=", README)
        or re.search(rf"^\s*{re.escape(feature)} \w+", README, re.M)      # a CLI invocation
        or re.search(rf"openai_agents_nano/{re.escape(feature)}\.py", README)
    )


def test_release_fixture_is_real_measured_data():
    """Guard the fixture itself: a hand-emptied module list would disarm every check below."""
    assert RELEASE["modules"], "the fixture lists no modules; re-record it from the release asset"
    assert "tool" in RELEASE["modules"], RELEASE["modules"]
    assert re.fullmatch(r"[0-9a-f]{64}", RELEASE["asset_sha256"]), "asset_sha256 must be a sha256"


def test_readme_still_offers_the_pinned_install():
    """The checks below are only meaningful while the README pins that release."""
    assert f"releases/download/{TAG}/" in README, (
        "the README no longer points at the pinned release asset; if the install path changed, "
        "re-record the fixture and revisit this law rather than deleting it."
    )


def test_modules_the_pinned_release_lacks_are_flagged():
    missing = sorted(_src_modules() - set(RELEASE["modules"]))
    for feature in missing:
        if not _readme_documents(feature):
            continue  # documented nowhere, so no reader is misled
        assert _has_caveat(feature), (
            f"README documents {feature!r} (src/openai_agents_nano/{feature}.py) but the "
            f"published {TAG} wheel does not ship it, and no paragraph mentioning {TAG} says so. "
            f"A reader who installs the pinned wheel and follows that section gets "
            f"ModuleNotFoundError. Either say plainly that {TAG} predates {feature}, or publish a "
            f"release that carries it and re-record tests/data/release-{TAG}-contents.json."
        )


def test_console_scripts_the_pinned_release_lacks_are_flagged():
    missing = sorted(_declared_scripts() - set(RELEASE["console_scripts"]))
    for script in missing:
        assert _has_caveat(script), (
            f"pyproject declares the {script!r} console script and the README shows it being run, "
            f"but the published {TAG} wheel installs no entry point, so the command does not exist "
            f"after the README's own install step. Say so next to {TAG}, or publish a release that "
            f"carries it."
        )
