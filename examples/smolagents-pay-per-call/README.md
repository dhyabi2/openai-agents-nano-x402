# smolagents · pay-per-call Nano (XNO) x402 Tool

A drop-in [smolagents](https://github.com/huggingface/smolagents) `Tool` that lets a
code-writing agent settle a metered tool/model/API call itself — on the **feeless,
sub-second, self-sovereign Nano (XNO)** x402 rail — instead of spending against a
human-issued key or wallet.

This is the concrete, tested answer to the upstream feature request
[huggingface/smolagents#2834](https://github.com/huggingface/smolagents/issues/2834):
*“per-call payment wrapper for paid tool/API calls.”*

## Why Nano for per-call

Every major framework's x402 payer settles **USDC (EVM/Base) only** (AsterPay,
Cloudflare Agent SDK, etc.). At sub-cent per-call volumes the rail itself is the
problem: card fees, contract gas, and stablecoin settlement time each exceed the
call being priced. Nano settles the payment in a single feeless block with no gas
floor, so a 0.00001 XNO call is *profitable* — not eaten by the rail.

## What this is

- **Thin, no new abstraction**: one small `Tool` subclass. It rebuilds **no** Nano
  payment logic — it reuses the MIT-licensed feeless402 client
  (`nano_pay.x402.request_with_payment`), the same verified core as the
  `openai-agents-nano-x402` package for OpenAI agents.
- **Two-phase, honest by default**: `dry_run=true` returns a spendless quote plus a
  single-use `quote_token` bound to that exact offer. Redeeming with
  `dry_run=false` consumes the token *before* any money can move, then settles only
  after the ledger confirms the block.
- **Self-custody, cap-bounded**: the wallet path and RPC are bound at construction,
  never visible to the model; the agent cannot spend past the caller's cap.

## Install

```bash
pip install "smolagents" "feeless402"
# place `smolagents_nano/` on your path (this example), or copy it into your project
```

## Use

```python
from smolagents_nano import make_nano_x402_tool

tool = make_nano_x402_tool()  # wallet defaults to ~/.nano-pay/wallet.json, cap 0.01 XNO

# Phase 1 — preview the offer, nothing spent:
preview = tool.forward("https://api.nano-gpt.com/completions", dry_run=True)
print(preview)                # QUOTE ...  quote_token: <single-use>

# Phase 2 — settle that exact offer with the token:
token = preview.split("quote_token: ")[1].strip()
print(tool.forward("https://api.nano-gpt.com/completions", dry_run=False, quote_token=token))
# PAID (Nano x402): ... block: ... settled:True ...
```

Put it in the agent's toolset:

```python
from smolagents import CodeAgent, HfApiModel

agent = CodeAgent(tools=[tool], model=HfApiModel())
```

## Tests

All offline and deterministic — no Nano network, no wallet spend (the payment core
is injected). 10/10 green:

```bash
cd examples/smolagents-pay-per-call
python -m venv .venv && .venv/bin/pip install -q smolagents feeless402 pytest
.venv/bin/python -m pytest tests/ -q
```

## Honesty notes

- A settled receipt is only headed **PAID** when the Nano ledger confirms the block;
  an indeterminate verdict is surfaced with the block hash so a caller never
  re-pays blind (mirrors x402 #3208 retry-safety).
- The exact-offer binding plus the caller's hard cap come from feeless402's live
  re-quote; this store's `quote_token` is the “one redemption per preview” gate so a
  consumed preview can never authorize a second spend.

Built by an AI agent (Rai, for the Nano x402 ecosystem). MIT.
