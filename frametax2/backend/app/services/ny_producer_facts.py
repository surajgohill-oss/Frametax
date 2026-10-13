"""Durable producer-stated program facts for statutory uplifts (New York, Ontario, British Columbia): backend write/read path.

Everything here is a stated PRODUCER fact or planning election stored in the existing ProjectFact table, read back by
canonical_project_economics.build_project_economic_inputs into the fields the evaluation fingerprint already covers
(evidenced_program_facts, amount_facts). Absence is Unknown, never false; nothing here is proof of an incurred expenditure.

This module is the backend path only. The Overview/Inspector controls that call it are a separate, still-pending UI stage."""
from __future__ import annotations

import json
import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact

EVIDENCED_PREFIX = "evidenced_program_fact:"
UPLIFT_BASIS_FACT_KEY = "uplift_basis_subsets"     # one JSON row: {program: {uplift_id: {line_id: amount_usd}}}

#: Producer-stated boolean program facts a caller may set. (fact id, mutually exclusive partner or None)
NY_EVIDENCED_FACTS = {
    "ny_post_facility_outside_mctd": "ny_post_facility_inside_mctd",
    "ny_post_facility_inside_mctd": "ny_post_facility_outside_mctd",
    "ny_all_costs_in_listed_counties": None,
    "ny_majority_principal_photography_days_in_listed_counties": None,
    "ny_scoring_five_musicians_in_state": None,
    "ny_production_plus_10pct_tier": "ny_production_plus_5pct_tier",
    "ny_production_plus_5pct_tier": "ny_production_plus_10pct_tier",
    # Canada (statutory uplifts on a narrower base; each states a zone or producer fact, or a per-account evidenced portion)
    "on_ofttc_first_time_producer": None,
    "on_ofttc_labour_outside_gta": None,
    "bc_labour_in_regional_zone": None,
    "bc_labour_in_distant_location_zone": None,
    "mb_frequent_filming_third_film_in_two_years": None,
    "mb_frequent_filming_principal_owner_declared": None,
    "mb_resident_producer_screen_credit": None,
    "mb_rural_permanent_establishment_35km": None,
    "mb_rural_majority_days_35km": None,
    "mb_production_company_bonus_eligible": None,
    "mb_t4_payroll_below_25pct_stated": None,
    "ab_fttc_30pct_criteria_met": None,
    "ca_cptc_cavco_certified": None,
    "ca_cptc_canadian_controlled_applicant": None,
    "on_opstc_ontario_labour_25pct_confirmed": None,
    "on_ocase_claim_conditions_met": None,
    "ca_nl_part1_registered_before_production": None,
    "us_co_workforce_and_preapproval_met": None,
    "us_az_eligibility_conditions_met": None,
    "mb_two_residents_trained_per_nonresident": "mb_one_resident_trained_per_nonresident",
    "mb_one_resident_trained_per_nonresident": "mb_two_residents_trained_per_nonresident",
}


def expand_uplift_basis(rows) -> tuple[dict[str, float], frozenset[str]]:
    """Stored subsets -> the logical `uplift_basis:<program>:<uplift>:<line id>` amount keys and the SAME keys as evidenced facts
    that allocation_pricing._price_subset_uplifts reads. (The logical key is longer than the 100-character fact_key column, so it
    is stored as one JSON row instead.) A malformed or non-finite amount is dropped, never coerced."""
    amounts: dict[str, float] = {}
    for row in rows:
        if getattr(row, "fact_key", None) != UPLIFT_BASIS_FACT_KEY or not row.value:
            continue
        try:
            data = json.loads(row.value)
        except (TypeError, ValueError):
            continue
        for program, by_uplift in (data or {}).items():
            for uplift, by_line in (by_uplift or {}).items():
                for line_id, amount in (by_line or {}).items():
                    if isinstance(amount, (int, float)) and not isinstance(amount, bool) and math.isfinite(amount) and amount >= 0:
                        amounts[f"uplift_basis:{program}:{uplift}:{line_id}"] = float(amount)
    return amounts, frozenset(amounts)


async def _project_line_amounts(session: AsyncSession, project_id) -> dict[str, float]:
    rows = (await session.execute(
        select(BudgetLineItem.id, BudgetLineItem.amount_usd).join(BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id)
        .where(BudgetDocument.project_id == project_id))).all()
    return {str(i): float(a or 0.0) for i, a in rows}


async def _upsert(session: AsyncSession, project_id, key: str, value: str | None, value_type: str) -> None:
    existing = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == key))).scalar_one_or_none()
    if value is None:
        if existing is not None:
            await session.delete(existing)
        return
    if existing is not None:
        existing.value, existing.value_type = value, value_type
        existing.source_type = ProjectFactSourceType.USER_OVERRIDE.value
        existing.review_status = ReviewStatus.APPROVED.value
    else:
        session.add(ProjectFact(id=uuid.uuid4(), project_id=project_id, fact_key=key, value=value, value_type=value_type,
                                source_type=ProjectFactSourceType.USER_OVERRIDE.value, review_status=ReviewStatus.APPROVED.value))


PRODUCER_ROLES = ("executive", "line", "other")


async def write_ny_program_facts(session: AsyncSession, project_id, *, evidenced: dict | None = None,
                                 payees: list[dict] | None = None, uplift_basis: list[dict] | None = None,
                                 producer_roles: list[dict] | None = None, composer_portions: list[dict] | None = None) -> dict:
    """Validate and persist producer-stated facts. `evidenced`: {fact id: true|null} (null clears -> Unknown). Stating one fact of a
    mutually exclusive pair (inside/outside the commuter district, Production Plus 10%/5% tier) REPLACES the stored partner in the same
    transaction, so two contradictory elections can never be stored; stating both in one request is rejected. `payees`:
    [{line_id, payee_id, compensation_complete}] (payee_id null clears). `producer_roles`: [{line_id, role: executive|line|other|null}].
    `composer_portions`: [{line_id, amount_usd}] -- the part of a music account that is composer compensation (null clears).
    `uplift_basis`: [{program, uplift, line_id, amount_usd}] (amount_usd null clears). Raises ValueError with the reason on any invalid
    entry; nothing is written then."""
    from app.data.program_rate_rules import SUBSET_UPLIFT_RULES
    evidenced, payees, uplift_basis = evidenced or {}, payees or [], uplift_basis or []
    producer_roles, composer_portions = producer_roles or [], composer_portions or []
    lines = await _project_line_amounts(session, project_id) if (payees or uplift_basis or producer_roles or composer_portions) else {}
    for fid, value in evidenced.items():
        if fid not in NY_EVIDENCED_FACTS:
            raise ValueError(f"'{fid}' is not a settable program fact")
        if value not in (True, None):
            raise ValueError(f"'{fid}' accepts true (stated) or null (Unknown); a false is never stored as evidence")
        partner = NY_EVIDENCED_FACTS[fid]
        if value is True and partner and evidenced.get(partner) is True:
            raise ValueError(f"'{fid}' and '{partner}' cannot both be stated")
    for p in payees:
        if str(p.get("line_id")) not in lines:
            raise ValueError(f"payee line {p.get('line_id')!r} is not a line of this project's budget")
        if p.get("payee_id") is not None and not str(p["payee_id"]).strip():
            raise ValueError("payee_id must be a non-empty identifier or null")
        if p.get("payee_type") is not None:
            from app.calculators.per_payee_limits import PAYEE_TYPE_CODES
            if p["payee_type"] not in PAYEE_TYPE_CODES:
                raise ValueError(f"payee_type must be one of {sorted(PAYEE_TYPE_CODES)} or null")
    for r in producer_roles:
        if str(r.get("line_id")) not in lines:
            raise ValueError(f"producer role line {r.get('line_id')!r} is not a line of this project's budget")
        if r.get("role") is not None and r["role"] not in PRODUCER_ROLES:
            raise ValueError(f"producer role must be one of {PRODUCER_ROLES} or null")
    for c in composer_portions:
        if str(c.get("line_id")) not in lines:
            raise ValueError(f"composer line {c.get('line_id')!r} is not a line of this project's budget")
        amount = c.get("amount_usd")
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount)
                                   or amount < 0 or amount > lines[str(c["line_id"])] + 0.005):
            raise ValueError(f"composer portion for line {c['line_id']} must be a finite number within the line's budget amount")
    for u in uplift_basis:
        rule_ids = {r.uplift_id for r in SUBSET_UPLIFT_RULES.get(u.get("program"), ())}
        if u.get("uplift") not in rule_ids:
            raise ValueError(f"unknown uplift {u.get('program')!r}/{u.get('uplift')!r}")
        if str(u.get("line_id")) not in lines:
            raise ValueError(f"uplift line {u.get('line_id')!r} is not a line of this project's budget")
        amount = u.get("amount_usd")
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount)
                                   or amount < 0 or amount > lines[str(u["line_id"])] + 0.005):
            raise ValueError(f"uplift amount for line {u['line_id']} must be a finite number within the line's budget amount")
    replaced: list[str] = []
    for fid, value in evidenced.items():
        partner = NY_EVIDENCED_FACTS[fid]
        if value is True and partner:
            stored = (await session.execute(select(ProjectFact).where(
                ProjectFact.project_id == project_id, ProjectFact.fact_key == EVIDENCED_PREFIX + partner))).scalar_one_or_none()
            if stored is not None:
                await session.delete(stored)       # the producer changed the answer: the contradictory partner is cleared atomically
                replaced.append(partner)
        await _upsert(session, project_id, EVIDENCED_PREFIX + fid, "true" if value is True else None, "boolean")
    for p in payees:
        lid = str(p["line_id"])
        pid = None if p.get("payee_id") is None else str(p["payee_id"]).strip()
        await _upsert(session, project_id, f"line_fact:{lid}:payee_id", pid, "string")
        await _upsert(session, project_id, f"line_fact:{lid}:payee_compensation_complete",
                      "true" if (pid and p.get("compensation_complete") is True) else None, "boolean")
        if "payee_type" in p:
            await _upsert(session, project_id, f"line_fact:{lid}:payee_type", p["payee_type"] if pid else None, "string")
    for r in producer_roles:
        await _upsert(session, project_id, f"line_fact:{str(r['line_id'])}:producer_role", r.get("role"), "string")
    for c in composer_portions:
        amount = c.get("amount_usd")
        await _upsert(session, project_id, f"line_fact:{str(c['line_id'])}:composer_compensation_usd", None if amount is None else repr(float(amount)), "number")
    if uplift_basis:
        row = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == UPLIFT_BASIS_FACT_KEY))).scalar_one_or_none()
        data = json.loads(row.value) if row is not None and row.value else {}
        for u in uplift_basis:
            by_line = data.setdefault(u["program"], {}).setdefault(u["uplift"], {})
            if u.get("amount_usd") is None:
                by_line.pop(str(u["line_id"]), None)
            else:
                by_line[str(u["line_id"])] = float(u["amount_usd"])
        await _upsert(session, project_id, UPLIFT_BASIS_FACT_KEY, json.dumps(data, sort_keys=True), "json")
    await session.flush()
    return {"evidenced": sorted(evidenced), "replaced": replaced, "payee_lines": [str(p["line_id"]) for p in payees],
            "producer_role_lines": [str(r["line_id"]) for r in producer_roles], "composer_lines": [str(c["line_id"]) for c in composer_portions],
            "uplift_lines": [str(u["line_id"]) for u in uplift_basis]}
