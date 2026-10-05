# openai-agents-nano-x402 — audit 2026-10-05

Lens: can an agent pay an x402-priced endpoint in XNO with this today, without
being hurt. Audited at `ce85feb` (`main` after #17).

## Checked

- `src/openai_agents_nano/tool.py` end to end: `QuoteTokenStore.mint/reject`,
  `_MandatedWallet`, `_apply_cap`, the whole `_nano_x402_fetch` body (both
  phases), and every formatter.
- The payment path **through the dependency**, not just up to it: read
  `nano_pay/x402.py` of the installed `feeless402` 0.2.13 —
  `request_with_payment`, `pick_nano_offer`, `offer_amount_raw`, `offer_pay_to`,
  `build_payment_header`, the journal re-present path, `_settle_outcome`.
- `src/openai_agents_nano/__init__.py`, `mandate.py` (`spend`, `_check`, the
  ledger shape), `x402_sdk.py`, `pyproject.toml`, `.github/workflows/ci.yml`.
- Amount handling: `_apply_cap` (`Decimal`, `is_finite`, `< 0`, `min`), the
  `xno_to_raw`/`raw_to_xno` boundary, `price_raw` as the ceiling handed to the
  payer. No float on any amount.
- Standing duty 1: all 13 remote branches against `main`. **0 orphans** —
  `fix/untrack-build-output` (fetched this run, no pull request) is fully
  superseded: `.gitignore` line 9 is already `build/`, `git ls-files build/` is
  empty, and `tests/test_repo_tree.py` is on `main`.
- Secret scan of the tree. None found.
- `pip install -e ".[dev]"` then `python3 -m pytest tests/ -q`: **164 passed** on
  `main`, **173** after this change. `compileall` clean.

## Found and fixed (this PR)

**The two-phase redeem pins the amount the paying read may charge. It pinned the
payee nowhere.**

`request_with_payment` RE-READS the 402 before it signs and takes both numbers
from THAT read (`nano_pay/x402.py:444-447`):

```python
offer   = pick_nano_offer(quote)
amount  = offer_amount_raw(offer)
pay_to  = offer_pay_to(offer)
if amount > max_raw:                      # the amount is checked
    raise PriceCapExceeded(...)
...
block, ... = wallet.build_payment_block(rpc, pay_to, amount)   # pay_to is not
```

`tool.py` closed the amount half earlier (the comment at `:481-490`: hand
`price_raw`, the quoted amount, instead of the operator's whole `cap_raw`). The
payee half was still open, for the identical reason the moved price was: the
`quote_token` binds `pay_to` (`tool.py:477`), but **against the tool's own
dry-run read, never against the address finally signed**. So a seller could quote
`nano_A` on both dry runs, answer `nano_B` for the same amount on the paying
read, and the block was signed to `nano_B`.

Measured, before the fix, with the switched-payee seller in
`tests/test_payee_moved_after_preview.py`:

```
PAID (Nano x402):
  status:    200
  amount:    0.001 XNO  (cap 0.01)
  pay_to:    nano_3t6k35gi95xu6tergt6p69ck76…      <- never previewed, never authorised
  settled:   True
```

The amount is correct, the cap is satisfied, feeless402's own check passes, and
the money is in the wrong account. `_MandatedWallet` (`tool.py:113-118`) already
checks the signing-time payee — but **only when an operator mandate is
configured**, which is not the default.

**The fix** is `_PayeePinnedWallet`, the same proxy shape `_MandatedWallet`
already uses, applied on **every** redeem: `build_payment_block` refuses when
`to_addr` is not the address just quoted and authorised, so no block exists. It
is wrapped **outside** the mandate proxy on purpose — `MandateGuard.spend`
appends to `payments` and adds to `spent_raw` *before* it calls the block
builder, so a pin inside it would leave a phantom reservation against the
operator's cap for a payment that never happened.

This **only adds a refusal**: no amount, rounding, destination or key path
changes, and the single address allowed is the one the agent previewed.

Failing-then-passing, `src/openai_agents_nano/tool.py` alone reverted to `main`
with the tests kept: **5 failed, 168 passed** — the four new ones plus
`test_tool_mandate.py::test_payee_switched_after_the_preview_is_refused_at_signing`.

Five of the ten additions are **controls that hold either way**: an unchanged
payee still pays, a payee re-stated identically on the paying read still pays, a
price cut with the same payee is still paid, dry-run previewing is never refused
for its address, and the mandate ledger does record a payment that does happen
(which is what makes the "ledger untouched" assertion non-vacuous).

**One existing test changed its expectation, and did not lose coverage.**
`test_tool_mandate.py::test_payee_switched_after_the_preview_is_refused_at_signing`
asserted the switched payee was refused by the *mandate*
(`payee_not_allowed`). The pin now refuses first, so it asserts the pin's
refusal and that both addresses are named; its real invariant,
`seller.signed == []`, is unchanged. The mandate's own allow-list is untouched and
still covered: `test_env_var_is_read_at_construction` refuses a payee the
operator never allowed with `payee_not_allowed`, and `tests/test_mandate.py:255`
covers the guard directly.

## Found, not fixed here (one concern per branch)

**`.github/workflows/ci.yml:51` installs this package from a GitHub Pages index
on a deleted account.**

```yaml
--extra-index-url https://pandeveloper001.github.io/openai-agents-nano-x402/simple/
```

`PANDeveloper001` is gone, and `funnel.md:357` records first-hand that
`github.com/PANDeveloper001/openai-agents-nano-x402` returns 404. The step runs
on the weekly cron and on `workflow_dispatch`, so the job this workflow describes
as "Weekly: test install from every mirror" fails every Monday, and the
"Import and smoke-test the installed package" step after it never runs — the
weekly signal about what is actually installable has been permanently red rather
than absent. This is the **only** reference to that account left in a live path:
`README.md` already installs from `dhyabi2` (lines 35, 51, 54, 72, 148), and the
other matches are in `scripts/` and `.ledger/` operator notes. Left for its own
branch because it is a CI/release-path change, not a code fix.

## Could not verify

- **Any external URL.** This session's egress proxy answers 403 to CONNECT for
  every host outside its allow-list, including `pandeveloper001.github.io`,
  `pages.github.com` and `github.com/PANDeveloper001`
  (`curl "$HTTPS_PROXY/__agentproxy/status"` lists the denials). So the dead
  index above is established from the account's deletion and the repository's own
  recorded 404, not re-probed here.
- **The journal re-present path against a pin.** `_journal_key` includes
  `pay_to`, and a journal hit returns a stored header without calling
  `build_payment_block`, so the pin is not consulted. That path re-presents a
  block that was already signed in an earlier run and moves no new money, so
  re-presenting is the correct behaviour — but an entry signed to a switched
  payee *before* this fix would still be re-presentable. No such entry is known
  to exist.
- A real wallet, a real node and a real broadcast: none exist in this session,
  and the suite opens no socket by design.
