# Quebec & Manitoba Federal PSTC Assistance Netting: Four-Anchor Independent Audit

**Frozen Engine Baseline:** `canonical-1.122.0` (`59566fd1`).
**Remediation Checkout Baseline:** Commit `9ae7c5af` (incorporating `c52e2cd7` and `29740f70`).
**Document Purpose:** Establishes the independent calculation of Quebec and Manitoba provincial stacks with the federal Film or Video Production Services Tax Credit (`ca_federal_pstc`), expressing incentives on separate expenditure bases, comparing proportional-netting scenarios against whole-credit conservative bounds, examining reverse provincial netting from primary statutes, and reconciling all four anchor budgets.

---

## 1. Statutory Authorities & Dual Assistance Netting Rules

### 1.1 Federal PSTC Netting Rule (*Income Tax Act* § 125.5(1)(b))
Under subsection 125.5(1)(b) of the Canadian *Income Tax Act* (R.S.C. 1985, c. 1 (5th Supp.)):
- The federal PSTC is 16% of the **qualified Canadian labour expenditure (QCLE)**.
- QCLE is defined as Canadian labour expenditure less:
  > *"the total of all amounts, each of which is an amount of assistance that can reasonably be considered to be in respect of amounts included in [Canadian labour expenditure]..."*
- Assistance is defined via paragraph 12(1)(x) and includes provincial film tax credits.
- **Critical Distinction:** When a provincial program subsidizes only labour (like Ontario OPSTC or BC PSTC), 100% of the provincial assistance is attributable to labour. When a provincial program subsidizes **all production expenditures** (like Quebec QPSTC or Manitoba Cost-of-Production), the statute does not prescribe a mechanical formula for how assistance is allocated between labour and non-labour components.

### 1.2 Quebec QPSTC (*Loi sur les impôts*, RLRQ c. I-3, s. 1029.8.36.0.0.4) & Reverse Assistance
- **Credit Base & Rate:** 25% of eligible production costs incurred in Quebec by an eligible production services corporation holding a SODEC certificate.
- **Reverse Provincial Assistance Check:** Under s. 1029.8.36.0.0.4, eligible production costs must be reduced by government assistance received or receivable that is attributable to those costs. However, Quebec tax practice and Revenu Québec Form **CO-1029.8.36.SP** exclude the federal PSTC from being deducted against the provincial base (i.e. federal PSTC does not grind Quebec QPSTC).
- **Federal Netting Against PSTC:**
  - **Proportional Labour Allocation (Planning Baseline):** If the 25% provincial subsidy is attributed proportionally across all eligible spend, the assistance in respect of labour is $25\% 	imes 	ext{labour}$. The remaining net labour base is $(1 - 0.25) 	imes 	ext{labour} = 75\% 	imes 	ext{labour}$.
  - **Whole-Credit Deduction (Lower-Incentive Bound):** If the CRA treats the entire dollar amount of Quebec assistance ($25\% 	imes 	ext{open base}$) as reducing Canadian labour dollar-for-dollar, the net labour base is $\max(0, 	ext{labour} - 	ext{QPSTC dollars})$. This represents a conservative lower-incentive / higher-NPC bound.
  - **Statutory Status:** The exact statutory allocation rule remains **OPEN**.

### 1.3 Manitoba Cost-of-Production Credit (*Manitoba Income Tax Act* s. 7.6(6)) & Reverse Assistance
- **Credit Base & Rate:** 30% of eligible Manitoba production expenditures (all-spend) under s. 7.6(6), plus an 8% bonus if eligible.
- **Reverse Provincial Assistance Check:** Section 7.5(1) defines government assistance but excludes provincial credits under section 7.6. Manitoba does not grind its Cost-of-Production credit by federal PSTC.
- **Federal Netting Against PSTC:**
  - **Proportional Labour Allocation (Planning Baseline):** Net labour is $(1 - 0.30) 	imes 	ext{labour} = 70\% 	imes 	ext{labour}$.
  - **Whole-Credit Deduction (Conservative Lower-Incentive Bound):** In Claude remediation commit `c52e2cd7` (engine 1.128.0), Manitoba assistance is recognized as a conservative bound where the gross provincial credit ($30\% 	imes 	ext{open base}$) is subtracted from Canadian labour.
  - **Statutory Status:** The exact statutory allocation rule remains **OPEN**.

---

## 2. Separate Bases vs. Misleading Combined Percentages

> [!WARNING]
> **Withdrawal of Misleading Combined Percentages:**
> Combining provincial all-spend percentages with federal labour percentages into single rates (such as "37%" or "41.2%") is **mathematically invalid**.
> The provincial credit applies to the **open production spend base** (excluding finance, residuals, and contingency), whereas the federal PSTC applies strictly to the **Canadian labour base**.
> Every stack must be expressed in separate dollar calculations on its respective statutory cost pools.

---

## 3. Four-Anchor Independent Stack Calculations

The table below presents the independent calculations across all four anchor budgets, showing the open spend base, labour base, provincial credit, federal PSTC under both proportional allocation and the whole-credit conservative bound, total incentive, and Net Production Cost (NPC):

### 3.1 Quebec Service Stack (`ca_federal_pstc + ca_qc_pstc`)

| Project | Gross Budget (USD) | Open Spend Base (USD) | Labour Base (USD) | QPSTC Dollars (25% on Open Base) | Scenario | Federal Net Labour (USD) | Federal PSTC Dollars (16%) | Total Incentive (USD) | Net Production Cost (NPC) (USD) |
|:---|---:|---:|---:|---:|:---|---:|---:|---:|---:|
| **`LU`** | \$4,364,395.00 | \$4,063,264.00 | \$192,974.00 | \$1,015,816.00 | **Proportional (75%)** | \$144,730.50 | \$23,156.88 | **\$1,038,972.88** | **\$3,325,422.12** |
| | | | | | **Conservative Bound** | \$0.00 | \$0.00 | **\$1,015,816.00** | **\$3,348,579.00** |
| **`FVD`** | \$4,517,687.00 | \$3,701,238.00 | \$2,009,309.00 | \$925,309.50 | **Proportional (75%)** | \$1,506,981.75 | \$241,117.08 | **\$1,166,426.58** | **\$3,351,260.42** |
| | | | | | **Conservative Bound** | \$1,083,999.50 | \$173,439.92 | **\$1,098,749.42** | **\$3,418,937.58** |
| **`BH`** | \$2,482,023.00 | \$2,327,641.00 | \$1,478,106.00 | \$581,910.25 | **Proportional (75%)** | \$1,108,579.50 | \$177,372.72 | **\$759,282.97** | **\$1,722,740.03** |
| | | | | | **Conservative Bound** | \$896,195.75 | \$143,391.32 | **\$725,301.57** | **\$1,756,721.43** |
| **`LLS`** | \$11,983,654.00 | \$9,483,654.00 | \$2,935,298.00 | \$2,370,913.50 | **Proportional (75%)** | \$2,201,473.50 | \$352,235.76 | **\$2,723,149.26** | **\$9,260,504.74** |
| | | | | | **Conservative Bound** | \$564,384.50 | \$90,301.52 | **\$2,461,215.02** | **\$9,522,438.98** |

### 3.2 Manitoba Service Stack (`ca_federal_pstc + ca_mb_film_video_credit`)

| Project | Gross Budget (USD) | Open Spend Base (USD) | Labour Base (USD) | MB Credit Dollars (30% on Open Base) | Scenario | Federal Net Labour (USD) | Federal PSTC Dollars (16%) | Total Incentive (USD) | Net Production Cost (NPC) (USD) |
|:---|---:|---:|---:|---:|:---|---:|---:|---:|---:|
| **`LU`** | \$4,364,395.00 | \$4,063,264.00 | \$192,974.00 | \$1,218,979.20 | **Proportional (70%)** | \$135,081.80 | \$21,613.09 | **\$1,240,592.29** | **\$3,123,802.71** |
| | | | | | **Conservative Bound** | \$0.00 | \$0.00 | **\$1,218,979.20** | **\$3,145,415.80** |
| **`FVD`** | \$4,517,687.00 | \$3,701,238.00 | \$2,009,309.00 | \$1,110,371.40 | **Proportional (70%)** | \$1,406,516.30 | \$225,042.61 | **\$1,335,414.01** | **\$3,182,272.99** |
| | | | | | **Conservative Bound** | \$898,937.60 | \$143,830.02 | **\$1,254,201.42** | **\$3,263,485.58** |
| **`BH`** | \$2,482,023.00 | \$2,327,641.00 | \$1,478,106.00 | \$698,292.30 | **Proportional (70%)** | \$1,034,674.20 | \$165,547.87 | **\$863,840.17** | **\$1,618,182.83** |
| | | | | | **Conservative Bound** | \$779,813.70 | \$124,770.19 | **\$823,062.49** | **\$1,658,960.51** |
| **`LLS`** | \$11,983,654.00 | \$9,483,654.00 | \$2,935,298.00 | \$2,845,096.20 | **Proportional (70%)** | \$2,054,708.60 | \$328,753.38 | **\$3,173,849.58** | **\$8,809,804.42** |
| | | | | | **Conservative Bound** | \$90,201.80 | \$14,432.29 | **\$2,859,528.49** | **\$9,124,125.51** |

---

## 4. Comparison with Claude Code & Defect Separation

| Defect / Code Path | Frozen Engine 1.122 (`59566fd1`) State | Claude Remediation Checkout (`9ae7c5af`) State | Independent Audit Finding & Attribution |
|:---|:---|:---|:---|
| **Manitoba Federal PSTC Stack Pair** | Completely omitted from `_SLUG_PAIR_RULES` (`stacking_rules.py`). `check_all_pairs` fails to generate stack. | **Repaired in commit `29740f70`** (engine 1.127.0) and refined in **`c52e2cd7`** (engine 1.128.0) using conservative bound. | Confirmed **active engine omission defect in frozen 1.122**. |
| **Quebec Federal PSTC Stack Pair** | Completely omitted from `_SLUG_PAIR_RULES` (`stacking_rules.py`). | **Repaired in commit `3a8f7370`** (engine 1.125.0) via generic foreign service pairing. | Confirmed **active engine omission defect in frozen 1.122**. |
| **Reverse Provincial Assistance** | Not modeled in baseline. | Not modeled in baseline. | Provincial statutes (*BC ITA* s. 79(1), *Manitoba ITA* s. 7.5(1), *Loi sur les impôts* s. 1029.8.36.0.0.4) do not deduct federal PSTC from provincial spend. |
| **Producer Fact Follow-Ups** | Missing T4 ledgers, residency proofs, CAVCO certificates. | Treated as planning mode inputs with disclosures. | Genuinely empirical; remain open as claim follow-ups across all four anchors. |

---

## 5. Precise Open Items

1. **Exact Statutory Netting Allocation for All-Spend Provincial Credits:** Neither the federal *Income Tax Act* § 125.5(1)(b) nor CRA Guide RC4385 explicitly prescribes whether all-spend credits are apportioned proportionally to labour or subtracted dollar-for-dollar in gross. The proportional baseline and whole-credit conservative bound represent the exact bounded sensitivity range; the precise statutory allocation remains **OPEN**.
2. **Producer Incurred Facts:** Individual deal memos, T4 resident payroll ledgers, and CAVCO/SODEC certificates remain claim-level follow-ups.
