"""
Consolidated Global Remediation, Phase C verification.

Locks in the safety invariant for the 25 UNPRICEABLE_AUTHORITY_INSUFFICIENT
+ 4 NON_ECONOMIC_CONFIRMED canonical identities: they must never become
priceable, must never enter the executable jurisdiction registry, and must
never carry synthetic economics.
"""
from app.calculators.jurisdiction_comparison import ALL_PROFILES
from app.data.program_rate_rules import get_rate_rules  # noqa: F401 -- triggers registration import order
from app.data.executable_jurisdiction_registry import _REGISTRY as DOCTRINE_REGISTRY
from app.data.authority_coverage_registry import (
    COVERAGE_REGISTRY,
    get_coverage_status,
    is_covered_unpriceable,
)


def test_registry_has_exactly_29_records():
    assert len(COVERAGE_REGISTRY) == 29


def test_registry_disposition_counts_match_the_validation_gate():
    unpriceable = [r for r in COVERAGE_REGISTRY.values() if r.disposition == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"]
    non_economic = [r for r in COVERAGE_REGISTRY.values() if r.disposition == "NON_ECONOMIC_CONFIRMED"]
    assert len(unpriceable) == 25
    assert len(non_economic) == 4


def test_no_covered_slug_has_an_executable_doctrine_record():
    """The actual pricing-safety guarantee: no RateRule/DoctrineRecord means
    the executable path has nothing to join to and cannot price these."""
    overlap = set(COVERAGE_REGISTRY.keys()) & set(DOCTRINE_REGISTRY.keys())
    assert overlap == set(), f"unpriceable/non-economic slugs leaked into the doctrine registry: {overlap}"


def test_no_covered_slug_is_an_executable_jurisdiction_profile():
    """ALL_PROFILES is jurisdiction_comparison.py's authoritative
    executable-jurisdiction list (resolved doctrine + non-empty RateRule)."""
    profile_slugs = {
        getattr(p, "program_slug", None) for p in ALL_PROFILES.values()
    }
    overlap = set(COVERAGE_REGISTRY.keys()) & profile_slugs
    assert overlap == set(), f"unpriceable/non-economic slugs leaked into ALL_PROFILES: {overlap}"


def test_get_coverage_status_round_trips():
    rec = get_coverage_status("qa_film_incentive")
    assert rec is not None
    assert rec.disposition == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"
    assert rec.jurisdiction_name == "Qatar"


def test_is_covered_unpriceable_true_for_registry_members_false_otherwise():
    assert is_covered_unpriceable("cn_film_incentive") is True  # non-economic
    assert is_covered_unpriceable("pk_pfc_rebate") is True       # unpriceable
    assert is_covered_unpriceable("mu_edb_incentive") is False   # real priced program
    assert is_covered_unpriceable("not_a_real_slug") is False


def test_every_record_carries_reactivation_metadata_not_a_synthetic_rate():
    for rec in COVERAGE_REGISTRY.values():
        assert rec.reason
        assert rec.source_artifact
        assert rec.reactivation_note
        assert not hasattr(rec, "base_rate")
        assert not hasattr(rec, "rate")
