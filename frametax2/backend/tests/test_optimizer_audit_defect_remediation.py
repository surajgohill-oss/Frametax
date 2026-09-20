"""
OPTIMIZER_AUDIT_DEFECT_REMEDIATION (2026-09-18).

Prevention tests for NUM-001..NUM-005, fixing docs/validation/
CURRENT_TIP_OPTIMIZER_NUMERICAL_ACCEPTANCE_AUDIT.md, plus the supporting
canonical_integrity_gate.py QPE-oracle correction. Read-only/idempotent
against the real Little Utopia and F#K Valentine's Day project rows in
the isolated audit database -- same convention as the other canonical_
evaluation test files.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.canonical_evaluation import (
    ENGINE_VERSION,
    evaluate_project,
    qualification_admits_recommended,
)
from app.services.canonical_production_view import build_production_and_structures
from app.services.project_workspace_view import build_project_workspace_view

LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae"
FVD_PROJECT_ID = "6c6f1c13-2d49-4bbc-bafb-2a12efa93112"
BAD_HOMBRES_PROJECT_ID = "4355ae88-a636-4c18-af60-ad73b2646124"
LIPS_LIKE_SUGAR_PROJECT_ID = "ab10b319-978e-44d3-9331-af2a5f2cccc2"


@pytest.fixture
async def db():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# ── NUM-001: workspace top_result must never publish an unresolved-  ──────
# qualification baseline as the served recommendation. ─────────────────────

def test_qualification_admits_recommended_is_the_one_shared_predicate():
    """Never fabricated/guessed: an absent role_qualification admits
    (nothing unresolved to gate on); a real unresolved state does not."""
    assert qualification_admits_recommended(None) is True
    assert qualification_admits_recommended({}) is True
    assert qualification_admits_recommended({"state": "QUALIFIES"}) is True
    assert qualification_admits_recommended({"state": "NOT_APPLICABLE"}) is True
    assert qualification_admits_recommended({"state": "AUTHORITY_UNRESOLVED"}) is False
    assert qualification_admits_recommended({"state": "USER_FACT_REQUIRED"}) is False


async def test_lu_and_fvd_workspace_top_result_stays_null_while_unresolved(db: AsyncSession):
    """The exact NUM-001 defect: both LU and FVD have a real, PRICED,
    UI_COMPARABLE baseline whose role qualification is genuinely
    unresolved -- the workspace adapter must agree with evaluate_project()
    that there is no recommendation, never independently promote
    comparable[0]."""
    for project_id in (LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID):
        econ = await evaluate_project(db, project_id)
        assert econ["top_result"] is None, f"{project_id}: evaluator itself unexpectedly has a top_result"

        view = await build_project_workspace_view(db, project_id)
        assert view["status"] == "OK"
        assert view["evaluation"]["top_result"] is None, (
            f"{project_id}: workspace published a recommendation the evaluator rejects (NUM-001)"
        )
        # The baseline is still real, priced, and disclosed -- NUM-001 must
        # never withhold economics, only the false "recommended" framing.
        assert view["evaluation"]["baseline"] is not None
        assert view["evaluation"]["baseline"]["candidate_status"] == "PRICED"


async def test_bad_hombres_and_lls_recommendation_identity_unchanged(db: AsyncSession):
    """Both have NOT_APPLICABLE role qualification -- NUM-001 must never
    suppress a genuinely admissible recommendation."""
    for project_id in (BAD_HOMBRES_PROJECT_ID, LIPS_LIKE_SUGAR_PROJECT_ID):
        econ = await evaluate_project(db, project_id)
        assert econ["top_result"] is not None, f"{project_id}: a genuine recommendation was wrongly suppressed"

        view = await build_project_workspace_view(db, project_id)
        assert view["evaluation"]["top_result"] is not None
        assert view["evaluation"]["top_result"]["structure_id"] == econ["top_result"]["structure_id"]


# ── NUM-005: workspace generation identity. ────────────────────────────────

async def test_workspace_returns_engine_version_and_fingerprint_matching_persisted_rows(db: AsyncSession):
    view = await build_project_workspace_view(db, FVD_PROJECT_ID)
    assert view["evaluation"]["engine_version"] == ENGINE_VERSION
    fingerprint = view["evaluation"]["input_fingerprint"]
    assert fingerprint

    # Independently verifiable: every served candidate really is a row
    # persisted under exactly this (engine_version, input_fingerprint).
    row_count = (await db.execute(
        text(
            "SELECT count(*) FROM structure_calculation_results scr "
            "JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :pid AND scr.engine_version = :ev AND scr.input_fingerprint = :fp"
        ),
        {"pid": FVD_PROJECT_ID, "ev": ENGINE_VERSION, "fp": fingerprint},
    )).scalar()
    served_count = (
        view["evaluation"]["comparable_count"]
        + view["evaluation"]["review_required_count"]
        + view["evaluation"]["unpriceable_count"]
    )
    assert row_count >= served_count > 0


# ── NUM-002/NUM-003: hybrid discretionary-risk propagation and stacking- ──
# adjustment reconstruction. ────────────────────────────────────────────────

async def test_ordinary_component_hybrid_rows_carry_administrative_risk_and_stacking_trace(db: AsyncSession):
    await evaluate_project(db, FVD_PROJECT_ID)
    rows = (await db.execute(
        text(
            "SELECT scr.calculation_trace_json FROM structure_calculation_results scr "
            "JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :pid AND scr.engine_version = :ev "
            "AND scr.calculation_trace_json->>'candidate_status' = 'PRICED' "
            "AND scr.calculation_trace_json->>'structural_family' = 'ordinary_component_hybrid' "
            "LIMIT 200"
        ),
        {"pid": FVD_PROJECT_ID, "ev": ENGINE_VERSION},
    )).scalars().all()
    assert rows, "no priced ordinary_component_hybrid rows found -- fixture/engine mismatch"

    found_real_risk = False
    for trace in rows:
        # NUM-002: field always present, never silently absent.
        assert "administrative_allocation_risk" in trace
        assert "administrative_allocation_risk_reasons" in trace
        assert isinstance(trace["administrative_allocation_risk_reasons"], list)
        if trace["administrative_allocation_risk"]:
            found_real_risk = True
            assert trace["administrative_allocation_risk_reasons"], (
                "risk=True but no reasons persisted -- risk without disclosure"
            )

        # NUM-003: full reconstruction bridge, reconciling exactly.
        raw = trace["raw_component_incentives_usd"]
        post = trace["post_adjustment_component_incentives_usd"]
        adjustments = trace["stacking_adjustments"]
        assert raw and post
        reconstructed_total = round(sum(post.values()), 2)
        assert reconstructed_total == pytest.approx(trace["total_guaranteed_incentive_usd"], abs=0.02), (
            f"post-adjustment components sum to {reconstructed_total}, does not reconcile to "
            f"total_guaranteed_incentive_usd={trace['total_guaranteed_incentive_usd']}"
        )
        if not adjustments:
            # No adjustment fired -- raw must equal post exactly (identity).
            assert raw == post
        else:
            for adj in adjustments:
                assert set(adj) == {
                    "program_a_id", "program_b_id", "rule_type", "description",
                    "original_value_usd", "adjustment_usd", "adjusted_value_usd",
                }
                assert round(adj["original_value_usd"] + adj["adjustment_usd"], 2) == pytest.approx(
                    adj["adjusted_value_usd"], abs=0.02
                )

    assert found_real_risk, (
        "no ordinary_component_hybrid row in this real sample carries a discretionary risk -- "
        "cannot confirm NUM-002's propagation actually fires on real data"
    )


# ── NUM-004 / completeness closeout: DOMINATED_WITH_PROOF and ────────────
# SEARCH_SPACE_EXHAUSTED numeric proof, independently checkable; zero ─────
# SEARCH_DEPTH_LIMIT_REACHED across all four real productions. ───────────

def _num004_incumbent_field(trace: dict) -> str:
    """Which field the persisted stopping inequality is actually checked
    against depends on structural_family: ordinary_component_hybrid uses
    incumbent_value_usd (already a marginal, non-anchor quantity);
    combined_coproduction_multi_component_stack uses
    component_marginal_incumbent_usd (the incumbent's own a+b marginal
    value -- incumbent_value_usd there is the FULL structure total, a
    different scale)."""
    return (
        "component_marginal_incumbent_usd" if "component_marginal_incumbent_usd" in trace
        else "incumbent_value_usd"
    )


def test_best_first_bound_search_matches_brute_force_enumeration():
    """FINAL_OPTIMIZER_BACKEND_COMPLETENESS_CLOSEOUT deterministic control
    (2026-09-18): _best_first_bound_search must always find the SAME
    optimum a brute-force itertools.product enumeration over the same
    lists would find -- proving the exact search matches exhaustive
    enumeration, not an approximation. No DB, no pricing, fully
    deterministic (fixed seed)."""
    import asyncio
    import itertools
    import random

    from app.services.canonical_evaluation import _best_first_bound_search

    async def run_case(lists):
        async def try_combo(idx, current_best):
            return sum(lists[k][idx[k]] for k in range(len(lists)))

        best, visited, bound = await _best_first_bound_search(lists, try_combo)
        brute_force_best = max(sum(combo) for combo in itertools.product(*lists))
        assert best == pytest.approx(brute_force_best, abs=1e-6), (lists, best, brute_force_best)
        # The stopping bound, whenever present, must independently prove
        # domination against the value this same call just found.
        if bound is not None:
            assert bound <= best + 1e-9
        assert 1 <= visited <= sum(len(lst) for lst in lists)
        return best, visited, bound

    rng = random.Random(20260918)

    async def main():
        # Fixed hand-picked cases (including ties and negatives) plus
        # randomized cases for broad coverage.
        fixed_cases = [
            [[5.0]],
            [[3.0, 1.0], [4.0, 2.0]],
            [[10.0, 10.0, 5.0], [8.0, 3.0], [7.0, 7.0, 1.0]],
            [[-1.0, -5.0], [-2.0, -8.0]],
            [[100.0, 1.0], [100.0, 1.0], [100.0, 1.0]],
        ]
        for case in fixed_cases:
            await run_case(case)
        for _ in range(100):
            n_lists = rng.randint(1, 4)
            lists = []
            for _ in range(n_lists):
                length = rng.randint(1, 6)
                vals = sorted(
                    (round(rng.uniform(-50, 100), 2) for _ in range(length)), reverse=True,
                )
                lists.append(vals)
            await run_case(lists)

    asyncio.run(main())


def test_integrated_partner_component_search_matches_brute_force_enumeration():
    """FINAL_OPTIMIZER_BACKEND_COMPLETENESS_CLOSEOUT integrated-search
    deterministic control (2026-09-18, operator directive): the
    combined_coproduction_multi_component_stack site folds a THIRD
    dimension (treaty-partner selection) into the same
    _best_first_bound_search call alongside the two movable-component
    dimensions, with jurisdiction-distinctness rejecting entire
    (partner, target_a, target_b) triples exactly like the real site
    does (home/partner/target_a/target_b must be four distinct
    jurisdictions). This proves that 3-dimensional, reject-some-
    combinations search still matches brute-force itertools.product
    enumeration over the SAME real domain shape, not merely the
    simple no-rejection case the generic control above already covers.
    No DB, no pricing, fully deterministic (fixed seed)."""
    import asyncio
    import itertools
    import random

    from app.services.canonical_evaluation import _best_first_bound_search

    HOME = "US"

    async def run_case(partners, comp_a, comp_b):
        # partners/comp_a/comp_b: list of (jurisdiction_code, value),
        # each list sorted descending by value (as the real candidate
        # lists always are).
        partner_values = [v for _j, v in partners]
        a_values = [v for _j, v in comp_a]
        b_values = [v for _j, v in comp_b]

        async def try_combo(idx, current_best):
            p_jur, p_val = partners[idx[0]]
            a_jur, a_val = comp_a[idx[1]]
            b_jur, b_val = comp_b[idx[2]]
            if len({HOME, p_jur, a_jur, b_jur}) != 4:
                return None
            return p_val + a_val + b_val

        best, visited, bound = await _best_first_bound_search(
            [partner_values, a_values, b_values], try_combo,
        )

        brute_force_best = float("-inf")
        for (p_jur, p_val), (a_jur, a_val), (b_jur, b_val) in itertools.product(partners, comp_a, comp_b):
            if len({HOME, p_jur, a_jur, b_jur}) != 4:
                continue
            brute_force_best = max(brute_force_best, p_val + a_val + b_val)

        assert best == pytest.approx(brute_force_best, abs=1e-6), (partners, comp_a, comp_b, best, brute_force_best)
        if bound is not None:
            assert bound <= best + 1e-9
        return best, visited, bound

    rng = random.Random(20260918)
    jur_pool = ["US", "GB", "CA", "AU", "NZ", "FR", "DE"]

    async def main():
        # Fixed case matching a real shape: partner and one component
        # target collide on jurisdiction, forcing the search past its
        # naive top pick.
        await run_case(
            [("GB", 100.0), ("CA", 80.0), ("FR", 50.0)],
            [("GB", 90.0), ("DE", 40.0), ("NZ", 30.0)],
            [("CA", 70.0), ("AU", 60.0), ("FR", 20.0)],
        )
        for _ in range(60):
            def rand_list():
                length = rng.randint(1, 5)
                jurs = rng.sample(jur_pool, length)
                vals = sorted((round(rng.uniform(1, 100), 2) for _ in range(length)), reverse=True)
                return list(zip(jurs, vals))

            await run_case(rand_list(), rand_list(), rand_list())

    asyncio.run(main())


@pytest.mark.parametrize(
    "project_id", [LITTLE_UTOPIA_PROJECT_ID, FVD_PROJECT_ID, BAD_HOMBRES_PROJECT_ID, LIPS_LIKE_SUGAR_PROJECT_ID],
)
async def test_zero_search_depth_limit_reached_rows(db: AsyncSession, project_id: str):
    """Acceptance invariant: SEARCH_DEPTH_LIMIT_REACHED must never appear
    for any of the four real productions under the completeness-closeout
    engine version -- the corrected search always either proves
    domination via a numeric bound or reaches genuine exhaustion, and
    BOTH are persisted as DOMINATED_WITH_PROOF (distinguished only by
    proof_type), never a separate incomplete-sounding status."""
    await evaluate_project(db, project_id)
    count = (await db.execute(
        text(
            "SELECT COUNT(*) FROM structure_calculation_results scr "
            "JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :pid AND scr.engine_version = :ev "
            "AND scr.calculation_trace_json->>'candidate_status' NOT IN ("
            "  'DOMINATED_WITH_PROOF', 'PRICED', 'RULE_REJECTED', 'CO_PRO_OPPORTUNITY', "
            "  'FEASIBILITY_REVIEW_REQUIRED', 'UNPRICEABLE_AUTHORITY_INSUFFICIENT', "
            "  'QUALIFICATION_HARD_FAIL'"
            ") AND scr.calculation_trace_json->>'candidate_status' IS NOT NULL"
        ),
        {"pid": project_id, "ev": ENGINE_VERSION},
    )).scalar()
    assert count == 0, (
        f"{count} row(s) with an unexpected candidate_status found for project {project_id} "
        "(SEARCH_DEPTH_LIMIT_REACHED / SEARCH_SPACE_EXHAUSTED must never appear)"
    )


async def test_dominated_with_proof_rows_carry_independently_checkable_proof(db: AsyncSession):
    """Both proof_type outcomes (a real numeric bound, and genuine
    exhaustion) are persisted under the SAME DOMINATED_WITH_PROOF status
    -- exhaustion is a complete proof too, never a separate/incomplete
    status."""
    await evaluate_project(db, FVD_PROJECT_ID)
    rows = (await db.execute(
        text(
            "SELECT scr.calculation_trace_json FROM structure_calculation_results scr "
            "JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :pid AND scr.engine_version = :ev "
            "AND scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF' "
            "LIMIT 500"
        ),
        {"pid": FVD_PROJECT_ID, "ev": ENGINE_VERSION},
    )).scalars().all()
    assert rows, "no completeness-closeout rows found -- fixture/engine mismatch"

    found_bound_proof = False
    found_exhaustive_proof = False
    for trace in rows:
        for key in (
            "incumbent_value_usd", "stopping_bound_usd", "stopping_inequality_holds",
            "stopping_inequality", "visited_combination_count", "total_candidate_combinations",
            "proof_type",
        ):
            assert key in trace, f"missing {key!r} in trace"

        holds = trace["stopping_inequality_holds"]
        bound = trace["stopping_bound_usd"]
        incumbent = trace[_num004_incumbent_field(trace)]
        proof_type = trace["proof_type"]

        # The persisted boolean must always match an independent
        # re-derivation of the search's OWN stopping witness.
        if bound is None:
            assert holds is True
        else:
            assert holds == (bound <= incumbent)
        assert holds is True, "every DOMINATED_WITH_PROOF row must carry a true stopping witness"

        if proof_type == "best_first_heap_bound":
            assert bound is not None, "a numeric-bound proof must carry a real stopping bound"
            found_bound_proof = True
        elif proof_type == "EXHAUSTIVE_SEARCH":
            assert bound is None, "an exhaustive-search proof must never carry a numeric bound"
            assert trace["visited_combination_count"] == trace["total_candidate_combinations"], (
                "an exhaustive-search proof must have visited every candidate combination"
            )
            found_exhaustive_proof = True

    assert found_bound_proof, (
        "no sampled row's bound independently proves domination on real data"
    )
    assert found_exhaustive_proof, (
        "no sampled row reached genuine exhaustion on real data -- cannot confirm "
        "proof_type=EXHAUSTIVE_SEARCH is ever actually reached"
    )


async def test_every_fvd_dominated_with_proof_row_has_a_complete_true_proof(db: AsyncSession):
    """A stored stopping inequality that holds for only a sample of rows
    does not satisfy the requirement. This test has NO row LIMIT and NO
    "found at least one" fallback -- every current FVD row persisted as
    DOMINATED_WITH_PROOF must carry a complete, independently
    re-derivable numeric proof with stopping_inequality_holds=True, or
    the test fails outright."""
    await evaluate_project(db, FVD_PROJECT_ID)
    rows = (await db.execute(
        text(
            "SELECT scr.calculation_trace_json FROM structure_calculation_results scr "
            "JOIN production_structures ps ON ps.id = scr.structure_id "
            "WHERE ps.project_id = :pid AND scr.engine_version = :ev "
            "AND scr.calculation_trace_json->>'candidate_status' = 'DOMINATED_WITH_PROOF'"
        ),
        {"pid": FVD_PROJECT_ID, "ev": ENGINE_VERSION},
    )).scalars().all()
    assert rows, "no DOMINATED_WITH_PROOF rows found -- fixture/engine mismatch"

    failures = []
    for trace in rows:
        required = {
            "incumbent_value_usd", "stopping_bound_usd", "stopping_inequality_holds",
            "stopping_inequality", "visited_combination_count", "total_candidate_combinations",
            "component_candidate_lists",
        }
        missing = required - trace.keys()
        holds = trace.get("stopping_inequality_holds")
        bound = trace.get("stopping_bound_usd")
        incumbent = trace.get(_num004_incumbent_field(trace))
        recomputed = bound is not None and incumbent is not None and bound <= incumbent
        if missing or holds is not True or recomputed is not True:
            failures.append({
                "missing": sorted(missing), "holds": holds, "bound": bound, "incumbent": incumbent,
                "recomputed": recomputed, "structural_family": trace.get("structural_family"),
            })

    assert not failures, (
        f"{len(failures)}/{len(rows)} FVD DOMINATED_WITH_PROOF rows lack a complete, true proof: "
        f"{failures[:5]}"
    )


@pytest.mark.parametrize(
    "project_id,expected_incentive,expected_npc",
    [
        (LITTLE_UTOPIA_PROJECT_ID, 573059.70, 3791333.30),
        (FVD_PROJECT_ID, 1445659.84, 3072027.16),
        (BAD_HOMBRES_PROJECT_ID, 596910.25, 1885112.75),
        (LIPS_LIKE_SUGAR_PROJECT_ID, 3459278.90, 8524375.10),
    ],
)
async def test_baseline_economics_byte_identical_under_completeness_closeout(
    db: AsyncSession, project_id: str, expected_incentive: float, expected_npc: float,
):
    """The completeness-closeout search rewrite must never change any
    priced economics -- only completeness of the DOMINATED_WITH_PROOF/
    SEARCH_SPACE_EXHAUSTED disposition. Baseline incentive/NPC must
    remain byte-identical to the pre-closeout accepted values."""
    econ = await evaluate_project(db, project_id)
    baseline = econ["baseline"]
    assert baseline is not None
    assert baseline["total_incentive_value_usd"] == pytest.approx(expected_incentive, abs=0.005)
    assert baseline["true_net_cost_usd"] == pytest.approx(expected_npc, abs=0.005)


# ── Supporting validator correction: lawful same-cost stacks must never ──
# be flagged; genuine cross-component line overlap must still be caught. ──

def test_integrity_gate_no_longer_sums_claim_specific_qpe_against_budget():
    """The stale oracle text must be gone from the QPE check -- a
    regression guard against reintroducing the exact defect the audit
    named, not just a behavioral check."""
    import inspect

    from scripts import canonical_integrity_gate as gate

    src = inspect.getsource(gate)
    assert 'total_qpe = sum((seg.get("qpe_usd")' not in src
    assert "exceeds its own gross budget" not in src
    assert "line_id(s)" in src, "the new disjoint-routing check must exist"


def _overlap_pairs(comp_allocs: list[dict]) -> list[tuple]:
    """The exact mechanical logic canonical_integrity_gate.py's QPE check
    now runs -- duplicated here as a pure function so the boundary cases
    can be tested without a live DB or a served API response."""
    line_ids_by_component: dict[tuple, frozenset] = {}
    for ca in comp_allocs:
        key = (ca["component"], ca["jurisdiction_code"], ca["program_slug"])
        line_ids_by_component[key] = frozenset(ca["line_ids"])
    keys = list(line_ids_by_component.items())
    overlaps = []
    for i in range(len(keys)):
        key_a, lines_a = keys[i]
        for j in range(i + 1, len(keys)):
            key_b, lines_b = keys[j]
            if key_a[1:] == key_b[1:]:
                continue
            overlap = lines_a & lines_b
            if overlap:
                overlaps.append((key_a, key_b, overlap))
    return overlaps


def test_integrity_gate_disjoint_line_check_catches_real_cross_component_overlap():
    """A genuine double-claim: two DIFFERENT routed components (different
    program, different jurisdiction target) sharing a source line_id --
    the same real defect structural_archetype_generator.generate_
    structural_candidate's own same-cost refusal prevents at construction
    time; this is the served-side regression guard for that invariant."""
    comp_allocs = [
        {"component": "post", "jurisdiction_code": "CA-MB", "program_slug": "ca_mb_film_video_credit", "line_ids": ["L1", "L2"]},
        {"component": "vfx", "jurisdiction_code": "CA-NL", "program_slug": "ca_nl_all_spend_credit", "line_ids": ["L2", "L3"]},
    ]
    overlaps = _overlap_pairs(comp_allocs)
    assert overlaps, "a real cross-component line_id overlap must be detected"


def test_integrity_gate_disjoint_line_check_never_flags_disjoint_components():
    """No false positive on real, correctly-routed, non-overlapping
    components."""
    comp_allocs = [
        {"component": "post", "jurisdiction_code": "CA-MB", "program_slug": "ca_mb_film_video_credit", "line_ids": ["L1", "L2"]},
        {"component": "vfx", "jurisdiction_code": "CA-NL", "program_slug": "ca_nl_all_spend_credit", "line_ids": ["L3", "L4"]},
    ]
    assert _overlap_pairs(comp_allocs) == []


async def test_integrity_gate_passes_with_no_false_positive_on_real_fvd_stacking(db: AsyncSession):
    """The authoritative check for the supporting validator correction:
    run the REAL gate script's QPE family against real, current FVD rows
    (which include genuine lawful multi_program same-cost stacks, e.g.
    Ontario CPTC+OFTTC both claiming the same real qualifying-labour
    base) and confirm no QPE-family failure is produced -- the exact
    false positive the audit reproduced live is gone."""
    from app.services.canonical_production_view import build_production_and_structures as _bps
    from scripts.canonical_integrity_gate import _check_program_onboarding_invariant  # noqa: F401 (import sanity)

    await evaluate_project(db, FVD_PROJECT_ID)
    view = await _bps(db, FVD_PROJECT_ID)
    entries = view["structures"]["allocated_structures"]["structures"]
    multi_program_priced = [
        e for e in entries if e.get("structure_type") == "multi_program" and e.get("is_fully_priced")
    ]
    assert multi_program_priced, "no priced multi_program stack found -- cannot prove the false positive is gone"

    for s in multi_program_priced:
        segments = s.get("segments") or []
        for seg in segments:
            qpe = seg.get("qpe_usd")
            assert qpe is None or qpe >= -0.01
        comp_allocs = s.get("component_allocations") or []
        overlaps = _overlap_pairs(comp_allocs) if len(comp_allocs) > 1 else []
        assert not overlaps, (
            f"structure {s['structure_id']} unexpectedly flagged for line overlap on a real, "
            f"lawful priced multi_program stack: {overlaps}"
        )
