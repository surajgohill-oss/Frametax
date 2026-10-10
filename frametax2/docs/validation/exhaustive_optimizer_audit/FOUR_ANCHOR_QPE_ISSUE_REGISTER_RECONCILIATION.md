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

## 2. IN-DEPTH RECONSTRUCTION: GREECE $926,855.84 DISCREPANCY (F#K VALENTINE'S DAY)

### A. The Triad of Numbers & Dollar Variance Bridge

The comparison between the canonical saved run, the producer topsheet, and statutory authorities is established as follows:

| Metric | Amount (USD) | Effective Rate | Underlying Source / Origin | Evidentiary Classification |
| :--- | :---: | :---: | :--- | :--- |
| **Gross Production Budget** | **$4,517,687.00** | — | Movie Magic Budget Topsheet (34 leaf accounts, Accts 1100–7905) | `PRIMARY_DOCUMENT_VALUE` |
| **Engine Persisted Baseline** | **$1,445,659.84** | 40.0% | QPE clamped to 80.00% statutory ceiling: $3,614,149.60 ($4,517,687 × 80.00%) in Structure `e8649797-b143-40d7-978b-35bf7ca07cc1` (fingerprint `bb48c6e76623545f7718ebff65cfd14bfd8ff47ea4c6cbd07ec6a5b7473ae79f`) | `PERSISTED_COMPARISON_ONLY` (Unproven open-default relocation) |
| **Producer Budget Line 8004** | **$518,804.00** | 40.0% | Topsheet Line 8004: `Greek Estimate Cash Rebate (40%)` = -$518,804.00 | `ESTIMATE_IMPLIED_ONLY` (Implied QPE: $1,297,010.00) |
| **Observed Control Difference** | **+$926,855.84** | — | Engine Incentive ($1,445,659.84) minus Producer Estimate ($518,804.00). Base variance: $3,614,149.60 − $1,297,010.00 = $2,317,139.60 ($2,317,139.60 × 40.0% = $926,855.84) | `UNRESOLVED_PLANNING_VARIANCE` |

---

### B. Root-Cause Reconciliation: Why Prior Claims of a Confirmed Engine Defect Were Invalid

1. **The Fallacy of Estimate-Implied QPE (GR-A04):**
   Earlier AG audit reports treated the producer's line credit estimate ($518,804.00, erroneously labeled 7903 instead of **Account 8004**) as an inviolable oracle of actual qualifying spend, dividing by 0.40 to declare $1,297,010.00 as "confirmed Greek QPE." That was circular and invalid:
   - A producer’s credit line is an internal pre-production financing estimate, not an audited cost schedule.
   - The F#K Valentine’s Day budget is an American production topsheet (predominantly New Mexico). It contains no itemized breakdown of services performed in Greece, Greek vendor invoices, Greek shoot dates, or Greek crew payroll.
2. **The Nature of CineGlobe's Engine Calculation:**
   CineGlobe's engine evaluated `gr_cash_rebate` under `OPEN_DEFAULT_INCLUDE`:
   - It excluded finance fees ($453,583) and contingency ($362,866).
   - It treated all remaining spend as qualifying Greek expenditures, including US lead actors ($1,246,288) and US producers ($401,831).
   - It then clamped the qualifying spend to the 80.00% statutory budget cap ($3,614,149.60) under Greek Law 4487/2017 Art. 26(1).
   - Clamping to an 80% statutory ceiling does not make that ceiling an itemized territorial schedule.
3. **Retraction of Speculative Physical Spend Hypothesis (GR-A03):**
   The prior AG report attempted to correlate the producer's implied $1,297,010 base by summing BTL physical ($1,090,130) + post ($166,646) = $1,256,776, leaving an unexplained difference of $40,234 and hypothesizing administrative or director fees.
   - Per `AG_1EDB718_GREECE_ADJUDICATION.md` Finding `GR-A03`, this was an **UNPROVEN HYPOTHESIS**, not a root-cause reconciliation.
   - The source document is a 1-page topsheet that genuinely lacks detail or an attached service schedule (`PAR-A01`).
   - Neither the engine's 80% ceiling model ($3,614,149.60 QPE / $1,445,659.84 rebate) nor the producer's planning estimate ($1,297,010.00 base / $518,804.00 rebate) is independently confirmed.
   - The $926,855.84 difference is an **unresolved planning variance** between two unevidenced projections.

---

### C. Account-by-Account Reconstruction of All 34 Accounts (F#K Valentine's Day)

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

## 5. FOUR-ANCHOR ACCEPTANCE GATE DISPOSITION

**`STATUS: ANCHOR ACCEPTANCE GATE REMAINS OPEN`**  
**`FORMULATION: ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`**

Every discrepancy in `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` and `AG_1EDB718_GREECE_ADJUDICATION.md` has been investigated, categorized, and reconciled against primary authorities and Codex adjudication. Unsupported numbers remain unresolved, contradictory claims are corrected, and production regeneration remains held pending explicit authorization.
