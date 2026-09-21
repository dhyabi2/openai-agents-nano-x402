#!/usr/bin/env python3
"""Find prepared PR-branch targets that have NO open PR and a safe listing-edit diff.

Distribution block: open a real upstream PR for every clean prepared branch that:
  - has no open PR under that head ref already (no duplicates),
  - is a listing-editorial edit (few files, small diff, README/json/md only, no src/ code),
  - target repo is reachable and NOT archived,
so existing built-and-verified listing branches stop sitting as un-closable drafts.

Read-only list mode by default; --open actually creates PRs (dry run: POST -> verify -> log).
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh_cred

API = "https://api.github.com"
FORK_OWNER = "PANDeveloper001"
# (target upstream, branch) — pulled from the drift tool's own target derivation where possible;
MY_BRANCHES = [
    "ANVEAI/agentpay add-nano-settlement-note",
    "AiFinPay/sdk add-nano-x402-example-v2",
    "AlexMili/Awesome-MCP add-nano-mcp",
    "Cooperiano/agora add-nano-settlement-note",
    "Floe-Labs/agentkit-actions add-nano-settlement-note",
    "Haustorium12/gold-402 add-openai-agents-nano-v7",
    "IcoinX/agenttasker add-nano-settlement-note",
    "MentionNetwork/awesome-agentic-commerce add-nano-x402-rail",
    "Merit-Systems/awesome-agentic-commerce add-openai-agents-nano-v2",
    "PayAINetwork/agentic-payments add-nano-x402-adapter",
    "Recall-Kitchen/awesome-x402-mcp-services add-vend",
    "Scottcjn/awesome-agents add-openai-agents-nano-v4",
    "assafbar2/agentswitchboard.dev add-openai-agents-nano-v9",
    "bitrefill/awesome-agentic-payments add-openai-agents-nano",
    "bitrefill/awesome-agentic-payments add-openai-agents-nano-x402",
    "caramaschiHG/awesome-ai-agents-2026 add-openai-agents-nano",
    "chgaowei/ai-agent-infra-list add-x402-nano-settlement-rail",
    "danyeah/a2amarket-cli add-nano-settlement-note",
    "derNif/payanagent add-nano-xno-settlement",
    "e2b-dev/awesome-ai-sdks add-openai-agents-nano-v2",
    "facundofarias/awesome-agent-first-tools add-openai-agents-nano",
    "frankxai/awesome-payment-agent-skills add-openai-agents-nano",
    "goodmeta/agent-payments-landscape add-nano-payment-rail",
    "internet-court/internet-court-skill add-x402-nano-integration",
    "kairovate/agent-payment-templates add-python-nano-pay-per-call",
    "langchain-ai/agent-auth-payments add-nano-credit-funding",
    "mbeato/awesome-mpp add-nano-x402-agent-framework",
    "michielpost/x402-dev add-openai-agents-nano",
    "mpp-best/awesome_mpp add-openai-agents-nano",
    "mpp-best/awesome_mpp add-openai-agents-nano-x402",
    "ndsgbm-web/agentpay add-nano-settlement-note",
    "nirium-protocol/nirium add-nano-settlement-note",
    "open-experiments/agent-exchange add-nano-settlement-note",
    "punkpeye/awesome-mcp-servers add-nano-mcp",
    "satohubai/onchain-agents add-openai-agents-nano-v3",
    "tsubasakong/awesome-agent-payments-protocol add-openai-agents-nano-v2",
    "vaaya-ai/vaaya-mcp add-nano-settlement-note",
    "x402-foundation/x402 docs/list-openai-agents-nano-v10",
    "x402eco/website add-openai-agents-nano-x402eco-v2",
    "xpaysh/awesome-x402 add-openai-agents-nano-v2",
]
# repos we are read-only on / must not open PRs to (per AGENTS.md / memory)
READ_ONLY = {"x402-foundation/x402"}

def api(path, tok, method="GET", body=None, retries=4):
    req = urllib.request.Request(API + path, method=method,
        headers={"Authorization": f"Bearer {tok}", "User-Agent": "rai-agent",
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    if body is not None:
        req.data = json.dumps(body).encode()
    last = None
    for attempt in range(retries):
        try:
            r = urllib.request.urlopen(req, timeout=30)
            return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.load(e)
            except Exception:
                return e.code, e.read().decode()[:200]
        except Exception as e:  # transient network error (conn reset / timeout) — retry
            last = e
            time.sleep(2 * (attempt + 1))
    raise last

def is_listing_edit(comp):
    """Safe listing = only docs/readme/json/md/yaml, no executable source changed."""
    if not isinstance(comp, dict) or "files" not in comp:
        return False
    paths = [f["filename"] for f in comp["files"]]
    if len(paths) > 4:
        return False
    bad = re.compile(r"(\.go$|\.rs$|\.py$|\.ts$|\.js$|\.sol$|\.tsx$|\.jsx$|/src/|/lib/|/packages/|/core/)")
    for p in paths:
        if bad.search(p):
            return False
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true", help="actually create the PRs (dry list otherwise)")
    ap.add_argument("--only", help="only these upstreams (comma list), other targets skipped")
    args = ap.parse_args()

    tok = gh_cred.token()
    only = set(args.only.split(",")) if args.only else None

    for entry in MY_BRANCHES:
        up, branch = entry.split()
        if up in READ_ONLY:
            print(f"SKIP(read-only) {up}/{branch}")
            continue
        if only is not None and up not in only:
            continue
        # archives / gone upstream
        st, d = api(f"/repos/{up}", tok)
        if st != 200:
            print(f"GONE {up}: {st}")
            continue
        if d.get("archived"):
            print(f"SKIP(archived) {up}")
            continue
        # does an open PR under this head already exist?
        st, prs = api(f"/repos/{up}/pulls?state=open&head={FORK_OWNER}:{branch}", tok)
        exists = isinstance(prs, list) and len(prs) > 0
        if exists:
            print(f"HAVE-PR {up} #{prs[0]['number']} {branch}")
            continue
        st, comp = api(f"/repos/{up}/compare/{d['default_branch']}...{FORK_OWNER}:{branch}", tok)
        if st != 200 or not isinstance(comp, dict):
            print(f"NODIFF {up}/{branch}: {st}")
            continue
        if comp.get("ahead_by", 0) == 0:
            print(f"EMPTY {up}/{branch}")
            continue
        kind = "listing" if is_listing_edit(comp) else "feature"
        names = ", ".join(f["filename"] for f in comp.get("files", []))
        desc = (d.get("description") or "")[:40]
        print(f"{'OPEN' if args.open else 'CAND'} {kind} {up} {branch} +{comp.get('ahead_by')}/-{comp.get('behind_by')} files[{names}] {d['stargazers_count']}*")
        if not args.open or kind != "listing":
            continue
        # create the PR
        title = f"Add {branch.replace('add-','').replace('-',' ')} (Nano x402)"
        body = (f"Adds an openai-agents-nano x402 entry to {up.split('/')[0]}'s listing.\n\n"
                f"Submitted by Rai, an autonomous AI agent building Nano (XNO) settlement for agent "
                f"payments. See https://github.com/PANDeveloper001/openai-agents-nano-x402.\n\n"
                f"Compare: https://github.com/{up}/compare/{d['default_branch']}...{FORK_OWNER}:{branch}?expand=1")
        st, pr = api(f"/repos/{up}/pulls", tok, "POST", body={
                     "title": title, "head": f"{FORK_OWNER}:{branch}", "base": d["default_branch"], "body": body})
        print(f"  -> create PR: {st} [{pr.get('html_url') if isinstance(pr, dict) else pr}]")

if __name__ == "__main__":
    main()