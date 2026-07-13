"""
little_utopia_real_budget.py

The ACTUAL Little Utopia production budget, parsed from the real source
document — not a sanitized fixture, not a reconstruction. Every account
code, description, and amount below is a faithful snapshot of what
app.ingestion.budget_parser._parse_film_budget() extracts from:

    "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf"
    (Movie Magic Budgeting export, 60 pages, bare 4-digit account-code
    convention, top sheet on pages 1-2 with per-account page references,
    detail pages 3-60 with "Account Total for CODE" confirmation lines)

Reproduce with:
    from app.ingestion.pdf_extractor import extract_text_from_pdf
    from app.ingestion.budget_parser import parse_budget_from_text
    ex = extract_text_from_pdf(path_to_pdf)
    result = parse_budget_from_text(ex.raw_text, filename=ex.filename, pages=ex.pages)

RECONCILIATION NOTE (accepted, not a parser defect — see
docs/ engineering discussion; verified via two independent extraction
methods and two independent amount sources that agree with each other):

    Authoritative document total ("Grand Total", stated on the top sheet):
        AUTHORITATIVE_GROSS_BUDGET_USD = 4_364_393.0
    Sum of the 44 displayed leaf accounts below:
        LEAF_ACCOUNT_SUM_USD = 4_364_395.0
    Source-document rounding variance:
        RECONCILIATION_VARIANCE_USD = 2.0

The $2 variance traces to two independent $1 rounding artifacts already
present in the source spreadsheet's own subtotal lines: "BELOW THE LINE
- PRODUCTION" ($3,080,755 stated) is $1 short of the sum of its own 21
constituent leaf accounts ($3,080,756), and "Total Above and Below-The-
Line" ($4,015,081 stated) is $1 short of its own "Total Above-The-Line"
+ "Total Below-The-Line" ($538,444 + $3,476,638 = $4,015,082). Neither
is attributable to a single misparsed line. Per instruction: no
balancing entry is fabricated, no parsed line-item amount is altered,
and AUTHORITATIVE_GROSS_BUDGET_USD (not the leaf sum) is the production's
controlling gross budget for rate/NPC calculations — the leaf sum is
preserved alongside it, and the variance is surfaced (not hidden) via
optimization_engine.build_risk_cases()'s own existing reconciliation
warning mechanism.
"""
from __future__ import annotations

PRODUCTION_ID = "LITTLE-UTOPIA"
SOURCE_PDF_FILENAME = "The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf"
SOURCE_PDF_BUDGET_DATE = "2025-06-03"

AUTHORITATIVE_GROSS_BUDGET_USD = 4_364_393.0
LEAF_ACCOUNT_SUM_USD = 4_364_395.0
RECONCILIATION_VARIANCE_USD = 2.0
RECONCILIATION_NOTE = (
    "Authoritative document total (Grand Total, top sheet) is $4,364,393.00. "
    "The sum of the 44 displayed leaf accounts is $4,364,395.00 — a $2.00 "
    "source-document rounding variance (two independent $1 discrepancies "
    "already present in the source spreadsheet's own 'BELOW THE LINE - "
    "PRODUCTION' and 'Total Above and Below-The-Line' subtotal lines, "
    "confirmed via two independent extraction methods and two independent "
    "amount sources). Accepted, not corrected: no balancing entry is "
    "fabricated and no parsed amount is altered. AUTHORITATIVE_GROSS_BUDGET_USD "
    "is the production's controlling gross budget."
)

# ── The 44 real leaf accounts ────────────────────────────────────────────────
# (account_code, description, amount_usd, pdf_page_index)
# pdf_page_index is the exact pymupdf page (1-indexed) the "Account Total
# for CODE" confirmation line was read from — None for 8100/8200/8300
# (percentage-based top-sheet lines with no dedicated detail page).
LITTLE_UTOPIA_REAL_BUDGET_LINES: tuple[tuple[str, str, float, int | None], ...] = (
    ("1000", "DEVELOPMENT", 0.0, 3),
    ("1100", "SCRIPT", 5_050.0, 3),
    ("1200", "PRODUCERS UNIT", 0.0, 4),
    ("1300", "DIRECTION", 0.0, 4),
    ("1400", "CAST", 136_115.0, 7),
    ("1600", "ATL TRAVEL & LIVING", 397_279.0, 10),
    ("2000", "PRODUCTION STAFF", 321_594.0, 13),
    ("2100", "EXTRA TALENT", 21_981.0, 14),
    ("2200", "SET DESIGN", 65_873.0, 15),
    ("2300", "SET CONSTRUCTION", 107_628.0, 17),
    ("2400", "SET DRESSING", 154_826.0, 18),
    ("2500", "PROPERTIES", 68_854.0, 20),
    ("2600", "PICTURE VEHICLES AND ANIMALS", 215_218.0, 21),
    ("2700", "WARDROBE", 58_815.0, 23),
    ("2800", "MAKE-UP & HAIR", 51_809.0, 25),
    ("2900", "SET OPERATIONS", 90_679.0, 27),
    ("3000", "ELECTRICAL", 155_375.0, 29),
    ("3100", "CAMERA", 288_729.0, 32),
    ("3200", "PRODUCTION SOUND", 69_532.0, 33),
    ("3300", "SPECIAL EFFECTS & MARINE", 99_837.0, 34),
    ("3400", "LOCATION EXPENSE", 496_232.0, 39),
    ("3500", "AERIAL/DRONE UNIT", 16_215.0, 40),
    ("3600", "TRANSPORTATION", 321_899.0, 42),
    ("3700", "STAGE & OFFICE RENTALS", 27_732.0, 43),
    ("3800", "PRODUCTION LAB & MEDIA MANAGEMENT", 9_674.0, 43),
    ("3900", "BTL TRAVEL & LIVING", 438_254.0, 45),
    ("4000", "SPECIAL SHOOT UNITS", 0.0, 46),
    ("5000", "EDITORIAL", 9_068.0, 46),
    ("5100", "EDITORIAL - USA", 0.0, 47),
    ("5200", "SOUND POST PRODUCTION", 0.0, 49),
    ("5300", "PICTURE POST PRODUCTION", 0.0, 50),
    ("5400", "GRAPHICS / TITLES / STOCK FOOTAGE", 0.0, 50),
    ("5500", "DELIVERABLES", 0.0, 51),
    ("6000", "MUSIC", 0.0, 52),
    ("6100", "VFX DEPARTMENT", 52_500.0, 52),
    ("6500", "USA ADMIN COSTS", 0.0, 52),
    ("7000", "ADMINISTRATIVE EXPENSES", 297_593.0, 55),
    ("7100", "PUBLICITY", 24_348.0, 55),
    ("7200", "INSURANCE", 12_374.0, 56),
    ("7300", "MARKETING", 0.0, 56),
    ("7800", "FINANCE & LEGAL", 0.0, 57),
    ("8100", "Insurance : 1.2%", 48_181.0, None),
    ("8200", "Bond : 0.0%", 0.0, None),
    ("8300", "Contigency : 7.5%", 301_131.0, None),
)

# ── Spend-category classification ───────────────────────────────────────────
# Maps each real account code onto the SAME SpendCategory vocabulary
# app.data.program_spend_rules.MU_EDB_RULES already keys on — the
# statutory rules are shared with the fixture-based register; only the
# budget DATA and this classification are specific to the real document.
# Where a category admits no clean single match (Publicity, Marketing,
# general Administrative overhead not tied to a named QPE category, and
# Music — no category names composition/licensing), the account is left
# WITHOUT a spend_category override so the derivation ladder's own
# "no rule for this category" branch escalates it to
# GREY_AREA_REQUIRES_AUTHORITY / ABSENCE_OF_AUTHORITY — visible,
# disclosed, never silently included or excluded.
LITTLE_UTOPIA_REAL_SPEND_CATEGORY: dict[str, str] = {
    "1000": "atl_writer",              # DEVELOPMENT — screenplay development
    "1100": "atl_writer",              # SCRIPT
    "1200": "atl_producer",            # PRODUCERS UNIT
    "1300": "atl_director",            # DIRECTION
    "1400": "atl_cast",                # CAST
    "1600": "travel",                  # ATL TRAVEL & LIVING
    "2000": "btl_crew_labor",          # PRODUCTION STAFF
    "2100": "btl_crew_labor",          # EXTRA TALENT
    "2200": "btl_set_construction",    # SET DESIGN
    "2300": "btl_set_construction",    # SET CONSTRUCTION
    "2400": "btl_set_construction",    # SET DRESSING
    "2500": "btl_equipment_rental",    # PROPERTIES
    "2600": "btl_equipment_rental",    # PICTURE VEHICLES AND ANIMALS
    "2700": "btl_equipment_rental",    # WARDROBE ("Wardrobe rentals" — named QPE category)
    "2800": "btl_crew_labor",          # MAKE-UP & HAIR
    "2900": "btl_crew_labor",          # SET OPERATIONS
    "3000": "btl_equipment_rental",    # ELECTRICAL ("Rental of camera and lighting equipment")
    "3100": "btl_equipment_rental",    # CAMERA
    "3200": "btl_crew_labor",          # PRODUCTION SOUND
    "3300": "vessel_marine",           # SPECIAL EFFECTS & MARINE
    "3400": "btl_location_fees",       # LOCATION EXPENSE
    "3500": "btl_equipment_rental",    # AERIAL/DRONE UNIT ("Rental of helicopters and airplanes")
    "3600": "btl_transportation",      # TRANSPORTATION
    "3700": "btl_stage_facility",      # STAGE & OFFICE RENTALS
    "3800": "btl_equipment_rental",    # PRODUCTION LAB & MEDIA MANAGEMENT
    "3900": "travel",                  # BTL TRAVEL & LIVING (bundles travel/lodging/per diems)
    "4000": "btl_equipment_rental",    # SPECIAL SHOOT UNITS ($0)
    "5000": "post_production",         # EDITORIAL — budget header states "PICTURE EDIT: LA"
    "5100": "post_production",         # EDITORIAL - USA (name itself states USA)
    "5200": "sound",                   # SOUND POST PRODUCTION — header states "SOUND EDIT: LA"
    "5300": "post_production",         # PICTURE POST PRODUCTION
    "5400": "post_production",         # GRAPHICS / TITLES / STOCK FOOTAGE
    "5500": "post_production",         # DELIVERABLES
    "6000": "music",                   # MUSIC — no rule; no category names composition/licensing
    "6100": "vfx",                     # VFX DEPARTMENT — location not stated (unlike post/sound)
    "6500": "legal_accounting",        # USA ADMIN COSTS (name states USA; category choice moot at $0)
    # 7000 ADMINISTRATIVE EXPENSES, 7100 PUBLICITY, 7300 MARKETING: no
    # spend_category assigned — no QPE category plausibly covers general
    # admin overhead or publicity/marketing spend; left as a genuine,
    # disclosed grey area rather than assumed either way.
    "7200": "insurance",               # INSURANCE
    "7800": "legal_accounting",        # FINANCE & LEGAL ($0 — see note below)
    "8100": "insurance",               # Insurance : 1.2%
    "8200": "completion_bond",         # Bond : 0.0%
    "8300": "contingency",             # Contigency : 7.5%
}

# 7800 "FINANCE & LEGAL" bundles two concepts the derivation ladder treats
# differently (finance costs are NOT_APPLICABLE, modeled as a cashflow
# item; legal fees are a QPE category question) with no $ split available.
# The account is $0 in the real budget, so the classification choice
# (legal_accounting) is immaterial to any total — documented, not hidden.
FINANCE_LEGAL_ZERO_DOLLAR_NOTE = (
    "Account 7800 'FINANCE & LEGAL' bundles finance costs (would be "
    "NOT_APPLICABLE / cashflow-modeled) and legal fees (a QPE category "
    "question) in one line with no $ breakdown. Classified as "
    "legal_accounting for register purposes; the account is $0.00 in the "
    "real budget so this choice affects no total."
)

# ── Territorial facts ────────────────────────────────────────────────────────
# Accounts KNOWN (from the budget's own header text, or the account's own
# name) to be incurred outside Mauritius. "PICTURE EDIT: LA" / "SOUND
# EDIT: LA" are stated on the budget's cover page; "USA ADMIN COSTS" and
# "EDITORIAL - USA" name their own location. VFX (6100) is deliberately
# NOT in this set — its location is not stated anywhere in the budget,
# so per the canonical rule it is included provisionally rather than
# excluded on an assumed fact.
LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU: frozenset[str] = frozenset({
    "5000",  # EDITORIAL — "PICTURE EDIT: LA"
    "5100",  # EDITORIAL - USA
    "5200",  # SOUND POST PRODUCTION — "SOUND EDIT: LA"
    "5300",  # PICTURE POST PRODUCTION
    "5400",  # GRAPHICS / TITLES / STOCK FOOTAGE
    "5500",  # DELIVERABLES
    "6500",  # USA ADMIN COSTS
})

# No offshore-payroll fact is evidenced anywhere in the real budget (the
# fixture's "Frogsquad SPV" precedent was fixture-specific narrative, not
# independently verifiable against this document) — left empty rather
# than assumed. No account is held in STRUCTURING_OPPORTUNITY as a result.
LITTLE_UTOPIA_REAL_OFFSHORE_PAYROLL: frozenset[str] = frozenset()
