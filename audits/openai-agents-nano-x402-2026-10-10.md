# openai-agents-nano-x402 — audit 2026-10-10

Previous audits 2026-10-08 and 2026-10-05. Audited at `d5579de` (`main` after
#20), then re-measured on `bfed72a` (`main` after #21, below).

Lens: can an agent PAY in XNO with this today without being hurt — overpaying,
paying the wrong account, paying twice, or being unable to pay at all.

`pip install -e ".[dev]"` then `python3 -m pytest tests -q`: **279 passed** on
`d5579de`, **284** after #21, **289** after #22.

> **A correction about this run's own numbers.** #21's and #22's first bodies
> said "173 → 178". Those were measured against a local `main` two commits
> behind `origin/main` (`66528af`, before #19 and #20), so the absolute counts
> were wrong; the real ones are above. The failing-then-passing evidence in both
> is unaffected — it is a revert of one file against its own tests — and CI ran
> both against the real base. Corrected in #22's body and in a comment on #21.

## Found and fixed

**1. An unusable wallet file left the tool as an exception, so the model was
told to retry for ever (#21, merged).** `wallet.exists()` / `create()` /
`load()` sat outside every `try` in `_nano_x402_fetch` and outside its lock
(`tool.py:430-433`). `load()` is `json.loads(path.read_text())`, so any
`X402_WALLET_PATH` that exists but is not a usable wallet — a directory, a
truncated or hand-edited file, the wrong artefact — raised out of the tool, and
the Agents SDK renders that to the model as *"An error occurred while running
the tool. Please try again."*: an unbounded retry that cannot ever succeed, no
reason given, and the agent cannot even **preview** a price. The module's own
docstring (line 15) promises *"the return value is always agent-readable text"*.
Measured on a directory and on a truncated file, both through the real
`on_invoke_tool`. Same defect class the 2026-10-03 audit fixed for `xno_to_raw`
one line further in — its comment is still two lines below. Nothing signs on
that path, so no payment behaviour changed. Four tests fail with `tool.py`
reverted; a fifth is the control (a missing wallet is still created, a
pre-existing one still loaded).

**2. The receipt's `pay_to` was the merchant's word, not where the money went
(#22).** `_PayeePinnedWallet` (#18) guarantees the *signing* half: a redeem that
reaches a receipt was signed to the quoted, token-bound, authorised payee or no
block exists. The *record* half was open. feeless402 sets its own ground truth
and merges the merchant's receipt fields over it (`nano_pay/x402.py:563-591`);
the exclusion list its own comment calls *"never let them speak for ours"* names
`settled`, `block`, `amount_xno`, `amount_raw`, `note`, `ledger` — and not
`pay_to`, which is also not re-asserted afterwards as `amount_xno` and `block`
are. So a merchant returning a `payment-response` header naming any address at
all wrote the one line of the record that says where the money went, in the
field the pinning exists to guarantee; the block hash is right, so
`receipt_hash_mismatch` does not fire. Measured: `pay_to:` printed
`nano_3t6k35g…ncuohr3` while the block was signed to `nano_1p7cqqn…tcoa5`. Two
harms — the operator's audit trail becomes attacker-chosen text, and an agent
told to check the receipt against its preview concludes its money went astray
and buys again. Fixed in this repository: `_format_receipt` is handed
`quote["pay_to"]` and prints that; a differing merchant claim is still shown,
named as the merchant's and UNTRUSTED. Four tests fail reverted; the fifth is
the honest-merchant control.

## Found, NOT fixed — these are the owner's

**3. An UNCONFIRMED redeem drops the only thing that stops a second signature,
so one resource can be bought twice.** `nano_pay/x402.py:543-545` pops the
pending-payment journal entry on `200 <= status < 300`, and `_settle_outcome`
can return `("indeterminate", "absent")` for that same 2xx when
`_ledger_verdict` has not seen the block inside `CONFIRM_WAIT_S` (8 s) — a late
facilitator broadcast, or a node that has not indexed yet. The journal is
feeless402's only de-duplication and is deliberately written *before* the block
leaves. Deleting it in exactly the unknown case leaves nothing that remembers
the first attempt: the tool mints a fresh `quote_token` on the next preview
(`tool.py:473`) and has no refusal for "you already hold an unconfirmed block
for this request" (`_REFUSAL_REASONS`, `tool.py:243-262`), so the next redeem
signs a second valid send against the advanced frontier. Measured: two redeems,
two signed blocks of 0.001 XNO each, journal `{}` after each one, for one
resource. Note the asymmetry — on *no reply* (`r2 is None`) line 543 is never
reached, the entry survives, and `_format_failed_payment` correctly says *"do
NOT pay again … Re-present the SAME block"*; the 200-but-unconfirmed path only
says "check the block hash" and enforces nothing.
**Why it is not fixed here:** the deletion is in feeless402, a separate project
outside this repository. The compensating fix on our side — state that refuses a
redeem while an unconfirmed block for the same request is outstanding — is new
state on the money-send path, which is the owner's call and not a minimal fix.
Not covered by any test here: nothing in `tests/` calls the real
`request_with_payment`, so the journal is never exercised.

**4. The README's official-x402-SDK quickstart cannot run.** `README.md:209`
(and the generated `PKG-INFO:235`) says
`Wallet("~/.nano-pay/wallet.json").load()`. `nano_pay.wallet.Wallet.__init__` is
`self.path = Path(path)` with no `.expanduser()`, so with a real wallet present
at `/root/.nano-pay/wallet.json` the line raises *"no wallet at
~/.nano-pay/wallet.json — run `nano-pay init` first"*, sending the reader to fix
a wallet that is already there. Every other wallet construction in this tree
does expand, `tool.py:395` included. The edge worth naming: if a literal
`./~/.nano-pay/wallet.json` ever exists (an ordinary shell-quoting accident),
`exists()` is true and the snippet loads a **different seed** — a payer bound to
the wrong account. The one-line fix is
`Wallet(Path("~/.nano-pay/wallet.json").expanduser())`, and
`tests/test_readme_release_claims.py` is where a law for it belongs. Left for a
run of its own rather than folded into an unrelated branch; the same section's
`pip install "openai-agents-nano[x402]"` is already documented as impossible at
`README.md:80-84`.

## Also checked, found clean

- No float on any amount in `src/`. `_apply_cap` and `xno_to_raw` are exact, and
  #20's `_xno_to_raw_exact` places digits by integer arithmetic rather than
  multiplying in the ambient `decimal` context.
- The payee pin (#18) and the price pin hold: a seller that quotes `nano_A` and
  answers `nano_B` for the same amount is refused with nothing signed, and the
  pin sits outside the mandate proxy so a moved payee never reserves.
- `MandateGuard.spend` keeping a reservation when `send()` raises is documented
  and deliberate (`mandate.py:617-641`).
- No secret in the tree; no `subprocess`, `eval` or shell anywhere in `src/`;
  `method` cannot CRLF-inject (`http.client._validate_method`).
- The two release-asset URLs in the README resolve (GitHub hands out a signed
  `objects.githubusercontent.com` redirect; the 401 seen from here is this
  session's egress proxy, not a 404).

## Could not verify

- **No live payment and no live merchant.** Every measurement stubs
  `requests.request` and the block signer, as the repository's own tests do. No
  XNO moved, and finding 3's second signature was observed as two calls to
  `build_payment_block`, not as two confirmed blocks on the ledger.
- `x402_sdk.py:174`/`:158` multiply an amount in the **ambient** decimal
  context, which #20 removed elsewhere for exactly that reason. It is masked
  because `nanopy/__init__.py:19` sets `prec = 40` process-wide on import. Under
  the stdlib default, or inside a caller's `localcontext()`, `_cap_to_raw`
  rounds rather than refusing a cap finer than one raw — but the error could not
  be driven above ~1e-27 relative, i.e. sub-raw at any realistic cap, so there
  is no money loss to show and nothing was changed. A contract violation,
  reported rather than repaired.
- `nano_pay/x402.py:485` calls `wallet.account()` where `Wallet.account` is a
  property, so it always raises into the bare `except Exception: pass` below and
  `X-PAYMENT-PROOF` is never attached for anyone. Dependency-only; nothing in
  `src/` claims to send that header.
