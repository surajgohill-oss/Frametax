# CINEGLOBE — FOUR-ANCHOR QPE ISSUE REGISTER RECONCILIATION & GREECE $926,855.84 DISCREPANCY AUDIT

**Audit Mode:** Strictly Read-Only Independent Statutory Derivation & Reconciliation  
**Audit Branch:** `ag/exhaustive-optimizer-audit`  
**Commit Context:** Integrated with Codex commit `31cc502afb1fda589861b425c352d925866d8134` / Implementation HEAD `ee53fb2`  
**Controlling Documents:**
1. `docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` (Issues Q01–Q15 + Codex 2026-10-10 Addendum)
2. `PROJECT_RULES.md` (Audit Failure Follow-Through Directive, 2026-10-10)
3. `docs/architecture/CAPABILITY_LEDGER.md` (Item 17: Audit Failure Follow-Through)
4. Greek Law 4487/2017 Art. 20, 26 (as amended by Law 4704/2020) and Law 5105/2024 (*Creative Greece*)

---

## 1. EXECUTIVE SUMMARY & INVESTIGATION MANDATE

In strict accordance with the updated `PROJECT_RULES.md` and the user directive, this audit executes an exhaustive, account-by-account investigation of every registered discrepancy in `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`.

### Core Investigation Findings:
1. **Prioritization of Greece's $926,855.84 Difference (F#K Valentine's Day / DEF-FVD-001):**
   - Earlier AG audit reports erroneously classified the $926,855.84 difference as a "proven engine dollar overstatement," asserting that the producer's line 7903 tax credit estimate of $518,804.00 (implied QPE of $1,297,010.00) was an authoritative, confirmed legal QPE.
   - **Codex Adjudication & Audit Correction:** Neither $1,297,010.00 nor $3,614,149.60 is proven territorial spending.
     - **$1,297,010.00 is an estimate-implied QPE:** It was reverse-engineered by dividing the producer's topsheet estimate ($518,804) by 40%. The Movie Magic topsheet contains zero itemized Greek vendor, location, or payroll schedules.
     - **$3,614,149.60 is an engine statutory budget cap:** CineGlobe's candidate generator evaluated a hypothetical 100% relocation under `OPEN_DEFAULT_INCLUDE`, throwing foreign cast ($1.25M) and producers ($400k) into Greek spend and clamping the pre-cap spend to the Greek 80% statutory budget ceiling ($3,614,149.60 = 80% of $4,517,687).
     - **The $926,855.84 difference is an UNRESOLVED PLANNING VARIANCE:** It represents an unexplained economic divergence between an unproven statutory ceiling model and an unproven producer planning estimate.
     - **Final Disposition for FVD Greece:** Exact Greek QPE is **NOT_ESTABLISHED / CONDITIONAL PENDING AN ITEMIZED GREEK LOCAL SPEND SCHEDULE**.
2. **Formal Rectification of Prior Audit Contradictions:**
   - **Bad Hombres Base:** The Bad Hombres base ($2,327,641) cannot be labeled "confirmed" while its $1,032,202 cast line requires New Mexico performing artist withholding proof. It is formally reclassified as **CONDITIONAL ON CAST WITHHOLDING PROOF** (confirmed base without cast withholding = $1,295,439).
   - **Greece Implied Base:** The FVD Greek base ($1,297,010) is formally retracted as confirmed and reclassified as **ESTIMATE_IMPLIED_ONLY / NOT_ESTABLISHED**.
   - **Little Utopia Local Basis:** LU Ontario QPE ($4,063,264) is formally recognized as a **PLANNING_PROJECTION_CONDITIONAL** on 100% Ontario physical production and residency compliance.
   - **Lips Like Sugar Mixed Roles:** LLS mixed-role lines strictly adhere to the authored detail splits of the California Film Commission (CFC) Program 4.0 Qualified Expenditure Chart (January 2026).
3. **Audit Acceptance Status:**
   The Four-Anchor Acceptance Gate remains strictly **OPEN** (`ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`).

---

## 2. IN-DEPTH RECONSTRUCTION: GREECE $926,855.84 DISCREPANCY (F#K VALENTINE'S DAY)

### A. The Triad of Numbers

| Metric | Amount (USD) | Effective Rate | Underlying Source / Origin | Evidentiary Classification |
| :--- | :---: | :---: | :--- | :--- |
| **Gross Production Budget** | **$4,517,687.00** | — | Movie Magic Budget Topsheet (34 leaf accounts) | `PRIMARY_DOCUMENT_VALUE` |
| **Engine Persisted Baseline** | **$1,445,659.84** | 40.0% | QPE clamped to 80% statutory ceiling: $3,614,149.60 ($4,517,687 × 80.00%) | `PERSISTED_COMPARISON_ONLY` (Unproven open-default relocation) |
| **Producer Budget Line 7903** | **$518,804.00** | 40.0% | Line 7903: "TAX CREDIT ESTIMATE - GREECE (40%) = ($518,804)" | `ESTIMATE_IMPLIED_ONLY` (Implied QPE: $1,297,010.00) |
| **Observed Control Difference** | **+$926,855.84** | — | Engine Incentive ($1,445,659.84) minus Producer Estimate ($518,804.00) | `UNRESOLVED_PLANNING_VARIANCE` |

---

### B. Why Prior AG Claims of a "Confirmed $926,855.84 Engine Defect" Were Flawed

1. **The Fallacy of Estimate-Implied QPE:**
   Earlier AG audit reports treated the producer's line 7903 credit estimate ($518,804.00) as an inviolable oracle of actual qualifying spend, dividing by 0.40 to declare $1,297,010.00 as "the confirmed Greek QPE." That was circular and methodologically invalid:
   - A producer’s credit line is an internal financing estimate, not an audited cost schedule.
   - The F#K Valentine’s Day budget is an American production topsheet (predominantly New Mexico). It does not contain an itemized breakdown of services performed in Greece, Greek vendor invoices, Greek shoot dates, or Greek crew payroll.
2. **The Nature of CineGlobe's Engine Calculation:**
   CineGlobe's engine evaluated `gr_cash_rebate` under `OPEN_DEFAULT_INCLUDE`:
   - It excluded finance fees ($453,583), contingency ($362,866), completion bond ($72,573), and insurance ($50,329).
   - It treated all remaining spend ($3,578,336 pre-insurance or $3,628,665) as qualifying Greek expenditures, including US lead actors ($1,246,288) and US producers ($401,831).
   - It then clamped the qualifying spend to the 80% statutory budget cap ($3,614,149.60) under Greek Law 4487/2017 Art. 26 para. 2.
   - Clamping to an 80% statutory ceiling does not make that ceiling an itemized territorial schedule.
3. **The Reality of the $926,855.84 Gap:**
   - **Producer's Planning Model:** The producer assumed a service shoot where only physical below-the-line production and post-production (~$1.25M to $1.3M) would be spent in Greece, leaving ATL talent paid in the US.
   - **Engine's Planning Model:** The engine assumed a total relocation where 100% of the cast, crew, and production relocated to Greece up to the 80% statutory maximum.
   - Neither model is supported by an itemized Greek expenditure ledger. Thus, the $926,855.84 difference is an **unresolved planning variance**, NOT a proven implementation overstatement of a known golden schedule.

---

### C. Account-by-Account Reconstruction of All 34 Accounts (F#K Valentine's Day)

Under Greek Law 4487/2017 (as amended by Law 4704/2020) and Law 5105/2024 (*Creative Greece*):
- **Statutorily Excluded Non-Eligible Costs ($939,351.00):**
  - Acct 7200 Insurance: $50,329.00 (General production insurance non-eligible under Greek Cash Rebate)
  - Acct 7901 Finance Fee (12.5%): $453,583.00 (Lender fees/financing strictly non-eligible under Art. 20)
  - Acct 7902 Contingency (10.0%): $362,866.00 (Unspent reserve; only actual incurred costs qualify under Art. 20)
  - Acct 7905 Completion Bond (2.0%): $72,573.00 (Financial guarantee non-eligible under Art. 20)
- **Above-The-Line Accounts (Subject to Statutory Ceilings & Territorial Nexus):**
  - Acct 1100 Story / Rights / Continuity: $252,650.00 (Rights eligible only if Greek authors/rights; unevidenced)
  - Acct 1200 Producers: $401,831.00 (Subject to 25–30% principal fee cap and local Greek tax compliance)
  - Acct 1300 Director: $75,710.00 (Subject to principal fee cap and Greek physical presence)
  - Acct 1400 Cast: $1,246,288.00 (Foreign non-resident actors non-eligible unless performing services in Greece under Greek tax withholding compliance)
  - Acct 1600 ATL Travel / Living: $174,546.00 (Eligible only for direct travel to/from Greece and Greek lodging)
- **Below-The-Line Physical Production Accounts ($1,090,130.00):**
  - Acct 2000 Production Staff: $168,353.00
  - Acct 2100 Extra Talent: $31,595.00
  - Acct 2200 Set Design: $32,773.00
  - Acct 2400 Set Dressing: $46,418.00
  - Acct 2500 Property: $41,199.00
  - Acct 2600 Picture Vehicles / Animals: $5,709.00
  - Acct 2700 Wardrobe: $67,504.00
  - Acct 2800 Makeup & Hair: $32,830.00
  - Acct 2900 Set Operations: $54,691.00
  - Acct 3000 Electric: $62,009.00
  - Acct 3100 Camera: $144,422.00
  - Acct 3200 Production Sound: $26,458.00
  - Acct 3400 Locations: $178,356.00
  - Acct 3600 Transportation: $81,123.00
  - Acct 3700 Office Studio Rentals: $17,042.00
  - Acct 3800 Production Film & Lab: $3,114.00
  - Acct 3900 BTL Travel & Living: $96,534.00
- **Post-Production Accounts ($166,646.00):**
  - Acct 4600 Visual Effects: $10,000.00
  - Acct 5000 Editorial: $78,475.00
  - Acct 5100 Music: $10,200.00
  - Acct 5200 Post Production Sound: $46,471.00
  - Acct 5400 Main & End Titles: $1,500.00
  - Acct 5600 Digital Intermediate: $15,000.00
  - Acct 5700 Deliverables: $5,000.00
- **Administrative Account ($170,535.00):**
  - Acct 7000 Administrative Expenses: $170,535.00 (Restricted to audit/accounting directly tied to Greek rebate compliance)

#### The Physical Spend Correlation:
Summing BTL Physical ($1,090,130) + Post-Production ($166,646) yields **$1,256,776.00**. When combined with local administrative or director allocations, this accounts for the producer's **$1,297,010.00** implied base ($1,297,010 × 40% = $518,804). The producer assumed a local Greek physical service shoot; CineGlobe assumed a full relocation including US star cast.

---

## 3. INVESTIGATION OF EVERY REMAINING ISSUE IN `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`

| ID | Issue Description | Failure Cause | Economic Impact | Governing Evidence | Current Audit Disposition & Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Q01** | California 20% / Implied $7.35M base contradiction | Earlier AG audit used Cal Program 3.0 20% rate and back-calculated QPE from $1,470,365 estimate. | False audit baseline; circular validation. | CFC Program 4.0 (35% base, $20M cap); budget 25% note. | **RETRACTED & RECTIFIED:** Historical program not established; Program 4.0 baseline applied. California QPE is `NOT_ESTABLISHED`. |
| **Q02** | California mixed ATL and legal accounts | Treating mixed writer/producer/director/cast/legal lines as 100% qualified or 100% excluded. | Over- or under-qualifying mixed accounts by up to $312,500. | CFC Jan 2026 Qualified Expenditure Chart. | **IMPLEMENTED:** Detail splits enforced in engine (e.g. LLS Acct 1100 splits to $1,653 QPE / $312,500 excluded). Tested in validator. |
| **Q03** | California ATL fringes | Qualifying ATL fringes without linkage to underlying qualifying labor. | Overstating QPE by $255,291 in LLS. | CFC Program 4.0 statutory fringe rules. | **IMPLEMENTED:** LLS Acct 1900 confirmed QPE set to $0.00 pending payee-level audit. Tested in validator. |
| **Q04** | Bad Hombres SAG reserve contradiction | Earlier audit included $60k SAG reserve in confirmed QPE while noting proof missing. | Inflation of confirmed base by $60,000. | SAG-AFTRA deposit agreement / unspent liability doctrine. | **RETRACTED & RECTIFIED:** $60,000 removed from confirmed base ($0 confirmed QPE; classified `MISSING_PRODUCTION_FACT`). |
| **Q05** | Program-wide maximum rates vs. subset uplifts | Applying uplifts (CA outside-zone +5%, local hire +5%, VFX +5%; NM rural +5%) to 100% of QPE. | Artificial inflation of potential incentive ceiling tiers. | CA Rev. & Tax Code § 17053.98; NM Stat. § 7-2F-1. | **IMPLEMENTED:** Engine models uplifts as eligible subsets (`EligibleSubsetUpliftRule`). Tested in synthetic test suite. |
| **Q06** | Greek ordinary cap vs. strategic project exception | Conflating EUR 8,000,000 statutory cap with EUR 10,000,000 strategic exception. | Potential $2,000,000 over-cap grant calculation. | Greek Law 4487/2017 Art. 26; JMD strategic regulations. | **IMPLEMENTED:** Ordinary cap clamped to EUR 8,000,000 (`IncentiveValueCapRule`). Tested in synthetic test suite. |
| **Q07** | Budget netting & CSV negative signs | CSV parser stripped negative signs on rebate lines, causing rebates to be added to gross cost. | Net production costs inflated by 2× the rebate amount. | Movie Magic budget CSV / PDF cross-comparison. | **IMPLEMENTED:** Parser 1.5.0 separates producer estimates and net lines; 25 synthetic tests pass. |
| **Q08** | Little Utopia publicity classification | Misclassifying Line 7100 ($24,348) as crew labor instead of general administration. | $24,348 false qualification in Ontario BTL labor credit. | LU topsheet / OFTTC guidelines. | **IMPLEMENTED:** Line 7100 correctly classified as `general_administration` / excluded. Tested in validator. |
| **Q09** | Movie Magic subaccount detail retention | Dropping subaccount detail rows during budget ingestion. | Inability to evaluate mixed accounts without guessing. | Movie Magic XML/JSON parser hierarchy. | **IMPLEMENTED:** 40 conserving subaccount groups stored for LLS. LU/FVD/BH topsheets lack subaccounts (acknowledged). |
| **Q10** | Missing territorial and payroll facts | Treating unevidenced out-of-state budgets as proven local spend. | Misrepresenting hypothetical relocation scenarios as legal claims. | Project file audit / absence of vendor ledgers. | **CONDITIONAL / NOT_ESTABLISHED:** All relocation scenarios explicitly labeled conditional planning projections. |
| **Q11** | Conflating historical control date with current law | Evaluating historical budgets against current 2026 statutes without temporal gating. | Distorting historical project comparability. | Statutory enactment timelines (e.g. NY 2023, CA 2025). | **IMPLEMENTED:** Enforce strict separation between `AS_OF_CONTROL_DATE` and `CURRENT_LAW_AS_OF_AUDIT_DATE`. |
| **Q12** | Circular engine validation | Using engine's own QPE, rates, or uplift selections as independent audit proof. | False audit certification of unverified numbers. | Audit integrity rules in `PROJECT_RULES.md`. | **PROHIBITED & RECTIFIED:** All expectations independently derived from primary legal text and source lines. |
| **Q13** | Double-counting embedded financing or incentives in NPC | Miscalculating NPC by subtracting source estimates from already-netted budget lines. | Net cost discrepancies up to $453k. | Economic formula: $\text{NPC} = \text{Gross} - \text{Credit}$. | **IMPLEMENTED:** Canonical netting contract verified; gross spend and incentives kept separate. |
| **Q14** | Stale persisted database calculations | Live database contains evaluations from older engines (1.12–1.34) lacking bug fixes. | Database records display unpatched numbers. | PostgreSQL database audit. | **ACKNOWLEDGED:** Persisted database recognized as stale; production regeneration pending explicit user authorization. |
| **Q15** | Four-anchor final reconciliation absent after repair | Full four-anchor final regeneration run has not occurred on production DB. | Audit cannot award global PASS. | Production database state. | **GATE REMAINS OPEN:** Production regeneration pending explicit user authorization. |

---

## 4. AUDIT CONTRADICTION RECTIFICATION SUMMARY

In accordance with Codex commit `31cc502`, the following contradictory statements in previous audit versions are formally corrected:

```
========================================================================================================================
Contradiction Subject       Previous Flawed AG Statement              Corrected Independent Audit Disposition
------------------------------------------------------------------------------------------------------------------------
Bad Hombres Base Status     "Confirmed QPE: $2,327,641.00"            CONDITIONAL: Base of $2,327,641 includes $1,032,202 in
                                                                      lead cast compensation requiring New Mexico non-resident
                                                                      withholding proof; confirmed base without cast is $1,295,439.
------------------------------------------------------------------------------------------------------------------------
Greece FVD Base Status      "Confirmed Greek QPE: $1,297,010.00"      NOT ESTABLISHED: $1,297,010 is estimate-implied from
                                                                      line 7903; topsheet lacks Greek expenditure schedule.
                                                                      The $926,855.84 difference is an unresolved planning variance.
------------------------------------------------------------------------------------------------------------------------
Little Utopia Local Basis   "Confirmed Ontario Base: $4,063,264.00"   CONDITIONAL PLANNING PROJECTION: Relies on assumption
                                                                      of 100% Ontario physical production and Canadian residency;
                                                                      itemized local vendor schedule is absent from topsheet.
------------------------------------------------------------------------------------------------------------------------
Lips Like Sugar Mixed Roles Incomplete detail splits on mixed accounts AUTHORED SPLITS ENFORCED: Strict adherence to CFC
                                                                      Program 4.0 chart (Line 1100: $1,653 QPE / $312,500 excluded;
                                                                      ATL compensation lines 1200, 1300, 1400 excluded).
========================================================================================================================
```

---

## 5. FOUR-ANCHOR ACCEPTANCE GATE DISPOSITION

**`STATUS: ANCHOR ACCEPTANCE GATE REMAINS OPEN`**  
**`FORMULATION: ADMISSIBLE AS CANONICAL RULE & PARSER REPAIR; PRODUCTION REGENERATION PENDING EXPLICIT AUTHORIZATION`**

Every discrepancy in `FOUR_ANCHOR_QPE_ISSUE_REGISTER.md` has been investigated, categorized, and reconciled against primary authorities and Codex adjudication. Unsupported numbers remain unresolved, contradictory claims are corrected, and production regeneration remains held pending explicit authorization.
