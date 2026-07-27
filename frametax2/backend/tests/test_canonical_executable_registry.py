"""
Backend-completion tranche, Objective 1: canonical executable registry.

Regression coverage against the exact reporting bug this module fixes:
a jurisdiction/requirements-profile gap count computed from only
executable_jurisdiction_registry.py silently excluded six real
executable jurisdictions (MU, GR, IE, MT, ES, FR) whose doctrine
predates that registry.
"""
from __future__ import annotations

# Pre-existing circular-import ordering quirk between program_rate_rules.py,
# program_rate_rules_worldwide.py, and executable_jurisdiction_registry.py
# (not introduced by this module): whichever of the first/third is imported
# as the very first top-level import in the process determines whether the
# cycle resolves cleanly. Warming up program_rate_rules first makes this
# file's tests pass under any collection order, not just inside the full
# suite where some earlier-collected file happens to warm it up already.
import app.data.program_rate_rules  # noqa: F401

from app.data.canonical_executable_registry import (
    canonical_executable_jurisdictions,
    canonical_executable_program_slugs,
    executable_jurisdictions_without_requirements_profile,
    is_executable_program_slug,
    total_executable_jurisdiction_count,
)


class TestCanonicalRegistryMatchesKnownAuthoritativeSources:
    def test_total_matches_jurisdiction_comparison_all_profiles(self):
        from app.calculators import jurisdiction_comparison as jc

        assert total_executable_jurisdiction_count() == len(jc.ALL_PROFILES)

    def test_total_matches_harness_total_executable_jurisdictions(self):
        from app.calculators.production_validation_harness import run_stage1_engine_validation

        s1 = run_stage1_engine_validation()
        assert s1["total_executable_jurisdictions"] == total_executable_jurisdiction_count()

    def test_total_is_110(self):
        """A hardcoded spot-check, not the source of truth (the two tests
        above are) — protects against a SILENT drift going unnoticed."""
        assert total_executable_jurisdiction_count() == 110


class TestEveryEntryReallyIsExecutable:
    def test_every_primary_slug_resolves_doctrine_and_rate(self):
        from app.data.program_rate_rules import get_rate_rules
        from app.data.program_spend_rules import resolve_program_doctrine

        for code, entry in canonical_executable_jurisdictions().items():
            assert resolve_program_doctrine(entry.primary_program_slug) is not None, code
            assert len(get_rate_rules(entry.primary_program_slug)) > 0, code

    def test_every_secondary_slug_resolves_doctrine_and_rate(self):
        from app.data.program_rate_rules import get_rate_rules
        from app.data.program_spend_rules import resolve_program_doctrine

        for code, entry in canonical_executable_jurisdictions().items():
            for slug in entry.secondary_program_slugs:
                assert resolve_program_doctrine(slug) is not None, (code, slug)
                assert len(get_rate_rules(slug)) > 0, (code, slug)


class TestLegacyPreRegistryJurisdictionsAreIncluded:
    """The six jurisdictions executable_jurisdiction_registry.py's own
    docstring says were deliberately never migrated onto it."""

    def test_legacy_jurisdictions_present(self):
        codes = set(canonical_executable_jurisdictions())
        for code in ("MU", "GR", "IE", "MT", "ES", "FR"):
            assert code in codes

    def test_legacy_jurisdictions_flagged_with_correct_source(self):
        registry = canonical_executable_jurisdictions()
        for code in ("MU", "GR", "IE", "MT", "ES", "FR"):
            assert registry[code].doctrine_source == "legacy_pre_registry"


class TestSecondarySlugsSurfaced:
    """Programs like NY's post-production credit and CZ's animation
    variant are real, executable, second programs for an already-counted
    jurisdiction — must be discoverable, not silently dropped."""

    def test_ny_post_production_credit_is_a_secondary_slug(self):
        registry = canonical_executable_jurisdictions()
        assert "us_ny_post_production_credit" in registry["US-NY"].secondary_program_slugs

    def test_cz_animation_variant_is_a_secondary_slug(self):
        registry = canonical_executable_jurisdictions()
        assert "cz_film_incentive_animation" in registry["CZ"].secondary_program_slugs

    def test_secondary_slugs_included_in_program_slug_universe(self):
        all_slugs = canonical_executable_program_slugs()
        assert "us_ny_post_production_credit" in all_slugs
        assert "cz_film_incentive_animation" in all_slugs

    def test_is_executable_program_slug_true_for_secondary(self):
        assert is_executable_program_slug("us_ny_post_production_credit") is True

    def test_is_executable_program_slug_false_for_unknown(self):
        assert is_executable_program_slug("__not_a_real_program__") is False


class TestRequirementsGapAnalysis:
    """The exact accounting that was wrong (95 instead of 98, computed
    against only executable_jurisdiction_registry.py, at the point this
    module was introduced). Deliberately NOT a hardcoded snapshot count
    here — the Production Requirements Database grows in batches every
    session, so a hardcoded number would need editing every time and
    would stop being a real regression guard. The invariant below is
    what should never break instead."""

    def test_gap_plus_populated_equals_total(self):
        from app.data.program_requirements import all_program_requirements

        gap = executable_jurisdictions_without_requirements_profile()
        populated_primary_count = total_executable_jurisdiction_count() - len(gap)
        assert populated_primary_count == len(
            {e.primary_program_slug for e in canonical_executable_jurisdictions().values()}
            & set(all_program_requirements())
        )
        assert len(gap) + populated_primary_count == total_executable_jurisdiction_count()

    def test_es_is_not_in_the_gap_it_already_has_a_profile(self):
        """ES (es_tax_credit_foreign) is exactly the jurisdiction the
        executable_jurisdiction_registry-only scan silently mis-scoped
        earlier this session — it has a profile but wasn't a member of
        that registry, so it was invisible to that scan."""
        gap = executable_jurisdictions_without_requirements_profile()
        assert "ES" not in gap

    def test_gap_shrinks_when_a_profile_is_added_and_grows_back_on_removal(self):
        from app.data.program_requirements import _REGISTRY as req_registry
        from app.data.program_requirements import get_program_requirements

        before = len(executable_jurisdictions_without_requirements_profile())
        # Pick any currently-unpopulated executable primary slug.
        target = next(
            entry.primary_program_slug
            for entry in canonical_executable_jurisdictions().values()
            if get_program_requirements(entry.primary_program_slug) is None
        )
        assert target not in req_registry
        from app.data.program_requirements import EvidenceRecord, ProgramRequirementsProfile, RecordStatus, SourceType, register
        jurisdiction_code = next(
            e.jurisdiction_code for e in canonical_executable_jurisdictions().values()
            if e.primary_program_slug == target
        )
        register(ProgramRequirementsProfile(
            program_slug=target, jurisdiction_code=jurisdiction_code,
            evidence=EvidenceRecord(
                source_title="test", source_url=None, issuing_authority="test",
                source_type=SourceType.SECONDARY, status=RecordStatus.CURRENT,
            ),
        ))
        try:
            after = len(executable_jurisdictions_without_requirements_profile())
            assert after == before - 1
        finally:
            del req_registry[target]
            after_cleanup = len(executable_jurisdictions_without_requirements_profile())
            assert after_cleanup == before
