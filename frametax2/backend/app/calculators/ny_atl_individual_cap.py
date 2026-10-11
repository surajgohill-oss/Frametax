"""New York above-the-line per-individual cap ($500,000), applied only where it can lawfully be applied.

Authority (dated): ESD "New York State Film Tax Credit Program Guidelines", April 2025 version (published file
Film-Credit-Guidelines-W-Appendix-20250418.pdf), pp.2 and the glossary, restates the rule introduced for costs on or
after April 1, 2023: salaries of directors, writers, actors, composers and two producers (one executive, one line) qualify
"up to $500,000 per individual" and, collectively, up to 40% of all other qualified costs. The May 2023 guidelines state
the same cap. The statute text displayed on nysenate.gov (Tax Law 24, revision 2025-07-11) states the 40% group limit
and the two-producer limit but no per-individual dollar figure; agency guidance is applied, and the statutory silence is
recorded rather than treated as disproof.

The cap is per INDIVIDUAL, so it is applied only to an identified payee whose applicable compensation is evidenced as
complete. A budget account that aggregates several people, or a payee whose other compensation is not evidenced, is
reported as UNRESOLVED and is never capped or assumed under the cap. Nothing here estimates a payroll split.

Called from qualification_derivation.derive_qualification_register (NY production credit) with facts built from the derived
amount facts below, so the limits reach every priced NY segment."""
from __future__ import annotations

from datetime import date

NY_ATL_INDIVIDUAL_CAP_USD = 500_000.0
NY_ATL_CAP_EFFECTIVE_FROM = date(2023, 4, 1)
NY_ATL_CAP_SOURCE = "ESD Film Tax Credit Program Guidelines (April 2025 version; May 2023 version identical on the cap), effective April 1, 2023"


# ── Qualification integration ──────────────────────────────────────────────────────────────────────────────────────────

ATL_CATEGORIES = frozenset({"atl_writer", "atl_director", "atl_producer", "atl_cast"})
NY_ATL_GROUP_LIMIT_PCT = 0.40
NY_ATL_GROUP_SOURCE = ("Tax Law 24(a)(5) (revision displayed 2025-07-11): aggregate eligible compensation for writers, directors, composers, "
                       "producers and performers 'shall not exceed forty percent of the aggregate sum total of all other qualified production costs'")

#: Derived amount-fact keys carried from input assembly to the segment pricer (numbers only, like the Canadian labour facts).
FACT_PERIOD_APPLIES = "ny_atl_limits_period_applies"     # 1.0 when the dated rule is established for this project's costs
FACT_PAYEE_PREFIX = "ny_atl_payee:"                       # + line_id -> ordinal of an identified payee whose compensation is evidenced complete


def period_applies(*, target_shoot_year: int | None, lifecycle: str | None) -> bool | None:
    """True when the April 1, 2023 rule is established for the project's costs, None when it cannot be established.
    A shoot year after 2023 applies; 2023 straddles the effective date (unknown); an earlier year predates it (False). With no
    shoot year, a project that has not started production (Evaluation / Development) is a prospective plan and applies; one
    already in production or completed with no date stays unknown."""
    if target_shoot_year is not None:
        return True if target_shoot_year > NY_ATL_CAP_EFFECTIVE_FROM.year else (None if target_shoot_year == NY_ATL_CAP_EFFECTIVE_FROM.year else False)
    return True if (lifecycle or "").upper() in ("EVALUATION", "DEVELOPMENT") else None


def payee_amount_facts(fact_rows, line_ids: set[str]) -> dict[str, float]:
    """`ny_atl_payee:<line_id>` -> payee ordinal, only for lines whose ProjectFact rows `line_fact:<line_id>:payee_id` and
    `line_fact:<line_id>:payee_compensation_complete` (= true) both exist. Equal ordinals are the same individual."""
    raw: dict[str, dict[str, str]] = {}
    for row in fact_rows:
        key = getattr(row, "fact_key", "") or ""
        if not key.startswith("line_fact:"):
            continue
        line_id, _, field = key[len("line_fact:"):].partition(":")
        if line_id in line_ids and field in ("payee_id", "payee_compensation_complete"):
            raw.setdefault(line_id, {})[field] = (getattr(row, "value", None) or "").strip()
    ids = {lid: f["payee_id"] for lid, f in raw.items()
           if f.get("payee_id") and f.get("payee_compensation_complete", "").lower() in ("true", "1", "yes")}
    ordinal = {name: float(i + 1) for i, name in enumerate(sorted(set(ids.values())))}
    return {FACT_PAYEE_PREFIX + lid: ordinal[name] for lid, name in ids.items()}


def limits_facts_from_amount_facts(amount_facts) -> dict:
    """ProductionFacts keyword arguments derived from the numeric facts above."""
    amounts = amount_facts or {}
    payees = tuple(sorted((k[len(FACT_PAYEE_PREFIX):], int(v)) for k, v in amounts.items() if k.startswith(FACT_PAYEE_PREFIX)))
    return {"ny_atl_limits_apply": bool(amounts.get(FACT_PERIOD_APPLIES)), "ny_atl_payee_by_line": payees}


def apply_ny_atl_limits(register, category_by_line: dict[str, str], payee_by_line: dict[str, int]):
    """Apply the two statutory/agency ATL limits to one NY production-credit register, in this order:
    1. $500,000 per individual (ESD guidelines) -- EXCLUDED only for an identified payee with complete compensation; an
       account that is not tied to an identified payee and exceeds the figure stays QUALIFIES with an explicit UNRESOLVED note.
    2. 40% of all other qualified costs (Tax Law 24(a)(5)) -- computable from the register itself, so applied definitively,
       pro rata across the remaining qualifying ATL accounts.
    Returns a new register; split accounts keep their line_id so downstream line sums still reconcile."""
    from dataclasses import replace

    from app.calculators.qualification_model import AuthorityBasis, QualificationConfidence, QualificationState

    is_atl = lambda e: e.state == QualificationState.QUALIFIES and category_by_line.get(e.line_id) in ATL_CATEGORIES   # noqa: E731
    atl_idx = [i for i, e in enumerate(register) if is_atl(e)]
    if not atl_idx:
        return list(register)
    cut1: dict[int, float] = {}
    by_payee: dict[int, list[int]] = {}
    for i in atl_idx:
        pid = payee_by_line.get(register[i].line_id)
        if pid is not None:
            by_payee.setdefault(pid, []).append(i)
    for idxs in by_payee.values():
        over = round(sum(register[i].amount_usd for i in idxs) - NY_ATL_INDIVIDUAL_CAP_USD, 2)
        for i in idxs:
            if over <= 0:
                break
            take = round(min(over, register[i].amount_usd), 2)
            cut1[i] = take
            over = round(over - take, 2)
    remaining = {i: round(register[i].amount_usd - cut1.get(i, 0.0), 2) for i in atl_idx}
    others = round(sum(e.amount_usd for i, e in enumerate(register) if e.state == QualificationState.QUALIFIES and i not in remaining), 2)
    atl_total = round(sum(remaining.values()), 2)
    limit = round(NY_ATL_GROUP_LIMIT_PCT * others, 2)
    cut2: dict[int, float] = {}
    if atl_total > limit + 0.005:
        need, left = round(atl_total - limit, 2), None
        order = [i for i in atl_idx if remaining[i] > 0]
        left = need
        for n, i in enumerate(order):
            share = left if n == len(order) - 1 else round(need * remaining[i] / atl_total, 2)
            cut2[i] = round(min(share, remaining[i]), 2)
            left = round(left - cut2[i], 2)
    unresolved_note = (" UNRESOLVED: the $500,000 per-individual cap (ESD Film Tax Credit Program Guidelines, April 2025, effective April 1, 2023) "
                       "cannot be tested because this account is not tied to an identified payee with complete New York compensation; it is "
                       "carried at its qualified amount as a planning figure, not a certified claim.")
    out = []
    for i, e in enumerate(register):
        c1, c2 = cut1.get(i, 0.0), cut2.get(i, 0.0)
        kept = round(e.amount_usd - c1 - c2, 2)
        untested = i in remaining and e.line_id not in payee_by_line and kept > NY_ATL_INDIVIDUAL_CAP_USD
        if not (c1 or c2):
            out.append(replace(e, reason=e.reason + unresolved_note,
                               resolving_evidence=e.resolving_evidence or "Identified payee and complete NY compensation for each individual in this account.")
                       if untested else e)
            continue
        if kept > 0:
            out.append(replace(e, amount_usd=kept, financial_impact_usd=kept,
                               **({"reason": e.reason + unresolved_note,
                                   "resolving_evidence": e.resolving_evidence or "Identified payee and complete NY compensation for each individual in this account."}
                                  if untested else {})))
        for cut, why in ((c1, f"Excluded above the ${NY_ATL_INDIVIDUAL_CAP_USD:,.0f} per-individual cap for an identified payee whose New York "
                               f"compensation is evidenced complete ({NY_ATL_CAP_SOURCE})."),
                         (c2, f"Excluded above the {NY_ATL_GROUP_LIMIT_PCT:.0%}-of-other-qualified-costs group limit on above-the-line compensation "
                               f"({NY_ATL_GROUP_SOURCE}).")):
            if cut > 0:
                out.append(replace(e, amount_usd=cut, financial_impact_usd=cut, state=QualificationState.EXCLUDED,
                                   confidence=QualificationConfidence.HIGH, authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
                                   reason=why, incentive_upside_usd=None, grey_reason=None, resolving_evidence=None))
    return out
