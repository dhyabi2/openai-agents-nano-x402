"""Release-readiness proof for L21/L22 (block 5).

Proves a FRESH `pip install` of the built openai-agents-nano wheel yields a
real, SDK-invokable tool:

  L21  -- the wheel installs into a brand-new venv; `openai_agents_nano`
         imports and `make_nano_x402_tool()` returns an OpenAI Agents SDK
         FunctionTool named `nano_x402_fetch` with the full argument schema.
  L22  -- that installed tool EXECUTES through the SDK invoker
         (`FunctionTool.on_invoke_tool(ctx, args)`): a dry_run preview returns
         a QUOTE (nothing spent, no frontier created) and an over-cap redeem
         is refused before signing (still no frontier).

This is offline: only a local HTTP 402 server runs, no real Nano network, no
real spend. Running this makes a one-shot decision: how to run the assertions.

Run (phase 1, from the repo):  python tests/release_install_offline.py
  -> builds the wheel, creates a fresh venv, installs it, then re-executes
     itself inside that venv with --in-venv to run the checks.
Prints RELEASE_INSTALL_OK and exits 0 on success.
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def find_uv() -> str:
    """Locate uv: $UV if set, else whatever is on PATH.

    The default used to be the hard-coded `/root/.hermes/bin/uv`, a path that exists on one agent box
    and nowhere else. That made this file -- the repository's proof that the PUBLISHED wheel installs
    and runs -- unrunnable by anyone who installs the package, and unrunnable in CI too, where the
    workflows get uv from `pip install uv` and so find it on PATH. It died with a bare
    FileNotFoundError from the first subprocess, before a single check ran.
    """
    explicit = os.environ.get("UV")
    if explicit:
        return explicit
    found = shutil.which("uv")
    if found:
        return found
    # Say what is missing and how to get it, rather than raising FileNotFoundError on a path the
    # reader never chose.
    raise SystemExit(
        "uv not found on PATH. Install it (`pip install uv`) or point UV at it "
        "(`UV=/path/to/uv python tests/release_install_offline.py`)."
    )

PAY_TO = "nano_1x9k4qmqwc6f9amcq8gdgyb1gm7b3s5w1kzn9aafoza3tr4tbrmq1j4xyg4z"
LOW_RAW = "100000000000000000000000000000"  # 0.1 XNO
HIGH_RAW = "1000000000000000000000000000000"  # 1.0 XNO
CAP = "0.05"  # below the low price


def make_quote(raw_amount: str) -> bytes:
    envelope = {
        "x402Version": 1,
        "accepts": [
            {
                "scheme": "exact",
                "protocolScheme": "exact",
                "network": "nano:mainnet",
                "asset": "XNO",
                "amount": raw_amount,
                "payTo": PAY_TO,
            }
        ],
    }
    return base64.b64encode(json.dumps(envelope).encode())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(402)
        raw = HIGH_RAW if self.path.startswith("/high") else LOW_RAW
        self.send_header("payment-required", make_quote(raw).decode())
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        pass


async def invoke(tool, json_args: str) -> str:
    from agents.tool_context import ToolContext

    ctx = ToolContext(
        context={"nano": True},
        tool_name=tool.name,
        tool_arguments=json_args,
        tool_call_id="call_release_01",
    )
    return await tool.on_invoke_tool(ctx, json_args)


def _frontier(walletp: str):
    if not os.path.exists(walletp):
        return None
    try:
        d = json.load(open(walletp))
        for k in ("frontier", "new_frontier"):
            if d.get(k):
                return d[k]
        return d.get("block") or None
    except Exception:
        return None


def phase_two_in_venv(cap: str) -> None:
    """Assertions run inside the freshly-installed package."""
    import asyncio

    from openai_agents_nano import make_nano_x402_tool

    # L21: the installed package constructs a real, fully-typed tool.
    tool = make_nano_x402_tool(wallet_path=_wallet(), default_max_xno=cap)
    assert type(tool).__name__ == "FunctionTool", type(tool)
    assert tool.name == "nano_x402_fetch", tool.name
    want = {"url", "method", "json_body", "max_xno", "dry_run", "quote_token"}
    assert set(tool.params_json_schema["properties"]) == want, set(
        tool.params_json_schema["properties"]
    )

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    # L22a: dry_run spends nothing -> QUOTE, no frontier created.
    out = asyncio.run(
        invoke(tool, json.dumps({"url": f"{base}/low", "dry_run": True}))
    )
    assert out.startswith("QUOTE"), out
    assert "0.1 XNO" in out, out
    assert _frontier(_wallet()) is None, "dry_run must not sign/broadcast"
    print("  dry_run preview ->", out.splitlines()[0], "| 0.1 XNO | no frontier")

    # L22b: over-cap redeem (valid token) -> REFUSED before signing, no spend.
    import re as _re

    prev = asyncio.run(invoke(tool, json.dumps({"url": f"{base}/high", "dry_run": True})))
    assert prev.startswith("QUOTE"), prev
    m = _re.search(r"quote_token: (\S+)", prev)
    assert m, f"no quote_token: {prev!r}"
    token = m.group(1)
    out2 = asyncio.run(
        invoke(tool, json.dumps({"url": f"{base}/high", "dry_run": False, "quote_token": token}))
    )
    assert out2.startswith("REFUSED"), out2
    assert "1 XNO" in out2 and f"{cap} XNO" in out2, out2
    assert _frontier(_wallet()) is None, "cap refusal must not spend"
    print("  over-cap redeem ->", out2.splitlines()[0], "| 1 XNO >", cap, "XNO | no frontier")

    print("RELEASE_INSTALL_OK")
    print("name:", tool.name)
    print("args:", sorted(tool.params_json_schema["properties"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-venv", action="store_true")
    parser.add_argument("--wallet", default=None)
    args = parser.parse_args()

    if not args.in_venv:
        # Phase 1: build the wheel, fresh venv, install, re-exec inside it.
        uv = find_uv()  # resolved here, not at import: --in-venv phase 2 needs no uv at all
        with tempfile.TemporaryDirectory() as td:
            build_dir = Path(td) / "dist"
            subprocess.run(
                [uv, "build", "--out-dir", str(build_dir), str(REPO)],
                check=True, capture_output=True,
            )
            wheel = next(build_dir.glob("openai_agents_nano-*.whl"))
            venv = Path(td) / "venv"
            subprocess.run([uv, "venv", str(venv)], check=True, capture_output=True)
            subprocess.run(
                [uv, "pip", "install", "--python", str(venv / "bin" / "python"), str(wheel)],
                check=True, capture_output=True,
            )
            wallet = str(Path(td) / "wallet.json")
            env = dict(os.environ, X402_WALLET_PATH=wallet)
            r = subprocess.run(
                [str(venv / "bin" / "python"), __file__, "--in-venv", "--wallet", wallet],
                capture_output=True, text=True, env=env,
            )
            print(r.stdout, end="")
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                sys.exit(r.returncode)
        return

    # Phase 2: assertions inside the installed package.
    global _wallet
    _wallet = lambda: args.wallet  # noqa: E731
    phase_two_in_venv(CAP)


_wallet = lambda: "/tmp/__unset__"  # noqa: E731  (replaced in phase 2)

if __name__ == "__main__":
    main()