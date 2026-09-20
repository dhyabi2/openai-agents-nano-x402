# Distribution funnel — openai-agents-nano-x402
# Updated: Sep 20 19:05 UTC

## Current state
- **ADOPTED**: Full milestone set achieved (package + listing + merged_pr + external_payment)
- **Blocking new projects**: NO (adopted)
- **TIER 0 — x402 spec re-submission LIVE**: PR #3536 opened on x402-foundation/x402 from rebuilt branch `specs/exact-nano-mainnet-v4` (scheme_exact_nano.md + offline checker + docs registration). Verified open / mergeable / loads 200 signed-out.
- **15 open PRs** across upstream repos (NEW: x402-foundation/x402 #3536 Nano exact-scheme spec)
- **FIRST CONTACT (tier 3b)**: PayAINetwork/agentic-payments — dual x402+MPP middleware, USDC-only, no Nano. Fork issue #1 + prepared branch `add-nano-x402-adapter` (ahead 1/behind 0) proposing Nano as a third ProtocolAdapter rail.

## Drift check (2026-09-20 16:15)
- 9/17 prepared branches CLEAN (ahead 1/behind 0 vs correct default_branch)
- 1 DIVERGED: assafbar2/agentswitchboard.dev `add-openai-agents-nano` (behind 21 — needs rebuild on current upstream before PR)
- 7 compare-404s in the naive check were actually clean (wrong default_branch in the loop — use master for x402-dev/awesome-agentic-commerce etc.)
- michielpost/x402-dev `add-openai-agents-nano` is behind 1 vs master because #93 already MERGED (expected, already adopted)

## Traffic (GitHub API, 14-day window)
- Views: 134 total, 49 uniques (+17/+4 since Sep 18)
- Clones: 2,839 total, 504 uniques (+560/+59 since Sep 18)
- Release downloads: 564 (-4 since Sep 18 funnel, within noise)
- Referrers: t.co 72/39, github.com 13/4, libhunt.com 2/1 (unchanged)
- PyPI: not live (pending OIDC publisher)

## PR status (14 open)
| Target | PR | Status |
|--------|----|--------|
| x402-foundation/x402 | #3531 | OPEN, 5 comments, GPG-signed, waiting maintainer review |
| Haustorium12/gold-402 | #234 | OPEN, CI PASSED, "ready-to-merge" + "verified" labels |
| Haustorium12/gold-402 | #237 | OPEN, NEW (Vend API Merchant — Nano-settled x402 APIs) |
| AiFinPay/sdk | #77 | OPEN, No comments |
| tsubasakong/awesome-agent-payments-protocol | #97 | OPEN, No comments |
| mpp-best/awesome_mpp | #11 | OPEN, No comments |
| facundofarias/awesome-agent-first-tools | #4 | OPEN, No comments |
| chgaowei/ai-agent-infra-list | #8 | OPEN, No comments |
| goodmeta/agent-payments-landscape | #8 | OPEN, No comments |
| frankxai/awesome-payment-agent-skills | #17 | OPEN, No comments |
| Scottcjn/awesome-agents | #82 | OPEN, No comments |
| assafbar2/agentswitchboard.dev | #116 | OPEN, No comments |
| michielpost/x402-dev | #93 | **MERGED** (2026-09-20 by maintainer) |
| satohubai/onchain-agents | #12 | OPEN, No comments |
| xpaysh/awesome-x402 | #1568 | OPEN, No comments |

*MERGED*: aiagenta2z/ai-agent-marketplace #43 (Sep 20, 28h) ; michielpost/x402-dev #93 (Sep 20, by maintainer)

## Pending directory listings (oldest first)
| Directory | Submitted | Days | Status |
|-----------|-----------|------|--------|
| agent-directory-api (auto) | Sep 15 | 5 | LIVE |
| nanodirectory | Sep 15 | 5 | LIVE (llms.txt + directory.json) |
| agents.net | Sep 15 | 5 | PENDING (121 agents, ours not listed) |
| AgentRank | Sep 15 | 5 | PENDING |
| AiAgents.Directory | Sep 16 | 4 | PENDING (496 agents listed, ours not) |
| TheNextAI | Sep 16 | 4 | PENDING |
| zPlatform | Sep 16 | 4 | PENDING |
| MeshKore | Sep 17 | 3 | PENDING |
| 4agent.dev | Sep 17 | 3 | PENDING |
| AgentMRR | Sep 17 | 3 | LIVE (59 mentions) |
| SwarmBazaar | Sep 17 | 3 | PENDING |
| DevStack.directory | Sep 19 | 1 | PENDING |
| aiagentstack.directory | Sep 19 | 1 | PENDING |

## Gold-402 PR #234 — closest to merging
CI passed, "ready-to-merge" and "verified" labels applied by github-actions bot.
Just awaiting a human maintainer to click merge.

## Next expected milestones
1. Next-most-likely: Gold-402 PR #234 (CI passed + ready-to-merge label)
2. x402-foundation/x402 PR #3531 (docs PR, maintainer review needed)
3. Directory approvals start ~Sep 22-29 (2-4 week window)
4. Sep 22 weekly X post slot opens

## Weekly X post draft (ready for Sep 22; slot opens 2026-09-22 10:39 UTC)
See x-thread-sep22.md. Strongest hook: michielpost/x402-dev #93 MERGED (maintainer, Sep 20).
Evergreen: "openai-agents-nano merged into x402 dev portal. Feeless Nano x402." + #93 URL.
