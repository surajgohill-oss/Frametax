"""
California and Louisiana validation fixtures — source-backed rates, deterministic.

Sources:
  CA: CA Gov Code § 17053.98; California Film Commission (film.ca.gov)
  LA: LA RS § 47:6007; Louisiana Entertainment (louisianaentertainment.gov)

All rates PARSED — see 0005 migration for confidence tier rationale.

Hand-verified expected outputs documented in each EXPECTED dict below.
"""
from __future__ import annotations

# ===========================================================================
# CALIFORNIA
# ===========================================================================
CA_JURISDICTION = {
    "id": "jur-us-ca",
    "name": "California",
    "currency_code": "USD",
    "country_code": "US",
}

CA_PROGRAM = {
    "id": "prog-ca-film30",
    "slug": "ca_film_30",
    "program_type": "tax_credit",
    "base_rate": 0.20,
    "max_rate": 0.30,
    "is_refundable": False,
    "is_transferable": True,
    "transferable_value_pct": 0.92,
    "is_competitive": True,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# ATL excluded; BTL + Post qualify when incurred in California
CA_QUALIFYING_CATEGORIES = [
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
    {"spend_category": "vfx",             "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "music",           "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "sound",           "qualifies": True, "jurisdiction_spend_only": True},
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

CA_VFX_UPLIFT = {
    "id": "uplift-ca-vfx",
    "name": "California VFX Uplift",
    "additional_rate": 0.05,
    "applies_to": "vfx_spend_only",
    "condition_type": "",
    "condition_threshold": None,
    "condition_text": "",
    "is_stackable_with_other_uplifts": True,
    "confidence_tier": "PARSED",
}

CA_MUSIC_UPLIFT = {
    "id": "uplift-ca-music",
    "name": "California Music Recording Uplift",
    "additional_rate": 0.05,
    "applies_to": "music_spend_only",
    "condition_type": "",
    "condition_threshold": None,
    "condition_text": "",
    "is_stackable_with_other_uplifts": True,
    "confidence_tier": "PARSED",
}

CA_INDIE_UPLIFT = {
    "id": "uplift-ca-indie",
    "name": "California Independent Film Uplift",
    "additional_rate": 0.05,
    "applies_to": "same_qualifying_spend",
    "condition_type": "budget_under",
    "condition_threshold": 10_000_000,
    "condition_text": "Independent film: budget <= $10,000,000",
    "is_stackable_with_other_uplifts": True,
    "confidence_tier": "PARSED",
}

# ---------------------------------------------------------------------------
# Budget: $3,500,000 — California feature film, 100% shot in CA
# ATL excluded from CA qualified wages (§ 17053.98 BTL-only credit)
#
# Line-item classification (via classify_line_item):
#   Director Fee      → atl_director     → ATL → NOT qualifying
#   Lead Cast         → atl_cast         → ATL → NOT qualifying
#   Crew Labor        → btl_crew_labor   → BTL → qualifying
#   Equipment Rental  → btl_equipment_rental  → BTL → qualifying
#   Stage Rental      → btl_stage_facility    → BTL → qualifying
#   Location Fees     → btl_location_fees     → BTL → qualifying
#   Set Construction  → btl_set_construction  → BTL → qualifying
#   Transportation    → btl_transportation    → BTL → qualifying
#   Catering          → btl_catering          → BTL → qualifying
#   VFX               → vfx               → Post → qualifying (VFX uplift basis)
#   Post Production   → post_production   → Post → qualifying
#   Music Score       → music             → Post → qualifying (music uplift basis)
#   Sound Mix         → sound             → Post → qualifying
#   Insurance         → insurance         → Other → NOT qualifying
#   Completion Bond   → completion_bond   → Other → NOT qualifying
#   Contingency       → contingency       → Other → NOT qualifying
#   Finance Costs     → finance_costs     → Other → NOT qualifying
#
# Expected qualifying spend:
#   BTL:  $900K + $200K + $150K + $100K + $80K + $50K + $30K = $1,510,000
#   Post: $300K + $150K + $100K + $60K = $610,000
#   Total qualifying: $2,120,000
#
# Credit:
#   Base (20%): $2,120,000 * 0.20         = $424,000
#   VFX uplift (5% of $300K VFX):          =  $15,000
#   Music uplift (5% of $100K music):      =   $5,000
#   Total credit:                           = $444,000
#   Economic value (non-refundable, 92%):  = $408,480  ($444,000 * 0.92)
#
# True net cost (ATL + BTL - economic_value):
#   fixed_atl    = $400K + $700K = $1,100,000
#   variable_btl = $900K + $200K + $150K + $100K + $80K + $50K + $30K = $1,510,000
#   true_net     = $1,100,000 + $1,510,000 - $408,480 = $2,201,520
# ---------------------------------------------------------------------------
CA_LINE_ITEMS = [
    # ATL — excluded from CA qualified wages
    {"description": "Director Fee",         "department": "ATL", "amount_usd": 400_000},
    {"description": "Lead Cast",            "department": "ATL", "amount_usd": 700_000},
    # BTL Labor
    {"description": "Crew Labor",           "department": "BTL", "amount_usd": 900_000},
    # BTL Non-labor
    {"description": "Equipment Rental",     "department": "BTL", "amount_usd": 200_000},
    {"description": "Stage Rental",         "department": "BTL", "amount_usd": 150_000},
    {"description": "Location Fees",        "department": "BTL", "amount_usd": 100_000},
    {"description": "Set Construction",     "department": "BTL", "amount_usd":  80_000},
    {"description": "Transportation",       "department": "BTL", "amount_usd":  50_000},
    {"description": "Catering",             "department": "BTL", "amount_usd":  30_000},
    # Post
    {"description": "VFX",                 "department": "Post", "amount_usd": 300_000},
    {"description": "Post Production",     "department": "Post", "amount_usd": 150_000},
    {"description": "Music Score",         "department": "Post", "amount_usd": 100_000},
    {"description": "Sound Mix",           "department": "Post", "amount_usd":  60_000},
    # Non-qualifying
    {"description": "Insurance",           "department": "Other", "amount_usd":  90_000},
    {"description": "Completion Bond",     "department": "Other", "amount_usd":  70_000},
    {"description": "Contingency",         "department": "Other", "amount_usd":  80_000},
    {"description": "Finance Costs",       "department": "Other", "amount_usd":  40_000},
]

CA_TOTAL_BUDGET = sum(item["amount_usd"] for item in CA_LINE_ITEMS)  # 3_500_000

CA_EXPECTED = {
    "total_budget_usd": 3_500_000,
    "qualifying_spend_usd": 2_120_000,   # BTL ($1,510K) + Post ($610K)
    "base_credit_usd": 424_000,          # $2,120,000 * 0.20
    "vfx_uplift_usd": 15_000,            # $300,000 * 0.05
    "music_uplift_usd": 5_000,           # $100,000 * 0.05
    "total_credit_usd": 444_000,         # 424K + 15K + 5K
    "economic_value_usd": 408_480,       # $444,000 * 0.92 (non-refundable, transferable)
    "true_net_cost_usd": 2_201_520,      # $1,100K + $1,510K - $408,480
}

FIXTURE_CA = {
    "name": "California Film & TV Tax Credit 3.0 — 20% base + VFX/music uplifts",
    "description": "$3.5M CA feature, 20% base + 5% VFX + 5% music uplifts, competitive allocation",
    "jurisdiction": CA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ca",
    "line_items": CA_LINE_ITEMS,
    "programs_with_categories": [{
        "program": CA_PROGRAM,
        "qualifying_categories": CA_QUALIFYING_CATEGORIES,
        "uplifts": [CA_VFX_UPLIFT, CA_MUSIC_UPLIFT, CA_INDIE_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    # production_details: no total_budget_usd set → budget_under(10M) fires False
    # (budget is $3.5M but production_details doesn't have total_budget_usd key)
    "production_details": {},
}


# ===========================================================================
# LOUISIANA
# ===========================================================================
LA_JURISDICTION = {
    "id": "jur-us-la",
    "name": "Louisiana",
    "currency_code": "USD",
    "country_code": "US",
}

LA_PROGRAM = {
    "id": "prog-la-film",
    "slug": "la_film_production",
    "program_type": "tax_credit",
    "base_rate": 0.25,
    "max_rate": 0.35,
    "is_refundable": True,
    "is_transferable": True,
    "transferable_value_pct": 0.90,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "PARSED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

# ATL qualifies as Louisiana-certified expenditure (RS § 47:6007)
# btl_resident_labor has a +10% uplift; all btl and post qualify
LA_QUALIFYING_CATEGORIES = [
    {"spend_category": "atl_director",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",  "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",      "qualifies": True, "jurisdiction_spend_only": True},
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
    {"spend_category": "vfx",             "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "music",           "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "sound",           "qualifies": True, "jurisdiction_spend_only": True},
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

LA_RESIDENT_UPLIFT = {
    "id": "uplift-la-resident",
    "name": "Louisiana Resident Payroll Uplift",
    "additional_rate": 0.10,
    "applies_to": "resident_labor_only",
    "condition_type": "",
    "condition_threshold": None,
    "condition_text": "",
    "is_stackable_with_other_uplifts": True,
    "confidence_tier": "PARSED",
}

# ---------------------------------------------------------------------------
# Budget: $2,630,000 — Louisiana feature film, 100% shot in Louisiana
# ATL qualifies under LA RS § 47:6007 (broad definition of certified costs)
# btl_resident_labor qualifies for both 25% base AND 10% resident uplift
#
# Line-item classification (via classify_line_item):
#   Director Fee               → atl_director       → ATL → qualifying (LA)
#   Lead Cast                  → atl_cast            → ATL → qualifying (LA)
#   Crew Labor                 → btl_crew_labor      → BTL → qualifying
#   Louisiana Resident Labor   → btl_resident_labor  → BTL → qualifying + uplift basis
#   Equipment Rental           → btl_equipment_rental → BTL → qualifying
#   Stage Rental               → btl_stage_facility   → BTL → qualifying
#   Location Fees              → btl_location_fees    → BTL → qualifying
#   Transportation             → btl_transportation   → BTL → qualifying
#   Catering                   → btl_catering         → BTL → qualifying
#   VFX                        → vfx                  → Post → qualifying
#   Post Production            → post_production      → Post → qualifying
#   Music Score                → music                → Post → qualifying
#   Sound Mix                  → sound                → Post → qualifying
#   Insurance                  → insurance            → Other → NOT qualifying
#   Completion Bond            → completion_bond      → Other → NOT qualifying
#   Contingency                → contingency          → Other → NOT qualifying
#
# Expected qualifying spend:
#   ATL:  $350K + $550K = $900,000
#   BTL:  $600K + $300K + $150K + $100K + $80K + $40K + $20K = $1,290,000
#   Post: $100K + $80K + $50K + $30K = $260,000
#   Total qualifying: $2,450,000
#   Resident labor basis: $300,000
#
# Credit:
#   Base (25%): $2,450,000 * 0.25          = $612,500
#   Resident uplift (10% of $300K):        =  $30,000
#   Total credit:                           = $642,500
#   Economic value (refundable = face):    = $642,500
#
# True net cost:
#   fixed_atl    = $350K + $550K = $900,000
#   variable_btl = $600K + $300K + $150K + $100K + $80K + $40K + $20K = $1,290,000
#   true_net     = $900,000 + $1,290,000 - $642,500 = $1,547,500
# ---------------------------------------------------------------------------
LA_LINE_ITEMS = [
    # ATL — qualifies under Louisiana (RS § 47:6007)
    {"description": "Director Fee",              "department": "ATL", "amount_usd": 350_000},
    {"description": "Lead Cast",                 "department": "ATL", "amount_usd": 550_000},
    # BTL Labor
    {"description": "Crew Labor",                "department": "BTL", "amount_usd": 600_000},
    {"description": "Louisiana Resident Labor",  "department": "BTL", "amount_usd": 300_000},
    # BTL Non-labor
    {"description": "Equipment Rental",          "department": "BTL", "amount_usd": 150_000},
    {"description": "Stage Rental",              "department": "BTL", "amount_usd": 100_000},
    {"description": "Location Fees",             "department": "BTL", "amount_usd":  80_000},
    {"description": "Transportation",            "department": "BTL", "amount_usd":  40_000},
    {"description": "Catering",                  "department": "BTL", "amount_usd":  20_000},
    # Post
    {"description": "VFX",                      "department": "Post", "amount_usd": 100_000},
    {"description": "Post Production",          "department": "Post", "amount_usd":  80_000},
    {"description": "Music Score",              "department": "Post", "amount_usd":  50_000},
    {"description": "Sound Mix",               "department": "Post", "amount_usd":  30_000},
    # Non-qualifying
    {"description": "Insurance",               "department": "Other", "amount_usd":  70_000},
    {"description": "Completion Bond",         "department": "Other", "amount_usd":  50_000},
    {"description": "Contingency",             "department": "Other", "amount_usd":  60_000},
]

LA_TOTAL_BUDGET = sum(item["amount_usd"] for item in LA_LINE_ITEMS)  # 2_630_000

LA_EXPECTED = {
    "total_budget_usd": 2_630_000,
    "qualifying_spend_usd": 2_450_000,   # ATL ($900K) + BTL ($1,290K) + Post ($260K)
    "qualifying_spend_min_usd": 1_550_000,  # BTL + Post minimum (if ATL excluded)
    "resident_labor_usd": 300_000,        # btl_resident_labor basis for uplift
    "base_credit_usd": 612_500,           # $2,450,000 * 0.25
    "resident_uplift_usd": 30_000,        # $300,000 * 0.10
    "total_credit_usd": 642_500,          # 612.5K + 30K
    "economic_value_usd": 642_500,        # refundable = face value
    "true_net_cost_usd": 1_547_500,       # $900K + $1,290K - $642,500
}

FIXTURE_LA = {
    "name": "Louisiana Motion Picture Production Tax Credit — 25% base + resident labor uplift",
    "description": "$2.63M Louisiana feature, 25% base + 10% resident labor uplift, refundable",
    "jurisdiction": LA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-la",
    "line_items": LA_LINE_ITEMS,
    "programs_with_categories": [{
        "program": LA_PROGRAM,
        "qualifying_categories": LA_QUALIFYING_CATEGORIES,
        "uplifts": [LA_RESIDENT_UPLIFT],
        "jurisdiction_spend_pct": 1.0,
    }],
    "stacking_rules": [],
    "production_details": {},
}
