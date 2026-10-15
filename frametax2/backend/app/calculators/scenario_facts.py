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

LOC = "locality:"

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
PROVENANCE_LOCALITY_RESOLVED = "LOCALITY_RESOLVED"
PROVENANCE_UNKNOWN = "UNKNOWN"


def refuted(key: str) -> str:
    return REFUTED_PREFIX + key


@dataclass(frozen=True)
class ShareRule:
    """A boolean 'at least <min_share> of the shoot is in <jurisdiction>' fact (Missouri, BC) or a share-gate between two day counts (Saskatchewan)."""
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
    ShareRule("ca_bc_film_tv_tax_credit", "CA-BC", "ca_bc_film_tv_photography_days_75pct_in_bc_confirmed", 0.75,
              "Income Tax Act (BC) s.79(1) 'eligible production': principal photography in British Columbia on at least 75% of the days"),
)


@dataclass(frozen=True)
class SpendShareRule:
    """A requirement on the share of budget allocations (all rows, or only the named components) placed in the jurisdiction. The allocation is what the scenario establishes; a share at or above the minimum
    meets it, a share below it fails it in THIS scenario. No rows in the component set means no derivation."""
    program_slug: str
    jurisdiction_code: str
    fact_key: str
    min_share: float
    components: frozenset | None
    authority: str


SPEND_SHARE_RULES: tuple[SpendShareRule, ...] = (
    SpendShareRule("ca_bc_film_tv_tax_credit", "CA-BC", "ca_bc_film_tv_bc_cost_75pct_confirmed", 0.75, None,
                   "Income Tax Act (BC) s.79(1) 'eligible production' (f)(i)(B): at least 75% of the cost payable to BC-based individuals or corporations for goods and services in British Columbia"),
    SpendShareRule("ca_bc_film_tv_tax_credit", "CA-BC", "ca_bc_film_tv_post_75pct_in_bc_confirmed", 0.75, frozenset({"post", "vfx", "music"}),
                   "Income Tax Act (BC) s.79(1) 'eligible production' (f)(i)(C): at least 75% of the cost of postproduction work carried out in British Columbia"),
)

#: locality predicates -> the programs they feed (a predicate with a fact_key establishes a boolean; one with a day_fact establishes a day count)
PREDICATE_PROGRAMS: dict[str, tuple[str, ...]] = {
    "mo_county_qualifying": ("us_mo_motion_media_production_tax_credit",), "mo_rural_or_blighted": ("us_mo_motion_media_production_tax_credit",),
    "bc_outside_vancouver": ("ca_bc_film_tv_tax_credit", "ca_bc_pstc"), "bc_distant": ("ca_bc_film_tv_tax_credit", "ca_bc_pstc"),
    "ns_zone_a": ("ca_ns_production_incentive_fund",), "ns_zone_b": ("ca_ns_production_incentive_fund",),
    "nb_rural": ("ca_nb_film_tax_credit",), "nb_remote": ("ca_nb_film_tax_credit",), "sk_rural50": ("ca_sk_creative_saskatchewan_grant",),
}


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


def _is_parent(code: str, child: str) -> bool:
    return bool(code) and "-" not in code and child.startswith(code + "-")


def principal_photography_placement(rows: Iterable[tuple], jurisdiction_code: str, primary_jurisdiction: str | None) -> tuple[str, str]:
    """("FULL" | "NONE" | "SPLIT" | "UNKNOWN", basis). rows: (jurisdiction_code, amount_usd, component_label, ...). Same evidence discipline as the California gate."""
    pp = [(r[0], float(r[1])) for r in rows if r[2] == "principal_photography" and float(r[1]) > 0]
    # a row coded to a PARENT jurisdiction (the federal "CA" layer of a stack) does not say where the shoot is: it neither places nor displaces it
    if any(_is_parent(j, jurisdiction_code) for r in rows for j in [r[0]] if float(r[1]) > 0 and (r[2] == "principal_photography" or len(r) > 3 and r[3] == "principal_production")):
        return "UNKNOWN", f"rows coded to the parent jurisdiction of {jurisdiction_code} do not locate the shoot"
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


def _share_interval(jurisdiction_code: str, placement: str, stated: Mapping) -> tuple[float, float] | None:
    """(lower, upper) share of the whole shoot's days in the jurisdiction. A modeled FULL / NONE placement is exact; otherwise only exact schedule days at explicit locations bound it."""
    if placement == "FULL":
        return 1.0, 1.0
    if placement == "NONE":
        return 0.0, 0.0
    total = stated.get(SCHEDULE_TOTAL_DAYS_FACT)
    all_days = stated.get(LOC + "days:ALL")
    if not total or total <= 0 or all_days is None or all_days > total:
        return None
    here = stated.get(f"{LOC}days:{jurisdiction_code}", 0.0)
    return here / total, (here + (total - all_days)) / total


def _decide(interval: tuple[float, float] | None, min_share: float, exclusive: bool = False) -> bool | None:
    if interval is None:
        return None
    lo, hi = interval
    eps = 1e-9
    if (lo > min_share + eps) if exclusive else (lo + eps >= min_share):
        return True
    if (hi <= min_share + eps) if exclusive else (hi + eps < min_share):
        return False
    return None


def _jurisdiction_days(jurisdiction_code: str, placement: str, stated: Mapping) -> float | None:
    """Exact days of principal photography in the jurisdiction: the schedule total for a FULL placement, else the dated explicit locations when every location is dated and the shoot is fully allocated."""
    total = stated.get(SCHEDULE_TOTAL_DAYS_FACT)
    if placement == "FULL":
        return float(total) if total else None
    if placement == "NONE" or not total:
        return None
    if stated.get(LOC + "undated:ALL", 1.0) == 0.0 and stated.get(LOC + "days:ALL") == total:
        return float(stated.get(f"{LOC}days:{jurisdiction_code}", 0.0))
    return None


def _predicate_state(pred, placement: str, stated: Mapping, jdays: float | None) -> tuple[bool | None, float | None]:
    """(boolean state for a share/all predicate, band day count) from the locality facts. None = Unknown."""
    j = pred.jurisdiction
    n = stated.get(f"{LOC}n:{j}", 0.0)
    if not n or placement == "NONE":
        return None, None                                       # no explicit location here (or no shoot here): nothing to classify; a slice that is only spend is not a filming location
    tn, fn, un = (stated.get(f"{LOC}{pred.key}:{k}:{j}", 0.0) for k in ("Tn", "Fn", "Un"))
    t_days, f_days = stated.get(f"{LOC}{pred.key}:T:{j}", 0.0), stated.get(f"{LOC}{pred.key}:F:{j}", 0.0)
    state: bool | None = None
    day_count: float | None = None
    if pred.mode == "all":
        state = True if (tn > 0 and fn == 0 and un == 0) else (False if (fn > 0 and tn == 0 and un == 0) else None)
    else:
        if n == 1 and jdays is not None:                       # one explicit location holds every day of the jurisdiction
            t_days, f_days = (jdays, 0.0) if tn else ((0.0, jdays) if fn else (0.0, 0.0))
        if jdays:
            lo, hi = t_days / jdays, (jdays - f_days) / jdays
            if pred.min_share is not None:
                state = _decide((lo, hi), pred.min_share)
        if jdays is not None and un == 0 and (stated.get(f"{LOC}undated:{j}", 0.0) == 0.0 or n == 1) and (n == 1 or stated.get(f"{LOC}days:{j}") == jdays):
            day_count = float(t_days)
    return state, day_count


def scenario_derived_facts(program_slug: str | None, jurisdiction_code: str, rows: Iterable[tuple], primary_jurisdiction: str | None,
                           evidenced: Iterable[str] | None = None, amount_facts: Mapping | None = None) -> ScenarioFacts:
    """The facts this structure establishes for `program_slug` priced in `jurisdiction_code`. Only unestablished facts are filled (stated true, refuted and stated numbers are never overwritten).
    Sources, strongest first among derivations: explicit locations with exact schedule days (LOCALITY_RESOLVED), the structure's placement (SCENARIO_ASSUMED), the retained schedule total."""
    slug = _canon(program_slug)
    if not slug:
        return ScenarioFacts(amounts={})
    rows = list(rows)
    have = frozenset(evidenced or ())
    stated = dict(amount_facts or {})
    placement, basis = principal_photography_placement(rows, jurisdiction_code, primary_jurisdiction)
    interval = _share_interval(jurisdiction_code, placement, stated)
    prov_place = PROVENANCE_SCENARIO_ASSUMED if placement in ("FULL", "NONE") else PROVENANCE_LOCALITY_RESOLVED
    place_basis = basis if placement in ("FULL", "NONE") else f"explicit locations with exact schedule days put {interval[0]:.1%} to {interval[1]:.1%} of the shoot in {jurisdiction_code}" if interval else basis
    true_facts: set[str] = set()
    refuted_facts: set[str] = set()
    amounts: dict[str, float] = {}
    derived: list[DerivedFact] = []

    def settle(key: str, state: bool | None, prov: str, why: str) -> None:
        if state is None or key in have or refuted(key) in have or key in true_facts or key in refuted_facts:
            return
        (true_facts if state else refuted_facts).add(key)
        derived.append(DerivedFact(key, state, prov, why))

    for rule in SHARE_RULES:
        if rule.program_slug == slug and rule.jurisdiction_code == jurisdiction_code:
            key = (SCENARIO_SHARE_PREFIX + rule.fact_key) if rule.is_share_gate else rule.fact_key
            st = _decide(interval, rule.min_share)
            settle(key, st, prov_place, f"{place_basis}, so the {rule.min_share:.0%} filming test is {'met' if st else 'not met'}. {rule.authority}")

    for rule in SPEND_SHARE_RULES:
        if rule.program_slug != slug or rule.jurisdiction_code != jurisdiction_code:
            continue
        pool = [(j, float(a)) for j, a, c, _ in (tuple(r) + ("",) * (4 - len(r)) for r in rows) if rule.components is None or c in rule.components]
        total_amt = sum(a for _, a in pool)
        if total_amt <= 0:
            continue
        inside = sum(a for j, a in pool if j == jurisdiction_code)
        unlocated = sum(a for j, a in pool if _is_parent(j, jurisdiction_code))                 # parent-coded (federal-layer) rows do not say where the cost is spent
        lo, hi = inside / total_amt, (inside + unlocated) / total_amt
        met = _decide((lo, hi), rule.min_share)
        if met is not None:
            share_txt = f"{lo:.1%}" if lo == hi else f"{lo:.1%} to {hi:.1%}"
            settle(rule.fact_key, met, PROVENANCE_SCENARIO_ASSUMED,
                   f"the scenario's allocation puts {share_txt} of {'the budget' if rule.components is None else 'postproduction'} in {jurisdiction_code} (needs {rule.min_share:.0%}), so the requirement is {'met' if met else 'not met'} in this scenario. {rule.authority}")

    schedule_total = stated.get(SCHEDULE_TOTAL_DAYS_FACT)
    if schedule_total is not None and schedule_total > 0:
        for rule in DAY_RULES:
            if slug not in rule.program_slugs or rule.jurisdiction_code != jurisdiction_code:
                continue
            if rule.total_fact and rule.total_fact not in stated:
                amounts[rule.total_fact] = float(schedule_total)
                derived.append(DerivedFact(rule.total_fact, float(schedule_total), PROVENANCE_SCHEDULE_DERIVED,
                                           f"the retained schedule's {schedule_total:g} principal-photography days. {rule.authority}"))
            jd = _jurisdiction_days(jurisdiction_code, placement, stated)
            if jd is not None:
                for k in rule.in_facts:
                    if k not in stated:
                        amounts[k] = jd
                        derived.append(DerivedFact(k, jd, prov_place, f"{place_basis}: {jd:g} of the retained schedule's {schedule_total:g} days are in {jurisdiction_code}. {rule.authority}"))

    jd = _jurisdiction_days(jurisdiction_code, placement, stated)
    for pred in PREDICATES_FOR(slug, jurisdiction_code):
        state, day_count = _predicate_state(pred, placement, stated, jd)
        if pred.fact_key and state is not None:
            settle(pred.fact_key, state, PROVENANCE_LOCALITY_RESOLVED if stated.get(f"{LOC}n:{jurisdiction_code}") else prov_place,
                   f"explicit location(s) in {jurisdiction_code} ({pred.label}) resolve this: {'met' if state else 'not met'}")
        if pred.day_fact and day_count is not None and pred.day_fact not in stated and pred.day_fact not in amounts:
            amounts[pred.day_fact] = day_count
            derived.append(DerivedFact(pred.day_fact, day_count, PROVENANCE_LOCALITY_RESOLVED, f"{day_count:g} exact schedule days at locations resolved as {pred.label}; never derived from dollars"))
    return ScenarioFacts(frozenset(true_facts), frozenset(refuted_facts), amounts, tuple(derived))


def PREDICATES_FOR(slug: str, jurisdiction_code: str):
    from app.calculators.locality import PREDICATES
    return [p for p in PREDICATES if p.jurisdiction == jurisdiction_code and slug in PREDICATE_PROGRAMS.get(p.key, ())]


def apply_scenario_facts(evidenced: frozenset | None, amount_facts: Mapping | None, sf: ScenarioFacts) -> tuple[frozenset, dict]:
    """Merge a ScenarioFacts into a component's fact sets without ever overwriting an established fact."""
    ev = frozenset(evidenced or ()) | sf.evidence_tokens()
    am = dict(amount_facts or {})
    for k, v in (sf.amounts or {}).items():
        am.setdefault(k, v)
    return ev, am
