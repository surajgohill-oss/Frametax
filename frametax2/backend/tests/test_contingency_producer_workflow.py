"""Contingency producer-input workflow on isolated synthetic records: Unknown versus stated utilization, the deployment plan API (validation, destination category read from the budget,
round trip, clearing back to NOT_STATED), the evaluation fingerprint, and that contingency is applied ONCE: the Use % moves the planned cost (NPC) by the undeployed reserve and never the
qualifying spend; a deployment moves the destination category's qualifying spend and never the planned cost. No real project is read or written."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.v1.cineglobe import (
    ContingencyDeploymentsBody, ProjectAssumptions, get_project_contingency_deployments, post_project_assumptions, post_project_contingency_deployments)
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

pytestmark = pytest.mark.asyncio

LINES = (("1000", "ABOVE THE LINE CAST", "atl_cast", "atl", 500_000.0), ("3100", "CREW", "btl_crew_labor", "btl", 800_000.0),
         ("8300", "CONTINGENCY", "contingency", "other", 100_000.0))


def _entry(amount, account="3100", category="btl_crew_labor"):
    return {"destination_account_code": account, "destination_spend_category": category, "amount_usd": amount}


async def _inputs(db, pid):
    from app.services.canonical_project_economics import build_project_economic_inputs
    return (await build_project_economic_inputs(db, pid)).inputs


async def _baseline(db, pid):
    """(NPC, qualifying spend) of the priced baseline of a fresh evaluation of the project's CURRENT inputs."""
    from app.services import canonical_evaluation as ce
    await ce.evaluate_project(db, pid)
    base = next(e for e in await served_structures(db, pid) if e.get("is_baseline") and e["candidate_status"] == "PRICED")
    npc = base.get("npc_with_adjustments_usd", base.get("npc_verified_usd"))
    return float(npc), sum(float(s.get("qpe_usd") or 0.0) for s in base.get("segments", []))


async def test_unknown_versus_stated_utilization_round_trips_and_a_cleared_value_returns_to_the_original_fingerprint():
    from app.services import canonical_evaluation as ce
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-GA")
        original = await ce.current_generation_fingerprint(db, pid)
        assert (await _inputs(db, pid)).contingency_expected_utilization_pct is None, "unknown, not 0% or 100%"
        plan = await get_project_contingency_deployments(pid, db=db)
        assert plan["planning"]["state"] == "NOT_STATED" and plan["planning"]["planned_cost_usd"] == 1_400_000.0

        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": 0}), db)
        stated_zero = await get_project_contingency_deployments(pid, db=db)
        assert stated_zero["expected_utilization_pct"] == 0.0 and stated_zero["planning"]["state"] == "ELECTED"
        assert stated_zero["planning"]["undeployed_reserve_usd"] == 100_000.0 and stated_zero["planning"]["planned_cost_usd"] == 1_300_000.0
        assert await ce.current_generation_fingerprint(db, pid) != original, "a stated 0% is a different input from unknown"

        with pytest.raises(HTTPException) as bad:
            await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": 150}), db)
        assert bad.value.status_code == 400
        assert (await get_project_contingency_deployments(pid, db=db))["expected_utilization_pct"] == 0.0, "a refused value changes nothing"

        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": None}), db)
        cleared = await get_project_contingency_deployments(pid, db=db)
        assert cleared["planning"]["state"] == "NOT_STATED" and cleared["expected_utilization_pct"] is None
        assert await ce.current_generation_fingerprint(db, pid) == original, "Reset returns to unknown and the original generation"


async def test_the_deployment_plan_api_validates_against_the_budget_round_trips_and_clears_to_not_stated():
    from app.services import canonical_evaluation as ce
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-GA")
        original = await ce.current_generation_fingerprint(db, pid)
        plan = await get_project_contingency_deployments(pid, db=db)
        assert plan["state"] == "NOT_STATED" and len(plan["accounts"]) == 1
        assert {k: plan["accounts"][0][k] for k in ("account_code", "reserve_usd", "deployed_usd", "undeployed_usd", "deployments")} == {
            "account_code": "8300", "reserve_usd": 100_000.0, "deployed_usd": 0.0, "undeployed_usd": 100_000.0, "deployments": []}
        offered = {d["account_code"]: d["spend_category"] for d in plan["destinations"]}
        assert offered.get("3100") == "btl_crew_labor" and "8300" not in offered, "a contingency account is never a destination"

        for bad in ({"9999": [_entry(10.0)]}, {"8300": [_entry(120_000.0)]}, {"8300": [_entry(60_000.0), _entry(50_000.0)]}, {"8300": [_entry(0)]}, {"8300": [_entry(-5)]},
                    {"8300": [_entry(10.0, account="8300")]}, {"8300": [_entry(10.0, account="0000")]}, {"8300": [{"destination_account_code": "3100", "amount_usd": "10"}]},
                    {"8300": "x"}):
            with pytest.raises(HTTPException) as refused:
                await post_project_contingency_deployments(pid, ContingencyDeploymentsBody.model_construct(deployments=bad), db=db)
            assert refused.value.status_code == 400, bad
        assert (await get_project_contingency_deployments(pid, db=db))["state"] == "NOT_STATED", "a refused plan writes nothing"
        assert await ce.current_generation_fingerprint(db, pid) == original

        saved = await post_project_contingency_deployments(
            pid, ContingencyDeploymentsBody(deployments={"8300": [_entry(40_000.0, category="atl_cast")]}), db=db)    # a wrong client category is ignored
        assert saved["state"] == "STATED" and saved["accounts"][0]["deployed_usd"] == 40_000.0 and saved["accounts"][0]["undeployed_usd"] == 60_000.0
        assert saved["accounts"][0]["deployments"][0]["destination_spend_category"] == "btl_crew_labor", "the category comes from the budget line"
        assert (await get_project_contingency_deployments(pid, db=db)) == saved, "reload returns what was saved"
        assert await ce.current_generation_fingerprint(db, pid) != original
        inputs = await _inputs(db, pid)
        assert inputs.gross_budget_usd == 1_400_000.0 and inputs.contingency_reserve_usd == 100_000.0

        cleared = await post_project_contingency_deployments(pid, ContingencyDeploymentsBody(deployments=None), db=db)
        assert cleared["state"] == "NOT_STATED" and cleared["accounts"][0]["deployments"] == []
        assert await ce.current_generation_fingerprint(db, pid) == original


async def test_contingency_is_applied_once_the_percentage_moves_planned_cost_and_a_deployment_moves_only_qualifying_spend():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-GA")
        npc_none, qpe_none = await _baseline(db, pid)

        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": 50}), db)
        npc_half, qpe_half = await _baseline(db, pid)
        assert qpe_half == pytest.approx(qpe_none), "the election alone proves no eligible expenditure"
        assert npc_none - npc_half == pytest.approx(50_000.0, abs=0.01), "the undeployed reserve (50% of 100,000) leaves the planned cost exactly once"

        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": None}), db)
        await post_project_contingency_deployments(pid, ContingencyDeploymentsBody(deployments={"8300": [_entry(40_000.0)]}), db=db)
        npc_dep, qpe_dep = await _baseline(db, pid)
        assert qpe_dep == pytest.approx(qpe_none + 40_000.0), "the deployed amount qualifies under the destination category"
        planning = (await get_project_contingency_deployments(pid, db=db))["planning"]
        assert planning["state"] == "NOT_STATED" and planning["planned_cost_usd"] == 1_400_000.0, "a deployment does not change the planned cost"

        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": 50}), db)
        npc_both, qpe_both = await _baseline(db, pid)
        assert qpe_both == pytest.approx(qpe_dep), "adding the election does not move the qualifying spend again"
        assert npc_dep - npc_both == pytest.approx(50_000.0, abs=0.01), "the same undeployed reserve is removed once, with or without a deployment"
        both = (await get_project_contingency_deployments(pid, db=db))["planning"]
        assert both["planned_cost_usd"] == 1_350_000.0 and both["undeployed_reserve_usd"] == 50_000.0
