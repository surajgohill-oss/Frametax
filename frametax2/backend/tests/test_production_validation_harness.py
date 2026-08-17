"""
Acceptance Testing / Optimizer Validation phase: tests for the PERMANENT
production validation harness. These protect the harness's own contract
(deterministic, no unexplained failures, constraints toggle correctly,
never contaminates NPC) — not the underlying optimizer, which its own
suites already cover.
"""
from __future__ import annotations

import pytest

from app.calculators.production_validation_harness import (
    FailureClassification,
    run_full_acceptance_harness,
    run_stage1_engine_validation,
    run_stage2_progressive_constraints,
    run_stage3_scenario_diversity,
    run_stage4_recommendation,
)


@pytest.fixture(scope="module")
def full_report():
    return run_full_acceptance_harness()


class TestHarnessDoesNotMutateProduction:
    """The harness must observe the real Little Utopia production, never
    alter it — the default (no override) served path must be byte-
    identical before and after running the harness."""

    def test_default_served_output_unchanged_after_harness_runs(self):
        from app.demo.little_utopia_state import build_allocated_structures, get_state

        state = get_state()
        before = build_allocated_structures(state)
        run_full_acceptance_harness(state)
        after = build_allocated_structures(state)
        assert before["discovery"]["metrics"] == after["discovery"]["metrics"]
        assert [s["structure_id"] for s in before["structures"]] == [
            s["structure_id"] for s in after["structures"]
        ]


class TestStage1EngineValidation:
    def test_unconstrained_reaches_the_complete_executable_set_for_readiness(self):
        """With the capability gate off, incentive_ready must equal the
        full executable set (jc.ALL_PROFILES) MINUS jurisdictions whose
        OWN statutory conditions are genuinely unmet for this production
        — nothing statutory should be blocked by a physical/creative
        capability requirement, but a real statutory gate is not a
        capability requirement and must still bind.

        Incentive/Optimizer Core Closeout: Australia's Location Offset
        now enforces its real A$20M minimum QAPE (via the conservative
        USD bound documented on au-location-offset-30 in
        program_rate_rules_worldwide.py), which Little Utopia's real QPE
        (~$4M) does not meet — AU is therefore correctly EXPECTED_
        EXCLUSION at the discovery stage itself ("the production's
        statutory conditions are unmet"), one fewer than the full set.
        This is the test's own documented invariant ("minimum spend...
        remain fully enforced, never relaxed") now actually holding for
        AU, which it could not before this threshold was enforced.

        Global Data Application: the executable set is now additionally
        reduced by every program the completed primary-authority corpus
        adjudicated non-priceable (authority-insufficient, selective,
        non-economic, superseded, duplicate). Those are canonical DATA
        exclusions, not capability or statutory ones, so the invariant is
        expressed against the coverage registry rather than a bare count.
        """
        from app.calculators import jurisdiction_comparison as jc
        from app.data.authority_coverage_registry import blocks_economic_candidacy

        s1 = run_stage1_engine_validation()
        canonically_blocked = {
            code for code, p in jc.ALL_PROFILES.items()
            if blocks_economic_candidacy(getattr(p, "program_slug", None))
        }
        # AU remains the one STATUTORY (non-coverage) exclusion.
        assert "AU" not in canonically_blocked
        expected_ready = len(jc.ALL_PROFILES) - len(canonically_blocked) - 1
        assert s1["incentive_ready_count"] == expected_ready
        assert s1["total_executable_jurisdictions"] == len(jc.ALL_PROFILES)

    def test_australia_is_the_one_statutory_exclusion(self):
        """Names the exclusion explicitly so a FUTURE unrelated drop in
        incentive_ready_count fails loudly instead of silently matching
        a stale '-1'."""
        from app.demo.little_utopia_state import build_allocated_structures, get_state
        from app.calculators.production_requirements import derive_production_requirements
        from app.calculators.production_validation_harness import _requirements_with_capabilities

        state = get_state()
        real_requirements = derive_production_requirements(state.physical_requirements)
        unconstrained = _requirements_with_capabilities(real_requirements, frozenset())
        out = build_allocated_structures(state, requirements_override=unconstrained)
        au_ex = next(e for e in out["discovery"]["examinations"] if e["jurisdiction_code"] == "AU")
        assert au_ex["accepted"] is False
        assert au_ex["resolves_for_production"] is False
        assert "statutory conditions are unmet" in au_ex["reason"]

    def test_no_unexplained_failures(self):
        s1 = run_stage1_engine_validation()
        assert s1["no_unexplained_failures"] is True

    def test_every_unpriced_jurisdiction_carries_exactly_one_of_five_classifications(self):
        s1 = run_stage1_engine_validation()
        valid = {c.value for c in FailureClassification}
        for row in s1["unpriced_jurisdictions"]:
            assert row["classification"] in valid
            assert row["reason"], f"{row['jurisdiction_code']} classified without a reason"

    def test_fully_priced_plus_unpriced_equals_incentive_ready(self):
        s1 = run_stage1_engine_validation()
        assert s1["fully_priced_count"] + s1["unpriced_incentive_ready_count"] == s1["incentive_ready_count"]

    def test_deterministic(self):
        a = run_stage1_engine_validation()
        b = run_stage1_engine_validation()
        assert a["fully_priced_count"] == b["fully_priced_count"]
        assert a["unpriced_jurisdictions"] == b["unpriced_jurisdictions"]


class TestStage2ProgressiveConstraints:
    def test_steps_are_monotonically_non_increasing_in_remaining_count(self):
        """Cumulatively re-enabling constraints can only ever ELIMINATE
        jurisdictions, never add them back."""
        s2 = run_stage2_progressive_constraints()
        remaining = [step["jurisdictions_remaining"] for step in s2["capability_steps"]]
        assert remaining == sorted(remaining, reverse=True)

    def test_eliminated_count_matches_the_remaining_delta(self):
        s2 = run_stage2_progressive_constraints()
        steps = s2["capability_steps"]
        for prev, cur in zip(steps, steps[1:]):
            assert cur["jurisdictions_eliminated_this_step"] == (
                prev["jurisdictions_remaining"] - cur["jurisdictions_remaining"]
            )

    def test_every_elimination_carries_evidence(self):
        s2 = run_stage2_progressive_constraints()
        for step in s2["capability_steps"]:
            for e in step["eliminated"]:
                assert e["evidence"], f"{e['jurisdiction_code']} eliminated without evidence"

    def test_non_applicable_probe_tokens_eliminate_nothing(self):
        """A capability token this production does not require must never
        eliminate a jurisdiction — proves the toggle is real, not a no-op
        that happens to look like one."""
        s2 = run_stage2_progressive_constraints()
        for step in s2["capability_steps"][1:]:
            if not step["capability_applies_to_this_production"]:
                assert step["jurisdictions_eliminated_this_step"] == 0

    def test_at_least_one_applicable_constraint_eliminates_something(self):
        """Regression guard: if the real production's own hard requirements
        stop eliminating anything, the toggle mechanism itself is broken."""
        s2 = run_stage2_progressive_constraints()
        applicable_eliminations = sum(
            step["jurisdictions_eliminated_this_step"]
            for step in s2["capability_steps"]
            if step["capability_applies_to_this_production"]
        )
        assert applicable_eliminations > 0

    def test_non_eliminating_constraints_all_documented(self):
        s2 = run_stage2_progressive_constraints()
        required_topics = {
            "production_type", "minimum_spend_thresholds", "qualifying_spend_rules",
            "cultural_requirements", "mediterranean_setting", "post_production_requirements",
            "treaty_eligibility", "broadcaster_requirements", "financing_assumptions",
            "language_requirements",
        }
        assert required_topics <= set(s2["non_eliminating_constraints"])
        for topic, explanation in s2["non_eliminating_constraints"].items():
            assert explanation, f"{topic} documented with no explanation"


class TestStage3ScenarioDiversity:
    def test_multiple_structure_families_generated(self):
        s3 = run_stage3_scenario_diversity()
        assert len(s3["structure_families_generated"]) >= 2

    def test_conditional_layer_is_nonzero(self):
        s3 = run_stage3_scenario_diversity()
        assert s3["conditional_layer"]["total_nodes_worldwide"] > 0
        assert s3["conditional_layer"]["structures_surfacing_conditional_funding"] > 0

    def test_conditional_actively_influences_scenarios_passes(self):
        s3 = run_stage3_scenario_diversity()
        assert s3["conditional_actively_influences_scenarios"]["verdict"].startswith("PASS")

    def test_coverage_categories_all_evaluated(self):
        s3 = run_stage3_scenario_diversity()
        for cat in s3["coverage_categories"]:
            assert cat["candidates_evaluated"] >= 0
            assert cat["zero_reason"] is None or isinstance(cat["zero_reason"], str)


class TestStage4Recommendation:
    def test_multi_scenario_not_a_single_answer(self):
        s4 = run_stage4_recommendation()
        assert s4["is_multi_scenario"] is True
        assert s4["scenario_count"] > 1

    def test_scenarios_strictly_ascending_by_npc(self):
        s4 = run_stage4_recommendation()
        npcs = [s["net_production_cost_usd"] for s in s4["scenarios"]]
        assert npcs == sorted(npcs)

    def test_every_scenario_carries_required_fields(self):
        s4 = run_stage4_recommendation()
        for s in s4["scenarios"]:
            assert s["participating_jurisdictions"]
            assert s["net_production_cost_usd"] is not None
            assert "assumptions" in s and "evidence" in s
            assert isinstance(s["unresolved_questions"], list)

    def test_rank_one_matches_the_real_served_ranking(self):
        from app.demo.little_utopia_state import build_allocated_structures, get_state

        s4 = run_stage4_recommendation()
        served = build_allocated_structures(get_state())
        served_rank1 = next(r for r in served["ranking"] if r["rank"] == 1)
        assert s4["scenarios"][0]["structure_id"] == served_rank1["structure_id"]
        assert s4["scenarios"][0]["net_production_cost_usd"] == served_rank1["npc_with_adjustments_usd"]


class TestFullHarnessDeliverables:
    def test_all_five_deliverables_present(self, full_report):
        d = full_report["deliverables"]
        for key in (
            "1_optimizer_coverage_statistics",
            "2_jurisdiction_participation_statistics",
            "3_scenario_generation_statistics",
            "4_remaining_implementation_gaps",
            "5_next_phase_recommendations",
        ):
            assert key in d

    def test_participation_stats_internally_consistent(self, full_report):
        p = full_report["deliverables"]["2_jurisdiction_participation_statistics"]
        assert p["incentive_ready_unconstrained"] >= p["incentive_ready_real_constraints"]
        assert p["eliminated_by_real_constraints"] == (
            p["incentive_ready_unconstrained"] - p["incentive_ready_real_constraints"]
        )

    def test_gaps_are_never_empty_strings(self, full_report):
        for gap in full_report["deliverables"]["4_remaining_implementation_gaps"]:
            assert gap and isinstance(gap, str)

    def test_language_gap_is_always_disclosed(self, full_report):
        """Regression guard against ever silently 'fixing' this by fabricating
        a language filter instead of implementing one for real."""
        gaps = " ".join(full_report["deliverables"]["4_remaining_implementation_gaps"])
        assert "language" in gaps.lower()


class TestServedBlockersNeverContradictTheDoctrineRegistry:
    """Regression coverage for the Cyprus incident (2026-07-24): the SERVED
    /structures payload showed a live "CY/cy_film_rebate: no classified
    qualification doctrine and no statutory rate rules" blocker, even
    though resolve_program_doctrine('cy_film_rebate') and
    get_rate_rules('cy_film_rebate') both return real, fully-classified
    data. Root cause was NOT a code defect: a long-lived stale backend
    process (started days earlier, no --reload, bound to the port the
    frontend's default API_BASE targets) was serving pre-fix code while
    the current source tree was already correct. `build_allocated_structures`
    itself has never produced this contradiction when actually invoked
    against current code — this test proves that and guards against a
    REAL future regression reintroducing it (e.g. a rename/alias drift
    between the registry a structure spec's slug comes from and the
    registry price_segment/production_discovery resolve against)."""

    def test_no_full_relocation_structure_blocks_on_a_program_the_registry_says_is_classified(self):
        from app.data.program_rate_rules import get_rate_rules
        from app.data.program_spend_rules import resolve_program_doctrine
        from app.demo.little_utopia_state import build_allocated_structures, get_state

        served = build_allocated_structures(get_state())
        contradictions = []
        for s in served["structures"]:
            if s["structure_type"] != "full_relocation":
                continue
            for seg in s["segments"]:
                slug = seg.get("program_slug")
                if not slug:
                    continue
                doctrine_resolution = resolve_program_doctrine(slug)
                has_doctrine = doctrine_resolution is not None
                has_rate = len(get_rate_rules(slug)) > 0
                if not (has_doctrine and has_rate):
                    continue  # genuinely unclassified — a blocker here is correct, not a contradiction
                for b in list(seg.get("blockers", ())) + list(s.get("blockers", ())):
                    if "no classified qualification doctrine" in b or "no statutory rate rules" in b:
                        contradictions.append((s["structure_id"], slug, b))
        assert contradictions == [], (
            f"{len(contradictions)} structure(s) claim a program is unclassified while "
            f"the registry says otherwise: {contradictions}"
        )

    def test_cyprus_specifically_was_reactivated_and_now_prices(self):
        """Global Data Application originally reclassified cy_film_rebate
        UNPRICEABLE_AUTHORITY_INSUFFICIENT by the completed corpus. The
        Global Formulaic Economic Completion batch 4 later independently
        re-fetched film.investcyprus.org.cy (Cyprus Film Commission,
        official) directly this task, reproduced the identical "Up to 45%
        Tax Rebate" figure the existing citation had already recorded, and
        removed the veto -- Cyprus is now correctly PRICEABLE again, a
        deliberate, evidenced reversal, not a regression. The test's real
        invariant -- that served blockers never contradict the doctrine
        registry -- is preserved by asserting the served state agrees with
        the registry in whichever direction the registry currently says.
        """
        from app.data.authority_coverage_registry import coverage_state
        from app.demo.little_utopia_state import build_allocated_structures, get_state

        served = build_allocated_structures(get_state())
        cy = next((s for s in served["structures"] if s["structure_id"] == "ALLOC-RELOC-CY"), None)
        assert cy is not None, "ALLOC-RELOC-CY is expected to be a candidate structure for Little Utopia"
        assert coverage_state("cy_film_rebate") == "PRICEABLE_VALIDATED"
        assert cy["is_fully_priced"] is True
        seg = next(sg for sg in cy["segments"] if sg["jurisdiction_code"] == "CY")
        assert seg["executable"] is True
        assert seg["program_slug"] == "cy_film_rebate"
        assert list(seg["blockers"]) == []
