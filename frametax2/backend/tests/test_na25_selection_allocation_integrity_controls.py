"""NA25_SELECTION_AND_ALLOCATION_INTEGRITY_REPAIR controls.

1. The producer-selected leading structure is part of the served candidate page even when its ordinary rank is beyond the first page.
2. An allocation key no pricing path reads is refused by name before any write, never accepted and silently dropped.

Isolated synthetic projects on the ``frametax2_pytest`` database only (rolled back); no real production is read or evaluated."""
from __future__ import annotations

import time
import uuid

import pytest
from sqlalchemy import func, select

from app.calculators import line_allocations as la
from app.models.production import ProductionStructure, StructureCalculationResult
from app.models.project import Project
from app.models.project_fact import ProjectFact
from app.services import canonical_evaluation as ce
from app.services import ny_producer_facts as npf
from app.services.canonical_production_view import build_production_and_structures
from app.services.leading_selection import selection_identity
from app.services.line_inputs import field_specs, line_inputs_view
from tests.isolated_records import create_synthetic_project, isolated_session

SPECS = field_specs()
LINES = (("1000", "CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_resident_labor", "btl", 1_000_000.0),
         ("3200", "EQUIPMENT", "btl_equipment_rental", "btl", 700_000.0))
SMALL = (("1000", "CAST", "atl_cast", "atl", 600_000.0),)
PROGS = ["us_mt_media_act_tax_credit", "ca_federal_cptc"]


# ── allocation fields: DB-free ───────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("key", ["canadian_status", "service_location", "role", "payment_status", "not_a_field", "payee_compensation_complete"])
def test_an_unsupported_allocation_key_is_refused_by_name(key):
    with pytest.raises(ValueError) as err:
        la.validate("L1", 1_000_000.0, [{"payee_id": "A", "amount_usd": 500_000.0, key: "x"}], SPECS)
    assert key in str(err.value) and "L1" in str(err.value)


def test_a_valid_person_before_an_invalid_one_still_fails_the_whole_line():
    with pytest.raises(ValueError, match="service_location"):
        la.validate("L1", 1_000_000.0, [{"payee_id": "A", "amount_usd": 400_000.0}, {"payee_id": "B", "amount_usd": 600_000.0, "service_location": "in_canada"}], SPECS)


def test_the_canadian_refusal_does_not_claim_per_person_eligibility_and_directs_to_separate_lines():
    with pytest.raises(ValueError) as err:
        la.validate("L1", 1_000_000.0, [{"payee_id": "A", "amount_usd": 1_000_000.0, "canadian_status": "resident_citizen"}], SPECS)
    text = str(err.value)
    assert "separate budget lines" in text and "not computed per person" in text and "no line-split editor" in text
    assert "implemented" not in text.replace("not implemented", "")


def test_a_non_object_person_is_refused():
    with pytest.raises(ValueError, match="object"):
        la.validate("L1", 1_000_000.0, ["A"], SPECS)


def test_every_supported_field_is_accepted_and_stored_unchanged():
    person = {"payee_id": "A", "amount_usd": 800_000.0, "payee_type": "employee", "mt_residency": "resident", "mt_tax_withheld": True, "mt_status": "none",
              "producer_role": "line", "composer_compensation_usd": 1_000.0,
              "evidence": {"source": "deal memo", "method": "DEAL_MEMO", "confidence": "DOCUMENTED", "date": "2026-10-01"}}
    assert la.ALLOCATION_KEYS == {"payee_id", "amount_usd", "evidence", *la.PERSON_FIELDS}
    assert la.validate("L1", 1_000_000.0, [dict(person)], SPECS) == [person]


# ── allocation fields: writer, zero partial writes ───────────────────────────────────────────────────────────────────────

async def _fact_rows(session, pid):
    return sorted((await session.execute(select(ProjectFact.fact_key, ProjectFact.value).where(ProjectFact.project_id == uuid.UUID(pid)))).all())


async def _structure_count(session, pid):
    return (await session.scalar(select(func.count()).select_from(ProductionStructure).where(ProductionStructure.project_id == uuid.UUID(pid)))) or 0


async def _line_id(session, pid, category="btl_resident_labor"):
    view = await line_inputs_view(session, uuid.UUID(pid), PROGS)
    return next(l["line_id"] for l in view["lines"] if l["category"] == category)


async def test_a_mixed_valid_and_invalid_request_writes_nothing_and_creates_no_generation():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        lid = await _line_id(db, pid)
        before_facts, before_structures = await _fact_rows(db, pid), await _structure_count(db, pid)
        with pytest.raises(ValueError, match="service_location"):
            await npf.write_ny_program_facts(
                db, uuid.UUID(pid),
                line_facts=[{"line_id": lid, "field": "role", "value": "other"}],
                line_allocations=[{"line_id": lid, "allocations": [{"payee_id": "A", "amount_usd": 400_000.0},
                                                                     {"payee_id": "B", "amount_usd": 600_000.0, "service_location": "in_canada"}]}])
        await db.flush()
        assert await _fact_rows(db, pid) == before_facts, "no fact row of the valid part was written"
        assert await _structure_count(db, pid) == before_structures == 0, "no generation was created"
        with pytest.raises(ValueError, match="entries take only"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": [{"payee_id": "A", "amount_usd": 1.0}], "extra": 1}])
        assert await _fact_rows(db, pid) == before_facts


async def test_supported_allocations_survive_save_and_cold_reload_unchanged_and_the_canadian_line_facts_stay_per_line():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        lid = await _line_id(db, pid)
        people = [{"payee_id": "A", "amount_usd": 700_000.0, "mt_residency": "resident", "mt_status": "none", "mt_tax_withheld": True},
                  {"payee_id": "B", "amount_usd": 300_000.0, "mt_residency": "nonresident", "mt_status": "none", "mt_tax_withheld": False}]
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": people}])
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "canadian_status", "value": "resident_citizen"}])
        await db.flush()
        db.expire_all()
        view = await line_inputs_view(db, uuid.UUID(pid), PROGS)
        line = next(l for l in view["lines"] if l["line_id"] == lid)
        got = [{k: v for k, v in a.items() if k in {"payee_id", "amount_usd", "mt_residency", "mt_status", "mt_tax_withheld"}} for a in line["allocations"]["people"]]
        assert got == people
        keys = {k for k, _ in await _fact_rows(db, pid)}
        assert f"line_fact:{lid}:canadian_status" in keys, "the Canadian status remains a LINE fact; it is not stored on a person"


# ── producer-selected structure remains served ───────────────────────────────────────────────────────────────────────────

async def _ids(session, pid, offset=0):
    allocated = (await build_production_and_structures(session, pid, candidate_offset=offset))["structures"]["allocated_structures"]
    return [e["structure_id"] for e in allocated["structures"]], allocated["candidates_page"], allocated


async def _all_pages(session, pid):
    offset, out, pages = 0, [], []
    while True:
        ids, page, _ = await _ids(session, pid, offset)
        out += ids
        pages.append(page)
        if not page["has_more"]:
            return out, pages
        offset += page["limit"]


async def test_the_producer_selection_beyond_the_first_page_is_served_and_nothing_else_changes():
    started = time.monotonic()
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        u = uuid.UUID(pid)
        await ce.evaluate_project(db, u)
        first_ids, first_page, first = await _ids(db, pid)
        assert first_page["total"] > 100, "the fixture must exceed one page of candidates"
        all_before, pages_before = await _all_pages(db, pid)
        assert len(all_before) == len(set(all_before)) == first_page["total"]
        beyond = all_before[100:]
        assert beyond, "a structure exists whose ordinary rank is beyond the first page"
        pick = uuid.UUID(beyond[0])
        project = (await db.execute(select(Project).where(Project.id == u))).scalar_one()
        project.leading_structure_id, project.leading_selection_identity = pick, await selection_identity(db, pick)
        await db.flush()

        served = await build_production_and_structures(db, pid)
        ids, page, allocated = await _ids(db, pid)
        assert served["production"]["leading_structure_id"] == str(pick)
        assert str(pick) in ids, "the selected structure is in the served first page"
        assert str(pick) in ids[:5], "pinned with the other headline candidates, not left to rank"
        assert page["limit"] == first_page["limit"] <= 100 and len(ids) <= page["limit"]
        # the page is the previous page with the pick added: every other entry keeps its position and order (the last ranked entry makes room)
        assert [i for i in ids if i != str(pick)] == first_ids[:len(ids) - 1]
        # served identity equals stored identity, and the structure carries that same economic identity
        assert served["production"]["leading_selection"] == {"user_selected": True, "unavailable": False}
        assert await selection_identity(db, uuid.UUID(ids[ids.index(str(pick))])) == project.leading_selection_identity
        # pagination: every served candidate exactly once, total unchanged
        all_after, pages_after = await _all_pages(db, pid)
        assert len(all_after) == len(set(all_after)) == page["total"] == first_page["total"]
        assert set(all_after) == set(all_before)
        assert all_after.index(str(pick)) < 100

        # a pick that is already a pinned entry is not duplicated
        baseline_id = next(e["structure_id"] for e in first["structures"] if e["is_baseline"])
        project.leading_structure_id = uuid.UUID(baseline_id)
        project.leading_selection_identity = await selection_identity(db, uuid.UUID(baseline_id))
        await db.flush()
        ids_b, page_b, _ = await _ids(db, pid)
        assert ids_b.count(baseline_id) == 1 and page_b["total"] == first_page["total"]

        # an identity that no longer exists is disclosed, never replaced by another structure
        project.leading_structure_id = None
        project.leading_selection_identity = f"structure:{uuid.uuid4()}"
        await db.flush()
        gone = await build_production_and_structures(db, pid)
        assert gone["production"]["leading_selection"] == {"user_selected": True, "unavailable": True}
        ids_gone, _, _ = await _ids(db, pid)
        assert str(pick) not in ids_gone and ids_gone == first_ids

        # cross-project isolation: another project's pointer to this project's structure pins nothing and resolves nothing
        other = await create_synthetic_project(db, home_code="MU", lines=SMALL)
        await ce.evaluate_project(db, uuid.UUID(other))
        other_project = (await db.execute(select(Project).where(Project.id == uuid.UUID(other)))).scalar_one()
        other_project.leading_structure_id = pick
        other_project.leading_selection_identity = f"structure:{pick}"
        await db.flush()
        other_ids, _, _ = await _ids(db, other)
        assert str(pick) not in other_ids
        other_all, _ = await _all_pages(db, other)
        assert str(pick) not in other_all
        assert (await db.scalar(select(func.count()).select_from(StructureCalculationResult).join(ProductionStructure, ProductionStructure.id == StructureCalculationResult.structure_id)
                                .where(ProductionStructure.project_id == uuid.UUID(other), StructureCalculationResult.structure_id == pick))) == 0
    print(f"selection pinning control: {time.monotonic() - started:.1f}s")
