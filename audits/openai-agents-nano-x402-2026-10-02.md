# openai-agents-nano-x402 — code audit, 2026-10-02

Clone of `main` at `86e86bc`. Baseline in a clean venv, before any change:

```
$ pip install -e ".[dev]"      # succeeds
$ python3 -m pytest tests/ -q  # 85 passed
$ ruff check .                 # All checks passed!
```

After: **88 passed**, `ruff check .` clean.

## Checked

- The whole redeem path in `tool.py` read against what `feeless402` actually does, not against
  its docstring: `nano_pay/x402.py:361-500` was read to confirm `request_with_payment` re-reads
  the 402 and calls `wallet.build_payment_block(rpc, pay_to, amount)`, which is the hook
  `_MandatedWallet` relies on. It does.
- `pick_nano_offer` / `offer_amount_raw` / `offer_pay_to` in feeless402 — the same class of bug
  found in `langchain-vend` today (an amount from one rail quoted against another rail's payee).
  Clean here: the offer must be `network` starting `nano` or `asset` in (xno, nano), and
  `offer_pay_to` returns only an address starting `nano_`/`xrb_`, so amount and payee come from
  one Nano offer.
- Every path an amount takes through `_apply_cap` -> `xno_to_raw`. `_apply_cap` returns a
  `Decimal` and `str()` of it is scientific notation below 1e-6 (`"1E-7"`), which reaches
  `xno_to_raw`; `feeless402`'s `xno_to_raw` reads the decimal tuple rather than multiplying, so
  `1E-7`, `5E-14` and `100` all convert exactly and round-trip. No float, no truncation. Not a
  defect — recorded because it looks like one.
- `MandateGuard` end to end: `parse_raw` (floats, bools, leading zeros, `>2**128` all refused),
  `xno_to_raw`/`raw_to_xno`, `verify_signed`, the ledger's totals check, and the spend/`unknown`
  reservation. The over-counting on a re-presented block is deliberate and documented.
- **The vendoring claim in the README.** `src/openai_agents_nano/mandate.py` is claimed to be
  byte-for-byte identical to `agent-wallet-multirail`'s. Verified across all three copies on
  disk: `md5 810320ca04bc…`, 828 lines, identical in `nano-wallet-xno/mandate.py`,
  `agent-wallet-multirail/src/agent_wallet_multirail/mandate.py` and this repo.
- Both published install URLs in the README, live: the v0.1.0 wheel (HTTP 200, 9816 bytes) and
  the sdist (HTTP 200, 12674 bytes). Every relative link in `README.md` and `docs/*.md` resolves.

## Found and fixed

**An operator mandate whose ledger path cannot be opened raised an exception out of the tool
instead of refusing.** `MandateGuard` reaches its ledger through `_Locked.__enter__`, which is a
plain `open(path + ".lock", "a+")` (`mandate.py:518`). A ledger path whose directory does not
exist — or sits under a regular file, or on a read-only mount — raises `OSError`, not
`MandateRefused`. Both call sites in `tool.py` caught only `MandateRefused`:

```
check:  *** FileNotFoundError: …/no-such-dir/ledger.json.lock   <- escapes
status: *** FileNotFoundError: …/no-such-dir/ledger.json.lock   <- escapes
spend:  *** FileNotFoundError: …/no-such-dir/ledger.json.lock   <- escapes
```

Two contracts broken at once. `mandate.py`'s own: *"Any doubt - an unreadable ledger, a ledger
for another mandate, an unknown field, a clock before issue time - is a refusal with a
machine-readable reason."* And `tool.py`'s: *"The return value is always agent-readable text."*
Reached through the tool, `X402_MANDATE_LEDGER` pointing anywhere unwritable took the whole
`nano_x402_fetch` call down with a raw `FileNotFoundError` — on the dry run too, so the agent did
not even get the spendless quote it asked for.

Fixed in `tool.py`, where both call sites live:

- redeem: a non-`MandateRefused` exception from `_guard()` or `guard.check()` now returns
  `REFUSED: … reason: mandate_unavailable`. Fail closed — an unrecordable spend is not spent.
- dry run: nothing is spent, so the quote still stands, but it now reads
  `mandate: could not be checked (FileNotFoundError: …); a redeem will refuse until this is
  fixed` instead of `mandate: allows this payment`.

`mandate.py` is deliberately **not** changed: it is vendored byte-for-byte into three Tier 0
repositories and a test pins the bytes, so the fix belongs at this repo's call sites. The README's
refusal-reason list now includes `mandate_unavailable`.

Tests: 3 new cases in `tests/test_tool_mandate.py` (missing directory, ledger path under a
regular file, and an unparseable mandate file as a regression guard on the path that already
worked). The first two fail on `main` and pass with the fix; each also asserts `seller.signed ==
[]`, so a payment is never signed while the mandate cannot be checked.

## Found, NOT fixed

1. **`MandateGuard.status()` still raises on an unusable ledger path** (`mandate.py:643-658`),
   which is what `mandate status` calls. Same root cause, but the fix belongs in `mandate.py`,
   and that file is vendored byte-for-byte into `agent-wallet-multirail` and `nano-wallet-xno`
   with a test pinning the bytes — changing it here alone would break the vendoring and split
   the enforcement logic across three repositories. It needs one change landed in all three
   together; that is the owner's sequencing call, not an audit's.
2. **`feeless402`'s journal re-presents a signed block without calling `build_payment_block`**
   (`nano_pay/x402.py:414-420`), so `MandateGuard.spend` does not run for a re-presentation.
   Not a cap overrun — the first attempt already reserved that amount, and the recursive
   re-payment path does go through the guard — but it means the mandate ledger's `status` field
   stays `unknown` for a block the merchant later honours. In an external MIT dependency, not
   this repository.
3. The v0.1.0 release still predates `mandate.py` and the `_apply_cap` hardening. Documented in
   the README since 2026-09-30 and guarded by `tests/test_readme_release_claims.py`. Only a
   person can cut a release.

## Could not verify

- No live payment and no live 402. The audit is offline plus the two release-URL HEAD requests
  above; `api.nano-gpt.com` was not called, and this run had no funded wallet.
- The read-only-directory variant of the finding could not be tested here: this container runs as
  root, so a `0o500` directory is still writable and the guard happily succeeded. The committed
  test uses a ledger path under a regular file instead (`NotADirectoryError`), which no privilege
  bypasses. The read-only-mount case is the same code path but is not covered by a test.
