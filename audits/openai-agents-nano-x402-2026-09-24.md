# openai-agents-nano-x402 — code audit, 2026-09-24

Scope: the published tree at `defb0b1` (`main`). Read `src/openai_agents_nano/`
in full, `tests/`, `pyproject.toml`, `README.md`, `llms.txt` and the two GitHub
workflows.

## How it was checked

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest tests/ -q        # 9 passed   <- baseline
```

The package is **not** on PyPI (`pypi.org/pypi/openai-agents-nano/json` → 404),
so nothing there is affected. Its two declared dependencies, `feeless402` and
`openai-agents`, both resolve.

The nine `tests/*_offline.py` files are not collected by pytest. That is not a
gap: they carry no `test_*` functions and each has a `__main__` guard — they are
standalone checks, run deliberately, not pytest modules. Checked rather than
assumed.

## Found and fixed

**The README's install command could not work, and the README said it had been
verified.** Under "all verified from a clean venv with no credentials", one of
the two documented commands pointed at `github.com/PANDeveloper001/...`, which
does not serve anonymous reads:

```
$ pip install "git+https://github.com/PANDeveloper001/openai-agents-nano-x402.git@v0.1.0"
  fatal: could not read Username for 'https://github.com': terminal prompts disabled
  error: subprocess-exited-with-error
```

The same stale account was in `pyproject.toml`'s `Homepage` and `Source` (the
links PyPI would render on the project page) and in fourteen `llms.txt` links —
the file whose entire job is to hand an agent working URLs. The wheel URL a few
lines above it had already been migrated to `dhyabi2`, so the repository was
half-moved.

Rewritten to `dhyabi2`, and **every** rewritten URL was fetched: all 200. The
corrected install command was run end to end in a clean venv:

```
$ pip install "git+https://github.com/dhyabi2/openai-agents-nano-x402.git@v0.1.0"
$ python -c "from openai_agents_nano import make_nano_x402_tool, NanoX402ToolError; ..."
smoke test OK: make_nano_x402_tool NanoX402ToolError
```

Only the user-facing files were rewritten (`README.md`, `pyproject.toml`,
`llms.txt`). The remaining ~60 references live in `scripts/`, `.ledger/` and the
funnel notes, which are this project's own operational history, not something a
user follows.

## Found, proved, and left open for the owner

**`_apply_cap` raises out of the tool for a non-finite `max_xno`** — PR "tool:
refuse a non-finite max_xno instead of raising out of the tool". `Decimal("nan")`
is valid input, so the "is not a number" guard never fires, `req < 0` is False
for a NaN, and `min()` then raises `decimal.InvalidOperation` — an
`ArithmeticError`, which sails past the caller's `except ValueError` and out of
the tool call. `max_xno` is a model-supplied argument, and the module's own
docstring promises the return value is "always agent-readable text".

Not self-merged: it is the spending-cap path of a wallet tool, even though the
change can only refuse more.

## Urgent, and not fixable from here

**CI has never run this repository's test suite.** The repo has two workflow runs
and both are `failure`. On every matrix leg the step that fails is *"Install from
GitHub Pages PEP 503 index"* — `https://pandeveloper001.github.io/openai-agents-nano-x402/simple/` —
and because it fails, the two steps after it, including *"Run project test suite
(editable install)"*, are **skipped**:

```
failure    test (3.11, pip)
        5 Install from GitHub Pages PEP 503 index -> failure
        6 Import and smoke-test the installed package -> skipped
        7 Run project test suite (editable install) -> skipped
```

So the repository's correctness signal is gated behind a *distribution* check
against an account that no longer serves it. The suite passes locally (9, now 10)
and CI has never once said so.

The fix is to decouple them — run the project's own tests first, independently of
the external-index smoke test — but that is **not** done here: this sandbox's
egress proxy denies `*.github.io`, so it could not be established whether the
index is gone or merely unreachable, and a workflow change cannot be verified
from here at all. Owner's call, with the diagnosis above.

## Checked and clean

- No secrets in the tree. The `ghp_` matches in `funnel.md`, `docs/funnel.md` and
  `scripts/gh_cred.py` are the bare four-character prefix used as a description
  or a prefix test, never a token value. Confirmed with a length-bounded pattern
  (`ghp_[A-Za-z0-9]{30,}` and friends): zero matches across the tree.
- The two-phase quote-token design holds up. `QuoteTokenStore.reject` checks
  presence, expiry, and that `pay_to` *and* amount both match the offer about to
  be paid, and pops the token before returning success — so a replayed, stale or
  re-offered token is refused before anything is signed. Payments serialise
  behind one `asyncio.Lock`.
- The receipt formatter is honest by construction: only `settled is True` reads
  `PAID`; `False` reads `NOT PAID`; anything else reads `UNCONFIRMED`, and the
  block hash is printed in all three. `PaidRequestFailed` is handled separately
  and tells the caller to re-present the same block rather than pay again — the
  right instinct for a rail where the money may already have moved.
- The wallet path and RPC are construction-bound, never tool arguments, and a
  test asserts neither appears in the schema the model sees.
- `ruff check` passes; the narrowed rule set in `pyproject.toml` is documented
  with the measurement behind it.

## Noted, not changed

- `tool.py`'s `ImportError` advises `pip install openai-agents-nano[x402]`, but
  `pyproject.toml` declares no `x402` extra (only `dev`). A user following that
  message gets pip's "does not provide the extra" warning and no install.

## Not audited this run

`nano-mcp-public`, `agent-runtime`, `swarm-proof`, `outreach-tracker` — next run
takes those. `invent-stack` is private and therefore out of scope.
