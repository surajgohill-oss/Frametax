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

### Formal Withdrawal of Unsupported LU Figures & Single Dollar Claims (`RET-09`):
In accordance with Evidence Gate Rules 2, 3, and 5, all previously asserted single-dollar QPE figures and unsupported category substitutions on The Little Utopia are **FORMALLY WITHDRAWN**:
1. **Withdrawal of Fabricated BTL Travel Amount:** The previously asserted BTL travel amount of $82,347.00 is withdrawn. The actual source topsheet contains Account 3900 ($438,254.00), which is an unsplit line lacking in-state lodging versus foreign airfare schedules.
2. **Withdrawal of Fabricated Post-Production Amount:** The previously asserted post-production amount of $208,670.00 is withdrawn. The actual source accounts contain Account 5000 (Editorial in Los Angeles, CA: $9,068.00) and Account 6100 (VFX Department: $52,500.00), totaling $61,568.00.
3. **Withdrawal of Erroneous Contingency Reserve:** The previously asserted contingency reserve of $310,197.00 is corrected to the exact source account figure of $301,131.00 (Account 8300).
4. **Withdrawal of Single Verified Dollar Claim:** Under Evidence Gate Rules 2, 3, and 5, where empirical evidence (travel lodging splits and actual contingency disbursement) is absent, auditors must NOT fabricate exact qualified spend. LU NY is classified as **`NOT_ESTABLISHED (MISSING_TRAVEL_SCHEDULE_AND_CONTINGENCY_DEPLOYMENT)`** with fully evidenced statutory bounds proving engine credit overstatement across all bounds.

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
* **Statutory ATL Ceilings:**
  - **Individual Salary Cap (§ 24(b)(1)(B)):** Maximum of $500,000 in qualifying wages per individual person.
  - **Producer Headcount Limit (§ 24(b)(1)):** Maximum of two (2) individual producers per qualified production.
  - **Aggregate ATL Ceiling (§ 24(b)(1)):** The aggregate amount of all qualifying above-the-line costs shall **not exceed forty percent (40%) of the sum of all other qualified production costs** (i.e., qualified BTL physical production + qualified post-production costs).
* **Statutory Non-Qualifying Exclusions (§ 24(a)(2)):**
  - Financing costs, interest, bridge loan fees, completion bond fees, corporate insurance premiums, and general corporate administration are statutorily excluded.
* **Travel and Living Expenses (5 NYCRR § 170.2):**
  - Under 5 NYCRR § 170.2(b), Below-The-Line travel and living expenses qualify ONLY IF incurred within New York State directly for production crew lodging, meals, and local ground transportation. Airfares originating from or terminating outside New York State, foreign travel, and all Above-The-Line travel are strictly non-qualifying.
* **Upstate Production Credit Uplift (§ 24(a)(5)):**
  - **County Definition:** 53 upstate counties. In accordance with primary text and adjudication finding `NY-A05`, **Dutchess, Orange, and Putnam counties ARE statutorily included** in the upstate production credit county list (unlike the MCTD post-production boundary).
  - **Uplift Rate:** Additional +10% credit (40% total).
  - **Labor Limb:** Wages paid to New York residents for work performed in upstate counties qualify for the +10% uplift.
  - **Non-Labor Limb:** Non-labor qualified costs incurred in upstate counties qualify for the +10% uplift **ONLY IF more than fifty percent (> 50%) of principal photography shoot days** occur in upstate counties.
  - **ATL Exclusion:** ATL wages are statutorily excluded from the +10% uplift (they remain capped at the 30% base rate).

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
  - Editorial (Account 5000): **$9,068.00** (performed in Los Angeles, CA; excluded from NY qualified spend under § 24 territorial rules; allocated outside NY to generic US unpriced in engine trace Segment 0)
  - Accounts 5100, 5200, 5300, 5400, 5500, 6000: **$0.00** in budget file
  - **Total Post-Production Spend:** $52,500.00 + $9,068.00 = **$61,568.00** (reconciling source accounts exactly; withdrawing hallucinated $208,670.00)
* **BTL Travel & Living (Reconciling Source $438,254 vs Hallucinated $82,347):**
  - Account 3900 (`3900 BTL TRAVEL & LIVING`): **$438,254.00**
  - Under 5 NYCRR § 170.2, in-state crew lodging/per diem qualifies, but foreign and out-of-state airfares are statutorily excluded. Because the topsheet lacks departmental ledgers for hotel receipts vs airfares, Account 3900 is an empirical unknown (`CONDITIONAL_BTL_TRAVEL_LIVING`). (Withdrawing hallucinated $82,347.00)
* **Statutory Non-Qualifying Exclusions:**
  - ATL Travel & Living (Account 1600): **$397,279.00** (statutorily excluded under § 24(b)(1))
  - Administrative Expenses (Account 7000): **$297,593.00** (statutorily excluded under § 24(a)(2))
  - Publicity (Account 7100): **$24,348.00** (statutorily excluded under § 24(a)(2))
  - Corporate Insurance (Account 7200): **$12,374.00** (statutorily excluded under § 24(a)(2))
  - Insurance : 1.2% (Account 8100): **$48,181.00** (statutorily excluded under § 24(a)(2))
  - Contingency Reserve : 7.5% (Account 8300): **$301,131.00** (unspent reserve; withdrawing hallucinated $310,197.00; producer election 1.0 is a scenario election, not incurred spend under Rule 2; engine trace Segment 1 excluded $301,131.00)
  - **Total Statutory Exclusions:** $397,279 + $297,593 + $24,348 + $12,374 + $48,181 + $301,131 = **$1,080,906.00** ($1,080,904.00 against controlling gross topsheet)

#### Mathematical Explanation & Resolution of the $138,850 Exclusion Residual:
The previously reported handoff stated:
- Contingency: $310,197.00
- Financing & Legal: $421,791.00
- Insurance & Bond: $130,081.00
- Administrative: $79,985.00
- **Sum of listed lines:** $\$310,197.00 + \$421,791.00 + \$130,081.00 + \$79,985.00 = \mathbf{\$942,054.00}$
- However, the handoff simultaneously asserted total exclusions of **$1,080,904.00** (the difference between $4,364,393 gross and $3,283,489 max spend base).
- The difference between the claimed total and the sum of listed lines was:
  $$\$1,080,904.00 - \$942,054.00 = \mathbf{\$138,850.00}$$
- **Root Cause:** The $138,850 discrepancy was not an unexplained gap in the production budget, but the exact arithmetic shortfall of four manually substituted category figures that did not match the underlying accounts.
- **Evidence-Backed Conservation:** Grounded in the actual 44 source accounts, statutory exclusions total exactly **$1,080,906.00** ($1,080,904.00 gross). Conserving leaf sum: $\$4,364,395.00 - \$1,080,906.00 = \$3,283,489.00$, yielding an unexplained residual of exactly **$0.00**.

#### Supported Statutory Bounds for The Little Utopia (`ny_state_film`):
Because the exact qualifying split of BTL travel ($438,254) and actual disbursement of contingency reserve ($301,131) are empirical unknowns, AUDIT INPUT EVIDENCE GATE Rules 2, 3, and 5 prohibit asserting a single dollar figure. The audit provides rigorous statutory bounds:
1. **Minimum QPE (Lower Bound):**
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
3. **Maximum QPE (Hypothetical Upper Bound):**
   - Hypothetical ceiling assuming 100% BTL travel qualifies and out-of-state editorial is admitted.
   - Other qualified costs (BTL Physical $2,642,502.00 + BTL Travel $438,254.00 + Post VFX $52,500.00 + Post Edit $9,068.00) = **$3,142,324.00**.
   - 40% Statutory ATL Ceiling: $\$3,142,324.00 \times 0.40 = \$1,256,929.60$.
   - Creative ATL Incurred: $141,165.00 (fully admitted).
   - **Max QPE:** $\$3,142,324.00 + \$141,165.00 = \mathbf{\$3,283,489.00}$
   - **Max Base Credit (30%):** $\$3,283,489.00 \times 0.30 = \mathbf{\$985,046.70}$

#### Comparison against Engine Saved Result (`canonical-1.106.0`):
* **Saved Database Match:** Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903` (Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`, Name `Full relocation to US-NY (New York State Film Tax Credit Program (Production))`)
* **Actual Engine Figures:**
  - Segment 0 (Generic US Unpriced): Allocated $9,068.00 (LA Editorial); Qualified Spend = $0.00
  - Segment 1 (US-NY ny_state_film): Allocated $4,355,327.00; Excluded $301,131.00 (Contingency Reserve 8300); Qualified Spend = **$4,054,196.00**
  - Actual Base Incentive: **$1,216,258.80** ($4,054,196.00 × 0.30)
* **Defect Proof across All Bounds (`NA-DEFECT-01`):**
  - Overstatement at Max QPE Upper Bound: $\$1,216,258.80 - \$985,046.70 = \mathbf{+\$231,212.10}$
  - Overstatement at Relocation Baseline: $\$1,216,258.80 - \$982,326.30 = \mathbf{+\$233,932.50}$
  - Overstatement at Min QPE Lower Bound: $\$1,216,258.80 - \$850,850.10 = \mathbf{+\$365,408.70}$
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
* **Engine Comparison (`canonical-1.106.0`, Result ID `602efade-0ccf-43f2-b529-81434c6fd912`):**
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
* **Engine Comparison (`canonical-1.106.0`, Result ID `f7ef008d-ec84-4c96-a9fc-035638a420e7`):**
  - Engine Qualified: $2,327,641.00; Engine Credit: $698,292.30.
  - Overstatement at Maximum Upper Bound: $\Delta \text{Credit}_{\min} = \$698,292.30 - \$314,953.38 = \mathbf{+\$383,338.92}$
  - Overstatement at Lower Bound: $\Delta \text{Credit}_{\max} = \$698,292.30 - \$224,966.70 = \mathbf{+\$473,325.60}$
  - **Conclusion:** Confirms `NA-DEFECT-01` without fabricating an exact payee split.

---

### 3.4 Lips Like Sugar (`LLS`) — Supported Statutory Bounds
* **Gross Controlling Budget:** $11,947,562.00.
* **Source BTL + Post Base (Accounting for `NY-A01` Financing Exclusions):**
  - Production BTL: $5,166,417.00; Travel/Living: $200,000.00; On-Set Sound: $87,067.00; Post: $400,000.00.
  - Excluded Financing Costs (NY-A01): Account 6500 ($450,000), Account 6600 ($250,000), Account 6700 ($1,000,000) are fully excluded.
  - **Sum of Other Qualified Costs (BTL + Post):** **$5,853,484.00**
* **Statutory 40% Aggregate Ceiling:**
  $$\text{Ceiling} = 0.40 \times \$5,853,484.00 = \mathbf{\$2,341,393.60}$$
* **Audit Evidence Evaluation under Rule 5:**
  - Cast (Account 1400, $1,675,000.00) and Producer accounts ($1,184,123.00) exceed $500,000 without payee contracts.
  - Disposition: **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**.
* **Evidenced Statutory Bounds:**
  - **Minimum QPE (Zero ATL Qualified):**
    $$\text{Min QPE} = \mathbf{\$5,853,484.00} \quad [\text{Credit at 30\%: } \mathbf{\$1,756,045.20}]$$
  - **Maximum QPE (Statutory 40% Ceiling Fully Satisfied):**
    $$\text{Max QPE} = \$5,853,484.00 + \$2,341,393.60 = \mathbf{\$8,194,877.60} \quad [\text{Credit at 30\%: } \mathbf{\$2,458,463.28}]$$
* **Engine Comparison (`canonical-1.106.0`, Result ID `f167da0f-bb1a-47e7-829b-b208cc08b38d`):**
  - Engine Qualified: $9,483,654.00; Engine Credit: $2,845,096.20.
  - Overstatement at Maximum Upper Bound: $\Delta \text{Credit}_{\min} = \$2,845,096.20 - \$2,458,463.28 = \mathbf{+\$386,632.92}$
  - Overstatement at Lower Bound: $\Delta \text{Credit}_{\max} = \$2,845,096.20 - \$1,756,045.20 = \mathbf{+\$1,089,051.00}$
  - **Conclusion:** Confirms `NA-DEFECT-01` without fabricating an exact payee split.

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

## 6. Irreducible Empirical Blockers & Acceptance Gate Status

In compliance with `PROJECT_RULES.md` Rule 4 and Rule 8, the following empirical evidence gaps cannot be resolved from existing budget files and represent **irreducible blockers**:

1. **BTL Crew Travel & Living Ledger (LU):**
   - Account 3900 ($438,254.00) is an unsplit topsheet line lacking general ledger records distinguishing in-state crew hotel/per diem from foreign/out-of-state airfares (5 NYCRR § 170.2).
   - **Remediation Action:** Requires itemized crew travel schedules and hotel invoices from production accounting.
2. **Contingency Disbursement Records (LU):**
   - Account 8300 ($301,131.00) is an unspent reserve. Actual incurred spend cannot be established without post-production cost reports showing into which qualifying accounts contingency was deployed.
   - **Remediation Action:** Requires final audited cost reports and general ledger expenditure registers.
3. **Individual Talent Contracts (`MISSING_INDIVIDUAL_TALENT_CONTRACTS` - FVD, BH, LLS):**
   - General ledger talent agreements, per-person compensation schedules, and producer contracts are absent from budget files for FVD, BH, and LLS.
   - Statutory $500k per-person caps and the 2-producer limit cannot be definitively calculated on aggregate topsheet lines without fabricating payee splits.
   - **Remediation Action:** Requires audit access to executed talent payroll ledgers and contracts from production accounting.
4. **Qualified Post-Production Facility Contracts (`MISSING_QPF_CERTIFICATION`):**
   - Qualified post facility agreements, county registrations, and worldwide post spend certifications are absent from source records.
   - **Remediation Action:** Requires post-production accounting logs and ESD-certified QPF vendor invoices.
5. **Upstate Principal Photography Shoot Logs (`MISSING_UPSTATE_SHOOT_LOGS`):**
   - Daily production reports (call sheets / shoot logs) establishing that >50% of principal photography shoot days occurred in upstate counties are absent.
   - Upstate non-labor uplift remains an explicit conditional planning scenario (`CONDITIONAL_UPSTATE_EXPANSION`).
   - **Remediation Action:** Requires production shoot day logs signed by the 1st AD / Unit Production Manager.

---

## 7. Mandatory Gate Disposition & Sign-off

> [!IMPORTANT]
> ### FINAL HANDOFF GATE DISPOSITION:
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> 1. **Zero Acceptance of Defective Totals:** The engine's saved results in `canonical-1.106.0` overstate New York State film tax credits by at least **+$231,212.10** on The Little Utopia (Result ID `340d2041-b11e-4ceb-8c9b-7162f4956903`, Structure ID `14535c49-2dbe-4357-ab61-d3bf5b51c0f4`), **+$582,525.48** on FVD, **+$383,338.92** on Bad Hombres, and **+$386,632.92** on Lips Like Sugar.
> 2. **Remediation Gate Closed Only upon Codex Review & Regeneration:** Acceptance will NOT close until Codex implements the repair specifications (`NA-DEFECT-01`, `DISC-NY-001`, `DISC-NY-002`, `DISC-NY-003`), runs authorized canonical regeneration, and verifies agreement against independent bounds.
> 3. **Rest-of-World (ROW) Expansion Boundary:** Regional expansion remains strictly paused. ROW audit will not commence until Codex adjudicates this package.
