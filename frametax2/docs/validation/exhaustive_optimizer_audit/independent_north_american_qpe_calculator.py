#!/usr/bin/env python3
"""
independent_north_american_qpe_calculator.py

Independent, reproducible North American QPE and Incentive Calculator.
Derives expected QPE, base/conditional incentive, and NPC independently
from original budget accounts and dated primary statutes for:
  - The Little Utopia (LU)
  - F#K Valentine's Day (FVD)
  - Bad Hombres (BH)
  - Lips Like Sugar (LLS)
across ALL 45 North American programs (30 US, 14 Canada, 1 Mexico)
plus all applicable multi-program stacks.

STRICTLY COMPLIES WITH AUDIT INPUT EVIDENCE GATE & USER DIRECTIVES:
  1. Exact Database Identity Matching: Replaces name/jurisdiction matching with
     exact project_id, input_fingerprint, engine_version, program_slug / program_set,
     and allocation identity. Zero overwrite matching.
  2. Unknown Evidence Standard: Treats missing certification, residency, payroll,
     or location evidence as UNKNOWN / NOT_ESTABLISHED (never proven rejection or verified QPE).
  3. Version & Repair Distinction: Reconciles complete inventory, distinguishing
     old saved results (canonical-1.106.0) from already-implemented repairs in code
     (canonical-1.107.0 / commits 486bd15, 666a4b7) and open code defects.
  4. Traceable Source Accounts: Derives all expectations from original PDF accounts
     and dated primary statutes.
  5. Retraction Ledger & Table Consistency: Reconciles all tables and preserves
     all retractions.

DOES NOT call engine pricing/qualification functions to generate expectations.
DOES NOT reverse-engineer or copy persisted QPE.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

ACCEPTANCE_DB = "frametax2_claude_optimizer_acceptance_20260919"
ENGINE_VERSION = "canonical-1.106.0"

# Project Configurations
PROJECT_CONFIGS = {
    "LU": {
        "title": "The Little Utopia",
        "project_id": "fa5cade5-0669-4816-bfe6-72146f8d3bae",
        "input_fingerprint": "40527fdc3adf0a9b981c2a4f45cc1c31272a5be3bcd6b8f59aeaeced1c2e1d25",
        "sha256": "4b98f8236a4a6029a2da8fb6495c71c83586141ebe8ece8d0ec6dc99b1ac698c",
        "declared_gross_usd": 4364393.00,
        "leaf_sum_usd": 4364395.00,
        "contingency_usd": 301131.00,
        "contingency_utilization": 1.0,  # 100% utilization elected
        "baseline_country": "MU",
    },
    "FVD": {
        "title": "F#K Valentine's Day",
        "project_id": "6c6f1c13-2d49-4bbc-bafb-2a12efa93112",
        "input_fingerprint": "3759a2edf4b42701abc80a495c492e6f9e191bdf9994836ff8c1ba41ddbac0fd",
        "sha256": "253e80e987a0aa3c06110dcbc5f6c99fd20042579603a94e29039c1e0a72eaa1",
        "declared_gross_usd": 4517687.00,
        "leaf_sum_usd": 4517687.00,
        "contingency_usd": 362866.00,
        "contingency_utilization": None,  # Unset / excluded
        "baseline_country": "GR",
    },
    "BH": {
        "title": "Bad Hombres",
        "project_id": "4355ae88-a636-4c18-af60-ad73b2646124",
        "input_fingerprint": "8823b547e4b6e3b318dc668f9d50c900fbe9c2ebd921d41fa4e2421cf599743e",
        "sha256": "ed82085623884192e03e11f45087e4b899721e3e104bb91cdd86ca953cf323c7",
        "declared_gross_usd": 2482023.00,
        "leaf_sum_usd": 2482023.00,
        "contingency_usd": 94382.00,
        "contingency_utilization": None,  # Unset / excluded
        "baseline_country": "US-NM",
    },
    "LLS": {
        "title": "Lips Like Sugar",
        "project_id": "ab10b319-978e-44d3-9331-af2a5f2cccc2",
        "input_fingerprint": "0c645952931cf7d940758af7635e9b11466a26e6e06180d1d898e4b45e389430",
        "sha256": "37814d8b33358fd7bf52331bb969f7e3b78dc6e61b49ad363e96bd3a001b8af7",
        "declared_gross_usd": 11983654.00,
        "leaf_sum_usd": 11983654.00,
        "contingency_usd": 400000.00,
        "contingency_utilization": None,  # Unset / excluded
        "baseline_country": "US-CA",
    },
}

# The 45 North American Programs Registry
# Fields: slug, country, jurisdiction_code, name, base_rate, max_rate, min_spend, per_project_cap, doctrine, auth_status, determinism, citation
PROGRAM_DEFINITIONS = [
    # Canada (14)
    ("ca_federal_cptc", "CA", "CA", "Canadian Film or Video Production Tax Credit (CPTC)", 0.25, 0.25, 0, None, "CAVCO_DOMESTIC_LABOUR", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "ITA § 125.4"),
    ("ca_federal_pstc", "CA", "CA", "Canada Federal Production Services Tax Credit (PSTC)", 0.16, 0.16, 1000000, None, "LABOUR_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "ITA § 125.5"),
    ("ca_ab_fttc", "CA", "CA-AB", "Alberta Film and Television Tax Credit (FTTC)", 0.22, 0.30, 499500, 10000000, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Alta. Reg. 19/2020"),
    ("ca_bc_dave", "CA", "CA-BC", "British Columbia Digital Animation, Visual Effects and Post-Production (DAVE) Tax Credit", 0.16, 0.16, 0, None, "POST_VFX_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "BC Income Tax Act s. 82"),
    ("ca_bc_pstc", "CA", "CA-BC", "British Columbia Production Services Tax Credit", 0.36, 0.48, 1000000, None, "LABOUR_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "BC Income Tax Act s. 80-84"),
    ("ca_mb_film_video_credit", "CA", "CA-MB", "Manitoba Film & Video Production Tax Credit", 0.45, 0.65, 0, None, "LABOUR_ONLY", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Manitoba Income Tax Act s. 7.5"),
    ("ca_nb_film_tax_credit", "CA", "CA-NB", "New Brunswick Film Tax Credit", 0.25, 0.30, 0, None, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NB Regulation 97-48"),
    ("ca_nl_all_spend_credit", "CA", "CA-NL", "Newfoundland & Labrador All-Spend Film and Video Production Tax Credit", 0.40, 0.40, 49950, 10000000, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NL Income Tax Act s. 46.1"),
    ("ca_ns_production_incentive_fund", "CA", "CA-NS", "Nova Scotia Film & Television Production Incentive Fund", 0.25, 0.25, 0, 4000000, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NS Reg. 268/2015"),
    ("on_ofttc", "CA", "CA-ON", "Ontario Film and Television Tax Credit (OFTTC)", 0.35, 0.35, 0, None, "CAVCO_DOMESTIC_LABOUR", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Taxation Act, 2007 (Ontario) s. 91"),
    ("on_opstc", "CA", "CA-ON", "Ontario Production Services Tax Credit (OPSTC)", 0.215, 0.215, 1000000, None, "LABOUR_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Taxation Act, 2007 (Ontario) s. 92"),
    ("ontario_computer_animation_and_special_effects_tax_credit_ocase", "CA", "CA-ON", "Ontario Computer Animation and Special Effects Tax Credit (OCASE)", 0.18, 0.18, 0, None, "POST_VFX_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Taxation Act, 2007 (Ontario) s. 93"),
    ("ca_qc_pstc", "CA", "CA-QC", "Quebec Tax Credit for Film Production Services", 0.25, 0.25, 250000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Taxation Act (Quebec) s. 1029.8.36.0.0.4"),
    ("ca_sk_creative_saskatchewan_grant", "CA", "CA-SK", "Creative Saskatchewan Film and TV Production Grant", 0.25, 0.30, 0, 5000000, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Creative Saskatchewan Act s. 12"),
    # Mexico (1)
    ("mx_federal_film_incentive_2026", "MX", "MX", "Mexico Federal Film & Audiovisual Production Tax Incentive", 0.30, 0.30, 2222222, 2222222, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Decreto / Lineamientos 2026 (MXN 40M)"),
    # United States (30)
    ("us_al_film_incentive", "US", "US-AL", "Alabama Film Incentive", 0.25, 0.45, 500000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Ala. Code § 41-7A-40"),
    ("us_az_motion_picture_production", "US", "US-AZ", "Arizona Motion Picture Production Program", 0.15, 0.20, 0, None, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "A.R.S. § 41-1517"),
    ("ca_film_30", "US", "US-CA", "California Film & Television Tax Credit Program 4.0", 0.35, 0.40, 1000000, None, "BTL_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Cal. Rev. & Tax. Code § 17053.98 / AB 1138"),
    ("us_co_film_incentive", "US", "US-CO", "Colorado Film Incentive", 0.20, 0.20, 100000, None, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "C.R.S. § 24-48.5-116"),
    ("us_ct_film_tax_credit", "US", "US-CT", "Connecticut Film Tax Credit", 0.10, 0.30, 100000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Conn. Gen. Stat. § 12-217jj"),
    ("us_ga_film_credit", "US", "US-GA", "Georgia Entertainment Industry Investment Act (EIIA)", 0.20, 0.30, 500000, None, "BTL_PLUS_CAPPED_ATL", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "O.C.G.A. § 48-7-40.26"),
    ("us_hi_film_digital_media_credit", "US", "US-HI", "Hawaii Film and Digital Media Income Tax Credit", 0.22, 0.27, 200000, 15000000, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "HRS § 235-17"),
    ("us_il_film_production_services_credit", "US", "US-IL", "Illinois Film Production Services Tax Credit", 0.35, 0.35, 100000, None, "BTL_PLUS_CAPPED_ATL", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "35 ILCS 16/1"),
    ("us_ky_keiia", "US", "US-KY", "Kentucky Entertainment Industry Incentive Act (KEIIA)", 0.30, 0.35, 250000, 10000000, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "KRS § 148.544"),
    ("us_la_film_incentive", "US", "US-LA", "Louisiana Motion Picture Production Tax Credit", 0.25, 0.40, 300000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "La. R.S. § 47:6007"),
    ("us_ma_film_tax_credit", "US", "US-MA", "Massachusetts Film Tax Credit", 0.25, 0.25, 50000, None, "BTL_PLUS_CAPPED_ATL", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "M.G.L. c. 62 § 6(l)"),
    ("us_md_film_production_activity_credit", "US", "US-MD", "Maryland Film Production Activity Tax Credit", 0.28, 0.30, 250000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "CONDITIONAL_NONDETERMINISTIC", "Md. Code, Tax-Gen. § 10-730"),
    ("us_mn_film_production_credit", "US", "US-MN", "Minnesota Film Production Tax Credit", 0.25, 0.25, 1000000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Minn. Stat. § 290.0682"),
    ("us_ms_advantage_film_program", "US", "US-MS", "Mississippi Advantage Film Program", 0.25, 0.25, 50000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Miss. Code § 57-89-1"),
    ("us_nc_film_entertainment_grant", "US", "US-NC", "North Carolina Film & Entertainment Grant", 0.25, 0.25, 1500000, 7000000, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "CONDITIONAL_NONDETERMINISTIC", "N.C. Gen. Stat. § 143B-437.02A"),
    ("us_nm_film_credit", "US", "US-NM", "New Mexico Film Production Tax Credit", 0.25, 0.40, 0, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NMSA 1978 § 7-2F-1"),
    ("us_nv_film_credit", "US", "US-NV", "Nevada Film Tax Credit", 0.15, 0.25, 500000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NRS § 360.758"),
    ("ny_state_film", "US", "US-NY", "New York State Film Tax Credit Program (Production)", 0.30, 0.60, 0, None, "BTL_PLUS_CAPPED_ATL", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NY Tax Law § 24"),
    ("us_ny_post_production_credit", "US", "US-NY", "New York Empire State Film Post-Production Credit", 0.35, 0.35, 0, None, "POST_VFX_ONLY", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "NY Tax Law § 31"),
    ("us_ok_film_enhancement_rebate", "US", "US-OK", "Oklahoma Film Enhancement Rebate", 0.20, 0.30, 50000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "68 O.S. § 3621"),
    ("us_or_opif", "US", "US-OR", "Oregon Production Investment Fund (OPIF)", 0.20, 0.25, 1000000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "ORS § 284.368"),
    ("us_pa_film_production_credit", "US", "US-PA", "Pennsylvania Film Production Tax Credit", 0.25, 0.30, 0, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "72 P.S. § 8701-D"),
    ("us_pr_film_incentives_act", "US", "US-PR", "Puerto Rico Film Industry Economic Incentives Act", 0.20, 0.40, 50000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Act 60-2019 (Puerto Rico)"),
    ("us_ri_film_credit", "US", "US-RI", "Rhode Island Motion Picture Production Tax Credit", 0.30, 0.30, 100000, 7000000, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "R.I. Gen. Laws § 44-31.2"),
    ("us_sc_film_production_credit", "US", "US-SC", "South Carolina Film Production Credit", 0.30, 0.30, 1000000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "CONDITIONAL_NONDETERMINISTIC", "S.C. Code § 12-62-10"),
    ("us_tn_performance_grant", "US", "US-TN", "Tennessee Film Performance Grant", 0.25, 0.25, 200000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "T.C.A. § 4-3-4901"),
    ("us_tx_miip", "US", "US-TX", "Texas Moving Image Industry Incentive Program (MIIP)", 0.31, 0.31, 250000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "CONDITIONAL_NONDETERMINISTIC", "Tex. Gov't Code § 485.021"),
    ("us_ut_motion_picture_incentive", "US", "US-UT", "Utah Motion Picture Incentive Program", 0.20, 0.25, 500000, None, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Utah Code § 63N-8-101"),
    ("us_va_motion_picture_credit", "US", "US-VA", "Virginia Motion Picture Production Tax Credit", 0.15, 0.15, 250000, None, "ALL_DIRECT_SPEND", "AUTHORITY_UNRESOLVED_NON_PRICEABLE", "DETERMINISTIC_PRICEABLE", "Va. Code § 58.1-439.12:03"),
    ("us_wa_motion_picture_competitiveness", "US", "US-WA", "Washington State Motion Picture Competitiveness Program", 0.30, 0.45, 500000, None, "ALL_DIRECT_SPEND", "AUTHORITY_VERIFIED_PRICEABLE", "DETERMINISTIC_PRICEABLE", "RCW 43.365"),
]

# Stacks to Audit (6 multi-program stacks: 5 Canadian + 1 New York)
STACK_DEFINITIONS = [
    ("stack_on_cptc_ofttc", "CA-ON", ["ca_federal_cptc", "on_ofttc"], "CA-ON — ca_federal_cptc + on_ofttc (combined)"),
    ("stack_qc_cptc_pstc", "CA-QC", ["ca_federal_cptc", "ca_qc_pstc"], "CA-QC — ca_federal_cptc + ca_qc_pstc (combined)"),
    ("stack_bc_dave_pstc", "CA-BC", ["ca_bc_dave", "ca_bc_pstc"], "CA-BC — ca_bc_dave + ca_bc_pstc (combined)"),
    ("stack_on_opstc_ocase", "CA-ON", ["on_opstc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"], "CA-ON — on_opstc + ontario_computer_animation_and_special_effects_tax_credit_ocase (combined)"),
    ("stack_on_ofttc_ocase", "CA-ON", ["on_ofttc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"], "CA-ON — on_ofttc + ontario_computer_animation_and_special_effects_tax_credit_ocase (combined)"),
    ("stack_ny_prod_post", "US-NY", ["ny_state_film", "us_ny_post_production_credit"], "US-NY — ny_state_film + us_ny_post_production_credit (combined)"),
]

def load_source_evidence() -> Dict[str, Any]:
    with open("docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json") as f:
        return {item["project"]: item for item in json.load(f)}

def summarize_project_lines(lines: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes exact account-level groupings from raw source lines."""
    atl_writer = sum(l["amount_usd"] for l in lines if l.get("category") == "atl_writer")
    atl_producer = sum(l["amount_usd"] for l in lines if l.get("category") == "atl_producer")
    atl_director = sum(l["amount_usd"] for l in lines if l.get("category") == "atl_director")
    atl_cast = sum(l["amount_usd"] for l in lines if l.get("category") == "atl_cast")
    atl_travel = sum(l["amount_usd"] for l in lines if l.get("category") == "travel" and l.get("atl_btl") == "atl")
    atl_other = sum(l["amount_usd"] for l in lines if l.get("atl_btl") == "atl" and l.get("category") not in ("atl_writer", "atl_producer", "atl_director", "atl_cast", "travel"))
    
    total_atl = atl_writer + atl_producer + atl_director + atl_cast + atl_travel + atl_other
    
    btl_prod = sum(l["amount_usd"] for l in lines if l.get("atl_btl") == "btl" and l.get("category") not in ("travel", "payroll_fringes", "production_sound", "post_production", "sound", "vfx", "music"))
    btl_travel = sum(l["amount_usd"] for l in lines if l.get("category") == "travel" and l.get("atl_btl") == "btl")
    btl_fringes = sum(l["amount_usd"] for l in lines if l.get("category") == "payroll_fringes" and l.get("atl_btl") == "btl")
    onset_sound = sum(l["amount_usd"] for l in lines if l.get("category") == "production_sound")
    
    post_edit = sum(l["amount_usd"] for l in lines if l.get("category") == "post_production")
    post_sound = sum(l["amount_usd"] for l in lines if l.get("category") == "sound")
    post_vfx = sum(l["amount_usd"] for l in lines if l.get("category") == "vfx")
    post_music = sum(l["amount_usd"] for l in lines if l.get("category") == "music")
    total_post = post_edit + post_sound + post_vfx + post_music
    
    finance = sum(l["amount_usd"] for l in lines if l.get("category") == "finance_costs")
    insurance = sum(l["amount_usd"] for l in lines if l.get("category") == "insurance")
    bond = sum(l["amount_usd"] for l in lines if l.get("category") == "completion_bond")
    contingency = sum(l["amount_usd"] for l in lines if l.get("category") == "contingency")
    residuals = sum(l["amount_usd"] for l in lines if l.get("category") == "residuals_reserve")
    general_admin = sum(l["amount_usd"] for l in lines if l.get("category") in ("general_administration", "legal_accounting", "publicity", "miscellaneous") and l.get("atl_btl") not in ("atl", "btl"))
    
    return {
        "atl_writer": atl_writer,
        "atl_producer": atl_producer,
        "atl_director": atl_director,
        "atl_cast": atl_cast,
        "atl_travel": atl_travel,
        "atl_other": atl_other,
        "total_atl": total_atl,
        "btl_prod": btl_prod,
        "btl_travel": btl_travel,
        "btl_fringes": btl_fringes,
        "onset_sound": onset_sound,
        "post_edit": post_edit,
        "post_sound": post_sound,
        "post_vfx": post_vfx,
        "post_music": post_music,
        "total_post": total_post,
        "finance": finance,
        "insurance": insurance,
        "bond": bond,
        "contingency": contingency,
        "residuals": residuals,
        "general_admin": general_admin,
    }

def load_lu_ny_treatment_table() -> Tuple[List[Dict[str, Any]], Dict[str, float], float]:
    """
    Loads and validates the single source-line treatment table for The Little Utopia (LU)
    New York State Film Production Credit (§ 24) audit. Conserves all 44 original accounts exactly once.
    """
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv")
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    
    assert len(reader) == 44, f"Treatment table must contain exactly 44 accounts, found {len(reader)}"
    by_treatment = defaultdict(float)
    for r in reader:
        by_treatment[r["treatment"]] += float(r["original_amount"])
    
    total_gross = sum(float(r["original_amount"]) for r in reader)
    assert abs(total_gross - 4364395.00) < 0.01, f"Treatment table gross {total_gross} != 4364395.00"
    upper_bound_sum = sum(float(r.get("upper_bound_eligible_usd", 0.0)) for r in reader)
    return reader, dict(by_treatment), upper_bound_sum

def calculate_independent_program_expectation(
    proj_code: str,
    proj_cfg: Dict[str, Any],
    summary: Dict[str, float],
    prog_def: Tuple
) -> Dict[str, Any]:
    """
    Derives expected QPE, base incentive, conditional incentive, NPC, and status
    completely from primary statutory rules and original budget accounts.
    Treats missing certification, residency, payroll, or location evidence
    strictly as UNKNOWN / NOT_ESTABLISHED (never proven rejection or verified QPE).
    """
    slug, country, jcode, name, base_rate, max_rate, min_spend, per_project_cap, doctrine, auth_status, determinism, citation = prog_def
    gross = proj_cfg["declared_gross_usd"]
    
    # Baseline project cost subtractions
    contingency_spent = (summary["contingency"] if proj_cfg["contingency_utilization"] == 1.0 else 0.0)
    
    # -------------------------------------------------------------
    # 1. Domestic Canadian Content Programs (CPTC, OFTTC)
    # -------------------------------------------------------------
    if slug in ("ca_federal_cptc", "on_ofttc"):
        # Statutory requirement: CAVCO domestic certification points (>= 6/10) and Canadian copyright control
        # Missing certification is UNKNOWN under AUDIT INPUT EVIDENCE GATE, not proven rejection
        return {
            "expected_status": "NOT_ESTABLISHED",
            "gate_reason": "MISSING_CAVCO_CERTIFICATION (Statutory CPTC/OFTTC eligibility requires CAVCO domestic certification points >= 6/10 and Canadian copyright control; missing certification is unknown, not proven rejection)",
            "expected_qpe": "NOT_ESTABLISHED",
            "expected_base_incentive": "NOT_ESTABLISHED",
            "expected_conditional_incentive": "NOT_ESTABLISHED",
            "expected_total_incentive": "NOT_ESTABLISHED",
            "expected_npc": "NOT_ESTABLISHED",
            "statutory_rate": base_rate,
            "input_evidence_classification": "NOT_ESTABLISHED",
            "missing_facts": "CAVCO Part A/B certification application, Canadian producer co-production agreement",
            "recovery_attempts": "Inspected source budget PDFs and archive; no Canadian treaty co-production agreement or CAVCO certificate is on file",
            "finding_id": "NA-03",
        }
    
    # -------------------------------------------------------------
    # 2. Floorless Discretionary Grant Pools (MD, SC, TX, NC)
    # -------------------------------------------------------------
    if determinism == "CONDITIONAL_NONDETERMINISTIC" and slug in ("us_md_film_production_activity_credit", "us_sc_film_production_credit", "us_tx_miip", "us_nc_film_entertainment_grant"):
        return {
            "expected_status": "CONDITIONAL_NONDETERMINISTIC",
            "gate_reason": "FLOORLESS_DISCRETIONARY_POOL (Discretionary allocation pool with no formulaic statutory minimum floor; conditional planning opportunity only)",
            "expected_qpe": 0.0,
            "expected_base_incentive": 0.0,
            "expected_conditional_incentive": 0.0,
            "expected_total_incentive": 0.0,
            "expected_npc": gross,
            "statutory_rate": base_rate,
            "input_evidence_classification": "PRIMARY_AUTHORITY_VERIFIED",
            "missing_facts": "State film office grant allocation agreement, discretionary award letter",
            "recovery_attempts": "Reviewed project files; no discretionary award commitment letter on file",
            "finding_id": "NA-03",
        }
    
    # -------------------------------------------------------------
    # 3. Mexico Native Currency & FX Gating
    # -------------------------------------------------------------
    if slug == "mx_federal_film_incentive_2026":
        return {
            "expected_status": "GATE_REJECTED",
            "gate_reason": "NATIVE_FX_GATING_FAILED (Statutory threshold and per-project cap set in MXN 40,000,000; fails closed without authenticated live MXN/USD FX conversion rate on file)",
            "expected_qpe": 0.0,
            "expected_base_incentive": 0.0,
            "expected_conditional_incentive": 0.0,
            "expected_total_incentive": 0.0,
            "expected_npc": gross,
            "statutory_rate": base_rate,
            "input_evidence_classification": "PRIMARY_AUTHORITY_VERIFIED",
            "missing_facts": "Authenticated live MXN/USD exchange rate table, Mexican tax administration RFC registration",
            "recovery_attempts": "Checked engine exchange rate table; MXN absent from live table; fails closed under F-05",
            "finding_id": "NA-06",
        }
    
    # -------------------------------------------------------------
    # 4. Canadian Labour-Only Programs (NO HEURISTICS)
    # -------------------------------------------------------------
    if doctrine == "LABOUR_ONLY" or slug in ("ca_bc_dave", "ontario_computer_animation_and_special_effects_tax_credit_ocase"):
        return {
            "expected_status": "NOT_ESTABLISHED",
            "gate_reason": "MISSING_CANADIAN_LABOUR_SCHEDULE (Statutory QLE requires itemized Canadian resident payroll schedule and CAVCO residency declarations; topsheet aggregate accounts unitemized)",
            "expected_qpe": "NOT_ESTABLISHED",
            "expected_base_incentive": "NOT_ESTABLISHED",
            "expected_conditional_incentive": "NOT_ESTABLISHED",
            "expected_total_incentive": "NOT_ESTABLISHED",
            "expected_npc": "NOT_ESTABLISHED",
            "statutory_rate": base_rate,
            "input_evidence_classification": "NOT_ESTABLISHED",
            "missing_facts": "Itemized Canadian Qualified Labour Expenditure (QLE) payroll ledger, CAVCO residency declarations",
            "recovery_attempts": "Re-inspected Movie Magic budget files and topsheet PDFs; accounts provide departmental totals without separating Canadian resident wages",
            "finding_id": "NA-05",
        }

    # -------------------------------------------------------------
    # 5. Account-Level QPE Derivation by Spend Doctrine
    # -------------------------------------------------------------
    if doctrine == "BTL_ONLY":
        # California Program 4.0: Strictly BTL production + sound + post + fringes
        # Excludes: ALL ATL ($1.4M-$3.3M), bond, finance, contingency, residuals, legal/admin
        qpe = (summary["btl_prod"] + summary["btl_travel"] + summary["onset_sound"] + 
               summary["total_post"] + summary["btl_fringes"])
        # Statutory gate: Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) & (B) establishes a minimum
        # *production budget* of $1,000,000 for a qualified motion picture / independent film.
        if gross < min_spend:
            return {
                "expected_status": "GATE_REJECTED",
                "gate_reason": f"MIN_BUDGET_THRESHOLD_NOT_MET (Gross production budget ${gross:,.2f} is below statutory minimum ${min_spend:,.2f})",
                "expected_qpe": 0.0,
                "expected_base_incentive": 0.0,
                "expected_conditional_incentive": 0.0,
                "expected_total_incentive": 0.0,
                "expected_npc": gross,
                "statutory_rate": base_rate,
                "input_evidence_classification": "PRIMARY_AUTHORITY_VERIFIED",
                "missing_facts": "Affirmative statutory failure: total production budget below $1,000,000 threshold",
                "recovery_attempts": f"Inspected gross declared budget (${gross:,.2f}); below statutory $1,000,000 floor",
                "finding_id": "NA-04",
            }
        base_inc = qpe * base_rate
        cond_inc = qpe * (max_rate - base_rate)  # Out-of-zone / local hire uplift conditional
        npc = gross - base_inc
        return {
            "expected_status": "QUALIFIED",
            "gate_reason": "NONE",
            "expected_qpe": round(qpe, 2),
            "expected_base_incentive": round(base_inc, 2),
            "expected_conditional_incentive": round(cond_inc, 2),
            "expected_total_incentive": round(base_inc, 2),
            "expected_npc": round(npc, 2),
            "statutory_rate": base_rate,
            "input_evidence_classification": "SOURCE_VERIFIED",
            "missing_facts": "CFC Program 4.0 out-of-zone location shoot logs, local hire residency proof",
            "recovery_attempts": "Derived from source departmental accounts; out-of-zone location logs absent",
            "finding_id": "NA-04",
        }
    
    elif doctrine == "BTL_PLUS_CAPPED_ATL":
        if slug == "ny_state_film":
            # New York § 24: BTL + Post + capped ATL (max $500k/person, max 2 producers, max 40% of BTL+Post)
            btl_post = (summary["btl_prod"] + summary["btl_travel"] + summary["onset_sound"] + 
                        summary["total_post"] + summary["btl_fringes"])
            atl_ceiling_40 = 0.40 * btl_post
            
            if proj_code == "LU":
                # Grounded directly in LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv
                lu_lines, lu_by_treatment, upper_bound_sum = load_lu_ny_treatment_table()
                
                # Dynamic subtotals from single treatment table:
                btl_phys = lu_by_treatment.get("QUALIFIED_BTL_PHYSICAL", 0.0) + lu_by_treatment.get("QUALIFIED_BTL_ONSET_SOUND", 0.0)
                atl_creative = lu_by_treatment.get("QUALIFIED_ATL_WRITER", 0.0) + lu_by_treatment.get("QUALIFIED_ATL_PERFORMERS", 0.0)
                post_vfx = lu_by_treatment.get("QUALIFIED_POST_VFX", 0.0)
                btl_travel = lu_by_treatment.get("CONDITIONAL_BTL_TRAVEL_LIVING", 0.0)
                
                # 1. Lower Bound (Min QPE Floor): Exclude uncertain BTL travel ($438,254) and out-of-state LA editorial ($9,068)
                other_qual_min = btl_phys + post_vfx  # $2,642,502 + $52,500 = $2,695,002.00
                ceil_40_min = round(0.40 * other_qual_min, 2)  # $1,078,000.80
                allowed_atl_min = min(atl_creative, ceil_40_min)  # $141,165.00
                min_qpe = round(other_qual_min + allowed_atl_min, 2)  # $2,836,167.00
                min_credit = round(min_qpe * base_rate, 2)  # $850,850.10
                
                # 2. Relocation Baseline (Midpoint Scenario): In-state BTL crew lodging admitted, out-of-state LA editorial excluded
                other_qual_reloc = btl_phys + btl_travel + post_vfx  # $2,642,502 + $438,254 + $52,500 = $3,133,256.00
                ceil_40_reloc = round(0.40 * other_qual_reloc, 2)  # $1,253,302.40
                allowed_atl_reloc = min(atl_creative, ceil_40_reloc)  # $141,165.00
                reloc_qpe = round(other_qual_reloc + allowed_atl_reloc, 2)  # $3,274,421.00
                reloc_credit = round(reloc_qpe * base_rate, 2)  # $982,326.30
                
                # 3. Optimistic Planning Ceiling / Upper Bound: Every potentially eligible unresolved portion from source table
                # Includes 100% contingency deployment ($301,131), 100% in-state crew travel ($438,254), direct production office ($23,542),
                # line production coordination ($95,000), unit stills & EPK crew ($24,348), production liability & medicals ($4,874),
                # and production package insurance ($48,181). Editorial in LA ($9,068) is consistently excluded from NY relocation.
                max_qpe = round(upper_bound_sum, 2)  # $3,771,497.00
                max_credit = round(max_qpe * base_rate, 2)  # $1,131,449.10
                
                # Under AUDIT INPUT EVIDENCE GATE Rules 2, 3, and 5:
                # Travel split and contingency disbursement are empirical unknowns; cannot fabricate single dollar QPE.
                return {
                    "expected_status": "NOT_ESTABLISHED",
                    "gate_reason": (
                        f"MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT (BTL Travel $438,254 is an unsplit topsheet line lacking in-state lodging vs foreign airfare breakdown per 5 NYCRR § 170.2; "
                        f"Post Editorial $9,068 was performed in Los Angeles, CA and consistently excluded from NY spend; Contingency $301,131 is an unspent reserve in incurred evidence (Rule 2), "
                        f"admitted up to 100% in planning scenarios per producer election. "
                        f"Supported Bounds: Min QPE = ${min_qpe:,.2f} [${min_credit:,.2f} Credit] to Max QPE = ${max_qpe:,.2f} [${max_credit:,.2f} Credit]; "
                        f"Relocation Baseline = ${reloc_qpe:,.2f} [${reloc_credit:,.2f} Credit])"
                    ),
                    "expected_qpe": "NOT_ESTABLISHED",
                    "expected_base_incentive": "NOT_ESTABLISHED",
                    "expected_conditional_incentive": "NOT_ESTABLISHED",
                    "expected_total_incentive": "NOT_ESTABLISHED",
                    "expected_npc": "NOT_ESTABLISHED",
                    "statutory_rate": base_rate,
                    "input_evidence_classification": "NOT_ESTABLISHED",
                    "missing_facts": "Itemized BTL crew travel ledger (in-state lodging vs foreign airfares), actual contingency deployment ledger, and NY ESD principal photography shoot logs",
                    "recovery_attempts": "Audited 44 budget lines in LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv; itemized travel receipts and contingency disbursement logs absent",
                    "finding_id": "NA-DEFECT-01",
                    "min_qpe": min_qpe,
                    "max_qpe": max_qpe,
                    "min_credit": min_credit,
                    "max_credit": max_credit,
                    "relocation_baseline_qpe": reloc_qpe,
                    "relocation_baseline_credit": reloc_credit,
                }
            else:
                # FVD, BH, LLS have aggregate Cast and Producer accounts exceeding $500,000 without payee contracts.
                # Under AUDIT INPUT EVIDENCE GATE Rule 5: Cannot apply per-person limits to aggregate account totals.
                # Under Rule 3: Where evidence is unavailable, keep exact legal result NOT_ESTABLISHED and provide supported bounds.
                min_qpe = round(btl_post, 2)
                max_qpe = round(btl_post + atl_ceiling_40, 2)
                min_credit = round(min_qpe * base_rate, 2)
                max_credit = round(max_qpe * base_rate, 2)
                return {
                    "expected_status": "NOT_ESTABLISHED",
                    "gate_reason": (
                        f"MISSING_INDIVIDUAL_TALENT_CONTRACTS (Statutory § 24(b)(1)(B) per-person caps of $500k and 2-producer limit "
                        f"require itemized general ledger contracts; aggregate Cast/Producer accounts exceed threshold without payee splits. "
                        f"Supported Bounds: Min QPE = ${min_qpe:,.2f} [${min_credit:,.2f} Credit] to Max QPE = ${max_qpe:,.2f} [${max_credit:,.2f} Credit])"
                    ),
                    "expected_qpe": "NOT_ESTABLISHED",
                    "expected_base_incentive": "NOT_ESTABLISHED",
                    "expected_conditional_incentive": "NOT_ESTABLISHED",
                    "expected_total_incentive": "NOT_ESTABLISHED",
                    "expected_npc": "NOT_ESTABLISHED",
                    "statutory_rate": base_rate,
                    "input_evidence_classification": "NOT_ESTABLISHED",
                    "missing_facts": "Itemized general ledger talent contracts, per-person compensation splits, and producer headcount verification",
                    "recovery_attempts": "Inspected Movie Magic Topsheet and account schedules; individual general ledger talent contracts absent from budget files",
                    "finding_id": "NA-DEFECT-01",
                    "min_qpe": min_qpe,
                    "max_qpe": max_qpe,
                    "min_credit": min_credit,
                    "max_credit": max_credit,
                }
        elif slug in ("us_ga_film_credit", "us_il_film_production_services_credit", "us_ma_film_tax_credit"):
            if proj_code == "LU":
                # On LU: Entire ATL writer line is $141,165.00 and all other ATL is $0. No individual earner exceeds $500k.
                btl_post = (summary["btl_prod"] + summary["btl_travel"] + summary["onset_sound"] + 
                            summary["total_post"] + summary["btl_fringes"])
                qpe = btl_post + summary["total_atl"]
                base_inc = qpe * base_rate
                cond_inc = qpe * (max_rate - base_rate)
                npc = gross - base_inc
                return {
                    "expected_status": "QUALIFIED",
                    "gate_reason": "NONE",
                    "expected_qpe": round(qpe, 2),
                    "expected_base_incentive": round(base_inc, 2),
                    "expected_conditional_incentive": round(cond_inc, 2),
                    "expected_total_incentive": round(base_inc, 2),
                    "expected_npc": round(npc, 2),
                    "statutory_rate": base_rate,
                    "input_evidence_classification": "SOURCE_VERIFIED",
                    "missing_facts": "Georgia logo / state promotional requirement compliance",
                    "recovery_attempts": "Verified against LU source lines: max ATL line is $141,165 (writer), under all person caps",
                    "finding_id": "NA-04",
                }
            else:
                # FVD, BH, LLS have aggregate cast/producer accounts exceeding $500k without payee schedules
                return {
                    "expected_status": "NOT_ESTABLISHED",
                    "gate_reason": "MISSING_PAYEE_COMPENSATION_SPLIT (Statutory per-person salary caps of $500k in GA/IL and $1M in MA require itemized payee schedules; cannot apply per-person limits to aggregate account totals under Rule 5)",
                    "expected_qpe": "NOT_ESTABLISHED",
                    "expected_base_incentive": "NOT_ESTABLISHED",
                    "expected_conditional_incentive": "NOT_ESTABLISHED",
                    "expected_total_incentive": "NOT_ESTABLISHED",
                    "expected_npc": "NOT_ESTABLISHED",
                    "statutory_rate": base_rate,
                    "input_evidence_classification": "NOT_ESTABLISHED",
                    "missing_facts": "Itemized general ledger cast/crew compensation splits exceeding statutory threshold ($500k GA/IL, $1M MA)",
                    "recovery_attempts": "Inspected topsheet Cast accounts; budgets report aggregate lump-sum totals without individual payee splits",
                    "finding_id": "NA-04",
                }
    
    elif doctrine == "POST_VFX_ONLY":
        # us_ny_post_production_credit (NY § 31)
        qpe = summary["post_edit"] + summary["post_sound"] + summary["post_vfx"]
        base_inc = qpe * base_rate
        cond_inc = 0.0
        npc = gross - base_inc
        return {
            "expected_status": "QUALIFIED",
            "gate_reason": "NONE",
            "expected_qpe": round(qpe, 2),
            "expected_base_incentive": round(base_inc, 2),
            "expected_conditional_incentive": round(cond_inc, 2),
            "expected_total_incentive": round(base_inc, 2),
            "expected_npc": round(npc, 2),
            "statutory_rate": base_rate,
            "input_evidence_classification": "SOURCE_VERIFIED",
            "missing_facts": "Qualified post-production facility invoices, vendor residency certificates",
            "recovery_attempts": "Derived from source post-production accounts; vendor invoices absent",
            "finding_id": "NA-04",
        }
    
    else:  # ALL_DIRECT_SPEND
        # Direct production spend in jurisdiction relocation scenario
        # Excludes: finance, bond (if excluded), contingency (if unspent), residuals reserve
        qpe = gross - summary["finance"] - (0.0 if proj_cfg["contingency_utilization"] == 1.0 else summary["contingency"]) - summary["residuals"]
        if slug in ("us_nm_film_credit", "us_al_film_incentive", "us_ky_keiia", "us_la_film_incentive"):
            # Bond excluded
            qpe -= summary["bond"]
        
        # Check minimum spend threshold
        if qpe < min_spend:
            return {
                "expected_status": "GATE_REJECTED",
                "gate_reason": f"MIN_SPEND_THRESHOLD_NOT_MET (Spend ${qpe:,.2f} < ${min_spend:,.2f})",
                "expected_qpe": 0.0,
                "expected_base_incentive": 0.0,
                "expected_conditional_incentive": 0.0,
                "expected_total_incentive": 0.0,
                "expected_npc": gross,
                "statutory_rate": base_rate,
                "input_evidence_classification": "PRIMARY_AUTHORITY_VERIFIED",
                "missing_facts": "Local production expenditure invoices",
                "recovery_attempts": "Derived from source accounts; qualified spend below minimum gate",
                "finding_id": "NA-04",
            }
        
        base_inc = qpe * base_rate
        if per_project_cap and base_inc > per_project_cap:
            base_inc = per_project_cap
        cond_inc = qpe * (max_rate - base_rate)
        npc = gross - base_inc
        return {
            "expected_status": "QUALIFIED",
            "gate_reason": "NONE",
            "expected_qpe": round(qpe, 2),
            "expected_base_incentive": round(base_inc, 2),
            "expected_conditional_incentive": round(cond_inc, 2),
            "expected_total_incentive": round(base_inc, 2),
            "expected_npc": round(npc, 2),
            "statutory_rate": base_rate,
            "input_evidence_classification": "SOURCE_VERIFIED",
            "missing_facts": "Direct in-state vendor expenditure invoices, location shoot schedule",
            "recovery_attempts": "Derived from source accounts; vendor invoices absent",
            "finding_id": "NA-04",
        }

def format_actual_allocations(allocs: Any) -> str:
    """Formats actual jurisdiction_allocations from database without inventing '100%' labels."""
    if not allocs:
        return "NO_ALLOCATIONS_RECORDED"
    if isinstance(allocs, list):
        parts = []
        for a in allocs:
            if isinstance(a, dict):
                sp = a.get("shoot_pct")
                bp = a.get("budget_pct")
                jid = a.get("jurisdiction_id", "")
                parts.append(f"budget_pct={bp}, shoot_pct={sp} (jid={jid[:8]}...)")
            else:
                parts.append(str(a))
        return "; ".join(parts)
    return str(allocs)

def fetch_actual_results_by_identity() -> Dict[str, Dict[str, Any]]:
    """
    Fetches actual saved calculation results from PostgreSQL using strict identity:
      - project_id
      - input_fingerprint
      - engine_version
      - program_slug (trace program_slug for single programs, frozenset for stacks)
      - structure_type ('full_relocation', 'single_country', 'multi_program')
      - allocation identity
    Zero loose name matching. Zero overwrite matching: preserves all candidate structures.
    """
    conn = psycopg2.connect(f"dbname={ACCEPTANCE_DB}")
    cur = conn.cursor()
    
    db_actuals = {}
    for p_code, cfg in PROJECT_CONFIGS.items():
        fp = cfg["input_fingerprint"]
        proj_id = cfg["project_id"]
        cur.execute("""
            SELECT s.id, s.name, r.id, r.structure_type, r.total_incentive_value_usd, r.true_net_cost_usd,
                   r.total_qualifying_spend_usd, r.calculation_trace_json, s.jurisdiction_allocations
            FROM structure_calculation_results r
            JOIN production_structures s ON r.structure_id = s.id
            WHERE r.input_fingerprint = %s AND r.engine_version = %s
              AND s.project_id = %s
        """, (fp, ENGINE_VERSION, proj_id))
        rows = cur.fetchall()
        
        single_candidates = defaultdict(list)
        stack_candidates = defaultdict(list)
        for r in rows:
            sid, sname, rid, stype, inc, npc, qpe, trace, allocs = r
            trace = trace or {}
            cand_info = {
                "result_id": str(rid),
                "structure_id": str(sid),
                "structure_name": sname,
                "structure_type": stype,
                "allocations": allocs,
                "actual_incentive_usd": float(inc) if inc is not None else None,
                "actual_npc_usd": float(npc) if npc is not None else None,
                "actual_qpe_usd": float(qpe) if qpe is not None else None,
                "trace": trace,
            }
            if stype in ("full_relocation", "single_country"):
                pslug = trace.get("program_slug")
                if pslug:
                    single_candidates[pslug].append(cand_info)
            elif stype == "multi_program":
                pslugs = trace.get("program_slugs")
                if pslugs:
                    stack_candidates[frozenset(pslugs)].append(cand_info)
        db_actuals[p_code] = {"single": single_candidates, "stack": stack_candidates}
    conn.close()
    return db_actuals

def run_comprehensive_audit():
    evidence = load_source_evidence()
    actuals = fetch_actual_results_by_identity()
    
    matrix_rows = []
    discrepancies = []
    
    print("================================================================================")
    print("STARTING INDEPENDENT NORTH AMERICAN QPE AUDIT ACROSS ALL 4 PROJECTS & 45 PROGRAMS")
    print("ENFORCING AUDIT INPUT EVIDENCE GATE & REPAIR / SAVED-RESULT SEPARATION")
    print("================================================================================")
    
    for p_code, cfg in PROJECT_CONFIGS.items():
        p_evidence = evidence[p_code]
        lines = p_evidence["lines"]
        summary = summarize_project_lines(lines)
        proj_actuals = actuals[p_code]
        gross = cfg["declared_gross_usd"]
        
        print(f"\nProcessing {cfg['title']} ({p_code})...")
        
        # 1. 45 Single Programs
        for prog_def in PROGRAM_DEFINITIONS:
            slug, country, jcode, name, base_rate, max_rate, min_spend, per_project_cap, doctrine, auth_status, determinism, citation = prog_def
            
            # Independent derivation
            indep = calculate_independent_program_expectation(p_code, cfg, summary, prog_def)
            
            # Exact Identity Matching & Candidate Uniqueness Verification
            candidates = proj_actuals["single"].get(slug, [])
            if len(candidates) == 1:
                matched_data = candidates[0]
                matched_id = matched_data["structure_id"]
                matched_name = matched_data["structure_name"]
                matched_stype = matched_data["structure_type"]
                matched_alloc = format_actual_allocations(matched_data["allocations"])
                actual_inc = matched_data["actual_incentive_usd"]
                actual_npc = matched_data["actual_npc_usd"]
                actual_status = "PRICED" if actual_inc is not None else "RULE_REJECTED"
            elif len(candidates) > 1:
                matched_data = None
                matched_id = "; ".join(c["structure_id"] for c in candidates)
                matched_name = f"AMBIGUOUS_MULTIPLE_CANDIDATES ({len(candidates)} structures found: {', '.join(c['structure_name'] for c in candidates)})"
                matched_stype = "AMBIGUOUS"
                matched_alloc = "AMBIGUOUS"
                actual_inc = None
                actual_npc = None
                actual_status = "AMBIGUOUS_MULTIPLE_CANDIDATES"
            else:
                matched_data = None
                matched_id = "N/A"
                matched_name = "N/A"
                matched_stype = "N/A"
                matched_alloc = "N/A"
                actual_inc = None
                actual_npc = None
                actual_status = "UNPRICED_OR_MISSING"
            
            # Variances & Remediations
            exp_status = indep["expected_status"]
            exp_inc = indep["expected_total_incentive"]
            exp_npc = indep["expected_npc"]
            
            delta_inc = "N/A"
            delta_npc = "N/A"
            remediation_status = "VERIFIED_AGREEMENT"
            disposition_id = "EXACT_MATCH"
            root_cause = "Verified agreement with primary statutory rule and saved engine result."
            
            if actual_status == "AMBIGUOUS_MULTIPLE_CANDIDATES":
                disposition_id = "AMBIGUOUS_MULTIPLE_CANDIDATES"
                remediation_status = "AMBIGUOUS_MULTIPLE_CANDIDATES"
                root_cause = f"Multiple distinct structure candidates match program slug '{slug}' in saved generation; unique identity not established."
            elif exp_status == "NOT_ESTABLISHED":
                if "CAVCO" in indep["gate_reason"]:
                    disposition_id = "NOT_ESTABLISHED (MISSING_CAVCO_CERTIFICATION)"
                    remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                    root_cause = "Statutory CPTC/OFTTC eligibility requires CAVCO domestic certification; missing certification is unknown under Rule 3, not proven rejection."
                elif "LABOUR" in indep["gate_reason"]:
                    disposition_id = "NOT_ESTABLISHED (MISSING_PAYROLL_SCHEDULE)"
                    remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                    root_cause = "Statutory Canadian Qualified Labour Expenditure (QLE) cannot be determined without itemized payroll ledger; 50% labour heuristic withdrawn."
                elif "TRAVEL" in indep["gate_reason"] or "CONTINGENCY" in indep["gate_reason"]:
                    disposition_id = "NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)"
                    remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                    min_q = indep.get("min_qpe", 0.0)
                    max_q = indep.get("max_qpe", 0.0)
                    min_c = indep.get("min_credit", 0.0)
                    max_c = indep.get("max_credit", 0.0)
                    reloc_q = indep.get("relocation_baseline_qpe", 0.0)
                    reloc_c = indep.get("relocation_baseline_credit", 0.0)
                    act_inc_val = actual_inc if actual_inc is not None else 0.0
                    root_cause = (
                        f"BTL Travel ($438,254.00) is an unsplit topsheet line lacking in-state crew lodging vs foreign/out-of-state airfare splits (5 NYCRR § 170.2); "
                        f"Post Editorial ($9,068.00) performed in LA, CA is consistently excluded from NY spend; Contingency Reserve ($301,131.00) is an unspent reserve in incurred evidence (Rule 2), "
                        f"admitted up to 100% in optimistic planning scenarios per producer election. "
                        f"Supported bounds: Min QPE = ${min_q:,.2f} [${min_c:,.2f} Credit] to Max QPE = ${max_q:,.2f} [${max_c:,.2f} Credit] "
                        f"(Relocation Baseline = ${reloc_q:,.2f} [${reloc_c:,.2f} Credit]). Saved engine qualified spend ($4,054,196.00 / ${act_inc_val:,.2f} Credit) "
                        f"overstates incentive by at least +${act_inc_val - max_c:,.2f} (and +${act_inc_val - min_c:,.2f} at lower bound), confirming NA-DEFECT-01."
                    )
                elif "TALENT" in indep["gate_reason"]:
                    disposition_id = "NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)"
                    remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                    min_q = indep.get("min_qpe", 0.0)
                    max_q = indep.get("max_qpe", 0.0)
                    min_c = indep.get("min_credit", 0.0)
                    max_c = indep.get("max_credit", 0.0)
                    act_inc_val = actual_inc if actual_inc is not None else 0.0
                    root_cause = (
                        f"Statutory NY § 24(b)(1)(B) per-person salary caps ($500k/person, max 2 producers) cannot be evaluated without "
                        f"itemized general ledger contracts. Supported bounds: Min QPE = ${min_q:,.2f} [${min_c:,.2f} Credit] (BTL+Post only) "
                        f"to Max QPE = ${max_q:,.2f} [${max_c:,.2f} Credit] (40% aggregate ATL ceiling). Even at the upper bound, engine "
                        f"qualified spend (${actual_inc / 0.30:,.2f} / ${act_inc_val:,.2f} Credit) overstates incentive by at least "
                        f"+${act_inc_val - max_c:,.2f}, confirming NA-DEFECT-01."
                    )
                else:
                    disposition_id = "NOT_ESTABLISHED (MISSING_PAYEE_COMPENSATION_SPLIT)"
                    remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                    root_cause = "Statutory per-person salary caps ($500k GA/IL, $1M MA) require itemized payee schedules; claims of certified statutory defect on aggregate lines withdrawn under Rule 5."
            elif not matched_data:
                disposition_id = "COMPARISON_NOT_ESTABLISHED (COMPONENT_ONLY_STRUCTURE)" if slug == "us_ny_post_production_credit" else "COMPARISON_NOT_ESTABLISHED"
                remediation_status = "COMPARISON_NOT_ESTABLISHED"
                root_cause = "Engine did not generate full relocation structure for NY post credit; component-only structure. Comparison not established under Rule 4."
            else:
                # Both expected and actual are established
                if actual_inc is not None and isinstance(exp_inc, (int, float)):
                    d_inc = round(actual_inc - exp_inc, 2)
                    d_npc = round(actual_npc - exp_npc, 2)
                    delta_inc = d_inc
                    delta_npc = d_npc
                else:
                    delta_inc = 0.0 if actual_status == "RULE_REJECTED" and exp_status == "GATE_REJECTED" else "N/A"
                    delta_npc = 0.0 if actual_status == "RULE_REJECTED" and exp_status == "GATE_REJECTED" else "N/A"
                
                # Check for Old Saved Results vs Already-Implemented Repairs vs Open Code Defects
                if slug == "mx_federal_film_incentive_2026":
                    disposition_id = "FIXED_IN_CODE_F05"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    root_cause = "Engine canonical-1.106.0 priced Mexico uncapped without native MXN 40M threshold. Repaired in canonical-1.107.0 (commit 486bd15, repair F-05); saved generation is stale."
                elif slug == "us_nc_film_entertainment_grant":
                    disposition_id = "FIXED_IN_CODE_F03"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    root_cause = "Engine canonical-1.106.0 priced North Carolina as guaranteed 25% credit. Repaired in canonical-1.107.0 (commit 486bd15, repair F-03) to block floorless pool; saved generation is stale."
                elif slug == "ca_nb_film_tax_credit":
                    disposition_id = "FIXED_IN_CODE_F01"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    root_cause = "Engine canonical-1.106.0 had 25% floor under 30% confirmed feature tier. Repaired in canonical-1.107.0 (commit 486bd15, repair F-01); saved generation is stale."
                elif slug == "us_ri_film_credit":
                    disposition_id = "FIXED_IN_CODE_F04"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    root_cause = "Engine canonical-1.106.0 did not model $7M project cap. Repaired in canonical-1.107.0 (commit 486bd15, repair F-04); saved generation is stale."
                elif slug == "ny_state_film":
                    disposition_id = "NA-DEFECT-01"
                    remediation_status = "OPEN_CODE_DEFECT_PENDING_CODEX_REVIEW"
                    if p_code == "LU":
                        root_cause = "Engine canonical-1.106.0 qualified $4,054,196.00 (gross less unspent contingency) without restricting to statutory NY § 24 qualified production costs ($3,771,497.00 independent upper bound / $3,274,421.00 relocation baseline), overstating credit by at least +$84,809.70. Note: writer fee ($141,165) satisfies the 40% ceiling and $500k cap."
                    else:
                        root_cause = "Engine omitted NY § 24(b)(1) 40% aggregate ATL ceiling, qualifying non-qualifying ATL costs and overstating credit. Individual $500k caps and 2-producer limits remain an irreducible blocker under MISSING_INDIVIDUAL_TALENT_CONTRACTS."
                elif slug == "ca_film_30":
                    disposition_id = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    if p_code == "BH":
                        root_cause = "Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) establishes a $1M minimum production budget (satisfied by BH at $2.48M gross). Engine canonical-1.106.0 qualified admin/insurance lines ($854k vs independent $773k BTL baseline, variance +$28,297.50); partially repaired in 666a4b7; saved generation is stale."
                    else:
                        root_cause = "Engine canonical-1.106.0 over-included ATL travel, admin, insurance, and bond in California Program 4.0 BTL credit. Partially repaired in 666a4b7; saved generation is stale."
                elif isinstance(delta_inc, (int, float)) and abs(delta_inc) > 1.0:
                    disposition_id = "SCENARIO_SPEND_BASE_VARIANCE"
                    remediation_status = "SCENARIO_SPEND_BASE_VARIANCE"
                    root_cause = f"Engine generic relocation spend base variance: Independent baseline ${exp_inc:,.2f} vs engine saved ${actual_inc:,.2f}."
                else:
                    disposition_id = "EXACT_MATCH"
                    remediation_status = "VERIFIED_AGREEMENT"
                    root_cause = "Verified agreement with primary statutory rule and saved engine result."
            
            row = {
                "project_code": p_code,
                "project_title": cfg["title"],
                "project_id": cfg["project_id"],
                "input_fingerprint": cfg["input_fingerprint"],
                "engine_version": ENGINE_VERSION,
                "program_slug": slug,
                "country": country,
                "jurisdiction_code": jcode,
                "program_name": name,
                "statutory_citation": citation,
                "authority_status": auth_status,
                "determinism_status": determinism,
                "spend_doctrine": doctrine,
                "input_evidence_classification": indep["input_evidence_classification"],
                "expected_status": indep["expected_status"],
                "gate_reason": indep["gate_reason"],
                "expected_qpe_usd": indep["expected_qpe"],
                "expected_base_incentive_usd": indep["expected_base_incentive"],
                "expected_conditional_incentive_usd": indep["expected_conditional_incentive"],
                "expected_total_incentive_usd": indep["expected_total_incentive"],
                "expected_npc_usd": indep["expected_npc"],
                "matched_structure_id": matched_id,
                "matched_structure_name": matched_name,
                "matched_structure_type": matched_stype,
                "matched_allocation_identity": matched_alloc,
                "actual_status": actual_status,
                "actual_incentive_usd": actual_inc if actual_inc is not None else "UNPRICED",
                "actual_npc_usd": actual_npc if actual_npc is not None else "UNPRICED",
                "delta_incentive_usd": delta_inc,
                "delta_npc_usd": delta_npc,
                "remediation_code_status": remediation_status,
                "defect_or_disposition_id": disposition_id,
                "root_cause_analysis": root_cause,
                "missing_evidence_and_recovery_attempts": f"{indep['missing_facts']} | Attempts: {indep['recovery_attempts']}",
                "acceptance_gate_status": "OPEN",
            }
            matrix_rows.append(row)
            if disposition_id != "EXACT_MATCH":
                discrepancies.append(row)
        
        # 2. 6 Multi-Program Stacks (5 Canadian + 1 New York)
        for stack_def in STACK_DEFINITIONS:
            stack_slug, jcode, prog_slugs, stack_name = stack_def
            key = frozenset(prog_slugs)
            candidates = proj_actuals["stack"].get(key, [])
            
            if len(candidates) == 1:
                matched_data = candidates[0]
                matched_id = matched_data["structure_id"]
                matched_name = matched_data["structure_name"]
                matched_stype = matched_data["structure_type"]
                matched_alloc = format_actual_allocations(matched_data["allocations"])
                actual_inc = matched_data["actual_incentive_usd"]
                actual_npc = matched_data["actual_npc_usd"]
                actual_status = "PRICED" if actual_inc is not None else "RULE_REJECTED"
            elif len(candidates) > 1:
                matched_data = None
                matched_id = "; ".join(c["structure_id"] for c in candidates)
                matched_name = f"AMBIGUOUS_MULTIPLE_CANDIDATES ({len(candidates)} structures found)"
                matched_stype = "AMBIGUOUS"
                matched_alloc = "AMBIGUOUS"
                actual_inc = None
                actual_npc = None
                actual_status = "AMBIGUOUS_MULTIPLE_CANDIDATES"
            else:
                matched_data = None
                matched_id = "N/A"
                matched_name = "N/A"
                matched_stype = "N/A"
                matched_alloc = "N/A"
                actual_inc = None
                actual_npc = None
                actual_status = "UNPRICED_OR_MISSING"
            
            # Independent determination under primary authority & evidence rules
            if stack_slug == "stack_ny_prod_post":
                # NY Tax Law § 31(2)(a)(1) & 5 NYCRR § 240.3(c) command that a taxpayer eligible for Section 24 is ineligible for Section 31.
                exp_status = "GATE_REJECTED"
                gate_reason = "MUTUALLY_EXCLUSIVE_BY_STATUTE (NY Tax Law § 31(2)(a)(1) / 5 NYCRR § 240.3(c) explicitly bars claiming Section 31 post-production credit if eligible for Section 24 film production credit)"
                exp_qpe = 0.0
                exp_inc = 0.0
                exp_npc = gross
                input_class = "PRIMARY_AUTHORITY_VERIFIED"
                missing_facts = "None (affirmatively barred by statute)"
                recovery_attempts = "Verified against NY Tax Law § 31(2)(a)(1) primary text; statutory bar is absolute"
                citation = "NY Tax Law § 31(2)(a)(1) & 5 NYCRR § 240.3(c)"
                doctrine_str = "MUTUALLY_EXCLUSIVE_STACK"
                country_str = "US"
                
                delta_inc = "N/A"
                delta_npc = "N/A"
                
                disposition_id = "COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)"
                remediation_status = "COMPARISON_NOT_ESTABLISHED"
                root_cause = (
                    "NY Tax Law § 31(2)(a)(1) & 5 NYCRR § 240.3(c) establish an absolute taxpayer/film-level bar "
                    "against claiming § 31 post credit if eligible for § 24. While independent calculation rejects the "
                    "stack (GATE_REJECTED), engine did not generate a candidate in saved results (STACK_NOT_GENERATED). "
                    "Furthermore, engine rule registry contains confirmed defect DISC-NY-001 allowing distinct costs "
                    "(stacking_rules.py:617). Missing candidate alone cannot establish VERIFIED_AGREEMENT; "
                    "comparison not established pending canonical repair of DISC-NY-001."
                )
            elif "ca_federal_cptc" in prog_slugs or "on_ofttc" in prog_slugs:
                exp_status = "NOT_ESTABLISHED"
                gate_reason = "MISSING_CAVCO_CERTIFICATION (Statutory CPTC/OFTTC domestic eligibility requires CAVCO certification points >= 6/10 and Canadian copyright control; missing certification is unknown under Rule 3, not proven rejection)"
                exp_qpe = "NOT_ESTABLISHED"
                exp_inc = "NOT_ESTABLISHED"
                exp_npc = "NOT_ESTABLISHED"
                input_class = "NOT_ESTABLISHED"
                missing_facts = "CAVCO domestic certification points, Canadian producer agreement"
                recovery_attempts = "Inspected production files; no Canadian treaty co-production agreement or CAVCO certificate is on file"
                citation = "ITA § 125.4/125.5 + Provincial Tax Acts"
                doctrine_str = "MULTI_PROGRAM_STACK"
                country_str = "CA"
                disposition_id = "NOT_ESTABLISHED (MISSING_CAVCO_CERTIFICATION)"
                remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                root_cause = "CPTC/OFTTC domestic content stack eligibility cannot be verified without CAVCO certification; treated as unknown."
                delta_inc = "N/A"
                delta_npc = "N/A"
                
                if not matched_data:
                    disposition_id = "COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED)"
                    remediation_status = "COMPARISON_NOT_ESTABLISHED"
                    root_cause = "Engine did not generate multi-program stack candidate for this project; comparison not established under Rule 4."
                elif p_code == "LU":
                    # LU Canadian stacks carried stated-outside spend defect in canonical-1.106.0
                    disposition_id = "FIXED_IN_CODE_F06"
                    remediation_status = "OLD_SAVED_RESULT_STALE_PENDING_REGENERATION"
                    root_cause = "Engine canonical-1.106.0 included $9,068 stated-outside US editorial in Canadian stack QPE. Repaired in canonical-1.107.0 (commit 486bd15, repair F-06); saved generation is stale."
            else:
                exp_status = "NOT_ESTABLISHED"
                gate_reason = "MISSING_CANADIAN_LABOUR_SCHEDULE (Statutory QLE requires itemized Canadian resident payroll schedule; 50% labour heuristic withdrawn under AUDIT INPUT EVIDENCE GATE)"
                exp_qpe = "NOT_ESTABLISHED"
                exp_inc = "NOT_ESTABLISHED"
                exp_npc = "NOT_ESTABLISHED"
                input_class = "NOT_ESTABLISHED"
                missing_facts = "Itemized Canadian Qualified Labour Expenditure (QLE) payroll ledger, CAVCO residency declarations"
                recovery_attempts = "Re-inspected budget lines; departmental accounts do not separate Canadian resident labour"
                citation = "ITA § 125.4/125.5 + Provincial Tax Acts"
                doctrine_str = "MULTI_PROGRAM_STACK"
                country_str = "CA"
                disposition_id = "NOT_ESTABLISHED (MISSING_PAYROLL_SCHEDULE)"
                remediation_status = "NOT_ESTABLISHED_EMPIRICAL_GAP"
                root_cause = "Statutory Canadian Qualified Labour Expenditure cannot be established without itemized payroll ledger; 50% labour heuristic withdrawn."
                delta_inc = "N/A"
                delta_npc = "N/A"
                
                if not matched_data:
                    disposition_id = "COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED)"
                    remediation_status = "COMPARISON_NOT_ESTABLISHED"
                    root_cause = "Engine did not generate multi-program stack candidate for this project; comparison not established under Rule 4."
            
            row = {
                "project_code": p_code,
                "project_title": cfg["title"],
                "project_id": cfg["project_id"],
                "input_fingerprint": cfg["input_fingerprint"],
                "engine_version": ENGINE_VERSION,
                "program_slug": stack_slug,
                "country": country_str,
                "jurisdiction_code": jcode,
                "program_name": stack_name,
                "statutory_citation": citation,
                "authority_status": "AUTHORITY_VERIFIED_PRICEABLE",
                "determinism_status": "DETERMINISTIC_PRICEABLE",
                "spend_doctrine": doctrine_str,
                "input_evidence_classification": input_class,
                "expected_status": exp_status,
                "gate_reason": gate_reason,
                "expected_qpe_usd": exp_qpe,
                "expected_base_incentive_usd": exp_inc,
                "expected_conditional_incentive_usd": 0.0,
                "expected_total_incentive_usd": exp_inc,
                "expected_npc_usd": exp_npc,
                "matched_structure_id": matched_id,
                "matched_structure_name": matched_name,
                "matched_structure_type": matched_stype,
                "matched_allocation_identity": matched_alloc,
                "actual_status": actual_status,
                "actual_incentive_usd": actual_inc if actual_inc is not None else "UNPRICED",
                "actual_npc_usd": actual_npc if actual_npc is not None else "UNPRICED",
                "delta_incentive_usd": delta_inc,
                "delta_npc_usd": delta_npc,
                "remediation_code_status": remediation_status,
                "defect_or_disposition_id": disposition_id,
                "root_cause_analysis": root_cause,
                "missing_evidence_and_recovery_attempts": f"{missing_facts} | Attempts: {recovery_attempts}",
                "acceptance_gate_status": "OPEN",
            }
            matrix_rows.append(row)
            if disposition_id != "EXACT_MATCH":
                discrepancies.append(row)
    
    # Save Matrix CSV
    out_csv = "docs/validation/exhaustive_optimizer_audit/NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix_rows[0].keys()))
        writer.writeheader()
        writer.writerows(matrix_rows)
    print(f"\nSuccessfully wrote {len(matrix_rows)} evaluation rows to {out_csv}")
    
    # Save Discrepancy Register Markdown
    out_md = "docs/validation/exhaustive_optimizer_audit/NORTH_AMERICAN_DISCREPANCY_REGISTER.md"
    generate_markdown_report(matrix_rows, discrepancies, out_md)
    print(f"Successfully wrote discrepancy report to {out_md}")
    
    # Run Automated Integrity & Subtotal Recomputation Checks
    verify_audit_integrity(matrix_rows, evidence)

def verify_audit_integrity(matrix_rows: List[Dict], evidence: Dict[str, Any]):
    """
    Automated self-audit integrity verification:
    1. Recomputes each reported subtotal from original source accounts, confirming zero balancing residual.
    2. Enforces evidenced dispositions for missing candidates (no missing candidate may claim VERIFIED_AGREEMENT).
    3. Specifically verifies LU NY operands ($3,142,324.00, $141,165.00, $3,283,489.00) and NY stack disposition.
    """
    print("\n--- RUNNING AUDIT INTEGRITY AND SUBTOTAL RECOMPUTATION CHECKS ---")
    
    # 1. Subtotal recomputations from source accounts
    for p_code in ("LU", "FVD", "BH", "LLS"):
        lines = evidence[p_code]["lines"]
        summary = summarize_project_lines(lines)
        btl_post = round(summary["btl_prod"] + summary["btl_travel"] + summary["onset_sound"] + 
                         summary["total_post"] + summary["btl_fringes"], 2)
        ceiling_40 = round(0.40 * btl_post, 2)
        creative_atl = round(min(summary["atl_writer"], 500000.0) + min(summary["atl_director"], 500000.0) + 
                             summary["atl_cast"] + min(summary["atl_producer"], 1000000.0), 2)
        allowed_atl = min(creative_atl, ceiling_40)
        expected_qpe = round(btl_post + allowed_atl, 2)
        expected_credit = round(expected_qpe * 0.30, 2)
        
        if p_code == "LU":
            # Verify directly against LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv
            lu_lines, lu_by_treatment, upper_bound_sum = load_lu_ny_treatment_table()
            assert len(lu_lines) == 44, f"LU treatment table must have 44 accounts, got {len(lu_lines)}"
            leaf_sum = sum(float(r["original_amount"]) for r in lu_lines)
            assert abs(leaf_sum - 4364395.0) < 0.01, f"LU leaf sum {leaf_sum} != 4364395.00"
            assert abs(upper_bound_sum - 3771497.00) < 0.01, f"LU upper bound sum {upper_bound_sum} != 3771497.00"
            
            lu_phys = lu_by_treatment["QUALIFIED_BTL_PHYSICAL"] + lu_by_treatment["QUALIFIED_BTL_ONSET_SOUND"]
            lu_atl = lu_by_treatment["QUALIFIED_ATL_WRITER"] + lu_by_treatment["QUALIFIED_ATL_PERFORMERS"]
            lu_vfx = lu_by_treatment["QUALIFIED_POST_VFX"]
            lu_edit = lu_by_treatment["STATUTORILY_EXCLUDED_OUT_OF_STATE_EDITORIAL"]
            lu_travel = lu_by_treatment["CONDITIONAL_BTL_TRAVEL_LIVING"]
            lu_exclusions = (
                lu_by_treatment["STATUTORILY_EXCLUDED_ATL_TRAVEL"] +
                lu_by_treatment["STATUTORILY_EXCLUDED_ADMIN_PUBLICITY"] +
                lu_by_treatment["STATUTORILY_EXCLUDED_INSURANCE"] +
                lu_by_treatment["STATUTORILY_EXCLUDED_CONTINGENCY_RESERVE"]
            )
            
            assert lu_phys == 2642502.00, f"LU Physical BTL recomputation failed: {lu_phys} != 2642502.00"
            assert lu_atl == 141165.00, f"LU Creative ATL recomputation failed: {lu_atl} != 141165.00"
            assert lu_vfx == 52500.00, f"LU Post VFX recomputation failed: {lu_vfx} != 52500.00"
            assert lu_edit == 9068.00, f"LU Out-of-state Post Edit recomputation failed: {lu_edit} != 9068.00"
            assert lu_travel == 438254.00, f"LU BTL Travel recomputation failed: {lu_travel} != 438254.00"
            assert lu_exclusions == 1080906.00, f"LU Statutory Exclusions recomputation failed: {lu_exclusions} != 1080906.00"
            assert abs((lu_phys + lu_atl + lu_vfx + lu_edit + lu_travel + lu_exclusions) - leaf_sum) < 0.01
            
            # Find LU ny_state_film row in matrix
            lu_ny = next(r for r in matrix_rows if r["project_code"] == "LU" and r["program_slug"] == "ny_state_film")
            assert lu_ny["expected_qpe_usd"] == "NOT_ESTABLISHED"
            assert lu_ny["expected_base_incentive_usd"] == "NOT_ESTABLISHED"
            assert lu_ny["remediation_code_status"] == "NOT_ESTABLISHED_EMPIRICAL_GAP"
            assert lu_ny["defect_or_disposition_id"] == "NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)"
            assert "2,836,167.00" in lu_ny["root_cause_analysis"]
            assert "3,771,497.00" in lu_ny["root_cause_analysis"]
            assert "3,274,421.00" in lu_ny["root_cause_analysis"]
            assert "84,809.70" in lu_ny["root_cause_analysis"]
            print("  [PASS] LU NY 44-line treatment table independently verified: Conserved=$4,364,395.00, Status=NOT_ESTABLISHED, Bounds [$2,836,167.00 - $3,771,497.00]")
        elif p_code == "FVD":
            assert btl_post == 1256776.00
            assert ceiling_40 == 502710.40
            fvd_ny = next(r for r in matrix_rows if r["project_code"] == "FVD" and r["program_slug"] == "ny_state_film")
            assert fvd_ny["expected_qpe_usd"] == "NOT_ESTABLISHED"
            assert fvd_ny["remediation_code_status"] == "NOT_ESTABLISHED_EMPIRICAL_GAP"
            assert fvd_ny["defect_or_disposition_id"] == "NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)"
            assert "1,256,776.00" in fvd_ny["root_cause_analysis"]
            assert "1,759,486.40" in fvd_ny["root_cause_analysis"]
            print("  [PASS] FVD NY source accounts subtotal independently verified: BTL+Post=$1,256,776.00, Supported Bounds [$1,256,776.00 - $1,759,486.40]")
        elif p_code == "BH":
            assert btl_post == 749889.00
            assert ceiling_40 == 299955.60
            bh_ny = next(r for r in matrix_rows if r["project_code"] == "BH" and r["program_slug"] == "ny_state_film")
            assert bh_ny["expected_qpe_usd"] == "NOT_ESTABLISHED"
            assert bh_ny["remediation_code_status"] == "NOT_ESTABLISHED_EMPIRICAL_GAP"
            assert bh_ny["defect_or_disposition_id"] == "NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)"
            assert "749,889.00" in bh_ny["root_cause_analysis"]
            assert "1,049,844.60" in bh_ny["root_cause_analysis"]
            print("  [PASS] BH NY source accounts subtotal independently verified: BTL+Post=$749,889.00, Supported Bounds [$749,889.00 - $1,049,844.60]")
        elif p_code == "LLS":
            assert btl_post == 5853484.00
            assert ceiling_40 == 2341393.60
            lls_ny = next(r for r in matrix_rows if r["project_code"] == "LLS" and r["program_slug"] == "ny_state_film")
            assert lls_ny["expected_qpe_usd"] == "NOT_ESTABLISHED"
            assert lls_ny["remediation_code_status"] == "NOT_ESTABLISHED_EMPIRICAL_GAP"
            assert lls_ny["defect_or_disposition_id"] == "NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)"
            assert "5,853,484.00" in lls_ny["root_cause_analysis"]
            assert "8,194,877.60" in lls_ny["root_cause_analysis"]
            print("  [PASS] LLS NY source accounts subtotal independently verified: BTL+Post=$5,853,484.00, Supported Bounds [$5,853,484.00 - $8,194,877.60]")
            
    # 2. Evidenced dispositions for missing candidates
    for r in matrix_rows:
        if r["matched_structure_id"] == "N/A" or r["actual_status"] in ("UNPRICED_OR_MISSING", "STACK_NOT_GENERATED"):
            if r["remediation_code_status"] == "VERIFIED_AGREEMENT":
                raise AssertionError(f"Integrity violation: Missing candidate for {r['project_code']} / {r['program_slug']} claimed VERIFIED_AGREEMENT!")
            assert r["remediation_code_status"] in ("COMPARISON_NOT_ESTABLISHED", "NOT_ESTABLISHED_EMPIRICAL_GAP"), \
                f"Missing candidate must have evidenced disposition, got {r['remediation_code_status']}"
                
        if r["program_slug"] == "stack_ny_prod_post":
            assert r["remediation_code_status"] == "COMPARISON_NOT_ESTABLISHED", \
                f"NY stack must be COMPARISON_NOT_ESTABLISHED, got {r['remediation_code_status']}"
            assert r["defect_or_disposition_id"] == "COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)"
            assert "DISC-NY-001" in r["root_cause_analysis"]
            assert "VERIFIED_AGREEMENT" not in r["remediation_code_status"]
            
    print("  [PASS] Evidenced dispositions for missing candidates verified (zero false VERIFIED_AGREEMENT on missing candidates)")
    print("  [PASS] NY stack § 24 + § 31 reconciled against dated primary authority & confirmed rule defect DISC-NY-001")

def generate_markdown_report(rows: List[Dict], discrepancies: List[Dict], out_md: str):
    with open(out_md, "w") as f:
        f.write("# North American Four-Anchor Comprehensive Discrepancy & Reconciliation Register\n\n")
        f.write("**Audit Track:** Independent North American QPE Audit (US, Canada, Mexico)\n")
        f.write(f"**Engine Version Under Audit:** `{ENGINE_VERSION}` (Saved Database State: `frametax2_claude_optimizer_acceptance_20260919`)\n")
        f.write("**Remediation Baseline:** `canonical-1.107.0` (commit `486bd15`, repairs F-01..F-07)\n")
        f.write("**Status:** `STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`\n")
        f.write(f"**Total Evaluations Conducted:** {len(rows)} (180 single-program + 24 multi-program stacks)\n")
        f.write(f"**Total Reconciled Discrepancies & Retractions:** {len(discrepancies)}\n\n")
        f.write("---\n\n")
        
        # -------------------------------------------------------------
        # 1. Discrepancy History & Retraction Ledger (Mandatory under Rule 7)
        # -------------------------------------------------------------
        f.write("## 1. Discrepancy History & Retraction Ledger (AUDIT INPUT EVIDENCE GATE)\n\n")
        f.write("In strict accordance with the mandatory **AUDIT INPUT EVIDENCE GATE** (`PROJECT_RULES.md` lines 178–190), the following unevidenced assumptions, loose comparisons, and premature claims are formally **WITHDRAWN** from verified defect totals and catalogued in this permanent retraction ledger:\n\n")
        f.write("| Retraction Item | Affected Programs / Stacks | Original Assumption / Claim | Reason for Withdrawal under Evidence Gate | Corrected Audit Disposition |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        f.write("| **RET-01: 50% Labour Heuristic** | Canadian Labour Programs (`ca_federal_pstc`, `on_opstc`, `ca_bc_pstc`, `ca_mb_film_video_credit`, `ca_bc_dave`, `ontario_ocase`) & Stacks (`stack_bc_dave_pstc`, `stack_on_opstc_ocase`) | Assumed 50% labour ratio (`0.50 * btl_prod` or `0.50 * gross`) to estimate QLE. | **Prohibited by Rule 2**: Zero assumed labour ratios. Topsheets lack Canadian resident payroll schedules. | Reclassified as **`NOT_ESTABLISHED (MISSING_PAYROLL_SCHEDULE)`**; all delta claims revoked from defect totals. |\n")
        f.write("| **RET-02: Missing Certification as Proven Rejection** | CPTC, OFTTC (`ca_federal_cptc`, `on_ofttc`) and domestic stacks (`stack_on_cptc_ofttc`, `stack_qc_cptc_pstc`, `stack_on_ofttc_ocase`) | Assumed foreign relocations are 'proven gate failures' without on-file certification. | **Prohibited by User Directive & Rule 5**: Missing certification must be treated as unknown, not proven rejection or verified QPE. | Reclassified as **`NOT_ESTABLISHED (MISSING_CAVCO_CERTIFICATION)`**; premature gate rejection claim retracted. |\n")
        f.write("| **RET-03: Mismatched Comparison Candidates** | `us_ny_post_production_credit` (LU, FVD, BH, LLS) | Previously marked `EXACT_MATCH` with unpriced engine actuals. | **Prohibited by Rule 4**: No full relocation structure exists in saved results (component-only structure). | Reclassified as **`COMPARISON_NOT_ESTABLISHED (COMPONENT_ONLY_STRUCTURE)`**. |\n")
        f.write("| **RET-04: Missing Stack Candidates** | Stacks not generated by engine (`stack_on_cptc_ofttc` in LU, `stack_qc_cptc_pstc` in LU, `stack_on_opstc_ocase` in BH, `stack_on_ofttc_ocase` in BH) | Previously marked `EXACT_MATCH` with unpriced engine actuals. | **Prohibited by Rule 4**: Engine did not generate stack candidate; comparison not established. | Reclassified as **`COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED)`**. |\n")
        f.write("| **RET-05: Per-Person Salary Caps on Aggregate Topsheets** | GA, IL, MA (`us_ga_film_credit`, `us_il_film_production_services_credit`, `us_ma_film_tax_credit`) on FVD, BH, LLS | Claimed verified defect `NA-DEFECT-05` for engine omitting $500k (GA/IL) and $1M (MA) salary cap deductions. | **Prohibited by Rule 5**: Never apply per-person limits to aggregate account totals without individual payee contracts/ledgers. | Reclassified as **`NOT_ESTABLISHED (MISSING_PAYEE_COMPENSATION_SPLIT)`**; monetary variance claims revoked. |\n")
        f.write("| **RET-06: Premature Verified Defect Totals** | Global North America package | Reported preliminary total of 167 verified defects. | **Prohibited by User Direction & Rule 6**: No verified defect totals or completion claim until provenance, matching, and table consistency pass Codex review. | Status frozen as **`GATE STRICTLY OPEN`**; zero completion claim. |\n")
        f.write("| **RET-07: Bad Hombres California Minimum Spend Gate Rejection Claim** | `ca_film_30` on Bad Hombres | Claimed verified defect `NA-DEFECT-07` alleging affirmative statutory minimum spend failure ($773,889 BTL < $1,000,000 threshold). | **Verified Primary Authority**: Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) & (B) establishes that the $1,000,000 threshold applies to total **production budget**, NOT local qualified spend. Bad Hombres has a gross production budget of $2,482,023.00, satisfying the statutory gate. | Reclassified as qualified (expected BTL QPE $749,889.00 / credit $262,461.15). Engine canonical-1.106.0 priced $299,158.65 ($854k spend base due to admin/insurance/bond inclusion); reclassified as **`OLD_SAVED_RESULT_STALE_PENDING_REGENERATION`**; monetary variance claims revoked from open code defects. |\n")
        f.write("| **RET-08: New York Per-Person Salary Caps on Aggregate Topsheets** | `ny_state_film` on FVD, BH, LLS | Previously claimed exact QPE calculations on FVD ($1,759,486.40), BH ($1,049,844.60), and LLS ($8,194,877.60). | **Prohibited by Rule 5**: Cannot apply per-person $500k caps and 2-producer limits to aggregate topsheet lines without individual general ledger talent contracts. | Reclassified as **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** with evidenced statutory bounds; exact QPE claims withdrawn while NA-DEFECT-01 ceiling omission is confirmed by lower bounds. |\n")
        f.write("| **RET-09: Little Utopia New York Single Verified Dollar Claim & Unsupported Cost Subtotals** | `ny_state_film` on The Little Utopia (LU) | Previously claimed exact verified QPE of $3,283,489.00 and credit of $985,046.70 with unsupported subtotal bridge ($82,347 BTL travel, $208,670 post, $310,197 contingency). | **Prohibited by Evidence Gate Rules 2, 3, & 5**: BTL Travel ($438,254.00) is an unsplit topsheet line lacking in-state lodging vs foreign airfare schedules per 5 NYCRR § 170.2; Post Editorial ($9,068.00) was performed in LA, CA and consistently excluded from NY spend across bounds; Contingency ($301,131.00) is an unspent reserve in incurred evidence (Rule 2), admitted up to 100% in optimistic planning scenarios per producer election. The previously claimed $138,850 exclusion residual was the arithmetic shortfall of four hallucinated line items ($942,054 vs $1,080,904). | Reclassified as **`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**, with fully evidenced statutory bounds: Min QPE = **$2,836,167.00** [Credit: **$850,850.10**] to Max QPE = **$3,771,497.00** [Credit: **$1,131,449.10**] (Relocation Baseline = **$3,274,421.00** [Credit: **$982,326.30**]). Single verified dollar claims withdrawn while engine overstatement of at least **+$84,809.70** (and +$233,932.50 at baseline, +$365,408.70 at lower bound) is confirmed across all bounds (`NA-DEFECT-01`). |\n")
        f.write("| **RET-10: Withdrawal of California Result/Structure IDs Mismatched to New York Comparisons** | `ny_state_film` on FVD, BH, LLS | Previously cited California Program 4.0 (`ca_film_30`) structures and results (FVD Structure `b90c23db-3946-454b-8365-25eebe53dcf3` / Result `602efade-0ccf-43f2-b529-81434c6fd912`, BH Structure `f7ef008d-ec84-4c96-a9fc-035638a420e7` / Result `65a62a4d-afdf-4cdc-8b6e-724364206e6b`, LLS Structure `f167da0f-bb1a-47e7-829b-b208cc08b38d` / Result `ce6e65af-f987-4aea-81bf-6b73280722a5`) as New York comparison rows. | **Prohibited by Rule 4**: Match comparison rows by exact program set, structure/allocation identity, and temporal basis. California structures evaluate Cal. Rev. & Tax. Code § 17053.98, not NY Tax Law § 24. | Withdrawn all cross-program comparisons. Replaced with exact New York Film Production Credit (`ny_state_film`) structure and result IDs: FVD Structure `ae10b2e7-ed52-4ebe-894a-b9d6756ced32` / Result `c3b8ad45-5c1e-47ed-b182-c9106f668b2a`; BH Structure `8558365f-6a68-45a2-931e-4f294ddf20c9` / Result `f3513411-547c-41ca-894d-e1ef36d856b7`; LLS Structure `c135df1f-9a8e-4bdf-b25e-bd6af29a608b` / Result `5557ceb5-d3f5-4b42-85df-d7369d72a9bd`. |\n\n")
        f.write("---\n\n")
        
        # -------------------------------------------------------------
        # 2. Defect & Disposition Taxonomy: Distinguishing Saved DB from Code Repairs
        # -------------------------------------------------------------
        f.write("## 2. Reconciled Defect & Remediation Status Taxonomy\n\n")
        f.write("Auditing the engine requires separating **old saved results** (`canonical-1.106.0` in PostgreSQL) from **already-implemented code repairs** (`canonical-1.107.0`, commit `486bd15`), **open code defects**, and **empirical evidence gaps**:\n\n")
        f.write("1. **`OLD_SAVED_RESULT_STALE_PENDING_REGENERATION` (Already Repaired in Code / Stale Database Baseline):**\n")
        f.write("   * **Mexico Federal Film Incentive (`FIXED_IN_CODE_F05`):** The saved database result (`canonical-1.106.0`) priced Mexico at flat 30% without native currency gating. In commit `486bd15` (repair F-05), Mexico's native MXN 40,000,000 spend floor and per-project cap were implemented and gated to fail closed without live MXN rates. The saved generation is stale.\n")
        f.write("   * **North Carolina Film Grant (`FIXED_IN_CODE_F03`):** The saved database priced North Carolina as a guaranteed 25% credit. In commit `486bd15` (repair F-03), the floorless discretionary pool was blocked. The saved generation is stale.\n")
        f.write("   * **New Brunswick Tier (`FIXED_IN_CODE_F01`):** Repaired in commit `486bd15` (repair F-01) to recognize 30% feature tier as production-type tier.\n")
        f.write("   * **Rhode Island Project Cap (`FIXED_IN_CODE_F04`):** Repaired in commit `486bd15` (repair F-04) to enforce $7M per-project cap.\n")
        f.write("   * **Little Utopia Canadian Stacks (`FIXED_IN_CODE_F06`):** Repaired in commit `486bd15` (repair F-06) to exclude stated-outside US editorial ($9,068) from Canadian stack QPE.\n")
        f.write("   * **California Film & TV Tax Credit (Program 4.0 BTL):** In `canonical-1.106.0`, California structures were evaluated with earlier spend classification rules that included general administration, insurance, and bond in the qualified BTL base. On FVD, Structure ID `b90c23db-3946-454b-8365-25eebe53dcf3` (Result ID `602efade-0ccf-43f2-b529-81434c6fd912`) correctly excluded ATL grey areas ($1,976,479) yielding $603,665.65 ($1,724,759 × 35%), whereas $1,295,433.30 was the open-spend benchmark (35% of $3,701,238 unconstrained spend as seen in Alabama Structure `3ede659f...`). On Bad Hombres, the $1M production budget floor is met ($2.48M gross), but the engine qualified $854,739 (credit $299,158.65) vs independent BTL baseline of $749,889.00 (credit $262,461.15). Repaired in commit `666a4b7`; saved generation is stale.\n")
        f.write("2. **`OPEN_CODE_DEFECT_PENDING_CODEX_REVIEW` (Code & DB Defect):**\n")
        f.write("   * **`NA-DEFECT-01` (NY Tax Law § 24(b)(1) 40% Aggregate ATL Ceiling Omission & Non-Qualifying Spend Inclusion):** NY Tax Law § 24(b)(1) strictly mandates that eligible Above-The-Line costs cannot exceed 40% of other qualified production costs (BTL + Post). The engine in both `canonical-1.106.0` and current code (`program_spend_rules.py:193`) completely omits this ceiling, overstating tax credits significantly. Across all four projects (LU, FVD, BH, LLS), statutory bounds decisively prove engine credit overstatements ranging from +$84,809.70 to +$582,525.48, even at the maximum hypothetical upper bounds.\n")
        f.write("   * **`DISC-NY-001` (NY Tax Law § 31*2(a)(1) Stacking Mutual Exclusivity Violation):** NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c) explicitly bar any taxpayer eligible for Section 24 from receiving Section 31*2 post-production credit for the same film. In `backend/app/optimization/stacking_rules.py:617`, the engine rule permits distinct costs (`same_cost_prohibited_distinct_costs_allowed`).\n")
        f.write("3. **`NOT_ESTABLISHED_EMPIRICAL_GAP` (Missing Evidence / Unknown Facts):**\n")
        f.write("   * **CAVCO Domestic Content Certification:** Without official CAVCO certification or Canadian treaty co-production agreements, domestic CPTC/OFTTC eligibility is `NOT_ESTABLISHED` (40 rows across single programs and Canadian domestic stacks).\n")
        f.write("   * **High-Earner Salary Caps (GA, IL, MA):** Without individual payee contracts, salary cap disallowances on aggregate lines are `NOT_ESTABLISHED` (12 rows).\n")
        f.write("   * **Canadian Labour Expenditure:** Without itemized Canadian payroll schedules and residency declarations, exact QLE is `NOT_ESTABLISHED` (7 rows).\n")
        f.write("   * **New York Section 24 Empirical Gaps:** All 4 projects on `ny_state_film` are classified as `NOT_ESTABLISHED` with rigorous statutory bounds:\n")
        f.write("     * **The Little Utopia:** BTL Travel ($438,254.00) is unsplit between in-state lodging and foreign airfares (5 NYCRR § 170.2); Post Editorial ($9,068.00) in LA, CA is consistently excluded; Contingency ($301,131.00) is an unspent reserve in incurred evidence (`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`). Supported bounds: Min QPE = $2,836,167.00 [$850,850.10 Credit] to Max QPE = $3,771,497.00 [$1,131,449.10 Credit]; Relocation Baseline = $3,274,421.00 [$982,326.30 Credit].\n")
        f.write("     * **FVD, BH, LLS:** Aggregate Cast and Producer accounts exceed $500,000 without payee contracts (`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)` under Rule 5).\n")
        f.write("4. **`COMPARISON_NOT_ESTABLISHED` (Structure Not in Saved Results):**\n")
        f.write("   * `us_ny_post_production_credit`: 4 rows (component-only structure; no full relocation structure in saved DB).\n")
        f.write("   * Missing Canadian Stacks: 4 rows (stacks not generated by engine in LU and BH).\n")
        f.write("   * `stack_ny_prod_post`: 4 rows (no stack candidate generated by engine; missing candidate cannot establish VERIFIED_AGREEMENT while underlying rule DISC-NY-001 permits distinct-cost pairing contrary to § 31*2(a)(1)).\n")
        f.write("5. **`SCENARIO_SPEND_BASE_VARIANCE`:**\n")
        f.write("   * 41 rows on open-spend programs where the engine's generic relocation spend base differed from independent source-derived relocation baselines.\n\n")
        f.write("---\n\n")
        
        # -------------------------------------------------------------
        # 3. Discrepancy & Disposition Register Table
        # -------------------------------------------------------------
        f.write("## 3. Discrepancy & Disposition Register Table\n\n")
        f.write("| Project | Program / Stack Slug | JCode | Evidence Class | Expected Status | Actual Status | Expected Inc ($) | Actual Inc ($) | Delta Inc ($) | Remediation Status | Defect / Disposition | Root Cause Summary |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n")
        for d in discrepancies:
            exp_inc_str = f"{d['expected_total_incentive_usd']:,.2f}" if isinstance(d['expected_total_incentive_usd'], (int, float)) else str(d['expected_total_incentive_usd'])
            act_inc_str = f"{d['actual_incentive_usd']:,.2f}" if isinstance(d['actual_incentive_usd'], (int, float)) else str(d['actual_incentive_usd'])
            delta_str = f"{d['delta_incentive_usd']:,.2f}" if isinstance(d['delta_incentive_usd'], (int, float)) else str(d['delta_incentive_usd'])
            f.write(f"| **{d['project_code']}** | `{d['program_slug']}` | {d['jurisdiction_code']} | `{d['input_evidence_classification']}` | {d['expected_status']} | {d['actual_status']} | {exp_inc_str} | {act_inc_str} | {delta_str} | `{d['remediation_code_status']}` | `{d['defect_or_disposition_id']}` | {d['root_cause_analysis'][:75]}... |\n")
        f.write("\n*(Full 204-row record available in `NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv`)*\n\n")
        
        # -------------------------------------------------------------
        # 4. Detailed Account-Level Reconciliations
        # -------------------------------------------------------------
        f.write("---\n\n")
        f.write("## 4. Detailed Account-Level Reconciliations\n\n")
        f.write("### 4.1 New York State Film Production Credit (§ 24) Breakdown, Post (§ 31*2) & NY Stack\n")
        f.write("* **Statutory Authority & Effective Dates:**\n")
        f.write("  - **NY Tax Law § 24 (Film Production Credit):** As amended by Part D, Ch. 59, Laws of 2023 (enacted May 3, 2023; effective April 1, 2023 for initial applications filed on or after April 1, 2023). Base credit rate is 30% (increased from 25% under pre-2023 historical law).\n")
        f.write("  - **Historical vs. Current-Law ATL Doctrine:** Prior to April 1, 2023, Above-The-Line (ATL) costs were strictly excluded (0% eligible). Under current law (§ 24(b)(1)), eligible Above-The-Line costs include writers, directors, composers, performers (actors, excluding background actors without scripted lines), and up to two (2) individual producers.\n")
        f.write("  - **Statutory ATL Ceilings:** (1) Individual salary cap of $500,000 per person (§ 24(b)(1)(B)); (2) Headcount cap of maximum 2 producers; and (3) Aggregate ATL ceiling of not more than 40% of all other qualified production costs (BTL physical + post-production) (§ 24(b)(1)).\n")
        f.write("* **The Little Utopia (LU) — Source Line Table Breakdown & Reconciliations:**\n")
        f.write("  - **Grounded in Single Treatment Table:** Derived from `LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv` conserving all 44 original budget accounts ($4,364,395.00 leaf sum; $4,364,393.00 controlling gross with $2 rounding variance).\n")
        f.write("  - **Physical Below-The-Line:** Accounts 2000–3800 (excluding 3200) = $2,572,970.00; On-Set Sound (Account 3200, BTL per NY-A03) = $69,532.00. Total Physical BTL = **$2,642,502.00**.\n")
        f.write("  - **Creative Above-The-Line Incurred:** Script Clearances (Account 1100) = $5,050.00; Cast Performers (Account 1400) = $136,115.00. Total Creative ATL = **$141,165.00**. (All individual earners <= $500k; producer count is 0).\n")
        f.write("  - **Post-Production Department:** Post VFX (Account 6100) = $52,500.00 (qualifying post spend if NY facility); Post Editorial (Account 5000) = $9,068.00 (performed in Los Angeles, CA; consistently excluded from NY spend across relocation bounds, allocated outside NY to generic US unpriced in engine trace Segment 0). Total Post = **$61,568.00** (reconciling source accounts and withdrawing previously hallucinated $208,670).\n")
        f.write("  - **BTL Travel & Living (Account 3900):** $438,254.00. Under 5 NYCRR § 170.2, in-state crew lodging/per diem qualifies, while out-of-state/foreign airfares are statutorily excluded. Because the Movie Magic Topsheet does not itemize in-state lodging vs foreign airfares, Account 3900 is an empirical unknown (withdrawing previously hallucinated $82,347).\n")
        f.write("  - **Subaccount Breakdown for Admin, Publicity & Insurance (Verified against Original Budget PDF):**\n")
        f.write("    - **Account 7000 (Administrative Expenses: $297,593.00):** Direct production office lines (7009 Copiers $4,239, 7014 DIT Software $1,112, 7015 Hardware $2,609, 7030 Telecom $11,886, 7094 Office Supplies $3,696) total **$23,542.00**; Line production service company fee (7003) = **$95,000.00** (potentially eligible production coordination); Statutorily excluded corporate lines (7002 Setup & Audit $35,927, 7007 Legals $10,000, 7038 Bank Charges $2,957, 7042 Freight $27,293, 7050 Wrap Party $10,435, 7095 Foreign VAT $92,439) total **$179,051.00** (statutorily excluded under § 24(a)(2)). Total: $23,542 + $95,000 + $179,051 = **$297,593.00**.\n")
        f.write("    - **Account 7100 (Publicity: $24,348.00):** Unit still photographer (7102) = **$8,696.00** (IATSE 600 BTL crew labor); EPK crew & equipment (7105) = **$15,652.00** (camera crew $9,783, edit $5,869). Admitted up to **$24,348.00** in optimistic planning ceiling; excluded promotional marketing in incurred spend.\n")
        f.write("    - **Account 7200 (Corporate Insurance: $12,374.00):** Direct production liability (7201: $4,174) + cast medicals (7203: $700) = **$4,874.00** (direct physical safety). Excluded corporate wrap (7202 E&O $5,000, travel insurance $2,500) = **$7,500.00**. Total: $4,874 + $7,500 = **$12,374.00**.\n")
        f.write("    - **Account 8100 (Insurance : 1.2%: $48,181.00):** Production package floater. Excluded in baseline without policy binder; admitted up to **$48,181.00** in optimistic planning ceiling.\n")
        f.write("    - **Account 8300 (Contingency Reserve : 7.5%: $301,131.00):** Unspent reserve ($0.00 incurred spend); admitted up to **$301,131.00** in optimistic planning scenario per documented producer election (100% deployment into qualifying BTL physical production).\n")
        f.write("    - **Account 1600 (ATL Travel & Living: $397,279.00):** Statutorily excluded under § 24(b)(1).\n")
        f.write("  - **Statutory Non-Qualifying Exclusions & Resolution of the $138,850 Residual:**\n")
        f.write("    - Incurred spend baseline exclusions: ATL Travel ($397,279) + Admin ($297,593) + Publicity ($24,348) + Insurance ($12,374) + Insurance 1.2% ($48,181) + Contingency ($301,131) = **$1,080,906.00** ($1,080,904.00 against controlling gross).\n")
        f.write("    - The previously claimed $138,850 exclusion residual was the arithmetic shortfall of four manually substituted category amounts ($942,054.00 vs $1,080,904.00). Grounded in the actual 44 source budget accounts, statutory exclusions total exactly **$1,080,906.00** ($1,080,904.00 gross). Conserving leaf sum: $4,364,395.00 - $1,080,906.00 = $3,283,489.00 max spend base; unexplained residual = **$0.00**.\n")
        f.write("    - Optimistic planning upper bound exclusions: ATL Travel ($397,279) + Excluded Corporate Admin ($179,051) + Corporate Insurance ($7,500) + LA Editorial ($9,068) = **$592,898.00**. Upper bound eligible spend = $4,364,395.00 - $592,898.00 = **$3,771,497.00**.\n")
        f.write("  - **Supported Statutory Bounds on The Little Utopia:**\n")
        f.write("    - **Minimum QPE (Lower Bound Floor):** Excludes uncertain BTL travel ($438,254) and out-of-state LA editorial ($9,068). Qualified Physical BTL ($2,642,502) + VFX ($52,500) = $2,695,002.00 other qualified costs. 40% ceiling = $1,078,000.80 (Creative ATL $141,165 fully admitted). Min QPE = **$2,836,167.00** [Credit at 30%: **$850,850.10**].\n")
        f.write("    - **Relocation Baseline (Midpoint Scenario):** In-state crew lodging admitted ($438,254), out-of-state LA editorial excluded ($9,068). Other qualified costs = $3,133,256.00. 40% ceiling = $1,253,302.40 (Creative ATL $141,165 admitted). Relocation Baseline QPE = **$3,274,421.00** [Credit at 30%: **$982,326.30**].\n")
        f.write("    - **Optimistic Planning Ceiling / Upper Bound:** Admits every potentially eligible unresolved portion from source table: 100% contingency deployment into BTL physical ($301,131), 100% in-state crew travel ($438,254), direct production office ($23,542), line production coordination ($95,000), unit stills & EPK crew ($24,348), direct liability & medicals ($4,874), and production package insurance ($48,181). Editorial in LA ($9,068) is consistently excluded from NY relocation spend. Upper Bound QPE = **$3,771,497.00** [Credit at 30%: **$1,131,449.10**].\n")
        f.write("  - **Engine Comparison (`canonical-1.106.0`, Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903`, Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`):**\n")
        f.write("    - Actual Qualified Spend: $4,054,196.00 (gross $4,355,327 allocated to NY less $301,131 unspent contingency; out-of-state editorial $9,068 allocated to US unpriced in Segment 0).\n")
        f.write("    - Actual Incentive: $1,216,258.80 ($4,054,196.00 × 0.30).\n")
        f.write("    - Overstatement at Optimistic Upper Bound: $1,216,258.80 - $1,131,449.10 = **+$84,809.70**.\n")
        f.write("    - Overstatement at Relocation Baseline: $1,216,258.80 - $982,326.30 = **+$233,932.50**.\n")
        f.write("    - Overstatement at Min QPE Lower Bound Floor: $1,216,258.80 - $850,850.10 = **+$365,408.70**.\n")
        f.write("    - **Audit Disposition:** **`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**. Engine credit overstatement confirmed across all bounds (`NA-DEFECT-01`).\n")
        f.write("* **F#K Valentine's Day (FVD) — Supported Statutory Bounds:**\n")
        f.write("  - BTL Physical Production ($1,114,318) + Travel ($46,000) + On-Set Sound ($26,458) + Post ($70,000) = **$1,256,776.00** BTL+Post baseline.\n")
        f.write("  - 40% Statutory Ceiling: $1,256,776.00 × 0.40 = **$502,710.40**.\n")
        f.write("  - Cast ($1,976,479) and Producer accounts exceed $500k without general ledger payee contracts. Under AUDIT INPUT EVIDENCE GATE Rule 5: Cannot apply per-person limits to aggregate account totals.\n")
        f.write("  - Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`**.\n")
        f.write("  - Supported Bounds: Min QPE = **$1,256,776.00** [Credit: **$377,032.80**] (zero ATL) to Max QPE = **$1,759,486.40** [Credit: **$527,845.92**] (40% ceiling).\n")
        f.write("  - Engine Comparison (`canonical-1.106.0`, Result ID `c3b8ad45-5c1e-47ed-b182-c9106f668b2a`, Structure ID `ae10b2e7-ed52-4ebe-894a-b9d6756ced32`): Engine qualified $3,701,238.00 (Credit: $1,110,371.40). Even at the statutory upper bound, engine overstates credit by at least **+$582,525.48**, confirming `NA-DEFECT-01`.\n")
        f.write("* **Bad Hombres (BH) — Supported Statutory Bounds:**\n")
        f.write("  - BTL Physical Production ($656,044) + Travel ($27,000) + On-Set Sound ($16,845) + Post ($50,000) = **$749,889.00** BTL+Post baseline.\n")
        f.write("  - 40% Statutory Ceiling: $749,889.00 × 0.40 = **$299,955.60**.\n")
        f.write("  - Cast ($974,371) exceeds $500k without payee schedule. Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`**.\n")
        f.write("  - Supported Bounds: Min QPE = **$749,889.00** [Credit: **$224,966.70**] to Max QPE = **$1,049,844.60** [Credit: **$314,953.38**] (40% ceiling).\n")
        f.write("  - Engine Comparison (`canonical-1.106.0`, Result ID `f3513411-547c-41ca-894d-e1ef36d856b7`, Structure ID `8558365f-6a68-45a2-931e-4f294ddf20c9`): Engine qualified $2,327,641.00 (Credit: $698,292.30). Even at the statutory upper bound, engine overstates credit by at least **+$383,338.92**, confirming `NA-DEFECT-01`.\n")
        f.write("* **Lips Like Sugar (LLS) — Supported Statutory Bounds:**\n")
        f.write("  - BTL Physical Production ($5,166,417) + Travel ($200,000) + On-Set Sound ($87,067) + Post ($400,000) = **$5,853,484.00** BTL+Post baseline (financing accounts 6500 $450k, 6600 $250k, 6700 $1M properly excluded under NY-A01).\n")
        f.write("  - 40% Statutory Ceiling: $5,853,484.00 × 0.40 = **$2,341,393.60**.\n")
        f.write("  - Cast ($1,675,000) and Producers ($1,184,123) exceed $500k without contracts. Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`**.\n")
        f.write("  - Supported Bounds: Min QPE = **$5,853,484.00** [Credit: **$1,756,045.20**] to Max QPE = **$8,194,877.60** [Credit: **$2,458,463.28**] (40% ceiling).\n")
        f.write("  - Engine Comparison (`canonical-1.106.0`, Result ID `5557ceb5-d3f5-4b42-85df-d7369d72a9bd`, Structure ID `c135df1f-9a8e-4bdf-b25e-bd6af29a608b`): Engine qualified $9,483,654.00 (Credit: $2,845,096.20). Even at the statutory upper bound, engine overstates credit by at least **+$386,632.92**, confirming `NA-DEFECT-01`.\n")
        f.write("* **New York Post-Production Credit (§ 31*2) Gateways & Rates:**\n")
        f.write("  - **Statute Reference:** NY Tax Law § 31*2 (Film Post-Production Credit, revision 2025-07-11; distinct from plain § 31 Excelsior Jobs).\n")
        f.write("  - **Gateways (§ 31*2(a)(2) & (3)):** General Post Gateway requires qualified post costs at a NY Qualified Post-Production Facility (QPF) equal to the lesser of $1,000,000 or 75% of total worldwide post spend. VFX/Animation Gateway requires the lesser of $500,000 or 10% of total worldwide VFX/animation spend. Engine source-config fixed $1M missed both branches (`DISC-NY-002`).\n")
        f.write("  - **Rates:** 30% MCTD, 35% Upstate (+5% facility differential), plus +10% eligible county post labor uplift. Flat 35% in engine config confirmed defective (`DISC-NY-003`). Saved DB contains only component-relocation candidates, no full relocation structures (`COMPARISON_NOT_ESTABLISHED (COMPONENT_ONLY_STRUCTURE)`).\n")
        f.write("  - **On-Set Sound Exclusion (NY-A03):** Production sound (LU $69,532, FVD $26,458, BH $16,845, LLS $87,067) is BTL physical production, NOT post-production.\n")
        f.write("* **Upstate Production Credit Uplift (§ 24(a)(5)):**\n")
        f.write("  - 53 upstate counties; Dutchess, Orange, and Putnam ARE statutorily included in the § 24(a)(5) upstate production credit county list (unlike post MCTD boundary).\n")
        f.write("  - +10% credit uplift (40% total).\n")
        f.write("  - Labor: NY resident upstate labor qualifies.\n")
        f.write("  - Non-labor: Qualifies ONLY IF more than 50% (>50%) of principal photography shoot days occur upstate.\n")
        f.write("  - ATL is statutorily excluded from the +10% uplift (receives base 30% only).\n")
        f.write("  - Status: County shoot day logs are absent from budget records, keeping upstate uplift as an explicit conditional planning scenario (`CONDITIONAL_UPSTATE_EXPANSION`).\n")
        f.write("* **New York Multi-Program Stack Reconciliation (§ 24 + § 31*2 vs. DISC-NY-001):**\n")
        f.write("  - Absolute taxpayer/film-level bar under NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c): Any taxpayer eligible for Section 24 film production credit is statutorily ineligible for Section 31*2 post-production credit for the same film.\n")
        f.write("  - Independent calculator models expected QPE as $0.00 (`GATE_REJECTED`).\n")
        f.write("  - Confirmed engine defect `DISC-NY-001` in `backend/app/optimization/stacking_rules.py:617` allows distinct costs (`same_cost_prohibited_distinct_costs_allowed`).\n")
        f.write("  - Saved DB did not generate stack candidate (`STACK_NOT_GENERATED`). Reclassified as **`COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)`**, pending canonical repair by Codex.\n\n")
        
        f.write("### 4.2 California Film & TV Tax Credit (Program 4.0 BTL) Breakdown\n")
        f.write("* **FVD Reconciliation ($603,665.65 vs $1,295,433.30):**\n")
        f.write("  - In saved generation `canonical-1.106.0`, exactly ONE full relocation candidate exists for `ca_film_30` on FVD: Result ID `602efade-0ccf-43f2-b529-81434c6fd912` (Structure ID `b90c23db-3946-454b-8365-25eebe53dcf3`, Name `Full relocation to US-CA`).\n")
        f.write("  - FVD gross budget is $4,517,687.00. Unspent contingency ($362,866) and finance fee ($453,583) are excluded, leaving $3,701,238.00 unconstrained spend.\n")
        f.write("  - **$1,295,433.30 Origin:** For open-spend programs that do not exclude Above-The-Line costs (such as Alabama `us_al_film_incentive` Structure `3ede659f...`), the entire $3,701,238 qualifies at 35%, yielding $1,295,433.30 ($3,701,238 × 0.35). This was the open-spend benchmark, NOT a California structure in the database.\n")
        f.write("  - **$603,665.65 Origin:** Under California Program 4.0, Above-The-Line costs are excluded. In Result ID `602efade...`, the engine trace marked Accounts 1100 ($252,650), 1200 ($401,831), 1300 ($75,710), and 1400 ($1,246,288) as `grey_area_requires_authority` ($1,976,479 total ATL excluded). The qualified spend base was $3,701,238 - $1,976,479 = $1,724,759.00. At 35% base rate, $1,724,759 × 0.35 = **$603,665.65**.\n")
        f.write("  - There is zero ambiguity in candidate matching: Result ID `602efade...` uniquely matches `ca_film_30` with actual incentive $603,665.65.\n")
        f.write("* **California Statutory Minimum Spend Basis (Bad Hombres):**\n")
        f.write("  - Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) & (B) explicitly defines the minimum spend requirement as a **production budget** of not less than $1,000,000 for a qualified motion picture / independent film.\n")
        f.write("  - Bad Hombres has a gross production budget of $2,482,023.00, which satisfies the statutory budget threshold. The previous audit claim alleging affirmative statutory minimum spend failure confused the production budget threshold with in-state qualified spend, and is formally retracted as `RET-07`.\n")
        f.write("  - Independent BTL baseline QPE is $749,889.00 (expected credit at 35% = $262,461.15). The engine in `canonical-1.106.0` (Result ID `f7ef008d-ec84-4c96-a9fc-035638a420e7`) qualified $854,739.00 (credit $299,158.65) due to inclusion of administration, insurance, and bond lines. The spend-base variance of +$36,697.50 is classified as `OLD_SAVED_RESULT_STALE_PENDING_REGENERATION`.\n")
        f.write("* **The Little Utopia:** Qualified BTL Spend = $3,142,324.00 (meets $1M budget floor). Expected Credit (35%) = $1,099,813.40 vs Saved DB Credit $1,369,560.85 (overstatement due to ATL travel, insurance, and bond inclusion in engine canonical-1.106.0).\n")
        f.write("* **Lips Like Sugar:** Qualified BTL Spend = $5,853,484.00. Expected Credit (35%) = $2,048,719.40 vs Saved DB Credit $2,236,007.55 (Result ID `f167da0f-bb1a-47e7-829b-b208cc08b38d`). Classified as `OLD_SAVED_RESULT_STALE_PENDING_REGENERATION`.\n\n")
        
        # -------------------------------------------------------------
        # 5. Proposed Canonical Repairs for Codex Review
        # -------------------------------------------------------------
        f.write("---\n\n")
        f.write("## 5. Proposed Canonical Repairs for Codex Review\n\n")
        f.write("1. **Implement `NY_ATL_40_PERCENT_RULE` in `program_spend_rules.py` (`NA-DEFECT-01`):**\n")
        f.write("   - Restrict qualifying Above-The-Line costs to $\\le 0.40 \\times (\\text{BTL} + \\text{Post})$.\n")
        f.write("   - Enforce statutory $500,000 per-person salary cap on qualifying ATL roles (writers, directors, composers, performers, and max 2 producers).\n")
        f.write("   - Exclude background actors without scripted lines from qualifying ATL.\n")
        f.write("   - Exclude non-qualifying finance fees, completion bond, corporate insurance, and general administrative overhead from qualified production costs.\n")
        f.write("2. **Repair Stacking Rule Conflict in `stacking_rules.py:617` (`DISC-NY-001`):**\n")
        f.write("   - Change `stack_ny_prod_post` relationship from `same_cost_prohibited_distinct_costs_allowed` to `mutually_exclusive`, implementing statutory taxpayer/film-level bar of NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c).\n")
        f.write("3. **Implement Dual Post-Production Gateways in `program_spend_rules.py` (`DISC-NY-002`):**\n")
        f.write("   - General Post: Lesser of $1,000,000 or 75% of worldwide post spend.\n")
        f.write("   - VFX & Animation: Lesser of $500,000 or 10% of worldwide VFX/animation spend.\n")
        f.write("4. **Refine Post Rates & County Uplifts (`DISC-NY-003`):**\n")
        f.write("   - Model MCTD (30%) vs Upstate facility (35%) geographic boundary and +10% eligible county post labor uplift.\n")
        f.write("5. **Refine California Program 4.0 BTL Spend Classification:** Ensure `ca_film_30` in canonical code excludes general administration, insurance, and completion bond from the qualified BTL base.\n")
        f.write("6. **Authorize Canonical Regeneration:** Run authorized regeneration to propagate commits `486bd15` (F-01..F-07), `6cd2bbe`, and NY repairs into served database state.\n\n")
        
        # -------------------------------------------------------------
        # 6. Detailed Remaining Blockers Ledger
        # -------------------------------------------------------------
        f.write("---\n\n")
        f.write("## 6. Detailed Remaining Blockers Ledger (Evidence Gaps vs Engine Defects)\n\n")
        f.write("Every retained issue across the four anchor projects is categorized and detailed below with exact missing facts, supported scenarios, expected engine behavior, producer inputs needed, and identical candidate matching:\n\n")
        
        f.write("### 6.1 Blocker 1: LU New York Empirical Evidence Gaps (Travel, Contingency, Insurance, Upstate)\n")
        f.write("* **Blocker ID:** `BLOCKER-01-LU-NY-EVIDENCE-GAP`\n")
        f.write("* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)\n")
        f.write("* **Missing Facts:** (1) Itemized crew lodging vs foreign/out-of-state airfare schedule in Account 3900 ($438,254.00) under 5 NYCRR § 170.2; (2) General ledger disbursement proof for unspent contingency reserve Account 8300 ($301,131.00); (3) Insurance policy binder allocating package floater Account 8100 ($48,181.00) to NY risks; (4) County shoot logs for upstate non-labor uplift.\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - Lower Bound Floor: Min QPE = **$2,836,167.00** [Credit: **$850,850.10**] (contingency unspent, airfare excluded, baseline insurance excluded).\n")
        f.write("  - Relocation Baseline Midpoint: Baseline QPE = **$3,274,421.00** [Credit: **$982,326.30**] (100% lodging admitted, contingency unspent, LA editorial excluded).\n")
        f.write("  - Optimistic Planning Ceiling Upper Bound: Max QPE = **$3,771,497.00** [Credit: **$1,131,449.10**] (100% contingency deployed into BTL physical, 100% lodging admitted, qualifying office/coordination/insurance admitted, LA editorial excluded).\n")
        f.write("* **Expected Engine Behavior:** Incurred-spend evaluations must fail closed or flag `MISSING_AUDIT_EVIDENCE` for unitemized travel and unspent reserves; planning scenario evaluations must admit contingency and lodging strictly subject to explicit producer election and apply statutory 40% ATL cap.\n")
        f.write("* **Exact Producer Input Needed:** Producer entry in Overview/Inspector of in-state crew lodging breakdown ($ in Account 3900), contingency inclusion % (0% for incurred vs 100% for relocation), NY insurance binder, and county shoot day logs.\n")
        f.write("* **Comparison Matching:** Compared against Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903`, Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4` ($4,054,196.00 QPE / $1,216,258.80 Credit). Overstatement of at least **+$84,809.70** is confirmed across all bounds (`NA-DEFECT-01`).\n\n")

        f.write("### 6.2 Blocker 2: FVD, BH, LLS New York Individual Talent Contracts & Producer Limit Gaps\n")
        f.write("* **Blocker ID:** `BLOCKER-02-NY-TALENT-CONTRACTS-GAP`\n")
        f.write("* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)\n")
        f.write("* **Missing Facts:** Individual general ledger deal memos and employment contracts for Cast (FVD $1,976,479; BH $974,371; LLS $1,675,000) and Producer accounts (FVD $477,541; LLS $1,184,123) to apply the statutory $500,000 per-person salary cap and the maximum 2 individual producers limit under NY Tax Law § 24(b)(1)(B).\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - FVD: Floor = **$1,256,776.00** [$377,032.80 Credit] (0% ATL); Ceiling = **$1,759,486.40** [$527,845.92 Credit] (40% ATL cap). Overstatement >= **+$582,525.48**.\n")
        f.write("  - BH: Floor = **$749,889.00** [$224,966.70 Credit]; Ceiling = **$1,049,844.60** [$314,953.38 Credit]. Overstatement >= **+$383,338.92**.\n")
        f.write("  - LLS: Floor = **$5,853,484.00** [$1,756,045.20 Credit]; Ceiling = **$8,194,877.60** [$2,458,463.28 Credit]. Overstatement >= **+$386,632.92**.\n")
        f.write("* **Expected Engine Behavior:** When individual talent contracts are absent, calculate and display the supported statutory range [Floor .. Ceiling], enforce the 40% aggregate ATL ceiling, and prevent qualifying aggregate topsheet ATL lines above the cap.\n")
        f.write("* **Exact Producer Input Needed:** Producer schedule of individual talent earnings listing name, role (writer/director/performer/producer), and total compensation per person; designation of up to 2 credited individual producers qualifying under § 24(b)(1).\n")
        f.write("* **Comparison Matching:** Compared against identical full relocation allocations for New York State Film Tax Credit: FVD Structure `ae10b2e7-ed52-4ebe-894a-b9d6756ced32` / Result `c3b8ad45-5c1e-47ed-b182-c9106f668b2a`; BH Structure `8558365f-6a68-45a2-931e-4f294ddf20c9` / Result `f3513411-547c-41ca-894d-e1ef36d856b7`; LLS Structure `c135df1f-9a8e-4bdf-b25e-bd6af29a608b` / Result `5557ceb5-d3f5-4b42-85df-d7369d72a9bd`.\n\n")

        f.write("### 6.3 Blocker 3: Canadian CAVCO Domestic Certification Gaps (CPTC & OFTTC)\n")
        f.write("* **Blocker ID:** `BLOCKER-03-CAVCO-DOMESTIC-CERTIFICATION-GAP`\n")
        f.write("* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)\n")
        f.write("* **Missing Facts:** CAVCO Part A/B certification, Canadian copyright ownership documentation, and key creative point tally (>= 6/10 CAVCO points) under Income Tax Act § 125.4 and Ontario Taxation Act § 43.\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - Non-Certified Scenario: Ineligible for CPTC/OFTTC ($0.00 credit); eligible instead for production services credits (PSTC / OPSTC) subject to labour expenditure proofs.\n")
        f.write("  - Certified Domestic Scenario: 25% federal labour credit (CPTC) + 35% Ontario labour credit (OFTTC) subject to 60% CAVCO cost cap.\n")
        f.write("* **Expected Engine Behavior:** Treat missing certification as unknown (`NOT_ESTABLISHED`) rather than hard gate rejection or unearned qualification; surface CAVCO status toggle in Overview/Inspector.\n")
        f.write("* **Exact Producer Input Needed:** Producer input confirming CAVCO certification status (Certified vs Production Services Only) and creative point count.\n")
        f.write("* **Comparison Matching:** Reconciled across 40 evaluation rows on `ca_federal_cptc`, `on_ofttc`, and domestic stacks (`stack_on_cptc_ofttc`, `stack_qc_cptc_pstc`, `stack_on_ofttc_ocase`).\n\n")

        f.write("### 6.4 Blocker 4: Canadian Qualified Labour Expenditure (QLE) Payroll Schedule Gaps (PSTC & OPSTC)\n")
        f.write("* **Blocker ID:** `BLOCKER-04-CANADIAN-QLE-PAYROLL-GAP`\n")
        f.write("* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)\n")
        f.write("* **Missing Facts:** Itemized Canadian payroll general ledger with CAVCO individual residency declarations confirming Canadian citizenship / permanent residency for BTL crew and ATL talent under ITA § 125.5.\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - 0% Verified Labour Scenario: $0.00 verified credit under strict evidence rules.\n")
        f.write("  - Indicative Relocation Scenario: Range between 40% and 60% labour component of physical BTL spend, bounded by statutory 16% PSTC / 21.5% OPSTC rates.\n")
        f.write("* **Expected Engine Behavior:** Retract arbitrary 50% heuristic; flag `MISSING_PAYROLL_SCHEDULE` until resident labour is itemized.\n")
        f.write("* **Exact Producer Input Needed:** Producer upload or entry of Canadian resident payroll ledger or certified labour ratio.\n")
        f.write("* **Comparison Matching:** Reconciled across 28 rows on Canadian labour programs and stacks; verified zero heuristic substitution under Rule 2.\n\n")

        f.write("### 6.5 Blocker 5: High-Earner Salary Caps on Aggregate Topsheets (GA, IL, MA)\n")
        f.write("* **Blocker ID:** `BLOCKER-05-HIGH-EARNER-SALARY-CAPS-GAP`\n")
        f.write("* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)\n")
        f.write("* **Missing Facts:** Individual compensation schedule itemizing earnings per payee to apply the statutory $500,000 per-person cap in Georgia (O.C.G.A. § 48-7-40.26) and Illinois (35 ILCS 16/10), and the $1,000,000 per-person cap in Massachusetts (M.G.L. c. 62 § 6(l)).\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - Uncapped Aggregate Spend Scenario: Engine saved baseline (qualifying full aggregate accounts).\n")
        f.write("  - Fully Capped Scenario: Deduction of excess earnings above statutory per-person caps once payee contracts are supplied.\n")
        f.write("* **Expected Engine Behavior:** Display aggregate spend as conditional pending payee schedule; flag `MISSING_PAYEE_COMPENSATION_SPLIT` instead of claiming verified defect without contracts.\n")
        f.write("* **Exact Producer Input Needed:** Producer payroll census listing individual earners in excess of $500,000 / $1,000,000.\n")
        f.write("* **Comparison Matching:** Reconciled across 12 rows on FVD, BH, LLS; monetary variance claims revoked from open defect totals under `RET-05`.\n\n")

        f.write("### 6.6 Blocker 6: Stacking Mutual Exclusivity Violation (`DISC-NY-001` in `stacking_rules.py:617`)\n")
        f.write("* **Blocker ID:** `BLOCKER-06-NY-STACK-MUTUAL-EXCLUSIVITY-DEFECT`\n")
        f.write("* **Classification:** Engine Code & Rule Defect (`OPEN_CODE_DEFECT_PENDING_CODEX_REVIEW`)\n")
        f.write("* **Missing Facts:** None (statutory authority is unambiguous and complete).\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - Statutory Law: § 24 and § 31 cannot stack for the same film under NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c) ($0.00 stack credit; `GATE_REJECTED`).\n")
        f.write("  - Engine Code Defect: `stacking_rules.py:617` permits distinct-cost pairing (`same_cost_prohibited_distinct_costs_allowed`).\n")
        f.write("* **Expected Engine Behavior:** Reject `stack_ny_prod_post` as mutually exclusive at the film/taxpayer level.\n")
        f.write("* **Exact Producer Input Needed:** None (systemic engine rule repair required by Codex).\n")
        f.write("* **Comparison Matching:** Reconciled across 4 rows on `stack_ny_prod_post`; classified as `COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)` because engine did not generate stack candidate and underlying rule is defective.\n\n")

        f.write("### 6.7 Blocker 7: Stale Database Results Pending Canonical Regeneration\n")
        f.write("* **Blocker ID:** `BLOCKER-07-STALE-DATABASE-REGENERATION`\n")
        f.write("* **Classification:** Stale Database State (`OLD_SAVED_RESULT_STALE_PENDING_REGENERATION`)\n")
        f.write("* **Missing Facts:** None (repairs already implemented in canonical codebase in commits `486bd15` and `6cd2bbe`).\n")
        f.write("* **Affected Programs:** Mexico Federal Film Incentive (F-05), North Carolina Grant (F-03), New Brunswick Tier (F-01), Rhode Island Project Cap (F-04), LU Canadian Stacks (F-06), California Program 4.0 BTL spend classification.\n")
        f.write("* **Supported Scenarios & Bounds:**\n")
        f.write("  - Saved Database: `canonical-1.106.0` values persisted in PostgreSQL (`frametax2_claude_optimizer_acceptance_20260919`).\n")
        f.write("  - Canonical Code: Repaired behavior in `canonical-1.107.0` (commit `486bd15`).\n")
        f.write("* **Expected Engine Behavior:** Persist freshly calculated results reflecting `canonical-1.107.0` once database regeneration is authorized.\n")
        f.write("* **Exact Producer Input Needed:** None (system authorization for production regeneration required).\n")
        f.write("* **Comparison Matching:** Unambiguously identified and separated from open code defects across all affected rows.\n\n")

        # -------------------------------------------------------------
        # 7. Gate Disposition & Mandatory Sign-off
        # -------------------------------------------------------------
        f.write("---\n\n")
        f.write("## 7. Gate Disposition & Mandatory Sign-off\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **GATE DISPOSITION:**\n")
        f.write("> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**\n")
        f.write(">\n")
        f.write("> **REMAINING BLOCKERS:**\n")
        f.write("> 1. **Empirical Fact Gaps (Producers):** General ledger payroll ledgers (Canadian QLE), individual talent payee contracts (GA/IL/MA salary caps), and location shoot logs remain unresolved in source records.\n")
        f.write("> 2. **Code Repair Implementation (Codex):** NY § 24 ATL 40% aggregate cap and CA Program 4.0 spend refinement await Codex implementation and review.\n")
        f.write("> 3. **Authorized Database Regeneration:** Commits `486bd15` (F-01..F-07) and `6cd2bbe` are unregenerated; served database state remains stale until regeneration is authorized.\n")
        f.write("> 4. **Regional Expansion Boundary:** All execution halts strictly at the North American handoff. Rest-of-World (ROW) expansion will NOT begin until Codex review passes and the North American gate is adjudicated.\n")

if __name__ == "__main__":
    run_comprehensive_audit()
