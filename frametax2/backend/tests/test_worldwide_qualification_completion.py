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


# ── Second research batch, 2026-08-19 (same pass, continued) ────────────

def test_greece_cultural_test_points_confirmed_real():
    """gr_cash_rebate (FVD's own home program) -- confirmed via
    Saturation.io, fixersingreece.gr, and Lexology's Law 5105/2024 legal
    summary: min 20 of 50 points (fiction/documentary)."""
    p = get_program_requirements("gr_cash_rebate")
    assert p.cultural_test_required is True
    assert p.cultural_test_points == 50
    assert p.cultural_test_threshold == 20
    assert "cultural_test_animation_points" in p.additional_facts


def test_canada_pstc_confirmed_no_cultural_test():
    """Confirmed via canada.ca (official CAVCO/CRA page, primary
    authority): PSTC has no Canadian content requirement, unlike the
    content-gated CPTC."""
    p = get_program_requirements("ca_federal_pstc")
    assert p.cultural_test_required is False


def test_de_dfff_and_nz_spg_internal_consistency_fixed():
    """Two DATA_EXISTS_BUT_STILL_NOT_CONSUMED consistency defects fixed
    without new research: de_dfff already had real role rows in
    cultural_qualification_model.py but cultural_test_required was never
    set to match (now True); nz_spg_international is in the confirmed
    spend-only allowlist but was never set to match (now False)."""
    from app.calculators.canonical_role_qualification_bridge import ROLE_QUALIFICATION_COVERED_SLUGS

    de = get_program_requirements("de_dfff")
    assert de.cultural_test_required is True
    assert "de_dfff" in ROLE_QUALIFICATION_COVERED_SLUGS

    nz = get_program_requirements("nz_spg_international")
    assert nz.cultural_test_required is False
    assert is_spend_only_program("nz_spg_international") is True


def test_us_state_and_service_programs_confirmed_no_cultural_test():
    """us_or_opif (oregonfilm.org + Oregon Administrative Rules) and
    us_ny_post_production_credit (tax.ny.gov) confirmed no cultural test
    -- consistent with every other US program in this registry."""
    for slug in ("us_or_opif", "us_ny_post_production_credit"):
        p = get_program_requirements(slug)
        assert p.cultural_test_required is False, slug


def test_authority_unresolved_programs_have_real_researched_propositions():
    """Task 5/12 -- mu_edb_incentive and fj_film_rebate both had real
    external research performed this pass and genuinely could not be
    resolved. Distinct from RULE_DATA_INCOMPLETE (never researched)."""
    from app.calculators.canonical_role_qualification_bridge import (
        AUTHORITY_UNRESOLVED_PROGRAMS,
        evaluate_role_qualification,
    )
    for slug in ("mu_edb_incentive", "fj_film_rebate"):
        assert slug in AUTHORITY_UNRESOLVED_PROGRAMS
        result = evaluate_role_qualification(slug, "XX", {})
        assert result.state == QUAL_AUTHORITY_UNRESOLVED
        assert result.missing_facts
        # cultural_test_required must genuinely stay None -- never
        # silently defaulted to True or False without real authority.
        p = get_program_requirements(slug)
        assert p.cultural_test_required is None


def test_mauritius_prior_rejected_claim_not_reintroduced():
    """Regression guard: a prior Codex/Gemini cross-verification already
    investigated and REJECTED the '90% Mauritius filming for 40% tier'
    claim (it belongs to a different government measure -- National
    Assembly Hansard, 14 May 2019). This pass's new research surfaced the
    same claim from a secondary fixer site; it must NOT be reintroduced
    as a confirmed fact anywhere in the qualification data."""
    from app.data.program_rate_rules import MU_UNVERIFIED_CLAIMS
    rejected = [c for c in MU_UNVERIFIED_CLAIMS if "90%" in c.claim]
    assert rejected
    assert "REJECTED" in rejected[0].verification_status
    # The claim may legitimately be DISCLOSED elsewhere (e.g. as a
    # not-applied item in additional_facts) -- what must never happen is
    # it being presented as a confirmed/applied condition anywhere.
    p = get_program_requirements("mu_edb_incentive")
    facts_text = str(p.additional_facts)
    if "90%" in facts_text:
        assert "NOT" in facts_text or "not applied" in facts_text.lower(), (
            "the 90% claim must never be disclosed as a confirmed/applied condition"
        )


def test_program_universe_terminal_states_have_exact_proposition_or_resolution():
    """Task 12 -- every program in the canonical 71-program universe must
    resolve cultural_test_required to True, False, or (for the 2 real
    AUTHORITY_UNRESOLVED cases) have an exact, non-generic proposition on
    file. No unexplained unknown."""
    from app.data.program_requirements import all_program_requirements
    from app.calculators.canonical_role_qualification_bridge import AUTHORITY_UNRESOLVED_PROGRAMS

    profiles = all_program_requirements()
    unresolved = {s for s, p in profiles.items() if p.cultural_test_required is None}
    assert unresolved == set(AUTHORITY_UNRESOLVED_PROGRAMS.keys()), (
        "Every cultural_test_required=None program must have a registered, "
        "exact AUTHORITY_UNRESOLVED proposition -- no silent/unexplained unknown."
    )
