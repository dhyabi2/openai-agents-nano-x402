# Tutorial: paying an x402 API in Nano (XNO) from an OpenAI Agents SDK agent

This tutorial walks through paying a real x402-priced HTTP endpoint in
**self-custodied Nano (XNO)** with `openai-agents-nano` — a thin adapter on the
MIT [`feeless402`](https://feeless402.com) client. No other Nano payment logic
is involved; the adapter just exposes feeless402's `request_with_payment`,
`Wallet` and `RPC` as one OpenAI Agents SDK `Tool`.

Built by an AI agent. See `scope-manifest.json` for the scope decision.

## What you get

Your OpenAI agent gains a rail no other agent framework offers today:

| Property | Nano (this tool) | USDC on Base (AsterPay / CDP x402) |
|---|---|---|
| Cost to the payer | **0 XNO** (feeless, no gas) | 0–$0.001/tx facilitation + ~0.5% facilitator + gas (~$0.009–0.012) once volume passes the free tier |
| First finality | **sub-second** (~0.3 s) | ~2 s soft confirmation; full settlement to Ethereum later |
| Issuer that can freeze | **none** (self-custodied, no stablecoin) | USDC is issued by Circle; a freezable stablecoin |

Full numbers and sources in `docs/fee-finality-comparison.md`.

## 1. Install

The v0.1.0 release is the immutable public install path (works today, no credentials):

```bash
# one wheel file, no git and no build:
pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl

# or the tagged source:
pip install "git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0"
```

The sdist is at `.../releases/download/v0.1.0/openai_agents_nano-0.1.0.tar.gz`.

(PyPI is prepared but not uploaded: creating a PyPI project needs a human with a PyPI login to register
the pending trusted publisher. Once that exists, `pip install openai-agents-nano` is enough.)

The install carries a fresh `feeless402` dependency, so nothing else is
installed for you to pay.

## 2. First run (spendless)

```python
from agents import Agent, Runner
from openai_agents_nano import make_nano_x402_tool

tool = make_nano_x402_tool()   # binds ~/.nano-pay/wallet.json + RPC; model never sees them

agent = Agent(
    name="Paying agent",
    instructions=(
        "You can buy from paid x402 APIs. Always call nano_x402_fetch with "
        "dry_run=true first to see the price and get its quote_token; only "
        "call with dry_run=false, passing that quote_token back, if the "
        "price is within an acceptable cap."
    ),
    tools=[tool],
)

result = Runner.run_sync(
    agent,
    "Fetch https://api.example.com/report",     # an x402-priced endpoint
)
print(result.final_output)
```

The tool is **two-phase**, so the agent pays only an offer it has actually
seen:

1. `dry_run=true` reads the server's 402 quote and returns the price, `pay_to`
   and cap as plain text, **plus a single-use `quote_token`** binding that exact
   offer. Nothing is signed or broadcast.
2. `dry_run=false` (redeem) re-reads the quote and refuses with a plain refusal
   string unless a valid, unspent `quote_token` matching the current offer is
   passed back. A missing, expired, reused or offer-changed token is refused
   *before* anything is signed. A valid token is consumed, then feeless402
   signs locally, retries with the payment header, and verifies on the ledger.

The receipt the tool returns looks like:

```
PAID (Nano x402) — status 200, amount 0.0001 XNO, block 66b5e8c3...,
settled True, ledger confirmed
```

Only a ledger-confirmed settlement is ever reported as PAID. If a merchant
never replies after the block is signed, the tool surfaces the signed block and
verdict with "re-present the SAME block, do not re-pay blind" — never a generic
failure that invites a double payment.

## 3. Real safety defaults

- Default wallet `~/.nano-pay/wallet.json` (override with `X402_WALLET_PATH`).
- Default per-call cap `0.01 XNO` (override with `X402_MAX_XNO`). A price above
  the cap is refused without signing.
- Existing funded wallet? The tool **loads** it (never re-creates), so an
  imported or topped-up wallet signs with its held balance.
- One wallet never sends concurrently: payments are serialised behind an
  `asyncio.Lock` because Nano blocks are stateful and non-replayable.

## 4. Verify for yourself

The repo ships offline tests that need no network and no wallet with funds:

```bash
python tests/fail_closed_offline.py             # dry_run spends nothing; over-cap refused
python tests/two_phase_offline.py               # single-use token gate; offer-change refusal
python tests/receipt_honesty_offline.py         # never "PAID" unless ledger confirmed
python tests/payment_failure_honesty_offline.py # never re-pay blind after no merchant reply
python tests/wallet_load_offline.py             # existing funded wallet is loaded, not re-created
python tests/release_install_offline.py         # a built wheel installs and runs in a fresh venv
```

The ledger (`ledger summary`) is at 9 laws, all passing, probe 100/100, receipt
chain intact — see `docs/live-proof.md` for the recorded live mainnet redeem.