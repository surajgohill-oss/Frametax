"""
Recommendation-confidence status (Final Backend Closeout — Phase 2).

A single, deterministic, producer-facing status per scenario that reflects
HOW CERTAIN the recommendation is — never allowing a structure to read as a
clean "recommended" purely because it has the lowest Net Production Cost when
mandatory qualification information is missing.

This module ADDS NO ECONOMICS. It never changes a structure's price, its NPC,
or its rank. It is a pure classification over signals the pricing/qualification
engines already produce:

  - is_fully_priced          (allocation_pricing: a defensible price exists)
  - gated                    (allocation_pricing.build_structure_recommendation:
                              blockers OR unresolved routing/relocation reqs)
  - each incentive-claiming program's ProductionRequirementsProfile
                             (program_requirements.py — verbatim, never guessed)

GROUNDING (Phase 1 reconciliation, verified this closeout by reading
program_rate_rules.resolve_program_rate's tier-selection loop and grepping the
served path): the ONLY qualification gate any engine machine-enforces is
`min_qpe_usd` (minimum spend). Cultural tests, preapproval, local-entity,
timing, filing, transfer restrictions are DISCLOSED-ONLY where a profile states
them and NOT IMPLEMENTED where it does not. Therefore the engine can never, on
its own, assert that a production PASSES a cultural test / preapproval / local-
entity gate. When a profile states such a gate is mandatory, the honest status
is CONDITIONAL (priced, but adoption is conditional on clearing a mandatory
statutory gate the engine cannot confirm). When no profile states the gates at
all, the honest status is PRICED (priced, but qualification is not fully known)
— never CONFIRMED, which is reserved for the case where every applicable hard
gate is positively known not to block.

Status taxonomy (spec Phase 2), first match wins:

  UNAVAILABLE  - not fully priced: no defensible price exists (rate did not
                 resolve, a real minimum-spend floor failed, or no active
                 applicable program). The structure cannot currently be adopted
                 as a priced option.
  CONDITIONAL  - fully priced, but at least one participating incentive program
                 asserts a MANDATORY hard eligibility gate (cultural test,
                 preapproval, local entity, or official-coproduction) that this
                 engine cannot confirm is satisfied.
  PRICED_BUT_QUALIFICATION_PENDING
               - fully priced, no known-mandatory statutory gate, but the
                 structure is gated on outstanding routing/relocation
                 confirmations or authority approval (recommendation.gated).
  CONFIRMED    - fully priced, not gated, and EVERY participating incentive
                 program has a populated requirements profile that positively
                 states none of its hard gates block (all hard-gate fields
                 explicitly False, not merely unstated).
  PRICED       - fully priced, not gated, but at least one participating program
                 has no profile or leaves a hard-gate field unstated: priced,
                 qualification not fully known.
  UNKNOWN      - could not be classified (defensive; should not occur for a
                 structure that carries the fields above).
"""
from __future__ import annotations

import enum

from app.data.program_requirements import get_program_requirements


class ConfidenceStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CONDITIONAL = "CONDITIONAL"
    PRICED = "PRICED"
    PRICED_QUALIFICATION_PENDING = "PRICED_BUT_QUALIFICATION_PENDING"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


# Requirements-profile boolean fields that, when True, mean "a mandatory
# statutory eligibility gate applies that no engine in the served path can
# confirm is satisfied" (see module docstring / Phase 1 reconciliation).
HARD_GATE_FIELDS: tuple[str, ...] = (
    "cultural_test_required",
    "preapproval_mandatory",
    "local_entity_required",
    "treaty_or_official_coproduction_required",
)

_GATE_LABEL = {
    "cultural_test_required": "cultural test",
    "preapproval_mandatory": "pre-approval",
    "local_entity_required": "local production entity",
    "treaty_or_official_coproduction_required": "official co-production status",
}


def derive_confidence_status(
    *,
    is_fully_priced: bool,
    gated: bool,
    incentive_program_slugs: tuple[str, ...],
) -> tuple[ConfidenceStatus, list[str]]:
    """Classify one structure. `incentive_program_slugs` is the set of
    program slugs whose segments actually claim the incentive (the priced
    programs), deduped. Pure and deterministic: same inputs -> same output,
    no I/O beyond the in-memory requirements registry."""
    reasons: list[str] = []

    if not is_fully_priced:
        return ConfidenceStatus.UNAVAILABLE, [
            "No defensible price: the incentive rate did not resolve, a real "
            "minimum-spend floor was not met, or no active applicable program "
            "exists. Not adoptable as a priced option until the blocker clears."
        ]

    slugs = tuple(dict.fromkeys(s for s in incentive_program_slugs if s))

    asserted_gates: list[str] = []
    has_silent_or_missing_profile = False
    every_program_positively_clear = bool(slugs)

    for slug in slugs:
        profile = get_program_requirements(slug)
        if profile is None:
            has_silent_or_missing_profile = True
            every_program_positively_clear = False
            continue
        for field in HARD_GATE_FIELDS:
            value = getattr(profile, field, None)
            if value is True:
                asserted_gates.append(_GATE_LABEL[field])
            elif value is None:
                # Unstated: we do not positively know this gate does not block.
                every_program_positively_clear = False

    if asserted_gates:
        uniq = list(dict.fromkeys(asserted_gates))
        reasons.append(
            "Adoption is conditional on clearing a mandatory statutory gate the "
            "engine cannot confirm is satisfied: " + ", ".join(uniq) + "."
        )
        return ConfidenceStatus.CONDITIONAL, reasons

    if gated:
        reasons.append(
            "Priced, but gated on outstanding routing/relocation confirmations "
            "or authority approval before it can be adopted."
        )
        return ConfidenceStatus.PRICED_QUALIFICATION_PENDING, reasons

    if every_program_positively_clear:
        reasons.append(
            "Fully priced and not gated; every participating program's known "
            "hard gates are positively confirmed not to block."
        )
        return ConfidenceStatus.CONFIRMED, reasons

    if slugs:
        reasons.append(
            "Fully priced and not gated, but qualification is not fully known: "
            "at least one participating program has no requirements profile or "
            "leaves a hard gate unstated."
        )
        return ConfidenceStatus.PRICED, reasons

    # A priced structure with no incentive-claiming program (e.g. a pure
    # baseline that qualifies zero incentive) — priced, nothing to qualify.
    reasons.append("Fully priced; no incentive program to qualify.")
    return ConfidenceStatus.PRICED, reasons


def confidence_status_for_structure(pricing) -> tuple[ConfidenceStatus, list[str]]:
    """Convenience wrapper over an AllocatedStructurePricing object."""
    slugs = tuple(
        s.program_slug for s in pricing.segments
        if getattr(s, "claims_incentive", False) and s.program_slug
    )
    gated = bool(pricing.recommendation.gated) if pricing.recommendation else bool(pricing.blockers)
    return derive_confidence_status(
        is_fully_priced=pricing.is_fully_priced,
        gated=gated,
        incentive_program_slugs=slugs,
    )
