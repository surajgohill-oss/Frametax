"""NA-RECONCILIATION-24: budget-line inputs (person, role, status, qualifying portion) through the existing line_fact / uplift_basis owners, and the Montana person-level caps they make exact.

Isolated synthetic fixtures only. Arithmetic by hand from MCA 15-31-1007(3)(b): resident crew 25% (credit not above USD 150,000 per person), non-resident crew 15% where Montana tax is withheld (USD 150,000 per person),
students 30% (USD 50,000 each), actors / directors / producers / writers 20% of the first USD 7,500,000 per person where Montana tax is withheld; compensation is not a 'production expenditure'."""
from __future__ import annotations

import uuid

import pytest

import app.data.program_rate_rules_worldwide  # noqa: F401
from app.calculators.allocation_pricing import price_segment
from app.calculators.scenario_facts import refuted
from tests.isolated_records import create_synthetic_project, isolated_session
from tests.test_na_stack_and_gate_repairs_controls import _alloc

MT = "us_mt_media_act_tax_credit"
ZERO = {"us_mt_media_expenditure_year": 2031.0, "us_mt_college_campus_payments_usd": 0.0, "us_mt_studio_rental_expenditure_usd": 0.0, "us_mt_studio_rental_days": 0.0, "us_mt_underserved_area_expenditure_usd": 0.0}


def _price(lines, facts=None):
    """lines: [(line_id, category, amount)]; facts: amount facts (payee ordinals, status codes). The total IS the compensation credit (the 20% base leaves the compensation)."""
    from app.services.canonical_evaluation import _PRODUCER_CONTROLLED_ASSUMPTION_FACT_KEYS as P
    allocs = [_alloc(f"A{i}", amt, "production", "US-MT", lid, cat) for i, (lid, cat, amt) in enumerate(lines)]
    total = sum(a for _, _, a in lines)
    seg = price_segment(jurisdiction_code="US-MT", program_slug=MT, allocations=allocs, spend_category_by_code={f"A{i}": c for i, (_, c, _) in enumerate(lines)}, offshore_payroll_accounts=frozenset(),
                        production_type="feature_film", gross_budget_usd=2 * total, confirmed_ceiling_programs=frozenset({MT}),
                        evidenced_requirement_facts=frozenset({refuted("us_mt_screen_credit_furnished_confirmed")}) | P, amount_facts={**ZERO, **(facts or {})})
    return seg.incentive_floor_usd, seg.incentive_ceiling_usd


def _payees(**by_line):
    """{line: ordinal} -> ny_atl_payee facts"""
    return {f"ny_atl_payee:{k}": float(v) for k, v in by_line.items()}


# ── exact caps with identified persons; a lawful range otherwise ─────────────────────────────────────────────────────────────────────────────────

def test_identified_persons_make_the_resident_crew_cap_exact_across_their_lines():
    lines = [("L1", "btl_resident_labor", 400_000.0), ("L2", "btl_resident_labor", 400_000.0), ("L3", "btl_resident_labor", 200_000.0)]
    # person 1 holds L1 + L2 (800,000: 25% = 200,000 -> capped 150,000), person 2 holds L3 (200,000: 25% = 50,000)
    assert _price(lines, _payees(L1=1, L2=1, L3=2)) == pytest.approx((200_000.0, 200_000.0))
    # one person holds every line: 25% x 1,000,000 = 250,000 capped at 150,000
    assert _price(lines, _payees(L1=1, L2=1, L3=1)) == pytest.approx((150_000.0, 150_000.0))
    # three different persons: 100,000 + 100,000 + 50,000, none capped
    assert _price(lines, _payees(L1=1, L2=2, L3=3)) == pytest.approx((250_000.0, 250_000.0))


@pytest.mark.parametrize("comp,credit", [(599_999.0, 149_999.75), (600_000.0, 150_000.0), (600_001.0, 150_000.0)])
def test_the_per_person_resident_cap_binds_at_exactly_600000_of_compensation(comp, credit):
    assert _price([("L1", "btl_resident_labor", comp)], _payees(L1=1)) == pytest.approx((credit, credit))


def test_partial_identification_prices_a_disclosed_range_never_hiding_the_opportunity():
    lines = [("L1", "btl_resident_labor", 800_000.0), ("L2", "btl_resident_labor", 200_000.0)]
    floor, ceiling = _price(lines, _payees(L1=1))                     # L2 has no identified person
    assert floor == pytest.approx(150_000.0), "the identified person's capped credit is a lawful lower bound (and equals the one-person bound on the whole)"
    assert ceiling == pytest.approx(150_000.0 + 0.25 * 200_000.0), "the unidentified line may belong to other persons: 25% of it is the upper bound"


def test_a_person_is_never_counted_twice_when_the_same_payee_appears_on_several_lines():
    one_line = _price([("L1", "btl_resident_labor", 1_000_000.0)], _payees(L1=1))
    split = _price([("L1", "btl_resident_labor", 500_000.0), ("L2", "btl_resident_labor", 500_000.0)], _payees(L1=1, L2=1))
    assert split == pytest.approx(one_line)
    assert split == pytest.approx((150_000.0, 150_000.0))


# ── status, withholding and Unknown versus False ─────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("persons,credit", [(5, 250_000.0), (6, 300_000.0), (7, 300_000.0)])
def test_students_are_30_percent_with_a_50000_credit_cap_per_student_by_line_status(persons, credit):
    lines = [(f"L{i}", "btl_crew_labor", 1_000_000.0 / persons) for i in range(persons)]
    facts = {**_payees(**{f"L{i}": i + 1 for i in range(persons)}), **{f"mt_status_code:L{i}": 1.0 for i in range(persons)}}
    floor, ceiling = _price(lines, facts)
    assert credit == min(0.30 * 1_000_000.0, persons * 50_000.0)
    assert (floor, ceiling) == pytest.approx((credit, credit))


def test_veterans_and_tribal_members_are_30_percent_with_a_150000_cap_each():
    assert _price([("L1", "btl_crew_labor", 1_000_000.0)], {**_payees(L1=1), "mt_status_code:L1": 2.0}) == pytest.approx((150_000.0, 150_000.0))
    lines = [("L1", "btl_crew_labor", 500_000.0), ("L2", "btl_crew_labor", 500_000.0)]
    assert _price(lines, {**_payees(L1=1, L2=2), "mt_status_code:L1": 2.0, "mt_status_code:L2": 2.0}) == pytest.approx((300_000.0, 300_000.0))


def test_nonresident_crew_is_15_percent_only_where_montana_tax_is_withheld_and_unknown_is_not_false():
    base = [("L1", "btl_nonresident_labor", 1_000_000.0)]
    unknown = _price(base)
    withheld = _price(base, {"mt_tax_withheld:L1": 1.0})
    not_withheld = _price(base, {"mt_tax_withheld:L1": 0.0})
    assert unknown == pytest.approx((0.0, 150_000.0)), "withholding not stated: no confirmed credit, the 15% category potential stays visible"
    assert withheld == pytest.approx((150_000.0, 150_000.0))
    assert not_withheld == pytest.approx((0.0, 0.0)), "a stated No (tax not withheld) applies the failed treatment: no credit and no conditional upside"


def test_talent_is_20_percent_of_the_first_7_5_million_per_person_and_needs_withholding():
    lines = [("L1", "atl_cast", 8_000_000.0)]
    assert _price(lines, {**_payees(L1=1), "mt_tax_withheld:L1": 1.0}) == pytest.approx((1_500_000.0, 1_500_000.0))
    unknown = _price(lines, _payees(L1=1))
    assert unknown[0] == pytest.approx(0.0) and unknown[1] == pytest.approx(1_500_000.0)
    assert _price(lines, {**_payees(L1=1), "mt_tax_withheld:L1": 0.0}) == pytest.approx((0.0, 0.0))


def test_the_budgets_own_resident_classification_is_never_overwritten_by_a_weaker_statement():
    floor, ceiling = _price([("L1", "btl_resident_labor", 400_000.0)], {**_payees(L1=1), "mt_residency_code:L1": 2.0})
    assert (floor, ceiling) == pytest.approx((100_000.0, 100_000.0)), "priced as resident crew (25%), not as a non-resident"


def test_a_stated_residency_classifies_an_unclassified_crew_line():
    assert _price([("L1", "btl_crew_labor", 400_000.0)], {**_payees(L1=1), "mt_residency_code:L1": 1.0}) == pytest.approx((100_000.0, 100_000.0))
    unknown = _price([("L1", "btl_crew_labor", 400_000.0)], _payees(L1=1))
    assert unknown == pytest.approx((0.0, 0.30 * 400_000.0)), "no residency: the highest category rate bounds the potential and nothing is confirmed"


# ── database: the writer, applicability, reconciliation ──────────────────────────────────────────────────────────────────────────────────────

LINES = (("1000", "WRITER", "atl_writer", "atl", 300_000.0), ("3100", "CREW", "btl_resident_labor", "btl", 500_000.0), ("3200", "EQUIPMENT", "btl_equipment_rental", "btl", 200_000.0),
         ("4100", "MUSIC", "music", "btl", 100_000.0))


@pytest.mark.asyncio
async def test_the_picker_offers_only_the_fields_a_selected_program_reads_for_each_line_category():
    from app.services.line_inputs import line_amounts, line_inputs_view
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        mt = await line_inputs_view(db, project_id, [MT])
        by_cat = {l["category"]: {f["name"] for f in l["fields"]} for l in mt["lines"]}
        assert set(by_cat) == {"atl_writer", "btl_resident_labor"}, "an equipment line has no field any Montana rule reads; the music line neither"
        assert {"payee_id", "payee_compensation_complete", "mt_residency", "mt_tax_withheld", "mt_status"} <= by_cat["btl_resident_labor"]
        assert "role" not in by_cat["btl_resident_labor"], "Canadian labour fields are not offered for a Montana-only selection"
        ca = await line_inputs_view(db, project_id, ["ca_federal_cptc"])
        names = {f["name"] for l in ca["lines"] for f in l["fields"]}
        assert {"role", "canadian_status", "service_location", "payment_status", "look_through_wages_usd", "assistance_usd", "related_party"} <= names and "mt_status" not in names
        ny = await line_inputs_view(db, project_id, ["ny_state_film"])
        assert {l["category"] for l in ny["lines"] if l["fields"]} == {"atl_writer", "btl_resident_labor", "music"} and "composer_compensation_usd" in {f["name"] for l in ny["lines"] if l["category"] == "music" for f in l["fields"]}
        assert (await line_inputs_view(db, project_id, []))["lines"] == [], "no selected program: nothing is asked"
        assert len(await line_amounts(db, project_id)) == 4


@pytest.mark.asyncio
async def test_line_facts_are_validated_stored_once_distinguish_unknown_from_false_and_change_the_fingerprint_only_when_changed():
    from app.services import ny_producer_facts as npf
    from app.services.canonical_evaluation import current_generation_fingerprint
    from app.services.line_inputs import line_amounts, line_inputs_view
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU", lines=LINES)
        project_id = uuid.UUID(pid)
        ids = {v["description"]: k for k, v in (await line_amounts(db, project_id)).items()}
        crew, writer, music = ids["3100 CREW"] if "3100 CREW" in ids else next(k for k, v in (await line_amounts(db, project_id)).items() if v["category"] == "btl_resident_labor"), \
            next(k for k, v in (await line_amounts(db, project_id)).items() if v["category"] == "atl_writer"), next(k for k, v in (await line_amounts(db, project_id)).items() if v["category"] == "music")
        base_fp = await current_generation_fingerprint(db, project_id)
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, "field": "payee_id", "value": "Pat Crew"}, {"line_id": crew, "field": "payee_compensation_complete", "value": True},
                                                                       {"line_id": writer, "field": "mt_tax_withheld", "value": False}, {"line_id": crew, "field": "mt_status", "value": "student"}])
        fp1 = await current_generation_fingerprint(db, project_id)
        assert fp1 != base_fp
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, "field": "payee_id", "value": "Pat Crew"}])      # the same value again
        assert await current_generation_fingerprint(db, project_id) == fp1, "an unchanged save changes nothing"
        view = {l["line_id"]: {f["name"]: f for f in l["fields"]} for l in (await line_inputs_view(db, project_id, [MT]))["lines"]}
        assert view[writer]["mt_tax_withheld"]["value"] is False and view[writer]["mt_tax_withheld"]["state"] == "STATED", "a stated No is stored and shown as No"
        assert view[writer]["mt_residency"]["value"] is None and view[writer]["mt_residency"]["state"] == "UNKNOWN", "Unknown is a different state from No"
        assert view[crew]["payee_id"]["value"] == "Pat Crew" and view[crew]["mt_status"]["value"] == "student"
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": writer, "field": "mt_tax_withheld", "value": None}])  # reset to Unknown
        view2 = {l["line_id"]: {f["name"]: f for f in l["fields"]} for l in (await line_inputs_view(db, project_id, [MT]))["lines"]}
        assert view2[writer]["mt_tax_withheld"]["state"] == "UNKNOWN"
        persons = (await line_inputs_view(db, project_id, [MT]))["persons"]
        assert persons == [{"payee": "Pat Crew", "lines": [crew], "total_usd": 500_000.0, "complete": True}], "the person's total reconciles to the lines assigned to them"


@pytest.mark.asyncio
@pytest.mark.parametrize("row,match", [
    ({"field": "mt_status", "value": "teacher"}, "must be one of"),
    ({"field": "assistance_usd", "value": 600_000.0}, "exceeds the line amount"),
    ({"field": "assistance_usd", "value": -1}, "at least 0"),
    ({"field": "composer_compensation_usd", "value": float("nan")}, "finite"),
    ({"field": "mt_tax_withheld", "value": "yes"}, "true, false or null"),
    ({"field": "vibes", "value": "x"}, "not a line-level fact"),
    ({"field": "payee_compensation_complete", "value": True}, "no person is identified"),
])
async def test_invalid_line_facts_are_refused(row, match):
    from app.services import ny_producer_facts as npf
    from app.services.line_inputs import line_amounts
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU", lines=LINES))
        crew = next(k for k, v in (await line_amounts(db, project_id)).items() if v["category"] == "btl_resident_labor")
        with pytest.raises(ValueError, match=match):
            await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, **row}])
        with pytest.raises(ValueError, match="not a line of this project"):
            await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": "nope", "field": "mt_status", "value": "student"}])


@pytest.mark.asyncio
async def test_a_qualifying_portion_cannot_exceed_its_line_and_is_stored_once_per_line():
    from app.services import ny_producer_facts as npf
    from app.services.line_inputs import line_amounts, line_inputs_view
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU", lines=LINES))
        lines = await line_amounts(db, project_id)
        crew = next(k for k, v in lines.items() if v["category"] == "btl_resident_labor")
        ar = "us_ar_digital_motion_picture_incentive"
        with pytest.raises(ValueError, match="within the line"):
            await npf.write_ny_program_facts(db, project_id, uplift_basis=[{"program": ar, "uplift": "addons_to_the_30pct_cap", "line_id": crew, "amount_usd": 500_000.01}])
        await npf.write_ny_program_facts(db, project_id, uplift_basis=[{"program": ar, "uplift": "addons_to_the_30pct_cap", "line_id": crew, "amount_usd": 500_000.0}])
        await npf.write_ny_program_facts(db, project_id, uplift_basis=[{"program": ar, "uplift": "addons_to_the_30pct_cap", "line_id": crew, "amount_usd": 120_000.0}])   # replaces, never adds
        view = await line_inputs_view(db, project_id, [ar])
        portions = [p for l in view["lines"] if l["line_id"] == crew for p in l["portions"]]
        assert [p["amount_usd"] for p in portions] == [120_000.0]


@pytest.mark.asyncio
async def test_line_status_facts_resolve_the_pstc_canadian_labour_evidence_and_unknown_status_fails_closed():
    """CPTC/PSTC Canadian-labour evidence from the picker: PSTC needs the individual's Canadian status AND the service location affirmatively evidenced; a stated nonresident or a deferred payment excludes the line;
    Unknown status is not a confirmed yes (T1131 / PSTC guide, as encoded in canadian_labour_basis)."""
    from app.services import ny_producer_facts as npf
    from app.services.canonical_project_economics import build_project_economic_inputs
    from app.services.line_inputs import line_amounts
    key = "ca_federal_pstc_qualified_labour_usd"
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU", lines=LINES))
        lines = await line_amounts(db, project_id)
        crew = next(k for k, v in lines.items() if v["category"] == "btl_resident_labor")
        cast = next(k for k, v in lines.items() if v["category"] == "atl_writer")

        async def qualified():
            res = await build_project_economic_inputs(db, project_id, read_only=True)
            return (res.inputs.amount_facts or {}).get(key)

        assert await qualified() is None, "no line fact: nothing is confirmed (a missing fact fails closed)"
        await npf.write_ny_program_facts(db, project_id, line_facts=[
            {"line_id": crew, "field": "canadian_status", "value": "resident_citizen"}, {"line_id": crew, "field": "service_location", "value": "in_canada"},
            {"line_id": cast, "field": "canadian_status", "value": "nonresident"}, {"line_id": cast, "field": "service_location", "value": "in_canada"}])
        assert await qualified() == pytest.approx(500_000.0), "the resident crew line counts in full; the stated non-resident writer line is excluded"
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, "field": "payment_status", "value": "deferred"}])
        assert await qualified() in (None, 0.0), "a deferred amount is not a labour expenditure"
        await npf.write_ny_program_facts(db, project_id, line_facts=[{"line_id": crew, "field": "payment_status", "value": None}, {"line_id": crew, "field": "service_location", "value": None}])
        assert await qualified() in (None, 0.0), "service location back to Unknown (not outside Canada): PSTC fails closed until it is evidenced again"
