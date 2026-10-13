"""NA synthetic pipeline controls (2026-10-13): isolated, rolled-back records only. They replace, for North America, the real-production tests that evaluate FVD and delete its stored facts (see the register).

Texas MIIP: the 31% is a band ceiling with no floor, so with no award nothing is guaranteed; the award, the pool period and the resident thresholds (crew and cast at least 35%) gate it; a valid awarded rate (a fraction within
[0, 0.31]) prices at THAT rate, never the ceiling. Facts are written through the real producer writer (program-facts), so the writer, the fingerprint and the pricing path are exercised together."""
from __future__ import annotations

import uuid

import pytest

from app.services.canonical_evaluation import evaluate_project
from app.services.ny_producer_facts import write_ny_program_facts
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

LINES = (("1000", "ABOVE THE LINE CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_crew_labor", "btl", 1_400_000.0),
         ("3200", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 700_000.0), ("5000", "POST SOUND", "sound", "post", 300_000.0))


async def _tx(db, pid):
    await evaluate_project(db, pid)
    return next(e for e in await served_structures(db, pid) if e["program_slugs"] == ["us_tx_miip"] and e["structure_type"] == "single_country")


@pytest.mark.asyncio
async def test_texas_award_facts_gate_the_ceiling_and_the_awarded_rate_prices_not_the_ceiling():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-TX")
        project_id = uuid.UUID(pid)
        before = await _tx(db, pid)
        assert before["candidate_status"] != "PRICED" or not before["confirmed_incentive_floor_usd"], "no award: zero guaranteed"

        await write_ny_program_facts(db, project_id, evidenced={"us_tx_miip_award_confirmed": True})
        assert not (await _tx(db, pid))["confirmed_incentive_floor_usd"], "the award alone never prices the ceiling"

        await write_ny_program_facts(db, project_id, evidenced={"us_tx_miip_pool_period_valid": True},
                                     amounts={"us_tx_miip_resident_crew_pct": 20.0, "us_tx_miip_resident_cast_pct": 40.0, "us_tx_miip_awarded_rate_pct": 0.28})
        assert not (await _tx(db, pid))["confirmed_incentive_floor_usd"], "crew residency 20% is below the 35% threshold: a genuine failure, never priced"

        await write_ny_program_facts(db, project_id, amounts={"us_tx_miip_resident_crew_pct": 40.0, "us_tx_miip_awarded_rate_pct": 0.24})
        at24 = await _tx(db, pid)
        qpe = sum(l[4] for l in LINES)   # every account is spent in Texas (home US-TX, nothing relocated): independent base 3,000,000
        assert at24["confirmed_incentive_floor_usd"] == pytest.approx(round(qpe * 0.24, 2), abs=0.01), "a 24% award prices at 24% of the qualifying spend (720,000)"

        await write_ny_program_facts(db, project_id, amounts={"us_tx_miip_awarded_rate_pct": 0.28})
        at28 = await _tx(db, pid)
        assert at28["confirmed_incentive_floor_usd"] == pytest.approx(round(qpe * 0.28, 2), abs=0.01) and at28["confirmed_incentive_floor_usd"] > at24["confirmed_incentive_floor_usd"]

        await write_ny_program_facts(db, project_id, amounts={"us_tx_miip_awarded_rate_pct": None})
        assert not (await _tx(db, pid))["confirmed_incentive_floor_usd"], "clearing the awarded rate returns to Unknown: nothing is guaranteed (never the 31% ceiling)"


@pytest.mark.asyncio
async def test_a_write_naming_a_real_production_is_refused_on_any_session():
    """The conftest guard (not the isolated harness): a plain session on the configured engine cannot delete or write a real anchor production's facts."""
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.session import engine
    from app.models.project_fact import ProjectFact
    from tests.isolated_records import RealProjectWriteRefused
    async with AsyncSession(engine) as session:
        with pytest.raises(RealProjectWriteRefused):
            await session.execute(delete(ProjectFact).where(ProjectFact.project_id == uuid.UUID("6c6f1c13-2d49-4bbc-bafb-2a12efa93112")))
        await session.rollback()


@pytest.mark.asyncio
async def test_the_served_view_contract_holds_on_a_synthetic_production():
    """The generic contract the real-production tests asserted on FVD/Lips (a status, a production, structures with program slugs and candidate statuses), proven on a synthetic production."""
    from app.services.canonical_production_view import build_production_and_structures

    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-TX")
        await evaluate_project(db, pid)
        view = await build_production_and_structures(db, pid)
        assert view["status"] == "OK" and view["production"]["production_id"] == pid
        entries = view["structures"]["allocated_structures"]["structures"]
        assert entries, "a synthetic US-TX production discovers candidate structures"
        assert all("program_slugs" in e and "candidate_status" in e for e in entries)


@pytest.mark.asyncio
@pytest.mark.parametrize("slug,rate", [("us_ny_empire_state_independent_film_credit", 0.30), ("us_ut_motion_picture_incentive", 0.20), ("us_va_motion_picture_credit", 0.15),
                                       ("ca_ns_production_incentive_fund", 0.25), ("ca_ab_fttc", 0.22)])
async def test_programs_with_corrected_bases_price_end_to_end_on_all_eligible_cost(slug, rate):
    """Independent arithmetic: the production spends 3,000,000 in total (labour, equipment and post), so a full relocation prices the corrected all-eligible-cost base at rate x 3,000,000.
    Nova Scotia is 25% of ALL eligible cost (CCTH Guidelines s.6.2), not of the 2,000,000 of labour; Alberta 22% (alberta.ca FTTC page); Utah, Virginia and New York per their official pages."""
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="US-TX")
        await evaluate_project(db, pid)
        entry = next((e for e in await served_structures(db, pid) if e["program_slugs"] == [slug] and e["structure_type"] == "full_relocation"), None)
        assert entry is not None, f"{slug} is discovered as a full-relocation candidate"
        assert entry["confirmed_incentive_floor_usd"] == pytest.approx(round(3_000_000.0 * rate, 2), abs=0.01)
