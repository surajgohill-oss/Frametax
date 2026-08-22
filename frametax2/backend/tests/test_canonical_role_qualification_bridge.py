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
    # OH-004 fix (CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT): `"fr_composer" in
    # lever or True` is always True regardless of `lever`'s actual content
    # -- the assertion below passed unconditionally, proving nothing about
    # whether "fr_composer" is genuinely present. Fixed to a real,
    # falsifiable membership check.
    assert "fr_composer" in result.available_levers  # composer is an open, curable slot


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
    universe.

    CBA-005 fix (Codex audit 4db2cea): this test previously skipped
    every profile with cultural_test_required=False — exactly the
    programs whose served state the audit found was actually wrong
    (RULE_DATA_INCOMPLETE despite a confirmed no-cultural-test profile).
    The skip is removed now that the underlying defect is fixed: the
    served bridge derives NOT_APPLICABLE directly from cultural_test_
    required=False, so this test can honestly check the REAL state for
    all 71 programs, not a filtered subset."""
    from app.data.program_requirements import all_program_requirements
    from app.data.cultural_qualification_model import is_spend_only_program

    profiles = all_program_requirements()
    disconnected = []
    for slug, p in profiles.items():
        if slug in ROLE_QUALIFICATION_COVERED_SLUGS:
            continue
        result = evaluate_role_qualification(slug, p.jurisdiction_code, {}, script_facts={})
        if result.state == QUAL_RULE_DATA_INCOMPLETE and not is_spend_only_program(slug):
            disconnected.append(slug)
    assert disconnected == [], f"researched-but-disconnected programs found: {disconnected}"


# ═══════════════════════════════════════════════════════════════════════
# Consolidated Backend Correction (2026-08-20), Codex audit 4db2cea —
# focused prevention tests for CBA-003/004/005.
# ═══════════════════════════════════════════════════════════════════════

def test_pstc_confirmed_not_applicable_not_rule_data_incomplete():
    """Codex acceptance proof #3 — Canada PSTC is NOT_APPLICABLE for
    cultural qualification (it has no cultural test by real statute),
    never RULE_DATA_INCOMPLETE."""
    result = evaluate_role_qualification("ca_federal_pstc", "CA", {})
    assert result.state == QUAL_NOT_APPLICABLE


def test_all_confirmed_no_cultural_test_programs_are_not_applicable():
    """CBA-005 — every one of the 48 programs with program_requirements.
    py's own cultural_test_required=False must resolve NOT_APPLICABLE,
    derived directly from that field, never RULE_DATA_INCOMPLETE
    (Codex's demonstrated defect: 46 of 48 previously fell through)."""
    from app.data.program_requirements import all_program_requirements
    profiles = all_program_requirements()
    no_cultural_test = [s for s, p in profiles.items() if p.cultural_test_required is False]
    assert len(no_cultural_test) >= 40  # real, not a coincidentally-small sample
    for slug in no_cultural_test:
        p = profiles[slug]
        result = evaluate_role_qualification(slug, p.jurisdiction_code, {})
        assert result.state == QUAL_NOT_APPLICABLE, f"{slug} incorrectly reports {result.state}"


def test_script_fact_semantic_match_closes_false_qualifies_defect():
    """CBA-003 — Codex's exact demonstrated false-positive: a Tokyo
    location / US character nationality / English language fact set must
    NEVER satisfy fr_trip's France-specific criteria merely because a
    fact of the right element_type exists. A genuinely matching fact set
    (Paris/French) must still be able to QUALIFY."""
    codes = {"director": ("FR",), "writer": ("FR",), "producer": ("FR",),
             "composer": ("FR",), "lead_cast": ("FR",), "editor": ("FR",)}
    wrong = evaluate_role_qualification(
        "fr_trip", "FR", codes,
        script_facts={"location": ("Tokyo",), "character_nationality": ("US",), "language": ("English",)},
    )
    assert wrong.state != QUAL_QUALIFIES

    right = evaluate_role_qualification(
        "fr_trip", "FR", codes,
        script_facts={"location": ("Paris",), "language": ("French",), "cultural_reference": ("French painter",)},
    )
    assert right.state == QUAL_QUALIFIES


def test_authority_incomplete_table_never_emits_false_qualifies():
    """CBA-003 — an AUTHORITY_INCOMPLETE (aggregate/approximate) cultural
    point table must be quarantined from deterministic QUALIFIES even
    when its own arithmetic crosses the threshold: the aggregate cannot
    verify the real official item-level breakdown would also pass."""
    from app.data.cultural_point_tables import TABLE_AUTHORITY_INCOMPLETE, CULTURAL_POINT_TABLES
    incomplete_slugs = [s for s, t in CULTURAL_POINT_TABLES.items() if t.completeness == TABLE_AUTHORITY_INCOMPLETE]
    assert "hr_cash_rebate" in incomplete_slugs
    assert "pl_pisf_cash_rebate" in incomplete_slugs
    # pl_pisf_cash_rebate has a real CATEGORY_ROLE criterion its own
    # arithmetic can cross the threshold through — the quarantine must
    # still intercept it before QUALIFIES.
    result = evaluate_role_qualification(
        "pl_pisf_cash_rebate", "PL", {"entity": ("PL",)},
        script_facts={"location": ("Warsaw",), "cultural_reference": ("Polish",)},
    )
    assert result.state == QUAL_AUTHORITY_UNRESOLVED
    assert result.state != QUAL_QUALIFIES


def test_table_completeness_classification_matches_codex_audit():
    """CBA-003 — completeness must be an explicit, per-table classification
    (never inferred from modeled_max == total_points alone, which would
    incorrectly treat mt_mfc_rebate's single-aggregate 40/40 as COMPLETE)."""
    from app.data.cultural_point_tables import (
        CULTURAL_POINT_TABLES, TABLE_COMPLETE, TABLE_PARTIAL_WITH_KNOWN_HEADROOM, TABLE_AUTHORITY_INCOMPLETE,
    )
    assert CULTURAL_POINT_TABLES["no_film_incentive"].completeness == TABLE_COMPLETE
    assert CULTURAL_POINT_TABLES["at_fisa_plus"].completeness == TABLE_PARTIAL_WITH_KNOWN_HEADROOM
    # mt_mfc_rebate's modeled sum EQUALS total_points (40==40) despite being
    # a single all-or-nothing aggregate, not a real itemised table -- proves
    # completeness is a real, independent classification, not a derived one.
    mt = CULTURAL_POINT_TABLES["mt_mfc_rebate"]
    assert sum(c.max_points for c in mt.criteria) == mt.total_points
    assert mt.completeness == TABLE_AUTHORITY_INCOMPLETE


def test_invalid_coproduction_cultural_test_text_stays_unresolved_not_false():
    """CBA-004 — an invalid/unrecognized coproduction_cultural_test_passed
    value must resolve None (unresolved), never a silently-confirmed
    False (which the pre-fix code produced for anything other than an
    exact true/1/yes token)."""
    import asyncio
    from app.services.canonical_evaluation import _coproduction_facts

    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows
        def all(self):
            return self._rows

    class _FakeSession:
        def __init__(self, rows):
            self._rows = rows
        async def execute(self, *_a, **_kw):
            return _FakeResult(self._rows)

    session = _FakeSession([("coproduction_cultural_test_passed", "unknown")])
    _maj, _min, cultural = asyncio.run(_coproduction_facts(session, "fake-project-id"))
    assert cultural is None


# ── Final Consolidated Backend Correction + Global Structuring
# Intelligence Acceptance, Part 4/CBA-004 — nationality vs residency ─────
# vs work-location must remain typed, distinct facts. Uses a synthetic,
# temporarily-registered table (never touching any of the 13 real,
# researched tables) so the test proves the MECHANISM generically,
# without fabricating a nationality/residency distinction for any real
# program's criteria that hasn't actually been re-researched.

def test_residency_cannot_satisfy_a_nationality_only_criterion():
    from unittest.mock import patch

    from app.calculators.canonical_role_qualification_bridge import evaluate_point_table_qualification
    from app.data.cultural_point_tables import (
        CATEGORY_ROLE, FACT_KIND_NATIONALITY, FACT_USER, TABLE_COMPLETE,
        CulturalPointCriterion, CulturalPointTable,
    )

    synthetic = CulturalPointTable(
        program_slug="zz_test_nationality_only", total_points=10.0, threshold=10.0,
        completeness=TABLE_COMPLETE, source_note="synthetic test fixture",
        criteria=(
            CulturalPointCriterion(
                key="director-nat", category=CATEGORY_ROLE, fact_type=FACT_USER,
                max_points=10.0, role="director", fact_kind=FACT_KIND_NATIONALITY,
                description="Director must be a national of ZZ",
            ),
        ),
    )
    with patch.dict(CULTURAL_POINT_TABLES, {"zz_test_nationality_only": synthetic}):
        # Director is a RESIDENT of ZZ but a national of elsewhere — a
        # nationality-only criterion must NOT be satisfied by residency.
        result = evaluate_point_table_qualification(
            "zz_test_nationality_only", "ZZ",
            role_known_codes={"director": ("ZZ",)},  # merged set has ZZ (would falsely satisfy pre-fix)
            script_facts={},
            typed_personnel_facts={"director": {"nationality": ("YY",), "residency": ("ZZ",)}},
        )
        assert result.state != QUAL_QUALIFIES
        assert any("director-nat" in f for f in result.failed_requirements)


def test_nationality_cannot_satisfy_a_residency_only_criterion():
    from unittest.mock import patch

    from app.calculators.canonical_role_qualification_bridge import evaluate_point_table_qualification
    from app.data.cultural_point_tables import (
        CATEGORY_ROLE, FACT_KIND_RESIDENCY, FACT_USER, TABLE_COMPLETE,
        CulturalPointCriterion, CulturalPointTable,
    )

    synthetic = CulturalPointTable(
        program_slug="zz_test_residency_only", total_points=10.0, threshold=10.0,
        completeness=TABLE_COMPLETE, source_note="synthetic test fixture",
        criteria=(
            CulturalPointCriterion(
                key="director-res", category=CATEGORY_ROLE, fact_type=FACT_USER,
                max_points=10.0, role="director", fact_kind=FACT_KIND_RESIDENCY,
                description="Director must be resident in ZZ",
            ),
        ),
    )
    with patch.dict(CULTURAL_POINT_TABLES, {"zz_test_residency_only": synthetic}):
        # Director is a NATIONAL of ZZ but resides elsewhere — a
        # residency-only criterion must NOT be satisfied by nationality.
        result = evaluate_point_table_qualification(
            "zz_test_residency_only", "ZZ",
            role_known_codes={"director": ("ZZ",)},
            script_facts={},
            typed_personnel_facts={"director": {"nationality": ("ZZ",), "residency": ("YY",)}},
        )
        assert result.state != QUAL_QUALIFIES
        assert any("director-res" in f for f in result.failed_requirements)


def test_matching_typed_fact_does_satisfy_its_own_kind():
    from unittest.mock import patch

    from app.calculators.canonical_role_qualification_bridge import evaluate_point_table_qualification
    from app.data.cultural_point_tables import (
        CATEGORY_ROLE, FACT_KIND_RESIDENCY, FACT_USER, TABLE_COMPLETE,
        CulturalPointCriterion, CulturalPointTable,
    )

    synthetic = CulturalPointTable(
        program_slug="zz_test_residency_match", total_points=10.0, threshold=10.0,
        completeness=TABLE_COMPLETE, source_note="synthetic test fixture",
        criteria=(
            CulturalPointCriterion(
                key="director-res", category=CATEGORY_ROLE, fact_type=FACT_USER,
                max_points=10.0, role="director", fact_kind=FACT_KIND_RESIDENCY,
                description="Director must be resident in ZZ",
            ),
        ),
    )
    with patch.dict(CULTURAL_POINT_TABLES, {"zz_test_residency_match": synthetic}):
        result = evaluate_point_table_qualification(
            "zz_test_residency_match", "ZZ",
            role_known_codes={"director": ("ZZ",)},
            script_facts={},
            typed_personnel_facts={"director": {"nationality": ("YY",), "residency": ("ZZ",)}},
        )
        assert result.state == QUAL_QUALIFIES


def test_either_fact_kind_is_unaffected_by_typed_facts_being_absent():
    """Every one of the 13 real, currently-encoded tables defaults to
    FACT_KIND_EITHER — omitting typed_personnel_facts entirely (as every
    pre-existing caller not yet updated does) must reproduce byte-
    identical behavior to before this fix."""
    result_without_typed = evaluate_role_qualification(
        "fr_trip", "FR", role_known_codes={"director": ("FR",)}, script_facts={},
    )
    result_with_typed_but_either = evaluate_role_qualification(
        "fr_trip", "FR", role_known_codes={"director": ("FR",)}, script_facts={},
        typed_personnel_facts={"director": {"nationality": ("FR",), "residency": ()}},
    )
    assert result_without_typed.state == result_with_typed_but_either.state
