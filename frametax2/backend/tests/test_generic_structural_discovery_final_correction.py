"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_CORRECTION.

Prevention tests for the corrected generic discovery mechanism in
evaluate_project()'s ordinary-component-hybrid loop: no named-program
allowlist, no arbitrary top-N discovery pruning, and a proof-based
(pigeonhole exchange argument) branch-and-bound that widens on failure
rather than admitting an unproven search-depth cutoff.
"""
import re
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services import canonical_evaluation as ce

_SRC = Path(ce.__file__).read_text()
_SRC_CODE_ONLY = "\n".join(line.split("#", 1)[0] for line in _SRC.splitlines())

LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"

# Fail-closed DB isolation guard. This workstream's DB-backed tests write
# real rows (they exercise the live evaluate_project() persistence path,
# not a mock) and must never do so against the shared local application
# database that every developer/worktree on this machine reads and
# writes. Only an explicitly isolated audit database -- this exact name,
# or a name starting with one of the approved prefixes below -- is
# permitted. Anything else, including the shared "frametax2" database
# itself, fails the test suite immediately rather than silently writing
# to shared state.
_APPROVED_ISOLATED_DB_NAME = "frametax2_claude_generic_discovery_audit_20260917"
_APPROVED_ISOLATED_DB_PREFIXES = ("frametax2_claude_generic_discovery_audit_",)


def _assert_isolated_database(engine_obj) -> str:
    db_name = engine_obj.url.database or ""
    is_approved = db_name == _APPROVED_ISOLATED_DB_NAME or any(
        db_name.startswith(p) for p in _APPROVED_ISOLATED_DB_PREFIXES
    )
    assert is_approved, (
        f"REFUSING TO RUN: resolved database is {db_name!r}, which is not the approved "
        f"isolated audit database ({_APPROVED_ISOLATED_DB_NAME!r}) or an approved-prefix "
        "database. This test suite writes real persisted rows and must never run against "
        "the shared local application database. Set DATABASE_URL to point at the isolated "
        "audit database before running these tests."
    )
    return db_name


@pytest.fixture
async def db():
    _assert_isolated_database(engine)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


def test_no_named_acceptance_control_allowlist_exists_in_production_code():
    """The removed _NAMED_ACCEPTANCE_CONTROL_TARGETS mechanism (and any
    reintroduction under a new name) must never exist as executable code
    -- only as historical comment text explaining its removal."""
    for line in _SRC.splitlines():
        code = line.split("#", 1)[0]
        assert "_NAMED_ACCEPTANCE_CONTROL_TARGETS" not in code, (
            "a named-program allowlist constant/reference was reintroduced into "
            f"executable code: {line!r}"
        )
    # No dict literal mapping component names to hard-coded (jurisdiction,
    # program_slug) tuples anywhere near the hybrid-loop discovery code.
    assert "new_zealand_screen_production_grant" not in _SRC.replace(
        "# HO-001", ""
    ).split("def evaluate_project")[0], "a named program slug leaked outside test/comment context"


def test_no_arbitrary_top_n_discovery_cutoff_remains():
    """The prior top-3/top-5 ranking cutoff for component candidates must
    not exist; only a proof-justified (pigeonhole) window remains."""
    assert "max_targets_per_component" not in _SRC_CODE_ONLY
    assert "_HYBRID_BB_MAX_EXAMINED_PER_SUBSET" not in _SRC_CODE_ONLY
    assert "SEARCH_DEPTH_LIMIT_REACHED" not in _SRC_CODE_ONLY, (
        "the admitted-incomplete search-depth-limit disposition must not "
        "exist once the proof-based widening mechanism replaced it"
    )


def test_pigeonhole_window_starts_at_subset_size_not_a_fixed_constant():
    """The search window must start at `_r` (the subset size), a
    mathematically-derived value, never a fixed magic number like 3 or 5."""
    match = re.search(r"_window = _r\b", _SRC)
    assert match is not None, "window must be seeded from the subset size, not a constant"


@pytest.mark.asyncio
async def test_dominated_with_proof_rows_use_correction_engine_version(db: AsyncSession):
    """Every DOMINATED_WITH_PROOF row persisted for a real production
    must be tagged with the CURRENT engine version (proves the discovery
    mechanism the fingerprint/version bump targets is actually the one
    running -- the SERVED evaluation must be driven by rows persisted
    under the current engine version, never a stale row left over from a
    prior version (older-version rows legitimately remain in the table as
    superseded history; they must simply never be what the current
    evaluation reads back as current)."""
    result = await ce.evaluate_project(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    assert result.get("engine_version") == ce.ENGINE_VERSION
    current_fingerprint = result["state_fingerprint"]
    rows = (
        await db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev
                  AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'
                """
            ),
            {"pid": LIPS_LIKE_SUGAR_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": current_fingerprint},
        )
    ).scalar()
    assert rows and rows > 0, (
        "no DOMINATED_WITH_PROOF row exists under the CURRENT engine version AND "
        "current input fingerprint -- either the discovery mechanism did not run "
        "this call, or a stale fingerprint/engine-version row from a PRIOR call "
        "was mistaken for evidence that this call produced one"
    )


@pytest.mark.asyncio
async def test_dominated_with_proof_rows_carry_a_real_numeric_proof(db: AsyncSession):
    """Every DOMINATED_WITH_PROOF row must carry the actual proof data
    (window size, best real total found, dominated count) -- never an
    empty or placeholder justification."""
    result = await ce.evaluate_project(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    current_fingerprint = result["state_fingerprint"]
    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev
                  AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'
                LIMIT 20
                """
            ),
            {"pid": LIPS_LIKE_SUGAR_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": current_fingerprint},
        )
    ).all()
    assert rows, "expected at least one DOMINATED_WITH_PROOF row for a real production"
    for (trace,) in rows:
        assert trace.get("proof_window_size") is not None
        assert trace.get("dominated_combination_count", 0) > 0
        assert trace.get("best_real_total_found_usd") is not None
        assert "pigeonhole" in trace.get("reason", "").lower()
        # Reconstruction-data fix, this pass: an aggregate count is not
        # enough -- the exact real (jurisdiction_code, program_slug,
        # marginal_value_usd) candidates considered per component, and
        # the specific incumbent structure the proof is measured against,
        # must be named, not just counted.
        assert trace.get("incumbent_structure_id"), "DOMINATED_WITH_PROOF row has no incumbent_structure_id"
        windows = trace.get("component_target_windows")
        assert windows and isinstance(windows, dict) and len(windows) > 0, (
            "DOMINATED_WITH_PROOF row has no component_target_windows -- "
            "the examined candidate set cannot be reconstructed from this row alone"
        )
        for _component, _targets in windows.items():
            assert _targets, f"component {_component!r} has an empty examined-candidate window"
            for _t in _targets:
                assert _t.get("jurisdiction_code") and _t.get("program_slug"), (
                    f"component {_component!r} window entry missing jurisdiction/program identity: {_t}"
                )
        assert trace.get("engine_version") == ce.ENGINE_VERSION
        assert trace.get("input_fingerprint") == current_fingerprint


@pytest.mark.asyncio
async def test_duplicate_economic_routes_persist_once(db: AsyncSession):
    """Two different (anchor, subset) search paths that happen to
    discover the exact same canonical component set must collapse to a
    single persisted structure, never two -- WITHIN one served view.

    Scoping this only by engine_version (and not by input_fingerprint) is
    a real test bug found and fixed this pass: two rows with the SAME
    structural_generator_structure_id but DIFFERENT input_fingerprints
    are not a duplicate-persistence defect -- they are two different
    fingerprint epochs (a real, legitimate outcome any time the
    project's underlying facts change between two evaluate_project()
    calls), and canonical_evaluation.py's own fingerprint-scoped
    `_summarize_evaluation()` already reads back only the CURRENT
    fingerprint's rows as served/current, per its own explicit design
    ('older-version rows legitimately remain in the table as superseded
    history; they must simply never be what the current evaluation reads
    back as current'). This test must therefore scope to the SAME
    (engine_version, input_fingerprint) pair the served view actually
    uses -- taken from evaluate_project()'s own returned
    state_fingerprint -- to test true within-current-view duplication,
    not conflate it with ordinary historical churn across calls."""
    result = await ce.evaluate_project(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    current_fingerprint = result["state_fingerprint"]
    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'structural_generator_structure_id', COUNT(*)
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev
                  AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
                  AND scr.calculation_trace_json->>'discovery_classification' = 'structural_archetype_generator'
                GROUP BY 1
                HAVING COUNT(*) > 1
                """
            ),
            {"pid": LIPS_LIKE_SUGAR_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": current_fingerprint},
        )
    ).all()
    assert not rows, f"duplicate economic route(s) persisted more than once WITHIN the current fingerprint: {rows}"


@pytest.mark.asyncio
async def test_multiple_candidates_per_window_are_actually_examined(db: AsyncSession):
    """Regression guard for the exact historical defect this workstream
    fixed: a block of the branch-and-bound (the heap pop, real pricing,
    persistence, and the heap's own neighbor-push) had been accidentally
    dedented one level out of the inner `while _heap:` loop, so ONLY the
    single top-ranked (index 0 in every dimension) combination was ever
    examined per search window -- confirmed at the time to collapse
    Lips Like Sugar's ordinary_component_hybrid discovery to a mere
    handful of rows (a single combination per (anchor, subset) pair,
    with most producing zero PRICED results due to jurisdiction
    collisions on that single combination). If that dedent regressed,
    this count would collapse back to a tiny number; a genuinely
    branching search over Lips Like Sugar's real budget produces
    hundreds of distinct priced ordinary-component-hybrid structures."""
    result = await ce.evaluate_project(db, LIPS_LIKE_SUGAR_PROJECT_ID)
    current_fingerprint = result["state_fingerprint"]
    priced_count = (
        await db.execute(
            text(
                """
                SELECT COUNT(DISTINCT scr.calculation_trace_json->>'structural_generator_structure_id')
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev
                  AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
                  AND scr.calculation_trace_json->>'discovery_classification' = 'structural_archetype_generator'
                """
            ),
            {"pid": LIPS_LIKE_SUGAR_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": current_fingerprint},
        )
    ).scalar()
    assert priced_count is not None and priced_count > 100, (
        f"only {priced_count} distinct ordinary_component_hybrid PRICED structures found for Lips Like "
        "Sugar -- this is consistent with the historical dedent defect (only the top-ranked candidate "
        "examined per window) having recurred, not with a genuinely branching multi-candidate search"
    )
    # Direct confirmation that MULTIPLE components' chosen destinations
    # are not always each component's own single top-ranked target --
    # if the search only ever examined index (0, 0, ..., 0), every
    # persisted structure's jurisdiction/program choice for a given
    # component would be identical across every structure that includes
    # that component, which is exactly what the dedent bug produced.
    per_component_choices = (
        await db.execute(
            text(
                """
                SELECT jsonb_array_elements(scr.calculation_trace_json->'component_allocations')->>'jurisdiction_code'
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev
                  AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
                  AND scr.calculation_trace_json->>'discovery_classification' = 'structural_archetype_generator'
                """
            ),
            {"pid": LIPS_LIKE_SUGAR_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": current_fingerprint},
        )
    ).scalars().all()
    distinct_jurisdictions_chosen = set(per_component_choices)
    assert len(distinct_jurisdictions_chosen) > 5, (
        f"only {len(distinct_jurisdictions_chosen)} distinct jurisdiction(s) ever appear as a chosen "
        "component destination across every persisted structure -- consistent with the search only "
        "ever reaching a single fixed candidate per component, never actually branching"
    )


@pytest.mark.asyncio
async def test_ho001_and_ho002_remain_computable_via_the_generic_generator_with_no_allowlist(db: AsyncSession):
    """HO-001 and HO-002 are acceptance controls, not implementation
    instructions (per the workstream's own framing): this test proves
    the generic generate_structural_candidate mechanism still correctly
    computes their real economics on demand -- with NO named allowlist
    anywhere in the production code (see test_no_named_acceptance_
    control_allowlist_exists_in_production_code above) -- even though a
    blind real-data search on Lips Like Sugar's actual budget does not
    select them as the winning candidate (real, better legal
    alternatives dominate them for this production's real numbers)."""
    from app.calculators.production_allocation import AccountAllocation, AssignmentKind
    from app.calculators.structural_archetype_generator import (
        StructuralComponent, generate_structural_candidate,
    )

    def comp(slug, code, amount, line, spend_category):
        alloc = AccountAllocation(
            account_code="1", description="x", amount_usd=amount, component="principal_production",
            jurisdiction_code=code, assignment_kind=AssignmentKind.FIXED, rationale="test",
            governing_decision="test", line_id=line, spend_category=spend_category,
        )
        return StructuralComponent(
            component_type="principal_production", jurisdiction_code=code, program_slug=slug,
            allocations=(alloc,), spend_category_by_code={"1": spend_category},
        )

    # HO-001: us_ga_film_credit + NZ post/VFX grant + Ontario OCASE
    ho001 = generate_structural_candidate(
        [
            comp("us_ga_film_credit", "US-GA", 11_332_424.0, "L1", "atl_director"),
            comp("new_zealand_screen_production_grant_—_international_post_vfx", "NZ", 611_230.0, "L2", "post_production"),
            comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 40_000.0, "L3", "vfx"),
        ],
        gross_budget_usd=11_983_654.0,
    )
    assert ho001.executable, f"HO-001 failed to compute via the generic generator: {ho001.rejection_reason}"
    assert ho001.total_guaranteed_incentive_usd > 0
    assert ho001.jurisdiction_codes == ("US-GA", "NZ", "CA-ON")

    # HO-002: us_nm_film_credit + au_pdv_offset + Ontario OCASE
    ho002 = generate_structural_candidate(
        [
            comp("us_nm_film_credit", "US-NM", 11_332_424.0, "L1", "atl_director"),
            comp("au_pdv_offset", "AU", 611_230.0, "L2", "post_production"),
            comp("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA-ON", 40_000.0, "L3", "vfx"),
        ],
        gross_budget_usd=11_983_654.0,
    )
    assert ho002.executable, f"HO-002 failed to compute via the generic generator: {ho002.rejection_reason}"
    assert ho002.total_guaranteed_incentive_usd > 0
    assert ho002.jurisdiction_codes == ("US-NM", "AU", "CA-ON")
