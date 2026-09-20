# Distribution funnel — 2026-09-20 13:10 UTC

## Milestone: openai-agents-nano-x402 is ADOPTED (rai-scope status: adopted: true)
- Package: true (GitHub release v0.1.0 wheel + sdist downloadable signed-out; GitHub release satisfies the "published" bar).
  - NOTE: the rai-scope `package` milestone at pypi.org/project/openai-agents-nano/ is a FALSE POSITIVE (bot-challenge page returns 200 for any name, per directory-listing skill). Real PyPI publish still 404 (req2 / trusted-publisher one-time registration pending from customer since Sep 15). Adoption is satisfied regardless by the listing + merged_pr + external_payment milestones below.
- Listing: true — recorded milestones: Agent Directory API (auto-approved, id d8cd7de3), AgentLaunch (agents-launch.lovable.app/agents/openai-agents-nano), AgentMRR, glama (nano-mcp-public), LibHunt x2, Corican/nanodir (nanodirectory.info), agentmrr.ai. All load 200 signed-out (re-verified Sep 20).
- Merged PR: TRUE — **aiagenta2z/ai-agent-marketplace #43** merged Sep 20 06:36 UTC by AI-Hub-Admin (third-party 55★ repo). 28h turnaround. This is the project's first merged third-party PR.
- External payment: TRUE — 7 external_payment milestones recorded (nanexplorer block hashes, from outside accounts).

## Release assets (v0.1.0) — Sep 20
- wheel: 548 dl (+ sdist 9) = 557 total. Downloads trending up (~+6/day).
- Traffic plateau: views/clones flat for 4+ runs; no new referrers beyond LibHunt (auto-indexed).

## Open PRs — 13 total (Sep 20 13:00, verified via GitHub search + PR API)
All OPEN, all mergeable/mostly MERGEABLE. No new maintainer replies since Sep 20 05:08.
- **gold-402 #234**: labels `verified` + `ready-to-merge`, bot "approved for merge" — CLOSEST TO MERGE, just needs a maintainer click.
- **x402-foundation/x402 #3531**: SDK listing doc PR (Third-Party SDKs). Signed commits now pass the vercel/verified-commits gate. Reviewer evidence posted Sep 20 05:08. No maintainer reply yet.
- tsubasakong/awesome-agent-payments-protocol #97, mpp-best/awesome_mpp #11, facundofarias/awesome-agent-first-tools #4, chgaowei/ai-agent-infra-list #8, goodmeta/agent-payments-landscape #8, frankxai/awesome-payment-agent-skills #17, Scottcjn/awesome-agents #82, assafbar2/agentswitchboard.dev #116, AiFinPay/sdk #77, satohubai/onchain-agents #12, xpaysh/awesome-x402 #1568.

## Tier 0 — x402-foundation
- #3512 "Record of prepared Nano-mainnet exact-scheme spec" — open, 2 self comments, no maintainer reply (last self-update Sep 20 05:08).
- #3531 SDK listing PR — open, mergeable, gate passes, awaiting review.
- #3532 spec PR — CLOSED by maintainer phdargen on AI-policy grounds (opened straight to PR without prior Discussion, per specs/CONTRIBUTING Step 1). Lesson learned: for x402 spec PRs, open a Discussion FIRST + include review evidence in the PR body. Documented in open-integration-pr skill.

## Pending directory listings: 0/14 live (day 20-21, re-checked Sep 20)
- agents.net (submitted Sep 15, day 5; rendered directory does NOT name the project yet — browser-verified). Still within 2-4 wk review window. Do NOT re-submit.
- theagentrank.com (Sep 15), bestaiagents.org (Sep 15), x402info.com/ecosystem (Sep 16), aiagentcensus.com (Sep 17), aiagentslist.io (Sep 17), SwarmBazaar (Sep 17), AiAgents.Directory (Sep 17), aikendra.com (Sep 18), MeshKore (Sep 17), 4agent.dev (Sep 17), devstack.directory (Sep 20), freeaiagents.net (Sep 20), aiagentstack.directory (Sep 19).
- Realistic first-approval horizon is 2-4 weeks (revised 2026-09-20); not a broken queue. Earliest approvals expected Sep 22-29.

## Evaluated-new-this-run (Sep 20)
- **LangChain x402 tools page** (docs.langchain.com/oss/python/integrations/tools): lists x402 payment tools (X402PaymentTool/langchain-x402, x402-langchain, openlibx402-langchain, fly402langchain) — ALL USDC/EVM/Solana-only, NO Nano. Real gap. BUT openai-agents-nano is an OpenAI-Agents adapter, NOT a LangChain tool, so it cannot be added to that page accurately. Future: a genuine Nano LangChain x402 tool would fit (build-when-not-distribution-first).
- gigs.sh / Circle Agent Marketplace / OKX AI: USDC-only agent marketplaces; no Nano rail; listing requires an agent-service/product (not a client SDK). Not-fit for a client library.
- awesome-codex-cli (RoggeOhta, 521★): Codex CLI plugins/skills/MCP only; our OpenAI-Agents-SDK library is not a Codex CLI artifact. Not-fit.

## Blocker state
1. req (PyPI publisher trusted-publisher one-time registration): still pending from customer — real PyPI publish gated. GitHub release satisfies "published" bar; not blocking adoption.
2. External repo issue/comment writes: fine-grained token can open PRs (req2 resolved) but issue-comment scope still 403 on third-party repos.

## Next actions
- Next run: check gold-402 #234 first (closest to merge); re-check #3512/#3531 for maintainer reply.
- Sep 22: weekly X post slot opens — draft at scripts/sep22-xpost.txt (update numbers before posting; verify link loads signed-out).
- When PyPI publisher registered: publish openai-agents-nano package properly, then update docs/michielpost x402-dev row if still pending.
- Continue re-checking directories at day 21-28 horizon; do not re-submit pending.
