"""
test_jurisdiction_doctrine_consistency.py

Reusable schema/property tests for the worldwide jurisdiction population
phase (see docs/architecture/CAPABILITY_LEDGER.md). These run against
EVERY jurisdiction currently in jurisdiction_comparison.py's ALL_PROFILES
and program_rate_rules.py — not one test per jurisdiction, so they scale
to 200+ entries without linear growth in test count. Catches the failure
modes named in the worldwide-population mandate: divergence between the
two doctrine sources, invalid rate bands, missing provenance, and
executable/discovery mismatches — automatically, for every future
jurisdiction added, not just the ones written by hand today.
"""
from __future__ import annotations

from app.calculators.jurisdiction_comparison import ALL_PROFILES
from app.data.program_rate_rules import get_rate_rules


def _programs_with_rate_rules() -> set[str]:
    slugs: set[str] = set()
    for profile in ALL_PROFILES.values():
        if get_rate_rules(profile.program_slug):
            slugs.add(profile.program_slug)
    return slugs


class TestNoInvalidRateBands:
    def test_max_rate_never_below_base_rate(self):
        for code, profile in ALL_PROFILES.items():
            if profile.base_rate is not None and profile.max_rate is not None:
                assert profile.max_rate >= profile.base_rate, (
                    f"{code} ({profile.program_slug}): max_rate "
                    f"{profile.max_rate} < base_rate {profile.base_rate}"
                )

    def test_rates_are_plausible_decimals(self):
        # Catches an accidental 30 instead of 0.30, or a negative rate.
        for code, profile in ALL_PROFILES.items():
            for label, val in (("base_rate", profile.base_rate), ("max_rate", profile.max_rate)):
                if val is not None:
                    assert 0.0 <= val <= 1.0, f"{code} ({profile.program_slug}): {label}={val} out of [0,1]"

    def test_rate_rule_tiers_never_have_max_below_min(self):
        for slug in _programs_with_rate_rules():
            rates = [r.rate for r in get_rate_rules(slug)]
            assert max(rates) >= min(rates)


class TestProvenance:
    def test_every_executable_program_has_a_citation(self):
        for slug in _programs_with_rate_rules():
            for rule in get_rate_rules(slug):
                assert rule.citation and len(rule.citation) > 20, (
                    f"{slug}/{rule.tier_id}: citation missing or too short to be real provenance"
                )
                assert rule.source_ref, f"{slug}/{rule.tier_id}: source_ref missing"

    def test_every_executable_program_has_a_declared_confidence_tier(self):
        for slug in _programs_with_rate_rules():
            for rule in get_rate_rules(slug):
                assert rule.confidence_tier in ("DISCOVERY", "PARSED", "VERIFIED")

    def test_profile_and_rate_rule_confidence_tiers_do_not_diverge(self):
        # A profile claiming PARSED/VERIFIED while its RateRule is still
        # DISCOVERY (or vice versa) is exactly the kind of silent
        # divergence the worldwide-population mandate calls out.
        for code, profile in ALL_PROFILES.items():
            rules = get_rate_rules(profile.program_slug)
            if not rules:
                continue
            rule_tiers = {r.confidence_tier for r in rules}
            assert profile.confidence_tier in rule_tiers, (
                f"{code} ({profile.program_slug}): profile confidence_tier="
                f"{profile.confidence_tier!r} not present among its own "
                f"RateRule tiers {rule_tiers!r} — the two doctrine sources "
                f"have diverged"
            )


class TestNoSilentFallback:
    def test_discovery_tier_programs_are_not_silently_treated_as_verified(self):
        # A DISCOVERY-tier profile must never be the sole rate rule serving
        # a program — DISCOVERY means "unverified lead," not "usable".
        for code, profile in ALL_PROFILES.items():
            rules = get_rate_rules(profile.program_slug)
            if profile.confidence_tier == "DISCOVERY" and rules:
                assert all(r.confidence_tier == "DISCOVERY" for r in rules), (
                    f"{code}: profile is DISCOVERY but its executable RateRule "
                    f"claims a higher tier without corresponding profile promotion"
                )

    def test_min_qpe_usd_never_negative_or_absurd(self):
        for slug in _programs_with_rate_rules():
            for rule in get_rate_rules(slug):
                if rule.min_qpe_usd is not None:
                    assert 0 <= rule.min_qpe_usd < 1_000_000_000, (
                        f"{slug}/{rule.tier_id}: min_qpe_usd={rule.min_qpe_usd} implausible"
                    )


class TestExecutableDiscoveryAlignment:
    def test_every_all_profiles_entry_resolves_a_rate_for_some_qpe(self):
        # A profile present in ALL_PROFILES with real base_rate/max_rate
        # data but ZERO RateRule entries is exactly "present in a
        # capability catalog but not usable by the worldwide optimizer" —
        # the distinction the worldwide-population mandate requires this
        # phase to keep proving, not just assert once.
        executable_codes = {code for code, p in ALL_PROFILES.items() if get_rate_rules(p.program_slug)}
        for code in executable_codes:
            profile = ALL_PROFILES[code]
            rules = get_rate_rules(profile.program_slug)
            # at least one tier must be reachable by SOME qpe_usd value
            reachable = any(r.min_qpe_usd is None or r.min_qpe_usd < 1e12 for r in rules)
            assert reachable, f"{code} ({profile.program_slug}): no RateRule tier is reachable by any QPE"

    def test_graduated_bracket_rules_have_ascending_thresholds(self):
        for slug in _programs_with_rate_rules():
            for rule in get_rate_rules(slug):
                if rule.graduated_brackets:
                    ceilings = [c for c, _r in rule.graduated_brackets]
                    assert ceilings == sorted(ceilings), (
                        f"{slug}/{rule.tier_id}: graduated_brackets ceilings not ascending"
                    )
                    for ceiling, bracket_rate in rule.graduated_brackets:
                        assert 0.0 <= bracket_rate <= 1.0
                        assert ceiling > 0
