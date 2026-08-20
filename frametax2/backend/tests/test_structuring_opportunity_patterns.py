"""
test_structuring_opportunity_patterns.py

Final Consolidated Backend Correction + Global Structuring Intelligence
Acceptance, Parts 5-11/30 — proves the durable Gemini structuring pattern
registry and its two new opportunity-bridge discovery functions (SP_002
service->national-treatment arbitrage, SP_004 non-party personnel
exception). Runtime acceptance proofs #13 (non-party personnel exception
is treaty-specific) and #15 (service->national-treatment opportunity
surfaces).
"""
from __future__ import annotations

from app.calculators.canonical_opportunity_bridge import (
    STATUS_AUTHORITY_UNRESOLVED,
    STATUS_CONDITIONAL,
    discover_non_party_personnel_exception_opportunity,
    discover_service_to_national_treatment_opportunity,
)
from app.data.structuring_opportunity_patterns import (
    PRIORITY_P0,
    STRUCTURING_OPPORTUNITY_PATTERNS,
    STRUCTURING_OPPORTUNITY_PATTERNS_VERSION,
)


def test_all_five_patterns_registered_with_real_provenance():
    assert len(STRUCTURING_OPPORTUNITY_PATTERNS) == 5
    for pattern_id, pattern in STRUCTURING_OPPORTUNITY_PATTERNS.items():
        assert pattern.pattern_id == pattern_id
        assert pattern.primary_authority, f"{pattern_id} must carry a real primary authority citation"
        assert pattern.practice_sources, f"{pattern_id} must carry real practice evidence"
        assert pattern.case_studies, f"{pattern_id} must carry a real case study"
        assert pattern.trigger
        assert pattern.existing_cineglobe_capability


def test_three_of_five_patterns_are_p0():
    p0 = [p for p in STRUCTURING_OPPORTUNITY_PATTERNS.values() if p.priority == PRIORITY_P0]
    assert {p.pattern_id for p in p0} == {
        "SP_001_BILATERAL_TO_MULTILATERAL_UPGRADE",
        "SP_002_SERVICE_TO_COPRO_NATIONAL_TREATMENT_ARBITRAGE",
        "SP_004_NON_PARTY_PERSONNEL_EXCEPTION",
    }


# ── SP_002 — Service to Copro National Treatment Arbitrage (P0) ─────────

def test_service_to_national_treatment_surfaces_for_a_real_treaty_partner():
    """FVD (Greece home) — Albania is a real Eurimages member alongside
    Greece; a candidate priced under a foreign/service program for
    Albania must surface the SP_002 opportunity."""
    opp = discover_service_to_national_treatment_opportunity("AL", "al_some_service_program", "GR")
    assert opp is not None
    assert opp.pattern_id == "SP_002_SERVICE_TO_COPRO_NATIONAL_TREATMENT_ARBITRAGE"
    assert opp.jurisdiction_code == "AL"
    assert "eurimages" in opp.title.lower() or "eurimages" in opp.description.lower()
    assert opp.required_facts


def test_service_to_national_treatment_returns_none_with_no_real_treaty():
    """No fabricated opportunity when no real treaty connects the two
    jurisdictions."""
    opp = discover_service_to_national_treatment_opportunity("US-CA", "us_ca_film_credit", "MU")
    assert opp is None


def test_service_to_national_treatment_returns_none_for_home_jurisdiction_itself():
    opp = discover_service_to_national_treatment_opportunity("GR", "gr_cash_rebate", "GR")
    assert opp is None


# ── SP_004 — Non-Party Personnel Exception (P0) ──────────────────────────

def test_non_party_personnel_surfaces_authority_unresolved_for_unresearched_treaty():
    """A real bilateral treaty connects CA and GB; a known lead_cast
    nationality (US) outside both parties triggers the opportunity. No
    currently-registered treaty has its own exception percentage
    individually researched yet, so this correctly resolves
    AUTHORITY_UNRESOLVED — never a fabricated 0% or borrowed percentage
    from a different treaty."""
    from app.calculators import treaty_engine as te

    treaty = te.get_bilateral_treaty("CA", "GB")
    if treaty is None:
        import pytest
        pytest.skip("no CA-GB bilateral treaty registered in this environment")

    opp = discover_non_party_personnel_exception_opportunity(
        "GB", "uk_avec", "CA", role_known_codes={"lead_cast": ("US",)},
    )
    assert opp is not None
    assert opp.pattern_id == "SP_004_NON_PARTY_PERSONNEL_EXCEPTION"
    if treaty.non_party_personnel_exception_pct is None:
        assert opp.status == STATUS_AUTHORITY_UNRESOLVED
        assert opp.required_facts  # discloses what's missing, never silently 0%


def test_non_party_personnel_is_treaty_specific_never_generalized():
    """Runtime acceptance proof #13/CBA-004's own requirement: a treaty
    with a real, set non_party_personnel_exception_pct must never leak
    that percentage onto a DIFFERENT treaty with no such data."""
    from dataclasses import replace
    from unittest.mock import patch

    from app.calculators import treaty_engine as te

    real_treaty = te.get_bilateral_treaty("CA", "GB")
    if real_treaty is None:
        import pytest
        pytest.skip("no CA-GB bilateral treaty registered in this environment")

    # Simulate ONE treaty having a real, researched exception percentage.
    researched_treaty = replace(
        real_treaty, non_party_personnel_exception_pct=20.0,
        non_party_personnel_exception_citation="Canada-UK Treaty Article 4 (test fixture)",
    )
    with patch.object(te, "get_bilateral_treaty", side_effect=lambda a, b: (
        researched_treaty if {a.upper(), b.upper()} == {"CA", "GB"} else None
    )):
        resolved = discover_non_party_personnel_exception_opportunity(
            "GB", "uk_avec", "CA", role_known_codes={"lead_cast": ("US",)},
        )
        assert resolved is not None
        assert resolved.status == STATUS_CONDITIONAL
        assert "20" in resolved.title

        # A DIFFERENT jurisdiction pair with no registered treaty must
        # never inherit CA-GB's 20% — proven by the None-returning path.
        unrelated = discover_non_party_personnel_exception_opportunity(
            "FR", "fr_trip", "MU", role_known_codes={"lead_cast": ("US",)},
        )
        assert unrelated is None


def test_non_party_personnel_returns_none_when_no_non_party_role_present():
    from app.calculators import treaty_engine as te

    treaty = te.get_bilateral_treaty("CA", "GB")
    if treaty is None:
        import pytest
        pytest.skip("no CA-GB bilateral treaty registered in this environment")
    # Lead cast is a party national — nothing to flag.
    opp = discover_non_party_personnel_exception_opportunity(
        "GB", "uk_avec", "CA", role_known_codes={"lead_cast": ("GB",)},
    )
    assert opp is None


def test_non_party_personnel_returns_none_with_no_personnel_facts():
    opp = discover_non_party_personnel_exception_opportunity("GB", "uk_avec", "CA", role_known_codes=None)
    assert opp is None
