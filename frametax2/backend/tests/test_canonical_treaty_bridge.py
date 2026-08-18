"""
canonical_treaty_bridge.py — focused unit tests.

Proves the fail-closed correction Codex's optimizer-correctness
classification demanded: registry presence != eligibility, and an
unresolved or failed cultural test can NEVER produce an ELIGIBLE result,
even though the underlying treaty_engine functions' own is_eligible
booleans do not enforce that by themselves.
"""
from __future__ import annotations

from app.calculators import treaty_engine as te
from app.calculators.canonical_treaty_bridge import (
    RESOLUTION_ELIGIBLE,
    RESOLUTION_INELIGIBLE,
    RESOLUTION_UNRESOLVED_FACTS,
    evaluate_bilateral_coproduction_opportunity,
    evaluate_eurimages_coproduction_opportunity,
    find_eurimages_partners,
    find_real_bilateral_partners,
)


def _real_bilateral_pair() -> tuple[str, str]:
    """Find one real, currently-registered bilateral treaty pair to test
    against, without hard-coding a specific pair that might not exist —
    reads the live registry."""
    for code in ("CA", "FR", "GB", "DE", "IT", "AU"):
        partners = te.get_available_bilateral_treaties(code)
        if partners:
            other = partners[0].jurisdiction_b if partners[0].jurisdiction_a == code else partners[0].jurisdiction_a
            return code, other
    raise AssertionError("expected at least one real bilateral treaty in treaty_engine's registry")


def _real_bilateral_pair_requiring_cultural_test() -> tuple[str, str]:
    """Same as _real_bilateral_pair but specifically finds a pair whose
    treaty DOES require a cultural test — needed to exercise the
    fail-closed cultural gate unconditionally rather than skip."""
    for code in ("CA", "FR", "GB", "DE", "IT", "AU", "MU", "GR", "AT", "ES", "BE", "IE"):
        for treaty in te.get_available_bilateral_treaties(code):
            if treaty.cultural_test_required:
                other = treaty.jurisdiction_b if treaty.jurisdiction_a == code else treaty.jurisdiction_a
                return code, other
    raise AssertionError("expected at least one real bilateral treaty requiring a cultural test")


def test_registry_presence_alone_is_never_reported_as_eligible():
    """The single most important invariant: calling the adapter with NO
    ownership facts must never return ELIGIBLE, no matter how real the
    treaty is."""
    a, b = _real_bilateral_pair()
    result = evaluate_bilateral_coproduction_opportunity(a, b)
    assert result is not None
    assert result.resolution_state == RESOLUTION_UNRESOLVED_FACTS
    assert result.unlocked_slugs == ()


def test_unassessed_cultural_test_never_resolves_eligible_even_with_valid_shares():
    """The confirmed defect: the underlying treaty_engine function accepts
    cultural_test_passed=None and its own is_eligible can still be True.
    The adapter must override this and refuse ELIGIBLE."""
    a, b = _real_bilateral_pair_requiring_cultural_test()
    treaty = te.get_bilateral_treaty(a, b)
    result = evaluate_bilateral_coproduction_opportunity(
        a, b, majority_pct=treaty.majority_min_pct + 1, minority_pct=treaty.minority_min_pct + 1,
        cultural_test_passed=None,
    )
    assert result.resolution_state != RESOLUTION_ELIGIBLE
    assert result.cultural_test_resolved is False


def test_explicit_cultural_test_failure_fails_closed():
    a, b = _real_bilateral_pair_requiring_cultural_test()
    treaty = te.get_bilateral_treaty(a, b)
    result = evaluate_bilateral_coproduction_opportunity(
        a, b, majority_pct=treaty.majority_min_pct + 1, minority_pct=treaty.minority_min_pct + 1,
        cultural_test_passed=False,
    )
    assert result.resolution_state == RESOLUTION_INELIGIBLE
    assert result.unlocked_slugs == ()
    assert any("cultural" in r.lower() for r in result.disqualification_reasons)


def test_insufficient_minority_share_fails_closed():
    """A mandatory numeric threshold failure must produce INELIGIBLE,
    never ELIGIBLE, regardless of cultural test outcome."""
    a, b = _real_bilateral_pair()
    treaty = te.get_bilateral_treaty(a, b)
    result = evaluate_bilateral_coproduction_opportunity(
        a, b, majority_pct=99.0, minority_pct=0.5,  # deliberately below any real minimum
        cultural_test_passed=True,
    )
    assert result.resolution_state == RESOLUTION_INELIGIBLE
    assert result.disqualification_reasons


def test_fully_resolved_valid_facts_can_reach_eligible():
    """When real facts clear every threshold AND the cultural test is
    explicitly passed, the adapter must report ELIGIBLE — fail-closed
    does not mean permanently closed."""
    a, b = _real_bilateral_pair()
    treaty = te.get_bilateral_treaty(a, b)
    minority_pct = treaty.minority_min_pct + 1
    if treaty.minority_max_pct is not None:
        minority_pct = min(minority_pct, treaty.minority_max_pct - 0.5)
    majority_pct = 100.0 - minority_pct
    result = evaluate_bilateral_coproduction_opportunity(
        a, b, majority_pct=majority_pct, minority_pct=minority_pct,
        cultural_test_passed=True,
    )
    assert result.resolution_state == RESOLUTION_ELIGIBLE
    assert result.cultural_test_resolved is True


def test_no_registered_treaty_returns_none_never_a_fabricated_opportunity():
    result = evaluate_bilateral_coproduction_opportunity("ZZ", "YY", majority_pct=80, minority_pct=20)
    assert result is None


def test_eurimages_membership_alone_is_never_eligible():
    """France and Germany are both real Eurimages members (confirmed live
    registry) -- membership alone must not resolve to ELIGIBLE."""
    if not (te.is_eurimages_member("FR") and te.is_eurimages_member("DE")):
        import pytest
        pytest.skip("FR/DE Eurimages membership assumption no longer holds in the live registry")
    result = evaluate_eurimages_coproduction_opportunity(["FR", "DE"])
    assert result is not None
    assert result.resolution_state == RESOLUTION_UNRESOLVED_FACTS


def test_eurimages_unassessed_cultural_test_never_eligible():
    if not (te.is_eurimages_member("FR") and te.is_eurimages_member("DE")):
        import pytest
        pytest.skip("FR/DE Eurimages membership assumption no longer holds in the live registry")
    result = evaluate_eurimages_coproduction_opportunity(
        ["FR", "DE"], country_pcts={"FR": 60.0, "DE": 40.0}, cultural_test_passed=None,
    )
    assert result.resolution_state != RESOLUTION_ELIGIBLE


def test_find_real_bilateral_partners_uses_registry_only():
    a, b = _real_bilateral_pair()
    partners = find_real_bilateral_partners(a, [b, "ZZ", "YY"])
    assert b in partners
    assert "ZZ" not in partners


def test_find_eurimages_partners_requires_home_membership():
    if te.is_eurimages_member("ZZ"):
        import pytest
        pytest.skip("ZZ unexpectedly a Eurimages member")
    assert find_eurimages_partners("ZZ", ["FR", "DE"]) == []
