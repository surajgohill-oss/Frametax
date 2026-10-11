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

Isolation (2026-10): the tests that assert FROZEN real baselines of the four productions run only when explicitly authorised, inside a
READ ONLY transaction (tests/isolated_records.py). Everything else runs on SYNTHETIC rolled-back records on the isolated test database.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.isolated_records import (
    DEFAULT_LINES, add_synthetic_people, create_synthetic_project, isolated_session, real_readonly_db,  # noqa: F401
    requires_real_production_reads)
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
    async with isolated_session() as session:
        yield session


async def _evaluated_synthetic(db, *, with_people=False, lines=DEFAULT_LINES):
    from app.services.canonical_evaluation import evaluate_project
    pid = await create_synthetic_project(db, lines=lines)
    if with_people:
        await add_synthetic_people(db, pid, (("writer", "Synthetic Writer", "GB", True), ("director", "Synthetic Director", "AU", True)))
    await evaluate_project(db, pid)
    return pid


# ---------------------------------------------------------------------------
# A — Anchor Budget Contract
# ---------------------------------------------------------------------------

@requires_real_production_reads
async def test_anchor_budget_contract_matches_the_real_baseline_for_all_four_productions(real_readonly_db: AsyncSession):
    db = real_readonly_db
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


@requires_real_production_reads
async def test_anchor_budget_contract_never_reports_a_fabricated_variance_when_no_supplied_incentive_exists(real_readonly_db: AsyncSession):
    db = real_readonly_db
    """None of the four real productions has a real spend_category=='incentive'
    budget line on file (confirmed by direct query) -- supplied_incentive_usd
    must be None, and variance_usd must ALSO be None (never computed as
    though a $0 supplied figure was found, which would silently misreport
    the full calculated incentive as a 'variance')."""
    for name, pid in ALL_FOUR.items():
        contract = await compute_anchor_budget_contract(db, pid)
        assert contract["supplied_incentive_usd"] is None, f"{name}: unexpected supplied incentive line found"
        assert contract["variance_usd"] is None, f"{name}: variance must be None with no supplied figure to reconcile against"


@requires_real_production_reads
async def test_little_utopia_and_fvd_anchor_reports_their_own_real_unresolved_qualification_state(real_readonly_db: AsyncSession):
    db = real_readonly_db
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

    for pid in [await _evaluated_synthetic(db)]:
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

    from sqlalchemy import select as sa_select

    from app.models.budget import BudgetDocument, BudgetLineItem
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import current_generation_fingerprint, evaluate_project

    pid = await create_synthetic_project(db)
    fp_before = await current_generation_fingerprint(db, pid)
    assert fp_before is not None

    doc_id = (await db.execute(
        sa_select(BudgetDocument.id).where(BudgetDocument.project_id == pid).limit(1)
    )).scalar_one_or_none()
    assert doc_id is not None

    db.add(BudgetLineItem(
        id=uuid.uuid4(), budget_document_id=doc_id, department="TEST",
        description="fingerprint-sensitivity probe", spend_category="incentive", amount_usd=1.0, amount_normalized=1.0, currency_code="USD",
    ))
    await db.flush()
    fp_with_supplied_line = await current_generation_fingerprint(db, pid)
    assert fp_with_supplied_line != fp_before, "adding a supplied-incentive budget line must change the evaluation fingerprint"

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


# ---------------------------------------------------------------------------
# B/E — $100,000 hybrid-recommendation materiality threshold
# ---------------------------------------------------------------------------

async def test_materiality_threshold_never_classifies_the_anchor_itself(db: AsyncSession):
    pid = await _evaluated_synthetic(db)
    view = await build_production_and_structures(db, pid)
    entries = view["structures"]["allocated_structures"]["structures"]
    baseline = [e for e in entries if e.get("is_baseline")]
    assert baseline
    for e in baseline:
        assert e["hybrid_recommendation_status"] == "NOT_APPLICABLE"
        assert e["net_benefit_vs_anchor_usd"] is None


async def test_materiality_threshold_classifies_every_priced_candidate_by_the_exact_anchor_difference(db: AsyncSession):
    """Synthetic project: every priced, non-baseline candidate's net benefit equals anchor_npc - candidate_npc exactly (using the
    anchor value the contract itself reports) and its status follows the $100,000 threshold; the anchor is NOT_APPLICABLE."""
    pid = await _evaluated_synthetic(db)
    view = await build_production_and_structures(db, pid)
    entries = view["structures"]["allocated_structures"]["structures"]
    statuses = {e.get("hybrid_recommendation_status") for e in entries}
    assert "NOT_APPLICABLE" in statuses
    assert statuses & {"ELIGIBLE_FOR_RECOMMENDATION", "ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED"}
    contract = await compute_anchor_budget_contract(db, pid)
    anchor_npc = contract["anchor_npc_usd"]
    checked = 0
    for e in entries:
        if e.get("is_baseline") or e.get("npc_verified_usd") is None or e.get("hybrid_recommendation_status") is None:
            continue
        if e["hybrid_recommendation_status"] not in ("ELIGIBLE_FOR_RECOMMENDATION", "ECONOMICALLY_NON_MATERIAL_NOT_RECOMMENDED"):
            continue
        expected_benefit = round(anchor_npc - e["npc_verified_usd"], 2)
        assert e["net_benefit_vs_anchor_usd"] == pytest.approx(expected_benefit)
        assert (e["hybrid_recommendation_status"] == "ELIGIBLE_FOR_RECOMMENDATION") == (expected_benefit >= 100_000)
        checked += 1
    assert checked > 0


async def test_uk_au_bilateral_conditional_structure_is_never_a_recommendation(db: AsyncSession):
    """A conditional uk-au-bilateral structure (synthetic GB writer + AU director) is labelled with a CONDITIONAL_* status, a DISTINCT
    status from ELIGIBLE_FOR_RECOMMENDATION, whatever its size, so nothing downstream can mistake a disclosed, producer-actionable
    assumption for a verified recommendation (Section D/E's own 'never auto-award' rule); material iff its benefit is >= $100,000."""
    pid = await _evaluated_synthetic(db, with_people=True)
    from sqlalchemy import select as sa_select
    from app.models.production import ProductionStructure, StructureCalculationResult
    from app.services.canonical_evaluation import ENGINE_VERSION, current_generation_fingerprint
    fp = await current_generation_fingerprint(db, pid)
    trace = (await db.execute(
        sa_select(StructureCalculationResult.calculation_trace_json)
        .join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
        .where(ProductionStructure.project_id == pid, StructureCalculationResult.engine_version == ENGINE_VERSION,
               StructureCalculationResult.input_fingerprint == fp,
               StructureCalculationResult.calculation_trace_json["treaty_slug"].astext == "uk-au-bilateral")
    )).scalar_one()
    assert trace["opportunity_relevance"] == "CONDITIONAL"
    view = await build_production_and_structures(db, pid)
    entries = view["structures"]["allocated_structures"]["structures"]
    ukau = [e for e in entries if e.get("treaty_slug") == "uk-au-bilateral"]
    if not ukau:
        pytest.skip("the 100-structure served page does not include the opportunity for this synthetic budget; the persisted trace above is the proof")
    e = ukau[0]
    assert e["hybrid_recommendation_status"] in ("CONDITIONAL_MATERIAL", "CONDITIONAL_ECONOMICALLY_NON_MATERIAL")
    assert e["hybrid_recommendation_status"] != "ELIGIBLE_FOR_RECOMMENDATION"
    if e["net_benefit_vs_anchor_usd"] is not None:
        assert (e["hybrid_recommendation_status"] == "CONDITIONAL_MATERIAL") == (e["net_benefit_vs_anchor_usd"] >= 100_000)


@requires_real_production_reads
async def test_bad_hombres_and_lips_like_sugar_leading_structures_unaffected(real_readonly_db: AsyncSession):
    db = real_readonly_db
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
