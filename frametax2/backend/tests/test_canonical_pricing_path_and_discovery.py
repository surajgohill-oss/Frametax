"""
CineGlobe canonical pricing path + discovery repair — regression tests.

Locks in the two structural repairs this task made:

1. ONE canonical served economic path for every project. `get_project_state`
   (app/api/v1/cineglobe.py) previously special-cased Little Utopia by exact
   project TITLE, routing it through the legacy in-memory
   `little_utopia_state.get_state()` path while every other project used the
   generic, persisted-StructureCalculationResult-backed
   `canonical_production_view.build_production_and_structures()`. That
   title-based fork is removed; Little Utopia and F#K Valentine's Day (and
   any future project) now traverse the identical implementation.

2. Canonical program identity, not jurisdiction_code, is the discovery
   uniqueness key. `production_discovery.py` previously read at most one
   program_slug per jurisdiction_code (from `jurisdiction_comparison.
   ALL_PROFILES`, a dict that can structurally hold only one entry per
   code), silently discarding every other independently-registered
   DoctrineRecord for that code. Ontario (ca_on_opstc / on_ofttc / the
   OCASE animation credit — three distinct, separately-cited programs, all
   jurisdiction_code="CA-ON") is the control case.

Read/idempotent against real, already-persisted projects — same precedent
as test_canonical_evaluation.py.
"""
from __future__ import annotations

import ast
import inspect

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.production_discovery import discover_executable_jurisdictions
from app.calculators.production_requirements import derive_production_requirements
from app.db.session import engine
from app.models.project import Project
from app.services.canonical_evaluation import ENGINE_VERSION, evaluate_project

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
#: Production Page Integrity Closeout (migration 0071): Little Utopia's
#: beta 100% contingency-utilization election was removed as a stale
#: default; with no election on file the reserve is genuinely
#: GREY_AREA_REQUIRES_AUTHORITY, reproducing the same figures as an
#: explicit 0% election. See the matching note in
#: test_canonical_evaluation.py and CAPABILITY_LEDGER.md.
ACCEPTED_LU_NPC_USD = 3_791_333.30  # ITEM 4 REPAIR (budget classification): Little Utopia's real "1400 CAST" ($136,115) and "1100 SCRIPT" ($5,050) accounts were classified `miscellaneous` because the rule table could not read the source document's own account-code department convention. Mauritius' EDB-2020-QPE-List explicitly qualifies atl_cast and atl_writer (program_spend_rules.MU_EDB_RULES, VERIFIED tier), so $141,165 of statutorily-qualifying labour was excluded from QPE. QPE $1,838,566 -> $1,979,731; incentive $551,569.80 -> $593,919.30 (30%); NPC $3,812,823.20 -> $3,770,473.70. Baseline IDENTITY (MU / mu_edb_incentive) is unchanged -- only the contaminated QPE is repaired. Canonical Budget Parser Remediation (2026-09-04): the real "3200 PRODUCTION SOUND" account ($69,532) was previously misclassified into the POST-scoped "sound" category, whose ONLY Mauritius EDB-2020 citation is "Post production services (picture and sound)" -- a rule that never covered production-phase sound work. Correctly splitting production sound into its own category (never eligible under that citation) moved this $69,532 from certain QPE to GREY_AREA_REQUIRES_AUTHORITY (uncertain, pending real authority evidence) -- incentive $593,919.30 -> $573,059.70 (rate-30%); NPC $3,770,473.70 -> $3,791,333.30. This is a genuine correction (less overclaiming), not a regression.

#: The three known, independently-cited Ontario programs (Task 6's control
#: case) — real program_slugs, not aliases.
ONTARIO_PROGRAM_SLUGS = {
    "ca_on_opstc",
    "on_ofttc",
    "ontario_computer_animation_and_special_effects_tax_credit_ocase",
}


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── 1. Production title cannot select a different economic evaluator ──────

def test_get_project_state_carries_no_title_based_economic_dispatch():
    """The exact defect this task fixes: `get_project_state` must never
    branch on `project.title` to decide which evaluation path serves a
    project's economics. AST check (not a prose/comment substring match) so
    this fails immediately if the title-keyed fork is ever reintroduced,
    without needing a live DB."""
    from app.api.v1 import cineglobe as route_mod

    tree = ast.parse(inspect.getsource(route_mod.get_project_state))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "title":
            pytest.fail(
                "get_project_state must not read project.title to select an economic "
                "evaluation path — every project (Little Utopia included) must reach "
                "canonical_production_view.build_production_and_structures() the same way."
            )
        if isinstance(node, ast.Name) and node.id == "is_demo_project":
            pytest.fail("get_project_state must not carry an is_demo_project branch.")


def test_get_project_state_calls_the_shared_canonical_view_unconditionally():
    tree = ast.parse(inspect.getsource(__import__(
        "app.api.v1.cineglobe", fromlist=["get_project_state"]
    ).get_project_state))
    called_names = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "build_production_and_structures" in called_names
    assert "build_generic_pkg_and_economics" in called_names


# ── 2/3. LU and FVD traverse the SAME canonical persisted evaluation path ──

async def test_lu_and_fvd_share_the_same_canonical_evaluation_engine(db: AsyncSession):
    """No PROJECT_SPECIFIC_DIVERGENCE in economic calculation/serving
    (Task 7's required final state) — both projects' own baseline
    structure was produced by the identical evaluate_project() service at
    the identical engine version.

    Final Consolidated Backend Correction + Global Structuring
    Intelligence Acceptance, Part 4/CBA-001: neither project's baseline
    currently admits Recommended (both have a genuinely unresolved
    cultural-test qualification), so `leading_structure_id` is correctly
    None (never a stale pointer) — the SAME-ENGINE invariant this test
    exists to prove is checked against `result["baseline"]` instead,
    which remains real, priced, and disclosed either way."""
    from app.models.production import StructureCalculationResult

    for project_id in (LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID):
        project = await db.get(Project, project_id)
        assert project.leading_structure_id is None
        served = await evaluate_project(db, project_id)
        assert served["engine_version"] == ENGINE_VERSION
        result = (await db.execute(
            __import__("sqlalchemy").select(StructureCalculationResult)
            .where(StructureCalculationResult.structure_id == served["baseline"]["structure_id"])
            .order_by(StructureCalculationResult.created_at.desc())
        )).scalars().first()
        assert result is not None
        assert result.engine_version == ENGINE_VERSION


async def test_lu_reevaluates_through_canonical_engine_at_accepted_npc(db: AsyncSession):
    """Little Utopia, re-run through the SAME service FVD uses (no forced
    historical value, no special-cased inputs), reconciles to the accepted
    Mauritius NPC — proving the canonical persisted inputs are correct, not
    that the number was hardcoded somewhere. Disclosed on `baseline`;
    `top_result` is correctly None (Part 4/CBA-001 — Mauritius's own
    cultural-test applicability remains genuinely unresolved)."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["base_jurisdiction_code"] == "MU"
    assert result["baseline"]["true_net_cost_usd"] == ACCEPTED_LU_NPC_USD
    assert result["baseline"]["is_baseline"] is True
    assert result["top_result"] is None


# ── 7. Final NPC reconciles exactly: budget - incentive + adjustments = NPC ─

async def test_npc_reconciles_exactly_for_lu_and_fvd_baselines(db: AsyncSession):
    from sqlalchemy import select as sa_select

    from app.models.production import ProductionStructure, StructureCalculationResult

    for project_id in (LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID):
        served = await evaluate_project(db, project_id)
        result = (await db.execute(
            sa_select(StructureCalculationResult)
            .where(StructureCalculationResult.structure_id == served["baseline"]["structure_id"])
        )).scalars().first()
        trace = result.calculation_trace_json or {}
        budget = trace["gross_budget_usd"]
        incentive = trace["selected_incentive_usd"]
        adjustments = trace["adjustments"]
        total_adjustments = adjustments["total_adjustments_usd"]
        reconciled = round(budget - incentive + total_adjustments, 2)
        assert reconciled == round(float(result.risk_adjusted_net_cost_usd), 2), (
            f"{project_id}: budget - incentive + adjustments must equal the served "
            f"npc_with_adjustments_usd with no hidden residual"
        )
        # Every adjustment is a NAMED field — never absent from the contract,
        # even when its value is 0.0/None (no per-project travel/FX/in-kind/
        # local-cost/financing/implementation input exists generically yet).
        for key in (
            "travel_incremental_delta_usd", "fx_delta_usd", "inkind_replacement_delta_usd",
            "local_cost_delta_usd", "financing_cost_usd", "implementation_cost_usd",
            "total_adjustments_usd",
        ):
            assert key in adjustments


# ── 4/5/6. Discovery: canonical program identity is the uniqueness key ────

def test_discovery_examines_every_program_sharing_a_jurisdiction_code():
    """Ontario control (Task 6): all three independently-cited Ontario
    programs must be examined and accepted independently — none silently
    overwritten by a jurisdiction_code collapse."""
    result = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type="feature_film",
        qpe_usd=4_000_000,
        home_code="CA-ON",
    )
    on_examinations = [e for e in result.examinations if e.jurisdiction_code == "CA-ON"]
    on_slugs = {e.program_slug for e in on_examinations}
    assert ONTARIO_PROGRAM_SLUGS <= on_slugs, (
        f"expected all of {ONTARIO_PROGRAM_SLUGS} to be independently examined, got {on_slugs}"
    )
    # No jurisdiction-code overwrite: three distinct examination rows, not one.
    assert len(on_examinations) == len(set(on_examinations)) >= 3

    accepted_on_pairs = {(c, s) for c, s in result.accepted if c == "CA-ON"}
    assert ONTARIO_PROGRAM_SLUGS <= {s for _, s in accepted_on_pairs}


def test_discovery_does_not_duplicate_via_alias_spelling():
    """Aliases must resolve to canonical program IDs and must never create a
    duplicate economic candidate — ca_on_opstc appears in BOTH
    jurisdiction_comparison.ALL_PROFILES and executable_jurisdiction_registry;
    it must still examine as exactly one candidate, not two."""
    result = discover_executable_jurisdictions(
        requirements=derive_production_requirements({}),
        production_type="feature_film",
        qpe_usd=4_000_000,
        home_code="CA-ON",
    )
    opstc_examinations = [
        e for e in result.examinations
        if e.jurisdiction_code == "CA-ON" and e.program_slug == "ca_on_opstc"
    ]
    assert len(opstc_examinations) == 1


async def test_fvd_evaluation_prices_all_three_ontario_programs_independently(db: AsyncSession):
    """End-to-end proof through the real served evaluate_project() path (not
    just the discovery unit above): Ontario as a relocation destination for
    a real project yields three independent, independently-priced
    candidates with distinct structure rows and distinct NPCs — never
    collapsed to one.

    Existing Optimizer/Stacker Reconnection: a 4th, additive multi_program
    row (federal ca_federal_cptc + on_ofttc combined under a named
    spend_reduction rule) now also exists for CA-ON — that was always the
    explicitly deferred next phase, not a permanent constraint. The three
    single-program rows this test originally proved remain independently
    priced and unchanged; the combined row is asserted separately below,
    never conflated with them."""
    from sqlalchemy import select as sa_select

    from app.models.production import ProductionStructure, StructureCalculationResult

    from app.services.canonical_evaluation import current_result_fingerprint

    await evaluate_project(db, FVD_PROJECT_ID)
    # ITEM 8. ENGINE_VERSION alone is NOT a freshness filter. Evaluation is
    # append-only (superseded generations are retained as history, exactly
    # like a superseded DocumentVersion), and a rule or pricing-source change
    # now invalidates the FINGERPRINT without bumping ENGINE_VERSION -- so
    # several generations legitimately coexist under one engine version.
    # Reading on engine_version alone returned 12 "independently priced
    # Ontario candidates" where 3 exist, i.e. it served results computed from
    # inputs that are no longer true. Pin to the current generation, the same
    # selector the engine and the served view use.
    current_fingerprint = await current_result_fingerprint(db, FVD_PROJECT_ID)
    rows = (await db.execute(
        sa_select(ProductionStructure, StructureCalculationResult)
        .join(StructureCalculationResult, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(
            ProductionStructure.project_id == FVD_PROJECT_ID,
            StructureCalculationResult.engine_version == ENGINE_VERSION,
            StructureCalculationResult.input_fingerprint == current_fingerprint,
        )
    )).all()
    on_rows = [
        (structure, result) for structure, result in rows
        if (result.calculation_trace_json or {}).get("primary_jurisdiction") == "CA-ON"
    ]
    single_program_on_rows = [
        (s, r) for s, r in on_rows
        if (r.calculation_trace_json or {}).get("structure_type") != "multi_program"
    ]
    multi_program_on_rows = [
        (s, r) for s, r in on_rows
        if (r.calculation_trace_json or {}).get("structure_type") == "multi_program"
    ]
    # capability_only/unpriceable rows carry program_slug in trace too; only
    # assert the priced ones for the NPC-distinctness check below.
    priced_on = [(s, r) for s, r in single_program_on_rows if r.true_net_cost_usd is not None]
    assert len(priced_on) == 3, f"expected 3 independently priced Ontario candidates, got {len(priced_on)}"
    npc_values = {float(r.true_net_cost_usd) for _s, r in priced_on}
    assert len(npc_values) == 3, "each Ontario program must price to its own distinct NPC"
    structure_ids = {str(s.id) for s, _r in priced_on}
    assert len(structure_ids) == 3, "each Ontario program must be its own structure row"
    names = {s.name for s, _r in priced_on}
    assert len(names) == 3, "disambiguated structure names must not collide"

    # 4 additive combined CA-ON structures: 3 pairs + 1 N-way triple (see
    # test_on_ofttc_and_ocase_now_independently_served for the itemized
    # per-combination proof).
    # ITEM 8 CORRECTION. This previously asserted 4 combined CA-ON structures.
    # There has only ever been ONE: querying every generation returns four
    # rows that are all the SAME combination ['ca_on_opstc', 'on_ofttc'] under
    # four DIFFERENT input_fingerprints -- superseded history, not four
    # combinations. The old expectation counted accumulated stale generations,
    # so an accumulating-history defect read as a passing invariant.
    #
    # One is also the canonically CORRECT count: load_named_rules_for_group
    # reports fully_covered only for (ca_on_opstc, on_ofttc). Both OCASE pairs
    # and the triple are uncovered, and price_program_group_stack leaves an
    # uncovered group ungenerated rather than partially trusted. OCASE stack
    # coverage is a real rule-DATA gap, disclosed, never invented here.
    assert len(multi_program_on_rows) == 1, (
        "expected exactly 1 additive combined CA-ON structure "
        "(ca_on_opstc + on_ofttc -- the only fully-covered pair)"
    )
    # CLUSTER 8. The only fully-covered CA-ON pair is MUTUALLY EXCLUSIVE
    # (VERIFIED: OFTTC is for Ontario domestic-content productions, OPSTC for
    # foreign service productions -- a production cannot be both). A mutually
    # exclusive combination is disclosed but is NOT a priced structure, so it
    # correctly carries no incentive and no NPC and never enters ranking.
    for _s, r in multi_program_on_rows:
        trace = r.calculation_trace_json or {}
        assert trace.get("stacking_rule_type") == "mutually_exclusive" or r.true_net_cost_usd is None, (
            "a combined structure must either price or be a disclosed "
            "mutually-exclusive combination"
        )


def test_canonical_evaluation_candidate_loop_never_collapses_to_first_per_code():
    """Static regression guard for the exact defect Codex flagged: the
    per-code `next(...)` lookups that silently kept only the FIRST accepted/
    capability_only program for a jurisdiction. Must not reappear."""
    from app.services import canonical_evaluation as mod

    source = inspect.getsource(mod.evaluate_project)
    assert "next((s for c, s in discovery.accepted" not in source
    assert 'discovery.metrics.get("capability_only_jurisdictions"' not in source
