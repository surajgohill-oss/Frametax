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
    accepted: bool
    reason: str
    program_slug: str | None
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
    production_type: str,
    qpe_usd: float | None,
    home_code: str,
) -> DiscoveryResult:
    """Examine every implemented jurisdiction and return the executable set
    plus a full, reasoned audit. Pure function of the data + the production
    facts; iterates registries, never a hard-coded country list."""
    from app.calculators import jurisdiction_comparison as jc
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

        resolves = False
        if slug is None:
            reason = ("Catalog inventory only — no structured executable profile "
                      "(no classified qualification doctrine and no statutory rate "
                      "rules). Cannot be priced without guessing; excluded.")
            _reject("catalog_only_no_profile")
            ok = False
        elif not has_doctrine and not has_rate:
            reason = ("Modeled profile but neither classified qualification doctrine "
                      "nor statutory rate rules — insufficient knowledge to price; "
                      "excluded rather than guessed.")
            _reject("no_doctrine_no_rate")
            ok = False
        elif not has_doctrine:
            reason = ("Statutory rate rules present but no classified qualification "
                      "doctrine — cannot derive a qualification register; excluded "
                      "rather than guessed.")
            _reject("no_doctrine")
            ok = False
        elif not has_rate:
            reason = ("Qualification doctrine present but no statutory rate rules — "
                      "cannot resolve an incentive rate; excluded rather than guessed.")
            _reject("no_rate_rules")
            ok = False
        else:
            # KNOWLEDGE gate passed → REQUIREMENT gate: does THIS production
            # (its type + qualifying spend) actually resolve a statutory rate?
            rr = resolve_program_rate(slug, production_type=production_type, qpe_usd=qpe_usd)
            resolves = rr is not None
            if not resolves:
                reason = ("Executable knowledge present, but this production's type "
                          f"'{production_type}' / qualifying spend does not meet the "
                          "program's statutory conditions (production-type scope or "
                          "minimum spend); excluded rather than guessed.")
                _reject("production_conditions_unmet")
                ok = False
            else:
                reason = ("Executable: classified qualification doctrine + statutory "
                          "rate rules present and the production resolves a statutory "
                          "rate — enters optimization.")
                ok = True
                accepted.append((code, slug))

        examinations.append(JurisdictionExamination(
            jurisdiction_code=code, jurisdiction_name=name, accepted=ok, reason=reason,
            program_slug=slug, has_doctrine=has_doctrine, has_rate_rules=has_rate,
            resolves_for_production=resolves, stated_base_rate=stated_rate,
            requires_cultural_test=req_cultural, requires_local_entity=req_entity,
        ))

    metrics = {
        "jurisdictions_examined": len(examinations),
        "accepted_count": len(accepted),
        "rejected_count": len(examinations) - len(accepted),
        "accepted_jurisdictions": [c for c, _ in accepted],
        "rejection_reason_counts": rejection_reason_counts,
        "home_jurisdiction": home_code,
        "production_type": production_type,
    }
    return DiscoveryResult(tuple(examinations), tuple(accepted), metrics)
