"""Producer-stated contingency deployment: stored as one project fact, parsed into ContingencyAllocation objects bounded by the reserve, included in the input
fingerprint, and priced by the DESTINATION category's own rule on every pricing path. DB-free parsing plus one rolled-back synthetic evaluation (isolated database).
The planned-cost election alone proves no eligible expenditure; a deployment moves QPE, never the original gross or the reserve."""
from __future__ import annotations

import json
import types

import pytest

from app.calculators.qualification_derivation import BudgetLine
from app.services.contingency_deployment_facts import CONTINGENCY_DEPLOYMENTS_FACT_KEY, fingerprint_part, parse_contingency_deployments

LINES = [BudgetLine(account_code="3100", description="CREW", amount_usd=800_000.0, spend_category="btl_crew_labor", is_memo=False, line_id="a"),
         BudgetLine(account_code="8300", description="CONTINGENCY", amount_usd=100_000.0, spend_category="contingency", is_memo=False, line_id="b")]
CATS = {"3100": "btl_crew_labor", "8300": "contingency"}


def _rows(payload):
    return [types.SimpleNamespace(fact_key=CONTINGENCY_DEPLOYMENTS_FACT_KEY, value=json.dumps(payload))]


def _entry(amount, category="btl_crew_labor"):
    return {"destination_account_code": "3100", "destination_description": "crew overage", "destination_spend_category": category, "amount_usd": amount}


def test_deployments_are_bounded_by_the_reserve_and_malformed_entries_are_dropped_not_coerced():
    ok = parse_contingency_deployments(_rows({"8300": [_entry(40_000.0), _entry(30_000.0)]}), LINES, CATS)
    assert ok["8300"].deployed_amount_usd == 70_000.0 and ok["8300"].undeployed_amount_usd == 30_000.0
    over = parse_contingency_deployments(_rows({"8300": [_entry(90_000.0), _entry(20_000.0)]}), LINES, CATS)
    assert over["8300"].deployed_amount_usd == 90_000.0, "the second deployment would exceed the reserve and is dropped"
    for bad in (_entry(-5.0), _entry(float("inf")), _entry(10.0, "contingency"), _entry(10.0, ""), {"amount_usd": "10"}, "x"):
        assert parse_contingency_deployments(_rows({"8300": [bad]}), LINES, CATS) == {}
    assert parse_contingency_deployments(_rows({"9999": [_entry(10.0)]}), LINES, CATS) == {}, "an account that is not a contingency line is ignored"
    assert parse_contingency_deployments([], LINES, CATS) == {} and parse_contingency_deployments(_rows({}), LINES, CATS) == {}
    assert fingerprint_part(ok) != fingerprint_part({})


@pytest.mark.asyncio
async def test_a_stored_deployment_changes_the_fingerprint_and_the_priced_qualifying_spend_but_not_gross_or_reserve():
    from app.services import canonical_evaluation as ce
    from app.services.canonical_project_economics import build_project_economic_inputs
    from app.services.contingency_deployment_facts import write_contingency_deployments
    from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

    lines = (("1000", "ABOVE THE LINE CAST", "atl_cast", "atl", 500_000.0), ("3100", "CREW", "btl_crew_labor", "btl", 800_000.0),
             ("8300", "CONTINGENCY", "contingency", "other", 100_000.0))

    async def baseline_qpe(db, pid):
        await ce.evaluate_project(db, pid)
        entries = await served_structures(db, pid)
        base = next(e for e in entries if e.get("is_baseline") and e["candidate_status"] == "PRICED")
        return sum(float(s.get("qpe_usd") or 0.0) for s in base.get("segments", []))

    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=lines, home_code="US-GA")
        before_fp = await ce.current_generation_fingerprint(db, pid)
        plain = await baseline_qpe(db, pid)
        assert (await build_project_economic_inputs(db, pid)).inputs.contingency_allocations == {}
        await write_contingency_deployments(db, pid, {"8300": [_entry(40_000.0)]})
        inputs = (await build_project_economic_inputs(db, pid)).inputs
        assert inputs.contingency_allocations["8300"].deployed_amount_usd == 40_000.0
        assert inputs.gross_budget_usd == 1_400_000.0 and inputs.contingency_reserve_usd == 100_000.0
        assert await ce.current_generation_fingerprint(db, pid) != before_fp
        deployed = await baseline_qpe(db, pid)
    assert deployed == pytest.approx(plain + 40_000.0)
