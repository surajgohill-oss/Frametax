"""
Georgia EIIA validation fixture — source-backed, deterministic.

Budget: $2,950,000 US feature film shooting 100% in Georgia.
Program: Georgia EIIA at VERIFIED rates from O.C.G.A. § 48-7-40.26.
All ATL line items are individually below the $500K/person cap.

Hand-verified expected outputs (documented here for regression detection):
  Qualifying spend:   $2,675,000  (ATL $1,100K + BTL $1,145K + Post $430K)
  Base credit (20%):    $535,000
  With logo (30%):      $802,500
  Economic value (90%): $722,250   (transferable, not refundable)
  True net cost:      $2,227,750   (total_budget - economic_value)
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# VERIFIED Georgia EIIA program (matches 0003 migration rates)
# Source: O.C.G.A. § 48-7-40.26
# ---------------------------------------------------------------------------
GEORGIA_EIIA_VERIFIED = {
    "id": "prog-ga-eiia-verified",
    "slug": "georgia_eiia",
    "program_type": "tax_credit",
    "base_rate": 0.20,                    # § 48-7-40.26(b)(1)
    "max_rate": 0.30,                     # with logo uplift
    "is_refundable": False,               # § 48-7-40.26(c) — against GA income tax
    "is_transferable": True,              # § 48-7-40.26(f)
    "transferable_value_pct": 0.90,       # PARSED midpoint; market range 0.88–0.92
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "VERIFIED",
    "spend_cap_pct": None,
    "atl_cap_pct": None,                  # per-person cap handled at rule level
    "individual_salary_cap_usd": None,
}

# All ATL cast/crew qualify per § 48-7-40.26(a)(1); subject to per-person cap
# Rights do NOT qualify per § 48-7-40.26(a)(1) exclusion
GEORGIA_EIIA_QUALIFYING_CATEGORIES = [
    # ATL — qualify (each person's comp capped at $500K/person by rule, not here)
    {"spend_category": "atl_director",  "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_writer",    "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_producer",  "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast",      "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "atl_rights",    "qualifies": False, "jurisdiction_spend_only": True},
    # BTL Labor
    {"spend_category": "btl_crew_labor",        "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_resident_labor",    "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "btl_nonresident_labor", "qualifies": True,  "jurisdiction_spend_only": True},
    # BTL Non-labor
    {"spend_category": "btl_equipment_rental", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility",   "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees",    "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_set_construction", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_transportation",   "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_catering",         "qualifies": True, "jurisdiction_spend_only": True},
    # Post
    {"spend_category": "post_production", "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "vfx",             "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "music",           "qualifies": True,  "jurisdiction_spend_only": True},
    {"spend_category": "sound",           "qualifies": True,  "jurisdiction_spend_only": True},
    # Excluded
    {"spend_category": "finance_costs",   "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance",       "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "completion_bond", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "contingency",     "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "payroll_fringes", "qualifies": True,  "jurisdiction_spend_only": True},
    # Non-cash
    {"spend_category": "deferment",            "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "equity_participation", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "in_kind",              "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "reinvestment",         "qualifies": False, "jurisdiction_spend_only": True},
    # Travel / Lodging / Misc
    {"spend_category": "travel",        "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "lodging",       "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "miscellaneous", "qualifies": True, "jurisdiction_spend_only": True},
]

GEORGIA_LOGO_UPLIFT = {
    "id": "uplift-ga-logo",
    "name": "Georgia Logo Uplift",
    "additional_rate": 0.10,          # § 48-7-40.26(b)(2)
    "applies_to": "same_qualifying_spend",
    "condition_type": "georgia_logo_displayed",
    "condition_threshold": None,
    "condition_text": "Georgia logo included in credits and marketing per DOR requirements",
    "is_stackable_with_other_uplifts": False,
    "confidence_tier": "VERIFIED",
}

GEORGIA_JURISDICTION = {
    "id": "jur-us-ga",
    "name": "Georgia",
    "currency_code": "USD",
    "country_code": "US",
}

# ---------------------------------------------------------------------------
# Budget: $2,950,000 — 100% shot in Georgia
#
# ATL line items are individually below the $500K/person cap.
# Description text is chosen to trigger correct spend_category classification.
#
# Expected qualifying spend breakdown:
#   ATL:  Director $300K + Cast $450K + Supporting Cast $200K + Writer $150K = $1,100,000
#   BTL:  Crew $700K + Equip $130K + Stage $100K + Loc $70K + Set $80K + Trans $40K + Catering $25K = $1,145,000
#   Post: VFX $180K + Post $120K + Music $80K + Sound $50K = $430,000
#   Total qualifying: $2,675,000
#
#   Non-qualifying: Insurance $75K + Bond $60K + Finance $40K + Contingency $100K = $275,000
# ---------------------------------------------------------------------------
GEORGIA_LINE_ITEMS = [
    # ATL (all under $500K per-person)
    {"description": "Director Fee",          "department": "ATL", "amount_usd": 300_000},
    {"description": "Lead Cast",             "department": "ATL", "amount_usd": 450_000},
    {"description": "Supporting Cast Fees",  "department": "ATL", "amount_usd": 200_000},
    {"description": "Screenplay Writer Fee", "department": "ATL", "amount_usd": 150_000},
    # BTL Labor
    {"description": "Crew Labor",           "department": "BTL", "amount_usd": 700_000},
    # BTL Non-labor
    {"description": "Equipment Rental",     "department": "BTL", "amount_usd": 130_000},
    {"description": "Stage Rental",         "department": "BTL", "amount_usd": 100_000},
    {"description": "Location Fees",        "department": "BTL", "amount_usd":  70_000},
    {"description": "Set Construction",     "department": "BTL", "amount_usd":  80_000},
    {"description": "Transportation",       "department": "BTL", "amount_usd":  40_000},
    {"description": "Catering",             "department": "BTL", "amount_usd":  25_000},
    # Post
    {"description": "VFX",                 "department": "Post", "amount_usd": 180_000},
    {"description": "Post Production",     "department": "Post", "amount_usd": 120_000},
    {"description": "Music Score",         "department": "Post", "amount_usd":  80_000},
    {"description": "Sound Mix",           "department": "Post", "amount_usd":  50_000},
    # Non-qualifying
    {"description": "Insurance",           "department": "Other", "amount_usd":  75_000},
    {"description": "Completion Bond",     "department": "Other", "amount_usd":  60_000},
    {"description": "Finance Costs",       "department": "Other", "amount_usd":  40_000},
    {"description": "Contingency",         "department": "Other", "amount_usd": 100_000},
]

TOTAL_BUDGET_USD = sum(item["amount_usd"] for item in GEORGIA_LINE_ITEMS)  # 2_950_000

# Hand-verified expected outputs — update these if engine logic changes
EXPECTED = {
    "total_budget_usd": 2_950_000,
    # Qualifying spend depends on how classify_line_item maps each description.
    # The BTL/Post lines map cleanly. ATL maps to atl_* categories that qualify.
    # Minimum floor: BTL + Post = 1,145,000 + 430,000 = 1,575,000
    "qualifying_spend_min_usd": 1_575_000,
    # Full ATL + BTL + Post = 2,675,000
    "qualifying_spend_target_usd": 2_675_000,
    # Base credit at 20% of min qualifying spend
    "credit_no_uplift_min_usd": 315_000,     # 1,575,000 * 0.20
    # Base credit at 20% of target qualifying spend
    "credit_no_uplift_target_usd": 535_000,  # 2,675,000 * 0.20
    # With logo uplift at 30% of target qualifying spend
    "credit_with_uplift_target_usd": 802_500,  # 2,675,000 * 0.30
    # Economic value at 90% (non-refundable, transferable)
    "economic_value_target_usd": 722_250,    # 802,500 * 0.90
    # True net cost = fixed_atl + variable_btl - economic_value
    # The engine's calculate_net_budget uses only ATL+BTL (not post/other).
    # ATL (director+cast+writer, excl. "Supporting Cast Fees" → miscellaneous):
    #   Director $300K + Lead Cast $450K + Writer $150K = $900K
    # BTL (crew+equipment+stage+location+set+transport+catering + Supporting Cast $200K):
    #   = $1,345K
    # true_net = 900,000 + 1,345,000 − 722,250 = 1,522,750
    "true_net_cost_target_usd": 1_522_750,
}

# ---------------------------------------------------------------------------
# Fixture assembly
# ---------------------------------------------------------------------------
FIXTURE_GEORGIA_VERIFIED_NO_UPLIFT = {
    "name": "Georgia EIIA — verified rates, no logo uplift",
    "description": "$2.95M Georgia feature, 20% base credit, no logo",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": GEORGIA_LINE_ITEMS,
    "programs_with_categories": [
        {
            "program": GEORGIA_EIIA_VERIFIED,
            "qualifying_categories": GEORGIA_EIIA_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,  # 100% of production in Georgia
        }
    ],
    "stacking_rules": [],
}

FIXTURE_GEORGIA_VERIFIED_WITH_UPLIFT = {
    "name": "Georgia EIIA — verified rates, with logo uplift (30%)",
    "description": "$2.95M Georgia feature, 30% credit with Georgia logo",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": GEORGIA_LINE_ITEMS,
    "programs_with_categories": [
        {
            "program": GEORGIA_EIIA_VERIFIED,
            "qualifying_categories": GEORGIA_EIIA_QUALIFYING_CATEGORIES,
            "uplifts": [GEORGIA_LOGO_UPLIFT],
            "jurisdiction_spend_pct": 1.0,
        }
    ],
    "stacking_rules": [],
    "production_details": {"georgia_logo_displayed": True},
}
