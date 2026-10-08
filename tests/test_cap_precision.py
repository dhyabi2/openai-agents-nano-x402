"""Laws for the spend cap's scaling to raw (``_cap_to_raw`` in x402_sdk.py).

The cap is the ceiling a quote is refused above. It is configured in XNO and
compared in raw, so the scaling between the two has to be exact -- and it used
to be exact only by accident.

``_cap_to_raw`` scaled with ``value * RAW_PER_XNO``, which is ``decimal``
arithmetic and so runs in the **ambient context**. The default precision is 28
significant digits; a raw amount reaches 39. The function's own guard could not
see the loss, because a value rounded at the 28th significant digit is still an
integer and ``to_integral_value()`` says so.

What hid it is that ``nanopy`` -- a transitive dependency, through
``feeless402`` -- executes ``decimal.getcontext().prec = 40`` at import time
(``nanopy/__init__.py:19``). Importing this package therefore widened the
process-global context as a side effect, and every test that ran in the normal
way got an exact answer. The cap was correct because of a third-party import,
not because this module made it so.

So these laws measure the cap under a context this package does not control,
which is the caller's to set: a program that owns its own ``decimal`` context,
or that calls the payer from inside a ``localcontext()`` around its own money
arithmetic. Measured on the shipped code at precision 28, with caps that are a
legal whole number of raw (30 decimal places or fewer) and which the conversion
therefore owes back unchanged:

| ``max_xno``                            | cap it produced | against the ask |
|----------------------------------------|-----------------|-----------------|
| ``99.99999999999999999999999999999``   | ``…000000``     | **+10 raw**     |
| ``1.00000000000000000000000000006``    | ``…000000``     | **-60 raw**     |
| ``12.345678901234567890123456789012``  | ``…790000``     | **+988 raw**    |

The positive rows are the ones that cost something: the ceiling came back
*above* what was configured, so a quote over the operator's cap was payable and
nothing refused it.

The scaling now places the digits by integer arithmetic on the decimal tuple and
never multiplies, which is what ``nano_pay.raw_to_xno`` already does in the
other direction and for this same reason.
"""
from __future__ import annotations

import os
import sys
import tempfile
from decimal import Decimal, localcontext

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nano_pay import RAW_PER_XNO, raw_to_xno

from openai_agents_nano.x402_sdk import (
    DEFAULT_MAX_XNO,
    NanoX402Refused,
    _cap_to_raw,
    nano_spend_controls,
    parse_raw_amount,
)

#: ``RAW_PER_XNO == 10 ** RAW_EXPONENT``; pinned by a law below rather than
#: imported, so this module still collects against a tree without the fix.
RAW_EXPONENT = 30

# Every precision a caller might plausibly have in force, including the two that
# matter: 28 is the `decimal` default, 40 is what nanopy happens to set.
AMBIENT_PRECISIONS = [1, 9, 28, 40, 60]

# cap in XNO -> the raw it is, by hand. All are 30 decimal places or fewer, so
# each is a whole number of raw and the conversion owes it back unchanged.
EXACT_CAPS = {
    "99.99999999999999999999999999999": 99999999999999999999999999999990,
    "1.00000000000000000000000000006": 1000000000000000000000000000060,
    "12.345678901234567890123456789012": 12345678901234567890123456789012,
    "0.000000000000000000000000000001": 1,  # one raw
    "0.01": 10000000000000000000000000000,
    "0.001": 1000000000000000000000000000,
    "1": 1000000000000000000000000000000,
    "100": 100000000000000000000000000000000,
}


# ------------------------------------------------- the defect, stated directly

@pytest.mark.parametrize("cap,expected", sorted(EXACT_CAPS.items()))
@pytest.mark.parametrize("prec", AMBIENT_PRECISIONS)
def test_a_cap_is_the_number_the_operator_wrote_whatever_the_ambient_context(cap, expected, prec):
    """The ceiling must not depend on the precision the calling program set."""
    with localcontext() as ctx:
        ctx.prec = prec
        assert _cap_to_raw(cap) == expected, (cap, prec)


@pytest.mark.parametrize("cap", ["99.99999999999999999999999999999",
                                 "12.345678901234567890123456789012"])
def test_a_cap_is_never_rounded_up_above_what_was_configured(cap):
    """The expensive direction: a ceiling higher than the one you typed."""
    with localcontext() as ctx:
        ctx.prec = 28
        assert _cap_to_raw(cap) <= EXACT_CAPS[cap]


def test_every_one_of_the_thirty_decimal_places_survives():
    """A cap at full raw precision: 30 places, each a distinct digit position."""
    cap = "0." + "".join(str((i % 9) + 1) for i in range(30))
    expected = int(cap.split(".")[1])
    with localcontext() as ctx:
        ctx.prec = 28
        assert _cap_to_raw(cap) == expected


def test_the_corrected_cap_reaches_the_spend_controls_that_read_it():
    """Not just the helper: the number the x402 client is actually handed."""
    cap = "99.99999999999999999999999999999"
    with localcontext() as ctx:
        ctx.prec = 28
        controls = nano_spend_controls(max_xno=cap)
    allowed = controls["allowed_assets"][0]
    assert allowed["max_amount_per_payment"] == str(EXACT_CAPS[cap]), allowed


def test_the_refusal_hint_names_the_raw_amount_exactly():
    """A hint that names the wrong number is worse than no hint."""
    with localcontext() as ctx:
        ctx.prec = 28
        with pytest.raises(NanoX402Refused) as exc:
            parse_raw_amount("12.345678901234567890123456789012")
    assert "12345678901234567890123456789012" in str(exc.value)


# ----------------------------------------------------- controls: must hold too

@pytest.mark.parametrize("prec", AMBIENT_PRECISIONS)
def test_the_default_cap_is_unchanged_at_every_precision(prec):
    with localcontext() as ctx:
        ctx.prec = prec
        assert _cap_to_raw(DEFAULT_MAX_XNO) == EXACT_CAPS["0.01"]


@pytest.mark.parametrize("prec", AMBIENT_PRECISIONS)
def test_a_cap_finer_than_one_raw_is_still_refused_not_rounded_up(prec):
    """31 decimal places is sub-raw: a refusal, never a silent 1 raw."""
    with localcontext() as ctx:
        ctx.prec = prec
        with pytest.raises(NanoX402Refused):
            _cap_to_raw("0." + "0" * 30 + "1")


@pytest.mark.parametrize("cap", ["nan", "Infinity", "-Infinity", "0", "-1", "abc", None])
@pytest.mark.parametrize("prec", [28, 40])
def test_a_non_finite_or_non_positive_cap_is_still_refused(cap, prec):
    with localcontext() as ctx:
        ctx.prec = prec
        with pytest.raises(NanoX402Refused):
            _cap_to_raw(cap)


def test_the_conversion_does_not_leak_a_context_out_to_the_caller():
    """This package must not set the caller's precision -- that is the bug above."""
    with localcontext() as ctx:
        ctx.prec = 28
        before_prec, before_traps = ctx.prec, dict(ctx.traps)
        _cap_to_raw("1.00000000000000000000000000006")
        assert ctx.prec == before_prec
        assert dict(ctx.traps) == before_traps


def test_the_raw_exponent_matches_the_dependency_it_mirrors():
    """If nano_pay ever redefines RAW_PER_XNO, this fails instead of mis-scaling."""
    assert RAW_PER_XNO == 10 ** RAW_EXPONENT


@pytest.mark.parametrize("cap,expected", sorted(EXACT_CAPS.items()))
def test_a_cap_round_trips_back_to_the_text_it_came_from(cap, expected):
    """raw_to_xno is the inverse; the pair agreeing pins both directions."""
    assert Decimal(raw_to_xno(expected)) == Decimal(cap)
