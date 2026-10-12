"""Producer-stated contingency deployment: the portion of a budgeted contingency reserve the producer elects to spend in a real destination category.

A budgeted-but-undeployed reserve is not incurred spend; a deployed amount is priced by the jurisdiction's own rules for its DESTINATION category
(calculators/contingency_treatment.py). The deployment is stored as ONE JSON project fact, ``contingency_deployments``:

    {"<contingency account code>": [{"destination_account_code", "destination_description", "destination_spend_category", "amount_usd", "note"}]}

It is a planning input: it never rewrites the original gross or the reserve, and an election of the planned-cost percentage alone proves no eligible
expenditure (the percentage only moves the planned cost once). A malformed, non-finite, non-positive or over-the-reserve entry is dropped, never coerced.
"""
from __future__ import annotations

import json
import math

from app.calculators.contingency_treatment import ContingencyAllocation, ContingencyDeployment, add_deployment

CONTINGENCY_DEPLOYMENTS_FACT_KEY = "contingency_deployments"
_DEPLOYED_BY = "producer-stated project fact"
_DEPLOYED_AT = "producer-stated"


def _clean(entry, remaining: float):
    if not isinstance(entry, dict):
        return None
    amount, category = entry.get("amount_usd"), str(entry.get("destination_spend_category") or "").strip()
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        return None
    if not category or category == "contingency" or amount > remaining + 0.005:
        return None
    return ContingencyDeployment(
        destination_account_code=str(entry.get("destination_account_code") or ""), destination_description=str(entry.get("destination_description") or category),
        destination_spend_category=category, amount_usd=round(float(amount), 2), note=str(entry.get("note") or "producer-stated deployment"),
        deployed_by=_DEPLOYED_BY, deployed_at=_DEPLOYED_AT)


def parse_contingency_deployments(fact_rows, budget_lines, spend_category_by_code) -> dict[str, ContingencyAllocation]:
    """{contingency account code: ContingencyAllocation} from the stored fact, bounded by each reserve's own budgeted amount."""
    raw = next((r.value for r in fact_rows if getattr(r, "fact_key", None) == CONTINGENCY_DEPLOYMENTS_FACT_KEY and r.value), None)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    reserve: dict[str, float] = {}
    description: dict[str, str] = {}
    for line in budget_lines:
        if (line.spend_category or spend_category_by_code.get(line.account_code)) == "contingency":
            reserve[line.account_code] = reserve.get(line.account_code, 0.0) + float(line.amount_usd)
            description.setdefault(line.account_code, line.description)
    out: dict[str, ContingencyAllocation] = {}
    for code, entries in (data or {}).items():
        if code not in reserve or not isinstance(entries, list):
            continue
        allocation = ContingencyAllocation(source_account_code=code, source_description=description[code], original_amount_usd=round(reserve[code], 2))
        for entry in entries:
            deployment = _clean(entry, allocation.undeployed_amount_usd)
            if deployment is not None:
                allocation = add_deployment(allocation, deployment)
        if allocation.deployments:
            out[code] = allocation
    return out


def fingerprint_part(allocations: dict[str, ContingencyAllocation]) -> list:
    return sorted((code, [(d.destination_account_code, d.destination_spend_category, d.amount_usd) for d in a.deployments]) for code, a in allocations.items())


async def write_contingency_deployments(session, project_id, deployments: dict[str, list[dict]] | None) -> dict:
    """Replace the stored deployment plan (None or {} clears it). Returns the accounts written."""
    from app.services.ny_producer_facts import _upsert
    value = json.dumps(deployments, sort_keys=True) if deployments else None
    await _upsert(session, project_id, CONTINGENCY_DEPLOYMENTS_FACT_KEY, value, "json")
    await session.flush()
    return {"accounts": sorted((deployments or {}).keys())}
