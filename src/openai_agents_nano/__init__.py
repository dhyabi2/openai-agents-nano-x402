"""openai-agents-nano — a thin OpenAI Agents SDK Tool that lets any OpenAI
agent pay any x402-priced HTTP endpoint in self-custodied Nano (XNO).

This adapter REUSES the MIT-licensed feeless402 client (Wallet, RPC,
request_with_payment) verbatim. It rebuilds no Nano payment logic: the whole
x402 handshake (quote parse, price cap, local signing, retry with payment
header, on-ledger verification) lives in feeless402.

`mandate` (vendored from agent-wallet-multirail) adds an operator mandate: a
spend cap the human operator signs once with their own Nano key, checked
against the payee and amount actually being signed (`mandate_path=`).

`x402_sdk` is the same payer for the OFFICIAL x402 Python SDK rather than for
the Agents SDK: `ExactNanoClientScheme` is the client-side `exact` mechanism on
`nano:mainnet`, which the SDK ships for EVM and SVM only. Register it on an
`x402Client` and an agent that already speaks x402 can pay a Nano quote. It
imports no x402 code, so it adds no required dependency: `pip install
"openai-agents-nano[x402]"` for the SDK itself.
"""

from .tool import make_nano_x402_tool, NanoX402ToolError
from .mandate import MandateGuard, MandateRefused
from .x402_sdk import ExactNanoClientScheme, NanoX402Refused, nano_spend_controls

__all__ = [
    "make_nano_x402_tool",
    "NanoX402ToolError",
    "MandateGuard",
    "MandateRefused",
    "ExactNanoClientScheme",
    "NanoX402Refused",
    "nano_spend_controls",
]