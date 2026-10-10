"""Independent spend-eligibility controls (AG adjudication repair plan, items 1-2).

SYNTHETIC ONLY: every budget below is built here from raw amounts and categories; no production row, persisted generation or
engine output supplies an expected value. Each expectation is derived from the primary rule text cited in the rule row
(California Film Commission Qualified Expenditure Chart, Program 4.0, Jan 2026; New Mexico TRD FYI-370; EDB Film Rebate
Scheme guidelines), by explicit sums over the raw lines. The pre-cap QPE is NOT asserted to equal any producer estimate."""
from __future__ import annotations

import pytest

from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import GreyReason, QualificationState as S
from app.data.program_spend_rules import get_program_rules

CA, NM, MU = "ca_film_30", "us_nm_film_credit", "mu_edb_incentive"
# A synthetic feature budget with the raw account amounts below (independent of any real production).
RAW = {
    "1100": ("SCRIPT", 300_000.0, "atl_writer"),
    "1200": ("PRODUCING", 700_000.0, "atl_producer"),
    "1300": ("DIRECTING", 250_000.0, "atl_director"),
    "1400": ("CAST", 800_000.0, "atl_cast"),
    "3100": ("CAMERA DEPARTMENT", 400_000.0, "btl_crew_labor"),
    "3500": ("TRANSPORTATION", 150_000.0, "btl_transportation"),
    "6200": ("LEGAL COSTS", 100_000.0, "legal_accounting"),
    "6800": ("RESIDUALS RESERVE", 200_000.0, "residuals_reserve"),
}


def _lines() -> list[BudgetLine]:
    return [BudgetLine(code, desc, amt, spend_category=cat) for code, (desc, amt, cat) in RAW.items()]


def _reg(slug: str, jur: str, rate: float = 0.35):
    return {a.account_code: a for a in derive_qualification_register(_lines(), program_slug=slug, facts=ProductionFacts(jurisdiction_code=jur), rate=rate)}


def test_ca_atl_compensation_accounts_are_mixed_never_wholly_qualified_and_never_dropped():
    reg = _reg(CA, "US-CA")
    for code in ("1100", "1200", "1300", "1400"):
        a = reg[code]
        assert a.state == S.GREY_AREA_REQUIRES_AUTHORITY and a.grey_reason == GreyReason.MIXED_ACCOUNT, code
        assert a.incentive_upside_usd == pytest.approx(RAW[code][1] * 0.35), "visible as conditional upside, not silently removed"
    # The confirmed base is the explicit sum of the lines no NQ clause touches (independent of the engine's own total).
    expected_qualifying = RAW["3100"][1] + RAW["3500"][1]
    assert sum(a.amount_usd for a in reg.values() if a.state == S.QUALIFIES) == pytest.approx(expected_qualifying)
    assert sum(a.amount_usd for a in reg.values() if a.state == S.GREY_AREA_REQUIRES_AUTHORITY) == pytest.approx(
        sum(RAW[c][1] for c in ("1100", "1200", "1300", "1400", "6200")))
    assert reg["6800"].state == S.EXCLUDED


def test_ca_every_atl_compensation_rule_row_is_an_explicit_mixed_row_with_the_primary_source():
    rules = get_program_rules(CA)
    for cat in ("atl_writer", "atl_producer", "atl_director", "atl_cast", "legal_accounting"):
        r = rules[cat]
        assert r.qualifies is None and r.confidence_tier == "VERIFIED" and "Qualified Expenditure Chart" in r.notes, cat
    # Mutant guard: a "CA writer leak" (the category defaulting back to qualified) is exactly rules[...] disappearing or flipping.
    assert rules["atl_writer"].qualifies is not True


def test_ca_residuals_reserve_is_explicitly_excluded_residual_compensation():
    a = _reg(CA, "US-CA")["6800"]
    assert a.state == S.EXCLUDED, "Program 4.0 Guidelines list residual compensation as Non-Qualified"
    assert get_program_rules(CA)["residuals_reserve"].qualifies is False


def test_residuals_reserve_without_an_express_rule_is_a_fact_gap_not_incurred_qualified_spend():
    for slug, jur in ((NM, "US-NM"), (MU, "MU")):
        a = _reg(slug, jur, 0.30)["6800"]
        assert a.state == S.GREY_AREA_REQUIRES_AUTHORITY and a.grey_reason == GreyReason.MISSING_PRODUCTION_FACT, slug
        assert a.incentive_upside_usd == pytest.approx(200_000.0 * 0.30), "counted exactly once later, so visible as conditional upside"


def test_nm_nonresident_performers_are_not_blanket_excluded_by_residence():
    # New Mexico FYI-370: nonresident performing-artist payments can qualify subject to withholding / tax predicates, so the cast
    # account keeps qualifying under the open-default doctrine; it must not turn into an exclusion on residence alone.
    reg = _reg(NM, "US-NM")
    assert reg["1400"].state == S.QUALIFIES and reg["1100"].state == S.QUALIFIES


def test_mu_labor_travel_and_professional_services_keep_their_express_eligibility():
    reg = _reg(MU, "MU")
    assert reg["1400"].state == S.QUALIFIES and reg["1100"].state == S.QUALIFIES
    assert reg["6200"].state in (S.QUALIFIES, S.GREY_AREA_REQUIRES_AUTHORITY)


def test_budgeting_a_reserve_never_changes_the_qualifying_total_of_the_other_lines():
    with_reserve = {a.account_code: a.state for a in derive_qualification_register(_lines(), CA, ProductionFacts("US-CA"), 0.35)}
    without = {a.account_code: a.state for a in derive_qualification_register(
        [l for l in _lines() if l.account_code != "6800"], CA, ProductionFacts("US-CA"), 0.35)}
    assert all(with_reserve[c] == without[c] for c in without), "no double subtraction or cross-effect"


# ── Cap families are separate concepts (AG adjudication repair plan, item 3) ───────────────────────────────────────────
def _probe(slug: str, jur: str, qpe: float, facts: frozenset[str] | None = None):
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind

    alloc = AccountAllocation(
        account_code="3100", description="below-the-line production spend", amount_usd=qpe, component="production",
        jurisdiction_code=jur, assignment_kind=AssignmentKind.FIXED, rationale="cap probe", governing_decision="cap-control",
        line_id="cap-1",
    )
    return price_segment(
        jurisdiction_code=jur, program_slug=slug, allocations=[alloc], spend_category_by_code={"3100": "btl_crew_labor"},
        offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=qpe * 1.4,
        evidenced_requirement_facts=facts,
    )


def test_ca_qualified_expenditure_limit_is_a_base_limit_not_an_annual_fund_or_incentive_cap():
    from app.data.program_rate_rules import get_qpe_dollar_cap

    rule = get_qpe_dollar_cap(CA)
    assert (rule.default_limit_usd, rule.independent_limit_usd) == (120_000_000.0, 20_000_000.0)
    big = _probe(CA, "US-CA", 150_000_000.0)
    assert big.qpe_usd == pytest.approx(120_000_000.0) and big.qpe_dollar_cap_applied_usd == pytest.approx(30_000_000.0)
    assert big.qpe_dollar_limit_basis == "non_independent_default"
    assert big.incentive_cap_usd is None and big.annual_fund_budget_usd == pytest.approx(750_000_000.0)
    # The independent limit is used only when the independent category is evidenced, never inferred.
    ind = _probe(CA, "US-CA", 30_000_000.0, frozenset({rule.independent_fact}))
    assert ind.qpe_usd == pytest.approx(20_000_000.0) and ind.qpe_dollar_limit_basis == "independent_category_evidenced"
    assert _probe(CA, "US-CA", 30_000_000.0).qpe_usd == pytest.approx(30_000_000.0), "no independence fact -> non-independent limit"
    # A cap never creates spending evidence: below the limit nothing is applied.
    small = _probe(CA, "US-CA", 5_000_000.0)
    assert small.qpe_usd == pytest.approx(5_000_000.0) and small.qpe_dollar_cap_applied_usd == 0.0


def test_nm_annual_fund_is_disclosed_as_the_fund_and_never_as_a_per_project_incentive_cap():
    res = _probe(NM, "US-NM", 2_000_000.0)
    assert res.annual_fund_budget_usd == pytest.approx(140_000_000.0)
    assert res.incentive_cap_usd is None, "the annual fund is not a project incentive cap"
