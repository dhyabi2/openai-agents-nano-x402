"""openai-agents-nano — a thin OpenAI Agents SDK Tool that lets any OpenAI
agent pay any x402-priced HTTP endpoint in self-custodied Nano (XNO).

This adapter REUSES the MIT-licensed feeless402 client (Wallet, RPC,
request_with_payment) verbatim. It rebuilds no Nano payment logic: the whole
x402 handshake (quote parse, price cap, local signing, retry with payment
header, on-ledger verification) lives in feeless402.

`mandate` (vendored from agent-wallet-multirail) adds an operator mandate: a
spend cap the human operator signs once with their own Nano key, checked
against the payee and amount actually being signed (`mandate_path=`).
"""

from .tool import make_nano_x402_tool, NanoX402ToolError
from .mandate import MandateGuard, MandateRefused

__all__ = ["make_nano_x402_tool", "NanoX402ToolError", "MandateGuard", "MandateRefused"]