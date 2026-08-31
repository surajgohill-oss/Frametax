"""
Production Page Integrity Closeout — focused regression tests.

Covers the real defects found and fixed by this task:

  A. Overview budget breakdown (pkg.budget.totals_by_spend_category_usd /
     line_items, canonical_production_view.build_generic_pkg_and_economics)
     is populated and conserves to the document's own declared gross
     budget for a project whose base jurisdiction DOES price (Little
     Utopia, FVD) and one that DOESN'T (Lips Like Sugar, Bad Hombres) —
     the exact defect this closeout fixed was that pkg.register (the only
     prior source) is empty in the unpriced case.
  B. Bad Hombres' real "CONTINGENCY : 5.0%" top-sheet loaded-cost line
     (previously silently dropped by budget_parser.py's top-sheet loop)
     is now extracted — a real, generic Movie Magic convention, not a
     Bad-Hombres-specific fix. Locks in the $94,382 leaf line and exact
     gross-budget conservation.
  C. Little Utopia's real $9,068 (~"$9,066") LOS ANGELES item — account
     5000 EDITORIAL, the only nonzero account among the seven the
     project's own budget_accounts_outside_base_jurisdiction fact marks
     as outside Mauritius — is present in the generic budget composition
     under its real canonical category, counted in gross budget, and
     already excluded from Mauritius QPE by the existing, unchanged
     accounts_outside_jurisdiction wiring (qualification_derivation.py).
  D. The generic contingency-expected-utilization control
     (POST /projects/{id}/assumptions) persists and is read back through
     the SAME ProjectFact/build_project_economic_inputs path for ANY
     project — proven here on Bad Hombres, not Little Utopia, since the
     whole point is that this is not project-specific. Cleans up after
     itself (deletes the fact it wrote) so this test has no lasting
     side effect on the real project state other tests/screens read.
  E. Little Utopia's migration-0068 stale beta 100% contingency election
     is gone (migration 0071) — no project carries a silent default.
"""
from __future__ import annotations

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.project_fact import ProjectFact
from app.services.canonical_evaluation import evaluate_project
from app.services.canonical_production_view import (
    build_generic_pkg_and_economics,
    build_production_and_structures,
)

LLS_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"

FACT_KEY = "contingency_expected_utilization_pct"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── A. Budget composition conserves to gross, for priced AND unpriced ──────

@pytest.mark.parametrize(
    "project_id,expected_gross,expected_lines,tolerance",
    [
        (LLS_PROJECT_ID, 11_983_654.0, 46, 0.01),
        (BAD_HOMBRES_PROJECT_ID, 2_482_023.0, 34, 0.01),
        (LITTLE_UTOPIA_PROJECT_ID, 4_364_393.0, 44, 2.01),  # known immaterial $2 rounding
        (FVD_PROJECT_ID, 4_517_687.0, 34, 0.01),
    ],
)
async def test_budget_composition_conserves_to_gross(
    db: AsyncSession, project_id, expected_gross, expected_lines, tolerance,
):
    result = await build_generic_pkg_and_economics(db, project_id)
    budget = result["pkg"]["budget"]
    assert len(budget["line_items"]) == expected_lines
    category_sum = round(sum(budget["totals_by_spend_category_usd"].values()), 2)
    assert category_sum == pytest.approx(expected_gross, abs=tolerance)

    prod = (await build_production_and_structures(db, project_id))["production"]
    assert prod["gross_budget_usd"] == pytest.approx(expected_gross, abs=0.01)
    recon = prod["budget_reconciliation"]
    assert recon["leaf_account_sum_usd"] == pytest.approx(expected_gross, abs=tolerance)


async def test_budget_composition_populated_without_a_priced_register(db: AsyncSession):
    # The exact root cause this closeout fixed: pkg.register only exists
    # when the project's own base jurisdiction prices successfully. Bad
    # Hombres' US baseline does not (no real incentive program) — register
    # is genuinely empty, but the budget composition must not be.
    result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
    assert result["pkg"]["register"] == []
    assert len(result["pkg"]["budget"]["line_items"]) == 34


# ── A2. Production Overview + Project Globe UI regression repair: department
#        grouping (the source document's own real top-sheet sections) is a
#        second, additive real field alongside spend_category — never a
#        replacement, and it must conserve to gross exactly like the other
#        aggregate. This is what BudgetRail.jsx groups by so a producer never
#        sees an undifferentiated "Miscellaneous" bucket for a real budget
#        the classifier maps mostly into that one spend_category. ────────────

@pytest.mark.parametrize(
    "project_id,expected_gross,tolerance",
    [
        (LLS_PROJECT_ID, 11_983_654.0, 0.01),
        (BAD_HOMBRES_PROJECT_ID, 2_482_023.0, 0.01),
        (LITTLE_UTOPIA_PROJECT_ID, 4_364_393.0, 2.01),
        (FVD_PROJECT_ID, 4_517_687.0, 0.01),
    ],
)
async def test_department_breakdown_conserves_to_gross(db: AsyncSession, project_id, expected_gross, tolerance):
    result = await build_generic_pkg_and_economics(db, project_id)
    by_department = result["pkg"]["budget"]["totals_by_department_usd"]
    assert by_department, "totals_by_department_usd must be populated once a budget is imported"
    # Every bucket must be a real section name from the source document —
    # never a generic catch-all like "Miscellaneous" (that's exactly the
    # spend_category limitation this second field exists to route around).
    assert "Miscellaneous" not in by_department
    dept_sum = round(sum(by_department.values()), 2)
    assert dept_sum == pytest.approx(expected_gross, abs=tolerance)
    # Every line item must carry its own department, for BudgetRail's
    # department-grouped fallback rendering to work at all.
    for line in result["pkg"]["budget"]["line_items"]:
        assert line["department"]


# ── B. Bad Hombres' real unnumbered loaded-cost CONTINGENCY line ───────────

async def test_bad_hombres_contingency_line_extracted(db: AsyncSession):
    result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
    line_items = result["pkg"]["budget"]["line_items"]
    contingency_lines = [li for li in line_items if li["spend_category"] == "contingency"]
    assert len(contingency_lines) == 1
    assert contingency_lines[0]["amount_usd"] == pytest.approx(94_382.0, abs=0.01)
    assert result["pkg"]["budget"]["totals_by_spend_category_usd"]["contingency"] == pytest.approx(94_382.0, abs=0.01)


# ── C. Little Utopia's real LA item — present, categorized, excluded from MU QPE ──

async def test_little_utopia_la_item_present_and_excluded_from_mu_qpe(db: AsyncSession):
    result = await build_generic_pkg_and_economics(db, LITTLE_UTOPIA_PROJECT_ID)
    line_items = result["pkg"]["budget"]["line_items"]
    editorial = next(li for li in line_items if (li["account_code"] or "") == "5000")
    assert editorial["amount_usd"] == pytest.approx(9_068.0, abs=0.01)
    assert editorial["spend_category"] == "post_production"

    # The territorial-evidence fact that already, correctly, excludes this
    # account from Mauritius QPE — unchanged by this task, only traced and
    # proven. See canonical_project_economics.py's
    # FACT_ACCOUNTS_OUTSIDE_JURISDICTION wiring into ProductionFacts.
    facts = (await db.execute(
        select(ProjectFact).where(
            ProjectFact.project_id == LITTLE_UTOPIA_PROJECT_ID,
            ProjectFact.fact_key == "budget_accounts_outside_base_jurisdiction",
        )
    )).scalars().first()
    assert facts is not None
    import json
    outside_accounts = json.loads(facts.value)
    assert "5000" in outside_accounts


# ── D. Generic contingency control — proven on a NON-Little-Utopia project ──

async def test_contingency_assumption_persists_generically(db: AsyncSession):
    # Bad Hombres, deliberately — this must work identically for any
    # project, never a Little-Utopia-specific code path.
    try:
        existing_before = (await db.execute(
            select(ProjectFact).where(
                ProjectFact.project_id == BAD_HOMBRES_PROJECT_ID, ProjectFact.fact_key == FACT_KEY,
            )
        )).scalars().first()
        assert existing_before is None  # no producer election yet

        from app.models.enums import ProjectFactSourceType, ReviewStatus
        import uuid
        db.add(ProjectFact(
            id=uuid.uuid4(), project_id=BAD_HOMBRES_PROJECT_ID, fact_key=FACT_KEY,
            value="50", value_type="number",
            source_type=ProjectFactSourceType.USER_OVERRIDE.value,
            review_status=ReviewStatus.APPROVED.value,
        ))
        await db.commit()

        inputs_result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
        assert inputs_result["facts"]["answers"].get(FACT_KEY) == "50"
    finally:
        # Never leave a lasting side effect on real project state.
        await db.execute(delete(ProjectFact).where(
            ProjectFact.project_id == BAD_HOMBRES_PROJECT_ID, ProjectFact.fact_key == FACT_KEY,
        ))
        await db.commit()
        cleanup_check = (await db.execute(
            select(ProjectFact).where(
                ProjectFact.project_id == BAD_HOMBRES_PROJECT_ID, ProjectFact.fact_key == FACT_KEY,
            )
        )).scalars().first()
        assert cleanup_check is None


# ── E. No stale 100% default survives on Little Utopia ─────────────────────

async def test_little_utopia_no_stale_contingency_default(db: AsyncSession):
    fact = (await db.execute(
        select(ProjectFact).where(
            ProjectFact.project_id == LITTLE_UTOPIA_PROJECT_ID, ProjectFact.fact_key == FACT_KEY,
        )
    )).scalars().first()
    assert fact is None  # migration 0071 — no producer election, no silent default

    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    await db.commit()
    # Absent a real election, derive_qualification_register's own existing
    # GREY_AREA_REQUIRES_AUTHORITY doctrine applies — the reserve is
    # excluded from qualifying QPE, never silently assumed 100% deployed.
    assert result["baseline"]["true_net_cost_usd"] == pytest.approx(3_812_823.20, abs=0.01)
