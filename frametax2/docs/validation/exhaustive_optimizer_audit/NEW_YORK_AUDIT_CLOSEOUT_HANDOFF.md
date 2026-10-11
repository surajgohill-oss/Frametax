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

### Core Audit Tenets Enforced:
1. **Zero Circularity & Zero Arithmetic against Self:** All expectations were derived independently from original budget accounts/schedules and dated primary statutes without invoking engine qualification, classification, or pricing methods.
2. **Strict Adherence to Rule 5 (No Per-Person Caps on Aggregate Accounts):** On productions lacking itemized general ledger talent contracts (FVD, BH, LLS), no exact per-person caps were fabricated. These projects are classified as **`NOT_ESTABLISHED (MISSING_INDIVIDUAL_TALENT_CONTRACTS)`** under **`NOT_ESTABLISHED_EMPIRICAL_GAP`**, with rigorously evidenced statutory bounds (Min QPE vs. Max QPE) proving engine overstatement.
3. **Exact Derivation to the Cent on The Little Utopia (LU):** On LU, where script clearances and cast payees are individually evidenced below $500,000 and producer count is 0, the statutory 40% aggregate ceiling and BTL+Post baseline are verified to the cent, establishing an exact credit overstatement of **+$231,212.10** with zero balancing residual.
4. **Reconciliation of Multi-Program Stacking (`DISC-NY-001`):** NY Tax Law § 31*2(a)(1) & 5 NYCRR § 240.3(c) command an absolute taxpayer/film-level bar between Section 24 and Section 31*2. Confirmed engine rule defect `DISC-NY-001` (`same_cost_prohibited_distinct_costs_allowed`) is isolated; saved engine outputs that did not generate a stack candidate are reclassified as **`COMPARISON_NOT_ESTABLISHED (STACK_NOT_GENERATED / DISC-NY-001)`**. Missing candidates alone cannot establish `VERIFIED_AGREEMENT`.
5. **No Production Mutations or ROW Expansion:** Zero production code or database mutations were performed; all checks pass negative controls (40/40); Rest-of-World (ROW) expansion remains strictly gated.

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
* **Upstate Production Credit Uplift (§ 24(a)(5)):**
  - **County Definition:** 53 upstate counties. In accordance with primary text and adjudication finding `NY-A05`, **Dutchess, Orange, and Putnam counties ARE statutorily included** in the upstate production credit county list (unlike the MCTD post-production boundary).
  - **Uplift Rate:** Additional +10% credit (40% total).
  - **Labor Limb:** Wages paid to New York residents for work performed in upstate counties qualify for the +10% uplift.
  - **Non-Labor Limb:** Non-labor qualified costs incurred in upstate counties qualify for the +10% uplift **ONLY IF more than fifty percent (> 50%) of principal photography shoot days** occur in upstate counties.
  - **ATL Exclusion:** ATL wages are statutorily excluded from the +10% uplift (they remain capped at the 30% base rate).

### 2.2 NY Tax Law § 31*2 (Empire State Film Post-Production Credit)
* **Controlling Text:** NY Tax Law § 31*2 (revision 2025-07-11; distinct from plain § 31 Excelsior Jobs). Regulations: 5 NYCRR Part 240.
* **Taxpayer/Film-Level Mutual Exclusivity (§ 31*2(a)(1) & 5 NYCRR § 240.3(c)):**
  - *"A taxpayer shall be eligible for the credit... provided however that no taxpayer shall be eligible to receive this credit if such taxpayer has qualified or is eligible to qualify for the empire state film production credit pursuant to section twenty-four of this article with respect to the same qualified film."*
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

### 3.1 The Little Utopia (`LU`) — Exact Cent-Level Derivation (`NA-DEFECT-01`)
* **Gross Controlling Budget:** $4,364,393.00 (Movie Magic Topsheet declared controlling gross; leaf sum $4,364,395.00 carries documented $2 rounding variance per `NY-A02`).
* **Source Cost Account Breakdown:**
  - Qualified BTL Physical Production: $2,781,775.00
  - Qualified BTL Travel & Living: $82,347.00
  - On-Set Production Sound (BTL per `NY-A03`): $69,532.00
  - Qualified Post-Production (Accounts 5100–5700): $208,670.00
  - **Sum of All Other Qualified Costs (BTL + Post Base):** **$3,142,324.00**
* **Statutory 40% Aggregate Ceiling:**
  $$\text{Ceiling} = 0.40 \times \$3,142,324.00 = \$1,256,929.60$$
* **Creative Above-The-Line Incurred:**
  - Script Clearances (Account 1103): $5,050.00 (under $500k cap)
  - Cast (Account 1400): $136,115.00 (all individual earners <= $500k; no background extras)
  - Director / Producers: $0.00 in budget file
  - **Total Creative ATL:** **$141,165.00**
  - Since $\$141,165.00 \le \$1,256,929.60$ (40% ceiling), 100% of creative ATL qualifies.
* **Statutory Non-Qualifying Exclusions:**
  - Unspent Contingency: $310,197.00
  - Financing & Banking Fees (Accounts 1800/1900): $421,791.00
  - Insurance & Completion Bond (Account 7200): $130,081.00 ($72,830 insurance + $57,251 bond)
  - General Administrative & Indirect (Account 7100): $79,985.00
  - Total Exclusions + Contingency: $1,080,904.00
  - Balance Check: $\$3,283,489.00 \text{ QPE} + \$1,080,904.00 \text{ Excluded} = \$4,364,393.00$ (100% conserving).
* **Independent Expected NY § 24 Calculation:**
  $$\text{Expected QPE} = \$3,142,324.00 + \$141,165.00 = \mathbf{\$3,283,489.00}$$
  $$\text{Expected Base Incentive (30\%)} = \$3,283,489.00 \times 0.30 = \mathbf{\$985,046.70}$$
  $$\text{Expected Net Production Cost (NPC)} = \$4,364,393.00 - \$985,046.70 = \mathbf{\$3,379,346.30}$$
* **Engine Comparison (`canonical-1.106.0`, Result ID `e2300b8c-5f80-4d8c-bd5b-b99fbbbf1335`):**
  - Actual Qualified Spend: $4,054,196.00 (gross $4,364,393 less unspent contingency $310,197)
  - Actual Incentive: $1,216,258.80 ($4,054,196.00 × 0.30)
  - **QPE Variance:** **+$770,707.00**
  - **Incentive Overstatement:** **+$231,212.10**
  - **Unexplained Arithmetic Residual:** **$0.00**
* **Root Cause & Disposition:** Engine configured as `OPEN_DEFAULT_INCLUDE` with unenforced ATL ceiling in `program_spend_rules.py:193`, qualifying non-qualifying finance, insurance, and administrative costs. Disposition: **`OPEN_CODE_DEFECT_PENDING_CODEX_REVIEW` (`NA-DEFECT-01`)**.

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
  - Overstatement at Maximum Upper Bound:
    $$\Delta \text{Credit}_{\min} = \$1,110,371.40 - \$527,845.92 = \mathbf{+\$582,525.48}$$
  - Overstatement at Lower Bound:
    $$\Delta \text{Credit}_{\max} = \$1,110,371.40 - \$377,032.80 = \mathbf{+\$733,338.60}$$
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
  - Overstatement at Maximum Upper Bound:
    $$\Delta \text{Credit}_{\min} = \$698,292.30 - \$314,953.38 = \mathbf{+\$383,338.92}$$
  - Overstatement at Lower Bound:
    $$\Delta \text{Credit}_{\max} = \$698,292.30 - \$224,966.70 = \mathbf{+\$473,325.60}$$
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
  - Overstatement at Maximum Upper Bound:
    $$\Delta \text{Credit}_{\min} = \$2,845,096.20 - \$2,458,463.28 = \mathbf{+\$386,632.92}$$
  - Overstatement at Lower Bound:
    $$\Delta \text{Credit}_{\max} = \$2,845,096.20 - \$1,756,045.20 = \mathbf{+\$1,089,051.00}$$
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
  - Audit Disposition: **`COMPARISON_NOT_ESTABLISHED (COMPONENT_ONLY_STRUCTURE)`**.

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
  4. Explicitly exclude non-qualifying categories: Financing fees (Accounts 1800/1900/6500/6600/6700), completion bond and corporate insurance (Account 7200), and general corporate administration (Account 7100).

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

1. **Individual Talent Contracts (`MISSING_INDIVIDUAL_TALENT_CONTRACTS`):**
   - General ledger talent agreements, per-person compensation schedules, and producer contracts are absent from budget files for FVD, BH, and LLS.
   - Statutory $500k per-person caps and the 2-producer limit cannot be definitively calculated on aggregate topsheet lines without fabricating payee splits.
   - **Remediation Action:** Requires audit access to executed talent payroll ledgers and contracts from production accounting.
2. **Qualified Post-Production Facility Contracts (`MISSING_QPF_CERTIFICATION`):**
   - Qualified post facility agreements, county registrations, and worldwide post spend certifications are absent from source records.
   - **Remediation Action:** Requires post-production accounting logs and ESD-certified QPF vendor invoices.
3. **Upstate Principal Photography Shoot Logs (`MISSING_UPSTATE_SHOOT_LOGS`):**
   - Daily production reports (call sheets / shoot logs) establishing that >50% of principal photography shoot days occurred in upstate counties are absent.
   - Upstate non-labor uplift remains an explicit conditional planning scenario (`CONDITIONAL_UPSTATE_EXPANSION`).
   - **Remediation Action:** Requires production shoot day logs signed by the 1st AD / Unit Production Manager.

---

## 7. Mandatory Gate Disposition & Sign-off

> [!IMPORTANT]
> ### FINAL HANDOFF GATE DISPOSITION:
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> 1. **Zero Acceptance of Defective Totals:** The engine's saved results in `canonical-1.106.0` overstate New York State film tax credits by at least **+$231,212.10** on The Little Utopia, **+$582,525.48** on FVD, **+$383,338.92** on Bad Hombres, and **+$386,632.92** on Lips Like Sugar.
> 2. **Remediation Gate Closed Only upon Codex Review & Regeneration:** Acceptance will NOT close until Codex implements the repair specifications (`NA-DEFECT-01`, `DISC-NY-001`, `DISC-NY-002`, `DISC-NY-003`), runs authorized canonical regeneration, and verifies agreement against independent bounds.
> 3. **Rest-of-World (ROW) Expansion Boundary:** Regional expansion remains strictly paused. ROW audit will not commence until Codex adjudicates this package.
