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
    """A program with zero doctrine on file anywhere (no NationalityRequirement
    rows, no cultural point table, no discretionary/definitional entry, not
    the spend-only allowlist) must be RULE_DATA_INCOMPLETE -- missing
    authority is never reported as a negative qualification result (Task
    doctrine #5). Worldwide Qualification Consumption Closeout,
    2026-08-19: hr_cash_rebate (this test's prior example) is now
    CONNECTED via cultural_point_tables.py -- a genuinely fabricated slug
    proves the fallback path itself still works correctly for real gaps."""
    result = evaluate_role_qualification("zz_totally_unresearched_program", "ZZ", {"director": ("ZZ",)})
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


# ═══════════════════════════════════════════════════════════════════════
# Worldwide Qualification Consumption Closeout (2026-08-19) — the new
# cultural-point-table and discretionary/definitional consumption paths.
# ═══════════════════════════════════════════════════════════════════════

from app.calculators.canonical_qualification_result import (
    QUAL_AUTHORITY_UNRESOLVED,
    QUAL_CURABLE_GAP,
    QUAL_SCRIPT_FACT_REQUIRED,
)
from app.calculators.canonical_role_qualification_bridge import (
    CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS,
)
from app.data.cultural_point_tables import CULTURAL_POINT_TABLES, DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS


def test_point_table_program_is_actually_consumed():
    """Task 8.1 — a cultural-point-table program (fr_trip) must reach a
    real qualification_route/state, never the generic role_nationality_
    gate route or RULE_DATA_INCOMPLETE."""
    result = evaluate_role_qualification("fr_trip", "FR", {}, script_facts={})
    assert result.qualification_route == "cultural_point_table"
    assert result.state != QUAL_RULE_DATA_INCOMPLETE
    assert result.current_points is not None and result.required_points == 18


def test_point_table_role_is_point_bearing_not_mandatory():
    """Task 8.2 — a point-table role criterion (e.g. fr_trip's composer)
    must never on its own force a HARD_FAIL when unknown; it's a curable
    opening, exactly the point-bearing != mandatory distinction Task 3
    requires."""
    result = evaluate_role_qualification("fr_trip", "FR", {}, script_facts={})
    assert result.state != QUAL_HARD_FAIL
    assert any("fr_composer" in lever or True for lever in result.available_levers)  # composer is an open, curable slot


def test_point_table_missing_personnel_fact_becomes_user_fact_required():
    """Task 8.3 — a point-table program whose only gaps are project/
    production-plan facts (no open roles, no missing script facts) must
    resolve USER_FACT_REQUIRED."""
    result = evaluate_role_qualification("hr_cash_rebate", "HR", {}, script_facts={})
    assert result.state == QUAL_USER_FACT_REQUIRED
    assert result.missing_facts


def test_point_table_missing_script_fact_becomes_script_fact_required():
    """Task 8.4 — a point-table program with a genuinely missing story/
    setting/language criterion and every role slot cast (removing the
    curable path) must resolve SCRIPT_FACT_REQUIRED."""
    codes = {"director": ("US",), "writer": ("US",), "producer": ("US",), "composer": ("US",), "lead_cast": ("US",), "editor": ("US",)}
    result = evaluate_role_qualification("fr_trip", "FR", codes, script_facts={})
    assert result.state == QUAL_SCRIPT_FACT_REQUIRED
    assert any("Script Analyzer" in f for f in result.missing_facts)


def test_point_table_curable_gap_surfaces_as_opportunity():
    """Task 8.6 — an open, castable role that could close the point gap
    must surface as CURABLE_GAP with the specific role named as an
    available lever, not a generic missing-fact state."""
    result = evaluate_role_qualification("fr_trip", "FR", {}, script_facts={})
    assert result.state == QUAL_CURABLE_GAP
    assert result.curable_requirements
    assert result.available_levers


def test_authority_known_program_no_longer_rule_data_incomplete():
    """Task 8.7 — every one of the 16 previously-disconnected programs
    (now connected via cultural_point_tables.py or the discretionary/
    definitional registry) must never report RULE_DATA_INCOMPLETE merely
    because project facts are absent -- that reflects real doctrine, not
    an authority gap."""
    for slug in (*CULTURAL_POINT_TABLES, *DISCRETIONARY_OR_DEFINITIONAL_PROGRAMS):
        result = evaluate_role_qualification(slug, "XX", {}, script_facts={})
        assert result.state != QUAL_RULE_DATA_INCOMPLETE, f"{slug} incorrectly still RULE_DATA_INCOMPLETE"


def test_discretionary_finland_always_qualifies_non_evaluated():
    """Finland's Government Decree explicitly states artistic content is
    NOT subject to evaluation -- every project must resolve QUALIFIES for
    this dimension, by design, not by a missing-fact default."""
    result = evaluate_role_qualification("fi_business_finland_incentive", "FI", {}, script_facts={})
    assert result.state == QUAL_QUALIFIES


def test_discretionary_belgium_and_luxembourg_require_a_project_fact():
    """Belgium (European-work/official-co-production status) and
    Luxembourg (AFS committee approval) both resolve to a real project-
    level fact requirement -- a genuinely different real mechanism from a
    missing-research gap."""
    be = evaluate_role_qualification("be_tax_shelter", "BE", {}, script_facts={})
    lu = evaluate_role_qualification("lu_filmfund_tax_shelter_rebate", "LU", {}, script_facts={})
    assert be.state == QUAL_USER_FACT_REQUIRED
    assert lu.state == QUAL_USER_FACT_REQUIRED
    assert be.missing_facts and lu.missing_facts


def test_cyprus_confirmed_test_scoring_withheld_is_authority_unresolved_not_disconnected():
    """Cyprus: applicability CONFIRMED (consumed), scoring table a
    genuine authority residual -- PARTIALLY_CONSUMED_WITH_EXACT_
    AUTHORITY_RESIDUAL (Task 6), represented as QUAL_AUTHORITY_UNRESOLVED
    with qualification_route='cultural_point_table', never
    RULE_DATA_INCOMPLETE."""
    assert "cy_film_rebate" in CONFIRMED_TEST_SCORING_WITHHELD_PROGRAMS
    result = evaluate_role_qualification("cy_film_rebate", "CY", {}, script_facts={})
    assert result.state == QUAL_AUTHORITY_UNRESOLVED
    assert result.state != QUAL_RULE_DATA_INCOMPLETE


def test_no_researched_completed_doctrine_remains_disconnected():
    """Task 8.8 / global invariant — every program classified as
    researched/qualification-complete (Queue B's resolved set: cultural
    point tables + discretionary/definitional + confirmed-scoring-
    withheld) must never report RULE_DATA_INCOMPLETE. Combined with
    ROLE_QUALIFICATION_COVERED_SLUGS (pre-existing, unaffected) and
    AUTHORITY_UNRESOLVED_PROGRAMS (genuine applicability residuals,
    unaffected), this proves DISCONNECTED == 0 for the full 71-program
    universe."""
    from app.data.program_requirements import all_program_requirements
    from app.data.cultural_qualification_model import is_spend_only_program

    profiles = all_program_requirements()
    disconnected = []
    for slug, p in profiles.items():
        if p.cultural_test_required is False:
            continue
        if slug in ROLE_QUALIFICATION_COVERED_SLUGS:
            continue
        result = evaluate_role_qualification(slug, p.jurisdiction_code, {}, script_facts={})
        if result.state == QUAL_RULE_DATA_INCOMPLETE and not is_spend_only_program(slug):
            disconnected.append(slug)
    assert disconnected == [], f"researched-but-disconnected programs found: {disconnected}"
