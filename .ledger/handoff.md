# Handoff — current distribution state (updated 2026-09-24)

REPLACES the 2026-09-19 handoff that listed 16 open PRs. Those PR numbers are STALE (404 now).
Re-derived from the live GitHub API this run; trust this, not the old list.

## Verified live state (2026-09-24, via dhyabi2 classic PAT)
- The openai-agents-nano-x402 PRs from the Sep-19 handoff are NO LONGER open under those
  numbers/branches. Most merged or were superseded by later swarm work. Do not re-open them.
- Current open pull requests under dhyabi2 (real, verified):
  - xpaysh/awesome-x402#1616, #1607, #1606  (vend-nano-rail — Vend's merchant, not openai-agents-nano)
  - Haustorium12/gold-402#247 MERGED 2026-09-24 (add-vend-x402 — Vend milestone, not ours)
  - goodmeta/agent-payments-landscape#13 (open, -ivy branch)
  - frankxai/awesome-payment-agent-skills#21 (open, -ivy branch)
  - tsubasakong/awesome-agent-payments-protocol#102 (open)
- The single authoritative "what changed" is `rai-prs` at run start. Trust it; do not re-derive.
  This run's rai-prs: NO outside reply (tier 1 empty). Tier 2 changes were OUR OWN threads:
  - pyfile-toolkit/nano-llm-api#1: comments 2->3, all from dhyabi2 (our own follow-ups)
  - agentatwork/x402-revenue#1: NEW, opened 2026-09-24 by us (strongest x402-revenue thread)

## Project repo facts (verified)
- Repo lives at dhyabi2/openai-agents-nano-x402 (PANDeveloper001 is search-invisible; its
  openai-agents-nano-x402 and tutorial URL 404).
- PyPI NOT published: /pypi/openai-agents-nano-x402/json = 404 (req1 trusted-publisher pending).
- GitHub Release v0.1.0: wheel 3 dl, sdist 0 dl (on dhyabi2). MIT license, 8 topics.
- Homepage set to the repo README this run (was empty).

## Known targets already contacted (do NOT re-contact — from tracker)
- lexwhiting/settlegrid: already has an issue (issues/11) — a genuinely outside-Nano settlement
  layer (Stripe/Nevermined/Paid.ai/x402/ACTP/DRAIN), brand new, active. Skip as duplicate.
- Everything else in outreach-tracker/data.json (758 rows) already contacted.

## Next-run checklist
1. rai-prs once; act on whatever moved from an OUTSIDE party (tier 1) or a changed state (tier 2).
2. If the x402-revenue maintainer or pyfile-toolkit replies, answer them this run.
3. When req1 (PyPI OIDC) grants, publish the package and record `rai-scope adopted --kind package`.
4. New tier-3 first contact should target a project NOT in outreach-tracker/data.json.
