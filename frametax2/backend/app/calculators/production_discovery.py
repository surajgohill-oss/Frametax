"""
production_discovery.py

Requirement-first GLOBAL DISCOVERY (Phase 6). Before any structure is
generated or priced, the optimizer examines EVERY jurisdiction implemented
in the CineGlobe database — not a hand-picked country list — and decides,
per jurisdiction and from data alone, whether the production can actually be
executed there.

The examined universe is the full incentive-program inventory
(`global_inventory.ALL_PROGRAMS`, ~211 distinct jurisdictions) unioned with
the structured jurisdiction profiles (`jurisdiction_comparison.ALL_PROFILES`).
No jurisdiction is enumerated by hand; no rate is invented for a jurisdiction
that lacks classified rules.

Executability is a two-gate, evidence-only test:
  1. KNOWLEDGE gate — the jurisdiction must have BOTH a classified
     qualification doctrine (`program_spend_rules.get_program_doctrine`) and
     statutory rate rules (`program_rate_rules.get_rate_rules`). Without both
     the production cannot be priced without guessing, so it is rejected.
  2. REQUIREMENT gate — the production's own facts (production type + total
     qualifying spend) must actually resolve a statutory rate for that
     program (`resolve_program_rate`). A jurisdiction that has the knowledge
     but whose statutory conditions the production does not meet (wrong
     production type, below minimum spend) is rejected with that reason.

Every jurisdiction — accepted or rejected — is returned with its reason and
what is known about it, plus aggregate discovery metrics, so the whole
decision is inspectable. Only the accepted set enters structure generation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JurisdictionExamination:
    jurisdiction_code: str
    jurisdiction_name: str
    # Production-first classification:
    #   "incentive_ready"     — production-capable AND priceable → optimized
    #   "capability_only"     — production-capable, incentive model pending
    #   "rejected"            — cannot make the production here, or no data
    classification: str
    accepted: bool           # True only for incentive_ready (enters optimization)
    production_capable: bool
    reason: str
    capability_reasons: tuple[str, ...]
    program_slug: str | None
    has_capability_data: bool
    has_doctrine: bool
    has_rate_rules: bool
    resolves_for_production: bool
    stated_base_rate: float | None
    requires_cultural_test: bool | None
    requires_local_entity: bool | None


@dataclass(frozen=True)
class DiscoveryResult:
    examinations: tuple[JurisdictionExamination, ...]
    accepted: tuple[tuple[str, str], ...]  # (jurisdiction_code, program_slug)
    metrics: dict

    def accepted_alternatives(self, home_code: str) -> list[tuple[str, str]]:
        """Accepted executable jurisdictions other than the production's home
        (baseline) jurisdiction — the relocation/component partner set."""
        return [(c, s) for c, s in self.accepted if c != home_code]


def discover_executable_jurisdictions(
    *,
    requirements,
    production_type: str,
    qpe_usd: float | None,
    home_code: str,
) -> DiscoveryResult:
    """Production-first discovery. Examine every implemented jurisdiction and,
    for each, first ask 'can this PRODUCTION be made here?' (capability match)
    and then 'can the incentive be priced?' (knowledge + statutory gate),
    classifying it as incentive_ready / capability_only / rejected. Only
    incentive_ready jurisdictions enter optimization; capability_only
    jurisdictions are retained (production-capable, incentive pending) rather
    than silently discarded. Pure function of the data + the production —
    iterates registries, never a hard-coded country list."""
    from app.calculators import jurisdiction_comparison as jc
    from app.calculators.production_requirements import (
        jurisdiction_capability_profile,
        match_capability,
    )
    from app.data import global_inventory as gi
    from app.data.program_rate_rules import get_rate_rules, resolve_program_rate
    from app.data.program_spend_rules import get_program_doctrine

    # Every implemented jurisdiction: distinct codes across the full program
    # inventory, unioned with the structured profiles (the latter is normally
    # a subset, but the union guarantees nothing modeled is missed).
    inventory_by_code: dict[str, object] = {}
    for p in gi.ALL_PROGRAMS:
        inventory_by_code.setdefault(p.jurisdiction_code, p)
    for code in jc.ALL_PROFILES:
        inventory_by_code.setdefault(code, None)

    examinations: list[JurisdictionExamination] = []
    accepted: list[tuple[str, str]] = []
    rejection_reason_counts: dict[str, int] = {}

    def _reject(bucket: str) -> None:
        rejection_reason_counts[bucket] = rejection_reason_counts.get(bucket, 0) + 1

    for code in sorted(inventory_by_code):
        profile = jc.ALL_PROFILES.get(code)
        inv = inventory_by_code[code]
        name = (
            getattr(inv, "jurisdiction_name", None)
            or (getattr(profile, "jurisdiction_name", None) if profile else None)
            or code
        )
        slug = profile.program_slug if profile is not None else None
        has_doctrine = slug is not None and get_program_doctrine(slug) is not None
        has_rate = slug is not None and len(get_rate_rules(slug)) > 0
        stated_rate = getattr(inv, "base_rate", None) if inv is not None else None
        req_cultural = getattr(inv, "requires_cultural_test", None) if inv is not None else None
        req_entity = getattr(inv, "requires_local_entity", None) if inv is not None else None

        # ── STAGE 1: can the PRODUCTION be made here? (capability, not tax) ──
        cap = jurisdiction_capability_profile(code)
        cm = match_capability(requirements, cap)
        cap_reasons = cm.reasons

        # ── STAGE 2: can the incentive be priced? (knowledge + statutory) ──
        resolves = False
        priceable = False
        if slug is not None and has_doctrine and has_rate:
            rr = resolve_program_rate(slug, production_type=production_type, qpe_usd=qpe_usd)
            resolves = rr is not None
            priceable = resolves

        # ── Classification (production-first) ──
        if cap.has_capability_data and not cm.production_capable:
            classification = "rejected"
            missing = ", ".join(cm.incompatible) or "a required environment"
            reason = (f"Not production-capable: the production requires {missing}, which "
                      f"this jurisdiction cannot provide. Rejected on capability, "
                      "independent of any incentive.")
            _reject("capability_mismatch")
            ok = False
            capable = False
        elif cm.production_capable and priceable:
            classification = "incentive_ready"
            reason = ("Production-capable AND incentive-ready: capabilities match the "
                      "production's requirements and a statutory incentive resolves — "
                      "enters optimization.")
            ok = True
            capable = True
            accepted.append((code, slug))
        elif cm.production_capable and not priceable:
            classification = "capability_only"
            why_pending = ("no statutory rate rules" if not has_rate else
                           "no classified qualification doctrine" if not has_doctrine else
                           "the production's statutory conditions are unmet")
            reason = ("Production-capable, incentive pending: the jurisdiction can "
                      f"physically support the production, but {why_pending}. Retained "
                      "for capability, not priced (never guessed).")
            _reject("capability_only_incentive_pending")
            ok = False
            capable = True
        else:
            # No capability data AND not priceable → nothing to act on.
            classification = "rejected"
            reason = ("No structured capability profile and no priceable incentive "
                      "model (catalog rate only, if any) — cannot assess production "
                      "fit or price; excluded rather than guessed.")
            _reject("no_capability_no_incentive")
            ok = False
            capable = False

        examinations.append(JurisdictionExamination(
            jurisdiction_code=code, jurisdiction_name=name, classification=classification,
            accepted=ok, production_capable=capable, reason=reason,
            capability_reasons=cap_reasons, program_slug=slug,
            has_capability_data=cap.has_capability_data, has_doctrine=has_doctrine,
            has_rate_rules=has_rate, resolves_for_production=resolves,
            stated_base_rate=stated_rate, requires_cultural_test=req_cultural,
            requires_local_entity=req_entity,
        ))

    n_capable = sum(1 for e in examinations if e.production_capable)
    n_capability_only = sum(1 for e in examinations if e.classification == "capability_only")
    metrics = {
        "jurisdictions_examined": len(examinations),
        "production_capable_count": n_capable,
        "incentive_ready_count": len(accepted),
        "capability_only_count": n_capability_only,
        "rejected_count": sum(1 for e in examinations if e.classification == "rejected"),
        "accepted_count": len(accepted),  # back-compat alias for incentive_ready
        "incentive_ready_jurisdictions": [c for c, _ in accepted],
        "capability_only_jurisdictions": [
            e.jurisdiction_code for e in examinations if e.classification == "capability_only"
        ],
        "accepted_jurisdictions": [c for c, _ in accepted],  # back-compat alias
        "rejection_reason_counts": rejection_reason_counts,
        "home_jurisdiction": home_code,
        "production_type": production_type,
        "required_capabilities": sorted(requirements.required_capabilities),
    }
    return DiscoveryResult(tuple(examinations), tuple(accepted), metrics)
