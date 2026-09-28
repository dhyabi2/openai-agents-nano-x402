# openai-agents-nano-x402 — audit 2026-09-28

Tree audited at `7ffa577` (branch `main`). Environment: Python 3.11.15, a fresh `.venv`
with `pip install -e '.[dev]'`, plus `ruff` to run CI's own lint gate.

## Baseline

`pytest -q` — **79 passed**, before any change. `ruff check .` — **All checks passed**,
under the repository's own pinned rule set (`E9`, `F63`, `F7`, `F82`).

## What was checked

- `src/openai_agents_nano/tool.py` in full: the two-phase quote/redeem flow, the
  `QuoteTokenStore`, `_apply_cap`, every `_format_*` renderer, `_MandatedWallet`, and the
  ordering of guard / token-consume / cap-check / sign inside `_nano_x402_fetch`. The
  ordering is right — the mandate is checked before the token is consumed, the token is
  consumed before the cap check, and the cap check is the last thing before signing.
  **One defect found — see below.**
- The README's install path. `pip install …/releases/download/v0.1.0/openai_agents_nano-0.1.0-py3-none-any.whl`
  **resolves 200**, and the API confirms one release `v0.1.0` carrying both the wheel and
  the sdist. Every install URL in `README.md` names `dhyabi2`, not the old account.
- The stale-account sweep. `PANDeveloper001` still appears in `.github/workflows/ci.yml:51`
  (the weekly mirror index), in `scripts/*.py`, and in `funnel.md` / `x-thread-sep22.md` /
  `distribution-funnel.txt`. The repository's own `funnel.md:357` already records that
  `github.com/PANDeveloper001/openai-agents-nano-x402` 404s. None of these are in the
  README or in `src/`, so no user following the documented path hits one; the CI line is a
  release-workflow decision and deliberately untouched here.
- `ruff check .` re-run after the change: still clean.

## Found and fixed — pull request open, NOT merged

**`src/openai_agents_nano/tool.py:139` — a typo in the operator's cap turned every call
into an unreadable retry loop.**

`_apply_cap(requested, default)` checks the *requested* cap with real care. The comment
there spells out why: `max_xno` is model-supplied, `Decimal()` accepts `"nan"` and
`"Infinity"` happily, and comparing a `Decimal` NaN raises `InvalidOperation`, which is an
`ArithmeticError` and so escapes the caller's `except ValueError`.

The *default* cap — `default_max_xno`, else the `X402_MAX_XNO` environment variable — got
none of that, and it is `min(requested, default)`, so it is the **harder** of the two:

    cap = Decimal(str(default))     # no try, no is_finite, no sign check

Measured, before the fix:

    default='abc'       max_xno=None   -> ESCAPES as InvalidOperation: ConversionSyntax
    default=''          max_xno='0.5'  -> ESCAPES as InvalidOperation: ConversionSyntax
    default='nan'       max_xno='0.5'  -> ESCAPES as InvalidOperation
    default='Infinity'  max_xno=None   -> cap=Infinity, then AmountError out of xno_to_raw
    default='-5'        max_xno=None   -> cap=-5,       then AmountError out of xno_to_raw

The last two get *past* `_apply_cap` and die at `cap_raw = xno_to_raw(cap_xno)`, which is
not inside any `try` at all.

End to end, an operator who exports `X402_MAX_XNO="0.01 XNO"` gets this from every call:

    An error occurred while running the tool. Please try again.
    Error: [<class 'decimal.ConversionSyntax'>]

The module's docstring says "The return value is always agent-readable text", and
`NanoX402ToolError` is documented as being for conditions the tool *cannot* represent as
text. This one can — the code already does exactly that for the model-supplied twin. As
shipped, the agent is told to try again, the retry can only fail identically, and the
reason names nothing an operator can act on.

**The change** applies the same three checks to the default that the requested value
already gets. It can only refuse *earlier and more clearly*: every finite, non-negative
default behaves exactly as before, and no input that previously produced a working cap
changes. After it, the same misconfiguration reads:

    REFUSED: the configured default cap is not a number: '0.01 XNO'

**The laws**: `test_a_bad_configured_default_cap_is_refused_as_text_not_raised` (six bad
values × with and without a requested cap) and
`test_a_bad_configured_default_cap_reaches_the_agent_as_a_refusal` (the real tool, the
real SDK invoke path). Both fail on the tree without the fix and pass with it.

After: `pytest -q` — **81 passed**. `ruff check .` — All checks passed.

**Why it is not merged.** `_apply_cap` computes the spend cap of a package people install
and pay real XNO through. The change is provably refusal-only, but a cap is money code and
a person should look at it rather than an audit merging its own work there. This is the
same call earlier passes made for `nano-mcp-public` #3, #4, #6 and #8.

## Found, not fixed

- **`QuoteTokenStore` never forgets a token nobody redeemed.** `mint` inserts into
  `self._tokens` and only `reject` removes — on a hit, on expiry, or on a mismatch. A
  preview that is never redeemed (the common case: the agent looks at the price and walks
  away) stays in the dict for the life of the process. Measured: 1000 previews, all
  expired, then a refused redeem — **1000 tokens still held**, because the expiry sweep
  only ever touches the token being presented. Each entry is small and the TTL is 30
  minutes, so this is growth, not a leak that bites today; it is reported rather than
  changed because a fix means deciding an eviction policy, which is a design call and not
  an audit's.

## Not verified

- **No payment was made and no live endpoint was called.** Everything above is the offline
  suite plus direct calls into `_apply_cap` and `QuoteTokenStore`; `request_with_payment`
  was never driven against a real 402 server, and no block was signed.
- **CI was not observed green on the branch.** The workflow runs a 3×2 matrix on
  `pull_request`; whatever it reports is on the pull request itself.
- **The weekly mirror install step** (`pandeveloper001.github.io/.../simple/`) was not
  exercised. It runs only on the schedule and on dispatch, so it does not gate this change,
  but it points at the old account and is very likely dead.
- **The published `v0.1.0` wheel and sdist** were confirmed to exist and the wheel URL to
  resolve; neither was downloaded or installed.
