# CINEGLOBE — FOUR-ANCHOR QPE ISSUE REGISTER RECONCILIATION & GREECE $926,855.84 DISCREPANCY AUDIT

**Audit Mode:** Strictly Read-Only Independent Statutory Derivation & Reconciliation  
**Audit Branch:** `ag/exhaustive-optimizer-audit`  
**Commit Context:** Integrated with Codex commit `31cc502afb1fda589861b425c352d925866d8134` / Implementation HEAD `ee53fb2`  
**Controlling Documents & Adjudications:**
1. `docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` (Issues Q01–Q15 + Codex 2026-10-10 Addendum)
2. `docs/validation/AG_1EDB718_GREECE_ADJUDICATION.md` (Findings GR-A01 through GR-A04, AN-A01 through AN-A06, PAR-A01)
3. `PROJECT_RULES.md` (Audit Failure Follow-Through Directive, 2026-10-10)
4. `docs/architecture/CAPABILITY_LEDGER.md` (Item 17: Audit Failure Follow-Through)
5. Greek Law 4487/2017 Art. 20, 26 (as amended by Law 4704/2020), Joint Ministerial Decision (KYA) 607434 Annex B, and Law 5105/2024 (*Creative Greece*)

---

## 1. EXECUTIVE SUMMARY & INVESTIGATION MANDATE

In strict accordance with `PROJECT_RULES.md` and `AG_1EDB718_GREECE_ADJUDICATION.md`, this audit executes an exhaustive, account-by-account independent investigation of every registered discrepancy in `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`.

### Core Investigation Findings:
1. **Prioritization of Greece's $926,855.84 Difference (F#K Valentine's Day / DEF-FVD-001):**
   - Earlier AG audit reports erroneously classified the $926,855.84 difference as a "proven engine dollar overstatement," asserting that the producer's line credit estimate of -$518,804.00 (implied QPE of $1,297,010.00) was an authoritative, confirmed legal QPE.
   - **Source Identity Verification (GR-A04):** The embedded producer estimate line in `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` is **Account 8004** (`Greek Estimate Cash Rebate (40%)` -$518,804.00), not line 7903. The gross budget consists of exactly 34 parent lines (Accounts 1100–7905) summing to $4,517,687.00. Account 8004 sits at the foot of the topsheet below gross spend, netting the total to $3,998,883.00.
   - **Codex Adjudication & Audit Correction (GR-A03):** Neither $1,297,010.00 nor $3,614,149.60 is proven territorial spending.
     - **$1,297,010.00 is an estimate-implied QPE:** Reverse-engineered by dividing the producer's topsheet estimate ($518,804) by 40.0%. The 1-page topsheet contains zero itemized Greek vendor, location, or payroll schedules.
     - **$3,614,149.60 is an engine statutory budget ceiling model:** CineGlobe's candidate generator evaluated a hypothetical 100% relocation under `OPEN_DEFAULT_INCLUDE`, throwing foreign cast ($1.25M) and producers ($400k) into Greek spend and clamping the pre-cap spend to the Greek 80.00% statutory budget ceiling ($3,614,149.60 = 80.00% of $4,517,687) under Law 4487/2017 Art. 26(1).
     - **The $926,855.84 difference is an UNRESOLVED_PLANNING_VARIANCE:** It represents an unexplained economic divergence between an unproven statutory ceiling model and an unproven producer planning estimate. Neither model is independently confirmed.
     - **Final Disposition for FVD Greece:** Exact Greek QPE is **NOT_ESTABLISHED / CONDITIONAL PENDING AN ITEMIZED GREEK LOCAL SPEND SCHEDULE**.
2. **Correction of Insurance & Completion Bond Treatment (GR-A01):**
   - In previous audits, Account 7200 Insurance ($50,329) and Account 7905 Completion Bond ($72,573) were marked as categorically statutorily excluded.
   - **Primary Authority Correction:** Both historical Law 4487/2017 Art. 26(2)(a) (PDF p. 6) and current KYA 607434 Annex B.3(i) (PDF p. 50) expressly permit insurance premiums and completion guarantee expenses as eligible production costs subject to a **combined 5.0% cap** of total eligible Greek production costs ($Q_{\text{GR}}$).
   - Blanket exclusion is formally REJECTED. Both accounts are classified as `ELIGIBLE_SUBJECT_TO_5PCT_CAP` (`is_statutorily_excluded=FALSE`). Because the 1-page topsheet lacks an itemized local vendor schedule, territorial incurrence is `MISSING_LOCAL_SPEND_SCHEDULE` and the exact dollar portion remains `NOT ESTABLISHED`.
3. **Correction of Versioned Principal Fee Caps (GR-A02):**
   - Vague "25–30%" fee cap placeholders are retracted and replaced with exact statutory provisions:
     - **Historical Regime (Law 4487/2017 Art. 26(2)(b)):** Enumerated principal fees (director, scriptwriter, and maximum 2 lead actors) are capped at **35.0%** of total eligible Greek production costs ($Q_{\text{GR}}$). Producer fees under cross-border production service contracts are statutorily non-qualifying (Art. 26(2)(c)).
     - **Current Regime (KYA 607434 Annex B.3(ii)):** Enumerated principal fees (directors, scriptwriters, actors) are capped at **30.0%** of total qualifying Greek production costs ($Q_{\text{GR}}$).
4. **Formal Rectification of Prior Audit Contradictions:**
   - **Bad Hombres Base (AN-A05):** The Bad Hombres base ($2,327,641) cannot be labeled "confirmed" while its $1,032,202 cast line requires New Mexico performing artist withholding proof. It is formally reclassified as **CONDITIONAL ON CAST WITHHOLDING PROOF** (conditional model basis only: confirmed base without cast withholding = $1,295,439; subtraction does not certify remaining accounts without local payee proof).
   - **Greece Implied Base (GR-A03, GR-A04):** The FVD Greek base ($1,297,010) is formally retracted as confirmed and reclassified as **ESTIMATE_IMPLIED_ONLY / NOT_ESTABLISHED**.
   - **Little Utopia Local Basis:** LU Ontario QPE ($4,063,264) is formally recognized as a **PLANNING_PROJECTION_CONDITIONAL** on 100% Ontario physical production and residency compliance.
   - **Lips Like Sugar Mixed Roles (AN-A01):** LLS mixed accounts strictly follow authored detail splits under the CFC Program 4.0 Chart (Line 1100: $1,653 QPE / $312,500 excluded; Line 1200: $1,310,198 excluded / $104,000 conditional; Line 1300: $267,384 excluded; Line 1400: $167,700 qualified-category / $617,949 excluded / $77,739 conditional; Line 1900: $255,291 conditional). These authored portions do not establish actual local incurrence without payee records.
5. **Audit Acceptance Status:**
   The Four-Anchor Acceptance Gate remains strictly **OPEN** (`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`).

---

### 2. IN-DEPTH RECONSTRUCTION: GREECE $926,855.84 DISCREPANCY (F#K VALENTINE'S DAY)

### A. The Triad of Numbers & Dollar Variance Bridge

The comparison between the canonical saved run, the producer topsheet, and statutory authorities is established as follows:

| Metric | Amount (USD) | Effective Rate | Underlying Source / Origin | Evidentiary Classification |
| :--- | :---: | :---: | :---: | :--- |
| **Gross Production Budget** | **$4,517,687.00** | — | Movie Magic Budget Topsheet (34 leaf accounts, Accts 1100–7905; Header: "PRELIMINARY BUDGET - GREECE, Location: Greece, Total Shoot 18 Days, SAG (7 roles), Non Union Crew") | `PRIMARY_DOCUMENT_VALUE` |
| **Engine Served Generation** | **$1,445,659.84** | 40.0% | QPE clamped to 80.00% statutory ceiling: $3,614,149.60 ($4,517,687 × 80.00%) in FVD baseline structure (evaluation fingerprint `3759a2edf4b42701abc80a495c492e6f9e191bdf9994836ff8c1ba41ddbac0fd`, engine `canonical-1.106.0`, live refresh 2026-10-10) | `PERSISTED_COMPARISON_ONLY` (Unproven open-default relocation) |
| **Producer Budget Line 8004** | **$518,804.00** | 40.0% | Topsheet Line 8004: `Greek Estimate Cash Rebate (40%)` = -$518,804.00 | `ESTIMATE_IMPLIED_ONLY` (Implied QPE: $1,297,010.00) |
| **Observed Control Difference** | **+$926,855.84** | — | Engine Incentive ($1,445,659.84) minus Producer Estimate ($518,804.00). Base variance: $3,614,149.60 − $1,297,010.00 = $2,317,139.60 ($2,317,139.60 × 40.0% = $926,855.84) | `UNRESOLVED_PLANNING_VARIANCE` |

---

### B. Project-Level Contingency Election Ordering & Current Served Generation Nexus

Tracing the current served evaluation for F#K Valentine's Day (evaluation fingerprint `3759a2edf4b42701abc80a495c492e6f9e191bdf9994836ff8c1ba41ddbac0fd`, engine `canonical-1.106.0`, refreshed 2026-10-10 on acceptance database `frametax2_claude_optimizer_acceptance_20260919` under Alembic migration 0081) establishes the exact mechanical derivation of the engine's candidate baseline and Greece-specific QPE:

1. **Gross Budget Across 34 Leaf Accounts:**
   The sum of all 34 leaf cost accounts (Accounts 1100 through 7905) is exactly **$4,517,687.00**. The topsheet header explicitly reads: `"PRELIMINARY BUDGET - GREECE, Location: Greece, Total Shoot 18 Days, SAG (7 roles), Non Union Crew"`. It is NOT "zero shooting days"; however, the 1-page topsheet genuinely lacks itemized account/payee line schedules, vendor invoices, and tax residency proof.
2. **Actual Project Contingency Election Facts (CBA-009 / Part 19-20 / R39):**
   - Account 7902 `CONTINGENCY : 10%` = **$362,866.00**.
   - Inspection of `project_facts` in the acceptance database confirms that **only The Little Utopia** has an explicit contingency election (`contingency_expected_utilization_pct = 100.0%`), where the provenance is recorded as `source_type = 'recovered_demo_state'` and `source_location = 'Production election, no partial-utilization evidence on file (see little_utopia_real_budget.py LITTLE_UTOPIA_CONTINGENCY_EXPECTED_UTILIZATION_PCT)'`.
   - For F#K Valentine's Day, Bad Hombres, and Lips Like Sugar, `contingency_expected_utilization_pct` is **genuinely unset (`None`)**.
   - Under CBA-009 and `qualification_derivation.py`, when a project's contingency utilization is unset, the engine treats the undeployed reserve as an unspent liability (`MISSING_PRODUCTION_FACT`), yielding $0 qualified QPE.
   - In CineGlobe's candidate generator, this unspent liability reserve is excluded at the project level *prior* to evaluating jurisdiction-specific eligibility rules:
     $$\text{Net Production Spend (Pre-Jurisdiction Baseline)} = \$4,517,687.00 - \$362,866.00 = \mathbf{\$4,154,821.00}$$
3. **The $4,154,821.00 Baseline Across Alternative Candidate Structures:**
   - In the served traces, this $4,154,821.00 net production baseline serves as the unadjusted global spend base prior to jurisdiction exclusions across all alternative international candidate structures.
4. **Jurisdiction-Specific Deduction for Greece (`gr_cash_rebate`):**
   - For Greece, the engine applies statutory exclusions under Law 4487/2017 Art. 20 and KYA 607434 Annex B, specifically excluding Account 7901 `FINANCE FEE : 12.5%` = **$453,583.00**.
   - Pre-Cap Eligible Greek Baseline:
     $$\$4,154,821.00 - \$453,583.00 = \mathbf{\$3,701,238.00}$$
     *(Note: If Completion Bond Account 7905 of $72,573 was also excluded in alternative runs, pre-cap spend was $\$3,628,665.00$. Under either treatment, pre-cap spend exceeds the statutory budget ceiling).*
5. **Clamping to the 80.00% Statutory Budget Ceiling:**
   - Under Greek Law 4487/2017 Art. 26(1), qualifying expenditures cannot exceed 80.00% of the total production budget:
     $$\text{Statutory Budget Ceiling} = 80.00\% \times \$4,517,687.00 = \mathbf{\$3,614,149.60}$$
   - Because $\$3,701,238.00 > \$3,614,149.60$, the engine clamped QPE to **$3,614,149.60**.
   - At the statutory 40.0% cash rebate rate:
     $$\text{Incentive} = 40.0\% \times \$3,614,149.60 = \mathbf{\$1,445,659.84}$$
   - And Net Production Cost (NPC):
     $$\text{NPC} = \text{Gross Budget} - \text{Incentive} = \$4,517,687.00 - \$1,445,659.84 = \mathbf{\$3,072,027.16}$$
   - This matches the current served generation under `canonical-1.106.0` (fingerprint `3759a2edf4b42701abc80a495c492e6f9e191bdf9994836ff8c1ba41ddbac0fd`) byte-for-byte with zero unexplained residuals.
6. **Separation of Embedded Producer Rebate Line 8004:**
   - Account 8004 `Greek Estimate Cash Rebate (40%)` = **-$518,804.00** sits at the foot of the topsheet below gross costs.
   - Gross Production Costs = **$4,517,687.00** (sum of Accounts 1100–7905).
   - Producer Net Budget = $\$4,517,687.00 - \$518,804.00 = \mathbf{\$3,998,883.00}$.
   - Account 8004 is NOT a cost line; separating it from gross spend ensures that producer financing estimates do not contaminate gross cost or corrupt NPC formulas.

---

### C. Deep Investigation: Why the $926,855.84 Gap is a Structural Planning Variance, Not an Engine Defect

Investigating the deep structural cause of the $926,855.84 difference without inventing explanations reveals a fundamental divergence between two unevidenced production planning models:

1. **Retraction of All Unsupported Hypotheses:**
   - Prior audit notes conjectured that F#K Valentine’s Day was planned as an "Albuquerque, New Mexico shoot", that it involved a "2–3 week European exterior split shoot", or that it operated under a "local Greek production services contract under Law 4487/2017 Art. 26(2)(c)".
   - **All such claims are formally and fully retracted.** None of these assertions appear anywhere in `V-BRAT_V8_Greece_041224 TOPSHEET.pdf`. The source document is a single-page topsheet containing only 34 account names and numbers, followed by line 8004. It contains zero location shoot schedules, zero shooting day allocations, zero vendor invoices, zero service contracts, and zero payroll withholding records.
2. **The Factual Basis of the Divergence:**
   - **The Producer's Line Estimate:**
     * The producer included an unitemized financing credit line: Line 8004 `Greek Estimate Cash Rebate (40%)` = -$518,804.00.
     * Dividing $518,804.00 by 0.40 implies an expenditure base of **$1,297,010.00** (28.71% of gross).
     * However, the producer provided **zero schedule or ledger** explaining how $1,297,010.00 was calculated, which accounts were included, or which payees qualified.
   - **CineGlobe's 100% Relocation Model:**
     * Conversely, CineGlobe's candidate generator evaluated a hypothetical **100% full relocation candidate**:
     * Under `OPEN_DEFAULT_INCLUDE`, it threw all gross accounts into Greece, deducting only finance fee ($453,583) and contingency ($362,866).
     * This pre-cap total ($3,701,238.00) hit and was clamped to the statutory 80.00% budget ceiling cap ($3,614,149.60).
3. **The Dollar Variance Bridge:**
   $$\text{Engine Relocation QPE Base} = \$3,614,149.60$$
   $$\text{Producer Estimate-Implied Base} = \$1,297,010.00$$
   $$\text{Base Variance} = \$3,614,149.60 - \$1,297,010.00 = \mathbf{\$2,317,139.60}$$
   $$\text{Rebate Variance} = \$2,317,139.60 \times 0.40 = \mathbf{\$926,855.84}$$
4. **Evidentiary Resolution & Missing Facts:**
   - Earlier AG reports erred by labeling $1,297,010.00 as "confirmed legal QPE" and branding the $926,855.84 gap as a "proven engine overstatement."
   - That claim was invalid: the producer's line credit is an internal pre-production financing estimate without supporting vendor invoices, payroll records, or local service contracts.
   - Conversely, CineGlobe's 100% relocation model is an unevidenced hypothetical that assumed foreign talent would qualify without Greek withholding.
   - The $926,855.84 difference is an **unresolved planning variance** between two unevidenced projections.
   - Because the 1-page topsheet genuinely lacks an itemized Greek schedule (`PAR-A01`), exact legal QPE is **NOT ESTABLISHED — MISSING LOCAL SPEND SCHEDULE**. Neither number is substantiated by primary evidence in the topsheet.

---

### D. Account-by-Account Reconstruction of All 34 Accounts (F#K Valentine's Day)

Under Greek Law 4487/2017 (as amended by Law 4704/2020), Joint Ministerial Decision (KYA) 607434 Annex B, and Law 5105/2024:

- **Categorically Excluded Costs ($816,449.00):**
  - **Acct 7901 Finance Fee (12.5%): $453,583.00** — Financing fees, loan interest, bank charges, and financial arrangement fees are strictly non-eligible under Law 4487/2017 Art. 20 and KYA 607434 Annex B (`is_statutorily_excluded=TRUE`).
  - **Acct 7902 Contingency (10.0%): $362,866.00** — Contingency reserve is an unspent liability; only actual incurred, paid, and audited production expenses qualify under Law 4487/2017 Art. 20 and KYA 607434 Annex B (`is_statutorily_excluded=TRUE`).

- **Eligible Subject to Category-Specific 5.0% Cap ($122,902.00) (GR-A01 Correction):**
  - **Acct 7200 Insurance: $50,329.00** — Insurance premiums are eligible production expenses subject to a **combined 5.0% cap** of total eligible Greek production costs ($Q_{\text{GR}}$) under historical Law 4487/2017 Art. 26(2)(a) (PDF p. 6) and current KYA 607434 Annex B.3(i) (PDF p. 50). Blanket exclusion rejected (`is_statutorily_excluded=FALSE`, `statutory_treatment_greece=ELIGIBLE_SUBJECT_TO_5PCT_CAP`). Exact eligible portion is `NOT ESTABLISHED` due to missing Greek insurer/vendor schedule.
  - **Acct 7905 Completion Bond (2.0%): $72,573.00** — Completion guarantee expenses are eligible production expenses subject to the same **combined 5.0% cap** of total eligible Greek production costs ($Q_{\text{GR}}$) under historical Law 4487/2017 Art. 26(2)(a) and current KYA 607434 Annex B.3(i). Blanket exclusion rejected (`is_statutorily_excluded=FALSE`, `statutory_treatment_greece=ELIGIBLE_SUBJECT_TO_5PCT_CAP`). Exact eligible portion is `NOT ESTABLISHED` due to missing Greek guarantor/vendor schedule.

- **Above-The-Line Accounts Subject to Versioned Fee Caps & Territorial Nexus (GR-A02):**
  - **Acct 1100 Story / Rights / Continuity: $252,650.00** — Scriptwriter compensation is an enumerated principal fee subject to a statutory cap of **35.0%** under historical Law 4487/2017 Art. 26(2)(b) or **30.0%** under current KYA 607434 Annex B.3(ii) of total eligible Greek production costs ($Q_{\text{GR}}$); pre-existing story/underlying rights acquisitions are non-qualifying without Greek author nexus. Unevidenced in US topsheet.
  - **Acct 1200 Producers: $401,831.00** — Under cross-border production service contracts, producer fees are statutorily non-qualifying (Law 4487/2017 Art. 26(2)(c); KYA 607434 Annex B). In co-productions, principal fees are subject to statutory cap of **35.0%** under historical Law 4487/2017 Art. 26(2)(b) for enumerated roles (director, scriptwriter, max 2 lead actors) or **30.0%** under current KYA 607434 Annex B.3(ii) of total eligible Greek production costs ($Q_{\text{GR}}$); US producer compensation lacks Greek territorial performance or tax nexus.
  - **Acct 1300 Director: $75,710.00** — Director compensation is an enumerated principal fee subject to a statutory cap of **35.0%** under historical Law 4487/2017 Art. 26(2)(b) or **30.0%** under current KYA 607434 Annex B.3(ii) of total eligible Greek production costs ($Q_{\text{GR}}$); requires physical performance in Greece and Greek tax compliance/withholding. Unevidenced in US topsheet.
  - **Acct 1400 Cast: $1,246,288.00** — Lead actor compensation is an enumerated principal fee (up to 2 lead actors under historical Law 4487/2017 Art. 26(2)(b) subject to **35.0%** cap; actors under current KYA 607434 Annex B.3(ii) subject to **30.0%** cap of total eligible Greek costs); foreign ATL cast ($1,246,288.00) non-eligible unless performing services physically in Greece under Greek income tax withholding compliance.
  - **Acct 1600 ATL Travel / Living: $174,546.00** — Travel eligible only for direct travel to/from Greece and domestic Greek lodging/per diems; foreign travel strictly excluded (Law 4487/2017 Art. 20; KYA 607434 Annex B).

- **Below-The-Line Physical Production Accounts ($1,090,130.00) (Accts 2000–3900):**
  - Accts 2000 ($168,353), 2100 ($31,595), 2200 ($32,773), 2400 ($46,418), 2500 ($41,199), 2600 ($5,709), 2700 ($67,504), 2800 ($32,830), 2900 ($54,691), 3000 ($62,009), 3100 ($144,422), 3200 ($26,458), 3400 ($178,356), 3600 ($81,123), 3700 ($17,042), 3800 ($3,114), 3900 ($96,534).
  - All categories eligible in principle, but topsheet lacks Greek vendor/location line schedule (`MISSING_LOCAL_SPEND_SCHEDULE`).

- **Post-Production Accounts ($166,646.00) (Accts 4600–5700):**
  - Accts 4600 ($10,000), 5000 ($78,475), 5100 ($10,200), 5200 ($46,471), 5400 ($1,500), 5600 ($15,000), 5700 ($5,000).
  - Categories eligible in principle, but territorial spend is unproven in the 1-page topsheet.

- **Administrative Account ($170,535.00) (Acct 7000):**
  - Acct 7000 Administrative Expenses: $170,535.00. Restricted under Greek rules to audit and accounting directly tied to Greek rebate compliance.

- **Embedded Producer Incentive Line (Account 8004):**
  - **Acct 8004 Greek Estimate Cash Rebate (40%): -$518,804.00** — Credit line at the foot of the topsheet below gross spend; nets gross budget ($4,517,687.00) down to $3,998,883.00.

---

## 3. INVESTIGATION OF EVERY REMAINING ISSUE IN `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`

| ID | Issue Description | Failure Cause | Economic Impact | Governing Evidence | Current Audit Disposition & Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q01** | California 20% / Implied $7.35M base contradiction | Earlier AG audit used Cal Program 3.0 20% rate and back-calculated QPE from $1,470,365 estimate. | False audit baseline; circular validation. | CFC Program 4.0 (35% base, $20M cap); budget 25% note. | **RETRACTED & RECTIFIED:** Historical program not established; Program 4.0 baseline applied. California QPE is `NOT_ESTABLISHED`. |
| **Q02** | California mixed ATL and legal accounts (AN-A01) | Treating mixed writer/producer/director/cast/legal lines as 100% qualified or 100% excluded. | Over- or under-qualifying mixed accounts by up to $312,500. | CFC Jan 2026 Qualified Expenditure Chart. | **AUTHORED SPLITS ENFORCED:** Strict adherence to CFC Program 4.0 chart (Line 1100: $1,653 QPE / $312,500 excluded; Line 1200: $1,310,198 excluded / $104,000 conditional; Line 1300: $267,384 excluded; Line 1400: $167,700 qualified-category / $617,949 excluded / $77,739 conditional; Line 1900: $255,291 conditional). These authored implementation portions do not prove actual local incurrence. Tested in validator. |
| **Q03** | California ATL fringes | Qualifying ATL fringes without linkage to underlying qualifying labor. | Overstating QPE by $255,291 in LLS. | CFC Program 4.0 statutory fringe rules. | **IMPLEMENTED IN AUDIT DESIGN:** LLS Acct 1900 confirmed QPE set to $0.00 pending payee-level audit. Tested in validator. |
| **Q04** | Bad Hombres SAG reserve contradiction | Earlier audit included $60k SAG reserve in confirmed QPE while noting proof missing. | Inflation of confirmed base by $60,000. | SAG-AFTRA deposit agreement / unspent liability doctrine. | **RETRACTED & RECTIFIED:** $60,000 removed from confirmed base ($0 confirmed QPE; classified `MISSING_PRODUCTION_FACT`). |
| **Q05** | Program-wide maximum rates vs. subset uplifts (AN-A02) | Applying uplifts (CA outside-zone +5%, local hire +10%, VFX +5%; NM rural +10%) to 100% of QPE. | Artificial inflation of potential incentive ceiling tiers. | CA Rev. & Tax Code § 17053.98; NM Stat. § 7-2F-1. | **CORRECTED STATUTORY RULES:** CA local hire is +10% (not +5%), outside-zone is +5%, VFX is +5%; NM rural is +10% (not +5%) for counties outside Bernalillo/Santa Fe. Model applies uplifts to eligible subsets only (`EligibleSubsetUpliftRule`). |
| **Q06** | Greek ordinary cap vs. strategic project exception | Conflating EUR 8,000,000 statutory cap with EUR 10,000,000 strategic exception. | Potential $2,000,000 over-cap grant calculation. | Greek Law 4487/2017 Art. 26; JMD strategic regulations. | **IMPLEMENTED IN AUDIT DESIGN:** Ordinary cap clamped to EUR 8,000,000 (`IncentiveValueCapRule`). Tested in synthetic test suite. |
| **Q07** | Budget netting & CSV negative signs | CSV parser stripped negative signs on rebate lines, causing rebates to be added to gross cost. | Net production costs inflated by 2× the rebate amount. | Movie Magic budget CSV / PDF cross-comparison. | **IMPLEMENTED IN PARSER:** Parser 1.5.0 separates producer estimates and net lines; 25 synthetic tests pass. |
| **Q08** | Little Utopia publicity classification | Misclassifying Line 7100 ($24,348) as crew labor instead of general administration. | $24,348 false qualification in Ontario BTL labor credit. | LU topsheet / OFTTC guidelines. | **IMPLEMENTED IN AUDIT DESIGN:** Line 7100 correctly classified as `general_administration` / excluded. Tested in validator. |
| **Q09** | Movie Magic subaccount detail retention (PAR-A01) | Dropping subaccount detail rows during budget ingestion due to regex gap (`CODE DESCRIPTION` without hyphen). | Inability to evaluate mixed accounts without guessing. | Movie Magic XML/JSON parser hierarchy; LU 60pp & BH 43pp PDF detail. | **DETAIL COVERAGE GAP CONFIRMED:** FVD is 1p topsheet and genuinely lacks detail in this source; LU (60pp) and BH (43pp) contain subaccount detail that canonical budget parser dropped. Canonical parser repair is pending; fail-closed mixed treatment preserved. |
| **Q10** | Missing territorial and payroll facts | Treating unevidenced out-of-state budgets as proven local spend. | Misrepresenting hypothetical relocation scenarios as legal claims. | Project file audit / absence of vendor ledgers. | **CONDITIONAL / NOT_ESTABLISHED:** All relocation scenarios explicitly labeled conditional planning projections. |
| **Q11** | Conflating historical control date with current law (AN-A03) | Evaluating historical budgets against current 2026 statutes without temporal gating. | Distorting historical project comparability. | Statutory enactment timelines (e.g. NY 2023, CA 2025). | **SPECIFIED IN AUDIT DESIGN; RUNTIME PERSISTENCE PENDING REGENERATION:** Retracted premature "implemented" status; temporal rules specified in audit contract, live served engine runtime pending regeneration. |
| **Q12** | Circular engine validation | Using engine's own QPE, rates, or uplift selections as independent audit proof. | False audit certification of unverified numbers. | Audit integrity rules in `PROJECT_RULES.md`. | **PROHIBITED & RECTIFIED:** All expectations independently derived from primary legal text and source lines. |
| **Q13** | Double-counting embedded financing or incentives in NPC | Miscalculating NPC by subtracting source estimates from already-netted budget lines. | Net cost discrepancies up to $453k. | Economic formula: $\text{NPC} = \text{Gross} - \text{Credit}$. | **IMPLEMENTED IN AUDIT DESIGN:** Canonical netting contract verified; gross spend and incentives kept separate. |
| **Q14** | Stale persisted database calculations (AN-A04, AN-A06) | Live database contains evaluations from older engines (1.12–1.34) lacking bug fixes. | Database records display unpatched numbers. | PostgreSQL database audit. | **ACKNOWLEDGED:** Persisted database recognized as stale; bounded reuse-only current-generation evidence; production regeneration pending explicit user authorization. |
| **Q15** | Four-anchor final reconciliation absent after repair | Full four-anchor final regeneration run has not occurred on production DB. | Audit cannot award global PASS. | Production database state. | **GATE REMAINS OPEN:** Production regeneration pending explicit user authorization. |

---

## 4. AUDIT CONTRADICTION RECTIFICATION SUMMARY

In accordance with Codex commit `31cc502` and `AG_1EDB718_GREECE_ADJUDICATION.md`, the following contradictory statements in previous audit versions are formally corrected:

```
========================================================================================================================
Contradiction Subject       Previous Flawed AG Statement              Corrected Independent Audit Disposition
------------------------------------------------------------------------------------------------------------------------
Bad Hombres Base Status     "Confirmed QPE: $2,327,641.00"            CONDITIONAL ON CAST WITHHOLDING PROOF: Base of $2,327,641
(AN-A05)                                                              includes $1,032,202 in lead cast compensation requiring NM
                                                                      non-resident withholding proof (conditional model basis only;
                                                                      confirmed base without cast is $1,295,439; subtraction cannot
                                                                      certify other accounts without local payee proof).
------------------------------------------------------------------------------------------------------------------------
Greece FVD Base Status      "Confirmed Greek QPE: $1,297,010.00"      NOT ESTABLISHED: $1,297,010 is estimate-implied from
(GR-A01, GR-A02, GR-A03,                                              Account 8004 (Greek Estimate Cash Rebate (40%) -$518,804.00);
GR-A04)                                                               topsheet lacks Greek expenditure schedule. The $926,855.84
                                                                      difference is an unresolved planning variance between an
                                                                      unevidenced statutory 80% ceiling model ($3,614,149.60)
                                                                      and an unevidenced producer estimate ($1,297,010.00).
------------------------------------------------------------------------------------------------------------------------
Little Utopia Local Basis   "Confirmed Ontario Base: $4,063,264.00"   CONDITIONAL PLANNING PROJECTION: Relies on assumption
                                                                      of 100% Ontario physical production and Canadian residency;
                                                                      itemized local vendor schedule is absent from topsheet.
------------------------------------------------------------------------------------------------------------------------
Lips Like Sugar Mixed Roles Incomplete detail splits on mixed accounts AUTHORED SPLITS ENFORCED: Strict adherence to CFC
(AN-A01)                                                              Program 4.0 chart (Line 1100: $1,653 QPE / $312,500 excluded;
                                                                      Line 1200: $1,310,198 excluded / $104,000 conditional;
                                                                      Line 1300: $267,384 excluded; Line 1400: $167,700 qualified /
                                                                      $617,949 excluded / $77,739 conditional; Line 1900: $255,291
                                                                      conditional). Implementation portions not proof of incurrence.
========================================================================================================================
```

---

## 5. FOUR-ANCHOR ACCEPTANCE GATE DISPOSITION & ADJUDICATION STATUS

**`STATUS: ANCHOR ACCEPTANCE GATE REMAINS OPEN`** (STRICTLY OPEN)  
**`FORMULATION: ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`**

Every discrepancy in `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` and `AG_1EDB718_GREECE_ADJUDICATION.md` has been investigated, categorized, and reconciled against primary authorities and Codex adjudication. Premature closure claims are formally rejected and reopened.

### A. Supported Corrections Established by Primary Authority
1. **Greek Insurance & Bond Treatment (GR-A01):** Blanket exclusion rejected; classified as eligible production costs subject to combined 5.0% statutory cap under Law 4487/2017 Art. 26(2)(a) and KYA 607434 Annex B.3(i).
2. **Greek Versioned Fee Caps (GR-A02):** Delineated historical 35.0% cap (director, writer, max 2 lead actors) from current 30.0% cap under KYA 607434 Annex B.3(ii).
3. **Contingency Election Ground Truth (CBA-009):** In `project_facts`, only Little Utopia has `contingency_expected_utilization_pct = 100.0%`; FVD, BH, and LLS are unset (`None`), correctly excluding Account 7902 ($362,866.00) from QPE as an unspent liability reserve.
4. **Producer Rebate Line Separation (GR-A04):** Account 8004 `Greek Estimate Cash Rebate (40%)` -$518,804.00 separated from gross costs, preventing net distortion in gross spend and NPC formulas.
5. **New York County Enumeration (§ 24(a)(5)):** Dutchess, Orange, and Putnam are explicitly enumerated and eligible under § 24(a)(5) for the additional 10% credit.
6. **New York ATL Treatment (§ 24(b)(1) & § 24(a)(5)):** Under Part D, Chapter 59 of Laws of 2023, eligible ATL (writers, directors, composers, performers) is admitted into qualified production costs subject to the $500,000/person cap, max 2 producers, and aggregate 40% BTL ceiling. The statutory wage exclusion previously quoted was drawn from post-production § 31*2(a)(6).
7. **New York ATL Ceilings & Post Gateways:** Enforced $500k/person individual cap, max 2 producers, 40% BTL ceiling under § 24(b)(1), and disaggregated post gateways (75%/$1M post under § 31*2(a)(2)(i) and 10%/$500k VFX under § 31*2(a)(3)(ii) without geographic split).
8. **Financing Fee Preservation (NY-A01):** LLS financing fees ($1,700,000 across Accts 6500, 6600, 6700) preserved in gross/NPC and excluded from QPE.
9. **Production Sound Disaggregation (NY-A03):** On-set sound across all 4 budgets categorized as physical BTL spend, excluded from Section 31 post credit.

### B. Remaining Blockers
1. **FVD Greece Missing Local Spend Schedule (DEF-FVD-001):** Gross budget ($4,517,687) lacks an itemized Greek schedule, vendor ledger, or payroll breakdown. The $926,855.84 difference ($2,317,139.60 base variance) is an unevidenced structural planning model divergence. Exact legal QPE is genuinely `NOT ESTABLISHED — MISSING LOCAL SPEND SCHEDULE`.
2. **Bad Hombres Non-Resident Cast Withholding (AN-A05):** Lead cast line ($1,032,202) requires proof of New Mexico performing artist withholding compliance under NMSA 1978 § 7-2F-1(B). Base remains conditional.
3. **California Mixed Account Payee Proof (AN-A01):** LLS mixed lines (Line 1100, 1200, 1400, 1900) require payee-level records to verify actual local spend.
4. **Canonical Budget Parser Subaccount Detail Gap (Q09 / PAR-A01):** Parser drops subaccount rows for LU (60pp) and BH (43pp) PDFs due to unhyphenated headers.
5. **Persisted Engine State Pending Regeneration:** Database contains stale evaluations; production regeneration remains held pending explicit authorization.

### C. Reconciled Dollar Impacts
- **Greece FVD Planning Variance:** +$926,855.84 incentive ($2,317,139.60 base variance between 80% ceiling model $3,614,149.60 and producer estimate $1,297,010.00).
- **LLS NY Financing Exclusion:** -$1,700,000.00 from QPE; reduces BTL base by $1.25M and ATL cap by $500k (total QPE reduction: $1,750,000.00; incentive reduction: $525,000.00).
- **BH NY ATL 40% Cap Disallowance:** -$1,155,265.40 from QPE (-$346,579.62 incentive).
- **FVD NY ATL 40% Cap Disallowance:** -$1,327,450.60 from QPE (-$398,235.18 incentive).
- **LLS NY ATL 40% Cap Disallowance:** -$799,903.40 from QPE (-$239,971.02 incentive).

In strict compliance with audit governance rules:
- Strictly zero production code (`backend/app/`, `frontend/`) has been modified.
- Strictly zero project records or database tables have been mutated.
- Strictly zero cold evaluations or project regenerations have been executed.
- The four-anchor acceptance gate remains strictly **OPEN**.
