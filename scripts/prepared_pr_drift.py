#!/usr/bin/env python3
"""Drift-check every prepared PR fork branch against its upstream default branch.

Uses the GitHub compare API with the stored credential (see the open-integration-pr skill:
read the token in PYTHON - a shell sed round-trip silently truncates it to 13 chars and every
call then answers 401, which looks like "the API does not work keylessly").

For each fork branch this prints status / ahead_by / behind_by against upstream HEAD:
  - ahead_by >= 1 and behind_by == 0   -> CLEAN, safe to open a PR from
  - behind_by > 0 or diverged          -> DRIFTED, rebuild as a NEW -vN branch (never force-push)

Usage: python3 scripts/prepared_pr_drift.py targets.tsv
targets.tsv: upstream_owner/repo <TAB> fork_branch
"""
import json
import sys
import urllib.request

FORK_OWNER = "PANDeveloper001"


from gh_cred import token


def api(url, tok):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + tok, "User-Agent": "rai-agent/1.0",
        "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode()[:200]}


def main():
    path = sys.argv[1]
    tok = token()
    print(f"token length {len(tok)} (93 = intact)")
    rows = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        upstream, branch = line.split("\t")[:2]
        base = api(f"https://api.github.com/repos/{upstream}", tok).get("default_branch", "main")
        cmp_ = api(f"https://api.github.com/repos/{upstream}/compare/"
                   f"{base}...{FORK_OWNER}:{branch}?per_page=1", tok)
        if "_http_error" in cmp_:
            verdict = f"API {cmp_['_http_error']}"
        else:
            a, b = cmp_.get("ahead_by"), cmp_.get("behind_by")
            st = cmp_.get("status")
            if a and b == 0:
                verdict = f"CLEAN ahead {a} / behind 0"
            elif a == 0 and b == 0:
                verdict = "IDENTICAL (no commits to open)"
            else:
                verdict = f"DRIFTED status={st} ahead {a} / behind {b}"
        rows.append((upstream, branch, verdict))
        print(f"{upstream:48s} {branch:44s} {verdict}")
    clean = sum(1 for r in rows if r[2].startswith("CLEAN"))
    print(f"\n{len(rows)} branches: {clean} clean")


if __name__ == "__main__":
    main()
