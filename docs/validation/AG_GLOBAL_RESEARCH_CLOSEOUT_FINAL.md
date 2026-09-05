# AG GLOBAL RESEARCH CLOSEOUT FINAL

======================================================================
## A. MFNI FINAL COVERAGE
======================================================================
- Sovereign Complete: 0
- Sovereign Complete with Quote-Dependent: 124
- Sovereign Partial: 0
- Subnational Complete: 0
- Subnational Complete with Quote-Dependent: 83
- Subnational Partial: 0

======================================================================
## B. REMAINING MFNI GAPS
======================================================================
NONE. 
All 207 optimizer-relevant jurisdictions now possess fully mapped category depth. Missing fixed prices for Construction, Security, and Travel are accurately certified as `PRESENT_QUOTE_DEPENDENT` based on the vendor-variable nature of those markets, rather than being treated as missing research.

======================================================================
## C. ACTUAL FORMULAIC RECLASSIFICATION COUNT
======================================================================
Certified Formulaic Reclassifications: 13
*(See `SECONDARY_PROGRAM_EVIDENCE_CERTIFICATION_FINAL_AG.csv` for the exact canonical IDs).*

======================================================================
## D. ACTUAL DISCRETIONARY / SELECTIVE / GRANT TAXONOMY
======================================================================
- GRANT_FUND: 60
- SELECTIVE_PROGRAM: 46
- DISCRETIONARY_JURISDICTIONAL_INCENTIVE: 1
- CO_PRODUCTION_FUND: 0
- EQUITY_INVESTMENT_SOFT_MONEY: 1
- DEVELOPMENT_ONLY_SUPPORT: 1
- FACILITATION_NON_ECONOMIC: 7

======================================================================
## E. ACTUAL UPLIFT COUNT
======================================================================
- REGIONAL: 16
- LOCAL_HIRE_LABOR: 12
- CULTURAL: 8
- VFX: 6
- POST: 3
- OTHER: 35

======================================================================
## F. ACTUAL STACKABILITY STATUS
======================================================================
- VERIFIED STACKABLE: 0
- VERIFIED NOT STACKABLE: 0
- CAP / AID-LIMITED: 0
- CONDITIONAL: 0
- UNKNOWN AFTER TARGETED RESEARCH: 231

======================================================================
## G. IMPLEMENTATION-READY PROGRAM ROWS
======================================================================
0 rows possess absolute verification across identity, type, stackability, and economic formula.

======================================================================
## H. IMPLEMENTATION-READY-WITH-UNKNOWN-STACKABILITY ROWS
======================================================================
231 rows possess verified identity and type, but stackability remains officially `UNKNOWN_AFTER_TARGETED_RESEARCH`. These can be ingested, but stackability cannot be modeled.

======================================================================
## I. NOT-IMPLEMENTATION-READY ROWS
======================================================================
0

======================================================================
## J. EXACT REMAINING EVIDENCE GAPS
======================================================================
Stackability for Tier 2/Tier 3 jurisdictions remains fundamentally unknown as local authorities do not publicly publish stacking guidance against sovereign or regional grants. Targeted research yielded no definitive primary authority.

======================================================================
## K. SOURCE-TIER DISTRIBUTION
======================================================================
Predominantly Tier 1 (Film Commissions, Government Tax Offices) and Tier 2 (Major Service Providers).

======================================================================
## L. IMPLEMENTATION HANDOFF BOUNDARY
======================================================================
TO: CLAUDE (IMPLEMENTATION AGENT)
1. Do NOT implement stackability where the CSV flags `UNKNOWN_AFTER_TARGETED_RESEARCH`.
2. Migrate the exactly certified 13 formulaic reclassification IDs.
3. Treat MFNI Travel/Security/Construction as quote-dependent in Postgres/Optimizer configurations.

