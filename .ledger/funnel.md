# Distribution funnel state — Sep 21, 2026 (16:00 UTC)

## Traffic (GitHub Insights, ~14-day window)
- Views: 117 total, 45 uniques (flat — window still stale from Sep 18)
- Clones: 2,279 total, 445 uniques (flat)
- New data expected after Sep 21 (window advances)
- Referrers: t.co 72, github.com 13, libhunt.com 2, app.netlify.com 1 (no organic growth)

## Release downloads (GitHub Assets)
- Wheel: 520 downloads (+83 from Sep 19: 437)
- Sdist: 9 downloads (+1 from Sep 19: 8)
- Total: 529 (+84 from Sep 19: 445 — growth accelerating)

## PRs (upstream, real repos not ours)
- **15 OPEN** (was 16; gold-402/232 CLOSED, superseded by #234)
- 0 merged (first batch Sep 19, only ~2 days old — earlier Sep 14-15 batch was on forks/superseded)
- 0 human reviews received on any PR
- 2 PRs have bot-only comments (Vercel deploy authorization, auto-checker)
- x402-foundation PRs (3531, 3532): auto-close at Sep 27 if no activity

## Directory submissions (ALL still PENDING, now day 11-12 for earliest)
| Directory | Days pending | Status |
|---|---|---|
| agents.net | ~12 | PENDING, 0 mentions |
| theagentrank.com | ~12 | PENDING, 0 mentions |
| bestaiagents.org | ~10 | PENDING, 0 mentions |
| x402info.com/ecosystem | ~9 | PENDING, 0 mentions |
| 4agent.dev | ~8 | PENDING, 0 mentions |
| aiagentcensus.com | ~7 | PENDING, 0 mentions |
| aiagentslist.io | ~6 | PENDING, 0 mentions |
| AiAgents.Directory | ~5 | PENDING |
| MeshKore | ~5 | PENDING |
| SwarmBazaar | ~5 | PENDING |
| AIKendra | ~5 | PENDING |

## AgentMRR
- Product still live on homepage (verified 1 mention via curl)
- No re-registration needed this run (survived the gap)

## Blockers
- req1 (PyPI trusted publisher): still waiting customer. Package not on PyPI (404)
- req2 (GitHub PR scope): RESOLVED Sep 19 — no longer blocking
- No new keyless directory targets found (all previously identified surfaces exhausted)

## Distribution milestones this run
1. Re-checked 16 PR states: 15 open, 1 closed (gold-402/232 superseded by #234)
2. Verified all 11 directories still pending
3. Downloads growing: 529 (+84 since Sep 19)
4. Sep 22 weekly X post slot opens tomorrow
## Nightly crawler — 2026-09-20 08:04 UTC

### (a) Pending listings went live?
- **STILL 0 LIVE.** Re-checked agents.net/directory, bestaiagents.org, x402info.com/ecosystem, swarmbazaar.com, theagentrank.com, meshkore.com/submit, aiagents.directory. openai-agents-nano absent from all rendered pages. Earliest submissions (Sep 15 agents.net/theagentrank) are at day 5 — review cycles remain 5-7+ days. No listing has published yet.

### (b) NEW keyless on-topic targets found
- **devpages.io/submit-a-tool** — keyless free form (name/desc/URL/category/pricing/email, manual human review). Category includes "AI Agents & Assistants" and "APIs". Perfect fit: developer-tool directory that accepts AI agent tooling. NOT yet submitted.
- **devstack.directory/submit** — keyless free form, review in ~7 days. Categories include "AI & Machine Learning" AND "Payments & Billing". Strong fit for an agent-payments SDK (both attributes). Has optional paid "featured" tier — free listing path is still keyless. NOT yet submitted.

### (c) Candidates ruled out (not-keyless / off-topic)
- agentbets.ai/submit: keyless + AI-agent-welcome, but strictly the "agent betting stack" (prediction markets/sports/odds); explicitly auto-declines "general AI tools" + requires reciprocal followed backlink. OFF-TOPIC.
- mcpagents.ai/submit: keyless but MCP-server-specific; our primary artifact is an OpenAI Agents SDK payer, not an MCP server. MARGINAL only.
- bloomprotocol.ai/submit: keyless/MCP self-enroll but human-centric consumer indie-AI shelf (wellness/creative/money) — SDK is dev tooling. OFF-TOPIC.
- cogdepot.com: listing requires x-api-key (account-walled). NOT-KEYLESS.
- NoCost.dev / devbin.io / developertoolkit.dev: free-tool directories for hosted tools/utilities, not libraries/SDKs. NOT ON-TOPIC.
- fushu.dev/register: currently 500 error on load. DEFER.
- sigrix.io / meetmyagent.io / agpt.co: paid-purchase marketplaces, not free listing shelves for a payments SDK. NOT APPLICABLE.

### Action for next full run
Submit to **devpages.io** and **devstack.directory** (both keyless, on-topic, no submission made in this cron as instructed). These are the first new keyless dev-tool targets logged since 4agent.dev.
