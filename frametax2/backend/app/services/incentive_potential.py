"""MAXIMUM-POTENTIAL INCENTIVE CONTRACT (2026-10-01) -- the single served definition of
confirmed vs. maximum-supportable incentive economics for one structure.

Canonical owner of: confirmed_incentive_floor_usd, maximum_supported_incentive_usd,
confirmed_npc_usd, potential_npc_usd, ceiling_status, ceiling_missing_facts,
ceiling_basis, economics_certainty, and the two rank fields.

This module is NOT a second calculator. Every dollar it serves is read from values the
pricing kernel (allocation_pricing.price_segment) already computed and the evaluator
already persisted per segment / per hybrid component: incentive_floor_usd,
incentive_ceiling_usd, ceiling_requires_confirmation and the unmet rate-tier conditions
(ceiling_conditions). It only (a) selects which of those the project's currently
established facts support, (b) sums them without double counting, and (c) names the
exact conditions still missing. It is a serving-time reader: it deliberately lives
outside canonical_runtime_attribution._SEMANTIC_PRICING_MODULES.

Binding behaviour
-----------------
* The confirmed floor is ``selected_incentive_usd`` -- the incentive the evaluator already
  prices into NPC (per segment: the floor tier while the ceiling needs confirmation,
  otherwise the ceiling). Missing facts can therefore never enter it.
* The maximum is the confirmed floor plus, for each conditional leg, the evaluator's own
  ceiling-tier uplift (ceiling - confirmed). It is never greater-than-or-equal-by-invention:
  a leg with no persisted ceiling contributes no upside, and a structure whose legs cannot
  be reconciled to its selected incentive is NOT_ESTABLISHED (no maximum is served).
* Shared QPE / stacking: the sum is taken over the persisted legs only. Stack legs already
  carry de-duplicated per-program adjusted values (floor == ceiling), so nothing is
  double counted; component legs are disjoint by construction.
* Potential NPC = confirmed NPC - upside. Non-incentive adjustments are rate-independent
  (the same identity canonical_production_view already uses for npc_ceiling_usd).
* Potential never replaces confirmed values or any recommendation status; it is served
  alongside, and ordered by its own rank.
"""
from __future__ import annotations

from typing import Any

CEILING_CONFIRMED = "CONFIRMED"          # maximum == confirmed floor; nothing conditional
CEILING_CONDITIONAL = "CONDITIONAL"      # maximum > confirmed floor; facts/authority missing
CEILING_NOT_ESTABLISHED = "NOT_ESTABLISHED"  # canonical data does not establish a maximum

CERTAINTY_CONFIRMED = "CONFIRMED"
CERTAINTY_CONDITIONAL = "CONDITIONAL"
CERTAINTY_REFERENCE_ONLY = "REFERENCE_ONLY"

#: Reconciliation tolerance (USD) between the leg sum and selected_incentive_usd.
_RECONCILE_TOLERANCE_USD = 1.0

# Actionability order for missing facts: things the producer can supply first.
_STATE_ORDER = {
    "USER_FACT_REQUIRED": 0,
    "SCRIPT_FACT_REQUIRED": 1,
    "AUTHORITY_UNRESOLVED": 2,
    "EXECUTABLE": 3,
    "DISCLOSURE_ONLY": 4,
}


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _missing_facts_for_leg(leg: dict) -> list[dict]:
    conditions = [c for c in (leg.get("ceiling_conditions") or []) if isinstance(c, dict)]
    actionable = [c for c in conditions if c.get("condition_state") != "DISCLOSURE_ONLY"]
    chosen = actionable or conditions
    facts = [
        {
            "fact_id": c.get("condition_id"),
            "description": c.get("description"),
            "state": c.get("condition_state"),
            "note": c.get("note"),
            "program_slug": leg["program_slug"],
            "jurisdiction_code": leg["jurisdiction_code"],
            "unlocks_incentive_usd": leg["upside_usd"],
        }
        for c in chosen
    ]
    facts.sort(key=lambda f: _STATE_ORDER.get(f["state"], 9))
    if not facts:
        # A conditional leg whose unmet conditions were not persisted (a generation that
        # predates ceiling_conditions). Disclosed generically -- never an invented fact.
        facts.append({
            "fact_id": "CEILING_TIER_NOT_CONFIRMED",
            "description": (
                "The program's maximum tier is not confirmed for this production; the "
                "specific unmet condition was not retained in this evaluation generation."
            ),
            "state": "AUTHORITY_UNRESOLVED",
            "note": None,
            "program_slug": leg["program_slug"],
            "jurisdiction_code": leg["jurisdiction_code"],
            "unlocks_incentive_usd": leg["upside_usd"],
        })
    return facts


def _legs_from_trace(trace: dict) -> tuple[str, list[dict]] | None:
    """Return (method, legs) from the persisted trace, or None if it carries no
    per-leg floor/ceiling data. Each leg: confirmed_usd, maximum_usd (>= confirmed)."""
    segments = trace.get("segments") or []
    legs: list[dict] = []
    if segments:
        for seg in segments:
            floor = _num(seg.get("incentive_floor_usd"))
            ceiling = _num(seg.get("incentive_ceiling_usd"))
            if floor is None and ceiling is None:
                continue
            floor = floor if floor is not None else 0.0
            ceiling = ceiling if ceiling is not None else floor
            conditional = bool(seg.get("ceiling_requires_confirmation"))
            confirmed = floor if conditional else ceiling
            maximum = max(ceiling, confirmed)
            legs.append({
                "jurisdiction_code": seg.get("jurisdiction_code"),
                "program_slug": seg.get("program_slug"),
                "confirmed_usd": round(confirmed, 2),
                "maximum_usd": round(maximum, 2),
                "rate_confirmed": seg.get("rate_floor") if conditional else seg.get("rate_ceiling"),
                "rate_maximum": seg.get("rate_ceiling"),
                "conditional": conditional,
                "ceiling_conditions": seg.get("ceiling_conditions") or [],
            })
        return ("SEGMENT_TIERS", legs) if legs else None
    components = trace.get("component_allocations") or []
    for comp in components:
        guaranteed = _num(comp.get("guaranteed_incentive_usd"))
        if guaranteed is None:
            continue
        ceiling = _num(comp.get("incentive_ceiling_usd"))
        if ceiling is None:
            # A component that persisted no ceiling (a generation that predates the contract)
            # cannot support ANY maximum for the structure -- never assume "no upside".
            return None
        maximum = max(ceiling, guaranteed)
        legs.append({
            "jurisdiction_code": comp.get("jurisdiction_code"),
            "program_slug": comp.get("program_slug"),
            "confirmed_usd": round(guaranteed, 2),
            "maximum_usd": round(maximum, 2),
            "rate_confirmed": None,
            "rate_maximum": None,
            "conditional": maximum - guaranteed > _RECONCILE_TOLERANCE_USD / 100.0,
            "ceiling_conditions": comp.get("ceiling_conditions") or [],
            "component": comp.get("component"),
        })
    return ("COMPONENT_SEGMENT_TIERS", legs) if legs else None


def build_incentive_potential(
    trace: dict,
    *,
    is_priced: bool,
    selected_incentive_usd: float | None,
    npc_with_adjustments_usd: float | None,
    legal_review_required: bool = False,
    administrative_allocation_risk: bool = False,
) -> dict:
    """The one served definition. Pure function of already-persisted/served values."""
    confirmed_npc = (
        round(float(npc_with_adjustments_usd), 2) if npc_with_adjustments_usd is not None else None
    )
    confirmed_floor = (
        round(float(selected_incentive_usd), 2) if selected_incentive_usd is not None else None
    )
    base = {
        "confirmed_incentive_floor_usd": confirmed_floor,
        "maximum_supported_incentive_usd": None,
        "potential_upside_usd": None,
        "confirmed_npc_usd": confirmed_npc,
        "potential_npc_usd": None,
        "ceiling_status": CEILING_NOT_ESTABLISHED,
        "ceiling_missing_facts": [],
        "ceiling_basis": {"method": "NONE", "legs": [], "note": None},
        "economics_certainty": CERTAINTY_REFERENCE_ONLY,
    }
    if not is_priced or confirmed_floor is None or confirmed_npc is None:
        base["ceiling_basis"]["note"] = "Structure is not fully priced; no confirmed or maximum economics are served."
        return base

    extracted = _legs_from_trace(trace)
    if extracted is None:
        base["ceiling_basis"]["note"] = (
            "No per-segment/component floor and ceiling were persisted for this structure; "
            "no maximum is established."
        )
        base["economics_certainty"] = (
            CERTAINTY_CONDITIONAL if (legal_review_required or administrative_allocation_risk)
            else CERTAINTY_CONFIRMED
        )
        return base
    method, legs = extracted

    legs_confirmed = round(sum(l["confirmed_usd"] for l in legs), 2)
    legs_upside = round(sum(max(0.0, l["maximum_usd"] - l["confirmed_usd"]) for l in legs), 2)
    reconciles = abs(legs_confirmed - confirmed_floor) <= _RECONCILE_TOLERANCE_USD
    if not reconciles and legs_upside > 0.0:
        # The legs do not reconstruct the incentive the evaluator priced into NPC (a
        # structure-level adjustment, e.g. a federal/provincial stacking reduction, sits on top
        # of them) AND at least one leg has conditional upside whose effect on that adjustment
        # is not persisted. Fail closed: serve the confirmed values, establish no maximum.
        base["ceiling_basis"] = {
            "method": method,
            "legs": [],
            "note": (
                f"Leg incentives (${legs_confirmed:,.2f}) do not reconcile to the selected "
                f"incentive (${confirmed_floor:,.2f}) and a leg carries conditional upside; "
                "no maximum is established."
            ),
        }
        base["economics_certainty"] = (
            CERTAINTY_CONDITIONAL if (legal_review_required or administrative_allocation_risk)
            else CERTAINTY_CONFIRMED
        )
        return base
    # A structure-level adjustment with NO conditional leg cannot move the maximum: with every
    # leg already at its ceiling, the priced incentive IS the maximum.

    upside = 0.0
    missing: list[dict] = []
    basis_legs: list[dict] = []
    for leg in legs:
        leg_upside = round(max(0.0, leg["maximum_usd"] - leg["confirmed_usd"]), 2)
        leg["upside_usd"] = leg_upside
        if leg_upside > 0.0:
            upside += leg_upside
            missing.extend(_missing_facts_for_leg(leg))
        basis_legs.append({
            "jurisdiction_code": leg["jurisdiction_code"],
            "program_slug": leg["program_slug"],
            "component": leg.get("component"),
            "confirmed_usd": leg["confirmed_usd"],
            "maximum_usd": leg["maximum_usd"],
            "rate_confirmed": leg.get("rate_confirmed"),
            "rate_maximum": leg.get("rate_maximum"),
            "conditional": leg_upside > 0.0,
        })
    upside = round(upside, 2)
    conditional = upside > 0.0
    maximum = round(confirmed_floor + upside, 2)
    base.update({
        "maximum_supported_incentive_usd": maximum,
        "potential_upside_usd": upside,
        "potential_npc_usd": round(confirmed_npc - upside, 2),
        "ceiling_status": CEILING_CONDITIONAL if conditional else CEILING_CONFIRMED,
        "ceiling_missing_facts": missing,
        "ceiling_basis": {
            "method": method,
            "legs": basis_legs,
            "note": (
                "Maximum = confirmed floor + each conditional leg's evaluator ceiling-tier uplift; "
                "potential NPC = confirmed NPC - upside (adjustments are rate-independent)."
            ),
        },
        "economics_certainty": (
            CERTAINTY_CONDITIONAL
            if (conditional or legal_review_required or administrative_allocation_risk)
            else CERTAINTY_CONFIRMED
        ),
    })
    return base


def assign_incentive_potential_ranks(scenarios: list[dict]) -> None:
    """Two separate, independent orderings over the SAME never-filtered scenario list.

    confirmed_financial_rank: ascending confirmed NPC -- what is financially established.
    potential_opportunity_rank: ascending potential NPC -- the producer-visible upside.
    Neither mutates ordering, status, or any other field; both are None for a scenario
    with no value on that axis. Ties break by economic identity then structure id so the
    rank is deterministic."""
    def _key(field: str):
        def inner(e: dict):
            return (e[field], str(e.get("economic_identity") or ""), str(e.get("structure_id") or ""))
        return inner

    confirmed = sorted((e for e in scenarios if e.get("confirmed_npc_usd") is not None), key=_key("confirmed_npc_usd"))
    for i, e in enumerate(confirmed, start=1):
        e["confirmed_financial_rank"] = i
    potential = sorted((e for e in scenarios if e.get("potential_npc_usd") is not None), key=_key("potential_npc_usd"))
    for i, e in enumerate(potential, start=1):
        e["potential_opportunity_rank"] = i
    for e in scenarios:
        e.setdefault("confirmed_financial_rank", None)
        e.setdefault("potential_opportunity_rank", None)
