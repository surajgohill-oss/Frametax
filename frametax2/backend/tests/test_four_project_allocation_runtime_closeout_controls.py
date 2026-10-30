"""FOUR_PROJECT_ALLOCATION_RUNTIME_CLOSEOUT controls.

A. cache / fingerprint correctness: every module whose ARITHMETIC decides the allocation, cap and labour-basis economics is in the pricing-source digest, and a real change to a fact,
   a rule or that source changes the fingerprint (while an unchanged project reuses its result and an unrelated project is untouched).
B. the agreed planning default is CONSUMED by pricing, labelled ASSUMED_FOR_PLANNING, scoped to a routed segment's own lines, and never promoted to a stated fact or a guaranteed entitlement.

Every expected dollar figure is hand-computed in the test. DB cases use isolated, rolled-back synthetic projects on ``frametax2_pytest`` only."""
from __future__ import annotations

import importlib
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.calculators.allocation_pricing import AccountAllocation, AssignmentKind, price_segment
from app.calculators.canadian_labour_basis import (
    ASSUMABLE_CATEGORIES, basis_status, derive_canadian_labour_basis, planning_presumption, to_amount_facts, to_planning_amount_facts,
)
from app.models.enums import ProjectFactSourceType
from app.models.project_fact import ProjectFact
from app.services import canonical_runtime_attribution as attribution
from tests.isolated_records import create_synthetic_project, isolated_session

PSTC, RATE = "ca_federal_pstc", 0.16


# ── A. the digest covers the arithmetic ────────────────────────────────────────────────────────

ALLOCATION_ARITHMETIC_MODULES = (
    "app.calculators.per_payee_limits", "app.calculators.canadian_labour_basis", "app.calculators.line_allocations", "app.calculators.ny_atl_individual_cap",
    "app.calculators.scenario_facts", "app.calculators.locality", "app.services.resolved_facts", "app.services.canonical_project_economics",
)


def test_every_module_that_decides_allocation_cap_and_labour_basis_arithmetic_is_in_the_pricing_source_digest():
    covered = set(attribution._SEMANTIC_PRICING_MODULES)
    for module in ALLOCATION_ARITHMETIC_MODULES:
        assert module in covered, f"{module} can change served economics without invalidating a retained result"
    for module in covered:
        assert importlib.import_module(module).__file__, module


@pytest.mark.parametrize("module", ALLOCATION_ARITHMETIC_MODULES)
def test_changing_the_source_of_a_covered_module_changes_the_digest(module, monkeypatch, tmp_path):
    """The old cap arithmetic cannot be served as current: editing ANY of these sources moves the digest, hence every fingerprint."""
    original_path = Path(importlib.import_module(module).__file__)
    attribution.pricing_source_digest.cache_clear()
    before = attribution.pricing_source_digest()
    edited = tmp_path / original_path.name
    edited.write_bytes(original_path.read_bytes() + b"\n# an arithmetic edit\n")
    real = attribution._module_path
    monkeypatch.setattr(attribution, "_module_path", lambda name: edited if name == module else real(name))
    attribution.pricing_source_digest.cache_clear()
    try:
        assert attribution.pricing_source_digest() != before
    finally:
        monkeypatch.undo()
        attribution.pricing_source_digest.cache_clear()
    assert attribution.pricing_source_digest() == before, "restoring the source restores the identical digest (nothing else moved it)"


# ── B. the planning default is consumed, labelled, scoped ──────────────────────────────────────

def _facts(rows):
    return [SimpleNamespace(fact_key=f"line_fact:{lid}:{field}", value=str(value)) for lid, field, value in rows]


def _line(lid, amount, category):
    return SimpleNamespace(line_id=lid, amount_usd=amount, spend_category=category, is_memo=False)


PROJECT_LINES = [_line("L1", 400_000.0, "atl_director"), _line("L2", 1_000_000.0, "btl_crew_labor"), _line("L3", 200_000.0, "btl_nonresident_labor"), _line("L4", 500_000.0, "production")]
CODES = {"L1": ("1000", "atl_director"), "L2": ("3000", "btl_crew_labor"), "L3": ("4000", "btl_nonresident_labor"), "L4": ("5000", "production"), "L5": ("3500", "btl_crew_labor")}


def _amount_facts(lines, rows, *, nonlocal_scenario=False):
    gross = sum(l.amount_usd for l in lines)
    assumable = frozenset() if nonlocal_scenario else frozenset(l.line_id for l in lines if l.spend_category in ASSUMABLE_CATEGORIES)
    result = derive_canadian_labour_basis(lines, _facts(rows), gross, assumable_line_ids=assumable)
    return to_planning_amount_facts(result), gross


def _segment(lines, facts, gross, only=None):
    chosen = [l for l in lines if only is None or l.line_id in only]
    allocations = [AccountAllocation(account_code=CODES[l.line_id][0], description=l.line_id, amount_usd=l.amount_usd, component="principal_photography", jurisdiction_code="XX",
                                     assignment_kind=AssignmentKind.FIXED, rationale="probe", governing_decision="x", line_id=l.line_id, spend_category=l.spend_category) for l in chosen]
    return price_segment(jurisdiction_code="XX", program_slug=PSTC, allocations=allocations, spend_category_by_code={CODES[l.line_id][0]: l.spend_category for l in chosen},
                         offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=gross, amount_facts=facts)


def _assumption(segment):
    return [p for p in segment.presumed_facts if p.get("condition_id") == "ca-pstc-labour-share-assumed"]


def test_with_nothing_stated_the_planning_default_prices_only_the_unstated_below_the_line_crew_and_says_so():
    """Hand: only L2 (btl_crew_labor, 1,000,000) is assumable -> basis 1,000,000 x 100%; PSTC 16% -> 160,000. The atl_director (400,000) and the budget-classified non-resident
    labour (200,000) are never defaulted. The superseded undisclosed behaviour priced 16% of 1,600,000 = 256,000 with no disclosure."""
    facts, gross = _amount_facts(PROJECT_LINES, [])
    assert facts["ca_federal_pstc_qualified_labour_usd"] == 1_000_000.0 and facts["ca_federal_pstc_assumed_labour_usd"] == 1_000_000.0
    assert "ca_federal_pstc_stated_labour_usd" not in facts and "ca_federal_pstc_qualified_labour_usd" not in to_amount_facts(derive_canadian_labour_basis(PROJECT_LINES, [], gross)), "nothing is stated"
    segment = _segment(PROJECT_LINES, facts, gross)
    assert segment.executable and segment.incentive_floor_usd == pytest.approx(1_000_000.0 * RATE) == pytest.approx(160_000.0)
    (entry,) = _assumption(segment)
    assert entry["basis_status"] == "ASSUMED_FOR_PLANNING" and entry["assumed_usd"] == 1_000_000.0 and entry["stated_usd"] == 0.0
    assert "not a residency fact" in entry["note"] and "never assumed" in entry["note"]
    assert "UNKNOWN share" in entry["note"] and "historical source data" in entry["note"] and "does not determine eligibility for the prospective production" in entry["note"]
    assert segment.allocated_usd == pytest.approx(gross), "the gross budget is conserved"
    assert basis_status(facts) == "ASSUMED_FOR_PLANNING"


def test_a_fully_stated_basis_is_priced_as_stated_with_no_assumption_layered_on_it():
    """L2 stated 40% resident and 100% performed in Canada -> intersection exactly 40% -> 400,000 x 16% = 64,000; nothing assumed."""
    facts, gross = _amount_facts(PROJECT_LINES, [("L2", "canadian_resident_share_pct", 40.0), ("L2", "service_in_canada_share_pct", 100.0)])
    assert facts["ca_federal_pstc_qualified_labour_usd"] == 400_000.0 and "ca_federal_pstc_assumed_labour_usd" not in facts
    segment = _segment(PROJECT_LINES, facts, gross)
    assert segment.incentive_floor_usd == pytest.approx(64_000.0) and not _assumption(segment)
    assert basis_status(facts) == "PRODUCER_STATED" and basis_status(facts, "EVIDENCED") == "EVIDENCED"


def test_an_explicit_zero_percent_is_a_stated_zero_not_an_unknown_and_nothing_is_priced():
    facts, gross = _amount_facts(PROJECT_LINES, [("L2", "canadian_resident_share_pct", 0.0)])
    assert "ca_federal_pstc_qualified_labour_usd" not in facts and "ca_federal_pstc_assumed_labour_usd" not in facts
    segment = _segment(PROJECT_LINES, facts, gross)
    assert not segment.incentive_floor_usd and not _assumption(segment), "a stated 0% outranks the default"


def test_a_stated_contrary_fact_outranks_the_default_and_the_scenario_election_removes_it():
    deferred, gross = _amount_facts(PROJECT_LINES, [("L2", "payment_status", "deferred")])
    assert "ca_federal_pstc_qualified_labour_usd" not in deferred, "a deferred amount is not a labour expenditure, assumed or not"
    scenario, _ = _amount_facts(PROJECT_LINES, [], nonlocal_scenario=True)
    assert "ca_federal_pstc_qualified_labour_usd" not in scenario and not _segment(PROJECT_LINES, scenario, gross).incentive_floor_usd, "scenario_btl_nonlocal: BTL is not hired locally, nothing is assumed"


def test_budget_classified_non_resident_labour_and_above_the_line_roles_are_never_assumed():
    lines = [_line("L1", 400_000.0, "atl_director"), _line("L3", 200_000.0, "btl_nonresident_labor"), _line("L4", 500_000.0, "production")]
    facts, gross = _amount_facts(lines, [])
    assert "ca_federal_pstc_qualified_labour_usd" not in facts and "ca_federal_pstc_assumed_labour_usd" not in facts
    assert not _segment(lines, facts, gross).incentive_floor_usd


def test_a_routed_segment_takes_only_its_own_lines_never_the_whole_projects_figure():
    """L2 (1,000,000) stated 40%/100% = 400,000 stated; L5 (500,000) unstated -> assumed 500,000. Whole project: 900,000 x 16% = 144,000.
    A segment holding only L2: 400,000 x 16% = 64,000 and NO assumption (L5 is not in it). A segment holding only L5: 500,000 x 16% = 80,000, assumed_usd 500,000."""
    lines = PROJECT_LINES + [_line("L5", 500_000.0, "btl_crew_labor")]
    facts, gross = _amount_facts(lines, [("L2", "canadian_resident_share_pct", 40.0), ("L2", "service_in_canada_share_pct", 100.0)])
    assert facts["ca_federal_pstc_qualified_labour_usd"] == 900_000.0 and facts["ca_federal_pstc_assumed_labour_usd"] == 500_000.0 and facts["ca_federal_pstc_stated_labour_usd"] == 400_000.0
    whole = _segment(lines, facts, gross)
    assert whole.incentive_floor_usd == pytest.approx(144_000.0)
    (whole_entry,) = _assumption(whole)
    assert whole_entry["assumed_usd"] == 500_000.0 and whole_entry["stated_usd"] == 400_000.0
    only_stated = _segment(lines, facts, gross, only={"L2"})
    assert only_stated.incentive_floor_usd == pytest.approx(64_000.0) and not _assumption(only_stated)
    only_assumed = _segment(lines, facts, gross, only={"L5"})
    assert only_assumed.incentive_floor_usd == pytest.approx(80_000.0) and _assumption(only_assumed)[0]["assumed_usd"] == 500_000.0
    assert whole.incentive_floor_usd == pytest.approx(only_stated.incentive_floor_usd + only_assumed.incentive_floor_usd), "the pieces conserve the whole"


def test_the_stack_leg_disclosure_is_the_same_entry_the_direct_segment_carries():
    facts, gross = _amount_facts(PROJECT_LINES, [])
    direct = _assumption(_segment(PROJECT_LINES, facts, gross))[0]
    stack = planning_presumption(facts)
    assert {k: stack[k] for k in ("condition_id", "state", "basis_status", "assumed_usd", "stated_usd", "note")} == {k: direct[k] for k in ("condition_id", "state", "basis_status", "assumed_usd", "stated_usd", "note")}
    assert planning_presumption({"ca_federal_pstc_stated_labour_usd": 5.0}) is None, "a stated basis has nothing to disclose"


def test_an_explicit_project_level_basis_override_is_priced_as_stated_with_no_assumption():
    """The legacy path (a stated amount fact, no line fractions) keeps its figure and its trust: 700,000 x 16% = 112,000, no assumption."""
    segment = _segment(PROJECT_LINES, {"ca_federal_pstc_qualified_labour_usd": 700_000.0}, 2_100_000.0, only={"L2"})
    assert segment.executable and segment.incentive_floor_usd == pytest.approx(112_000.0)
    assert not _assumption(segment)


# ── A/B on the served pipeline (isolated DB) ───────────────────────────────────────────────────

STACK_LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
               ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("4000", "VFX", "vfx", "post", 300_000.0))


async def _entries(db, pid):
    from tests.isolated_records import served_structures
    return await served_structures(db, pid)


async def _pstc_entries(db, pid):
    entries = await _entries(db, pid)
    alone = next(e for e in entries if e["program_slugs"] == [PSTC] and e["candidate_status"] == "PRICED")
    stack = next((e for e in entries if e["structure_type"] == "multi_program" and PSTC in e["program_slugs"] and e["candidate_status"] == "PRICED"), None)
    return alone, stack


@pytest.mark.asyncio
async def test_served_economics_carry_the_assumed_planning_disclosure_and_stating_the_share_changes_certainty_not_dollars():
    """Direct and stack legs carry the same ASSUMED_FOR_PLANNING entry; stating 100% / 100% on the crew line (which is the assumption) leaves the planning dollars identical and clears it."""
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import evaluate_project
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=STACK_LINES, home_code="CA-ON")
        project_id = uuid.UUID(pid)
        assert (await evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE"
        alone, stack = await _pstc_entries(db, pid)
        crew = 1_500_000.0
        assert alone["confirmed_incentive_floor_usd"] == pytest.approx(crew * RATE) == pytest.approx(240_000.0), "hand: assumed crew 1,500,000 x 16%; the 400,000 director fee is not defaulted"
        mine = [m for m in alone["claim_base_missing_facts"] if m["fact_id"] == "ca-pstc-labour-share-assumed"]
        assert len(mine) == 1 and "ASSUMED FOR PLANNING" in mine[0]["note"] and "not a residency fact" in mine[0]["note"]
        assert alone["economics_certainty"] == "CONDITIONAL"
        if stack is not None:
            assert "ca-pstc-labour-share-assumed" in {m["fact_id"] for m in stack["claim_base_missing_facts"]}, "the stack leg carries the same disclosure"
        lines = (await _crew_line(db, project_id))
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": lines, "field": "canadian_resident_share_pct", "value": 100.0}, {"line_id": lines, "field": "service_in_canada_share_pct", "value": 100.0}])
        await evaluate_project(db, project_id)
        alone2, _ = await _pstc_entries(db, pid)
        assert alone2["confirmed_incentive_floor_usd"] == pytest.approx(alone["confirmed_incentive_floor_usd"]), "stating what was assumed changes the certainty, never the planning dollars"
        assert "ca-pstc-labour-share-assumed" not in {m["fact_id"] for m in alone2["claim_base_missing_facts"]}


async def _crew_line(db, project_id):
    from app.services.line_inputs import line_amounts
    lines = await line_amounts(db, project_id)
    return next(k for k, v in lines.items() if v["category"] == "btl_crew_labor")


@pytest.mark.asyncio
async def test_fingerprint_follows_every_allocation_share_payee_and_scenario_input_and_only_that_projects():
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import current_generation_fingerprint, evaluate_project
    async with isolated_session() as db:
        a = uuid.UUID(await create_synthetic_project(db, lines=STACK_LINES, home_code="CA-ON"))
        b = uuid.UUID(await create_synthetic_project(db, lines=STACK_LINES, home_code="CA-ON"))
        await evaluate_project(db, a)
        await evaluate_project(db, b)
        base_a, base_b = await current_generation_fingerprint(db, a), await current_generation_fingerprint(db, b)
        assert base_a and base_b
        assert await current_generation_fingerprint(db, a) == base_a, "unchanged inputs: the identical fingerprint on every read"
        crew = await _crew_line(db, a)

        async def changed(edit):
            before = await current_generation_fingerprint(db, a)
            await edit()
            after = await current_generation_fingerprint(db, a)
            assert after != before
            return after

        await changed(lambda: npf.write_ny_program_facts(db, a, line_facts=[{"line_id": crew, "field": "canadian_resident_share_pct", "value": 40.0}, {"line_id": crew, "field": "service_in_canada_share_pct", "value": 100.0}]))
        await changed(lambda: npf.write_ny_program_facts(db, a, line_facts=[{"line_id": crew, "field": "canadian_resident_share_pct", "value": 60.0}]))
        await changed(lambda: npf.write_ny_program_facts(db, a, line_facts=[{"line_id": crew, "field": "payee_type", "value": "personal_service_corp"}]))

        async def nonlocal_on():
            db.add(ProjectFact(id=uuid.uuid4(), project_id=a, fact_key="scenario_btl_nonlocal", value="true", source_type=ProjectFactSourceType.USER_OVERRIDE))
            await db.flush()
        await changed(nonlocal_on)
        assert await current_generation_fingerprint(db, b) == base_b, "an unrelated project's fingerprint does not move"


@pytest.mark.asyncio
async def test_a_changed_input_regenerates_once_and_an_unchanged_one_reuses_the_identical_generation_without_duplicate_rows():
    from sqlalchemy import func, select
    from app.models.production import EvaluationGenerationSummary, ProductionStructure, StructureCalculationResult
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import evaluate_project
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, lines=STACK_LINES, home_code="CA-ON"))

        async def counts():
            gens = (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary).where(EvaluationGenerationSummary.project_id == project_id))).scalar_one()
            rows = (await db.execute(select(func.count()).select_from(StructureCalculationResult).join(ProductionStructure, StructureCalculationResult.structure_id == ProductionStructure.id)
                                     .where(ProductionStructure.project_id == project_id))).scalar_one()
            return gens, rows

        await evaluate_project(db, project_id)
        first = await counts()
        for _ in range(3):                                           # repeated opens / evaluations of unchanged inputs
            await evaluate_project(db, project_id)
        assert await counts() == first, "unchanged inputs reuse the identical generation: no new generation, no duplicate rows"
        crew = await _crew_line(db, project_id)
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, "field": "canadian_resident_share_pct", "value": 50.0}, {"line_id": crew, "field": "service_in_canada_share_pct", "value": 100.0}])
        from app.services.canonical_production_view import build_production_and_structures
        for _ in range(3):                                           # repeated API / browser reads of the now-stale project
            db.expunge_all()
            view = await build_production_and_structures(db, project_id, allow_retained=True)
        assert view["production"]["evaluation_freshness"] == "STALE" and await counts() == first, "reading a stale project (any number of times) never regenerates"
        await evaluate_project(db, project_id)
        second = await counts()
        assert second[0] == first[0] + 1 and second[1] > first[1], "the changed share regenerates exactly one new generation"
        await evaluate_project(db, project_id)
        assert await counts() == second, "and the next evaluation of the new inputs reuses it"
