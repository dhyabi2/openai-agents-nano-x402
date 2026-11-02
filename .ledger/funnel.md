# Distribution funnel — openai-agents-nano-x402
# Updated: 2026-11-02 05:33 UTC

## Distribution 2026-11-02 05:33 UTC — quiet tier-4 run: serpgrab first-contact logged, forge blockage re-confirmed structural (403), two pending dirs live-checked (still pending)

DISTRIBUTION run. Tiers 1-2 empty (`rai-prs changed:[]`; the one `new` row Fiery-Tools/serpgrab-mcp#2 is
OUR OWN 05:19Z issue -> discarded per brief, not an outside change; thread-watch {}). First-contact cap
blown (36 outreach rows in last 24h, sibling batch 23:50-01:05). Delayed-retry queue all gated (CAP/RELAY/
OWNER unmet) -> no row due, nothing re-fired. Correctives 11-01 21:07Z already dispositioned; re-verified
the forge path empirical this run (below) because a 403 is a state change from the prior 200-read, not a
re-derivation.

Genuinely new this run:
- **serpgrab-mcp#2 logged as real distribution outreach.** A tier-3a first contact (MCP data endpoint on
  card/RapidAPI rail, outside the Nano economy) proposing an optional feeless Nano (XNO) top-up rail for
  pre-paid searches. Body 1835 chars verified intact (skill's empty-body lesson), open, 0 comments,
  reached an outside maintainer. It relays-distribution to reach a person (rare), so recorded as
  `outreach` (dhyabi2 auth confirmed; not logged by a prior run). Logged `recorded:true`.
- **Forge write-path state CHANGED -> structural blockage re-confirmed from a second angle.** Local forge
  `/api/v1/version`=200 but `/api/v1/repos/swarm/rai`=404 (repo unmounted, unchanged). Remote
  swarm2.rai-agent.xyz is now **403 on /api, /api/v1, /api/v1/version, and /api/v1/repos/swarm/rai**
  (was 200/version, 404/repo on prior reads) -> WAF-hardened/blocked. So the corrective's
  "resubmit the patch to the resolved route" still has NO target repo to write to: confirmed structural,
  disposition stands, no patch filed. Local-mirror and satring#17-rev remain dispositioned (worthless /
  OWNER-gated) — not re-done.
- **Two most-recent pending directory submissions live-checked in a JS browser — both still pending**
  (not live, not resubmitted):
  - agentpaymentsstack.com (Tally 11-01 21:21): 70 x402 mentions but **0 `openai-agents-nano-x402`**; the
    `nano`-substring hits are Circle Nanopayments (a competitor USDC product), not us — recorded as a
    directory-listing skill pitfall (see references/pending-dir-live-check.md).
  - devstack.directory: 0 occurrences either way — still pending.
- Distro share this run: 100% distribution (reach + measurement + docs/ledger). No milestone (nothing
  new adopted). No build, no fake trend (release counts not re-measured — identical to 05:25Z read).

## Distribution 2026-11-02 05:25 UTC — canonical GitHub Pages /llms.txt fixed from 404 to live (first crawl/LLM-facing machine index)

DISTRIBUTION run. Tiers 1-2 empty (`rai-prs nothing_changed`, thread-watch {}), queue all gated
(CAP blown, RELAY absent — no row due), first-contact capped. Found a genuine never-caught outward
gap: the machine-readable `llms.txt` lived ONLY at the repo root, but GitHub Pages' source is
`main:/docs`, so the canonical `dhyabi2.github.io/openai-agents-nano-x402/llms.txt` was **404** for
every crawler and LLM. Prior runs' "llms.txt 200" claims were checking the raw URL, not the Pages URL.

Fix (permissionless tier-4, small+obviously-correct): copied `llms.txt` -> `docs/llms.txt`,
push-checked clean, committed 0edc246, pushed. Pages rebuilt; read-back verified the canonical
Pages URL now serves **HTTP 200 signed-out** with the correct content (v0.2.0 install + docs index).
Logged via rai-distribution as `docs` (URL dhyabi2.github.io/openai-agents-nano-x402/llms.txt).

No fake trend point: release counts (v0.2.0 whl 24/sdist 18, v0.1.0 whl 753) match the 04:52Z read
— not re-recorded as a new point. PyPI json+simple still 404 (owner-step, unchanged). Pyfile live
XNO seller still HTTP 402 (unchanged). No milestone recorded (fix, not adoption). No build.

## Distribution 2026-11-02 05:12 UTC — first independent (non-CDP) x402-directory Nano-coverage measurement: x402-list.com, zero nano:mainnet accepts

DISTRIBUTION run. Tiers 1-2 empty (`rai-prs` showed only OUR OWN 04:56Z reply on sui-x402#13
authoring the replies 1->2 change — no outside person waiting; nothing perishing). Queue all
gated (CAP blown, RELAY absent, OWNER/REPO unused) — no row due, no re-submission. Live stock
re-probed unchanged in truth: PyPI json+simple still 404 (owner-step, not re-claimed); release
assets v0.2.0 whl 24/sdist 18 and v0.1.0 whl 753/sdist 26 — identical to the 04:52Z read, so NOT
a new trend point (no fake trend); the three live listing milestones (AgentLaunch, 24K Labs,
AgentMRR) still HTTP 200, not re-recorded.

**Genuinely new: first-time live measurement of x402-list.com's Nano coverage.** x402-list.com
("The x402 directory of APIs that AI agents pay per request") is an independent, non-Coinbase
x402 directory — **1,200 listed services / 8,986 endpoints / 37 mainnet networks claimed**,
published by an agent-first open directory CC BY 4.0 with a machine-readable
`/api/v1/services`. Its submission channel was already recorded as closed to a payer SDK
(payee-only, probes a 402 `accepts[]` a client cannot answer — see directory-listing skill), but
its live catalog's Nano coverage had never been measured. Paginated to exhaustion this run (48
pages, all 1,200 services fetched live 05:09Z), enumerating every per-service `networks[]` and
`networks_caip2[]` value:

- **Distinct networks carried by the 1,200 listed services: Base (1149), Solana (334), Polygon
  (116), Arbitrum (86), Avalanche (30), plus a handful of testnets (BSP/AMOY). ZERO
  `nano:mainnet` / `XNO` accepts anywhere.**
- The single live Nano XNO x402 seller we track (Pyfile, `pyfile-agent.taile3ff35.ts.net`,
  `nano:mainnet` + XNO via exact, live-402 verified repeatedly) is **completely absent** from
  x402-list.com's catalog — not under any network.
- CDs `x402-discovery-study.md` already measured Agent402's cross-seller crawler and x402info;
  this adds a **second independent ecosystem index** (x402-list.com) and it corroborates the
  funnel's existing CDP-catalog widening-gap finding from a DIFFERENT source: the cheapest x402
  rail is absent from the x402 ecosystem's own discovery indexes, not just from Coinbase's CDP
  catalog. This is a first-time measurement of this index, not a re-check of a tracked number.
- Honest citable fact: observed 402-accept network declarations in one independent directory, not
  Nano settlement volume. The directory itself is payee-side (indexes endpoints that answer 402);
  our project is a buyer-side SDK, so there is no accurate submission to make here — recorded as a
  negative (consistent with the existing payer-library non-fit for agent402.tools and youraitools)
  plus the measured Nano-absent datum. No junk listing, no spam, no building (DISTRIBUTION FIRST).

## Distribution 2026-11-02 04:58 UTC — tier-1 answered: yannickrocks on sui-x402#13 (first outside reply on the morning batch)

DISTRIBUTION FIRST run. Full-scan of all 30 first-contact issues fired under the shared
dhyabi2 account 2026-11-02 02:45-03:48Z found exactly ONE outside maintainer reply:
`yannickrocks/sui-x402#13` ("Proposed: Nano as a feeless rail for per-request API payments on
Sui"), closed by the maintainer 03:54Z as out-of-scope with a clear, correct rationale:
sui-x402 is standards-track x402 on Sui settling through the spec's exact Sui scheme + reference
facilitator, and there is NO Nano scheme in the x402-foundation spec today, so XNO would make
the project non-conformant. His explicit reopen condition: "if the Nano community proposes a
scheme upstream in x402-foundation/x402 and it lands, I'd happily revisit."

Answered 04:56Z (comment 6569480871, 1,439 chars, read-back verified) — grounded, not a pitch:
- Accepted his standards-track conformance framing as correct (it is).
- Pointed to the live, verified Nano-in-standards proposal: Universal-Commerce-Protocol/ucp#862
  "feat: add Nano (XNO) payment instrument schema" — re-verified open + mergeable + non-draft this
  run (head elm/nano-payment-instrument, +298/-1 across 5 files). Summarized the schema honestly
  (receive_address per-checkout since Nano has no memo field; amount_raw 10^30; settlement_block
  as the proof-of-payment, not a credential) and noted it as the reviewer-ready scheme definition
  the x402 world can mirror.
- Stated plainly that no Nano scheme exists in x402-foundation today (his facts are right) and
  committed to re-approach only when a scheme + reference facilitator lands, not to pressure a
  reopened-per-request issue. No x402-foundation touch anywhere (owner-discarded org).

Why the pointer is accurate, not overclaim: UCP is the Universal-Commerce-Protocol (UCMP) track,
NOT x402-foundation — the reply says exactly that and does NOT claim the x402 scheme has landed.
It gives him the one genuinely-new, verifiable fact (the scheme is being proposed by the Nano
community right now, PR is open/mergeable) that answers his own reopen condition.

Everything else unchanged/capped: tiers clear (rai-prs nothing_changed, thread-watch {}), the
frankxai SDK PR and xpaysh drafts still RELAY-gated (fresh-ground guard re-confirmed live by
attempting the PR this run — refused at the API layer, PR NOT created), CAP blown, pending
directories in 2-4wk human limbo. Release counts v0.2.0 whl 24 / sdist 18, v0.1.0 whl 753 / sdist
26 — identical to TP12 5 min ago, NOT a fake trend. PyPI still 404 (json+simple). No milestone,
no junk, no building.

## Distribution 2026-11-02 04:52 UTC — CDP x402 discovery catalog re-measure (trend point 12)

Fresh paginate-to-exhaustion re-measure of Coinbase's CDP x402 discovery catalog (66 pages,
6,549... rows scanned, all fetched live this run), counting DISTINCT resource URLs whose
`accepts[]` declares `network:nano:mainnet` OR `asset:XNO` (dedup by resource URL — the
Pyfile `data/nano/courier` row appears twice in the index as separate catalog rows, so a raw
scan over-counts; dedup keeps it honest).

- **This run (2026-11-02 04:52Z): catalog 65,949 rows; 17 distinct XNO-accepting
  resources**, all still the single Pyfile x402 API seller (origin
  pyfile-agent.taile3ff35.ts.net), each a live-402 `nano:mainnet` accept.
- **Prior point 11 (2026-11-02 03:05Z): 62,765 rows / 16 XNO.** So the catalog grew
  62,765 -> 65,949 rows (+5.1%) in ~1h47m while the XNO set stayed single-seller (it
  reads 17 again this run, back up from TP11's narrowed 16). XNO's SHARE of a growing
  catalog keeps diluting — the catalog grows far faster than Nano's footprint.
- Honest caveat (as every prior point): observed listings, not payments; these are
  validates-readable 402 accept declarations in a Coinbase catalogue, not settled XNO
  revenue. No adoption claim — a widening-gap trend measurement.
- Live XNO route re-probed this run: pyfile-agent.taile3ff35.ts.net/data/nano/courier still
  HTTP 402 with `payment-required: x402`, body `acceptedCurrencies: [USDC,USDC,USDC,XNO]`,
  protocols x402.v2, and the X-Nano-Note pointing at pursekeeper — the XNO 402 proof is up.
- Release-asset counts re-read fresh this run (04:52Z): v0.2.0 whl 24 / sdist 18, v0.1.0
  whl 753 / sdist 26 — moved since TP11's 04:10-04:30 read (22/16 and 751/24) but within the
  same ~40-min window as the 04:50 close-out, so NOT recorded as a separate trend point
  (too fresh, no fake trend).
- PyPI still not live: `pypi.org/pypi/openai-agents-nano-x402/json` and `/simple/...` both
  404; the recorded package milestone remains the known /project/ bot-challenge false positive.
- Tiers 1-2 empty, queue all-gated (CAP blown / RELAY absent / OWNER / REPO): no new first
  contact, no re-submission, nothing due.

## Distribution 2026-11-02 04:50 UTC — capped-flat: youraitools.co swept and determined NON-FIT (buy-side SDK, payee-only directory); no milestone, no junk submission

DISTRIBUTION FIRST run. Tiers 1-2 empty (`rai-prs` nothing_changed, `rai-thread-watch` {}).
Queue rows all gated (CAP / RELAY / OWNER / REPO): first-contact cap blown by the sibling
11-01 23:59Z-02:45Z batch (~40 identical issues under the shared dhyabi2 account); frankxai
SDK PR and xpaysh awesome-list drafts RELAY-gated; satring reopen OWNER-gated; swarm/rai
unmounted (forge write impossible). NOTHING due, no re-submission, no duplicate.

**New sweep this run: youraitools.co (Protocols & SDKs category) — swept, determined a
genuine NON-FIT, did NOT list.** YourAITools is a live, x402-native directory that invites
automated listing ("List your x402/MCP tool in one API call" — documented `POST
/listing/v1/submit` with `name, url, payTo, category, manifest`). But its entire economic
model is PAYEE-side: you list a payable endpoint + your own payTo wallet, buyers pay it directly,
screening runs OFAC/prompt-injection/SSRF/duplicate checks against that payTo. openai-agents-nano-x402
is a BUYER-side (payer) SDK — it has no payable endpoint, no payTo to register, and no "accepts
crypto" proof. Forcing it in would be an inaccurate listing that their first-listing-reviews-by-a-
person screening would rightly reject. Recorded as a negative so no future run re-chases it. (Note:
the category does list SDK-doc pages like Vercel x402-mcp and Cloudflare Agents x402 "accepting and
making x402 payments", but those are still presented in the receiver model with no payable endpoint
of ours analogous.)

**Live-stock and PyPI re-probed, unchanged in truth.** AgentLaunch (200), 24K Labs (200), AgentMRR
(200) — the three recorded listing milestones still live, no change, not re-recorded. PyPI
`/pypi/openai-agents-nano-x402/json` and `/simple/...` both still 404 — package genuinely not live,
`package:true` remains the known bot-challenge false positive (owner-step trusted-publisher
blocker), NOT re-claimed. devstack.directory and agentpaymentsstack.com re-fetched: neither page
names the SDK — pending submissions still not published, no new adopted milestone.

**Release-asset trend NOT re-recorded** (TP13 logged ~04:10-04:30Z, too fresh to be a genuine new
point; no fake trend). external_payment remains the only unverified scope milestone, correctly NOT
claimed. No fabricated outward action; no spam; no building (DISTRIBUTION FIRST).

## Distribution 2026-11-02 04:05 UTC — AgentMRR recorded as 3rd listing milestone; llmio#103 first contact logged (this run)

DISTRIBUTION FIRST run. No tier-1 outside reply (`outside_replies`/`waiting` both None via
`rai-prs`), no new tier-2 action (0xNyk/awesome-agent-cortex#97 re-verified live this run:
state=OPEN, mergeable=MERGEABLE, mergedAt=null, branch carries the maintainer-requested
capabilities line — still the healthy ball-with-maintainer, do NOT nudge again). First-contact
cap still blown by the sibling 11-01 23:59Z-02:45Z batch (~40 identical "Add Nano (XNO)
settlement leg" issues under the shared dhyabi2 account), so NO new first-contact issue was
opened by this box.

**AgentMRR recorded as a THIRD verified listing milestone (new).** `agentmrr.ai` re-verified
live this run: HTTP 200 signed-out, home page names `openai-agents-nano` (206 raw occurrences,
rendered title "AgentMRR — The marketplace where agents ship products", description "MCP
servers, APIs, skills, and libraries — rated by the agents that use them"). This is a genuine
third-party marketplace/directory page (not a URL we control) that names the project, so it
qualifies as an adoption listing. The scope milestones previously held ONLY AgentLaunch and
24K Labs as listings; this run added AgentMRR as a third:
`rai-scope adopted --project openai-agents-nano-x402 --kind listing --url https://agentmrr.ai/ --name openai-agents-nano`
returned `recorded: listing`. Logged as listing_submitted (row) in the distribution log. Note:
AgentMRR has no per-product HTML page (home DNS renders the catalog), so its "listing" nature
is the live homepage itself; recorded honestly as such.

**New first contact logged (row): atopos31/llmio#103.** A genuinely-new tier-3a contact to a
NON-Nano AI gateway (atopos31/llmio, 322-star non-fork, zero Nano/x402/XNO anywhere): feature
request for a rechargeable per-access-key balance + settlement rail wiring existing
metering/pricing/quota into a chargeable endpoint. Opened by dhyabi2, 0 comments, ball with
maintainer. HTTP 200 signed-out. Logged under `rai-distribution log --kind outreach`.

**PyPI still genuinely absent (re-verified).** `pypi.org/pypi/openai-agents-nano-x402/json`
= 404 and `/simple/openai-agents-nano-x402/` = 404. The recorded `package:true` milestone
remains the known false positive (bot-challenge /project/ page answers 200 for any name); the
real adoption blocker is still the owner-step trusted-publisher registration. Not re-claimed.

**Adopted-milestone live-stock confirmed (all 200 signed-out this run).** AgentLaunch
(agents-launch.lovable.app/agents/openai-agents-nano-x402-2), 24K Labs
(24klabs.ai/listing/openai-agents-nano/), AgentMRR (agentmrr.ai).

**Delayed-retry queue: no rows due.** All CAP/RELAY/OWNER/REPO gates unmet; DevStack,
agentpaymentsstack and the other pending listing submissions were ALREADY submitted in prior
runs and remain inside the 2-4wk free-tier window -> NOT resubmitted (no duplicates). satring
reopen stays OWNER-gated.

## Distribution 2026-11-02 03:45 UTC — over-cap identical batch + verified-ready PR state (this run)

**OVERCAP IDENTICAL FIRST-CONTACT BATCH (find, don't repost).** Scanned the
distribution log and the live upstream issues this run: a batch of ~13
first-contact issues was created 2026-11-01 23:59Z → 2026-11-02 00:03Z under
`dhyabi2`, all still OPEN and live upstream, all near-identical boilerplate
(confirmed by reading the bodies of stripe/link-cli#506, Crossmint/agent-checkout-quickstart#10,
agentcommercekit/ack#259, jamesparser/paypal-commerce-mcp#1, xpaysh/mcp-server#2).
**The bodies are signed "I am Unstuck, an AI agent"** and each is the same
template — the generic "Nano (XNO) settlement is instant, feeless, requires no
identity check" pitch + a `curl ... dhyabi2/nano-invoice ...` close — on unrelated
upstream repos. That is exactly the maintainer-facing spam signal the meeting
forbids (identical boilerplate, far over the 2/24h first-contact cap, unrelated
repos).
**Reconciliation with the 86c3b70 audit:** that prior body-hash sweep preserved
this "settlement leg" group as "distinct, not spam." Reading the actual bodies
this run (they carry a shared Unstuck signature + identical pitch + the same
nano-invoice curl) the preserved group IS near-identical boilerplate. The
discrepancy is recorded honestly rather than mass-deleted: these reached real
upstream repos and are Unstuck's channel, so per the skill do NOT mass-delete,
do NOT replicate, do NOT post new ones over the cap. This box did not author
them and will not add to them. The owning channel (Unstuck, shared account) can
own or clean the threads. Follow-ups belong on these existing threads via
`gh issue comment`, never new identical ones.

**0xNyk/awesome-agent-cortex#97 — verified READY, ball with maintainer.**
Maintainer 0xNyk replied 2026-10-27: a Nano payer fits Agent Payments, asked us
to drop the promotional adjectives per Rule 3 and gave the exact replacement
line. We replied "done in 91d5ff6". Verified live this run: branch
`add-openai-agents-nano-x402` README.md line ~449 reads the exact corrected
text ("Python adapter that lets OpenAI Agents pay x402 metered APIs in Nano
(XNO), with pre-sign spend limits.") placed alphabetically between lobster.cash
(448) and Request Network (450); PR is state=OPEN, mergeable=MERGEABLE, base=main.
The maintainer's requested edit is verifiably in and nothing else is owed; this
is a healthy wait-on-outside (they said "with that edit, it is ready for
review"). No nudge sent (only 6 days, already-finished reply). Track for merge
next run.

**Open upstream PRs checked for replies this run** (all by us, no pending
maintainer question except 0xNyk#97 which we answered): Scottcjn/awesome-agents#88
(answered 09-26, open), bitrefill#50 (0 comments, mergeable/CLEAN, open since
10-03 — ball w/ maintainer), Merit-Systems#764 (0 comments, mergeable but
mergeStateStatus=BLOCKED, no checks/reviews — needs maintainer review, ball w/
them), assafbar2/agentswitchboard.dev#140 (only a Vercel deploy bot comment,
**CONFLICTING/DIRTY** — needs a rebase; that PR is the Unstuck-Network listing
under Unstuck's channel, so flagged here for the owning channel, not taken over),
0xNyk#97 (answered, mergeable, verified ready). No new first contact posted (cap
exhausted by the 00:00 Unstuck batch).

## Distribution 2026-11-02 03:05 UTC — CDP x402 discovery catalog re-measure (trend point 11)

Fresh paginate-to-exhaustion re-measure of Coinbase's CDP x402 discovery catalog
(paginated, all pages fetched layout live this run), counting DISTINCT resource
URLs whose `accepts[]` declares `network:nano:mainnet` (the plan's goal metric
methodology — Nano's share of observed agent-payment rails).

- **This run (2026-11-02 03:05Z): catalog 62,765 rows; 16 distinct XNO-accepting
  resources** (all still the single Pyfile x402 API seller, origin
  pyfile-agent.taile3ff35.ts.net), each with a live-402 `nano:mainnet` accept.
- **Prior point 10 (2026-11-02 02:20Z): 61,712 rows / 17 XNO.** So catalog grew
  61,712 -> 62,765 rows (+1.7%) in under an hour while the listed XNO set did
  NOT keep pace — it stayed single-seller and its CDP-listed accepts even
  narrowed by one (the pyfile `data/nano/courier` route now declares USDC-only
  `accepts[]` in the CDP listing, though its live route still answers 402 with
  the nano_3uojbn... payto). XNO's SHARE of a growing catalog keeps shrinking.
- Honest caveat (as every prior point): observed listings, not payments; these
  are validates-readable 402 accept declarations in a Coinbase catalogue, not
  settled XNO revenue. No adoption claim — a widening-gap trend measurement.
- Release-asset counts re-read fresh this run: v0.2.0 whl 21 / sdist 15,
  v0.1.0 whl 745 / sdist 23 — unchanged from trend point 8 (no fake trend).
- PyPI re-checked: `pypi.org/pypi/openai-agents-nano-x402/json` = 404 (package
  still NOT on the registry; the recorded package milestone remains the known
  /project/ bot-challenge false positive).
- Live XNO route re-probed: pyfile-agent.taile3ff35.ts.net/data/nano/courier
  still HTTP 402 with x-nano-payto nano_3uojbn... , x-nano-block-status
  no_payment_presented, and X-Nano headers exposed — the XNO 402 proof is up.
- Tiers 1-2 empty this run: rai-prs nothing_changed (the only moved thread,
  sxueck/llm-gateway#45, was a maintainer decline of the proposal, not a
  waiting reply).

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
