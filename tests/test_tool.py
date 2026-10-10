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


def test_sub_raw_cap_is_refused_as_text_not_an_sdk_error():
    # max_xno is model-supplied and the tool's own description tells the model to
    # "keep max_xno small". A cap finer than one raw (1 raw = 10**-30 XNO) cannot
    # be converted: xno_to_raw raises AmountError. That conversion used to sit
    # outside the `except ValueError` that already refuses "nan" and "-5", so the
    # exception escaped and the Agents SDK handed the model "An error occurred
    # while running the tool. Please try again." -- a retry loop with no reason,
    # for a value no retry can fix.
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"), default_max_xno="0.01")
        for bad in ("0.0000000000000000000000000000005", "1e-40"):
            out = asyncio.run(
                invoke(tool, json.dumps({
                    "url": "https://example.invalid/x",
                    "max_xno": bad,
                    "dry_run": True,
                }))
            )
            assert out.startswith("REFUSED"), (bad, out)
            assert "raw" in out, (bad, out)


def test_sub_raw_default_cap_is_refused_as_text():
    # The same conversion, reached from the operator's side: a default cap of
    # half a raw is a misconfiguration, and must read as one rather than as an
    # unexplained tool error on every call.
    with tempfile.TemporaryDirectory() as td:
        tool = _make(str(Path(td) / "w.json"),
                     default_max_xno="0.0000000000000000000000000000005")
        out = asyncio.run(
            invoke(tool, json.dumps({"url": "https://example.invalid/x", "dry_run": True}))
        )
        assert out.startswith("REFUSED"), out


# --- an unusable wallet file is text, not an exception ------------------------
#
# `wallet.exists()` / `create()` / `load()` sat outside every guard in
# `_nano_x402_fetch` and outside its lock. `load()` is
# `json.loads(path.read_text())`, so a path that exists but is not a usable
# wallet left the tool as an exception; the Agents SDK renders that to the model
# as "An error occurred while running the tool. Please try again." - an unbounded
# retry that cannot ever succeed, with no reason given, and the agent cannot even
# preview a price. The module's own contract (tool.py docstring) is that "the
# return value is always agent-readable text".


def _unusable_wallet_answer(path, dry_run=True):
    tool = _make(str(path))
    args = json.dumps({"url": "https://example.test/paid", "dry_run": dry_run})
    return asyncio.run(invoke(tool, args))


def test_a_wallet_path_that_is_a_directory_answers_in_text():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "as-a-dir.json"
        path.mkdir()

        answer = _unusable_wallet_answer(path)

        assert answer.startswith("ERROR: the wallet at "), answer
        assert "Nothing was spent" in answer
        assert "not something to retry" in answer
        assert str(path) in answer, "the answer names the path the operator has to fix"


def test_a_wallet_file_that_is_not_json_answers_in_text():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "corrupt.json"
        path.write_text("{this is not json")

        answer = _unusable_wallet_answer(path)

        assert answer.startswith("ERROR: the wallet at "), answer
        assert "Nothing was spent" in answer


def test_an_unusable_wallet_refuses_a_redeem_the_same_way():
    """dry_run=false too: the refusal is before any quote, so nothing signs."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "corrupt.json"
        path.write_text("")

        answer = _unusable_wallet_answer(path, dry_run=False)

        assert answer.startswith("ERROR: the wallet at "), answer
        assert "no payment was attempted" in answer


def test_the_generic_sdk_retry_text_is_never_the_answer():
    """What the model saw before: no reason, and an instruction to try again."""
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "as-a-dir.json"
        path.mkdir()

        answer = _unusable_wallet_answer(path)

        assert "An error occurred while running the tool" not in answer
        assert "Please try again" not in answer


def test_a_usable_wallet_path_is_still_created_and_used():
    """The control: a path that does not exist yet is still created, and a
    pre-existing wallet is still loaded - the guard changes neither."""
    with tempfile.TemporaryDirectory() as td:
        fresh = Path(td) / "fresh.json"
        answer = _unusable_wallet_answer(fresh)
        assert not answer.startswith("ERROR: the wallet at "), answer
        assert fresh.exists(), "a missing wallet is still created"

        again = _unusable_wallet_answer(fresh)
        assert not again.startswith("ERROR: the wallet at "), again
