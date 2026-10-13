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
import shlex
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


# --- The README's own install commands must be runnable ----------------------
#
# The Install section above states plainly that `pip install openai-agents-nano`
# fails with "No matching distribution found - this project is not on PyPI, and
# the name is not registered", because the PyPI project can only be created by a
# human with a PyPI login. A later section nonetheless opened with that very
# command (`pip install "openai-agents-nano[x402]"`), so a reader who started at
# the official-SDK section - which is self-contained, with its own install block
# and its own imports - got that error and no payer at all. Measured in a clean
# venv:
#
#     $ pip install "openai-agents-nano[x402]"
#     ERROR: Could not find a version that satisfies the requirement
#            openai-agents-nano[x402] (from versions: none)
#     ERROR: No matching distribution found for openai-agents-nano[x402]
#
# This law reads the commands out of the README's own fenced `bash` blocks, so it
# covers any section added later, and it is derived from `project.name` rather
# than a literal. Prose is deliberately not parsed: the Install section has to be
# able to say that the bare-name install fails without tripping the check.
#
# It lapses by itself the day the name is registered - at that point the fixture
# `pypi_registered` below is flipped to True in the same commit that publishes,
# and bare-name installs are legal again.

PYPI_REGISTERED = False
"""Whether `project.name` resolves on PyPI. Flip this in the commit that
publishes, together with the README's install paragraph."""

_PIP_INSTALL = re.compile(r"^\s*(?:\$\s*)?(?:python[0-9.]*\s+-m\s+)?pip\s+install\s+(.*)$", re.M)


def _normalise_dist(name: str) -> str:
    """PEP 503 normalisation, so openai_agents_nano == openai-agents-nano."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _project_name() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return _normalise_dist(data["project"]["name"])


def _bash_blocks() -> list[str]:
    return re.findall(r"```bash\n(.*?)```", README, re.S)


def _install_requirements() -> list[tuple[str, str]]:
    """(requirement, whole command) for every requirement a README bash block installs."""
    found = []
    for block in _bash_blocks():
        for args in _PIP_INSTALL.findall(block):
            command = args.strip()
            try:
                tokens = shlex.split(command, comments=True)
            except ValueError:
                continue  # an unbalanced quote is not an install this law can read
            for token in tokens:
                if token.startswith("-"):
                    continue
                found.append((token, command))
    return found


def test_the_readme_installs_something_so_this_law_can_see_it():
    """Guard the parser: a README whose bash blocks stopped parsing would disarm the law."""
    assert _install_requirements(), (
        "no `pip install` requirement was parsed out of the README's bash blocks; "
        "the fenced-block or command shape changed, so fix this parser rather than "
        "deleting the law below."
    )


def test_no_readme_command_installs_this_project_by_bare_pypi_name():
    if PYPI_REGISTERED:
        return  # the name resolves; a bare install is a real install path again
    project = _project_name()
    for requirement, command in _install_requirements():
        if "://" in requirement or "@" in requirement:
            continue  # a direct reference (URL, or PEP 508 `name[extra] @ git+...`)
        named = _normalise_dist(re.sub(r"\[.*?\]", "", requirement).split("[")[0])
        assert named != project, (
            f"README runs `pip install {requirement}`, which installs {project!r} by bare "
            f"name from PyPI. The README's own Install section says that name is not "
            f"registered, so this command fails with 'No matching distribution found' and "
            f"the reader gets no payer at all. Full command: `pip install {command}`.\n"
            f"Install from source instead, keeping any extra:\n"
            f'  pip install "openai_agents_nano[x402] @ '
            f'git+https://github.com/dhyabi2/openai-agents-nano-x402"\n'
            f"When the PyPI name is registered, flip PYPI_REGISTERED in this file in the "
            f"same commit that publishes."
        )
