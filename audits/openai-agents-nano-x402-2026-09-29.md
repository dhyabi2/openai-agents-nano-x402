# openai-agents-nano-x402 — audit 2026-09-29

Tree audited at `f6bd7d1` (branch `main`). Environment: Python 3.11, a fresh `.venv` with
`pip install -e '.[dev]'`, plus `ruff` to run CI's own lint gate.

## Baseline

`pytest -q` — **81 passed**, before any change. `ruff check .` — **All checks passed**, under the
repository's own pinned rule set (`E9`, `F63`, `F7`, `F82`).

## What was checked

- `src/openai_agents_nano/tool.py` in full, with the emphasis on the **order of the refusals** in
  `_nano_x402_fetch`, since every one of them decides whether an agent can still pay. The 09-28 run
  read the same ordering and recorded it as right; re-reading it against the file's own stated rule
  found one place where the rule is not applied. See below.
- `_apply_cap` after the 09-28 fix: the operator default and the model-supplied `max_xno` are now
  checked identically (`Decimal`, `is_finite`, sign), and both refusals reach the agent as text.
  Re-probed with `"nan"`, `"Infinity"`, `"snan"`, `""`, `"0.01 XNO"` and negatives — every one is a
  `REFUSED:` string, none an `ArithmeticError`.
- `QuoteTokenStore` in full: mint, TTL expiry, single use, and the `pay_to` + `amount_raw` binding
  that makes a re-offered price a refusal rather than a silent overpay. The store itself is correct;
  the defect below is in *when* it is asked.
- The README's install path. `pip install …/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl`
  still **resolves 200**, and the release still carries both the wheel and the sdist.
- **No secrets.** No tracked `.env`, `.pem` or `.key`; the 64-hex constants in `tests/` are marked
  `# test-fixture` operator seeds that derive the test mandate's own signing key and nothing else.

## Found and fixed — pull request open, NOT merged

**`tool.py` — a cap refusal consumed the agent's single-use quote token, so the tool's own
instruction could not be followed.**

In the redeem path the token was consumed before the cap was checked:

```python
reason = tokens.reject(...)          # consumes the token on success
if reason is not None: return _format_refusal(reason)

price_raw = int(quote.get("amount_raw") or 0)
if price_raw > cap_raw:
    return _format_cap_refusal(...)  # ... the token is already gone
```

A cap refusal signs nothing, broadcasts nothing and spends nothing — exactly like the mandate
refusal five lines above, which the file deliberately places *before* the consume with the comment
"Checked before the token is consumed, so a refusal costs no preview". The same property, the
opposite placement.

What it costs is not theoretical, because the refusal text ends with advice. Measured, offline,
against the repository's own fake seller (price 0.001 XNO):

```
1. dry_run=true                       -> QUOTE, quote_token minted
2. dry_run=false, max_xno=0.0001      -> REFUSED: the endpoint's price is above your cap.
                                         Nothing was paid. Raise max_xno (or the tool's
                                         default cap) if you intend to pay this endpoint.
                                         blocks signed: 0
3. the same token, max_xno=0.01       -> REFUSED: the quote token is invalid or already used.
                                         blocks signed: 0
```

Step 3 is the tool's own instruction from step 2, carried out exactly, and refused. An agent that
follows it is told to re-preview, which costs another round trip and — on a seller that re-quotes —
a different offer. Nothing is unsafe here; it is a tool that cannot be used the way it tells you to
use it.

**Fixed** by moving the cap check above `tokens.reject`, so the token is consumed only on the path
that reaches a signature. Single use is unchanged, and the law below pins that too: after a
successful redeem, the same token is still refused.

Proved both directions. Against the unfixed `tool.py`:

```
FAILED tests/test_tool_mandate.py::test_a_cap_refusal_does_not_burn_the_quote_token
E   AssertionError: the cap refusal consumed the single-use token, so the tool's own
E   instruction to raise max_xno and retry cannot be followed
```

With the fix: **82 passed** (81 before), and `ruff check .` still clean.

**Not merged.** `tool.py` is the payment path — it is what decides whether a block gets signed — and
the standing instruction for these runs excludes money code from self-merging. The 09-28 run left
its `tool.py` fix open for the same reason. Two notes for whoever reviews it: the change moves a
refusal earlier and adds none, so the set of requests that reach a signature can only shrink; and
the third assertion in the new law exists to prove the single-use property did not weaken.

## Carried over — for a person

- **`PANDeveloper001` still appears in `.github/workflows/ci.yml:51`** (the weekly mirror index) and
  in `scripts/*.py`, `funnel.md`, `x-thread-sep22.md` and `distribution-funnel.txt`. The repository's
  own `funnel.md:357` records that `github.com/PANDeveloper001/openai-agents-nano-x402` 404s. None of
  these are in the README or in `src/`, so no user following the documented path hits one. The CI
  line is a release-workflow decision and is deliberately untouched by these runs.

## Not verified

- Anything requiring a live Nano node, a funded wallet or a real x402 seller. The whole suite is
  offline by design and `request_with_payment` is faked; a real end-to-end payment is not something
  an audit should be doing.
- The CI workflow itself was not run. `tests/test_ci_workflow.py` asserts its shape and passes, and
  this change touches no workflow file.
