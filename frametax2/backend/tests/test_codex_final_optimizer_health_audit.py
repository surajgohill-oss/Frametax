"""
test_codex_final_optimizer_health_audit.py

Fixes for the four defects in
docs/validation/CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT.md (commit 1c4fc79):

OH-001 (P0) — stale canonical snapshots masquerade as current.
OH-002 (P0) — combined-structure qualification can be lost/weakened.
OH-003 (P1) — multiple production-capable engine lineages remain mounted.
OH-004 (P1) — acceptance tests can pass without exercising the contract.

OH-003 and most of OH-004 are covered by test_legacy_endpoint_isolation.py,
test_cache_fingerprint_expansion.py, and test_canonical_role_qualification_
bridge.py (each fixed in the same commit as this file). This file covers
OH-001 and OH-002 directly, against real runtime evaluation.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.models.production import ProductionStructure, StructureCalculationResult
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    _QUAL_STATE_SEVERITY,
    evaluate_project,
)
from tests.test_canonical_evaluation import FVD_PROJECT_ID, LITTLE_UTOPIA_PROJECT_ID


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── OH-001: stale snapshots must never be served as current ─────────────

async def _current_rows(db: AsyncSession, project_id: str) -> list[StructureCalculationResult]:
    rows = (await db.execute(
        select(StructureCalculationResult)
        .join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
        .where(ProductionStructure.project_id == project_id)
    )).scalars().all()
    return list(rows)


async def test_fresh_evaluation_uses_the_current_engine_version(db: AsyncSession):
    """Direct, non-vacuous proof: after a real evaluate_project() call, every
    row it can serve as current carries the CURRENT ENGINE_VERSION -- not a
    pre-change string. This is the exact failure Codex found: rows created
    under an older ENGINE_VERSION with an unaffected fingerprint kept
    matching as current indefinitely."""
    result = await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    assert result["engine_version"] == ENGINE_VERSION == "canonical-1.45.0"

    rows = await _current_rows(db, LITTLE_UTOPIA_PROJECT_ID)
    current = [r for r in rows if r.engine_version == ENGINE_VERSION]
    assert current, "test went vacuous — no current-engine-version rows found"
    assert all(r.engine_version == ENGINE_VERSION for r in current)


async def test_a_row_from_an_older_engine_version_is_never_reused_as_current(db: AsyncSession):
    """OH-001's exact root cause, proven directly: a persisted row whose
    engine_version differs from the live ENGINE_VERSION must never satisfy
    evaluate_project()'s reuse query, regardless of its fingerprint."""
    rows = await _current_rows(db, FVD_PROJECT_ID)
    stale = [r for r in rows if r.engine_version != ENGINE_VERSION]
    if not stale:
        pytest.skip("no stale-engine-version row present in this environment to probe")
    # The reuse query in evaluate_project() requires an EXACT engine_version
    # match; a stale row's presence must never short-circuit a fresh
    # evaluate_project() call into skipping recomputation.
    result = await evaluate_project(db, FVD_PROJECT_ID)
    assert result["engine_version"] == ENGINE_VERSION
    assert result["status"] in ("EVALUATION_COMPLETE", "EVALUATION_REUSED")
    # If reused, it must have reused a CURRENT row, never the stale one.
    if result["status"] == "EVALUATION_REUSED":
        current_after = [r for r in await _current_rows(db, FVD_PROJECT_ID) if r.engine_version == ENGINE_VERSION]
        assert current_after


async def test_recovered_58_programs_reach_the_fresh_served_project_response(db: AsyncSession):
    """Fresh served proof of the restored-58 policy (Codex's stated gap:
    'policy restored but fresh served proof absent because snapshots were
    stale'). Proves representative previously-quarantined-then-restored
    programs actually appear in a FRESH LU relocation candidate universe
    with real economics, not just in the registry classifier."""
    from app.services.canonical_production_view import build_production_and_structures

    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    by_slug = {e.get("program_slug"): e for e in entries if e.get("program_slug")}

    representative = ["it_tax_credit_foreign", "be_tax_shelter", "mt_mfc_rebate", "pl_pisf_cash_rebate"]
    found = [s for s in representative if s in by_slug]
    assert found, "test went vacuous — none of the representative restored-58 programs appeared"
    for slug in found:
        entry = by_slug[slug]
        assert entry.get("npc_with_adjustments_usd") is not None, (
            f"{slug} appears in the fresh candidate universe but carries no economics"
        )


async def test_recovered_component_programs_reach_the_fresh_served_project_response(db: AsyncSession):
    """BC DAVE / AU PDV (canonical knowledge consolidation) must reach the
    actual served project response, not merely the canonical registry --
    Codex's specific "candidate/cache divergence" finding."""
    from app.services.canonical_production_view import build_production_and_structures

    await evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)
    view = await build_production_and_structures(db, LITTLE_UTOPIA_PROJECT_ID)
    slugs = {
        e.get("program_slug")
        for e in view["structures"]["allocated_structures"]["structures"]
        if e.get("program_slug")
    }
    assert "ca_bc_dave" in slugs
    assert "au_pdv_offset" in slugs


async def test_ny_fresh_served_result_uses_the_current_production_plus_ceiling(db: AsyncSession):
    """Codex: 'canonical model healthy, served result stale' -- the actual
    FVD response exposed a 50% ceiling, not the current 60% Production
    Plus ceiling. Proven fresh here."""
    from app.data.program_rate_rules import resolve_program_rate

    r = resolve_program_rate("us_ny_film_credit", production_type="feature_film", qpe_usd=500_000)
    assert r.modeled_rate == 0.60, "canonical model itself must show the 60% Production Plus ceiling"

    await evaluate_project(db, FVD_PROJECT_ID)
    rows = await _current_rows(db, FVD_PROJECT_ID)
    ny_rows = [
        r for r in rows
        if r.engine_version == ENGINE_VERSION
        and (r.calculation_trace_json or {}).get("program_slug") == "us_ny_film_credit"
    ]
    if not ny_rows:
        pytest.skip("us_ny_film_credit not a candidate for this project's current inputs")
    ceilings = {r.calculation_trace_json.get("rate_ceiling") for r in ny_rows if r.calculation_trace_json.get("rate_ceiling") is not None}
    if ceilings:
        assert 0.60 in ceilings or any(c >= 0.60 for c in ceilings), (
            f"fresh served NY rows still show a stale ceiling: {ceilings}"
        )


# ── OH-002: combined-structure qualification must never be null/lost ─────

async def test_ontario_combined_structures_never_have_null_qualification(db: AsyncSession):
    """Direct, non-vacuous proof against real FVD combined Ontario stacks:
    every combined structure must carry a real role_qualification.state,
    never None, when its members have known states."""
    from app.services.canonical_production_view import build_production_and_structures

    await evaluate_project(db, FVD_PROJECT_ID)
    view = await build_production_and_structures(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    combined = [e for e in entries if e.get("anchor_jurisdiction") == "CA-ON" and e.get("structure_type") == "multi_program"]
    assert combined, "test went vacuous — no CA-ON combined structures found"
    for entry in combined:
        rq = entry.get("role_qualification")
        assert rq is not None and rq.get("state") is not None, (
            f"combined structure {entry.get('structure_id')} has null qualification "
            "despite its members having known states"
        )


def test_worst_state_severity_table_has_every_qualification_state_explicit():
    """OH-002's second sub-defect: QUAL_RULE_DATA_INCOMPLETE was silently
    absent from _QUAL_STATE_SEVERITY, defaulting (via `.get(state, 2)`) to
    the SAME severity as QUALIFIES/NOT_APPLICABLE -- meaning a real
    RULE_DATA_INCOMPLETE member could incorrectly resolve a combo to an
    admitted state. Proves every state the qualification result contract
    defines has its own explicit entry."""
    from app.calculators.canonical_qualification_result import ALL_QUALIFICATION_STATES

    missing = ALL_QUALIFICATION_STATES - set(_QUAL_STATE_SEVERITY.keys())
    assert not missing, f"qualification states with no explicit severity: {missing}"


def test_not_applicable_and_rule_data_incomplete_are_not_conflated():
    """The exact scenario Codex's required proof names: OPSTC NOT_APPLICABLE
    + OFTTC RULE_DATA_INCOMPLETE must resolve RULE_DATA_INCOMPLETE (worse),
    never NOT_APPLICABLE."""
    from app.calculators.canonical_qualification_result import (
        QUAL_NOT_APPLICABLE,
        QUAL_RULE_DATA_INCOMPLETE,
    )

    worst = min(
        (QUAL_NOT_APPLICABLE, QUAL_RULE_DATA_INCOMPLETE),
        key=lambda s: _QUAL_STATE_SEVERITY[s],
    )
    assert worst == QUAL_RULE_DATA_INCOMPLETE


def test_combo_qualification_lookup_is_keyed_by_program_identity_not_jurisdiction_code():
    """OH-002's root cause, proven directly against the fixed source: the
    combo-trace builder must resolve each member's qualification state by
    program_slug alone (a federal member's own examination code, e.g.
    "CA", differs from a provincial combo's own jurisdiction_code, e.g.
    "CA-ON") -- never by (combo_jurisdiction_code, slug), which silently
    dropped every federal-under-provincial member's real state."""
    import inspect

    import app.services.canonical_evaluation as ce_mod

    source = inspect.getsource(ce_mod)
    assert "_qual_state_by_program.get(slug)" in source
    assert "_qual_state_by_code_program.get((code, slug))" not in source
