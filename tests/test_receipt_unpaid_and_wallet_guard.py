"""Two records that said more than happened. Offline: a local HTTP server on
127.0.0.1, a fresh temporary wallet that is never funded, no node, no money.

1. A paying read that is not a 402. feeless402 returns `(response, None)` when
   the read it would pay answers anything but 402, so nothing is signed or sent.
   The tool turned that into an empty receipt and `_format_receipt` printed the
   authorised `pay_to` beside `block: None` under an UNCONFIRMED head line - a
   payee named for a payment that never existed.

2. A wallet file that is valid JSON but not a wallet (`{}`, `[]`). `load()` is
   only `json.loads`, so it passed the load guard; the dry run quoted and minted
   a token, and the redeem consumed the token and then failed at signing time
   with "'seed'". It must be the same configuration ERROR as a corrupt file,
   before any request is made.
"""
import asyncio
import base64
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.tool_context import ToolContext

import openai_agents_nano.tool as T

PAY_TO = "nano_1p7cqqnfo91zwcnse54f3ucyfi6xwzsbnkt3ay14cd1g6epmiygnt7jtcoa5"
PRICE_RAW = "1000000000000000000000000000"  # 0.001 XNO, under the 0.01 cap


def _quote_header() -> str:
    envelope = {
        "x402Version": 1,
        "accepts": [{
            "scheme": "exact", "protocolScheme": "exact",
            "network": "nano:mainnet", "asset": "XNO",
            "amount": PRICE_RAW, "payTo": PAY_TO,
        }],
    }
    return base64.b64encode(json.dumps(envelope).encode()).decode()


class _Server:
    """Answers 402 for the first `quotes` requests, then 200 with a body."""

    def __init__(self, quotes):
        self.requests = 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.requests += 1
                if outer.requests <= quotes:
                    self.send_response(402)
                    self.send_header("payment-required", _quote_header())
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                body = b"free after all"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/paid"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class _OfflineRPC:
    def __getattr__(self, name):
        def _fail(*a, **k):
            raise RuntimeError("offline rpc: nothing may reach a node here")
        return _fail


def _invoke(tool, **args) -> str:
    raw = json.dumps(args)
    ctx = ToolContext(context=None, tool_name=tool.name, tool_arguments=raw,
                      tool_call_id="call_test")
    return asyncio.run(tool.on_invoke_tool(ctx, raw))


def _tool(wallet_path):
    return T.make_nano_x402_tool(wallet_path=str(wallet_path), rpc=_OfflineRPC(),
                                 default_max_xno="0.01")


@pytest.fixture
def server_402_then_200():
    # preview read, redeem's quote read -> 402; the paying read -> 200
    s = _Server(quotes=2)
    yield s
    s.close()


def test_a_paying_read_that_is_not_a_402_names_no_payee(server_402_then_200):
    s = server_402_then_200
    with tempfile.TemporaryDirectory() as td:
        tool = _tool(Path(td) / "w.json")
        preview = _invoke(tool, url=s.url, dry_run=True)
        assert PAY_TO in preview, preview
        token = preview.split("quote_token: ")[1].strip()

        answer = _invoke(tool, url=s.url, dry_run=False, quote_token=token)

        assert s.requests == 3, "preview, redeem quote, paying read"
        assert answer.startswith("NOT PAID"), answer
        assert "no payment was requested on the paying read" in answer, answer
        assert PAY_TO not in answer, "no block exists, so no payee may be named"
        assert "PAID (Nano x402)" not in answer
        assert "UNCONFIRMED" not in answer
        assert "free after all" in answer, "the resource body is still returned"


def test_format_receipt_with_a_block_still_names_the_authorised_payee():
    """Control: a real receipt keeps the authorised payee, as before."""
    class R:
        status_code, text = 200, "ok"
    out = T._format_receipt(R(), {"settled": True, "block": "AB" * 32,
                                  "amount_xno": "0.001", "ledger": "confirmed"},
                            "0.01", authorised_pay_to=PAY_TO)
    assert out.startswith("PAID (Nano x402):")
    assert f"pay_to:    {PAY_TO}" in out


@pytest.mark.parametrize("content", ["{}", "[]"])
@pytest.mark.parametrize("dry_run", [True, False])
def test_json_that_is_not_a_wallet_is_a_configuration_error(content, dry_run):
    s = _Server(quotes=99)
    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "not-a-wallet.json"
            path.write_text(content)
            answer = _invoke(_tool(path), url=s.url, dry_run=dry_run,
                             quote_token="anything")

            assert answer.startswith("ERROR: the wallet at not-a-wallet.json cannot be used"), answer
            assert "configuration problem" in answer
            assert "no payment was attempted" in answer
            assert "quote_token" not in answer and "QUOTE" not in answer
            assert s.requests == 0, "no request is made with an unusable wallet"
            assert td not in answer, "the absolute path stays out of model context"
    finally:
        s.close()


def test_a_wallet_with_a_bad_seed_is_a_configuration_error():
    s = _Server(quotes=99)
    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad-seed.json"
            path.write_text(json.dumps({"seed": "not hex", "index": 0}))
            answer = _invoke(_tool(path), url=s.url, dry_run=True)
            assert answer.startswith("ERROR: the wallet at bad-seed.json cannot be used"), answer
            assert s.requests == 0
    finally:
        s.close()


def test_the_error_names_only_the_wallet_file_not_its_absolute_path():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "as-a-dir.json"
        path.mkdir()
        answer = _invoke(_tool(path), url="http://127.0.0.1:9/never", dry_run=True)
        assert answer.startswith("ERROR: the wallet at as-a-dir.json cannot be used"), answer
        assert str(path) not in answer and td not in answer, answer
