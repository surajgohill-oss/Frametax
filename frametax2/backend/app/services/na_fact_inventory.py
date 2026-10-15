"""Complete inventory of every North American fact the engine consumes (NA-RECONCILIATION-22).

The inventory is GENERATED from the canonical registries, never typed by hand, so a new reader cannot appear without being classified: rate-rule conditions, eligible-subset uplift rules (every fact
field), the producer-fact writer, the content-gate whitelist, project eligibility gates, structural prerequisites, scenario rules and the line-level fact families. For each fact it records the nine
columns the architecture review required. Classification is by an ordered rule table (`_CLASSES`); a fact no rule names is `PRODUCER_ASSERTION` with an explicit reason, never silently derivable.

Derivation classes (who may legitimately establish the fact):
  SCENARIO_PLACEMENT  the selected optimizer structure places all / none of principal photography in the jurisdiction (scenario_facts)
  SCHEDULE_DAYS       the retained schedule's total principal-photography days (ProductionAssumption 'intended_shoot_days')
  BUDGET_ALLOCATION   an amount the normalized budget allocation already contains (labour / non-labour / post / ATL / BTL)
  STRUCTURE           the programs of the selected structure (host credit present)
  LOCALITY            needs a retained locality / geospatial owner (county class, rural, blighted, distant, regional): NONE exists, so producer-stated or Unknown
  PAYEE               needs identified payee / person records (person-level caps, counts)
  PRODUCER_ELECTION   a genuine producer election between alternatives
  PRODUCER_ASSERTION  a legal predicate only the producer or a retained document can establish (ownership, residency, application made, content threshold)
  AGENCY_APPROVAL     an approval / certification / allocation only the agency can grant
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# (class, regex on the fact key). First match wins.
_CLASSES: tuple[tuple[str, str], ...] = (
    ("STRUCTURE", r"structure_host_credit_present"),
    ("SCENARIO_PLACEMENT", r"^mo_filmed_50pct_in_missouri_confirmed$|^scenario_share_met:|principal_photography_days_in_(bc|ns|sk)$"),
    ("SCHEDULE_DAYS", r"principal_photography_days_total$|^schedule_principal_photography_days_total$"),
    ("LOCALITY", r"rural|blighted|distant_location|outside_vancouver|50km_outside|remote_151|rural_30_to_150|100_to_150km|over_150km|second_third_fourth_class_county|underserved_area|"
                 r"listed_counties|commuter|zone|eligible_county|out_of_zone|distressed|opportunity_zone"),
    ("PAYEE", r"_persons$|payee|producer_role|composer_compensation|ny_atl_payee|individual_cap|per_person"),
    ("BUDGET_ALLOCATION", r"_qualified_labour_usd$|^us_or_(payroll|other)_qpe_usd$|^us_mt_(resident_crew|nonresident_crew|talent|student|veteran_tribal)_compensation_usd$|^us_mt_postproduction_wages_usd$"),
    ("AGENCY_APPROVAL", r"approv|certif|allocation|preapproval|awarded|office_confirmed|commission_confirmed"),
    ("PRODUCER_ELECTION", r"stream_confirmed|photography_(after|before)_20|election|elect"),
)

#: Facts that are mutually exclusive elections (a False is not a legal predicate: the producer states the chosen alternative).
def is_election(key: str, partner) -> bool:
    return bool(partner)


@dataclass
class FactRow:
    key: str
    kind: str = "boolean"                       # boolean | number | gate
    consumers: list = None                      # type: ignore[assignment]
    legal_effect: list = None                   # type: ignore[assignment]
    writer: str = ""
    storage: str = ""
    writable: bool = False
    restorable: bool = False
    derivation_class: str = "PRODUCER_ASSERTION"
    current_status: str = ""
    derivable_from: str = ""
    producer_decision: bool = True
    behaviour: str = ""
    unknown_pricing: str = ""
    gap: str = ""

    def __post_init__(self):
        self.consumers = self.consumers or []
        self.legal_effect = self.legal_effect or []

    def as_dict(self) -> dict:
        return {"fact_key": self.key, "kind": self.kind, "consumers": sorted(set(self.consumers)), "legal_economic_effect": sorted(set(self.legal_effect)),
                "writer": self.writer, "storage_owner": self.storage, "writable": self.writable, "restorable": self.restorable, "derivation_class": self.derivation_class,
                "current_status": self.current_status, "derivable_from": self.derivable_from, "genuine_producer_decision": self.producer_decision, "true_false_unknown_behaviour": self.behaviour,
                "pricing_when_unknown": self.unknown_pricing, "missing_control_or_path": self.gap}


def _status(key: str, cls: str) -> str:
    """What the engine does with the fact TODAY (the class says who could establish it; this says whether the system now does)."""
    if cls == "STRUCTURE":
        return "DERIVED_AUTOMATICALLY"
    if cls == "SCENARIO_PLACEMENT":
        return "DERIVED_FOR_FULL_OR_NO_PLACEMENT; a split shoot is stated by the producer or stays Unknown"
    if cls == "SCHEDULE_DAYS":
        return "DERIVED_FROM_RETAINED_SCHEDULE; unavailable evidence is stated by the producer"
    if key == "us_mt_resident_crew_compensation_usd":
        return "DERIVED_FROM_BUDGET at the lawful lower bound until the number of persons is stated"
    if cls == "BUDGET_ALLOCATION":
        if re.search(r"_qualified_labour_usd$|^us_or_", key):
            return "DERIVED_AUTOMATICALLY"
        return "BUDGET_AMOUNT_NEEDS_A_PRODUCER_FACT (withholding, student, veteran or approved-company status is not in the budget); producer states it"
    if cls == "LOCALITY":
        return "BLOCKED_BY_UNAVAILABLE_EVIDENCE: no retained locality or geospatial owner"
    if cls == "PAYEE":
        return "BLOCKED_BY_UNAVAILABLE_EVIDENCE: needs identified payee records; otherwise a lawful upper bound with a missing-evidence flag"
    if cls == "AGENCY_APPROVAL":
        return "GENUINE_EXTERNAL_APPROVAL"
    return "GENUINE_PRODUCER_DECISION"


def classify(key: str, *, is_election_fact: bool = False) -> str:
    if is_election_fact:
        return "PRODUCER_ELECTION"
    for cls, rx in _CLASSES:
        if re.search(rx, key):
            return cls
    return "PRODUCER_ASSERTION"


_DERIVABLE_FROM = {
    "STRUCTURE": "programs of the selected optimizer structure",
    "SCENARIO_PLACEMENT": "selected structure's placement of principal photography (all / none in the jurisdiction); a split stays Unknown",
    "SCHEDULE_DAYS": "retained schedule / day-out-of-days total (ProductionAssumption intended_shoot_days)",
    "BUDGET_ALLOCATION": "normalized budget allocation categories (labour / non-labour / ATL / BTL / post / compensation); a category a line cannot evidence stays Unknown",
    "LOCALITY": "selected locality or geospatial owner - NONE RETAINED, so producer-stated or Unknown",
    "PAYEE": "identified payee / person records - derived only where identified; otherwise a lawful upper bound plus a missing-evidence flag",
    "PRODUCER_ELECTION": "not derivable: a producer election between alternatives",
    "PRODUCER_ASSERTION": "not derivable from retained records: ownership, residency, application or content predicate the producer or a document must establish",
    "AGENCY_APPROVAL": "not derivable: only the granting agency can establish it",
}

_AUTOMATIC = {"STRUCTURE", "SCENARIO_PLACEMENT", "SCHEDULE_DAYS"}
_PARTIAL_BUDGET = {"us_mt_resident_crew_compensation_usd"}


def _fact_rows() -> dict[str, FactRow]:
    import app.data.program_rate_rules as r
    from app.calculators.project_eligibility_gates import PROJECT_GATES
    from app.optimization.structural_prerequisites import STRUCTURAL_PREREQUISITES
    from app.services import ny_producer_facts as npf
    from app.services.program_content_gates import gate_control_whitelist

    rows: dict[str, FactRow] = {}

    def row(key: str, kind: str = "boolean") -> FactRow:
        return rows.setdefault(key, FactRow(key, kind))

    # ── writers: the one producer-fact writer and the content-gate controls ──
    for key, partner in npf.NY_EVIDENCED_FACTS.items():
        f = row(key)
        f.writer = "POST /projects/{id}/program-facts (write_ny_program_facts)"
        f.storage = "ProjectFact evidenced_program_fact:<key> (USER_OVERRIDE)"
        f.writable = f.restorable = True
        if partner:
            f.legal_effect.append(f"election, mutually exclusive with {partner}")
    for key in npf.PROGRAM_AMOUNT_FACTS:
        f = row(key, "number")
        f.writer = "POST /projects/{id}/program-facts (write_ny_program_facts)"
        f.storage = "ProjectFact amount_fact:<key> (USER_OVERRIDE)"
        f.writable = f.restorable = True
    for key, meta in gate_control_whitelist().items():
        f = row(key, "gate")
        f.writer = "program content-gate controls (program_content_gates)"
        f.storage = "ProjectFact gate row (confirmed | refused)"
        f.writable = f.restorable = True
        f.legal_effect.append(str(meta.get("category") or meta.get("kind") or "gate"))
        f.consumers.append(str(meta.get("program_slug") or ""))

    # ── readers ──
    na_programs = [k for k in r._RULES_BY_PROGRAM if k.startswith(("us_", "ca_"))]
    for slug in na_programs:
        for rule in r._RULES_BY_PROGRAM[slug]:
            for c in rule.conditions or ():
                for attr, kind, effect in (("required_boolean_fact_key", "boolean", "tier requires the fact"), ("amount_fact_key", "number", "tier gated on the amount"),
                                           ("superseded_by_boolean_fact_key", "boolean", "tier superseded"), ("regional_uplift_multiplier_fact_key", "boolean", "regional multiplier")):
                    k = getattr(c, attr, None)
                    if k:
                        f = row(k, kind)
                        f.consumers.append(f"{slug}:{rule.tier_id}:{c.condition_id}")
                        f.legal_effect.append(effect)
                for k in c.blocked_by_boolean_fact_keys or ():
                    f = row(k)
                    f.consumers.append(f"{slug}:{rule.tier_id}:{c.condition_id}")
                    f.legal_effect.append("tier blocked by the fact")
            if rule.awarded_rate_fact_key:
                f = row(rule.awarded_rate_fact_key, "number")
                f.consumers.append(f"{slug}:{rule.tier_id}")
                f.legal_effect.append("awarded rate")
    for slug, uplifts in r.SUBSET_UPLIFT_RULES.items():
        if not slug.startswith(("us_", "ca_")):
            continue
        for u in uplifts:
            def add(k, kind, effect):
                if k:
                    f = row(k, kind)
                    f.consumers.append(f"{slug}:{u.uplift_id}")
                    f.legal_effect.append(effect)
            add(u.prerequisite_fact, "boolean", f"uplift {u.rate:.0%} prerequisite")
            add(u.excluded_fact, "boolean", "uplift excluded when stated")
            add(u.whole_base_fact, "boolean", "whole eligible base inside the uplift")
            for k in u.criteria_facts or ():
                add(k, "boolean", "content criterion")
            for k in (u.day_numerator_fact, u.day_denominator_fact, u.amount_fact, u.post_wage_fact):
                add(k, "number", "formula input")
            for k in tuple(u.assistance_facts or ()) + tuple(u.tier_numerator_facts or ()):
                add(k, "number", "formula input")
            for group in u.tier_numerator_groups or ():
                for k in group:
                    add(k, "number", "formula input")
            for k in (u.hod_filled_fact, u.hod_resident_fact, u.stream_i_fact, u.stream_ii_fact):
                add(k, "number", "formula input")
            for comp_fact, count_fact, _rate, _cc, _mc, required in u.compensation_credits or ():
                add(comp_fact, "number", "compensation credit amount")
                add(count_fact, "number", "persons (per-person cap)")
                add(required, "boolean", "compensation credit prerequisite")
    for gid, g in PROJECT_GATES.items():
        if g.photography_fact_key:
            f = row(g.photography_fact_key, "number")
            f.consumers.append(f"{gid} project gate")
            f.legal_effect.append("principal-photography days branch of the project eligibility gate")
    for slug, pre in STRUCTURAL_PREREQUISITES.items():
        f = row(pre.fact_key)
        f.consumers.append(slug)
        f.legal_effect.append("host credit present")
    # line-level families (writer: write_ny_program_facts payees / producer_roles / composer_portions / uplift_basis)
    for fam, kind, effect in (("line_fact:<line>:payee_id", "string", "person-level caps, aggregate payee limits"),
                              ("line_fact:<line>:payee_compensation_complete", "boolean", "exact person-level cap (otherwise upper bound)"),
                              ("line_fact:<line>:payee_type", "string", "payee-type limits"),
                              ("line_fact:<line>:producer_role", "string", "producer position limits (NS second-position fee)"),
                              ("line_fact:<line>:composer_compensation_usd", "number", "composer portion of a music account"),
                              ("uplift_basis_subsets", "json", "per-line eligible portion of a subset uplift base"),
                              ("ny_atl_payee:<line>", "number", "NY above-the-line individual limit payee ordinal")):
        f = row(fam, kind)
        f.writer = "POST /projects/{id}/program-facts (payees / producer_roles / composer_portions / uplift_basis)"
        f.storage = "ProjectFact " + fam
        f.writable = f.restorable = True
        f.legal_effect.append(effect)
        f.consumers.append("per_payee_limits / allocation_pricing")
    for key in ("schedule_principal_photography_days_total",):
        f = row(key, "number")
        f.writer = "none needed: derived from ProductionAssumption intended_shoot_days"
        f.storage = "ProductionAssumption (evidence_state ACTUAL | USER_CONFIRMED | DETERMINISTIC_DERIVED)"
        f.restorable = True
        f.consumers.append("scenario_facts DAY_RULES")
        f.legal_effect.append("total principal-photography days")
    # amounts the pricing kernel / loaders already derive from the normalized budget (no producer control needed)
    for key, f in rows.items():
        if re.search(r"_qualified_labour_usd$", key):
            f.writer, f.storage, f.restorable = "canadian_labour_basis (derived from evidenced line-level facts)", "derived on every load (never stored)", True
        elif re.fullmatch(r"us_or_(payroll|other)_qpe_usd", key):
            f.writer, f.storage, f.restorable = "component-basis derivation in allocation_pricing (from the allocation)", "derived per structure (never stored)", True
    from app.calculators.scenario_facts import SHARE_RULES
    for rule in SHARE_RULES:
        key = ("scenario_share_met:" + rule.fact_key) if rule.is_share_gate else rule.fact_key
        f = row(key)
        f.consumers.append(rule.program_slug)
        f.legal_effect.append(f"{rule.min_share:.0%} filming test")
        f.storage = f.storage or "derived per structure (never stored)"
    return rows


def build_inventory() -> list[dict]:
    from app.services import ny_producer_facts as npf
    rows = _fact_rows()
    out = []
    for key, f in sorted(rows.items()):
        partner = npf.NY_EVIDENCED_FACTS.get(key)
        cls = classify(key, is_election_fact=bool(partner))
        if key in _PARTIAL_BUDGET:
            cls = "BUDGET_ALLOCATION"
        f.derivation_class = cls
        f.current_status = _status(key, cls)
        f.derivable_from = _DERIVABLE_FROM[cls]
        f.producer_decision = cls in {"PRODUCER_ELECTION", "PRODUCER_ASSERTION", "AGENCY_APPROVAL", "LOCALITY", "PAYEE"}
        has_writer = bool(f.writer)
        if not has_writer and cls not in _AUTOMATIC and not key.startswith("scenario_share_met:"):
            f.gap = "READER WITH NO CANONICAL WRITER: a rule reads this fact but no producer control or derivation establishes it"
        elif cls in _AUTOMATIC and not f.storage:
            f.storage = "derived per structure / schedule (never stored)"
        if f.kind in ("boolean", "gate"):
            if cls == "PRODUCER_ELECTION":
                f.behaviour = "TRUE = the elected alternative; FALSE is not stored (state the chosen alternative instead); UNKNOWN = unelected, conditional potential"
            elif cls in _AUTOMATIC:
                f.behaviour = "TRUE = scenario/schedule establishes it; FALSE = scenario fails it (rule's failed treatment); UNKNOWN = split or no placement modeled"
            else:
                f.behaviour = "VERIFIED_TRUE / VERIFIED_FALSE (rule's failed treatment, no conditional upside) / UNKNOWN (conditional potential preserved)"
            f.unknown_pricing = "guaranteed 0, bounded potential shown with the exact requirement"
        elif f.kind == "number":
            f.behaviour = "stated number (0 is a real zero) / UNKNOWN"
            f.unknown_pricing = "bounded potential at the rule's ceiling; guaranteed excludes the formula"
            if cls == "BUDGET_ALLOCATION":
                f.derivable_from += "; the producer states only what the budget cannot evidence"
        if cls in {"LOCALITY"} and not f.gap:
            f.gap = "no retained locality / geospatial owner: producer-stated or Unknown until one exists"
        if cls == "PAYEE" and not f.gap:
            f.gap = "needs identified payee records; absent payees leave a lawful upper bound with a missing-evidence flag"
        out.append(f.as_dict())
    return out
