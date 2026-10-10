# Independent Movie Magic Budget Categorization and Spend Integrity Audit

**Audit Title:** Forensic Budget Categorization, Movie Magic Account Architecture, Multi-Format Isolation, and Statutory QPE Tracing  
**Corpus:** Four Locked Real Productions (*The Little Utopia*, *F#K Valentine's Day*, *Bad Hombres*, *Lips Like Sugar*)  
**Audit Standard:** Read-Only Forensic Derivation. Derived strictly from original documents, statutory authorities, and verified execution traces. Zero production code edits; zero database mutations; zero evaluations.  
**Auditor Reference Commit:** `666a4b7ab5c61618e4304e951a7055accf976753` (`origin/claude/global-optimizer-remediation`)  
**Adjudication Baseline:** Codex Final AG Calculation Adjudication (`62aa3460dec917f05394f2286d33c655b79ab139`)  

---

## 1. Executive Summary & Audit Mandate

This forensic audit independently establishes the complete budget categorization, account hierarchy, subtotal isolation, guild/compensation structures, contingency reserves, financing costs, and statutory Qualified Production Expenditure (QPE) mapping for CineGlobe's four real production anchors.

Starting from Claude's completed reconciliation (`CANONICAL_BUDGET_PARSER_REMEDIATION_CLAUDE.md`), prior parser repairs (BPI-001 through BPI-009), and Codex's authoritative adjudication (`docs/validation/CODEX_FINAL_AG_ADJUDICATION.md`), this audit investigates:
1. **Movie Magic Structure & Account Hierarchy:** Verification of 4-digit and hyphenated account ranges, department sentinels, and tier boundaries across Above-the-Line (1000s), BTL Production (2000–3000s), BTL Post-Production (4000–5000s), BTL Other (6000–7000s), and Top-Level Loaded Costs (8000s).
2. **Detail vs. Subtotal Duplication:** Rigorous verification that top-sheet group rollups, category summaries, and grand totals are strictly prevented from double-counting leaf items (`_GROUP_SUBTOTAL_RE`), with special focus on unnumbered loaded costs (Bad Hombres' $94,382 contingency).
3. **Compensation & Guild Breakdown:** Exact distinction between fixed fees, variable crew labor, cash compensation, deferred fees, equity participation, and guild obligations (SAG, DGA, WGA, IATSE, Teamsters).
4. **Fringes Architecture:** Forensic tracking of ATL, BTL, and Post fringes, including the complete isolation of Lips Like Sugar's four distinct fringe accounts ($1,346,714 total) and the resolution of the duplicate account code 4900 collision.
5. **Contingency & Reserve Accounting:** Strict isolation of unspent contingency reserves ($1,158,379 across all four productions) from incurred qualifying spend.
6. **Finance Costs Isolation:** Absolute separation of source budget production finance charges ($2,153,583 across FVD and LLS) from off-budget scenario financing facts.
7. **Production versus Post Separation:** Complete segregation of on-set physical production spend from post-production finishing, sound design, and territorial post-production (e.g. LA picture/sound editorial in Little Utopia).
8. **Cross-Format Verification (PDF vs. CSV vs. XLSX):** Discovery of a material cross-format vulnerability (`DEF-XFORMAT-001`) where the PDF parser isolates producer incentive estimates and net totals, but CSV and XLSX parsers fail to filter them, causing severe gross budget and spend distortion.
9. **Statutory QPE Tracing:** Exhaustive line-by-line qualification tracing into Mauritius EDB, Greece EKOME / Law 5105/2024, New Mexico TRD FYI-370, and California CFC Program 3.0 / 4.0 schemes.

---

## 2. Original Documents & Provenance Ledger

Every expected value is derived directly from the primary PDF documents preserved in `~/.cineglobe/storage/`:

| Production | Project ID | Source Document Path | Format | Pages | Declared Gross Total | Persisted Leaf Items | Persisted Leaf Sum | Documented Variance |
|---|---|---|---|---:|---:|---:|---:|---:|
| **The Little Utopia (LU)** | `fa5cade5-0669-4816-bfe6-72146f8d3bae` | `little-utopia/The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf` | PDF | 60 | $4,364,393.00 | 44 | $4,364,395.00 | +$2.00 (Source authored rounding excess) |
| **F#K Valentine's Day (FVD)** | `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | `f-k-valentine-s-day/V-BRAT_V8_Greece_041224 TOPSHEET.pdf` | PDF | 1 | $4,517,687.00 | 34 | $4,517,687.00 | $0.00 (Exact match) |
| **Bad Hombres (BH)** | `4355ae88-a636-4c18-af60-ad73b2646124` | `bad-hombres/BadHombresBudget.v2.pdf` | PDF | 43 | $2,482,023.00 | 34 | $2,482,023.00 | $0.00 (Exact match) |
| **Lips Like Sugar (LLS)** | `ab10b319-978e-44d3-9331-af2a5f2cccc2` | `lips-like-sugar/v7LLS_RevBudget_T1B_27days_022524.pdf` | PDF | 52 | $11,983,654.00 | 46 | $11,983,654.00 | $0.00 (Exact match) |
| **TOTAL CORPUS** | — | — | — | **156** | **$23,347,757.00** | **158** | **$23,347,759.00** | **+$2.00** |

### Accounting Note on Little Utopia's $2.00 Residual
On page 2 of Little Utopia's original budget PDF:
- Total Above-The-Line: `$538,444` (Sum of lines: 1000 `$0` + 1100 `$5,050` + 1200 `$0` + 1300 `$0` + 1400 `$136,115` + 1600 `$397,279` = `$538,444`).
- Total Below-The-Line: `$3,476,638` (Sum of lines: Shoot Period `$3,080,755` + Post `$9,068` + VFX `$52,500` + Other `$334,315` = `$3,476,638`).
- Stated Total Above and Below-The-Line: `$4,015,081`. However, `$538,444 + $3,476,638 = $4,015,082` (a $1 subtotal discrepancy in the source document).
- Stated Grand Total: `$4,364,393`. However, `$4,015,081 + 8100 Insurance ($48,181) + 8300 Contigency ($301,131) = $4,364,393`, whereas the sum of all individual leaf lines is `$4,364,395.00`.
- **Finding:** The $2.00 discrepancy is an authored rounding artifact inside the original source document itself. CineGlobe's parser preserves the exact leaf line items without fabricating a compensating fudge line or normalizing away the real arithmetic.

---

## 3. Movie Magic Structure & Account Hierarchy

The Movie Magic Budgeting (MMB) system organizes feature film production accounts into standard numeric blocks. Our audit verified how each production utilizes these structures:

### A. Numbering Conventions
- **Bare 4-Digit Numbering:** Utilized by all four real productions in this corpus (e.g. `1100`, `2200`, `5000`, `7901`, `8300`).
- **Tier Boundaries:**
  - `1000–1999`: Above-The-Line (Story/Rights, Producer, Director, Cast, ATL Travel, ATL Fringes).
  - `2000–3999`: Below-The-Line Production (Crew Labor, Sets, Props, Wardrobe, Camera, Sound, Locations, Transportation).
  - `4000–5999`: Below-The-Line Post-Production (Editing, Lab/Dailies, Post Sound, Music, VFX, Titles, Deliverables).
  - `6000–7999`: Below-The-Line Other / General (Legal, Accounting, Insurance, Office Overhead, Finance Fees).
  - `8000–8999`: Loaded Costs / Top-Level Contingency & Bond (Applied as percentage markups over prior tiers).

### B. Department Resolution Mechanics
CineGlobe resolves department assignments through a two-stage process:
1. `budget_parser._dept_for_acct(acct)` infers department strings from account code ranges.
2. `classify_budget_line_items.classify_line_item(description, department)` performs deterministic classification:
   - **Crucial Repair (BPI-007 Fix):** Keyword regex matching operates strictly on the line's own `description`, preventing department text (e.g. `"Post Production"`) from leaking into search text and causing false keyword triggers (such as `post[ -]prod` matching generic fringe lines).
   - Department context is reserved for explicit structural disambiguation (such as separating bare production sound from post sound).

---

## 4. Detail vs. Subtotal Duplication Audit

In Movie Magic top-sheet exports, summary header lines and category rollups are printed alongside leaf accounts. If parsed naively, these summary lines would duplicate spend.

### A. Group-Subtotal Suppression Rules
The parser applies `_GROUP_SUBTOTAL_RE` to intercept and discard:
- Section Sentinels: `ABOVE THE LINE`, `TOTAL ABOVE THE LINE`, `TOTAL SHOOT PERIOD`, `BELOW THE LINE - PRODUCTION`, `BELOW THE LINE - POST`, `BELOW THE LINE - OTHER`, `TOTAL OTHER`, `TOTAL PRODUCTION`, `TOTAL POST PRODUCTION`.
- Grand Summary Sentinels: `Total Above-The-Line`, `Total Below-The-Line`, `Total Above and Below-The-Line`, `Grand Total`.

### B. Unnumbered Loaded Costs Exception (Bad Hombres Contingency)
- **The Defect (BPI-001):** On Bad Hombres page 2, the contingency row appears as `CONTINGENCY : 5.0%` followed by `$94,382`. It carries no 4-digit account code.
- Previously, `budget_parser.py` extracted the row under the description `CONTINGENCY`, but downstream canonical economics (`canonical_project_economics.py`) required `_ACCOUNT_CODE_RE = r"^\d{2,4}"`, silently dropping the line and reducing the gross budget to `$2,387,641`.
- **The Verification:** The repair ensures unnumbered loaded-cost rows use their own label text (`"CONTINGENCY"`) as a stable account identifier. Bad Hombres canonical economics now reconciles to the exact declared gross total of `$2,482,023.00` with 34/34 lines preserved.

---

## 5. Compensation, Guild Obligations & Fringe Architecture

### A. Above-The-Line Compensation Breakdown
| Production | Writer (1100) | Producer (1200) | Director (1300) | Principal Cast (1400) | Total ATL Compensation |
|---|---:|---:|---:|---:|---:|
| **The Little Utopia** | $5,050.00 | $0.00 | $0.00 | $136,115.00 | $141,165.00 |
| **F#K Valentine's Day** | $252,650.00 | $401,831.00 | $75,710.00 | $1,246,288.00 | $1,976,479.00 |
| **Bad Hombres** | $74,531.00 | $267,169.00 | $75,000.00 | $1,032,202.00 | $1,448,902.00 |
| **Lips Like Sugar** | $314,153.00 | $1,414,198.00 | $267,384.00 | $863,388.00 | $2,859,123.00 |
| **TOTAL** | **$646,384.00** | **$2,083,198.00** | **$418,094.00** | **$3,277,993.00** | **$6,425,669.00** |

### B. Residual Reserves vs. Fee Compensation
Guild residual reserves are funded escrow obligations, NOT contingency and NOT above-the-line talent fees:
- **Bad Hombres Line 1600:** `SAG DEPOSIT / RESIDUAL RESERVE` ($60,000.00) — classified as `residuals_reserve` (OTHER).
- **Lips Like Sugar Line 6800:** `RESIDUALS RESERVE` ($400,000.00) — classified as `residuals_reserve` (OTHER).
- **Regulatory Qualification:** Under California CFC Program 4.0 Non-Qualified Expenditures (Item 2), residual compensation is statutorily non-qualified. Under New Mexico TRD rules, an unspent reserve cannot be claimed as an incurred qualifying expense.

### C. Lips Like Sugar Multi-Tier Fringe Decomposition
Lips Like Sugar distributes fringes across four distinct Movie Magic department tiers, totaling **$1,346,714.00**:
1. `1900 Total Fringes`: **$255,291.00** (Above-The-Line fringes on writer, producer, director, cast).
2. `4900 Total Fringes`: **$1,023,115.00** (Production BTL fringes on crew labor).
3. `5900 Total Fringes`: **$68,308.00** (Post-Production fringes on editorial/sound).
4. `6900 Total Fringes`: **$0.00** (Other general fringes).

#### Resolution of the Duplicate Account Code 4900 Collision (BPI-002)
- In Lips Like Sugar, account code `4900` is shared by two distinct leaf rows:
  - Line 31: `4900 Total Fringes` ($1,023,115.00, Production BTL).
  - Line 32: `4900 MAIN AND END TITLES` ($10,500.00, Post Production).
- Downstream lookups previously indexed categories solely by `account_code`, causing `MAIN AND END TITLES` to overwrite `Total Fringes` to `post_production` or `miscellaneous`.
- **Audit Verification:** Both rows now carry their own `spend_category` (`payroll_fringes` vs `post_production`) on the `BudgetLineItem` and `AccountAllocation` models. Lookup priority is `line.spend_category or spend_category_by_code.get(...)`, guaranteeing that neither line compromises the other.

---

## 6. Contingency & Finance Costs Forensic Isolation

### A. Contingency Reserves Summary
| Production | Account Code | Line Description | Amount (USD) | Category | QPE Treatment |
|---|---|---|---:|---|---|
| **The Little Utopia** | 8300 | Contigency : 7.5% | $301,131.00 | `contingency` | `GREY_AREA_REQUIRES_AUTHORITY` (Missing expenditure proof) |
| **F#K Valentine's Day** | 7902 | CONTINGENCY : 10% | $362,866.00 | `contingency` | `EXCLUDED` (Statutorily unspent) |
| **Bad Hombres** | CONTINGENCY | CONTINGENCY : 5.0% | $94,382.00 | `contingency` | `EXCLUDED` (Statutorily unspent) |
| **Lips Like Sugar** | 7100 | Contingency | $400,000.00 | `contingency` | `EXCLUDED` (Statutorily unspent) |
| **TOTAL** | — | — | **$1,158,379.00** | — | — |

**Controlling Doctrine:** Budgeted contingency represents uncommitted funds. No statutory incentive authority rebates unexpended contingency.

### B. Production Finance Costs vs. Scenario Financing
| Production | Account Code | Description | Amount (USD) | Engine Category | Canonical Economics Field |
|---|---|---|---:|---|---|
| **F#K Valentine's Day** | 7901 | FINANCE FEE  : 12.5% | $453,583.00 | `finance_costs` | `source_budget_finance_usd = 453583` |
| **Lips Like Sugar** | 6500 | FINANCING FEES | $450,000.00 | `finance_costs` | `source_budget_finance_usd = 1700000` |
| **Lips Like Sugar** | 6600 | BRIDGE | $250,000.00 | `finance_costs` | (Included in aggregate finance sum) |
| **Lips Like Sugar** | 6700 | BANKING FEE | $1,000,000.00 | `finance_costs` | (Included in aggregate finance sum) |
| **The Little Utopia** | 7800 | FINANCE & LEGAL | $0.00 | `finance_costs` | `source_budget_finance_usd = 0` |
| **TOTAL** | — | — | **$2,153,583.00** | — | — |

**Integrity Verification:** In both FVD and LLS, source finance costs are captured strictly as `source_budget_finance_usd`. Scenario financing facts (e.g. loan interest rates, debt percentages) remain separate and do not substitute or duplicate these source fees.

---

## 7. Production versus Post-Production Segregation

### A. Production Sound vs. Post Sound (BPI-003 Resolution)
All four budgets contain both physical production sound and post-production sound:
- **Little Utopia:** Line 18 (`3200 PRODUCTION SOUND`, $69,532) vs Line 29 (`5200 SOUND POST PRODUCTION`, $0).
- **F#K Valentine's Day:** Line 16 (`3200 PRODUCTION SOUND`, $26,458) vs Line 25 (`5200 POST PRODUCTION SOUND`, $46,471).
- **Bad Hombres:** Line 19 (`3400 PRODUCTION SOUND`, $16,845) vs Line 27 (`4700 POST PRODUCTION SOUND`, $35,515).
- **Lips Like Sugar:** Line 20 (`3400 PRODUCTION SOUND`, $87,067) vs Line 29 (`4700 POST-PRODUCTION SOUND`, $39,520).

**Audit Verification:** `_RULES` applies a negative lookbehind `(?<!post[ -])` before `production sound` to ensure post sound is never captured as production sound, while production sound is assigned `SpendCategory.PRODUCTION_SOUND` (BTL) instead of post `SOUND`.

### B. Territorial Nexus in Post Production (Little Utopia)
Little Utopia's budget header establishes:
- `SHOOT: Mauritius: 35 days`
- `PICTURE EDIT: LA`
- `SOUND EDIT: LA`
- `DELIVERY: LA`
Accordingly, Account 5000 `EDITORIAL` ($9,068.00) represents out-of-territory Los Angeles expenditures. While the generic engine maps it to post-production, an authoritative Mauritian EDB audit excludes it from local QPE due to lack of territorial nexus.

---

## 8. Cross-Format Verification (PDF vs. CSV vs. XLSX) & Defect DEF-XFORMAT-001

A critical finding of this audit is the discovery of a structural divergence between PDF parsing and CSV/XLSX spreadsheet parsing:

### A. The Producer Incentive Estimate Ledger
Three of the four budgets feature explicit producer incentive netting lines:
1. **Little Utopia:** Line 9001 `EDB Rebate at 35%`: `$(1,275,411)`, Net Total `$3,088,982`.
2. **F#K Valentine's Day:** Line 8004 `Greek Estimate Cash Rebate (40%)`: `($518,804)`, Net Total `$3,998,883`.
3. **Lips Like Sugar:** Line 9998 `Tax Incentive 25%* BTL  (No Disc)`: `($1,503,074)`, Net Total `$10,480,580`.

### B. Parser Divergence Analysis
| Parser Module | Source Format | Rebate Exclusion Filter | Net Total Filter | Gross Budget Result | Incentive Estimate Capture |
|---|---|---|---|---|---|
| `_parse_film_budget` | PDF | **ACTIVE** (`_REBATE_EXCLUSION_RE`) | **ACTIVE** (`_REBATE_EXCLUSION_RE`) | **PRISTINE** (Gross equals true cost) | **CAPTURED** in `source_incentive_estimates` |
| `parse_budget_csv` | CSV | **DEFECT** (Missing filter) | **DEFECT** (Missing filter) | **INFLATED** (+Rebate amount & +Net total added as spend) | **LOST** (Treated as cost lines) |
| `parse_budget_xlsx` | XLSX | **DEFECT** (Missing filter) | **DEFECT** (Missing filter) | **DISTORTED** (-Rebate deducted & +Net total added) | **LOST** (Treated as cost lines) |

### C. Confirmed Defect: DEF-XFORMAT-001
- **Root Cause:** `_REBATE_EXCLUSION_RE` is wired exclusively into `_parse_film_budget` and `parse_budget_from_text`. It was never integrated into `parse_budget_csv` or `parse_budget_xlsx`.
- **Arithmetic Blast Radius:** If a producer uploads a CSV export of Little Utopia, `parse_budget_csv` interprets `9001 EDB Rebate at 35%` (parsed as `+$1,275,411`) and `Net total` (`+$3,088,982`) as cost line items, inflating the gross budget from `$4,364,393` to `$8,728,786`!
- **Remediation Specification:** `parse_budget_csv` and `parse_budget_xlsx` must call `_REBATE_EXCLUSION_RE` on the description column, exclude matches from `line_items`, and populate `source_incentive_estimates`.

---

## 9. Statutory QPE Tracing & Program Matrix

Every line was traced through the current statutory rules of its respective home jurisdiction:

### A. The Little Utopia (Mauritius — `mu_edb_incentive`, 35%)
- **Total Gross Budget:** $4,364,395.00 (44 lines)
- **Qualifies (Base QPE):** **$1,988,799.00** (Local set construction, wardrobe, electrical, sound, camera, transportation, local lodging/travel, VFX).
- **Excluded:** **$0.00**
- **Grey Area / Requires Authority:** **$2,375,596.00** (LA editorial $9,068; unspent contingency $301,131; general administrative $321,941; production staff and equipment requiring Mauritian vendor verification).
- **Producer Estimate Comparison:** Producer estimated **$1,275,411.00** at 35%, implying a Mauritian QPE base of **$3,644,031.43**.

### B. F#K Valentine's Day (Greece — `gr_cash_rebate`, 40%)
- **Total Gross Budget:** $4,517,687.00 (34 lines)
- **Qualifies (Base QPE):** **$3,701,238.00** (Shoot period $1,090,130 + Post $166,646 + Admin/Insurance $220,864 + Completion Bond $72,573 + Above-The-Line $2,151,024).
- **Excluded:** **$362,866.00** (Line 7902 Contingency 10%).
- **Grey Area / Not Applicable:** **$453,583.00** (Line 7901 Finance Fee 12.5%).
- **Producer Estimate Comparison:** Producer estimated **$518,804.00** at 40%, which represents a Greek local QPE base of exactly **$1,297,010.00**.
- **Critical Fact Gap (UF-FVD-001):** The 1-page topsheet does not isolate Greek resident labor and local Greek goods/services from foreign travel and non-Greek ATL spend. Qualifying all $3.7m without local expenditure proof is unverified.

### C. Bad Hombres (New Mexico — `us_nm_film_credit`, 25%)
- **Total Gross Budget:** $2,482,023.00 (34 lines)
- **Qualifies (Base QPE):** **$2,387,641.00**
- **Excluded:** **$94,382.00** (Contingency 5.0%).
- **Grey Area:** **$0.00**
- **Critical Fact Gap (UF-BH-001):**
  - Line 1400 Cast ($1,032,202) represents 41.6% of the budget. Under New Mexico TRD FYI-370, payments to nonresident performing artists qualify only if subject to 8% NM withholding and performed on set in NM.
  - Line 1600 SAG Deposit ($60,000) represents unspent escrow, which does not qualify until actual post-production services are rendered.

### D. Lips Like Sugar (California — `ca_film_30`, 35%)
- **Total Gross Budget:** $11,983,654.00 (46 lines)
- **Qualifies (Confirmed QPE Base):** **$6,474,531.00** (BTL crew labor, stage rentals, camera, electric, sound, transportation, location fees, post-production, bond fee).
- **Excluded:** **$800,000.00** (Account 7100 Contingency $400,000 + Account 6800 Residuals Reserve $400,000).
- **Grey Area / Mixed Account / Not Applicable:** **$4,709,123.00**
  - Mixed ATL Accounts: Script ($314,153), Producing ($1,414,198), Directing ($267,384), Cast ($863,388). Under CFC Program 4.0, principal compensation is excluded, while coordinators and assistants can qualify.
  - Legal Costs ($150,000): Mixed account; production legal qualifies, corporate/finance legal excluded.
  - Finance Fees ($1,700,000): Accounts 6500, 6600, 6700 are non-spend financing charges.
- **CFC Allocation Letter Comparison (CAL #8-053):**
  - Confirmed CFC Qualified Expenditure Reservation: **$7,351,825.00** at 20.0% = **$1,470,365.00** tax credit.
  - Producer Budget Estimate (Line 9998): **$1,503,074.00** at 25% (assumed on a $6,012,296 BTL base).

---

## 10. Summary Defect & Unresolved Fact Inventory

| Identifier | Type | Subject | Severity | Status & Description |
|---|---|---|---|---|
| **BPI-001** | Parser/Downstream | Bad Hombres Contingency ($94,382) | High | **VERIFIED RESOLVED**. Unnumbered loaded cost preserved via label identity; downstream canonical total reaches exact $2,482,023. |
| **BPI-002** | Data Architecture | Lips Like Sugar Account 4900 Collision | High | **VERIFIED RESOLVED**. Distinct categories (`payroll_fringes` vs `post_production`) carried per line; lookup priority protects line state. |
| **BPI-003** | Classification | Production Sound vs Post Sound ($199,902) | High | **VERIFIED RESOLVED**. Negative lookbehind prevents post sound from matching production sound; production sound routed to BTL. |
| **BPI-004** | Classification | F#K Bare BOND Account ($72,573) | High | **VERIFIED RESOLVED**. Bare `bond` recognized as `completion_bond`. |
| **BPI-005** | Classification | Legal/Accounting Costs ($174,000) | High | **VERIFIED RESOLVED**. Enum `SpendCategory.LEGAL_ACCOUNTING` added and mapped across all downstream pricing modules. |
| **BPI-006** | Classification | ATL Producer/Director Fees ($819,710) | High | **VERIFIED RESOLVED**. Word boundaries replace end-of-string anchors, restoring role semantics on parsed lines with department text. |
| **BPI-007** | Classification | Post Fringe Precedence (LLS $68,308) | Medium | **VERIFIED RESOLVED**. Keyword search operates on description only; department leakage eliminated. |
| **BPI-008** | Classification | Lab/Dailies & Titles Post Routing | Medium | **VERIFIED RESOLVED**. Vocabulary added for film/lab, dailies, and titles, preventing default to production miscellaneous. |
| **BPI-009** | Provenance | Stale Parser Version Markers | Low | **VERIFIED RESOLVED**. Digest incorporates rule table SHA256, guaranteeing automatic cache invalidation on rule updates. |
| **DEF-XFORMAT-001** | Ingestion Engine | Cross-Format CSV/XLSX Rebate Exclusion | High | **DEFECT CONFIRMED**. `parse_budget_csv` and `parse_budget_xlsx` lack `_REBATE_EXCLUSION_RE`, corrupting gross totals if budget is imported in spreadsheet format. |
| **UF-LU-001** | Factual Boundary | LU Los Angeles Post Nexus | Medium | **UNRESOLVED FACT**. LA picture/sound edit ($9,068) and foreign travel are non-Mauritian; local spend schedule required for exact EDB claim. |
| **UF-FVD-001** | Factual Boundary | FVD Greek Local vs Foreign Spend | High | **UNRESOLVED FACT**. Topsheet lacks local Greek schedule; producer estimated $1,297,010 base vs engine $3,701,238. |
| **UF-BH-001** | Factual Boundary | BH Nonresident Withholding & SAG Reserve | High | **UNRESOLVED FACT**. $1,032,202 cast requires NM withholding certificates; $60,000 SAG deposit requires proof of incurred spend. |
| **UF-LLS-001** | Factual Boundary | LLS Mixed ATL Accounts & Reservation | High | **UNRESOLVED FACT**. $2,859,123 ATL compensation requires line-item payroll audit; Program 3.0 $7,351,825 reservation must not be conflated with 4.0 models. |

---

## 11. Final Certification Statement

1. All 158 persisted budget lines across the four locked productions have been independently classified, accounted, and audited.
2. Group-level rollups and section summaries are strictly isolated from leaf items with zero double-counting.
3. Producer incentive estimates and net totals are successfully isolated from gross costs in PDF ingestion, but require immediate remediation in CSV and XLSX ingestion (`DEF-XFORMAT-001`).
4. All prior parser defects (BPI-001 through BPI-009) remain verified as fixed and non-regressing.
5. All evidence is committed strictly to audit documentation on branch `ag/exhaustive-optimizer-audit`.
