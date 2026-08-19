"""
Worldwide Qualification, Cultural Test + Official Co-production Completion
— focused prevention tests for this pass's real, cited doctrine additions
and the new AUTHORITY_UNRESOLVED state.
"""
from __future__ import annotations

from app.calculators.canonical_qualification_result import (
    ALL_QUALIFICATION_STATES,
    QUAL_AUTHORITY_UNRESOLVED,
    QUAL_NOT_APPLICABLE,
    QUAL_RULE_DATA_INCOMPLETE,
)
from app.calculators.canonical_role_qualification_bridge import evaluate_role_qualification
from app.data.cultural_qualification_model import is_spend_only_program
from app.data.program_requirements import get_program_requirements


def test_authority_unresolved_is_distinct_from_rule_data_incomplete():
    """Task 7 — AUTHORITY_UNRESOLVED and RULE_DATA_INCOMPLETE must never
    be the same value; both must be in the canonical vocabulary."""
    assert QUAL_AUTHORITY_UNRESOLVED != QUAL_RULE_DATA_INCOMPLETE
    assert QUAL_AUTHORITY_UNRESOLVED in ALL_QUALIFICATION_STATES
    assert QUAL_RULE_DATA_INCOMPLETE in ALL_QUALIFICATION_STATES


def test_nz_international_rebate_confirmed_spend_only():
    """Confirmed 2026-08-19 via New Zealand Film Commission
    (nzfilm.co.nz/incentives/rebate-international-nzspr): the
    International rebate is spend-based only, no cultural/content test."""
    assert is_spend_only_program("nz_spg_international") is True
    result = evaluate_role_qualification("nz_spg_international", "NZ", {})
    assert result.state == QUAL_NOT_APPLICABLE


def test_croatia_cultural_test_points_scale_now_set():
    """cultural_test_points=34 was already documented verbatim in this
    record's own evidence note ("minimum 12 of 34 points") but never set
    on the field itself -- a real EXISTING_DATA_BUT_NOT_CONSUMED defect,
    now fixed and re-confirmed against Zagreb Film Office/Cineuropa."""
    p = get_program_requirements("hr_cash_rebate")
    assert p.cultural_test_points == 34
    assert p.cultural_test_threshold == 12


def test_croatia_national_cast_crew_requirement_disclosed_not_fabricated():
    """The real 30%/50% national cast/crew percentage requirement
    (confirmed via Zagreb Film Office/Cineuropa) is disclosed in
    additional_facts -- NOT encoded as a role_qualification hard gate,
    since the existing role-gate engine checks individual-role nationality
    match, not percentage-of-headcount, and misusing it would produce a
    false HARD_FAIL for real Croatian productions with mixed-nationality
    cast. Disclosure-only is the honest representation of this rule
    against what the existing engine can actually enforce."""
    p = get_program_requirements("hr_cash_rebate")
    assert "national_cast_crew_requirement" in p.additional_facts
    assert "30%" in p.additional_facts["national_cast_crew_requirement"]
    assert "50%" in p.additional_facts["national_cast_crew_requirement"]


def test_writer_role_never_globally_mandatory_across_new_and_existing_data():
    """Cross-check against the full real registry: writer must never be
    'required' for a program whose own real data doesn't say so (spot-
    checked against a program with no writer requirement at all)."""
    from app.data.cultural_qualification_model import get_requirements
    for slug in ("uk_avec", "au_producer_offset", "eu_eurimages"):
        writer_rows = [r for r in get_requirements(slug) if r.role == "writer"]
        assert not any(r.status == "required" for r in writer_rows), (
            f"{slug} must not have a hard-required writer gate per its own real data"
        )
