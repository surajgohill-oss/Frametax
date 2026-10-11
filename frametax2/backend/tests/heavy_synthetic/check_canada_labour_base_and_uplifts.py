"""HEAVY synthetic check (explicit path, bounded: each evaluation fails after 240 s rather than passing on a timeout; `DATABASE_URL unset python -m pytest tests/heavy_synthetic/check_canada_labour_base_and_uplifts.py -q`).
Behavioral controls (rolled-back synthetic records only) for the Canadian repairs: Ontario OFTTC and Nova Scotia apply their rate to
LABOUR, not to all qualifying spend; the statutory uplifts on a narrower base (OFTTC first-time producer and outside-GTA bonus, Quebec
16% VFX labour enhancement, BC regional and distant-location credits) are priced when their base is stated and stay a disclosed bound
when it is not. Every figure is hand-computed from the cited rule."""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import select, text

from app.models.budget import BudgetDocument, BudgetLineItem
from app.services import canonical_evaluation as ce
from app.services.ny_producer_facts import write_ny_program_facts
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

pytestmark = pytest.mark.asyncio

#: labour = director 400,000 + crew 1,500,000 = 1,900,000 ; non-labour = equipment 600,000 ; QPE 2,500,000 (+ post 300,000 below)
LINES = (
    ("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0),
    ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
    ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0),
    ("5000", "POST PRODUCTION", "post_production", "post", 300_000.0),
)
LABOUR = 1_900_000.0
ALL_SPEND = 2_800_000.0


EVALUATION_BUDGET_SECONDS = 240   # an evaluation that exceeds this FAILS the check (asyncio.TimeoutError); a timeout is never a pass


async def _evaluate(db, pid):
    """One bounded evaluation, then fresh planner statistics (a precaution: each evaluation inside this rolled-back transaction adds hundreds
    of structure rows autovacuum cannot analyze until commit; whether that explained the 2026-10-11 stall is an unproven hypothesis)."""
    result = await asyncio.wait_for(ce.evaluate_project(db, pid), EVALUATION_BUDGET_SECONDS)
    await db.execute(text("ANALYZE production_structures"))
    await db.execute(text("ANALYZE structure_calculation_results"))
    return result


async def _entry(db, pid, slug):
    hits = [e for e in await asyncio.wait_for(served_structures(db, pid), EVALUATION_BUDGET_SECONDS)
            if e["program_slugs"] == [slug] and e["candidate_status"] == "PRICED"]
    assert hits, f"no priced {slug} structure"
    return hits[0]


async def test_labour_bases_and_every_uplift_price_when_their_base_is_stated_and_stay_bounds_when_not():
    """Two evaluations of one project: nothing stated, then every producer fact stated at once."""
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="CA-ON")
        await _evaluate(db, pid)
        ofttc = await _entry(db, pid, "on_ofttc")
        # 35% of the eligible Ontario LABOUR (1.9M), not of all qualifying spend (2.8M, which would be 980,000)
        assert ofttc["confirmed_incentive_floor_usd"] == pytest.approx(0.35 * LABOUR)
        # unstated outside-GTA bonus is a bound (10% of labour); the first-time-producer enhancement is election-only: nothing
        assert ofttc["maximum_supported_incentive_usd"] == pytest.approx(0.45 * LABOUR) and ofttc["ceiling_requires_confirmation"] is True
        assert (await _entry(db, pid, "ca_ns_production_incentive_fund"))["confirmed_incentive_floor_usd"] == pytest.approx(0.25 * LABOUR)
        # all-spend credits keep their all-spend base (Ontario OPSTC states "all qualifying production expenditures")
        assert (await _entry(db, pid, "on_opstc"))["confirmed_incentive_floor_usd"] == pytest.approx(0.215 * ALL_SPEND)
        bc = await _entry(db, pid, "ca_bc_pstc")
        assert bc["confirmed_incentive_floor_usd"] == pytest.approx(0.36 * LABOUR)
        assert bc["maximum_supported_incentive_usd"] == pytest.approx(0.48 * LABOUR) and bc["ceiling_requires_confirmation"] is True
        # Manitoba cost-of-salaries credit: 45% of labour; the three bonuses (+10, +5, +5) are bounds until stated
        mb = await _entry(db, pid, "ca_mb_film_video_credit")
        assert mb["confirmed_incentive_floor_usd"] == pytest.approx(0.45 * LABOUR)
        assert mb["maximum_supported_incentive_usd"] == pytest.approx(0.65 * LABOUR) and mb["ceiling_requires_confirmation"] is True

        await write_ny_program_facts(db, pid, evidenced={
            "on_ofttc_labour_outside_gta": True, "on_ofttc_first_time_producer": True,
            "bc_labour_in_regional_zone": True, "bc_labour_in_distant_location_zone": True,
            "mb_frequent_filming_third_film_in_two_years": True, "mb_frequent_filming_principal_owner_declared": True,
            "mb_resident_producer_screen_credit": True, "mb_rural_permanent_establishment_35km": True, "mb_rural_majority_days_35km": True,
        })
        await _evaluate(db, pid)
        ofttc = await _entry(db, pid, "on_ofttc")
        # +10 points on all labour, plus +5 points on only the FIRST $240,000 of labour
        assert ofttc["confirmed_incentive_floor_usd"] == pytest.approx(0.45 * LABOUR + 0.05 * 240_000.0) and ofttc["ceiling_requires_confirmation"] is False
        bc = await _entry(db, pid, "ca_bc_pstc")
        assert bc["confirmed_incentive_floor_usd"] == pytest.approx(0.48 * LABOUR) and bc["ceiling_requires_confirmation"] is False
        mb = await _entry(db, pid, "ca_mb_film_video_credit")
        assert mb["confirmed_incentive_floor_usd"] == pytest.approx(0.65 * LABOUR) and mb["ceiling_requires_confirmation"] is False


async def test_quebec_vfx_labour_enhancement_prices_on_the_evidenced_labour_portion_only():
    # Budget shape matters, not size. Measured 2026-10-11 on this isolated database with a Canada-Ontario home: director + crew + equipment + VFX
    # (ONE movable component) evaluates in 33.6 s including the served read; the same budget plus a 300,000 post-production line (TWO movable
    # components, post_vfx_package and a VFX split) exceeded the 240 s bound in the hybrid component search. The Quebec VFX enhancement needs
    # only a VFX account, so this control uses the one-movable-component shape. (The slowdown with two movable components is recorded as an
    # open performance finding; stale planner statistics are an unproven hypothesis, not the established cause.)
    lines = tuple(l for l in LINES if l[2] != "post_production") + (("6100", "VFX", "vfx", "post", 300_000.0),)
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=lines, home_code="CA-ON")
        rows = (await db.execute(select(BudgetLineItem.id, BudgetLineItem.description).join(
            BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id).where(BudgetDocument.project_id == pid))).all()
        vfx_line = next(str(i) for i, d in rows if d.startswith("6100"))
        await _evaluate(db, pid)
        qc = await _entry(db, pid, "ca_qc_pstc")
        assert qc["confirmed_incentive_floor_usd"] == pytest.approx(0.25 * qc["qpe_usd"])
        # unstated: a bound of 16% on the whole qualified VFX account
        assert qc["maximum_supported_incentive_usd"] == pytest.approx(0.25 * qc["qpe_usd"] + 0.16 * 300_000.0) and qc["ceiling_requires_confirmation"] is True
        # stated: only 65% of the VFX service contract is recognized -> 195,000 of qualifying labour earns the 16%
        await write_ny_program_facts(db, pid, uplift_basis=[{"program": "ca_qc_pstc", "uplift": "vfx_labour_enhancement", "line_id": vfx_line, "amount_usd": 195_000.0}])
        await _evaluate(db, pid)
        qc = await _entry(db, pid, "ca_qc_pstc")
        assert qc["confirmed_incentive_floor_usd"] == pytest.approx(0.25 * qc["qpe_usd"] + 0.16 * 195_000.0) and qc["ceiling_requires_confirmation"] is False
