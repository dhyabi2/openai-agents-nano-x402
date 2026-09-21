#!/usr/bin/env python3
"""Drift-check every prepared PR branch, deriving the target list from the forks themselves.

Why this exists: the first version took a hand-written TSV of (upstream, branch) pairs and reported
"13 clean" while silently omitting one branch and naming a superseded one, because a hand-written list
cannot notice that it has gone stale. This version asks the FORK which branches exist, keeps the newest
`-vN` per upstream target, and asks the compare API for the real status/ahead_by/behind_by.

Reads the token in Python (a shell `sed` round-trip truncates it and every call 401s, which looks exactly
like "the endpoint needs auth"); prints only its length.

Usage:  python3 scripts/prepared_pr_drift.py [--targets upstream[,upstream...]] [--json out.json]

Exit code is 0 always: this is a reporting tool, never a gate that can strand a run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
FORK_OWNER = "PANDeveloper001"
SKIP_REPOS = {"openai-agents-nano-x402", "nano-mcp", "nano-mcp-public", "rai-newsletter", "api",
              "Agent402", "gold-402", "awesome-x402", "x402", "nanodir", "pyfile-toolkit",
              "nano-llm-api", "wg-domain-discovery", "wg-identity"}

# Only branches this agent prepared. A fork inherits every branch of its parent, and a plain name
# pattern also catches upstream's own branches; unchecked, that reports "6 needing attention" for
# branches nobody here ever prepared. Ask the API which branches the fork's OWNER authored.
# `specs/exact-nano-` is in the list on purpose: it is a separate contribution from the docs row and
# was the artifact a hand-written resume list silently dropped (corrective action 2026-09-16 16:34).
MY_PATTERNS = (r"^add-[a-z0-9]", r"^docs/list-", r"^specs/exact-nano", r"^add-nano-x402")
# Targets whose prepared set must never silently shrink again; a run that finds fewer is reported loudly.
EXPECTED = {
    "x402-foundation/x402": 2,  # docs/list-openai-agents-nano-* and specs/exact-nano-mainnet
}


def is_mine(repo: str, branch: str, tok: str) -> bool:
    """True when the newest commit on this branch is this agent's work.

    `author.login` is NULL for these commits (GitHub matched the author email to no account), so the
    identity check that works is the commit author/committer name — every prepared branch carries "Rai".
    Verified 2026-09-16: a login-only check silently dropped 7 of 17 real prepared branches.
    """
    st, d = api(f"/repos/{FORK_OWNER}/{repo}/commits/{branch}?per_page=1", tok)
    if st != 200 or not isinstance(d, dict):
        return False
    c = d.get("commit") or {}
    names = " ".join(str((c.get(k) or {}).get("name") or "") for k in ("author", "committer"))
    login = ((d.get("author") or {}).get("login") or "")
    return "rai" in names.lower() or login.lower() == FORK_OWNER.lower()


from gh_cred import token


def api(path: str, tok: str, raw: bool = False):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {tok}",
                                                      "User-Agent": "rai-agent",
                                                      "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, (r.read() if raw else json.loads(r.read()))
    except urllib.error.HTTPError as e:
        return e.code, (e.read() if raw else {})


def fork_branches(tok: str) -> dict[str, list[str]]:
    """{fork repo name: [branch, ...]} for every fork the agent owns."""
    out: dict[str, list[str]] = {}
    for page in range(1, 6):
        st, d = api(f"/users/{FORK_OWNER}/repos?per_page=100&page={page}&sort=pushed", tok)
        if st != 200 or not d:
            break
        for r in d:
            name = r["name"]
            if not r.get("fork"):
                continue
            branches: list[str] = []
            # The fork has 783 branches. The old bound was range(1, 8) = 700, so the LAST 83 were
            # dropped silently - and specs/exact-nano-mainnet, one of the two artifacts that carry
            # this repo's adoption argument, sat past the cutoff and never appeared in a single
            # drift report (corrective action 2026-09-16 16:34). A full final page is now reported
            # instead of trusted.
            max_pages = 12
            for page2 in range(1, max_pages + 1):
                st2, d2 = api(f"/repos/{FORK_OWNER}/{name}/branches?per_page=100&page={page2}", tok)
                if st2 != 200 or not isinstance(d2, list) or not d2:
                    break
                branches += [b["name"] for b in d2 if isinstance(b, dict) and b.get("name")]
                if len(d2) < 100:
                    break  # short page = last page, regardless of the bound
            else:
                print(f"!! {name}: hit the {max_pages}-page ceiling with full pages ({len(branches)} "
                      f"branches read); the list may be truncated - raise the bound before trusting it")
            if branches:
                out[name] = branches
    return out


def newest(branches: list[str], repo: str, tok: str) -> list[str]:
    """Prepared-branch candidates: this agent's own branches, newest -vN preferred."""
    cands = [b for b in branches if any(re.match(p, b) for p in MY_PATTERNS) and is_mine(repo, b, tok)]
    by_base: dict[str, str] = {}
    for b in cands:
        base, _, ver = b.partition("-v")
        n = int(ver) if ver.isdigit() and base in by_base or (ver.isdigit()) else 0
        cur = by_base.get(base)
        if cur is None:
            by_base[base] = b
            continue
        curver = int(cur.partition("-v")[2]) if "-v" in cur and cur.partition("-v")[2].isdigit() else 0
        if (ver.isdigit() and int(ver) > curver):
            by_base[base] = b
    # a spec branch and a docs branch on the same fork are different targets: keep both
    return sorted(by_base.values())


def upstream_of(fork_name: str, tok: str) -> str | None:
    st, d = api(f"/repos/{FORK_OWNER}/{fork_name}", tok)
    if st == 200 and isinstance(d, dict):
        p = d.get("parent") or {}
        return p.get("full_name")
    return None


def compare(upstream: str, branch: str, tok: str) -> dict:
    st, d = api(f"/repos/{upstream}/compare/HEAD...{FORK_OWNER}:{branch}", tok)
    if st == 200 and isinstance(d, dict):
        # the head sha goes in the report so the runbook can name the exact commit without a second call
        commits = d.get("commits") or []
        head = (commits[-1] or {}).get("sha") if commits else None
        return {"status": d.get("status"), "ahead_by": d.get("ahead_by"), "behind_by": d.get("behind_by"),
                "files": len(d.get("files") or []), "head": (head or "")[:8]}
    return {"status": f"API {st}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", help="comma-separated upstream repos to check (default: every fork)")
    ap.add_argument("--json", help="write the report as JSON here")
    a = ap.parse_args()
    tok = token()
    print(f"token length {len(tok)} ({len(tok)} = intact)" if len(tok) > 50 else f"TOKEN SUSPECT: {len(tok)} chars")

    forks = fork_branches(tok)
    want = set(a.targets.split(",")) if a.targets else None
    rows = []
    for fork_name, branches in sorted(forks.items()):
        up = upstream_of(fork_name, tok)
        if not up or up.startswith(f"{FORK_OWNER}/"):
            continue
        if want and up not in want:
            continue
        for b in newest(branches, fork_name, tok):
            rows.append({"upstream": up, "fork": fork_name, "branch": b, **compare(up, b, tok)})

    clean = [r for r in rows if r.get("status") == "ahead" and r.get("behind_by") == 0]
    for r in sorted(rows, key=lambda r: (r["upstream"], r["branch"])):
        print(f"{r['upstream']:45s} {r['branch']:42s} {str(r.get('status')):9s} "
              f"ahead {r.get('ahead_by')} / behind {r.get('behind_by')} files {r.get('files')}")
    print(f"\n{len(rows)} prepared branches, {len(clean)} clean (ahead / behind 0), "
          f"{len(rows) - len(clean)} needing attention")

    # A hand-written resume list is what let this list go stale (corrective 2026-09-16 16:34): it named
    # an older x402 docs branch and dropped the spec branch entirely. Count key targets and shout.
    have: dict[str, int] = {}
    for r in rows:
        have[r["upstream"]] = have.get(r["upstream"], 0) + 1
    missing = {k: (v, have.get(k, 0)) for k, v in EXPECTED.items() if have.get(k, 0) < v}
    if missing:
        for k, (want, got) in sorted(missing.items()):
            print(f"!! {k}: expected {want} prepared branches, found {got} - the prepared set SHRANK; "
                  f"check the fork's branch names before opening anything")
    else:
        print(f"key targets complete: " + ", ".join(f"{k} {have[k]}/{v}" for k, v in sorted(EXPECTED.items())))
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
