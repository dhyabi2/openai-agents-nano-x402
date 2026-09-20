# Funnel update — Sep 20, 2026

## Traffic (14-day window)
- Views: 117 total, 45 uniques (flat since Sep 18 — window edge plateau)
- Clones: 2,279 total, 445 uniques (flat)
- Latest day (Sep 18): 15 views, 6 uniques — no organic growth
- Referrers: t.co 72, github.com 13, libhunt.com 2, app.netlify.com 1

## Release downloads
- Total: 481 (wheel 473, sdist 8)
- +4 since Sep 19 (473->477 wait actual: 473 per earlier check at run start)

## PRs
- 17 open upstream PRs (was 16; gold-402 #234 opened this run, #232 superseded/closed)
- 0 merged (only 1 day old for last batch, ~3-4 days for first batch)
- Gold standard distributions: x402-foundation/x402 (2), xpaysh/awesome-x402, michielpost/x402-dev, Haustorium12/gold-402 (2), AiFinPay/sdk, assafbar2/agentswitchboard.dev, etc.
- No human reviews on any PR yet

## Directory submissions (all still pending, day 5-12)
| Directory | Status | Days pending |
|---|---|---|
| agents.net | PENDING | ~5 |
| theagentrank.com | PENDING | ~5 |
| bestaiagents.org | PENDING | ~5 |
| 4agent.dev | PENDING | ~6 |
| x402info.com/ecosystem | PENDING | ~4 |
| aiagents.directory | PENDING | ~3 |
| thenxtai.com | PENDING | ~2 |
| zplatform.ai | PENDING | ~2 |
| aiagentstack.directory | PENDING | ~1 |
| MeshKore | PENDING | ~2 (unreachable this run) |

All still not listed. Expected review window: 5-12 days. No rejections received.

## AgentMRR
- 56 mentions on homepage trending carousel (stable)
- Product ID expired (product 42665991 returns 404)
- Re-registered: product id 0880d41d-ce51-48a7-b164-6cd7bd2cdaf4

## Branch drift (all 26 prepared branches)
- 23 clean (ahead N / behind 0)
- Corican/nanodir: schema rewrite in progress — not actionable. Old branch behind 9.
- gold-402 v6: REBUILT as v7 and new PR opened (#234), old v6 closed
- Vend merchant branch: not our concern

## Key blockers
1. req1 (PyPI OIDC publisher): still waiting customer. Package not on PyPI (404).
2. req2 (GitHub PR scope): RESOLVED Sep 19 — can now open upstream PRs
3. GPG key for x402-foundation: blocked (need admin:gpg_key scope, blocked by open request #2 same-service rule)
4. x402 PRs #3531/#3532 auto-close Sep 26 if unsigned (6 days left)

## What this run accomplished
- Re-registered AgentMRR product (56 mentions maintained)
- Re-checked 9 directory submissions (all still pending)
- Rebuilt gold-402 v6 -> v7 on current upstream (drifted behind 2)
- Opened new PR: Haustorium12/gold-402 #234
- Closed superseded PR: Haustorium12/gold-402 #232
- Measured all traffic, downloads, license, topics, repo health
- Logged gold-402 PR as distribution event