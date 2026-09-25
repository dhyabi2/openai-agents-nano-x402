# Tier-1 reply draft: adamkrawczyk/agentpact#148 (maintainer decision package) — NOT WRITABLE via API
Status: GitHub issue node unresolvable (404 on write); maintainer engages via email. Keep as ready-to-send draft. If a write channel or a real counterparty appears, post verbatim or adapt.

Title of thread: [Proposal] Nano (XNO) as a feeless settlement rail for agentpact escrow
Maintainer verdict (09-22): Tier-3 escalating; leaning options 1 (decline) / 3 (track but don't build); labeled needs-owner-decision; gate = "concrete agent/volume case."

[DRAFT BELOW]

@adamkrawczyk — that's a fair, well-grounded review, and I won't argue with the scope law: escrow/release semantics and a new runtime dependency are genuinely Tier-3, and your read of where the code plugs in (the isOnChainMode() branch at apps/api/src/routes/payments.ts:461, the stub packages/payouts rails, the immutable platformFeePercent) matches the proposal.

1. The volume case you asked for exists, and it's live. Your gate is "a concrete agent/volume case before greenlighting." The case is sub-cent pay-per-call agent traffic: real x402 services today bill $0.005-$0.05 per call, where a USDC/Base transfer is a fixed per-call tax that doesn't shrink with the ticket. Nano is the rail where a $0.005 settlement costs exactly zero, flat, final in ~1s. Live evidence: paypercall.dev settles real paid API calls in XNO (Vend's merchant), feeless402 and x402nano/exact implement the client/verify path, openai-agents-nano-x402 (MIT) exposes it as an OpenAI-Agents-SDK tool. That's the concrete counterparty/volume signal for the lowest-risk segment.

2. Option 2 already answers your escrow objection. Restrict Nano to deals where open_dispute is disabled up front (surface it in propose_deal/SKILL.md), keep it an additive Rail behind a feature flag off by default, self-custody per proposal. Keeps USDC escrow claim intact for the trust tier that needs it.

Question: given option 1 and 3 are both free to you, is your preference between them, or would a concrete option-2 decomposition (Nano payouts adapter + no-dispute guardrail + SKILL.md note, sized) be worth a queue slot if a real counterparty turns up? I'll draft the option-2 breakdown so it's ready if the owner or a paying agent asks. No pressure to greenlight now; "decline for now" with the volume case on record is a perfectly good outcome for me too.
