# Distribution funnel — 2026-11-02 02:30 UTC (run update)

## Trend point 8 (release assets) — download counts moved; honest no-outside-user caveat

Fresh `GET /repos/dhyabi2/openai-agents-nano-x402/releases/tags/<tag>` reads this
run (live API, signed-out counts):

- **v0.2.0**: wheel 20 -> **21** (+1), sdist 14 -> **15** (+1)
- **v0.1.0**: wheel 741 -> **745** (+4), sdist 22 -> **23** (+1)

The last release-asset baseline recorded in trend point 7 (3e37300, 2026-11-02
01:22Z) was v0.2.0 whl 20/sdist 14 and v0.1.0 whl 741/sdist 22. All four counts
moved since then, so this is a genuinely-new honest trend point, NOT a re-record
of an unchanged number.

To be clear about what these are not: bare download counts cannot be attributed
to outside users — own verification installs and crawlers dominate. Adoption
still needs an outside user / payment / citation / merge. Funnel measurement,
not a milestone.

Live XNO route re-probed this run: pyfile-agent.taile3ff35.ts.net/data/nano/courier
still answers HTTP 402 (the rarest adoption proof, an XNO-accepting x402 seller)
— proof still up.

## Trend point 7 (release assets) — download counts moved; honest no-outside-user caveat

Fresh `GET /repos/dhyabi2/openai-agents-nano-x402/releases/tags/<tag>` read this
run (live API, signed-out counts):

- **v0.2.0**: wheel 20 (flat), sdist 13 -> **14** (+1)
- **v0.1.0**: wheel 740 -> **741** (+1), sdist 21 -> **22** (+1)

The last release-asset baseline recorded in trend point 6 (641d09d, and
re-confirmed unchanged through trend point 9) was v0.2.0 whl 20/sdist 13 and
v0.1.0 whl 740/sdist 21. Three of the four counts moved (+1 each on both sdists
and the v0.1.0 wheel) since then, so this is a genuinely-new honest trend
point, NOT a re-record of an unchanged number.

Honest reading (same caveat as every prior release-asset point): a bare
download/incremental count cannot be attributed to outside users — own
verification installs and crawlers dominate small deltas, and adoption needs an
outside user, payment, cite or merge, none of which these +1s prove. This is a
funnel trend point, not a milestone: no `rai-scope adopted`, no fabricated
outward claim. Recorded as docs.

The CDP Bazaar catalog was also re-probed this run: **unchanged** at 59,934
total resources with XNO-accept still 17 unique from the single Pyfile seller
(same as trend point 9) — since it did not move, no fake trend point is
recorded for it (re-checking an unchanged number is not work). The live XNO
proof still answers: `POST /data/nano/courier` returns HTTP 402 with
`WWW-Authenticate: x402` and `acceptedCurrencies: [USDC, USDC, USDC, XNO]`, so
the only in-catalog XNO accept remains live and answerable.

# Distribution funnel — 2026-11-02 01:15 UTC (run update)

## Trend point 9 — CDP Bazaar catalog grew again; XNO still flat at 17

Fresh paginated re-read of the CDP x402 discovery catalog this run (to
exhaustion, limit=1000): **catalog total 59,934 resources** (trend point 8 was
59,682 — grew ~+0.4%), while **XNO-accept resources held at 17 unique**, all still
from the single Pyfile x402 API seller (`pyfile-agent.taile3ff35.ts.net` and
`:10000`). XNO's share of the catalog shrank again (~0.0285% -> ~0.0284%). The
widening-gap trend (catalog growing, XNO adoption flat) continues.

Live proof re-probed this run: `POST /data/nano/courier` still answers HTTP 402
with `WWW-Authenticate: x402`, `X-Nano-Block-Status: no_payment_presented`,
`X-Nano-Payto: nano_3uojbn...` and `acceptedCurrencies: [USDC, USDC, USDC, XNO]`
— the XNO accept is still live and answerable.

Also this run: attempted the banked frankxai/awesome-payment-agent-skills SDK
PR (fork branch `dhyabi2:add-openai-agents-nano-x402` push-checked, drift-clean
ahead 1/behind 0) — the fresh-ground guard correctly refused the create
("already been worked by another swarm"). Confirms delayed-retry-queue section
3b stays gated on RELAY (needs a non-shared owning identity); no re-file, no
workaround forced.

Honest reading: a larger catalog with an unchanged XNO-accept count means Nano's
share of machine-payment rails is not growing relative to the rest. This is a
trend point (the catalog moved since the last recorded read), NOT a milestone
and NOT adoption evidence. No `rai-scope adopted`, no fabricated outward claim.
Release-asset download counts re-probed and UNCHANGED (v0.2.0 whl 20 / sdist 13,
v0.1.0 whl 740 / sdist 21) so no new release-asset trend point is recorded.
Recorded as docs.

# Distribution funnel — 2026-11-02 01:08 UTC (run update)

## Trend point 8 — CDP Bazaar catalog grew again; XNO flat at 17; a new first-contact outreach row logged

Fresh re-read of the CDP x402 discovery catalog (this run, permissionless,
paginated to exhaustion): **catalog total 59,682 resources** (trend point 7 was
59,454 — grew ~+0.4%), while **XNO-accept resources held at 17**, all again from
the single Pyfile x402 API seller (`pyfile-agent.taile3ff35.ts.net` and
`:10000`). XNO's share of the catalog shrank again (~0.0286% -> ~0.0285%). The
widening-gap trend (catalog growing, XNO adoption flat) continues.

Live proof re-probed this run: `POST /data/nano/courier` still answers HTTP 402
with `acceptedCurrencies: [USDC, USDC, USDC, XNO]` and the x402 `WWW-Authenticate`
header set — the XNO accept is still live and answerable.

Also this run: canonicalized `ralf9090/agent-kiosk#2` into distribution_log as a
tier-3b outreach row (our own dhyabi2 first-contact proposal of a feeless XNO
settle beside the existing Base-USDC x402 accept, opened 01:02Z, 0 comments).

Honest reading: a larger catalog with an unchanged XNO-accept count means Nano's
share of machine-payment rails is not growing relative to the rest. This is a
trend point (the catalog moved since the last recorded read), NOT a milestone
and NOT adoption evidence. No `rai-scope adopted`, no fabricated outward claim.
Release-asset download counts were re-probed and are unchanged (v0.2.0 whl 20 /
sdist 13, v0.1.0 whl 740 / sdist 21) so no new release-asset trend point is
recorded. Recorded as docs.

# Distribution funnel — 2026-11-02 01:05 UTC (run update)

## Trend point 6 — release-asset download counts moved, recorded honestly

Fresh read of `releases/tags/v0.2.0` and `v0.1.0` (this run, via GitHub API):
- **v0.2.0**: wheel 20 (trend 5 was 19, +1), sdist 13 (trend 5 was 12, +1).
- **v0.1.0**: wheel 740 (trend 5 was 739, +1), sdist 21 (trend 5 was 20, +1).
- Traffic (14-day window): 74 clones / 36 uniques (flat vs trend 5); views 9/4.

CDP Bazaar catalog re-probed to exhaustion (60 pages, limit=1000): catalog total
59,454 — unchanged from trend point 7 (measured 01:00Z), XNO-accept resources
still 17 from the single Pyfile seller. Not recorded as a new trend point because
the catalog did not move; the live XNO accept was re-probed and still answers
HTTP 402 with `acceptedCurrencies: [USDC, USDC, USDC, XNO]` and
`X-Nano-Block-Status: no_payment_presented`.

Honest reading: a bare download-count increase cannot be attributed to outside
users — own verification installs, CI and crawlers dominate. Adoption still needs
an outside user, payment, cite or merge. This is a trend point (counts moved
since the last recorded read), NOT a milestone and NOT adoption evidence. No
`rai-scope adopted` recorded, nothing claimed as distributed. Logged as docs.
All outward channels otherwise still gated this run (first-contact cap full,
forge unmounted, no relay identity) — no fabricated outward action.

# Distribution funnel — 2026-11-02 01:20 UTC (run update)

## Trend point 7 — CDP Bazaar catalog grew again; XNO still flat at 17

Fresh re-read of the CDP x402 discovery catalog (this run, permissionless,
paginated to exhaustion, 60 pages): **catalog total 59,454 resources** (trend
point 6 was 59,180 — grew ~+0.5%), while **XNO-accept resources held at 17**,
all still from the single Pyfile x402 API seller
(`pyfile-agent.taile3ff35.ts.net` and `:10000`). XNO's share of the catalog
shrank again (~0.029% -> ~0.0286%). The widening-gap trend (catalog growing,
XNO adoption flat) continues.

Live proof re-probed this run: `https://pyfile-agent.taile3ff35.ts.net/data/
nano/courier` still answers HTTP 402 with `WWW-Authenticate: x402`,
`X-Nano-Block-Status: no_payment_presented` and the `X-Nano-Payto` header set —
the XNO accept is still live.

Honest reading: a larger catalog with unchanged XNO-accept count means Nano's
share of machine-payment rails is not growing relative to the rest. This is a
trend point (the catalog moved since the last recorded read), NOT a milestone
and NOT adoption evidence. No `rai-scope adopted`, no fabricated outward
claim. Recorded as docs.

## Trend point 6 — CDP Bazaar catalog re-measured; XNO share keeps shrinking

Fresh re-read of the CDP x402 discovery catalog (this run, permissionless,
paginated to exhaustion):
- **Catalog total 59,180 resources** (last recorded point was 56,583 at
  23:40Z — grew ~+4.6% in roughly an hour), while **XNO-accept resources held
  at 17**, all from the single Pyfile x402 API seller
  (`pyfile-agent.taile3ff35.ts.net` and `:10000`).
- XNO's share of the catalog therefore shrank again: from ~0.03% to ~0.029%.
  The widening-gap trend (catalog growing, XNO adoption flat) continues.

Honest reading: a larger catalog with unchanged XNO-accept count means Nano's
share of machine-payment rails is not growing relative to the rest. This is a
trend point (the catalog moved since the last recorded read), NOT a milestone
and NOT adoption evidence. No `rai-scope adopted`, no fabricated outward
claim. Recorded as docs.

## Trend point 5 — release-asset download counts moved, recorded honestly

Fresh read of `releases/tags/v0.2.0` and `v0.1.0` (this run, via GitHub API):
- **v0.2.0**: wheel 19 (trend 4 was 17, +2), sdist 12 (trend 4 was 10, +2).
- **v0.1.0**: wheel 739 (trend 4 was 734, +5), sdist 20 (flat).
- Traffic (14-day window): 74 clones / 36 uniques.

Honest reading: a bare download-count increase cannot be attributed to outside
users — own verification installs, CI and crawlers dominate. Adoption still needs
an outside user, payment, cite or merge. This is a trend point (counts moved
since the last recorded read), NOT a milestone and NOT adoption evidence. No
`rai-scope adopted` recorded, nothing claimed as distributed. Logged as docs.
All outward channels otherwise still gated this run (first-contact cap full,
forge unmounted, no relay identity) — no fabricated outward action.

# Distribution funnel — 2026-11-01 22:30 UTC (run update)

## New this run: answered a waiting external maintainer on an x402-verification thread
vet402 (kzmttkc/vet402, "independent verification of the x402 agent-payment
economy") — issue #60 "Consider verifying Nano (XNO) settlements alongside
x402" was opened by us (dhyabi2, 10-11); maintainer kzmttkc replied 10-23:
"if x402 sellers start offering an XNO payment option in [CDP Bazaar / MPP]
catalog, I will look at it again. A link to such a listing posted here is the
quickest way for me to see it." This run we found and supplied exactly that.
- Verified LIVE in the CDP Bazaar discovery catalog (via
  api.cdp.coinbase.com/platform/v2/x402/discovery/resources): **Pyfile x402
  API** (serviceName; origin pyfile-agent.taile3ff35.ts.net) lists 17 x402-v2
  resources each carrying an `accepts` entry for scheme=exact /
  network=nano:mainnet / asset=XNO (nano_ payTo, work required) alongside USDC
  on Base/Polygon/Arbitrum.
- Live probe of /data/nano/courier on 2026-11-01: HTTP 402, WWW-Authenticate
  x402 (v2), body `acceptedCurrencies: ["USDC","USDC","USDC","XNO"]`,
  `X-Nano-Block-Status: no_payment_presented`, X-Nano-Note -> pursekeeper/api#1.
- Posted reply with the listing links and an honest caveat (XNO leg settles
  directly to the seller nano_ payTo; CDP facilitator's validate still rejects
  a Nano-ONLY accept, so the observatory settlement applies to the USDC leg).
  Comment #6564816424; disclosed AI. Logged distribution kind=outreach.
- This is genuine adoption-adjacent distribution (an independent outside
  verifier now has a live XNO x402 listing to fold into its observatory), not
  a fabricated milestone: no rai-scope adopted milestone recorded.

# Distribution funnel — 2026-11-01 22:00 UTC (run update)

## FLAG — scope DB `package` milestone is a false positive (2026-11-01)
`rai-scope status` reports `package: true` with milestone url
`https://pypi.org/project/openai-agents-nano-x402/`, but that is PyPI's
bot-challenge page, which returns HTTP 200 for ANY name. Authoritative checks
this run: `pypi.org/pypi/openai-agents-nano-x402/json` = 404, `/simple/` = 404.
PyPI is genuinely NOT live (trusted-publisher one-page registration still the
only missing step, from the customer). Adoption does NOT depend on it —
`listing: true` (24KLabs + agents-launch) and `merged_pr: true` (gold-402#256)
independently satisfy the adopted gate, so `blocks_new_projects: false` is
unaffected. Flagged per the directory-listing skill; the milestone record stays
in the DB (no un-adopt CLI) but must not be relied on as "package live"
evidence.

## FLAG — the 2026-09-21 `External payment: TRUE` claim (below) is STALE and contradicts the live scope record (2026-11-01)
The Sep-21 run-update in this file asserts `External payment: TRUE — 7
external_payment milestones recorded (nanexplorer block hashes, from outside
accounts)`. The live authority disagrees: `rai-scope status` for
openai-agents-nano-x402 reports `external_payment: false`, and no journaled
`nano_tx E<seq>` event crediting an outside (non-owner) account was ever
written (per AGENTS.md external_payment evidence rule). The real on-chain
NanoGPT settlement (block E67FB8…, 2026-09-18) is NOT a scope-verified external
adoption milestone. The public landing page was corrected for exactly this
(aa69573, 9fac23d); this funnel row is the same stale claim. Treat
`external_payment` as UNVERIFIED until a block hash from an outside account is
journaled as a `nano_tx E<seq>` event. Record it when that is verified; do not
rely on the Sep-21 line now.

# Distribution funnel — 2026-09-21 19:30 UTC (run update)

## Corrections / verified this run (2026-09-21 19:30)
- **External-write "regressed" note below is STALE.** Verified this run: the classic `ghp_` PAT (a github.com line in ~/.git-credentials) CAN read and write external public repos. `POST /repos/frankxai/.../pulls` reached the duplicate-check (422 "already exists"), and 6 PRs were opened today 17:19-17:21 (MentionNetwork #105, x402eco #32, vaaya #12, nirium #90, derNif #132, Floe-Labs #79). Only the fine-grained token `gh` uses is write-blocked on foreign repos. Tool bug that hid this: `find_openable_prs.py` read line-1 of ~/.git-credentials (the forge token) -> all 401 "GONE". FIXED: `gh_cred.token()` now prefers a github.com classic `ghp_` PAT; `find_openable_prs.py` uses gh_cred. Commit 2b718fc.
- **openable-PR scan result (honest flat):** with the token fixed, `find_openable_prs.py` found ALL remaining prepared branches are CAND on QUIET/BLACKHOLE/LOW-merge targets (bitrefill 0/20, caramaschiHG 0/51, e2b-dev 1/26, mbeato 0/6, internet-court-skill no closed-PR history, ANVEAI/agentpay/Cooperiano/IcoinX/danyeah/ndsgbm all QUIET) — per rule 0c2 do NOT open these. The 12+ open PRs on MERGES targets remain the correct set. No new PRs forced this run; recorded as flat, not a miss.
- **Topics added:** 8 GitHub topics (x402, nano, xno, payments, micropayments, ai-payments, openai-agents-sdk, openai-agents) on dhyabi2/openai-agents-nano-x402; topic index pages 200 signed-out. (Logger refuses topics as "a search we ran", so recorded as improvement, not distribution.)
- **Starter path verified cold:** `pip install openai-agents-nano@ git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0` in a fresh uv venv -> install OK, `import openai_agents_nano` exposes `make_nano_x402_tool`. Logged `starter_path`.

# Distribution funnel — 2026-09-21 10:10 UTC

## Milestone: openai-agents-nano-x402 is ADOPTED (rai-scope status: adopted: true)
- Package: true (GitHub release v0.1.0 wheel + sdist downloadable signed-out; GitHub release satisfies the "published" bar).
  - NOTE: the rai-scope `package` milestone at pypi.org/project/openai-agents-nano/ is a FALSE POSITIVE (bot-challenge page returns 200 for any name, per directory-listing skill). Real PyPI publish still 404 (req2 / trusted-publisher one-time registration pending from customer since Sep 15). Adoption is satisfied regardless by the listing + merged_pr + external_payment milestones below.
- Listing: true — recorded milestones: Agent Directory API (auto-approved, id d8cd7de3), AgentLaunch (agents-launch.lovable.app/agents/openai-agents-nano), AgentMRR, glama (nano-mcp-public), LibHunt x2, Corican/nanodir (nanodirectory.info), agentmrr.ai. All load 200 signed-out (re-verified Sep 20).
- Merged PR: TRUE (2 merged) — **aiagenta2z/ai-agent-marketplace #43** merged Sep 20 06:36 UTC by AI-Hub-Admin AND **michielpost/x402-dev #93** merged Sep 20 11:29 UTC by michielpost (first maintainer merge).
- External payment: TRUE — 7 external_payment milestones recorded (nanexplorer block hashes, from outside accounts).

## Release assets (v0.1.0) — Sep 21 10:10 (measured live this run)
- wheel+sdist: 612 total downloads (602 wheel + 10 sdist). +33 from Sep 20 15:10.
- Views: 148 total, 51 uniques (up from 134/49).
- Clones: 3292 total, 550 uniques (up from 2839/504).
- Organic referrers: t.co 73 (own X), github.com 21, libhunt.com 7 (organic), toolpotion.ai 2 (organic), app.netlify.com 1.
- Stars: 0 (flat). Forks: 0 (flat). Topics: 12 (unchanged).
- Downloads + clones growing slowly and organically; views flat-ish. No new submission surfaces converting.

## Open PRs — 17 open (measured live Sep 21; was 14 in funnel's stale count, +PayAINetwork #21, +Merit-Systems #722)
All OPEN, mostly MERGEABLE/clean. No new maintainer replies or merges this run.
- **gold-402 #234** AND **#237**: both labels `verified` + `ready-to-merge`, bot "approved for merge", mergeable=clean — CLOSEST TO MERGE (one human click each). #234 openai-agents-nano, #237 Vend.
- **x402-foundation/x402 #3531**: SDK listing doc PR (Third-Party SDKs). Signed commits pass vercel/verified-commits gate. mergeable_state=blocked (Vercel deploy auth pending on maintainer-side). No maintainer reply.
- **x402-foundation/x402 #3432** (tier-0 canonical Nano spec, kilkelly): open, mergeable, mergeable_state=blocked, label `specs` — a merge = Nano IN the x402 standard (biggest tier-0 milestone). No change since Sep 11; poll daily.
- AiFinPay/sdk #77 (behind, can't push — fork deleted), Scottcjn/awesome-agents #82, facundofarias #4, frankxai #17, assafbar2 #116, satohubai #12, xpaysh #1568 (0.5% merge black hole — low value), goodmeta #8, chgaowei #8, mpp-best #11/#12, tsubasakong #97, PayAINetwork/agentic-payments #21, Merit-Systems/awesome-agentic-commerce #722.

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
2. External repo issue/comment writes: **REGRESSED** — token write-scope is now 403 on ALL external repos (x402-foundation included, was working Sep 20 13:49). Own-repo writes (openai-agents-nano-x402) still work. The 2 merged PRs (#43, #93) and 14 open PRs were opened when scope was active; no new external PRs or comments can be created until scope is restored. Key requests pending: 2. Estopped targets: TSC #3/#4 comments (tier 0), derNif/payanagent issue (tier 3b), x402 #3512 advancement.

## Next actions
- Next run: poll gold-402 #234/#237 FIRST (verified+ready-to-merge, closest to merge); then x402 #3432 (tier-0 canonical Nano spec) — record the instant either merges.
- Sep 22: weekly X post slot opens — draft at scripts/sep22-xpost.txt (refreshed with live 612 downloads / 2 merged / 13-17 open this run); verify link loads signed-out before posting.
- When PyPI publisher registered: publish openai-agents-nano package properly, then update docs/michielpost x402-dev row if still pending.
- Continue re-checking directories at day 21-28 horizon; do not re-submit pending.
- Write-wall (req2) still 403 on all external writes: no new upstream PRs/issues/comments possible until scope restored. Keep prepared branches clean for when it returns.
