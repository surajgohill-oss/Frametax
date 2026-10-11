"""Project-level contingency election -> planned cost and NPC (original gross and reserve preserved; no double counting).

SYNTHETIC ONLY: the Little Utopia fixture module (no database, no evaluation, no persisted generation). Expectations are closed
forms over the fixture's reserve: planned cost = gross - reserve x (1 - utilization); the jurisdiction QPE rules separately decide
what part of the DEPLOYED reserve qualifies; the NPC cost reduction is applied exactly once and never changes QPE or incentive."""
from __future__ import annotations

import pathlib
import re

import pytest

from app.calculators.allocation_pricing import price_allocated_structure
from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.calculators.qualification_derivation import BudgetLine
from app.data.little_utopia_real_budget import (
    AUTHORITATIVE_GROSS_BUDGET_USD as GROSS, LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU, LITTLE_UTOPIA_REAL_BUDGET_LINES,
    LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL, LITTLE_UTOPIA_REAL_SPEND_CATEGORY)
from app.services.canonical_project_economics import ProjectEconomicInputs, contingency_planning_view

LINES = [BudgetLine(account_code=c, description=d, amount_usd=a, spend_category=LITTLE_UTOPIA_REAL_SPEND_CATEGORY.get(c), is_memo=False)
         for c, d, a, _p in LITTLE_UTOPIA_REAL_BUDGET_LINES]
RESERVE = round(sum(l.amount_usd for l in LINES if l.spend_category == "contingency"), 2)
SPEC = StructureSpec(structure_id="P-BASE-MU", structure_type="single_country", label="base", primary_jurisdiction="MU",
                     participants=("MU",), incentive_programs={"MU": "mu_edb_incentive"})


def _price(pct, reduction):
    allocation = derive_account_allocation(lines=LINES, spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY, spec=SPEC,
                                           stated_outside_accounts=LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU)
    return price_allocated_structure(
        spec=SPEC, allocation=allocation, spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY,
        offshore_payroll_accounts=LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL, gross_budget_usd=GROSS,
        contingency_expected_utilization_pct=pct, planned_cost_reduction_usd=reduction)


def _inputs(pct):
    return ProjectEconomicInputs(
        project_id="synthetic", project_name="Synthetic", jurisdiction_code="MU", production_type="feature_film",
        gross_budget_usd=GROSS, leaf_account_sum_usd=GROSS, budget_lines=LINES,
        spend_category_by_code=LITTLE_UTOPIA_REAL_SPEND_CATEGORY, accounts_outside_jurisdiction=frozenset(),
        offshore_payroll_accounts=frozenset(), contingency_expected_utilization_pct=pct, contingency_reserve_usd=RESERVE)


def test_planned_cost_basis_follows_the_election_and_never_rewrites_gross_or_the_reserve():
    assert RESERVE > 0
    unset = _inputs(None)
    assert unset.contingency_planned_reduction_usd == 0.0 and unset.npc_basis_usd == GROSS      # unknown is not 0% or 100%
    assert _inputs(100.0).contingency_planned_reduction_usd == 0.0
    assert _inputs(0.0).contingency_planned_reduction_usd == pytest.approx(RESERVE)
    half = _inputs(50.0)
    assert half.contingency_planned_reduction_usd == pytest.approx(RESERVE / 2, abs=0.01)
    assert half.npc_basis_usd == pytest.approx(GROSS - RESERVE / 2, abs=0.01)
    assert half.gross_budget_usd == GROSS and half.contingency_reserve_usd == RESERVE


def test_npc_moves_by_exactly_the_undeployed_reserve_and_qpe_and_incentive_are_untouched_by_it():
    pct = 50.0
    k = round(RESERVE * (1 - pct / 100), 2)
    without, with_k = _price(pct, 0.0), _price(pct, k)
    assert with_k.npc_with_adjustments_usd == pytest.approx(without.npc_with_adjustments_usd - k, abs=0.01)   # applied once
    assert with_k.npc_verified_usd == pytest.approx(without.npc_verified_usd - k, abs=0.01)
    assert with_k.npc_conservative_usd == pytest.approx(without.npc_conservative_usd - k, abs=0.01)
    assert with_k.selected_incentive_usd == without.selected_incentive_usd                                    # cost basis != QPE
    assert [s.qpe_usd for s in with_k.segments] == [s.qpe_usd for s in without.segments]
    assert with_k.gross_budget_usd == GROSS and with_k.planned_cost_reduction_usd == k                         # gross preserved


def test_the_jurisdiction_rule_applies_separately_to_the_deployed_share_without_double_counting():
    # MU qualifies the contingency category, so the deployed share is QPE while the undeployed share leaves the planned cost.
    full, half, none = (_price(p, round(RESERVE * (1 - p / 100), 2)) for p in (100.0, 50.0, 0.0))
    qpe = lambda r: sum(s.qpe_usd for s in r.segments)
    assert qpe(full) - qpe(half) == pytest.approx(RESERVE / 2, abs=0.02) and qpe(half) - qpe(none) == pytest.approx(RESERVE / 2, abs=0.02)
    # NPC change from 100% -> 50% = +undeployed cost saving and -lost incentive on that QPE; each counted once.
    rate = (full.selected_incentive_usd - half.selected_incentive_usd) / (qpe(full) - qpe(half))
    expected = -(RESERVE / 2) + rate * (RESERVE / 2)
    assert half.npc_with_adjustments_usd - full.npc_with_adjustments_usd == pytest.approx(expected, abs=0.05)


def test_served_planning_view_states_election_not_stated_and_no_reserve():
    elected = contingency_planning_view(GROSS, RESERVE, 25)
    assert elected["state"] == "ELECTED" and elected["original_gross_usd"] == GROSS
    assert elected["undeployed_reserve_usd"] == pytest.approx(RESERVE * 0.75, abs=0.01)
    assert elected["planned_cost_usd"] == pytest.approx(GROSS - RESERVE * 0.75, abs=0.01)
    unset = contingency_planning_view(GROSS, RESERVE, None)
    assert unset["state"] == "NOT_STATED" and unset["planned_cost_usd"] == GROSS and unset["undeployed_reserve_usd"] is None
    assert contingency_planning_view(GROSS, 0.0, 50)["state"] == "NO_RESERVE"


def test_no_canonical_npc_derivation_still_starts_from_original_gross():
    src = (pathlib.Path(__file__).parents[1] / "app/services/canonical_evaluation.py").read_text()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert not re.search(r"npc\w* = round\(inputs\.gross_budget_usd - ", code)
    assert code.count("planned_cost_reduction_usd=inputs.contingency_planned_reduction_usd") == 9   # 6 pricing + 3 hybrid generator
    gen = (pathlib.Path(__file__).parents[1] / "app/calculators/structural_archetype_generator.py").read_text()
    assert "npc = round(gross_budget_usd - planned_cost_reduction_usd - total_guaranteed, 2)" in gen
    assert gen.count("planned_cost_reduction_usd") >= 6      # both entry points carry and forward it


# ── save / reload / reset of the saved election (synthetic project inside a rolled-back transaction) ──────────────────────
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.api.v1.cineglobe import ProjectAssumptions, post_project_assumptions  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.project import Project  # noqa: E402
from app.models.project_fact import ProjectFact  # noqa: E402
from app.services.canonical_project_economics import FACT_CONTINGENCY_EXPECTED_UTILIZATION_PCT, _fact_float  # noqa: E402

ORG_ID = "11381771-5b1c-4980-9117-e3e47a4cb354"


@pytest.fixture
async def synthetic_project_session():
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        project = Project(title="SYNTHETIC contingency control (rolled back)", organization_id=ORG_ID)
        session.add(project)
        await session.flush()
        try:
            yield session, project
        finally:
            await session.close()
            await outer.rollback()           # nothing from this test is ever committed


async def _reload(session, project_id):
    rows = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id))).scalars().all()
    return _fact_float(rows, FACT_CONTINGENCY_EXPECTED_UTILIZATION_PCT)


async def test_the_saved_election_reloads_resets_and_rejects_out_of_range_values(synthetic_project_session):
    session, project = synthetic_project_session
    assert await _reload(session, project.id) is None                                       # nothing stated
    await post_project_assumptions(str(project.id), ProjectAssumptions(answers={"contingency_expected_utilization_pct": 50}), session)
    assert await _reload(session, project.id) == 50.0                                       # saved and read back by the canonical reader
    await post_project_assumptions(str(project.id), ProjectAssumptions(answers={"contingency_expected_utilization_pct": 0}), session)
    assert await _reload(session, project.id) == 0.0                                        # 0% is a real election, not "unset"
    with pytest.raises(HTTPException) as bad:
        await post_project_assumptions(str(project.id), ProjectAssumptions(answers={"contingency_expected_utilization_pct": 150}), session)
    assert bad.value.status_code == 400 and await _reload(session, project.id) == 0.0       # rejected, prior value kept
    await post_project_assumptions(str(project.id), ProjectAssumptions(answers={"contingency_expected_utilization_pct": None}), session)
    assert await _reload(session, project.id) is None                                       # reset restores the unstated state


def test_a_flagged_item_serves_its_source_value_unresolved_reason_and_needed_evidence_in_the_trace():
    from app.calculators.allocation_pricing import price_segment
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    import app.data.program_rate_rules_worldwide  # noqa: F401
    alloc = [AccountAllocation(account_code=c, description=d, amount_usd=a, component="production", jurisdiction_code="GR",
                               assignment_kind=AssignmentKind.FIXED, rationale="x", governing_decision="x", line_id=f"L{c}", spend_category=k)
             for c, d, a, k in [("3100", "CAMERA", 1_000_000.0, "btl_crew_labor"), ("7902", "CONTINGENCY", 250_000.0, "contingency")]]
    seg = price_segment(jurisdiction_code="GR", program_slug="gr_cash_rebate", allocations=alloc,
                        spend_category_by_code={"3100": "btl_crew_labor", "7902": "contingency"}, offshore_payroll_accounts=frozenset(),
                        production_type="feature_film", gross_budget_usd=2_000_000.0, contingency_expected_utilization_pct=100.0)
    (row,) = [t for t in seg.register_trace if t["account_code"] == "7902"]
    assert row["state"] == "grey_area_requires_authority" and row["amount_usd"] == 250_000.0      # source value, not eligible by default
    assert row["line_id"] == "L7902" and row["grey_reason"] == "missing_production_fact"
    assert "gr_action_a_applicant_evidenced" in row["resolving_evidence"]                       # the evidence that would settle it
