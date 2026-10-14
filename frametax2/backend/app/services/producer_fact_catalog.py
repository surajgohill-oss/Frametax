"""Display catalog and cross-field relations for the producer-stated program facts added in NA-RECONCILIATION-16 to NA-20 (NA-RECONCILIATION-21).

This module owns METADATA ONLY (group, label, help, unit). Storage, bounds, exclusivity and the one writer stay in ``ny_producer_facts`` (ProjectFact rows, prefixes ``evidenced_program_fact:`` and
``amount_fact:``); the evaluation fingerprint already covers them through ``canonical_project_economics``. Nothing here defaults a value: an absent row is UNKNOWN, a boolean can only be STATED (a false is never
stored), a stated 0 is a real zero and is different from Unknown. The served view separates original document evidence from these producer-stated assumptions: every value carries
``source: PRODUCER_STATED`` and none is ever merged into the budget-derived evidence."""
from __future__ import annotations

import json
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_fact import ProjectFact
from app.services import ny_producer_facts as npf

# (group id, title, programs it feeds, authority, [(fact key, label, help)])
GROUPS: tuple = (
    ("ca_bc_film_tv", "British Columbia film and television credit", ("ca_bc_film_tv_tax_credit", "ca_bc_pstc"), "Income Tax Act (BC) Part 5 (s.80-82.4)", [
        ("ca_bc_film_tv_photography_after_2024_confirmed", "Principal photography begins after 31 Dec 2024", "40% regime (s.80(8)); excludes the opposite statement"),
        ("ca_bc_film_tv_photography_before_2025_confirmed", "Principal photography began on or before 31 Dec 2024", "35% regime; removes the 40% scenario"),
        ("ca_bc_principal_photography_days_in_bc", "Principal photography days in British Columbia (TD)", "Whole days; the denominator of the regional and distant-location credits"),
        ("ca_bc_principal_photography_days_outside_vancouver", "Days outside the designated Vancouver area (RD)", "Regional credit needs at least 5 days and more than 50% of TD"),
        ("ca_bc_principal_photography_days_distant_location", "Days in a distant location (DLD)", "Distant-location credit needs at least 1 day and the regional credit"),
        ("ca_bc_film_training_program_approved_confirmed", "An approved training program with BC-based trainees exists", "The film training credit exists only with this (s.82)"),
        ("ca_bc_training_payments_usd", "Payments attributable to training (USD)", "Salary and remuneration paid to the trainees while in the program"),
        ("ca_bc_training_assistance_usd", "Assistance received for the trainees or program (USD)", "State 0 when there is none; leaving it blank keeps the figure unconfirmed"),
        ("ca_bc_scriptwriting_application_confirmed", "A scriptwriting credit application is made", "Photography begins in the taxation year (s.80.1)"),
        ("ca_bc_scriptwriting_expenditure_usd", "Eligible BC scriptwriting expenditure (SE, USD)", "Paid to BC-based scriptwriters within 60 days of year end"),
        ("ca_bc_scriptwriting_assistance_usd", "Assistance in respect of the scriptwriting expenditure (TA, USD)", "State 0 when there is none"),
        ("ca_bc_scriptwriting_parent_reimbursement_usd", "Parent reimbursement included in SE (RE, USD)", "State 0 when there is none"),
    ]),
    ("ca_federal_cptc", "Federal CPTC cost base", ("ca_federal_cptc",), "CRA RC4164 / T1131 lines 421-430", [
        ("ca_federal_cptc_assistance_usd", "Assistance received or expected (USD)", "Provincial credits and grants are assistance (line 423)"),
        ("ca_federal_cptc_contingent_liabilities_usd", "Deferred contingent liabilities in the budget (USD)", "Excluded from cost of production (line 421); an enforceable liability is included"),
    ]),
    ("ca_nb", "New Brunswick LIFT (Major Production)", ("ca_nb_film_tax_credit",), "LIFT 2026/2027 Program Guidelines", [
        ("ca_nb_principal_photography_days_total", "Total principal photography days", "Whole days"),
        ("ca_nb_days_rural_30_to_150km", "Days 30-150 km from Fredericton, Moncton or Saint John City Hall", "Rural NB communities"),
        ("ca_nb_days_remote_151km_plus", "Days 151 km or more from those city halls", "Remote locations"),
        ("ca_nb_bonus_hod_lead_talent_30pct_confirmed", "30%+ of Head of Department positions or Lead Talent are NB residents", "No deemed residents"),
        ("ca_nb_made_spend_50pct_confirmed", "NB Made: NB spend is at least 50% of total cost", "Two of the six NB Made criteria are needed"),
        ("ca_nb_made_copyright_50pct_confirmed", "NB Made: NB copyright is at least 50%", ""),
        ("ca_nb_made_writer_nb_resident_confirmed", "NB Made: principal writer is an NB resident", "For a series, most episodes"),
        ("ca_nb_made_director_nb_resident_confirmed", "NB Made: principal director is an NB resident", "For a series, most episodes"),
        ("ca_nb_made_post_20pct_in_nb_confirmed", "NB Made: at least 20% of post-production is in NB", ""),
        ("ca_nb_made_photography_days_25pct_in_nb_confirmed", "NB Made: at least 25% of photography days are in NB", ""),
        ("ca_nb_eligible_deemed_spend_usd", "Eligible deemed spend (USD)", "From the Deemed Spend Worksheet (portal only); not above-the-line; counted up to 15% of eligible NB spend"),
    ]),
    ("ca_ns", "Nova Scotia Film & Television Production Incentive Fund", ("ca_ns_production_incentive_fund",), "NSFPIF Guidelines (April 1, 2024)", [
        ("ca_ns_stream_i_ownership_control_confirmed", "Stream I: Nova Scotian ownership and control of production (50%+)", "Base 26%; excludes Stream II"),
        ("ca_ns_stream_ii_confirmed", "Stream II: less than 50% Nova Scotian ownership and control", "Base 25%; excludes Stream I"),
        ("ca_ns_rural_majority_principal_photography_confirmed", "More than 50% of principal photography is rural / non-metropolitan (over 30 km from Halifax City Hall)", "Location Incentive; needed first for the Distant Location Incentive"),
        ("ca_ns_principal_photography_days_total", "Total principal photography days", "Whole days; the denominator of the Distant Location Incentive"),
        ("ca_ns_principal_photography_days_100_to_150km", "Days 100-150 km from Halifax City Hall", "7% band"),
        ("ca_ns_principal_photography_days_over_150km", "Days more than 150 km from Halifax City Hall", "10% band"),
        ("ca_ns_principal_photography_days_in_ns", "Principal photography days in Nova Scotia", "Shooting Length Incentive needs more than 30"),
        ("ca_ns_hod_positions_filled", "Head of Department positions filled (of 16)", "Whole number"),
        ("ca_ns_hod_positions_held_by_ns_residents", "Of those, held by Nova Scotia residents (including eligible substitutions)", "Below the stream minimum the base falls 0.5 point per position"),
        ("ca_ns_principal_performers_total", "Principal performers, actors, stunt performers and stunt actors (excluding background)", "Whole number"),
        ("ca_ns_principal_performers_ns_residents", "Of those, Nova Scotia residents", "60% or more earns +1.5 points"),
        ("ca_ns_content_majority_copyright_ns_ownership_confirmed", "Content: majority copyright with Nova Scotian ownership and control", "Three of the seven content criteria earn +1.5 points"),
        ("ca_ns_content_two_new_trainees_confirmed", "Content: two trainees with no prior paid experience for the whole production", ""),
        ("ca_ns_content_post_75pct_in_ns_confirmed", "Content: 75% of post-production in Nova Scotia", ""),
        ("ca_ns_content_ns_resident_producer_confirmed", "Content: producer is a Nova Scotia resident of two years", ""),
        ("ca_ns_content_ns_spend_75pct_confirmed", "Content: Nova Scotia spend is 75% of total cost and over CAD 25,000", ""),
        ("ca_ns_content_ns_writer_confirmed", "Content: principal writer is a Nova Scotia resident", ""),
        ("ca_ns_content_ns_director_confirmed", "Content: principal director is a Nova Scotia resident", ""),
        ("ca_ns_ineligible_supplier_spend_usd", "Spend that is not Eligible Nova Scotia Cost (USD)", "Non-Nova Scotia suppliers, out-of-province subcontracts, in-kind, capital items"),
        ("ca_ns_equity_tax_credit_financing_usd", "Equity Tax Credit Act financing received (USD)", "Deducted from eligible costs (s.3.2(b))"),
        ("ca_ns_producer_extra_position_fees_usd", "Fees for a producer's second and further Head of Department / performer positions (USD)", "Not eligible without the Administrator's advance approval"),
        ("ca_ns_producer_extra_positions_approved_confirmed", "The Administrator approved those extra positions in advance", "Total such fees are then limited to 20% of the budget"),
        ("ca_ns_producer_hod_performer_fees_total_usd", "Total Head of Department / performer fees paid to producers (USD)", "Above 20% of the budget is not eligible"),
    ]),
    ("ca_sk", "Saskatchewan Feature Film & Television Production Grant", ("ca_sk_creative_saskatchewan_grant",), "Creative Saskatchewan FFTV Guidelines 2026-27", [
        ("ca_sk_saskatchewan_stream_confirmed", "Saskatchewan Stream applicant (Saskatchewan-owned, copyright share proportional to funding)", "Base 30%; excludes the Service Production Stream"),
        ("ca_sk_service_production_stream_confirmed", "Service Production Stream applicant", "Base 25%, total capped at 35%; excludes the Saskatchewan Stream"),
        ("ca_sk_principal_photography_days_total", "Total principal photography days", "Whole days"),
        ("ca_sk_principal_photography_days_in_sk", "Principal photography days in Saskatchewan", "51% or more is the activity test every bonus needs"),
        ("ca_sk_days_50km_outside_regina_saskatoon", "Days at least 50 km outside Regina or Saskatoon", "Rural Bonus needs more than half of the days"),
        ("ca_sk_majority_post_spend_in_sk_confirmed", "The majority of post-production spend is in Saskatchewan", "Post Production Bonus"),
        ("ca_sk_volume_threshold_confirmed", "Production Volume threshold met (two eligible completed projects and CAD 1.5 million over four fiscal years)", "Volume Bonus"),
        ("ca_sk_apprenticeship_mentor_salaries_usd", "Eligible non-resident mentor salaries during training (USD)", "Apprenticeship Stream; below-the-line unless approved"),
    ]),
    ("us_mt", "Montana MEDIA credit", ("us_mt_media_act_tax_credit",), "MCA 15-31-1003, 15-31-1007, 15-31-1009", [
        ("us_mt_media_expenditure_year", "Year the expenditures are incurred", "The Department of Revenue states 2031 is the first credit year"),
        ("us_mt_resident_crew_compensation_usd", "Resident crew and production staff compensation (USD)", "25%, up to USD 150,000 of credit per person"),
        ("us_mt_resident_crew_persons", "Resident crew and production staff persons", "Whole number; each person in one category only"),
        ("us_mt_nonresident_crew_compensation_usd", "Non-resident crew compensation with Montana tax withheld (USD)", "15%, up to USD 150,000 of credit per person"),
        ("us_mt_nonresident_crew_persons", "Non-resident crew persons", ""),
        ("us_mt_talent_compensation_usd", "Actor, director, producer and writer compensation with Montana tax withheld (USD)", "20% of the first USD 7.5 million per person"),
        ("us_mt_talent_persons", "Actor, director, producer and writer persons", ""),
        ("us_mt_student_compensation_usd", "Enrolled student compensation (USD)", "30%, up to USD 50,000 of credit per student"),
        ("us_mt_student_persons", "Student persons", ""),
        ("us_mt_veteran_tribal_compensation_usd", "Resident veteran or tribal member compensation (USD)", "30%, up to USD 150,000 of credit per person"),
        ("us_mt_veteran_tribal_persons", "Veteran or tribal member persons", ""),
        ("us_mt_college_campus_payments_usd", "Payments to a Montana college for on-campus stages, equipment or locations (USD)", "+10%"),
        ("us_mt_studio_rental_expenditure_usd", "In-studio facility and equipment rental in Montana (USD)", "+10% for a studio rented 20 days or more"),
        ("us_mt_studio_rental_days", "Days the studio is rented", "Whole days"),
        ("us_mt_underserved_area_expenditure_usd", "Production expenditure in an underserved area (USD)", "+5%; a county with 14%+ poverty"),
        ("us_mt_screen_credit_furnished_confirmed", "The production includes a Montana screen credit furnished by the state", "+5% of base investment"),
        ("us_mt_postproduction_wages_usd", "Qualified postproduction wages in Montana (USD)", "Wages inside the post-production lines"),
        ("us_mt_postproduction_company_approved_confirmed", "The claimant is a Commerce-approved postproduction company", "25% of qualified postproduction wages (15-31-1009)"),
    ]),
)

#: Cross-field relations (a <= b): checked when both sides are stated, on the merged stored + incoming values. (a, b, reason)
RELATIONS: tuple = (
    ("ca_bc_principal_photography_days_outside_vancouver", "ca_bc_principal_photography_days_in_bc", "days outside the designated Vancouver area cannot exceed the principal photography days in British Columbia"),
    ("ca_bc_principal_photography_days_distant_location", "ca_bc_principal_photography_days_outside_vancouver", "distant-location days lie outside the designated Vancouver area, so they cannot exceed those days"),
    ("ca_ns_principal_photography_days_100_to_150km", "ca_ns_principal_photography_days_total", "band days cannot exceed the total principal photography days"),
    ("ca_ns_principal_photography_days_over_150km", "ca_ns_principal_photography_days_total", "band days cannot exceed the total principal photography days"),
    ("ca_ns_principal_photography_days_in_ns", "ca_ns_principal_photography_days_total", "days in Nova Scotia cannot exceed the total principal photography days"),
    ("ca_ns_hod_positions_held_by_ns_residents", "ca_ns_hod_positions_filled", "positions held by residents cannot exceed the positions filled"),
    ("ca_ns_principal_performers_ns_residents", "ca_ns_principal_performers_total", "resident performers cannot exceed the performers"),
    ("ca_sk_principal_photography_days_in_sk", "ca_sk_principal_photography_days_total", "days in Saskatchewan cannot exceed the total principal photography days"),
    ("ca_sk_days_50km_outside_regina_saskatoon", "ca_sk_principal_photography_days_total", "rural days cannot exceed the total principal photography days"),
)
#: Sums (a + b <= c): the distance bands are exclusive.
SUM_RELATIONS: tuple = (
    (("ca_nb_days_rural_30_to_150km", "ca_nb_days_remote_151km_plus"), "ca_nb_principal_photography_days_total", "rural and remote days together cannot exceed the total principal photography days"),
    (("ca_ns_principal_photography_days_100_to_150km", "ca_ns_principal_photography_days_over_150km"), "ca_ns_principal_photography_days_total", "the two distance bands are exclusive and together cannot exceed the total principal photography days"),
)


def _catalog() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for gid, title, programs, authority, facts in GROUPS:
        for key, label, hint in facts:
            out[key] = {"group": gid, "group_title": title, "programs": list(programs), "authority": authority, "label": label, "help": hint}
    return out


CATALOG: dict[str, dict] = _catalog()


def validate_relations(values: dict[str, float | None]) -> None:
    """ValueError for any stated pair that contradicts another stated number; an unstated side is never assumed."""
    for a, b, reason in RELATIONS:
        if values.get(a) is not None and values.get(b) is not None and values[a] > values[b]:
            raise ValueError(f"{a} ({values[a]:g}) and {b} ({values[b]:g}): {reason}")
    for members, total, reason in SUM_RELATIONS:
        stated = [values.get(m) for m in members]
        if values.get(total) is not None and any(v is not None for v in stated) and sum(v for v in stated if v is not None) > values[total]:
            raise ValueError(f"{' + '.join(members)} exceed {total} ({values[total]:g}): {reason}")


async def stored_values(session: AsyncSession, project_id) -> tuple[dict[str, bool], dict[str, float]]:
    """(stated booleans, stated numbers) for the catalog keys, read from the ONE canonical ProjectFact rows. Absent = Unknown."""
    rows = (await session.execute(select(ProjectFact).where(ProjectFact.project_id == project_id))).scalars().all()
    booleans: dict[str, bool] = {}
    numbers: dict[str, float] = {}
    for row in rows:
        key = row.fact_key
        if key.startswith(npf.EVIDENCED_PREFIX):
            name = key[len(npf.EVIDENCED_PREFIX):]
            if name in CATALOG and (row.value or "").strip().lower() in ("true", "1", "yes"):
                booleans[name] = True
        elif key.startswith(npf.AMOUNT_PREFIX):
            name = key[len(npf.AMOUNT_PREFIX):]
            if name in CATALOG and row.value not in (None, ""):
                try:
                    parsed = float(row.value)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(parsed):
                    numbers[name] = parsed
    return booleans, numbers


async def program_facts_view(session: AsyncSession, project_id) -> dict:
    """The served view of the producer-stated program facts (read-only; never evaluates). Per fact: kind, STATED / UNKNOWN, the stated number, bounds, exclusive partner and provenance."""
    booleans, numbers = await stored_values(session, project_id)
    groups = []
    for gid, title, programs, authority, facts in GROUPS:
        rows = []
        for key, label, hint in facts:
            if key in npf.PROGRAM_AMOUNT_FACTS:
                lo, hi = npf.PROGRAM_AMOUNT_FACTS[key]
                value = numbers.get(key)
                rows.append({"key": key, "kind": "number", "label": label, "help": hint, "state": "STATED" if value is not None else "UNKNOWN", "value": value, "min": lo, "max": hi,
                             "whole": npf.is_whole_number_fact(key),
                             "unit": "USD" if key.endswith("_usd") else None, "source": "PRODUCER_STATED"})
            else:
                partner = npf.NY_EVIDENCED_FACTS.get(key)
                rows.append({"key": key, "kind": "boolean", "label": label, "help": hint, "state": "STATED" if booleans.get(key) else "UNKNOWN", "value": True if booleans.get(key) else None,
                             "exclusive_with": partner if isinstance(partner, str) else None, "source": "PRODUCER_STATED"})
        groups.append({"id": gid, "title": title, "programs": list(programs), "authority": authority, "facts": rows,
                       "stated_count": sum(1 for r in rows if r["state"] == "STATED")})
    return {
        "groups": groups,
        "stated_count": sum(g["stated_count"] for g in groups),
        "note": ("Producer-stated inputs, kept separate from the evidence read from the budget and documents. Leaving a field blank means Unknown, never zero or No; a yes/no statement can only be made as Yes "
                 "(a No is never stored). Nothing is assumed for an unstated day count, wage, approval or eligibility gate: the affected credit stays a bounded potential until it is stated."),
    }
