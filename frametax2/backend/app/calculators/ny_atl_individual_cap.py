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

import re
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
FACT_COMPOSER_PREFIX = "ny_composer_portion:"             # + line_id -> USD of a music account that is composer compensation (producer-stated)
FACT_PRODUCER_ROLE_PREFIX = "ny_producer_role:"           # + line_id -> 1 executive, 2 line, 3 other (producer-stated)
_ROLE_CODES = {"executive": 1, "line": 2, "other": 3}
_ROLE_NAMES = {v: k for k, v in _ROLE_CODES.items()}

#: Authored source-subaccount descriptions that establish composer compensation inside a music account. Deliberately narrow: a child is
#: composer compensation only when its own description names the composer or composition, and never when it names recording, musicians,
#: licensing, clearance, supervision, libraries or mixing. Anything else is not inferred.
_COMPOSER_CHILD = re.compile(r"\bcomposer\b|\bcomposition\b|\bscore composer\b", re.I)
_NOT_COMPOSER_CHILD = re.compile(r"record|musician|orchestra|licens|clearance|supervis|librar|mix|sync|rights|royalt", re.I)


def period_applies(*, target_shoot_year: int | None, lifecycle: str | None) -> bool | None:
    """True when the April 1, 2023 rule is established for the project's costs, None when it cannot be established.
    A shoot year after 2023 applies; 2023 straddles the effective date (unknown); an earlier year predates it (False). With no
    shoot year, a project that has not started production (Evaluation / Development) is a prospective plan and applies; one
    already in production or completed with no date stays unknown."""
    if target_shoot_year is not None:
        return True if target_shoot_year > NY_ATL_CAP_EFFECTIVE_FROM.year else (None if target_shoot_year == NY_ATL_CAP_EFFECTIVE_FROM.year else False)
    return True if (lifecycle or "").upper() in ("EVALUATION", "DEVELOPMENT") else None


def _line_fact_rows(fact_rows, line_ids: set[str], fields: tuple[str, ...]) -> dict[str, dict[str, str]]:
    raw: dict[str, dict[str, str]] = {}
    for row in fact_rows:
        key = getattr(row, "fact_key", "") or ""
        if not key.startswith("line_fact:"):
            continue
        line_id, _, field = key[len("line_fact:"):].partition(":")
        if line_id in line_ids and field in fields:
            raw.setdefault(line_id, {})[field] = (getattr(row, "value", None) or "").strip()
    return raw


def payee_amount_facts(fact_rows, line_ids: set[str]) -> dict[str, float]:
    """Derived NY amount facts from stated line facts: `ny_atl_payee:<line_id>` -> payee ordinal, only for lines whose rows
    `payee_id` and `payee_compensation_complete` (= true) both exist (equal ordinals are the same individual);
    `ny_composer_portion:<line_id>` -> the stated composer compensation inside a music account; `ny_producer_role:<line_id>` -> role code."""
    raw = _line_fact_rows(fact_rows, line_ids, ("payee_id", "payee_compensation_complete", "composer_compensation_usd", "producer_role"))
    ids = {lid: f["payee_id"] for lid, f in raw.items()
           if f.get("payee_id") and f.get("payee_compensation_complete", "").lower() in ("true", "1", "yes")}
    ordinal = {name: float(i + 1) for i, name in enumerate(sorted(set(ids.values())))}
    out = {FACT_PAYEE_PREFIX + lid: ordinal[name] for lid, name in ids.items()}
    for lid, f in raw.items():
        try:
            c = float(f["composer_compensation_usd"]) if f.get("composer_compensation_usd") else None
        except ValueError:
            c = None
        if c is not None and c == c and c not in (float("inf"), float("-inf")) and c >= 0:
            out[FACT_COMPOSER_PREFIX + lid] = c
        if f.get("producer_role") in _ROLE_CODES:
            out[FACT_PRODUCER_ROLE_PREFIX + lid] = float(_ROLE_CODES[f["producer_role"]])
    return out


def limits_facts_from_amount_facts(amount_facts) -> dict:
    """ProductionFacts keyword arguments derived from the numeric facts above."""
    amounts = amount_facts or {}
    def pairs(prefix, cast):
        return tuple(sorted((k[len(prefix):], cast(v)) for k, v in amounts.items() if k.startswith(prefix)))
    return {"ny_atl_limits_apply": bool(amounts.get(FACT_PERIOD_APPLIES)), "ny_atl_payee_by_line": pairs(FACT_PAYEE_PREFIX, int),
            "ny_atl_composer_by_line": pairs(FACT_COMPOSER_PREFIX, float), "ny_atl_producer_role_by_line": pairs(FACT_PRODUCER_ROLE_PREFIX, int)}


def composer_portion_from_subaccounts(children, line_amount: float) -> float | None:
    """Composer compensation established by the authored source detail of a music account: the sum of children whose own description names
    the composer or composition. Only when the children conserve the account exactly with unique codes; otherwise None (not inferred)."""
    if not children:
        return None
    try:
        amounts = [float(c["amount_usd"]) for c in children]
    except (KeyError, TypeError, ValueError):
        return None
    if any(a != a or a < 0 for a in amounts) or len({c.get("account_code") for c in children}) != len(children) or abs(sum(amounts) - line_amount) > 0.005:
        return None
    total = round(sum(a for a, c in zip(amounts, children) if _COMPOSER_CHILD.search(c.get("description") or "") and not _NOT_COMPOSER_CHILD.search(c.get("description") or "")), 2)
    return total if total > 0 else None


def apply_ny_atl_limits(register, category_by_line: dict[str, str], payee_by_line: dict[str, int], *, composer_by_line=None,
                        role_by_line=None, subaccounts_by_line=None):
    """Apply the statutory/agency compensation-group limits to one NY production-credit register, in this order:
    0. Producers: only one executive and one line producer qualify. A producer account stated as role "other" is EXCLUDED; two different
       identified individuals stated for the same role are a producer-election question (GREY, none counted); an unstated role stays
       qualified with an explicit UNRESOLVED note.
    0b. Composers (Tax Law 24(a)(5) names composers in the group): the composer-compensation part of a MUSIC account -- stated by the
       producer, or established by authored source subaccounts that name the composer -- joins the group; recording, musicians and
       licensing stay ordinary costs. A music account with no such evidence is not capped; it stays visible as UNRESOLVED mixed membership.
    1. $500,000 per individual (ESD guidelines): EXCLUDED only for an identified payee with complete compensation.
    2. 40% of all other qualified costs (Tax Law 24(a)(5)): applied definitively, pro rata, to the group.
    Returns a new register; split accounts keep their line_id so downstream line sums still reconcile."""
    from dataclasses import replace

    from app.calculators.qualification_model import AuthorityBasis, GreyReason, QualificationConfidence, QualificationState

    composer_by_line, role_by_line, subaccounts_by_line = composer_by_line or {}, role_by_line or {}, subaccounts_by_line or {}
    Q = QualificationState.QUALIFIES
    UNRESOLVED_CAP = (" UNRESOLVED: the $500,000 per-individual cap (ESD Film Tax Credit Program Guidelines, April 2025, effective April 1, 2023) "
                      "cannot be tested because this account is not tied to an identified payee with complete New York compensation; it is "
                      "carried at its qualified amount as a planning figure, not a certified claim.")
    EVIDENCE = "Identified payee and complete NY compensation for each individual in this account."

    # entries: [entry, is_group_member]
    entries: list[list] = []
    for e in register:
        cat = category_by_line.get(e.line_id)
        if e.state != Q:
            entries.append([e, False])
        elif cat == "atl_producer":
            role = _ROLE_NAMES.get(role_by_line.get(e.line_id))
            if role == "other":
                entries.append([replace(e, state=QualificationState.EXCLUDED, confidence=QualificationConfidence.HIGH, authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
                                        reason="Excluded: only one executive producer and one line producer salary qualifies (ESD Film Tax Credit Program Guidelines, "
                                               "April 2025, effective April 1, 2023); this producer account is stated as neither.", incentive_upside_usd=None,
                                        grey_reason=None, resolving_evidence=None), False])
            elif role is None:
                entries.append([replace(e, reason=e.reason + " UNRESOLVED: only one executive producer and one line producer qualify; this producer account's role is not stated.",
                                        resolving_evidence=e.resolving_evidence or "Each producer account's role (executive, line or other)."), True])
            else:
                entries.append([e, True])
        elif cat in ATL_CATEGORIES:
            entries.append([e, True])
        elif cat == "music":
            stated = composer_by_line.get(e.line_id)
            portion = stated if stated is not None else composer_portion_from_subaccounts(subaccounts_by_line.get(e.line_id), e.amount_usd)
            if portion is not None and 0 < portion <= e.amount_usd + 0.005:
                portion = min(portion, e.amount_usd)
                entries.append([replace(e, amount_usd=round(portion, 2), financial_impact_usd=round(portion, 2),
                                        reason=e.reason + " Composer compensation within this music account: a member of the Tax Law 24(a)(5) compensation group."), True])
                if e.amount_usd - portion > 0.004:
                    entries.append([replace(e, amount_usd=round(e.amount_usd - portion, 2), financial_impact_usd=round(e.amount_usd - portion, 2)), False])
            else:
                entries.append([replace(e, reason=e.reason + " UNRESOLVED: whether part of this music account is composer compensation (a member of the 40% / $500,000 "
                                                              "compensation group) is not evidenced; it is counted as an ordinary cost, which could overstate the group limit.",
                                        resolving_evidence=e.resolving_evidence or "The composer-compensation portion of this account (producer-stated or authored source subaccounts)."), False])
        else:
            entries.append([e, False])

    # 0. producers stated for the same role as two different individuals: a producer election, none counted
    by_role: dict[int, set[int]] = {}
    for e, member in entries:
        if member and e.state == Q and category_by_line.get(e.line_id) == "atl_producer" and role_by_line.get(e.line_id) in (1, 2):
            pid = payee_by_line.get(e.line_id)
            if pid is not None:
                by_role.setdefault(role_by_line[e.line_id], set()).add(pid)
    contested = {r for r, people in by_role.items() if len(people) > 1}
    for item in entries:
        e, member = item
        if member and e.state == Q and category_by_line.get(e.line_id) == "atl_producer" and role_by_line.get(e.line_id) in contested:
            item[0] = replace(e, state=QualificationState.GREY_AREA_REQUIRES_AUTHORITY, confidence=QualificationConfidence.LOW, authority_basis=AuthorityBasis.FACT_DEPENDENT,
                              grey_reason=GreyReason.REQUIRES_PRODUCER_ELECTION, incentive_upside_usd=None,
                              reason="Two different individuals are stated for the same producer role, but only one executive producer and one line producer qualify "
                                     "(ESD guidelines, April 2025); which individual is the qualifying producer is a producer election, so none is counted.",
                              resolving_evidence="The single individual who is the qualifying " + _ROLE_NAMES[role_by_line[e.line_id]] + " producer.")
            item[1] = False

    members = [i for i, (e, m) in enumerate(entries) if m and e.state == Q]
    if not members:
        return [e for e, _ in entries]
    cut1: dict[int, float] = {}
    by_payee: dict[int, list[int]] = {}
    for i in members:
        pid = payee_by_line.get(entries[i][0].line_id)
        if pid is not None:
            by_payee.setdefault(pid, []).append(i)
    for idxs in by_payee.values():
        over = round(sum(entries[i][0].amount_usd for i in idxs) - NY_ATL_INDIVIDUAL_CAP_USD, 2)
        for i in idxs:
            if over <= 0:
                break
            take = round(min(over, entries[i][0].amount_usd), 2)
            cut1[i] = take
            over = round(over - take, 2)
    remaining = {i: round(entries[i][0].amount_usd - cut1.get(i, 0.0), 2) for i in members}
    others = round(sum(e.amount_usd for i, (e, m) in enumerate(entries) if e.state == Q and i not in remaining), 2)
    group_total = round(sum(remaining.values()), 2)
    limit = round(NY_ATL_GROUP_LIMIT_PCT * others, 2)
    cut2: dict[int, float] = {}
    if group_total > limit + 0.005:
        need = round(group_total - limit, 2)
        order = [i for i in members if remaining[i] > 0]
        left = need
        for n, i in enumerate(order):
            share = left if n == len(order) - 1 else round(need * remaining[i] / group_total, 2)
            cut2[i] = round(min(share, remaining[i]), 2)
            left = round(left - cut2[i], 2)

    out = []
    for i, (e, m) in enumerate(entries):
        c1, c2 = cut1.get(i, 0.0), cut2.get(i, 0.0)
        kept = round(e.amount_usd - c1 - c2, 2)
        untested = i in remaining and e.line_id not in payee_by_line and kept > NY_ATL_INDIVIDUAL_CAP_USD
        if not (c1 or c2):
            out.append(replace(e, reason=e.reason + UNRESOLVED_CAP, resolving_evidence=e.resolving_evidence or EVIDENCE) if untested else e)
            continue
        if kept > 0:
            out.append(replace(e, amount_usd=kept, financial_impact_usd=kept,
                               **({"reason": e.reason + UNRESOLVED_CAP, "resolving_evidence": e.resolving_evidence or EVIDENCE} if untested else {})))
        for cut, why in ((c1, f"Excluded above the ${NY_ATL_INDIVIDUAL_CAP_USD:,.0f} per-individual cap for an identified payee whose New York "
                               f"compensation is evidenced complete ({NY_ATL_CAP_SOURCE})."),
                         (c2, f"Excluded above the {NY_ATL_GROUP_LIMIT_PCT:.0%}-of-other-qualified-costs group limit on above-the-line compensation "
                               f"({NY_ATL_GROUP_SOURCE}).")):
            if cut > 0:
                out.append(replace(e, amount_usd=cut, financial_impact_usd=cut, state=QualificationState.EXCLUDED,
                                   confidence=QualificationConfidence.HIGH, authority_basis=AuthorityBasis.EXPLICIT_STATUTE,
                                   reason=why, incentive_upside_usd=None, grey_reason=None, resolving_evidence=None))
    return out
