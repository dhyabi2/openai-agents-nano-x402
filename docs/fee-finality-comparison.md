# Measured fee and finality comparison: Nano (XNO) x402 vs USDC-on-Base x402

A plain, cited comparison so agents and developers can choose a rail with
numbers, not slogans. Nano and the USDC rails are both real payment options
for AI agents; they differ in cost, speed, finality model and custody. Nano's
numbers come from this repo's own measured runs and public node lookups; the
USDC/Base numbers come from the sources cited in each row.

## Headline

| | **Nano (XNO) — `openai-agents-nano`** | **USDC on Base — AsterPay / Coinbase CDP x402** |
|---|---|---|
| Payer cost per call | **0 XNO** (feeless, no gas) | ~$0–0.001 facilitation, plus ~0.5% facilitator, plus gas |
| First settlement | **sub-second, ~0.3 s** | ~2–4 s on Base (soft confirm) |
| Full finality | on this network (see caveat) | settlement to Ethereum later |
| Custody | self-custodied seed; **no issuer that can freeze** | USDC is issued by Circle (a **freezable stablecoin**) |
| Network / onboarding | Nano node + a wallet file; no facilitator account | facilitator account, KYA/screening, off-ramp to fiat |

## Cost — measured / sourced

**Nano: 0 XNO per transaction.** Nano is feeless by design — no miners or
validators take a cut (Nano whitepaper; Coins Wiki: "zero transaction fees",
"17 million times more energy-efficient than Bitcoin"). In this repo's live
proof (`docs/live-proof.md`) a real redeem settled 0.0001 XNO with **0 XNO
paid in fees**; the block was confirmed on two independent public nodes
(`rpc.nano.to` and `rainstorm.city`).

**USDC on Base (x402):** facilitation is advertised as ~$0 at the surface
(AsterPay "facilitation is free forever"; CDP "$0" precedent), but the real
cost is layered:

- **On-chain settlement:** CDP Facilitator is free only for the first 1,000
  onchain transactions/month, then **$0.001 per onchain transaction**
  (stablecoininsider.org, September 2026).
- **Facilitator percentage:** other measured providers charge ~**0.3–0.5%**,
  with a minimum like $0.01, e.g. eSIM-x402: "0.5% facilitator fee (minimum
  $0.01 per transaction)". Coinbase SDK itself is cited there at 0.5% and a
  $0.01 minimum on top of gas.
- **Gas:** measured on Polygon, ~$0.009–0.012 per transaction
  (eSIM-x402, 500-tx comparison: avg 47,200 gas at 32 gwei ≈ $0.0091). Gas is
  a real per-call cost an agent's wallet must fund.

So for a small call, a USDC payer can pay a few cents of gas + facilitator
percent, while a Nano payer pays 0 XNO. For high volume, CDP's $0.001/tx
onchain fee still beats a DIY self-settle, but all of these that CDP/AsterPay
price at $0 are "free to verify + settle"; the per-call gas and the
facilitator cut (where charged) are what actually reach the payer.

## Speed and finality

**Nano:** sub-second. Coins Wiki: "average settlement time of **0.3
seconds**"; NowNodes (2026): "confirms in under a second". Nano's block-lattice
has no block interval; a block is "immediately" usable once its PoW is computed
(whitepaper). The repo's live redeem `docs/live-proof.md` was confirmed on two
public nodes.

**USDC on Base:** the x402 docs put on-chain settlement at "~2–4 s on Base"
(AsterPay). Base's own spec distinguishes soft confirmation (~2 s) from full
finality (settlement to Ethereum, later); stablecoin transfer estimators list
Arbitrum/Optimism/Base soft confirms "within seconds, though full finality
(settlement to Ethereum) takes longer".

**Caveat (honest):** "fast" on Base is soft confirmation of an L2 block;
true cross-L2 / to-L1 finality takes longer. Nano confirms *on its own
network* — there is no separate parent chain to settle onto, so sub-second
is its full finality. The trade-off is that Nano is its own ledger, not an
EVM L2 inside the Ethereum settlement umbrella.

## Custody and who can freeze

- **Nano:** fully self-custodied. Your seed stays in a wallet file on disk;
  `openai-agents-nano` never holds or exposes it, and there is **no entity
  that can freeze or blacklist** a Nano payment.
- **USDC:** is a Circle-issued stablecoin. Every USDC payment is settled by an
  issuer that can freeze or blacklist addresses, and the x402 facilitator
  itself runs sanctions/OFAC screening (CDP "built-in OFAC/KYT"; AsterPay KYA
  + Chainalysis) that can decline a payment before it settles. That screening
  is a feature for a compliant merchant and a central point of control for an
  agent that wants censorship-resistant payment.

## A fair "when to use which"

- **Use Nano** when the priority is zero per-call cost, sub-second finality,
  and self-custody with no freezeable issuer — the default for an autonomous
  agent spending its own XNO on many small calls.
- **Use USDC/Base** when you must settle into a bank account in fiat (EUR/SEPA
  via AsterPay), need a stablecoin with an existing merchant/compliance story,
  or the payee explicitly quotes USDC. Nano is not a stablecoin and it has
  price volatility; for ticket values where you cannot tolerate Nano's price
  exposure, that is a real reason to prefer a stablecoin.

That last point is the honest limit of Nano: it is feeless and fast, but it is
not a USD-pegged asset. For an agent paying sub-cent-micro fees with its own
holdings the trade-off is usually worth it; for a merchant who needs euros in
a bank account, a stablecoin rail is currently the closer fit.

## Evidence record: how finality model shapes post-settlement audit

Beyond cost and speed, the choice of rail changes what the **evidence record**
for a completed x402 payment looks like — which is the open question in the
x402 TSC's post-settlement accountability / evidence-record item (TSC #4) and
its two-tier requirements structure (TSC #9).

- **Nano.** Settlement evidence *is* the block. A Nano payment is a single
  self-verifying block in a per-account block lattice — no mempool, no reorgs,
  no irreversible-reverting dispute window. `confirmation_height = 1` is
  final; there is nothing to wait out and nothing an attacker can roll back.
  Any nano node verifies the block from bytes alone with a standard library
  (a POV block hash + signature check) — no hosted call, no API key, no
  account. That matches the recomputability bar the working group already
  set for cross-project evidence. Live example: block
  `66b5e8c352e10d6d7078cd9562f7501f41e318e3d4ac3c12b00511b1f96cd4cf`
  (0.0001 XNO x402 redeem, `docs/live-proof.md`) was confirmed on two
  independent public nodes; an auditor re-derives the same verdict from the
  block bytes on any nano node. Verified `count`/`cemented` = 224,490,367
  blocks on `rpc.nano.to` (2026-09-20) — every one of them is a settled,
  conflict-free final record.

- **USDC on Base.** The evidence record must prove more. A Base ERC-20
  transfer is an L2 event under an Ethereum optimistic rollup: to be safe
  from challenge it must reference the L2 block *and* the eventual L1 state,
  and track the 7-day dispute window. Two working systems (e.g. Tersign's
  evidence-record-conformance vectors, the AXES Golden Trace corpus) already
  model this richer shape — it is workable, but it is strictly more state to
  carry and verify than Nano's single self-verifying block.

This is not an argument that Nano replaces USDC — a merchant needing EUR in a
bank account should still pick the stablecoin rail. It is a concrete,
verifiable way the rail choice lowers the cost of the evidence layer, which
is exactly the "one substrate, many profiles" / "no hidden role transitions"
direction the two-tier structure the TSC is weighing (TSC #9) points at.

## Sources

- Nano fee + speed: Coins Wiki — "zero-fee, instant", "0.3 seconds", "17Mx
  more energy-efficient than Bitcoin"; Nano whitepaper (block-lattice, no block
  interval, "no transaction fees"); NowNodes (2026) "confirms in under a
  second".
- Nano measured run: this repo — `docs/live-proof.md`, block
  `66b5e8c3...` confirmed on `rpc.nano.to` and `rainstorm.city`, 0 XNO fee.
- USDC/Base speed: AsterPay "What is x402?" — on-chain settle "~2–4 s on
  Base"; Base docs "Transaction Finality"; Spark USDC/USDT transfer estimator —
  L2 soft confirms within seconds, full finality to Ethereum later.
- USDC cost: stablecoininsider.org (2026-09) — CDP free to 1,000 onchain
  txs/mo, then $0.001/tx, verify always free; eSIM-x402 — measured 47,200 gas
  @ 32 gwei ≈ $0.0091, 0.5% facilitator (min $0.01); AsterPay — "facilitation
  is free forever", 0.5% + €0.10 SEPA settlement, KYA + Chainalysis screening.
- Custody / freeze: AsterPay, stablecoininsider.org (CDP OFAC/KYT).