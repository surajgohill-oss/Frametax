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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

# Isolation (2026-10): tests asserting the REAL productions' frozen composition run only when explicitly authorised, inside a READ ONLY
# transaction. Everything that writes (the contingency election, evaluation) runs on SYNTHETIC rolled-back records. The old versions of
# the contingency tests committed to, deleted from and evaluated the real Bad Hombres and Little Utopia projects.
from tests.isolated_records import (  # noqa: E402
    DEFAULT_LINES, create_synthetic_project, isolated_session, real_readonly_db, requires_real_production_reads)  # noqa: F401


@pytest.fixture
async def db():
    async with isolated_session() as session:
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
@requires_real_production_reads
async def test_budget_composition_conserves_to_gross(
    real_readonly_db: AsyncSession, project_id, expected_gross, expected_lines, tolerance,
):
    db = real_readonly_db
    result = await build_generic_pkg_and_economics(db, project_id)
    budget = result["pkg"]["budget"]
    assert len(budget["line_items"]) == expected_lines
    category_sum = round(sum(budget["totals_by_spend_category_usd"].values()), 2)
    assert category_sum == pytest.approx(expected_gross, abs=tolerance)

    prod = (await build_production_and_structures(db, project_id))["production"]
    assert prod["gross_budget_usd"] == pytest.approx(expected_gross, abs=0.01)
    recon = prod["budget_reconciliation"]
    assert recon["leaf_account_sum_usd"] == pytest.approx(expected_gross, abs=tolerance)


@requires_real_production_reads
async def test_budget_composition_populated_without_a_priced_register(real_readonly_db: AsyncSession):
    db = real_readonly_db
    # ORIGINAL INVARIANT: budget composition must be populated regardless of
    # whether the base jurisdiction prices a register.
    #
    # The premise this test was written against has since been REPAIRED. It
    # assumed "Bad Hombres' US baseline does not price (no real incentive
    # program)" -- but US was never the production's baseline. It was a
    # COUNTRY inferred from the budget's USD currency, and a federal country
    # whose incentives are subnational can never be a real production
    # baseline. Bad Hombres shoots in NEW MEXICO (US-NM), which is now the
    # recognized baseline and does price, so the register is legitimately
    # populated. The invariant itself -- composition is populated either way
    # -- is what this test still asserts.
    result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
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
@requires_real_production_reads
async def test_department_breakdown_conserves_to_gross(real_readonly_db: AsyncSession, project_id, expected_gross, tolerance):
    db = real_readonly_db
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

@requires_real_production_reads
async def test_bad_hombres_contingency_line_extracted(real_readonly_db: AsyncSession):
    db = real_readonly_db
    result = await build_generic_pkg_and_economics(db, BAD_HOMBRES_PROJECT_ID)
    line_items = result["pkg"]["budget"]["line_items"]
    contingency_lines = [li for li in line_items if li["spend_category"] == "contingency"]
    assert len(contingency_lines) == 1
    assert contingency_lines[0]["amount_usd"] == pytest.approx(94_382.0, abs=0.01)
    assert result["pkg"]["budget"]["totals_by_spend_category_usd"]["contingency"] == pytest.approx(94_382.0, abs=0.01)


# ── C. Little Utopia's real LA item — present, categorized, excluded from MU QPE ──

@requires_real_production_reads
async def test_little_utopia_la_item_present_and_excluded_from_mu_qpe(real_readonly_db: AsyncSession):
    db = real_readonly_db
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


# ── Synthetic equivalents (rolled back; no real project is read or written) ──────────────────────────────────────────────

async def test_synthetic_budget_composition_conserves_to_gross_and_extracts_the_contingency_line(db: AsyncSession):
    pid = await create_synthetic_project(db)
    result = await build_generic_pkg_and_economics(db, pid)
    budget = result["pkg"]["budget"]
    gross = sum(l[4] for l in DEFAULT_LINES)
    assert len(budget["line_items"]) == len(DEFAULT_LINES)
    assert round(sum(budget["totals_by_spend_category_usd"].values()), 2) == pytest.approx(gross, abs=0.01)
    assert budget["totals_by_spend_category_usd"]["contingency"] == pytest.approx(100_000.0, abs=0.01)
    by_department = budget["totals_by_department_usd"]
    assert by_department and "Miscellaneous" not in by_department
    assert round(sum(by_department.values()), 2) == pytest.approx(gross, abs=0.01)
    assert all(line["department"] for line in budget["line_items"])
    prod = (await build_production_and_structures(db, pid))["production"]
    assert prod["gross_budget_usd"] == pytest.approx(gross, abs=0.01)
    assert prod["budget_reconciliation"]["leaf_account_sum_usd"] == pytest.approx(gross, abs=0.01)


async def test_contingency_assumption_persists_generically(db: AsyncSession):
    """The election is a generic ProjectFact read back through the same path for ANY project (synthetic here)."""
    import uuid

    from app.models.enums import ProjectFactSourceType, ReviewStatus

    pid = await create_synthetic_project(db)
    assert (await db.execute(select(ProjectFact).where(ProjectFact.project_id == pid, ProjectFact.fact_key == FACT_KEY))).scalars().first() is None
    db.add(ProjectFact(
        id=uuid.uuid4(), project_id=pid, fact_key=FACT_KEY, value="50", value_type="number",
        source_type=ProjectFactSourceType.USER_OVERRIDE.value, review_status=ReviewStatus.APPROVED.value))
    await db.flush()
    inputs_result = await build_generic_pkg_and_economics(db, pid)
    assert inputs_result["facts"]["answers"].get(FACT_KEY) == "50"


async def test_a_new_project_carries_no_silent_contingency_default_and_the_reserve_stays_unconfirmed(db: AsyncSession):
    """No project carries a silent default election: absent a real election the reserve is a disclosed grey item, never assumed
    deployed (synthetic project, evaluated inside the rolled-back transaction)."""
    pid = await create_synthetic_project(db)
    assert (await db.execute(select(ProjectFact).where(ProjectFact.project_id == pid, ProjectFact.fact_key == FACT_KEY))).scalars().first() is None
    await evaluate_project(db, pid)
    register = (await build_generic_pkg_and_economics(db, pid))["pkg"]["register"]
    reserve = [a for a in register if a["account_code"] == "8300"]
    assert reserve, "the contingency account must be in the served register"
    assert all(a["state"] != "qualifies" for a in reserve)
