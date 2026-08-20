"""
canonical_treaty_bridge.py

Existing Optimizer/Stacker Reconnection, Task B (treaty/official
co-production) — the canonical eligibility adapter connecting real
project facts to the EXISTING treaty_engine.py (bilateral, Eurimages,
European Convention, Ibermedia registries and eligibility functions).
No new treaty engine, no new registry, no new eligibility doctrine.

Codex's optimizer-correctness classification found the surviving treaty
logic cannot simply be exposed because:
  - registry PRESENCE (a treaty existing between two countries) is not
    the same as ELIGIBILITY (real ownership/spend facts clearing the
    treaty's own thresholds);
  - `evaluate_eurimages_eligibility()` / `evaluate_ibermedia_eligibility()`
    / `evaluate_european_convention_eligibility()` all set
    `cultural_test_required=True` unconditionally but their own
    `is_eligible` boolean NEVER actually checks whether that cultural
    test was passed — it is only ever surfaced as a warning string. A
    caller that read `is_eligible` alone would treat an unassessed
    cultural test as satisfied. `evaluate_bilateral_eligibility()`
    has the same shape: `cultural_test_passed=None` (unassessed) leaves
    `cultural_ok=True`, so `is_eligible` can be True with a cultural test
    that was never actually verified.

This module does NOT edit those functions (no redesign of the treaty
engine's own math/doctrine — explicitly out of scope for this pass; a
separate, later pass will inspect/extend the cultural-qualification
system). Instead, it wraps their results with the CORRECT admission
rule at the boundary that actually matters for canonical publication:
an unresolved (None) or failed (False) cultural fact NEVER allows a
treaty co-production candidate to be reported as fully ELIGIBLE,
regardless of what the underlying engine's own `is_eligible` says.

Resolution states (never conflated):
  UNRESOLVED_FACTS — no real ownership-share/cultural-test project facts
                      exist yet; a registered treaty pathway is real and
                      disclosed as an OPPORTUNITY, never as qualified,
                      priced, or comparable economics.
  ELIGIBLE          — real facts were supplied, cleared every mandatory
                      threshold (majority/minority share, minimum
                      co-producer count, cultural test explicitly
                      TRUE) — a genuinely qualified co-production.
  INELIGIBLE        — real facts were supplied and at least one
                      mandatory requirement failed (including a cultural
                      test explicitly FALSE) — fails closed, with the
                      exact disqualification reasons preserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.calculators import treaty_engine as te

RESOLUTION_UNRESOLVED_FACTS = "UNRESOLVED_FACTS"
RESOLUTION_ELIGIBLE = "ELIGIBLE"
RESOLUTION_INELIGIBLE = "INELIGIBLE"


@dataclass
class CoproOpportunity:
    treaty_type: str                    # "bilateral" | "eurimages" | "european_convention" | "ibermedia"
    treaty_slug: str | None
    parties: tuple[str, ...]            # ISO country codes involved
    resolution_state: str               # one of RESOLUTION_*
    cultural_test_required: bool
    cultural_test_resolved: bool         # True only if an explicit True/False fact was supplied
    unlocked_slugs: tuple[str, ...] = field(default_factory=tuple)
    disqualification_reasons: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)


def evaluate_bilateral_coproduction_opportunity(
    majority_country: str,
    minority_country: str,
    majority_pct: float | None = None,
    minority_pct: float | None = None,
    cultural_test_passed: bool | None = None,
) -> CoproOpportunity | None:
    """
    The canonical bilateral treaty adapter. Returns None if no registered
    treaty exists between the two countries (registry presence is
    checked first, but presence alone is never reported as eligibility).

    Real ownership facts (majority_pct/minority_pct) are required to
    resolve anything beyond UNRESOLVED_FACTS — this function never
    invents a percentage split. Cultural test fails closed: only an
    EXPLICIT True clears it; None (unassessed) or False both prevent
    ELIGIBLE.
    """
    treaty = te.get_bilateral_treaty(majority_country, minority_country)
    if treaty is None:
        return None

    if majority_pct is None or minority_pct is None:
        return CoproOpportunity(
            treaty_type="bilateral",
            treaty_slug=treaty.treaty_slug,
            parties=(majority_country.upper(), minority_country.upper()),
            resolution_state=RESOLUTION_UNRESOLVED_FACTS,
            cultural_test_required=treaty.cultural_test_required,
            cultural_test_resolved=False,
            notes=(
                "A registered bilateral co-production treaty exists between "
                f"{majority_country.upper()} and {minority_country.upper()} "
                f"({treaty.treaty_slug}), but no project fact states each "
                "party's real ownership/spend share — eligibility cannot be "
                "resolved from registry presence alone. Disclosed as an "
                "opportunity, not a qualified structure.",
            ),
        )

    result = te.evaluate_bilateral_eligibility(
        majority_country, minority_country, majority_pct, minority_pct,
        cultural_test_passed=cultural_test_passed,
    )

    cultural_resolved = cultural_test_passed is not None
    # FAIL-CLOSED CORRECTION: the underlying engine's own is_eligible does
    # not require an explicit True for a required cultural test (None
    # leaves it passing) — this adapter overrides that at the boundary.
    cultural_gate_ok = (not treaty.cultural_test_required) or (cultural_test_passed is True)
    is_eligible = result.is_eligible and cultural_gate_ok

    reasons = list(result.disqualification_reasons)
    if treaty.cultural_test_required and cultural_test_passed is not True and result.is_eligible:
        reasons.append(
            f"Treaty {treaty.treaty_slug} requires a cultural test; it was "
            + ("explicitly failed." if cultural_test_passed is False else "never assessed.")
        )

    return CoproOpportunity(
        treaty_type="bilateral",
        treaty_slug=treaty.treaty_slug,
        parties=(majority_country.upper(), minority_country.upper()),
        resolution_state=(
            RESOLUTION_ELIGIBLE if is_eligible
            else (RESOLUTION_INELIGIBLE if cultural_resolved or result.disqualification_reasons
                  else RESOLUTION_UNRESOLVED_FACTS)
        ),
        cultural_test_required=treaty.cultural_test_required,
        cultural_test_resolved=cultural_resolved,
        unlocked_slugs=tuple(result.unlocked_majority_slugs + result.unlocked_minority_slugs + result.unlocked_fund_slugs)
        if is_eligible else (),
        disqualification_reasons=tuple(reasons),
    )


def evaluate_eurimages_coproduction_opportunity(
    co_producer_countries: list[str],
    country_pcts: dict[str, float] | None = None,
    cultural_test_passed: bool | None = None,
) -> CoproOpportunity | None:
    """The canonical Eurimages adapter. Returns None if fewer than 2 of
    the given countries are Eurimages members (nothing to evaluate)."""
    members = [c for c in co_producer_countries if te.is_eurimages_member(c)]
    if len(members) < 2:
        return None

    if country_pcts is None:
        return CoproOpportunity(
            treaty_type="eurimages",
            treaty_slug="eurimages",
            parties=tuple(c.upper() for c in members),
            resolution_state=RESOLUTION_UNRESOLVED_FACTS,
            cultural_test_required=True,
            cultural_test_resolved=False,
            notes=(
                f"{members} are all Eurimages members, but no project fact "
                "states each party's real budget share — eligibility cannot "
                "be resolved from membership alone.",
            ),
        )

    result = te.evaluate_eurimages_eligibility(members, country_pcts)
    cultural_resolved = cultural_test_passed is not None
    cultural_gate_ok = cultural_test_passed is True
    is_eligible = result.is_eligible and cultural_gate_ok

    reasons = list(result.disqualification_reasons)
    if cultural_test_passed is not True and result.is_eligible:
        reasons.append(
            "Eurimages requires a cultural test (European cultural character); "
            + ("explicitly failed." if cultural_test_passed is False else "never assessed.")
        )

    return CoproOpportunity(
        treaty_type="eurimages",
        treaty_slug="eurimages",
        parties=tuple(c.upper() for c in members),
        resolution_state=(
            RESOLUTION_ELIGIBLE if is_eligible
            else (RESOLUTION_INELIGIBLE if cultural_resolved or result.disqualification_reasons
                  else RESOLUTION_UNRESOLVED_FACTS)
        ),
        cultural_test_required=True,
        cultural_test_resolved=cultural_resolved,
        unlocked_slugs=tuple(result.unlocked_fund_slugs) if is_eligible else (),
        disqualification_reasons=tuple(reasons),
    )


def evaluate_european_convention_coproduction_opportunity(
    co_producer_countries: list[str],
    country_pcts: dict[str, float] | None = None,
    cultural_test_passed: bool | None = None,
) -> CoproOpportunity | None:
    """Final Consolidated Backend Correction + Global Structuring
    Intelligence Acceptance, Part 3/CBA-006 -- the canonical European
    Convention on Cinematographic Co-Production adapter, the SAME
    fail-closed pattern as evaluate_eurimages_coproduction_opportunity()
    above (no new treaty doctrine -- treaty_engine.evaluate_european_
    convention_eligibility() and its own real, parsed-tier
    _MULTILATERAL["european_convention"] thresholds, majority_min_pct=30,
    minority_min_pct=10.0, min_coproducer_countries=2, are untouched).

    Also the real, primary-source-cited backing for Gemini P0 pattern
    SP_001 (Bilateral to Multilateral Upgrade, European Convention Art.
    6): a minority contribution between 10% and 19.9% that cannot clear
    a typical bilateral treaty's ~20% floor may still clear this
    multilateral instrument's real 10% floor once a third country is
    genuinely party to the structure -- see structuring_opportunity_
    patterns.py for the durable pattern record this function's own
    resolution feeds into (canonical_evaluation.py's opportunity
    discovery, never a second eligibility engine)."""
    signatories = [c for c in co_producer_countries if te.is_european_convention_signatory(c)]
    if len(signatories) < 2:
        return None

    if country_pcts is None:
        return CoproOpportunity(
            treaty_type="european_convention",
            treaty_slug="european-convention-coproduction",
            parties=tuple(c.upper() for c in signatories),
            resolution_state=RESOLUTION_UNRESOLVED_FACTS,
            cultural_test_required=True,
            cultural_test_resolved=False,
            notes=(
                f"{signatories} are all European Convention signatories, but no "
                "project fact states each party's real budget share — "
                "eligibility cannot be resolved from signatory status alone.",
            ),
        )

    result = te.evaluate_european_convention_eligibility(signatories, country_pcts)
    cultural_resolved = cultural_test_passed is not None
    cultural_gate_ok = cultural_test_passed is True
    is_eligible = result.is_eligible and cultural_gate_ok

    reasons = list(result.disqualification_reasons)
    if cultural_test_passed is not True and result.is_eligible:
        reasons.append(
            "The European Convention requires a cultural test (European "
            "cultural character); "
            + ("explicitly failed." if cultural_test_passed is False else "never assessed.")
        )

    return CoproOpportunity(
        treaty_type="european_convention",
        treaty_slug="european-convention-coproduction",
        parties=tuple(c.upper() for c in signatories),
        resolution_state=(
            RESOLUTION_ELIGIBLE if is_eligible
            else (RESOLUTION_INELIGIBLE if cultural_resolved or result.disqualification_reasons
                  else RESOLUTION_UNRESOLVED_FACTS)
        ),
        cultural_test_required=True,
        cultural_test_resolved=cultural_resolved,
        unlocked_slugs=tuple(result.unlocked_fund_slugs) if is_eligible else (),
        disqualification_reasons=tuple(reasons),
    )


def evaluate_ibermedia_coproduction_opportunity(
    co_producer_countries: list[str],
    country_pcts: dict[str, float] | None = None,
    cultural_test_passed: bool | None = None,
) -> CoproOpportunity | None:
    """CBA-006 -- the canonical Ibermedia adapter, the SAME fail-closed
    pattern as the Eurimages/European Convention adapters (no new treaty
    doctrine -- treaty_engine.evaluate_ibermedia_eligibility() and its
    own real, parsed-tier _MULTILATERAL["ibermedia"] thresholds,
    majority_min_pct=20.0, minority_min_pct=10.0, min_coproducer_
    countries=2, are untouched)."""
    members = [c for c in co_producer_countries if te.is_ibermedia_member(c)]
    if len(members) < 2:
        return None

    if country_pcts is None:
        return CoproOpportunity(
            treaty_type="ibermedia",
            treaty_slug="ibermedia-multilateral",
            parties=tuple(c.upper() for c in members),
            resolution_state=RESOLUTION_UNRESOLVED_FACTS,
            cultural_test_required=True,
            cultural_test_resolved=False,
            notes=(
                f"{members} are all Ibermedia members, but no project fact "
                "states each party's real budget share — eligibility cannot "
                "be resolved from membership alone.",
            ),
        )

    result = te.evaluate_ibermedia_eligibility(members, country_pcts)
    cultural_resolved = cultural_test_passed is not None
    cultural_gate_ok = cultural_test_passed is True
    is_eligible = result.is_eligible and cultural_gate_ok

    reasons = list(result.disqualification_reasons)
    if cultural_test_passed is not True and result.is_eligible:
        reasons.append(
            "Ibermedia requires a cultural test (Ibero-American cultural "
            "identity); "
            + ("explicitly failed." if cultural_test_passed is False else "never assessed.")
        )

    return CoproOpportunity(
        treaty_type="ibermedia",
        treaty_slug="ibermedia-multilateral",
        parties=tuple(c.upper() for c in members),
        resolution_state=(
            RESOLUTION_ELIGIBLE if is_eligible
            else (RESOLUTION_INELIGIBLE if cultural_resolved or result.disqualification_reasons
                  else RESOLUTION_UNRESOLVED_FACTS)
        ),
        cultural_test_required=True,
        cultural_test_resolved=cultural_resolved,
        unlocked_slugs=tuple(result.unlocked_fund_slugs) if is_eligible else (),
        disqualification_reasons=tuple(reasons),
    )


def find_real_bilateral_partners(home_code: str, candidate_codes: list[str]) -> list[str]:
    """Every candidate code with a REAL registered bilateral treaty
    against home_code — registry presence only, never eligibility."""
    return [
        code for code in candidate_codes
        if te.get_bilateral_treaty(home_code, code) is not None
    ]


def find_eurimages_partners(home_code: str, candidate_codes: list[str]) -> list[str]:
    """Every candidate code that, together with home_code, would make a
    real (>=2 member) Eurimages co-production — membership only, never
    eligibility."""
    if not te.is_eurimages_member(home_code):
        return []
    return [code for code in candidate_codes if te.is_eurimages_member(code)]


def find_european_convention_partners(home_code: str, candidate_codes: list[str]) -> list[str]:
    """CBA-006 -- every candidate code that, together with home_code,
    would make a real (>=2 signatory) European Convention co-production —
    signatory status only, never eligibility."""
    if not te.is_european_convention_signatory(home_code):
        return []
    return [code for code in candidate_codes if te.is_european_convention_signatory(code)]


def find_ibermedia_partners(home_code: str, candidate_codes: list[str]) -> list[str]:
    """CBA-006 -- every candidate code that, together with home_code,
    would make a real (>=2 member) Ibermedia co-production — membership
    only, never eligibility."""
    if not te.is_ibermedia_member(home_code):
        return []
    return [code for code in candidate_codes if te.is_ibermedia_member(code)]
