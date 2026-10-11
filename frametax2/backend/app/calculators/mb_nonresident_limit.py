"""Manitoba cost-of-salaries credit: the non-resident salary limit.

Source (Manitoba Film & Music and Manitoba Finance corporate tax credits pages, retrieved 2026-10-11): salary of non-resident employees
cannot exceed 30% of the eligible salaries paid to Manitoba residents when two or more Manitoba residents are trained for each
non-resident employee, or 10% when only one resident is trained.

Primary text: Manitoba Film & Music TC1 Cost of Salaries Tax Credit Guidelines (June 2024), section H: the deeming provision applies only to
TECHNICAL positions (never producers, directors, actors, performers or any above-the-line position), needs at least one Manitoba trainee per
deemed non-resident, and caps eligible non-resident salaries at 30% of total eligible Manitoba salaries (two or more trainees per deemed
non-resident) or 10% (one); the ratio is the production average.

Applied to the accounts the budget itself labels non-resident BTL labour against the other qualifying labour accounts (above-the-line, resident
and generic crew), which are presumed Manitoba residents under the planning scenario: Personal Residency Declarations are a claim follow-up, not
a planning blocker. A non-resident above-the-line account cannot be deemed, but the budget's ATL categories carry no residency label.
The training ratio is a stated producer fact: with 'mb_two_residents_trained_per_nonresident' the 30% limit applies, with
'mb_one_resident_trained_per_nonresident' the 10% limit, and with neither the amount between 10% and 30% is a GREY producer-fact question
(none of it counted) while only the part above 30% is excluded outright. Inert for a relocation scenario that hires BTL labour locally."""
from __future__ import annotations

from dataclasses import replace

NONRESIDENT_STRICT_PCT = 0.10
NONRESIDENT_LOOSE_PCT = 0.30
FACT_TWO_TRAINED = "mb_two_residents_trained_per_nonresident"
FACT_ONE_TRAINED = "mb_one_resident_trained_per_nonresident"
SOURCE = "Manitoba Film & Music / Manitoba Finance cost-of-salaries credit: non-resident salary limited to 30% (two or more residents trained per non-resident) or 10% (one) of eligible resident salaries"


def apply_mb_nonresident_limit(register, category_by_line: dict[str, str], evidenced: frozenset[str]):
    from app.calculators.qualification_model import AuthorityBasis, GreyReason, QualificationConfidence, QualificationState
    Q = QualificationState.QUALIFIES
    nonres = [i for i, e in enumerate(register) if e.state == Q and category_by_line.get(e.line_id) == "btl_nonresident_labor"]
    if not nonres:
        return list(register)
    labour = ("atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor")
    resident = round(sum(e.amount_usd for e in register if e.state == Q and category_by_line.get(e.line_id) in labour), 2)
    total = round(sum(register[i].amount_usd for i in nonres), 2)
    strict, loose = round(NONRESIDENT_STRICT_PCT * resident, 2), round(NONRESIDENT_LOOSE_PCT * resident, 2)
    if FACT_TWO_TRAINED in evidenced:
        allowed, grey_up_to = loose, loose
    elif FACT_ONE_TRAINED in evidenced:
        allowed, grey_up_to = strict, strict
    else:
        allowed, grey_up_to = strict, loose
    excluded_amt = round(max(0.0, total - max(grey_up_to, allowed)), 2)
    grey_amt = round(max(0.0, min(total, grey_up_to) - allowed), 2)
    if excluded_amt <= 0 and grey_amt <= 0:
        return list(register)

    def share(amount, i):
        return round(amount * register[i].amount_usd / total, 2)

    out = []
    done_ex = done_gr = 0.0
    for idx, e in enumerate(register):
        if idx not in nonres:
            out.append(e)
            continue
        last = idx == nonres[-1]
        ex = round(excluded_amt - done_ex, 2) if last else share(excluded_amt, idx)
        gr = round(grey_amt - done_gr, 2) if last else share(grey_amt, idx)
        done_ex, done_gr = round(done_ex + ex, 2), round(done_gr + gr, 2)
        kept = round(e.amount_usd - ex - gr, 2)
        if kept > 0:
            out.append(replace(e, amount_usd=kept, financial_impact_usd=kept))
        if gr > 0:
            out.append(replace(e, amount_usd=gr, financial_impact_usd=gr, state=QualificationState.GREY_AREA_REQUIRES_AUTHORITY, confidence=QualificationConfidence.LOW,
                               authority_basis=AuthorityBasis.FACT_DEPENDENT, grey_reason=GreyReason.MISSING_PRODUCTION_FACT, incentive_upside_usd=None,
                               reason=f"Non-resident salary above 10% of eligible resident salaries qualifies only if two or more Manitoba residents are trained per non-resident ({SOURCE}); the training ratio is not stated.",
                               resolving_evidence="The number of Manitoba residents trained per non-resident employee."))
        if ex > 0:
            out.append(replace(e, amount_usd=ex, financial_impact_usd=ex, state=QualificationState.EXCLUDED, confidence=QualificationConfidence.HIGH,
                               authority_basis=AuthorityBasis.EXPLICIT_STATUTE, grey_reason=None, incentive_upside_usd=None, resolving_evidence=None,
                               reason=f"Excluded above the non-resident salary limit ({SOURCE})."))
    return out
