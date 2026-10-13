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


def reserve_accounts(budget_lines, spend_category_by_code) -> dict[str, dict]:
    """{contingency account code: {"description", "reserve_usd"}} from the source budget (the same reading parse_contingency_deployments uses)."""
    out: dict[str, dict] = {}
    for line in budget_lines:
        if (line.spend_category or spend_category_by_code.get(line.account_code)) == "contingency":
            cell = out.setdefault(line.account_code, {"description": line.description, "reserve_usd": 0.0})
            cell["reserve_usd"] = round(cell["reserve_usd"] + float(line.amount_usd), 2)
    return out


def destination_options(budget_lines, spend_category_by_code) -> list[dict]:
    """Every non-contingency budget account a deployment may be directed to, with the spend category its own jurisdiction rules price it under."""
    seen: dict[str, dict] = {}
    for line in budget_lines:
        category = line.spend_category or spend_category_by_code.get(line.account_code)
        if not category or category == "contingency" or getattr(line, "is_memo", False):
            continue
        seen.setdefault(line.account_code, {"account_code": line.account_code, "description": line.description, "spend_category": category})
    return sorted(seen.values(), key=lambda d: d["account_code"])


def validate_deployment_request(deployments, budget_lines, spend_category_by_code) -> tuple[dict, list[str]]:
    """Normalize a producer's deployment request against the source budget. The destination category is read from the budget line, never from the caller; every invalid entry is an
    error (the API refuses it) rather than being dropped as parse_contingency_deployments does for a stored fact. None or {} is valid and means 'no deployment stated'."""
    if not deployments:
        return {}, []
    reserves = reserve_accounts(budget_lines, spend_category_by_code)
    destinations = {d["account_code"]: d for d in destination_options(budget_lines, spend_category_by_code)}
    errors: list[str] = []
    out: dict[str, list[dict]] = {}
    if not isinstance(deployments, dict):
        return {}, ["deployments must be an object keyed by contingency account code"]
    for code, entries in deployments.items():
        if code not in reserves:
            errors.append(f"{code} is not a contingency account of this budget")
            continue
        if not isinstance(entries, list):
            errors.append(f"{code}: deployments must be a list")
            continue
        total = 0.0
        clean: list[dict] = []
        for i, entry in enumerate(entries):
            where = f"{code} deployment {i + 1}"
            if not isinstance(entry, dict):
                errors.append(f"{where} is not an object")
                continue
            amount = entry.get("amount_usd")
            if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
                errors.append(f"{where}: amount_usd must be a finite number above zero")
                continue
            destination = destinations.get(str(entry.get("destination_account_code") or ""))
            if destination is None:
                errors.append(f"{where}: destination account {entry.get('destination_account_code')!r} is not a non-contingency account of this budget")
                continue
            total += float(amount)
            clean.append({"destination_account_code": destination["account_code"], "destination_description": destination["description"],
                          "destination_spend_category": destination["spend_category"], "amount_usd": round(float(amount), 2),
                          "note": str(entry.get("note") or "producer-stated deployment")[:300]})
        if total > reserves[code]["reserve_usd"] + 0.005:
            errors.append(f"{code}: deployments total {total:,.2f}, above the {reserves[code]['reserve_usd']:,.2f} reserve")
        elif clean:
            out[code] = clean
    return ({} if errors else out), errors


def deployment_plan_view(inputs) -> dict:
    """The served deployment plan for the producer controls: STATED / NOT_STATED (unknown is not 'zero deployed'), the reserve accounts with deployed and undeployed amounts, and the
    destination accounts offered. ``inputs`` is a CanonicalEconomicInputs."""
    from app.services.canonical_project_economics import contingency_planning_view
    reserves = reserve_accounts(inputs.budget_lines, inputs.spend_category_by_code)
    accounts = []
    for code, cell in sorted(reserves.items()):
        allocation = inputs.contingency_allocations.get(code)
        deployments = [] if allocation is None else [
            {"destination_account_code": d.destination_account_code, "destination_description": d.destination_description,
             "destination_spend_category": d.destination_spend_category, "amount_usd": d.amount_usd, "note": d.note} for d in allocation.deployments]
        deployed = 0.0 if allocation is None else allocation.deployed_amount_usd
        accounts.append({"account_code": code, "description": cell["description"], "reserve_usd": cell["reserve_usd"], "deployed_usd": round(deployed, 2),
                         "undeployed_usd": round(cell["reserve_usd"] - deployed, 2), "deployments": deployments})
    return {
        "state": "STATED" if inputs.contingency_allocations else "NOT_STATED",
        "accounts": accounts, "destinations": destination_options(inputs.budget_lines, inputs.spend_category_by_code),
        "expected_utilization_pct": inputs.contingency_expected_utilization_pct,
        "planning": contingency_planning_view(inputs.gross_budget_usd, inputs.contingency_reserve_usd, inputs.contingency_expected_utilization_pct),
    }
