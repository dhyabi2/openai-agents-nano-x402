# Quickstart: pay the live XNO-priced x402 endpoints that exist today

Most x402 writing assumes USDC on Base. This is a short, verifiable path for the **Nano (XNO)** corner of the
same protocol — using only public endpoints and commands you can re-run. Every command below was executed
before this page was committed.

## 1. Confirm the Nano corner is real (no keys, no wallet)

The CDP x402 Bazaar is publicly readable:

```bash
curl -s "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?limit=1000&offset=0" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['pagination'])"
```

That index held **15,774 resources** when this page was written (the number moves hourly). Filter for the
Nano accepts:

```bash
python3 - <<'PY'
import json, urllib.request
off, nano = 0, []
while off < 16000:
    with urllib.request.urlopen(
        f"https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?limit=1000&offset={off}", timeout=60) as r:
        d = json.load(r)
    if not d.get("items"):
        break
    for x in d["items"]:
        for a in x.get("accepts", []) or []:
            if str(a.get("network", "")).startswith("nano") or a.get("asset") == "XNO":
                nano.append((x["resource"], a["scheme"], a["amount"], a.get("payTo")))
    off += 1000
print(len(nano), "nano accepts")
print(*nano[:3], sep="\n")
PY
```

Expected shape: a count (55 at the time of writing, all from one host) and tuples of
`(resource, "exact", amount_in_raw, nano_... address)`.

## 2. Read the 402 terms yourself

Any Nano-priced resource answers `402` with machine-readable terms — no signup, no API key:

```bash
curl -si "https://pyfile-agent.taile3ff35.ts.net/data/ip" | head -20
```

You get `HTTP/2 402` plus a `payment-required` header holding base64 JSON whose `accepts[]` lists USDC on
several chains **and** one Nano option: `scheme "exact"`, `network "nano:mainnet"`, `asset "XNO"`, an amount in
raw units, and the `payTo` account. Search the body for `nano:mainnet`:

```bash
curl -s "https://pyfile-agent.taile3ff35.ts.net/data/ip" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for a in d.get('accepts',[]): print(a['network'], a['asset'], a['amount'])"
```

## 3. Verify the client side installs and gates spend (no wallet, no funds)

```bash
uv venv /tmp/xno-qs && uv pip install --python /tmp/xno-qs/bin/python \
  "git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0"
```

(`python3 -m venv` + `pip install` is equivalent where `ensurepip` is available; on a minimal Debian/Ubuntu
box you need `python3-venv` installed first, or just use `uv` as above.)

The repo's own fail-closed check runs entirely offline against a local mock x402 server and proves the spend
gate before any money moves:

```bash
git clone -q https://github.com/dhyabi2/openai-agents-nano-x402 /tmp/xno-src
cd /tmp/xno-src && /tmp/xno-qs/bin/python tests/fail_closed_offline.py
```

Expected last line: `FAIL_CLOSED_OK`. What it asserts: a `dry_run` call spends nothing and returns a `QUOTE`;
a redeem without the matching single-use `quote_token` is `REFUSED`; and an over-cap price is `REFUSED`
**before** anything is signed (the wallet frontier is still empty).

## 4. Use it from an OpenAI Agents SDK agent

```python
from agents import Agent, Runner
from openai_agents_nano import make_nano_x402_tool

tool = make_nano_x402_tool()   # binds the wallet file + RPC; the model never sees them

agent = Agent(
    name="Paying agent",
    instructions=(
        "You can buy from paid x402 APIs. Always call nano_x402_fetch with dry_run=true "
        "first to see the price and get its quote_token; only call with dry_run=false, "
        "passing that quote_token back, if the price is within an acceptable cap."
    ),
    tools=[tool],
)
result = Runner.run_sync(agent, "Fetch https://api.example.com/report and summarize it.")
print(result.final_output)
```

The tool is **two-phase**: `dry_run=true` mints a single-use, offer-bound `quote_token`; `dry_run=false`
refuses a missing, stale, replayed or re-offered token; the applied cap is `min(max_xno, 0.01 XNO)`; and the
verdict is `PAID` only on a ledger-confirmed block, carrying the settled block hash.

`Runner.run_sync` needs a model (e.g. `OPENAI_API_KEY`) because an LLM decides when to call the tool — that is
the only thing step 4 adds over step 3.

## 5. What is proven, and what is not

- **Proven:** the Bazaar indexes XNO accepts and those endpoints answer 402; the adapter installs from git into
  a fresh venv; the spend gate fails closed offline (step 3); a real capped redeem on mainnet is documented in
  [`live-proof.md`](live-proof.md) — own accounts, so a correctness proof, not adoption evidence.
- **Also proven:** a settled paid call against a **third-party** seller. On 2026-09-18 this exact two-phase flow
  bought a chat completion from NanoGPT (`api.nano-gpt.com`, an independent LLM host) in **0.00001292 XNO**,
  block `E67FB89426F46E6AE4E0E5750B5F814A699965B8639DA89F38689EA1AFE57FC3`, confirmed on the Nano network and
  independently verified by a third party (see [`pay-x402-from-openai-agent.md`](pay-x402-from-openai-agent.md)
  and the repo issue thread). The Nano corner of x402 is real and pay-from-a-clean-outside-buyer has happened.
- **Not proven:** general adoption at scale — the one settled third-party payment is the first of its kind, not
  a usage rate. Claim it as a verified first, never as a volume.

## 6. If you run a 402 resource

A route that answers 402 with Nano in `accepts[]` is indexable in the CDP Bazaar today — the network string is
already accepted there. Check any endpoint (yours or someone else's) with the keyless preflight:

```bash
curl -s -X POST https://api.cdp.coinbase.com/platform/v2/x402/validate \
  -H "Content-Type: application/json" \
  -d '{"resource":"https://your-endpoint.example/report","method":"GET"}'
```

Caveat: the preflight's reachability check runs from Coinbase's egress and could not reach the one live XNO
host we tested, while that host answered 402 from other networks. Do not read `endpoint_reachable: false` as
proof that your endpoint is down.

Measured details and sources: [`x402-discovery-study.md`](x402-discovery-study.md).
