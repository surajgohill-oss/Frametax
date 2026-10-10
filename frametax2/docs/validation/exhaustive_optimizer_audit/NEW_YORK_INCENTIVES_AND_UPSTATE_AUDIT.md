# CINEGLOBE — INDEPENDENT STATUTORY AUDIT: NEW YORK FILM & POST-PRODUCTION INCENTIVES, UPSTATE BENEFITS, AND FOUR-PROJECT SCENARIO EVALUATION

**Audit Mode:** Strictly Read-Only Independent Statutory & Economic Derivation  
**Audit Branch:** `ag/exhaustive-optimizer-audit`  
**Commit Target Audited:** Codex commit `d0e01e285edb8baed4cf1517a4250b6ba6b0051b`  
**Target Codebase HEAD:** `origin/claude/global-optimizer-remediation` at `ee53fb2`  
**Governing Statutory Authorities:**
1. New York Tax Law § 24 (*Empire State Film Production Tax Credit*)
2. New York Tax Law § 31 (*Empire State Film Post-Production Tax Credit*)
3. Empire State Development (ESD) Regulations: 5 NYCRR Part 170 (*Film Production*), Part 240 (*Post-Production*), Part 250 (*Commercials*)
4. Part D of Chapter 59 of the Laws of 2023 (effective April 1, 2023)
5. New York State Department of Taxation and Finance Form CT-261 / IT-261 Instructions

---

## 1. EXECUTIVE SUMMARY & STATUTORY PURPOSE

This audit provides an independent statutory derivation and empirical audit of New York State’s film production and post-production incentive architecture, directly challenging CineGlobe’s current optimizer, rate rules, spend rules, and stacking engine against primary statutory law.

### Core Audit Determinations
1. **Statutory Mutual Exclusivity Between Section 24 and Section 31:**
   Under **NY Tax Law § 31(a)**, an entity or production eligible for the Film Production Credit under **Section 24** is statutorily **prohibited** from claiming the Post-Production Credit under **Section 31**. CineGlobe’s current optimization engine (`backend/app/optimization/stacking_rules.py`, line 617) classifies `frozenset({"ny_state_film", "us_ny_post_production_credit"})` as `same_cost_prohibited_distinct_costs_allowed` and asserts distinct-cost stacking in `test_structural_archetype_generator.py` (lines 504–519). **This is statutorily illegal.** Section 24 already subsumes qualified post-production expenses incurred in NYS within the principal production credit. Section 31 was created exclusively for productions filmed outside New York that bring post-production work to NYS facilities. A single project cannot file under both sections, even on disjoint line items.
2. **Above-The-Line (ATL) Wage Limitations (2023 Statutory Overhaul):**
   Under Part D of Chapter 59 of the Laws of 2023, qualified ATL compensation (writers, directors, producers, performers) is eligible under Section 24 subject to two mandatory statutory ceilings:
   - **Individual Cap:** Capped at **$500,000 per person** (§ 24(b)(2)).
   - **Aggregate Ceiling:** Total qualified ATL costs **cannot exceed 40% of the aggregate sum of all other qualified production costs** (i.e., qualifying BTL physical production + post-production costs).
   CineGlobe's engine (`program_rate_rules_worldwide.py`) identifies this 40% limit in descriptive notes but marks it `unmodeled_spend_split_ratio`, leaving it completely unenforced during candidate pricing.
3. **Severe Flaw in Post-Production Spend Thresholds:**
   CineGlobe’s `US_NY_POST_DOCTRINE` in `program_rate_rules_worldwide.py` hardcodes `min_spend_usd = 1_000_000.0` as an absolute threshold. This directly misrepresents **NY Tax Law § 31(a)(2)**, which provides an alternative statutory gateway: spend must equal or exceed the **lesser of $1,000,000 OR 75% of total post-production costs**. Because of this defect, CineGlobe's candidate evaluation engine evaluated `us_ny_post_production_credit` as `RULE_REJECTED` (`STATUTORY_CONDITIONS_UNMET`) across **all four source budgets** (100% false negative rate), falsely reporting that none of the projects could access New York post-production incentives.
4. **Rate and Uplift Modeling Distortions:**
   - CineGlobe models `us_ny_post_production_credit` as a flat 35% rate, ignoring that downstate post-production receives only 30% and that 35% is strictly an upstate facility uplift (+5%).
   - CineGlobe models 50% and 60% ceiling bands in `program_rate_rules_worldwide.py` that apply to 100% of project QPE, ignoring that the upstate uplift (+10%) and music scoring uplift (+10%) apply only to qualifying labor/scoring subsets, and that "Production Plus" requires high-volume multi-project qualifying history ($100M+ corporate spend).
5. **Four-Project Source Budget Calculations:**
   Independent account-by-account disaggregation of all 158 lines across The Little Utopia ($4,364,395), F#K Valentine’s Day ($4,517,687), Bad Hombres ($2,482,023), and Lips Like Sugar ($11,983,654) proves that CineGlobe's persisted pricing in Bad Hombres overstated NY QPE by **+$1,224,838.40 (+116.7%)** by failing to enforce the 40% ATL cap and failing to exclude non-qualifying development, story rights, insurance, and legal fees.
6. **Open Anchor Acceptance Gate:**
   In compliance with audit governance rules, the Four-Anchor Acceptance Gate remains **OPEN** (`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`).

---

## 2. PRIMARY STATUTORY AUTHORITIES & LEGAL ARCHITECTURE

### A. New York Tax Law § 24: Empire State Film Production Tax Credit
The Empire State Film Production Credit is codified under NY Tax Law § 24 and regulated under 5 NYCRR Part 170. It was substantially revised by Part D, Chapter 59 of the Laws of 2023 for initial applications submitted on or after April 1, 2023.

#### 1. Statutory Rate Structure
- **Base Credit:** **30.0%** of qualified production costs incurred in New York State (§ 24(a)(1)).
- **Upstate Uplift:** Additional **10.0%** (effective **40.0%** credit rate) on qualified production expenditures incurred in designated counties outside the Metropolitan Commuter Transportation District (MCTD) (§ 24(a)(2)).
  - *MCTD Counties (Downstate):* New York (Manhattan), Kings (Brooklyn), Queens, Bronx, Richmond (Staten Island), Nassau, Suffolk, Westchester, Rockland, Putnam, Orange, and Dutchess.
  - *Upstate Designation:* All 50 NYS counties outside the MCTD (e.g., Albany, Erie, Monroe, Onondaga, Ulster, Sullivan, Greene).
  - *Shooting Days Threshold:* The production must shoot at least **50% of its principal photography days** in designated upstate counties. If the production has fewer than 5 principal photography days, all shooting days must be upstate.
  - *Spend Limitation:* The 10% uplift applies strictly to qualifying costs incurred in upstate counties; it does not lift downstate expenditures to 40%.
- **Music Scoring Uplift:** Additional **10.0%** credit on qualified music production/scoring costs incurred in New York State, provided at least 5 musicians participate in the recording sessions (§ 24(a)(2)).
- **Refundability:** Fully refundable tax credit under NY Tax Law § 24(c) (or transferable/carried forward under corporate tax provisions; for Article 9-A corporations, refundable in full over statutory schedules).
- **Program Funding Cap:** Annual statewide aggregate allocation of **$700,000,000** through taxable years beginning before 2035.

#### 2. Eligible Cost Base & Statutory Exclusions
Under NY Tax Law § 24(b)(2) and 5 NYCRR § 170.2:
- **Qualified Costs Include:** Direct physical production costs incurred in New York State for sets, costumes, accessories, camera, lighting, sound recording, grip, studio rental, location fees, equipment rental, travel/transportation within NYS, editing, post-production sound, color grading, visual effects, and qualified ATL/BTL labor.
- **Mandatory Exclusions (Non-Qualifying Costs):**
  1. *Story rights, options, script purchases, and development expenses.*
  2. *Financing costs, loan origination fees, interest payments, bridge loan fees.*
  3. *Legal fees and independent auditing/accounting fees.*
  4. *Marketing, publicity, advertising, public relations, and distribution fees.*
  5. *Contingency reserves, escrow balances, and completion bond fees.*
  6. *Production insurance premiums (general liability, E&O, wrap policies).*
  7. *Wages and expenditures incurred outside New York State.*

#### 3. Above-The-Line (ATL) Labor Ceilings (§ 24(b)(2))
Effective for applications on or after April 1, 2023, ATL salaries are permitted into QPE subject to two non-waivable statutory barriers:
1. **Individual Compensation Cap:** No individual writer, director, producer, or actor can qualify more than **$500,000** in compensation.
2. **The 40% Aggregate BTL Ratio Ceiling:**
   > *"provided further that the total qualified salaries, wages and other compensation paid to writers, directors, producers, and performers shall not exceed forty percent of the aggregate sum of all other qualified production costs incurred in the production of the qualified film."*
   - Let $Q_{\text{BTL+Post}}$ be the sum of all qualifying below-the-line physical production and post-production costs incurred in New York.
   - The maximum allowable qualified ATL compensation is strictly:
     $$Q_{\text{ATL, allowed}} = \min\left(\sum \text{ATL}_{\text{qualified}}, 0.40 \times Q_{\text{BTL+Post}}\right)$$
   - Any ATL compensation exceeding $0.40 \times Q_{\text{BTL+Post}}$ is **disallowed** from New York QPE.

---

### B. New York Tax Law § 31: Empire State Film Post-Production Tax Credit
The Empire State Film Post-Production Credit is codified under NY Tax Law § 31 and regulated under 5 NYCRR Part 240.

#### 1. Statutory Scope & Rate Structure
- **Target Audience:** Productions that film outside of New York State (or shoot minimal footage not qualifying under § 24) and contract post-production work to a qualified New York post-production facility.
- **Base Downstate Rate:** **30.0%** of qualified post-production costs incurred at a qualified facility located within the MCTD (§ 31(a)).
- **Upstate Facility Uplift:** **35.0%** (30% base + 5% upstate uplift) for post-production costs incurred at a qualified facility located outside the MCTD (§ 31(a)(2)).
- **Statutory Spending Thresholds (§ 31(a)(2)):**
  - General Rule: Qualified post-production costs must equal or exceed the **lesser of $1,000,000 OR 75% of total post-production costs**.
  - Visual Effects & Animation Sub-threshold: If post consists primarily of VFX/animation, qualifying costs must equal or exceed the lesser of $500,000 or 10% of total VFX/animation spend (upstate), or $3,000,000 or 20% (downstate).

---

### C. Statutory Anti-Stacking & Mutual Exclusivity: § 24 vs. § 31

The central legal question in CineGlobe’s structural optimizer is whether a single production can claim both the Section 24 Film Production Credit (for principal photography) and the Section 31 Film Post-Production Credit (for post-production).

#### 1. The Controlling Statutory Prohibition
**New York Tax Law § 31(a)** explicitly commands:
> *"A taxpayer which is a qualified film production company or a qualified independent film production company... shall be allowed a credit against such tax... **provided, however, that a taxpayer that is eligible for a credit under section twenty-four of this article shall not be eligible for a credit under this section.**"*

#### 2. Administrative Regulations and Official Forms
- **5 NYCRR § 240.3(c):** *"A taxpayer that is eligible for a credit under section 170 of this Title (Film Production Tax Credit) shall not be eligible for a credit under this Part."*
- **Form CT-261 / IT-261 Instructions:** *"You cannot claim the film post-production credit if you are eligible for the film production credit under Tax Law section 24."*

#### 3. Statutory Mechanics & Rationale
Section 24 already includes qualified post-production expenses as part of the overall film production credit. Under § 24, post-production incurred in NY receives the 30% base rate (or 40% if the production qualifies as upstate). Section 31 was enacted specifically to capture productions that shoot out-of-state and would otherwise never bring post work to New York. The Legislature explicitly prevented double-dipping and dual-program filings by barring any taxpayer eligible for Section 24 from accessing Section 31.

---

## 3. DISCREPANCY ANALYSIS AGAINST CINEGLOBE'S CURRENT RULES

| Discrepancy ID | Rule / Module Affected | CineGlobe Implementation | Primary Statutory Authority | Severity & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **DISC-NY-001** | `backend/app/optimization/stacking_rules.py` (L617) & `test_structural_archetype_generator.py` (L504) | Classifies `(ny_state_film, us_ny_post_production_credit)` as `same_cost_prohibited_distinct_costs_allowed`, allowing simultaneous execution on separate cost pools. | **NY Tax Law § 31(a)**: *"a taxpayer that is eligible for a credit under section twenty-four of this article shall not be eligible for a credit under this section."* | **CRITICAL DEFECT**: Legal invalidity. Engine outputs non-compliant structures claiming both § 24 and § 31. Must be restored to `mutually_exclusive`. |
| **DISC-NY-002** | `backend/app/data/program_rate_rules_worldwide.py` (`US_NY_POST_DOCTRINE`, L2385) | Hardcodes `min_spend_usd = 1_000_000.0` as an absolute threshold for `us_ny_post_production_credit`. | **NY Tax Law § 31(a)(2)**: Minimum spend is the **lesser of $1,000,000 OR 75% of total post spend**. | **CRITICAL DEFECT**: 100% false-negative rate. Rejects post-production incentives for all productions under $1M post spend even when 100% of post is done in NY. |
| **DISC-NY-003** | `backend/app/data/program_rate_rules_worldwide.py` (`US_NY_POST_DOCTRINE`, L2404) | Models `us_ny_post_production_credit` as a flat 35% rate across the board. | **NY Tax Law § 31(a)**: Base downstate post rate is **30.0%**; **35.0%** is an upstate facility uplift (+5.0%). | **HIGH DEFECT**: Overstates downstate post credits by 5.0% across all NYC/downstate post facilities. |
| **DISC-NY-004** | `backend/app/data/program_rate_rules_worldwide.py` (`US_NY_DOCTRINE`, L2249) | Documents the 40% ATL cap in descriptive text but classifies it as `kind="unmodeled_spend_split_ratio"`, failing to enforce it in code. | **NY Tax Law § 24(b)(2)**: Qualified ATL wages capped at **$500,000/person** and aggregate ATL capped at **40% of all other qualified costs**. | **HIGH DEFECT**: Overstates NY production QPE on high-ATL budgets (e.g. Bad Hombres QPE overstated by $1.15M; FVD by $1.33M). |
| **DISC-NY-005** | `backend/app/data/program_spend_rules.py` (L193) | Classifies `ny_state_film` as `QualificationDoctrine.OPEN_DEFAULT_INCLUDE`. | **NY Tax Law § 24(b)(2)**: Expressly excludes development, rights, financing, legal, accounting, marketing, publicity, contingency, and insurance. | **HIGH DEFECT**: In hybrid allocations, engine includes excluded cost categories in NY QPE unless caught by broad negative keywords. |
| **DISC-NY-006** | `backend/app/data/program_rate_rules_worldwide.py` (`US_NY_DOCTRINE`, L2262–2333) | Defines 50% and 60% ceiling tiers that multiply against 100% of project QPE. | **NY Tax Law § 24(a)(2)**: Upstate (+10%) and Scoring (+10%) are **subset uplifts** applying only to specific qualifying spend subsets. | **HIGH DEFECT**: Inflates maximum potential calculations by multiplying entire budget by 50% or 60% instead of subset pricing. |
| **DISC-NY-007** | `backend/app/data/program_rate_rules_worldwide.py` (`US_NY_DOCTRINE`, L2221) | Sets `is_refundable = None` (UNKNOWN). | **NY Tax Law § 24(c)**: Explicitly provides that the credit is fully refundable. | **MEDIUM DEFECT**: Creates uncertainty in optimizer net cash flow modeling for a fully refundable statutory credit. |

---

## 4. INDEPENDENT ACCOUNT-BY-ACCOUNT CALCULATIONS (FOUR SOURCE BUDGETS)

To establish rigorous external benchmarks, every account across the four source budgets was classified under NY Tax Law § 24 and § 31 based on original Movie Magic budget structures.

### Methodology & Control Equations
1. **Excluded Non-QPE Costs ($E$):**
   $$E = \sum (\text{Story/Rights} + \text{Legal/Accounting} + \text{Financing} + \text{Insurance/Bond} + \text{Contingency/Reserves} + \text{Publicity})$$
2. **Other Qualified Production Costs ($Q_{\text{BTL+Post}}$):**
   $$Q_{\text{BTL+Post}} = \sum (\text{BTL Physical Production Lines}) + \sum (\text{Post/Sound/VFX Lines})$$
3. **Allowable Qualified ATL Compensation ($Q_{\text{ATL}}$):**
   $$Q_{\text{ATL}} = \min\left(\sum \text{ATL Lines}, 0.40 \times Q_{\text{BTL+Post}}\right)$$
4. **Total Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
   $$Q_{\text{NY, Prod}} = Q_{\text{BTL+Post}} + Q_{\text{ATL}}$$
5. **Net Production Cost (NPC):**
   $$\text{NPC} = \text{Stated Gross Budget} - \text{Incentive Credit}$$

---

### A. The Little Utopia (LU) — Gross Budget: $4,364,395.00

#### 1. Account Categorization Breakdown (44 Leaf Accounts)
- **Non-Qualifying Excluded Costs ($386,034.00):**
  - Acct 1000 Development: $0.00
  - Acct 7100 Publicity: $24,348.00 (§ 24(b)(2) non-qualifying marketing)
  - Acct 7200 Insurance: $12,374.00 (§ 24(b)(2) non-qualifying insurance)
  - Acct 7300 Marketing: $0.00
  - Acct 7800 Finance & Legal: $0.00
  - Acct 8100 Insurance (1.2%): $48,181.00 (§ 24(b)(2) wrap insurance)
  - Acct 8200 Completion Bond: $0.00
  - Acct 8300 Contingency (7.5%): $301,131.00 (§ 24(b)(2) unspent contingency reserve)
- **BTL Physical Production Spend:** **$3,299,143.00**
- **Post-Production / Sound Spend:** **$140,774.00** (Accts 5100 Editorial $26,087; 5200 Post Sound $17,000; 5300 Lab/Post $26,187; 5400 Titles $2,500; 5500 Music $69,000)
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$3,439,917.00**
- **Above-The-Line Spend ($538,444.00):**
  - Acct 1100 Script: $5,050.00 (under $500k individual cap)
  - Acct 1200 Producer: $0.00
  - Acct 1300 Director: $0.00
  - Acct 1400 Cast: $136,115.00 (under $500k individual cap)
  - Acct 1600 ATL Travel & Living: $397,279.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$3,439,917.00 = \mathbf{\$1,375,966.80}$
  - Actual ATL Spend: $\$538,444.00 \le \$1,375,966.80 \implies$ **100% of ATL Qualifies ($0.00 Disallowance)**.
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):** **$3,978,361.00**

#### 2. Scenario Economics
- **Scenario 1: Downstate NY Full Relocation (§ 24 @ 30.0%):**
  - Qualified QPE: **$3,978,361.00**
  - Incentive Credit: **$1,193,508.30**
  - Net Production Cost (NPC): **$3,170,886.70**
- **Scenario 2: Upstate NY Full Relocation (§ 24 @ 40.0%):**
  - Qualified QPE: **$3,978,361.00**
  - Incentive Credit: **$1,591,344.40**
  - Net Production Cost (NPC): **$2,773,050.60**
  - *Upstate Uplift Benefit (+10%):* **+$397,836.10**
- **Scenario 3: Stand-Alone Post-Production (§ 31):**
  - Post-Production Base: **$140,774.00**
  - Threshold Gateway: Spend ($140,774) $\ge \min(\$1,000,000, 0.75 \times \$140,774 = \$105,580.50) \implies$ **QUALIFIES**.
  - Downstate Post Credit (30.0%): **$42,232.20**
  - Upstate Post Credit (35.0%): **$49,270.90**

---

### B. F#K Valentine’s Day (FVD) — Gross Budget: $4,517,687.00

#### 1. Account Categorization Breakdown (34 Leaf Accounts)
- **Non-Qualifying Excluded Costs ($1,192,001.00):**
  - Acct 1100 Story / Rights / Continuity: $252,650.00 (§ 24(b)(2) non-qualifying development/rights)
  - Acct 7200 Insurance: $50,329.00 (§ 24(b)(2) non-qualifying insurance)
  - Acct 7901 Finance Fee (12.5%): $453,583.00 (§ 24(b)(2) non-qualifying lender financing fee)
  - Acct 7902 Contingency (10.0%): $362,866.00 (§ 24(b)(2) unspent contingency reserve)
  - Acct 7905 Completion Bond (2.0%): $72,573.00 (§ 24(b)(2) non-qualifying bond fee)
- **BTL Physical Production Spend:** **$1,241,293.00**
- **Post-Production / Sound Spend:** **$186,018.00** (Accts 6100 Post $141,018; 6200 Post Sound $45,000)
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$1,427,311.00**
- **Above-The-Line Spend ($1,898,375.00):**
  - Acct 1200 Producers: $401,831.00
  - Acct 1300 Director: $75,710.00
  - Acct 1400 Cast: $1,246,288.00
  - Acct 1600 ATL Travel / Living: $174,546.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$1,427,311.00 = \mathbf{\$570,924.40}$
  - Actual ATL Spend: $\$1,898,375.00 > \$570,924.40$
  - **Statutory Disallowance:** $\$1,898,375.00 - \$570,924.40 = \mathbf{\$1,327,450.60}$ disallowed!
  - Allowable ATL QPE: **$570,924.40**
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$1,427,311.00 + \$570,924.40 = \mathbf{\$1,998,235.40}$$

#### 2. Scenario Economics
- **Scenario 1: Downstate NY Full Relocation (§ 24 @ 30.0%):**
  - Qualified QPE: **$1,998,235.40**
  - Incentive Credit: **$599,470.62**
  - Net Production Cost (NPC): **$3,918,216.38**
- **Scenario 2: Upstate NY Full Relocation (§ 24 @ 40.0%):**
  - Qualified QPE: **$1,998,235.40**
  - Incentive Credit: **$799,294.16**
  - Net Production Cost (NPC): **$3,718,392.84**
  - *Upstate Uplift Benefit (+10%):* **+$199,823.54**
- **Scenario 3: Stand-Alone Post-Production (§ 31):**
  - Post-Production Base: **$186,018.00**
  - Threshold Gateway: Spend ($186,018) $\ge \min(\$1,000,000, 0.75 \times \$186,018 = \$139,513.50) \implies$ **QUALIFIES**.
  - Downstate Post Credit (30.0%): **$55,805.40**
  - Upstate Post Credit (35.0%): **$65,106.30**

---

### C. Bad Hombres (BH) — Gross Budget: $2,482,023.00

#### 1. Account Categorization Breakdown (34 Leaf Accounts)
- **Non-Qualifying Excluded Costs ($276,913.00):**
  - Acct 1100 Story, Rights & Continuity: $74,531.00 (§ 24(b)(2) non-qualifying development/rights)
  - Acct 1600 SAG Deposit / Residual Reserve: $60,000.00 (§ 24(b)(2) unspent escrow reserve)
  - Acct 6700 Insurance: $0.00
  - Acct 7600 Legal and Accounting: $24,000.00 (§ 24(b)(2) professional fees)
  - Acct 7700 Insurance: $24,000.00 (§ 24(b)(2) insurance premium)
  - Acct CONTINGENCY Contingency: $94,382.00 (§ 24(b)(2) unspent contingency reserve)
- **BTL Physical Production Spend:** **$625,086.00**
- **Post-Production / Sound Spend:** **$124,803.00** (Accts 5100 Post $107,958; 5200 Post Sound $16,845)
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$749,889.00**
- **Above-The-Line Spend ($1,455,221.00):**
  - Acct 1200 Producers Unit: $267,169.00
  - Acct 1300 Director: $75,000.00
  - Acct 1400 Cast: $1,032,202.00
  - Acct 1500 Travel & Living: $80,850.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$749,889.00 = \mathbf{\$299,955.60}$
  - Actual ATL Spend: $\$1,455,221.00 > \$299,955.60$
  - **Statutory Disallowance:** $\$1,455,221.00 - \$299,955.60 = \mathbf{\$1,155,265.40}$ disallowed!
  - Allowable ATL QPE: **$299,955.60**
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$749,889.00 + \$299,955.60 = \mathbf{\$1,049,844.60}$$

#### 2. Scenario Economics
- **Scenario 1: Downstate NY Full Relocation (§ 24 @ 30.0%):**
  - Qualified QPE: **$1,049,844.60**
  - Incentive Credit: **$314,953.38**
  - Net Production Cost (NPC): **$2,167,069.62**
- **Scenario 2: Upstate NY Full Relocation (§ 24 @ 40.0%):**
  - Qualified QPE: **$1,049,844.60**
  - Incentive Credit: **$419,937.84**
  - Net Production Cost (NPC): **$2,062,085.16**
  - *Upstate Uplift Benefit (+10%):* **+$104,984.46**
- **Scenario 3: Stand-Alone Post-Production (§ 31):**
  - Post-Production Base: **$124,803.00**
  - Threshold Gateway: Spend ($124,803) $\ge \min(\$1,000,000, 0.75 \times \$124,803 = \$93,602.25) \implies$ **QUALIFIES**.
  - Downstate Post Credit (30.0%): **$37,440.90**
  - Upstate Post Credit (35.0%): **$43,681.05**

---

### D. Lips Like Sugar (LLS) — Gross Budget: $11,983,654.00

#### 1. Account Categorization Breakdown (46 Leaf Accounts)
- **Non-Qualifying Excluded Costs ($1,621,000.00):**
  - Acct 6100 Publicity: $0.00
  - Acct 6200 Legal Costs: $150,000.00 (§ 24(b)(2) professional legal fees)
  - Acct 6300 Insurance: $106,000.00 (§ 24(b)(2) wrap insurance)
  - Acct 6500 Financing Fees: $450,000.00 (§ 24(b)(2) lender/bank financing fees)
  - Acct 6800 Residuals Reserve: $400,000.00 (§ 24(b)(2) unspent contingency escrow)
  - Acct 7100 Contingency: $400,000.00 (§ 24(b)(2) unspent contingency reserve)
  - Acct 7200 Completion Bond Fee: $115,000.00 (§ 24(b)(2) bond fee)
- **BTL Physical Production Spend:** **$6,449,382.00**
- **Post-Production / Sound Spend:** **$738,297.00** (Accts 4100 Editorial $208,614; 4200 Post Sound $115,000; 4300 Music $200,000; 4400 Post Lab $149,683; 4500 Titles $65,000)
- **Base "All Other Qualified Costs" ($Q_{\text{BTL+Post}}$):** **$7,187,679.00**
- **Above-The-Line Spend ($3,174,975.00):**
  - Acct 1100 Script: $314,153.00
  - Acct 1200 Producing: $1,414,198.00
  - Acct 1300 Directing: $267,384.00
  - Acct 1400 Cast: $863,388.00
  - Acct 1500 ATL Travel & Living: $60,561.00
  - Acct 1900 Total Fringes (ATL): $255,291.00
- **ATL Ceiling Evaluation:**
  - 40% Aggregate Ceiling: $0.40 \times \$7,187,679.00 = \mathbf{\$2,875,071.60}$
  - Actual ATL Spend: $\$3,174,975.00 > \$2,875,071.60$
  - **Statutory Disallowance:** $\$3,174,975.00 - \$2,875,071.60 = \mathbf{\$299,903.40}$ disallowed!
  - Allowable ATL QPE: **$2,875,071.60**
- **Total NY Qualified Production Expenditure ($Q_{\text{NY, Prod}}$):**
  $$Q_{\text{NY, Prod}} = \$7,187,679.00 + \$2,875,071.60 = \mathbf{\$10,062,750.60}$$

#### 2. Scenario Economics
- **Scenario 1: Downstate NY Full Relocation (§ 24 @ 30.0%):**
  - Qualified QPE: **$10,062,750.60**
  - Incentive Credit: **$3,018,825.18**
  - Net Production Cost (NPC): **$8,964,828.82**
- **Scenario 2: Upstate NY Full Relocation (§ 24 @ 40.0%):**
  - Qualified QPE: **$10,062,750.60**
  - Incentive Credit: **$4,025,100.24**
  - Net Production Cost (NPC): **$7,958,553.76**
  - *Upstate Uplift Benefit (+10%):* **+$1,006,275.06**
- **Scenario 3: Stand-Alone Post-Production (§ 31):**
  - Post-Production Base: **$738,297.00**
  - Threshold Gateway: Spend ($738,297) $\ge \min(\$1,000,000, 0.75 \times \$738,297 = \$553,722.75) \implies$ **QUALIFIES**.
  - Downstate Post Credit (30.0%): **$221,489.10**
  - Upstate Post Credit (35.0%): **$258,403.95**

---

### E. Comparative Synthesis Across All Four Source Budgets

```
===================================================================================================================================
Project                  Stated Gross     Non-QPE Excluded    BTL Base (Other)    Capped ATL (≤40%)   Total NY QPE (§ 24)
-----------------------------------------------------------------------------------------------------------------------------------
The Little Utopia (LU)   $4,364,395.00    $386,034.00         $3,439,917.00       $538,444.00         $3,978,361.00
F#K Valentine's Day(FVD) $4,517,687.00    $1,192,001.00       $1,427,311.00       $570,924.40         $1,998,235.40
Bad Hombres (BH)         $2,482,023.00    $276,913.00         $749,889.00         $299,955.60         $1,049,844.60
Lips Like Sugar (LLS)    $11,983,654.00   $1,621,000.00       $7,187,679.00       $2,875,071.60       $10,062,750.60
===================================================================================================================================

===================================================================================================================================
Project                  Downstate (30%) Credit   Downstate NPC        Upstate (40%) Credit     Upstate NPC          Upstate Gain (+10%)
-----------------------------------------------------------------------------------------------------------------------------------
The Little Utopia (LU)   $1,193,508.30            $3,170,886.70        $1,591,344.40            $2,773,050.60        +$397,836.10
F#K Valentine's Day(FVD) $599,470.62              $3,918,216.38        $799,294.16              $3,718,392.84        +$199,823.54
Bad Hombres (BH)         $314,953.38              $2,167,069.62        $419,937.84              $2,062,085.16        +$104,984.46
Lips Like Sugar (LLS)    $3,018,825.18            $8,964,828.82        $4,025,100.24            $7,958,553.76        +$1,006,275.06
===================================================================================================================================

===================================================================================================================================
Project                  Post Base (§ 31)   Meets Gateway (75% Rule)   Downstate Post (30%)     Upstate Post (35%)
-----------------------------------------------------------------------------------------------------------------------------------
The Little Utopia (LU)   $140,774.00        True ($140.8k ≥ $105.6k)   $42,232.20               $49,270.90
F#K Valentine's Day(FVD) $186,018.00        True ($186.0k ≥ $139.5k)   $55,805.40               $65,106.30
Bad Hombres (BH)         $124,803.00        True ($124.8k ≥ $93.6k)    $37,440.90               $43,681.05
Lips Like Sugar (LLS)    $738,297.00        True ($738.3k ≥ $553.7k)   $221,489.10              $258,403.95
===================================================================================================================================
```

---

## 5. COMPARISON WITH CINEGLOBE'S EXISTING CALCULATIONS

A direct empirical comparison was conducted against CineGlobe’s persisted calculation aggregates in PostgreSQL (`evaluation_candidate_aggregates`):

### 1. Massive Overstatement in Bad Hombres Hybrid Allocation
- **CineGlobe Persisted Record:** In a 3-way hybrid candidate (`ny_state_film` + `us_nm_film_credit` + `ca_nl_all_spend_credit`), CineGlobe allocated **$2,369,065.00** to `ny_state_film` and priced an incentive of **$682,404.90** based on **$2,274,683.00 QPE** ($2,369,065.00 minus $94,382 contingency).
- **Statutory Audit Finding:** CineGlobe’s QPE included:
  - $74,531 Story Rights (statutorily non-qualifying under § 24(b)(2))
  - $60,000 SAG Deposit / Escrow Reserve (statutorily non-qualifying under § 24(b)(2))
  - $24,000 Legal & Accounting Fees (statutorily non-qualifying under § 24(b)(2))
  - $24,000 Insurance (statutorily non-qualifying under § 24(b)(2))
  - $1,455,221 Raw ATL Compensation without applying the 40% aggregate cap ($299,955.60 maximum allowable).
- **Variance:** CineGlobe overstated QPE by **+$1,224,838.40 (+116.7%)** and overstated incentive credit by **+$367,451.52 (+116.7%)** compared to the statutory downstate baseline ($314,953.38).

### 2. False Rejections of Post-Production Across All Four Budgets
- In `evaluation_candidate_aggregates`, exactly **82 candidate aggregates** evaluated pure `us_ny_post_production_credit`.
- **100% of these rows were classified `status=RULE_REJECTED`, `reason_class=STATUTORY_CONDITIONS_UNMET`**.
- **Root Cause:** CineGlobe evaluated only the $1,000,000 branch of the minimum spend rule, completely ignoring the statutory 75% alternative branch. Because LU ($140.8k), FVD ($186.0k), BH ($124.8k), and LLS ($738.3k) all have post budgets below $1M, CineGlobe falsely disqualified all four projects from New York post incentives.

---

## 6. DISCLOSED ASSUMPTIONS & MISSING PRODUCTION FACTS

In accordance with PROJECT_RULES.md, all independent derivations disclose explicit operating assumptions and identify missing production facts that prevent final certification:

1. **Relocation & Nexus Assumptions:**
   - *Full Relocation Scenario:* Assumes 100% of principal photography and 100% of physical production, cast, and crew services are performed within New York State.
   - *Upstate Scenario:* Assumes at least 50% of principal photography shooting days occur in designated upstate counties outside the MCTD, and that 100% of qualified spend is incurred in those upstate counties.
   - *Stand-Alone Post Scenario:* Assumes filming occurs out-of-state and 100% of post-production editorial, sound, VFX, and lab services are performed at a qualified New York post-production facility.
2. **Missing Production Facts (Non-Deducible from Budgets):**
   - *Individual Talent Contracts:* Budgets aggregate producer and cast accounts (e.g. LLS Producer $1,414,198; LLS Cast $863,388). Individual per-actor and per-producer contracts are not disclosed, preventing empirical verification of individual $500,000 caps.
   - *Shooting Day Location Breakdown:* Actual shooting day counts by county are not provided in the Movie Magic budget files.
   - *Scoring Musician Headcount:* Music scoring budgets do not disclose whether at least 5 musicians participate, preventing definitive application of the +10% scoring uplift.
   - *Corporate Track Record:* Whether the production company has concurrent NY productions meeting the high-spend thresholds required for "Production Plus" (+5% to +10%) is an unknown producer election fact.

---

## 7. FOUR-ANCHOR ACCEPTANCE GATE DISPOSITION

**STATUS: ANCHOR ACCEPTANCE GATE REMAINS OPEN**

**Disposition Formulation:**
`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`

The calculations and statutory rules derived in this report represent the independent, source-grounded expectations for New York State film and post-production incentives. However, because production evaluations must not be run cold without explicit user instruction, the four-anchor acceptance gate remains strictly **OPEN** until the optimizer rules are updated and regenerated under authorized execution.
