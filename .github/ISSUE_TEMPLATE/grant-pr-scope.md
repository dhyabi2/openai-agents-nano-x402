---
name: "\U0001F500 Grant GitHub PR scope"
about: "One-click action for the repo owner: grant the `public_repo` scope so 18 prepared PRs can be opened."
title: "[Action] Grant public_repo scope"
labels: ["customer-action", "req2"]
assignees: ""
---

**What to do (one click, ~30 seconds):**

1. Go to https://github.com/settings/tokens
2. Find the existing fine-grained token in use (the one with `repo` scope on `dhyabi2/*`)
3. Click the token → "Edit"
4. Under "Repository permissions", find **Contents** → change to **Read and write**
5. (Or create a new token with **public_repo** scope, which includes Contents: write on public repos)
6. Click "Save"

**After you do this:**

- Running `./scripts/open-prs.sh` will open all 18 prepared PRs at once (they are already fork-pushed, drift-checked, and merge-rate-ranked)
- The repos that will receive PRs include: x402-foundation/x402 (6,620★), xpaysh/awesome-x402, Scottcjn/awesome-agents, facundofarias/awesome-agent-first-tools, frankxai/awesome-payment-agent-skills, and 12 more
- Each PR states it is from an AI agent, follows the target's CONTRIBUTING rules, and adds Nano (XNO) / x402 as a payment rail to their integration list or docs
- Close this issue and watch the PRs land

**Verified preconditions (already true):**

- All 18 branches are drift-checked clean (ahead/behind 0 vs upstream) — confirmed by `prepared_pr_drift_all.py`
- All target repos accept PRs with stated AI-agent authorship (checked merge rates from closed-PR history)