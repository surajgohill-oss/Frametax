"""The ONE resolved-fact layer for the North American programs (NA-RECONCILIATION-22).

Every fact the engine consumes is resolved to a value AND a provenance, with a fixed precedence (a weaker tier never overwrites a stronger one):

    1. VERIFIED          retained document / database evidence (a schedule row with evidence state ACTUAL or DETERMINISTIC_DERIVED; budget-derived amounts)
    2. PRODUCER_STATED   an explicit saved producer statement or election (ProjectFact USER_OVERRIDE)
    3. SCENARIO_ASSUMED  an explicit optimizer planning assumption (the structure places all / none of principal photography in the jurisdiction)
    4. UNKNOWN

Booleans that are ordinary legal predicates are tri-state: TRUE, FALSE (a REFUTED fact: the rule's actual failed treatment applies and no conditional upside is shown) or UNKNOWN (conditional potential
preserved). A False is never represented by deleting the fact. A mutually exclusive election is not a predicate: the producer states the alternative that applies and a No is refused.

The served view never evaluates anything; it reads ProjectFact rows and ProductionAssumption rows only. Scenario-assumed facts are per-structure (scenario_facts) and are listed here as RULES, because
which structure is selected is not a project fact.
"""
from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators.scenario_facts import (
    DAY_RULES, PROVENANCE_PRODUCER_STATED, PROVENANCE_SCENARIO_ASSUMED, PROVENANCE_SCHEDULE_DERIVED, PROVENANCE_UNKNOWN, PROVENANCE_VERIFIED, SHARE_RULES, SCHEDULE_TOTAL_DAYS_FACT,
)

#: Schedule rows with these evidence states are retained evidence (tier 1); USER_CONFIRMED is a producer-level statement (tier 2).
VERIFIED_SCHEDULE_STATES = frozenset({"ACTUAL", "DETERMINISTIC_DERIVED"})
PRODUCER_SCHEDULE_STATES = frozenset({"USER_CONFIRMED"})
#: Program-specific totals the verified schedule overrides (a producer figure that disagrees is reported as a conflict, never used).
SCHEDULE_TOTAL_FACT_KEYS = ("ca_ns_principal_photography_days_total", "ca_nb_principal_photography_days_total", "ca_sk_principal_photography_days_total")


async def schedule_total_days_with_tier(session: AsyncSession, project_id) -> tuple[int | None, str | None]:
    """(total principal-photography days, tier) from ProductionAssumption 'intended_shoot_days'; (None, None) when absent or not a positive whole number. Never defaults."""
    from app.models.production_requirement import EVIDENCE_PRECEDENCE, ProductionAssumption
    rows = (await session.execute(select(ProductionAssumption).where(
        ProductionAssumption.project_id == project_id, ProductionAssumption.assumption_key == "intended_shoot_days"))).scalars().all()
    usable = [r for r in rows if r.evidence_state in VERIFIED_SCHEDULE_STATES | PRODUCER_SCHEDULE_STATES]
    for r in sorted(usable, key=lambda x: EVIDENCE_PRECEDENCE.get(x.evidence_state, 99)):
        try:
            v = float(str(r.value).strip())
        except (TypeError, ValueError):
            continue
        if math.isfinite(v) and v >= 1 and abs(v - round(v)) < 1e-9:
            return int(round(v)), (PROVENANCE_VERIFIED if r.evidence_state in VERIFIED_SCHEDULE_STATES else PROVENANCE_PRODUCER_STATED)
    return None, None


async def schedule_total_days(session: AsyncSession, project_id) -> int | None:
    return (await schedule_total_days_with_tier(session, project_id))[0]


def resolve_boolean(*, verified: bool | None = None, stated: bool | None = None, scenario: bool | None = None) -> tuple[str, str, bool | None]:
    """(state, provenance, value) by precedence VERIFIED > PRODUCER_STATED > SCENARIO_ASSUMED > UNKNOWN. A weaker tier never overwrites a stronger one, False included."""
    for value, prov in ((verified, PROVENANCE_VERIFIED), (stated, PROVENANCE_PRODUCER_STATED), (scenario, PROVENANCE_SCENARIO_ASSUMED)):
        if value is True:
            return "TRUE", prov, True
        if value is False:
            return "FALSE", prov, False
    return "UNKNOWN", PROVENANCE_UNKNOWN, None


def _effects() -> dict[str, list[str]]:
    """fact key -> the pricing effects the rate rules attach to it (uplift points, tier gates), read from the canonical registries."""
    import app.data.program_rate_rules as r
    out: dict[str, list[str]] = {}
    for slug, uplifts in r.SUBSET_UPLIFT_RULES.items():
        for u in uplifts:
            if u.kind == "points_on_base" and u.prerequisite_fact:
                pts = u.rate * 100
                out.setdefault(u.prerequisite_fact, []).append(f"+{pts:g} points on the base rate ({slug})")
            elif u.prerequisite_fact:
                out.setdefault(u.prerequisite_fact, []).append(f"{u.uplift_id.replace('_', ' ')} uplift prerequisite ({slug})")
            for k in (u.whole_base_fact, *(u.criteria_facts or ())):
                if k:
                    out.setdefault(k, []).append(f"{u.uplift_id.replace('_', ' ')} uplift ({slug})")
    return out


def missouri_ladder(states: dict[str, str]) -> dict:
    """The Missouri rate display: 20% base; +5 if at least 50% is filmed in Missouri; +5 if at least 15% of the Missouri filming is in a rural or blighted area (15% is a THRESHOLD, not 15 points);
    +5 qualifying department hires; +5 script marketing; +2 for a second-, third- or fourth-class county; 42% maximum. `states`: fact key -> TRUE | FALSE | UNKNOWN."""
    import app.data.program_rate_rules as r
    slug = "us_mo_motion_media_production_tax_credit"
    base = min(t.rate for t in r._RULES_BY_PROGRAM[slug])
    steps = []
    confirmed = potential = base * 100
    for u in r.SUBSET_UPLIFT_RULES[slug]:
        st = states.get(u.prerequisite_fact, "UNKNOWN")
        pts = round(u.rate * 100, 6)
        steps.append({"id": u.uplift_id, "fact_key": u.prerequisite_fact, "points": pts, "state": st})
        if st == "TRUE":
            confirmed += pts
            potential += pts
        elif st == "UNKNOWN":
            potential += pts
    cap = r.SUBSET_COMBINED_RATE_CAPS.get(slug, (0.42,))[0] * 100
    return {"program": slug, "base_pct": round(base * 100, 6), "steps": steps, "confirmed_pct": round(min(confirmed, cap), 6), "potential_pct": round(min(potential, cap), 6), "max_pct": round(cap, 6)}


async def resolved_requirements_view(session: AsyncSession, project_id) -> dict:
    """The served resolved-requirements view (read-only; never evaluates): every catalogued NA fact with value, provenance, editability and the exact requirement, plus the scenario rules."""
    from app.services import ny_producer_facts as npf
    from app.services.na_fact_inventory import classify
    from app.services.producer_fact_catalog import GROUPS, stored_values

    booleans, numbers = await stored_values(session, project_id)
    sched_days, sched_tier = await schedule_total_days_with_tier(session, project_id)
    effects = _effects()
    groups = []
    states: dict[str, str] = {}
    for gid, title, programs, authority, facts in GROUPS:
        rows = []
        for key, label, hint in facts:
            partner = npf.NY_EVIDENCED_FACTS.get(key)
            cls = classify(key, is_election_fact=bool(partner))
            row = {"key": key, "label": label, "help": hint, "derivation_class": cls, "effects": effects.get(key, [])}
            if key in npf.PROGRAM_AMOUNT_FACTS:
                lo, hi = npf.PROGRAM_AMOUNT_FACTS[key]
                stated = numbers.get(key)
                row.update({"kind": "number", "min": lo, "max": hi, "whole": npf.is_whole_number_fact(key), "unit": "USD" if key.endswith("_usd") else None})
                derived = None
                if key in SCHEDULE_TOTAL_FACT_KEYS and sched_days is not None:
                    derived = float(sched_days)
                if derived is not None and sched_tier == PROVENANCE_VERIFIED:
                    row.update({"state": "VALUE", "value": derived, "provenance": PROVENANCE_SCHEDULE_DERIVED, "editable": False,
                                "basis": f"the retained schedule's {sched_days} principal-photography days (verified)"})
                    if stated is not None and abs(stated - derived) > 1e-9:
                        row["conflict"] = f"a producer statement of {stated:g} disagrees with the verified schedule; the schedule is used"
                elif stated is not None:
                    row.update({"state": "VALUE", "value": stated, "provenance": PROVENANCE_PRODUCER_STATED, "editable": True, "basis": "stated by the producer"})
                elif derived is not None:
                    row.update({"state": "VALUE", "value": derived, "provenance": PROVENANCE_SCHEDULE_DERIVED, "editable": True,
                                "basis": f"the schedule's {sched_days} days (producer-confirmed); state a different number to override"})
                else:
                    row.update({"state": "UNKNOWN", "value": None, "provenance": PROVENANCE_UNKNOWN, "editable": True,
                                "basis": "not stated; the affected credit stays a bounded potential"})
            else:
                stated_b = booleans.get(key)
                state, prov, value = resolve_boolean(stated=stated_b)
                row.update({"kind": "election" if partner else "boolean", "exclusive_with": partner if isinstance(partner, str) else None, "state": state, "value": value,
                            "provenance": prov, "editable": True,
                            "basis": {"TRUE": "stated Yes by the producer", "FALSE": "stated No by the producer: the rule's failed treatment applies, no conditional upside",
                                      "UNKNOWN": "not stated: conditional potential is preserved"}[state]})
                if key in {sr.fact_key for sr in SHARE_RULES if not sr.is_share_gate}:
                    row["scenario_rule"] = "A scenario that places all of the principal photography in the jurisdiction establishes this; a split scenario leaves it to the producer."
                states[key] = state
            if row["state"] == "UNKNOWN":
                row["requirement"] = label
            rows.append(row)
        groups.append({"id": gid, "title": title, "programs": list(programs), "authority": authority, "facts": rows,
                       "stated_count": sum(1 for r in rows if r["state"] not in ("UNKNOWN",) and r["provenance"] == PROVENANCE_PRODUCER_STATED),
                       "resolved_count": sum(1 for r in rows if r["state"] != "UNKNOWN")})
    return {
        "groups": groups,
        "stated_count": sum(g["stated_count"] for g in groups),
        "resolved_count": sum(g["resolved_count"] for g in groups),
        "schedule": {"total_days": sched_days, "tier": sched_tier},
        "scenario_rules": [{"program": sr.program_slug, "jurisdiction": sr.jurisdiction_code, "fact_key": sr.fact_key, "min_share": sr.min_share, "authority": sr.authority,
                            "rule": f"All principal photography in {sr.jurisdiction_code}: the {sr.min_share:.0%} test is met (scenario-assumed). None: it is not met. A split is left Unknown."} for sr in SHARE_RULES]
                          + [{"program": slug, "jurisdiction": dr.jurisdiction_code, "fact_key": k, "authority": dr.authority,
                              "rule": f"All principal photography in {dr.jurisdiction_code}: {k} equals the retained schedule's total days (scenario-assumed)."}
                             for dr in DAY_RULES for slug in dr.program_slugs for k in dr.in_facts],
        "missouri": missouri_ladder(states),
        "provenance_legend": {PROVENANCE_VERIFIED: "retained document or database evidence", PROVENANCE_PRODUCER_STATED: "stated by the producer",
                              PROVENANCE_SCENARIO_ASSUMED: "assumed by the selected optimizer scenario", PROVENANCE_SCHEDULE_DERIVED: "derived from the retained schedule", PROVENANCE_UNKNOWN: "not established"},
        "note": ("Resolved requirements. Verified evidence outranks a producer statement, which outranks a scenario assumption. A derived or assumed fact is shown read-only; only a genuine producer decision or "
                 "evidence the system cannot hold is asked for. Unknown keeps the conditional potential; No applies the rule's failed treatment."),
    }
