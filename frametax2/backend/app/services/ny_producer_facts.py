"""Durable producer-stated program facts for statutory uplifts (New York, Ontario, British Columbia): backend write/read path.

Everything here is a stated PRODUCER fact or planning election stored in the existing ProjectFact table, read back by
canonical_project_economics.build_project_economic_inputs into the fields the evaluation fingerprint already covers
(evidenced_program_facts, amount_facts). Absence is Unknown, never false; nothing here is proof of an incurred expenditure.

This module is the backend path only. The Overview/Inspector controls that call it are a separate, still-pending UI stage."""
from __future__ import annotations

import json
import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import BudgetDocument, BudgetLineItem
from app.models.enums import ProjectFactSourceType, ReviewStatus
from app.models.project_fact import ProjectFact

EVIDENCED_PREFIX = "evidenced_program_fact:"
UPLIFT_BASIS_FACT_KEY = "uplift_basis_subsets"     # one JSON row: {program: {uplift_id: {line_id: amount_usd}}}

#: Producer-stated boolean program facts a caller may set. (fact id, mutually exclusive partner or None)
NY_EVIDENCED_FACTS = {
    "ny_post_facility_outside_mctd": "ny_post_facility_inside_mctd",
    "ny_post_facility_inside_mctd": "ny_post_facility_outside_mctd",
    "ny_all_costs_in_listed_counties": None,
    "ny_majority_principal_photography_days_in_listed_counties": None,
    "ny_scoring_five_musicians_in_state": None,
    "ny_production_plus_10pct_tier": "ny_production_plus_5pct_tier",
    "ny_production_plus_5pct_tier": "ny_production_plus_10pct_tier",
    # Canada (statutory uplifts on a narrower base; each states a zone or producer fact, or a per-account evidenced portion)
    "on_ofttc_first_time_producer": None,
    "on_ofttc_labour_outside_gta": None,
    # NA-RECONCILIATION-16: the earlier "labour in the regional / distant zone" booleans priced a dollar proxy and are retired; the British Columbia regional and distant-location credits take
    # shooting DAYS (numeric facts below). Two further credits exist only by application: their prerequisite is a stated fact.
    "ca_bc_film_training_program_approved_confirmed": None,
    "ca_bc_scriptwriting_application_confirmed": None,
    # Nova Scotia Location Incentive (NSFPIF Guidelines s.6): more than 50% of principal photography in a rural / non-metropolitan area of Nova Scotia
    "ca_ns_rural_majority_principal_photography_confirmed": None,
    # Nova Scotia Stream (s.6): ownership and control decides the stream, so the two statements are mutually exclusive writers; Content Incentive s.7(b) criteria
    "ca_ns_stream_i_ownership_control_confirmed": "ca_ns_stream_ii_confirmed",
    "ca_ns_stream_ii_confirmed": "ca_ns_stream_i_ownership_control_confirmed",
    "ca_ns_content_majority_copyright_ns_ownership_confirmed": None,
    "ca_ns_content_two_new_trainees_confirmed": None,
    "ca_ns_content_post_75pct_in_ns_confirmed": None,
    "ca_ns_content_ns_resident_producer_confirmed": None,
    "ca_ns_content_ns_spend_75pct_confirmed": None,
    "ca_ns_content_ns_writer_confirmed": None,
    "ca_ns_content_ns_director_confirmed": None,
    # Saskatchewan FFTV (2026-27) streams and bonuses
    "ca_sk_saskatchewan_stream_confirmed": "ca_sk_service_production_stream_confirmed",
    "ca_sk_service_production_stream_confirmed": "ca_sk_saskatchewan_stream_confirmed",
    "ca_sk_majority_post_spend_in_sk_confirmed": None,
    "ca_sk_volume_threshold_confirmed": None,
    # Nova Scotia producer second-position approval (s.4(c)); Montana approved postproduction company (15-31-1009)
    "ca_ns_producer_extra_positions_approved_confirmed": None,
    "us_mt_postproduction_company_approved_confirmed": None,
    # Montana MEDIA (MCA 15-31-1007(3)(b)(ix))
    "us_mt_screen_credit_furnished_confirmed": None,
    # New Brunswick LIFT 2026/27 stackable bonuses
    "ca_nb_bonus_hod_lead_talent_30pct_confirmed": None,
    "ca_nb_made_spend_50pct_confirmed": None,
    "ca_nb_made_copyright_50pct_confirmed": None,
    "ca_nb_made_writer_nb_resident_confirmed": None,
    "ca_nb_made_director_nb_resident_confirmed": None,
    "ca_nb_made_post_20pct_in_nb_confirmed": None,
    "ca_nb_made_photography_days_25pct_in_nb_confirmed": None,
    "mb_frequent_filming_third_film_in_two_years": None,
    "mb_frequent_filming_principal_owner_declared": None,
    "mb_resident_producer_screen_credit": None,
    "mb_rural_permanent_establishment_35km": None,
    "mb_rural_majority_days_35km": None,
    "mb_production_company_bonus_eligible": None,
    "mb_t4_payroll_below_25pct_stated": None,
    "ab_fttc_30pct_criteria_met": None,
    "wv_ten_resident_hires_confirmed": None,
    # BC domestic rate regime by the date principal photography BEGINS (ITA (BC) s.80(8)): the two statements are mutually exclusive (a later statement replaces the earlier one).
    "ca_bc_film_tv_photography_after_2024_confirmed": "ca_bc_film_tv_photography_before_2025_confirmed",
    "ca_bc_film_tv_photography_before_2025_confirmed": "ca_bc_film_tv_photography_after_2024_confirmed",
    # BC 'eligible production' content requirements, each its own resolved requirement (Income Tax Act (BC) s.79(1)); the scenario derives the first three where the allocation establishes them
    "ca_bc_film_tv_bc_cost_75pct_confirmed": None,
    "ca_bc_film_tv_post_75pct_in_bc_confirmed": None,
    "ca_bc_film_tv_photography_days_75pct_in_bc_confirmed": None,
    "ca_bc_film_tv_canadian_content_6_points_confirmed": None,
    "ca_bc_film_tv_distribution_agreement_confirmed": None,
    "nj_film_spend_outside_nyc_radius_confirmed": None,
    # NA-RECONCILIATION-13: Missouri RSMo 135.750 eligibility and uplift facts (statute subsections 3(2)-(6) and 4); none can be read from a topsheet
    "mo_apprentice_or_veteran_minimum_confirmed": None,
    "mo_filmed_50pct_in_missouri_confirmed": None,
    "mo_rural_or_blighted_15pct_confirmed": None,
    "mo_three_departments_missouri_hires_confirmed": None,
    "mo_script_markets_missouri_confirmed": None,
    "mo_second_third_fourth_class_county_confirmed": None,
    # NA-RECONCILIATION-11. Propositions that are ALSO content/approval gates (CPTC certificate and control, NL Part I registration, Colorado/Arizona pre-approval, OCASE permanent
    # establishment) are NOT repeated here: their one persistence owner is the Inspector content-gate control (POST /projects/{id}/content-gates, key <slug>__<kind>_confirmed).
    "on_opstc_ontario_labour_25pct_confirmed": None,
    "on_ocase_ontario_labour_over_cad_25000_stated": None,
    "us_co_workforce_50pct_and_cpa_review_stated": None,
    # facts the canonical rules already read but no producer path could write
    "al_all_payroll_to_alabama_residents": None,
    "ca_bc_dave_eligible_activity_confirmed": None,
    "ca_film_independent_category": None,
    "us_or_opif_award_confirmed": None,
    "us_or_opif_fund_amount_current_confirmed": None,
    "us_or_opif_regional_uplift_confirmed": None,
    "us_tx_miip_award_confirmed": None,
    "us_tx_miip_pool_period_valid": None,
    "mb_two_residents_trained_per_nonresident": "mb_one_resident_trained_per_nonresident",
    "mb_one_resident_trained_per_nonresident": "mb_two_residents_trained_per_nonresident",
}


#: Producer-stated NUMERIC program facts a caller may set: key -> (minimum, maximum). Stored as ``amount_fact:<key>``; null clears (Unknown, never 0).
PROGRAM_AMOUNT_FACTS: dict[str, tuple[float, float]] = {
    "us_tx_miip_awarded_rate_pct": (0.0, 0.31),   # a FRACTION despite the name: the award letter's rate within [0, the 31% ceiling] (RateRule.awarded_rate_min/max)
    "us_tx_miip_resident_crew_pct": (0.0, 100.0),
    "us_tx_miip_resident_cast_pct": (0.0, 100.0),
    # Federal CPTC cost base (CRA RC4164 / T1131 lines 421-430): assistance received or expected, and deferred amounts that are contingent liabilities (excluded from the cost of production)
    "ca_federal_cptc_assistance_usd": (0.0, 1e9),
    "ca_federal_cptc_contingent_liabilities_usd": (0.0, 1e9),
    # British Columbia statutory-formula inputs (ITA (BC) s.81.1, 81.11, 82, 82.2, 82.21, 80.1): day counts and USD amounts, stated by the producer; null (Unknown) clears.
    "ca_bc_principal_photography_days_in_bc": (1.0, 2000.0),
    "ca_bc_principal_photography_days_outside_vancouver": (0.0, 2000.0),
    "ca_bc_principal_photography_days_distant_location": (0.0, 2000.0),
    "ca_bc_training_payments_usd": (0.0, 1e9),
    "ca_bc_training_assistance_usd": (0.0, 1e9),
    "ca_bc_scriptwriting_expenditure_usd": (0.0, 1e9),
    "ca_bc_scriptwriting_assistance_usd": (0.0, 1e9),
    "ca_bc_scriptwriting_parent_reimbursement_usd": (0.0, 1e9),
    # Nova Scotia distant-location incentive inputs: whole days of principal photography in total and in each Halifax City Hall distance band
    "ca_ns_principal_photography_days_total": (1.0, 2000.0),
    "ca_ns_principal_photography_days_100_to_150km": (0.0, 2000.0),
    "ca_ns_principal_photography_days_over_150km": (0.0, 2000.0),
    "ca_ns_principal_photography_days_in_ns": (0.0, 2000.0),
    "ca_ns_hod_positions_filled": (0.0, 16.0),
    "ca_ns_hod_positions_held_by_ns_residents": (0.0, 16.0),
    "ca_ns_principal_performers_total": (1.0, 5000.0),
    "ca_ns_principal_performers_ns_residents": (0.0, 5000.0),
    # Saskatchewan activity test and rural bonus day counts
    "ca_sk_principal_photography_days_total": (1.0, 2000.0),
    "ca_sk_principal_photography_days_in_sk": (0.0, 2000.0),
    "ca_sk_days_50km_outside_regina_saskatoon": (0.0, 2000.0),
    # Montana MEDIA compensation categories (USD and persons), additions and the first expenditure year (MCA 15-31-1007(3)(b), Department of Revenue timing)
    "us_mt_resident_crew_compensation_usd": (0.0, 1e9), "us_mt_resident_crew_persons": (0.0, 5000.0),
    "us_mt_nonresident_crew_compensation_usd": (0.0, 1e9), "us_mt_nonresident_crew_persons": (0.0, 5000.0),
    "us_mt_talent_compensation_usd": (0.0, 1e10), "us_mt_talent_persons": (0.0, 5000.0),
    "us_mt_student_compensation_usd": (0.0, 1e9), "us_mt_student_persons": (0.0, 5000.0),
    "us_mt_veteran_tribal_compensation_usd": (0.0, 1e9), "us_mt_veteran_tribal_persons": (0.0, 5000.0),
    "us_mt_college_campus_payments_usd": (0.0, 1e9), "us_mt_studio_rental_expenditure_usd": (0.0, 1e9), "us_mt_studio_rental_days": (0.0, 2000.0),
    "us_mt_underserved_area_expenditure_usd": (0.0, 1e9), "us_mt_media_expenditure_year": (2025.0, 2100.0),
    # New Brunswick eligible deemed spend (USD, from the Deemed Spend Worksheet) and Nova Scotia amounts that are not eligible costs
    "ca_nb_eligible_deemed_spend_usd": (0.0, 1e9),
    "us_mt_postproduction_wages_usd": (0.0, 1e9),
    "ca_ns_producer_extra_position_fees_usd": (0.0, 1e9),
    "ca_ns_producer_hod_performer_fees_total_usd": (0.0, 1e9),
    "ca_sk_apprenticeship_mentor_salaries_usd": (0.0, 1e9),
    "ca_ns_ineligible_supplier_spend_usd": (0.0, 1e9),
    "ca_ns_equity_tax_credit_financing_usd": (0.0, 1e9),
    # New Brunswick rural / remote principal photography days (distance from Fredericton, Moncton or Saint John City Hall)
    "ca_nb_principal_photography_days_total": (1.0, 2000.0),
    "ca_nb_days_rural_30_to_150km": (0.0, 2000.0),
    "ca_nb_days_remote_151km_plus": (0.0, 2000.0),
    # Project-level eligibility gates (project_eligibility_gates): the producer-stated share of principal-photography days wholly in the jurisdiction, for a split shoot the scenario cannot decide
    "ca_principal_photography_days_in_california_pct": (0.0, 100.0),
    "ma_filming_days_in_massachusetts_pct": (0.0, 100.0),
    "ri_principal_photography_days_in_rhode_island_pct": (0.0, 100.0),
}
AMOUNT_PREFIX = "amount_fact:"

#: Day, person, position and year counts must be whole numbers (the pricing paths refuse a fraction rather than round it).
WHOLE_NUMBER_FACT_PREFIXES = ("ca_bc_principal_photography_days_", "ca_ns_principal_photography_days_", "ca_ns_hod_", "ca_ns_principal_performers_", "ca_nb_principal_photography_days_", "ca_nb_days_", "ca_sk_principal_photography_days_", "ca_sk_days_", "us_mt_studio_rental_days", "us_mt_media_expenditure_year", "us_mt_resident_crew_persons", "us_mt_nonresident_crew_persons", "us_mt_talent_persons", "us_mt_student_persons", "us_mt_veteran_tribal_persons")


def is_whole_number_fact(key: str) -> bool:
    return key.startswith(WHOLE_NUMBER_FACT_PREFIXES)


def expand_uplift_basis(rows) -> tuple[dict[str, float], frozenset[str]]:
    """Stored subsets -> the logical `uplift_basis:<program>:<uplift>:<line id>` amount keys and the SAME keys as evidenced facts
    that allocation_pricing._price_subset_uplifts reads. (The logical key is longer than the 100-character fact_key column, so it
    is stored as one JSON row instead.) A malformed or non-finite amount is dropped, never coerced."""
    amounts: dict[str, float] = {}
    for row in rows:
        if getattr(row, "fact_key", None) != UPLIFT_BASIS_FACT_KEY or not row.value:
            continue
        try:
            data = json.loads(row.value)
        except (TypeError, ValueError):
            continue
        for program, by_uplift in (data or {}).items():
            for uplift, by_line in (by_uplift or {}).items():
                for line_id, amount in (by_line or {}).items():
                    if isinstance(amount, (int, float)) and not isinstance(amount, bool) and math.isfinite(amount) and amount >= 0:
                        amounts[f"uplift_basis:{program}:{uplift}:{line_id}"] = float(amount)
    return amounts, frozenset(amounts)


async def _project_line_amounts(session: AsyncSession, project_id) -> dict[str, float]:
    rows = (await session.execute(
        select(BudgetLineItem.id, BudgetLineItem.amount_usd).join(BudgetDocument, BudgetDocument.id == BudgetLineItem.budget_document_id)
        .where(BudgetDocument.project_id == project_id))).all()
    return {str(i): float(a or 0.0) for i, a in rows}


async def _upsert(session: AsyncSession, project_id, key: str, value: str | None, value_type: str) -> None:
    existing = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == key))).scalar_one_or_none()
    if value is None:
        if existing is not None:
            await session.delete(existing)
        return
    if existing is not None:
        existing.value, existing.value_type = value, value_type
        existing.source_type = ProjectFactSourceType.USER_OVERRIDE.value
        existing.review_status = ReviewStatus.APPROVED.value
    else:
        session.add(ProjectFact(id=uuid.uuid4(), project_id=project_id, fact_key=key, value=value, value_type=value_type,
                                source_type=ProjectFactSourceType.USER_OVERRIDE.value, review_status=ReviewStatus.APPROVED.value))


PRODUCER_ROLES = ("executive", "line", "other")


async def write_ny_program_facts(session: AsyncSession, project_id, *, evidenced: dict | None = None,
                                 payees: list[dict] | None = None, uplift_basis: list[dict] | None = None,
                                 producer_roles: list[dict] | None = None, composer_portions: list[dict] | None = None,
                                 amounts: dict | None = None) -> dict:
    """Validate and persist producer-stated facts. `evidenced`: {fact id: true|null} (null clears -> Unknown). Stating one fact of a
    mutually exclusive pair (inside/outside the commuter district, Production Plus 10%/5% tier) REPLACES the stored partner in the same
    transaction, so two contradictory elections can never be stored; stating both in one request is rejected. NA-RECONCILIATION-22: `evidenced` is tri-state for ordinary legal
    predicates ({fact id: true | false | null}: Yes, a stated No - a REFUTED fact that applies the rule's actual failed treatment - or Unknown); an election accepts only its chosen alternative. `payees`:
    [{line_id, payee_id, compensation_complete}] (payee_id null clears). `producer_roles`: [{line_id, role: executive|line|other|null}].
    `composer_portions`: [{line_id, amount_usd}] -- the part of a music account that is composer compensation (null clears).
    `uplift_basis`: [{program, uplift, line_id, amount_usd}] (amount_usd null clears). Raises ValueError with the reason on any invalid
    entry; nothing is written then."""
    from app.data.program_rate_rules import SUBSET_UPLIFT_RULES
    evidenced, payees, uplift_basis = evidenced or {}, payees or [], uplift_basis or []
    producer_roles, composer_portions = producer_roles or [], composer_portions or []
    amounts = amounts or {}
    for key, value in amounts.items():
        if key not in PROGRAM_AMOUNT_FACTS:
            raise ValueError(f"'{key}' is not a settable numeric program fact")
        lo, hi = PROGRAM_AMOUNT_FACTS[key]
        if is_whole_number_fact(key) and value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and abs(value - round(value)) > 1e-9:
            raise ValueError(f"'{key}' must be a whole number of days")
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < lo or value > hi):
            raise ValueError(f"'{key}' must be a finite number between {lo:g} and {hi:g}, or null (Unknown)")
    lines = await _project_line_amounts(session, project_id) if (payees or uplift_basis or producer_roles or composer_portions) else {}
    for fid, value in evidenced.items():
        if fid not in NY_EVIDENCED_FACTS:
            raise ValueError(f"'{fid}' is not a settable program fact")
        partner = NY_EVIDENCED_FACTS[fid]
        if value not in (True, False, None):
            raise ValueError(f"'{fid}' accepts true (Yes), false (No) or null (Unknown)")
        if value is False and partner:
            raise ValueError(f"'{fid}' is an election between mutually exclusive alternatives: state the alternative that applies ('{partner}') instead of a No")
        if value is True and partner and evidenced.get(partner) is True:
            raise ValueError(f"'{fid}' and '{partner}' cannot both be stated")
    for p in payees:
        if str(p.get("line_id")) not in lines:
            raise ValueError(f"payee line {p.get('line_id')!r} is not a line of this project's budget")
        if p.get("payee_id") is not None and not str(p["payee_id"]).strip():
            raise ValueError("payee_id must be a non-empty identifier or null")
        if p.get("payee_type") is not None:
            from app.calculators.per_payee_limits import PAYEE_TYPE_CODES
            if p["payee_type"] not in PAYEE_TYPE_CODES:
                raise ValueError(f"payee_type must be one of {sorted(PAYEE_TYPE_CODES)} or null")
    for r in producer_roles:
        if str(r.get("line_id")) not in lines:
            raise ValueError(f"producer role line {r.get('line_id')!r} is not a line of this project's budget")
        if r.get("role") is not None and r["role"] not in PRODUCER_ROLES:
            raise ValueError(f"producer role must be one of {PRODUCER_ROLES} or null")
    for c in composer_portions:
        if str(c.get("line_id")) not in lines:
            raise ValueError(f"composer line {c.get('line_id')!r} is not a line of this project's budget")
        amount = c.get("amount_usd")
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount)
                                   or amount < 0 or amount > lines[str(c["line_id"])] + 0.005):
            raise ValueError(f"composer portion for line {c['line_id']} must be a finite number within the line's budget amount")
    for u in uplift_basis:
        rule_ids = {r.uplift_id for r in SUBSET_UPLIFT_RULES.get(u.get("program"), ())}
        if u.get("uplift") not in rule_ids:
            raise ValueError(f"unknown uplift {u.get('program')!r}/{u.get('uplift')!r}")
        if str(u.get("line_id")) not in lines:
            raise ValueError(f"uplift line {u.get('line_id')!r} is not a line of this project's budget")
        amount = u.get("amount_usd")
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount)
                                   or amount < 0 or amount > lines[str(u["line_id"])] + 0.005):
            raise ValueError(f"uplift amount for line {u['line_id']} must be a finite number within the line's budget amount")
    if amounts:
        # cross-field relations on the merged stored + incoming numbers (an unstated side is never assumed); NA-RECONCILIATION-21
        from app.services.producer_fact_catalog import stored_values, validate_relations
        _stored_bool, merged = await stored_values(session, project_id)
        for k, v in amounts.items():
            if v is None:
                merged.pop(k, None)
            else:
                merged[k] = float(v)
        try:
            validate_relations(merged)
        except ValueError as exc:
            raise ValueError(str(exc)) from None
    replaced: list[str] = []
    for fid, value in evidenced.items():
        partner = NY_EVIDENCED_FACTS[fid]
        if value is True and partner:
            stored = (await session.execute(select(ProjectFact).where(
                ProjectFact.project_id == project_id, ProjectFact.fact_key == EVIDENCED_PREFIX + partner))).scalar_one_or_none()
            if stored is not None:
                await session.delete(stored)       # the producer changed the answer: the contradictory partner is cleared atomically
                replaced.append(partner)
        await _upsert(session, project_id, EVIDENCED_PREFIX + fid, "true" if value is True else ("false" if value is False else None), "boolean")
    for key, value in amounts.items():
        await _upsert(session, project_id, AMOUNT_PREFIX + key, None if value is None else repr(float(value)), "number")
    for p in payees:
        lid = str(p["line_id"])
        pid = None if p.get("payee_id") is None else str(p["payee_id"]).strip()
        await _upsert(session, project_id, f"line_fact:{lid}:payee_id", pid, "string")
        await _upsert(session, project_id, f"line_fact:{lid}:payee_compensation_complete",
                      "true" if (pid and p.get("compensation_complete") is True) else None, "boolean")
        if "payee_type" in p:
            await _upsert(session, project_id, f"line_fact:{lid}:payee_type", p["payee_type"] if pid else None, "string")
    for r in producer_roles:
        await _upsert(session, project_id, f"line_fact:{str(r['line_id'])}:producer_role", r.get("role"), "string")
    for c in composer_portions:
        amount = c.get("amount_usd")
        await _upsert(session, project_id, f"line_fact:{str(c['line_id'])}:composer_compensation_usd", None if amount is None else repr(float(amount)), "number")
    if uplift_basis:
        row = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id, ProjectFact.fact_key == UPLIFT_BASIS_FACT_KEY))).scalar_one_or_none()
        data = json.loads(row.value) if row is not None and row.value else {}
        for u in uplift_basis:
            by_line = data.setdefault(u["program"], {}).setdefault(u["uplift"], {})
            if u.get("amount_usd") is None:
                by_line.pop(str(u["line_id"]), None)
            else:
                by_line[str(u["line_id"])] = float(u["amount_usd"])
        await _upsert(session, project_id, UPLIFT_BASIS_FACT_KEY, json.dumps(data, sort_keys=True), "json")
    await session.flush()
    return {"evidenced": sorted(evidenced), "amounts": sorted(amounts), "replaced": replaced, "payee_lines": [str(p["line_id"]) for p in payees],
            "producer_role_lines": [str(r["line_id"]) for r in producer_roles], "composer_lines": [str(c["line_id"]) for c in composer_portions],
            "uplift_lines": [str(u["line_id"]) for u in uplift_basis]}
