"""
Canonical Co-production Qualification Reconnection — focused unit tests.

Proves the mandatory invariants (Task 18): writer is never globally
mandatory, role requirements are regime-specific, registry presence !=
qualification, unknown mandatory fact fails closed (USER_FACT_REQUIRED,
never QUALIFIES), missing authority != hard failure (RULE_DATA_INCOMPLETE,
never HARD_FAIL), point-bearing != mandatory, known mandatory role can
HARD_FAIL when explicitly violated.
"""
from __future__ import annotations

from app.calculators.canonical_qualification_result import (
    QUAL_HARD_FAIL,
    QUAL_NOT_APPLICABLE,
    QUAL_QUALIFIES,
    QUAL_RULE_DATA_INCOMPLETE,
    QUAL_USER_FACT_REQUIRED,
)
from app.calculators.canonical_role_qualification_bridge import (
    ROLE_QUALIFICATION_COVERED_SLUGS,
    evaluate_role_qualification,
)


def test_writer_is_never_globally_mandatory():
    """uk_avec's writer is point-bearing, NOT a hard-gate requirement --
    a program with no writer on file must NOT hard-fail or block on writer
    (only ca_federal_cptc/ca_cmf/fr_cnc_production make writer a REQUIRED
    gate -- regime-specific, never generalized)."""
    result = evaluate_role_qualification("uk_avec", "GB", {})
    # writer never appears as a REQUIRED gate finding for uk_avec
    assert not any(f.role == "writer" for f in result.role_findings)


def test_unknown_mandatory_role_fails_closed_to_user_fact_required():
    """ca_federal_cptc requires director/writer/producer/lead_cast --
    with NO people on file at all, the result must be USER_FACT_REQUIRED,
    never QUALIFIES (never silently assumed satisfied)."""
    result = evaluate_role_qualification("ca_federal_cptc", "CA", {})
    assert result.state == QUAL_USER_FACT_REQUIRED
    assert result.missing_facts


def test_known_mandatory_role_violation_hard_fails():
    """Both director AND writer known to be non-Canadian against
    ca_federal_cptc's real CAVCO alternative-group rule ("director OR
    writer must be Canadian" -- corrected 2026-08-19, see cultural_
    qualification_model.py) must HARD_FAIL -- a genuine, explicit rule
    violation, not a missing fact."""
    result = evaluate_role_qualification(
        "ca_federal_cptc", "CA",
        {"director": ("FR",), "writer": ("GB",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert result.state == QUAL_HARD_FAIL
    assert result.failed_requirements


def test_cavco_alternative_group_director_or_writer_either_satisfies():
    """CAVCO's real rule: EITHER director OR writer being Canadian
    satisfies the requirement -- neither is independently mandatory.
    Confirmed via canada.ca CPTC application guidelines (10-point scale,
    director=2pts/writer=2pts, min 6/10) -- corrects a prior defect where
    this codebase required both unconditionally."""
    # writer Canadian, director foreign -> QUALIFIES (writer satisfies the group)
    r1 = evaluate_role_qualification(
        "ca_federal_cptc", "CA",
        {"director": ("FR",), "writer": ("CA",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert r1.state == QUAL_QUALIFIES
    # director Canadian, writer foreign -> QUALIFIES (director satisfies the group)
    r2 = evaluate_role_qualification(
        "ca_federal_cptc", "CA",
        {"director": ("CA",), "writer": ("GB",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert r2.state == QUAL_QUALIFIES


def test_all_known_and_satisfied_qualifies():
    result = evaluate_role_qualification(
        "ca_federal_cptc", "CA",
        {"director": ("CA",), "writer": ("CA",), "producer": ("CA",), "lead_cast": ("CA",)},
    )
    assert result.state == QUAL_QUALIFIES
    assert not result.failed_requirements
    assert not result.missing_facts


def test_point_bearing_role_never_becomes_a_hard_requirement():
    """uk_avec's director is point-bearing (weighted), never 'required' --
    even with zero people known, uk_avec's role gate layer (which only
    enforces status=='required' rows) has nothing to fail or wait on for
    that dimension, since uk_avec has no required-status role rows at
    all -- its state is NOT_APPLICABLE for the hard-gate layer, never
    HARD_FAIL, never QUALIFIES presumed from points alone."""
    result = evaluate_role_qualification("uk_avec", "GB", {})
    assert result.state == QUAL_NOT_APPLICABLE
    assert result.state != QUAL_HARD_FAIL


def test_missing_authority_is_rule_data_incomplete_never_hard_fail():
    """A program with zero NationalityRequirement rows on file (e.g. any
    of the 157 unknown/not-captured regimes) must be RULE_DATA_INCOMPLETE
    -- missing authority is never reported as a negative qualification
    result (Task doctrine #5)."""
    result = evaluate_role_qualification("hr_cash_rebate", "HR", {"director": ("HR",)})
    assert result.state == QUAL_RULE_DATA_INCOMPLETE
    assert result.state != QUAL_HARD_FAIL


def test_role_requirements_are_regime_specific_not_generalized():
    """fr_cnc_production's producer=FR required gate must NOT leak into
    ca_federal_cptc's evaluation, and vice versa -- each regime's own
    rows only."""
    fr_result = evaluate_role_qualification("fr_cnc_production", "FR", {"producer": ("CA",)})
    ca_result = evaluate_role_qualification("ca_federal_cptc", "CA", {"producer": ("CA",)})
    assert fr_result.state == QUAL_HARD_FAIL  # CA producer fails FR's FR-only gate
    # ca_federal_cptc's other required roles (director/writer/lead_cast) are
    # still unknown -> USER_FACT_REQUIRED, never contaminated by fr's failure
    assert ca_result.state == QUAL_USER_FACT_REQUIRED


def test_registry_presence_never_equals_qualification():
    """The mere fact that a program_slug is covered by cultural_
    qualification_model.py (registry presence) must never itself imply
    QUALIFIES -- only real, resolved, satisfied facts do."""
    assert "ca_federal_cptc" in ROLE_QUALIFICATION_COVERED_SLUGS
    result = evaluate_role_qualification("ca_federal_cptc", "CA", {})
    assert result.state != QUAL_QUALIFIES


def test_covered_slugs_matches_real_registry_count():
    """Codex's audit found exactly 24 program slugs with real role/
    nationality rule data in cultural_qualification_model.py."""
    assert len(ROLE_QUALIFICATION_COVERED_SLUGS) == 24
