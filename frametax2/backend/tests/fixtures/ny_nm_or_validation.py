"""
NY, NM, and Oregon validation fixtures — source-backed rates, deterministic.

Sources:
  NY:  NY Tax Law § 24; Empire State Development
  NM:  NMSA 1978 § 7-2F-1 et seq.; NM Film Office
  OR:  ORS § 284.368; Oregon Film Office (OPIF)

All rates PARSED — see 0004 migration for confidence tier rationale.

Hand-verified expected outputs are documented in each EXPECTED dict.
"""
from __future__ import annotations

# ===========================================================================
# NEW YORK
# ===========================================================================
NY_JURISDICTION = {
    "id": "jur-us-ny",
    "name": "New York",
    "currency_code": "USD",
    "country_code": "US",
}

NY_PROGRAM = {
    "id": "prog-ny-state",
    "slug": "ny_state_film",
    "program_type": "tax_credit",
    "base_rate": 0.25,
    "max_rate": 0.35,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": True,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# ATL excluded; BTL + post qualify when incurred in NYS
NY_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",     "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "post_production", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",            "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "music",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "sound",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",       "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",     "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",       "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous", "qualifies": True, "jurisdiction_spend_only": True},
]

NY_UPSTATE_UPLIFT = {
    "id": "uplift-ny-upstate",
    "name": "NY Upstate Production Uplift",
    "additional_rate": 0.10,
    "applies_to": "same_qualifying_spend",
    "condition_type": "shooting_location",
    "condition_threshold": None,
    "condition_text": "upstate_ny",
    "is_stackable_with_other_uplifts": False,
    "confidence_tier": "PARSED",
}

# Budget: $3,470,000 — NYC area feature, 100% in NYS
# ATL (director $400K + cast $700K) does NOT qualify for NY credit
# BTL+Post: $2,130,000 qualifies
NY_LINE_ITEMS = [
    # ATL — excluded from NY credit
    {"description": "Director Fee",     "department": "ATL", "amount_usd": 400_000},
    {"description": "Lead Cast",        "department": "ATL", "amount_usd": 700_000},
    # BTL Labor
    {"description": "Crew Labor",       "department": "BTL", "amount_usd": 1_000_000},
    # BTL Non-labor
    {"description": "Equipment Rental", "department": "BTL", "amount_usd": 200_000},
    {"description": "Stage Rental",     "department": "BTL", "amount_usd": 150_000},
    {"description": "Location Fees",    "department": "BTL", "amount_usd": 120_000},
    {"description": "Set Construction", "department": "BTL", "amount_usd": 100_000},
    {"description": "Transportation",   "department": "BTL", "amount_usd":  60_000},
    {"description": "Catering",         "department": "BTL", "amount_usd":  40_000},
    # Post
    {"description": "VFX",              "department": "Post", "amount_usd": 200_000},
    {"description": "Post Production",  "department": "Post", "amount_usd": 150_000},
    {"description": "Music Score",      "department": "Post", "amount_usd":  60_000},
    {"description": "Sound Mix",        "department": "Post", "amount_usd":  50_000},
    # Non-qualifying
    {"description": "Insurance",        "department": "Other", "amount_usd":  90_000},
    {"description": "Completion Bond",  "department": "Other", "amount_usd":  70_000},
    {"description": "Contingency",      "department": "Other", "amount_usd":  80_000},
]

# Hand-verified:
#   Qualifying (BTL+Post, ATL excluded): $2,130,000
#   Credit at 25%: $532,500  | at 35% upstate: $745,500
#   Economic value (refundable = face): $532,500 / $745,500
#   Engine true_net_cost uses fixed_atl + variable_btl:
#     ATL = director $400K + cast $700K = $1,100K
#     BTL = crew $1M + equip $200K + stage $150K + loc $120K + set $100K + trans $60K + catering $40K = $1,670K
#     true_net_nyc  = 1,100K + 1,670K - 532.5K = $2,237,500
#     true_net_up   = 1,100K + 1,670K - 745.5K = $2,024,500
NY_EXPECTED_NYC = {
    "total_budget_usd": 3_470_000,
    "qualifying_spend_usd": 2_130_000,
    "credit_usd": 532_500,          # 2,130,000 * 0.25
    "economic_value_usd": 532_500,  # refundable = face value
    "true_net_cost_usd": 2_237_500, # ATL+BTL - credit
    "atl_qualifies": False,
}

NY_EXPECTED_UPSTATE = {
    "qualifying_spend_usd": 2_130_000,
    "credit_usd": 745_500,          # 2,130,000 * 0.35
    "economic_value_usd": 745_500,
    "uplift_ratio": 1.40,           # 35%/25% = 1.4
}

FIXTURE_NY_NYC = {
    "name": "New York — NYC area, 25% base credit",
    "jurisdiction": NY_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ny",
    "line_items": NY_LINE_ITEMS,
    "programs_with_categories": [{
        "program": NY_PROGRAM,
        "qualifying_categories": NY_QUALIFYING_CATEGORIES,
        "uplifts": [NY_UPSTATE_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    # No shooting_location in production_details → upstate condition evaluates False
    "production_details": {},
}

FIXTURE_NY_UPSTATE = {
    "name": "New York — upstate production, 35% credit",
    "jurisdiction": NY_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ny",
    "line_items": NY_LINE_ITEMS,
    "programs_with_categories": [{
        "program": NY_PROGRAM,
        "qualifying_categories": NY_QUALIFYING_CATEGORIES,
        "uplifts": [NY_UPSTATE_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {"shooting_location": "upstate_ny"},
}


# ===========================================================================
# NEW MEXICO
# ===========================================================================
NM_JURISDICTION = {
    "id": "jur-us-nm",
    "name": "New Mexico",
    "currency_code": "USD",
    "country_code": "US",
}

NM_PROGRAM = {
    "id": "prog-nm-film",
    "slug": "nm_film_production",
    "program_type": "tax_credit",
    "base_rate": 0.25,
    "max_rate": 0.30,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": True,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# NM broader definition — ATL qualifies (PARSED) per NMSA § 7-2F-1
NM_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",     "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",     "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "post_production", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",            "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "music",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "sound",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",       "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",     "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",       "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous", "qualifies": True, "jurisdiction_spend_only": True},
]

# Budget: $1,980,000 — NM production, all in-state
# ATL qualifies (per PARSED NM definition)
# Qualifying = all except insurance, bond, contingency
NM_LINE_ITEMS = [
    # ATL (qualifies in NM, each under any likely per-person cap)
    {"description": "Director Fee",     "department": "ATL", "amount_usd": 200_000},
    {"description": "Lead Cast",        "department": "ATL", "amount_usd": 350_000},
    # BTL Labor
    {"description": "Crew Labor",       "department": "BTL", "amount_usd": 600_000},
    # BTL Non-labor
    {"description": "Equipment Rental", "department": "BTL", "amount_usd": 100_000},
    {"description": "Stage Rental",     "department": "BTL", "amount_usd":  80_000},
    {"description": "Location Fees",    "department": "BTL", "amount_usd":  50_000},
    {"description": "Set Construction", "department": "BTL", "amount_usd":  60_000},
    {"description": "Transportation",   "department": "BTL", "amount_usd":  30_000},
    {"description": "Catering",         "department": "BTL", "amount_usd":  20_000},
    # Post
    {"description": "VFX",              "department": "Post", "amount_usd": 150_000},
    {"description": "Post Production",  "department": "Post", "amount_usd": 100_000},
    {"description": "Music Score",      "department": "Post", "amount_usd":  50_000},
    # Non-qualifying
    {"description": "Insurance",        "department": "Other", "amount_usd":  60_000},
    {"description": "Completion Bond",  "department": "Other", "amount_usd":  50_000},
    {"description": "Contingency",      "department": "Other", "amount_usd":  80_000},
]

# Hand-verified:
#   Qualifying: ATL $550K + BTL $940K + Post $300K = $1,790,000
#   Note: "Lead Cast" → atl_cast, "Director Fee" → atl_director (both qualify)
#   Credit at 25%: $447,500
#   Economic value (refundable): $447,500
#   Engine net cost uses ATL+BTL:
#     ATL: director $200K + cast $350K = $550K
#     BTL: crew $600K + equip $100K + stage $80K + loc $50K + set $60K + trans $30K + catering $20K = $940K
#     true_net = 550K + 940K - 447.5K = $1,042,500
NM_EXPECTED = {
    "total_budget_usd": 1_980_000,
    "qualifying_spend_min_usd": 940_000,   # BTL only (conservative floor)
    "qualifying_spend_target_usd": 1_790_000,
    "credit_usd": 447_500,          # 1,790,000 * 0.25
    "economic_value_usd": 447_500,  # refundable
    "true_net_cost_usd": 1_042_500, # ATL+BTL - credit
    "atl_qualifies": True,
}

FIXTURE_NM = {
    "name": "New Mexico — $2M feature, 25% base credit",
    "jurisdiction": NM_JURISDICTION,
    "home_jurisdiction_id": "jur-us-nm",
    "line_items": NM_LINE_ITEMS,
    "programs_with_categories": [{
        "program": NM_PROGRAM,
        "qualifying_categories": NM_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
}


# ===========================================================================
# OREGON
# ===========================================================================
OR_JURISDICTION = {
    "id": "jur-us-or",
    "name": "Oregon",
    "currency_code": "USD",
    "country_code": "US",
}

OR_PROGRAM = {
    "id": "prog-or-opif",
    "slug": "or_opif",
    "program_type": "cash_rebate",
    "base_rate": 0.20,
    "max_rate": 0.20,
    "is_refundable": True,    # cash rebate = refundable equivalent
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": True,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# OR: Oregon-based expenditures broadly (ATL and BTL both qualify)
OR_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",     "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",     "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "post_production", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",            "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "music",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "sound",          "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",       "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",     "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",       "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous", "qualifies": True, "jurisdiction_spend_only": True},
]

# Budget: $2,620,000 — Oregon production, all Oregon-based
# ATL qualifies under OPIF
OR_LINE_ITEMS = [
    # ATL
    {"description": "Director Fee",     "department": "ATL", "amount_usd": 300_000},
    {"description": "Lead Cast",        "department": "ATL", "amount_usd": 500_000},
    # BTL Labor
    {"description": "Crew Labor",       "department": "BTL", "amount_usd": 700_000},
    # BTL Non-labor
    {"description": "Equipment Rental", "department": "BTL", "amount_usd": 150_000},
    {"description": "Stage Rental",     "department": "BTL", "amount_usd": 100_000},
    {"description": "Location Fees",    "department": "BTL", "amount_usd":  80_000},
    {"description": "Set Construction", "department": "BTL", "amount_usd":  80_000},
    {"description": "Transportation",   "department": "BTL", "amount_usd":  40_000},
    {"description": "Catering",         "department": "BTL", "amount_usd":  30_000},
    # Post
    {"description": "VFX",              "department": "Post", "amount_usd": 200_000},
    {"description": "Post Production",  "department": "Post", "amount_usd": 150_000},
    {"description": "Music Score",      "department": "Post", "amount_usd":  70_000},
    # Non-qualifying
    {"description": "Insurance",        "department": "Other", "amount_usd":  80_000},
    {"description": "Completion Bond",  "department": "Other", "amount_usd":  60_000},
    {"description": "Contingency",      "department": "Other", "amount_usd":  80_000},
]

# Hand-verified:
#   Qualifying (ATL+BTL+Post): dir $300K + cast $500K + crew $700K + equip $150K
#     + stage $100K + loc $80K + set $80K + trans $40K + cat $30K
#     + VFX $200K + post $150K + music $70K = $2,400,000
#   Credit at 20%: $480,000
#   Economic value (cash rebate / refundable = face): $480,000
#   Engine true_net_cost: ATL+BTL - credit
#     ATL: director $300K + cast $500K = $800K
#     BTL: crew $700K + equip $150K + stage $100K + loc $80K + set $80K + trans $40K + cat $30K = $1,180K
#     true_net = 800K + 1,180K - 480K = $1,500,000
OR_EXPECTED = {
    "total_budget_usd": 2_620_000,
    "qualifying_spend_min_usd": 1_180_000,  # BTL only (conservative floor)
    "qualifying_spend_target_usd": 2_400_000,
    "credit_usd": 480_000,          # 2,400,000 * 0.20
    "economic_value_usd": 480_000,  # cash rebate = face value
    "true_net_cost_usd": 1_500_000, # ATL+BTL - credit
    "atl_qualifies": True,
}

FIXTURE_OR = {
    "name": "Oregon — $2.6M feature, 20% OPIF rebate",
    "jurisdiction": OR_JURISDICTION,
    "home_jurisdiction_id": "jur-us-or",
    "line_items": OR_LINE_ITEMS,
    "programs_with_categories": [{
        "program": OR_PROGRAM,
        "qualifying_categories": OR_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
}
