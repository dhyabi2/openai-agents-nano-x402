"""Structural tests for L0: the tool factory returns an OpenAI Agents SDK
FunctionTool named nano_x402_fetch that reuses feeless402's client.

Offline and deterministic: no real Nano network, no wallet spend.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agents.tool_context import ToolContext

from openai_agents_nano.tool import make_nano_x402_tool


async def invoke(tool, json_args: str) -> str:
    ctx = ToolContext(
    context={"nano": True},
    tool_name=tool.name,
    tool_arguments=json_args,
    tool_call_id="call_test_01",
)
    return await tool.on_invoke_tool(ctx, json_args)


def _make(wallet_path, default_max_xno="0.01"):
    return make_nano_x402_tool(wallet_path=wallet_path, default_max_xno=default_max_xno)


def test_returns_named_functiontool():
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"))
        assert tool.name == "nano_x402_fetch"
        assert hasattr(tool, "on_invoke_tool")


def test_factory_binds_wallet_not_exposing_it_to_model():
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "wallet.json"))
        # Wallet path and RPC are construction-bound, never tool args.
        schema = json.dumps(tool.params_json_schema)
        assert "wallet" not in schema.lower()
        assert "rpc" not in schema.lower()


def test_dry_run_returns_text_not_exception():
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"))
        out = asyncio.run(
            invoke(tool, json.dumps({"url": "https://example.invalid/x", "dry_run": True}))
        )
        assert isinstance(out, str)
        assert out.startswith("ERROR") or out.startswith("NOTE") or "QUOTE" in out


def test_cap_validation_returns_refusal_string():
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"), default_max_xno="0.02")
        out = asyncio.run(
            invoke(tool, json.dumps({"url": "https://example.invalid/x", "max_xno": "-5", "dry_run": True}))
        )
        assert out.startswith("REFUSED")


def test_non_finite_cap_is_refused_as_text_not_raised():
    # max_xno is model-supplied, and a model asking for "no limit" may well say
    # "nan" or "Infinity". Decimal() accepts both; comparing a Decimal NaN raises
    # InvalidOperation, which is an ArithmeticError and so escapes the caller's
    # `except ValueError` -- breaking the module's contract that the tool always
    # returns agent-readable text.
    from openai_agents_nano.tool import _apply_cap

    for bad in ("nan", "NaN", "snan", "Infinity", "-Infinity"):
        try:
            _apply_cap(bad, "0.01")
        except ValueError:
            pass  # refused the way a bad number is refused
        except Exception as exc:  # pragma: no cover - the defect this pins
            raise AssertionError(f"max_xno={bad!r} raised {type(exc).__name__}, not ValueError") from exc
        else:
            raise AssertionError(f"max_xno={bad!r} was accepted as a cap")

    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"))
        out = asyncio.run(
            invoke(tool, json.dumps({"url": "https://example.invalid/x", "max_xno": "nan", "dry_run": True}))
        )
        assert isinstance(out, str) and out.startswith("REFUSED"), out

def test_a_bad_configured_default_cap_is_refused_as_text_not_raised():
    # The law above guards the cap the MODEL supplies. The cap the OPERATOR
    # supplies -- default_max_xno, else X402_MAX_XNO -- reaches the same
    # Decimal() with no check at all, and the applied cap is min(requested,
    # default), so it is the hard limit of the two.
    #
    # A typo in that value ("0.01 XNO", an empty export, "nan") raises
    # decimal.InvalidOperation out of _apply_cap, past the caller's
    # `except ValueError`; a negative one gets past _apply_cap and then raises
    # AmountError out of xno_to_raw, which is not inside any try at all.
    # Either way the tool breaks its contract of always returning
    # agent-readable text, and the Agents SDK reports
    # "An error occurred while running the tool. Please try again.
    #  Error: [<class 'decimal.ConversionSyntax'>]" -- a retry that can only
    # fail again, for a reason naming nothing the operator can act on.
    from openai_agents_nano.tool import _apply_cap

    for bad in ("abc", "", "0.01 XNO", "nan", "Infinity", "-5"):
        for requested in (None, "0.5"):
            try:
                _apply_cap(requested, bad)
            except ValueError:
                pass  # refused the way a bad number is refused
            except Exception as exc:  # pragma: no cover - the defect this pins
                raise AssertionError(
                    f"default cap {bad!r} with max_xno={requested!r} raised "
                    f"{type(exc).__name__}, not ValueError"
                ) from exc
            else:
                raise AssertionError(
                    f"default cap {bad!r} with max_xno={requested!r} was accepted"
                )


def test_a_bad_configured_default_cap_reaches_the_agent_as_a_refusal():
    """End to end: the tool must answer REFUSED, not hand the SDK an exception."""
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"), default_max_xno="0.01 XNO")
        out = asyncio.run(
            invoke(tool, json.dumps({"url": "https://example.invalid/x",
                                     "max_xno": "0.5", "dry_run": True}))
        )
        assert out.startswith("REFUSED"), out[:200]
        assert "0.01 XNO" in out, out[:200]
