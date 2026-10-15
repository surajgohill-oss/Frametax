"""Facts a modeled structure establishes by itself (NA-RECONCILIATION-22).

A scenario that places ALL of its principal photography in one jurisdiction has, by construction, satisfied that jurisdiction's "share of the shoot filmed here" tests, and a scenario that places none of it
there has failed them. Asking the producer to re-enter what the scenario already says is the defect this module removes. Everything here is a pure function of (structure rows, the producer's stated facts,
the retained schedule's total shooting days); it never reads a database and never reads a real project.

Precedence (weaker never overwrites stronger): a fact the producer or a retained document already established - true OR refuted - is left exactly as it is; only an unestablished fact is filled.
A scenario-derived fact is disclosed as SCENARIO_ASSUMED, never as verified. A split placement is not decided here: dollars do not establish shooting days (project_eligibility_gates), so a split stays Unknown.

What is NOT derived, deliberately: county class, rural / blighted / distant / regional status (they need a retained locality or geospatial owner; none exists), anything that is a producer decision or
approval, and any share test the repository holds no executable rule for.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

REFUTED_PREFIX = "not:"
#: Synthetic evidence for a share test between two day counts: "scenario_share_met:<numerator day fact>" (met) or its refuted form (failed).
SCENARIO_SHARE_PREFIX = "scenario_share_met:"
#: The retained schedule's total principal-photography days, served as an amount fact (canonical_project_economics reads ProductionAssumption 'intended_shoot_days').
SCHEDULE_TOTAL_DAYS_FACT = "schedule_principal_photography_days_total"

PROVENANCE_VERIFIED = "VERIFIED"
PROVENANCE_PRODUCER_STATED = "PRODUCER_STATED"
PROVENANCE_SCENARIO_ASSUMED = "SCENARIO_ASSUMED"
PROVENANCE_SCHEDULE_DERIVED = "SCHEDULE_DERIVED"
PROVENANCE_BUDGET_DERIVED = "BUDGET_DERIVED"
PROVENANCE_UNKNOWN = "UNKNOWN"


def refuted(key: str) -> str:
    return REFUTED_PREFIX + key


@dataclass(frozen=True)
class ShareRule:
    """A boolean 'at least <min_share> of the shoot is in <jurisdiction>' fact (Missouri) or a share-gate between two day counts (Saskatchewan)."""
    program_slug: str
    jurisdiction_code: str
    fact_key: str                       # boolean evidence key, or the numerator day fact for a share gate
    min_share: float
    authority: str
    is_share_gate: bool = False


SHARE_RULES: tuple[ShareRule, ...] = (
    ShareRule("us_mo_motion_media_production_tax_credit", "US-MO", "mo_filmed_50pct_in_missouri_confirmed", 0.50,
              "RSMo 135.750 subsection 3(2): +5 points when at least fifty percent of the project is filmed in Missouri"),
    ShareRule("ca_sk_creative_saskatchewan_grant", "CA-SK", "ca_sk_principal_photography_days_in_sk", 0.51,
              "Creative Saskatchewan FFTV Guidelines, General Bonus Eligibility: at least 51% of principal photography days completed in Saskatchewan", is_share_gate=True),
)


@dataclass(frozen=True)
class DayRule:
    """Day counts a full placement fixes from the schedule's total: `total_fact` is the production's total (a schedule fact, jurisdiction-independent); `in_facts` equal that total when ALL photography is here."""
    program_slugs: tuple[str, ...]
    jurisdiction_code: str
    total_fact: str | None
    in_facts: tuple[str, ...]
    authority: str


DAY_RULES: tuple[DayRule, ...] = (
    DayRule(("ca_bc_film_tv_tax_credit", "ca_bc_pstc"), "CA-BC", None, ("ca_bc_principal_photography_days_in_bc",),
            "Income Tax Act (BC) Part 5: TD, the principal photography days in British Columbia, is the denominator of the regional and distant-location credits"),
    DayRule(("ca_ns_production_incentive_fund",), "CA-NS", "ca_ns_principal_photography_days_total", ("ca_ns_principal_photography_days_in_ns",),
            "Nova Scotia Film and Television Production Incentive Fund Regulations: Shooting Length and distance-band formulas"),
    DayRule(("ca_nb_film_tax_credit",), "CA-NB", "ca_nb_principal_photography_days_total", (),
            "LIFT 2026/2027 Guidelines: remote / rural bonus day shares"),
    DayRule(("ca_sk_creative_saskatchewan_grant",), "CA-SK", "ca_sk_principal_photography_days_total", ("ca_sk_principal_photography_days_in_sk",),
            "Creative Saskatchewan FFTV Guidelines: activity test and Rural Bonus day shares"),
)


@dataclass(frozen=True)
class DerivedFact:
    key: str
    value: bool | float
    provenance: str
    basis: str


@dataclass(frozen=True)
class ScenarioFacts:
    true_facts: frozenset = frozenset()
    refuted_facts: frozenset = frozenset()       # the keys (without the 'not:' prefix) the scenario fails
    amounts: Mapping = None                       # type: ignore[assignment]
    derived: tuple = ()

    def evidence_tokens(self) -> frozenset:
        return frozenset(self.true_facts) | frozenset(refuted(k) for k in self.refuted_facts)


def principal_photography_placement(rows: Iterable[tuple], jurisdiction_code: str, primary_jurisdiction: str | None) -> tuple[str, str]:
    """("FULL" | "NONE" | "SPLIT" | "UNKNOWN", basis). rows: (jurisdiction_code, amount_usd, component_label, ...). Same evidence discipline as the California gate."""
    pp = [(r[0], float(r[1])) for r in rows if r[2] == "principal_photography" and float(r[1]) > 0]
    if pp:
        inside = sum(a for j, a in pp if j == jurisdiction_code)
        outside = sum(a for j, a in pp if j != jurisdiction_code)
        if outside <= 0:
            return "FULL", f"the modeled structure places ALL of its principal photography in {jurisdiction_code}"
        if inside <= 0:
            return "NONE", f"the modeled structure places NONE of its principal photography in {jurisdiction_code}"
        return "SPLIT", f"the modeled principal photography is split between {jurisdiction_code} and elsewhere; dollar shares do not establish shooting days"
    # no photography accounts: principal-production COMPONENTS stand for the shoot. Two jurisdictions both hosting principal production is a modeled split, which dollars cannot resolve into days.
    holders = {r[0] for r in rows if len(r) > 3 and r[3] == "principal_production" and float(r[1]) > 0}
    if len(holders) > 1:
        return "SPLIT", f"principal production is modeled in several jurisdictions ({', '.join(sorted(holders))}); dollar shares do not establish shooting days"
    if len(holders) == 1:
        only = next(iter(holders))
        return ("FULL", f"principal production is modeled wholly in {jurisdiction_code}") if only == jurisdiction_code else ("NONE", f"principal production is modeled in {only}, outside {jurisdiction_code}")
    if primary_jurisdiction:
        if primary_jurisdiction == jurisdiction_code:
            return "FULL", f"no principal-photography accounts modeled: principal production is modeled in {jurisdiction_code}"
        return "NONE", f"no principal-photography accounts modeled: principal production is modeled in {primary_jurisdiction}, outside {jurisdiction_code}"
    return "UNKNOWN", "no principal-photography placement is modeled"


def _canon(slug: str | None) -> str | None:
    if not slug:
        return slug
    from app.data.program_slug_aliases import canonical_slug
    return canonical_slug(slug)


def scenario_derived_facts(program_slug: str | None, jurisdiction_code: str, rows: Iterable[tuple], primary_jurisdiction: str | None,
                           evidenced: Iterable[str] | None = None, amount_facts: Mapping | None = None) -> ScenarioFacts:
    """The facts this structure establishes for `program_slug` priced in `jurisdiction_code`. Only unestablished facts are filled (stated true, refuted and stated numbers are never overwritten)."""
    slug = _canon(program_slug)
    if not slug:
        return ScenarioFacts(amounts={})
    rows = list(rows)
    have = frozenset(evidenced or ())
    stated = dict(amount_facts or {})
    placement, basis = principal_photography_placement(rows, jurisdiction_code, primary_jurisdiction)
    true_facts: set[str] = set()
    refuted_facts: set[str] = set()
    amounts: dict[str, float] = {}
    derived: list[DerivedFact] = []

    for rule in SHARE_RULES:
        if rule.program_slug != slug or rule.jurisdiction_code != jurisdiction_code:
            continue
        key = (SCENARIO_SHARE_PREFIX + rule.fact_key) if rule.is_share_gate else rule.fact_key
        if key in have or refuted(key) in have:
            continue                                                    # a stronger tier already decided it
        if placement == "FULL":
            true_facts.add(key)
            derived.append(DerivedFact(key, True, PROVENANCE_SCENARIO_ASSUMED, f"{basis}, so the {rule.min_share:.0%} filming test is met. {rule.authority}"))
        elif placement == "NONE":
            refuted_facts.add(key)
            derived.append(DerivedFact(key, False, PROVENANCE_SCENARIO_ASSUMED, f"{basis}, so the {rule.min_share:.0%} filming test is not met. {rule.authority}"))

    schedule_total = stated.get(SCHEDULE_TOTAL_DAYS_FACT)
    if schedule_total is not None and schedule_total > 0:
        for rule in DAY_RULES:
            if slug not in rule.program_slugs or rule.jurisdiction_code != jurisdiction_code:
                continue
            if rule.total_fact and rule.total_fact not in stated:
                amounts[rule.total_fact] = float(schedule_total)
                derived.append(DerivedFact(rule.total_fact, float(schedule_total), PROVENANCE_SCHEDULE_DERIVED,
                                           f"the retained schedule's {schedule_total:g} principal-photography days. {rule.authority}"))
            if placement == "FULL":
                for k in rule.in_facts:
                    if k not in stated:
                        amounts[k] = float(schedule_total)
                        derived.append(DerivedFact(k, float(schedule_total), PROVENANCE_SCENARIO_ASSUMED,
                                                   f"{basis}: every one of the retained schedule's {schedule_total:g} days is in {jurisdiction_code}. {rule.authority}"))
    return ScenarioFacts(frozenset(true_facts), frozenset(refuted_facts), amounts, tuple(derived))


def apply_scenario_facts(evidenced: frozenset | None, amount_facts: Mapping | None, sf: ScenarioFacts) -> tuple[frozenset, dict]:
    """Merge a ScenarioFacts into a component's fact sets without ever overwriting an established fact."""
    ev = frozenset(evidenced or ()) | sf.evidence_tokens()
    am = dict(amount_facts or {})
    for k, v in (sf.amounts or {}).items():
        am.setdefault(k, v)
    return ev, am
