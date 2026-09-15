"""
Claude-owned permanent tests — CLAUDE_FINAL_ACTIVE_OPTIMIZER_IMPLEMENTATION_AND_RUNTIME_CLOSEOUT.

Proves the two new, additive pieces this workstream implements:
  - compute_anchor_budget_contract() — the Anchor Budget Contract (Section
    A): a real, separate reference calculation, never a candidate
    structure, reconciling any real supplied/embedded incentive budget
    line against the canonical anchor incentive.
  - the $100,000 hybrid-recommendation materiality threshold (Section
    B/E), computed once, post-hoc, over every served structure's own real
    net cost against the project's own real anchor NPC.

Both are proven against all four real, stored productions -- no synthetic
project, no invented fact.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_production_view import (
    build_production_and_structures,
    compute_anchor_budget_contract,
)

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"
ALL_FOUR = {
    "Little Utopia": LITTLE_UTOPIA_PROJECT_ID,
    "F#K Valentine's Day": FVD_PROJECT_ID,
    "Bad Hombres": BAD_HOMBRES_PROJECT_ID,
    "Lips Like Sugar": LIPS_LIKE_SUGAR_PROJECT_ID,
}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ---------------------------------------------------------------------------
# A — Anchor Budget Contract
# ---------------------------------------------------------------------------

async def test_anchor_budget_contract_matches_the_real_baseline_for_all_four_productions(db: AsyncSession):
    """The anchor contract's own calculated_anchor_incentive_usd/
    anchor_npc_usd must be byte-identical to every prior workstream's
    frozen baseline values -- it is a re-presentation of the SAME real
    baseline row, never a second calculation."""
    expected = {
        LITTLE_UTOPIA_PROJECT_ID: (573059.70, 3791333.30),
        FVD_PROJECT_ID: (1445659.84, 3072027.16),
        BAD_HOMBRES_PROJECT_ID: (596910.25, 1885112.75),
        LIPS_LIKE_SUGAR_PROJECT_ID: (3459278.90, 8524375.10),
    }
    for pid, (incentive, npc) in expected.items():
        contract = await compute_anchor_budget_contract(db, pid)
        assert contract["status"] == "OK"
        assert contract["calculated_anchor_incentive_usd"] == pytest.approx(incentive)
        assert contract["anchor_npc_usd"] == pytest.approx(npc)


async def test_anchor_budget_contract_never_reports_a_fabricated_variance_when_no_supplied_incentive_exists(db: AsyncSession):
    """None of the four real productions has a real spend_category=='incentive'
    budget line on file (confirmed by direct query) -- supplied_incentive_usd
    must be None, and variance_usd must ALSO be None (never computed as
    though a $0 supplied figure was found, which would silently misreport
    the full calculated incentive as a 'variance')."""
    for name, pid in ALL_FOUR.items():
        contract = await compute_anchor_budget_contract(db, pid)
        assert contract["supplied_incentive_usd"] is None, f"{name}: unexpected supplied incentive line found"
        assert contract["variance_usd"] is None, f"{name}: variance must be None with no supplied figure to reconcile against"


async def test_little_utopia_and_fvd_anchor_reports_their_own_real_unresolved_qualification_state(db: AsyncSession):
    """The anchor contract must expose the EXACT reason a project has no
    verified recommendation -- Little Utopia's real AUTHORITY_UNRESOLVED
    and FVD's real USER_FACT_REQUIRED cultural-test states, unchanged."""
    lu = await compute_anchor_budget_contract(db, LITTLE_UTOPIA_PROJECT_ID)
    assert lu["anchor_role_qualification_state"] == "AUTHORITY_UNRESOLVED"
    fvd = await compute_anchor_budget_contract(db, FVD_PROJECT_ID)
    assert fvd["anchor_role_qualification_state"] == "USER_FACT_REQUIRED"


async def test_anchor_contract_is_persisted_by_the_optimizer_not_recomputed_by_the_view(db: AsyncSession):
    """CLAUDE_CORRECT_FAILED_OPTIMIZER_CLOSEOUT, Section A — the anchor
    contract must be SOURCED inside canonical_evaluation.evaluate_project()
    (the optimizer's own evaluation path), never reconstructed by the
    served-view layer. Proven directly against the real, persisted
    StructureCalculationResult row: the baseline candidate's own
    calculation_trace_json carries a real, non-None anchor_contract dict
    with every required field, written at evaluation time -- not a
    presentation-layer fabrication. compute_anchor_budget_contract() is
    then proven to read this exact persisted dict verbatim (byte-identical
    values), never recomputing any of them."""
    from sqlalchemy import select as sa_select

    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint

    for pid in ALL_FOUR.values():
        fp = await current_generation_fingerprint(db, pid)
        row = (await db.execute(
            sa_select(StructureCalculationResult.calculation_trace_json)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(
                ProductionStructure.project_id == pid,
                StructureCalculationResult.engine_version == ENGINE_VERSION,
                StructureCalculationResult.input_fingerprint == fp,
                StructureCalculationResult.calculation_trace_json["is_baseline"].astext == "true",
            )
        )).scalar_one_or_none()
        assert row is not None, f"{pid}: no baseline row at the current fingerprint"
        engine_contract = row.get("anchor_contract")
        assert engine_contract is not None, f"{pid}: evaluate_project() did not persist an anchor_contract on its own baseline candidate"
        for key in ("gross_budget_usd", "supplied_incentive_usd", "calculated_anchor_incentive_usd",
                    "variance_usd", "financing_adjustment_usd", "anchor_npc_usd"):
            assert key in engine_contract

        view_contract = await compute_anchor_budget_contract(db, pid)
        assert view_contract["status"] == "OK"
        assert view_contract["gross_budget_usd"] == engine_contract["gross_budget_usd"]
        assert view_contract["calculated_anchor_incentive_usd"] == engine_contract["calculated_anchor_incentive_usd"]
        assert view_contract["anchor_npc_usd"] == engine_contract["anchor_npc_usd"]


async def test_supplied_incentive_budget_line_changes_the_fingerprint_and_forces_fresh_anchor_recompute(db: AsyncSession):
    """Required by this workstream: proves that changing an anchor-
    relevant fact (a real, producer-supplied incentive budget line)
    invalidates evaluate_project()'s own fingerprint and forces a fresh
    evaluation that recomputes the anchor_contract -- not a stale,
    reused row. Uses a real, temporary BudgetLineItem on Little Utopia's
    own real, current budget document, written and deleted within this
    test only; the project's real economics are restored exactly."""
    import uuid

    from sqlalchemy import delete as sa_delete
    from sqlalchemy import select as sa_select

    from app.models.budget import BudgetDocument, BudgetLineItem
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import current_generation_fingerprint, evaluate_project

    pid = LITTLE_UTOPIA_PROJECT_ID
    fp_before = await current_generation_fingerprint(db, pid)
    assert fp_before is not None

    doc_id = (await db.execute(
        sa_select(BudgetDocument.id).where(BudgetDocument.project_id == pid).limit(1)
    )).scalar_one_or_none()
    assert doc_id is not None, "Little Utopia must have a real budget document on file"

    line_id = uuid.uuid4()
    db.add(BudgetLineItem(
        id=line_id, budget_document_id=doc_id, department="TEST",
        description="Claude closeout fingerprint-sensitivity probe — deleted at test end",
        spend_category="incentive", amount_usd=1.0, amount_normalized=1.0, currency_code="USD",
    ))
    await db.commit()
    try:
        fp_with_supplied_line = await current_generation_fingerprint(db, pid)
        assert fp_with_supplied_line != fp_before, (
            "adding a real supplied-incentive budget line must change the evaluation fingerprint"
        )

        result = await evaluate_project(db, pid)
        assert result["status"] == "EVALUATION_COMPLETE"
        assert result["state_fingerprint"] == fp_with_supplied_line

        row = (await db.execute(
            sa_select(StructureCalculationResult.calculation_trace_json)
            .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
            .where(
                ProductionStructure.project_id == pid,
                StructureCalculationResult.input_fingerprint == fp_with_supplied_line,
                StructureCalculationResult.calculation_trace_json["is_baseline"].astext == "true",
            )
        )).scalar_one_or_none()
        assert row is not None
        assert row["anchor_contract"]["supplied_incentive_usd"] == pytest.approx(1.0)
    finally:
        await db.execute(sa_delete(BudgetLineItem).where(BudgetLineItem.id == line_id))
        await db.commit()
        fp_after = await current_generation_fingerprint(db, pid)
        assert fp_after == fp_before, "deleting the probe line must restore the original fingerprint exactly"


# ---------------------------------------------------------------------------
# B/E — $100,000 hybrid-recommendation materiality threshold
# ---------------------------------------------------------------------------

async def test_materiality_threshold_never_classifies_the_anchor_itself(db: AsyncSession):
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = [e for e in entries if e.get("is_baseline")]
    assert baseline
    for e in baseline:
        assert e["hybrid_recommendation_status"] == "NOT_APPLICABLE"
        assert e["net_benefit_vs_anchor_usd"] is None


async def test_materiality_threshold_real_distribution_across_all_categories(db: AsyncSession):
    """Real, live proof that all four required classification buckets
    genuinely occur for Little Utopia's real candidate universe -- not a
    synthetic scenario."""
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    statuses = {e.get("hybrid_recommendation_status") for e in entries}
    assert "ELIGIBLE_FOR_RECOMMENDATION" in statuses
    assert "ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED" in statuses
    assert "NOT_APPLICABLE" in statuses
    # every priced, non-baseline candidate's net benefit must equal
    # anchor_npc - candidate_npc exactly, using the SAME anchor value the
    # contract function itself reports.
    contract = await compute_anchor_budget_contract(db, LITTLE_UTOPIA_PROJECT_ID)
    anchor_npc = contract["anchor_npc_usd"]
    for e in entries:
        if e.get("is_baseline") or e.get("npc_verified_usd") is None:
            continue
        expected_benefit = round(anchor_npc - e["npc_verified_usd"], 2)
        assert e["net_benefit_vs_anchor_usd"] == pytest.approx(expected_benefit)
        if expected_benefit >= 100_000:
            assert e["hybrid_recommendation_status"] == "ELIGIBLE_FOR_RECOMMENDATION"
        else:
            assert e["hybrid_recommendation_status"] == "ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED"


async def test_uk_au_bilateral_conditional_structure_is_classified_material_never_a_recommendation(db: AsyncSession):
    """Little Utopia's real uk-au-bilateral conditional structure has a
    real ~$535K net benefit vs. the anchor -- comfortably material -- but
    must be labeled CONDITIONAL_MATERIAL, a DISTINCT status from
    ELIGIBLE_FOR_RECOMMENDATION, so nothing downstream can mistake a
    disclosed, producer-actionable assumption for a verified
    recommendation (Section D/E's own 'never auto-award' rule)."""
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    ukau = next(e for e in entries if e.get("treaty_slug") == "uk-au-bilateral")
    assert ukau["net_benefit_vs_anchor_usd"] is not None
    assert ukau["net_benefit_vs_anchor_usd"] > 100_000
    assert ukau["hybrid_recommendation_status"] == "CONDITIONAL_MATERIAL"
    assert ukau["hybrid_recommendation_status"] != "ELIGIBLE_FOR_RECOMMENDATION"


async def test_bad_hombres_and_lips_like_sugar_leading_structures_unaffected(db: AsyncSession):
    """Positive regression control: the new materiality/anchor-contract
    layer is purely additive and must not change either project's real
    leading structure or its economics."""
    expected = {
        BAD_HOMBRES_PROJECT_ID: 596910.25,
        LIPS_LIKE_SUGAR_PROJECT_ID: 3459278.90,
    }
    for pid, incentive in expected.items():
        contract = await compute_anchor_budget_contract(db, pid)
        assert contract["calculated_anchor_incentive_usd"] == pytest.approx(incentive)
        assert contract["anchor_candidate_status"] == "PRICED"
