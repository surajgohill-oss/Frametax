"""NA-RECONCILIATION-24: the resolved facts a priced structure actually used are persisted with its generation and served exactly as retained; a later producer edit stales the generation through the existing
fingerprint and opening the stale result stays read-only. Isolated synthetic project only (no real production is read or evaluated)."""
from __future__ import annotations

import uuid

import pytest

from app.services import canonical_evaluation as ce
from app.services import ny_producer_facts as npf
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

MO = "us_mo_motion_media_production_tax_credit"
LINES = (("1000", "CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_resident_labor", "btl", 1_400_000.0), ("3200", "EQUIPMENT", "btl_equipment_rental", "btl", 700_000.0))


async def _mo_structure(db, pid):
    cands = [e for e in await served_structures(db, pid) if e["program_slugs"] == [MO] and e["structure_type"] == "full_relocation"]
    return cands[0] if cands else None


@pytest.mark.asyncio
async def test_the_generation_retains_the_resolved_facts_with_provenance_scope_and_pricing_effect():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        await npf.write_ny_program_facts(db, project_id, evidenced={"mo_script_markets_missouri_confirmed": False, "mo_three_departments_missouri_hires_confirmed": True})
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE"
        entry = await _mo_structure(db, pid)
        assert entry is not None, "the isolated fixture surfaces the Missouri full relocation"
        facts = {r["fact_key"]: r for r in entry["resolved_facts"]}
        filmed = facts["mo_filmed_50pct_in_missouri_confirmed"]
        assert (filmed["state"], filmed["provenance"]) == ("TRUE", "SCENARIO_ASSUMED") and "ALL of its principal photography" in filmed["basis"]
        assert filmed["scope"]["jurisdiction"] == "US-MO" and filmed["scope"]["program"] == MO and "+5 points" in filmed["effect"]
        hires = facts["mo_three_departments_missouri_hires_confirmed"]
        script = facts["mo_script_markets_missouri_confirmed"]
        assert (hires["state"], hires["provenance"]) == ("TRUE", "PRODUCER_STATED")
        assert (script["state"], script["provenance"]) == ("FALSE", "PRODUCER_STATED") and "failed treatment" in script["basis"]
        county = facts["mo_second_third_fourth_class_county_confirmed"]
        assert (county["state"], county["provenance"], county["value"]) == ("UNKNOWN", "UNKNOWN", None) and "+2 points" in county["effect"], "Unknown is retained with its effect"
        assert not any(r["fact_key"].startswith("ca_bc_") for r in entry["resolved_facts"]), "only the facts of the structure's own programs are recorded"


@pytest.mark.asyncio
async def test_a_producer_edit_stales_the_generation_and_opening_the_stale_result_is_read_only_and_serves_the_retained_facts():
    from app.services.canonical_evaluation import current_generation_fingerprint
    from app.services.canonical_production_view import build_production_and_structures
    from sqlalchemy import func, select
    from app.models.production import EvaluationGenerationSummary
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        await ce.evaluate_project(db, project_id)

        async def generations():
            return (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary).where(EvaluationGenerationSummary.project_id == project_id))).scalar_one()

        before = await _mo_structure(db, pid)
        fp = await current_generation_fingerprint(db, project_id)
        await npf.write_ny_program_facts(db, project_id, evidenced={"mo_second_third_fourth_class_county_confirmed": True})
        assert await current_generation_fingerprint(db, project_id) != fp, "a later producer edit stales the generation through the existing fingerprint"
        n = await generations()
        db.expunge_all()
        view = await build_production_and_structures(db, project_id, allow_retained=True)        # opening: read-only (the retained-only guard)
        assert await generations() == n, "opening a stale result never evaluates"
        assert view["production"]["evaluation_freshness"] == "STALE"
        retained = next(e for e in view["structures"]["allocated_structures"]["structures"] if e["structure_id"] == before["structure_id"])
        county = {r["fact_key"]: r for r in retained["resolved_facts"]}["mo_second_third_fourth_class_county_confirmed"]
        assert county["state"] == "UNKNOWN", "the retained generation still shows what was resolved when it was priced; the new edit appears only after a re-evaluation"
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == n + 1
        after = await _mo_structure(db, pid)
        assert {r["fact_key"]: r for r in after["resolved_facts"]}["mo_second_third_fourth_class_county_confirmed"]["state"] == "TRUE"


@pytest.mark.asyncio
async def test_a_same_jurisdiction_stack_persists_the_same_resolved_facts_as_its_standalone_member():
    """NA-RECONCILIATION-25: the BC production services credit priced alone and inside the BC + federal PSTC stack resolves and records identical facts (the stack reuses the member's pricing and carries its records)."""
    from app.models.production_requirement import ProductionAssumption
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="CA-BC", lines=LINES)
        project_id = uuid.UUID(pid)
        db.add(ProductionAssumption(id=uuid.uuid4(), project_id=project_id, assumption_key="intended_shoot_days", value="20", value_type="number", evidence_state="ACTUAL"))
        await db.flush()
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE"
        structures = await served_structures(db, pid)
        alone = next(e for e in structures if e["program_slugs"] == ["ca_bc_pstc"] and e["structure_type"] in ("single_country", "full_relocation"))
        stack = next((e for e in structures if sorted(e["program_slugs"]) == ["ca_bc_pstc", "ca_federal_pstc"]), None)
        assert stack is not None, "the isolated fixture surfaces the BC + federal PSTC same-jurisdiction stack"

        def mine(entry):
            return {r["fact_key"]: (r["state"], r["provenance"], r["value"]) for r in entry["resolved_facts"] if r["scope"]["program"] == "ca_bc_pstc"}

        assert mine(alone), "the standalone structure persists its resolved facts"
        assert mine(alone) == mine(stack), "the stack carries exactly the facts its member's pricing used"
        assert mine(alone)["ca_bc_principal_photography_days_in_bc"] == ("VALUE", "SCENARIO_ASSUMED", 20.0), "schedule-derived BC days for a full BC placement"
