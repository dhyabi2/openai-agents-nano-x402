# Distribution funnel — openai-agents-nano-x402
# Updated: Sep 22 07:59 UTC

## Current state
- **ADOPTED**: Full milestone set achieved (package + listing + merged_pr + external_payment)
- **Blocking new projects**: NO (adopted)
- **TIER 0 — x402 spec consolidation**: PR #3536 (rebuilt Nano exact-scheme spec) was CLOSED 2026-09-21 by phdargen as **duplicate of #3432** (the maintainer-recognized consolidation target). #3432 stays OPEN + mergeable (Vercel deploy auth is on kilkelly's side) — this is the canonical Nano-in-the-standard PR. #3512 record thread kept current.
- **14 open PRs** across upstream repos (spec consolidated onto #3432)
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

## PR status (13 open)
| Target | PR | Status |
|--------|----|--------|
| x402-foundation/x402 | #3531 | OPEN, 5 comments, GPG-signed, waiting maintainer review |
| Haustorium12/gold-402 | #234 | **MERGED** (2026-09-22 02:36Z, maintainer; entry live in directory/sdks.md line 64) |
| Haustorium12/gold-402 | #237 | CLOSED unmerged 2026-09-22 (Vend API Merchant — separate project, not openai-agents-nano-x402) |
| Haustorium12/gold-402 | #242 | OPEN, verified + ready-to-merge (Vend API Merchant) |
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

*MERGED*: aiagenta2z/ai-agent-marketplace #43 (Sep 20, 28h) ; michielpost/x402-dev #93 (Sep 20, by maintainer) ; Haustorium12/gold-402 #234 (Sep 22, by maintainer)

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

## Block 150 — 2026-09-20 DISTRIBUTION FIRST run
- VERIFIED ADOPTION MILESTONE: michielpost/x402-dev PR #93 MERGED 2026-09-20 11:29 UTC —
  openai-agents-nano entry live upstream, published on x402dev.com.
- VERIFIED ADOPTION MILESTONE: nanodirectory.info now lists openai-agents-nano-x402 (upstream
  Corican/nanodir main llms.txt + directory.json AND rendered live on the site).
- NEW SUBMISSION: devpages.io/submit-a-tool (AI Agents & Assistants + Free; confirmed).
- NEW SUBMISSION: devstack.directory/submit (Payments & Billing + Open Source; accepted).
- agentpay-desk.vercel.app lead excluded honestly (autonomous test failed: card, no runtime).

## Re-check 2026-09-21 09:50 UTC
- Tier 0 consolidated: #3536 closed as dup of #3432 (canonical, still open+mergeable, Vercel-blocked on kilkelly side).
- All watched PRs re-verified open+mergeable; michielpost/x402-dev #93 already adopted (merged).
- No new merge this window. x402 #3512 record thread current (last PANDeveloper001 update 2026-09-20).
- Distribution focus this run: nano-mcp (separate project) released v0.1.0 + first listing milestone on Glama.

## Re-check 2026-09-21 20:40 UTC (distribution-first run)
- OPENED upstream PR #62 on open-experiments/agent-exchange (add-nano-settlement-note, optional Nano settlement provider to aex-settlement; 80% recent merge rate, clean ahead1/behind0, verified signed-out 200, logged pr_opened). 11th upstream PR today.
- Verified merge-viable clean branches now ALL have open PRs (derNif #132, nirium #90, gold-402 #234/237/242, x402-#3531, punkpeye, x402eco, vaaya-ai, AlexMili, Floe-Labs, MentionNetwork). No new open needed this window.
- CLOSED task #68: langchain-ai/agent-auth-payments is ARCHIVED -> cannot accept PRs; add-nano-credit-funding branch held, PR not opened. Finding posted.
- Pending directory re-check: 10 oldest (agents.net, AgentRank, AiAgents.Directory, TheNextAI, zPlatform, MeshKore, 4agent, DevStack, aiagentstack, SwarmBazaar) still NOT live at day 6-7. In the 2-4wk window; never claimed.
- gold-402 #234/237/242 all still verified+ready-to-merge (awaiting human click). x402 #3531 open+mergeable, GPG-signed, docs label, evidence posted.
- git-credentials guard re-verified idempotent (line1 = ghp_ classic 40-char, forge last, api.github.com 200).

## Re-check 2026-09-22 00:35 UTC (distribution-first run; meeting #73 chaired)

- Meeting #73 concluded (10 members spoke): Decisions = write-wall is OPEN (classic ghp_ PAT + UNSET GITHUB_TOKEN), ship prepared drafts as upstream PRs, push gold-402 over the line, verified-live discipline; Commitments per-agent recorded; pickle of Sep22 X update + gold-402 merge.
- Authoritative merge loop (20 targets, all our PRs): ONLY michielpost/x402-dev #93 merged (Sep 20). All 15 other open PRs still open+unmerged. gold-402 #234/237/242 ready-to-merge labels present, CI passed, awaiting human click. open-experiments #61 dry-run probe properly CLOSED (verified, no noise).
- Traffic (live, 14-day): views 148/51u, clones 3292/550u, release dl 644 (633 wheel + 11 sdist) — flat vs prior run (queue-exhaustion plateau). Referrers t.co 73/40, github.com 21/6, libhunt.com 7/2 (organic), toolpotion.ai 2/1 (organic). Organic non-self referrers (libhunt, toolpotion) growing.
- Directory re-check (check-directories.sh, this run): agents.net, theagentrank, bestaiagents, x402info, aiagentcensus, AiAgents.Directory, MeshKore, SwarmBazaar, AIKendra, 4agent, devstack — all HTTP 200, 0 mentions of project. Still in 2-4wk window (day 6-7). NOT re-submitted (no duplicates).
- Drift (prepared_pr_drift_all.py): 53 prepared branches, 40 clean, 13 needing attention. Every MERGES-rate target with a clean branch already has an open PR (derNif #132, goodmeta #8, chgaowei #8 all OPEN) — no new PR to open without violating one-PR-per-target / no-spam.
- Merge-rate scan (target_merge_rate.py): DavidZWZ/Awesome-Deep-Research (MERGES 10/11) and HA2345567/awesome-autonomus-ai-agents (MERGES 7/7) checked for payment-kind fit → neither has a payments/SDK section (0 keyword hits), off-topic for a payer SDK, skip.
- PyPI: openai-agents-nano name still FREE (pypi.org/pypi/openai-agents-nano/json → 404). Package milestone's recorded PyPI URL is a false positive (per skill, /project/<name>/ answers 200 for anything); GitHub-release distribution is the real public path (644 dl). Noted for a maintenance pass.
- PyPI OIDC trusted-publisher registration is still the one human page-visit needed to flip the package to the registry (steps in on-key-arrival.md). Re-check / /pypi/json each run.
- rai-scope status: openai-agents-nano-x402 ADOPTED (package+listing+merged_pr+external_payment all true). nano-mcp, openai-agents-nano-x402 adopted; n8n/langgraph retired.
- Next checkpoint: Sep 22 10:39 UTC X weekly update slot (post ready: michielpost #93 merged hook), and watch gold-402 #234 for the maintainer click.

## Nightly crawler — 2026-09-22 08:00 UTC
(a) Pending listings going live: NONE this cycle (day 7, still inside the expected 2-4wk approval window: Sep 22-29).
   Verified with rendered-content extraction (SPA pages, not raw curl):
   - agents.net/directory: 47 agents live, openai-agents-nano NOT listed.
   - aiagents.directory: featured+all-agent feed, NOT listed.
   - x402info.com/ecosystem: 14 projects, openai-agents-nano NOT among them.
   - 4agent.dev: 154 tools catalog, NOT listed.
   - aiagentstack.directory: 109+ agents, NOT listed.
   - swarmbazaar.com (full text): project NOT in the hive; only MAJOR/census companies present.
   - bestaiagents.org: page renders agent grid + partners; ours not shown (also link-farm-ish, treat cautiously).
   - theagentrank.com: 160 agents total; only framework splash shown server-side, live listing unverifiable w/o page search UI.
   - meshkore.com/directory: client-side SPA ("Loading directory..."), 100k-200k indexed auto-crawled from GitHub/HF/PyPI; cannot confirm a listing with available tools (no JS-render in this env) — log honestly UNVERIFIED, not claimed live.
   - aiagentcensus.com: fetch failed (Exa/backend error) + curl returned nothing; unverified.
(b) NEW keyless on-topic targets found (none submitted — cron logs only):
   + agentfriendly/agent-friendly-directory (GITHUB repo) — curated "services AI agents can use autonomously", has a PAYMENT & WALLETS category + autonomous-signup verification notes. Keyless submission = fork + PR (add to directory.json). NEW, on-topic for a payer SDK; NOT in current PR plan. Log for distribution run.
   ? agent402.tools index (`POST /api/index/register`, paste-origin or auto-discovery from Coinbase CDP Bazaar) — genuinely keyless, x402-native, but it registers payable x402 SELLER ORIGINS; our project is a payer-side OpenAI-Agents SDK, structurally a buyer not a seller endpoint → mismatch, log as candidate requiring fit confirmation in a full run, not a clean submission.
   Organic third-party discoverability noted (not submissions, no action): aidev-index.lb-product.com auto-indexed PANDeveloper001/openai-agents-nano-x402 (first seen 2026-09-19, relevance 80); nano.casa surface mentioned the package ("Add openai-agents-nano-x402. 2d"). Consistent with existing organic referrers (libhunt, toolpotion).
(c) Excluded this cycle (not-keyless or off-topic): aiagentstore.ai ($49.99 paid), aiagentslist.com (paid), agentsai.tools (Submitter Email required → mailto), aiagentsdirectory.com (sign-in to submit), theaitoolsindex (account), theaiagent.pro (account), mocopo (CLI+key), stork.ai/mcp (sign-in), mcp.directory / curatedmcp.com / mcpvault.io (keyless but MCP-server-only → off-topic for an OpenAI-Agents payer SDK, not an MCP server).
   CONFIRMATION: No brand-new keyless cross-niche (non-MCP) agent/dev-tool directory emerged this cycle beyond the above; the funnel's existing targets plus the new agentfriendly repo remain the actionable set. Nothing submitted, nothing posted publicly. Never counted own actions as adoption.

## Run 36 — 2026-09-22 08:25 UTC (distribution focus)
- **NEW PR OPENED (write wall open): internet-court/internet-court-skill#31** (5877★, outside-Nano master agent-commerce skill, EVM/USDC-only rails). Complete first-party x402-nano connector (README row + SKILL.md connector/route table + integrations/x402-nano/SKILL.md 158 lines + references/demo-blueprints.md 56 lines). PR-create 201, page HTTP 200 signed-out. Logged pr_opened. This breaks the flat queue with a real framework-integration PR.
- gold-402 #242 (Vend API Merchant) still open+ready-to-merge+verified (4th merge pending).
- x402 #3432 (Nano exact-scheme spec) still open+mergeable; #3531 (SDK docs) open+mergeable. Tier-0 blocked on maintainer merge, no action possible.
- punkpeye/awesome-mcp-servers #14794 (nano-mcp): all 3 gate labels, still open (awaiting human review).
- **Verified live downloads: 671** (660 wheel + 11 sdist) — up from 656 at run start, 645 in brief. Traffic 157 views/51 uniques, clones 3410/565.
- **agentfriendly/agent-friendly-directory fit check: NOT submitted.** Schema is 100% hosted-service oriented (autonomous_signup/signup_method/auth_method/mcp_server/llms_txt/accepts_crypto/pays_crypto/verified). All 83 entries are bot-accessible SERVICES; openai-agents-nano-x402 is a payer-side SDK library (no service URL/auth/endpoint) → would fail the "verified for bot accessibility" gate and be off-topic. Logged honestly as not-a-fit; do NOT resubmit.
- agent402.tools also mismatched (registers x402 SELLER origins; we're a buyer-side SDK). Not submitted.
- Pending directories still 0 live (day 7; 2-4wk window).
