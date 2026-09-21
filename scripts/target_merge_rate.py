#!/usr/bin/env python3
"""Rank the prepared branches by whether the target actually MERGES, not by how nice the list looks.

A prepared branch is only worth a maintainer's attention if that maintainer merges. This measures each
target's merge rate from its own closed-PR history (the last three active months) and flags the ones whose
branches are effectively dead on arrival.

Why: on 2026-09-16 a run prepared/rebuilt branches for targets that had stopped merging months earlier, and
a separate branch sat unopened on a repo pushed in 2026-05 (13 weeks quiet, no closed PRs) - i.e. effort
spent on surfaces that cannot convert. The measurement belongs in the pipeline, before a branch is prepared
or re-verified, not in a runbook note.

Usage: python3 scripts/target_merge_rate.py [--json .ledger/tmp/drift_all.json] [--out .ledger/target-health.md]
Exit code 0 always: reporting tool.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import urllib.error
import urllib.request

UA = {"User-Agent": "rai-agent"}
API = "https://api.github.com"


from gh_cred import token


TOK = token()
_ERRORS: list[str] = []


def get(path: str) -> dict | list | None:
    """GET with the token. A refused/failed call returns None AND records the reason.

    This matters: unauthenticated calls are rate-limited to 60/hour, and when that limit hit, this script
    silently reported 'QUIET - no closed PRs ever' and 'stars ?' for repos that demonstrably merge 90% -
    a confident wrong answer is worse than no answer. Callers must treat _ERRORS as fatal for the row.
    """
    headers = dict(UA)
    if TOK:
        headers["Authorization"] = f"Bearer {TOK}"
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        _ERRORS.append(f"{path} -> HTTP {e.code}")
        return None
    except Exception as e:
        _ERRORS.append(f"{path} -> {type(e).__name__}")
        return None


def repo_health(up: str) -> dict:
    d = get(f"/repos/{up}") or {}
    stale_days = None
    if d.get("pushed_at"):
        pushed = dt.datetime.strptime(d["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        stale_days = (dt.datetime.now(dt.timezone.utc) - pushed).days
    return {"stars": d.get("stargazers_count"), "pushed": (d.get("pushed_at") or "")[:10],
            "quiet_days": stale_days, "archived": d.get("archived")}


def merge_rate(up: str) -> dict:
    """merged/closed per month from the target's own PR history."""
    m: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for page in range(1, 4):
        d = get(f"/repos/{up}/pulls?state=closed&per_page=100&page={page}&sort=updated&direction=desc")
        if not isinstance(d, list) or not d:
            break
        for p in d:
            slot = m[(p.get("updated_at") or "")[:7]]
            slot[0] += 1
            if p.get("merged_at"):
                slot[1] += 1
    months = sorted(m, reverse=True)[:3]
    merged = sum(m[k][1] for k in months)
    closed = sum(m[k][0] for k in months)
    return {"months": months, "per_month": {k: f"{m[k][1]}/{m[k][0]}" for k in months},
            "merged": merged, "closed": closed,
            "rate": (merged / closed) if closed else None}


def verdict(h: dict, r: dict, errors: list[str]) -> str:
    if not h.get("pushed") or not r["months"]:
        return "UNMEASURED - API calls failed; do NOT read this as 'no merges'"
    if h.get("archived"):
        return "DEAD - archived"
    if not r["closed"]:
        return "QUIET - no closed PRs ever; nothing has been merged here"
    if r["rate"] is not None and r["rate"] >= 0.5:
        return "MERGES - worth a click"
    if r["rate"] is not None and r["rate"] >= 0.15:
        return "SOMETIMES - keep if the fit is exact"
    if h.get("quiet_days") and h["quiet_days"] > 60:
        return "DEAD - no push in %d days and merges stopped" % h["quiet_days"]
    return "BLACK HOLE - merges have stopped; a branch here stays open"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=".ledger/tmp/drift_all.json")
    ap.add_argument("--out", default=".ledger/target-health.md")
    a = ap.parse_args()
    rows = json.load(open(a.json))
    up = {}
    for r in rows:
        if r.get("status") == "ahead" and r.get("behind_by") == 0:
            up.setdefault(r["upstream"], []).append(r["branch"])

    out_rows = []
    for target in sorted(up):
        h, r = repo_health(target), merge_rate(target)
        n_err = len(_ERRORS)
        v = verdict(h, r, _ERRORS[n_err:])
        out_rows.append({"upstream": target, "branches": up[target], **h, **r, "verdict": v,
                         "api_error": v.startswith("UNMEASURED")})

    if _ERRORS:
        print(f"!! {len(_ERRORS)} API call(s) failed; affected rows read UNMEASURED, not 'quiet'")
        for e in _ERRORS[:5]:
            print(f"   {e}")
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Target health - does this repo actually merge?", "",
             f"Generated {now} by `scripts/target_merge_rate.py` from each target's own closed-PR history.",
             "A prepared branch is worth a click only where the second column says MERGES.", "",
             "| target | verdict | merged/closed (3 months) | per month | stars | last push | branches |",
             "|---|---|---|---|---|---|---|"]
    for o in sorted(out_rows, key=lambda o: -(o["rate"] or 0)):
        rate = f"{o['merged']}/{o['closed']}" if o["closed"] else "0/0"
        lines.append(f"| `{o['upstream']}` | {o['verdict']} | {rate} | "
                     f"{', '.join(f'{k} {v}' for k, v in o['per_month'].items())} | {o['stars']} | "
                     f"{o['pushed']} | {len(o['branches'])} |")
    open(a.out, "w").write("\n".join(lines) + "\n")
    for o in sorted(out_rows, key=lambda o: (o["api_error"], -(o["rate"] or 0))):
        print(f"{o['verdict'][:12]:12s} {o['upstream']:44s} merged {o['merged']}/{o['closed']} "
              f"stars {o['stars'] if o['stars'] is not None else '?'} last push {o['pushed'] or '?'}")
    print(f"\nwritten: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())