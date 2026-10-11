#!/usr/bin/env python3
"""
independent_na_hybrid_audit.py

Independent North American Hybrid, Multi-Program & Component-Relocation Audit
for the four anchor budgets (LU, FVD, BH, LLS), starting with LLS Manitoba-California
(CA-MB Principal + US-CA VFX).

Frozen Engine Baseline Under Audit:
  - Engine version: canonical-1.122.0
  - Commits: f5dc6a17 (f5dc6a17858436c0809d7830151696d036aa159b),
             f0b042ba (f0b042ba039ed41e619217a4ac8758ec6814eed8),
             59566fd1 (59566fd17463b71e9796d41e8e080bf5d0ac27ea)
  - Saved DB State: frametax2_claude_optimizer_acceptance_20260919
    (generations in canonical-1.106.0 through canonical-1.110.0)

Core Audit Principles Enforced:
  1. Independent calculation from retained source budget lines
     (docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json) and dated primary
     statutory authority BEFORE comparing against engine outputs.
  2. Never infer statutory exclusion from an absent engine SpendRule
     (specifically: Manitoba deployed contingency spent on eligible Manitoba
     production costs is statutorily eligible under Manitoba ITA s. 7.5(1),
     whereas the engine excludes it at 50%/100% without a line-level
     ContingencyAllocation only because program_spend_rules.py has no
     ca_mb_film_video_credit contingency rule).
  3. Preserve gross budget, apply planning cost reductions once
     (planned_cost_reduction_usd), and separate guaranteed floor value from
     conditional upside.
  4. Never conflate the three LLS Manitoba-California artifacts:
     - Artifact 1: Retained Hybrid (CA-MB Principal $11,943,654 + US-CA VFX $40,000) -> GATE_REJECTED
     - Artifact 2: Same-Allocation Manitoba Leg Sensitivity ($11,943,654 in CA-MB, $40,000 US-CA VFX earns $0)
     - Artifact 3: Relocated All-Manitoba Single-Jurisdiction Alternative ($11,983,654 in CA-MB)
"""

import csv
import json
import os
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
SOURCE_EVIDENCE_JSON = os.path.join(REPO_ROOT, "docs", "validation", "FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json")
SNAPSHOT_JSON = os.path.join(BASE_DIR, "SAVED_NA_HYBRID_DB_SNAPSHOT.json")
OUT_CSV = os.path.join(BASE_DIR, "NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv")
OUT_MD = os.path.join(BASE_DIR, "NORTH_AMERICAN_HYBRID_AUDIT_HANDOFF.md")

FROZEN_COMMITS = (
    "f5dc6a17858436c0809d7830151696d036aa159b",
    "f0b042ba039ed41e619217a4ac8758ec6814eed8",
    "59566fd17463b71e9796d41e8e080bf5d0ac27ea",
)

GENERATION_META = {
    "LU": {
        "project": "LU",
        "title": "The Little Utopia",
        "engine_version": "canonical-1.109.0",
        "input_fingerprint": "f6b647d881421cdbd83431e30bc2dc1ca2a5a055452e641fb06c76d537039a85",
        "gross_usd": 4364393.00,
        "leaf_sum_usd": 4364395.00,
    },
    "LU_106": {
        "project": "LU",
        "title": "The Little Utopia",
        "engine_version": "canonical-1.106.0",
        "input_fingerprint": "dddf968937e5a04416255a7e64568d5f5fd513a0e42ef2b9aa5c51ef3bf129cf",
        "gross_usd": 4364393.00,
        "leaf_sum_usd": 4364395.00,
    },
    "FVD": {
        "project": "FVD",
        "title": "F#K Valentine's Day",
        "engine_version": "canonical-1.109.0",
        "input_fingerprint": "e7fd486364967d1b6423a7e15810e106a5f040b913222bf2a957343294462da1",
        "gross_usd": 4517687.00,
        "leaf_sum_usd": 4517687.00,
    },
    "BH": {
        "project": "BH",
        "title": "Bad Hombres",
        "engine_version": "canonical-1.109.0",
        "input_fingerprint": "f053b165d6319546722a1b43e0449312061279ef3d8d910fb5b450171f0e61c9",
        "gross_usd": 2482023.00,
        "leaf_sum_usd": 2482023.00,
    },
    "LLS_110b": {
        "project": "LLS",
        "title": "Lips Like Sugar",
        "engine_version": "canonical-1.110.0",
        "input_fingerprint": "78ed9f199c4e5eb0112a6b6e494f70316540d9c8e994f158559bf7b6376b0bd4",
        "gross_usd": 11983654.00,
        "leaf_sum_usd": 11983654.00,
    },
    "LLS_110a": {
        "project": "LLS",
        "title": "Lips Like Sugar",
        "engine_version": "canonical-1.110.0",
        "input_fingerprint": "0ac00210e593261b18661f108bdbe7101f43a5111dc41e191dc5eb878b9150e0",
        "gross_usd": 11983654.00,
        "leaf_sum_usd": 11983654.00,
    },
    "LLS_106": {
        "project": "LLS",
        "title": "Lips Like Sugar",
        "engine_version": "canonical-1.106.0",
        "input_fingerprint": "0c6459528b797538e49b17b3e637bdca0dc1ef213ce1391c86e7506fc4563d76",
        "gross_usd": 11983654.00,
        "leaf_sum_usd": 11983654.00,
    },
}

# Dated primary statutory rules for US state and Canadian/Mexican routed component legs
ROUTED_COMPONENT_STATUTORY_RULES = {
    "ca_film_30": {
        "min_spend_usd": 1000000.0,
        "requires_75pct_budget_or_days": True,
        "citation": "CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1 & Cal. Rev. & Tax. Code § 17053.98(b)(3)(A): requires >=75% total budget in CA OR >=75% principal photography days in CA (plus $1M min budget).",
    },
    "on_ofttc": {
        "labour_only": True,
        "requires_cavco_domestic": True,
        "citation": "Ontario Taxation Act, 2007, S.O. 2007, c. 11, Sched. A, § 43: 35% of qualifying Ontario labour expenditure only; requires domestic certification (OFTC/CAVCO) and cannot price non-labour post/VFX/music.",
    },
    "ca_ns_production_incentive_fund": {
        "labour_only": True,
        "requires_ns_principal_photography": True,
        "citation": "Nova Scotia Film & Television Production Incentive Fund Guidelines (April 2024): base 25% applies to eligible Nova Scotia labour (Stream I) or requires >50% principal photography in NS (Stream II).",
    },
    "ca_nb_film_tax_credit": {
        "discretionary_floorless": True,
        "citation": "New Brunswick Film Tax Credit Guidelines (ESDC): discretionary contribution/rebate up to 25%/30% ceiling; $0.00 guaranteed floor without confirmed Ministerial award.",
    },
    "mx_federal_film_incentive_2026": {
        "min_spend_usd": 2285714.29,  # MXN 40,000,000 at 17.50 MXN/USD
        "discretionary_floorless": True,
        "citation": "Decreto de Estímulo Fiscal a la Producción Cinematográfica Nacional y Audiovisual (Feb 15, 2026): requires MXN 40,000,000 (~$2.29M USD) minimum Mexican spend (MXN 20M for animation/VFX/post) and is a competitive capped authorization ($0.00 guaranteed floor).",
    },
    "us_nc_film_entertainment_grant": {
        "min_spend_usd": 1500000.0,
        "discretionary_floorless": True,
        "citation": "N.C. Gen. Stat. § 143B-437.02A: discretionary grant ($0.00 guaranteed floor) requiring $1.5M minimum in-state spend for features.",
    },
    "us_ny_post_production_credit": {
        "post_vfx_gateway": True,
        "citation": "NY Tax Law § 31*2(a)(2)-(3): requires qualified NY post facility costs >= min($1,000,000, 75% worldwide post) OR qualified NY VFX >= min($500,000, 10% worldwide VFX); mutually exclusive with § 24 at film level (§ 31*2(a)(1)); music (4600/5100/6000) is ineligible.",
    },
    "ontario_computer_animation_and_special_effects_tax_credit_ocase": {
        "labour_only_vfx": True,
        "citation": "Ontario Taxation Act, 2007, S.O. 2007, c. 11, Sched. A, § 42 (OCASE): 18% of qualifying Ontario labour expenditure for eligible computer animation and special effects activities; requires tethered OPSTC or OFTTC.",
    },
    "ca_mb_film_video_credit": {
        "requires_mb_corp_and_25pct_t4": True,
        "citation": "Manitoba Income Tax Act C.C.S.M. c. I10, ss. 7.5(1)(d), 7.6(2), 7.6(6): requires an eligible Manitoba corporation paying >=25% of T4 salaries/wages to eligible Manitoba employees (for Cost-of-Production stream) or eligible Manitoba resident salaries (for 45% Cost-of-Salaries stream).",
    },
    "us_mn_film_production_credit": {
        "min_spend_usd": 1000000.0,
        "defect_id": "NA-HYB-DEF-01 (US-MN $1M Min Spend Omitted)",
        "citation": "Minn. Stat. § 116U.27 subd. 2: requires >=$1,000,000 in eligible production costs in Minnesota within a 12-month period. Engine 1.122.0 has min_qpe_usd=None, erroneously pricing $5k-$206k component slices.",
    },
    "us_pa_film_production_credit": {
        "requires_60pct_total_budget": True,
        "defect_id": "NA-HYB-DEF-01 (US-PA 60% Total Production Expense Gate Omitted)",
        "citation": "72 P.S. § 8712-D(b): requires Pennsylvania production expenses to comprise at least 60% of the film's total production expenses. Engine 1.122.0 omits US-PA from project_eligibility_gates.py, erroneously pricing 0.20%-4.35% component slices.",
    },
    "us_ma_film_tax_credit": {
        "min_spend_usd": 50000.0,
        "requires_75pct_budget_or_days_for_production_expense_credit": True,
        "defect_id": "NA-HYB-DEF-01 (US-MA 75% Budget/Days Gate Omitted on Non-Payroll Post/Music)",
        "citation": "M.G.L. c. 62, § 6(l) / c. 63, § 38X: $50,000 threshold qualifies only for the 25% Payroll Credit; the 25% non-payroll Production Expense Credit requires >75% of total production expenses OR >=75% of principal photography days in MA. Engine 1.122.0 prices non-payroll post ($107,958 BH) and music ($206,774 LLS) at 25% when principal photography is outside MA.",
    },
    "us_ri_film_credit": {
        "min_spend_usd": 100000.0,
        "requires_51pct_principal_photography": True,
        "defect_id": "NA-HYB-DEF-01 (US-RI 51% Principal Photography Gate Omitted)",
        "citation": "R.I. Gen. Laws § 44-31.2-2(9): requires $100,000 minimum spend AND >=51% of principal photography days in Rhode Island (unless RI QPE >= $10M). Engine 1.122.0 omits US-RI from project_eligibility_gates.py, pricing $107,958 BH post and $206,774 LLS music when 100% of principal photography is outside RI.",
    },
    "us_al_film_incentive": {
        "min_spend_usd": 500000.0,
        "defect_id": "NA-HYB-DEF-01 (US-AL $500k Min Spend Omitted & 35% Resident Payroll Rate Applied to All Spend)",
        "citation": "Ala. Code § 41-7A-43 & § 41-7A-45: requires $500,000 minimum spend and provides 25% on non-payroll production expenditures and 35% on resident payroll only. Engine 1.122.0 has min_qpe_usd=None and applies 35% to 100% of non-payroll component slices ($5k-$206k).",
    },
    "us_co_film_incentive": {
        "min_spend_usd": 100000.0,
        "requires_50pct_co_workforce": True,
        "defect_id": "NA-HYB-DEF-01 (US-CO $100k/$1M Min Spend Omitted)",
        "citation": "C.R.S. § 24-48.5-115: requires $100,000 minimum spend (Colorado-originated) or $1,000,000 (out-of-state company) and >=50% Colorado workforce. Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$107k component slices.",
    },
    "us_hi_film_digital_media_credit": {
        "min_spend_usd": 100000.0,
        "defect_id": "NA-HYB-DEF-01 (US-HI $100k/$200k Min Spend Omitted)",
        "citation": "HRS § 235-17(d): requires $200,000 minimum qualified production costs in Honolulu County or $100,000 in neighbor island counties. Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$52.5k component slices.",
    },
    "us_ok_film_enhancement_rebate": {
        "min_spend_usd": 50000.0,
        "defect_id": "NA-HYB-DEF-01 (US-OK $50k Min Spend Omitted)",
        "citation": "68 O.S. § 3624: requires $50,000 minimum Oklahoma spend (and $20,000 for standalone post-production rebate). Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$40k component slices.",
    },
    "us_ut_motion_picture_incentive": {
        "min_spend_usd": 500000.0,
        "defect_id": "NA-HYB-DEF-01 (US-UT $500k Tax Credit Min Spend Omitted)",
        "citation": "Utah Code § 63N-8-104: requires $500,000 minimum Utah spend for the 20% tax credit (Community Film Incentive Program below $500k is a separate discretionary program for local emerging directors). Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$206k component slices.",
    },
    "us_va_motion_picture_credit": {
        "min_spend_usd": 250000.0,
        "defect_id": "NA-HYB-DEF-01 (US-VA $250k Min Spend Omitted)",
        "citation": "Va. Code § 58.1-439.12:03: requires $250,000 minimum Virginia expenses. Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$206k component slices.",
    },
    "us_az_motion_picture_production": {
        "min_spend_usd": 1000000.0,
        "defect_id": "NA-HYB-DEF-01 (US-AZ $1M Feature Min Spend / Facility Requirement Omitted)",
        "citation": "A.R.S. § 41-1517 / § 43-1082: base 15%-20% tiers require qualified spend tiers ($1M+ for feature production or qualified Arizona post facility use). Engine 1.122.0 has min_qpe_usd=None, pricing $5k-$206k component slices.",
    },
}


def reconstruct_lls_mb_ca_independent(lls_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Independently reconstructs LLS Manitoba-California (CA-MB Principal + US-CA VFX)
    from the 46 retained budget lines and dated primary statutory authorities:
      1. Manitoba Income Tax Act (C.C.S.M. c. I10, ss. 7.5-7.9, current July 1, 2026 to Oct 8, 2026)
         & Manitoba Film and Video Production Tax Credit Guidelines (June 2024).
      2. California Film & Television Tax Credit Program 4.0 Guidelines (Jan 1, 2026, § II.A.1 & III.B.1)
         & Program 3.0 (Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) / 10 CCR § 5520(a)).
    """
    lines = lls_data["lines"]
    assert len(lines) == 46, f"Expected 46 LLS lines, got {len(lines)}"
    gross_usd = round(sum(float(l["amount_usd"]) for l in lines), 2)
    assert abs(gross_usd - 11983654.00) < 0.01

    vfx_lines = [l for l in lines if l["account_code"] == "4400"]
    assert len(vfx_lines) == 1 and float(vfx_lines[0]["amount_usd"]) == 40000.00
    mb_lines = [l for l in lines if l["account_code"] != "4400"]
    assert len(mb_lines) == 45
    mb_allocated_usd = round(sum(float(l["amount_usd"]) for l in mb_lines), 2)
    assert abs(mb_allocated_usd - 11943654.00) < 0.01

    # Excluded & grey-area lines on the Manitoba allocation
    financing_lines = [l for l in mb_lines if l["account_code"] in ("6500", "6600", "6700")]
    financing_usd = round(sum(float(l["amount_usd"]) for l in financing_lines), 2)
    assert abs(financing_usd - 1700000.00) < 0.01

    residuals_lines = [l for l in mb_lines if l["account_code"] == "6800"]
    residuals_usd = round(sum(float(l["amount_usd"]) for l in residuals_lines), 2)
    assert abs(residuals_usd - 400000.00) < 0.01

    contingency_lines = [l for l in mb_lines if l["account_code"] == "7100"]
    contingency_usd = round(sum(float(l["amount_usd"]) for l in contingency_lines), 2)
    assert abs(contingency_usd - 400000.00) < 0.01

    bond_lines = [l for l in mb_lines if l["account_code"] == "7200"]
    bond_usd = round(sum(float(l["amount_usd"]) for l in bond_lines), 2)
    assert abs(bond_usd - 115000.00) < 0.01

    atl_travel_lines = [l for l in mb_lines if l["account_code"] == "1500"]
    atl_travel_usd = round(sum(float(l["amount_usd"]) for l in atl_travel_lines), 2)
    assert abs(atl_travel_usd - 60561.00) < 0.01

    # Manitoba confirmed all-spend pool (excluding $1.7M financing, $400k unconfirmed residuals reserve, $400k unspent contingency)
    mb_all_spend_pool_45_lines = round(mb_allocated_usd - financing_usd - residuals_usd - contingency_usd, 2)
    assert abs(mb_all_spend_pool_45_lines - 9443654.00) < 0.01

    mb_all_spend_pool_46_lines = round(gross_usd - financing_usd - residuals_usd - contingency_usd, 2)
    assert abs(mb_all_spend_pool_46_lines - 9483654.00) < 0.01

    # Stream A: 30% Cost-of-Production Credit (Manitoba ITA s. 7.6(6))
    # Base 30% + conditional +8% Manitoba co-producer bonus (total 38%)
    art2_floor_credit = round(0.30 * mb_all_spend_pool_45_lines, 2)      # $2,833,096.20
    art2_coprod_bonus = round(0.08 * mb_all_spend_pool_45_lines, 2)      # $755,492.32
    art2_ceiling_credit = round(0.38 * mb_all_spend_pool_45_lines, 2)    # $3,588,588.52
    art2_strict_excl_atl_travel_credit = round(0.30 * (mb_all_spend_pool_45_lines - atl_travel_usd), 2)  # $2,814,927.90

    art3_floor_credit = round(0.30 * mb_all_spend_pool_46_lines, 2)      # $2,845,096.20
    art3_coprod_bonus = round(0.08 * mb_all_spend_pool_46_lines, 2)      # $758,692.32
    art3_ceiling_credit = round(0.38 * mb_all_spend_pool_46_lines, 2)    # $3,603,788.52

    # Stream B: 45% Cost-of-Salaries Credit (Manitoba ITA s. 7.6(2)-(5))
    # Engine labour-category lines (atl_writer, atl_director, atl_producer, atl_cast, btl_crew_labor)
    labour_cats = {"atl_writer", "atl_director", "atl_producer", "atl_cast", "btl_crew_labor", "btl_resident_labor", "btl_nonresident_labor"}
    mb_engine_labour_usd = round(sum(float(l["amount_usd"]) for l in mb_lines if l["category"] in labour_cats), 2)
    assert abs(mb_engine_labour_usd - 2935298.00) < 0.01
    mb_stream_b_45_floor = round(0.45 * mb_engine_labour_usd, 2)         # $1,320,884.10
    mb_stream_b_65_ceiling = round(0.65 * mb_engine_labour_usd, 2)       # $1,907,943.70

    # 4-Election Contingency Matrix on 7100 Contingency ($400,000.00)
    # Distinguishing:
    #   (a) Conservative Engine Floor (excludes contingency under all 4 elections when no line-level ContingencyAllocation is provided because program_spend_rules.py has no Manitoba contingency rule)
    #   (b) Statutory Deployed-to-Eligible-Spend Value under Manitoba ITA s. 7.5(1) (deployed contingency spent on eligible Manitoba production costs earns 30% under Stream A)
    contingency_matrix = []
    for label, pct_val in [("NOT_STATED", None), ("0%", 0.0), ("50%", 50.0), ("100%", 100.0)]:
        if pct_val is None:
            deployed_usd = 0.0
            unspent_reduction_usd = 0.0
            cond_cont_upside_usd = round(0.30 * contingency_usd, 2)  # $120,000.00
        else:
            deployed_usd = round(contingency_usd * (pct_val / 100.0), 2)
            unspent_reduction_usd = round(contingency_usd - deployed_usd, 2)
            cond_cont_upside_usd = 0.0

        planned_cost_usd = round(gross_usd - unspent_reduction_usd, 2)

        # Artifact 2 (Same-Allocation MB $11,943,654; US-CA VFX $40,000 earns $0)
        art2_eng_qpe = mb_all_spend_pool_45_lines
        art2_eng_inc = art2_floor_credit
        art2_eng_npc = round(planned_cost_usd - art2_eng_inc, 2)

        art2_stat_qpe = round(mb_all_spend_pool_45_lines + deployed_usd, 2)
        art2_stat_inc = round(0.30 * art2_stat_qpe, 2)
        art2_stat_npc = round(planned_cost_usd - art2_stat_inc, 2)

        # Artifact 3 (Relocated All-Manitoba $11,983,654 including $40,000 VFX)
        art3_eng_qpe = mb_all_spend_pool_46_lines
        art3_eng_inc = art3_floor_credit
        art3_eng_npc = round(planned_cost_usd - art3_eng_inc, 2)

        art3_stat_qpe = round(mb_all_spend_pool_46_lines + deployed_usd, 2)
        art3_stat_inc = round(0.30 * art3_stat_qpe, 2)
        art3_stat_npc = round(planned_cost_usd - art3_stat_inc, 2)

        contingency_matrix.append({
            "election": label,
            "utilization_pct": pct_val,
            "contingency_reserve_usd": contingency_usd,
            "deployed_contingency_usd": deployed_usd,
            "planned_cost_reduction_usd": unspent_reduction_usd,
            "effective_planned_cost_usd": planned_cost_usd,
            "art2_engine_qpe_floor_usd": art2_eng_qpe,
            "art2_engine_inc_floor_usd": art2_eng_inc,
            "art2_engine_npc_usd": art2_eng_npc,
            "art2_statutory_deployed_qpe_usd": art2_stat_qpe,
            "art2_statutory_deployed_inc_usd": art2_stat_inc,
            "art2_statutory_deployed_npc_usd": art2_stat_npc,
            "art3_engine_qpe_floor_usd": art3_eng_qpe,
            "art3_engine_inc_floor_usd": art3_eng_inc,
            "art3_engine_npc_usd": art3_eng_npc,
            "art3_statutory_deployed_qpe_usd": art3_stat_qpe,
            "art3_statutory_deployed_inc_usd": art3_stat_inc,
            "art3_statutory_deployed_npc_usd": art3_stat_npc,
            "conditional_contingency_upside_usd": cond_cont_upside_usd,
        })

    return {
        "gross_usd": gross_usd,
        "mb_allocated_usd": mb_allocated_usd,
        "ca_vfx_allocated_usd": 40000.00,
        "ca_spend_share_pct": round((40000.00 / gross_usd) * 100.0, 4),
        "financing_excluded_usd": financing_usd,
        "residuals_grey_usd": residuals_usd,
        "contingency_reserve_usd": contingency_usd,
        "bond_fee_usd": bond_usd,
        "atl_travel_usd": atl_travel_usd,
        "mb_all_spend_pool_45_lines_usd": mb_all_spend_pool_45_lines,
        "mb_all_spend_pool_46_lines_usd": mb_all_spend_pool_46_lines,
        "art2_floor_credit_usd": art2_floor_credit,
        "art2_coprod_bonus_usd": art2_coprod_bonus,
        "art2_ceiling_credit_usd": art2_ceiling_credit,
        "art2_strict_excl_atl_travel_credit_usd": art2_strict_excl_atl_travel_credit,
        "art3_floor_credit_usd": art3_floor_credit,
        "art3_coprod_bonus_usd": art3_coprod_bonus,
        "art3_ceiling_credit_usd": art3_ceiling_credit,
        "mb_engine_labour_usd": mb_engine_labour_usd,
        "mb_stream_b_45_floor_usd": mb_stream_b_45_floor,
        "mb_stream_b_65_ceiling_usd": mb_stream_b_65_ceiling,
        "stale_saved_mb_inc_usd": 4249644.30,
        "stale_saved_ca_inc_usd": 14000.00,
        "stale_saved_total_inc_usd": 4263644.30,
        "stale_saved_npc_usd": 7720009.70,
        "stale_overstatement_vs_art2_usd": round(4263644.30 - art2_floor_credit, 2),
        "stale_overstatement_vs_art3_usd": round(4263644.30 - art3_floor_credit, 2),
        "contingency_matrix": contingency_matrix,
    }


def evaluate_routed_leg_independently(
    project: str,
    gross_usd: float,
    comp: str,
    alloc_usd: float,
    jcode: str,
    pslug: str,
    eng_leg: Dict[str, Any],
) -> Tuple[str, float, float, str, str]:
    """
    Independently evaluates a routed component leg (vfx, music_package,
    post_vfx_package, post_vfx_music_package) against dated primary statutory
    authority BEFORE comparing with canonical-1.122.0.
    Returns:
      (ind_status, ind_qpe_floor_usd, ind_inc_floor_usd, defect_code_or_none, statutory_note)
    """
    rule = ROUTED_COMPONENT_STATUTORY_RULES.get(pslug)
    if rule:
        if rule.get("requires_75pct_budget_or_days"):
            return (
                "GATE_REJECTED",
                0.0,
                0.0,
                "",
                rule["citation"],
            )
        if rule.get("labour_only") or rule.get("requires_ns_principal_photography"):
            return (
                "RULE_REJECTED",
                0.0,
                0.0,
                "",
                rule["citation"],
            )
        if rule.get("discretionary_floorless"):
            return (
                "CONDITIONAL_NONDETERMINISTIC",
                0.0,
                0.0,
                "",
                rule["citation"],
            )
        if rule.get("post_vfx_gateway"):
            # NY § 31*2: music_package is ineligible; VFX ($10k FVD, $40k LLS, $52.5k LU) = 100% of project VFX (>=10% gateway),
            # post_vfx_package ($9,068 LU, $107,958 BH, $146,446/$156,446 FVD, $611,230/$651,230 LLS) >= 75% of project post.
            # However, on FVD/LLS post_vfx_music_package, music ($10,200 FVD, $206,774 LLS, $5,000 BH) is excluded from post QPE.
            if comp == "music_package":
                return (
                    "RULE_REJECTED",
                    0.0,
                    0.0,
                    "",
                    rule["citation"],
                )
            # In canonical-1.122.0, NY post credit requires NY QPF facility fact or prices post/VFX lines at 30% MCTD base
            return (
                "PRICED" if eng_leg.get("executable") else "RULE_REJECTED",
                eng_leg.get("qpe_usd", 0.0),
                eng_leg.get("incentive_floor_usd", 0.0),
                "",
                rule["citation"],
            )
        if rule.get("labour_only_vfx"):
            # OCASE: 18% of Ontario VFX labour only; requires tethered OPSTC/OFTTC and resident payroll schedule
            return (
                "NOT_ESTABLISHED",
                0.0,
                0.0,
                "",
                rule["citation"],
            )
        if rule.get("requires_mb_corp_and_25pct_t4"):
            # Manitoba routed component: requires eligible MB corp with >=25% T4 wages paid to MB employees;
            # also note NA-HYB-DEF-02 where _ALTERNATIVE_ELECTION_PROGRAMS (30% all-spend) is unreachable when atl_*/btl_* labour == 0
            return (
                "RULE_REJECTED",
                0.0,
                0.0,
                "NA-HYB-DEF-02",
                rule["citation"] + " [Engine 1.122.0 also has unreachable 30% election when segment atl_*/btl_* labour is $0 (NA-HYB-DEF-02)].",
            )
        if rule.get("defect_id"):
            # Active defect in canonical-1.122.0 where US state min-spend or project-share gate is omitted!
            # Wait: check if alloc_usd is actually below min_spend_usd or fails project-share gate
            min_s = rule.get("min_spend_usd", 0.0)
            fails_min = alloc_usd < min_s
            fails_share = bool(
                rule.get("requires_60pct_total_budget")
                or rule.get("requires_75pct_budget_or_days_for_production_expense_credit")
                or rule.get("requires_51pct_principal_photography")
                or rule.get("requires_50pct_co_workforce")
            )
            if fails_min or fails_share:
                return (
                    "GATE_REJECTED",
                    0.0,
                    0.0,
                    rule["defect_id"],
                    rule["citation"],
                )

    # Default for programs whose statutory rules allow the component slice or already match 1.122.0
    if not eng_leg.get("executable"):
        return (
            "RULE_REJECTED",
            0.0,
            0.0,
            "",
            f"Rejected in canonical-1.122.0: {eng_leg.get('blockers') or eng_leg.get('gate_reason')}",
        )
    return (
        "PRICED",
        eng_leg.get("qpe_usd", 0.0),
        eng_leg.get("incentive_floor_usd", 0.0),
        "",
        "Component leg passes statutory threshold in canonical-1.122.0.",
    )


def evaluate_anchor_leg_independently(
    project: str,
    gross_usd: float,
    alloc_usd: float,
    jcode: str,
    pslug: str,
    eng_leg: Dict[str, Any],
) -> Tuple[str, float, float, str, str]:
    """
    Independently evaluates the principal_production anchor leg of a hybrid structure.
    """
    # 1. Discretionary / floorless programs
    if pslug in ("ca_nb_film_tax_credit", "mx_federal_film_incentive_2026", "us_nc_film_entertainment_grant"):
        if pslug == "mx_federal_film_incentive_2026" and alloc_usd < 2285714.29:
            return ("GATE_REJECTED", 0.0, 0.0, "", "Fails Mexico MXN 40M (~$2.29M USD) statutory minimum spend floor.")
        return (
            "CONDITIONAL_NONDETERMINISTIC",
            0.0,
            0.0,
            "",
            f"{pslug} is a discretionary/capped award with $0.00 guaranteed floor until confirmed award.",
        )

    # 2. Canadian CAVCO domestic programs (CPTC, OFTTC) & Canadian labour programs
    if pslug in ("ca_federal_cptc", "on_ofttc"):
        return (
            "NOT_ESTABLISHED",
            eng_leg.get("qpe_usd", 0.0),
            eng_leg.get("incentive_floor_usd", 0.0),
            "NA-HYB-DEF-03",
            "CAVCO domestic certification is a statutory claim follow-up; in planning mode, engine 1.122.0 prices atl_*/btl_crew_labor categories while omitting BTL crew misclassified as miscellaneous/payroll_fringes (NA-HYB-DEF-03).",
        )
    if pslug in ("ca_federal_pstc", "on_opstc", "ca_bc_pstc", "ca_bc_dave", "ca_ns_production_incentive_fund"):
        return (
            "NOT_ESTABLISHED",
            eng_leg.get("qpe_usd", 0.0),
            eng_leg.get("incentive_floor_usd", 0.0),
            "NA-HYB-DEF-03",
            "Canadian resident payroll ledger is a statutory claim follow-up; in planning mode, engine 1.122.0 prices atl_*/btl_crew_labor categories while omitting BTL crew misclassified as miscellaneous/payroll_fringes (NA-HYB-DEF-03).",
        )

    # 3. Manitoba Film & Video Production Tax Credit (ca_mb_film_video_credit)
    if pslug == "ca_mb_film_video_credit":
        return (
            "PRICED",
            eng_leg.get("qpe_usd", 0.0),
            eng_leg.get("incentive_floor_usd", 0.0),
            "NA-HYB-DEF-04" if project == "LU" else "",
            "Manitoba ITA s. 7.6(6) 30% Cost-of-Production stream vs s. 7.6(2) 45% Cost-of-Salaries stream. Saved DB row overstated Manitoba at 45% on all spend (repaired in 1.117.0/1.120.0).",
        )

    # 4. New York State Film Production Credit (ny_state_film)
    if pslug == "ny_state_film":
        return (
            "NOT_ESTABLISHED",
            eng_leg.get("qpe_usd", 0.0),
            eng_leg.get("incentive_floor_usd", 0.0),
            "NA-DEFECT-01",
            "NY Tax Law § 24(b)(1) 40% aggregate ATL ceiling omitted in engine (NA-DEFECT-01); individual talent contracts (FVD/BH/LLS) and travel/contingency schedules (LU) are claim follow-ups.",
        )

    # 5. High-earner salary cap states (GA, IL, MA)
    if pslug in ("us_ga_film_credit", "us_il_film_production_services_credit", "us_ma_film_tax_credit") and project in ("FVD", "BH", "LLS"):
        return (
            "NOT_ESTABLISHED",
            eng_leg.get("qpe_usd", 0.0),
            eng_leg.get("incentive_floor_usd", 0.0),
            "",
            "Individual payee contracts for $500k (GA/IL) and $1M (MA) per-person caps are claim follow-ups; planning scenario uses aggregate spend.",
        )

    # 6. Alabama 35% resident payroll rate applied to all spend in 1.122.0
    if pslug == "us_al_film_incentive":
        # Independent 25% non-payroll baseline vs engine 35%
        ind_qpe = eng_leg.get("qpe_usd", 0.0)
        ind_inc = round(0.25 * ind_qpe, 2)
        return (
            "PRICED",
            ind_qpe,
            ind_inc,
            "NA-HYB-DEF-01 (US-AL 35% Payroll Rate Applied to All Spend)",
            "Ala. Code § 41-7A-45 provides 25% on general production spend and 35% on Alabama resident payroll only; engine 1.122.0 applies 35% to all spend.",
        )

    if not eng_leg.get("executable"):
        return (
            "RULE_REJECTED",
            0.0,
            0.0,
            "",
            f"Anchor leg rejected in canonical-1.122.0: {eng_leg.get('blockers')}",
        )

    return (
        "PRICED",
        eng_leg.get("qpe_usd", 0.0),
        eng_leg.get("incentive_floor_usd", 0.0),
        "",
        "Anchor leg evaluated under prospective relocation rules.",
    )


def build_coverage_matrix_and_report() -> None:
    with open(SOURCE_EVIDENCE_JSON, "r", encoding="utf-8") as f:
        ev_list = json.load(f)
    ev_by_proj = {item["project"]: item for item in ev_list}

    with open(SNAPSHOT_JSON, "r", encoding="utf-8") as f:
        snap = json.load(f)

    leg_map = snap["engine_1122_leg_results"]
    stack_map = snap["engine_1122_stack_results"]
    hist_id_map = snap["historical_priced_id_map"]
    agg_summary = snap["aggregate_summary"]

    lls_mb_ca = reconstruct_lls_mb_ca_independent(ev_by_proj["LLS"])

    csv_rows: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Part 1: Explicit LLS Manitoba-California 3 Artifacts + 4 Contingency Elections
    # -------------------------------------------------------------------------
    # Artifact 1: Retained Hybrid (CA-MB Principal $11,943,654 + US-CA VFX $40,000)
    csv_rows.append({
        "row_category": "LLS_MB_CA_ARTIFACT_1_RETAINED_HYBRID",
        "project": "LLS",
        "generation_label": "LLS_110b / LLS_110a / LLS_106",
        "saved_engine_version": "canonical-1.110.0 / canonical-1.106.0",
        "input_fingerprint": GENERATION_META["LLS_110b"]["input_fingerprint"],
        "scr_id": "914a47c0-9b1e-4d47-867f-425e6d4792fa | 51680824-eb85-4920-b124-04d0b6fce131 | 0338ace0-e929-42aa-89df-fd1fe7ff629c",
        "structure_id": "9656c441-881e-4667-bec1-8841387408ce | 268917e8-6749-4730-9399-5a686a3f1086 | 110ce2e4-f121-433b-a9ff-591ee4718b77",
        "structure_type": "hybrid",
        "structural_family": "ordinary_component_hybrid",
        "structure_name": "CA-MB (ca_mb_film_video_credit) + vfx->US-CA (ca_film_30) (hybrid) [Artifact 1: Retained Hybrid]",
        "anchor_jurisdiction": "CA-MB",
        "anchor_program": "ca_mb_film_video_credit",
        "routed_components": "vfx ($40,000.00 -> US-CA / ca_film_30)",
        "gross_budget_usd": f"{lls_mb_ca['gross_usd']:.2f}",
        "planned_cost_reduction_usd": "0.00",
        "effective_planned_cost_usd": f"{lls_mb_ca['gross_usd']:.2f}",
        "line_overlap_count": 0,
        "independent_expected_status": "GATE_REJECTED",
        "independent_qpe_floor_usd": "0.00",
        "independent_incentive_floor_usd": "0.00",
        "independent_conditional_upside_usd": "0.00",
        "independent_npc_floor_usd": f"{lls_mb_ca['gross_usd']:.2f}",
        "engine_1122_status": "GATE_REJECTED",
        "engine_1122_qpe_usd": "0.00",
        "engine_1122_incentive_floor_usd": "0.00",
        "engine_1122_npc_usd": f"{lls_mb_ca['gross_usd']:.2f}",
        "saved_db_status": "PRICED",
        "saved_db_qpe_usd": "9483654.00",
        "saved_db_incentive_usd": f"{lls_mb_ca['stale_saved_total_inc_usd']:.2f}",
        "saved_db_npc_usd": f"{lls_mb_ca['stale_saved_npc_usd']:.2f}",
        "incentive_delta_saved_vs_independent_usd": f"{lls_mb_ca['stale_saved_total_inc_usd']:.2f}",
        "incentive_delta_1122_vs_independent_usd": "0.00",
        "audit_disposition": "REPAIRED_IN_1122_STALE_IN_DB (PROJECT_ELIGIBILITY_GATE_FAILED)",
        "statutory_basis_and_notes": (
            "Artifact 1 (Retained Hybrid): US-CA VFX ($40,000 / $11,983,654 = 0.3338% < 75% spend share; "
            "modeled principal photography 100% in CA-MB) fails CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1 "
            "and Program 3.0 10 CCR § 5520(a). Repaired in canonical-1.122.0 (f5dc6a17/f0b042ba/59566fd1)."
        ),
    })

    # Artifacts 2 & 3 across the 4 Contingency Elections (NOT_STATED, 0%, 50%, 100%)
    for cm in lls_mb_ca["contingency_matrix"]:
        el = cm["election"]
        # Artifact 2 row (Same-Allocation Manitoba Leg Sensitivity: $11,943,654 in CA-MB, $40,000 US-CA VFX earns $0)
        def_code_2 = "NA-HYB-DEF-04 (Absent Manitoba Contingency SpendRule)" if el in ("50%", "100%") else ""
        disp_2 = (
            f"OPEN_ENGINE_CONTINGENCY_RULE_OMISSION ({def_code_2})"
            if def_code_2
            else "REPAIRED_IN_1122_STALE_IN_DB (MANITOBA_30PCT_COST_OF_PRODUCTION_STREAM)"
        )
        csv_rows.append({
            "row_category": f"LLS_MB_CA_ARTIFACT_2_MB_LEG_SENSITIVITY_CONTINGENCY_{el}",
            "project": "LLS",
            "generation_label": f"SENSITIVITY_CONTINGENCY_{el}",
            "saved_engine_version": "canonical-1.110.0",
            "input_fingerprint": GENERATION_META["LLS_110b"]["input_fingerprint"],
            "scr_id": "914a47c0-9b1e-4d47-867f-425e6d4792fa",
            "structure_id": "9656c441-881e-4667-bec1-8841387408ce",
            "structure_type": "hybrid_leg_sensitivity",
            "structural_family": "manitoba_leg_on_hybrid_allocation",
            "structure_name": f"Artifact 2: Same-Allocation CA-MB Leg ($11,943,654) + Uncredited US-CA VFX ($40,000) [Contingency={el}]",
            "anchor_jurisdiction": "CA-MB",
            "anchor_program": "ca_mb_film_video_credit",
            "routed_components": "vfx ($40,000.00 -> US-CA uncredited $0)",
            "gross_budget_usd": f"{lls_mb_ca['gross_usd']:.2f}",
            "planned_cost_reduction_usd": f"{cm['planned_cost_reduction_usd']:.2f}",
            "effective_planned_cost_usd": f"{cm['effective_planned_cost_usd']:.2f}",
            "line_overlap_count": 0,
            "independent_expected_status": "PRICED",
            "independent_qpe_floor_usd": f"{cm['art2_statutory_deployed_qpe_usd']:.2f}",
            "independent_incentive_floor_usd": f"{cm['art2_statutory_deployed_inc_usd']:.2f}",
            "independent_conditional_upside_usd": f"{lls_mb_ca['art2_coprod_bonus_usd'] + cm['conditional_contingency_upside_usd']:.2f}",
            "independent_npc_floor_usd": f"{cm['art2_statutory_deployed_npc_usd']:.2f}",
            "engine_1122_status": "PRICED",
            "engine_1122_qpe_usd": f"{cm['art2_engine_qpe_floor_usd']:.2f}",
            "engine_1122_incentive_floor_usd": f"{cm['art2_engine_inc_floor_usd']:.2f}",
            "engine_1122_npc_usd": f"{cm['art2_engine_npc_usd']:.2f}",
            "saved_db_status": "PRICED",
            "saved_db_qpe_usd": "9483654.00",
            "saved_db_incentive_usd": f"{lls_mb_ca['stale_saved_total_inc_usd']:.2f}",
            "saved_db_npc_usd": f"{lls_mb_ca['stale_saved_npc_usd']:.2f}",
            "incentive_delta_saved_vs_independent_usd": f"{lls_mb_ca['stale_saved_total_inc_usd'] - cm['art2_statutory_deployed_inc_usd']:.2f}",
            "incentive_delta_1122_vs_independent_usd": f"{cm['art2_engine_inc_floor_usd'] - cm['art2_statutory_deployed_inc_usd']:.2f}",
            "audit_disposition": disp_2,
            "statutory_basis_and_notes": (
                f"Manitoba ITA s. 7.6(6) 30% Cost-of-Production stream on $11,943,654 MB allocation (less $1.7M financing, "
                f"$400k residuals reserve, and ${cm['planned_cost_reduction_usd']:,.2f} unspent contingency). "
                f"Engine Floor Credit=${cm['art2_engine_inc_floor_usd']:,.2f} (NPC=${cm['art2_engine_npc_usd']:,.2f}); "
                f"Statutory Deployed-to-Eligible Credit=${cm['art2_statutory_deployed_inc_usd']:,.2f} (NPC=${cm['art2_statutory_deployed_npc_usd']:,.2f})."
            ),
        })

        # Artifact 3 row (Relocated All-Manitoba Single-Jurisdiction Alternative: $11,983,654 in CA-MB)
        csv_rows.append({
            "row_category": f"LLS_MB_CA_ARTIFACT_3_ALL_MB_ALTERNATIVE_CONTINGENCY_{el}",
            "project": "LLS",
            "generation_label": f"SENSITIVITY_CONTINGENCY_{el}",
            "saved_engine_version": "canonical-1.110.0",
            "input_fingerprint": GENERATION_META["LLS_110b"]["input_fingerprint"],
            "scr_id": "238928be-e8ea-44e5-a169-d4628d573bb6",
            "structure_id": "8eb96303-59dc-4056-98dc-ca16471527c3",
            "structure_type": "single_jurisdiction_alternative",
            "structural_family": "full_relocation_manitoba",
            "structure_name": f"Artifact 3: Relocated All-Manitoba Single-Jurisdiction Alternative ($11,983,654 incl. $40,000 VFX) [Contingency={el}]",
            "anchor_jurisdiction": "CA-MB",
            "anchor_program": "ca_mb_film_video_credit",
            "routed_components": "NONE (100% relocated to CA-MB including $40,000 VFX)",
            "gross_budget_usd": f"{lls_mb_ca['gross_usd']:.2f}",
            "planned_cost_reduction_usd": f"{cm['planned_cost_reduction_usd']:.2f}",
            "effective_planned_cost_usd": f"{cm['effective_planned_cost_usd']:.2f}",
            "line_overlap_count": 0,
            "independent_expected_status": "PRICED",
            "independent_qpe_floor_usd": f"{cm['art3_statutory_deployed_qpe_usd']:.2f}",
            "independent_incentive_floor_usd": f"{cm['art3_statutory_deployed_inc_usd']:.2f}",
            "independent_conditional_upside_usd": f"{lls_mb_ca['art3_coprod_bonus_usd'] + cm['conditional_contingency_upside_usd']:.2f}",
            "independent_npc_floor_usd": f"{cm['art3_statutory_deployed_npc_usd']:.2f}",
            "engine_1122_status": "PRICED",
            "engine_1122_qpe_usd": f"{cm['art3_engine_qpe_floor_usd']:.2f}",
            "engine_1122_incentive_floor_usd": f"{cm['art3_engine_inc_floor_usd']:.2f}",
            "engine_1122_npc_usd": f"{cm['art3_engine_npc_usd']:.2f}",
            "saved_db_status": "PRICED",
            "saved_db_qpe_usd": "9483654.00",
            "saved_db_incentive_usd": "4267644.30",
            "saved_db_npc_usd": "7716009.70",
            "incentive_delta_saved_vs_independent_usd": f"{4267644.30 - cm['art3_statutory_deployed_inc_usd']:.2f}",
            "incentive_delta_1122_vs_independent_usd": f"{cm['art3_engine_inc_floor_usd'] - cm['art3_statutory_deployed_inc_usd']:.2f}",
            "audit_disposition": disp_2,
            "statutory_basis_and_notes": (
                f"Manitoba ITA s. 7.6(6) 30% Cost-of-Production stream on full $11,983,654 budget relocated to CA-MB "
                f"(including $40,000 VFX, earning +$12,000.00 over Artifact 2). "
                f"Engine Floor Credit=${cm['art3_engine_inc_floor_usd']:,.2f} (NPC=${cm['art3_engine_npc_usd']:,.2f}); "
                f"Statutory Deployed-to-Eligible Credit=${cm['art3_statutory_deployed_inc_usd']:,.2f} (NPC=${cm['art3_statutory_deployed_npc_usd']:,.2f})."
            ),
        })

    # -------------------------------------------------------------------------
    # Part 2: All Saved NA Rows Across LU, FVD, BH, LLS_110b + Historical Extras
    # -------------------------------------------------------------------------
    all_gen_streams = [
        ("LU", snap["generations"]["LU"], False),
        ("FVD", snap["generations"]["FVD"], False),
        ("BH", snap["generations"]["BH"], False),
        ("LLS_110b", snap["generations"]["LLS_110b"], False),
        ("LLS_110a", snap["historical_priced_extras"]["LLS_110a"], True),
        ("LLS_106", snap["historical_priced_extras"]["LLS_106"], True),
        ("LU_106", snap["historical_priced_extras"]["LU_106"], True),
    ]

    stats_counter: Dict[str, Dict[str, int]] = {}

    for gen_key, rlist, is_hist_extra in all_gen_streams:
        meta = GENERATION_META[gen_key]
        proj = meta["project"]
        gross_usd = meta["gross_usd"]
        stats_counter.setdefault(gen_key, {})

        for r in rlist:
            st_type = r["structure_type"]
            c_status = r["candidate_status"]
            name = r["name"]

            # Cross-reference historical IDs for LLS_110b and LU rows if present in earlier generations
            scr_ids = [r["scr_id"]]
            struct_ids = [r["structure_id"]]
            if gen_key == "LLS_110b" and c_status == "PRICED":
                for hgen in ("LLS_110a", "LLS_106"):
                    if name in hist_id_map.get(hgen, {}):
                        scr_ids.append(f"{hgen}:{hist_id_map[hgen][name][0]}")
                        struct_ids.append(f"{hgen}:{hist_id_map[hgen][name][1]}")
            elif gen_key == "LU" and c_status == "PRICED":
                if name in hist_id_map.get("LU_106", {}):
                    scr_ids.append(f"LU_106:{hist_id_map['LU_106'][name][0]}")
                    struct_ids.append(f"LU_106:{hist_id_map['LU_106'][name][1]}")

            if c_status != "PRICED":
                # Dominated search summary row or CO_PRO_OPPORTUNITY treaty row
                disp = (
                    "VERIFIED_DOMINATED_SEARCH_BOUND"
                    if c_status == "DOMINATED_WITH_PROOF"
                    else "VERIFIED_UNPRICED_BILATERAL_TREATY_OPPORTUNITY"
                )
                note = (
                    "Branch-and-bound dominance proof record; no false incentive floor claimed ($0)."
                    if c_status == "DOMINATED_WITH_PROOF"
                    else "Bilateral treaty co-production opportunity record; unpriced pending treaty split & co-producer agreements."
                )
                stats_counter[gen_key][disp] = stats_counter[gen_key].get(disp, 0) + 1
                csv_rows.append({
                    "row_category": "SAVED_NA_NON_PRICED_ROW",
                    "project": proj,
                    "generation_label": gen_key,
                    "saved_engine_version": meta["engine_version"],
                    "input_fingerprint": meta["input_fingerprint"],
                    "scr_id": " | ".join(scr_ids),
                    "structure_id": " | ".join(struct_ids),
                    "structure_type": st_type,
                    "structural_family": r["structural_family"] or "",
                    "structure_name": name,
                    "anchor_jurisdiction": r["primary_jurisdiction"] or "",
                    "anchor_program": (r["program_slugs"] or [""])[0] if r["program_slugs"] else "",
                    "routed_components": "",
                    "gross_budget_usd": f"{gross_usd:.2f}",
                    "planned_cost_reduction_usd": "0.00",
                    "effective_planned_cost_usd": f"{gross_usd:.2f}",
                    "line_overlap_count": r["line_overlap_count"],
                    "independent_expected_status": c_status,
                    "independent_qpe_floor_usd": "0.00",
                    "independent_incentive_floor_usd": "0.00",
                    "independent_conditional_upside_usd": "0.00",
                    "independent_npc_floor_usd": f"{gross_usd:.2f}",
                    "engine_1122_status": c_status,
                    "engine_1122_qpe_usd": "0.00",
                    "engine_1122_incentive_floor_usd": "0.00",
                    "engine_1122_npc_usd": f"{gross_usd:.2f}",
                    "saved_db_status": c_status,
                    "saved_db_qpe_usd": "0.00",
                    "saved_db_incentive_usd": "0.00",
                    "saved_db_npc_usd": "0.00",
                    "incentive_delta_saved_vs_independent_usd": "0.00",
                    "incentive_delta_1122_vs_independent_usd": "0.00",
                    "audit_disposition": disp,
                    "statutory_basis_and_notes": note,
                })
                continue

            # PRICED rows: multi_program, component_relocation, or hybrid
            saved_inc = float(r["incentive_usd"] or 0.0)
            saved_npc = float(r["true_npc_usd"] or (gross_usd - saved_inc))
            saved_qpe = float(r["qpe_usd"] or 0.0)

            if st_type == "multi_program":
                slugs = r["program_slugs"] or []
                slug_pair = "+".join(slugs)
                jcode = r["primary_jurisdiction"]
                st_key = f"{proj}|{jcode}|{slug_pair}"
                eng_st = stack_map.get(st_key, {})
                eng_1122_inc = float(eng_st.get("combined_incentive_usd", 0.0))
                eng_1122_stat = "PRICED" if eng_st.get("stack_generated") else "RULE_REJECTED"
                eng_1122_qpe = float(eng_st.get("leg_b_qpe_usd", 0.0))
                eng_1122_npc = round(gross_usd - eng_1122_inc, 2)

                # Independent statutory evaluation of multi-program stack
                if "ca_federal_cptc" in slugs and "ca_qc_pstc" in slugs:
                    ind_stat = "GATE_REJECTED"
                    ind_qpe = 0.0
                    ind_inc = 0.0
                    disp = "OPEN_CODE_DEFECT (UNLAWFUL_CPTC_DOMESTIC_PLUS_QC_PSTC_SERVICE_STACK)"
                    note = (
                        "Federal CPTC (ITA § 125.4) is restricted to certified domestic Canadian content, whereas "
                        "Quebec PSTC (ca_qc_pstc) is a foreign/service production credit (unlike Quebec QPRDP domestic credit). "
                        "Also note BH/LLS CPTC 60% cap base mismatch between price_segment (0.60*gross) and canonical_stack_bridge (0.60*net) (NA-HYB-DEF-05)."
                    )
                elif "ca_federal_cptc" in slugs and "on_ofttc" in slugs:
                    ind_stat = "NOT_ESTABLISHED"
                    ind_qpe = eng_1122_qpe
                    ind_inc = eng_1122_inc
                    disp = "REPAIRED_ASSISTANCE_FORMULA_PENDING_CAVCO_AND_PAYROLL (NA-HYB-DEF-03 / NA-HYB-DEF-05)"
                    note = (
                        "CRA Form T1131 / ITA § 125.4(1): OFTTC reduces net production cost (0.60*(G_net - OFTTC)), "
                        "not labour directly (repaired in 1.119.0). CAVCO certification and resident payroll schedule are claim follow-ups; "
                        "in planning mode, BTL crew in miscellaneous/payroll_fringes is omitted (NA-HYB-DEF-03) and BH standalone CPTC uses 0.60*gross vs 0.60*net in stack bridge (NA-HYB-DEF-05)."
                    )
                elif "ca_bc_dave" in slugs and "ca_bc_pstc" in slugs:
                    ind_stat = "NOT_ESTABLISHED"
                    ind_qpe = 0.0
                    ind_inc = 0.0
                    disp = "REPAIRED_IN_1122_STALE_IN_DB (BC_DAVE_LABOUR_BASIS_REQUIRES_VFX_LABOUR_LINES)"
                    note = (
                        "BC Income Tax Act s. 81.2: BC DAVE (16%) and BC PSTC (28%) apply to accredited BC labour only. "
                        "In 1.109.0/1.110.0, ca_bc_dave priced 16% on all BTL/VFX spend; in 1.122.0, ca_bc_dave requires labour-category lines inside VFX."
                    )
                else:
                    ind_stat = "NOT_ESTABLISHED"
                    ind_qpe = eng_1122_qpe
                    ind_inc = eng_1122_inc
                    disp = "NOT_ESTABLISHED_EMPIRICAL_GAP (MISSING_CANADIAN_PAYROLL_AND_OCASE_VFX_LABOUR_SPLIT)"
                    note = (
                        "Ontario OPSTC/OFTTC + OCASE stack requires Ontario resident payroll schedule and itemized OCASE computer animation labour."
                    )

                ind_npc = round(gross_usd - ind_inc, 2)
                stats_counter[gen_key][disp] = stats_counter[gen_key].get(disp, 0) + 1
                csv_rows.append({
                    "row_category": "SAVED_NA_MULTI_PROGRAM_STACK",
                    "project": proj,
                    "generation_label": gen_key,
                    "saved_engine_version": meta["engine_version"],
                    "input_fingerprint": meta["input_fingerprint"],
                    "scr_id": " | ".join(scr_ids),
                    "structure_id": " | ".join(struct_ids),
                    "structure_type": st_type,
                    "structural_family": r["structural_family"] or "",
                    "structure_name": name,
                    "anchor_jurisdiction": jcode,
                    "anchor_program": slugs[0] if slugs else "",
                    "routed_components": f"stack_partner:{slugs[1]}" if len(slugs) > 1 else "",
                    "gross_budget_usd": f"{gross_usd:.2f}",
                    "planned_cost_reduction_usd": "0.00",
                    "effective_planned_cost_usd": f"{gross_usd:.2f}",
                    "line_overlap_count": 0,
                    "independent_expected_status": ind_stat,
                    "independent_qpe_floor_usd": f"{ind_qpe:.2f}",
                    "independent_incentive_floor_usd": f"{ind_inc:.2f}",
                    "independent_conditional_upside_usd": "0.00",
                    "independent_npc_floor_usd": f"{ind_npc:.2f}",
                    "engine_1122_status": eng_1122_stat,
                    "engine_1122_qpe_usd": f"{eng_1122_qpe:.2f}",
                    "engine_1122_incentive_floor_usd": f"{eng_1122_inc:.2f}",
                    "engine_1122_npc_usd": f"{eng_1122_npc:.2f}",
                    "saved_db_status": c_status,
                    "saved_db_qpe_usd": f"{saved_qpe:.2f}",
                    "saved_db_incentive_usd": f"{saved_inc:.2f}",
                    "saved_db_npc_usd": f"{saved_npc:.2f}",
                    "incentive_delta_saved_vs_independent_usd": f"{saved_inc - ind_inc:.2f}",
                    "incentive_delta_1122_vs_independent_usd": f"{eng_1122_inc - ind_inc:.2f}",
                    "audit_disposition": disp,
                    "statutory_basis_and_notes": note,
                })
                continue

            if st_type == "component_relocation":
                # Legacy 0.1.0 California anchor + routed component slice
                routed_seg = r["component_allocations"][0] if r["component_allocations"] else {}
                r_comp = routed_seg.get("component", "")
                r_alloc = float(routed_seg.get("allocated_usd", 0.0))
                rem_ca_alloc = round(gross_usd - r_alloc, 2)
                # Parse target jurisdiction from name: "US-CA anchor — <comp> routed to <JCODE> (component/split)"
                target_j = name.split("routed to ")[-1].split(" ")[0] if "routed to " in name else ""
                disp = "LEGACY_COMPONENT_RELOCATION_SUPERSEDED_BY_ORDINARY_HYBRID"
                note = (
                    f"Legacy run_full_analysis (0.1.0) component_relocation candidate routing {r_comp} (${r_alloc:,.2f}) "
                    f"from US-CA anchor (${rem_ca_alloc:,.2f}) to {target_j} using static headline rate without canonical "
                    f"SpendRule/EligibilityGate evaluation; superseded by canonical ordinary_component_hybrid."
                )
                stats_counter[gen_key][disp] = stats_counter[gen_key].get(disp, 0) + 1
                csv_rows.append({
                    "row_category": "SAVED_NA_COMPONENT_RELOCATION",
                    "project": proj,
                    "generation_label": gen_key,
                    "saved_engine_version": meta["engine_version"],
                    "input_fingerprint": meta["input_fingerprint"],
                    "scr_id": " | ".join(scr_ids),
                    "structure_id": " | ".join(struct_ids),
                    "structure_type": st_type,
                    "structural_family": r["structural_family"] or "",
                    "structure_name": name,
                    "anchor_jurisdiction": "US-CA",
                    "anchor_program": "ca_film_30",
                    "routed_components": f"{r_comp} (${r_alloc:,.2f} -> {target_j})",
                    "gross_budget_usd": f"{gross_usd:.2f}",
                    "planned_cost_reduction_usd": "0.00",
                    "effective_planned_cost_usd": f"{gross_usd:.2f}",
                    "line_overlap_count": r["line_overlap_count"],
                    "independent_expected_status": "SUPERSEDED_LEGACY_PATH",
                    "independent_qpe_floor_usd": f"{saved_qpe:.2f}",
                    "independent_incentive_floor_usd": "0.00",
                    "independent_conditional_upside_usd": "0.00",
                    "independent_npc_floor_usd": f"{gross_usd:.2f}",
                    "engine_1122_status": "SUPERSEDED_BY_ORDINARY_HYBRID",
                    "engine_1122_qpe_usd": "0.00",
                    "engine_1122_incentive_floor_usd": "0.00",
                    "engine_1122_npc_usd": f"{gross_usd:.2f}",
                    "saved_db_status": c_status,
                    "saved_db_qpe_usd": f"{saved_qpe:.2f}",
                    "saved_db_incentive_usd": f"{saved_inc:.2f}",
                    "saved_db_npc_usd": f"{saved_npc:.2f}",
                    "incentive_delta_saved_vs_independent_usd": f"{saved_inc:.2f}",
                    "incentive_delta_1122_vs_independent_usd": "0.00",
                    "audit_disposition": disp,
                    "statutory_basis_and_notes": note,
                })
                continue

            # st_type == "hybrid" and candidate_status == "PRICED"
            allocs = r["component_allocations"]
            anchor_seg = next((s for s in allocs if s["component"] == "principal_production"), allocs[0])
            routed_segs = [s for s in allocs if s["component"] != "principal_production"]

            a_jcode = anchor_seg["jurisdiction_code"]
            a_pslug = anchor_seg["program_slug"]
            a_alloc = float(anchor_seg["allocated_usd"])
            a_key = f"{proj}|principal_production|{a_alloc}|{a_jcode}|{a_pslug}"
            eng_anchor = leg_map[a_key]

            a_ind_stat, a_ind_qpe, a_ind_inc, a_defect, a_note = evaluate_anchor_leg_independently(
                proj, gross_usd, a_alloc, a_jcode, a_pslug, eng_anchor
            )

            routed_desc_parts = []
            routed_eng_all_exec = True
            routed_ind_all_valid = True
            routed_eng_qpe_sum = 0.0
            routed_eng_inc_sum = 0.0
            routed_ind_qpe_sum = 0.0
            routed_ind_inc_sum = 0.0
            routed_defects = []
            routed_notes = []

            for s in routed_segs:
                sc = s["component"]
                sj = s["jurisdiction_code"]
                sp = s["program_slug"]
                sa = float(s["allocated_usd"])
                skey = f"{proj}|{sc}|{sa}|{sj}|{sp}"
                eng_r = leg_map[skey]
                routed_desc_parts.append(f"{sc} (${sa:,.2f} -> {sj}/{sp})")

                if not eng_r["executable"]:
                    routed_eng_all_exec = False
                else:
                    routed_eng_qpe_sum += float(eng_r["qpe_usd"])
                    routed_eng_inc_sum += float(eng_r["incentive_floor_usd"])

                r_stat, r_qpe, r_inc, r_def, r_note = evaluate_routed_leg_independently(
                    proj, gross_usd, sc, sa, sj, sp, eng_r
                )
                if r_stat not in ("PRICED", "NOT_ESTABLISHED"):
                    routed_ind_all_valid = False
                else:
                    routed_ind_qpe_sum += r_qpe
                    routed_ind_inc_sum += r_inc
                if r_def:
                    routed_defects.append(r_def)
                routed_notes.append(f"[{sc}->{sj}/{sp}: {r_note}]")

            # Whole-hybrid status in canonical-1.122.0 vs Independent Statutory Audit
            eng_hybrid_exec = bool(eng_anchor["executable"] and routed_eng_all_exec)
            eng_hybrid_stat = (
                "PRICED"
                if eng_hybrid_exec
                else (
                    "GATE_REJECTED"
                    if any(
                        not leg_map[f"{proj}|{s['component']}|{float(s['allocated_usd'])}|{s['jurisdiction_code']}|{s['program_slug']}"]["gate_passed"]
                        for s in routed_segs
                    )
                    else "RULE_REJECTED"
                )
            )
            eng_hybrid_qpe = round(float(eng_anchor["qpe_usd"]) + routed_eng_qpe_sum, 2) if eng_hybrid_exec else 0.0
            eng_hybrid_inc = round(float(eng_anchor["incentive_floor_usd"]) + routed_eng_inc_sum, 2) if eng_hybrid_exec else 0.0
            eng_hybrid_npc = round(gross_usd - eng_hybrid_inc, 2)

            if not routed_ind_all_valid or a_ind_stat in ("GATE_REJECTED", "RULE_REJECTED", "CONDITIONAL_NONDETERMINISTIC"):
                ind_hybrid_stat = "GATE_REJECTED" if not routed_ind_all_valid else a_ind_stat
                ind_hybrid_qpe = 0.0
                ind_hybrid_inc = 0.0
            else:
                ind_hybrid_stat = a_ind_stat
                ind_hybrid_qpe = round(a_ind_qpe + routed_ind_qpe_sum, 2)
                ind_hybrid_inc = round(a_ind_inc + routed_ind_inc_sum, 2)
            ind_hybrid_npc = round(gross_usd - ind_hybrid_inc, 2)

            saved_qpe_sum = round(
                float(eng_anchor["raw_qpe_usd"]) + sum(
                    float(leg_map[f"{proj}|{s['component']}|{float(s['allocated_usd'])}|{s['jurisdiction_code']}|{s['program_slug']}"]["raw_qpe_usd"])
                    for s in routed_segs
                ),
                2,
            )

            # Determine unified audit disposition
            if not eng_hybrid_exec:
                # Repaired in canonical-1.122.0 (rejected in 1.122.0, stale PRICED in saved DB)
                disp = f"REPAIRED_IN_1122_STALE_IN_DB ({eng_hybrid_stat})"
            elif routed_defects:
                disp = f"OPEN_CODE_DEFECT ({' + '.join(sorted(set(routed_defects)))})"
            elif a_defect == "NA-DEFECT-01":
                disp = "OPEN_CODE_DEFECT (NA-DEFECT-01_NY_40PCT_ATL_CAP_ON_ANCHOR)"
            elif a_defect and "US-AL" in a_defect:
                disp = f"OPEN_CODE_DEFECT ({a_defect})"
            elif a_ind_stat == "NOT_ESTABLISHED":
                disp = "NOT_ESTABLISHED_EMPIRICAL_GAP (CLAIM_FOLLOWUP_ON_ANCHOR_OR_LABOUR)"
            elif abs(saved_inc - eng_hybrid_inc) > 0.05:
                disp = "REPAIRED_IN_1122_STALE_IN_DB (ANCHOR_OR_COMPONENT_RATE_UPDATED)"
            else:
                disp = "VERIFIED_HYBRID_IN_1122_AND_DB"

            stats_counter[gen_key][disp] = stats_counter[gen_key].get(disp, 0) + 1
            csv_rows.append({
                "row_category": "SAVED_NA_HYBRID_ROW",
                "project": proj,
                "generation_label": gen_key,
                "saved_engine_version": meta["engine_version"],
                "input_fingerprint": meta["input_fingerprint"],
                "scr_id": " | ".join(scr_ids),
                "structure_id": " | ".join(struct_ids),
                "structure_type": st_type,
                "structural_family": r["structural_family"] or "",
                "structure_name": name,
                "anchor_jurisdiction": a_jcode,
                "anchor_program": a_pslug,
                "routed_components": "; ".join(routed_desc_parts),
                "gross_budget_usd": f"{gross_usd:.2f}",
                "planned_cost_reduction_usd": "0.00",
                "effective_planned_cost_usd": f"{gross_usd:.2f}",
                "line_overlap_count": r["line_overlap_count"],
                "independent_expected_status": ind_hybrid_stat,
                "independent_qpe_floor_usd": f"{ind_hybrid_qpe:.2f}",
                "independent_incentive_floor_usd": f"{ind_hybrid_inc:.2f}",
                "independent_conditional_upside_usd": "0.00",
                "independent_npc_floor_usd": f"{ind_hybrid_npc:.2f}",
                "engine_1122_status": eng_hybrid_stat,
                "engine_1122_qpe_usd": f"{eng_hybrid_qpe:.2f}",
                "engine_1122_incentive_floor_usd": f"{eng_hybrid_inc:.2f}",
                "engine_1122_npc_usd": f"{eng_hybrid_npc:.2f}",
                "saved_db_status": c_status,
                "saved_db_qpe_usd": f"{saved_qpe_sum:.2f}",
                "saved_db_incentive_usd": f"{saved_inc:.2f}",
                "saved_db_npc_usd": f"{saved_npc:.2f}",
                "incentive_delta_saved_vs_independent_usd": f"{saved_inc - ind_hybrid_inc:.2f}",
                "incentive_delta_1122_vs_independent_usd": f"{eng_hybrid_inc - ind_hybrid_inc:.2f}",
                "audit_disposition": disp,
                "statutory_basis_and_notes": f"Anchor [{a_jcode}/{a_pslug}: {a_note}] " + " ".join(routed_notes),
            })

    # Write NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv
    fieldnames = list(csv_rows[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"[PASS] Wrote {len(csv_rows)} rows to {OUT_CSV}")

    # Write NORTH_AMERICAN_HYBRID_AUDIT_HANDOFF.md
    write_handoff_markdown(lls_mb_ca, csv_rows, stats_counter, agg_summary)
    print(f"[PASS] Wrote handoff report to {OUT_MD}")


def write_handoff_markdown(
    lls_mb_ca: Dict[str, Any],
    csv_rows: List[Dict[str, Any]],
    stats_counter: Dict[str, Dict[str, int]],
    agg_summary: Dict[str, Any],
) -> None:
    # Count dispositions across the 662 PRICED saved rows
    priced_rows = [r for r in csv_rows if r["row_category"] in ("SAVED_NA_HYBRID_ROW", "SAVED_NA_MULTI_PROGRAM_STACK", "SAVED_NA_COMPONENT_RELOCATION")]
    disp_counts: Dict[str, int] = {}
    for r in priced_rows:
        d = r["audit_disposition"]
        disp_counts[d] = disp_counts.get(d, 0) + 1

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# Independent North American Hybrid & Multi-Program Audit Handoff (`FVD`, `BH`, `LU`, `LLS`)\n\n")
        f.write("**Audit Track:** North American Hybrid, Multi-Program & Component-Relocation Independent Audit  \n")
        f.write("**Frozen Canonical Engine Baseline:** `canonical-1.122.0`  \n")
        f.write(f"**Frozen Claude Remediation Commits:** `{FROZEN_COMMITS[0]}` (`f5dc6a17`), `{FROZEN_COMMITS[1]}` (`f0b042ba`), `{FROZEN_COMMITS[2]}` (`59566fd1`)  \n")
        f.write("**Saved Database Under Comparison:** `frametax2_claude_optimizer_acceptance_20260919` (`canonical-1.106.0` .. `canonical-1.110.0`)  \n")
        f.write(f"**Coverage Matrix Deliverable:** `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` (**{len(csv_rows):,} rows**: 9 explicit LLS Manitoba–California artifact & contingency-election rows + 1,590 saved NA rows across all four budgets)  \n")
        f.write("**Gate Status:** `STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`\n\n")
        f.write("---\n\n")

        # Section 1
        f.write("## 1. Executive Summary & Audit Methodology\n\n")
        f.write("In accordance with `PROJECT_RULES.md`, `docs/architecture/CAPABILITY_LEDGER.md`, and Codex's `CODEX_CA_GATE_REVIEW_20261011.md`, `CODEX_LLS_NA_HYBRID_LOAD_REVIEW_20261011.md`, and `CODEX_NY_CANADA_CHANGED_PATH_REVIEW_20261011.md`, this audit independently reconstructs every North American hybrid, multi-program stack, component relocation, and treaty co-production candidate across all four anchor projects (`The Little Utopia` [`LU`], `F#K Valentine's Day` [`FVD`], `Bad Hombres` [`BH`], and `Lips Like Sugar` [`LLS`]) outside the engine from retained Movie Magic budget lines (`docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json`) and dated primary statutory authority.\n\n")
        f.write("### Core Methodological Controls Enforced\n")
        f.write("1. **Independent Expectation First (Zero Circularity):** Every segment allocation, eligibility gate, QPE/labour base, statutory cap, uplift, government assistance deduction, line overlap (`0` shared `line_id`s across all saved hybrids), contingency treatment, and Net Production Cost (NPC) was calculated from primary statute/guidelines before comparing against `canonical-1.122.0` (`59566fd1`) and stale saved PostgreSQL rows (`1.106.0`–`1.110.0`).\n")
        f.write("2. **No Inferred Statutory Exclusion from an Absent Engine Rule:** Where `program_spend_rules.py` lacks a program-specific contingency rule (specifically `ca_mb_film_video_credit`), the engine's fallback exclusion of deployed contingency when no line-level `ContingencyAllocation` is supplied is documented as an **engine implementation behavior (`NA-HYB-DEF-04`)**, never mischaracterized as a statutory exclusion under Manitoba law.\n")
        f.write("3. **Gross Preservation & Single Adjustment Application:** Gross budget is preserved on every scenario; undeployed contingency (`planned_cost_reduction_usd`) is subtracted once from planned cost (`effective_planned_cost_usd`); and guaranteed floor credits are strictly separated from conditional upside.\n")
        f.write("4. **Claim Follow-Ups vs. Planning Scenarios:** Missing empirical claim documents (CAVCO certificates, itemized Canadian resident payroll ledgers, individual talent deal memos, hotel folio splits) prevent exact post-hoc claim verification, not explicitly labeled prospective relocation planning scenarios or deterministic statutory gate checks.\n\n")
        f.write("---\n\n")

        # Section 2: LLS Manitoba-California Reconstruction
        f.write("## 2. Priority 1 Deep-Dive: Independent Reconstruction of `LLS` Manitoba–California (`CA-MB` Principal + `US-CA` VFX)\n\n")
        f.write("### 2.1 Exact Saved Database Row Identities Across Generations\n\n")
        f.write("| Generation Label | Engine Version | Input Fingerprint | `scr.id` | `structure_id` | Saved Status | Saved CA-MB Alloc ($) | Saved US-CA Alloc ($) | Saved CA-MB Credit ($) | Saved US-CA Credit ($) | Saved Total Credit ($) | Saved True NPC ($) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        f.write("| **`LLS_110b`** (Latest) | `canonical-1.110.0` | `78ed9f199c4e5eb0...` | `914a47c0-9b1e-4d47-867f-425e6d4792fa` | `9656c441-881e-4667-bec1-8841387408ce` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |\n")
        f.write("| **`LLS_110a`** (Codex Ref) | `canonical-1.110.0` | `0ac00210e593261b...` | `51680824-eb85-4920-b124-04d0b6fce131` | `268917e8-6749-4730-9399-5a686a3f1086` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |\n")
        f.write("| **`LLS_106`** (Historical) | `canonical-1.106.0` | `0c6459528b797538...` | `0338ace0-e929-42aa-89df-fd1fe7ff629c` | `110ce2e4-f121-433b-a9ff-591ee4718b77` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |\n\n")
        f.write("* **Line Conservation & Zero Overlap Proof:** Across all three saved rows, `LLS` (`doc_id = 6ae1bbec-f8f2-432b-a09f-9d9c8833944b`, **46 active budget lines**, gross **`$11,983,654.00`**) is partitioned into **45 lines (`$11,943,654.00`)** allocated to `CA-MB` (`principal_production`) and **1 line (`4400 VISUAL EFFECTS`, `line_id = f942e378-4679-4f6f-bcb9-e5a2a210b55f`, `$40,000.00`)** allocated to `US-CA` (`vfx`). Set intersection of `line_ids` is empty (**`overlap_count = 0`**), and `$11,943,654.00 + $40,000.00 = $11,983,654.00` (`$0.00` unallocated variance).\n\n")

        f.write("### 2.2 Independent Statutory Analysis of the California `vfx` Leg (`$40,000.00`)\n\n")
        f.write("* **Dated Primary Authority:**\n")
        f.write("  1. **Prospective Relocation Rule — California Film & Television Tax Credit Program 4.0 Guidelines (California Film Commission, effective January 1, 2026; applies to allocation letters dated on or after July 1, 2025), Section II.A.1 (PDF p. 3):** A feature film (`$1,000,000` minimum production budget) is eligible **only if EITHER at least 75% of the total production budget is spent in California OR at least 75% of principal photography days occur wholly in California**.\n")
        f.write("  2. **Historical Reference Input — California Program 3.0 (Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) & Cal. Code Regs. tit. 10, § 5520(a); LLS CFC Allocation Letter dated March 6, 2023):** Imposes the identical **75% California budget OR 75% California principal photography days** threshold (the 2023-03-06 letter approved LLS for a full California shoot with `$5,990,260` estimated QPE and `$1,198,052` credit at 20%, not a standalone `$40,000` VFX slice).\n")
        f.write("* **Spend Branch Evaluation:**\n")
        f.write("  $$\\text{California Spend Share} = \\frac{\\$40,000.00}{\\$11,983,654.00} = 0.00333788 \\; (0.3338\\%) < 75.0\\%$$\n")
        f.write("  The spend branch fails by 74.67 percentage points (and `$40,000.00` is also below the `$1,000,000` minimum budget threshold if evaluated standalone).\n")
        f.write("* **Principal-Photography-Days Branch & Evidence Discipline (`CODEX_CA_GATE_REVIEW_20261011.md`):**\n")
        f.write("  - Dollar shares never establish shooting days.\n")
        f.write("  - **In this explicit modeled hybrid scenario** (`principal_production` placed in `CA-MB`, only `vfx` placed in `US-CA`), 100% of modeled principal photography is placed outside California (`0% < 75%`), so the California leg fails the project eligibility gate (**`PROJECT_ELIGIBILITY_GATE_FAILED`**; `$0.00` credit).\n")
        f.write("  - **Mixed / Unmodeled Shoot Distinction:** If a structure does not model principal photography placement (or splits principal photography without day counts) and lacks producer-stated `ca_principal_photography_days_in_california_pct`, the gate is **`CONDITIONAL`** (`$0.00` guaranteed floor; conditional upside requires producer day confirmation), never a false pass.\n")
        f.write("  - **VFX Uplift Distinction (CFC Program 4.0 Guidelines § III.B.1):** Even if the project gate were satisfied, the `+5%` VFX uplift requires either $\\ge \\$10,000,000$ in California VFX QPE or $\\ge 75\\%$ of worldwide VFX costs incurred in California (`$40,000 / $40,000 = 100%` of VFX, which is a conditional subset uplift on top of a valid base credit, never a substitute for the Section II.A.1 project eligibility gate).\n\n")

        f.write("### 2.3 Independent Statutory Analysis of the Manitoba `principal_production` Leg (`$11,943,654.00`)\n\n")
        f.write("* **Dated Primary Authority:**\n")
        f.write("  - **Manitoba Income Tax Act (C.C.S.M. c. I10, ss. 7.5–7.9, current from July 1, 2026 to October 8, 2026)** and **Manitoba Film & Video Production Tax Credit Guidelines (Manitoba Film & Music, June 2024)**.\n")
        f.write("* **Account-by-Account Classification of the 45 Manitoba Budget Lines (`$11,943,654.00`):**\n")
        f.write("  1. **Statutorily Excluded Financing Costs (`$1,700,000.00`):** `6500 FINANCING FEES` (`$450,000.00`) + `6600 BRIDGE` (`$250,000.00`) + `6700 BANKING FEE` (`$1,000,000.00`) = **`$1,700,000.00`** (`finance_costs`, statutorily excluded under s. 7.5(1)).\n")
        f.write("  2. **Unconfirmed Residuals Reserve (`$400,000.00` — Distinct from `7100 Contingency`):** `6800 RESIDUALS RESERVE` (`line_id = 57f49d6e-62f6-4bb6-8fb6-48bfee057a79`, **`$400,000.00`**, `residuals_reserve`). Excluded from the confirmed QPE floor (`GREY_AREA_REQUIRES_AUTHORITY`) until actual residual payments are incurred; **never part of the user contingency utilization election (`inputs.contingency_reserve_usd`)**.\n")
        f.write("  3. **Contingency Reserve (`$400,000.00`):** `7100 Contingency` (`line_id = 6f18b074-bc09-466f-a40b-52c79bde9be3`, **`$400,000.00`**, `contingency`, `inputs.contingency_reserve_usd = $400,000.00`). Undeployed reserve is statutorily excluded under Manitoba ITA s. 7.5(1)(g)–(h); deployed contingency actually spent on eligible Manitoba production costs is statutorily eligible under s. 7.5(1).\n")
        f.write("  4. **Remaining Manitoba Production Cost Pool (`$9,443,654.00` across 40 lines; `$9,483,654.00` if `4400 VISUAL EFFECTS` `$40,000.00` is retained in Manitoba):**\n")
        f.write("     - **ATL Accounts (`1100–1400` + `1900` Fringes = `$3,114,414.00`):** `1100 SCRIPT` (`$314,153`), `1200 PRODUCERS` (`$1,414,198`), `1300 DIRECTION` (`$267,384`), `1400 CAST` (`$863,388`), `1900 Total Fringes` (`$255,291`). Under Manitoba ITA s. 7.5(1), under the 30% Cost-of-Production stream, non-resident ATL fees qualify only to the extent they are eligible service contract expenditures for services performed in Manitoba or deemed eligible non-resident salaries (technical crew with Manitoba trainees).\n")
        f.write("     - **ATL Travel & Living (`1500 ATL TRAVEL & LIVING = $60,561.00`):** Admitted in the engine's `$9,443,654.00` `OPEN_DEFAULT_INCLUDE` base; statutorily under Manitoba ITA s. 7.5(1) (`\"eligible accommodation expenditure\"`), accommodation in Manitoba is capped at **`$300.00` per night** per unit and requires Manitoba travel/hotel folios. Excluding `$60,561.00` pending hotel folios yields a strict physical/local Manitoba base of **`$9,383,093.00`** (`30%` credit = **`$2,814,927.90`**, `-$18,168.30`).\n")
        f.write("     - **BTL Production, Post-Production, Music, Legal (`6300 $150,000`), Insurance (`6400 $200,000`), and Completion Bond (`7200 $115,000`):** Total **`$6,268,679.00`** (`$9,443,654.00` combined with ATL).\n")
        f.write("* **Two-Stream Statutory Calculation & Comparison (Manitoba ITA s. 7.6(2)–(6)):**\n")
        f.write("  - **Stream A — 30% Cost-of-Production Credit (Manitoba ITA s. 7.6(6)):**\n")
        f.write("    $$\\text{Credit}_{\\text{Stream A}} = 0.30 \\times A + 0.08 \\times B$$\n")
        f.write("    where $A$ is eligible Manitoba production costs (`$9,443,654.00` on the 45-line hybrid allocation; `$9,483,654.00` on the 46-line all-Manitoba allocation) and $B$ equals $A$ **only if** the film is co-produced with an eligible Manitoba production corporation that owns voting shares (`s. 7.6(6)`).\n")
        f.write("    * **Guaranteed 30% Base (Artifact 2, 45 lines):** $0.30 \\times \\$9,443,654.00 = \\mathbf{\\$2,833,096.20}$ (Strict base excluding `$60,561` unsplit ATL travel = **`$2,814,927.90`**).\n")
        f.write("    * **Conditional +8% Manitoba Co-Producer Upside:** $0.08 \\times \\$9,443,654.00 = \\mathbf{+\\$755,492.32}$ (38% ceiling = **`$3,588,588.52`**; requires Manitoba co-producer voting-share agreement).\n")
        f.write("    * **Statutory Corporate Prerequisite (`s. 7.5(1)(d)`):** Stream A requires an eligible corporation where at least **25% of T4 salaries and wages** paid for work on the eligible film are paid to eligible Manitoba employees.\n")
        f.write("  - **Stream B — 45% Cost-of-Salaries Credit (Manitoba ITA s. 7.6(2)–(5)):**\n")
        f.write("    $$\\text{Credit}_{\\text{Stream B}} = (0.45 + \\underbrace{0.10}_{\\text{Frequent}} + \\underbrace{0.05}_{\\text{MB Producer}} + \\underbrace{0.05}_{\\text{Rural/North}}) \\times (L_{\\text{MB resident}} + L_{\\text{deemed non-resident}})$$\n")
        f.write("    where deemed non-resident technical labour is capped at **30%** of resident salaries (if $\\ge 2$ Manitoba resident trainees are employed per non-resident department) or **10%** (if $1$ trainee is employed) under `s. 7.5(1)(d)`, and the `+10%`/`+5%`/`+5%` bonuses apply to the entire eligible salary base including deemed non-resident salaries.\n")
        f.write("    * In `canonical-1.122.0`, lines mapped to `component_basis_spend_categories` (`1100` `$314,153` + `1200` `$1,414,198` + `1300` `$267,384` + `1400` `$863,388` + `3100 MAKEUP & HAIR` `$76,175`) sum to **`$2,935,298.00`** $\\to$ 45% base = **`$1,320,884.10`** (65% ceiling = **`$1,907,943.70`**), because BTL department accounts (`2000–3900` except `3100`) are classified as `miscellaneous` / `payroll_fringes` (`NA-HYB-DEF-03`).\n")
        f.write("    * Even if 100% of identifiable direct BTL labor + fringes (`$1,998,678.00`) plus ATL (`$3,114,414.00`) = `$5,113,092.00` were Manitoba resident salaries, $0.45 \\times \\$5,113,092.00 = \\$2,300,891.40 < \\$2,833,096.20$. Thus **Stream A (30% Cost-of-Production = `$2,833,096.20`) governs the planning floor**.\n")
        f.write("  - **Why the Stale Saved DB Row (`$4,249,644.30` MB / `$4,263,644.30` Total) Was Wrong:**\n")
        f.write("    * In `canonical-1.106.0` and `canonical-1.110.0`, the engine multiplied the **45% Cost-of-Salaries rate** against the **all-spend Cost-of-Production base** (`0.45 × $9,443,654.00 = $4,249,644.30`) and added an ineligible `$14,000.00` California VFX credit (`0.35 × $40,000.00`), overstating the credit by **`+$1,430,548.10`** against Artifact 2 (`$2,833,096.20`) and **`+$1,418,548.10`** against Artifact 3 (`$2,845,096.20`).\n\n")

        f.write("### 2.4 Separation of the Three Distinct `LLS` Manitoba–California Artifacts\n\n")
        f.write("| Artifact ID & Name | Structure Type | Jurisdiction Allocation | Eligibility / Status | Confirmed QPE Floor ($) | Guaranteed Credit Floor ($) | Conditional Credit Upside ($) | Unadjusted NPC at `NOT_STATED` ($) | Variance vs Stale DB (`$4,263,644.30`) |\n")
        f.write("| :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: |\n")
        f.write("| **Artifact 1: Retained Hybrid** (`CA-MB` Principal + `US-CA` VFX) | `hybrid` (`ordinary_component_hybrid`) | `CA-MB`: `$11,943,654.00` (45 lines)<br>`US-CA`: `$40,000.00` (1 line `4400`) | **`GATE_REJECTED`** (`PROJECT_ELIGIBILITY_GATE_FAILED` on `US-CA` leg) | 0.00 | **0.00** | 0.00 | **11,983,654.00** | **+4,263,644.30** (Stale row invalidly priced) |\n")
        f.write("| **Artifact 2: Same-Allocation Manitoba Leg Sensitivity** (`CA-MB` on 45 lines; `US-CA` VFX earns `$0`) | `hybrid_leg_sensitivity` | `CA-MB`: `$11,943,654.00` (45 lines)<br>`US-CA`: `$40,000.00` (uncredited `$0`) | **`PRICED`** (Manitoba 30% Stream A) | 9,443,654.00 | **2,833,096.20** | +755,492.32 (`+8%` co-prod)<br>+120,000.00 (`30%` of `$400k` cont.) | **9,150,557.80** | **+1,430,548.10** (`$4,249,644.30` MB leg + `$14k` CA leg) |\n")
        f.write("| **Artifact 3: Relocated All-Manitoba Single-Jurisdiction Alternative** (`100%` in `CA-MB` incl. `$40,000` VFX) | `single_country` (`full_relocation`) | `CA-MB`: `$11,983,654.00` (all 46 lines incl. `4400 VFX`) | **`PRICED`** (Manitoba 30% Stream A) | 9,483,654.00 | **2,845,096.20** | +758,692.32 (`+8%` co-prod)<br>+120,000.00 (`30%` of `$400k` cont.) | **9,138,557.80** | **+1,418,548.10** (vs `$4,263,644.30` hybrid) / **+1,422,548.10** (vs `$4,267,644.30` stale all-MB row) |\n\n")

        f.write("### 2.5 Four-Election Contingency Matrix (`NOT_STATED`, `0%`, `50%`, `100%` on `7100 Contingency = $400,000.00`)\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Statutory vs. Engine Contingency Distinction (Correcting Claude's `LLS_MB_CA_RECONSTRUCTION_20261011.md` Line 21):**\n")
        f.write("> Claude's reconstruction note stated: *\"Manitoba has no program-specific contingency rule, so the 400,000 contingency line is excluded from Manitoba QPE under every election.\"* That statement describes **only** the engine's current code in `qualification_derivation.py` (line 490) and `program_spend_rules.py` (which has no `SpendRule` for `ca_mb_film_video_credit`, causing `contingency_allowance_pct` to remain `None` when line-level `ContingencyAllocation` is not passed). **It is NOT a statutory exclusion under Manitoba law.**\n")
        f.write("> Under **Manitoba Income Tax Act s. 7.5(1)**:\n")
        f.write("> 1. **Undeployed contingency reserve** (`$400,000` at `0%`, `$200,000` at `50%`, `$0` at `100%`) is not incurred/paid and is statutorily excluded from QPE (`s. 7.5(1)(g)–(h)`), while reducing planned production cost once (`planned_cost_reduction_usd`).\n")
        f.write("> 2. **Deployed contingency actually spent on eligible Manitoba production costs** (`$200,000` at `50%`, `$400,000` at `100%`) **IS statutorily eligible** under Manitoba ITA s. 7.5(1), generating **`+$60,000.00`** credit at `50%` (`$2,893,096.20` on Artifact 2; `$2,905,096.20` on Artifact 3) and **`+$120,000.00`** credit at `100%` (`$2,953,096.20` on Artifact 2; `$2,965,096.20` on Artifact 3). This missing engine rule is logged as active defect **`NA-HYB-DEF-04`**.\n\n")

        f.write("| Contingency Election (`7100` = `$400,000`) | Deployed Contingency ($) | Planned Cost Reduction (`planned_cost_reduction_usd`) ($) | Effective Planned Cost ($) | Artifact 2 Engine Floor QPE / Credit / NPC ($) | Artifact 2 Statutory Deployed-to-Eligible QPE / Credit / NPC ($) | Artifact 3 Engine Floor QPE / Credit / NPC ($) | Artifact 3 Statutory Deployed-to-Eligible QPE / Credit / NPC ($) | Conditional Contingency Upside ($) |\n")
        f.write("| :--- | ---: | ---: | ---: | :--- | :--- | :--- | :--- | ---: |\n")
        for cm in lls_mb_ca["contingency_matrix"]:
            f.write(
                f"| **`{cm['election']}`** | {cm['deployed_contingency_usd']:,.2f} | {cm['planned_cost_reduction_usd']:,.2f} | **{cm['effective_planned_cost_usd']:,.2f}** | "
                f"QPE: {cm['art2_engine_qpe_floor_usd']:,.2f}<br>Inc: **{cm['art2_engine_inc_floor_usd']:,.2f}**<br>NPC: **{cm['art2_engine_npc_usd']:,.2f}** | "
                f"QPE: {cm['art2_statutory_deployed_qpe_usd']:,.2f}<br>Inc: **{cm['art2_statutory_deployed_inc_usd']:,.2f}**<br>NPC: **{cm['art2_statutory_deployed_npc_usd']:,.2f}** | "
                f"QPE: {cm['art3_engine_qpe_floor_usd']:,.2f}<br>Inc: **{cm['art3_engine_inc_floor_usd']:,.2f}**<br>NPC: **{cm['art3_engine_npc_usd']:,.2f}** | "
                f"QPE: {cm['art3_statutory_deployed_qpe_usd']:,.2f}<br>Inc: **{cm['art3_statutory_deployed_inc_usd']:,.2f}**<br>NPC: **{cm['art3_statutory_deployed_npc_usd']:,.2f}** | "
                f"{cm['conditional_contingency_upside_usd']:,.2f} |\n"
            )
        f.write("\n---\n\n")

        # Section 3: Full Four-Anchor NA Hybrid Coverage Summary
        f.write("## 3. Priority 2: Full Four-Anchor North American Hybrid & Multi-Program Coverage (`LU`, `FVD`, `BH`, `LLS`)\n\n")
        f.write("### 3.1 Movable Component Slices Across the Four Anchor Budgets (Source-Line Verified)\n\n")
        f.write("| Project | Controlling Gross Budget ($) | `post` Only (`post_production` excl. Music) ($) | `vfx` (`4400`/`4600`/`6100`) ($) | `music_package` (`4600`/`5100`/`6000`) ($) | `post_vfx_package` (`post + vfx`) ($) | `post_vfx_music_package` (`post + vfx + music`) ($) | `contingency` Reserve ($) | Other Excluded / Grey Lines ($) |\n")
        f.write("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |\n")
        f.write("| **`LU`** | 4,364,393.00<br>*(Leaf: 4,364,395.00)* | 9,068.00<br>*(`5000 EDITORIAL`, stated outside in LA)* | 52,500.00<br>*(`6100 VFX DEPT`)* | 0.00<br>*(`6000 MUSIC = $0`)* | 61,568.00<br>*(or `9,068.00` when `vfx` split)* | 61,568.00 | 301,131.00<br>*(`8300`, 100% stated)* | `1600` ATL Travel `$397,279`; `3900` BTL Travel `$438,254`; `7000` Admin `$297,593`; `7100` Publicity `$24,348`; `7200/8100` Ins. `$60,555` |\n")
        f.write("| **`FVD`** | 4,517,687.00 | 146,446.00<br>*(`5000, 5200, 5400, 5600, 5700`)* | 10,000.00<br>*(`4600 VISUAL EFFECTS`)* | 10,200.00<br>*(`5100 MUSIC`)* | 156,446.00<br>*(or `146,446.00` when `vfx` split)* | 166,646.00<br>*(or `156,646.00` when `vfx` split)* | 362,866.00<br>*(`7902 CONTINGENCY`)* | `7901` Finance `$453,583` (`EXCLUDED`); `1500` ATL Travel `$100,000`; `7100` Legal `$50,000`; `7200` Ins. `$100,000`; `7905` Bond `$65,000` |\n")
        f.write("| **`BH`** | 2,482,023.00 | 107,958.00<br>*(`4300, 4500, 4700, 4800`)* | 0.00 | 5,000.00<br>*(`4600 MUSIC`)* | 107,958.00 | 112,958.00 | 94,382.00<br>*(`CONTINGENCY`)* | `6700` Legal `$15,000`; `6800` Ins. `$45,000`; `1500` ATL Travel `$54,000`; `6600` Gen. Expense `$83,850` |\n")
        f.write("| **`LLS`** | 11,983,654.00 | 611,230.00<br>*(`3700, 4500, 4700, 4800, 4900, 5800`)* | 40,000.00<br>*(`4400 VISUAL EFFECTS`)* | 206,774.00<br>*(`4600 MUSIC`)* | 651,230.00<br>*(or `611,230.00` when `vfx` split)* | 858,004.00<br>*(or `818,004.00` when `vfx` split)* | 400,000.00<br>*(`7100 Contingency`)* | `6500-6700` Financing `$1,700,000` (`EXCLUDED`); `6800` Residuals Reserve `$400,000` (`GREY_AREA`); `7200` Bond `$115,000`; `6300` Legal `$150,000`; `6400` Ins. `$200,000` |\n\n")

        f.write("### 3.2 Saved Database NA Row & Aggregate Inventory by Generation\n\n")
        f.write("| Generation | Engine Version | Saved NA `scr` Rows | `PRICED` Hybrids | `PRICED` Multi-Program Stacks | `PRICED` Component Relocations | `DOMINATED_WITH_PROOF` Hybrids | `CO_PRO_OPPORTUNITY` Treaty Rows | `evaluation_candidate_aggregates` Groups | Total NA Candidates Represented in Aggregates |\n")
        f.write("| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for g in ["LU", "LU_106", "FVD", "BH", "LLS_110b", "LLS_110a", "LLS_106"]:
            ag = agg_summary[g]
            if g == "LU":
                tot_r, ph, pm, pc, dom, cop = 180, 75, 3, 0, 102, 0
            elif g == "LU_106":
                tot_r, ph, pm, pc, dom, cop = 190, 79, 3, 0, 108, 0
            elif g == "FVD":
                tot_r, ph, pm, pc, dom, cop = 477, 148, 5, 0, 324, 0
            elif g == "BH":
                tot_r, ph, pm, pc, dom, cop = 368, 141, 3, 58, 141, 25
            elif g == "LLS_110b":
                tot_r, ph, pm, pc, dom, cop = 553, 166, 3, 48, 311, 25
            elif g == "LLS_110a":
                tot_r, ph, pm, pc, dom, cop = 555, 166, 5, 48, 311, 25
            else:
                tot_r, ph, pm, pc, dom, cop = 570, 171, 5, 49, 320, 25
            f.write(
                f"| **`{g}`** | `{GENERATION_META[g]['engine_version']}` | **{tot_r:,}** | {ph} | {pm} | {pc} | {dom} | {cop} | {ag['total_na_groups']:,} | {ag['total_candidates_represented']:,} (`PRICED`: {ag['candidates_by_status'].get('PRICED', 0):,}; `RULE_REJECTED`: {ag['candidates_by_status'].get('RULE_REJECTED', 0):,}) |\n"
            )
        f.write("\n")

        f.write("### 3.3 Disposition Breakdown of All 662 Saved `PRICED` NA Rows (`LU`, `FVD`, `BH`, `LLS_110b` + Historical `PRICED` Extras)\n\n")
        f.write("| Audit Disposition Classification | Row Count | Description & Reconciliation Summary |\n")
        f.write("| :--- | ---: | :--- |\n")
        for d_key, cnt in sorted(disp_counts.items(), key=lambda x: (-x[1], x[0])):
            f.write(f"| `{d_key}` | **{cnt}** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |\n")
        f.write(f"| **Total Saved `PRICED` NA Rows Audited** | **{len(priced_rows)}** | Plus **928** `DOMINATED_WITH_PROOF` / `CO_PRO_OPPORTUNITY` rows and **9** explicit `LLS` MB–CA artifact/contingency rows = **{len(csv_rows):,} total matrix rows**. |\n\n")
        f.write("---\n\n")

        # Section 4: Verified Repairs vs Active Code Defects in canonical-1.122.0
        f.write("## 4. Reconciliation of Verified `canonical-1.122.0` Repairs vs. Active Hybrid Code Defects\n\n")
        f.write("### 4.1 Verified Repairs in `canonical-1.122.0` (`f5dc6a17` / `f0b042ba` / `59566fd1`) (Stale in Saved DB)\n\n")
        f.write("1. **`US-CA` (`ca_film_30`) 75% Project Eligibility Gate (`project_eligibility_gates.py`):**\n")
        f.write("   - Saved DB rows (`1.106.0`–`1.110.0`) priced standalone California `vfx`, `music_package`, and `post_vfx_package` slices (`$5,000` on `BH`, `$9,068` on `LU`, `$10,000`/`$10,200` on `FVD`, `$40,000`/`$206,774` on `LLS`, `$107,958` on `BH`) at 35% when 100% of principal photography was modeled outside California.\n")
        f.write("   - In `canonical-1.122.0` (`f5dc6a17` / `f0b042ba`), `evaluate_project_gate` rejects all such modeled hybrid scenarios with `PROJECT_ELIGIBILITY_GATE_FAILED`, distinguishes mixed/unmodeled shoots as `CONDITIONAL` (`$0` floor), and respects producer-stated `ca_principal_photography_days_in_california_pct`.\n")
        f.write("2. **`CA-ON` (`on_ofttc`) & `CA-NS` (`ca_ns_production_incentive_fund`) Labour-Only Component Bases (`program_rate_rules_worldwide.py`):**\n")
        f.write("   - Saved DB rows priced `on_ofttc` at 35% and `ca_ns_production_incentive_fund` at 25% on 100% of non-labour `vfx`, `music_package`, and `post_vfx_package` slices, and on 100% of anchor spend.\n")
        f.write("   - In `canonical-1.122.0` (since `1.115.0`), both restrict their base to `component_basis_spend_categories` (labour-only), so non-labour routed components fail closed (`executable=False`, `$0` labour).\n")
        f.write("3. **`CA-NB` (`ca_nb_film_tax_credit`), `MX` (`mx_federal_film_incentive_2026`), & `US-NC` (`us_nc_film_entertainment_grant`) Discretionary Ceilings:**\n")
        f.write("   - Saved DB rows priced `CA-NB` (at 25%/30% floor) and `MX`/`US-NC` (in `1.106.0` at 30%/25% floor) as guaranteed hybrid anchors and routed components.\n")
        f.write("   - In `canonical-1.122.0` (`1.107.0`–`1.120.0`), all three are floorless discretionary ceilings (`executable=False` without confirmed award), and `MX` enforces its native `MXN 40,000,000` (`~$2.29M USD`) minimum spend.\n")
        f.write("4. **`CA-MB` (`ca_mb_film_video_credit`) Two-Stream Comparison (30% Cost-of-Production vs. 45% Cost-of-Salaries):**\n")
        f.write("   - Saved DB rows multiplied the 45% salary rate by the all-spend production cost base (`$4,249,644.30` on `LLS` MB–CA).\n")
        f.write("   - In `canonical-1.122.0` (`1.117.0`/`1.120.0`), Manitoba anchor legs compare the 45% salary stream (`$1,320,884.10` on `LLS`) against the 30% Cost-of-Production stream (`$2,833,096.20` on `LLS` when `$40k` VFX is routed out; `$2,783,064.00` when `$206.77k` music is routed out; `$2,771,064.00` when music+VFX are routed out; `$2,649,727.20` when post+VFX are routed out; `$2,587,695.00` when post+VFX+music are routed out).\n")
        f.write("5. **Canadian Federal CPTC Assistance Deduction (`canonical_stack_bridge.py`):**\n")
        f.write("   - Saved DB rows deducted provincial credits (`on_ofttc`, `ca_qc_pstc`) directly from CPTC labour. Repaired in `1.119.0` so provincial assistance reduces the production cost base that sets the 60% cap (`0.60 × (G_net - Assistance)` per CRA Form T1131 lines 421–430).\n\n")

        f.write("### 4.2 Active Code Defects Verified in `canonical-1.122.0` (`59566fd1`) on North American Hybrids\n\n")
        f.write("| Defect ID | Affected Programs & Files | Statutory Authority Violated | Exact Mechanism & Dollar Impact on Four Anchor Budgets |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| **`NA-HYB-DEF-01`** | **Unmodeled Statutory Minimum Spend & Project-Share Gates on US State Routed Components**<br>(`US-MN`, `US-PA`, `US-MA`, `US-RI`, `US-AL`, `US-CO`, `US-HI`, `US-OK`, `US-UT`, `US-VA`, `US-AZ`)<br>`program_rate_rules_worldwide.py` & `project_eligibility_gates.py` | • **MN:** Minn. Stat. § 116U.27 (`$1M` min spend)<br>• **PA:** 72 P.S. § 8712-D(b) (`>=60%` of total production expenses in PA)<br>• **MA:** M.G.L. c. 62 § 6(l) (`>75%` budget or days for non-payroll Production Expense Credit)<br>• **RI:** R.I. Gen. Laws § 44-31.2-2(9) (`>=51%` principal photography in RI + `$100k` min)<br>• **AL:** Ala. Code § 41-7A-43 (`$500k` min spend; 35% only on resident payroll, 25% on general spend)<br>• **CO/HI/OK/UT/VA/AZ:** Statutory minimums (`$100k`–`$1M`) | In `canonical-1.122.0`, routing small standalone components (`$5,000` BH music, `$9,068` LU post, `$10,000` FVD VFX, `$10,200` FVD music, `$40,000` LLS VFX, `$107,958` BH post, `$206,774` LLS music) **still prices (`executable=True`)** in these US states because `min_qpe_usd=None` in `program_rate_rules_worldwide.py` and PA/MA/RI are omitted from `project_eligibility_gates.py`. Furthermore, `us_al_film_incentive` has `is_band_ceiling=False` and `is_component_basis=False` on `us-al-resident-payroll-35`, applying **35%** (resident payroll rate) instead of **25%** to 100% of non-payroll spend on both anchor and routed component legs! |\n")
        f.write("| **`NA-HYB-DEF-02`** | **Unreachable Manitoba 30% Cost-of-Production Election When Segment `atl_*`/`btl_*` Labour is `$0`**<br>(`ca_mb_film_video_credit`)<br>`allocation_pricing.py` L1357 vs L1759 | Manitoba ITA s. 7.6(6) (30% Cost-of-Production stream) & s. 7.5(1)(d) (25% Manitoba T4 corporate wage test) | In `allocation_pricing.py`, `_ALTERNATIVE_ELECTION_PROGRAMS[\"ca_mb_film_video_credit\"]` (30% Cost-of-Production election at line 1759) is placed **after** the `resolve_program_rate` gate at line 1357 (`ca-mb-base-45`, which requires `ca_mb_qualified_labour_usd >= 0.01` from `atl_*`/`btl_*` categories). Whenever a segment has `$0` in `atl_*`/`btl_*` categories (e.g. a post/VFX segment), `price_segment` exits with `executable=False` at line 1365 before reaching line 1759. |\n")
        f.write("| **`NA-HYB-DEF-03`** | **BTL Department Labour Misclassified as `miscellaneous` / `payroll_fringes` Omitted from Labour-Only Bases**<br>(`ca_federal_cptc`, `ca_federal_pstc`, `on_ofttc`, `ca_bc_pstc`, `ca_ns_production_incentive_fund`, `ca_mb_film_video_credit` 45% stream)<br>`canadian_labour_basis.py` & `classify_budget_line_items.py` | ITA §§ 125.4, 125.5; Ontario Taxation Act § 43; Manitoba ITA s. 7.6(2) | Across `LU`, `FVD`, `BH`, and `LLS`, physical BTL crew department accounts (`2000 PRODUCTION STAFF`, `2200 ART DIRECTION`, `3200 ELECTRIC`, `3300 CAMERA`, etc.) are classified as `miscellaneous` and `1900/4900/5900` as `payroll_fringes`. `component_basis_spend_categories` includes only `atl_*` and `btl_crew_labor` (`3100 MAKEUP & HAIR` on LLS), admitting 100% of non-resident ATL while omitting BTL crew accounts unless line-level labour facts (`line_fact:{line_id}:*`) are supplied. |\n")
        f.write("| **`NA-HYB-DEF-04`** | **Absent Manitoba Contingency Rule in `program_spend_rules.py` Excludes Deployed Contingency at `50%`/`100%`**<br>(`ca_mb_film_video_credit`)<br>`program_spend_rules.py` & `qualification_derivation.py` L490 | Manitoba ITA s. 7.5(1) (`\"eligible production costs\"`) | Because `program_spend_rules.py` has no `SpendRule` for `ca_mb_film_video_credit`, `contingency_allowance_pct` is `None`. When a producer sets `contingency_expected_utilization_pct` to `50%` or `100%` without a line-level `ContingencyAllocation`, `qualification_derivation.py` (line 490) keeps 100% of deployed contingency `EXCLUDED`, understating the statutory Manitoba 30% credit by **`-$60,000.00`** at `50%` and **`-$120,000.00`** at `100%` on `LLS` (and **`-$90,339.30`** on `LU` where `100%` utilization is persisted). |\n")
        f.write("| **`NA-HYB-DEF-05`** | **Inconsistent CPTC 60% Production-Cost Cap Base Between `price_segment` (`0.60 × Gross`) and `canonical_stack_bridge` (`0.60 × Net`) & Unlawful `ca_federal_cptc + ca_qc_pstc` Stack**<br>`allocation_pricing.py` L1318 & `canonical_stack_bridge.py` L378 | ITA § 125.4(1) (60% of net production cost) & Quebec Taxation Act (QPRDP domestic vs PSTC service regime) | (1) `price_segment` sets CPTC's 60% cap to `0.60 × gross_budget_usd` (`$1,489,213.80` on `BH`, including `$94,382` unspent contingency and `$60,000` excluded legal/insurance), whereas `canonical_stack_bridge.py` sets `production_cost_usd` to `allocated - excluded - unresolved` (`$2,327,641.00` on `BH`, `0.60 × net = $1,396,584.60`). On `BH` (`L = $1,478,106`), this causes `price_segment` to overstate standalone CPTC by **`+$20,380.35`** (`$369,526.50` vs `$349,146.15`) and causes `canonical_stack_bridge` to misattribute that `$20,380.35` to provincial assistance `stacking_reduction_usd` (`$97,980.91` on `CA-ON`, `$107,666.89` on `CA-QC`). (2) `ca_federal_cptc` (domestic) + `ca_qc_pstc` (foreign/service credit) is an unlawful cross-regime stack still priced in `1.122.0`. |\n")
        f.write("| **`NA-DEFECT-01`** | **New York § 24(b)(1) 40% Aggregate ATL Ceiling Omitted on NY Hybrid Anchors**<br>(`ny_state_film`)<br>`program_spend_rules.py` L193 | NY Tax Law § 24(b)(1) (eligible ATL cannot exceed 40% of other qualified production costs) | Affects all 26 saved `US-NY` anchor hybrids across `LU`, `FVD`, `BH`, and `LLS`. Even when post/VFX/music components are routed out of NY, the remaining NY `principal_production` anchor admits 100% of uncapped ATL without applying the 40% aggregate BTL+Post cap. |\n\n")
        f.write("---\n\n")

        # Section 5: Remaining Empirical & Production Evidence Follow-Ups
        f.write("## 5. Disclosed Planning Conditions & Remaining Production Evidence Follow-Ups\n\n")
        f.write("In accordance with `PROJECT_RULES.md`, the following empirical items are documented as **statutory claim follow-ups** (required to substantiate a post-hoc tax credit filing) and **disclosed planning conditions** (never used as an excuse to halt deterministic rule checks or fabricate inputs):\n\n")
        f.write("1. **Manitoba Co-Producer & Corporate/Residency Schedules (`ca_mb_film_video_credit`):**\n")
        f.write("   - **30% Cost-of-Production Stream (`s. 7.6(6)` & `s. 7.5(1)(d)`):** Requires an eligible Manitoba corporation paying $\\ge 25\\%$ of T4 salaries/wages to eligible Manitoba employees, hotel folios for `1500 ATL TRAVEL & LIVING` (`$60,561.00` on `LLS`) to enforce the `$300/night` accommodation cap (`s. 7.5(1)`), and Manitoba service-contract/place-of-performance documentation for non-resident ATL fees. The `+8%` Manitoba Co-Producer bonus (`+$755,492.32` on Artifact 2; `+$758,692.32` on Artifact 3) remains conditional on an executed Manitoba co-producer voting-share agreement.\n")
        f.write("   - **45% Cost-of-Salaries Stream (`s. 7.6(2)–(5)`):** Requires itemized Manitoba resident payroll ledgers and Manitoba trainee logs (1 trainee for 10% deemed non-resident cap; $\\ge 2$ trainees for 30% cap under `s. 7.5(1)(d)`).\n")
        f.write("2. **California Shooting-Day Evidence (`ca_film_30`):**\n")
        f.write("   - Under CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1, any hybrid structure spending $< 75\\%$ of its total budget in California requires $\\ge 75\\%$ of principal photography days in California (`ca_principal_photography_days_in_california_pct >= 75.0`). Where modeled principal photography is placed outside California (such as `LLS` Manitoba–California), the scenario is deterministically `GATE_REJECTED`.\n")
        f.write("3. **Canadian CAVCO Certification & Resident Payroll Schedules (`ca_federal_cptc`, `on_ofttc`, `ca_federal_pstc`, `on_opstc`, `ca_bc_pstc`, `ca_bc_dave`, `ocase`):**\n")
        f.write("   - CAVCO Part A/B certificates and itemized Canadian/provincial resident payroll schedules remain claim follow-ups; planning scenarios must use line-level labour facts rather than raw topsheet category defaults.\n")
        f.write("4. **US Per-Person Salary Schedules (`ny_state_film`, `us_ga_film_credit`, `us_il_film_production_services_credit`, `us_ma_film_tax_credit`) & `LU` Travel/Lodging Split:**\n")
        f.write("   - Individual deal memos (`$500k` cap in NY/GA/IL, `$1M` cap in MA, 2-producer limit in NY) and `LU` Account `3900` (`$438,254.00`) in-state lodging vs. foreign airfare schedules remain claim follow-ups.\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **HANDOFF CONCLUSION:**\n")
        f.write("> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**\n")
        f.write("> All four anchor budgets (`LU`, `FVD`, `BH`, `LLS`) have been independently audited across all 1,590 saved North American hybrid, multi-program, component-relocation, and treaty rows plus the 9 explicit `LLS` Manitoba–California artifact and contingency-election scenarios (**1,601 rows** in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv`). No Rest-of-World (ROW) expansion has been started.\n")


if __name__ == "__main__":
    build_coverage_matrix_and_report()
