"""
Canadian incentive program validation fixtures — source-backed rates, deterministic.

Sources:
  ON OPSTC: OMDC program guidelines; Ontario Reg 37/09 under Corporations Tax Act
  ON OFTTC: OMDC program guidelines; Ontario Reg 37/09; CAVCO certification
  BC PSTC:  Creative BC program guidelines; BC Income Tax Act ss.91-93
  QC QPRDP: SODEC program guidelines; Quebec Taxation Act § 1029.8.34
  CPTC:     CRA T4283 guide; Income Tax Act § 125.4

All rates PARSED — see 0006 migration for confidence tier rationale.
All amounts in CAD, treated as face-value USD (no fx_rates passed — tests verify mechanics only).

Hand-verified expected outputs documented in each EXPECTED dict below.
Math annotations show each step of the calculation.
"""
from __future__ import annotations

# ===========================================================================
# ONTARIO — Production Services Tax Credit (OPSTC)
# ===========================================================================

ON_OPSTC_JURISDICTION = {
    "id": "jur-ca-on",
    "name": "Ontario",
    "currency_code": "CAD",
    "country_code": "CA",
}

ON_OPSTC_PROGRAM = {
    "id": "prog-on-opstc",
    "slug": "on_opstc",
    "program_type": "tax_credit",
    "base_rate": 0.215,
    "max_rate": 0.215,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# OPSTC — broad qualifying: BTL labour + BTL non-labour + Post (ATL excluded)
ON_OPSTC_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",             "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",       "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor","qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "post_production",      "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "vfx",                  "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "music",                "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "sound",                "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes",      "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",        "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",          "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",               "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "lodging",              "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous",        "qualifies": True,  "jurisdiction_spend_only": True},
]

# ---------------------------------------------------------------------------
# Budget: C$2,500,000 — Ontario service production, broad OPSTC eligibility
#
# Line-item classification:
#   Director Fee         → atl_director      → ATL, is_fixed   → NOT qualifying
#   Lead Cast            → atl_cast          → ATL, is_fixed   → NOT qualifying
#   Ontario Crew Labor   → btl_crew_labor    → BTL, variable   → qualifying
#   Equipment Rental     → btl_equipment_rental → BTL          → qualifying
#   Stage Rental         → btl_stage_facility   → BTL          → qualifying
#   Set Construction     → btl_set_construction → BTL          → qualifying
#   Post Production      → post_production   → Post            → qualifying
#   VFX                  → vfx               → Post            → qualifying
#   Sound Mix            → sound             → Post            → qualifying
#   Insurance            → insurance         → Other           → NOT qualifying
#   Completion Bond      → completion_bond   → Other           → NOT qualifying
#   Contingency          → contingency       → Other           → NOT qualifying
#
# Budget breakdown:
#   fixed_atl     = 200K + 300K = 500,000
#   variable_btl  = 800K + 200K + 150K + 100K = 1,250,000
#   post          = 200K + 150K + 100K = 450,000
#   other         = 100K + 100K + 100K = 300,000
#   total_input   = 2,500,000
#
# Qualifying spend:
#   btl_crew_labor:      800,000
#   btl_equipment_rental:200,000
#   btl_stage_facility:  150,000
#   btl_set_construction:100,000
#   post_production:     200,000
#   vfx:                 150,000
#   sound:               100,000
#   Total qualifying:  1,700,000
#
# Credit:
#   OPSTC (21.5%): 1,700,000 * 0.215 = 365,500
#   Economic value (refundable):       365,500
#
# True net cost:
#   fixed_atl + variable_btl - economic_value
#   = 500,000 + 1,250,000 - 365,500 = 1,384,500
# ---------------------------------------------------------------------------

ON_OPSTC_LINE_ITEMS = [
    # ATL — excluded from OPSTC
    {"description": "Director Fee",        "department": "ATL", "amount_usd": 200_000},
    {"description": "Lead Cast",           "department": "ATL", "amount_usd": 300_000},
    # BTL Labour
    {"description": "Ontario Crew Labor",  "department": "BTL", "amount_usd": 800_000},
    # BTL Non-labour
    {"description": "Equipment Rental",    "department": "BTL", "amount_usd": 200_000},
    {"description": "Stage Rental",        "department": "BTL", "amount_usd": 150_000},
    {"description": "Set Construction",    "department": "BTL", "amount_usd": 100_000},
    # Post
    {"description": "Post Production",     "department": "Post", "amount_usd": 200_000},
    {"description": "VFX",                 "department": "Post", "amount_usd": 150_000},
    {"description": "Sound Mix",           "department": "Post", "amount_usd": 100_000},
    # Non-qualifying
    {"description": "Insurance",           "department": "Other", "amount_usd": 100_000},
    {"description": "Completion Bond",     "department": "Other", "amount_usd": 100_000},
    {"description": "Contingency",         "department": "Other", "amount_usd": 100_000},
]

ON_OPSTC_TOTAL_BUDGET = sum(i["amount_usd"] for i in ON_OPSTC_LINE_ITEMS)  # 2,500,000

ON_OPSTC_EXPECTED = {
    "total_budget_usd":         2_500_000,
    "qualifying_spend_usd":     1_700_000,
    "credit_usd":                 365_500,   # 1,700,000 * 0.215
    "economic_value_usd":         365_500,   # refundable → full face value
    "true_net_cost_usd":        1_384_500,   # 500K + 1,250K - 365.5K
    "qualifying_spend_min_usd":   800_000,   # at minimum: btl_crew_labor alone
}

FIXTURE_ON_OPSTC = {
    "name": "Ontario OPSTC — 21.5% broad spend credit",
    "description": "C$2.5M Ontario service production, OPSTC 21.5% on Ontario-eligible expenditures",
    "jurisdiction": ON_OPSTC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-on",
    "line_items": ON_OPSTC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": ON_OPSTC_PROGRAM,
        "qualifying_categories": ON_OPSTC_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},
}


# ===========================================================================
# ONTARIO — Film and Television Tax Credit (OFTTC)
# ===========================================================================

ON_OFTTC_JURISDICTION = {
    "id": "jur-ca-on",
    "name": "Ontario",
    "currency_code": "CAD",
    "country_code": "CA",
}

ON_OFTTC_PROGRAM = {
    "id": "prog-on-ofttc",
    "slug": "on_ofttc",
    "program_type": "tax_credit",
    "base_rate": 0.35,
    "max_rate": 0.35,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# OFTTC — labour only; ATL qualifies if Ontario resident
ON_OFTTC_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",         "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",           "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",         "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",             "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",       "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor","qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes",      "qualifies": True,  "jurisdiction_spend_only": True},
    # Non-labour — excluded
    {"spend_category": "btl_equipment_rental", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "post_production",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",                  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "music",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "sound",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",        "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",          "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",               "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous",        "qualifies": False, "jurisdiction_spend_only": True},
]

# ---------------------------------------------------------------------------
# Budget: C$2,000,000 — Ontario Canadian production with CAVCO certification
#
# Line-item classification:
#   Ontario Resident Director → atl_director      (matches "director$") → ATL, is_fixed → qualifying
#   Ontario Resident Cast     → atl_cast           (matches "cast$")     → ATL, is_fixed → qualifying
#   Ontario Resident Crew     → btl_resident_labor (matches "resident.*crew") → BTL → qualifying
#   Ontario Crew Labor        → btl_crew_labor     (matches "crew") → BTL → qualifying
#   Equipment Rental          → btl_equipment_rental → BTL → NOT qualifying (non-labour)
#   Post Production           → post_production    → Post → NOT qualifying (non-labour)
#   Insurance                 → insurance          → Other → NOT qualifying
#   Completion Bond           → completion_bond    → Other → NOT qualifying
#
# Budget breakdown:
#   fixed_atl     = 200K + 200K = 400,000
#   variable_btl  = 600K + 400K + 200K = 1,200,000
#   post          = 200,000 (post_production)
#   other         = 200,000 (insurance + completion bond)
#   total_input   = 2,000,000
#
# Qualifying spend (labour only):
#   atl_director:       200,000
#   atl_cast:           200,000
#   btl_resident_labor: 600,000
#   btl_crew_labor:     400,000
#   Total qualifying: 1,400,000
#
# Credit:
#   OFTTC (35%): 1,400,000 * 0.35 = 490,000
#   Economic value (refundable):     490,000
#
# True net cost:
#   fixed_atl + variable_btl - economic_value
#   = 400,000 + 1,200,000 - 490,000 = 1,110,000
# ---------------------------------------------------------------------------

ON_OFTTC_LINE_ITEMS = [
    # ATL — Ontario resident key creative → qualify under OFTTC
    # Use "Director Fee" / "Lead Cast" so the classifier matches via non-anchored sub-patterns
    # ("director fee" and "lead cast") even when department "ATL" is appended to search_text.
    {"description": "Director Fee",             "department": "ATL", "amount_usd": 200_000},
    {"description": "Lead Cast",                "department": "ATL", "amount_usd": 200_000},
    # BTL Labour
    {"description": "Ontario Resident Crew",     "department": "BTL", "amount_usd": 600_000},
    {"description": "Ontario Crew Labor",        "department": "BTL", "amount_usd": 400_000},
    # BTL Non-labour (excluded from OFTTC)
    {"description": "Equipment Rental",          "department": "BTL", "amount_usd": 200_000},
    # Post (excluded from OFTTC labour basis)
    {"description": "Post Production",           "department": "Post", "amount_usd": 200_000},
    # Non-qualifying
    {"description": "Insurance",                 "department": "Other", "amount_usd": 100_000},
    {"description": "Completion Bond",           "department": "Other", "amount_usd": 100_000},
]

ON_OFTTC_TOTAL_BUDGET = sum(i["amount_usd"] for i in ON_OFTTC_LINE_ITEMS)  # 2,000,000

ON_OFTTC_EXPECTED = {
    "total_budget_usd":         2_000_000,
    "qualifying_spend_usd":     1_400_000,   # ATL (200K+200K) + BTL labour (600K+400K)
    "credit_usd":                 490_000,   # 1,400,000 * 0.35
    "economic_value_usd":         490_000,   # refundable → full face value
    "true_net_cost_usd":        1_110_000,   # 400K + 1,200K - 490K
    "qualifying_spend_min_usd":   600_000,   # at minimum: btl_resident_labor alone
}

FIXTURE_ON_OFTTC = {
    "name": "Ontario OFTTC — 35% labour credit, CAVCO-certified",
    "description": "C$2.0M Ontario Canadian production, OFTTC 35% on Ontario-eligible labour",
    "jurisdiction": ON_OFTTC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-on",
    "line_items": ON_OFTTC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": ON_OFTTC_PROGRAM,
        "qualifying_categories": ON_OFTTC_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},
}


# ===========================================================================
# BRITISH COLUMBIA — Production Services Tax Credit (PSTC)
# ===========================================================================

BC_PSTC_JURISDICTION = {
    "id": "jur-ca-bc",
    "name": "British Columbia",
    "currency_code": "CAD",
    "country_code": "CA",
}

BC_PSTC_PROGRAM = {
    "id": "prog-bc-pstc",
    "slug": "bc_pstc",
    "program_type": "tax_credit",
    "base_rate": 0.28,
    "max_rate": 0.34,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# BC PSTC — labour only; ATL excluded
BC_PSTC_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",             "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",       "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor","qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes",      "qualifies": True,  "jurisdiction_spend_only": True},
    # Non-labour — excluded
    {"spend_category": "btl_equipment_rental", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "post_production",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",                  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "music",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "sound",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",        "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",          "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",               "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous",        "qualifies": False, "jurisdiction_spend_only": True},
]

BC_REGIONAL_UPLIFT = {
    "id": "uplift-bc-regional",
    "name": "BC Regional Production Uplift",
    "additional_rate": 0.06,
    "applies_to": "same_qualifying_spend",
    "condition_type": "shooting_location",
    "condition_threshold": None,
    "condition_text": "bc_regional",
    "is_stackable_with_other_uplifts": False,
    "confidence_tier": "PARSED",
}

# ---------------------------------------------------------------------------
# Budget: C$2,000,000 — BC service production, labour-only
#
# Line-item classification:
#   BC Crew Labor        → btl_crew_labor    (matches "crew") → BTL → qualifying
#   BC Resident Crew     → btl_resident_labor (matches "resident.*crew") → BTL → qualifying
#   Equipment Rental     → btl_equipment_rental → BTL → NOT qualifying (non-labour)
#   Stage Rental         → btl_stage_facility   → BTL → NOT qualifying
#   Post Production      → post_production      → Post → NOT qualifying
#   Insurance            → insurance            → Other → NOT qualifying
#   Completion Bond      → completion_bond      → Other → NOT qualifying
#
# Budget breakdown:
#   fixed_atl     = 0 (no ATL in this fixture)
#   variable_btl  = 800K + 500K + 200K + 150K = 1,650,000
#   post          = 200,000
#   other         = 150,000 (insurance 100K + completion bond 50K)
#   total_input   = 2,000,000
#
# Qualifying spend (labour only):
#   btl_crew_labor:      800,000
#   btl_resident_labor:  500,000
#   Total qualifying:  1,300,000
#
# Base credit (28%):
#   1,300,000 * 0.28 = 364,000
#   Economic value (refundable): 364,000
#   True net: 0 + 1,650,000 - 364,000 = 1,286,000
#
# With regional uplift (28% + 6% = 34%):
#   1,300,000 * 0.34 = 442,000
#   Economic value (refundable): 442,000
#   True net: 0 + 1,650,000 - 442,000 = 1,208,000
# ---------------------------------------------------------------------------

BC_PSTC_LINE_ITEMS = [
    # BTL Labour — qualifies
    {"description": "BC Crew Labor",       "department": "BTL", "amount_usd": 800_000},
    {"description": "BC Resident Crew",    "department": "BTL", "amount_usd": 500_000},
    # BTL Non-labour — excluded from PSTC
    {"description": "Equipment Rental",    "department": "BTL", "amount_usd": 200_000},
    {"description": "Stage Rental",        "department": "BTL", "amount_usd": 150_000},
    # Post — excluded from PSTC
    {"description": "Post Production",     "department": "Post", "amount_usd": 200_000},
    # Non-qualifying
    {"description": "Insurance",           "department": "Other", "amount_usd": 100_000},
    {"description": "Completion Bond",     "department": "Other", "amount_usd":  50_000},
]

BC_PSTC_TOTAL_BUDGET = sum(i["amount_usd"] for i in BC_PSTC_LINE_ITEMS)  # 2,000,000

BC_PSTC_EXPECTED_BASE = {
    "total_budget_usd":         2_000_000,
    "qualifying_spend_usd":     1_300_000,   # btl_crew (800K) + btl_resident (500K)
    "credit_usd":                 364_000,   # 1,300,000 * 0.28
    "economic_value_usd":         364_000,   # refundable → full face value
    "true_net_cost_usd":        1_286_000,   # 0 + 1,650K - 364K
    "qualifying_spend_min_usd":   500_000,   # at minimum: btl_resident_labor alone
}

BC_PSTC_EXPECTED_REGIONAL = {
    "total_budget_usd":         2_000_000,
    "qualifying_spend_usd":     1_300_000,
    "credit_usd":                 442_000,   # 1,300,000 * 0.34 (28% + 6% regional)
    "economic_value_usd":         442_000,   # refundable → full face value
    "true_net_cost_usd":        1_208_000,   # 0 + 1,650K - 442K
}

FIXTURE_BC_PSTC_BASE = {
    "name": "BC PSTC — 28% base labour credit",
    "description": "C$2.0M BC service production, PSTC 28% on BC-eligible labour, Metro Vancouver",
    "jurisdiction": BC_PSTC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-bc",
    "line_items": BC_PSTC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": BC_PSTC_PROGRAM,
        "qualifying_categories": BC_PSTC_QUALIFYING_CATEGORIES,
        "uplifts": [BC_REGIONAL_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},  # no shooting_location → regional uplift does NOT fire
}

FIXTURE_BC_PSTC_REGIONAL = {
    "name": "BC PSTC — 34% with regional uplift",
    "description": "C$2.0M BC service production in BC regional location, PSTC 28% + 6% regional",
    "jurisdiction": BC_PSTC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-bc",
    "line_items": BC_PSTC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": BC_PSTC_PROGRAM,
        "qualifying_categories": BC_PSTC_QUALIFYING_CATEGORIES,
        "uplifts": [BC_REGIONAL_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {"shooting_location": "bc_regional"},
}


# ===========================================================================
# QUEBEC — Production Tax Credit (QPRDP — service production variant)
# ===========================================================================

QC_JURISDICTION = {
    "id": "jur-ca-qc",
    "name": "Quebec",
    "currency_code": "CAD",
    "country_code": "CA",
}

QC_PROGRAM = {
    "id": "prog-qc-qprdp",
    "slug": "qc_film_production",
    "program_type": "tax_credit",
    "base_rate": 0.20,
    "max_rate": 0.20,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# QC QPRDP — labour only; ATL excluded
QC_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",             "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",       "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor","qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes",      "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "post_production",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",                  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "music",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "sound",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",        "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",          "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",               "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous",        "qualifies": False, "jurisdiction_spend_only": True},
]

# ---------------------------------------------------------------------------
# Budget: C$2,500,000 — Quebec service production, labour-only
#
# Line-item classification:
#   Quebec Crew Labor    → btl_crew_labor    → BTL → qualifying
#   Quebec Resident Crew → btl_resident_labor → BTL → qualifying
#   Equipment Rental     → btl_equipment_rental → BTL → NOT qualifying
#   Post Production      → post_production   → Post → NOT qualifying
#   Insurance            → insurance         → Other → NOT qualifying
#   Completion Bond      → completion_bond   → Other → NOT qualifying
#
# Budget breakdown:
#   fixed_atl     = 0
#   variable_btl  = 1,000K + 500K + 300K = 1,800,000
#   post          = 400,000
#   other         = 300,000
#   total_input   = 2,500,000
#
# Qualifying spend (labour only):
#   btl_crew_labor:    1,000,000
#   btl_resident_labor:  500,000
#   Total qualifying: 1,500,000
#
# Credit (20%):
#   1,500,000 * 0.20 = 300,000
#   Economic value (refundable): 300,000
#   True net: 0 + 1,800,000 - 300,000 = 1,500,000
# ---------------------------------------------------------------------------

QC_LINE_ITEMS = [
    {"description": "Quebec Crew Labor",    "department": "BTL", "amount_usd": 1_000_000},
    {"description": "Quebec Resident Crew", "department": "BTL", "amount_usd":   500_000},
    {"description": "Equipment Rental",     "department": "BTL", "amount_usd":   300_000},
    {"description": "Post Production",      "department": "Post", "amount_usd":  400_000},
    {"description": "Insurance",            "department": "Other", "amount_usd": 150_000},
    {"description": "Completion Bond",      "department": "Other", "amount_usd": 150_000},
]

QC_TOTAL_BUDGET = sum(i["amount_usd"] for i in QC_LINE_ITEMS)  # 2,500,000

QC_EXPECTED = {
    "total_budget_usd":         2_500_000,
    "qualifying_spend_usd":     1_500_000,   # btl_crew (1,000K) + btl_resident (500K)
    "credit_usd":                 300_000,   # 1,500,000 * 0.20
    "economic_value_usd":         300_000,   # refundable → full face value
    "true_net_cost_usd":        1_500_000,   # 0 + 1,800K - 300K
    "qualifying_spend_min_usd":   500_000,   # at minimum: btl_resident_labor alone
}

FIXTURE_QC = {
    "name": "Quebec QPRDP — 20% labour credit, service production",
    "description": "C$2.5M Quebec service production, QPRDP 20% on Quebec-eligible labour",
    "jurisdiction": QC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-qc",
    "line_items": QC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": QC_PROGRAM,
        "qualifying_categories": QC_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},
}


# ===========================================================================
# FEDERAL CANADA — Canadian Film or Video Production Tax Credit (CPTC)
# ===========================================================================

CA_FEDERAL_JURISDICTION = {
    "id": "jur-ca",
    "name": "Canada",
    "currency_code": "CAD",
    "country_code": "CA",
}

CA_CPTC_PROGRAM = {
    "id": "prog-ca-cptc",
    "slug": "ca_federal_cptc",
    "program_type": "tax_credit",
    "base_rate": 0.25,
    "max_rate": 0.25,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# Federal CPTC — Canadian labour only; ATL qualifies if Canadian resident key creative
CA_CPTC_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",         "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",           "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",         "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",             "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",           "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_crew_labor",       "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",   "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor","qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes",      "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "post_production",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "vfx",                  "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "music",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "sound",                "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "finance_costs",        "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond",      "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",          "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "travel",               "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous",        "qualifies": False, "jurisdiction_spend_only": True},
]

# ---------------------------------------------------------------------------
# Budget: C$3,000,000 — CAVCO-certified Canadian feature
#
# Line-item classification:
#   Canadian Director    → atl_director      → ATL, is_fixed  → qualifying (QCLE key creative)
#   Canadian Lead Cast   → atl_cast          → ATL, is_fixed  → qualifying (QCLE key creative)
#   Canadian Crew Labor  → btl_crew_labor    → BTL            → qualifying (QCLE)
#   Equipment Rental     → btl_equipment_rental → BTL         → NOT qualifying (non-labour)
#   Post Production      → post_production   → Post           → NOT qualifying
#   Insurance            → insurance         → Other          → NOT qualifying
#   Completion Bond      → completion_bond   → Other          → NOT qualifying
#
# Budget breakdown:
#   fixed_atl     = 300K + 500K = 800,000
#   variable_btl  = 1,000K + 400K = 1,400,000
#   post          = 500,000
#   other         = 300,000
#   total_input   = 3,000,000
#
# Qualifying spend (Canadian labour — QCLE):
#   atl_director:    300,000
#   atl_cast:        500,000
#   btl_crew_labor: 1,000,000
#   Total QCLE:     1,800,000
#
# Credit (25%):
#   1,800,000 * 0.25 = 450,000
#   Economic value (refundable): 450,000
#   True net: 800,000 + 1,400,000 - 450,000 = 1,750,000
# ---------------------------------------------------------------------------

CA_CPTC_LINE_ITEMS = [
    # ATL — Canadian resident key creative → qualify under CPTC
    # Use "Director Fee" / "Lead Cast" — non-anchored sub-patterns survive department appending.
    {"description": "Director Fee",         "department": "ATL", "amount_usd":   300_000},
    {"description": "Lead Cast",            "department": "ATL", "amount_usd":   500_000},
    # BTL Labour — Canadian crew → qualify under CPTC
    {"description": "Canadian Crew Labor",  "department": "BTL", "amount_usd": 1_000_000},
    # BTL Non-labour — excluded from QCLE
    {"description": "Equipment Rental",     "department": "BTL", "amount_usd":   400_000},
    # Post — excluded from QCLE
    {"description": "Post Production",      "department": "Post", "amount_usd":  500_000},
    # Non-qualifying
    {"description": "Insurance",            "department": "Other", "amount_usd": 150_000},
    {"description": "Completion Bond",      "department": "Other", "amount_usd": 150_000},
]

CA_CPTC_TOTAL_BUDGET = sum(i["amount_usd"] for i in CA_CPTC_LINE_ITEMS)  # 3,000,000

CA_CPTC_EXPECTED = {
    "total_budget_usd":         3_000_000,
    "qualifying_spend_usd":     1_800_000,   # ATL (300K+500K) + btl_crew (1,000K)
    "credit_usd":                 450_000,   # 1,800,000 * 0.25
    "economic_value_usd":         450_000,   # refundable → full face value
    "true_net_cost_usd":        1_750_000,   # 800K + 1,400K - 450K
    "qualifying_spend_min_usd":   800_000,   # at minimum: ATL (300K+500K) alone
}

FIXTURE_CA_CPTC = {
    "name": "Federal CPTC — 25% Canadian labour credit, CAVCO-certified",
    "description": "C$3.0M CAVCO-certified Canadian feature, CPTC 25% on qualified Canadian labour",
    "jurisdiction": CA_FEDERAL_JURISDICTION,
    "home_jurisdiction_id": "jur-ca",
    "line_items": CA_CPTC_LINE_ITEMS,
    "programs_with_categories": [{
        "program": CA_CPTC_PROGRAM,
        "qualifying_categories": CA_CPTC_QUALIFYING_CATEGORIES,
        "uplifts": [],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},
}
