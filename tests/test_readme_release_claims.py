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

import pytest

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
# This law reads the commands out of every fenced code block in the README and
# in docs/ (any info string - bash, sh, console, none), so it covers any section
# or page added later, and it is derived from `project.name` rather than a
# literal. Prose is deliberately not parsed: the Install section has to be able
# to say that the bare-name install fails without tripping the check.
#
# A command is recognised however it is spelled: pip, pip3, pip3.11,
# `python -m pip`, `uv pip install`, `uv add`, behind a `$ ` prompt, `sudo` or
# env assignments, chained after `&&`/`;`/`||`, or split over `\` line
# continuations; a requirement is read through version specifiers (`==`, `>=`,
# `~=`), extras and markers. `_BROKEN_SPELLINGS` below proves each of those is
# caught, so a parser regression shows up as a failing fixture, not a silent pass.
#
# It lapses by itself the day the name is registered - at that point the fixture
# `pypi_registered` below is flipped to True in the same commit that publishes,
# and bare-name installs are legal again.

PYPI_REGISTERED = False
"""Whether `project.name` resolves on PyPI. Flip this in the commit that
publishes, together with the README's install paragraph."""

_FENCE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.S | re.M)
_CHAIN = {"&&", "||", ";", "|", "&", ";;", "(", ")"}
# pip/uv options that take the next token as their value, so it is not a requirement.
_VALUED = {
    "-r", "--requirement", "-c", "--constraint", "-e", "--editable", "-i", "--index-url",
    "--extra-index-url", "-f", "--find-links", "-t", "--target", "--python", "-p",
    "--prefix", "--root", "--src", "--upgrade-strategy", "--platform", "--python-version",
    "--implementation", "--abi", "--only-binary", "--no-binary", "--config-settings", "-C",
    "--index", "--default-index", "--group", "--optional", "--extra", "--dev-group",
    "--package", "--directory", "--project", "--cache-dir", "--log", "--proxy", "--trusted-host",
    "--python-platform", "--index-strategy", "--keyring-provider", "--exclude-newer",
}
_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")


def _normalise_dist(name: str) -> str:
    """PEP 503 normalisation, so openai_agents_nano == openai-agents-nano."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _project_name() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return _normalise_dist(data["project"]["name"])


def _documents() -> dict[str, str]:
    docs = {"README.md": README}
    for path in sorted((ROOT / "docs").rglob("*.md")):
        docs[str(path.relative_to(ROOT))] = path.read_text()
    return docs


def _fenced_lines(text: str) -> list[str]:
    """Every logical line inside a fenced block, `\\` continuations joined."""
    lines = []
    for _, body in _FENCE.findall(text):
        lines.extend(re.sub(r"\\[ \t]*\r?\n", " ", body).splitlines())
    return lines


def _commands(line: str) -> list[list[str]]:
    """The simple commands on one shell line, split at `&&`, `;`, `|` ..."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        tokens = list(lexer)
    except ValueError:
        return []  # an unbalanced quote is not a command this law can read
    commands, current = [], []
    for token in tokens:
        if token in _CHAIN:
            commands.append(current)
            current = []
        else:
            current.append(token)
    commands.append(current)
    return [c for c in commands if c]


def _install_args(tokens: list[str]) -> list[str] | None:
    """The arguments of an install command (pip/pip3/python -m pip/uv pip install,
    uv add), or None when the tokens are some other command."""
    t = list(tokens)
    while t and (t[0] in {"$", "sudo", ">", "%", "!"} or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t[0])):
        t.pop(0)
    if t and t[0][:1] in "!%$" and len(t[0]) > 1:
        t[0] = t[0][1:]  # `!pip` (notebook), `$pip` (prompt without a space)
    if not t:
        return None
    head = t[0].rsplit("/", 1)[-1]
    if re.fullmatch(r"(?:python|py)[0-9.]*(?:\.exe)?", head) and t[1:3] == ["-m", "pip"]:
        t = t[2:]
        head = "pip"
    if re.fullmatch(r"pip[0-9.]*(?:\.exe)?", head):
        rest = t[1:]
    elif head == "uv" and t[1:2] == ["pip"]:
        rest = t[2:]
    elif head == "uv" and t[1:2] == ["add"]:
        return t[2:]
    else:
        return None
    while rest and rest[0].startswith("-"):  # global options before the subcommand
        rest = rest[2:] if rest[0] in _VALUED else rest[1:]
    return rest[1:] if rest[:1] == ["install"] else None


def _requirements(args: list[str]) -> list[str]:
    """Requirement specifiers among install arguments, direct references dropped."""
    found, i = [], 0
    while i < len(args):
        token = args[i]
        if token.startswith("-"):
            i += 2 if token in _VALUED else 1
            continue
        following = args[i + 1] if i + 1 < len(args) else ""
        if token.endswith("@") or following.startswith("@"):
            i += 1  # `name @ url`, unquoted: the URL token(s) are skipped below
            continue
        if token == "@" or "://" in token or "@" in token or token.startswith((".", "/", "~")):
            i += 1  # a direct reference (URL, path, or PEP 508 `name[extra] @ git+...`)
            continue
        found.append(token)
        i += 1
    return found


def _bare_installs(text: str, project: str) -> list[str]:
    """Each fenced command in `text` that installs `project` by bare PyPI name."""
    hits = []
    for line in _fenced_lines(text):
        for command in _commands(line):
            args = _install_args(command)
            if args is None:
                continue
            for req in _requirements(args):
                match = _NAME.match(req)
                if match and _normalise_dist(match.group()) == project:
                    hits.append(" ".join(command))
                    break
    return hits


def _looks_like_install(command: list[str]) -> bool:
    words = {w.rsplit("/", 1)[-1].lstrip("!%$") for w in command}
    return bool(words & {"install", "add"}) and any(
        re.fullmatch(r"pip[0-9.]*|uv", w) for w in words)


# Each way the broken install has been, or could be, written. Every one must be caught.
_BROKEN_SPELLINGS = [
    "```bash\npip install openai-agents-nano\n```",
    '```bash\npip install "openai-agents-nano[x402]"\n```',
    "```bash\npip install openai_agents_nano==0.1.0\n```",
    "```bash\npip install 'openai-agents-nano>=0.1'\n```",
    "```bash\npip install 'Openai.Agents_Nano~=0.1; python_version>\"3.9\"'\n```",
    "```bash\npip3 install openai-agents-nano\n```",
    "```bash\npip3.11 install -U openai-agents-nano\n```",
    "```bash\npython3 -m pip install --upgrade openai-agents-nano\n```",
    "```bash\nuv pip install openai-agents-nano\n```",
    "```bash\nuv pip install --python /tmp/v/bin/python openai-agents-nano[x402]\n```",
    "```bash\nuv add openai-agents-nano\n```",
    "```bash\nuv add 'openai-agents-nano[x402]>=0.1'\n```",
    "```bash\npython3 -m venv .venv && . .venv/bin/activate && pip install openai-agents-nano\n```",
    "```bash\ncd /tmp; pip install openai-agents-nano || echo failed\n```",
    "```bash\npip install feeless402 \\\n  openai-agents-nano\n```",
    "```bash\npip install \\\n  --extra-index-url https://example.invalid/simple \\\n  openai-agents-nano\n```",
    "```sh\npip install openai-agents-nano\n```",
    "```shell\npip install openai-agents-nano\n```",
    "```console\n$ pip install openai-agents-nano\nERROR: ...\n```",
    "```\npip install openai-agents-nano\n```",
    "~~~bash\npip install openai-agents-nano\n~~~",
    "```python\n!pip install openai-agents-nano\n```",
    "```bash\nPIP_NO_CACHE_DIR=1 sudo pip install openai-agents-nano\n```",
    "   ```bash\n   pip install openai-agents-nano\n   ```",
]

# Installs that are fine today, and prose: none of these may be flagged.
_WORKING_SPELLINGS = [
    'Until then `pip install openai-agents-nano` fails with "No matching distribution found".',
    "```bash\npip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/"
    "v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl\n```",
    '```bash\npip install "openai_agents_nano[x402] @ git+https://github.com/dhyabi2/openai-agents-nano-x402"\n```',
    "```bash\npip install openai-agents-nano@git+https://github.com/dhyabi2/openai-agents-nano-x402\n```",
    "```bash\npip install openai-agents-nano @ git+https://github.com/dhyabi2/openai-agents-nano-x402\n```",
    "```bash\nuv pip install --python /tmp/v/bin/python \\\n"
    '  "git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0"\n```',
    "```bash\npip install -e . && pip install openai-agents x402\n```",
    "```bash\n# pip install openai-agents-nano  (not on PyPI yet)\npip install -e .\n```",
    "```bash\npip install openai-agents-nano-extra\n```",
    "```bash\necho pip install openai-agents-nano\n```",
]


@pytest.mark.parametrize("text", _BROKEN_SPELLINGS)
def test_every_spelling_of_the_bare_name_install_is_caught(text):
    assert _bare_installs(text, _normalise_dist("openai-agents-nano")), text


@pytest.mark.parametrize("text", _WORKING_SPELLINGS)
def test_working_installs_and_prose_are_not_flagged(text):
    assert not _bare_installs(text, _normalise_dist("openai-agents-nano")), text


def test_the_readme_installs_something_so_this_law_can_see_it():
    """Guard the parser: every fenced line that looks like an install in the README
    and docs must be read as one, and the README must contain some."""
    seen = 0
    for name, text in _documents().items():
        for line in _fenced_lines(text):
            for command in _commands(line):
                if _install_args(command) is not None:
                    seen += name == "README.md"
                elif _looks_like_install(command):
                    raise AssertionError(
                        f"{name}: `{' '.join(command)}` looks like an install but this parser "
                        f"does not read it; teach the parser that spelling rather than "
                        f"deleting the law below.")
    assert seen, (
        "no install command was parsed out of the README's fenced blocks; the block or "
        "command shape changed, so fix this parser rather than deleting the law below."
    )


def test_no_readme_command_installs_this_project_by_bare_pypi_name():
    if PYPI_REGISTERED:
        return  # the name resolves; a bare install is a real install path again
    project = _project_name()
    for name, text in _documents().items():
        hits = _bare_installs(text, project)
        assert not hits, (
            f"{name} runs `{hits[0]}`, which installs {project!r} by bare name from PyPI. "
            f"The README's own Install section says that name is not registered, so this "
            f"command fails with 'No matching distribution found' and the reader gets no "
            f"payer at all.\n"
            f"Install from source instead, keeping any extra:\n"
            f'  pip install "openai_agents_nano[x402] @ '
            f'git+https://github.com/dhyabi2/openai-agents-nano-x402"\n'
            f"When the PyPI name is registered, flip PYPI_REGISTERED in this file in the "
            f"same commit that publishes."
        )
