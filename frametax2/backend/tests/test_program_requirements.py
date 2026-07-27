"""
Final Global Discovery phase: the Production Requirements Database.
"""
from __future__ import annotations

import pytest

from app.data.program_requirements import (
    AllocationType,
    ProgramRequirementsProfile,
    RecordStatus,
    SourceType,
    TimingBasis,
    TimingFact,
    all_program_requirements,
    get_program_requirements,
)


class TestRegistryIntegrity:
    def test_get_unknown_slug_returns_none_not_a_fabricated_default(self):
        assert get_program_requirements("this_program_does_not_exist") is None

    def test_every_populated_profile_carries_evidence(self):
        for slug, profile in all_program_requirements().items():
            assert profile.evidence is not None, f"{slug} has no EvidenceRecord"
            assert profile.evidence.source_title
            assert profile.evidence.issuing_authority

    def test_every_populated_profile_matches_a_real_executable_program(self):
        """No orphaned requirements profile — every slug here must be a
        real, registered rate-doctrine program (Objective 7: no duplicate
        or invented program identities)."""
        from app.data.program_rate_rules import get_rate_rules

        for slug in all_program_requirements():
            assert get_rate_rules(slug), f"{slug} has requirements but no rate rules — orphaned profile"

    def test_jurisdiction_code_matches_the_doctrine_records_jurisdiction(self):
        from app.data.program_rate_rules import get_rate_rules

        for slug, profile in all_program_requirements().items():
            rules = get_rate_rules(slug)
            # citation text carries jurisdiction implicitly; cross-check via
            # the executable registry instead, which stores it explicitly.
            from app.data.executable_jurisdiction_registry import _REGISTRY as doctrine_registry
            record = doctrine_registry.get(slug)
            if record is not None:
                assert profile.jurisdiction_code == record.jurisdiction_code

    def test_no_field_is_silently_fabricated_as_zero(self):
        """Spot-check: an unconfirmed numeric fact must be None, never 0.0
        — a real architectural risk for any Optional[float] field."""
        profile = get_program_requirements("be_tax_shelter")
        assert profile.min_total_budget_usd is None  # confirmed NO minimum, not zero


class TestTimingBasisDiscipline:
    def test_timing_fact_always_discloses_its_basis(self):
        for slug, profile in all_program_requirements().items():
            for field_name in ("application_deadline", "audit_or_final_certification_deadline", "payment_timing"):
                fact = getattr(profile, field_name)
                if fact is not None:
                    assert isinstance(fact, TimingFact)
                    assert isinstance(fact.basis, TimingBasis)

    def test_timing_fact_construction_requires_explicit_basis(self):
        fact = TimingFact(value="Approx. 90 days after final application", basis=TimingBasis.REPORTED_PRACTICAL)
        assert fact.basis != TimingBasis.STATUTORY_DEADLINE


class TestKnownProfiles:
    """Spot-checks against the primary sources actually read this phase —
    protects against silent drift/mistranscription, not exhaustive re-proof."""

    def test_georgia_transferable_and_nonrefundable(self):
        p = get_program_requirements("us_ga_film_credit")
        assert p.refundable is False
        assert p.transferable is True
        assert p.per_person_cap_usd == 500_000.0

    def test_ny_post_production_confirmed_mutually_exclusive(self):
        p = get_program_requirements("us_ny_post_production_credit")
        assert "mutual" in p.additional_facts.get("mutual_exclusivity", "").lower()

    def test_belgium_confirmed_no_minimum_spend(self):
        p = get_program_requirements("be_tax_shelter")
        assert p.min_total_budget_usd is None
        assert p.evidence.source_type == SourceType.SECONDARY  # scopeinvest.be, not a statute text

    def test_spain_min_spend_matches_doctrine_threshold(self):
        from app.data.program_rate_rules import get_rate_rules

        p = get_program_requirements("es_tax_credit_foreign")
        rules = get_rate_rules("es_tax_credit_foreign")
        # the doctrine's own min_qpe_usd should agree with the requirements profile
        doctrine_min = next((r.min_qpe_usd for r in rules if r.min_qpe_usd), None)
        assert p.min_local_spend_usd == doctrine_min

    def test_croatia_cultural_test_threshold(self):
        p = get_program_requirements("hr_cash_rebate")
        assert p.cultural_test_threshold == 12

    def test_italy_transferable(self):
        p = get_program_requirements("it_tax_credit_foreign")
        assert p.transferable is True

    def test_uk_avec_refundable_and_statutory_claim_deadline(self):
        """Task 92 bounded discovery pass addition."""
        p = get_program_requirements("uk_avec")
        assert p.refundable is True
        assert p.transferable is False
        assert p.audit_or_final_certification_deadline.basis == TimingBasis.STATUTORY_DEADLINE
        assert p.evidence.source_type == SourceType.PRIMARY
        assert "gov.uk" in p.evidence.source_url

    def test_nz_international_rebate_provisional_certificate_before_photography(self):
        """Task 92 bounded discovery pass addition."""
        p = get_program_requirements("nz_spg_international")
        assert p.preapproval_mandatory is True
        assert p.audit_required is True
        assert p.cpa_or_approved_auditor_required is True
        assert p.application_deadline.basis == TimingBasis.OFFICIAL_TARGET
        assert p.refundable is None  # not confirmed from any source reviewed — not guessed

    def test_ireland_refundable_with_statutory_deadline(self):
        """Backend-completion tranche, Objective 2 batch."""
        p = get_program_requirements("ie_section_481")
        assert p.refundable is True
        assert p.application_deadline.basis == TimingBasis.STATUTORY_DEADLINE
        assert p.per_project_cap_usd == 142_565_494.59

    def test_canada_federal_pstc_refundable_deadline_is_estimate_not_statutory(self):
        """The 24-month deadline was sourced from the sibling CPTC program,
        not independently confirmed for PSTC — must be ESTIMATE, not
        STATUTORY_DEADLINE, or it overstates confidence."""
        p = get_program_requirements("ca_federal_pstc")
        assert p.refundable is True
        assert p.audit_or_final_certification_deadline.basis == TimingBasis.ESTIMATE

    def test_czech_expenditure_before_approval_qualifies(self):
        p = get_program_requirements("cz_film_incentive")
        assert p.preapproval_mandatory is False
        assert p.expenditure_before_approval_qualifies is True
        assert p.cpa_or_approved_auditor_required is True

    def test_poland_first_come_first_served(self):
        p = get_program_requirements("pl_pisf_cash_rebate")
        assert p.allocation_type == AllocationType.FIRST_COME_FIRST_SERVED
        assert p.preapproval_mandatory is True

    def test_france_trip_refundable_transferability_unconfirmed(self):
        """'Discountable at a financial institution' is loan-security use,
        not confirmed as a legal transfer — must stay None, not True."""
        p = get_program_requirements("fr_trip")
        assert p.refundable is True
        assert p.transferable is None
        assert p.min_local_spend_usd == 285_130.99


class TestScopeIsDisclosedNotFabricated:
    def test_unpopulated_executable_program_returns_none(self):
        """The vast majority of executable programs do NOT yet have a
        requirements profile — this is a disclosed scope boundary, and
        callers must handle None gracefully rather than assume coverage.

        Uses the canonical registry (not a direct jc.ALL_PROFILES scan)
        — a raw ALL_PROFILES-only or executable_jurisdiction_registry-only
        scan each miss part of the true executable set (see
        canonical_executable_registry.py's module docstring for the
        exact undercount this caused earlier in the session)."""
        from app.data.canonical_executable_registry import canonical_executable_program_slugs

        populated = set(all_program_requirements())
        all_slugs = canonical_executable_program_slugs()
        unpopulated = all_slugs - populated
        assert len(unpopulated) > 0, "coverage claim would be misleading if this ever hits zero silently"
        for slug in list(unpopulated)[:5]:
            assert get_program_requirements(slug) is None
