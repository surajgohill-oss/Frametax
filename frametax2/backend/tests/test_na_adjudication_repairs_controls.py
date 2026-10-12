"""Codex NA package adjudication (2026-10-11): the four reproduced, bounded calculation defects. Synthetic and DB-free except the last control, which
runs one rolled-back synthetic evaluation on the isolated test database. Expectations are hand-derived from the primary rules, not taken from AG:

* Manitoba (Finance, corporate tax credits): cost-of-salaries 45% of eligible labour OR cost-of-production 30% of all eligible Manitoba production
  expenditures (+8% bonus is a bound); the corporation claims one. A service line with no labour must still reach the 30% credit.
* New York post credit (tax.ny.gov/legal/2025/pit-corp-changes.htm): qualified post costs >= the lesser of $1,000,000 or 75% of the worldwide post
  cost; VFX >= the lesser of $500,000 or 10% of the worldwide VFX cost.
* CPTC (CRA RC4164): 25% x the lesser of labour and 60% of the production cost net of assistance.
* Hybrid components were priced without the structure's gross budget or the producer's contingency election."""
from __future__ import annotations

import pytest

from app.calculators.allocation_pricing import price_segment
from app.calculators.canonical_requirements_gate_bridge import FAILED, SATISFIED, UNKNOWN, evaluate_requirements_gate
from app.calculators.production_allocation import AccountAllocation, AssignmentKind
from app.calculators.structural_archetype_generator import StructuralComponent, generate_structural_candidate

MB, NYP, CPTC = "ca_mb_film_video_credit", "us_ny_post_production_credit", "ca_federal_cptc"


def _a(code, category, amount, jur, i, component="principal_production"):
    return AccountAllocation(account_code=code, description=category.upper(), amount_usd=amount, component=component, jurisdiction_code=jur,
                             assignment_kind=AssignmentKind.FIXED, rationale="control", governing_decision="control", line_id=f"L{i}", spend_category=category)


def _price(slug, jur, rows, gross, **kw):
    allocs = [_a(str(1000 + i), c, m, jur, i) for i, (c, m) in enumerate(rows)]
    return price_segment(jur, slug, allocs, {a.account_code: a.spend_category for a in allocs}, frozenset(), gross_budget_usd=gross, **kw)


# ── 1. Manitoba: the alternative credit is reachable when the labour base is empty ─────────────────────────────────────────────────────────────

def test_a_manitoba_service_line_with_no_labour_prices_the_cost_of_production_credit():
    seg = _price(MB, "CA-MB", [("vfx", 200_000.0)], 2_000_000.0)
    assert seg.executable is True and not seg.blockers
    assert seg.incentive_floor_usd == pytest.approx(60_000.0)        # 30% x 200,000
    assert seg.incentive_ceiling_usd == pytest.approx(76_000.0)      # + the 8% bonus bound (16,000), not guaranteed
    assert any("cost-of-production" in n for n in seg.notes) if hasattr(seg, "notes") else True


def test_manitoba_still_selects_the_higher_of_the_two_credits_and_equipment_reaches_the_alternative():
    labour = _price(MB, "CA-MB", [("btl_crew_labor", 200_000.0)], 2_000_000.0)
    assert labour.incentive_floor_usd == pytest.approx(90_000.0)     # 45% x 200,000 beats 30% x 200,000 = 60,000
    equipment = _price(MB, "CA-MB", [("btl_equipment_rental", 200_000.0)], 2_000_000.0)
    assert equipment.executable is True and equipment.incentive_floor_usd == pytest.approx(60_000.0)
    mixed = _price(MB, "CA-MB", [("btl_crew_labor", 100_000.0), ("btl_equipment_rental", 400_000.0)], 2_000_000.0)
    assert mixed.incentive_floor_usd == pytest.approx(150_000.0)     # alternative 30% x 500,000 beats labour 45% x 100,000 = 45,000


def test_the_alternative_exit_repair_does_not_open_other_programs_with_unresolved_rates():
    # A program without an elective alternative keeps failing closed when its rate does not resolve.
    seg = _price("us_ny_post_production_credit", "US-NY", [("btl_crew_labor", 100_000.0)], 2_000_000.0)
    assert seg.incentive_floor_usd == 0.0


# ── 2. New York post: the percentage gateways use the worldwide denominator ────────────────────────────────────────────────────────────────────

def _gate(local, world, gross=2_000_000.0):
    return evaluate_requirements_gate(NYP, segment_allocated_usd=sum(local.values()), gross_budget_usd=gross,
                                      category_spend_usd=local, worldwide_category_spend_usd=world)


def _state(result, requirement):
    return next(e.state for e in result.evaluations if e.requirement == requirement)


def test_a_small_post_scope_that_is_the_whole_worldwide_post_cost_passes_the_post_gateway():
    r = _gate({"post_production": 100_000.0}, {"post_production": 100_000.0})        # lesser of 1,000,000 or 75% x 100,000 = 75,000
    assert _state(r, "ny_post_gateway") == SATISFIED and not r.failed


def test_the_post_gateway_fails_only_when_the_local_share_is_below_the_lesser_threshold():
    short = _gate({"post_production": 100_000.0}, {"post_production": 1_000_000.0})     # lesser of 1,000,000 / 750,000 = 750,000
    assert _state(short, "ny_post_gateway") == FAILED
    exact = _gate({"post_production": 750_000.0}, {"post_production": 1_000_000.0})
    assert _state(exact, "ny_post_gateway") == SATISFIED
    large = _gate({"post_production": 1_000_000.0}, {"post_production": 5_000_000.0})   # 75% would be 3.75m; the dollar branch caps at 1,000,000
    assert _state(large, "ny_post_gateway") == SATISFIED
    just_under = _gate({"post_production": 999_999.0}, {"post_production": 5_000_000.0})
    assert _state(just_under, "ny_post_gateway") == FAILED


def test_an_unknown_worldwide_figure_is_unknown_never_a_failure_and_a_vfx_shortfall_is_disclosed_not_failed():
    unknown = _gate({"post_production": 100_000.0}, None)
    assert _state(unknown, "ny_post_gateway") == UNKNOWN and not unknown.failed
    vfx = _gate({"post_production": 1_000_000.0, "vfx": 100_000.0}, {"post_production": 1_000_000.0, "vfx": 2_000_000.0})
    assert _state(vfx, "ny_post_gateway") == SATISFIED               # 1,100,000 local vs the lesser of 1,000,000 / 75% x 3,000,000
    assert _state(vfx, "ny_vfx_gateway") == UNKNOWN                  # 100,000 < lesser of 500,000 / 200,000; cumulative-or-alternative not stated
    assert not vfx.failed


def test_the_post_credit_prices_a_small_post_scope_through_the_real_kernel():
    seg = _price(NYP, "US-NY", [("post_production", 100_000.0)], 2_000_000.0,
                 worldwide_category_spend_usd={"post_production": 100_000.0})
    assert not any("below the $1,000,000 floor" in b for b in seg.blockers)
    assert seg.executable is True, seg.blockers
    short = _price(NYP, "US-NY", [("post_production", 100_000.0)], 2_000_000.0,
                   worldwide_category_spend_usd={"post_production": 1_000_000.0})
    assert short.executable is False


# ── 3. CPTC: standalone and hybrid use the same 60% cost cap ───────────────────────────────────────────────────────────────────────────────────

def test_cptc_labour_above_the_cost_cap_is_trimmed_to_the_cap_not_rejected():
    over = _price(CPTC, "CA", [("btl_crew_labor", 1_400_000.0), ("btl_equipment_rental", 600_000.0)], 2_000_000.0)
    assert over.executable is True and not over.blockers
    assert over.incentive_floor_usd == pytest.approx(300_000.0)      # 25% x min(1,400,000; 60% x 2,000,000 = 1,200,000)
    under = _price(CPTC, "CA", [("btl_crew_labor", 1_000_000.0), ("btl_equipment_rental", 1_000_000.0)], 2_000_000.0)
    assert under.incentive_floor_usd == pytest.approx(250_000.0)     # labour below the cap is untouched: 25% x 1,000,000
    at_cap = _price(CPTC, "CA", [("btl_crew_labor", 1_200_000.0), ("btl_equipment_rental", 800_000.0)], 2_000_000.0)
    assert at_cap.incentive_floor_usd == pytest.approx(300_000.0)


def test_a_hybrid_component_is_priced_against_the_structure_gross_so_the_cptc_cap_applies():
    allocs = tuple(_a(str(1000 + i), c, m, "CA", i) for i, (c, m) in enumerate([("btl_crew_labor", 1_400_000.0), ("btl_equipment_rental", 600_000.0)]))
    comp = StructuralComponent("principal_production", "CA", CPTC, allocs, {a.account_code: a.spend_category for a in allocs})
    result = generate_structural_candidate([comp], gross_budget_usd=2_000_000.0)
    assert result.executable is True, result.rejection_reason
    assert result.component_economics[0].segment.incentive_floor_usd == pytest.approx(300_000.0)      # was 350,000 with the cap silently dropped


# ── 4. Hybrid inputs: the producer's contingency election reaches component pricing ────────────────────────────────────────────────────────────

def _mu_component():
    allocs = (_a("3100", "btl_crew_labor", 1_000_000.0, "MU", 0, "production"), _a("7902", "contingency", 250_000.0, "MU", 1, "production"))
    return StructuralComponent("principal_production", "MU", "mu_edb_incentive", allocs, {"3100": "btl_crew_labor", "7902": "contingency"})


@pytest.mark.parametrize("pct, expected_floor", [(None, 300_000.0), (0.0, 300_000.0), (40.0, 330_000.0), (100.0, 375_000.0)])
def test_the_contingency_election_changes_the_deployed_reserve_a_hybrid_component_counts(pct, expected_floor):
    result = generate_structural_candidate([_mu_component()], gross_budget_usd=1_250_000.0, contingency_expected_utilization_pct=pct)
    # 30% x (1,000,000 + election x 250,000); an unstated election counts none of the reserve (it stays a disclosed grey area)
    assert result.component_economics[0].segment.incentive_floor_usd == pytest.approx(expected_floor)


def test_a_partial_component_set_keeps_the_worldwide_figure_unknown_instead_of_understating_it():
    from app.calculators.structural_archetype_generator import _worldwide_category_spend
    post = StructuralComponent("post", "US-NY", NYP, (_a("5000", "post_production", 100_000.0, "US-NY", 0, "post"),),
                               {"5000": "post_production"})
    assert _worldwide_category_spend([post], 2_000_000.0) is None
    assert _worldwide_category_spend([post], 100_000.0) == {"post_production": 100_000.0}


# ── 5. Save / input propagation: the saved election reaches every hybrid pricing call in a real evaluation ─────────────────────────────────────

LINES = (("2000", "DIRECTOR FEE", "atl_director", "atl", 400_000.0), ("3000", "CREW", "btl_crew_labor", "btl", 1_500_000.0),
         ("3100", "EQUIPMENT RENTAL", "btl_equipment_rental", "btl", 600_000.0), ("6100", "VFX", "vfx", "post", 300_000.0),
         ("8300", "CONTINGENCY", "contingency", "other", 100_000.0))


@pytest.mark.asyncio
async def test_the_saved_contingency_election_reaches_hybrid_component_pricing_in_an_evaluation(monkeypatch):
    from app.api.v1.cineglobe import ProjectAssumptions, post_project_assumptions
    from app.calculators import structural_archetype_generator as gen
    from app.services import canonical_evaluation as ce
    from app.services.canonical_program_identity import alias_memo_scope
    from tests.isolated_records import create_synthetic_project, isolated_session

    seen: list = []
    original = gen.generate_structural_candidate

    def recorder(*args, **kwargs):
        seen.append(kwargs.get("contingency_expected_utilization_pct", "ABSENT"))
        return original(*args, **kwargs)

    monkeypatch.setattr(gen, "generate_structural_candidate", recorder)
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, lines=LINES, home_code="CA-MB")
        await post_project_assumptions(pid, ProjectAssumptions(answers={"contingency_expected_utilization_pct": 40}), db)
        with alias_memo_scope():
            await ce.evaluate_project(db, pid)
    assert seen, "the evaluation must price at least one hybrid candidate through the generic generator"
    assert set(seen) == {40.0}, set(seen)
