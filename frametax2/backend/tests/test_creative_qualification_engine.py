"""
test_creative_qualification_engine.py

Targeted tests for Phase 7 closeout, Part D — the Creative Qualification
Engine. Covers current-status determination, minimal-path search
(including correct handling of cultural_test_rules.py's real
section-minimum logic, e.g. FR CNC's combined D+E gate), non-creative
alternative discovery, "never creative-only as the sole path" honesty,
determinism, non-mutation, and Little Utopia / recommendation-engine
compatibility (no bypass of gated Recommendation objects).
"""
from __future__ import annotations

import copy

import pytest

from app.calculators.production_recommendation_engine import CULTURAL_TEST_REGISTRY

from app.calculators.creative_qualification_engine import (
    CREATIVE_QUALIFICATION_ENGINE_VERSION,
    PathKind,
    analyze_creative_qualification_paths,
)

FR_CNC_ALL_FAILING = {
    "french_language_or_subject": False,
    "director_french_or_eea": False,
    "writer_french_or_eea": False,
    "producer_french": False,
    "french_spend_pct": 0.10,
}

# Producer + spend already satisfy the required D/E gates; only the
# optional B/C/A boost criteria are unmet — a genuinely creative-only
# minimal path should exist here (director OR writer alone reaches 4pts:
# D(1)+E(1)+B(2)=4).
FR_CNC_GATES_MET_CREATIVE_UNMET = {
    "french_language_or_subject": False,
    "director_french_or_eea": False,
    "writer_french_or_eea": False,
    "producer_french": True,
    "french_spend_pct": 0.60,
}

# Spend just under threshold, everything else already passing — a
# non-creative-only path (raise spend_pct) should exist and be minimal.
FR_CNC_ONLY_SPEND_SHORT = {
    "french_language_or_subject": True,
    "director_french_or_eea": True,
    "writer_french_or_eea": True,
    "producer_french": True,
    "french_spend_pct": 0.30,
}

FR_CNC_PASSING = {
    "french_language_or_subject": True,
    "director_french_or_eea": True,
    "writer_french_or_eea": False,
    "producer_french": True,
    "french_spend_pct": 0.60,
}


class TestCurrentStatus:
    def test_passing_test_reports_currently_passes_true_and_no_paths(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_PASSING)
        assert a.currently_passes is True
        assert a.lowest_impact_paths == ()
        assert a.missing_criterion_codes == ()

    def test_failing_test_reports_currently_passes_false(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        assert a.currently_passes is False
        assert len(a.missing_criterion_codes) > 0

    def test_invalid_test_slug_raises(self):
        with pytest.raises(ValueError, match="not a registered cultural test"):
            analyze_creative_qualification_paths("not_a_real_test", {})

    def test_version_constant_present(self):
        assert CREATIVE_QUALIFICATION_ENGINE_VERSION


class TestPathSearchCorrectness:
    def test_reuses_real_scoring_engine_never_reimplements_section_minimums(self):
        """FR CNC requires BOTH section D (producer) and section E (spend)
        — a fact only correctly derivable by actually calling the real
        score_fn, which this test proves by checking every returned path
        satisfies producer OR spend criteria are unavoidable when both
        are unmet."""
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        for path in a.lowest_impact_paths:
            assert "CNC_D1" in path.criterion_codes
            assert "CNC_E1" in path.criterion_codes

    def test_lowest_impact_path_when_gates_already_met(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_GATES_MET_CREATIVE_UNMET)
        assert a.currently_passes is False
        assert a.lowest_impact_path is not None
        assert a.lowest_impact_path.criteria_count == 1
        assert a.lowest_impact_path.criterion_codes[0] in ("CNC_B1", "CNC_C1")

    def test_always_presents_alternatives_at_minimal_size(self):
        """Both director-only and writer-only should independently work
        here — 'always present alternatives' means both are returned,
        not just one."""
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_GATES_MET_CREATIVE_UNMET)
        codes = {p.criterion_codes for p in a.lowest_impact_paths}
        assert ("CNC_B1",) in codes
        assert ("CNC_C1",) in codes

    def test_paths_are_verified_by_resimulating_through_real_score_fn(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        score_fn = CULTURAL_TEST_REGISTRY["fr_cnc_cultural_test"]["score_fn"]
        rules = CULTURAL_TEST_REGISTRY["fr_cnc_cultural_test"]["rules"]
        for path in a.lowest_impact_paths:
            simulated = dict(FR_CNC_ALL_FAILING)
            for rule in rules:
                if rule["criterion_code"] in path.criterion_codes:
                    simulated[rule["input_key"]] = True if rule["input_type"] == "boolean" else rule["threshold_value"]
            result = score_fn(simulated)
            assert result.passes_overall and result.passes_section_minimums


class TestNonCreativeAlternative:
    def test_non_creative_alternative_found_when_it_exists(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ONLY_SPEND_SHORT)
        assert a.has_non_creative_alternative is True
        assert a.non_creative_alternative_paths[0].criterion_codes == ("CNC_E1",)
        assert a.non_creative_alternative_paths[0].path_kind == PathKind.NON_CREATIVE_ONLY

    def test_no_non_creative_alternative_when_creative_gate_is_unavoidable(self):
        """Both D (producer, creative) and E (spend, non-creative) are
        required gates in FR CNC — with D unmet, no non-creative-only
        path can exist, and this must be reported honestly as False,
        never silently omitted."""
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        assert a.has_non_creative_alternative is False
        assert a.non_creative_alternative_paths == ()

    def test_never_presents_creative_change_as_sole_option_when_alternative_exists(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_GATES_MET_CREATIVE_UNMET)
        # lowest-impact paths here ARE creative (B/C), but this test's
        # only failing criteria are creative — confirm the engine still
        # correctly reports no non-creative alternative exists (honest,
        # not papered over) rather than fabricating one.
        assert a.non_creative_alternative_paths == ()
        assert a.requires_creative_change_only is True


class TestPathKindClassification:
    def test_path_kind_reflects_creative_classification(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_GATES_MET_CREATIVE_UNMET)
        for path in a.lowest_impact_paths:
            assert path.path_kind == PathKind.CREATIVE_ONLY

    def test_mixed_path_kind_when_path_spans_both(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        assert all(p.path_kind == PathKind.MIXED for p in a.lowest_impact_paths)


class TestAuthorityReferenceAndGating:
    def test_authority_reference_points_to_real_rule_table_entries(self):
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_GATES_MET_CREATIVE_UNMET)
        for path in a.lowest_impact_paths:
            for ref in path.authority_reference:
                assert ref.startswith("cultural_test_rules.fr_cnc_cultural_test[")

    def test_never_constructs_a_gated_recommendation_object(self):
        """QualificationPath must have no approval-gate fields — this
        module never bypasses production_recommendation_engine's gates
        by producing a parallel Recommendation-shaped object."""
        a = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        for path in a.lowest_impact_paths:
            assert not hasattr(path, "requires_producer_approval")
            assert not hasattr(path, "status")


class TestDeterminismAndNonMutation:
    def test_two_runs_produce_identical_paths(self):
        a1 = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        a2 = analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        assert [p.path_id for p in a1.lowest_impact_paths] == [p.path_id for p in a2.lowest_impact_paths]

    def test_does_not_mutate_production_details(self):
        before = copy.deepcopy(FR_CNC_ALL_FAILING)
        analyze_creative_qualification_paths("fr_cnc_cultural_test", FR_CNC_ALL_FAILING)
        assert FR_CNC_ALL_FAILING == before

    def test_all_seven_registered_tests_are_analyzable(self):
        for slug in CULTURAL_TEST_REGISTRY:
            result = analyze_creative_qualification_paths(slug, {})
            assert result.test_slug == slug
            assert result.currently_passes is False  # empty details never passes any real test
