"""
Synthetic project fixtures for validation testing.
All values are invented for testing only — not real production data.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Shared: a Georgia incentive program at 20% base rate (DISCOVERY)
# ---------------------------------------------------------------------------
GEORGIA_PROGRAM = {
    "id": "prog-ga-eiia",
    "slug": "georgia_eiia",
    "program_type": "tax_credit",
    "base_rate": 0.20,
    "max_rate": 0.30,
    "is_refundable": False,
    "is_transferable": True,
    "transferable_value_pct": 0.90,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "DISCOVERY",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

GEORGIA_QUALIFYING_CATEGORIES = [
    {"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_director", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "insurance", "qualifies": False, "jurisdiction_spend_only": False},
    {"spend_category": "finance_costs", "qualifies": False, "jurisdiction_spend_only": False},
]

GEORGIA_JURISDICTION = {
    "id": "jur-us-ga",
    "name": "Georgia",
    "currency_code": "USD",
    "country_code": "US",
}

NY_PROGRAM = {
    "id": "prog-ny-state",
    "slug": "ny_state_film",
    "program_type": "tax_credit",
    "base_rate": 0.25,
    "max_rate": 0.30,
    "is_refundable": True,
    "is_transferable": False,
    "transferable_value_pct": None,
    "is_competitive": False,
    "annual_cap_local": None,
    "confidence_tier": "DISCOVERY",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

NY_QUALIFYING_CATEGORIES = [
    {"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_director", "qualifies": False, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast", "qualifies": False, "jurisdiction_spend_only": True},
]

ONTARIO_PSTC_PROGRAM = {
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
    "confidence_tier": "DISCOVERY",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

ONTARIO_QUALIFYING_CATEGORIES = [
    {"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_equipment_rental", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_stage_facility", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "btl_location_fees", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_cast", "qualifies": False, "jurisdiction_spend_only": True},
]

ONTARIO_JURISDICTION = {
    "id": "jur-ca-on",
    "name": "Ontario",
    "currency_code": "CAD",
    "country_code": "CA",
}


# ---------------------------------------------------------------------------
# FIXTURE 1: Simple US domestic shoot — Georgia, single program, all cash
# ---------------------------------------------------------------------------
FIXTURE_1_US_DOMESTIC = {
    "name": "US Domestic — Georgia, $3M feature",
    "description": "Simple single-state shoot, all BTL in Georgia, DISCOVERY-tier credit",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 250_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 600_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 800_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 150_000},
        {"description": "Stage Rental", "department": "BTL", "amount_usd": 100_000},
        {"description": "Location Fees", "department": "BTL", "amount_usd": 80_000},
        {"description": "Catering", "department": "BTL", "amount_usd": 40_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 60_000},
        {"description": "Completion Bond", "department": "Other", "amount_usd": 50_000},
        {"description": "VFX", "department": "Post", "amount_usd": 200_000},
        {"description": "Editing and Color", "department": "Post", "amount_usd": 100_000},
        {"description": "Music Score", "department": "Post", "amount_usd": 80_000},
        {"description": "Contingency", "department": "Other", "amount_usd": 90_000},
    ],
    "programs_with_categories": [
        {
            "program": GEORGIA_PROGRAM,
            "qualifying_categories": GEORGIA_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        }
    ],
    "expected": {
        "fixed_atl_usd": 850_000,  # director + lead cast
        "total_input_budget_usd": 2_600_000,  # excl. not-classified correctly
        "has_incentive_value": True,
        "stacking_ok": True,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 2: Canadian province shoot — Ontario PSTC, resident/non-resident labor
# ---------------------------------------------------------------------------
FIXTURE_2_CANADA_ONTARIO = {
    "name": "Canadian Province — Ontario PSTC, $5M feature",
    "description": "Foreign production in Ontario; 80% of BTL labor is Ontario resident labor",
    "jurisdiction": ONTARIO_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ny",
    "fx_rates": {"CAD": 1.36},  # 1 USD = 1.36 CAD
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 300_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 700_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 1_200_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 250_000},
        {"description": "Stage Rental", "department": "BTL", "amount_usd": 200_000},
        {"description": "Location Fees", "department": "BTL", "amount_usd": 120_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 80_000},
        {"description": "VFX", "department": "Post", "amount_usd": 400_000},
        {"description": "Post Production", "department": "Post", "amount_usd": 250_000},
        {"description": "Music Score", "department": "Post", "amount_usd": 100_000},
        {"description": "Contingency", "department": "Other", "amount_usd": 150_000},
    ],
    "programs_with_categories": [
        {
            "program": ONTARIO_PSTC_PROGRAM,
            "qualifying_categories": ONTARIO_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 0.80,  # 80% of qualifying spend in Ontario
        }
    ],
    "production_details": {
        "local_labor_pct": 0.80,
        "total_budget_usd": 3_750_000,
    },
    "expected": {
        "has_incentive_value": True,
        "stacking_ok": True,
        "risk_level": "high",  # DISCOVERY tier
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 3: ATL cap applied — program limits ATL qualifying spend to 25% of budget
# ---------------------------------------------------------------------------
FIXTURE_3_ATL_CAP = {
    "name": "ATL Cap — $4M feature with inflated above-the-line",
    "description": "Director and cast fees are large; program caps ATL at 25% of total budget",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 750_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 1_500_000},
        {"description": "Writer Fee", "department": "ATL", "amount_usd": 250_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 600_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 200_000},
        {"description": "Location Fees", "department": "BTL", "amount_usd": 100_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 100_000},
    ],
    "programs_with_categories": [
        {
            "program": {**GEORGIA_PROGRAM, "atl_cap_pct": 0.25},
            "qualifying_categories": GEORGIA_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        }
    ],
    "expected": {
        "atl_cap_applied": True,
        "stacking_ok": True,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 4: BTL local labor — jurisdiction_spend_pct < 1.0
# ---------------------------------------------------------------------------
FIXTURE_4_BTL_LOCAL_LABOR = {
    "name": "BTL Local Labor — 60% of crew in jurisdiction",
    "description": "$2M film, only 60% of BTL spend qualifies as local",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 200_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 400_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 800_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 200_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 50_000},
    ],
    "programs_with_categories": [
        {
            "program": GEORGIA_PROGRAM,
            "qualifying_categories": GEORGIA_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 0.60,  # 60% local
        }
    ],
    "expected": {
        "qualifying_spend_lt_total": True,
        "stacking_ok": True,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 5: Deferred and equity compensation
# ---------------------------------------------------------------------------
FIXTURE_5_DEFERRED_COMPENSATION = {
    "name": "Deferred Compensation — $1.5M indie with deferred fees",
    "description": "Director and writer take deferred fees — non-cash, excluded from qualifying spend",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "line_items": [
        {"description": "Director deferred fee", "department": "ATL", "amount_usd": 200_000},
        {"description": "Writer deferred fee", "department": "ATL", "amount_usd": 100_000},
        {"description": "Lead Cast equity participation", "department": "ATL", "amount_usd": 150_000},
        {"description": "Crew labor (cash)", "department": "BTL", "amount_usd": 500_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 150_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 30_000},
    ],
    "programs_with_categories": [
        {
            "program": GEORGIA_PROGRAM,
            "qualifying_categories": GEORGIA_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        }
    ],
    "expected": {
        "has_deferred": True,  # classifier should mark compensation_type=deferred
        "stacking_ok": True,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 6: Regional uplift placeholder
# ---------------------------------------------------------------------------
GEORGIA_LOGO_UPLIFT = {
    "id": "uplift-ga-logo",
    "name": "Georgia Logo Uplift",
    "additional_rate": 0.10,
    "applies_to": "same_qualifying_spend",
    "condition_type": "uses_logo",
    "condition_threshold": None,
    "condition_text": "",
}

FIXTURE_6_REGIONAL_UPLIFT = {
    "name": "Regional Uplift — Georgia with 10% logo bonus",
    "description": "Production uses Georgia promotional logo, triggering +10% uplift",
    "jurisdiction": GEORGIA_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ga",
    "production_details": {"uses_georgia_logo": True},
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 200_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 400_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 600_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 150_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 50_000},
    ],
    "programs_with_categories": [
        {
            "program": GEORGIA_PROGRAM,
            "qualifying_categories": GEORGIA_QUALIFYING_CATEGORIES,
            "uplifts": [GEORGIA_LOGO_UPLIFT],
            "jurisdiction_spend_pct": 1.0,
        }
    ],
    "expected": {
        "uplift_applied": True,
        "effective_rate_above_base": True,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 7: Legal stacking ALLOWED — Ontario PSTC + federal CPTC (different basis)
# ---------------------------------------------------------------------------
CA_FEDERAL_CPTC_PROGRAM = {
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
    "confidence_tier": "DISCOVERY",
    "spend_cap_pct": None,
    "atl_cap_pct": None,
    "individual_salary_cap_usd": None,
}

CA_FEDERAL_CPTC_QUALIFYING = [
    {"spend_category": "btl_crew_labor", "qualifies": True, "jurisdiction_spend_only": True},
    {"spend_category": "atl_director", "qualifies": True, "jurisdiction_spend_only": True},
]

FIXTURE_7_STACKING_ALLOWED = {
    "name": "Legal Stacking ALLOWED — Ontario PSTC + federal CPTC",
    "description": "Foreign production claiming provincial PSTC and federal CPTC — allowed with different basis",
    "jurisdiction": ONTARIO_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ny",
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 300_000},
        {"description": "Lead Cast", "department": "ATL", "amount_usd": 600_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 900_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 300_000},
        {"description": "Insurance", "department": "Other", "amount_usd": 80_000},
    ],
    "programs_with_categories": [
        {
            "program": ONTARIO_PSTC_PROGRAM,
            "qualifying_categories": ONTARIO_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 0.90,
        },
        {
            "program": CA_FEDERAL_CPTC_PROGRAM,
            "qualifying_categories": CA_FEDERAL_CPTC_QUALIFYING,
            "uplifts": [],
            "jurisdiction_spend_pct": 0.90,
        },
    ],
    "stacking_rules": [
        {
            "program_a_id": "prog-on-opstc",
            "program_b_id": "prog-ca-cptc",
            "rule_type": "allowed",
            "condition_text": None,
            "statutory_reference": None,
            "confidence_tier": "DISCOVERY",
            "notes": "PSTC and federal CPTC can stack — different credit bases",
        }
    ],
    "expected": {
        "stacking_ok": True,
        "legal_review_required": False,
        "program_count": 2,
    },
}


# ---------------------------------------------------------------------------
# FIXTURE 8: Legal stacking PROHIBITED — two programs that cannot combine
# ---------------------------------------------------------------------------
FIXTURE_8_STACKING_PROHIBITED = {
    "name": "Legal Stacking PROHIBITED — two conflicting programs",
    "description": "Two programs with a PROHIBITED stacking rule — engine must flag violation",
    "jurisdiction": ONTARIO_JURISDICTION,
    "home_jurisdiction_id": "jur-us-ny",
    "line_items": [
        {"description": "Director Fee", "department": "ATL", "amount_usd": 300_000},
        {"description": "Crew labor", "department": "BTL", "amount_usd": 900_000},
        {"description": "Equipment Rental", "department": "BTL", "amount_usd": 200_000},
    ],
    "programs_with_categories": [
        {
            "program": ONTARIO_PSTC_PROGRAM,
            "qualifying_categories": ONTARIO_QUALIFYING_CATEGORIES,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
        {
            "program": CA_FEDERAL_CPTC_PROGRAM,
            "qualifying_categories": CA_FEDERAL_CPTC_QUALIFYING,
            "uplifts": [],
            "jurisdiction_spend_pct": 1.0,
        },
    ],
    "stacking_rules": [
        {
            "program_a_id": "prog-on-opstc",
            "program_b_id": "prog-ca-cptc",
            "rule_type": "prohibited",
            "condition_text": "Cannot claim both PSTC and CPTC on the same production",
            "statutory_reference": "CRA IT-441",
            "confidence_tier": "DISCOVERY",
            "notes": "PROVISIONAL — rule needs legal verification",
        }
    ],
    "expected": {
        "stacking_ok": False,
        "legal_review_required": True,
        "violation_count": 1,
    },
}


ALL_FIXTURES = [
    FIXTURE_1_US_DOMESTIC,
    FIXTURE_2_CANADA_ONTARIO,
    FIXTURE_3_ATL_CAP,
    FIXTURE_4_BTL_LOCAL_LABOR,
    FIXTURE_5_DEFERRED_COMPENSATION,
    FIXTURE_6_REGIONAL_UPLIFT,
    FIXTURE_7_STACKING_ALLOWED,
    FIXTURE_8_STACKING_PROHIBITED,
]
