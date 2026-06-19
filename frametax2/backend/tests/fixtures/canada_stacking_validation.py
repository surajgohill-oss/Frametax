"""
Canadian stacking validation fixtures — NOHFC (discretionary_fund) proof-of-concept.

Tests the spend_reduction stacking interaction where a government grant must be
deducted from the qualifying expenditure base of downstream tax credits.

Sources (PARSED):
  NOHFC:  nohfc.ca program guidelines
  OFTTC:  OMDC guidelines; Ontario Reg 37/09 under Corporations Tax Act
  CPTC:   CRA T4283 guide; Income Tax Act § 125.4 ("government assistance" deduction)

All amounts CAD treated as face-value USD (fx_rates=None, tests verify stacking mechanics).

Hand-verified expected outputs with annotated math:
  OFTTC + NOHFC:  OFTTC credit reduced by grant × effective_rate
  CPTC  + NOHFC:  CPTC credit reduced by grant × effective_rate
"""
from __future__ import annotations

from tests.fixtures.canada_validation import (
    CA_CPTC_LINE_ITEMS,
    CA_CPTC_PROGRAM,
    CA_CPTC_QUALIFYING_CATEGORIES,
    CA_FEDERAL_JURISDICTION,
    ON_OFTTC_LINE_ITEMS,
    ON_OFTTC_PROGRAM,
    ON_OFTTC_QUALIFYING_CATEGORIES,
    ON_OFTTC_JURISDICTION,
)

# ---------------------------------------------------------------------------
# NOHFC program (discretionary_fund — fixed grant, not rate-based)
# ---------------------------------------------------------------------------

NOHFC_PROGRAM = {
    "id":                     "prog-nohfc",
    "slug":                   "nohfc_production_fund",
    "program_type":           "discretionary_fund",
    "base_rate":              None,
    "max_rate":               None,
    "is_refundable":          True,
    "is_transferable":        False,
    "transferable_value_pct": None,
    "is_competitive":         True,
    "annual_cap_local":       None,
    "fixed_grant_amount_usd": 500_000,
    "confidence_tier":        "PARSED",
    "spend_cap_pct":          None,
    "atl_cap_pct":            None,
    "individual_salary_cap_usd": None,
}

# NOHFC grants are fixed amounts — no qualifying spend categories
NOHFC_QUALIFYING_CATEGORIES: list[dict] = []


# ---------------------------------------------------------------------------
# Stacking rule: NOHFC → OFTTC (spend_reduction)
# ---------------------------------------------------------------------------

STACKING_RULE_NOHFC_OFTTC = {
    "program_a_id":       "prog-nohfc",
    "program_b_id":       "prog-on-ofttc",
    "rule_type":          "spend_reduction",
    "condition_text":     (
        "NOHFC grant reduces OFTTC qualifying labour expenditure basis "
        "(OMDC guidelines; Ontario Reg 37/09)"
    ),
    "statutory_reference": "Ontario Reg 37/09; OMDC OFTTC guidelines",
    "confidence_tier":    "PARSED",
    "notes":              "spend_reduction stacking",
}

# ---------------------------------------------------------------------------
# Stacking rule: NOHFC → CPTC (spend_reduction)
# ---------------------------------------------------------------------------

STACKING_RULE_NOHFC_CPTC = {
    "program_a_id":       "prog-nohfc",
    "program_b_id":       "prog-ca-cptc",
    "rule_type":          "spend_reduction",
    "condition_text":     (
        "Government assistance (NOHFC grant) deducted from QCLE before computing CPTC "
        "(ITA § 125.4; CRA T4283)"
    ),
    "statutory_reference": "ITA § 125.4(1); CRA T4283 Guide",
    "confidence_tier":    "PARSED",
    "notes":              "spend_reduction stacking",
}


# ===========================================================================
# Fixture A — OFTTC + NOHFC (spend_reduction)
# ===========================================================================
#
# OFTTC (from canada_validation.py):
#   qualifying_spend = 1,400,000 (ATL 400K + BTL labour 1,000K)
#   effective_rate   = 0.35
#   credit           = 490,000
#   economic_value   = 490,000  (refundable)
#
# NOHFC:
#   fixed_grant      = 500,000
#   economic_value   = 500,000
#
# Stacking spend_reduction:
#   reducible_spend  = min(500,000, 1,400,000) = 500,000
#   credit_reduction = 500,000 × 0.35 = 175,000
#   adjusted_OFTTC   = 490,000 − 175,000 = 315,000
#
# Total raw        = 490,000 + 500,000 = 990,000
# Total adjusted   = 315,000 + 500,000 = 815,000
# Stacking delta   = −175,000
#
# True net (uses adjusted):
#   fixed_atl(400K) + variable_btl(1,200K) − 815,000 = 785,000
# ===========================================================================

ON_OFTTC_NOHFC_EXPECTED = {
    "total_budget_usd":                      2_000_000,
    # Per-program raw values
    "ofttc_raw_value_usd":                     490_000,
    "nohfc_raw_value_usd":                     500_000,
    "total_raw_incentive_usd":                 990_000,
    # Stacking adjustment
    "stacking_adjustment_usd":                -175_000,   # 500K × 0.35
    "adjusted_ofttc_value_usd":                315_000,   # 490K − 175K
    # Post-stacking totals
    "total_adjusted_incentive_usd":            815_000,   # 315K + 500K
    # Net budget uses adjusted value
    "true_net_cost_usd":                       785_000,   # 400K + 1,200K − 815K
}

FIXTURE_ON_OFTTC_NOHFC = {
    "name": "Ontario OFTTC + NOHFC (spend_reduction stacking)",
    "description": (
        "C$2.0M Ontario Canadian production claiming both OFTTC (35% labour credit) and "
        "NOHFC ($500K discretionary grant). NOHFC grant reduces OFTTC qualifying spend basis."
    ),
    "jurisdiction": ON_OFTTC_JURISDICTION,
    "home_jurisdiction_id": "jur-ca-on",
    "line_items": ON_OFTTC_LINE_ITEMS,
    "programs_with_categories": [
        {
            "program": ON_OFTTC_PROGRAM,
            "qualifying_categories": ON_OFTTC_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
        {
            "program": NOHFC_PROGRAM,
            "qualifying_categories": NOHFC_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
    ],
    "stacking_rules": [STACKING_RULE_NOHFC_OFTTC],
    "production_details": {},
}


# ===========================================================================
# Fixture B — CPTC + NOHFC (spend_reduction)
# ===========================================================================
#
# CPTC (from canada_validation.py):
#   qualifying_spend = 1,800,000 (ATL 800K + btl_crew 1,000K)
#   effective_rate   = 0.25
#   credit           = 450,000
#   economic_value   = 450,000  (refundable)
#
# NOHFC:
#   fixed_grant      = 500,000
#   economic_value   = 500,000
#
# Stacking spend_reduction:
#   reducible_spend  = min(500,000, 1,800,000) = 500,000
#   credit_reduction = 500,000 × 0.25 = 125,000
#   adjusted_CPTC    = 450,000 − 125,000 = 325,000
#
# Total raw        = 450,000 + 500,000 = 950,000
# Total adjusted   = 325,000 + 500,000 = 825,000
# Stacking delta   = −125,000
#
# True net (uses adjusted):
#   fixed_atl(800K) + variable_btl(1,400K) − 825,000 = 1,375,000
# ===========================================================================

CA_CPTC_NOHFC_EXPECTED = {
    "total_budget_usd":                      3_000_000,
    # Per-program raw values
    "cptc_raw_value_usd":                      450_000,
    "nohfc_raw_value_usd":                     500_000,
    "total_raw_incentive_usd":                 950_000,
    # Stacking adjustment
    "stacking_adjustment_usd":                -125_000,   # 500K × 0.25
    "adjusted_cptc_value_usd":                 325_000,   # 450K − 125K
    # Post-stacking totals
    "total_adjusted_incentive_usd":            825_000,   # 325K + 500K
    # Net budget uses adjusted value
    "true_net_cost_usd":                     1_375_000,   # 800K + 1,400K − 825K
}

FIXTURE_CA_CPTC_NOHFC = {
    "name": "Federal CPTC + NOHFC (spend_reduction stacking)",
    "description": (
        "C$3.0M CAVCO-certified Canadian feature claiming both CPTC (25% labour credit) and "
        "NOHFC ($500K discretionary grant). Government assistance reduces CPTC QCLE basis."
    ),
    "jurisdiction": CA_FEDERAL_JURISDICTION,
    "home_jurisdiction_id": "jur-ca",
    "line_items": CA_CPTC_LINE_ITEMS,
    "programs_with_categories": [
        {
            "program": CA_CPTC_PROGRAM,
            "qualifying_categories": CA_CPTC_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
        {
            "program": NOHFC_PROGRAM,
            "qualifying_categories": NOHFC_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
    ],
    "stacking_rules": [STACKING_RULE_NOHFC_CPTC],
    "production_details": {},
}
