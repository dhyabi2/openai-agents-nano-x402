# openai-agents-nano

Pay any x402-priced HTTP endpoint in **self-custodied Nano (XNO)** from an
OpenAI Agents SDK agent. A thin adapter on the MIT-licensed
[feeless402](https://feeless402.com) client — it rebuilds **no** Nano payment
logic; it just exposes feeless402's `request_with_payment`, `Wallet` and `RPC`
as an OpenAI Agents SDK `Tool`.

Built by an AI agent. Scope approved by `rai-scope`; see `scope-manifest.json`.

## Why

Every major agent framework's x402 payer settles **USDC (EVM/Base) only**: the
OpenAI Agents SDK ships AsterPay (USDC), Cloudflare Agents SDK pays EVM USDC,
paygraph and x402-agent cover LangGraph/CrewAI with USDC. **None speaks the
Nano x402 dialect.** This tool gives OpenAI agents the first fee-free, instant,
self-custody XNO rail — verified on the ledger, no gas, no freezeable
stablecoin.

## Spend XNO from your agent today

This is not a demo-only adapter — it has already paid a real third-party x402
seller. On 2026-09-18 this exact two-phase flow bought a live chat completion
from **NanoGPT** (`api.nano-gpt.com`, an independent LLM host) in **0.00001292
XNO** (block `E67FB89426F46E6AE4E0E5750B5F814A699965B8639DA89F38689EA1AFE57FC3`,
confirmed on the Nano network) — the first known payment from an OpenAI Agents
SDK agent to a third-party x402 seller settled in XNO.

The fastest way to *be* that buyer: [the pay-NanoGPT tutorial](docs/pay-x402-from-openai-agent.md)
— install, fund a wallet with a few hundred-thousandths of an XNO, and run one
agent that buys a completion. A fresh Nano seed with ~0.00005 XNO is enough for
dozens of calls.

```bash
pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl
# then follow docs/pay-x402-from-openai-agent.md step by step
```

If you operate a 402 endpoint (or want to), [add a Nano accept and join the
buyer side](docs/xno-x402-quickstart.md#6-if-you-run-a-402-resource) — the
CDP Bazaar already indexes `nano:mainnet`/XNO accepts, and your Nano option
gets real buyers that USDC-only rails cannot reach.

## Install

The v0.1.0 GitHub release is the immutable, public install path (works today). Two equivalent ways,
all verified from a clean venv with no credentials:

```bash
# single-file wheel from the release (no git, no build, cacheable):
pip install https://github.com/dhyabi2/openai-agents-nano-x402/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl

# or straight from the tagged source:
pip install "git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0"
```

The release also carries the sdist (`.../releases/download/v0.1.0/openai_agents_nano-0.1.0.tar.gz`).

A PyPI release is prepared but not uploaded yet — a PyPI project can only be created by a human with a
PyPI login. `.github/workflows/publish.yml` performs the upload with no stored secret once a *pending
trusted publisher* is registered for this project; the OIDC handshake itself is proven working, and the
workflow's only remaining failure is PyPI's `invalid-publisher` ("no corresponding publisher"), i.e. that
registration is the one missing step. Until then `pip install openai-agents-nano` fails with "No matching
distribution found" — this project is not on PyPI, and the name is not registered.

## Usage

```python
from agents import Agent, Runner
from openai_agents_nano import make_nano_x402_tool

# The wallet is bound here, never exposed to the model.
# Default: $X402_WALLET_PATH or ~/.nano-pay/wallet.json
# Default cap: $X402_MAX_XNO or 0.01 XNO
tool = make_nano_x402_tool()

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

result = Runner.run_sync(agent, "Fetch https://api.example.com/report")
```

### Tool behaviour

- One tool, `nano_x402_fetch(url, method="GET", json_body="", max_xno=None,
  dry_run=False, quote_token=None)`.
- **Two-phase**, so an agent only ever pays an offer it has actually seen:
  - **`dry_run=true` is spendless**: reads the server's 402 quote and returns
    the price, pay_to and cap as agent-readable text, plus a **single-use
    `quote_token`** binding that exact offer. Never signs or broadcasts.
  - **`dry_run=false` (redeem)**: re-reads the quote and refuses with a plain
    refusal string (not an exception) unless a valid, unspent `quote_token`
    matching the current offer is passed back. A missing, expired, reused or
    offer-changed token is refused before anything is signed. A valid token is
    consumed (single-use), then feeless402 signs locally, retries with the
    payment header, and verifies on the ledger before the tool returns a
    receipt (status, body, amount_xno, pay_to, block, settled, ledger, note).
- Payments are serialised behind an `asyncio.Lock`: Nano blocks are stateful
  and non-replayable, so one wallet never sends concurrently.
- Both a brand-new and an **existing funded wallet** work: the tool creates a
  fresh wallet file on first use and *loads* one that already exists, so an
  imported or topped-up `~/.nano-pay/wallet.json` signs with its held balance
  instead of crashing (block 4).
- **Proven live on mainnet** (`docs/live-proof.md`): a real capped redeem
  through a locally-run rail-reusing server settled a confirmed XNO block
  (0.0001 XNO, verified on two public nodes). This is a correctness proof
  using my own accounts — it is not adoption evidence.

## Docs and measured comparisons

- `docs/tutorial.md` — install + two-phase spendless usage + safety + verify commands.
- `docs/fee-finality-comparison.md` — measured Nano vs USDC-on-Base x402 (cost, finality, custody).
- `docs/agent-payment-rails-comparison.md` — the full agent-payment rail set: Nano x402 vs
  x402/USDC, Stripe+Tempo MPP, Google AP2, card-network agent rails.
- `docs/comparison-vs-x402-openai-python.md` — this repo vs the incumbent OpenAI x402 client
  (`qntx/x402-openai-python`): what each is, where it fits, and the honest differences
  (custody rail, fee model, framework fit).
- `docs/live-proof.md` — the real paid mainnet redeem (correctness proof, own accounts; not adoption evidence).
- `docs/x402-discovery-study.md` — measured study of x402 seller discovery (the CDP Bazaar): the Bazaar
  index already carries 53 `nano:mainnet`/XNO accepts across 15,757 resources (all from one seller), so an
  XNO-priced resource
  is discoverable today, and the discovery validator cannot reach at least one live Nano host.
- `docs/xno-x402-quickstart.md` — runnable quickstart against the **live** XNO-priced x402 endpoints
  (read the index, read a real 402 with a Nano option, install, prove the spend gate offline). Every
  command in it was executed before it was committed; the "not proven" section says what is missing.
- `docs/upstream-x402-nano-registration.md` — the prepared contribution to `x402-foundation/x402`: a live
  Nano-only route passes an independent x402 conformance checker (score 94.4, "network matches CAIP-2 shape —
  nano") while the same route is rejected by the CDP facilitator's four rail-value checks, and the exact
  three registration edits x402's own docs require for a new network.

## Safety

- The wallet path and RPC are construction-bound; the model sees neither.
- **Single-use quote tokens** stop an agent from paying a quote it never
  previewed, and stop an endpoint from changing pay_to/price between the
  preview and the redeem (an irreversible Nano block is only ever authorised
  against the offer the agent was shown).
- Per-call cap enforced in deterministic code before any signing.
- **Honest results:** only a ledger-confirmed settlement is reported as PAID.
  A block the ledger does not hold, or an indeterminate verdict, is reported
  as NOT PAID / UNCONFIRMED with its block hash; and if a merchant never
  replies after the block is signed, the tool surfaces the signed block and
  verdict with a "re-present the SAME block, do not re-pay blind" action —
  never a generic failure that invites a double payment.
- Self-custodied: your seed stays on disk; nothing here holds your funds.

## Tests

```bash
python -m pytest -q                          # structural
python tests/fail_closed_offline.py          # L1: dry_run spends nothing, over-cap refused
python tests/two_phase_offline.py            # L2/L3: single-use token gate + offer-change refusal
python tests/receipt_honesty_offline.py      # L11: never headed PAID unless the ledger confirmed settlement
python tests/payment_failure_honesty_offline.py  # L12: a never-replied redeem surfaces the signed block + verdict, so an agent never re-pays blind
python tests/wallet_load_offline.py              # L13: an existing funded wallet is loaded (not re-created) before signing
python tests/release_install_offline.py          # L21/L22: a built wheel installs in a fresh venv and the installed tool constructs + executes
```

## Building and verifying the distribution

```bash
uv build                                # builds dist/openai_agents_nano-0.1.0.tar.gz + .whl
python tests/release_install_offline.py # builds the wheel, installs it into a brand-new venv,
                                        # and asserts the installed tool is a real nano_x402_fetch
                                        # FunctionTool that dry-runs (QUOTE, nothing spent) and
                                        # refuses an over-cap redeem before signing
```

## License

MIT. Reuses [feeless402](https://github.com/feeless402/feeless402) (MIT) and the
x402nano exact dialect / 402nano facilitator.