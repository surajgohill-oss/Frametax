"""CLAUDE_GENERIC_STRUCTURAL_DISCOVERY_FINAL_COMPLETION, labour-basis pass.

Canonical, line-level qualification model for CPTC (`ca_federal_cptc`) and
PSTC (`ca_federal_pstc`) qualified-labour derivation. Replaces treating
ATL_DIRECTOR/ATL_WRITER/ATL_PRODUCER/ATL_CAST as qualifying by
spend_category alone -- that is the confirmed defect this module fixes.

Scope: Canadian federal CPTC/PSTC ONLY, per explicit instruction not to
research or model any other program this pass. Every substantive rule
below is sourced directly from the three official primary sources fetched
and quoted this workstream (never extrapolated to a rule not actually
read):

  [CPTC-GUIDE]  canada.ca CAVCO CPTC application guidelines
  [T1131]       canada.ca CRA Guide T1131 (CPTC)
  [PSTC-GUIDE]  canada.ca CAVCO PSTC application guidelines

Where a nuance was NOT found in the fetched text (e.g. whether CPTC's own
labour-expenditure definition gates on an individual's residency the way
PSTC's does), this module does NOT assume either answer -- see
`_CPTC_INDIVIDUAL_RESIDENCY_NOTE` below. Structured Unknowns over
guesses, matching this codebase's own stated engineering principle.

Line-level facts are ProjectFact rows keyed
`"line_fact:{line_id}:{field}"` -- an extension of ProjectFact's existing
extensible key/value shape (see its own docstring: "does not need a
migration every time a new fact type is needed"), never a schema
migration to BudgetLineItem itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LINE_FACT_PREFIX = "line_fact:"

# ---- Line-fact field names (all optional; absence is a genuine gap) ----
FIELD_ROLE = "role"                          # "director" | "writer" | "producer" | "cast" | "other"
FIELD_CANADIAN_STATUS = "canadian_status"    # "resident_citizen" | "resident_pr" | "nonresident"
FIELD_SERVICE_LOCATION = "service_location"  # "in_canada" | "outside_canada"
FIELD_PAYEE_TYPE = "payee_type"
# "employee" | "individual_contractor" | "loan_out_corp" | "personal_service_corp"
# | "partnership" | "non_taxable_canadian_corp" | "foreign_corp"
FIELD_PAYMENT_STATUS = "payment_status"      # "paid" | "payable" | "deferred" | "contingent"
FIELD_LOOK_THROUGH_WAGES_USD = "look_through_wages_usd"
# [T1131] lines 603/605/606/607: for a payee with its own employees, only
# the wages/salary PAID TO THOSE EMPLOYEES for the work counts -- never
# the contractor/corporation's own markup or profit element.
FIELD_PSC_PROFIT_ELEMENT_ELIGIBLE = "psc_profit_element_eligible"
# [T1131] line 606: "If [a solely-owned service corporation's] activities
# ... consist principally (more than 50%) of the provision of the
# shareholder's services," remuneration for the shareholder's OWN
# services may include a profit element (look-through does not apply to
# that portion). Must be an explicit, evidenced fact -- never assumed.
FIELD_ASSISTANCE_USD = "assistance_usd"
# [T1131] line 423 / [CPTC-GUIDE]: assistance (grants, provincial tax
# credits, forgivable loans, etc.) attributable to this line reduces the
# labour expenditure otherwise eligible for CPTC/PSTC purposes.
FIELD_RELATED_PARTY = "related_party"        # "true" | "false"
# Percentage-of-line eligibility (0-100). Three SEPARATE facts, because [PSTC-GUIDE] requires BOTH that the individual be resident in Canada when paid AND that the
# services be personally rendered in Canada, and those are different dollars of one line: a percentage of one condition is never the percentage of the other.
FIELD_RESIDENT_SHARE_PCT = "canadian_resident_share_pct"             # share of the line paid to individuals resident in Canada
FIELD_IN_CANADA_SHARE_PCT = "service_in_canada_share_pct"            # share of the line for services performed in Canada
FIELD_INTERSECTION_SHARE_PCT = "resident_and_in_canada_share_pct"    # share that satisfies BOTH (the qualifying intersection)
SHARE_FIELDS = (FIELD_RESIDENT_SHARE_PCT, FIELD_IN_CANADA_SHARE_PCT, FIELD_INTERSECTION_SHARE_PCT)
#: Lines on which a planning default of 100% (ASSUMED, never stored, never evidence) may stand in for an unstated residency / location share: below-the-line crew and resident labour,
#: the same scenario rule as app.services.scenario_local_labour (BTL labour assigned to a Canadian leg is modeled as locally hired). A line the budget itself classes as
#: non-resident labour, and every above-the-line role, stays separately evidenced.
ASSUMABLE_CATEGORIES = frozenset({"btl_crew_labor", "btl_resident_labor"})

_ELIGIBLE_LABOUR_SPEND_CATEGORIES = frozenset({
    "atl_director", "atl_writer", "atl_producer", "atl_cast",
    "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor",
})

# [CPTC-GUIDE]/[T1131]: "remuneration paid to non-taxable Canadian
# corporations and foreign corporations should not be included" (T1131,
# lines 605/606 exclusion note).
_EXCLUDED_PAYEE_TYPES = frozenset({"non_taxable_canadian_corp", "foreign_corp"})

# Payee types whose eligible amount is capped to the look-through wage
# figure rather than the full invoiced/paid amount (T1131 lines 603/605/606/607).
_LOOK_THROUGH_PAYEE_TYPES = frozenset({
    "loan_out_corp", "personal_service_corp", "partnership", "individual_contractor",
})

# [T1131]: "Salary or wages...do not include: stock options or amounts
# determined with reference to profits or revenues." [CPTC-GUIDE]:
# deferred amounts that are contingent liabilities are excluded from
# production cost "until [they become] a legitimate liability...
# enforceable by the creditor."
_DISQUALIFYING_PAYMENT_STATUSES = frozenset({"deferred", "contingent"})

# Not confirmed in the fetched [CPTC-GUIDE]/[T1131] text: whether CPTC's
# own labour-expenditure definition itself gates on an individual payee's
# Canadian residency (as opposed to the project-level CAVCO Canadian-
# content certification, which is a separate points-test on the
# PRODUCTION, not a per-line labour-expenditure eligibility rule per the
# text actually fetched). PSTC's guidance explicitly states individuals
# must be "resident in Canada at the time the amount is paid" and
# performing "services personally rendered...in Canada" -- CPTC's own
# guidance, as fetched, states no equivalent individual-residency test
# for its OWN labour-expenditure definition. This module therefore
# applies the residency/service-location gate to PSTC only, and leaves
# CPTC's treatment of a nonresident individual's remuneration governed
# solely by payee-type/look-through/payment-status rules that WERE
# confirmed -- never inventing a CPTC residency gate that was not read.
_CPTC_INDIVIDUAL_RESIDENCY_NOTE = (
    "Not confirmed by the fetched CPTC primary sources; CPTC's own "
    "labour-expenditure definition is not gated on individual residency "
    "in the text read. Do not exclude a CPTC line on residency grounds alone."
)


@dataclass(frozen=True)
class LineLabourFacts:
    line_id: str
    role: str | None = None
    canadian_status: str | None = None
    service_location: str | None = None
    payee_type: str | None = None
    payment_status: str | None = None
    look_through_wages_usd: float | None = None
    psc_profit_element_eligible: bool | None = None
    assistance_usd: float | None = None
    related_party: bool | None = None
    resident_share_pct: float | None = None
    in_canada_share_pct: float | None = None
    intersection_share_pct: float | None = None

    def has_any_fact(self) -> bool:
        return any((
            self.role, self.canadian_status, self.service_location, self.payee_type,
            self.payment_status, self.look_through_wages_usd is not None,
            self.assistance_usd is not None, self.resident_share_pct is not None,
            self.in_canada_share_pct is not None, self.intersection_share_pct is not None,
        ))


@dataclass(frozen=True)
class LineLabourDisposition:
    line_id: str
    program_slug: str
    eligible_usd: float
    excluded_usd: float
    reason: str
    #: "STATED" (every residency/location input is a producer statement), "ASSUMED" (a planning default of 100% stood in for at least one), or "" (no share question on this program).
    share_basis: str = ""
    #: the share of the line that reached the eligible basis (0-100) when the program asked a residency/location question
    eligible_share_pct: float | None = None
    #: PSTC only: the eligible amount if the ASSUMED planning default is applied to every unstated condition. `eligible_usd` is the STATED-evidence figure and is the only one that is priced.
    planning_eligible_usd: float | None = None
    planning_reason: str = ""


@dataclass(frozen=True)
class CanadianLabourBasisResult:
    """Every intermediate figure kept separate and inspectable, per this
    workstream's own explicit requirement -- never collapsed into one
    opaque scalar."""
    raw_atl_amount_usd: dict[str, float]           # by program_slug, sum of ALL eligible-category lines regardless of facts
    potentially_eligible_usd: dict[str, float]      # lines with facts present, before deferral/assistance/cap
    evidenced_eligible_labour_usd: dict[str, float]  # potentially_eligible minus deferred/contingent/excluded-payee/residency-failed
    net_labour_after_assistance_usd: dict[str, float]
    statutory_cap_usd: dict[str, float | None]      # None where no cap was confirmed (PSTC)
    qualified_labour_usd: dict[str, float | None]   # min(net_labour, cap) where cap applies, else net_labour; None if zero evidenced lines
    line_dispositions: list[LineLabourDisposition]
    missing_fact_line_ids: list[str]                # eligible-category lines with NO line-facts at all
    net_production_cost_usd: float
    assumed_line_ids: list[str] = field(default_factory=list)   # PSTC lines on which the ASSUMED planning default differs from the stated-evidence figure
    #: PSTC planning figure: stated evidence plus the ASSUMED 100% default on assumable lines. A planning estimate shown to the producer; it is NEVER priced and never becomes verified entitlement.
    planning_eligible_labour_usd: dict[str, float] = field(default_factory=dict)


def _parse_line_facts(line_id: str, raw: dict[str, str]) -> LineLabourFacts:
    def _f(key: str) -> str | None:
        return raw.get(key)

    def _amt(key: str) -> float | None:
        v = raw.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _b(key: str) -> bool | None:
        v = raw.get(key)
        if v is None:
            return None
        return v.strip().lower() in ("true", "1", "yes")

    return LineLabourFacts(
        line_id=line_id,
        role=_f(FIELD_ROLE),
        canadian_status=_f(FIELD_CANADIAN_STATUS),
        service_location=_f(FIELD_SERVICE_LOCATION),
        payee_type=_f(FIELD_PAYEE_TYPE),
        payment_status=_f(FIELD_PAYMENT_STATUS),
        look_through_wages_usd=_amt(FIELD_LOOK_THROUGH_WAGES_USD),
        psc_profit_element_eligible=_b(FIELD_PSC_PROFIT_ELEMENT_ELIGIBLE),
        assistance_usd=_amt(FIELD_ASSISTANCE_USD),
        related_party=_b(FIELD_RELATED_PARTY),
        resident_share_pct=_amt(FIELD_RESIDENT_SHARE_PCT),
        in_canada_share_pct=_amt(FIELD_IN_CANADA_SHARE_PCT),
        intersection_share_pct=_amt(FIELD_INTERSECTION_SHARE_PCT),
    )


def check_share_consistency(line_id: str, raw: dict[str, str]) -> None:
    """ValueError when the stored + incoming share facts of one line contradict each other. The qualifying intersection can never exceed either condition and can never be smaller than the guaranteed overlap
    (r + s - 100): a producer who states impossible numbers is told, not silently corrected. Nothing is derived or multiplied here."""
    def num(k):
        try:
            v = raw.get(k)
            return None if v in (None, "") else float(v)
        except (TypeError, ValueError):
            return None
    r, s_, i = num(FIELD_RESIDENT_SHARE_PCT), num(FIELD_IN_CANADA_SHARE_PCT), num(FIELD_INTERSECTION_SHARE_PCT)
    if i is None:
        return
    for name, v in ((FIELD_RESIDENT_SHARE_PCT, r), (FIELD_IN_CANADA_SHARE_PCT, s_)):
        if v is not None and i > v + 1e-9:
            raise ValueError(f"line {line_id}: {FIELD_INTERSECTION_SHARE_PCT} ({i:g}%) cannot exceed {name} ({v:g}%): the dollars that satisfy both conditions are part of the dollars that satisfy each")
    if r is not None and s_ is not None and i + 1e-9 < r + s_ - 100.0:
        raise ValueError(f"line {line_id}: {FIELD_INTERSECTION_SHARE_PCT} ({i:g}%) is below the guaranteed overlap of {FIELD_RESIDENT_SHARE_PCT} ({r:g}%) and {FIELD_IN_CANADA_SHARE_PCT} ({s_:g}%), which is {r + s_ - 100:g}%")


def collect_line_facts(fact_rows: list, line_ids: set[str]) -> dict[str, LineLabourFacts]:
    """fact_rows: iterable of objects with .fact_key/.value (ProjectFact
    rows or equivalent). Groups every `line_fact:{line_id}:{field}` row
    by line_id, ignoring rows for line_ids not in this project's budget
    (stale facts from a prior budget version are never silently reused)."""
    raw_by_line: dict[str, dict[str, str]] = {}
    for row in fact_rows:
        key = getattr(row, "fact_key", None)
        if not key or not key.startswith(LINE_FACT_PREFIX):
            continue
        rest = key[len(LINE_FACT_PREFIX):]
        if ":" not in rest:
            continue
        line_id, field_name = rest.split(":", 1)
        if line_id not in line_ids:
            continue
        raw_by_line.setdefault(line_id, {})[field_name] = getattr(row, "value", None)

    return {
        line_id: _parse_line_facts(line_id, raw)
        for line_id, raw in raw_by_line.items()
    }


@dataclass(frozen=True)
class ShareResolution:
    """The PSTC residency AND location test for one line, as a share of the line (0-100). `assumed` marks a result that rests on the planning default; `note` explains every step."""
    eligible_pct: float
    assumed: bool
    note: str
    conflict: bool = False


def _stated_resident_pct(facts: LineLabourFacts) -> float | None:
    if facts.resident_share_pct is not None:
        return facts.resident_share_pct
    if facts.canadian_status in ("resident_citizen", "resident_pr"):
        return 100.0
    if facts.canadian_status == "nonresident":
        return 0.0
    return None


def _stated_in_canada_pct(facts: LineLabourFacts) -> float | None:
    if facts.in_canada_share_pct is not None:
        return facts.in_canada_share_pct
    if facts.service_location == "in_canada":
        return 100.0
    if facts.service_location == "outside_canada":
        return 0.0
    return None


def resolve_pstc_share(facts: LineLabourFacts, *, assume_default: bool) -> ShareResolution:
    """[PSTC-GUIDE] needs the SAME dollars to be paid to a Canadian resident AND for services rendered in Canada. Producer statements always outrank the planning default.
    * an explicit intersection share is used as stated (it cannot exceed either stated share);
    * otherwise both shares must be known (stated, or assumed 100% where `assume_default`); the intersection is then exact only when one share is 0% or 100% (the other share IS the
      intersection); with two partial shares the intersection is NOT invented: the guaranteed overlap max(0, r + s - 100) is the planning floor and the possible range is disclosed.
    The shares are never multiplied and never reduced to their minimum without that basis."""
    r_stated, s_stated = _stated_resident_pct(facts), _stated_in_canada_pct(facts)
    # a producer statement that contradicts another producer statement of the same condition is a conflict, not a choice
    if facts.resident_share_pct is not None and facts.canadian_status == "nonresident" and facts.resident_share_pct > 0:
        return ShareResolution(0.0, False, f"conflict: canadian_status=nonresident but canadian_resident_share_pct={facts.resident_share_pct:g}; nothing is eligible until one is corrected.", True)
    if facts.resident_share_pct is not None and facts.canadian_status in ("resident_citizen", "resident_pr") and facts.resident_share_pct < 100:
        return ShareResolution(0.0, False, f"conflict: canadian_status={facts.canadian_status} but canadian_resident_share_pct={facts.resident_share_pct:g}; nothing is eligible until one is corrected.", True)
    if facts.in_canada_share_pct is not None and facts.service_location == "outside_canada" and facts.in_canada_share_pct > 0:
        return ShareResolution(0.0, False, f"conflict: service_location=outside_canada but service_in_canada_share_pct={facts.in_canada_share_pct:g}; nothing is eligible until one is corrected.", True)
    if facts.in_canada_share_pct is not None and facts.service_location == "in_canada" and facts.in_canada_share_pct < 100:
        return ShareResolution(0.0, False, f"conflict: service_location=in_canada but service_in_canada_share_pct={facts.in_canada_share_pct:g}; nothing is eligible until one is corrected.", True)
    r = r_stated if r_stated is not None else (100.0 if assume_default else None)
    s = s_stated if s_stated is not None else (100.0 if assume_default else None)
    assumed = (r_stated is None and r is not None) or (s_stated is None and s is not None)
    tag = " ASSUMED planning default (not verified): the unstated condition is taken as 100% for this below-the-line labour; set the fact to replace it." if assumed else ""
    i = facts.intersection_share_pct
    if i is not None:
        hi = min(x for x in (r, s) if x is not None) if (r is not None or s is not None) else 100.0
        if i > hi + 1e-9:
            return ShareResolution(0.0, assumed, f"conflict: resident_and_in_canada_share_pct={i:g} exceeds a stated condition share (at most {hi:g}); nothing is eligible until corrected.", True)
        return ShareResolution(i, assumed, f"{i:g}% of the line is stated as both resident in Canada and performed in Canada.{tag}")
    if r is None or s is None:
        miss = "residency" if r is None else "service location"
        return ShareResolution(0.0, False, f"excluded per [PSTC-GUIDE]: the {miss} of this line is not stated (a percentage, or a status/location), and the intersection of residency and service location is not stated; Unknown is never taken as Yes.")
    lo, hi = max(0.0, r + s - 100.0), min(r, s)
    if hi - lo < 1e-9:
        return ShareResolution(lo, assumed, f"{r:g}% resident and {s:g}% performed in Canada: the qualifying intersection is exactly {lo:g}% (one condition covers the whole line or none of it).{tag}")
    return ShareResolution(lo, assumed, (f"{r:g}% resident and {s:g}% performed in Canada, intersection NOT stated: planning floor {lo:g}% (the guaranteed overlap); the qualifying share could be anywhere from {lo:g}% to {hi:g}%. "
                                         f"State resident_and_in_canada_share_pct to settle it.{tag}"))


def _line_eligible_amount(amount_usd: float, facts: LineLabourFacts, *, program_slug: str, assume_default: bool = False) -> tuple[float, str]:
    """Returns (eligible_usd, reason). eligible_usd is always in
    [0, amount_usd]. reason explains any reduction/exclusion for full
    reconstruction -- never a silent zero."""
    if facts.payee_type in _EXCLUDED_PAYEE_TYPES:
        return 0.0, (
            f"payee_type={facts.payee_type!r} excluded per [T1131] lines 605/606: "
            "remuneration paid to non-taxable Canadian corporations and foreign "
            "corporations is not included."
        )

    if facts.payment_status in _DISQUALIFYING_PAYMENT_STATUSES:
        return 0.0, (
            f"payment_status={facts.payment_status!r} excluded per [T1131]/[CPTC-GUIDE]: "
            "deferred contingent-liability amounts and profit/revenue-contingent "
            "remuneration are excluded until they become a real, enforceable liability."
        )

    share_pct, share_basis, share_note = 100.0, "", ""
    if program_slug == "ca_federal_pstc" and (facts.resident_share_pct is not None or facts.in_canada_share_pct is not None or facts.intersection_share_pct is not None or assume_default):
        res = resolve_pstc_share(facts, assume_default=assume_default)
        share_pct, share_basis, share_note = res.eligible_pct, ("ASSUMED" if res.assumed else "STATED"), res.note
        if res.eligible_pct <= 0.0:
            return 0.0, share_note
    elif program_slug == "ca_federal_pstc":
        # [PSTC-GUIDE]: eligibility requires the individual be "resident
        # in Canada at the time the amount is paid" AND the services be
        # "personally rendered...in Canada" -- BOTH must be affirmatively
        # evidenced. Absence of either fact is not the same as a
        # confirmed "yes"; failing closed on missing evidence here (not
        # just on an explicit "nonresident"/"outside_canada" value) is
        # required by this workstream's own "missing facts must fail
        # closed" rule -- this program's test genuinely needs the
        # positive fact, unlike CPTC's (see _CPTC_INDIVIDUAL_RESIDENCY_NOTE).
        if facts.canadian_status != "resident_citizen" and facts.canadian_status != "resident_pr":
            return 0.0, (
                "excluded per [PSTC-GUIDE]: PSTC requires the individual be "
                "'resident in Canada at the time the amount is paid', evidenced "
                f"via canadian_status=resident_citizen|resident_pr (got {facts.canadian_status!r})."
            )
        if facts.service_location != "in_canada":
            return 0.0, (
                "excluded per [PSTC-GUIDE]: PSTC requires services "
                "'personally rendered...in Canada', evidenced via "
                f"service_location=in_canada (got {facts.service_location!r})."
            )

    # Only the share of the line that meets the residency AND location test is the relevant basis; the gross budget line and every other component are untouched. The share scales the
    # line (and the look-through wage figure, which is the payee's wages for the whole line) once; assistance is then deducted once, below.
    factor = share_pct / 100.0
    scaled = amount_usd if share_pct >= 100.0 else round(amount_usd * share_pct / 100.0, 2)
    base = scaled
    if facts.payee_type in _LOOK_THROUGH_PAYEE_TYPES:
        if facts.payee_type == "personal_service_corp" and facts.psc_profit_element_eligible:
            base = scaled  # [T1131] line 606: >50%-personal-services PSC may include a profit element for the owner's own services.
            reason_lt = (
                "full amount allowed per [T1131] line 606: evidenced "
                "psc_profit_element_eligible=true (>50%-personal-services corporation, owner's own services)."
            )
        elif facts.look_through_wages_usd is not None:
            base = min(scaled, facts.look_through_wages_usd if share_pct >= 100.0 else round(facts.look_through_wages_usd * share_pct / 100.0, 2))
            reason_lt = (
                f"look-through cap applied per [T1131] lines 603/605/606/607: only the "
                f"payee's own employees' wages (${facts.look_through_wages_usd:,.2f}) count, "
                "never the contractor/corporation's own markup or profit element."
            )
        else:
            return 0.0, (
                f"payee_type={facts.payee_type!r} requires look_through_wages_usd or an "
                "evidenced psc_profit_element_eligible fact per [T1131] lines 603/605/606/607 "
                "-- missing, so this line's eligible labour cannot be derived and fails closed to $0."
            )
    else:
        reason_lt = "full amount eligible (employee/individual, no look-through cap applies)."

    eligible = max(0.0, min(base, scaled))
    if share_basis:
        reason_lt = f"{share_note} {share_pct:g}% of the line (${scaled:,.2f} of ${amount_usd:,.2f}) is the relevant basis. " + reason_lt
    if facts.assistance_usd and program_slug != "ca_federal_cptc":
        eligible = max(0.0, eligible - facts.assistance_usd)
        reason_lt += f" Reduced by ${facts.assistance_usd:,.2f} line-level assistance."
    elif facts.assistance_usd:
        # CRA RC4164 (T1131 guide): assistance (line 423, including any provincial tax credit) reduces the PRODUCTION COST (line 421), which sets the
        # 60% cap (lines 421-430); line 618 labour expenditure is NOT reduced by it. It is therefore deducted from net production cost in
        # derive_canadian_labour_basis, never from this labour line.
        reason_lt += f" ${facts.assistance_usd:,.2f} line-level assistance reduces net production cost (the 60% cap), not this labour line (T1131 line 423/430)."
    return eligible, reason_lt


def derive_canadian_labour_basis(
    lines: list,  # BudgetLine-like: .line_id, .amount_usd, .spend_category, .is_memo
    fact_rows: list,
    gross_budget_usd: float,
    project_level_assistance_usd: float = 0.0,
    assumable_line_ids: frozenset[str] = frozenset(),
) -> CanadianLabourBasisResult:
    """The canonical CPTC/PSTC labour-basis derivation. Never returns a
    guessed aggregate scalar -- every figure is summed from real,
    evidenced line-level facts, with every exclusion reason recorded."""
    eligible_lines = [
        l for l in lines
        if not l.is_memo and (l.spend_category or "") in _ELIGIBLE_LABOUR_SPEND_CATEGORIES
    ]
    line_ids = {l.line_id for l in eligible_lines}
    facts_by_line = collect_line_facts(fact_rows, line_ids)

    raw_atl = {"ca_federal_cptc": 0.0, "ca_federal_pstc": 0.0}
    potentially_eligible = {"ca_federal_cptc": 0.0, "ca_federal_pstc": 0.0}
    evidenced_eligible = {"ca_federal_cptc": 0.0, "ca_federal_pstc": 0.0}
    dispositions: list[LineLabourDisposition] = []
    missing_fact_line_ids: list[str] = []
    assumed_lines: list[str] = []
    planning_eligible = {"ca_federal_cptc": 0.0, "ca_federal_pstc": 0.0}

    for line in eligible_lines:
        for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
            raw_atl[program_slug] = round(raw_atl[program_slug] + line.amount_usd, 2)

        facts = facts_by_line.get(line.line_id)
        assume = line.line_id in assumable_line_ids and (line.spend_category or "") in ASSUMABLE_CATEGORIES
        has_facts = facts is not None and facts.has_any_fact()
        if not has_facts:
            if line.line_id not in missing_fact_line_ids:
                missing_fact_line_ids.append(line.line_id)
            facts = facts or LineLabourFacts(line_id=line.line_id)
        for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
            plan_usd, plan_reason = None, ""
            if program_slug == "ca_federal_pstc" and assume:
                plan_usd, plan_reason = _line_eligible_amount(line.amount_usd, facts, program_slug=program_slug, assume_default=True)
            if not has_facts:
                dispositions.append(LineLabourDisposition(
                    line_id=line.line_id, program_slug=program_slug, eligible_usd=0.0,
                    excluded_usd=line.amount_usd,
                    reason=(
                        "NO line-level labour facts evidenced (role/canadian_status/service_location/"
                        "payee_type/payment_status) -- fails closed to $0 per this workstream's "
                        "explicit requirement that missing substantive facts never be inferred from "
                        "spend_category alone. Required: ProjectFact rows keyed "
                        f"'line_fact:{line.line_id}:<field>'."
                    ),
                    planning_eligible_usd=plan_usd, planning_reason=plan_reason,
                ))
                if program_slug == "ca_federal_pstc":
                    planning_eligible[program_slug] = round(planning_eligible[program_slug] + (plan_usd or 0.0), 2)
                if plan_usd is not None and plan_usd > 0 and line.line_id not in assumed_lines:
                    assumed_lines.append(line.line_id)
                continue
            potentially_eligible[program_slug] = round(potentially_eligible[program_slug] + line.amount_usd, 2)
            eligible_usd, reason = _line_eligible_amount(line.amount_usd, facts, program_slug=program_slug)
            share_basis, share_pct = "", None
            if program_slug == "ca_federal_pstc" and (facts.resident_share_pct is not None or facts.in_canada_share_pct is not None or facts.intersection_share_pct is not None):
                res = resolve_pstc_share(facts, assume_default=False)
                share_basis, share_pct = "STATED", res.eligible_pct
            if plan_usd is not None and abs(plan_usd - eligible_usd) > 0.004 and line.line_id not in assumed_lines:
                assumed_lines.append(line.line_id)
            evidenced_eligible[program_slug] = round(evidenced_eligible[program_slug] + eligible_usd, 2)
            if program_slug == "ca_federal_pstc":
                planning_eligible[program_slug] = round(planning_eligible[program_slug] + (plan_usd if plan_usd is not None else eligible_usd), 2)
            dispositions.append(LineLabourDisposition(
                line_id=line.line_id, program_slug=program_slug, eligible_usd=eligible_usd,
                excluded_usd=round(line.amount_usd - eligible_usd, 2), reason=reason,
                share_basis=share_basis, eligible_share_pct=share_pct,
                planning_eligible_usd=plan_usd, planning_reason=plan_reason,
            ))

    line_assistance = round(sum(
        (facts_by_line[l.line_id].assistance_usd or 0.0) for l in eligible_lines
        if l.line_id in facts_by_line
    ), 2)
    net_production_cost = round(max(0.0, gross_budget_usd - project_level_assistance_usd - line_assistance), 2)
    # [CPTC-GUIDE]/[T1131]: Amount B = 60% of net production cost after
    # assistance. Qualified labour expenditure = the LESSER of Amount B
    # and cumulative labour expenditure (evidenced_eligible here).
    cptc_cap = round(0.60 * net_production_cost, 2)
    net_labour = dict(evidenced_eligible)  # CPTC: assistance acts through net_production_cost (T1131 line 423 -> 430); PSTC: applied per line above
    statutory_cap = {"ca_federal_cptc": cptc_cap, "ca_federal_pstc": None}  # no PSTC cap confirmed in fetched text

    qualified: dict[str, float | None] = {}
    for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
        if evidenced_eligible[program_slug] <= 0.0:
            qualified[program_slug] = None
            continue
        cap = statutory_cap[program_slug]
        qualified[program_slug] = round(min(net_labour[program_slug], cap), 2) if cap is not None else net_labour[program_slug]

    return CanadianLabourBasisResult(
        raw_atl_amount_usd=raw_atl,
        potentially_eligible_usd=potentially_eligible,
        evidenced_eligible_labour_usd=evidenced_eligible,
        net_labour_after_assistance_usd=net_labour,
        statutory_cap_usd=statutory_cap,
        qualified_labour_usd=qualified,
        line_dispositions=dispositions,
        missing_fact_line_ids=missing_fact_line_ids,
        net_production_cost_usd=net_production_cost,
        assumed_line_ids=assumed_lines,
        planning_eligible_labour_usd=planning_eligible,
    )


def to_amount_facts(result: CanadianLabourBasisResult) -> dict[str, float]:
    """Only emits a key when a real, evidenced, non-zero qualified amount
    exists -- never a fabricated 0.0 standing in for 'no evidence', which
    would let the amount_fact_min>0 gate silently treat absence as a
    real, confirmed zero rather than a missing-fact condition."""
    out = {}
    for slug, val in result.qualified_labour_usd.items():
        if val is not None and val > 0:
            out[f"{slug}_qualified_labour_usd"] = val
    return out
