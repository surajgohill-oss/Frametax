"""Durable producer-stated New York program facts (backend write/read path).

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


async def write_ny_program_facts(session: AsyncSession, project_id, *, evidenced: dict | None = None,
                                 payees: list[dict] | None = None, uplift_basis: list[dict] | None = None) -> dict:
    """Validate and persist producer-stated NY facts. `evidenced`: {fact id: true|null} (null clears -> Unknown).
    `payees`: [{line_id, payee_id, compensation_complete}] (payee_id null clears). `uplift_basis`: [{program, uplift, line_id,
    amount_usd}] (amount_usd null clears). Raises ValueError with the reason on any invalid entry; nothing is written then."""
    from app.data.program_rate_rules import SUBSET_UPLIFT_RULES
    evidenced, payees, uplift_basis = evidenced or {}, payees or [], uplift_basis or []
    lines = await _project_line_amounts(session, project_id) if (payees or uplift_basis) else {}
    for fid, value in evidenced.items():
        if fid not in NY_EVIDENCED_FACTS:
            raise ValueError(f"'{fid}' is not a settable New York program fact")
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
    for fid, value in evidenced.items():
        await _upsert(session, project_id, EVIDENCED_PREFIX + fid, "true" if value is True else None, "boolean")
    for p in payees:
        lid = str(p["line_id"])
        pid = None if p.get("payee_id") is None else str(p["payee_id"]).strip()
        await _upsert(session, project_id, f"line_fact:{lid}:payee_id", pid, "string")
        await _upsert(session, project_id, f"line_fact:{lid}:payee_compensation_complete",
                      "true" if (pid and p.get("compensation_complete") is True) else None, "boolean")
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
    return {"evidenced": sorted(evidenced), "payee_lines": [str(p["line_id"]) for p in payees], "uplift_lines": [str(u["line_id"]) for u in uplift_basis]}
