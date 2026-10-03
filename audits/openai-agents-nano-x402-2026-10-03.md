# openai-agents-nano-x402 — code audit, 2026-10-03

Clone of `main` at `86e86bc`, clean venv. Baseline before any change:

```
$ pip install -e ".[dev]"      # succeeds
$ python3 -m pytest tests/ -q  # 85 passed
$ ruff check .                 # All checks passed!
```

Lens: can an agent pay an x402 endpoint in XNO with this today, without being hurt. This run read the
tool's amount path end to end — every value that becomes a number of raw — rather than the release
asset (run 2026-09-30) or the mandate ledger (open PR #12).

## Found and fixed

**A cap finer than one raw left the tool as an exception, and the SDK told the model to retry.**
`tool.py:358` converted the applied cap to raw *outside* the `try` that guards the line above it:

```python
try:
    cap_xno = str(_apply_cap(max_xno, default_cap))
except ValueError as e:
    return f"REFUSED: {e}"
cap_raw = xno_to_raw(cap_xno)        # <- outside the guard
```

`xno_to_raw` refuses an amount smaller than one raw (1 raw = 10**-30 XNO) by raising `AmountError`.
`max_xno` is **model-supplied**, and the tool's own description tells the model to "keep max_xno
small". Driven through `on_invoke_tool` exactly as the Agents SDK drives it:

| `max_xno` | before | after |
|---|---|---|
| `"nan"` | `REFUSED: max_xno is not a finite number: 'nan'` | unchanged |
| `"-5"` | `REFUSED: max_xno must be >= 0: '-5'` | unchanged |
| `"1e-40"` | `An error occurred while running the tool. Please try again.` | `REFUSED: '1E-40' XNO is smaller than one raw (10**-30 XNO) and cannot be represented exactly` |
| `"0.0000000000000000000000000000005"` | `An error occurred while running the tool. Please try again.` | same refusal, naming the value |

The old text is the Agents SDK's generic wrapper for an escaped exception. It is wrong twice: it
gives the model no reason, and it instructs it to **try again** — a retry that cannot ever succeed,
because the cap is a constant of the call. The same line is reached from the operator's side, so a
misconfigured `X402_MAX_XNO`/`default_max_xno` of half a raw made *every* call read as a transient
tool error. This is the same class as `#9` ("a typo in the operator's cap became an unreadable retry
loop"), one validation step further down.

**Fix:** move the conversion inside the existing guard. `AmountError` subclasses `ValueError`, so the
existing `except ValueError` catches it and refuses in text. The cap value, the comparison against
the price, and the payment path are untouched — nothing that signs or sends changed; the change can
only turn a crash into a refusal.

**Test:** `tests/test_tool.py::test_sub_raw_cap_is_refused_as_text_not_an_sdk_error` and
`::test_sub_raw_default_cap_is_refused_as_text`. Both fail on `main` with the SDK wrapper text and
pass with the fix. After: `87 passed`, `ruff check .` clean.

## Checked, nothing to fix

- `mandate.py` amount handling (lines 293–332). Money is an integer count of raw end to end;
  `parse_raw` refuses `bool`, `float` and non-canonical strings; the mandate JSON loader installs
  `parse_float=_refuse_float`, so a float cannot enter through a mandate file either. No float
  touches an amount anywhere in `src/`.
- `QuoteTokenStore` binding (`pay_to` + `amount_raw` + TTL, single-use) — correct as written.
- The redeem ordering (mandate check before token consumption) is correct on `main`.

## Could not verify / left to a person

- **Open PR #10** (cap refusal consumes the quote token) and **#12** (mandate ledger `OSError` is not
  a refusal) are still open from earlier runs. Both touch the same `_nano_x402_fetch` body as this
  change but in different places, and neither conflicts with it textually. They remain the owner's
  call.
- **The v0.1.0 release asset is still the only published install path and still predates
  `mandate.py`** (2026-09-30 finding). A person must cut a new tag; no routine can.
