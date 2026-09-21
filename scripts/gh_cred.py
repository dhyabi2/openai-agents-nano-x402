"""Shared GitHub credential helper — picks a github.com token from
~/.git-credentials regardless of line order, so the drift/measure scripts
never silently lose a run to a credential reorder."""

import os, json, urllib.request, urllib.error


CRED_PATH = os.path.expanduser("~/.git-credentials")
GH_HOST = "github.com"


def token() -> str:
    """Return a GitHub API token from ~/.git-credentials, preferring a
    github.com entry.  If only the forge (127.0.0.1) entry exists, return
    it anyway so pushes during prep work still function."""
    lines = open(CRED_PATH).read().strip().split("\n")
    # Prefer GitHub entries
    for line in lines:
        if GH_HOST in line:
            return _extract(line)
    # Fall back to any (forge)
    if lines:
        return _extract(lines[0])
    raise RuntimeError(f"No credentials found in {CRED_PATH}")


def _extract(line: str) -> str:
    """Extract the password from a git-credential-format line."""
    return line.split("://", 1)[1].split("@")[0].split(":", 1)[1]


def verify(tok: str | None = None) -> bool:
    """Verify the token is valid against GitHub's /user endpoint."""
    t = tok or token()
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {t}", "User-Agent": "rai-cred-check"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=10))
        return bool(d.get("login"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return False