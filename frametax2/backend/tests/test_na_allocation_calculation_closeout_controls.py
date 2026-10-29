"""NA_ALLOCATION_CALCULATION_AND_AFFECTED_CONTROL_CLOSEOUT controls.

A. percentage-of-line Canadian labour eligibility (stated shares priced; an ASSUMED planning default is shown, never priced or stored);
B. per-payee caps conserve a partially allocated line (the unallocated remainder is never capped as one person's);
C. an allocation save / reset never deletes the line's payee_type or unrelated facts.

Every expected figure is hand-computed in the test. DB-free cases are pure; DB cases use isolated, rolled-back synthetic projects on ``frametax2_pytest`` only."""
from __future__ import annotations

import math
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.calculators import canadian_labour_basis as clb
from app.calculators.canadian_labour_basis import LineLabourFacts, _line_eligible_amount, derive_canadian_labour_basis
from app.calculators.ny_atl_individual_cap import limits_facts_from_amount_facts, payee_amount_facts
from app.calculators.qualification_derivation import BudgetLine, ProductionFacts, derive_qualification_register
from app.calculators.qualification_model import QualificationState
from app.data.program_spend_rules import get_program_rules, resolve_program_doctrine
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact
from app.services import ny_producer_facts as npf
from app.services.canonical_project_economics import build_project_economic_inputs
from app.services.line_inputs import line_inputs_view
from tests.isolated_records import create_synthetic_project, isolated_session

Q, X = QualificationState.QUALIFIES, QualificationState.EXCLUDED
PSTC = "ca_federal_pstc"
GA, CO = "us_ga_film_credit", "us_co_film_incentive"
EMPLOYEE = 1
LINES = (("1000", "CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_resident_labor", "btl", 1_000_000.0),
         ("3200", "EQUIPMENT", "btl_equipment_rental", "btl", 700_000.0))


# ── A. percentage-of-line eligibility (DB-free) ───────────────────────────────────────────────

def _f(**kw):
    return LineLabourFacts(line_id="L", **kw)


def test_sixty_percent_qualifying_labour_is_a_sixty_thousand_basis_and_the_gross_is_untouched():
    """$100,000 line, 60% resident, 100% performed in Canada -> relevant basis $100,000 x 60% = $60,000 (the intersection is exact because one condition covers the whole line)."""
    eligible, reason = _line_eligible_amount(100_000.0, _f(resident_share_pct=60.0, in_canada_share_pct=100.0), program_slug=PSTC)
    assert eligible == 60_000.0
    assert "exactly 60%" in reason and "60% of the line ($60,000.00 of $100,000.00)" in reason

    lines = [SimpleNamespace(line_id="A", amount_usd=100_000.0, spend_category="btl_crew_labor", is_memo=False),
             SimpleNamespace(line_id="B", amount_usd=50_000.0, spend_category="btl_crew_labor", is_memo=False)]
    rows = [SimpleNamespace(fact_key=f"line_fact:A:{k}", value=v) for k, v in (("canadian_resident_share_pct", "60.0"), ("service_in_canada_share_pct", "100.0"))]
    rows += [SimpleNamespace(fact_key=f"line_fact:B:{k}", value=v) for k, v in (("canadian_status", "resident_citizen"), ("service_location", "in_canada"))]
    res = derive_canadian_labour_basis(lines, rows, 150_000.0)
    assert res.evidenced_eligible_labour_usd[PSTC] == 110_000.0, "60,000 from the partial line + 50,000 from the fully stated line"
    assert res.raw_atl_amount_usd[PSTC] == 150_000.0 and res.net_production_cost_usd == 150_000.0, "the gross and the unrelated component are unchanged"
    by_line = {d.line_id: d for d in res.line_dispositions if d.program_slug == PSTC}
    assert by_line["A"].eligible_usd == 60_000.0 and by_line["A"].excluded_usd == 40_000.0 and by_line["A"].eligible_share_pct == 60.0
    assert by_line["B"].eligible_usd == 50_000.0


def test_two_partial_shares_never_invent_an_intersection():
    """70% resident and 60% in Canada: the dollars meeting BOTH are somewhere in 30%..60%. Product (42%) and minimum (60%) are not bases; the guaranteed overlap (30%) is the floor."""
    eligible, reason = _line_eligible_amount(100_000.0, _f(resident_share_pct=70.0, in_canada_share_pct=60.0), program_slug=PSTC)
    assert eligible == 30_000.0 and eligible not in (42_000.0, 60_000.0)
    assert "from 30% to 60%" in reason and "intersection NOT stated" in reason
    # an explicit intersection settles it, within the bounds
    assert _line_eligible_amount(100_000.0, _f(resident_share_pct=70.0, in_canada_share_pct=60.0, intersection_share_pct=55.0), program_slug=PSTC)[0] == 55_000.0
    # one share at 100% or 0% makes the other the exact intersection
    assert _line_eligible_amount(100_000.0, _f(resident_share_pct=100.0, in_canada_share_pct=40.0), program_slug=PSTC)[0] == 40_000.0
    assert _line_eligible_amount(100_000.0, _f(resident_share_pct=0.0, in_canada_share_pct=100.0), program_slug=PSTC)[0] == 0.0


def test_a_missing_condition_is_unknown_not_yes_and_a_contradiction_is_not_a_choice():
    only_resident = _line_eligible_amount(100_000.0, _f(resident_share_pct=60.0), program_slug=PSTC)
    assert only_resident[0] == 0.0 and "service location of this line is not stated" in only_resident[1]
    for kw in ({"canadian_status": "nonresident", "resident_share_pct": 40.0}, {"canadian_status": "resident_pr", "resident_share_pct": 90.0},
               {"service_location": "outside_canada", "in_canada_share_pct": 10.0}, {"service_location": "in_canada", "in_canada_share_pct": 90.0}):
        eligible, reason = _line_eligible_amount(100_000.0, _f(**{"resident_share_pct": 100.0, "in_canada_share_pct": 100.0, **kw}), program_slug=PSTC)
        assert eligible == 0.0 and "conflict" in reason


def test_the_share_scales_the_look_through_wages_and_assistance_is_deducted_once():
    """Loan-out, look-through wages $80,000 for the whole line, 50% resident + 100% in Canada, $10,000 assistance on the line:
    share basis $200,000 x 50% = $100,000; look-through cap $80,000 x 50% = $40,000; eligible = min = $40,000; assistance once -> $30,000."""
    facts = _f(resident_share_pct=50.0, in_canada_share_pct=100.0, payee_type="loan_out_corp", look_through_wages_usd=80_000.0, assistance_usd=10_000.0)
    assert _line_eligible_amount(200_000.0, facts, program_slug=PSTC)[0] == 30_000.0


def test_cptc_is_not_gated_by_the_new_shares_because_no_cptc_residency_test_was_read():
    facts = _f(resident_share_pct=0.0, in_canada_share_pct=0.0, canadian_status="nonresident")
    assert _line_eligible_amount(100_000.0, facts, program_slug="ca_federal_cptc")[0] == 100_000.0


# ── A. assumed planning default is separate from evidence (DB-free) ───────────────────────────

def _derive(rows, assumable=frozenset({"CREW"}), cat="btl_crew_labor"):
    lines = [SimpleNamespace(line_id="CREW", amount_usd=100_000.0, spend_category=cat, is_memo=False),
             SimpleNamespace(line_id="WRITER", amount_usd=40_000.0, spend_category="atl_writer", is_memo=False)]
    return derive_canadian_labour_basis(lines, [SimpleNamespace(fact_key=k, value=v) for k, v in rows], 140_000.0, assumable_line_ids=assumable | {"WRITER"})


def test_the_assumed_default_is_a_planning_figure_never_the_priced_or_stated_figure():
    res = _derive([])
    assert res.evidenced_eligible_labour_usd[PSTC] == 0.0 and clb.to_amount_facts(res) == {}, "nothing stated -> nothing priced (Unknown is not Yes)"
    assert res.planning_eligible_labour_usd[PSTC] == 100_000.0, "BTL crew planned at an ASSUMED 100%; the ATL writer is never defaulted"
    crew = next(d for d in res.line_dispositions if d.line_id == "CREW" and d.program_slug == PSTC)
    assert crew.eligible_usd == 0.0 and crew.planning_eligible_usd == 100_000.0 and "ASSUMED planning default" in crew.planning_reason
    writer = next(d for d in res.line_dispositions if d.line_id == "WRITER" and d.program_slug == PSTC)
    assert writer.planning_eligible_usd is None, "ATL residency stays separately evidenced"
    assert res.assumed_line_ids == ["CREW"]


def test_a_stated_share_outranks_the_default_and_an_explicit_zero_is_a_real_zero():
    zero = _derive([("line_fact:CREW:canadian_resident_share_pct", "0.0")])
    assert zero.planning_eligible_labour_usd[PSTC] == 0.0 and zero.evidenced_eligible_labour_usd[PSTC] == 0.0
    partial = _derive([("line_fact:CREW:canadian_resident_share_pct", "40.0")])
    assert partial.planning_eligible_labour_usd[PSTC] == 40_000.0, "stated 40% resident + ASSUMED 100% in Canada -> exactly 40%"
    assert partial.evidenced_eligible_labour_usd[PSTC] == 0.0, "the location is still unstated, so nothing is priced"
    stated = _derive([("line_fact:CREW:canadian_resident_share_pct", "40.0"), ("line_fact:CREW:service_in_canada_share_pct", "100.0")])
    assert stated.evidenced_eligible_labour_usd[PSTC] == 40_000.0 and stated.planning_eligible_labour_usd[PSTC] == 40_000.0 and stated.assumed_line_ids == []
    assert clb.to_amount_facts(stated)["ca_federal_pstc_qualified_labour_usd"] == 40_000.0
    nonresident_class = _derive([], assumable=frozenset({"CREW"}), cat="btl_nonresident_labor")
    assert nonresident_class.planning_eligible_labour_usd[PSTC] == 0.0, "a line the budget classes as non-resident labour is never defaulted to resident"


# ── B. per-payee conservation (DB-free) ───────────────────────────────────────────────────────

def _reg(slug, rows, allocations):
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    pf = ProductionFacts(jurisdiction_code="US", payee_allocations_by_line=tuple(allocations))
    return derive_qualification_register(lines, program_slug=slug, facts=pf, rate=0.2, rules=get_program_rules(slug), doctrine=resolve_program_doctrine(slug).doctrine)


def _sum(reg, state, needle="", line=None):
    return round(sum(a.amount_usd for a in reg if a.state == state and needle in a.reason and (line is None or a.line_id == line)), 2)


def _conserved(reg, rows):
    for i, (_c, amount) in enumerate(rows):
        assert round(sum(a.amount_usd for a in reg if a.line_id == f"L{i}"), 2) == amount, f"line L{i} is conserved across qualified + excluded entries"


def test_a_partially_allocated_line_is_not_capped_as_if_one_person_owned_all_of_it():
    """$1,000,000 line, Georgia W-2 cap $500,000. A holds $300,000 of it: A is under the cap, so NOTHING is excluded (the old arithmetic treated A as owning the whole line and cut $500,000)."""
    rows = (("atl_director", 1_000_000.0),)
    reg = _reg(GA, rows, [("L0", ((1, 300_000.0, EMPLOYEE),))])
    assert _sum(reg, X) == 0.0 and _sum(reg, Q, line="L0") == 1_000_000.0
    assert _sum(reg, Q, "UNRESOLVED", line="L0") == 1_000_000.0, "the unallocated $700,000 is not tested and says so; nothing is fabricated for it"
    _conserved(reg, rows)


def test_a_partially_allocated_line_cuts_only_the_identified_persons_excess():
    """A holds $700,000 of a $1,000,000 line: over the $500,000 cap by $200,000. Excluded $200,000; qualified $800,000 = A's $500,000 + the $300,000 remainder, which is not capped and is disclosed."""
    rows = (("atl_director", 1_000_000.0),)
    reg = _reg(GA, rows, [("L0", ((1, 700_000.0, EMPLOYEE),))])
    assert _sum(reg, X, "per person") == 200_000.0 and _sum(reg, Q, line="L0") == 800_000.0
    assert "not allocated to an identified person" in " ".join(a.reason for a in reg if a.state == Q)
    _conserved(reg, rows)


def test_two_known_payees_are_each_capped_once():
    """One $1,200,000 line: A $600,000 and B $600,000 (both W-2). Each is $100,000 over the $500,000 cap -> $200,000 excluded in total, $1,000,000 qualified."""
    rows = (("atl_director", 1_200_000.0),)
    reg = _reg(GA, rows, [("L0", ((1, 600_000.0, EMPLOYEE), (2, 600_000.0, EMPLOYEE)))])
    assert _sum(reg, X, "per person") == 200_000.0 and _sum(reg, Q, line="L0") == 1_000_000.0
    assert "UNRESOLVED" not in " ".join(a.reason for a in reg if a.state == Q), "the line is fully allocated: nothing is left untested"
    _conserved(reg, rows)


def test_one_person_across_two_partially_allocated_lines_is_capped_on_their_total_once():
    """A holds $400,000 of a $900,000 line and $400,000 of a $500,000 line: A's total is $800,000, $300,000 over. Excluded $300,000 in total; every line conserved."""
    rows = (("atl_director", 900_000.0), ("atl_writer", 500_000.0))
    reg = _reg(GA, rows, [("L0", ((1, 400_000.0, EMPLOYEE),)), ("L1", ((1, 400_000.0, EMPLOYEE),))])
    assert _sum(reg, X, "per person") == 300_000.0
    _conserved(reg, rows)


def test_a_line_allocated_in_full_divides_exactly_as_before():
    rows = (("atl_director", 1_000_000.0),)
    reg = _reg(GA, rows, [("L0", ((1, 750_000.0, EMPLOYEE), (2, 250_000.0, EMPLOYEE)))])
    assert _sum(reg, X, "per person") == 250_000.0 and _sum(reg, Q, line="L0") == 750_000.0
    _conserved(reg, rows)


def test_an_aggregate_percentage_is_not_a_payee_identity():
    """Percentage-of-line facts create no payee ordinal, no allocation and no cap evidence: an over-cap account with only shares stays UNRESOLVED at its qualified amount (no headcount, equal split or exemption)."""
    fact_rows = [SimpleNamespace(fact_key=f"line_fact:L0:{k}", value="60.0") for k in ("canadian_resident_share_pct", "service_in_canada_share_pct", "resident_and_in_canada_share_pct")]
    derived = payee_amount_facts(fact_rows, {"L0"}, {"L0": 1_000_000.0})
    assert derived == {}, "no payee / allocation fact is derived from a percentage"
    rows = (("atl_director", 1_000_000.0),)
    reg = _reg(GA, rows, [])
    assert _sum(reg, X) == 0.0 and _sum(reg, Q, "UNRESOLVED", line="L0") == 1_000_000.0


def test_direct_and_stack_legs_consume_the_same_resolved_cap_basis():
    """The numeric facts become ProductionFacts through one function; a home leg and a relocated stack leg (scenario BTL default differs) exclude the same dollars on the same ATL accounts."""
    amounts = {"alloc_n:L0": 1.0, "alloc_ord:L0:0": 1.0, "alloc_usd:L0:0": 700_000.0, "alloc_type:L0:0": 1.0}
    kwargs = limits_facts_from_amount_facts(amounts)
    assert kwargs["payee_allocations_by_line"] == (("L0", ((1, 700_000.0, 1),)),)
    rows = (("atl_director", 1_000_000.0), ("btl_crew_labor", 300_000.0))
    lines = [BudgetLine(account_code=str(1000 + i), description=c.upper(), amount_usd=a, spend_category=c, is_memo=False, line_id=f"L{i}") for i, (c, a) in enumerate(rows)]
    out = []
    for local in (False, True):
        pf = ProductionFacts(jurisdiction_code="US", scenario_local_btl=local, **kwargs)
        reg = derive_qualification_register(lines, program_slug=GA, facts=pf, rate=0.2, rules=get_program_rules(GA), doctrine=resolve_program_doctrine(GA).doctrine)
        out.append((_sum(reg, X, "per person", line="L0"), _sum(reg, Q, line="L0")))
    assert out[0] == out[1] == (200_000.0, 800_000.0)


# ── A/C. persistence, reload, qualification, pricing input, disclosure (isolated DB) ───────────

async def _rows(session, pid):
    return dict((await session.execute(select(ProjectFact.fact_key, ProjectFact.value).where(ProjectFact.project_id == uuid.UUID(pid)))).all())


async def _line(session, pid, category):
    view = await line_inputs_view(session, uuid.UUID(pid), [PSTC])
    return next(l for l in view["lines"] if l["category"] == category), view


def _field(line, name):
    return next(f for f in line["fields"] if f["name"] == name)


async def test_assumed_to_zero_to_partial_to_reset_with_provenance_and_pricing_input():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        key = "ca_federal_pstc_qualified_labour_usd"
        crew, view = await _line(db, pid, "btl_resident_labor")
        lid = crew["line_id"]
        res_field = _field(crew, "canadian_resident_share_pct")

        # 1. nothing stated: ASSUMED 100% for planning only
        assert res_field["state"] == "ASSUMED" and res_field["value"] is None and res_field["assumed_pct"] == 100.0
        assert view["canadian_labour"]["stated_eligible_usd"] == 0.0 and view["canadian_labour"]["planning_eligible_usd"] == 1_000_000.0
        assert not [k for k in await _rows(db, pid) if "share_pct" in k], "an assumed share is never persisted as a fact"
        economics = (await build_project_economic_inputs(db, uuid.UUID(pid), read_only=True)).inputs
        assert key not in (economics.amount_facts or {}), "an assumption never reaches the priced inputs"
        gross = economics.gross_budget_usd

        # 2. explicit 0%: a stated real zero, not an unknown
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "canadian_resident_share_pct", "value": 0.0}])
        crew, view = await _line(db, pid, "btl_resident_labor")
        assert _field(crew, "canadian_resident_share_pct")["state"] == "STATED" and _field(crew, "canadian_resident_share_pct")["value"] == 0.0
        assert _field(crew, "canadian_resident_share_pct")["amount_usd"] == 0.0 and view["canadian_labour"]["planning_eligible_usd"] == 0.0

        # 3. explicit partial share: 40% resident + 100% in Canada, both stated -> $400,000 is priced; the gross is unchanged
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "canadian_resident_share_pct", "value": 40.0},
                                                                          {"line_id": lid, "field": "service_in_canada_share_pct", "value": 100.0}])
        crew, view = await _line(db, pid, "btl_resident_labor")
        assert _field(crew, "canadian_resident_share_pct")["amount_usd"] == 400_000.0 and _field(crew, "service_in_canada_share_pct")["amount_usd"] == 1_000_000.0
        assert view["canadian_labour"]["stated_eligible_usd"] == 400_000.0 == view["canadian_labour"]["planning_eligible_usd"]
        disposition = view["canadian_labour"]["lines"][lid]
        assert disposition["share_basis"] == "STATED" and disposition["eligible_share_pct"] == 40.0
        economics = (await build_project_economic_inputs(db, uuid.UUID(pid), read_only=True)).inputs
        assert economics.amount_facts[key] == 400_000.0 and economics.gross_budget_usd == gross, "qualification input reduced to the eligible basis; the gross is not"

        # 4. reset: both rows removed, back to ASSUMED planning, nothing priced
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "canadian_resident_share_pct", "value": None},
                                                                          {"line_id": lid, "field": "service_in_canada_share_pct", "value": None}])
        crew, view = await _line(db, pid, "btl_resident_labor")
        assert _field(crew, "canadian_resident_share_pct")["state"] == "ASSUMED" and view["canadian_labour"]["planning_eligible_usd"] == 1_000_000.0
        economics = (await build_project_economic_inputs(db, uuid.UUID(pid), read_only=True)).inputs
        assert key not in (economics.amount_facts or {})
        assert not [v for k, v in (await _rows(db, pid)).items() if "share_pct" in k and v not in (None, "")]


async def test_the_nonlocal_override_removes_the_assumed_default_and_atl_is_never_defaulted():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        cast, view = await _line(db, pid, "atl_cast")
        assert _field(cast, "canadian_resident_share_pct")["state"] == "UNKNOWN", "an above-the-line role is not defaulted"
        crew, _ = await _line(db, pid, "btl_resident_labor")
        assert _field(crew, "canadian_resident_share_pct")["state"] == "ASSUMED"
        db.add(ProjectFact(id=uuid.uuid4(), project_id=uuid.UUID(pid), fact_key="scenario_btl_nonlocal", value="true", value_type="boolean",
                           source_type=ProjectFactSourceType.USER_OVERRIDE.value, review_status=ReviewStatus.APPROVED.value))
        await db.flush()
        crew, view = await _line(db, pid, "btl_resident_labor")
        assert _field(crew, "canadian_resident_share_pct")["state"] == "UNKNOWN" and view["canadian_labour"]["planning_eligible_usd"] == 0.0


@pytest.mark.parametrize("bad", [-1.0, 100.01, 101, float("nan"), float("inf"), -float("inf"), "50", True])
async def test_an_invalid_percentage_is_rejected_atomically_with_zero_partial_writes(bad):
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        crew, _ = await _line(db, pid, "btl_resident_labor")
        lid = crew["line_id"]
        before = await _rows(db, pid)
        with pytest.raises(ValueError, match="canadian_resident_share_pct|service_in_canada_share_pct"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "role", "value": "other"},
                                                                             {"line_id": lid, "field": "canadian_resident_share_pct", "value": bad}])
        await db.flush()
        assert await _rows(db, pid) == before, "the valid role row of the same request was not written"


async def test_inconsistent_shares_and_unknown_keys_are_refused_before_any_write():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        crew, _ = await _line(db, pid, "btl_resident_labor")
        lid = crew["line_id"]
        before = await _rows(db, pid)
        # the intersection cannot exceed a condition, nor fall below the guaranteed overlap
        with pytest.raises(ValueError, match="cannot exceed"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[
                {"line_id": lid, "field": "canadian_resident_share_pct", "value": 50.0}, {"line_id": lid, "field": "resident_and_in_canada_share_pct", "value": 60.0}])
        with pytest.raises(ValueError, match="guaranteed overlap"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[
                {"line_id": lid, "field": "canadian_resident_share_pct", "value": 70.0}, {"line_id": lid, "field": "service_in_canada_share_pct", "value": 60.0},
                {"line_id": lid, "field": "resident_and_in_canada_share_pct", "value": 20.0}])
        with pytest.raises(ValueError, match="not a line-level fact"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "canadian_resident_percent", "value": 50.0}])
        with pytest.raises(ValueError, match="canadian_resident_share_pct"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": [{"payee_id": "A", "amount_usd": 1.0, "canadian_resident_share_pct": 50.0}]}])
        await db.flush()
        assert await _rows(db, pid) == before
        # a stored share constrains a later statement of the intersection (merged stored + incoming)
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "service_in_canada_share_pct", "value": 30.0}])
        with pytest.raises(ValueError, match="cannot exceed"):
            await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "resident_and_in_canada_share_pct", "value": 40.0}])


async def test_allocation_save_and_reset_preserve_payee_type_and_unrelated_facts_but_an_explicit_edit_changes_it():
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        crew, _ = await _line(db, pid, "btl_resident_labor")
        lid = crew["line_id"]
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[
            {"line_id": lid, "field": "payee_type", "value": "loan_out_corp"}, {"line_id": lid, "field": "canadian_status", "value": "resident_pr"},
            {"line_id": lid, "field": "canadian_resident_share_pct", "value": 80.0}, {"line_id": lid, "field": "role", "value": "other"}])
        await db.flush()

        def kept(rows):
            return {k: v for k, v in rows.items() if k.startswith(f"line_fact:{lid}:") and not k.endswith((":allocations", ":payee_id", ":payee_compensation_complete")) and v not in (None, "")}
        before = kept(await _rows(db, pid))
        assert before[f"line_fact:{lid}:payee_type"] == "loan_out_corp"
        # save allocations that state no payee_type
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": [{"payee_id": "A", "amount_usd": 600_000.0}, {"payee_id": "B", "amount_usd": 100_000.0}]}])
        await db.flush()
        assert kept(await _rows(db, pid)) == before, "saving allocations left payee_type, status, share and role untouched"
        # edit the allocations
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": [{"payee_id": "A", "amount_usd": 650_000.0, "payee_type": "employee"}]}])
        await db.flush()
        assert kept(await _rows(db, pid)) == before, "an allocation that states a person's type does not rewrite the line's classification"
        # reset (delete the override)
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_allocations=[{"line_id": lid, "allocations": None}])
        await db.flush()
        rows = await _rows(db, pid)
        assert kept(rows) == before and rows.get(f"line_fact:{lid}:allocations") in (None, "")
        # only an explicit producer edit of the fact itself changes it
        await npf.write_ny_program_facts(db, uuid.UUID(pid), line_facts=[{"line_id": lid, "field": "payee_type", "value": "employee"}])
        await db.flush()
        assert (await _rows(db, pid))[f"line_fact:{lid}:payee_type"] == "employee"
