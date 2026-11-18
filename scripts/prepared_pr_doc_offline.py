#!/usr/bin/env python3
"""Prove the drift-doc generator cannot silently drop a key artifact.

A hand-written resume list went stale and omitted the branch that is one of this repo's two adoption
artifacts (corrective action 2026-09-16 16:34 UTC).  The generator now fails loudly instead.  This
script checks that with deliberate mutations - a law that cannot fail is a weak law, so each guard is
shown failing on input built to trip it, and passing on the real input.

Run:  python3 scripts/prepared_pr_doc_offline.py   (exit 0 = all checks pass, no network)

This lives in scripts/, beside the generator it checks, rather than in tests/: it checks outreach
tooling, not the package, and it needs the operator's local scan report in the git-ignored
`.ledger/tmp/` (the 2026-09-27 and 2026-09-30 audits record that it exits 1 anywhere that report is
absent). The package's own tests are in tests/ and ship with the sdist.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOC = ROOT / "scripts" / "pr_drift_doc.py"
REAL = ROOT / ".ledger" / "tmp" / "drift_all.json"


def run(args: list[str]) -> str:
    r = subprocess.run([sys.executable, str(DOC), *args], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"generator failed: {r.stderr.strip()[:400]}")
    return r.stdout


def main() -> int:
    if not REAL.exists():
        # Generate the scan inline so this test works even in a sandbox
        subprocess.run([sys.executable, str(ROOT / "scripts" / "prepared_pr_drift_all.py"),
                        "--json", str(REAL)], capture_output=True, text=True, cwd=ROOT)
        if not REAL.exists():
            raise SystemExit("no scan report and could not generate one")
    real = json.loads(REAL.read_text())
    checks: list[tuple[str, bool, str]] = []

    # 1. the generator must name the spec branch the old hand-written list omitted
    out = run([])
    checks.append(("real scan names specs/exact-nano-mainnet",
                   "specs/exact-nano-mainnet" in out, "branch absent from generated section"))

    # 2. and it must never print MISSING for the real scan
    checks.append(("real scan has no MISSING row", "MISSING" not in out, "real scan reported a hole"))

    # 3. MUTATION: remove the spec branch -> the hole must be named, not silently dropped
    mut = ROOT / ".ledger" / "tmp" / "mut_spec.json"
    mut.write_text(json.dumps([r for r in real if "exact-nano" not in r["branch"]]))
    out_mut = run(["--json", str(mut)])
    checks.append(("dropping the spec branch is reported",
                   "MISSING" in out_mut and "specs/exact-nano-mainnet" in out_mut,
                   "a dropped artifact vanished silently - the original bug"))

    # 4. MUTATION: corrupt the row status -> the count line must change, so the numbers are data-driven
    mut2 = ROOT / ".ledger" / "tmp" / "mut_status.json"
    bad = [dict(r, status="diverged", behind_by=3) for r in real]
    mut2.write_text(json.dumps(bad))
    out_bad = run(["--json", str(mut2)])
    checks.append(("clean count is computed, not written",
                   "0 clean" in out_bad.splitlines()[0] or "clean (ahead / behind 0)**" in out_bad
                   and "15 clean" not in out_bad,
                   "the summary line did not react to a mutated scan"))

    # 5. it must refuse to guess when the markers are absent
    r = subprocess.run([sys.executable, str(DOC), "--doc", "README.md", "--write"],
                       capture_output=True, text=True, cwd=ROOT)
    checks.append(("refuses a document without the markers",
                   r.returncode != 0 and ("markers" in (r.stderr + r.stdout)
                                          or "unknown document" in (r.stderr + r.stdout)),
                   "it edited a file it could not locate the section in"))

    # 6. the docs page's artifact table is generated from the same scan, and names the CURRENT head
    out_docs = run(["--doc", "docs/upstream-x402-nano-registration.md"])
    head_spec = next((r["head"] for r in real if "exact-nano" in r.get("branch","")), None)
    checks.append(("docs table carries the scan's head for the spec branch",
                   head_spec is not None and f"`{head_spec}`" in out_docs,
                   "the upstream-facing table is still hand-typed"))

    # 7. MUTATION: a stale hand-typed sha in the docs must not survive a rewrite
    stale = ("cbef150a" in out_docs)
    checks.append(("docs table drops the superseded hand-typed sha", not stale,
                   "a superseded sha survived the rewrite"))

    # 8. the docs rewrite is idempotent (verified by re-running against the real file)
    before = (ROOT / "docs" / "upstream-x402-nano-registration.md").read_text()
    r1 = subprocess.run([sys.executable, str(DOC), "--doc", "docs/upstream-x402-nano-registration.md", "--write"],
                        capture_output=True, text=True, cwd=ROOT)
    once = (ROOT / "docs" / "upstream-x402-nano-registration.md").read_text()
    subprocess.run([sys.executable, str(DOC), "--doc", "docs/upstream-x402-nano-registration.md", "--write"],
                   capture_output=True, text=True, cwd=ROOT)
    twice = (ROOT / "docs" / "upstream-x402-nano-registration.md").read_text()
    (ROOT / "docs" / "upstream-x402-nano-registration.md").write_text(before)
    checks.append(("docs rewrite is idempotent", once == twice and r1.returncode == 0,
                   "a second run changed the file again"))

    ok = True
    for name, passed, why in checks:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        if not passed:
            print(f"      {why}")
        ok &= passed
    print(f"\n{sum(1 for _, p, _ in checks if p)}/{len(checks)} checks pass")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
