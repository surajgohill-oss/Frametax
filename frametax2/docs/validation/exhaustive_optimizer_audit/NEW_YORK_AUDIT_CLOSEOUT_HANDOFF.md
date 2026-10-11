# New York State Film & Post Tax Credit Audit Closeout Handoff

**Track:** Independent North American QPE Audit (New York Jurisdiction Closeout)  
**Auditor:** AG (Independent Anti-Circularity & Evidence Audit Track)  
**Recipient / Adjudicating Owner:** Codex / Canonical Engine Architecture Owners  
**Target Projects:** The Little Utopia (`LU`), F#K Valentine's Day (`FVD`), Bad Hombres (`BH`), Lips Like Sugar (`LLS`)  
**Engine Version Under Audit:** `canonical-1.106.0` (Saved DB State: `frametax2_claude_optimizer_acceptance_20260919`)  
**Remediation Baseline:** `canonical-1.107.0` (Commit `486bd15`, repairs F-01..F-07)  
**Gate Status:** **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**  
**Date:** 2026-10-10  

---

## 1. Executive Summary & Audit Mandate Compliance

In strict adherence to `PROJECT_RULES.md` (specifically the **AUDIT INPUT EVIDENCE GATE**, lines 178–190) and the primary statutory adjudications in `docs/validation/NY_AG_BDE0FEE_ADJUDICATION.md`, this closeout handoff delivers the comprehensive reconciliation of the New York State film tax credit programs across all four anchor projects.

### Two-Track Audit Assurance Architecture:
In compliance with the user directive, this assurance package is structured across two strictly separated tracks:
1. **Track 1: Evidenced Production Claims (Actual Legal Incurred Spend):**
   - Covers actual legal QPE and incurred-spend tax credit claims grounded in audited production evidence.
   - Where empirical facts (such as itemized crew travel hotel vs airfare breakdowns, general ledger payee contracts, or audited contingency disbursement records) are unavailable in budget files, actual legal QPE is kept strictly as **`NOT_ESTABLISHED`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**.
   - Zero assumed labour ratios, zero invented payee contracts, and zero converted unspent reserves under AUDIT INPUT EVIDENCE GATE Rules 2, 3, and 5.
2. **Track 2: Explicit Planning Scenarios (Producer Elections & Supported Statutory Bounds):**
   - Models producer relocation elections, contingency deployment scenarios, and rigorous statutory bounds [Floor .. Baseline .. Optimistic Ceiling] without inventing factual inputs.
   - Evaluates the producer's documented contingency election (100% deployment / $301,131.00 into qualifying physical production) strictly as a planning input, while distinguishing it from incurred-spend evidence (where it is an unspent reserve).
   - Establishes mathematical proofs that engine credit overstatements exist across **every single supported bound and scenario**, conclusively validating open engine defects (`NA-DEFECT-01`).

### Formal Withdrawal of Unsupported LU Figures & Single Dollar Claims (`RET-09`):
In accordance with Evidence Gate Rules 2, 3, and 5, all previously asserted single-dollar QPE figures and unsupported category substitutions on The Little Utopia are **FORMALLY WITHDRAWN**:
1. **Withdrawal of Fabricated BTL Travel Amount:** The previously asserted BTL travel amount of $82,347.00 is withdrawn. The actual source topsheet contains Account 3900 ($438,254.00), which is an unsplit line lacking in-state lodging versus foreign airfare schedules.
2. **Withdrawal of Fabricated Post-Production Amount:** The previously asserted post-production amount of $208,670.00 is withdrawn. The actual source accounts contain Account 5000 (Editorial in Los Angeles, CA: $9,068.00) and Account 6100 (VFX Department: $52,500.00), totaling $61,568.00.
3. **Withdrawal of Erroneous Contingency Reserve:** The previously asserted contingency reserve of $310,197.00 is corrected to the exact source account figure of $301,131.00 (Account 8300).
4. **Withdrawal of Single Verified Dollar Claim:** Under Evidence Gate Rules 2, 3, and 5, where empirical evidence (travel lodging splits and actual contingency disbursement) is absent, auditors must NOT fabricate exact qualified spend. LU NY is classified as **`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`** with fully evidenced statutory bounds proving engine credit overstatement across all bounds.

### Formal Withdrawal of California Result/Structure IDs Mismatched to New York Comparisons (`RET-10`):
In strict accordance with Evidence Gate Rule 4, all cross-program comparisons citing California Program 4.0 (`ca_film_30`) structures and results as New York comparisons are **FORMALLY WITHDRAWN**:
1. **Withdrawal of FVD California Result `602efade-0ccf-43f2-b529-81434c6fd912` / Structure `b90c23db-3946-454b-8365-25eebe53dcf3`**: Withdrawn from NY comparison. Replaced with exact New York Film Production Credit structure `ae10b2e7-ed52-4ebe-894a-b9d6756ced32` and calculation result `c3b8ad45-5c1e-47ed-b182-c9106f668b2a` (Engine Qualified: $3,701,238.00; Incentive: $1,110,371.40).
2. **Withdrawal of BH California Structure `f7ef008d-ec84-4c96-a9fc-035638a420e7` / Result `65a62a4d-afdf-4cdc-8b6e-724364206e6b`**: Withdrawn from NY comparison. Replaced with exact New York Film Production Credit structure `8558365f-6a68-45a2-931e-4f294ddf20c9` and calculation result `f3513411-547c-41ca-894d-e1ef36d856b7` (Engine Qualified: $2,327,641.00; Incentive: $698,292.30).
3. **Withdrawal of LLS California Structure `f167da0f-bb1a-47e7-829b-b208cc08b38d` / Result `ce6e65af-f987-4aea-81bf-6b73280722a5`**: Withdrawn from NY comparison. Replaced with exact New York Film Production Credit structure `c135df1f-9a8e-4bdf-b25e-bd6af29a608b` and calculation result `5557ceb5-d3f5-4b42-85df-d7369d72a9bd` (Engine Qualified: $9,483,654.00; Incentive: $2,845,096.20).

### Core Audit Tenets Enforced:
1. **Zero Circularity & Zero Arithmetic against Self:** All expectations and bounds are derived independently from original budget accounts and dated primary statutes without invoking engine qualification, classification, or pricing methods.
2. **Single 44-Line Source Treatment Table:** All figures, subtotals, and statutory treatments are generated from `LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv`, which conserves every original budget account exactly once ($4,364,395.00 leaf sum; $4,364,393.00 controlling gross with documented $2 rounding variance).
3. **Resolution of the $138,850 Exclusion Residual:** The previously claimed $138,850 exclusion residual was the arithmetic shortfall of four manually substituted category amounts ($942,054.00 vs $1,080,904.00). Grounded in the actual 44 source accounts, statutory exclusions total exactly **$1,080,906.00** ($1,080,904.00 against gross), leaving an unexplained residual of **$0.00**.
4. **Strict Adherence to Rule 5 (No Per-Person Caps on Aggregate Accounts):** On productions lacking itemized general ledger talent contracts (FVD, BH, LLS), no exact per-person caps are fabricated. These projects are classified as **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**, with evidenced statutory bounds proving engine overstatement.
5. **Reconciliation of Multi-Program Stacking (`DISC-NY-001`):** NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c) command an absolute taxpayer/film-level bar between Section 24 and Section 31*2. Confirmed engine rule defect `DISC-NY-001` (`same_cost_prohibited_distinct_costs_allowed`) is isolated; saved engine outputs that did not generate a stack candidate are reclassified as **`COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)`**. Missing candidates alone cannot establish `VERIFIED_AGREEMENT`.
6. **No Production Mutations or ROW Expansion:** Zero production code or database mutations were performed; Rest-of-World (ROW) expansion remains strictly gated.

---

## 2. Dated Primary Statutory Authorities & Regime Breakdown

All calculations and rule analyses are grounded in dated primary legal authorities:

### 2.1 NY Tax Law § 24 (Empire State Film Production Credit)
* **Controlling Text:** NY Tax Law § 24 (as amended by Part D, Ch. 59, Laws of 2023, enacted May 3, 2023; effective April 1, 2023, for initial applications filed on or after April 1, 2023). Regulations: 5 NYCRR Part 170.
* **Historical vs. Current-Law Regimes:**
  - **Historical (Pre-April 1, 2023):** Base credit rate was 25%. Above-The-Line (ATL) costs were **strictly excluded** (0% eligible). Only Below-The-Line (BTL) physical production costs qualified.
  - **Current Law (April 1, 2023+):** Base credit rate is 30%. Eligible Above-The-Line wages are admitted subject to strict individual and aggregate caps (§ 24(b)(1)).
* **Eligible Above-The-Line Roles (§ 24(b)(1)):**
  - Wages paid to writers, directors, composers, performers (actors, excluding background actors without scripted lines), and up to two (2) individual producers.
* **Statutory ATL Ceilings & May 2023 Guidelines:**
  - **Statutory 40% Aggregate ATL Ceiling (§ 24(b)(1)):** The aggregate amount of all qualifying above-the-line costs shall **not exceed forty percent (40%) of the sum of all other qualified production costs** (i.e., qualified BTL physical production + qualified post-production costs).
  - **Producer Headcount Limit (§ 24(b)(1)):** Maximum of two (2) individual producers per qualified production.
  - **Individual Salary Cap & Temporal Alignment:** The official May 2023 ESD Film Credit Guidelines (page 2) specify a $500,000 per-person salary cap on qualifying individual ATL talent. In accordance with Codex delta review, this administrative cap requires temporal and evidentiary alignment: applying a per-person cap to aggregate topsheet accounts without individual payee contracts is an unevidenced assumption (Rule 5). Actual legal QPE remains `NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)` pending individual payee contracts, bounded by the 0% ATL floor and 40% aggregate ATL ceiling.
* **Statutory Non-Qualifying Exclusions (§ 24(a)(2)):**
  - Financing costs, interest, bridge loan fees, completion bond fees, corporate insurance premiums, and general corporate administration are statutorily excluded.
* **Travel and Living Expenses (5 NYCRR § 170.2):**
  - Under 5 NYCRR § 170.2(b), Below-The-Line travel and living expenses qualify ONLY IF incurred within New York State directly for production crew lodging, meals, and local ground transportation. Airfares originating from or terminating outside New York State, foreign travel, and all Above-The-Line travel are strictly non-qualifying.
* **Upstate Production Credit Uplift (§ 24(a)(5)) vs. Post Uplift (§ 31*2(a)(6)):**
  - **County Definition:** 53 upstate counties. In accordance with primary text and adjudication finding `NY-A05`, **Dutchess, Orange, and Putnam counties ARE statutorily included** in the upstate production credit county list (unlike the MCTD post-production boundary).
  - **Uplift Rate:** Additional +10% credit (40% total).
  - **Labor Limb:** Under NY Tax Law § 24(a)(5), qualifying labor expenses (including eligible Above-The-Line wages within the 40% aggregate ATL ceiling and up to 2 credited producers) qualify for the +10% uplift if services are performed in an eligible upstate county. Blanket ATL exclusion from the production uplift is legally disproved by dated statutory text and ESD guidelines. By contrast, under NY Tax Law § 31*2(a)(6) (the post-production credit upstate uplift), ATL roles are expressly excluded from the post uplift.
  - **Non-Labor Limb:** Non-labor qualified costs incurred in upstate counties qualify for the § 24(a)(5) +10% uplift **ONLY IF more than fifty percent (> 50%) of principal photography shoot days** occur in upstate counties.
  - **Status:** County shoot day logs and territorial payroll ledgers are absent from budget records, keeping upstate uplift as an explicit conditional planning scenario (`CONDITIONAL_UPSTATE_EXPANSION`).

### 2.2 NY Tax Law § 31*2 (Empire State Film Post-Production Credit)
* **Controlling Text:** NY Tax Law § 31*2 (revision 2025-07-11; distinct from plain § 31 Excelsior Jobs). Regulations: 5 NYCRR Part 240.
* **Taxpayer/Film-Level Mutual Exclusivity (§ 31*2(a)(1) & 5 NYCRR § 240.3(c)):**
  - *'A taxpayer shall be eligible for the credit... provided however that no taxpayer shall be eligible to receive this credit if such taxpayer has qualified or is eligible to qualify for the empire state film production credit pursuant to section twenty-four of this article with respect to the same qualified film.'*
  - This establishes an absolute statutory bar against claiming both § 24 and § 31*2 for the same film.
* **Dual Statutory Gateways (§ 31*2(a)(2) & (3)):**
  - **General Post-Production Gateway (§ 31*2(a)(2)(i)):** Qualified post-production costs incurred at a Qualified Post-Production Facility (QPF) in New York must equal at least:
    - **75% of total worldwide post-production costs**, OR
    - **$1,000,000** (whichever is lesser).
  - **VFX & Animation Standalone Gateway (§ 31*2(a)(3)(ii)):** Qualified visual effects and animation costs incurred at a NY QPF must equal at least:
    - **10% of total worldwide VFX and animation costs**, OR
    - **$500,000** (whichever is lesser).
* **Geographic Rates & Labor Uplift (§ 31*2(a)(1)):**
  - 30% for qualified post spend incurred at a QPF within the Metropolitan Commuter Transportation District (MCTD: NYC, Westchester, Rockland, Nassau, Suffolk, Dutchess, Orange, Putnam).
  - 35% for qualified post spend incurred at a QPF outside the MCTD (+5% upstate facility differential).
  - Additional +10% uplift on eligible county post labor upstate.
* **On-Set Production Sound Classification (`NY-A03`):**
  - On-set sound mixing and recording is physical production (BTL), NOT post-production. Only post-production sound (ADR, Foley, sound editing, final re-recording mix) incurred at a registered QPF qualifies under § 31*2.

---

## 3. Account-Level Project Reconciliations & Discrepancy Findings

### 3.1 The Little Utopia (`LU`) — 44-Line Source Treatment Table & Reconciliations

Every figure in this section is derived strictly from `LITTLE_UTOPIA_NEW_YORK_SOURCE_LINE_TREATMENT.csv`, conserving all 44 original accounts exactly once:

| Account ID | Description | Original Amount ($) | Department | ATL/BTL | Category | Audit Treatment | Statutory Authority | Notes |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **1000** | 1000 DEVELOPMENT | 0.00 | Above The Line | atl | `miscellaneous` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **1100** | 1100 SCRIPT | 5,050.00 | Above The Line | atl | `atl_writer` | `QUALIFIED_ATL_WRITER` | NY Tax Law § 24(b)(1)(B) | Eligible creative ATL writer clearances; individual earner <= ,000 |
| **1200** | 1200 PRODUCERS UNIT | 0.00 | Above The Line | atl | `atl_producer` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **1300** | 1300 DIRECTION | 0.00 | Above The Line | atl | `atl_director` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **1400** | 1400 CAST | 136,115.00 | Above The Line | atl | `atl_cast` | `QUALIFIED_ATL_PERFORMERS` | NY Tax Law § 24(b)(1)(B) | Eligible creative ATL performers with speaking lines; individual earners <= ,000 |
| **1600** | 1600 ATL TRAVEL & LIVING | 397,279.00 | Above The Line | atl | `travel` | `STATUTORILY_EXCLUDED_ATL_TRAVEL` | NY Tax Law § 24(b)(1) | ATL travel and living non-qualifying; ATL restricted to wages of writers/directors/performers/composers/producers |
| **2000** | 2000 PRODUCTION STAFF | 321,594.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2100** | 2100 EXTRA TALENT | 21,981.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2200** | 2200 SET DESIGN | 65,873.00 | Production | btl | `btl_set_construction` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2300** | 2300 SET CONSTRUCTION | 107,628.00 | Production | btl | `btl_set_construction` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2400** | 2400 SET DRESSING | 154,826.00 | Production | btl | `btl_set_construction` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2500** | 2500 PROPERTIES | 68,854.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2600** | 2600 PICTURE VEHICLES AND ANIMALS | 215,218.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2700** | 2700 WARDROBE | 58,815.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2800** | 2800 MAKE-UP & HAIR | 51,809.00 | Production | btl | `btl_crew_labor` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **2900** | 2900 SET OPERATIONS | 90,679.00 | Production | btl | `btl_set_construction` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3000** | 3000 ELECTRICAL | 155,375.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3100** | 3100 CAMERA | 288,729.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3200** | 3200 PRODUCTION SOUND | 69,532.00 | Production | btl | `production_sound` | `QUALIFIED_BTL_ONSET_SOUND` | NY Tax Law § 24(a)(2) / NY-A03 | Physical production on-set sound; BTL physical spend per NY-A03 |
| **3300** | 3300 SPECIAL EFFECTS & MARINE | 99,837.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3400** | 3400 LOCATION EXPENSE | 496,232.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3500** | 3500 AERIAL/DRONE UNIT | 16,215.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3600** | 3600 TRANSPORTATION | 321,899.00 | Production | btl | `btl_transportation` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3700** | 3700 STAGE & OFFICE RENTALS | 27,732.00 | Production | btl | `btl_stage_facility` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3800** | 3800 PRODUCTION LAB & MEDIA MANAGEMENT | 9,674.00 | Production | btl | `miscellaneous` | `QUALIFIED_BTL_PHYSICAL` | NY Tax Law § 24(a)(2) | Physical production below-the-line goods, services, and crew labor |
| **3900** | 3900 BTL TRAVEL & LIVING | 438,254.00 | Production | btl | `travel` | `CONDITIONAL_BTL_TRAVEL_LIVING` | NY Tax Law § 24(a)(2) / 5 NYCRR § 170.2 | In-state crew lodging/per diem qualifies; foreign/out-of-state airfare excluded. Unsplit topsheet line |
| **4000** | 4000 SPECIAL SHOOT UNITS | 0.00 | Production | btl | `miscellaneous` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **5000** | 5000 EDITORIAL | 9,068.00 | Post Production | post | `post_production` | `STATUTORILY_EXCLUDED_OUT_OF_STATE_EDITORIAL` | NY Tax Law § 24(a)(2) | Editorial performed in Los Angeles, CA; excluded from NY qualified spend. Engine allocated outside NY |
| **5100** | 5100 EDITORIAL - USA | 0.00 | Post Production | post | `post_production` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **5200** | 5200 SOUND POST PRODUCTION | 0.00 | Post Production | post | `sound` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **5300** | 5300 PICTURE POST PRODUCTION | 0.00 | Post Production | post | `post_production` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **5400** | 5400 GRAPHICS / TITLES / STOCK FOOTAGE | 0.00 | Post Production | post | `post_production` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **5500** | 5500 DELIVERABLES | 0.00 | Post Production | post | `post_production` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **6000** | 6000 MUSIC | 0.00 | Other | post | `music` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **6100** | 6100 VFX DEPARTMENT | 52,500.00 | Other | post | `vfx` | `QUALIFIED_POST_VFX` | NY Tax Law § 24(a)(2) | Visual effects department; qualifying post-production spend if contracted to NY facility |
| **6500** | 6500 USA ADMIN COSTS | 0.00 | Other | btl | `miscellaneous` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **7000** | 7000 ADMINISTRATIVE EXPENSES | 297,593.00 | Other | other | `general_administration` | `STATUTORILY_EXCLUDED_ADMIN_PUBLICITY` | NY Tax Law § 24(a)(2) | General administrative overhead and marketing/publicity statutorily excluded |
| **7100** | 7100 PUBLICITY | 24,348.00 | Other | other | `general_administration` | `STATUTORILY_EXCLUDED_ADMIN_PUBLICITY` | NY Tax Law § 24(a)(2) | General administrative overhead and marketing/publicity statutorily excluded |
| **7200** | 7200 INSURANCE | 12,374.00 | Other | other | `insurance` | `STATUTORILY_EXCLUDED_INSURANCE` | NY Tax Law § 24(a)(2) | Corporate wrap and production insurance premiums statutorily excluded |
| **7300** | 7300 MARKETING | 0.00 | Other | btl | `miscellaneous` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **7800** | 7800 FINANCE & LEGAL | 0.00 | Other | other | `finance_costs` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **8100** | 8100 Insurance : 1.2% | 48,181.00 | Below The Line | other | `insurance` | `STATUTORILY_EXCLUDED_INSURANCE` | NY Tax Law § 24(a)(2) | Corporate wrap and production insurance premiums statutorily excluded |
| **8200** | 8200 Bond : 0.0% | 0.00 | Below The Line | other | `completion_bond` | `ZERO_BUDGET_LINE` | NY Tax Law § 24 | Zero budgeted spend in source budget file |
| **8300** | 8300 Contigency : 7.5% | 301,131.00 | Below The Line | other | `contingency` | `STATUTORILY_EXCLUDED_CONTINGENCY_RESERVE` | NY Tax Law § 24 / Rule 2 | Undeployed contingency reserve is an unspent reserve; excluded in engine trace and EDB control |

#### Reconciled Departmental & Category Subtotals:
* **Physical Below-The-Line Production:**
  - Physical BTL Spend (Accounts 2000–3800 excl. 3200): **$2,572,970.00**
  - On-Set Production Sound (Account 3200, BTL per `NY-A03`): **$69,532.00**
  - **Total Physical BTL Base:** **$2,642,502.00**
* **Creative Above-The-Line (ATL):**
  - Script Writer Clearances (Account 1100): **$5,050.00** (individual earner <= $500k)
  - Cast Performers (Account 1400): **$136,115.00** (speaking actors <= $500k; no unscripted extras)
  - Director (Account 1300) / Producers (Account 1200): **$0.00** in budget file
  - **Total Creative ATL:** **$141,165.00**
* **Post-Production Department (Reconciling Source $61,568 vs Hallucinated $208,670):**
  - Visual Effects Department (Account 6100): **$52,500.00** (qualifying post spend if NY facility)
  - Editorial (Account 5000): **$9,068.00** (performed in Los Angeles, CA; consistently excluded from NY relocation spend across bounds under § 24 territorial rules; allocated outside NY to generic US unpriced in engine trace Segment 0)
  - Accounts 5100, 5200, 5300, 5400, 5500, 6000: **$0.00** in budget file
  - **Total Post-Production Spend:** $52,500.00 + $9,068.00 = **$61,568.00** (reconciling source accounts exactly; withdrawing hallucinated $208,670.00)
* **BTL Travel & Living (Reconciling Source $438,254 vs Hallucinated $82,347):**
  - Account 3900 (`3900 BTL TRAVEL & LIVING`): **$438,254.00**
  - Under 5 NYCRR § 170.2, in-state crew lodging/per diem qualifies, but foreign and out-of-state airfares are statutorily excluded. Because the topsheet lacks departmental ledgers for hotel receipts vs airfares, Account 3900 is an empirical unknown (`CONDITIONAL_BTL_TRAVEL_LIVING`). (Withdrawing hallucinated $82,347.00)
* **Subaccount Breakdown for Admin, Publicity & Insurance (Verified against Original Budget PDF):**
  - **Account 7000 (Administrative Expenses: $297,593.00):** Direct production office lines (7009 Copiers $4,239, 7014 DIT Software $1,112, 7015 Hardware $2,609, 7030 Telecom $11,886, 7094 Office Supplies $3,696) total **$23,542.00**; Line production service company fee (7003) = **$95,000.00** (potentially eligible production coordination); Statutorily excluded corporate lines (7002 Setup & Audit $35,927, 7007 Legals $10,000, 7038 Bank Charges $2,957, 7042 Freight $27,293, 7050 Wrap Party $10,435, 7095 Foreign VAT $92,439) total **$179,051.00** (statutorily excluded under § 24(a)(2)). Total: $23,542 + $95,000 + $179,051 = **$297,593.00**.
  - **Account 7100 (Publicity: $24,348.00):** Unit still photographer (7102) = **$8,696.00** (IATSE 600 BTL crew labor); EPK crew & equipment (7105) = **$15,652.00** (camera crew $9,783, edit $5,869). Admitted up to **$24,348.00** in optimistic planning ceiling; excluded promotional marketing in incurred spend.
  - **Account 7200 (Corporate Insurance: $12,374.00):** Direct production liability (7201: $4,174) + cast medicals (7203: $700) = **$4,874.00** (direct physical safety). Excluded corporate wrap (7202 E&O $5,000, travel insurance $2,500) = **$7,500.00**. Total: $4,874 + $7,500 = **$12,374.00**.
  - **Account 8100 (Insurance : 1.2%: $48,181.00):** Production package floater. Excluded in baseline without policy binder; admitted up to **$48,181.00** in optimistic planning ceiling.
  - **Account 8300 (Contingency Reserve : 7.5%: $301,131.00):** Unspent reserve ($0.00 incurred spend); admitted up to **$301,131.00** in optimistic planning scenario per documented producer election (100% deployment into qualifying BTL physical production).
  - **Account 1600 (ATL Travel & Living: $397,279.00):** Statutorily excluded under § 24(b)(1).
* **Statutory Non-Qualifying Exclusions & Resolution of the $138,850 Residual:**
  - Incurred spend baseline exclusions: ATL Travel ($397,279) + Admin ($297,593) + Publicity ($24,348) + Insurance ($12,374) + Insurance 1.2% ($48,181) + Contingency ($301,131) = **$1,080,906.00** ($1,080,904.00 against controlling gross topsheet).
  - The previously reported handoff stated: Contingency $310,197.00 + Financing & Legal $421,791.00 + Insurance & Bond $130,081.00 + Administrative $79,985.00 = $942,054.00, while asserting total exclusions of $1,080,904.00. The difference was $\$1,080,904.00 - \$942,054.00 = \mathbf{\$138,850.00}$. Grounded in the actual 44 source accounts, statutory exclusions total exactly **$1,080,906.00** ($1,080,904.00 gross). Conserving leaf sum: $\$4,364,395.00 - \$1,080,906.00 = \$3,283,489.00$, yielding an unexplained residual of exactly **$0.00**.
  - Optimistic planning upper bound exclusions: ATL Travel ($397,279) + Excluded Corporate Admin ($179,051) + Corporate Insurance ($7,500) + LA Editorial ($9,068) = **$592,898.00**. Upper bound eligible spend = $\$4,364,395.00 - \$592,898.00 = \mathbf{\$3,771,497.00}$.

#### Supported Statutory Bounds for The Little Utopia (`ny_state_film`):
Because the exact qualifying split of BTL travel ($438,254) and actual disbursement of contingency reserve ($301,131) are empirical unknowns, AUDIT INPUT EVIDENCE GATE Rules 2, 3, and 5 prohibit asserting a single dollar figure. The audit provides rigorous statutory bounds:
1. **Minimum QPE (Lower Bound Floor):**
   - Excludes all uncertain BTL travel ($438,254.00) and out-of-state LA editorial ($9,068.00).
   - Other qualified costs (BTL Physical $2,642,502.00 + VFX $52,500.00) = **$2,695,002.00**.
   - 40% Statutory ATL Ceiling: $\$2,695,002.00 \times 0.40 = \$1,078,000.80$.
   - Creative ATL Incurred: $141,165.00 (fully admitted under ceiling).
   - **Min QPE:** $\$2,695,002.00 + \$141,165.00 = \mathbf{\$2,836,167.00}$
   - **Min Base Credit (30%):** $\$2,836,167.00 \times 0.30 = \mathbf{\$850,850.10}$
2. **Relocation Baseline (Midpoint Scenario):**
   - Admits 100% BTL crew travel as in-state lodging ($438,254.00); excludes out-of-state LA editorial ($9,068.00).
   - Other qualified costs (BTL Physical $2,642,502.00 + BTL Travel $438,254.00 + VFX $52,500.00) = **$3,133,256.00**.
   - 40% Statutory ATL Ceiling: $\$3,133,256.00 \times 0.40 = \$1,253,302.40$.
   - Creative ATL Incurred: $141,165.00 (fully admitted).
   - **Relocation Baseline QPE:** $\$3,133,256.00 + \$141,165.00 = \mathbf{\$3,274,421.00}$
   - **Relocation Baseline Credit (30%):** $\$3,274,421.00 \times 0.30 = \mathbf{\$982,326.30}$
3. **Optimistic Planning Ceiling / Upper Bound (Including Every Potentially Eligible Unresolved Portion):**
   - Admits 100% contingency deployment into BTL physical ($301,131.00), 100% in-state crew travel ($438,254.00), direct production office ($23,542.00), line production coordination fee ($95,000.00), unit still photography and EPK crew ($24,348.00), direct production liability & medicals ($4,874.00), and production package insurance floater ($48,181.00). Editorial in LA ($9,068.00) is consistently excluded from NY relocation spend across bounds.
   - Other qualified costs = Physical BTL $2,642,502 + Travel $438,254 + Contingency $301,131 + Post VFX $52,500 + Qualifying Admin $118,542 + Publicity $24,348 + Qualifying Insurance $53,055 = **$3,630,332.00**.
   - 40% Statutory ATL Ceiling: $\$3,630,332.00 \times 0.40 = \$1,452,132.80$.
   - Creative ATL Incurred: $141,165.00 (fully admitted).
   - **Max Upper Bound QPE:** $\$3,630,332.00 + \$141,165.00 = \mathbf{\$3,771,497.00}$
   - **Max Base Credit (30%):** $\$3,771,497.00 \times 0.30 = \mathbf{\$1,131,449.10}$
   - *(Note: Historical physical spend base prior to subaccount resolution was $3,283,489.00 [Credit: $985,046.70]).*

#### Comparison against Engine Saved Result (`canonical-1.106.0`):
* **Saved Database Match:** Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903` (Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`, Name `Full relocation to US-NY (New York State Film Tax Credit Program (Production))`)
* **Actual Engine Figures:**
  - Segment 0 (Generic US Unpriced): Allocated $9,068.00 (LA Editorial); Qualified Spend = $0.00
  - Segment 1 (US-NY ny_state_film): Allocated $4,355,327.00; Excluded $301,131.00 (Contingency Reserve 8300); Qualified Spend = **$4,054,196.00**
  - Actual Base Incentive: **$1,216,258.80** ($4,054,196.00 × 0.30)
* **Defect Proof across All Bounds (`NA-DEFECT-01`):**
  - Overstatement at Optimistic Upper Bound ($3,771,497.00): $\$1,216,258.80 - \$1,131,449.10 = \mathbf{+\$84,809.70}$
  - Overstatement at Relocation Baseline ($3,274,421.00): $\$1,216,258.80 - \$982,326.30 = \mathbf{+\$233,932.50}$
  - Overstatement at Min QPE Lower Bound Floor ($2,836,167.00): $\$1,216,258.80 - \$850,850.10 = \mathbf{+\$365,408.70}$
* **Audit Disposition:** **`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**. Engine credit overstatement is conclusively proven across every single supported bound (`NA-DEFECT-01`).

---

### 3.2 F#K Valentine's Day (`FVD`) — Supported Statutory Bounds
* **Gross Controlling Budget:** $4,517,687.00.
* **Source BTL + Post Base:**
  - Production BTL: $1,114,318.00; Travel/Living: $46,000.00; On-Set Sound: $26,458.00; Post: $70,000.00.
  - **Sum of Other Qualified Costs (BTL + Post):** **$1,256,776.00**
* **Statutory 40% Aggregate Ceiling:**
  $$\text{Ceiling} = 0.40 \times \$1,256,776.00 = \mathbf{\$502,710.40}$$
* **Audit Evidence Evaluation under AUDIT INPUT EVIDENCE GATE Rule 5:**
  - FVD is a 1-page topsheet without itemized general ledger contracts.
  - Cast (Account 1400, $1,976,479.00) and Producer accounts exceed $500,000.
  - Under Rule 5, auditors cannot apply per-person salary caps ($500k) or producer headcount limits (max 2) to aggregate topsheet totals without individual contract schedules.
  - Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**.
* **Evidenced Statutory Bounds:**
  - **Minimum QPE (Zero ATL Qualified):**
    $$\text{Min QPE} = \mathbf{\$1,256,776.00} \quad [\text{Credit at 30\%: } \mathbf{\$377,032.80}]$$
  - **Maximum QPE (Statutory 40% Ceiling Fully Satisfied):**
    $$\text{Max QPE} = \$1,256,776.00 + \$502,710.40 = \mathbf{\$1,759,486.40} \quad [\text{Credit at 30\%: } \mathbf{\$527,845.92}]$$
* **Engine Comparison (`canonical-1.106.0`, Result ID `c3b8ad45-5c1e-47ed-b182-c9106f668b2a`, Structure ID `ae10b2e7-ed52-4ebe-894a-b9d6756ced32`):**
  - Engine Qualified: $3,701,238.00; Engine Credit: $1,110,371.40.
  - Overstatement at Maximum Upper Bound: $\Delta \text{Credit}_{\min} = \$1,110,371.40 - \$527,845.92 = \mathbf{+\$582,525.48}$
  - Overstatement at Lower Bound: $\Delta \text{Credit}_{\max} = \$1,110,371.40 - \$377,032.80 = \mathbf{+\$733,338.60}$
  - **Conclusion:** Confirms `NA-DEFECT-01` without fabricating an exact payee split.

---

### 3.3 Bad Hombres (`BH`) — Supported Statutory Bounds
* **Gross Controlling Budget:** $2,482,023.00.
* **Source BTL + Post Base:**
  - Production BTL: $656,044.00; Travel/Living: $27,000.00; On-Set Sound: $16,845.00; Post: $50,000.00.
  - **Sum of Other Qualified Costs (BTL + Post):** **$749,889.00**
* **Statutory 40% Aggregate Ceiling:**
  $$\text{Ceiling} = 0.40 \times \$749,889.00 = \mathbf{\$299,955.60}$$
* **Audit Evidence Evaluation under Rule 5:**
  - Cast (Account 1400, $974,371.00) exceeds $500,000 without payee breakdown.
  - Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**.
* **Evidenced Statutory Bounds:**
  - **Minimum QPE (Zero ATL Qualified):**
    $$\text{Min QPE} = \mathbf{\$749,889.00} \quad [\text{Credit at 30\%: } \mathbf{\$224,966.70}]$$
  - **Maximum QPE (Statutory 40% Ceiling Fully Satisfied):**
    $$\text{Max QPE} = \$749,889.00 + \$299,955.60 = \mathbf{\$1,049,844.60} \quad [\text{Credit at 30\%: } \mathbf{\$314,953.38}]$$
* **Engine Comparison (`canonical-1.106.0`, Result ID `f3513411-547c-41ca-894d-e1ef36d856b7`, Structure ID `8558365f-6a68-45a2-931e-4f294ddf20c9`):**
  - Engine Qualified: $2,327,641.00; Engine Credit: $698,292.30.
  - Overstatement at Maximum Upper Bound: $\Delta \text{Credit}_{\min} = \$698,292.30 - \$314,953.38 = \mathbf{+\$383,338.92}$
  - Overstatement at Lower Bound: $\Delta \text{Credit}_{\max} = \$698,292.30 - \$224,966.70 = \mathbf{+\$473,325.60}$
  - **Conclusion:** Confirms `NA-DEFECT-01` without fabricating an exact payee split.

---

### 3.4 Lips Like Sugar (`LLS`) — Supported Statutory Bounds
* **Gross Controlling Budget & Source Conservation:**
  - Declared Topsheet Gross: **$11,947,562.00**; Leaf Sum with fringes: **$11,983,654.00**.
* **Statutory Financing Exclusions (`NY-A01`):**
  - Account 6500 (`FINANCING FEES`): $450,000.00
  - Account 6600 (`BRIDGE`): $250,000.00
  - Account 6700 (`BANKING FEE`): $1,000,000.00
  - **Total Non-Qualifying Financing Excluded:** **$1,700,000.00**
* **Source BTL + Post Departmental Base:**
  - Production BTL Physical (Accounts 2000-3600, 3900): $3,816,990.00
  - Fringes BTL (Accounts 4900, 5900): $1,091,423.00
  - On-Set Sound (Account 3400, BTL per `NY-A03`): $87,067.00
  - Post-Production (Accounts 3700, 4400-4800, 4900, 5800): $858,004.00
  - **Sum of Other Qualified Costs (BTL + Post):** **$5,853,484.00**
* **Statutory 40% Aggregate Ceiling:**
  $$\text{Ceiling} = 0.40 \times \$5,853,484.00 = \mathbf{\$2,341,393.60}$$
* **Audit Evidence Evaluation under Rule 5:**
  - Cast (Account 1400, $863,388.00 + fringes $255,291.00 = $1,118,679.00) and Producer accounts ($1,414,198.00) exceed $500,000 without individual contracts.
  - Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**.
* **Evidenced Statutory Bounds:**
  - **Minimum QPE (Zero ATL Qualified):**
    $$\text{Min QPE} = \mathbf{\$5,853,484.00} \quad [\text{Credit at 30\%: } \mathbf{\$1,756,045.20}]$$
  - **Maximum QPE (Statutory 40% Ceiling Fully Satisfied):**
    $$\text{Max QPE} = \$5,853,484.00 + \$2,341,393.60 = \mathbf{\$8,194,877.60} \quad [\text{Credit at 30\%: } \mathbf{\$2,458,463.28}]$$
* **Engine Comparison (`canonical-1.106.0`, Result ID `5557ceb5-d3f5-4b42-85df-d7369d72a9bd`, Structure ID `c135df1f-9a8e-4bdf-b25e-bd6af29a608b`):**
  - Engine Qualified: $9,483,654.00; Engine Credit: $2,845,096.20.
  - Overstatement at Maximum Upper Bound: $\Delta \text{Credit}_{\min} = \$2,845,096.20 - \$2,458,463.28 = \mathbf{+\$386,632.92}$
  - Overstatement at Lower Bound: $\Delta \text{Credit}_{\max} = \$2,845,096.20 - \$1,756,045.20 = \mathbf{+\$1,089,051.00}$
  - **Conclusion:** Confirms `NA-DEFECT-01` without fabricating an exact payee split.

---

### 3.5 Three-Unit Reconciled Defect & Variance Breakdown (`NA-DEFECT-01` in Saved Engine `canonical-1.106.0`)
*(Operands derived strictly within matching units: QPE vs QPE, Incentive vs Incentive, NPC vs NPC. Historical saved results in `canonical-1.106.0` do not prove defects in current code `canonical-1.111.0` / `canonical-1.112.0`)*

#### Unit 1: Qualified Production Expenditure (QPE)
| Project | Structure ID / Result ID | Saved Engine QPE (1.106.0) | Statutory Min QPE Floor | Relocation Baseline QPE | Statutory Max QPE Upper Bound | $\Delta \text{QPE}_{\min}$ (vs Max Bound) | $\Delta \text{QPE}_{\max}$ (vs Min Floor) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **LU** | `14535c49...` / `340d2041...` | $4,054,196.00 | $2,836,167.00 | $3,274,421.00 | $3,771,497.00 | +$282,699.00 | +$1,218,029.00 |
| **FVD** | `ae10b2e7...` / `c3b8ad45...` | $3,701,238.00 | $1,256,776.00 | — | $1,759,486.40 | +$1,941,751.60 | +$2,444,462.00 |
| **BH** | `8558365f...` / `f3513411...` | $2,327,641.00 | $749,889.00 | — | $1,049,844.60 | +$1,277,796.40 | +$1,577,752.00 |
| **LLS** | `c135df1f...` / `5557ceb5...` | $9,483,654.00 | $5,853,484.00 | — | $8,194,877.60 | +$1,288,776.40 | +$3,630,170.00 |

#### Unit 2: Incentive / Tax Credit (Base 30% Rate)
| Project | Structure ID / Result ID | Saved Engine Incentive (1.106.0) | Statutory Min Credit Floor | Relocation Baseline Credit | Statutory Max Credit Upper Bound | $\Delta \text{Incentive}_{\min}$ (vs Max Bound) | $\Delta \text{Incentive}_{\max}$ (vs Min Floor) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **LU** | `14535c49...` / `340d2041...` | $1,216,258.80 | $850,850.10 | $982,326.30 | $1,131,449.10 | +$84,809.70 | +$365,408.70 |
| **FVD** | `ae10b2e7...` / `c3b8ad45...` | $1,110,371.40 | $377,032.80 | — | $527,845.92 | +$582,525.48 | +$733,338.60 |
| **BH** | `8558365f...` / `f3513411...` | $698,292.30 | $224,966.70 | — | $314,953.38 | +$383,338.92 | +$473,325.60 |
| **LLS** | `c135df1f...` / `5557ceb5...` | $2,845,096.20 | $1,756,045.20 | — | $2,458,463.28 | +$386,632.92 | +$1,089,051.00 |

#### Unit 3: Net Production Cost (NPC)
| Project | Controlling Gross Budget | Saved Engine NPC (1.106.0) | Statutory Min NPC Floor (at Max Credit) | Relocation Baseline NPC | Statutory Max NPC Ceiling (at Min Credit) | $\Delta \text{NPC}$ (vs Min NPC) | $\Delta \text{NPC}$ (vs Max NPC) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **LU** | $4,364,395.00 | $3,148,136.20 | $3,232,945.90 | $3,382,068.70 | $3,513,544.90 | -$84,809.70 | -$365,408.70 |
| **FVD** | $4,517,687.00 | $3,407,315.60 | $3,989,841.08 | — | $4,140,654.20 | -$582,525.48 | -$733,338.60 |
| **BH** | $2,482,023.00 | $1,783,730.70 | $2,167,069.62 | — | $2,257,056.30 | -$383,338.92 | -$473,325.60 |
| **LLS** | $11,947,562.00 | $9,102,465.80 | $9,489,098.72 | — | $10,191,516.80 | -$386,632.92 | -$1,089,051.00 |

---

## 4. Multi-Program Stacking & Post-Production Gateways

### 4.1 New York Multi-Program Stack (`stack_ny_prod_post`) & Defect `DISC-NY-001`
* **Statutory Bar:** NY Tax Law § 31*2(a)(1) and 5 NYCRR § 240.3(c) command that any taxpayer eligible for the Section 24 film production credit is statutorily barred from receiving the Section 31*2 post-production credit with respect to the same film.
* **Independent Expected Determination:**
  - Status: **`GATE_REJECTED`**
  - Reason: `MUTUALLY_EXCLUSIVE_BY_STATUTE (NY Tax Law § 31*2(a)(1) / 5 NYCRR § 240.3(c))`
  - Expected QPE = $0.00; Expected Incentive = $0.00.
* **Engine Rule Conflict (`DISC-NY-001`):**
  - In `backend/app/optimization/stacking_rules.py:617`, the stack rule is defined as:
    ```python
    StackingRule(
        source_slug="ny_state_film",
        target_slug="us_ny_post_production_credit",
        relationship=StackRelationship.SAME_COST_PROHIBITED_DISTINCT_COSTS_ALLOWED,  # DEFECT DISC-NY-001
        legal_basis="NY Tax Law § 24 / § 31",
    )
    ```
  - This rule erroneously permits distinct-cost pairing, directly violating the taxpayer/film-level bar.
* **Engine Saved Candidate Status:**
  - In `canonical-1.106.0`, no stack candidate was generated for these projects (`STACK_NOT_GENERATED`).
  - Missing candidate alone cannot establish `VERIFIED_AGREEMENT` while the underlying rule is defective.
* **Audit Disposition:** **`COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)`**.

### 4.2 Post-Production Credit Gateways (`DISC-NY-002`) & Geographic Rates (`DISC-NY-003`)
* **Gateways:**
  - General Post Gateway (§ 31*2(a)(2)(i)): Lesser of $1,000,000 or 75% total worldwide post spend.
  - VFX/Animation Gateway (§ 31*2(a)(3)(ii)): Lesser of $500,000 or 10% worldwide VFX/animation spend.
  - Confirmed Engine Defect: Flat fixed $1M threshold in source config misses both branches (`DISC-NY-002`).
* **Rates:**
  - MCTD (30%) vs. Upstate QPF (35%), plus +10% eligible county post labor uplift.
  - Confirmed Engine Defect: Flat 35% rate in source config misses MCTD boundary and labor uplift (`DISC-NY-003`).
* **Saved Database Candidate Matching:**
  - Saved database contains only component-relocation candidates, with no full relocation structure in saved DB.
  - Audit Disposition:** **`COMPARISON_NOT_ESTABLISHED (COMPONENT_ONLY_STRUCTURE)`**.

---

## 5. Justified Canonical Repair Specifications for Codex Review

To resolve the confirmed New York defects in the engine without introducing circularity, Codex must implement the following canonical repairs:

### 5.1 Repair Specification 1: Implement `NY_ATL_40_PERCENT_RULE` (`NA-DEFECT-01`)
* **Target File:** `backend/app/data/program_spend_rules.py` (around line 193) and qualification pipeline.
* **Specification:**
  1. Change qualification doctrine for `ny_state_film` from `OPEN_DEFAULT_INCLUDE` to a specialized statutory doctrine (e.g., `NY_SECTION_24_DOCTRINE`).
  2. Implement an explicit cap calculation:
     $$\text{Qualified ATL} = \min\left(\sum \text{Eligible ATL Wages (capped at \$500k/person, max 2 producers)}, \; 0.40 \times (\text{BTL Physical} + \text{Post})\right)$$
  3. Exclude background actors without scripted lines from qualifying ATL.
  4. Explicitly exclude non-qualifying categories: Financing fees (Account 7800 on LU; Accounts 6500/6600/6700 on LLS), completion bond and corporate insurance (Accounts 7200/8100), and general corporate administration (Accounts 7000/7100).

### 5.2 Repair Specification 2: Correct Stacking Mutual Exclusivity (`DISC-NY-001`)
* **Target File:** `backend/app/optimization/stacking_rules.py` (line 617).
* **Specification:**
  ```python
  StackingRule(
      source_slug="ny_state_film",
      target_slug="us_ny_post_production_credit",
      relationship=StackRelationship.MUTUALLY_EXCLUSIVE,  # REPAIRED: § 31*2(a)(1) taxpayer/film-level bar
      legal_basis="NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c)",
  )
  ```

### 5.3 Repair Specification 3: Implement Dual Post-Production Gateways (`DISC-NY-002`)
* **Target File:** `backend/app/data/program_spend_rules.py` and requirements registry.
* **Specification:**
  - For `us_ny_post_production_credit`, implement conditional branch:
    - If project has visual effects and animation: Gateway is met if NY QPF VFX spend $\ge \min(\$500,000, \; 0.10 \times \text{Total Worldwide VFX Spend})$.
    - Otherwise (general post): Gateway is met if NY QPF post spend $\ge \min(\$1,000,000, \; 0.75 \times \text{Total Worldwide Post Spend})$.

### 5.4 Repair Specification 4: Refine Post Geographic Rates & Labor Uplift (`DISC-NY-003`)
* **Target File:** `backend/app/data/program_spend_rules.py`.
* **Specification:**
  - Base facility rate: 30% for MCTD facilities (NYC, Westchester, Rockland, Nassau, Suffolk, Dutchess, Orange, Putnam); 35% for facilities in upstate counties outside MCTD.
  - Labor uplift: Add +10% on qualifying upstate post labor wages.

---

## 6. Detailed Remaining Blockers Ledger (Evidence Gaps vs Engine Defects)

Every retained issue across the four anchor projects is categorized and detailed below with exact missing facts, supported scenarios, expected engine behavior, producer inputs needed, and identical candidate matching:

### 6.1 Blocker 1: LU New York Empirical Evidence Gaps (Travel, Contingency, Insurance, Upstate)
* **Blocker ID:** `BLOCKER-01-LU-NY-EVIDENCE-GAP`
* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)
* **Missing Facts:**
  1. Itemized departmental crew travel schedule distinguishing in-state crew hotel lodging/per diem from foreign/out-of-state airfares in Account 3900 ($438,254.00) under 5 NYCRR § 170.2.
  2. Final audited cost reports and general ledger expenditure registers showing actual post-production disbursement for contingency reserve Account 8300 ($301,131.00) (unspent reserve under Rule 2; producer election is a planning input).
  3. Formal insurance policy binder allocating production package floater Account 8100 ($48,181.00) specifically to New York risks.
  4. Principal photography shoot day logs signed by 1st AD / UPM proving >50% shoot days upstate for § 24(a)(5) non-labor uplift.
* **Supported Scenarios & Bounds:**
  - Lower Bound Floor: Min QPE = **$2,836,167.00** [Credit: **$850,850.10**] (contingency unspent, airfare excluded, baseline insurance excluded).
  - Relocation Baseline Midpoint: Baseline QPE = **$3,274,421.00** [Credit: **$982,326.30**] (100% lodging admitted, contingency unspent, LA editorial excluded).
  - Optimistic Planning Ceiling Upper Bound: Max QPE = **$3,771,497.00** [Credit: **$1,131,449.10**] (100% contingency deployed into BTL physical, 100% lodging admitted, qualifying office/coordination/insurance admitted, LA editorial excluded).
  - *(Historical physical spend base prior to subaccount resolution: **$3,283,489.00** [Credit: **$985,046.70**]).*
* **Expected Engine Behavior:** Incurred-spend evaluations must fail closed or flag `MISSING_AUDIT_EVIDENCE` for unitemized travel and unspent reserves; planning scenario evaluations must admit contingency and lodging strictly subject to explicit producer election and apply statutory 40% ATL cap.
* **Exact Producer Input Needed:** Producer entry in Overview/Inspector of in-state crew lodging breakdown ($ in Account 3900), contingency inclusion % (0% for incurred vs 100% for relocation), NY insurance binder, and county shoot day logs.
* **Comparison Matching:** Compared against identical allocation Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`, Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903` ($4,054,196.00 QPE / $1,216,258.80 Credit). Overstatement of at least **+$84,809.70** is confirmed across all bounds (`NA-DEFECT-01`).

### 6.2 Blocker 2: FVD, BH, LLS New York Individual Talent Contracts & Producer Limit Gaps
* **Blocker ID:** `BLOCKER-02-NY-TALENT-CONTRACTS-GAP`
* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)
* **Missing Facts:** Individual general ledger deal memos, payroll ledgers, and employment contracts for Cast (FVD $1,976,479; BH $974,371; LLS $1,675,000) and Producer accounts (FVD $477,541; LLS $1,184,123) to apply the statutory $500,000 per-person salary cap and the maximum 2 individual producers limit under NY Tax Law § 24(b)(1)(B).
* **Supported Scenarios & Bounds:**
  - FVD: Floor = **$1,256,776.00** [$377,032.80 Credit] (0% ATL); Ceiling = **$1,759,486.40** [$527,845.92 Credit] (40% ATL cap). Engine overstatement >= **+$582,525.48**.
  - BH: Floor = **$749,889.00** [$224,966.70 Credit]; Ceiling = **$1,049,844.60** [$314,953.38 Credit]. Engine overstatement >= **+$383,338.92**.
  - LLS: Floor = **$5,853,484.00** [$1,756,045.20 Credit]; Ceiling = **$8,194,877.60** [$2,458,463.28 Credit]. Engine overstatement >= **+$386,632.92**.
* **Expected Engine Behavior:** When individual talent contracts are absent, calculate and display the supported statutory range [Floor .. Ceiling], enforce the 40% aggregate ATL ceiling, and prevent qualifying aggregate topsheet ATL lines above the cap.
* **Exact Producer Input Needed:** Producer schedule of individual talent earnings listing name, role (writer/director/performer/producer), and total compensation per person; designation of up to 2 credited individual producers qualifying under § 24(b)(1).
* **Comparison Matching:** Compared against identical full relocation allocations for New York State Film Tax Credit: FVD Structure `ae10b2e7-ed52-4ebe-894a-b9d6756ced32` / Result `c3b8ad45-5c1e-47ed-b182-c9106f668b2a`; BH Structure `8558365f-6a68-45a2-931e-4f294ddf20c9` / Result `f3513411-547c-41ca-894d-e1ef36d856b7`; LLS Structure `c135df1f-9a8e-4bdf-b25e-bd6af29a608b` / Result `5557ceb5-d3f5-4b42-85df-d7369d72a9bd`.

### 6.3 Blocker 3: Canadian CAVCO Domestic Certification Gaps (CPTC & OFTTC) & Assistance Deductions
* **Blocker ID:** `BLOCKER-03-CAVCO-DOMESTIC-CERTIFICATION-GAP`
* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)
* **Missing Facts:** CAVCO Part A/B certification, Canadian copyright ownership documentation, and key creative point tally (>= 6/10 CAVCO points) under Income Tax Act § 125.4 and Ontario Taxation Act § 43.
* **Divergent CPTC vs OFTTC Labor Bases:**
  - **Federal CPTC Base ($L_{\text{CA}}$):** Remuneration paid to Canadian citizens or permanent residents residing anywhere in Canada for services rendered in Canada.
  - **Ontario OFTTC Base ($L_{\text{ON}}$):** Remuneration paid to individuals resident specifically in **Ontario** at the end of the calendar year, for services rendered in **Ontario** ($L_{\text{ON}} \le L_{\text{CA}}$).
  - In any production utilizing Canadian crew from other provinces (e.g. BC, Quebec, Alberta), $L_{\text{ON}} < L_{\text{CA}}$, and CPTC and OFTTC bases are NOT identical.
* **Statutory Assistance Deduction Equations:**
  - Ontario OFTTC: $\text{OFTTC} = 0.35 \times L_{\text{ON}}$.
  - Federal CPTC under ITA § 125.4(1): Provincial tax credits constitute government assistance under ITA § 12(1)(x), reducing net production cost: $\text{Net Production Cost} = \text{Gross} - 0.35 \times L_{\text{ON}}$.
  - CPTC Statutory 60% Net Cost Ceiling: $\text{QLE}_{\text{cap}} = 0.60 \times (\text{Gross} - 0.35 \times L_{\text{ON}})$.
  - CPTC Qualified Labour Expenditure: $\text{QLE}_{\text{CPTC}} = \min(L_{\text{CA}}, \text{QLE}_{\text{cap}})$; $\text{CPTC Credit} = 0.25 \times \text{QLE}_{\text{CPTC}}$.
  - **Ceiling at Maximum Ontario Labor ($L_{\text{ON}} = L_{\text{CA}} = L$):**
    $$L \le 0.60 \times (\text{Gross} - 0.35 \times L) \implies L \times 1.21 \le 0.60 \times \text{Gross} \implies L \le \frac{0.60}{1.21} \times \text{Gross} \approx 49.5868\% \times \text{Gross}$$
* **Supported Scenarios & Bounds (from Original Budgets):**
  - Non-Certified Scenario: Ineligible for CPTC/OFTTC ($0.00 credit); eligible instead for production services credits (PSTC / OPSTC) subject to Canadian resident labour expenditure proofs.
  - Certified Domestic Scenario (CPTC 25% + OFTTC 35% with Assistance Deduction at Statutory Ceiling):
    * LU (Gross $4,364,395.00): Max CPTC QLE = **$2,164,162.81**; OFTTC = **$757,456.98**; CPTC = **$541,040.70**; Combined domestic stack = **$1,298,497.68**.
    * FVD (Gross $4,517,687.00): Max CPTC QLE = **$2,240,175.37**; OFTTC = **$784,061.38**; CPTC = **$560,043.84**; Combined domestic stack = **$1,344,105.22**.
    * BH (Gross $2,482,023.00): Max CPTC QLE = **$1,230,755.21**; OFTTC = **$430,764.32**; CPTC = **$307,688.80**; Combined domestic stack = **$738,453.12**.
    * LLS (Gross $11,947,562.00): Max CPTC QLE = **$5,924,410.91**; OFTTC = **$2,073,543.82**; CPTC = **$1,481,102.73**; Combined domestic stack = **$3,554,646.55**.
* **Lawful vs Unlawful Stacking Analysis:** `stack_on_cptc_ofttc` is a lawful domestic stack (subject to CAVCO and assistance deduction). By contrast, `stack_qc_cptc_pstc` is an unlawful cross-regime stack: federal CPTC is restricted to CAVCO domestic content, whereas Quebec PSTC is a service production credit; they cannot legally combine on the same expenditure pool.
* **Expected Engine Behavior:** Treat missing certification as unknown (`NOT_ESTABLISHED`) rather than hard gate rejection or unearned qualification; surface CAVCO status toggle in Overview/Inspector.
* **Exact Producer Input Needed:** Producer input confirming CAVCO certification status (Certified vs Production Services Only) and creative point count.
* **Comparison Matching:** Reconciled across 40 evaluation rows on `ca_federal_cptc`, `on_ofttc`, and domestic stacks (`stack_on_cptc_ofttc`, `stack_qc_cptc_pstc`, `stack_on_ofttc_ocase`).

### 6.4 Blocker 4: Canadian Qualified Labour Expenditure (QLE) Payroll Schedule Gaps (PSTC & OPSTC)
* **Blocker ID:** `BLOCKER-04-CANADIAN-QLE-PAYROLL-GAP`
* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)
* **Missing Facts:** Itemized Canadian payroll general ledger with CAVCO individual residency declarations confirming Canadian citizenship / permanent residency for BTL crew and ATL talent under ITA § 125.5.
* **Retraction of Unsupported 40%–60% Labor Assumption:** Arbitrary default labor ratios (including any 40%–60% heuristic) are formally rejected. In accordance with Codex delta review and statutory rules, actual QLE requires itemized payroll records; planning scenarios must be independently bounded from original budget accounts without invented ratios.
* **Statutory Service Stack Mechanics & Assistance Deduction (ITA § 125.5(1)):**
  - Under ITA § 125.5(1), Qualified Canadian Labour Expenditure (QCLE) is Canadian labour expenditure *net of assistance*: $\text{QCLE} = L_{\text{CA}} - \text{Assistance}$.
  - If Ontario OPSTC ($21.5\% \times L_{\text{ON}}$) reduces federal QCLE: $\text{QCLE} = L_{\text{CA}} - 0.215 \times L_{\text{ON}}$. When $L_{\text{ON}} = L_{\text{CA}} = L$, $\text{QCLE} = 0.785 \times L$.
  - Federal PSTC (16% of QCLE) = $0.16 \times (0.785 \times L) = 12.56\% \times L$.
  - Ontario OPSTC (21.5% of labor) = $21.50\% \times L$.
  - **Statutory Net Stack Rate:** $21.50\% + 12.56\% = \mathbf{34.06\%}$ of labor.
  - **Unreduced Nominal Stack Rate:** $16.00\% + 21.50\% = \mathbf{37.50\%}$ (nominal sum assuming zero federal assistance clawback).
* **Non-Labor Physical BTL Disclaimer:** Departmental Below-The-Line physical totals include non-labor equipment rentals, materials, expendables, fuel, food, and facilities. Treating 100% of physical BTL as labor is an abstract mathematical ceiling, NOT established eligible labor.
* **Supported Scenarios & Bounds (from Original Budgets):**
  - Incurred Evidence Floor: **$0.00** verified credit under strict evidence rules (`NOT_ESTABLISHED (MISSING_PAYROLL_SCHEDULE)`).
  - Direct Line Labor Scenario (Identifiable Crew/Labor Accounts in Original Movie Magic Budgets):
    * LU (Direct Labor $464,916.00: Staff $321,594 + Extras $21,981 + Makeup/Hair $51,809 + Sound $69,532): Statutory Net Stack (34.06%) = **$158,350.39** [OPSTC $99,956.94 + PSTC $58,393.45]; Nominal Unreduced Stack (37.50%) = **$174,343.50** [OPSTC $99,956.94 + PSTC $74,386.56].
    * FVD (Direct Labor $227,641.00: Staff $168,353 + Makeup/Hair $32,830 + Sound $26,458): Statutory Net Stack (34.06%) = **$77,534.53** [OPSTC $48,942.82 + PSTC $28,591.71]; Nominal Unreduced Stack (37.50%) = **$85,365.38** [OPSTC $48,942.82 + PSTC $36,422.56].
    * BH (Direct Labor $167,190.00: Staff $114,906 + Extras $6,235 + Makeup/Hair $29,204 + Sound $16,845): Statutory Net Stack (34.06%) = **$56,944.91** [OPSTC $35,945.85 + PSTC $20,999.06]; Nominal Unreduced Stack (37.50%) = **$62,696.25** [OPSTC $35,945.85 + PSTC $26,750.40].
    * LLS (Direct Labor $1,998,678.00: Staff $608,606 + Background $203,715 + Makeup/Hair $76,175 + Sound $87,067 + Fringes $1,023,115): Statutory Net Stack (34.06%) = **$680,749.73** [OPSTC $429,715.77 + PSTC $251,033.96]; Nominal Unreduced Stack (37.50%) = **$749,504.25** [OPSTC $429,715.77 + PSTC $319,788.48].
  - Abstract Physical BTL Ceiling (Hypothetical Max Departmental Pool Boundary, NOT Established Eligible Labor):
    * LU ($2,642,502.00 BTL): Statutory Net Stack (34.06%) = **$900,036.18**; Nominal Stack (37.50%) = **$990,938.25**.
    * FVD ($1,139,276.00 BTL): Statutory Net Stack (34.06%) = **$388,037.40**; Nominal Stack (37.50%) = **$427,228.50**.
    * BH ($656,044.00 BTL): Statutory Net Stack (34.06%) = **$223,448.59**; Nominal Stack (37.50%) = **$246,016.50**.
    * LLS ($5,166,417.00 BTL): Statutory Net Stack (34.06%) = **$1,759,681.63**; Nominal Stack (37.50%) = **$1,937,406.38**.
* **Lawful Stacking Analysis:** `stack_on_opstc_ocase` (OPSTC on labor + OCASE on computer animation/VFX) and `stack_bc_dave_pstc` (BC PSTC on labor + BC DAVE on digital animation/VFX) are lawful service stacks with no statutory prohibition against stacking.
* **Expected Engine Behavior:** Retract arbitrary 50% heuristic; flag `MISSING_PAYROLL_SCHEDULE` until resident labour is itemized.
* **Exact Producer Input Needed:** Producer upload or entry of Canadian resident payroll ledger or certified labour ratio.
* **Comparison Matching:** Reconciled across 28 rows on Canadian labour programs and stacks; verified zero heuristic substitution under Rule 2.

### 6.5 Blocker 5: High-Earner Salary Caps on Aggregate Topsheets (GA, IL, MA)
* **Blocker ID:** `BLOCKER-05-HIGH-EARNER-SALARY-CAPS-GAP`
* **Classification:** Empirical Evidence Gap (`NOT_ESTABLISHED_EMPIRICAL_GAP`)
* **Missing Facts:** Individual compensation schedule itemizing earnings per payee to apply the statutory $500,000 per-person cap in Georgia (O.C.G.A. § 48-7-40.26) and Illinois (35 ILCS 16/10), and the $1,000,000 per-person cap in Massachusetts (M.G.L. c. 62 § 6(l)).
* **Supported Scenarios & Bounds:**
  - Uncapped Aggregate Spend Scenario: Engine saved baseline (qualifying full aggregate accounts).
  - Fully Capped Scenario: Deduction of excess earnings above statutory per-person caps once payee contracts are supplied.
* **Expected Engine Behavior:** Display aggregate spend as conditional pending payee schedule; flag `MISSING_PAYEE_COMPENSATION_SPLIT` instead of claiming verified defect without contracts.
* **Exact Producer Input Needed:** Producer payroll census listing individual earners in excess of $500,000 / $1,000,000.
* **Comparison Matching:** Reconciled across 12 rows on FVD, BH, LLS; monetary variance claims revoked from open defect totals under `RET-05`.

### 6.6 Blocker 6: Stacking Mutual Exclusivity Violation (`DISC-NY-001` in `stacking_rules.py:617`)
* **Blocker ID:** `BLOCKER-06-NY-STACK-MUTUAL-EXCLUSIVITY-DEFECT`
* **Classification:** Engine Code & Rule Defect (`OPEN_CODE_DEFECT_PENDING_CODEX_REVIEW`)
* **Missing Facts:** None (statutory authority is unambiguous and complete).
* **Supported Scenarios & Bounds:**
  - Statutory Law: § 24 and § 31 cannot stack for the same film under NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c) ($0.00 stack credit; `GATE_REJECTED`).
  - Engine Code Defect: `stacking_rules.py:617` permits distinct-cost pairing (`same_cost_prohibited_distinct_costs_allowed`).
* **Expected Engine Behavior:** Reject `stack_ny_prod_post` as mutually exclusive at the film/taxpayer level.
* **Exact Producer Input Needed:** None (systemic engine rule repair required by Codex).
* **Comparison Matching:** Reconciled across 4 rows on `stack_ny_prod_post`; classified as `COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)` because engine did not generate stack candidate and underlying rule is defective.

### 6.7 Blocker 7: Stale Database Results Pending Canonical Regeneration
* **Blocker ID:** `BLOCKER-07-STALE-DATABASE-REGENERATION`
* **Classification:** Stale Database State (`OLD_SAVED_RESULT_STALE_PENDING_REGENERATION`)
* **Missing Facts:** None (repairs already implemented in canonical codebase in commits `486bd15` and `6cd2bbe`).
* **Affected Programs:** Mexico Federal Film Incentive (F-05), North Carolina Grant (F-03), New Brunswick Tier (F-01), Rhode Island Project Cap (F-04), LU Canadian Stacks (F-06), California Program 4.0 BTL spend classification.
* **Supported Scenarios & Bounds:**
  - Saved Database: `canonical-1.106.0` values persisted in PostgreSQL (`frametax2_claude_optimizer_acceptance_20260919`).
  - Canonical Code: Repaired behavior in `canonical-1.107.0` (commit `486bd15`).
* **Expected Engine Behavior:** Persist freshly calculated results reflecting `canonical-1.107.0` once database regeneration is authorized.
* **Exact Producer Input Needed:** None (system authorization for production regeneration required).
* **Comparison Matching:** Unambiguously identified and separated from open code defects across all affected rows.

---

## 7. Mandatory Gate Disposition & Sign-off

> [!IMPORTANT]
> ### FINAL HANDOFF GATE DISPOSITION:
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> 1. **Zero Acceptance of Defective Totals:** The engine's saved results in `canonical-1.106.0` overstate New York State film tax credits by at least **+$84,809.70** on The Little Utopia (Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903`, Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`) at maximum upper bound ($3,771,497.00) (and +$233,932.50 at baseline, +$365,408.70 at floor), **+$582,525.48** on FVD, **+$383,338.92** on Bad Hombres, and **+$386,632.92** on Lips Like Sugar.
> 2. **Remediation Gate Closed Only upon Codex Review & Regeneration:** Acceptance will NOT close until Codex implements the repair specifications (`NA-DEFECT-01`, `DISC-NY-001`, `DISC-NY-002`, `DISC-NY-003`), runs authorized canonical regeneration, and verifies agreement against independent bounds.
> 3. **Rest-of-World (ROW) Expansion Boundary:** Regional expansion remains strictly paused. ROW audit will not commence until Codex adjudicates this package.
