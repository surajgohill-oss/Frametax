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

# NA-RECONCILIATION-22: facts that the producer-fact writer has always accepted but that no catalog group labelled, so the Overview never offered them (New York, Ontario, Manitoba, Alberta, Missouri, West Virginia,
# New Jersey, Colorado, Alabama, BC DAVE, California independent productions, Oregon, Texas and the project-level gate percentages).
GROUPS = GROUPS + (
    ("us_ny", "New York", ("ny_state_film", "us_ny_post_production_credit"), "Tax Law 24 and Public Authorities Law 1262", [
        ("ny_post_facility_outside_mctd", "The post-production facility is OUTSIDE the Metropolitan Commuter Transportation District", "35% post-production credit; an election with the inside statement"),
        ("ny_post_facility_inside_mctd", "The post-production facility is INSIDE the Metropolitan Commuter Transportation District", "10% rate; an election with the outside statement"),
        ("ny_all_costs_in_listed_counties", "All production costs are in the listed upstate counties", "+10% of compensation; the whole base is inside the uplift"),
        ("ny_majority_principal_photography_days_in_listed_counties", "The majority of principal-photography days are in the listed counties", "Other qualified costs in the listed counties earn +10% only with this"),
        ("ny_scoring_five_musicians_in_state", "Scoring includes payment to at least five New York musicians", "+10% of in-state scoring costs"),
        ("ny_production_plus_10pct_tier", "Production Plus 10% tier (initial applications total at least USD 50 million)", "An election with the 5% tier"),
        ("ny_production_plus_5pct_tier", "Production Plus 5% tier (initial applications total at least USD 20 million)", "An election with the 10% tier"),
    ]),
    ("ca_on", "Ontario", ("on_ofttc", "on_opstc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"), "Ontario Creates OFTTC, OPSTC and OCASE guidelines", [
        ("on_ofttc_first_time_producer", "The producer is a first-time producer", "40% on the first CAD 240,000 of qualifying labour"),
        ("on_ofttc_labour_outside_gta", "The production is shot outside the Greater Toronto Area", "10% bonus on Ontario labour expenditures"),
        ("on_opstc_ontario_labour_25pct_confirmed", "Ontario labour is at least 25% of the qualifying production expenditures claimed", "A condition of the OPSTC"),
        ("on_ocase_ontario_labour_over_cad_25000_stated", "More than CAD 25,000 of Ontario labour is spent on eligible animation or special effects", "OCASE threshold"),
    ]),
    ("ca_mb", "Manitoba", ("ca_mb_film_video_credit",), "Manitoba Film & Music TC1 guidelines", [
        ("mb_frequent_filming_third_film_in_two_years", "This is the third film shot in Manitoba within two years", "+10% Frequent Filming Bonus"),
        ("mb_frequent_filming_principal_owner_declared", "The principal owner of the production company is declared", "Required for the Frequent Filming Bonus"),
        ("mb_resident_producer_screen_credit", "A Manitoba resident is Producer, Co-Producer or Executive Producer with a screen credit", "+5%"),
        ("mb_rural_permanent_establishment_35km", "The applicant has a permanent establishment at least 35 km from Winnipeg", "Rural bonus (needs the days test too)"),
        ("mb_rural_majority_days_35km", "At least 50% of Manitoba shooting days are at least 35 km from Winnipeg", "Rural bonus (needs the establishment too)"),
        ("mb_production_company_bonus_eligible", "The production company bonus applies", "Production company bonus"),
        ("mb_t4_payroll_below_25pct_stated", "T4 payroll is below 25% of the Manitoba labour claimed", "Payroll treatment"),
        ("mb_two_residents_trained_per_nonresident", "Two Manitoba residents are trained per non-resident", "Training condition; an election with the one-per-non-resident statement"),
        ("mb_one_resident_trained_per_nonresident", "One Manitoba resident is trained per non-resident", "Training condition; an election with the two-per statement"),
    ]),
    ("ca_ab", "Alberta", ("ca_ab_fttc",), "Alberta Film and Television Tax Credit", [
        ("ab_fttc_30pct_criteria_met", "All of the 30% rate criteria are met (50% Alberta ownership, Alberta producer, Alberta copyright and more)", "The 30% rate needs ALL of them"),
    ]),
    ("us_mo", "Missouri", ("us_mo_motion_media_production_tax_credit",), "RSMo 135.750 subsection 3", [
        ("mo_apprentice_or_veteran_minimum_confirmed", "The project employs the statutory minimum of Missouri apprentices or resident veterans", "Eligibility condition"),
        ("mo_filmed_50pct_in_missouri_confirmed", "At least 50% of the project is filmed in Missouri", "+5 points; a full-relocation scenario establishes it"),
        ("mo_rural_or_blighted_15pct_confirmed", "At least 15% of the Missouri filming is in a rural or blighted area", "+5 points; 15% is the threshold, not 15 points"),
        ("mo_three_departments_missouri_hires_confirmed", "At least three departments hire a Missouri resident ready to advance or learn a new skillset", "+5 points"),
        ("mo_script_markets_missouri_confirmed", "The script positively markets a Missouri place (five cleared photographs)", "+5 points"),
        ("mo_second_third_fourth_class_county_confirmed", "The project is in a second-, third- or fourth-class county", "+2 points (10% of the 20% base)"),
    ]),
    ("us_wv_nj_co_al", "West Virginia, New Jersey, Colorado, Alabama", ("us_wv_film_production_tax_credit", "us_nj_garden_state_film_credit", "us_co_film_incentive", "us_al_film_incentive"), "State film incentive statutes and agency guidance", [
        ("wv_ten_resident_hires_confirmed", "The company employs 10 or more West Virginia residents as full-time employees", "Additional 4%"),
        ("nj_film_spend_outside_nyc_radius_confirmed", "Spend is outside the 30-mile radius of the New York City reference point", "35% rate"),
        ("us_co_workforce_50pct_and_cpa_review_stated", "At least 50% Colorado resident workforce with a Colorado-performed CPA review", "Colorado incentive condition"),
        ("al_all_payroll_to_alabama_residents", "All payroll is paid to Alabama residents", "35% of payroll"),
    ]),
    ("ca_film", "California and BC DAVE", ("ca_film_30", "ca_bc_dave"), "California Program 4.0 Guidelines; Income Tax Act (BC) s.81.2", [
        ("ca_film_independent_category", "The production is in the independent category", "Changes the VFX uplift treatment"),
        ("ca_bc_dave_eligible_activity_confirmed", "The activity is genuine digital animation, visual effects or post-production performed in BC", "DAVE eligibility"),
    ]),
    ("us_or_tx", "Oregon and Texas awards", ("us_or_opif", "us_tx_miip"), "Oregon OPIF and Texas SB22 Moving Image Industry Incentive", [
        ("us_or_opif_award_confirmed", "An Oregon OPIF award contract exists", "Agency award"),
        ("us_or_opif_fund_amount_current_confirmed", "The OPIF annual fund figure is confirmed current", "Fund ceiling"),
        ("us_or_opif_regional_uplift_confirmed", "Shooting is outside the Portland metropolitan zone", "x1.10 multiplier"),
        ("us_tx_miip_award_confirmed", "A Texas grant award exists", "Agency award"),
        ("us_tx_miip_pool_period_valid", "The award falls within a valid biennial appropriation period", "Pool period"),
        ("us_tx_miip_awarded_rate_pct", "Awarded rate (a fraction, for example 0.25)", "Within the 31% ceiling"),
        ("us_tx_miip_resident_crew_pct", "Percent of paid crew who are Texas residents (0-100)", "At least 35%"),
        ("us_tx_miip_resident_cast_pct", "Percent of paid cast who are Texas residents (0-100)", "At least 35%"),
    ]),
    ("project_gates", "Project-level eligibility gates", ("ca_film_30", "us_ma_film_tax_credit", "us_ri_film_credit"), "California Program 4.0 II.A.1; Massachusetts DOR; R.I. Gen. Laws 44-31.2", [
        ("ca_principal_photography_days_in_california_pct", "Share of principal-photography days wholly in California (0-100)", "75% days branch; needed only for a split shoot"),
        ("ma_filming_days_in_massachusetts_pct", "Share of filming days in Massachusetts (0-100)", "75% days branch; needed only for a split shoot"),
        ("ri_principal_photography_days_in_rhode_island_pct", "Share of principal-photography days in Rhode Island (0-100)", "51% primary-location test; needed only for a split shoot"),
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
            elif name in CATALOG and (row.value or "").strip().lower() in ("false", "0", "no"):
                booleans[name] = False                  # a stated No is a refuted fact (NA-RECONCILIATION-22), distinct from absence
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
    """The served view of the program facts (read-only; never evaluates): the resolved-requirements view (resolved_facts), one value + provenance per fact."""
    from app.services.resolved_facts import resolved_requirements_view
    return await resolved_requirements_view(session, project_id)
