# Independent Audit of Codex d0e01e2 Against Source Budgets and Statutory Rules

**Audit Target Commit:** `d0e01e285edb8baed4cf1517a4250b6ba6b0051b` (`origin/codex/four-anchor-qpe-closeout` / `origin/claude/global-optimizer-remediation`)  
**Audit Branch:** `ag/exhaustive-optimizer-audit`  
**Audit Date:** 2026-10-10  
**Scope Mode:** Read-Only Independent Audit — Zero Code or Production Data Modifications; No Cold Real-Project Evaluations  

---

## Executive Summary & Terminal Disposition

This report presents Antigravity's (AG) exhaustive, independent audit of Codex commit `d0e01e2` against the four canonical source production budgets (**The Little Utopia**, **F#K Valentine's Day**, **Bad Hombres**, and **Lips Like Sugar**) and primary statutory authority frameworks (Mauritius EDB, Greek Law 4487/2017 & JMD 607434/2026, New Mexico Film Production Tax Credit Act NMSA 1978 § 7-2F-1 & TRD FYI-370, and California Film & Television Tax Credit Program 4.0 / Cal. Rev. & Tax Code § 17053.98).

### Overall Disposition
**ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; FOUR-ANCHOR PRODUCTION REGENERATION REMAINS PENDING EXPLICIT USER AUTHORIZATION.**

Codex commit `d0e01e2` (and its constituent commits `37c13b6`, `666a4b7`, and `62aa346`) substantively closes the structural and canonical calculation defects identified across the four anchors. Specifically, it establishes:
1. **Source Detail Conservation:** Authored Movie Magic child subaccounts refine parent accounts without inflating gross spend (40 conserving groups in Lips Like Sugar; zero synthetic splits invented for other budgets).
2. **Cross-Format Netting Isolation:** Producer rebate estimates and net totals are strictly isolated from gross production costs across PDF, CSV, and XLSX formats, preserving credit financing/bridge fees as costs.
3. **California Detail Disaggregation:** Implementation of the California Film Commission (CFC) January 2026 Qualified Expenditure Chart disaggregates mixed Above-The-Line (ATL) accounts based solely on conserving detail, correctly excluding the $300,000 writer fee and capping the line producer at $100,000 conditional BTL spend.
4. **Fringe Allocation Linkage:** ATL payroll fringes are classified as fact-dependent grey areas requiring underlying qualified payee compensation linkage.
5. **Reserve Hygiene:** Unexpended escrow deposits and contingency reserves are excluded from confirmed qualifying base QPE unless proof of in-state disbursement is evidenced.
6. **Subset Uplift Precision:** Uplifts apply only to eligible qualifying subsets (e.g. out-of-zone shoot days, local resident hires, rural spend excluding nonresident BTL), rejecting program-wide blanket uplifts on 100% of QPE.
7. **Statutory Cap Separation:** The Greek ordinary grant cap of €8,000,000 is cleanly distinguished from the €10,000,000 strategic exception, and project caps are decoupled from annual fund appropriations.

However, in accordance with `PROJECT_RULES.md`, live production acceptance is **NOT GRANTED** because real-project recomputation and database mutations were not authorized and did not occur. Prospective current-law numbers remain conditional planning projections, and historical QPE claims remain `NOT_ESTABLISHED` where local payroll and tax records are absent.

---

## 1. Mandatory Rectification of Previous AG Contradictions

In accordance with user instructions, this audit explicitly identifies, retracts, and corrects previous AG analytical contradictions.

### 1.1 Formal Retraction of California Control Contradiction (Issue Q01)
- **Previous AG Error:** In earlier calculation passes, AG cited a California qualified expenditure base of **$7,351,825** and an incentive of **$1,470,365** as an "independently verified" control for Lips Like Sugar under current Program 4.0 modeling, deriving the base by reverse-dividing $1,470,365 by 20.0%.
- **Statutory & Evidentiary Reality:**
  1. The $1,470,365 figure originates from **CAL #8-053** (dated March 6, 2023), which is a historical **Program 3.0** conditional tax credit reservation form under the category *"Independent Film $10m & Under"*.
  2. Under California Film Commission Program 3.0 regulations, the base tax credit rate for the *"Independent Film $10m & Under"* category was **25.0%**, not 20.0% (the 20.0% rate governed non-independent feature films). The implied qualified expenditure base supporting that reservation was therefore **$5,881,460** ($1,470,365 / 0.25), not $7,351,825.
  3. The producer's revised budget (v7 dated 02/25/2024) Line 9998 contains a producer estimate of **$1,503,074 at 25%**, which implies a BTL spend base of **$6,012,296**. This represents producer internal planning, not a government-verified audit schedule.
  4. The current CineGlobe optimizer models **Program 4.0** (effective for applications beginning 2025/2026), where independent feature films receive a **35.0% base rate** with a **$20,000,000 qualified expenditure cap**.
- **Formal Retraction & Correction:** AG **formally retracts** the $7,351,825 base and $1,470,365 as an independent calculation control for Program 4.0. CAL #8-053 is historical evidence of a conditional reservation under a prior statutory regime; Line 9998 is producer planning evidence. Exact independent historical and prospective QPE for Lips Like Sugar remain **`NOT_ESTABLISHED`** due to the absence of underlying vendor residency and location spend schedules.

### 1.2 Formal Retraction of Bad Hombres SAG Reserve Contradiction (Issue Q04)
- **Previous AG Error:** AG previously included Line 1600 (**$60,000 SAG DEPOSIT / RESIDUAL RESERVE**) in New Mexico qualifying production spend ($2,387,641) while simultaneously noting in text that it was an unexpended escrow and missing incurred-cost proof.
- **Statutory & Evidentiary Reality:**
  1. Under the New Mexico Film Production Tax Credit Act (NMSA 1978 § 7-2F-1(B)) and New Mexico Taxation & Revenue Department (TRD) guidance Bulletin FYI-370 (July 2025), a qualifying expenditure must be directly incurred and disbursed for physical production services rendered in New Mexico.
  2. A guild escrow deposit (such as a SAG-AFTRA security deposit or residual reserve) is a contingent reserve against future liabilities. Unless and until affirmative proof of actual disbursement for qualified post-production services in New Mexico is evidenced, an unspent escrow cannot qualify as an incurred expenditure.
  3. Including the $60,000 in QPE while calling it an unproven fact gap created an irreconcilable internal contradiction.
- **Formal Retraction & Correction:** AG **formally retracts** the inclusion of Line 1600 ($60,000) in confirmed QPE. Line 1600 is classified as `GREY_AREA_REQUIRES_AUTHORITY` with reason `MISSING_PRODUCTION_FACT` (contingent upon local disbursement proof), and is **excluded from confirmed base QPE**.
  - Confirmed base QPE without reserve: **$2,327,641.00**
  - Confirmed base statutory incentive (25.0%): **$581,910.25** (vs engine served floor of $596,910.25 on $2,387,641)
  - Isolated reserve sensitivity delta: **$15,000.00** ($60,000 × 0.25).
  - Furthermore, AG formally retracts its previous blanket deduction of $1,032,202 for performing artists (cast): under NMSA 1978 § 7-2F-1(B) and NMAC 3.13.2, nonresident performing artists *are* eligible for the 25% credit subject to statutory 5% state tax withholding. Exact QPE is `NOT_ESTABLISHED` without payroll withholding audit records.

---

## 2. Technical Audit of Codex d0e01e2 Across Core Domains

### 2.1 Budget Categorization & Movie Magic Preservation (Issues Q08, Q09, Q14)
- **Account Census:** Read-only re-parsing of the 4 original PDFs confirms 158 leaf accounts across the four productions:
  - The Little Utopia: 44 accounts, $4,364,393 declared gross ($4,364,395 leaf sum, retaining the authored $2 discrepancy).
  - F#K Valentine's Day: 34 accounts, $4,517,687 declared gross.
  - Bad Hombres: 34 accounts, $2,482,023 declared gross.
  - Lips Like Sugar: 46 accounts, $11,983,654 declared gross.
- **Movie Magic Structure (`budget_parser._movie_magic_subaccounts`):**
  - Child subaccount detail totals are captured as non-cost metadata on parent lines.
  - Lips Like Sugar contains **40 conserving detail groups** where child lines exactly equal parent account totals.
  - For LU, FVD, and BH, the parser correctly identifies zero conserving groups; **no synthetic splits are fabricated**.
- **Publicity & Category Retention (`material_routing._preserve_recognized_source_categories`):**
  - The classifier correctly classifies LU Line 7100 ($24,348 PUBLICITY) as `general_administration`. In older persisted runs, this was stale `btl_crew_labor`.
  - The refresh mechanism ensures that fresh explicit classifications take precedence, fixing publicity, while unique source-identical lines retain reviewed historical categories when fresh parsing falls back to `miscellaneous`.

### 2.2 Incentive and Net Separation Across Formats (Issues Q07, Q13)
- **Regex Guard (`_is_budget_netting`):**
  - Distinguishes credit financing fees (which are expenses) from tax credit receipts/net totals. Descriptions matching `\b(financ(?:e|ing)|bridge|interest|application|audit)\b.*\b(fee|cost|expense)s?\b` remain costs.
- **Spreadsheet Netting Isolation (`_separate_spreadsheet_evidence`):**
  - In CSV and XLSX ingestion, producer incentive lines are extracted into `source_incentive_estimates`, net totals are removed, and `total_budget_raw` is computed solely from gross cost lines.
  - Negative signs in spreadsheets (`-$`, `$-`, parentheses) parse deterministically.
- **Isolated Synthetic Controls:**
  - `BudgetNettingControls` (4 tests) and `TextNettingControls` (2 tests) pass 100%, proving zero leakage of rebate receipts into gross spend.

### 2.3 California Mixed Accounts & Conserving Detail Splits (Issue Q02)
- **Statutory Authority:** California Film Commission Program 4.0 Qualified Expenditure Chart (January 2026).
- **Rule Implementation (`program_spend_rules.california_source_subaccount_treatment` & `qualification_derivation.derive_qualification_register`):**
  - Subaccount splitting occurs *only* when child lines are finite, non-negative, have unique account codes, and sum to the parent within $0.005. Non-conserving details leave the entire parent in `GREY_AREA_REQUIRES_AUTHORITY`.
  - **Account 1100 (SCRIPT - $314,153):**
    - 1109 WRITER FEES ($300,000): `EXCLUDED`
    - 1110 PUBLICATION ($12,500): `EXCLUDED`
    - 1124 RESEARCH ($1,350): `QUALIFIES`
    - 1150 DUPLICATION ($303): `QUALIFIES`
    - Confirmed Qualified: $1,653; Excluded: $312,500.
  - **Account 1200 (PRODUCERS - $1,414,198):**
    - Line Producer (1215 - $151,198): Capped at $100,000 conditional BTL spend (`GREY_AREA_REQUIRES_AUTHORITY`); $51,198 `EXCLUDED`.
    - Executive producers and overhead: `EXCLUDED`.
    - Producer assistants: `QUALIFIES`.
  - **Account 1300 (DIRECTING - $267,384) & Account 1400 (CAST - $863,388):**
    - Principal fees excluded; stunt/assistant lines qualify.

### 2.4 Fringes Linkage to Underlying Compensation (Issue Q03)
- Under CFC Program 4.0 QEC, payroll fringes follow the qualifying underlying labor.
- In `qualification_derivation.py`, ATL payroll fringes (LLS Line 5 / 1900 Total Fringes, $255,291) are classified as `GREY_AREA_REQUIRES_AUTHORITY` with reason `MISSING_PRODUCTION_FACT` because ATL labor mixes excluded principal compensation with qualifying assistants. No arbitrary percentage is guessed.

### 2.5 Uplift Subsets and Statutory Caps (Issues Q05, Q06)
- **Subset Uplift Engine (`allocation_pricing._price_subset_uplifts` and `EligibleSubsetUpliftRule`):**
  - Uplifts require line-specific evidenced bases (`uplift_basis:<slug>:<uplift_id>:<line_id>`).
  - **California (`ca_film_30`):**
    - Outside LA Zone (+5%): Applies only to qualified expenses incurred outside the zone.
    - Local Hire Outside LA (+10%): Constrained to qualifying resident labor (`btl_crew_labor`, `btl_resident_labor`, `payroll_fringes`).
    - Qualified VFX (+5%): Constrained to `vfx`; explicitly excluded for independent features (`ca_film_independent_category`).
  - **New Mexico (`us_nm_film_credit`):**
    - Rural Location (+10%): Excludes nonresident BTL labor.
    - Qualified Facility (+5%): Mutually exclusive with Qualified TV (+5%).
    - TV series uplift is excluded for feature films.
- **Greek Statutory Cap (`program_rate_rules.INCENTIVE_VALUE_CAP_RULES['gr_cash_rebate']`):**
  - Ordinary grant cap is set to **€8,000,000** (Law 4487/2017 Art. 4(2)).
  - Strategic investment exception of **€10,000,000** requires explicit joint ministerial decision (`exception_approval_fact_key="gr_strategic_project_joint_ministerial_approval"`). An application or request does not raise the cap.

---

## 3. Comprehensive Reconciliation Against Codex Issue Register (Q01–Q15)

| ID | Codex Issue & Adjudication | AG Independent Finding | AG Terminal Disposition |
|---|---|---|---|
| **Q01** | California 20% / $7,351,825 control rejected. Program 4.0 uses 35% base. Budget 25% is planning estimate. | **AGREED.** AG retracts $7,351,825 and 20% control. CAL #8-053 was 25% Program 3.0 reservation. Program 4.0 independent limit is $20M at 35%. Independent exact QPE is `NOT_ESTABLISHED`. | **RECONCILED / CORRECTED** |
| **Q02** | Mixed ATL accounts cannot qualify or be excluded as whole categories. Conserve authored subaccount splits under CFC Jan 2026 chart. | **AGREED.** Verified `program_spend_rules.py` and `qualification_derivation.py`. LLS SCRIPT splits $1,653 qualify, $312.5k exclude; Line producer capped at $100k conditional. | **RECONCILED / VERIFIED** |
| **Q03** | California ATL fringes qualified without underlying eligible compensation linkage. | **AGREED.** LLS Line 1900 ($255,291) classified as `GREY_AREA_REQUIRES_AUTHORITY` / `MISSING_PRODUCTION_FACT`. Fringes follow underlying payee eligibility. | **RECONCILED / VERIFIED** |
| **Q04** | BH reserve contradiction: AG included $60,000 while flagging proof missing. | **AGREED.** AG retracts inclusion of $60,000 SAG deposit in confirmed QPE. Classified as `GREY_AREA_REQUIRES_AUTHORITY` / `MISSING_PRODUCTION_FACT`. Confirmed base QPE is $2,327,641. | **RECONCILED / CORRECTED** |
| **Q05** | Program-wide maximum rates incorrectly apply uplifts to 100% of QPE. | **AGREED.** `_price_subset_uplifts` enforces line-specific predicates, excludes nonresident BTL from NM rural uplift, and excludes independent features from CA VFX uplift. | **RECONCILED / VERIFIED** |
| **Q06** | Greek ordinary grant cap (€8m) confused with strategic-project exception (€10m). | **AGREED.** `IncentiveValueCapRule` implements €8M ordinary cap and €10M exception gated on ministerial approval. | **RECONCILED / VERIFIED** |
| **Q07** | CSV/XLSX incentive and net rows enter gross cost; CSV negative sign lost. | **AGREED.** `_is_budget_netting`, `_separate_spreadsheet_evidence`, and negative sign parsing verified. Financing fees preserved. | **RECONCILED / VERIFIED** |
| **Q08** | LU stored publicity is crew labour. | **AGREED.** Canonical classifier correctly assigns `general_administration`. `_preserve_recognized_source_categories` ensures publicity is corrected on refresh. | **RECONCILED / VERIFIED** |
| **Q09** | Movie Magic subaccount details discarded before qualification. | **AGREED.** `source_subaccounts` captured in `ParsedLineItem` and propagated to `BudgetLineItem`. LLS 40 conserving groups preserved; 0 invented splits elsewhere. | **RECONCILED / VERIFIED** |
| **Q10** | Territorial spend, resident payroll, vendor status, and application date missing. | **AGREED.** Missing facts documented. Projections remain conditional planning scenarios; cannot be called certified claims. | **RECONCILED / VERIFIED** |
| **Q11** | Historical control and current-law hypothetical conflated. | **AGREED.** Historical baseline evidence kept strictly separated from prospective current-law evaluations. | **RECONCILED / VERIFIED** |
| **Q12** | Circular engine comparisons / copied expectations accepted as independent audit. | **AGREED.** Independent expectations derived from primary statutory texts and raw line schedules. Mutation controls passed. | **RECONCILED / VERIFIED** |
| **Q13** | NPC can double-count embedded financing or subtract incentives twice. | **AGREED.** Gross cost and financing contracts verified. Netting controls prevent receipts entering spend. | **RECONCILED / VERIFIED** |
| **Q14** | Older persisted calculations contain no newly retained source detail / different rules. | **AGREED.** Versions bumped (parser 1.5.0, spend rules 1.3.0, rate rules 1.5.0, engine 1.106.0). Detail changes invalidate fingerprint. | **RECONCILED / VERIFIED** |
| **Q15** | Served project calculations and four-anchor final reconciliation absent after repair. | **AGREED.** Live acceptance remains PENDING explicit authorization. No evaluation or DB mutation executed while Claude regenerates. | **RECONCILED / PENDING REGEN** |

---

## 4. Reconciled Four-Project Budget & Variance Summary

### 4.1 The Little Utopia (Mauritius)
- **Declared Gross Budget:** $4,364,393 (Leaf account sum $4,364,395 retains $2 source discrepancy).
- **Producer Planning Estimate:** $1,275,411 at 35% (implied base $3,644,031); net $3,088,982.
- **Engine Persisted Pre-Cap QPE:** $4,063,264 (excludes $301,131 contingency).
- **Codex d0e01e2 Repair:** Publicity Line 7100 ($24,348) reclassified to `general_administration`.
- **Status:** Contingency ($301,131) and offshore travel ($397,279) are grey areas contingent upon local disbursement and flight ticket vendor evidence. Exact independent QPE is `NOT_ESTABLISHED`.

### 4.2 F#K Valentine's Day (Greece)
- **Declared Gross Budget:** $4,517,687 across 34 accounts.
- **Producer Planning Estimate:** $518,804 at 40% (implied Greek base $1,297,010); net $3,998,883.
- **Engine Persisted QPE:** $3,614,149.60 (clamped to 80% statutory budget cap: `min($3,701,238, 0.80 × $4,517,687)`).
- **Statutory Cap Enforced:** Ordinary per-project grant cap of €8,000,000 (~$9.12M USD) verified.
- **Status:** Topsheet lacks itemized Greek expenditure schedule. The $926,855.84 difference between engine incentive and producer estimate is an unexplained planning variance. Exact independent QPE is `NOT_ESTABLISHED`.

### 4.3 Lips Like Sugar (California)
- **Declared Gross Budget:** $11,983,654 across 46 accounts.
- **Producer Planning Estimate:** $1,503,074 at 25% BTL (implied base $6,012,296); net $10,480,580.
- **Historical Reservation (CAL #8-053):** $1,470,365 at 25% Program 3.0 independent rate (implied base $5,881,460); net $10,513,289. Delta between budget and reservation is $32,709.
- **Engine Persisted QPE (Program 4.0 model):** $9,883,654 (excludes $1.7M financing and $400k contingency).
- **Codex d0e01e2 Detail Conservation:**
  - SCRIPT (1100): $1,653 qualifies, $312,500 excluded ($300k writer fee, $12.5k publication).
  - PRODUCERS (1200): Line producer capped at $100,000 conditional BTL spend; $51,198 excluded.
  - TOTAL FRINGES (1900): $255,291 ATL fringes classified as `GREY_AREA_REQUIRES_AUTHORITY`.
- **Status:** Exact independent Program 4.0 QPE is `NOT_ESTABLISHED` pending local payroll and vendor audit.

### 4.4 Bad Hombres (New Mexico)
- **Declared Gross Budget:** $2,482,023 across 34 accounts.
- **Undeployed Contingency:** Line 33 ($94,382) excluded.
- **Unexpended SAG Reserve (Line 1600):** $60,000 excluded from confirmed QPE; classified as `GREY_AREA_REQUIRES_AUTHORITY` / `MISSING_PRODUCTION_FACT`.
- **Confirmed Base QPE (Without Reserve):** **$2,327,641.00**
- **Confirmed Statutory Base Incentive (25%):** **$581,910.25** (Net $1,900,112.75).
- **Engine Persisted Floor Incentive:** $596,910.25 on $2,387,641 (incorporates $60k reserve at 25% = $15,000 delta).
- **Cast Qualification:** Nonresident performing artists ($1,032,202) are conditionally eligible subject to statutory 5% state tax withholding.
- **Status:** Exact independent QPE is `NOT_ESTABLISHED` pending tax withholding proof.

---

## 5. Verification & Negative Controls Audit

Codex's new test harness `test_budget_netting_independent_controls.py` was executed in synthetic, non-DB mode and passed all 25 tests:
- `BudgetNettingControls`: 4/4 passing
- `GreekCapControls`: 2/2 passing
- `QualificationMutationControls`: 16 mutations killed (1/1 passing)
- `GreekPricingControls`: 1/1 passing
- `TextNettingControls`: 2/2 passing
- `SubsetUpliftControls`: 7/7 passing
- `SourceDetailControls`: 5/5 passing
- `SourceFingerprintControls`: 1/1 passing
- `SourceIdentityControls`: 1/1 passing
- `RefreshCategoryControls`: 1/1 passing

Additionally, AG's static and negative control verification suite (`validate_independent_optimizer_audit.py`) was extended to include Negative Controls 25–28:
- **NC 25:** Rejection of California historical 20% rate or $7,351,825 reverse-implied base used as independent Program 4.0 proof.
- **NC 26:** Rejection of Bad Hombres $60,000 SAG reserve included in confirmed QPE.
- **NC 27:** Rejection of whole-QPE application of subset uplifts.
- **NC 28:** Rejection of Greek ordinary grant cap exceeding €8,000,000 without ministerial approval.

All **28/28 negative controls pass** (100% success rate).

---

## 6. Companion Audit Deliverables

The evidence supporting this audit is codified in the following companion artifacts:
1. `FOUR_ANCHOR_CODEX_D0E01E2_DISPOSITION_MATRIX.csv`: Complete 158-account line inventory across the four productions with exact Codex `d0e01e2` classification, confirmed QPE, grey QPE, excluded amounts, statutory citations, and missing fact disclosures.
2. `FOUR_PROJECT_ANCHOR_VARIANCE_BRIDGES.csv`: Fully reconciled arithmetic variance bridges for all four productions, reflecting the retraction of California 20% and Bad Hombres reserve contradictions.
3. `FOUR_PROJECT_BUDGET_CATEGORIZATION_MATRIX.csv`: Updated 158-line categorization matrix with Lips Like Sugar Line 1900 classified as `GREY_AREA_REQUIRES_AUTHORITY`.
4. `CROSS_FORMAT_INCENTIVE_ISOLATION_AUDIT.csv`: Cross-format parity proof confirming incentive isolation across PDF, CSV, and XLSX.
5. `validate_independent_optimizer_audit.py`: Automated 28-control negative test suite.

---

## Conclusion
Codex commit `d0e01e2` represents an admissible and necessary remediation of CineGlobe's parsing, categorization, netting, and economic pricing rules. With the formal retraction of AG's prior California-control and Bad Hombres reserve contradictions, both independent audit platforms (AG and Codex) now share an aligned, evidence-based standard: **source detail conservation, statutory subset precision, and transparent disclosure of unproven facts.**
