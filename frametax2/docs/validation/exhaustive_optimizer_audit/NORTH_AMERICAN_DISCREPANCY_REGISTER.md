# North American Four-Anchor Comprehensive Discrepancy Register

**Audit Track:** Independent North American QPE Audit (US, Canada, Mexico)
**Engine Version Under Audit:** `canonical-1.106.0`
**Database:** `frametax2_claude_optimizer_acceptance_20260919`
**Status:** `STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`
**Total Evaluations Conducted:** 200 (180 single-program + 20 multi-program stacks)
**Total Discrepancies Catalogued:** 167

---

## 1. Executive Summary & Defect Taxonomy

Auditing the CineGlobe engine against dated primary statutes reveals that the engine's internal arithmetic is consistent with its own generic-spend-base model, but systematically diverges from statutory realities in five major areas:

1. **NA-DEFECT-01 (NY § 24 ATL 40% Aggregate Ceiling Omission):** The engine completely omits NY Tax Law § 24(b)(1)'s aggregate 40% ATL cap and individual $500k person caps, qualifying $1.15M–$1.94M of non-qualifying ATL compensation per production and overstating NY tax credits by up to **$582,525.48**.
2. **NA-DEFECT-02 (Canadian Domestic Stacking Ineligibility):** The engine prices domestic Canadian content stacks (`ca_federal_cptc + on_ofttc`, `ca_federal_cptc + ca_qc_pstc`) as high-ranking alternatives for foreign productions (LU, FVD, BH, LLS) that fail CAVCO domestic content gates by statute.
3. **NA-DEFECT-03 (Mexico FX Gating & Native MXN Threshold Omission):** The engine evaluates Mexico at flat 30% rates on generic USD spend bases without enforcing native MXN 40,000,000 spend floors or live FX conversion.
4. **NA-DEFECT-04 (North Carolina Floorless Grant Persisted):** North Carolina's discretionary grant pool without a statutory floor was persisted as a guaranteed 25% credit in `canonical-1.106.0`.
5. **NA-DEFECT-05 (High-Earner Salary Cap Omission):** Statutory $500k individual wage ceilings (GA, IL) and $1M payroll exclusion thresholds (MA) were not deducted from topsheet line sums.
6. **NA-DEFECT-06 (Canadian Topsheet Labour-Basis Overstatement):** Canadian production services credits apply strictly to Canadian resident labor, whereas the engine applied statutory rates against the full production spend base.
7. **NA-DEFECT-07 (California Program 4.0 Minimum Spend Omission on Bad Hombres):** Bad Hombres has only $773,889.00 in BTL production spend, failing California Program 4.0's $1,000,000 minimum spend threshold.

---

## 2. Comprehensive Discrepancy Table

| Project | Program Slug | Jurisdiction | Expected Status | Actual Status | Expected Inc ($) | Actual Inc ($) | Delta Inc ($) | Defect ID | Root Cause Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **LU** | `ca_federal_pstc` | CA | QUALIFIED | PRICED | 205,837.60 | 111,706.40 | -94,131.20 | `NA-DEFECT-06` | Engine assumed uniform 100% budget spend as QLE rather than isolating Canadian r... |
| **LU** | `ca_ab_fttc` | CA-AB | QUALIFIED | PRICED | 960,166.46 | 1,824,808.16 | 864,641.70 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `ca_bc_dave` | CA-BC | QUALIFIED | PRICED | 9,850.88 | 279,005.48 | 269,154.60 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $61,568.00 vs engine generic spend ba... |
| **LU** | `ca_bc_pstc` | CA-BC | QUALIFIED | PRICED | 463,134.60 | 279,005.48 | -184,129.12 | `NA-DEFECT-06` | Engine assumed uniform 100% budget spend as QLE rather than isolating Canadian r... |
| **LU** | `ca_mb_film_video_credit` | CA-MB | QUALIFIED | PRICED | 578,918.25 | 1,826,621.76 | 1,247,703.51 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $1,286,485.00 vs engine generic spend... |
| **LU** | `ca_nb_film_tax_credit` | CA-NB | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `ca_nl_all_spend_credit` | CA-NL | QUALIFIED | PRICED | 1,745,757.20 | 1,826,440.40 | 80,683.20 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `ca_ns_production_incentive_fund` | CA-NS | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `on_ofttc` | CA-ON | GATE_REJECTED | PRICED | 0.00 | 1,825,987.00 | 1,825,987.00 | `NA-DEFECT-GATE-VIOLATION` | Engine priced candidate despite statutory gate failure: DOMESTIC_CONTENT_GATE_FA... |
| **LU** | `on_opstc` | CA-ON | QUALIFIED | PRICED | 276,594.28 | 881,102.14 | 604,507.86 | `NA-DEFECT-06` | Engine assumed uniform 100% budget spend as QLE rather than isolating Canadian r... |
| **LU** | `ontario_computer_animation_and_special_effects_tax_credit_ocase` | CA-ON | QUALIFIED | PRICED | 11,082.24 | 1,428,418.60 | 1,417,336.36 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $61,568.00 vs engine generic spend ba... |
| **LU** | `ca_qc_pstc` | CA-QC | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `mx_federal_film_incentive_2026` | MX | GATE_REJECTED | PRICED | 0.00 | 1,825,533.60 | 1,825,533.60 | `NA-DEFECT-GATE-VIOLATION` | Engine priced candidate despite statutory gate failure: NATIVE_FX_GATING_FAILED ... |
| **LU** | `us_al_film_incentive` | US-AL | QUALIFIED | PRICED | 1,091,098.25 | 1,825,987.00 | 734,888.75 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_az_motion_picture_production` | US-AZ | QUALIFIED | PRICED | 654,658.95 | 627,960.00 | -26,698.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `ca_film_30` | US-CA | QUALIFIED | PRICED | 1,099,813.40 | 1,825,987.00 | 726,173.60 | `NA-DEFECT-07` | Engine over-included ATL costs or omitted Program 4.0 $1M minimum spend threshol... |
| **LU** | `us_co_film_incentive` | US-CO | QUALIFIED | PRICED | 872,878.60 | 1,824,626.80 | 951,748.20 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ct_film_tax_credit` | US-CT | QUALIFIED | PRICED | 436,439.30 | 1,228,214.40 | 791,775.10 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ga_film_credit` | US-GA | QUALIFIED | PRICED | 736,153.60 | 828,044.80 | 91,891.20 | `NA-DEFECT-05` | Engine omitted high-earner salary cap deductions ($500k in GA/IL, $1M in MA).... |
| **LU** | `us_hi_film_digital_media_credit` | US-HI | QUALIFIED | PRICED | 960,166.46 | 1,824,808.16 | 864,641.70 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_il_film_production_services_credit` | US-IL | QUALIFIED | PRICED | 1,288,268.80 | 1,428,299.20 | 140,030.40 | `NA-DEFECT-05` | Engine omitted high-earner salary cap deductions ($500k in GA/IL, $1M in MA).... |
| **LU** | `us_ky_keiia` | US-KY | QUALIFIED | PRICED | 1,309,317.90 | 1,228,214.40 | -81,103.50 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_la_film_incentive` | US-LA | QUALIFIED | PRICED | 1,091,098.25 | 1,028,129.60 | -62,968.65 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ma_film_tax_credit` | US-MA | QUALIFIED | PRICED | 920,192.00 | 1,028,129.60 | 107,937.60 | `NA-DEFECT-05` | Engine omitted high-earner salary cap deductions ($500k in GA/IL, $1M in MA).... |
| **LU** | `us_mn_film_production_credit` | US-MN | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ms_advantage_film_program` | US-MS | QUALIFIED | PRICED | 1,091,098.25 | 1,028,129.60 | -62,968.65 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_nc_film_entertainment_grant` | US-NC | CONDITIONAL_NONDETERMINISTIC | PRICED | 0.00 | 1,028,129.60 | 1,028,129.60 | `NA-DEFECT-FLOORLESS-PRICED` | Engine priced floorless discretionary grant pool without allocation agreement.... |
| **LU** | `us_nm_film_credit` | US-NM | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_nv_film_credit` | US-NV | QUALIFIED | PRICED | 654,658.95 | 627,960.00 | -26,698.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `ny_state_film` | US-NY | QUALIFIED | PRICED | 985,046.70 | 1,228,214.40 | 243,167.70 | `NA-DEFECT-01` | Engine omitted NY § 24(b)(1) 40% aggregate ATL ceiling and individual $500k pers... |
| **LU** | `us_ok_film_enhancement_rebate` | US-OK | QUALIFIED | PRICED | 872,878.60 | 1,824,626.80 | 951,748.20 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_or_opif` | US-OR | QUALIFIED | PRICED | 872,878.60 | 1,001,302.15 | 128,423.55 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_pa_film_production_credit` | US-PA | QUALIFIED | PRICED | 1,091,098.25 | 1,825,080.20 | 733,981.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_pr_film_incentives_act` | US-PR | QUALIFIED | PRICED | 872,878.60 | 828,044.80 | -44,833.80 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ri_film_credit` | US-RI | QUALIFIED | PRICED | 1,309,317.90 | 1,228,214.40 | -81,103.50 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_tn_performance_grant` | US-TN | QUALIFIED | PRICED | 1,091,098.25 | 1,028,129.60 | -62,968.65 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_ut_motion_picture_incentive` | US-UT | QUALIFIED | PRICED | 872,878.60 | 1,824,626.80 | 951,748.20 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_va_motion_picture_credit` | US-VA | QUALIFIED | PRICED | 654,658.95 | 627,960.00 | -26,698.95 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **LU** | `us_wa_motion_picture_competitiveness` | US-WA | QUALIFIED | PRICED | 1,309,317.90 | 1,228,214.40 | -81,103.50 | `NA-DEFECT-VARIANCE` | Engine generic base variance: Expected QPE $4,364,393.00 vs engine generic spend... |
| **FVD** | `ca_federal_cptc` | CA | GATE_REJECTED | PRICED | 0.00 | 1,473,902.23 | 1,473,902.23 | `NA-DEFECT-GATE-VIOLATION` | Engine priced candidate despite statutory gate failure: DOMESTIC_CONTENT_GATE_FA... |

*(Full 200-row record available in `NORTH_AMERICAN_FOUR_PROJECT_COMPREHENSIVE_MATRIX.csv`)*

---

## 3. Detailed Account-Level Reconciliations

### 3.1 New York State Film Production Credit (§ 24) Breakdown
* **The Little Utopia:** Expected QPE $3,282,489.00 ($3,141,324 BTL+Post + $141,165 ATL) vs Engine Qualified $4,054,196.00 (Overstatement: +$771,707.00 QPE / +$231,512.10 Credit).
* **F#K Valentine's Day:** Expected QPE $1,759,486.40 ($1,256,776 BTL+Post + $502,710.40 capped ATL) vs Engine Qualified $3,701,238.00 (Overstatement: +$1,941,751.60 QPE / +$582,525.48 Credit).
* **Bad Hombres:** Expected QPE $1,049,844.60 ($749,889 BTL+Post + $299,955.60 capped ATL) vs Engine Qualified $2,327,641.00 (Overstatement: +$1,277,796.40 QPE / +$383,338.92 Credit).
* **Lips Like Sugar:** Expected QPE $8,194,877.60 ($5,853,484 BTL+Post + $2,341,393.60 capped ATL) vs Engine Qualified $9,483,654.00 (Overstatement: +$1,288,776.40 QPE / +$386,632.92 Credit).

### 3.2 California Film & TV Tax Credit (Program 4.0 BTL) Breakdown
* **The Little Utopia:** Expected QPE $3,524,820.00 vs Engine QPE $4,054,196.00 (Delta: -$529,376.00).
* **F#K Valentine's Day:** Expected QPE $1,600,542.00 vs Engine QPE $3,701,238.00 (Delta: -$2,100,696.00 due to ATL inclusion in engine).
* **Bad Hombres:** Expected Status `GATE_REJECTED` (BTL spend $773,889 fails $1M minimum threshold) vs Engine priced at $299,158.65.
* **Lips Like Sugar:** Expected QPE $6,043,679.00 (BTL only) matches producer topsheet line 9998 ($6,012,296.00) within 0.5%.

---

## 4. Proposed Canonical Repairs for Codex Review

1. **Implement `NY_ATL_40_PERCENT_RULE` in `program_spend_rules.py`:** Restrict qualifying ATL costs to $\le 0.40 \times (\text{BTL} + \text{Post})$ and enforce $500k/person and max 2 producer caps.
2. **Gate Domestic Stacking on CAVCO Status:** Add `domestic_content_certified` gate to `ca_federal_cptc` and `on_ofttc` in `stacking_rules.py` so foreign productions cannot claim domestic stacks.
3. **Enforce Mexico Native Currency Gating:** Ensure `mx_federal_film_incentive_2026` checks native MXN 40M spend floor and clamps to MXN 40M cap via live FX table.
4. **Deduct High-Earner Salary Caps in GA, IL, MA:** Deduct compensation exceeding $500,000 per person in GA and IL, and exclude compensation $\ge$ $1,000,000 in MA.

> [!IMPORTANT]
> **GATE DISPOSITION:**
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> All empirical missing facts (payroll schedules, out-of-zone shoot logs, general ledger employee splits) remain explicitly unresolved. No acceptance gate is closed.
