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

from dataclasses import dataclass

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

    def has_any_fact(self) -> bool:
        return any((
            self.role, self.canadian_status, self.service_location, self.payee_type,
            self.payment_status, self.look_through_wages_usd is not None,
            self.assistance_usd is not None,
        ))


@dataclass(frozen=True)
class LineLabourDisposition:
    line_id: str
    program_slug: str
    eligible_usd: float
    excluded_usd: float
    reason: str


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
    )


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


def _line_eligible_amount(amount_usd: float, facts: LineLabourFacts, *, program_slug: str) -> tuple[float, str]:
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

    if program_slug == "ca_federal_pstc":
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

    base = amount_usd
    if facts.payee_type in _LOOK_THROUGH_PAYEE_TYPES:
        if facts.payee_type == "personal_service_corp" and facts.psc_profit_element_eligible:
            base = amount_usd  # [T1131] line 606: >50%-personal-services PSC may include a profit element for the owner's own services.
            reason_lt = (
                "full amount allowed per [T1131] line 606: evidenced "
                "psc_profit_element_eligible=true (>50%-personal-services corporation, owner's own services)."
            )
        elif facts.look_through_wages_usd is not None:
            base = min(amount_usd, facts.look_through_wages_usd)
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

    eligible = max(0.0, min(base, amount_usd))
    if facts.assistance_usd:
        eligible = max(0.0, eligible - facts.assistance_usd)
        reason_lt += f" Reduced by ${facts.assistance_usd:,.2f} line-level assistance per [T1131] line 423/[CPTC-GUIDE]."
    return eligible, reason_lt


def derive_canadian_labour_basis(
    lines: list,  # BudgetLine-like: .line_id, .amount_usd, .spend_category, .is_memo
    fact_rows: list,
    gross_budget_usd: float,
    project_level_assistance_usd: float = 0.0,
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

    for line in eligible_lines:
        for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
            raw_atl[program_slug] = round(raw_atl[program_slug] + line.amount_usd, 2)

        facts = facts_by_line.get(line.line_id)
        if facts is None or not facts.has_any_fact():
            if line.line_id not in missing_fact_line_ids:
                missing_fact_line_ids.append(line.line_id)
            for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
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
                ))
            continue

        for program_slug in ("ca_federal_cptc", "ca_federal_pstc"):
            potentially_eligible[program_slug] = round(potentially_eligible[program_slug] + line.amount_usd, 2)
            eligible_usd, reason = _line_eligible_amount(line.amount_usd, facts, program_slug=program_slug)
            evidenced_eligible[program_slug] = round(evidenced_eligible[program_slug] + eligible_usd, 2)
            dispositions.append(LineLabourDisposition(
                line_id=line.line_id, program_slug=program_slug, eligible_usd=eligible_usd,
                excluded_usd=round(line.amount_usd - eligible_usd, 2), reason=reason,
            ))

    net_production_cost = round(max(0.0, gross_budget_usd - project_level_assistance_usd), 2)
    # [CPTC-GUIDE]/[T1131]: Amount B = 60% of net production cost after
    # assistance. Qualified labour expenditure = the LESSER of Amount B
    # and cumulative labour expenditure (evidenced_eligible here).
    cptc_cap = round(0.60 * net_production_cost, 2)
    net_labour = dict(evidenced_eligible)  # assistance already applied per-line above
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
