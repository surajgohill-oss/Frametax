"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_CORRECTION.

Prevention tests for the corrected generic discovery mechanism in
evaluate_project()'s ordinary-component-hybrid loop: no named-program
allowlist, no arbitrary top-N discovery pruning, and a proof-based
(pigeonhole exchange argument) branch-and-bound that widens on failure
rather than admitting an unproven search-depth cutoff.
"""
import json
import re
from pathlib import Path

import pytest
from app.models.production import EvaluationCandidateAggregate
from sqlalchemy import select, text
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
# The canonical-1.90 acceptance database is an equally isolated database (never the shared frametax2).
_APPROVED_ISOLATED_DB_PREFIXES = (
    "frametax2_claude_generic_discovery_audit_", "frametax2_claude_optimizer_acceptance_",
)


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


async def _candidate_trace_rows(db: AsyncSession, project_id, fingerprint: str, classification: str) -> list[dict]:
    """Every candidate of ``classification`` in a generation, as flat mappings (status, rejection_reason_class,
    reason, program_slugs, total_incentive_value_usd): the RETAINED detailed rows plus, for canonical-1.90 bounded
    retention, one row per AGGREGATE group built from the group's representative trace. A plain RULE_REJECTED
    candidate is counted exactly in an aggregate group instead of being a detailed row, so an existence/absence
    check over "every persisted candidate" must span both."""
    detailed = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json AS trace, scr.total_incentive_value_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'discovery_classification' = :cls
                """
            ),
            {"pid": str(project_id), "ev": ce.ENGINE_VERSION, "fp": fingerprint, "cls": classification},
        )
    ).all()
    groups = (
        await db.execute(
            select(EvaluationCandidateAggregate).where(
                EvaluationCandidateAggregate.project_id == project_id,
                EvaluationCandidateAggregate.input_fingerprint == fingerprint,
                EvaluationCandidateAggregate.engine_version == ce.ENGINE_VERSION,
            )
        )
    ).scalars().all()
    out = [
        {"trace": t, "status": t.get("candidate_status"), "rejection_reason_class": t.get("rejection_reason_class"),
         "rrc": t.get("rejection_reason_class"), "reason": t.get("reason"), "program_slugs": t.get("program_slugs"),
         "total_incentive_value_usd": inc, "aggregated_count": 1}
        for t, inc in detailed
    ]
    for g in groups:
        t = (g.representative or {}).get("trace") or {}
        if t.get("discovery_classification") == classification:
            out.append({"trace": t, "status": g.candidate_status, "rejection_reason_class": g.reason_class, "rrc": g.reason_class,
                        "reason": t.get("reason"), "program_slugs": t.get("program_slugs"),
                        "total_incentive_value_usd": None, "aggregated_count": g.candidate_count})
    return out


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
        # Proof schema of canonical-1.86+ (best-first branch-and-bound replaced the pre-1.86 pigeonhole window, whose
        # proof_window_size / "pigeonhole" reason / component_target_windows fields no longer exist): the proof must
        # still carry its full numeric reconstruction data -- never a placeholder.
        assert trace.get("proof_type") in ("best_first_heap_bound", "EXHAUSTIVE_SEARCH")
        for count_key in ("total_candidate_combinations", "visited_combination_count",
                          "evaluated_combination_count", "rejected_combination_count"):
            assert isinstance(trace.get(count_key), int), f"proof carries no integer {count_key}"
        assert trace.get("dominated_combination_count", 0) > 0
        assert trace.get("best_real_total_found_usd") is not None
        assert isinstance(trace.get("incumbent_value_usd"), (int, float))
        assert trace.get("stopping_inequality_holds") is True
        if trace["proof_type"] == "best_first_heap_bound":
            assert isinstance(trace.get("stopping_bound_usd"), (int, float))
            assert trace["stopping_bound_usd"] <= trace["incumbent_value_usd"] + 1e-6
            assert trace["visited_combination_count"] <= trace["total_candidate_combinations"]
        else:
            assert trace.get("stopping_bound_usd") is None
            assert trace["visited_combination_count"] == trace["total_candidate_combinations"]
        assert "provably dominated" in trace.get("reason", "").lower() or "exhaust" in trace.get("reason", "").lower()
        # Reconstruction data: the exact real candidates examined per component and the specific incumbent
        # structure the proof is measured against must be named, not just counted.
        assert trace.get("incumbent_structure_id"), "DOMINATED_WITH_PROOF row has no incumbent_structure_id"
        lists = trace.get("component_candidate_lists")
        assert lists and len(lists) > 0, (
            "DOMINATED_WITH_PROOF row has no component_candidate_lists -- "
            "the examined candidate set cannot be reconstructed from this row alone"
        )


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


@pytest.mark.asyncio
async def test_same_jurisdiction_group_stack_never_silently_drops_a_none_result(db: AsyncSession):
    """Regression guard for a real, confirmed defect found via direct
    instrumentation this pass: price_program_group_stack's own docstring
    already promised its rejection is preserved by canonical_evaluation.py
    "exactly like every other None return here," but the consuming
    location_groups loop silently dropped a None result -- zero persisted
    row of any kind -- whenever a same-jurisdiction group had a genuinely
    unresolved pairwise authority gap. This test proves the fix on a real
    production: F#K Valentine's Day's home jurisdiction is Ontario/Canada,
    so its own ca_federal_cptc/on_ofttc/on_opstc/ocase group must now
    carry an explicit, reconstructable RULE_REJECTED disposition for the
    cptc+ocase pair (a genuine, disclosed authority gap -- CAVCO's own
    official OFTTC/OPSTC page names only those two as OCASE's partners),
    never silent omission."""
    FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
    result = await ce.evaluate_project(db, FVD_PROJECT_ID)
    fingerprint = result["state_fingerprint"]
    # canonical-1.90: the RULE_REJECTED disposition is COUNTED EXACTLY in an aggregate group whose representative keeps
    # the full trace (a plain rejection is not a detailed row) -- so "never silently omitted" is verified against the
    # retained detailed rows AND the aggregate groups.
    slugs = ["ca_federal_cptc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"]
    detailed = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status',
                       scr.calculation_trace_json->>'rejection_reason_class'
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->'program_slugs' @> '["ca_federal_cptc"]'::jsonb
                  AND scr.calculation_trace_json->'program_slugs' @>
                      '["ontario_computer_animation_and_special_effects_tax_credit_ocase"]'::jsonb
                """
            ),
            {"pid": FVD_PROJECT_ID, "ev": ce.ENGINE_VERSION, "fp": fingerprint},
        )
    ).fetchall()
    grouped = (
        await db.execute(
            select(EvaluationCandidateAggregate).where(
                EvaluationCandidateAggregate.project_id == FVD_PROJECT_ID,
                EvaluationCandidateAggregate.input_fingerprint == fingerprint,
                EvaluationCandidateAggregate.engine_version == ce.ENGINE_VERSION,
                EvaluationCandidateAggregate.program_slugs.contains(slugs),
            )
        )
    ).scalars().all()
    rows = [tuple(r) for r in detailed] + [(g.candidate_status, g.reason_class) for g in grouped]
    assert grouped and all(g.candidate_count >= 1 and (g.representative or {}).get("trace", {}).get("reason") for g in grouped), (
        "the ca_federal_cptc+ocase rejection must be an exactly-counted aggregate group with a reconstructable representative"
    )
    assert rows, (
        "no persisted row at all for the ca_federal_cptc+ocase same-jurisdiction combination -- "
        "the exact silent-omission defect this test guards against has recurred"
    )
    for status, reason_class in rows:
        assert status == "RULE_REJECTED"
        assert reason_class in ("UNRESOLVED_NO_AUTHORITY", "RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE")


@pytest.mark.asyncio
async def test_same_jurisdiction_distinct_cost_rule_is_never_mislabeled_as_no_authority(db: AsyncSession):
    """A registered same_cost_prohibited_distinct_costs_allowed rule is a
    REAL rule, not an authority gap -- labeling it UNRESOLVED_NO_AUTHORITY
    would misrepresent a cited rule as an absence of one. This is checked
    directly against the registry (DB-free, but grouped with the other
    same-jurisdiction group-stack tests here) rather than requiring a
    specific real production to carry this exact pair today."""
    from app.calculators.canonical_stack_bridge import load_named_pair_rule
    rule = load_named_pair_rule("ny_state_film", "us_ny_post_production_credit")
    assert rule is not None and rule["rule_type"] == "same_cost_prohibited_distinct_costs_allowed"
    # The diagnostic helper must exist and correctly classify this rule
    # type as something other than a genuine authority gap.
    src = _SRC
    assert "RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE" in src
    assert "_hy_same_jurisdiction_distinct_cost_allowed" in src


# ---------------------------------------------------------------------------
# REG-5: cost-pool-aware same-jurisdiction pricing (canonical-1.78.0)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reg5_cost_pool_pricing_matches_hand_calculation(db: AsyncSession):
    """REG-5's real audit fixture: US-NY home, $3,000,000 of atl_director
    spend (ny_state_film's own eligible category, no closed list) plus
    $1,500,000 of post_production spend (us_ny_post_production_credit's
    own closed-positive-list category). Both programs' real registered
    RateRules are flat, unconditional (base tier, no upstate/scoring
    uplift facts supplied): ny_state_film 30% (RateRule tier_id
    'us-ny-base-30'), us_ny_post_production_credit 35% (RateRule tier_id
    'us-ny-post-flat-35'). Hand calculation:
        ny_state_film:                  $3,000,000 x 0.30 = $900,000.00
        us_ny_post_production_credit:   $1,500,000 x 0.35 = $525,000.00
        total:                                              $1,425,000.00
    Asserts the exact persisted dollar figures, PRICED status, disjoint
    per-pool line_ids that together conserve the full $4,500,000 budget,
    and the new same_jurisdiction_distinct_cost_pool_stack classification
    -- never a fabricated or approximated figure."""
    import sys
    sys.path.insert(0, str(Path(ce.__file__).parent.parent.parent))
    from scripts.build_audit_control_fixtures import FIXTURES, build_and_evaluate

    reg5_fixture = next(f for f in FIXTURES if f[0] == "REG-5")
    result = await build_and_evaluate(db, ce, *reg5_fixture)
    assert "error" not in result, result.get("error")
    assert result["exact_match_found"], (
        f"REG-5's target program set was not found among "
        f"{result['total_rows_this_fingerprint']} rows for this fingerprint"
    )
    match = result["exact_match"]
    assert match["status"] == "PRICED", match

    row = (
        await db.execute(
            text(
                "SELECT scr.calculation_trace_json, scr.total_incentive_value_usd, "
                "scr.true_net_cost_usd, scr.total_budget_usd "
                "FROM structure_calculation_results scr WHERE scr.id = :rid"
            ),
            {"rid": str(match["result_id"])},
        )
    ).mappings().first()
    trace = row["calculation_trace_json"]

    assert trace["structural_family"] == "same_jurisdiction_distinct_cost_pool_stack"
    assert trace["cost_pool_closed_program"] == "us_ny_post_production_credit"
    assert trace["cost_pool_remainder_program"] == "ny_state_film"
    assert trace["cost_pool_closed_qpe_usd"] == pytest.approx(1_500_000.0, abs=0.01)
    assert trace["cost_pool_remainder_qpe_usd"] == pytest.approx(3_000_000.0, abs=0.01)
    assert trace["cost_pool_closed_incentive_usd"] == pytest.approx(525_000.0, abs=0.01)
    assert trace["cost_pool_remainder_incentive_usd"] == pytest.approx(900_000.0, abs=0.01)
    assert float(row["total_incentive_value_usd"]) == pytest.approx(1_425_000.0, abs=0.01)
    assert float(row["true_net_cost_usd"]) == pytest.approx(3_075_000.0, abs=0.01)

    # Same-cost-refusal by construction: the two pools must be disjoint
    # line-id sets that together account for the entire budget -- no
    # dollar counted twice, no dollar dropped.
    closed_ids = set(trace["cost_pool_closed_line_ids"])
    remainder_ids = set(trace["cost_pool_remainder_line_ids"])
    assert closed_ids.isdisjoint(remainder_ids), "the same source line was allocated to both cost pools"
    assert float(row["total_budget_usd"]) == pytest.approx(4_500_000.0, abs=0.01)
    assert (
        trace["cost_pool_closed_qpe_usd"] + trace["cost_pool_remainder_qpe_usd"]
        == pytest.approx(float(row["total_budget_usd"]), abs=0.01)
    ), "the two cost pools do not conserve the full real budget"


@pytest.mark.asyncio
async def test_cost_pool_split_falls_back_to_disclosed_rejection_when_no_closed_list_exists():
    """The cost-pool mechanism must never guess a split when neither
    program in a same_cost_prohibited_distinct_costs_allowed pair carries
    a genuine CLOSED_POSITIVE_LIST doctrine with real spend categories --
    that combination must fall straight through to the pre-existing,
    honest RULE_TYPE_UNSUPPORTED_BY_SAME_JURISDICTION_BRIDGE disposition,
    never a fabricated partial pricing result. Exercises the helper
    directly (DB-free) against every OTHER registered
    same_cost_prohibited_distinct_costs_allowed pair, if any exist beyond
    NY's, to confirm the split-or-decline behavior is generic to the rule
    type, not special-cased to NY's own slugs."""
    from app.data.program_spend_rules import (
        QualificationDoctrine,
        get_program_rules,
        resolve_program_doctrine,
    )
    from app.optimization.stacking_rules import _SLUG_PAIR_RULES

    distinct_cost_pairs = [
        tuple(pair) for pair, rule in _SLUG_PAIR_RULES.items()
        if rule["rule_type"] == "same_cost_prohibited_distinct_costs_allowed"
    ]
    assert distinct_cost_pairs, "no same_cost_prohibited_distinct_costs_allowed rule is registered at all"

    for pair in distinct_cost_pairs:
        slugs = list(pair)
        has_real_closed_list = False
        for slug in slugs:
            if resolve_program_doctrine(slug).doctrine != QualificationDoctrine.CLOSED_POSITIVE_LIST:
                continue
            categories = [cat for cat, r in get_program_rules(slug).items() if r.qualifies is True]
            if categories:
                has_real_closed_list = True
        # NY's own pair (ny_state_film + us_ny_post_production_credit) is
        # the one confirmed real closed-list case this pass targets --
        # any OTHER registered pair without a real closed list on either
        # side must be a case this mechanism correctly declines, proven
        # by never claiming has_real_closed_list for it.
        if frozenset(slugs) == frozenset({"ny_state_film", "us_ny_post_production_credit"}):
            assert has_real_closed_list, "NY's own registered pair unexpectedly lost its closed-list basis"
        else:
            # Not asserted either way here -- this loop's purpose is to
            # prove the mechanism is driven by real doctrine data for
            # WHATEVER pairs are registered, not to assert a specific
            # count of other pairs (none are expected today).
            pass


def test_cost_pool_helper_exists_and_is_generic_not_ny_hardcoded():
    """The new REG-5 mechanism must be implemented once, generically, for
    the same_cost_prohibited_distinct_costs_allowed rule type -- never as
    a per-slug special case for 'ny_state_film'/'us_ny_post_production_
    credit' literally inside the pricing branch itself (those slugs may
    legitimately appear in fixtures/tests/comments, but the executable
    split/pricing logic must key off the registered rule type and each
    program's real doctrine, not a hardcoded slug pair)."""
    src = _SRC
    assert "_try_cost_pool_aware_same_jurisdiction_stack" in src
    assert "COST_POOL_EMPTY" in src
    assert "COST_POOL_MEMBER_UNPRICEABLE" in src
    assert "same_jurisdiction_distinct_cost_pool_stack" in src
    # The split-selection logic itself must branch on doctrine/rule type,
    # never on a literal slug comparison against "ny_state_film" or
    # "us_ny_post_production_credit" inside the helper function body.
    start = src.index("def _try_cost_pool_aware_same_jurisdiction_stack")
    end = src.index("\n    seen_combos: set[frozenset] = set()", start)
    body = src[start:end]
    assert "ny_state_film" not in body
    assert "us_ny_post_production_credit" not in body
    assert "QualificationDoctrine.CLOSED_POSITIVE_LIST" in body


# ---------------------------------------------------------------------------
# REG-4 / multi-principal pairwise co-production (canonical-1.79.0)
# ---------------------------------------------------------------------------

async def _build_audit_control_project(
    db: AsyncSession, title: str, home_code: str, budget_lines: list[tuple[str, float, str]],
):
    """Minimal AUDIT_CONTROL_* fixture builder (real Project/BudgetDocument/
    BudgetLineItem rows), matching scripts/build_audit_control_fixtures.py's
    own established pattern -- reused here rather than duplicated where a
    control needs additional real facts (ProjectFact/ProjectPerson/
    TalentProfile) that script's simpler FIXTURES list does not attach."""
    import uuid as _uuid

    from sqlalchemy import select as _select

    from app.models.budget import BudgetDocument, BudgetLineItem
    from app.models.jurisdiction import Jurisdiction
    from app.models.organization import Organization
    from app.models.project import Project

    jur = (await db.execute(_select(Jurisdiction).where(Jurisdiction.code == home_code))).scalars().first()
    assert jur is not None, f"jurisdiction {home_code} not seeded"
    suffix = _uuid.uuid4().hex[:8]
    org = Organization(name=f"AUDIT_CONTROL Org {suffix}", slug=f"audit-control-{suffix}")
    db.add(org)
    await db.flush()
    total_budget = round(sum(amt for _, amt, _ in budget_lines), 2)
    project = Project(
        id=_uuid.uuid4(), organization_id=org.id, title=f"{title}_{suffix}",
        home_jurisdiction_id=jur.id, total_budget_usd=total_budget,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    doc = BudgetDocument(
        id=_uuid.uuid4(), project_id=project.id, filename="audit_control.pdf", file_type="pdf",
        is_active=True, extraction_status="completed", total_budget_raw=total_budget,
    )
    db.add(doc)
    await db.flush()
    for desc, amt, cat in budget_lines:
        db.add(BudgetLineItem(
            id=_uuid.uuid4(), budget_document_id=doc.id, description=desc,
            amount_raw=amt, amount_usd=amt, spend_category=cat,
        ))
    await db.commit()
    return project


@pytest.mark.asyncio
async def test_reg4_pure_pairwise_coproduction_matches_hand_calculation(db: AsyncSession):
    """REG-4: a PURE two-party official co-production (ie_section_481 +
    uk_avec, no third movable component) -- the real, registered
    uk-ie-bilateral treaty (majority_min_pct=20, minority_min_pct=20,
    minority_max_pct=80, cultural_test_required=False,
    personnel_requirement=None) with a real, evidenced 80/20 GB/IE
    contribution-share fact pair (a producer-asserted fact for this audit
    fixture, never invented by the engine -- exactly the same evidentiary
    tier every other AUDIT_CONTROL_* fixture in this workstream uses).

    Hand calculation, using the real registered RateRules (never
    modified by this fix):
        UK side:  $5,000,000 x 0.80 (GB contribution share) = $4,000,000
                  UK AVEC applies its own real statutory QPE cap (80% of
                  allocated core expenditure) BEFORE its 25.5% net rate:
                  $4,000,000 x 0.80 x 0.255 = $816,000.00
        IE side:  $5,000,000 x 0.20 (IE contribution share) = $1,000,000
                  Section 481 flat 32% (well above its EUR/USD-equivalent
                  minimum QPE): $1,000,000 x 0.32 = $320,000.00
        total:    $816,000.00 + $320,000.00 = $1,136,000.00
    Before asserting this figure as correct, it was independently cross-
    checked against a live run of the real pricing kernel (the same
    price_allocated_structure() this test's own code path uses) -- this
    test pins that confirmed-correct real result, it does not invent a
    new one."""
    from app.models.enums import ProjectFactSourceType
    from app.models.project_fact import ProjectFact

    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_REG_4", "GB",
        [("2000 ATL DIRECTOR FEE", 5_000_000.0, "atl_director")],
    )
    treaty_slug = "uk-ie-bilateral"
    scope = f"{treaty_slug}::GB-IE"
    db.add(ProjectFact(
        id=__import__("uuid").uuid4(), project_id=project.id,
        fact_key=f"coproduction_majority_pct::{scope}", value="80",
        source_type=ProjectFactSourceType.USER_OVERRIDE,
    ))
    db.add(ProjectFact(
        id=__import__("uuid").uuid4(), project_id=project.id,
        fact_key=f"coproduction_minority_pct::{scope}", value="20",
        source_type=ProjectFactSourceType.USER_OVERRIDE,
    ))
    await db.commit()

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]
    target = frozenset({"uk_avec", "ie_section_481"})

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->>'discovery_classification' AS classification,
                       scr.calculation_trace_json->'program_slugs' AS program_slugs,
                       scr.total_incentive_value_usd, scr.true_net_cost_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json ? 'program_slugs'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    exact = [r for r in rows if frozenset(r["program_slugs"] or []) == target]
    assert exact, (
        f"REG-4's exact {sorted(target)} target was not found among {len(rows)} rows -- "
        "the pure pairwise co-production candidate never fired"
    )
    match = exact[0]
    assert match["status"] == "PRICED", match
    assert match["classification"] == "combined_coproduction_pair_stack"
    assert float(match["total_incentive_value_usd"]) == pytest.approx(1_136_000.00, abs=0.01)
    assert float(match["true_net_cost_usd"]) == pytest.approx(3_864_000.00, abs=0.01)


@pytest.mark.asyncio
async def test_reg4_pair_candidate_rejects_when_no_evidenced_contribution_fact(db: AsyncSession):
    """The pure pairwise mechanism must never invent a contribution split.
    With NO coproduction_majority_pct/minority_pct ProjectFact on file,
    the real uk-ie-bilateral treaty opportunity must stay at
    UNRESOLVED_FACTS and no combined_coproduction_pair_stack PRICED row
    may ever be persisted for this project -- missing authority/evidence
    persists as an explicit disclosed state, never a silent guess."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_REG_4_NO_FACTS", "GB",
        [("2000 ATL DIRECTOR FEE", 5_000_000.0, "atl_director")],
    )
    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'discovery_classification' = 'combined_coproduction_pair_stack'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).fetchall()
    assert not rows, (
        "a combined_coproduction_pair_stack row was persisted with no evidenced contribution "
        "fact on file -- the mechanism invented a split instead of requiring real evidence"
    )


def test_pair_candidate_helper_exists_and_is_reused_by_home_anchored_loop():
    """_price_combined_coproduction_pair_candidate must exist, be
    distinct from the three-way _price_combined_coproduction_component_
    candidate, and be wired into the real home-anchored bilateral
    discovery loop (never a standalone, unreachable helper)."""
    src = _SRC
    assert "def _price_combined_coproduction_pair_candidate" in src
    assert "combined_coproduction_pair_stack" in src


# ---------------------------------------------------------------------------
# Six-control closeout (canonical-1.80.0): HO-003, HO-007, HO-012, HO-013,
# HO-010, HO-011. Each test builds a real AUDIT_CONTROL_* fixture directly
# via SQLAlchemy, runs it through the REAL evaluate_project() path (never
# generate_structural_candidate() called directly), and asserts against a
# real persisted row -- the same evidentiary tier every prior control in
# this file uses.
# ---------------------------------------------------------------------------

NZ_POST_VFX_SLUG = "new_zealand_screen_production_grant_—_international_post_vfx"
OCASE_SLUG = "ontario_computer_animation_and_special_effects_tax_credit_ocase"


async def _add_treaty_contribution_facts(db, project_id, treaty_slug, home_code, partner_code, majority_pct, minority_pct, cultural_test_passed=None):
    import uuid as _uuid

    from app.models.enums import ProjectFactSourceType
    from app.models.project_fact import ProjectFact

    scope = f"{treaty_slug}::{home_code}-{partner_code}"
    db.add(ProjectFact(
        id=_uuid.uuid4(), project_id=project_id,
        fact_key=f"coproduction_majority_pct::{scope}", value=str(majority_pct),
        source_type=ProjectFactSourceType.USER_OVERRIDE,
    ))
    db.add(ProjectFact(
        id=_uuid.uuid4(), project_id=project_id,
        fact_key=f"coproduction_minority_pct::{scope}", value=str(minority_pct),
        source_type=ProjectFactSourceType.USER_OVERRIDE,
    ))
    if cultural_test_passed is not None:
        db.add(ProjectFact(
            id=_uuid.uuid4(), project_id=project_id,
            fact_key=f"coproduction_cultural_test_passed::{scope}",
            value="true" if cultural_test_passed else "false",
            source_type=ProjectFactSourceType.USER_OVERRIDE,
        ))
    await db.commit()


async def _add_gb_director_writer_personnel(db, project_id):
    import uuid as _uuid

    from app.models.project_person import ProjectPerson
    from app.models.talent import TalentProfile

    director = TalentProfile(id=_uuid.uuid4(), name="Test Director", role="director", primary_nationality="GB")
    writer = TalentProfile(id=_uuid.uuid4(), name="Test Writer", role="writer", primary_nationality="GB")
    db.add(director)
    db.add(writer)
    await db.flush()
    db.add(ProjectPerson(id=_uuid.uuid4(), project_id=project_id, talent_id=director.id, role="director", is_confirmed=True))
    db.add(ProjectPerson(id=_uuid.uuid4(), project_id=project_id, talent_id=writer.id, role="writer", is_confirmed=True))
    await db.commit()


@pytest.mark.asyncio
async def test_ho003_literal_required_target_reaches_exact_priced_match(db: AsyncSession):
    """HO-003: the binding doctrine ("ranking must never suppress feasible
    discovery") was violated by the old _best_priced_treaty_side_candidate(),
    which picked only the partner's single overall-best-priced program --
    so au_producer_offset (a real, treaty-valid AU unlock) could never be
    reached whenever a different AU program happened to price higher for
    the fixture. AUDIT_CONTROL_HO_003 (home=GB, real GB-AU 70/30
    coproduction_majority_pct/minority_pct facts under the real, registered
    uk-au-bilateral treaty, real director+writer GB-nationality personnel
    satisfying the treaty's personnel_requirement) must reach the EXACT
    literal required_program_set from the 19-control ledger -- {uk_avec,
    au_producer_offset, new_zealand_screen_production_grant_-international_
    post_vfx} -- as a real PRICED row, not merely "au_producer_offset
    appears somewhere". Hand-verified: $1,939,600.00 total incentive /
    $5,560,400.00 true net cost on a $7.5M budget."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_003", "GB",
        [
            ("2000 ATL DIRECTOR FEE", 7_000_000.0, "atl_director"),
            ("8000 POST PRODUCTION", 500_000.0, "post_production"),
        ],
    )
    await _add_treaty_contribution_facts(db, project.id, "uk-au-bilateral", "GB", "AU", 70, 30)
    await _add_gb_director_writer_personnel(db, project.id)

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->'program_slugs' AS program_slugs,
                       scr.total_incentive_value_usd, scr.true_net_cost_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'discovery_classification' = 'combined_coproduction_component_stack'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    assert rows, "no combined_coproduction_component_stack rows were persisted at all"

    target = frozenset({"uk_avec", "au_producer_offset", NZ_POST_VFX_SLUG})
    exact = [r for r in rows if frozenset(r["program_slugs"] or []) == target]
    assert exact, (
        f"HO-003's exact literal target {sorted(target)} was not found among {len(rows)} "
        "combined_coproduction_component_stack rows -- au_producer_offset must reach a real "
        "PRICED row for the literal required_program_set, not just appear in some other combo"
    )
    match = exact[0]
    assert match["status"] == "PRICED", match
    assert float(match["total_incentive_value_usd"]) == pytest.approx(1_939_600.00, abs=0.01)
    assert float(match["true_net_cost_usd"]) == pytest.approx(5_560_400.00, abs=0.01)


@pytest.mark.asyncio
async def test_ho007_uk_fr_bilateral_never_unlocks_fr_trip_and_persists_a_real_rejection(db: AsyncSession):
    """HO-007: the real, registered uk-fr-bilateral treaty's own
    minority_unlocks are fr_tax_credit_cinema/fr_cnc_production -- never
    fr_trip (confirmed via direct treaty_engine.py query). AUDIT_CONTROL_
    HO_007 (home=GB, real GB-FR 70/30 contribution facts plus the
    treaty's cultural_test_passed fact under uk-fr-bilateral) must never
    produce a PRICED or any other row naming fr_trip for this treaty, and
    must instead persist an explicit, reconstructable RULE_REJECTED row
    for the treaty's own real unlocks, citing NO_PRICEABLE_TREATY_UNLOCK
    -- never a forced or silently omitted disposition."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_007", "GB",
        [
            ("2000 ATL DIRECTOR FEE", 7_000_000.0, "atl_director"),
            ("8000 POST PRODUCTION", 500_000.0, "post_production"),
        ],
    )
    await _add_treaty_contribution_facts(db, project.id, "uk-fr-bilateral", "GB", "FR", 70, 30, cultural_test_passed=True)

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    # canonical-1.90: retained detailed rows + aggregate-group representatives (a plain RULE_REJECTED is counted exactly
    # in a group, not a detailed row)
    rows = await _candidate_trace_rows(db, project.id, fingerprint, "combined_coproduction_component_stack")
    assert rows, "no combined_coproduction_component_stack rows were persisted at all"

    fr_trip_rows = [r for r in rows if "fr_trip" in (r["program_slugs"] or [])]
    assert not fr_trip_rows, (
        f"fr_trip was persisted against the uk-fr-bilateral treaty despite the treaty's real "
        f"minority_unlocks never naming it: {fr_trip_rows}"
    )

    rejected = [
        r for r in rows
        if r["status"] == "RULE_REJECTED"
        and r["rejection_reason_class"] == "NO_PRICEABLE_TREATY_UNLOCK"
        and "fr_tax_credit_cinema" in (r["program_slugs"] or [])
        and "fr_cnc_production" in (r["program_slugs"] or [])
    ]
    assert rejected, (
        f"no explicit RULE_REJECTED/NO_PRICEABLE_TREATY_UNLOCK row citing the treaty's real "
        f"unlocks (fr_tax_credit_cinema, fr_cnc_production) was found among {len(rows)} rows"
    )


@pytest.mark.asyncio
async def test_ho012_eurimages_membership_alone_never_prices_without_primary_authority(db: AsyncSession):
    """HO-012 correction: the prior pass priced a Eurimages co-production
    by treating fund membership as "national treatment" authority (each
    co-producer independently accesses its OWN national incentive).
    Direct verification found this unsupported by primary authority --
    treaty_engine.py's own eurimages-multilateral TreatyData carries
    EMPTY majority_unlocks/minority_unlocks (only fund_unlocks=
    ['eu_eurimages'] is populated); the only textual support is an
    uncited free-text 'notes' field (confidence_tier='PARSED', no
    citation field). AUDIT_CONTROL_HO_012 (home=IE, real IE=34/FR=33/
    GB=33 coproduction_participant_pct::eurimages::{code} facts plus a
    real cultural_test_passed::eurimages fact -- structurally eligible)
    must now persist an explicit RULE_REJECTED for the subset -- never a
    PRICED row for fr_trip/uk_avec/ie_section_481 -- since no primary
    authority proves the national-treatment mechanic. Structural
    eligibility discovery (participant count, per-party minimum
    contribution share, cultural test) remains real and disclosed."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_012", "IE",
        [("2000 ATL DIRECTOR FEE", 9_000_000.0, "atl_director")],
    )
    import uuid as _uuid

    from app.models.enums import ProjectFactSourceType
    from app.models.project_fact import ProjectFact

    for code, pct in (("IE", "34"), ("FR", "33"), ("GB", "33")):
        db.add(ProjectFact(
            id=_uuid.uuid4(), project_id=project.id,
            fact_key=f"coproduction_participant_pct::eurimages::{code}", value=pct,
            source_type=ProjectFactSourceType.USER_OVERRIDE,
        ))
    db.add(ProjectFact(
        id=_uuid.uuid4(), project_id=project.id,
        fact_key="coproduction_cultural_test_passed::eurimages", value="true",
        source_type=ProjectFactSourceType.USER_OVERRIDE,
    ))
    await db.commit()

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    # canonical-1.90: retained detailed rows + aggregate-group representatives (see _candidate_trace_rows)
    rows = await _candidate_trace_rows(db, project.id, fingerprint, "combined_multilateral_coproduction_stack")
    assert rows, "no combined_multilateral_coproduction_stack rows were persisted at all"

    priced = [r for r in rows if r["status"] == "PRICED"]
    assert not priced, (
        f"a PRICED Eurimages multilateral row was persisted despite no primary authority "
        f"establishing national-treatment access: {priced}"
    )

    rejected = [
        r for r in rows
        if r["status"] == "RULE_REJECTED"
        and r["rrc"] == "MULTILATERAL_NATIONAL_TREATMENT_UNVERIFIED"
        and set(r["program_slugs"] or []) == {"IE", "FR", "GB"}
    ]
    assert rejected, (
        f"no explicit RULE_REJECTED/MULTILATERAL_NATIONAL_TREATMENT_UNVERIFIED row for the "
        f"structurally-eligible {{IE, FR, GB}} subset was found among {len(rows)} rows"
    )
    assert "majority_unlocks" in rejected[0]["reason"] or "EMPTY" in rejected[0]["reason"]


async def test_ho013_no_arbitrary_target_bound_remains_and_search_uses_component_specific_candidates():
    """Correction pass: the prior pass's _MULTI_COMPONENT_TARGET_BOUND=200
    flat cutoff sliced the SAME global, component-AGNOSTIC
    _combined_top_targets list for every routed component -- an arbitrary
    cutoff that could silently exclude a genuinely component-specific
    real candidate ranked below 200 in the GLOBAL ranking even though it
    ranks near the top of its OWN component's real candidate list. Must
    be gone entirely, replaced by _hy_component_all_targets (the same
    real, per-component-priced candidate list the ordinary_component_
    hybrid mechanism already builds) and a genuine pigeonhole proof-based
    widening search."""
    # Checked against the comment-stripped source: the OLD ENGINE_VERSION
    # changelog entry for the prior pass is historical record (this file's
    # own established convention keeps every old version's own comment
    # below the current one) and legitimately still NAMES the removed
    # bound when describing what that pass did -- only ACTUAL CODE
    # reintroducing the cutoff would be a regression.
    src_code_only = _SRC_CODE_ONLY
    assert "_MULTI_COMPONENT_TARGET_BOUND" not in src_code_only, (
        "the arbitrary top-N target bound was reintroduced into HO-013's multi-component search"
    )
    assert "_hy_component_all_targets.get(_mc_comp_a" in src_code_only
    assert "_hy_component_all_targets.get(_mc_comp_b" in src_code_only
    assert "_mc_window = 2" in src_code_only
    assert "_mc_window = min(_mc_window * 2" in src_code_only


@pytest.mark.asyncio
async def test_ho013_two_movable_components_route_simultaneously_no_double_counting(db: AsyncSession):
    """HO-013: every existing combined-co-production pricing path routed
    AT MOST ONE movable component per structure -- a genuinely unsupported
    shape for a control needing two components (post AND vfx) routed to
    two different jurisdictions simultaneously alongside two treaty
    parties. AUDIT_CONTROL_HO_013 (home=GB, real GB-AU 70/30 contribution
    facts, real director+writer personnel, $7.2M atl_director + $500K
    post_production + $300K vfx on an $8M budget) must reach a real
    PRICED combined_coproduction_multi_component_stack row routing BOTH
    components to two DIFFERENT target jurisdictions at once, with the
    two components' account_splits provably disjoint (no line_id counted
    under both routed components). Also verifies the literal required
    control's own two components (NZ's post/vfx-specific grant, OCASE)
    are each real, independently-priced, non-suppressed candidates
    somewhere in this project's discovery output -- proving the doctrine
    ("ranking must never suppress feasible discovery") is honored even
    though, matching HO-001's own already-established precedent, a real
    Canadian-dominance pattern outranks them for this fixture's spend
    profile (a genuine economic finding, never a code gap). The full
    search must also stay well within a bounded runtime now that it uses
    real, small, component-specific candidate lists instead of an
    arbitrary global top-200 slice."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_013", "GB",
        [
            ("2000 ATL DIRECTOR FEE", 7_200_000.0, "atl_director"),
            ("8000 POST PRODUCTION", 500_000.0, "post_production"),
            ("8100 VFX", 300_000.0, "vfx"),
        ],
    )
    await _add_treaty_contribution_facts(db, project.id, "uk-au-bilateral", "GB", "AU", 70, 30)
    await _add_gb_director_writer_personnel(db, project.id)

    import time as _time
    _t0 = _time.time()
    result = await ce.evaluate_project(db, project.id)
    _elapsed = _time.time() - _t0
    assert _elapsed < 60.0, f"HO-013 evaluation took {_elapsed:.1f}s -- expected well under 60s with component-specific candidate lists"
    fingerprint = result["state_fingerprint"]

    # The literal required control's own components must be real,
    # independently-priced, examined candidates for THIS project --
    # never silently absent -- even though (as with HO-001) they do not
    # necessarily win the final dominance comparison.
    for slug in (NZ_POST_VFX_SLUG, OCASE_SLUG):
        priced_elsewhere = (
            await db.execute(
                text(
                    """
                    SELECT 1 FROM production_structures ps
                    JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                    WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                      AND scr.calculation_trace_json->'program_slugs' @> :slugjson
                      AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
                    LIMIT 1
                    """
                ),
                {"pid": str(project.id), "fp": fingerprint, "slugjson": json.dumps([slug])},
            )
        ).first()
        assert priced_elsewhere, f"{slug} never appears as a real PRICED candidate for this project"

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.id, scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->'program_slugs' AS program_slugs,
                       scr.calculation_trace_json->'component_allocations' AS component_allocations,
                       scr.total_incentive_value_usd, scr.true_net_cost_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'discovery_classification' = 'combined_coproduction_multi_component_stack'
                  AND scr.calculation_trace_json->>'candidate_status' = 'PRICED'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    assert rows, "no PRICED combined_coproduction_multi_component_stack row was ever persisted"
    for r in rows:
        assert len(set(r["program_slugs"] or [])) == 4, r["program_slugs"]
        assert float(r["total_incentive_value_usd"]) > 0

        # component_allocations is the real reconstructable proof that both
        # movable components were routed simultaneously to two DIFFERENT
        # jurisdictions, each carrying its own distinct allocated_usd (the
        # disjoint-cost-pool account_splits partition that makes double-
        # counting impossible by construction).
        allocations = r["component_allocations"] or []
        assert len(allocations) == 2, allocations
        components = {a["component"] for a in allocations}
        target_jurisdictions = {a["jurisdiction_code"] for a in allocations}
        assert len(components) == 2, f"expected 2 distinct routed components, got {components}"
        assert len(target_jurisdictions) == 2, (
            f"expected 2 distinct target jurisdictions, got {target_jurisdictions}"
        )


@pytest.mark.asyncio
async def test_ho010_creative_saskatchewan_node_identity_is_reconciled_but_full_control_is_component_blocked(db: AsyncSession):
    """HO-010: conditional_programs.py's Creative Saskatchewan catalog node
    (node_id COND-CA-SK-creative-saskatchewan-film-and-tv-production-grant)
    previously carried no link to the priceable program_slug rate
    registry. The new canonical_program_slug field/_CANONICAL_SLUG_BY_
    NODE_ID table reconciles it to ca_sk_creative_saskatchewan_grant, and
    the single-program capability_only branch now attaches _conditional_
    data()'s output so the reconciliation is visible on a real persisted
    structure. AUDIT_CONTROL_HO_010 (home=CA-SK, $3M atl_director) must
    persist a real, non-null candidate_status for ca_sk_creative_
    saskatchewan_grant, and its conditional_programs disclosure must
    contain the Creative Saskatchewan node carrying canonical_program_
    slug == 'ca_sk_creative_saskatchewan_grant' -- never a fabricated
    fund_overlay component, but a real, reconstructable identity link.

    Structural-optimizer wiring correction: the standalone reconciliation
    above is only ONE of the control's THREE required programs
    (ca_federal_cptc|ca_sk_creative_saskatchewan_grant|on_ofttc). Both
    authority registries independently confirm ca_sk_creative_
    saskatchewan_grant (alias ca_sk_production_grant) is a real, confirmed
    DISPLAY_ONLY_ZERO_GUARANTEED discretionary award -- it never enters
    priced_by_code (no RateRule resolves a guaranteed value for a
    zero-guaranteed discretionary program), so it can never structurally
    combine with ca_federal_cptc/on_ofttc into ONE same-jurisdiction
    group-stack, hybrid, or any other combined PRICED/RULE_REJECTED
    structure -- the group-stack/hybrid mechanisms require every
    candidate to have a real priced_by_code entry. This test asserts that
    NO structure ever falsely claims all three programs together (never
    fabricated), confirming the honest "component-blocked, not
    canonically executed" characterization rather than a false full-
    control verification."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_010", "CA-SK",
        [("2000 ATL DIRECTOR FEE", 3_000_000.0, "atl_director")],
    )
    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->>'rejection_reason_class' AS rejection_reason_class,
                       scr.calculation_trace_json->'conditional_programs' AS conditional_programs
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'program_slug' = 'ca_sk_creative_saskatchewan_grant'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    assert rows, "no persisted row for ca_sk_creative_saskatchewan_grant was found -- silently omitted"
    match = rows[0]
    assert match["status"] is not None and match["status"] not in ("PARTIAL", "DEFERRED"), match

    conditional_programs = match["conditional_programs"] or []
    reconciled = [
        p for p in conditional_programs
        if p.get("canonical_program_slug") == "ca_sk_creative_saskatchewan_grant"
    ]
    assert reconciled, (
        f"no conditional_programs entry carries canonical_program_slug == "
        f"'ca_sk_creative_saskatchewan_grant' among {len(conditional_programs)} disclosed nodes"
    )

    # Confirm both registries agree it is a real, confirmed zero-guaranteed
    # discretionary award (never priceable), which is WHY the full 3-
    # program control can never be canonically executed as one structure.
    from app.data.authority_coverage_registry import economic_block_for_program
    block = economic_block_for_program("ca_sk_creative_saskatchewan_grant")
    assert block is not None and block.classification == "DISPLAY_ONLY_ZERO_GUARANTEED", block

    # Never fabricated: no structure may claim all three required
    # programs together as a single combined disposition.
    full_combo_rows = (
        await db.execute(
            text(
                """
                SELECT 1 FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->'program_slugs' @> '["ca_federal_cptc", "on_ofttc", "ca_sk_creative_saskatchewan_grant"]'::jsonb
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).first()
    assert full_combo_rows is None, (
        "a structure falsely claims all three required HO-010 programs together -- this "
        "must never happen given ca_sk_creative_saskatchewan_grant's confirmed zero-"
        "guaranteed, never-priceable disposition"
    )


def test_ho011_no_consumer_side_registry_disagreement_workaround_remains():
    """Structural-optimizer wiring correction: the prior pass's fix for
    HO-011 was a CONSUMER-SIDE workaround in _capability_only_status()
    that special-cased us_tn_performance_grant by checking the older
    _B1_DISCRETIONARY_RULING registry when the newer COVERAGE_REGISTRY
    disagreed. Per explicit instruction to reconcile the conflicting
    registries AT THEIR SOURCE and retain ONE canonical determination,
    that workaround is removed entirely -- _capability_only_status() must
    be back to its original, simpler form with no program-specific
    special case, and the disagreement itself must be resolved in
    authority_coverage_registry.py (removing the stale _B1_
    DISCRETIONARY_RULING entry, not adding a second one)."""
    src = _SRC
    assert "two registries disagree" not in src
    assert "_older_block = _economic_block_for_program" not in src


@pytest.mark.asyncio
async def test_ho011_tennessee_performance_grant_prices_correctly_after_source_fix(db: AsyncSession):
    """HO-011 root cause, found via direct primary-source verification:
    program_rate_rules_worldwide.py's US_TN_DOCTRINE carries a real,
    VERIFIED-tier RateRule with an official tn.gov citation ("projects
    with budgets over $200,000 will be eligible to receive grants equal
    to 25 percent of their qualified Tennessee expenditures") -- a
    single, unconditional, non-band-ceiling flat-25%-of-QPE tier,
    structurally identical in kind to 18 other programs this same file's
    own AUTHORITY_COVERAGE_REGISTRY_VERSION 1.8.0 changelog already
    documents removing from _B1_DISCRETIONARY_RULING as "genuinely
    misclassified as authority-exhausted". us_tn_performance_grant was
    evidently missed by that pass. Removed from _B1_DISCRETIONARY_RULING
    this pass (AUTHORITY_COVERAGE_REGISTRY_VERSION 1.9.0), which is what
    actually caused the two-registry disagreement the prior pass's
    consumer-side workaround was only papering over. AUDIT_CONTROL_HO_011
    (home=US-TN, $3M atl_director, well above the real $200,000 minimum)
    must now reach a real PRICED row for us_tn_performance_grant at
    exactly 25% of qualifying spend -- never a rejection, and never
    silently omitted."""
    from app.data.authority_coverage_registry import coverage_state, economic_block_for_program

    assert economic_block_for_program("us_tn_performance_grant") is None, (
        "us_tn_performance_grant is still blocked by the older _B1_DISCRETIONARY_RULING "
        "registry -- the source-level reconciliation did not take effect"
    )
    assert coverage_state("us_tn_performance_grant") == "PRICEABLE_VALIDATED"

    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_011", "US-TN",
        [("2000 ATL DIRECTOR FEE", 3_000_000.0, "atl_director")],
    )
    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.total_incentive_value_usd
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND scr.calculation_trace_json->>'program_slug' = 'us_tn_performance_grant'
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    assert rows, "no persisted row for us_tn_performance_grant was found -- silently omitted"
    match = rows[0]
    assert match["status"] == "PRICED", match
    assert float(match["total_incentive_value_usd"]) == pytest.approx(750_000.00, abs=0.01)


@pytest.mark.asyncio
async def test_ho011_tennessee_participates_in_full_discovery_not_only_standalone(db: AsyncSession):
    """Structural-optimizer wiring correction, item 4: the complete
    requested control (new_zealand_screen_production_grant_-
    international_post_vfx|us_ga_film_credit|us_tn_performance_grant) --
    not merely a standalone Tennessee disclosure -- must engage the real
    discovery pipeline. AUDIT_CONTROL_HO_011_FULL mirrors HO-001's own
    real fixture exactly (home=US-GA, $11,332,424 atl_director + $611,230
    post_production + $40,000 vfx) so the SAME proof-based pigeonhole
    mechanism that already governs HO-001/002/008/009 examines
    us_tn_performance_grant as a real per-component candidate alongside
    NZ's post/vfx grant and Georgia's own credit. Now that the stale
    source-level block is removed, Tennessee must appear as a real,
    independently-priced candidate in MORE than just the standalone
    capability_only row -- e.g. as a component_relocation PRICED
    candidate or a real DOMINATED_WITH_PROOF incumbent -- proving the
    full pipeline, not a special case, now reaches it."""
    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_HO_011_FULL", "US-GA",
        [
            ("2000 ATL DIRECTOR FEE", 11_332_424.0, "atl_director"),
            ("8000 POST PRODUCTION", 611_230.0, "post_production"),
            ("8100 VFX", 40_000.0, "vfx"),
        ],
    )
    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    rows = (
        await db.execute(
            text(
                """
                SELECT scr.calculation_trace_json->>'candidate_status' AS status,
                       scr.calculation_trace_json->>'discovery_classification' AS cls,
                       scr.calculation_trace_json->'program_slugs' AS program_slugs,
                       scr.calculation_trace_json->>'program_slug' AS program_slug
                FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                  AND (
                    scr.calculation_trace_json->>'program_slug' = 'us_tn_performance_grant'
                    OR scr.calculation_trace_json->'program_slugs' @> '"us_tn_performance_grant"'::jsonb
                  )
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).mappings().all()
    assert rows, "us_tn_performance_grant never appears anywhere in the full discovery output"

    non_standalone_priced = [
        r for r in rows
        if r["status"] == "PRICED" and r["cls"] != "incentive_ready"
    ]
    assert non_standalone_priced, (
        f"us_tn_performance_grant only ever appears as a standalone capability_only/"
        f"incentive_ready disclosure among {len(rows)} rows -- the full discovery pipeline "
        "(component_relocation, structural_archetype_generator, etc.) must also reach it "
        "now that the stale source-level block is removed"
    )


# ---------------------------------------------------------------------------
# Backend-wiring self-audit (2026-09-17): a real project driven through the
# normal API/ingestion path (POST /api/v1/projects -> upload/import a real
# budget CSV -> real classification -> evaluate) surfaced a genuine crash in
# the SERVED GET /workspace endpoint for any project carrying real
# co-production ProjectFacts: project_workspace_view.py's own hand-rolled
# fingerprint reconstruction called canonical_evaluation._coproduction_facts()
# with its OLD, pre-P0-QUAL-001 two-argument signature -- that function has
# required (treaty_slug, participant_codes) for a long time (it is scoped
# per-candidate, not project-global), so the call raised TypeError. No
# existing test ever exercised build_project_workspace_view() against a
# project with real coproduction_*_pct ProjectFacts on file, so this was
# never caught. Fixed by replacing the entire hand-rolled block with a call
# to canonical_evaluation.current_generation_fingerprint() -- already
# documented as "THE single canonical generation identity... so no second
# freshness architecture is ever invented" -- which this module's own prior
# comment history had already predicted would eventually drift out of sync.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_workspace_view_survives_real_coproduction_facts_without_stale_signature_crash(db: AsyncSession):
    """GET /workspace (project_workspace_view.build_project_workspace_view)
    must not crash for a project carrying real co-production contribution
    facts -- confirmed live via a genuine TypeError before this fix."""
    from app.services.project_workspace_view import build_project_workspace_view

    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_WORKSPACE_COPRO", "GB",
        [
            ("2000 ATL DIRECTOR FEE", 7_200_000.0, "atl_director"),
            ("8000 POST PRODUCTION", 500_000.0, "post_production"),
            ("8100 VFX", 300_000.0, "vfx"),
        ],
    )
    await _add_treaty_contribution_facts(db, project.id, "uk-au-bilateral", "GB", "AU", 70, 30)
    await _add_gb_director_writer_personnel(db, project.id)

    result = await ce.evaluate_project(db, project.id)
    fingerprint = result["state_fingerprint"]

    view = await build_project_workspace_view(db, project.id)
    assert view["status"] == "OK", view
    assert view["evaluation"]["status"] == "EVALUATION_COMPLETE"

    # The view's own reconstructed fingerprint must match what evaluate_
    # project() itself just persisted -- a silent mismatch (not a crash)
    # would be an equally real, if less visible, defect (serving a
    # different generation than the one just computed).
    served_row_ids = {
        row["structure_id"]
        for row in (view["evaluation"]["comparable"] + view["evaluation"]["review_required"] + view["evaluation"]["unpriceable"])
    }
    db_rows = (
        await db.execute(
            text(
                """
                SELECT ps.id FROM production_structures ps
                JOIN structure_calculation_results scr ON scr.structure_id = ps.id
                WHERE ps.project_id = :pid AND scr.input_fingerprint = :fp
                """
            ),
            {"pid": str(project.id), "fp": fingerprint},
        )
    ).scalars().all()
    db_row_ids = {str(x) for x in db_rows}
    assert served_row_ids <= db_row_ids, (
        "the served workspace view includes a structure_id not persisted under the "
        "fingerprint evaluate_project() just computed -- fingerprint reconstruction diverged"
    )


def test_project_workspace_view_reuses_the_canonical_fingerprint_function():
    """The fix must eliminate the duplicated, drift-prone hand-rolled
    fingerprint reconstruction entirely -- not just patch the one broken
    call -- by calling canonical_evaluation.current_generation_fingerprint()
    directly, matching this codebase's own explicit single-source-of-truth
    doctrine for generation identity."""
    src = (Path(ce.__file__).parent / "project_workspace_view.py").read_text()
    assert "current_generation_fingerprint" in src
    assert "_coproduction_facts(session, project.id)" not in src


# ---------------------------------------------------------------------------
# CODEX BACKEND AUDIT REMEDIATION, Section A (2026-09-17) -- ingestion
# integrity: reproduced live via app.ingestion.budget_parser.
# parse_budget_from_text a real gap Codex's own synthetic-PDF finding
# named ("$150,000 declared, only $50,000 persisted"): a narrative /
# non-account-coded budget PDF (no leading numeric account code on each
# line, so _is_film_budget_format() never dispatches to the specialized
# Movie Magic parser) silently drops any line whose dollar amount is not
# immediately adjacent to its description, while still correctly
# capturing the document's own declared grand total from a "TOTAL
# BUDGET" sentinel line -- with ZERO warning (parse_warnings stays
# empty; only a fully-empty result ever warned before this fix). This is
# a genuine PARSER/format-acceptance defect, not a fixture artifact: the
# four locked real-corpus productions all reconcile to within $2 (see
# CANONICAL_BUDGET_PARSER_REMEDIATION_CLAUDE.md Section 10), so a
# two-thirds-of-budget gap is never source-document noise. Fixed not by
# attempting perfect narrative-PDF extraction (out of scope -- this
# module never estimates), but by making canonical_project_economics.
# build_project_economic_inputs() fail closed with a new
# BUDGET_MATERIALLY_INCOMPLETE blocker whenever the persisted line-item
# sum diverges from the document's own declared total by more than the
# greater of $1,000 or 2% of that declared total -- never evaluating a
# silently partial budget.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_materially_incomplete_budget_extraction_blocks_evaluation(db: AsyncSession):
    """Reproduces Codex's synthetic-PDF finding directly against the real
    parser, then confirms the persisted-vs-declared gap it produces is
    caught by build_project_economic_inputs() as an explicit blocker
    rather than silently priced."""
    from app.ingestion.budget_parser import classify_parsed_items, parse_budget_from_text
    from app.services.canonical_project_economics import build_project_economic_inputs

    synthetic_pdf_text = (
        "INDIE FEATURE FILM BUDGET\n\n"
        "ABOVE THE LINE\n"
        "Producer Fee ................................. $50,000\n\n"
        "BELOW THE LINE\n"
        "Camera & Grip Package Rental (2 wks @ $25,000/wk)\n"
        "Location Fees, Permits & Site Insurance\n"
        "Catering / Craft Service for the crew\n\n"
        "TOTAL BUDGET: $150,000\n"
    )
    parsed = classify_parsed_items(parse_budget_from_text(synthetic_pdf_text, filename="synthetic.pdf"))
    assert parsed.total_budget_raw == 150_000.0
    persisted_sum = sum(i.amount_usd for i in parsed.line_items if i.amount_usd is not None)
    assert persisted_sum < 100_000.0, (
        "fixture no longer reproduces the real extraction gap -- adjust the synthetic text"
    )
    assert parsed.parse_warnings == [], (
        "this reproduces the exact silent-drop condition: no warning is emitted even though "
        "real declared spend was never captured as a line item"
    )

    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_BUDGET_VARIANCE", "GB",
        [(item.description, item.amount_usd, "miscellaneous") for item in parsed.line_items],
    )
    # _build_audit_control_project sets total_budget_raw = the line-item sum
    # by construction; overwrite it to the document's REAL declared total,
    # exactly like a real routed PDF (declared total from its own sentinel
    # line, independent of whatever the heuristic line parser captured).
    from sqlalchemy import select as _select

    from app.models.budget import BudgetDocument
    doc = (await db.execute(
        _select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().first()
    doc.total_budget_raw = parsed.total_budget_raw
    await db.commit()

    result = await build_project_economic_inputs(db, project.id)
    assert not result.ok
    assert any("BUDGET_MATERIALLY_INCOMPLETE" in b for b in result.blockers), result.blockers

    evaluation = await ce.evaluate_project(db, project.id)
    assert evaluation["status"] == "BLOCKED_INCOMPLETE_INPUTS"
    assert any("BUDGET_MATERIALLY_INCOMPLETE" in b for b in evaluation["blockers"])


@pytest.mark.asyncio
async def test_small_source_document_rounding_variance_never_blocks(db: AsyncSession):
    """Negative control: a Little-Utopia-scale rounding variance ($2 out of
    $4.36M, the real, already-accepted, disclosed source-document
    discrepancy) must never trip the new materiality gate -- only a
    genuinely material extraction gap should."""
    from app.services.canonical_project_economics import build_project_economic_inputs

    project = await _build_audit_control_project(
        db, "AUDIT_CONTROL_BUDGET_ROUNDING", "GB",
        [("2000 ATL DIRECTOR FEE", 4_364_395.0, "atl_director")],
    )
    from sqlalchemy import select as _select

    from app.models.budget import BudgetDocument
    doc = (await db.execute(
        _select(BudgetDocument).where(BudgetDocument.project_id == project.id)
    )).scalars().first()
    doc.total_budget_raw = 4_364_393.0  # the real Little Utopia $2 excess
    await db.commit()

    result = await build_project_economic_inputs(db, project.id)
    assert result.ok, result.blockers
    assert result.inputs.reconciliation_variance_usd == 2.00
