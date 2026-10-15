"""NA-RECONCILIATION-25: several identified people on ONE budget line through the existing `line_fact` owner (`line_fact:<line>:allocations`). Pricing controls are DB-free; the writer / view controls run on
isolated synthetic projects only (no real production is read or evaluated)."""
from __future__ import annotations

import uuid

import pytest

from app.calculators import line_allocations as la
from app.services import ny_producer_facts as npf
from app.services.line_inputs import field_specs, line_inputs_view
from tests.isolated_records import create_synthetic_project, isolated_session
from tests.test_na_line_inputs_controls import _price

MT = "us_mt_media_act_tax_credit"
SPECS = field_specs()


def _facts(by_line: dict, amounts: dict):
    names = [a["payee_id"] for al in by_line.values() for a in al]
    return la.amount_facts(by_line, la.person_ordinals(names), amounts)


def _p(name, usd, **kw):
    return {"payee_id": name, "amount_usd": usd, **kw}


# ── pricing: each person is assessed on their own share and their own cap, then aggregated ────────────────────────────────────────────────────────

def test_two_resident_crew_on_one_line_are_each_capped_before_aggregation():
    line = [("L1", "btl_resident_labor", 1_000_000.0)]
    one = _price(line, _facts({"L1": [_p("A", 1_000_000.0)]}, {"L1": 1_000_000.0}))
    two = _price(line, _facts({"L1": [_p("A", 700_000.0), _p("B", 300_000.0)]}, {"L1": 1_000_000.0}))
    assert one == pytest.approx((150_000.0, 150_000.0)), "one person holding the whole line: 25% = 250,000 capped at 150,000 (unchanged single-person behaviour)"
    assert two == pytest.approx((150_000.0 + 75_000.0, 150_000.0 + 75_000.0)), "A: 25% of 700,000 = 175,000 capped at 150,000; B: 75,000 - the cap applies to each person BEFORE aggregation"


def test_a_person_split_over_two_lines_is_one_person_for_the_cap_and_never_counted_twice():
    lines = [("L1", "btl_resident_labor", 600_000.0), ("L2", "btl_resident_labor", 400_000.0)]
    facts = _facts({"L1": [_p("A", 600_000.0)], "L2": [_p("A", 400_000.0)]}, {"L1": 600_000.0, "L2": 400_000.0})
    assert _price(lines, facts) == pytest.approx((150_000.0, 150_000.0))
    shared = _facts({"L1": [_p("A", 300_000.0), _p("B", 300_000.0)], "L2": [_p("A", 400_000.0)]}, {"L1": 600_000.0, "L2": 400_000.0})
    assert _price(lines, shared) == pytest.approx((150_000.0 + 75_000.0, 150_000.0 + 75_000.0)), "A holds 700,000 over two lines (one person, capped once); B holds 300,000"


def test_an_incomplete_allocation_keeps_a_lawful_bounded_potential_and_the_remainder_is_never_assigned():
    line = [("L1", "btl_resident_labor", 1_000_000.0)]
    floor, ceiling = _price(line, _facts({"L1": [_p("A", 300_000.0)]}, {"L1": 1_000_000.0}))
    assert floor == pytest.approx(150_000.0), "no less than the existing one-person lower bound on the whole (the same bound partial identification across lines already uses); A's identified 75,000 is inside it"
    assert ceiling == pytest.approx(75_000.0 + 0.25 * 700_000.0), "A's exact credit plus 25% of the 700,000 assigned to nobody (it may belong to many persons): a bounded potential, never a confirmed credit"
    complete = _price(line, _facts({"L1": [_p("A", 300_000.0), _p("B", 700_000.0)]}, {"L1": 1_000_000.0}))
    assert complete == pytest.approx((75_000.0 + 150_000.0, 75_000.0 + 150_000.0)), "completing the allocation makes the credit exact"


def test_students_and_veterans_on_one_line_each_use_their_own_category_rate_and_cap():
    line = [("L1", "btl_crew_labor", 1_000_000.0)]
    people = [_p("S", 100_000.0, mt_status="student", mt_residency="resident"), _p("V", 600_000.0, mt_status="veteran_tribal", mt_residency="resident"),
              _p("R", 300_000.0, mt_status="none", mt_residency="resident")]
    floor, ceiling = _price(line, _facts({"L1": people}, {"L1": 1_000_000.0}))
    expected = min(0.30 * 100_000.0, 50_000.0) + min(0.30 * 600_000.0, 150_000.0) + 0.25 * 300_000.0
    assert (floor, ceiling) == pytest.approx((expected, expected)), "student 30% capped at 50,000; veteran 30% capped at 150,000; resident crew 25% - one category per person"


def test_nonresident_withholding_is_stated_per_person_and_unknown_is_not_false():
    line = [("L1", "btl_nonresident_labor", 1_000_000.0)]
    people = [_p("W", 500_000.0, mt_tax_withheld=True), _p("N", 300_000.0, mt_tax_withheld=False), _p("U", 200_000.0)]
    floor, ceiling = _price(line, _facts({"L1": people}, {"L1": 1_000_000.0}))
    assert floor == pytest.approx(0.15 * 500_000.0), "only the withheld person is confirmed"
    assert ceiling == pytest.approx(0.15 * 500_000.0 + 0.15 * 200_000.0), "Unknown withholding keeps its bounded potential; a stated No applies the failed treatment (no credit, no upside)"


def test_a_single_person_row_prices_identically_through_the_allocation_and_the_legacy_facts():
    line = [("L1", "btl_resident_labor", 400_000.0)]
    legacy = _price(line, {"ny_atl_payee:L1": 1.0})
    allocation = _price(line, _facts({"L1": [_p("A", 400_000.0)]}, {"L1": 1_000_000.0 and 400_000.0}))
    assert legacy == pytest.approx(allocation)


# ── conservation, uniqueness and exclusivity (pure validation) ────────────────────────────────────────────────────────────────────────────────────

def test_allocations_cannot_exceed_the_line_or_repeat_a_person_and_the_remainder_is_explicit():
    with pytest.raises(ValueError, match="more than the line amount"):
        la.validate("L1", 1_000.0, [_p("A", 700.0), _p("B", 400.0)], SPECS)
    with pytest.raises(ValueError, match="appears twice"):
        la.validate("L1", 1_000.0, [_p("A", 100.0), _p("a", 100.0)], SPECS)
    with pytest.raises(ValueError, match="at least 0"):
        la.validate("L1", 1_000.0, [_p("A", -1.0)], SPECS)
    with pytest.raises(ValueError, match="evidence needs its source"):
        la.validate("L1", 1_000.0, [_p("A", 100.0, evidence={"method": "DEAL_MEMO", "confidence": "STATED"})], SPECS)
    ok = la.validate("L1", 1_000.0, [_p("A", 600.0, mt_status="student")], SPECS)
    assert sum(a["amount_usd"] for a in ok) == 600.0, "the other 400 is not assigned to anyone (it stays Unknown)"


def test_one_person_is_in_exactly_one_montana_category_across_lines():
    with pytest.raises(ValueError, match="exactly one"):
        la.check_across_lines({"L1": [_p("A", 1.0, mt_status="student")], "L2": [_p("A", 1.0, mt_status="veteran_tribal")]})
    with pytest.raises(ValueError, match="exactly one"):
        la.check_across_lines({"L1": [_p("A", 1.0, mt_residency="resident")], "L2": [_p("a", 1.0, mt_residency="nonresident")]})
    la.check_across_lines({"L1": [_p("A", 1.0, mt_status="student")], "L2": [_p("A", 1.0, mt_status="student")]})


# ── database: writer, view, legacy compatibility, reset, fingerprint ──────────────────────────────────────────────────────────────────────────────

LINES = (("3100", "CREW", "btl_resident_labor", "btl", 1_000_000.0), ("1000", "WRITER", "atl_writer", "atl", 300_000.0))


async def _line(db, project_id, category):
    view = await line_inputs_view(db, project_id, [MT])
    return next(l for l in view["lines"] if l["category"] == category), view


@pytest.mark.asyncio
async def test_writer_stores_people_once_reads_them_back_cold_and_reset_restores_unknown():
    from app.services.canonical_evaluation import current_generation_fingerprint
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        line, _ = await _line(db, project_id, "btl_resident_labor")
        assert line["allocations"]["people"] == [] and line["allocations"]["unallocated_usd"] == 1_000_000.0 and line["allocations"]["unallocated_state"] == "UNKNOWN"
        lid = line["line_id"]
        fp0 = await current_generation_fingerprint(db, project_id)
        body = [{"line_id": lid, "allocations": [_p("A", 600_000.0, mt_residency="resident", mt_status="none"), _p("B", 250_000.0, mt_residency="resident")]}]
        await npf.write_ny_program_facts(db, project_id, line_allocations=body)
        fp1 = await current_generation_fingerprint(db, project_id)
        assert fp1 != fp0, "a changed economic input changes the fingerprint (one evaluation will be required)"
        await npf.write_ny_program_facts(db, project_id, line_allocations=body)
        assert await current_generation_fingerprint(db, project_id) == fp1, "saving the same allocations again changes nothing (no evaluation is due)"
        db.expunge_all()
        line, view = await _line(db, project_id, "btl_resident_labor")                         # cold reload from the stored rows
        a = line["allocations"]
        assert [p["payee_id"] for p in a["people"]] == ["A", "B"] and a["assigned_usd"] == 850_000.0 and a["unallocated_usd"] == 150_000.0 and a["unallocated_state"] == "UNKNOWN"
        assert {p["payee"]: p["total_usd"] for p in view["persons"]} == {"A": 600_000.0, "B": 250_000.0}
        await npf.write_ny_program_facts(db, project_id, line_allocations=[{"line_id": lid, "allocations": None}])             # Reset
        db.expunge_all()
        line, view = await _line(db, project_id, "btl_resident_labor")
        assert line["allocations"]["people"] == [] and line["allocations"]["unallocated_state"] == "UNKNOWN" and view["persons"] == []
        assert await current_generation_fingerprint(db, project_id) == fp0, "Reset removes the producer allocation and restores the derived / Unknown state exactly"


@pytest.mark.asyncio
async def test_a_legacy_single_person_row_reads_as_one_allocation_and_saving_allocations_replaces_it():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        line, _ = await _line(db, project_id, "btl_resident_labor")
        lid = line["line_id"]
        await npf.write_ny_program_facts(db, project_id, payees=[{"line_id": lid, "payee_id": "Pat", "compensation_complete": True}])
        line, view = await _line(db, project_id, "btl_resident_labor")
        a = line["allocations"]
        assert a["legacy_single_person"] is True and [p["payee_id"] for p in a["people"]] == ["Pat"] and a["people"][0]["amount_usd"] == 1_000_000.0 and a["unallocated_usd"] == 0.0
        assert view["persons"][0]["payee"] == "Pat" and view["persons"][0]["complete"] is True
        await npf.write_ny_program_facts(db, project_id, line_allocations=[{"line_id": lid, "allocations": [_p("Pat", 400_000.0), _p("Sam", 100_000.0)]}])
        line, view = await _line(db, project_id, "btl_resident_labor")
        assert line["allocations"]["legacy_single_person"] is False and line["allocations"]["unallocated_usd"] == 500_000.0
        fields = {f["name"]: f["value"] for f in line["fields"]}
        assert fields["payee_id"] is None and fields["payee_compensation_complete"] is None, "the allocations replaced the legacy single-person identity rows"


@pytest.mark.asyncio
async def test_the_writer_refuses_invalid_allocations_and_cross_line_conflicts_and_writes_nothing():
    from app.services.canonical_evaluation import current_generation_fingerprint
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        crew, _ = await _line(db, project_id, "btl_resident_labor")
        writer, _ = await _line(db, project_id, "atl_writer")
        fp = await current_generation_fingerprint(db, project_id)
        with pytest.raises(ValueError, match="more than the line amount"):
            await npf.write_ny_program_facts(db, project_id, line_allocations=[{"line_id": crew["line_id"], "allocations": [_p("A", 900_000.0), _p("B", 200_000.0)]}])
        with pytest.raises(ValueError, match="not a line of this project"):
            await npf.write_ny_program_facts(db, project_id, line_allocations=[{"line_id": str(uuid.uuid4()), "allocations": [_p("A", 1.0)]}])
        with pytest.raises(ValueError, match="exactly one"):
            await npf.write_ny_program_facts(db, project_id, line_allocations=[
                {"line_id": crew["line_id"], "allocations": [_p("A", 100.0, mt_status="student")]}, {"line_id": writer["line_id"], "allocations": [_p("A", 100.0, mt_status="veteran_tribal")]}])
        assert await current_generation_fingerprint(db, project_id) == fp
