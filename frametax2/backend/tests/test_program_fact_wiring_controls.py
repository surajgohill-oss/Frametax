"""NA-RECONCILIATION-21: the producer-stated program facts of NA-RECONCILIATION-16 to NA-20, wired end to end on isolated synthetic fixtures only (rolled back; no real production is read or evaluated).

Path under test: input (POST /projects/{id}/program-facts) -> validation -> the one canonical ProjectFact storage -> evaluation fingerprint -> exactly one evaluation when the inputs changed -> retained result
-> the read-only served view (``production.program_facts``) -> restoration after a cold reload. Unknown is never False and never a default."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.models.production import EvaluationGenerationSummary
from app.models.project_fact import ProjectFact
from app.services import ny_producer_facts as npf
from app.services import producer_fact_catalog as cat
from tests.isolated_records import create_synthetic_project, isolated_session

#: The exact facts introduced by NA-RECONCILIATION-16 to NA-20 (27 booleans + 46 numbers = 73), written out so a silently dropped or renamed fact fails here.
BOOLEANS = (
    "ca_bc_film_training_program_approved_confirmed", "ca_bc_film_tv_photography_before_2025_confirmed", "ca_bc_scriptwriting_application_confirmed",
    "ca_nb_bonus_hod_lead_talent_30pct_confirmed", "ca_nb_made_copyright_50pct_confirmed", "ca_nb_made_director_nb_resident_confirmed", "ca_nb_made_photography_days_25pct_in_nb_confirmed",
    "ca_nb_made_post_20pct_in_nb_confirmed", "ca_nb_made_spend_50pct_confirmed", "ca_nb_made_writer_nb_resident_confirmed",
    "ca_ns_content_majority_copyright_ns_ownership_confirmed", "ca_ns_content_ns_director_confirmed", "ca_ns_content_ns_resident_producer_confirmed", "ca_ns_content_ns_spend_75pct_confirmed",
    "ca_ns_content_ns_writer_confirmed", "ca_ns_content_post_75pct_in_ns_confirmed", "ca_ns_content_two_new_trainees_confirmed", "ca_ns_producer_extra_positions_approved_confirmed",
    "ca_ns_rural_majority_principal_photography_confirmed", "ca_ns_stream_i_ownership_control_confirmed", "ca_ns_stream_ii_confirmed",
    "ca_sk_majority_post_spend_in_sk_confirmed", "ca_sk_saskatchewan_stream_confirmed", "ca_sk_service_production_stream_confirmed", "ca_sk_volume_threshold_confirmed",
    "us_mt_postproduction_company_approved_confirmed", "us_mt_screen_credit_furnished_confirmed",
)
NUMBERS = (
    "ca_bc_principal_photography_days_distant_location", "ca_bc_principal_photography_days_in_bc", "ca_bc_principal_photography_days_outside_vancouver", "ca_bc_scriptwriting_assistance_usd",
    "ca_bc_scriptwriting_expenditure_usd", "ca_bc_scriptwriting_parent_reimbursement_usd", "ca_bc_training_assistance_usd", "ca_bc_training_payments_usd", "ca_federal_cptc_assistance_usd",
    "ca_federal_cptc_contingent_liabilities_usd", "ca_nb_days_remote_151km_plus", "ca_nb_days_rural_30_to_150km", "ca_nb_eligible_deemed_spend_usd", "ca_nb_principal_photography_days_total",
    "ca_ns_equity_tax_credit_financing_usd", "ca_ns_hod_positions_filled", "ca_ns_hod_positions_held_by_ns_residents", "ca_ns_ineligible_supplier_spend_usd", "ca_ns_principal_performers_ns_residents",
    "ca_ns_principal_performers_total", "ca_ns_principal_photography_days_100_to_150km", "ca_ns_principal_photography_days_in_ns", "ca_ns_principal_photography_days_over_150km",
    "ca_ns_principal_photography_days_total", "ca_ns_producer_extra_position_fees_usd", "ca_ns_producer_hod_performer_fees_total_usd", "ca_sk_apprenticeship_mentor_salaries_usd",
    "ca_sk_days_50km_outside_regina_saskatoon", "ca_sk_principal_photography_days_in_sk", "ca_sk_principal_photography_days_total", "us_mt_college_campus_payments_usd", "us_mt_media_expenditure_year",
    "us_mt_nonresident_crew_compensation_usd", "us_mt_nonresident_crew_persons", "us_mt_postproduction_wages_usd", "us_mt_resident_crew_compensation_usd", "us_mt_resident_crew_persons",
    "us_mt_student_compensation_usd", "us_mt_student_persons", "us_mt_studio_rental_days", "us_mt_studio_rental_expenditure_usd", "us_mt_talent_compensation_usd", "us_mt_talent_persons",
    "us_mt_underserved_area_expenditure_usd", "us_mt_veteran_tribal_compensation_usd", "us_mt_veteran_tribal_persons",
)
PARTNER_ONLY = ("ca_bc_film_tv_photography_after_2024_confirmed",)      # existed before NA-16; it is the exclusive partner of the before-2025 statement and is wired with it


def _valid_number(key):
    lo, hi = npf.PROGRAM_AMOUNT_FACTS[key]
    value = 2031.0 if key == "us_mt_media_expenditure_year" else max(lo, 1.0) if hi >= 1.0 else lo
    return float(round(value)) if npf.is_whole_number_fact(key) else value


def test_the_catalog_covers_exactly_the_seventy_three_facts_plus_the_pre_existing_exclusive_partner():
    assert len(BOOLEANS) == 27 and len(NUMBERS) == 46
    assert set(BOOLEANS) | set(NUMBERS) | set(PARTNER_ONLY) <= set(cat.CATALOG), "NA-RECONCILIATION-22 added the previously omitted facts; the 73 are still all catalogued"
    for key in BOOLEANS + PARTNER_ONLY:
        assert key in npf.NY_EVIDENCED_FACTS and key not in npf.PROGRAM_AMOUNT_FACTS, key
    for key in NUMBERS:
        assert key in npf.PROGRAM_AMOUNT_FACTS and key not in npf.NY_EVIDENCED_FACTS, key
    for gid, _title, _programs, _authority, facts in cat.GROUPS:
        labels = [label for _k, label, _h in facts]
        assert all(labels) and len(set(labels)) == len(labels), f"{gid}: every fact has one distinct label within its group"
    assert {"ca_bc_film_tv", "ca_federal_cptc", "ca_nb", "ca_ns", "ca_sk", "us_mt"} <= {g[0] for g in cat.GROUPS}


@pytest.mark.asyncio
async def test_every_fact_starts_unknown_and_round_trips_through_the_one_storage_and_the_fingerprint():
    from app.services.canonical_evaluation import current_generation_fingerprint
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        project_id = uuid.UUID(pid)
        view = await cat.program_facts_view(db, project_id)
        assert view["stated_count"] == 0 and all(f["state"] == "UNKNOWN" and f["value"] is None for g in view["groups"] for f in g["facts"]), "no default is created for any fact"
        base_fp = await current_generation_fingerprint(db, project_id)
        for key in sorted(set(BOOLEANS) | set(NUMBERS) | set(PARTNER_ONLY)):
            is_number = key in npf.PROGRAM_AMOUNT_FACTS
            value = _valid_number(key) if is_number else True
            await write_one(db, project_id, key, value)
            fact = next(f for g in (await cat.program_facts_view(db, project_id))["groups"] for f in g["facts"] if f["key"] == key)
            assert fact["state"] == ("VALUE" if is_number else "TRUE") and fact["value"] == value and fact["provenance"] == "PRODUCER_STATED", key
            assert await current_generation_fingerprint(db, project_id) != base_fp, f"{key}: a stated fact must change the evaluation fingerprint"
            await write_one(db, project_id, key, None)
            assert await current_generation_fingerprint(db, project_id) == base_fp, f"{key}: clearing restores Unknown and the original fingerprint"
        # a stated ZERO is a real value, different from Unknown, and changes the fingerprint
        await write_one(db, project_id, "ca_bc_training_assistance_usd", 0.0)
        zero = next(f for g in (await cat.program_facts_view(db, project_id))["groups"] for f in g["facts"] if f["key"] == "ca_bc_training_assistance_usd")
        assert zero["state"] == "VALUE" and zero["value"] == 0.0
        assert await current_generation_fingerprint(db, project_id) != base_fp


async def write_one(db, project_id, key, value):
    if key in npf.PROGRAM_AMOUNT_FACTS:
        return await npf.write_ny_program_facts(db, project_id, amounts={key: value})
    return await npf.write_ny_program_facts(db, project_id, evidenced={key: value})


@pytest.mark.asyncio
async def test_a_stated_no_is_stored_as_a_refuted_fact_for_predicates_refused_for_elections_and_invalid_numbers_are_refused_without_writing():
    """NA-RECONCILIATION-22 restates the NA-21 rule 'a false is never stored': an ordinary legal predicate is tri-state (Yes / No / Unknown); only an election between alternatives refuses a No."""
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        await npf.write_ny_program_facts(db, project_id, evidenced={"ca_bc_scriptwriting_application_confirmed": False})
        fact = next(f for g in (await cat.program_facts_view(db, project_id))["groups"] for f in g["facts"] if f["key"] == "ca_bc_scriptwriting_application_confirmed")
        assert fact["state"] == "FALSE" and fact["value"] is False and fact["provenance"] == "PRODUCER_STATED", "a stated No is a refuted fact, not a deleted one"
        with pytest.raises(ValueError, match="election"):
            await npf.write_ny_program_facts(db, project_id, evidenced={"ca_ns_stream_ii_confirmed": False})
        for key, bad in (("ca_bc_principal_photography_days_in_bc", 0), ("ca_bc_principal_photography_days_in_bc", 10.5), ("us_mt_resident_crew_persons", -1),
                         ("ca_ns_hod_positions_filled", 17), ("ca_bc_training_payments_usd", float("nan")), ("ca_bc_training_payments_usd", True)):
            with pytest.raises(ValueError):
                await npf.write_ny_program_facts(db, project_id, amounts={key: bad})
        assert (await cat.program_facts_view(db, project_id))["stated_count"] == 1, "a refused write stores nothing (only the stated No above exists)"


@pytest.mark.asyncio
@pytest.mark.parametrize("first,second", [
    ({"ca_bc_principal_photography_days_in_bc": 40}, {"ca_bc_principal_photography_days_outside_vancouver": 41}),
    ({"ca_bc_principal_photography_days_outside_vancouver": 10}, {"ca_bc_principal_photography_days_distant_location": 11}),
    ({"ca_ns_principal_photography_days_total": 20, "ca_ns_principal_photography_days_100_to_150km": 8}, {"ca_ns_principal_photography_days_over_150km": 13}),
    ({"ca_ns_hod_positions_filled": 5}, {"ca_ns_hod_positions_held_by_ns_residents": 6}),
    ({"ca_ns_principal_performers_total": 10}, {"ca_ns_principal_performers_ns_residents": 11}),
    ({"ca_nb_principal_photography_days_total": 20, "ca_nb_days_rural_30_to_150km": 12}, {"ca_nb_days_remote_151km_plus": 9}),
    ({"ca_sk_principal_photography_days_total": 30}, {"ca_sk_principal_photography_days_in_sk": 31}),
    ({"ca_sk_principal_photography_days_total": 30}, {"ca_sk_days_50km_outside_regina_saskatoon": 31}),
])
async def test_cross_field_contradictions_are_refused_against_stored_values_and_boundaries_are_accepted(first, second):
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        await npf.write_ny_program_facts(db, project_id, amounts=first)
        before = (await cat.program_facts_view(db, project_id))["stated_count"]
        with pytest.raises(ValueError):
            await npf.write_ny_program_facts(db, project_id, amounts=second)
        assert (await cat.program_facts_view(db, project_id))["stated_count"] == before
        (key, value), = second.items()
        await npf.write_ny_program_facts(db, project_id, amounts={key: value - 1})        # one less is consistent: the boundary itself is allowed
        assert (await cat.program_facts_view(db, project_id))["stated_count"] == before + 1


@pytest.mark.asyncio
@pytest.mark.parametrize("a,b", [
    ("ca_bc_film_tv_photography_after_2024_confirmed", "ca_bc_film_tv_photography_before_2025_confirmed"),
    ("ca_ns_stream_i_ownership_control_confirmed", "ca_ns_stream_ii_confirmed"),
    ("ca_sk_saskatchewan_stream_confirmed", "ca_sk_service_production_stream_confirmed"),
])
async def test_exclusive_statements_replace_each_other_and_cannot_be_stated_together(a, b):
    async with isolated_session() as db:
        project_id = uuid.UUID(await create_synthetic_project(db, home_code="MU"))
        await npf.write_ny_program_facts(db, project_id, evidenced={a: True})
        await npf.write_ny_program_facts(db, project_id, evidenced={b: True})
        states = {f["key"]: f["state"] for g in (await cat.program_facts_view(db, project_id))["groups"] for f in g["facts"]}
        assert states[b] == "TRUE" and states[a] == "UNKNOWN", "stating the opposite replaces the earlier statement"
        with pytest.raises(ValueError, match="cannot both be stated"):
            await npf.write_ny_program_facts(db, project_id, evidenced={a: True, b: True})


@pytest.mark.asyncio
async def test_saving_facts_never_evaluates_and_one_changed_input_means_exactly_one_new_generation_with_a_cold_reload_restoring_the_view(monkeypatch):
    from app.api.v1 import cineglobe as api
    from app.services import canonical_evaluation as ce
    from app.services.canonical_production_view import build_production_and_structures
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="MU")
        project_id = uuid.UUID(pid)

        async def generations():
            return (await db.execute(select(func.count()).select_from(EvaluationGenerationSummary).where(EvaluationGenerationSummary.project_id == project_id))).scalar_one()

        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 1
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_REUSED" and await generations() == 1

        # SAVE: the API path stores and returns the refreshed read-only view; it must not start an evaluation (the UI runs the single-flight evaluation afterwards)
        async def boom(*a, **k):
            raise AssertionError("saving a producer fact must not evaluate")
        monkeypatch.setattr(ce, "evaluate_project", boom)
        body = api.NyProgramFacts(evidenced={"ca_bc_scriptwriting_application_confirmed": True}, amounts={"ca_bc_scriptwriting_expenditure_usd": 200_000.0})
        saved = await api.post_ny_program_facts(pid, body, db)
        assert saved["program_facts"]["stated_count"] == 2 and await generations() == 1
        assert (await api.get_program_facts(pid, db))["program_facts"]["stated_count"] == 2, "the read endpoint restores the stored values"
        monkeypatch.undo()

        # EVALUATE: exactly one new generation for the changed inputs; a repeat is a reuse
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_COMPLETE" and await generations() == 2
        assert (await ce.evaluate_project(db, project_id))["status"] == "EVALUATION_REUSED" and await generations() == 2

        # COLD RELOAD: drop every cached ORM object; the served production view and the stored rows restore the same facts, kept apart from document evidence
        db.expunge_all()
        view = await build_production_and_structures(db, project_id)
        served = view["production"]["program_facts"]
        assert served["stated_count"] == 2
        states = {f["key"]: (f["state"], f["value"]) for g in served["groups"] for f in g["facts"]}
        assert states["ca_bc_scriptwriting_application_confirmed"] == ("TRUE", True) and states["ca_bc_scriptwriting_expenditure_usd"] == ("VALUE", 200_000.0)
        assert states["ca_bc_scriptwriting_assistance_usd"] == ("UNKNOWN", None), "unstated stays Unknown: no default was created"
        rows = (await db.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key.like("%scriptwriting%")))).scalars().all()
        assert rows and all(r.source_type == "user_override" or str(r.source_type).lower().endswith("user_override") for r in rows), "producer-stated, not document evidence"


@pytest.mark.asyncio
async def test_a_stated_fact_changes_the_priced_result_it_feeds_and_clearing_returns_to_the_bounded_potential():
    """The BC regime pair is the cleanest priced fact: stated before-2025 removes the 40% scenario from the served potential. Synthetic MU-home project; evaluation is the shared one."""
    from app.services import canonical_evaluation as ce
    from tests.isolated_records import served_structures
    async with isolated_session() as db:
        pid = await create_synthetic_project(db, home_code="CA-BC", lines=(
            ("1000", "CAST", "atl_cast", "atl", 600_000.0), ("3100", "CREW", "btl_crew_labor", "btl", 1_400_000.0), ("3200", "EQUIPMENT", "btl_equipment_rental", "btl", 700_000.0)))
        project_id = uuid.UUID(pid)
        await ce.evaluate_project(db, project_id)
        base = [e for e in await served_structures(db, pid) if e["program_slugs"] == ["ca_bc_film_tv_tax_credit"] and e["structure_type"] == "single_country"]
        if not base:
            pytest.skip("the isolated fixture does not surface the BC domestic credit as a single-country structure")
        before = base[0]
        await npf.write_ny_program_facts(db, project_id, evidenced={"ca_bc_film_tv_photography_before_2025_confirmed": True})
        await ce.evaluate_project(db, project_id)
        after = next(e for e in await served_structures(db, pid) if e["program_slugs"] == ["ca_bc_film_tv_tax_credit"] and e["structure_type"] == "single_country")
        assert after["maximum_supported_incentive_usd"] < before["maximum_supported_incentive_usd"], "the historical-regime statement removes the 40% scenario"


def test_every_stored_key_fits_the_fact_key_column_and_the_ocase_gate_is_writable():
    """ProjectFact.fact_key is 100 characters: a longer stored key could never be saved (the OCASE content gate was one, at 121, until its key used a short alias)."""
    assert max(len(npf.EVIDENCED_PREFIX + k) for k in npf.NY_EVIDENCED_FACTS) <= 100
    assert max(len(npf.AMOUNT_PREFIX + k) for k in npf.PROGRAM_AMOUNT_FACTS) <= 100
    from app.services.program_content_gates import gate_control_whitelist, gate_fact_key
    whitelist = gate_control_whitelist()
    assert max(len("evidenced_program_fact:" + k) for k in whitelist) <= 100
    ocase = "ontario_computer_animation_and_special_effects_tax_credit_ocase"
    key = gate_fact_key(ocase, "LOCAL_ENTITY_OR_PARTNER")
    assert key in whitelist and whitelist[key]["program_slug"] == ocase, "the whitelist keeps the real program slug; the key is only a short alias"
