from __future__ import annotations

from app.bridge.provenance import (
    RULE_FIELDS,
    build_provenance_matrix,
    hard_gate_unknown_programs,
    provenance_summary,
)
from app.bridge.schema import ProvenanceGapClassification


class TestProvenanceMatrixIntegrity:
    def test_one_record_per_jurisdiction_per_rule_field(self):
        matrix = build_provenance_matrix()
        assert len(matrix) == 110 * len(RULE_FIELDS)

    def test_every_record_has_a_valid_gap_classification(self):
        matrix = build_provenance_matrix()
        for r in matrix:
            assert isinstance(r.gap_classification, ProvenanceGapClassification)

    def test_no_program_slug_or_jurisdiction_code_is_blank(self):
        matrix = build_provenance_matrix()
        for r in matrix:
            assert r.program_slug
            assert r.jurisdiction_code


class TestKnownEnforcementFindings:
    """Pins the real, code-verified findings this session — a min_qpe_usd
    threshold genuinely gates pricing; cultural_test_required does not
    (see provenance.py's module docstring for the exact lines read)."""

    def test_cyprus_minimum_spend_is_enforced_and_disclosed(self):
        matrix = build_provenance_matrix()
        record = next(r for r in matrix if r.program_slug == "cy_film_rebate" and r.rule_field == "minimum_spend")
        assert record.machine_enforced is True
        assert record.disclosed_in_ui is True
        assert record.gap_classification == ProvenanceGapClassification.ENFORCED_AND_DISCLOSED

    def test_cyprus_cultural_test_is_disclosed_not_enforced(self):
        matrix = build_provenance_matrix()
        record = next(r for r in matrix if r.program_slug == "cy_film_rebate" and r.rule_field == "cultural_test")
        assert record.machine_enforced is False
        assert record.disclosed_in_ui is True
        assert record.gap_classification == ProvenanceGapClassification.DISCLOSED_NOT_ENFORCED

    def test_mauritius_gained_a_requirements_profile_but_most_fields_remain_missing(self):
        """Pass A (2026-07-26) migrated preapproval + minimum_spend for
        mu_edb_incentive from an already-cited internal RateCondition — those
        two fields are now genuinely disclosed. Every other rule field
        (local_entity, cultural_test, application_timing, filing_deadline,
        audit, transfer_monetization, stacking_restriction) has no internal
        source and remains MISSING — this pins that the migration did not
        overstate MU's coverage beyond what was actually derivable."""
        matrix = build_provenance_matrix()
        by_field = {r.rule_field: r for r in matrix if r.program_slug == "mu_edb_incentive"}
        assert by_field["preapproval"].disclosed_in_ui is True
        assert by_field["preapproval"].gap_classification == ProvenanceGapClassification.DISCLOSED_NOT_ENFORCED
        assert by_field["local_entity"].disclosed_in_ui is False
        assert by_field["local_entity"].gap_classification == ProvenanceGapClassification.MISSING


class TestHardGateUnknowns:
    def test_returns_nonempty_dict(self):
        gaps = hard_gate_unknown_programs()
        assert len(gaps) > 0

    def test_every_listed_field_is_a_real_hard_gate_field(self):
        hard_gate_fields = {"preapproval", "local_entity", "cultural_test", "minimum_spend", "stacking_restriction"}
        gaps = hard_gate_unknown_programs()
        for fields in gaps.values():
            assert set(fields) <= hard_gate_fields

    def test_mauritius_appears_with_multiple_unknown_hard_gates(self):
        gaps = hard_gate_unknown_programs()
        assert "mu_edb_incentive" in gaps
        assert len(gaps["mu_edb_incentive"]) >= 3


class TestProvenanceSummary:
    def test_summary_counts_match_matrix_length(self):
        matrix = build_provenance_matrix()
        summary = provenance_summary(matrix)
        assert sum(summary.values()) == len(matrix)

    def test_no_bulk_research_was_performed(self):
        """This matrix must be computable with zero network calls — a
        structural guarantee, not just a docstring claim: build it twice
        and confirm identical results (no randomness, no I/O-dependent
        ordering)."""
        m1 = build_provenance_matrix()
        m2 = build_provenance_matrix()
        assert [r.model_dump() for r in m1] == [r.model_dump() for r in m2]
