"""NA-RECONCILIATION-22: the resolved-fact layer - what the engine derives or models itself, the tri-state boolean model, and the precedence between verified evidence, producer statements and scenario assumptions.

Isolated synthetic fixtures only (rolled back; no real production is read or evaluated). Every expectation is hand-derived from the statute cited beside it:
- RSMo 135.750 subsection 3: 20% base; +5 points when at least 50% of the project is filmed in Missouri; +5 when at least 15% (a THRESHOLD of the Missouri filming, not 15 points) is in a rural or blighted area;
  +5 for three qualifying departments' resident hires; +5 for script marketing; +2 (10% of the 20% base) for a second-, third- or fourth-class county = 42% at most.
- MCA 15-31-1007(3)(b)(i): resident crew compensation earns 25% of the compensation, not above a USD 150,000 credit per person; compensation is not a 'production expenditure' (15-31-1003(13)(b)(i)), so the
  20% base does not apply to it.
- Creative Saskatchewan FFTV Guidelines: at least 51% of principal photography days in Saskatchewan (integer arithmetic at the boundary)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import _share_gate_state, price_segment
from app.calculators.scenario_facts import (
    SCENARIO_SHARE_PREFIX, SCHEDULE_TOTAL_DAYS_FACT, apply_scenario_facts, principal_photography_placement, refuted, scenario_derived_facts,
)
from app.calculators.structural_archetype_generator import StructuralComponent, generate_structural_candidate
from tests.isolated_records import create_synthetic_project, isolated_session
from tests.test_na_bonus_formula_controls import BASE, MO, PT, UP, BASEF, _price
from tests.test_na_stack_and_gate_repairs_controls import _alloc

SK = "ca_sk_creative_saskatchewan_grant"
MT = "us_mt_media_act_tax_credit"
MB = "ca_mb_film_video_credit"
FILMED = UP["a"]


# ── tri-state pricing: Unknown preserves the potential, a refuted fact applies the failed treatment ─────────────────────────────────────────────

def test_missouri_filming_fact_is_tri_state_in_pricing():
    unknown = _price(MO, "US-MO", facts=set(BASEF))
    yes = _price(MO, "US-MO", facts=set(BASEF) | {FILMED})
    no = _price(MO, "US-MO", facts=set(BASEF) | {refuted(FILMED)})
    assert (unknown.incentive_floor_usd, unknown.incentive_ceiling_usd) == pytest.approx((20 * PT, 42 * PT)), "Unknown keeps all four 5-point uplifts and the county uplift as conditional potential"
    assert (yes.incentive_floor_usd, yes.incentive_ceiling_usd) == pytest.approx((25 * PT, 42 * PT))
    assert (no.incentive_floor_usd, no.incentive_ceiling_usd) == pytest.approx((20 * PT, 37 * PT)), "a stated No removes its 5 points from the potential: 20 + 5 + 5 + 5 + 2"


def test_the_missouri_ladder_reads_20_plus_5_plus_5_plus_5_plus_5_plus_2_and_15_percent_is_a_threshold():
    from app.services.resolved_facts import missouri_ladder
    keys = [UP[k] for k in ("a", "b", "c", "d", "county")]
    ladder = missouri_ladder({k: "UNKNOWN" for k in keys})
    assert ladder["base_pct"] == 20 and [s["points"] for s in ladder["steps"]] == [5, 5, 5, 5, 2] and ladder["max_pct"] == 42
    assert (ladder["confirmed_pct"], ladder["potential_pct"]) == (20, 42)
    rural = next(s for s in ladder["steps"] if s["id"] == "rural_or_blighted_15pct")
    assert rural["points"] == 5, "the 15 in 'rural or blighted 15%' is the share threshold of the Missouri filming, never 15 points"
    mixed = missouri_ladder({UP["a"]: "TRUE", UP["b"]: "FALSE", UP["c"]: "UNKNOWN", UP["d"]: "UNKNOWN", UP["county"]: "UNKNOWN"})
    assert (mixed["confirmed_pct"], mixed["potential_pct"]) == (25, 37)
    full = missouri_ladder({k: "TRUE" for k in keys})
    assert (full["confirmed_pct"], full["potential_pct"]) == (42, 42), "never above the statute's 42%"


# ── precedence: a weaker tier never overwrites a stronger one ─────────────────────────────────────────────────────────────────────────────────

def test_resolve_boolean_precedence_verified_then_producer_then_scenario_then_unknown():
    from app.services.resolved_facts import resolve_boolean
    assert resolve_boolean() == ("UNKNOWN", "UNKNOWN", None)
    assert resolve_boolean(scenario=True) == ("TRUE", "SCENARIO_ASSUMED", True)
    assert resolve_boolean(stated=False, scenario=True) == ("FALSE", "PRODUCER_STATED", False), "a producer No outranks a scenario assumption"
    assert resolve_boolean(verified=True, stated=False, scenario=False) == ("TRUE", "VERIFIED", True), "retained evidence outranks both"
    assert resolve_boolean(verified=False, stated=True)[0] == "FALSE"


ROWS_FULL = [("US-MO", 1_000_000.0, "principal_photography", "principal_production")]
ROWS_NONE = [("CA-MB", 1_000_000.0, "principal_photography", "principal_production"), ("US-MO", 200_000.0, "vfx", "vfx")]
ROWS_SPLIT = [("US-MO", 990_000.0, "principal_photography", "x"), ("CA-MB", 10_000.0, "principal_photography", "y")]


def test_a_full_relocation_scenario_establishes_the_missouri_filming_test_and_a_none_placement_refutes_it():
    full = scenario_derived_facts(MO, "US-MO", ROWS_FULL, "US-MO")
    assert FILMED in full.true_facts and not full.refuted_facts and full.derived[0].provenance == "SCENARIO_ASSUMED"
    none = scenario_derived_facts(MO, "US-MO", ROWS_NONE, "CA-MB")
    assert FILMED in none.refuted_facts and not none.true_facts
    split = scenario_derived_facts(MO, "US-MO", ROWS_SPLIT, "US-MO")
    assert not split.true_facts and not split.refuted_facts, "99% of the dollars in Missouri still does not establish shooting days: a split stays Unknown"
    assert principal_photography_placement(ROWS_SPLIT, "US-MO", "US-MO")[0] == "SPLIT"


def test_scenario_facts_never_overwrite_a_stronger_tier():
    stated_no = scenario_derived_facts(MO, "US-MO", ROWS_FULL, "US-MO", evidenced={refuted(FILMED)})
    assert not stated_no.true_facts, "a stated No stays No even when the scenario would assume Yes"
    stated_yes = scenario_derived_facts(MO, "US-MO", ROWS_NONE, "CA-MB", evidenced={FILMED})
    assert not stated_yes.refuted_facts, "a stated Yes stays Yes even when the scenario would assume No"
    ev, am = apply_scenario_facts(frozenset({FILMED}), {"x": 1.0}, scenario_derived_facts(MO, "US-MO", ROWS_FULL, "US-MO", {FILMED}))
    assert ev == {FILMED} and am == {"x": 1.0}


def test_the_generator_prices_a_full_missouri_relocation_with_the_filming_points_and_a_foreign_shoot_without_them():
    def comp(kind, jur, slug, allocs):
        return StructuralComponent(component_type=kind, jurisdiction_code=jur, program_slug=slug, allocations=tuple(allocs), spend_category_by_code={a.account_code: a.spend_category for a in allocs},
                                   evidenced_requirement_facts=frozenset(BASEF))
    pp = lambda jur, amount: _alloc("P", amount, "principal_photography", jur, "P", "vfx")           # noqa: E731
    full = generate_structural_candidate([comp("principal_production", "US-MO", MO, [pp("US-MO", BASE)])], gross_budget_usd=BASE)
    explicit = _price(MO, "US-MO", facts=set(BASEF) | {FILMED}, category="vfx")
    seg = next(c.segment for c in full.component_economics)
    assert seg.incentive_floor_usd == pytest.approx(explicit.incentive_floor_usd) and seg.incentive_floor_usd == pytest.approx(25 * PT), "20% base + the 5-point filming uplift, derived from the scenario"
    split_off = generate_structural_candidate([comp("principal_production", "CA-MB", MB, [pp("CA-MB", BASE)]),
                                               comp("vfx", "US-MO", MO, [_alloc("V", 200_000.0, "vfx", "US-MO", "V", "vfx")])], gross_budget_usd=BASE + 200_000.0)
    mo_seg = next(c.segment for c in split_off.component_economics if c.component.program_slug == MO)
    assert (mo_seg.incentive_floor_usd, mo_seg.incentive_ceiling_usd) == pytest.approx((0.20 * 200_000.0, 0.37 * 200_000.0)), \
        "the foreign shoot fails the 50% filming test: 20% guaranteed and a 37% ceiling (20 + 5 + 5 + 5 + 2), its 5 filming points are not conditional upside"


# ── schedule -> day facts; share gates with integer arithmetic at the boundary ───────────────────────────────────────────────────────────────────

def test_the_schedule_total_and_a_full_placement_derive_the_day_facts_without_overwriting_a_stated_number():
    rows_bc = [("CA-BC", 1_000_000.0, "principal_photography", "principal_production")]
    sf = scenario_derived_facts("ca_bc_film_tv_tax_credit", "CA-BC", rows_bc, "CA-BC", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 40.0})
    assert sf.amounts == {"ca_bc_principal_photography_days_in_bc": 40.0}
    rows_ns = [("CA-NS", 1_000_000.0, "principal_photography", "principal_production")]
    ns = scenario_derived_facts("ca_ns_production_incentive_fund", "CA-NS", rows_ns, "CA-NS", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 36.0})
    assert ns.amounts == {"ca_ns_principal_photography_days_total": 36.0, "ca_ns_principal_photography_days_in_ns": 36.0}
    stated = scenario_derived_facts("ca_ns_production_incentive_fund", "CA-NS", rows_ns, "CA-NS",
                                    amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 36.0, "ca_ns_principal_photography_days_total": 30.0})
    assert "ca_ns_principal_photography_days_total" not in stated.amounts, "a stated total is never overwritten by the scenario"
    none = scenario_derived_facts("ca_ns_production_incentive_fund", "CA-NS", [("CA-MB", 1.0, "principal_photography", "x")], "CA-MB", amount_facts={SCHEDULE_TOTAL_DAYS_FACT: 36.0})
    assert "ca_ns_principal_photography_days_in_ns" not in none.amounts, "no placement in Nova Scotia: the in-province days are not the schedule total"
    no_schedule = scenario_derived_facts("ca_ns_production_incentive_fund", "CA-NS", rows_ns, "CA-NS")
    assert not no_schedule.amounts, "no retained schedule: no day count is invented"


def _gate_rule():
    from app.data.program_rate_rules import get_subset_uplift_rules
    return next(u for u in get_subset_uplift_rules(SK) if u.uplift_id == "activity_test")


@pytest.mark.parametrize("num,den,met", [(51, 100, True), (50, 100, False), (102, 200, True), (101, 200, False), (100, 100, True), (0, 40, False)])
def test_the_saskatchewan_51_percent_activity_test_at_the_boundary(num, den, met):
    rule = _gate_rule()
    amounts = {rule.day_numerator_fact: float(num), rule.day_denominator_fact: float(den)}
    assert _share_gate_state(rule, amounts, frozenset()) is met
    assert _share_gate_state(rule, amounts, frozenset({SCENARIO_SHARE_PREFIX + rule.day_numerator_fact})) is met, "stated numbers outrank a scenario assumption"


def test_a_scenario_decides_the_saskatchewan_gate_only_while_the_day_counts_are_not_both_stated():
    rule = _gate_rule()
    token = SCENARIO_SHARE_PREFIX + rule.day_numerator_fact
    assert _share_gate_state(rule, {}, frozenset()) is None
    assert _share_gate_state(rule, {}, frozenset({token})) is True and _share_gate_state(rule, {}, frozenset({refuted(token)})) is False
    sf = scenario_derived_facts(SK, "CA-SK", [("CA-SK", 1.0, "principal_photography", "x")], "CA-SK")
    assert token in sf.true_facts, "a full-relocation scenario places 100% of principal photography in Saskatchewan: the 51% test is met"


# ── Montana: resident-crew compensation from the normalized budget, with the per-person cap honest ──────────────────────────────────────────────

def _mt(category, amounts=(), facts=()):
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P
    zero = {"us_mt_media_expenditure_year": 2031.0, "us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 0.0,
            "us_mt_underserved_area_expenditure_usd": 0.0}
    return price_segment(jurisdiction_code="US-MT", program_slug=MT, allocations=[_alloc("3100", BASE, "production", "US-MT", "S0", category)], spend_category_by_code={"3100": category},
                         offshore_payroll_accounts=frozenset(), production_type="feature_film", gross_budget_usd=2 * BASE, confirmed_ceiling_programs=frozenset({MT}),
                         evidenced_requirement_facts=frozenset(facts) | {refuted("us_mt_screen_credit_furnished_confirmed")} | P, amount_facts={**zero, **dict(amounts)})


def test_montana_derives_resident_crew_compensation_from_the_budget_and_prices_the_per_person_cap_at_the_lawful_lower_bound():
    plain = _mt("btl_crew_labor")
    derived = _mt("btl_resident_labor")
    # 1,000,000 of resident crew: compensation leaves the 20% base (-200,000); with no person count the credit is at least one person's min(25% x 1,000,000, 150,000) = 150,000
    assert plain.incentive_floor_usd == pytest.approx(0.0) and derived.incentive_floor_usd == pytest.approx(150_000.0)
    # restated in NA-RECONCILIATION-23: a KNOWN category is priced at its own 25% rate; only the per-person cap is a range, so the potential is 25% x 1,000,000, never the 30% maximum
    assert derived.incentive_ceiling_usd == pytest.approx(250_000.0)
    stated = _mt("btl_resident_labor", amounts={"us_mt_resident_crew_compensation_usd": BASE, "us_mt_resident_crew_persons": 10})
    assert stated.incentive_floor_usd == pytest.approx(250_000.0), "ten stated persons: 25% x 1,000,000, each well below the 150,000 credit cap (a producer statement outranks the derivation)"
    capped = _mt("btl_resident_labor", amounts={"us_mt_resident_crew_compensation_usd": 3_000_000.0 / 3, "us_mt_resident_crew_persons": 1})
    assert capped.incentive_floor_usd == pytest.approx(150_000.0), "one person: the 150,000 per-person cap binds exactly"
    assert any("person count not stated" in str(c.get("note", "")) for c in derived.ceiling_conditions), "the missing person-level evidence is disclosed"
    vfx = _mt("vfx")
    assert vfx.incentive_floor_usd == pytest.approx(200_000.0), "non-compensation Montana spend earns the 20% base"


# ── the inventory is complete and every reader has a canonical writer or derivation ──────────────────────────────────────────────────────────────

def test_the_inventory_classifies_every_fact_and_leaves_no_reader_without_a_writer():
    from app.services.na_fact_inventory import build_inventory
    inv = build_inventory()
    by_key = {r["fact_key"]: r for r in inv}
    assert len(inv) >= 250
    assert [r["fact_key"] for r in inv if r["missing_control_or_path"].startswith("READER WITH NO CANONICAL WRITER")] == []
    assert by_key[FILMED]["derivation_class"] == "SCENARIO_PLACEMENT" and by_key[UP["b"]]["derivation_class"] == "LOCALITY"
    assert by_key[UP["county"]]["derivation_class"] == "LOCALITY" and by_key["ca_ns_principal_photography_days_total"]["derivation_class"] == "SCHEDULE_DAYS"
    assert by_key["ny_post_facility_inside_mctd"]["derivation_class"] == "PRODUCER_ELECTION"
    for r in inv:
        assert r["derivation_class"] and r["true_false_unknown_behaviour"] is not None and r["derivable_from"], r["fact_key"]


def test_every_writable_fact_is_catalogued_and_therefore_offered():
    from app.services import ny_producer_facts as npf
    from app.services.producer_fact_catalog import CATALOG
    assert [k for k in list(npf.NY_EVIDENCED_FACTS) + list(npf.PROGRAM_AMOUNT_FACTS) if k not in CATALOG] == [], "a writable fact with no catalog entry could never be shown to the producer"
    for k in ("mo_filmed_50pct_in_missouri_confirmed", "on_ofttc_first_time_producer", "nj_film_spend_outside_nyc_radius_confirmed", "wv_ten_resident_hires_confirmed",
              "us_tx_miip_award_confirmed", "ca_film_independent_category", "ca_bc_dave_eligible_activity_confirmed"):
        assert k in CATALOG, k


# ── database-backed: the stored No, the schedule, the fingerprint ───────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_stored_no_is_a_refuted_token_changes_the_fingerprint_and_clears_back_to_unknown():
    from app.models.project_fact import ProjectFact
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import current_generation_fingerprint
    from app.services.canonical_project_economics import _evidenced_program_facts
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        base_fp = await current_generation_fingerprint(db, project_id)
        await npf.write_ny_program_facts(db, project_id, evidenced={FILMED: True})
        yes_fp = await current_generation_fingerprint(db, project_id)
        await npf.write_ny_program_facts(db, project_id, evidenced={FILMED: False})
        no_fp = await current_generation_fingerprint(db, project_id)
        assert len({base_fp, yes_fp, no_fp}) == 3, "Unknown, Yes and No are three different inputs"
        rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == project_id))).scalars().all()
        tokens = _evidenced_program_facts(rows)
        assert refuted(FILMED) in tokens and FILMED not in tokens, "the No is carried as a refuted token, not as an absent fact"
        await npf.write_ny_program_facts(db, project_id, evidenced={FILMED: None})
        assert await current_generation_fingerprint(db, project_id) == base_fp, "clearing returns to Unknown and the original fingerprint"


@pytest.mark.asyncio
async def test_the_retained_schedule_is_the_total_days_owner_and_verified_evidence_outranks_a_producer_statement():
    from app.models.production_requirement import ProductionAssumption
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import current_generation_fingerprint
    from app.services.producer_fact_catalog import program_facts_view
    from app.services.resolved_facts import schedule_total_days_with_tier
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        assert await schedule_total_days_with_tier(db, project_id) == (None, None)

        def fact(view, key):
            return next(f for g in view["groups"] for f in g["facts"] if f["key"] == key)

        before_fp = await current_generation_fingerprint(db, project_id)
        db.add(ProductionAssumption(id=uuid.uuid4(), project_id=project_id, assumption_key="intended_shoot_days", value="38", value_type="number", evidence_state="MODEL_ESTIMATE"))
        await db.flush()
        assert (await schedule_total_days_with_tier(db, project_id))[0] is None, "an estimate is not retained evidence: it derives nothing"
        row = (await db.execute(select(ProductionAssumption).where(ProductionAssumption.project_id == project_id))).scalars().one()
        row.evidence_state = "ACTUAL"
        await db.flush()
        assert await schedule_total_days_with_tier(db, project_id) == (38, "VERIFIED")
        view = await program_facts_view(db, project_id)
        ns_total = fact(view, "ca_ns_principal_photography_days_total")
        assert ns_total["value"] == 38.0 and ns_total["provenance"] == "SCHEDULE_DERIVED" and ns_total["editable"] is False, "derived and read-only: the producer is not asked to re-enter it"
        assert await current_generation_fingerprint(db, project_id) != before_fp, "a changed schedule is a changed economic input"
        await npf.write_ny_program_facts(db, project_id, amounts={"ca_ns_principal_photography_days_total": 30.0})
        conflict = fact(await program_facts_view(db, project_id), "ca_ns_principal_photography_days_total")
        assert conflict["value"] == 38.0 and "disagrees" in conflict["conflict"], "verified evidence outranks the producer figure, and the disagreement is shown"
        row.evidence_state = "USER_CONFIRMED"
        await db.flush()
        mid = fact(await program_facts_view(db, project_id), "ca_ns_principal_photography_days_total")
        assert mid["value"] == 30.0 and mid["provenance"] == "PRODUCER_STATED", "a producer-confirmed schedule does not outrank an explicit producer statement"


def test_two_principal_production_components_in_different_jurisdictions_are_a_split_not_a_none():
    rows = [("CA-MB", 600_000.0, "principal_production", "principal_production"), ("CA-SK", 600_000.0, "principal_production", "principal_production")]
    assert principal_photography_placement(rows, "CA-SK", "CA-MB")[0] == "SPLIT"
    federal = [("CA", 600_000.0, "principal_production", "principal_production"), ("CA-SK", 600_000.0, "principal_production", "principal_production")]
    assert principal_photography_placement(federal, "CA-SK", "CA")[0] == "UNKNOWN", "a federal-layer (parent-coded) row does not locate the shoot: neither placed nor displaced"
    sf = scenario_derived_facts(SK, "CA-SK", rows, "CA")
    assert not sf.true_facts and not sf.refuted_facts, "a modeled split leaves the 51% activity test Unknown: its bonuses stay conditional potential"


def test_the_inventory_artifact_is_current_or_rewritten_on_request():
    import importlib.util
    import os
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "scripts" / "na_fact_inventory.py"
    spec = importlib.util.spec_from_file_location("na_fact_inventory_script", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    j, c = mod.render()
    if os.environ.get("WRITE_NA_FACT_INVENTORY") == "1":
        (mod.OUT / f"{mod.STEM}.json").write_text(j)
        (mod.OUT / f"{mod.STEM}.csv").write_text(c)
    assert (mod.OUT / f"{mod.STEM}.json").read_text() == j and (mod.OUT / f"{mod.STEM}.csv").read_text() == c, "regenerate with WRITE_NA_FACT_INVENTORY=1"


@pytest.mark.asyncio
async def test_a_changed_no_means_exactly_one_new_evaluation_and_an_unchanged_save_means_none_with_a_cold_reload_restoring_the_view():
    from sqlalchemy import func

    from app.models.production import EvaluationGenerationSummary
    from app.services import canonical_evaluation as ce
    from app.services import ny_producer_facts as npf
    from app.services.canonical_production_view import build_production_and_structures
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))

        async def generations():
            return (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary).where(EvaluationGenerationSummary.project_id == project_id))).scalar_one()

        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 1
        await npf.write_ny_program_facts(db, project_id, evidenced={UP["b"]: False})                         # a stated No is a changed economic input
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 2
        await npf.write_ny_program_facts(db, project_id, evidenced={UP["b"]: False})                         # the same No saved again changes nothing
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_REUSED" and await generations() == 2
        db.expunge_all()
        served = (await build_production_and_structures(db, project_id))["production"]["program_facts"]
        fact = next(f for g in served["groups"] for f in g["facts"] if f["key"] == UP["b"])
        assert (fact["state"], fact["value"], fact["provenance"]) == ("FALSE", False, "PRODUCER_STATED"), "the stated No restores after a cold reload"
        assert served["missouri"]["potential_pct"] == 37 and served["missouri"]["confirmed_pct"] == 20, "the Missouri ladder follows the stored No"
