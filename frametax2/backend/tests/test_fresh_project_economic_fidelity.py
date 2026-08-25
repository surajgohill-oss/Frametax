"""
test_fresh_project_economic_fidelity.py

Fresh Project Economic Fidelity closeout — runtime reconciliation against
the real Lips Like Sugar production (v7LLS_RevBudget_T1B_27days_022524.pdf).

Real defect found and fixed this pass: _REBATE_EXCLUSION_RE (budget_parser.py)
already excluded "tax credit"/"incentive rebate"/"EDB rebate"/"net total"
netting lines as budget assumptions, not real spend, but did not match
"tax incentive" -- Lips Like Sugar's own real "9998 - Tax Incentive 25%*
BTL (No Disc)" ($1,503,074) netting line ahead of its stated "Net total".
That line was being parsed as a real, negative, QUALIFIES-eligible BTL
account and subtracted directly from whichever jurisdiction a candidate
priced -- a real QPE/incentive/NPC distortion. Generic fix: "tax incentive"
added to the same existing exclusion pattern (test_movie_magic_budget_
parser.py::TestTaxIncentiveNettingLineExclusion covers the parser unit
behavior directly). This file proves the fix end-to-end against the real,
already-ingested production and its real canonical optimizer output --
not a synthetic fixture.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_allocation import StructureSpec, derive_account_allocation
from app.db.session import engine
from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.production import StructureCalculationResult
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_project_economics import build_project_economic_inputs

LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def test_monetary_line_population_positive_and_no_stale_rebate_line(db: AsyncSession):
    doc = (await db.execute(
        select(BudgetDocument).where(BudgetDocument.project_id == LIPS_LIKE_SUGAR_PROJECT_ID)
    )).scalars().first()
    assert doc is not None
    lines = (await db.execute(
        select(BudgetLineItem).where(BudgetLineItem.budget_document_id == doc.id)
    )).scalars().all()
    assert len(lines) > 0
    # the real production's own document Grand Total, unchanged by this fix
    assert float(doc.total_budget_raw) == 11_983_654.00
    # the fixed rebate-exclusion regex must keep the netting line out —
    # no real budget account should carry a negative amount here
    assert all(float(l.amount_usd or 0) >= 0 for l in lines)


async def test_source_and_canonical_conservation_reconcile_exactly(db: AsyncSession):
    result = await build_project_economic_inputs(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    assert result.ok
    inputs = result.inputs
    assert inputs.gross_budget_usd == 11_983_654.00
    # canonical leaf sum must equal the document's own stated Grand Total —
    # no line lost, no rebate-assumption line masquerading as spend
    assert inputs.leaf_account_sum_usd == inputs.gross_budget_usd
    assert round(sum(l.amount_usd for l in inputs.budget_lines), 2) == inputs.gross_budget_usd


async def test_allocation_conserves_for_a_single_jurisdiction_structure(db: AsyncSession):
    result = await build_project_economic_inputs(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    inputs = result.inputs
    spec = StructureSpec(
        structure_id="FIDELITY-TEST-SA", structure_type="full_relocation", label="fidelity test",
        primary_jurisdiction="SA", participants=("SA",),
        incentive_programs={"SA": "sa_film_commission_rebate"},
    )
    allocation = derive_account_allocation(
        lines=inputs.budget_lines, spend_category_by_code=inputs.spend_category_by_code,
        spec=spec, stated_outside_accounts=inputs.accounts_outside_jurisdiction,
    )
    assert allocation.conserves
    assert allocation.is_complete
    assert allocation.duplicate_account_codes == ()
    assert allocation.total_allocated_usd == allocation.total_budget_lines_usd == inputs.gross_budget_usd


async def test_fresh_project_priced_and_top_scenario_fully_attributable(db: AsyncSession):
    result = await evaluate_project(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")
    assert result["priced_count"] > 0

    top = result["top_result"]
    assert top is not None
    assert top["candidate_status"] == "PRICED"

    row = (await db.execute(
        select(StructureCalculationResult)
        .where(StructureCalculationResult.structure_id == top["structure_id"])
        .order_by(StructureCalculationResult.created_at.desc())
    )).scalars().first()
    assert row is not None
    segments = row.calculation_trace_json["segments"]
    assert len(segments) > 0  # at least one priced program

    # program-level incentive sum must equal the reported structure incentive
    program_incentive_sum = round(sum(s["incentive_floor_usd"] for s in segments), 2)
    assert program_incentive_sum == round(top["total_incentive_value_usd"], 2)

    # every qualification_trace amount across every segment must reconcile
    # to the same gross budget — no leaf line lost or double-counted across
    # segments
    all_trace_amounts = sum(
        q["amount_usd"] for s in segments for q in s["qualification_trace"]
    )
    assert round(all_trace_amounts, 2) == result["gross_budget_usd"]

    # NPC arithmetic reconciles with zero unexplained residual (single-
    # jurisdiction full-relocation candidates carry no other cost delta)
    if len(segments) == 1 and not top.get("relocation_cost_normalized"):
        expected_npc = round(result["gross_budget_usd"] - top["total_incentive_value_usd"], 2)
        assert round(top["true_net_cost_usd"], 2) == expected_npc
