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
reported as UNRESOLVED and is never capped or assumed under the cap. Nothing here estimates a payroll split."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

NY_ATL_INDIVIDUAL_CAP_USD = 500_000.0
NY_ATL_CAP_EFFECTIVE_FROM = date(2023, 4, 1)
NY_ATL_CAP_SOURCE = "ESD Film Tax Credit Program Guidelines (April 2025 version; May 2023 version identical on the cap), effective April 1, 2023"


@dataclass(frozen=True)
class AtlPayeeLine:
    line_id: str
    amount_usd: float
    payee_id: str | None = None          # identified individual, or None when the account aggregates/does not name one
    compensation_complete: bool = False  # True only when ALL of this payee's applicable NY compensation is on the evidenced lines


@dataclass(frozen=True)
class AtlCapResult:
    excess_usd_by_line: dict[str, float]     # amount above the cap, by line (only for capped payees)
    capped_payees: dict[str, float]          # payee_id -> total evidenced NY compensation
    unresolved_line_ids: tuple[str, ...]     # lines where the cap could not be decided
    unresolved_usd: float
    applied: bool                            # False when the costs predate the effective date


def apply_ny_atl_individual_cap(lines: list[AtlPayeeLine], *, costs_incurred_on_or_after: date | None) -> AtlCapResult:
    """Excess over $500,000 per identified payee with complete compensation; everything else UNRESOLVED, never guessed.
    A missing/earlier incurred date means the dated rule is not established for these costs, so nothing is applied."""
    unresolved = [l for l in lines if not (l.payee_id and l.compensation_complete)]
    if costs_incurred_on_or_after is None or costs_incurred_on_or_after < NY_ATL_CAP_EFFECTIVE_FROM:
        return AtlCapResult({}, {}, tuple(l.line_id for l in lines), round(sum(l.amount_usd for l in lines), 2), False)
    totals: dict[str, float] = {}
    by_payee: dict[str, list[AtlPayeeLine]] = {}
    for l in lines:
        if l.payee_id and l.compensation_complete:
            totals[l.payee_id] = totals.get(l.payee_id, 0.0) + l.amount_usd
            by_payee.setdefault(l.payee_id, []).append(l)
    excess: dict[str, float] = {}
    for payee, total in totals.items():
        over = round(total - NY_ATL_INDIVIDUAL_CAP_USD, 2)
        if over <= 0:
            continue
        for l in by_payee[payee]:                    # assign the excess to the payee's lines in order, never more than a line holds
            take = round(min(over, l.amount_usd), 2)
            if take > 0:
                excess[l.line_id] = take
                over = round(over - take, 2)
            if over <= 0:
                break
    return AtlCapResult(excess, {p: round(t, 2) for p, t in totals.items()}, tuple(l.line_id for l in unresolved),
                        round(sum(l.amount_usd for l in unresolved), 2), True)
