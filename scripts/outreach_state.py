#!/usr/bin/env python3
"""Derive the OUTREACH state from the forks themselves: what has already been delivered, to whom.

Why this exists: the branch list went stale silently (corrective 2026-09-16 16:34) and then the OUTREACH
list did exactly the same thing hours later - a runbook line said a target had been contacted once, while
the fork already carried two issues, and a third duplicate was filed. Both failures are the same shape: a
hand-written note cannot notice it has gone stale. The forks can.

This asks the API which issues exist on each of the agent's forks, in every state, with the title, so a
run sees what was actually sent before writing anything new.

Reads the token in Python (a shell round-trip truncates it) and prints only its length.

Usage: python3 scripts/outreach_state.py [--json OUT] [--min]      (exit 0 always: reporting, not a gate)
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
FORK_OWNER = "PANDeveloper001"
# Repos owned outright (not forks of a target) are excluded: their issues are not outreach to a third party.
SKIP = {"openai-agents-nano-x402", "nano-mcp", "nano-mcp-public", "rai-newsletter", "api"}


from gh_cred import token


def api(path: str, tok: str):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {tok}",
                                                      "User-Agent": "rai-agent",
                                                      "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the report here")
    ap.add_argument("--min", action="store_true", help="print only per-target counts")
    a = ap.parse_args()
    tok = token()
    if len(tok) < 50:
        print(f"TOKEN SUSPECT: {len(tok)} chars")
        return 0

    forks: list[dict] = []
    for page in range(1, 5):
        st, d = api(f"/users/{FORK_OWNER}/repos?per_page=100&page={page}&sort=pushed", tok)
        if st != 200 or not d:
            break
        for r in d:
            if r.get("fork") and r["name"] not in SKIP:
                forks.append({"name": r["name"], "parent": ((r.get("parent") or {}).get("full_name"))})

    rows = []
    for f in forks:
        st, d = api(f"/repos/{FORK_OWNER}/{f['name']}/issues?state=all&per_page=100", tok)
        issues = []
        if st == 200 and isinstance(d, list):
            for i in d:
                if i.get("pull_request"):
                    continue  # PRs are tracked by the drift scanner, not here
                issues.append({"number": i["number"], "state": i["state"],
                               "created": (i.get("created_at") or "")[:16], "title": i["title"]})
        rows.append({**f, "issues": issues, "count": len(issues)})

    contacted = [r for r in rows if r["count"]]
    print(f"token length {len(tok)} (93 = intact)")
    print(f"{len(rows)} third-party forks checked, {len(contacted)} carry a delivered issue\n")
    for r in sorted(rows, key=lambda r: (-r["count"], r["name"])):
        if not r["count"]:
            continue
        print(f"{r['parent'] or r['name']:45s} {r['count']} issue(s)")
        if not a.min:
            for i in r["issues"]:
                print(f"    #{i['number']:3d} {i['state']:6s} {i['created']}  {i['title'][:68]}")
    zero = [r["parent"] or r["name"] for r in rows if not r["count"]]
    if zero and not a.min:
        print(f"\nforks with no delivered issue ({len(zero)}): " + ", ".join(sorted(zero)))
    print(f"\nTOTAL delivered issues: {sum(r['count'] for r in rows)} across {len(contacted)} targets "
          f"(one per target is the rule; a target above 1 is a duplicate to close)")
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())