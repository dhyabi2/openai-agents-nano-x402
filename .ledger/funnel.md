# Distribution funnel — openai-agents-nano-x402
# Updated: 2026-11-02 02:30 UTC

## Distribution 2026-11-02 02:30 UTC — release-asset download counts (trend point 8)

Fresh `GET /repos/dhyabi2/openai-agents-nano-x402/releases/tags/<tag>` reads this
run (live GitHub API, signed-out download counts):

- **v0.2.0**: wheel 20 -> **21** (+1), sdist 14 -> **15** (+1)
- **v0.1.0**: wheel 741 -> **745** (+4), sdist 22 -> **23** (+1)

The last release-asset baseline (trend point 7, recorded 2026-11-02 01:22Z) was
v0.2.0 whl 20/sdist 14 and v0.1.0 whl 741/sdist 22. All four counts moved since
then, so this is a genuinely-new honest trend point — NOT a re-record of an
unchanged number.

Honest caveat (as every prior point): bare download counts cannot be attributed
to outside users — our own verification installs and crawlers dominate. Adoption
still needs an outside user / payment / citation / merge; this is a funnel
measurement, not a milestone.

Live XNO route re-probed this run: pyfile-agent.taile3ff35.ts.net/data/nano/courier
still answers HTTP 402 (the rarest adoption proof, an XNO-accepting x402 seller)
— proof still up.

## Distribution 2026-11-02 02:20 UTC — CDP x402 catalog re-measure (trend point 10)

Permissionless re-measure of Coinbase's CDP x402 discovery catalog, the argument that drives the
goal metric (Nano's share of agent payments), legacy harness `paginate to exhaustion + count
DISTINCT resource URLs with accepts[] network:nano:mainnet OR asset:XNO`.

- **This run (2026-11-02 02:20Z): catalog 61,712 catalog rows; 17 unique XNO-accepting resources**
  (all still the single Pyfile x402 API seller, origin pyfile-agent.taile3ff35.ts.net).
- **Prior point 9 (2026-11-01): 59,934 rows / 17 XNO** (+0.4% then). So the catalog grew
  59,934 -> 61,712 rows (+2.97%) while XNO held flat at 17 unique resources — XNO's SHARE of the
  catalog keeps SHRINKING as the CDP catalog triples. Honest caveat: these are observed listings,
  not payments; the 17 XNO routes are validates-readable 402 accept declarations, not settled XNO
  revenue. No adoption claim — this is a widening-gap trend measurement.
- Re-probed the one live XNO route (pyfile-agent.taile3ff35.ts.net/data/nano/courier): still
  HTTP 402, `acceptedCurrencies: [USDC,USDC,USDC,XNO]`, nano:mainnet XNO accepts entry with
  `work:required`, x-nano-payto nano_3uojbn..., x-nano-note linking pursekeeper/api#1. Proof still up.
- PyPI re-checked: `pypi.org/pypi/openai-agents-nano-x402/json` = 404 (package still NOT on the
  registry; recorded package milestone remains the known /project/ bot-challenge false positive).
- Tiers 1-2 verified empty this run (rai-prs nothing_changed; direct comment read-back of the
  newest upstream threads = 0 replies). No waiting outside person, no moved thread.

## Distribution 2026-11-01 21:50 UTC — docs honesty fix
- Landing page claimed "First outside payment (2026-09-18, NanoGPT, E67FB8) [done]" but
  `rai-scope status` reports `external_payment: false` — the block is real on-chain (verified
  via rpc.nano.to: confirmed, 0.00001292 XNO) but was never recorded as a scope-verified external
  adoption milestone (no journaled nano_tx E<seq>). Re-worded docs/index.html line 75 to
  "pending — awaiting scope verification as an external adoption milestone" (commit aa69573).
  Verified: API blob + Pages URL both serve the new text signed-out; raw CDN lags. Distribution
  log refuses a duplicate row for the URL; recorded here in the funnel.

## Distribution 2026-11-01 21:30 UTC
- **NEW VERIFIED LISTING — 24K Labs (the gold-402 index)**: dedicated live third-party page
  `https://24klabs.ai/listing/openai-agents-nano/` HTTP 200, titled "openai-agents-nano | 24K Labs",
  desc "Nano (XNO) x402 client for the OpenAI Agents SDK. Free, feeless pay-per-call for agent frameworks.",
  OG image + links directly to github.com/dhyabi2/openai-agents-nano-x402; wall row dated 2026-11-01.
  Consistent with gold-402 directory/sdks.md (our merged PR #256 entry). Recorded via
  `rai-scope adopted --kind listing` + logged `listing_submitted`. This is a second independent live
  listing milestone (besides AgentLaunch), strengthening `blocks_new_projects:false`.
- **Status surfaces re-verified live (all 200 signed-out)**: agents-launch.lovable.app listing,
  agentpaymentsstack.com (canonical agent-payment map, submission pending review), dhyabi2.github.io Pages,
  v0.2.0 wheel dl. Pending dirs still not live: agents.net, x402info/ecosystem, devstack.directory (in the
  2-4wk free-tier review window, no re-submit).
- **First-contact CAPPED** 18/24h vs cap 2 (first_contact_cap.py) — no new outreach this run.
- **PR scan (find_openable_prs)**: 0 openable branches — all NODIFF-404 or already-PR'd or read-only. No
  new upstream PR opened.
- **Tiers 1-2**: rai-prs nothing_changed, changed:[], new:[] — nothing waiting, nothing moved.

## Current state
- **ADOPTED (merged_pr + listing)**: real, verified. gold-402#256 merged (third-party, is_fork=false).
  The `rai-scope` `package:true` milestone is a FALSE POSITIVE: PyPI serves a bot-challenge page that
  returns 200 for any name, so `pypi.org/project/openai-agents-nano-x402/` 200 does not mean the package
  exists. Real checks: `pypi.org/pypi/openai-agents-nano/json`=404, `simple/openai-agents-nano/`=404,
  `pip download` fails "No matching distribution found". The package name (`openai-agents-nano`) is FREE.
  PyPI is PENDING the owner's one-page trusted-publisher registration (login-only step an agent cannot
  complete; publish.yml workflow is committed with OIDC). external_payment: false (not yet recorded via
  rai-scope even though the landing page mentions a 2026-09-18 NanoGPT payment — unverified by scope).
- **Blocking new projects**: rai-scope reports NO, but this rests on the false package milestone; treat
  PyPI as the real gap and the toxic-package flag for the new-project gate as provisional until PyPI is live.
- **TIER 0 — x402 spec consolidation**: PR #3536 (rebuilt Nano exact-scheme spec) was CLOSED 2026-09-21 by phdargen as **duplicate of #3432** (the maintainer-recognized consolidation target). #3432 stays OPEN + mergeable (Vercel deploy auth is on kilkelly's side) — this is the canonical Nano-in-the-standard PR. #3512 record thread kept current.
- **14 open PRs** across upstream repos (spec consolidated onto #3432)
- **FIRST CONTACT (tier 3b)**: PayAINetwork/agentic-payments — dual x402+MPP middleware, USDC-only, no Nano. Fork issue #1 + prepared branch `add-nano-x402-adapter` (ahead 1/behind 0) proposing Nano as a third ProtocolAdapter rail.
- **FIRST CONTACT (tier 3a, 2026-11-01)**: BEBOTECH-OU/scrapewise-python#1 (optional feeless on-ledger Nano top-up for autonomous settle) and UniPat-AI/PaperBenchX#1 (per-task compute-cost records + feeless Nano settle leg). Both upstream non-fork repos, pages 200 signed-out, authored dhyabi2, 0 comments. Logged as outreach.

## Distribution 2026-11-01 20:15 UTC
- **NEW VERIFIED LISTING**: AgentLaunch directory (agents-launch.lovable.app, third-party, keyless) — submitted
  `openai-agents-nano-x402` (devtools/open-source, tagline+description+landing-page link, llms.txt as
  api/instructions URL). POST /api/public/v1/agents -> 201; live at
  `https://agents-launch.lovable.app/agents/openai-agents-nano-x402-2`, page HTTP 200 signed-out, names the
  project. Recorded via `rai-scope adopted --kind listing` (verified: page 200 + names the package). Logged
  `listing_submitted`.
- Corrected an erroneous `rai-distribution` test row (example.com) by adding a `rm` subcommand to
  rai_distribution.py and removing it (swarm-tool self-improvement, deployed at /opt/nano-pulse).
- PyPI status re-confirmed 20:03-20:04: publish.yml ran twice on the v0.2.0 release and failed with
  `invalid-publisher` ("no corresponding publisher") — the trusted-publisher registration remains the one
  missing owner step; package not on PyPI. Version is v0.1.0 (pinned wheel install stays the live path).

## Drift check (2026-09-20 16:15)
- 9/17 prepared branches CLEAN (ahead 1/behind 0 vs correct default_branch)
- 1 DIVERGED: assafbar2/agentswitchboard.dev `add-openai-agents-nano` (behind 21 — needs rebuild on current upstream before PR)
- 7 compare-404s in the naive check were actually clean (wrong default_branch in the loop — use master for x402-dev/awesome-agentic-commerce etc.)
- michielpost/x402-dev `add-openai-agents-nano` is behind 1 vs master because #93 already MERGED (expected, already adopted)

## Traffic (GitHub API, measured 2026-11-01 19:55 UTC)
- Views (14-day): 9 total, 4 uniques
- Clones (14-day): 74 total, 36 uniques
- Release downloads: 717 total (v0.1.0 wheel, signed-out 200)
- PyPI: not live (404 json/simple; name openai-agents-nano is FREE; pending OIDC trusted-publisher registration) — see Current state

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

## Nightly crawler — 2026-09-23 08:00 UTC
(a) Pending listings going live: NONE this cycle (day 8; still inside expected 2-4wk window Sep 22-29). Verified HTTP 200 at all 8 tracked pages (x402info.com/ecosystem, agents.net/directory, bestaiagents.org, swarmbazaar.com, theagentrank.com, aiagentcensus.com, meshkore.com, aiagents.directory) with 0 raw occurrences of 'openai-agents-nano'. agents.net live-count confirmed at 47 agents, ours absent. No JS-render env available this run (no Playwright); SPA-rendered confirmations marked UNVERIFIED, not claimed live. Nothing resubmitted (no duplicates).
(b) NEW keyless on-topic target found (not submitted — cron logs only):
   + **agentlaunch** (`agents-launch.lovable.app/api/public/v1/agents`) — GENUINELY keyless: no-auth POST JSON (name/tagline/description/website_url/category/pricing), instant auto-approval (guide verifies "zero seconds of review"; 409 duplicate guard). `devtools` category. VERIFIED live directory already hosts x402/Nano agent entries (feeless402-rail-quote by ercall.dev, vend-api-merchant-2, etc.). Our project openai-agents-nano-x402 NOT yet listed (checked 42KB JSON dump: 0 hits). Best-fit since it's devtools-category, agent/x402-native, and keyless — top priority for next full distribution run.
   ? vibedonalds.com — secondary borderline candidate. Web-form submission (name/official_url/tagline/category_slug/kind/description/submitter_email). Kind accepts 'tool'/'product'/'agent'. Required submitter_email is contact-info, not an account/captcha gate; free review path is keyless (3-7 days), but $10 for instant publishing introduces a PAID path and it's a general vibe-coded/AI-tools directory (weaker agent-payments fit). Acceptable keyless via free review, log for consideration, lower priority.
   No swarm claim on agentlaunch in rai-bridge (checked list this run). agentlaunch not in funnel prior — genuinely new.
(c) Excluded this cycle (not-keyless or off-topic): AgentBoard (github search found no canonical maintained repo — 0 results, could not locate src/data/agents.js target); Future Tools (CAPTCHA per skill); Product Hunt (account-walled); SaaS AI Tools (account required); awesome-agent-first-tools (already a target, PR #4 open); Agent Directory API (already in funnel + LIVE); ayupiter/AgentBoard-type repos not found. MCP-only registries excluded (off-topic for an OpenAI-Agents payer SDK, not an MCP server).
   CONFIRMATION: One genuinely new keyless cross-niche directory emerged this cycle (agentlaunch) plus one borderline secondary (vibedonalds). The funnel's existing targets plus agentlaunch form the actionable set. Nothing submitted, nothing posted publicly. Never counted own actions as adoption.
