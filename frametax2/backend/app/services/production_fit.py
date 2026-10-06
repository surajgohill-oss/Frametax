"""PRODUCTION-FIT RANKING (2026-10-01).

Production FEASIBILITY (does this jurisdiction suit the production's real
script / physical-location requirements?) is permanently separate from legal /
economic ELIGIBILITY. This module is the ONE serving-time owner that turns the
canonical capability vocabulary into a served fit for each executable scenario:

  * per-jurisdiction fit reuses the existing canonical classifier
    (``canonical_evaluation._feasibility_status`` over
    ``jurisdiction_capability_profile`` / ``match_capability``) -- no second
    feasibility engine; the only additions are (a) an EMPTY requirement set
    yields UNKNOWN rather than a manufactured fit claim and (b) the legs that
    are assessed are the PHYSICAL-PRODUCTION legs of the structure;
  * service-only routing (post / VFX / music / animation bundles) never creates
    a filming-location penalty;
  * a scenario's fit is the worst of its physical legs
    (WEAK < UNKNOWN < WORKABLE < STRONG).

Nothing here changes NPC, QPE, incentive, qualification, authority or the
$100,000 materiality rule, and nothing deletes a scenario: fit only decides
Leading/Strong eligibility, label and presentation priority. The canonical
financial ``rank`` stays untouched and auditable; ``fit_priority`` /
``fit_aware_rank`` are separate served fields.
"""
from __future__ import annotations

from types import SimpleNamespace

FIT_STRONG = "STRONG"
FIT_WORKABLE = "WORKABLE"
FIT_WEAK = "WEAK"
FIT_UNKNOWN = "UNKNOWN"

#: Fit statuses that may qualify for Leading/Strong alternative status.
FIT_CONFIRMED_STATUSES = frozenset({FIT_STRONG, FIT_WORKABLE})

BASIS_ON_FILE = "REQUIREMENTS_ON_FILE"
BASIS_NONE = "NO_REQUIREMENTS_ON_FILE"

# Fit-aware presentation priority (lower = earlier).
PRIORITY_RECOMMENDED = 1     # qualified, materially useful, fit-confirmed
PRIORITY_CONFIRMED_REFERENCE = 2   # other fit-confirmed references
PRIORITY_UNCONFIRMED = 3     # fit unconfirmed
PRIORITY_WEAK = 4            # weak-fit references
PRIORITY_UNAVAILABLE = 5     # legally / program unavailable outcomes

CAT_FIT_CONFIRMED = "FIT_CONFIRMED"
CAT_FIT_UNCONFIRMED = "FIT_UNCONFIRMED"
CAT_LOW_FIT_REFERENCE = "LOW_FIT_REFERENCE"
CAT_UNAVAILABLE = "UNAVAILABLE"

_FIT_SEVERITY = {FIT_WEAK: 0, FIT_UNKNOWN: 1, FIT_WORKABLE: 2, FIT_STRONG: 3}

# Components whose work is routed for service reasons and is NOT where the
# camera rolls. Reuses the canonical allocation vocabulary (MOVABLE_COMPONENTS,
# COMPONENT_BUNDLE_MEMBERS) plus animation, which the product names explicitly.
def _service_only_components() -> frozenset[str]:
    from app.calculators.production_allocation import COMPONENT_BUNDLE_MEMBERS, MOVABLE_COMPONENTS

    return frozenset(MOVABLE_COMPONENTS) | frozenset(COMPONENT_BUNDLE_MEMBERS) | frozenset({"animation"})


def requirements_disclosed(requirements) -> bool:
    """True when the production has any derived environment / hard capability.
    `post_production` infrastructure is always present and is not a location
    requirement, so it is deliberately not counted."""
    return bool(requirements.environments or requirements.required_capabilities)


#: Hard capabilities the jurisdiction capability profiles can actually AFFIRM or deny
#: (jurisdiction_capability_profile's `provisions` vocabulary). A hard requirement outside this
#: set (desert / snow / underwater, which no profile records for any jurisdiction) is not
#: assessable: counting it as "unsupported" would brand every jurisdiction WEAK from a gap in
#: the capability model, so it can only leave the fit UNCONFIRMED.
_ASSESSABLE_HARD_CAPABILITIES = frozenset({"marine_filming", "open_water_filming", "water_tanks"})


def classify_jurisdiction_fit(code: str, requirements) -> tuple[str, list[str]]:
    """Fit of ONE physical-production jurisdiction -- the HARD-requirement doctrine.

    Only the HARD physical requirements (production_requirements._HARD_REQUIREMENT_CAPABILITIES: marine / open-water /
    underwater filming, water tanks, desert, snow -- each present only when the script or the producer explicitly requires
    it) can decide the fit:
      * a hard requirement the structured capability data DENIES (landlocked vs marine / open water) -> WEAK, served as
        "not suitable for this production";
      * a hard requirement no profile can affirm or deny (desert / snow / underwater) -> UNKNOWN, `<TOKEN>_NOT_ASSESSABLE`
        (fit unconfirmed, never unsuitable);
      * otherwise the canonical classifier's STRONG / WORKABLE.
    SOFT suitability signals (beach/coast, island, jungle, mountains, urban, small town, rural, forest, historic, studio)
    never reach this decision: a missing soft datum is neutral and a confirmed soft mismatch is disclosed, never blocking
    (see `classify_soft_signals`). A missing datum is never a mismatch."""
    import dataclasses

    from app.calculators.production_requirements import jurisdiction_capability_profile, match_capability
    from app.services.canonical_evaluation import _feasibility_status

    cap = jurisdiction_capability_profile(code)
    if cap.has_capability_data and not requirements_disclosed(requirements):
        # An empty requirement set must not manufacture a fit claim.
        return FIT_UNKNOWN, ["NO_REQUIREMENTS_ON_FILE"]
    # A hard capability is assessable for THIS jurisdiction when the capability model can affirm or deny it: the marine / water
    # set always, and a location-census hard token (desert / snow) whenever the jurisdiction has a SUPPORTED (in provisions) or
    # NOT_SUPPORTED cell for it. UNKNOWN stays unassessed: Conditional, never a mismatch.
    assessable_here = _ASSESSABLE_HARD_CAPABILITIES | {
        t for t in requirements.required_capabilities if t in cap.provisions or t in cap.location_not_supported
    }
    unassessed = sorted(requirements.required_capabilities - assessable_here)
    assessable = dataclasses.replace(
        requirements, required_capabilities=requirements.required_capabilities & assessable_here,
    )
    match = match_capability(assessable, cap)
    exam = SimpleNamespace(
        jurisdiction_code=code, has_capability_data=cap.has_capability_data,
        production_capable=match.production_capable,
    )
    status, reasons = _feasibility_status(exam, assessable)
    denied = sorted(t for t in assessable.required_capabilities if t in cap.location_not_supported)
    if status == FIT_WEAK and denied:
        reasons = list(dict.fromkeys([*(f"{t.upper()}_NOT_SUPPORTED" for t in denied), *(r for r in reasons if r != "CAPABILITY_MISMATCH")]))
    if status in FIT_CONFIRMED_STATUSES and unassessed:
        # Nothing assessable contradicts the production, but a HARD requirement cannot be
        # confirmed from the capability data: unconfirmed, never a manufactured fit claim.
        return FIT_UNKNOWN, [f"{t.upper()}_NOT_ASSESSABLE" for t in unassessed]
    if status == FIT_UNKNOWN and not reasons:
        reasons = ["CAPABILITY_UNKNOWN"]
    if status == FIT_STRONG and classify_soft_signals(code, requirements)["mismatched"]:
        status = FIT_WORKABLE       # a confirmed soft mismatch may lower suitability; it never makes a fit Weak
    return status, list(reasons)


def classify_soft_signals(code: str, requirements) -> dict[str, list[str]]:
    """SOFT suitability signals of ONE jurisdiction: the active location requirements that are NOT hard physical needs,
    each assessed against the structured capability data (production_requirements.assess_location_capability):
    `matched` (confirmed support), `mismatched` (confirmed denial, e.g. a landlocked jurisdiction vs beach/coast) and
    `unassessed` (no structured data: neutral, disclosed, non-blocking). Disclosure only -- never a gate."""
    from app.calculators.production_requirements import (
        ASSESS_MATCH, ASSESS_MISMATCH, LOCATION_CAPABILITY_TOKENS, _HARD_REQUIREMENT_CAPABILITIES,
        assess_location_capability, jurisdiction_capability_profile,
    )

    cap = jurisdiction_capability_profile(code)
    out: dict[str, list[str]] = {"matched": [], "mismatched": [], "unassessed": []}
    if not cap.has_capability_data:
        return out
    soft = sorted((requirements.environments & LOCATION_CAPABILITY_TOKENS) - _HARD_REQUIREMENT_CAPABILITIES
                  - requirements.required_capabilities)
    for token in soft:
        verdict, _ = assess_location_capability(token, cap)
        out["matched" if verdict == ASSESS_MATCH else "mismatched" if verdict == ASSESS_MISMATCH else "unassessed"].append(token)
    return out


def classify_capability_evidence(code: str, requirements) -> list[dict]:
    """Retained location-census evidence behind this jurisdiction's SUPPORTED / NOT_SUPPORTED cells for the ACTIVE location
    requirements (hard and soft alike), served beside the fit so every surface can show the same provenance. UNKNOWN cells
    carry no evidence and are not listed."""
    from app.calculators.production_requirements import LOCATION_CENSUS_TOKENS, jurisdiction_capability_profile

    cap = jurisdiction_capability_profile(code)
    active = (requirements.environments | requirements.required_capabilities) & LOCATION_CENSUS_TOKENS
    return [
        {"jurisdiction": code, "category": c.category, "token": c.token, "status": c.status, "terminal_status": c.terminal_status,
         "hard_requirement": c.token in requirements.required_capabilities, "proposition": c.proposition,
         "source_title": c.source_title, "source_labels": list(c.source_labels), "source_url": c.source_url, "publisher": c.publisher,
         "source_version": c.source_version, "evidence_tier": c.evidence_tier, "derivation_method": c.derivation_method}
        for c in cap.location_evidence if c.token in active
    ]


def physical_production_legs(entry: dict) -> list[str]:
    """The jurisdictions that physically host production in this structure.

    * component / hybrid routing: the legs whose routed component is NOT
      service-only (e.g. ``principal_production``). Service-only legs (post,
      VFX, music, animation) are ignored. When principal production is routed,
      the anchor no longer hosts the shoot, so only the routed physical legs
      count; when nothing physical is routed, the anchor hosts the shoot.
    * everything else: the jurisdictions that carry allocated spend in the
      structure's own segments, falling back to participants / primary.
    """
    service_only = _service_only_components()
    anchor = entry.get("anchor_jurisdiction") or entry.get("primary_jurisdiction")
    allocations = entry.get("component_allocations") or []
    if allocations:
        routed_physical = [
            a.get("jurisdiction_code") for a in allocations
            if a.get("jurisdiction_code") and a.get("component") not in service_only
        ]
        legs = routed_physical or ([anchor] if anchor else [])
    else:
        legs = [
            s.get("jurisdiction_code") for s in (entry.get("segments") or [])
            if s.get("jurisdiction_code") and (s.get("allocated_usd") or 0) > 0
        ] or list(entry.get("participants") or []) or ([anchor] if anchor else [])
    return list(dict.fromkeys(c for c in legs if c))


def classify_entry_fit(entry: dict, requirements, cache: dict | None = None) -> dict:
    """Served production-fit fields for one scenario / structure entry."""
    cache = cache if cache is not None else {}
    legs = physical_production_legs(entry)
    basis = BASIS_ON_FILE if requirements_disclosed(requirements) else BASIS_NONE
    if not legs:
        return {
            "production_fit_status": FIT_UNKNOWN, "production_fit_reasons": ["NO_PHYSICAL_PRODUCTION_LEG"],
            "production_fit_legs": [], "production_fit_leg_status": {}, "production_fit_basis": basis,
            "production_fit_soft_signals": {"matched": [], "mismatched": [], "unassessed": []},
            "production_fit_capability_evidence": [],
        }
    per_leg: dict[str, str] = {}
    reasons: list[str] = []
    soft: dict[str, list[str]] = {"matched": [], "mismatched": [], "unassessed": []}
    evidence: list[dict] = []
    for code in legs:
        if code not in cache:
            cache[code] = classify_jurisdiction_fit(code, requirements)
        if ("soft", code) not in cache:
            cache[("soft", code)] = classify_soft_signals(code, requirements)
        if ("evidence", code) not in cache:
            cache[("evidence", code)] = classify_capability_evidence(code, requirements)
        evidence.extend(cache[("evidence", code)])
        for kind, tokens in cache[("soft", code)].items():
            soft[kind].extend(f"{code}:{t}" for t in tokens)
        status, leg_reasons = cache[code]
        per_leg[code] = status
        reasons.extend(f"{code}:{r}" for r in leg_reasons)
    worst = min(per_leg.values(), key=lambda s: _FIT_SEVERITY[s])
    return {
        "production_fit_status": worst,
        "production_fit_reasons": list(dict.fromkeys(reasons)),
        "production_fit_legs": legs,
        "production_fit_leg_status": per_leg,
        "production_fit_basis": basis,
        "production_fit_soft_signals": soft,
        "production_fit_capability_evidence": evidence,
    }


def fit_confirmed(entry: dict) -> bool:
    return entry.get("production_fit_status") in FIT_CONFIRMED_STATUSES


def fit_priority(entry: dict) -> int:
    """Presentation priority from served fields only. Legal/program
    unavailability always ranks last; priced scenarios rank by fit, with
    Leading/Strong (RECOMMENDED after the fit gate) first."""
    if not entry.get("is_fully_priced"):
        return PRIORITY_UNAVAILABLE
    status = entry.get("production_fit_status")
    if status == FIT_WEAK:
        return PRIORITY_WEAK
    if status not in FIT_CONFIRMED_STATUSES:
        return PRIORITY_UNCONFIRMED
    if entry.get("recommendation_status") == "RECOMMENDED":
        return PRIORITY_RECOMMENDED
    return PRIORITY_CONFIRMED_REFERENCE


def fit_aware_category(entry: dict) -> str:
    if not entry.get("is_fully_priced"):
        return CAT_UNAVAILABLE
    status = entry.get("production_fit_status")
    if status == FIT_WEAK:
        return CAT_LOW_FIT_REFERENCE
    if status not in FIT_CONFIRMED_STATUSES:
        return CAT_FIT_UNCONFIRMED
    return CAT_FIT_CONFIRMED


def fit_summary(entries: list[dict], unavailable_total: int) -> dict:
    """Exact counts for disclosure copy. `scenario_total` equals the served
    universe size: fit never removes a scenario."""
    priced = [e for e in entries if e.get("is_fully_priced")]
    return {
        "fit_confirmed": sum(1 for e in priced if fit_aware_category(e) == CAT_FIT_CONFIRMED),
        "fit_confirmed_leading_or_strong": sum(1 for e in priced if fit_priority(e) == PRIORITY_RECOMMENDED),
        "fit_confirmed_reference": sum(1 for e in priced if fit_priority(e) == PRIORITY_CONFIRMED_REFERENCE),
        "fit_unconfirmed": sum(1 for e in priced if fit_aware_category(e) == CAT_FIT_UNCONFIRMED),
        "weak_fit": sum(1 for e in priced if fit_aware_category(e) == CAT_LOW_FIT_REFERENCE),
        "unavailable": int(unavailable_total),
        "scenario_total": len(entries),
    }


def fit_actionability(entry: dict) -> dict:
    """Globe/producer ACTIONABILITY of a priced scenario (one served definition, 2026-10-01):
      GREEN  -- canonical RECOMMENDED (cost-saving, material, fit-confirmed);
      AMBER  -- executable but conditional on MISSING LOCATION-CAPABILITY DATA: a hard physical
                requirement (desert / snow / underwater ...) no capability profile can affirm or deny.
                Missing capability records are never a hard blocker and never RED;
      SLATE  -- every other valid executable alternative (reference, immaterial, neutral, weak-fit,
                more expensive, or fit-unconfirmed only because no requirements are on file)."""
    if entry.get("recommendation_status") == "RECOMMENDED":
        return {"actionability": "GREEN", "actionability_reason": None}
    reasons = entry.get("production_fit_reasons") or []
    missing = [r for r in reasons if isinstance(r, str) and r.endswith("_NOT_ASSESSABLE")]
    if missing and entry.get("production_fit_status") != FIT_WEAK:
        return {"actionability": "AMBER", "actionability_reason": "MISSING_LOCATION_CAPABILITY_DATA: " + ", ".join(sorted(set(missing)))}
    return {"actionability": "SLATE", "actionability_reason": None}
