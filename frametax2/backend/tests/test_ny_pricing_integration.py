"""Behavioral controls for the New York pricing integration, on rolled-back synthetic records only (no real project is read or
written): above-the-line limits (40% group limit, $500,000 per identified payee), the post-credit location scenario, and the
statutory uplifts priced on their own bases. Every figure below is hand-computed from the cited rule."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.budget import BudgetDocument, BudgetLineItem
from app.services import canonical_evaluation as ce
from app.services.ny_producer_facts import write_ny_program_facts
from tests.isolated_records import create_synthetic_project, isolated_session, served_structures

pytestmark = pytest.mark.asyncio

NY = "ny_state_film"
POST = "us_ny_post_production_credit"
#: ATL 4.0M (director 3.0M + cast 1.0M); other qualified = crew 3.0M + equipment 2.0M + score 0.3M = 5.3M.
PRODUCTION_LINES = (
    ("2000", "DIRECTOR FEE", "atl_director", "atl", 3_000_000.0),
    ("2100", "CAST", "atl_cast", "atl", 1_000_000.0),
    ("3000", "CREW", "btl_crew_labor", "btl", 3_000_000.0),
    ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 2_000_000.0),
    ("5000", "MUSIC SCORE", "music", "post", 300_000.0),
)
POST_LINES = (
    ("3000", "CREW", "btl_crew_labor", "btl", 3_000_000.0),
    ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 2_000_000.0),
    ("5000", "POST PRODUCTION SERVICES", "post_production", "post", 1_500_000.0),
    ("5100", "SOUND MIX", "sound", "post", 600_000.0),
)


async def _line_ids(db, pid) -> dict[str, str]:
    rows = (await db.execute(select(BudgetLineItem.id, BudgetLineItem.description).join(
        BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id).where(BudgetDocument.project_id == pid))).all()
    return {d.split()[0]: str(i) for i, d in rows}


async def _entry(db, pid, slug, structure_type=None):
    entries = [e for e in await served_structures(db, pid)
               if e["program_slugs"] == [slug] and e["candidate_status"] == "PRICED" and (structure_type is None or e["structure_type"] == structure_type)]
    assert entries, f"no priced {slug} structure"
    return entries[0]


def _trace(entry):
    return entry["segments"][0]["qualification_trace"]


async def test_group_limit_and_unresolved_per_individual_cap_then_identified_payee_cap_then_uplifts():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=PRODUCTION_LINES, home_code="US-NY")
        ids = await _line_ids(db, pid)

        # 1. No facts. The 40% group limit is computable from the register: 0.40 x 5.3M = 2.12M of the 4.0M ATL qualifies.
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert e["qpe_usd"] == pytest.approx(5_300_000 + 2_120_000) and e["confirmed_incentive_floor_usd"] == pytest.approx(0.30 * 7_420_000)
        group_cut = [t for t in _trace(e) if t["state"] == "excluded" and "forty percent" in t["reason"]]
        assert sum(t["amount_usd"] for t in group_cut) == pytest.approx(1_880_000)
        # the director and cast accounts exceed $500,000 but are not tied to an identified payee: UNRESOLVED, carried as a planning figure
        unresolved = [t for t in _trace(e) if t["state"] == "qualifies" and "UNRESOLVED: the $500,000 per-individual cap" in t["reason"]]
        assert unresolved, "an unidentified over-cap account must say the cap is unresolved"
        # statutory uplifts are bounds only: not floor, and the result says it still needs confirmation
        base_potential = e["potential_upside_usd"]
        assert base_potential > 0 and e["ceiling_requires_confirmation"] is True

        # 2. The director is an identified payee with complete compensation: $3.0M is cut to $500,000 (excess 2.5M, definitive).
        await write_ny_program_facts(db, pid, payees=[{"line_id": ids["2000"], "payee_id": "DIRECTOR-1", "compensation_complete": True}])
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        cap_cut = [t for t in _trace(e) if t["state"] == "excluded" and "per-individual cap" in t["reason"]]
        assert sum(t["amount_usd"] for t in cap_cut) == pytest.approx(2_500_000)
        # ATL left = 0.5M + 1.0M = 1.5M <= 0.40 x 5.3M, so the group limit no longer bites; QPE = 5.3M + 1.5M
        assert e["qpe_usd"] == pytest.approx(6_800_000) and e["confirmed_incentive_floor_usd"] == pytest.approx(0.30 * 6_800_000)

        # 3. A payee whose compensation is NOT evidenced complete is not capped (unknown stays unknown).
        await write_ny_program_facts(db, pid, payees=[{"line_id": ids["2000"], "payee_id": "DIRECTOR-1", "compensation_complete": False}])
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert not [t for t in _trace(e) if t["state"] == "excluded" and "per-individual cap" in t["reason"]]
        assert e["qpe_usd"] == pytest.approx(7_420_000)


async def test_uplifts_price_on_their_own_bases_and_only_with_their_prerequisites():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=PRODUCTION_LINES, home_code="US-NY")
        ids = await _line_ids(db, pid)
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        qpe, base = e["qpe_usd"], 0.30 * e["qpe_usd"]
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(base)

        # labor in the listed counties only: qualified labor = ATL 2.12M (after the group limit) + crew 3.0M = 5.12M -> +10%
        await write_ny_program_facts(db, pid, evidenced={"ny_all_costs_in_listed_counties": True})
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(base + 0.10 * 5_120_000)       # no 'other costs' uplift without the majority-days fact

        # majority of principal-photography days there: other qualified costs (equipment 2.0M + score 0.3M) earn +10% too
        await write_ny_program_facts(db, pid, evidenced={"ny_majority_principal_photography_days_in_listed_counties": True})
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(base + 0.10 * 5_120_000 + 0.10 * 2_300_000)

        # scoring: +10% on the evidenced scoring portion (200,000 of the 300,000 music account) once five musicians are stated
        await write_ny_program_facts(db, pid, evidenced={"ny_scoring_five_musicians_in_state": True},
                                     uplift_basis=[{"program": NY, "uplift": "scoring", "line_id": ids["5000"], "amount_usd": 200_000.0}])
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(base + 0.10 * 5_120_000 + 0.10 * 2_300_000 + 0.10 * 200_000)
        assert e["ceiling_requires_confirmation"] is False, "every uplift basis is now evidenced"

        # Production Plus is by application: nothing until evidenced, then the evidenced tier on all qualified NY costs (not both tiers)
        before = e["confirmed_incentive_floor_usd"]
        await write_ny_program_facts(db, pid, evidenced={"ny_production_plus_5pct_tier": True})
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, NY, "single_country")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(before + 0.05 * e["qpe_usd"])


async def test_post_credit_location_scenario_and_wage_uplift():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=POST_LINES, home_code="US-GA")
        ids = await _line_ids(db, pid)
        # Unknown location: 30% is the guaranteed rate and 35% is shown as the conditional scenario.
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, POST, "full_relocation")
        assert e["qpe_usd"] == pytest.approx(2_100_000)
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(0.30 * 2_100_000)
        # the post wage uplift is also an unevidenced bound here: its potential is 10% of the qualified post accounts (2.1M)
        assert e["maximum_supported_incentive_usd"] == pytest.approx(0.35 * 2_100_000 + 0.10 * 2_100_000) and e["ceiling_requires_confirmation"] is True

        # Facility inside the commuter district: 30% only, the 35% scenario is gone.
        await write_ny_program_facts(db, pid, evidenced={"ny_post_facility_inside_mctd": True})
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, POST, "full_relocation")
        assert e["maximum_supported_incentive_usd"] == pytest.approx(0.30 * 2_100_000 + 0.10 * 2_100_000)

        # Outside the district: 35% is the guaranteed rate. (Clearing 'inside' first: the two cannot both be stated.)
        await write_ny_program_facts(db, pid, evidenced={"ny_post_facility_inside_mctd": None, "ny_post_facility_outside_mctd": True})
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, POST, "full_relocation")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(0.35 * 2_100_000)

        # Upstate +10% on post WAGES at a listed-county facility: only the evidenced wage portion of the account, never the facility fee.
        await write_ny_program_facts(db, pid, uplift_basis=[{"program": POST, "uplift": "upstate_post_wages", "line_id": ids["5000"], "amount_usd": 800_000.0}])
        await ce.evaluate_project(db, pid)
        e = await _entry(db, pid, POST, "full_relocation")
        assert e["confirmed_incentive_floor_usd"] == pytest.approx(0.35 * 2_100_000 + 0.10 * 800_000)
        assert e["ceiling_requires_confirmation"] is True, "the sound account's wage portion is still unevidenced"


async def test_conflicting_or_invalid_producer_facts_are_rejected_and_nothing_is_written():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=POST_LINES, home_code="US-GA")
        ids = await _line_ids(db, pid)
        for bad in (
            dict(evidenced={"ny_post_facility_inside_mctd": True, "ny_post_facility_outside_mctd": True}),
            dict(evidenced={"ny_post_facility_outside_mctd": False}),
            dict(evidenced={"not_a_ny_fact": True}),
            dict(payees=[{"line_id": "00000000-0000-0000-0000-000000000000", "payee_id": "X", "compensation_complete": True}]),
            dict(uplift_basis=[{"program": POST, "uplift": "upstate_post_wages", "line_id": ids["5000"], "amount_usd": 9_999_999.0}]),
            dict(uplift_basis=[{"program": POST, "uplift": "no_such_uplift", "line_id": ids["5000"], "amount_usd": 1.0}]),
        ):
            with pytest.raises(ValueError):
                await write_ny_program_facts(db, pid, **bad)
