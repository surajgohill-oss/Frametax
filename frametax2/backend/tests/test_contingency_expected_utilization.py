"""
test_contingency_expected_utilization.py

Consolidated Backend Correction, Part 19-20 (CBA-009) — verifies the
GENERIC contingency-expected-utilization correction in
qualification_derivation.derive_qualification_register().

Codex's confirmed defect: a program whose statutory rule says the
"contingency" category qualifies (e.g. Mauritius's real, cited
EDB-2020-QPE-List finding) had the FULL undeployed reserve projected as
100% qualifying spend, unconditionally. At Mauritius's real 40% rate this
overstated the projected incentive by $120,452.40 on a $301,131.00
reserve.

The fix does not touch the statutory finding itself (qualifies=True stays
qualifies=True — that's a real legal fact). It scales what fraction of the
reserve a PROJECTION treats as likely to be incurred, using a new, real,
typed, user-controlled ProductionFacts.contingency_expected_utilization_pct
fact. Unset must never silently become 0% or 100% — both are asserted
below. The mechanism is verified GENERIC: it is exercised here through the
real Mauritius rule set (the only program with a live qualifies=True
contingency rule at the time this was written), but the branch itself is
keyed only on `category == "contingency" and qualifies is True`, never on
`program_slug`.
"""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import (
    BudgetLine,
    ProductionFacts,
    derive_qualification_register,
)
from app.calculators.qualification_model import GreyReason, QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine

MU_PROGRAM = "mu_edb_incentive"
RESERVE_USD = 301_131.00
MU_RATE = 0.40


def _mu_contingency_line() -> BudgetLine:
    return BudgetLine(
        account_code="9900", description="Contingency reserve",
        amount_usd=RESERVE_USD, spend_category="contingency",
    )


def _register(pct: float | None) -> list:
    rules = get_program_rules(MU_PROGRAM)
    doctrine = resolve_program_doctrine(MU_PROGRAM).doctrine
    facts = ProductionFacts(jurisdiction_code="MU", contingency_expected_utilization_pct=pct)
    return derive_qualification_register(
        [_mu_contingency_line()], MU_PROGRAM, facts, MU_RATE,
        program_territorial_text=None, rules=rules, doctrine=doctrine,
    )


def test_unset_utilization_is_grey_not_zero_or_hundred_percent():
    """Runtime acceptance #18/19 precondition: absence must be a genuine
    disclosed grey area, never silently 0% (would wrongly zero out a
    category the statute confirms qualifies) or 100% (the exact defect)."""
    register = _register(None)
    assert len(register) == 1
    row = register[0]
    assert row.state == QualificationState.GREY_AREA_REQUIRES_AUTHORITY
    assert row.grey_reason == GreyReason.MISSING_PRODUCTION_FACT
    # Full reserve disclosed as potential upside, not silently priced in.
    assert row.incentive_upside_usd == pytest.approx(RESERVE_USD * MU_RATE, abs=0.01)
    assert row.amount_usd == pytest.approx(RESERVE_USD, abs=0.01)


def test_zero_percent_utilization_excludes_full_reserve():
    """Runtime acceptance #18 — 0% utilization -> 0 projected contingency QPE."""
    register = _register(0.0)
    qualifying = [r for r in register if r.state == QualificationState.QUALIFIES]
    excluded = [r for r in register if r.state == QualificationState.EXCLUDED]
    assert qualifying == []
    assert len(excluded) == 1
    assert excluded[0].amount_usd == pytest.approx(RESERVE_USD, abs=0.01)


def test_hundred_percent_utilization_still_goes_through_qpe_rules():
    """Runtime acceptance #19 — 100% utilization is not a bypass; it still
    produces exactly one QUALIFIES record for the full amount via the same
    statutory-rule path, not a shortcut around it."""
    register = _register(100.0)
    qualifying = [r for r in register if r.state == QualificationState.QUALIFIES]
    excluded = [r for r in register if r.state == QualificationState.EXCLUDED]
    assert len(qualifying) == 1
    assert qualifying[0].amount_usd == pytest.approx(RESERVE_USD, abs=0.01)
    assert excluded == []


def test_forty_percent_utilization_matches_exact_task_figures():
    """The exact figures Codex's audit and the correction task cited:
    $301,131.00 reserve at 40% expected utilization projects $120,452.40
    of expected-deployed QPE (the qualifying portion) and $180,678.60 of
    expected-undeployed reserve (excluded, not incurred spend)."""
    register = _register(40.0)
    qualifying = [r for r in register if r.state == QualificationState.QUALIFIES]
    excluded = [r for r in register if r.state == QualificationState.EXCLUDED]
    assert len(qualifying) == 1
    assert len(excluded) == 1
    assert qualifying[0].amount_usd == pytest.approx(120_452.40, abs=0.01)
    assert excluded[0].amount_usd == pytest.approx(180_678.60, abs=0.01)
    # The two portions must sum back to the full reserve — no leakage.
    assert qualifying[0].amount_usd + excluded[0].amount_usd == pytest.approx(RESERVE_USD, abs=0.01)


def test_partial_utilization_is_monotonic_in_qualifying_amount():
    """Higher expected utilization must never project LESS qualifying
    spend — a basic sanity guard on the scaling arithmetic."""
    prev = 0.0
    for pct in (10.0, 25.0, 50.0, 75.0, 90.0):
        register = _register(pct)
        qualifying = [r for r in register if r.state == QualificationState.QUALIFIES]
        amt = qualifying[0].amount_usd if qualifying else 0.0
        assert amt >= prev
        prev = amt


def test_pct_is_clamped_to_valid_range():
    """A stray out-of-range value (e.g. a unit-confusion bug upstream
    passing 400 instead of 40) must clamp to the legal 0-100 band rather
    than projecting more spend than the reserve actually contains."""
    register = _register(400.0)
    qualifying = [r for r in register if r.state == QualificationState.QUALIFIES]
    assert len(qualifying) == 1
    assert qualifying[0].amount_usd == pytest.approx(RESERVE_USD, abs=0.01)


def test_contingency_correction_is_generic_not_hardcoded_to_mauritius():
    """The branch must be keyed on category+qualifies, never on
    program_slug — verified by confirming the source contains no
    conditional on the Mauritius slug within the contingency branch."""
    import inspect

    from app.calculators import qualification_derivation as qd

    source = inspect.getsource(qd.derive_qualification_register)
    # Isolate just the contingency branch for a scoped check.
    start = source.index('category == "contingency"')
    branch = source[start:start + 2000]
    assert "mu_edb" not in branch.lower()
    assert "mauritius" not in branch.lower()
    assert "little_utopia" not in branch.lower()
