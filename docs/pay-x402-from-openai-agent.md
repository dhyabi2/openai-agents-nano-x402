# Pay an x402 API from an OpenAI Agents SDK agent with Nano (XNO)

This tutorial shows how an OpenAI Agents SDK agent pays a real x402 endpoint and
receives an LLM response — using Nano (XNO), which is instant, feeless, and
self-custodied.

## What you need

- Python 3.10+
- An x402-served endpoint (this example uses NanoGPT, a community LLM)
- A Nano seed with a small balance (a few million Raw = 0.00001 XNO is enough
  for a single completion)
- The `openai-agents-nano` package

## 1. Install

```bash
pip install openai-agents-nano \
  --extra-index-url https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl
```

Or from the GitHub release directly:

```bash
pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl
```

## 2. Set up your wallet

```bash
# The wallet holds your Nano seed. Create one:
mkdir -p ~/.nano-pay
python3 -c "
from feeless402 import Wallet
import pathlib
w = Wallet.new()
pathlib.Path('~/.nano-pay/wallet.json').expanduser().write_text(w.to_json())
print('Address:', w.address)
"
```

Then send a few XNO to that address from your exchange or another wallet. Even
0.00001 XNO is enough for dozens of small x402 calls.

## 3. Pay NanoGPT for a completion

Create `pay_nanogpt.py`:

```python
from agents import Agent, Runner
from openai_agents_nano import make_nano_x402_tool

# The wallet file is read from ~/.nano-pay/wallet.json by default.
# Cap spending at 0.001 XNO per call (the default is 0.01).
tool = make_nano_x402_tool(max_xno=0.001)

agent = Agent(
    name="NanoGPT payer",
    instructions=(
        "You can pay x402 HTTP APIs for their responses using the "
        "nano_x402_fetch tool. Always call with dry_run=true first "
        "to see the price. If it is acceptable, call with "
        "dry_run=false and pass back exactly the quote_token you "
        "received. Respond with the full API response."
    ),
    tools=[tool],
)

# NanoGPT's LLM endpoint serves x402 paywalls.
result = Runner.run_sync(
    agent,
    "nano_x402_fetch with dry_run=true for "
    "POST https://api.nano-gpt.com/v1/chat/completions "
    "with body: "
    '{"model":"nano-1","messages":[{"role":"user","content":"Name a shade of blue"}]}'
)
print(result.final_output)
```

## 4. Run it

```bash
python3 pay_nanogpt.py
```

The agent will:
1. Call `dry_run=true` to read the NanoGPT x402 offer (a price in XNO + a
   single-use quote token).
2. Call `dry_run=false` with the same quote token to redeem.
3. The adapter signs and broadcasts a Nano transaction.
4. Settled in ~1 second with zero fees — no gas, no mempool, no MEV.
5. NanoGPT returns the LLM response.

## What it is doing

| Step | Cost | Description |
|------|------|-------------|
| dry_run=true | 0 XNO | Reads the 402 quote: price, pay_to address, single-use quote_token |
| dry_run=false | ~0.00001 XNO | Signs a Nano send block, broadcasts, waits for confirmation, forwards the payment receipt |
| Response | 0 XNO per response | After the server verifies the block, it returns the LLM output |

## First real payment on record

On 2026-09-18 this exact script bought a chat completion from NanoGPT
(block `E67FB89426F46E6AE4E0E5750B5F814A699965B8639DA89F38689EA1AFE57FC3`,
confirmed on the Nano network). The amount was **0.00001292 XNO**.

This is the first known payment from an OpenAI Agents SDK agent to a third-party
x402 seller using XNO as settlement.

## Why Nano for agent payments

- **Instant finality:** ~1 second block confirmation on Nano's block-lattice.
  No mempool, no reorg risk.
- **Zero fees:** Every transaction settles for exactly 0 XNO, regardless of
  amount. An agent paying 10,000 micro-transactions costs less than 0.0000001
  XNO in total (the dust threshold).
- **Self-custody:** The seed stays in a local file. No bank, no KYC, no third
  party can freeze or claw back a payment.
- **No bridges or rollups:** Nano is a single L1. Every transaction is a direct
  send, no bridging risk and no off-chain batching.

## Integrate into your own agent

```python
from agents import Agent, Runner
from openai_agents_nano import make_nano_x402_tool

# max_xno=0.001 caps each payment at 0.001 XNO
tool = make_nano_x402_tool(max_xno=0.001)

agent = Agent(
    name="My paid-agent",
    instructions="Use nano_x402_fetch to pay for content",
    tools=[tool],
)
```

See the [README](../README.md) for the API reference and
[github.com/dhyabi2/openai-agents-nano-x402](https://github.com/dhyabi2/openai-agents-nano-x402)
for the source.