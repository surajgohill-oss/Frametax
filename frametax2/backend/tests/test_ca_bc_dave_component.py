"""
test_ca_bc_dave_component.py

Codex canonical identity/authority cleanup (Phase 3, BC DAVE) — British
Columbia's Digital Animation, Visual Effects and Post-Production (DAVE)
16% credit is bound to real, canonical, labour-category-classified
budget lines (never generic BC/Canadian QPE), using the SAME generic
component-basis reconciliation mechanism already built and proven this
session for South Africa's post/VFX QSAPPE and Oregon's payroll/other
split.
"""
from __future__ import annotations

import pytest

from app.calculators.allocation_pricing import price_segment
from app.calculators.production_allocation import AccountAllocation, AssignmentKind


def _alloc(component, spend_category, amount, line_id):
    return AccountAllocation(
        account_code="1000", description=f"BC {spend_category}", amount_usd=amount,
        component=component, jurisdiction_code="CA-BC", assignment_kind=AssignmentKind.FIXED,
        rationale="DAVE component test", governing_decision="codex-canonical-identity-cleanup",
        line_id=line_id, spend_category=spend_category,
    )


def test_generic_labor_without_activity_confirmation_never_receives_dave():
    """Real qualified BC labour lines exist, but the DAVE-eligible
    activity fact is not evidenced -- must remain conditional, never
    price."""
    alloc = [_alloc("post", "btl_crew_labor", 500_000.0, "labour-1")]
    result = price_segment(
        jurisdiction_code="CA-BC", program_slug="ca_bc_dave", allocations=alloc,
        spend_category_by_code={"1000": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=500_000.0,
    )
    assert result.executable is False, "no evidenced DAVE-eligible activity fact -- must remain conditional"


def test_qualified_bc_labour_with_eligible_activity_reaches_component_calculation():
    """Real qualified BC labour lines + evidenced eligible DAVE activity
    fact -- must price 16% of the exact traced labour subtotal."""
    alloc = [
        _alloc("post", "btl_crew_labor", 500_000.0, "labour-1"),
        _alloc("vfx", "atl_director", 100_000.0, "labour-2"),
    ]
    result = price_segment(
        jurisdiction_code="CA-BC", program_slug="ca_bc_dave", allocations=alloc,
        spend_category_by_code={"1000": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=600_000.0,
        evidenced_requirement_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"}),
    )
    assert result.executable is True, f"blockers={result.blockers}"
    # 16% of the exact traced labour subtotal (500,000 + 100,000 = 600,000).
    assert result.incentive_floor_usd == pytest.approx(96_000.0, abs=0.01)


def test_generic_non_labor_bc_spend_never_receives_dave_percentage():
    """Real BC spend that is NOT a labour category (e.g. equipment/
    location) must never contribute to the DAVE 16% basis -- generic BC/
    Canadian QPE must never receive the DAVE percentage."""
    alloc = [_alloc("post", "general_administration", 1_000_000.0, "nonlabour-1")]
    result = price_segment(
        jurisdiction_code="CA-BC", program_slug="ca_bc_dave", allocations=alloc,
        spend_category_by_code={"1000": "general_administration"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=1_000_000.0,
        evidenced_requirement_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"}),
    )
    assert result.executable is False, (
        "non-labour BC spend has no real qualifying labour subtotal (0) -- must remain "
        "conditional, never price against generic BC spend"
    )


def test_asserted_labour_basis_mismatching_real_lines_rejects():
    """A caller-asserted labour basis with no exact relationship to the
    real traced labour lines must reject before pricing -- never accepted
    as an unreconciled scalar."""
    alloc = [_alloc("post", "btl_crew_labor", 500_000.0, "labour-1")]
    result = price_segment(
        jurisdiction_code="CA-BC", program_slug="ca_bc_dave", allocations=alloc,
        spend_category_by_code={"1000": "btl_crew_labor"}, offshore_payroll_accounts=frozenset(),
        production_type="feature_film", gross_budget_usd=500_000.0,
        amount_facts={"ca_bc_dave_qualified_labour_usd": 5_000_000.0},
        evidenced_requirement_facts=frozenset({"ca_bc_dave_eligible_activity_confirmed"}),
    )
    assert result.executable is False, "an asserted basis mismatching the real labour lines must reject"
