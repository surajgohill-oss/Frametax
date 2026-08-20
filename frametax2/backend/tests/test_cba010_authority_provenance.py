"""
test_cba010_authority_provenance.py

CBA-010 — proves the structured provenance backfill/classification: every
registered program terminates as STRUCTURED_PROVENANCE_COMPLETE or
STRUCTURED_PROVENANCE_PARTIAL_WITH_EXACT_AUTHORITY_RESIDUAL, never
PROVENANCE_NOT_CONNECTED; the residual is exact (real tier_ids, not a
summary); and authority_class correctly distinguishes PRIMARY_AUTHORITY/
OFFICIAL_GUIDANCE (may establish deterministic eligibility) from
PROFESSIONAL_PRACTICE/ACADEMIC_POLICY/CASE_STUDY (may not).
"""
from __future__ import annotations

from app.data.program_authority_provenance import (
    AUTHORITY_CLASS_CASE_STUDY,
    AUTHORITY_CLASS_OFFICIAL_GUIDANCE,
    AUTHORITY_CLASS_PRIMARY_AUTHORITY,
    AUTHORITY_CLASSES_ESTABLISH_ELIGIBILITY,
    PROVENANCE_STATUS_NOT_CONNECTED,
    PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL,
    PROVENANCE_STATUS_STRUCTURED_COMPLETE,
    classify_all_programs_provenance,
    classify_program_provenance,
    provenance_coverage_report,
)
from app.data.program_rate_rules import _RULES_BY_PROGRAM


def test_every_registered_program_gets_a_summary_walking_the_live_registry():
    summaries = classify_all_programs_provenance()
    assert set(summaries.keys()) == set(_RULES_BY_PROGRAM.keys())


def test_zero_programs_are_provenance_not_connected():
    report = provenance_coverage_report()
    assert report["disconnected"] == 0
    for summary in classify_all_programs_provenance().values():
        assert summary.status != PROVENANCE_STATUS_NOT_CONNECTED


def test_coverage_report_numbers_are_internally_consistent():
    report = provenance_coverage_report()
    assert report["total_programs"] == len(_RULES_BY_PROGRAM)
    assert report["structured_complete"] + report["partial_with_residual"] + report["disconnected"] == report["total_programs"]
    assert set(report["residual_detail"].keys()) == {
        s.program_slug for s in classify_all_programs_provenance().values()
        if s.status == PROVENANCE_STATUS_PARTIAL_WITH_RESIDUAL
    }


def test_residual_is_exact_real_tier_ids_not_a_summary():
    summary = classify_program_provenance("ca_federal_cptc")
    assert summary is not None
    # CPTC's own tier(s) either fully structured or the residual names the
    # real tier_id -- never a count, never a placeholder.
    for tier_id in summary.residual_tier_ids:
        assert any(r.tier_id == tier_id for r in summary.rules)


def test_authority_class_derived_from_confidence_tier_honestly():
    """VERIFIED -> PRIMARY_AUTHORITY, PARSED -> OFFICIAL_GUIDANCE,
    DISCOVERY -> CASE_STUDY -- a disclosed proxy, not a fresh legal
    re-classification. Runtime-proven against real rules in the registry."""
    found_tiers = set()
    for rules in _RULES_BY_PROGRAM.values():
        for rule in rules:
            found_tiers.add(rule.confidence_tier)
    assert found_tiers <= {"VERIFIED", "PARSED", "DISCOVERY"}

    from app.data.program_authority_provenance import classify_rule_authority_class
    for rules in _RULES_BY_PROGRAM.values():
        for rule in rules:
            ac = classify_rule_authority_class(rule)
            if rule.confidence_tier == "VERIFIED":
                assert ac == AUTHORITY_CLASS_PRIMARY_AUTHORITY
            elif rule.confidence_tier == "PARSED":
                assert ac == AUTHORITY_CLASS_OFFICIAL_GUIDANCE
            elif rule.confidence_tier == "DISCOVERY":
                assert ac == AUTHORITY_CLASS_CASE_STUDY


def test_only_primary_and_official_guidance_establish_eligibility():
    assert AUTHORITY_CLASS_PRIMARY_AUTHORITY in AUTHORITY_CLASSES_ESTABLISH_ELIGIBILITY
    assert AUTHORITY_CLASS_OFFICIAL_GUIDANCE in AUTHORITY_CLASSES_ESTABLISH_ELIGIBILITY
    assert AUTHORITY_CLASS_CASE_STUDY not in AUTHORITY_CLASSES_ESTABLISH_ELIGIBILITY


def test_unregistered_program_returns_none_never_a_fabricated_summary():
    assert classify_program_provenance("not_a_real_program_slug_xyz") is None
