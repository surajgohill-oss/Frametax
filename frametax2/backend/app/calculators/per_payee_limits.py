"""Per-individual compensation limits for Georgia and Illinois (PROJECT_OPEN_ITEM_RECOVERY F-10), applied to identified payees only.

Primary authority (retrieved 2026-10-11):
- Georgia: Georgia Department of Economic Development, 'Understanding the Georgia Film Tax Credit' (2026-04): 'There is a $500,000 per person, per production
  salary cap for individuals paid by W-2 ("salary"). There is no salary cap for individuals paid via 1099, personal services contract, or loanout; however,
  Georgia income tax must be withheld and remitted for those payments to qualify.' So the cap applies to W-2 employees only; a loan-out / 1099 payee is
  uncapped (its withholding is a claim follow-up, not a planning input).
- Illinois: DCEO Film Production Services Tax Credit FAQs 3 and 6: 'Only wages and employer paid benefits to Illinois residents up to $500,000 per worker',
  and non-resident labour up to $500,000 per worker for up to thirteen non-resident employees other than non-resident actors. The thirteen-position count
  is not evidenced from a budget and is not modeled.
- Massachusetts is NOT a cap: the payroll credit leaves out the salary of any employee paid $1,000,000 or more, but that pay still counts for the
  25% production-expense credit (DOR Directive 07-1; Letter Ruling 06-1), so with payroll and production credits at the same rate the exclusion has no
  value effect and the engine's single 25% rate is unchanged. See the register entry (M.G.L. c.63 s.38T itself is repealed; current text not retrieved).

Like the New York cap, a limit is applied only where it can be: an identified payee whose compensation is evidenced complete (and, for Georgia, who is
stated to be paid by W-2). An account over the limit that is not tied to such a payee stays qualified with an explicit UNRESOLVED note."""
from __future__ import annotations

from dataclasses import dataclass, replace

PERSONNEL_CATEGORIES = frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"})
FACT_PAYEE_TYPE_PREFIX = "payee_type_code:"
PAYEE_TYPE_CODES = {"employee": 1, "individual_contractor": 2, "loan_out_corp": 3, "personal_service_corp": 4, "partnership": 5}
_PAYEE_TYPE_NAMES = {v: k for k, v in PAYEE_TYPE_CODES.items()}


@dataclass(frozen=True)
class PayeeCap:
    cap_usd: float
    capped_payee_types: frozenset[str] | None     # None: every identified individual; otherwise only these stated payee types
    label: str
    source: str


PAYEE_CAPS: dict[str, PayeeCap] = {
    "us_ga_film_credit": PayeeCap(
        500_000.0, frozenset({"employee"}), "$500,000 per person, per production, W-2 salary",
        "Georgia Department of Economic Development, Understanding the Georgia Film Tax Credit (2026-04): no cap for 1099, personal services contract or loan-out payees"),
    "us_co_film_incentive": PayeeCap(
        1_000_000.0, None, "USD 1,000,000 per employee or contractor (per personal service corporation per calendar year)",
        "C.R.S. 24-48.5-114(7)(i) and (j) (official 2024 printout; HB 23-1275, Session Laws 2023 ch. 289, effective 2023-08-07): wages up to one million dollars per employee or contractor, "
        "payments up to one million dollars per calendar year per personal service corporation; any excess is excluded"),
    "us_il_film_production_services_credit": PayeeCap(
        500_000.0, None, "$500,000 per worker (wages and employer-paid benefits)",
        "Illinois DCEO Film Production Services Tax Credit FAQs 3 and 6: resident and non-resident labour up to $500,000 per worker"),
}


def payee_type_amount_facts(raw_by_line: dict[str, dict[str, str]]) -> dict[str, float]:
    return {FACT_PAYEE_TYPE_PREFIX + lid: float(PAYEE_TYPE_CODES[f["payee_type"]])
            for lid, f in raw_by_line.items() if f.get("payee_type") in PAYEE_TYPE_CODES}


def _decided(line_id, payee_by_line, payee_type_by_line, rule) -> bool:
    """True when the cap question is settled for this account: an identified payee and, where the rule depends on payee type, a stated type
    (a stated uncapped type -- a loan-out -- settles it as 'no cap')."""
    if line_id not in payee_by_line:
        return False
    return rule.capped_payee_types is None or _PAYEE_TYPE_NAMES.get(payee_type_by_line.get(line_id)) is not None


def apply_payee_cap(register, category_by_line: dict[str, str], payee_by_line: dict[str, int], payee_type_by_line: dict[str, int], rule: PayeeCap):
    from app.calculators.qualification_model import AuthorityBasis, QualificationConfidence, QualificationState
    Q = QualificationState.QUALIFIES
    members = [i for i, e in enumerate(register) if e.state == Q and category_by_line.get(e.line_id) in PERSONNEL_CATEGORIES]
    cut: dict[int, float] = {}
    by_payee: dict[int, list[int]] = {}
    for i in members:
        lid = register[i].line_id
        pid = payee_by_line.get(lid)
        if pid is None:
            continue
        if rule.capped_payee_types is not None and _PAYEE_TYPE_NAMES.get(payee_type_by_line.get(lid)) not in rule.capped_payee_types:
            continue
        by_payee.setdefault(pid, []).append(i)
    for idxs in by_payee.values():
        over = round(sum(register[i].amount_usd for i in idxs) - rule.cap_usd, 2)
        for i in idxs:
            if over <= 0:
                break
            take = round(min(over, register[i].amount_usd), 2)
            cut[i] = take
            over = round(over - take, 2)
    out = []
    for i, e in enumerate(register):
        c = cut.get(i, 0.0)
        untested = i in members and not c and e.amount_usd > rule.cap_usd and not _decided(e.line_id, payee_by_line, payee_type_by_line, rule)
        if c:
            if e.amount_usd - c > 0:
                out.append(replace(e, amount_usd=round(e.amount_usd - c, 2), financial_impact_usd=round(e.amount_usd - c, 2)))
            out.append(replace(e, amount_usd=c, financial_impact_usd=c, state=QualificationState.EXCLUDED, confidence=QualificationConfidence.HIGH,
                               authority_basis=AuthorityBasis.EXPLICIT_STATUTE, incentive_upside_usd=None, grey_reason=None, resolving_evidence=None,
                               reason=f"Excluded above the {rule.label} for an identified payee whose compensation is evidenced complete ({rule.source})."))
        elif untested:
            out.append(replace(e, reason=e.reason + f" UNRESOLVED: the {rule.label} cannot be tested because this account is not tied to an identified payee with complete "
                                                    "compensation" + (" paid by W-2" if rule.capped_payee_types else "") + "; it is carried at its qualified amount as a planning figure, not a certified claim.",
                               resolving_evidence=e.resolving_evidence or "Identified payee, complete compensation" + (" and payee type (W-2 employee vs loan-out / 1099)" if rule.capped_payee_types else "") + "."))
        else:
            out.append(e)
    return out


# ── Aggregate category cap: Pennsylvania (NA-RECONCILIATION-10) ─────────────────────────────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AggregateCategoryCap:
    cap_usd: float
    categories: frozenset[str]
    label: str
    source: str

#: Pennsylvania Film Production Tax Credit Guidelines (DCED, 10/28/2020), Component A note: "There is a $15 million cap on the aggregate amount of payments eligible for a tax credit for
#: 'above the line' services provided by principal actors in the production of a Film, whether directly or through a 'loan-out' company." The statute (Act 84 of 2016, Article XVII-D,
#: 'qualified film production expense', Appendix A to the Guidelines) is worded more widely: the term "shall not include more than $15,000,000 in the aggregate of compensation paid to
#: individuals or payment made to entities representing an individual for services provided in the production of the film". The administering agency's reading (principal actors) is
#: applied; the wider statutory reading is an OPEN interpretation recorded in the requirements profile. The budget's above-the-line cast account is the proxy for principal actors, so the
#: excluded part is an upper bound where supporting cast sits in the same account; it is an aggregate over the account, not a per-person limit (nothing needs to identify a payee).
AGGREGATE_CATEGORY_CAPS: dict[str, AggregateCategoryCap] = {
    "us_pa_film_production_credit": AggregateCategoryCap(
        15_000_000.0, frozenset({"atl_cast"}), "$15,000,000 aggregate cap on payments for above-the-line services of principal actors, directly or through loan-out companies",
        "Pennsylvania DCED Film Production Tax Credit Guidelines (10/28/2020), Component A note; Act 84 of 2016, Article XVII-D, definition of 'qualified film production expense'"),
}

def apply_aggregate_category_cap(register, category_by_line: dict[str, str], rule: AggregateCategoryCap):
    """Exclude the part of the QUALIFYING amount in ``rule.categories`` that exceeds the aggregate cap (taken from the last accounts first). Accounts outside the categories, and
    every non-qualifying entry, are untouched; at or below the cap the register is returned unchanged."""
    from app.calculators.qualification_model import AuthorityBasis, QualificationConfidence, QualificationState
    Q = QualificationState.QUALIFIES
    members = [i for i, e in enumerate(register) if e.state == Q and category_by_line.get(e.line_id) in rule.categories]
    over = round(sum(register[i].amount_usd for i in members) - rule.cap_usd, 2)
    if over <= 0:
        return list(register)
    cut: dict[int, float] = {}
    for i in reversed(members):
        if over <= 0:
            break
        take = round(min(register[i].amount_usd, over), 2)
        cut[i] = take
        over = round(over - take, 2)
    out = []
    for i, e in enumerate(register):
        c = cut.get(i, 0.0)
        if not c:
            out.append(e)
            continue
        if e.amount_usd - c > 0:
            out.append(replace(e, amount_usd=round(e.amount_usd - c, 2), financial_impact_usd=round(e.amount_usd - c, 2)))
        out.append(replace(e, amount_usd=c, financial_impact_usd=c, state=QualificationState.EXCLUDED, confidence=QualificationConfidence.HIGH,
                           authority_basis=AuthorityBasis.EXPLICIT_STATUTE, incentive_upside_usd=None, grey_reason=None, resolving_evidence=None,
                           reason=f"Excluded above the {rule.label} ({rule.source}). The above-the-line cast account is the proxy for principal actors, so this is an upper bound on the excluded amount; "
                                  "the statute's wider wording (all individuals) is an open interpretation."))
    return out
