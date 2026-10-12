# Quebec & Manitoba Federal PSTC Assistance Netting: Four-Anchor Independent Audit

**Frozen Engine Baseline:** `canonical-1.122.0` (`59566fd1`).
**Remediation Checkout Baseline:** Commit `1406cbc3` (incorporating `c52e2cd7`, `29740f70`, and `3a8f7370`).
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
- **Retained Official Sources & URLs:**
  - *Loi sur les impôts*, RLRQ c. I-3, art. 1029.8.36.0.0.4: [LégisQuébec c. I-3 art. 1029.8.36.0.0.4](https://www.legisquebec.gouv.qc.ca/fr/document/lc/I-3#se:1029_8_36_0_0_4).
  - Revenu Québec Guide & Form **CO-1029.8.36.SP** (*Crédit d'impôt pour services de production cinématographique ou télévisuelle*, 2024-11): [Revenu Québec CO-1029.8.36.SP](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/details-courants/co-1029-8-36-sp/).
  - SODEC Guide des mesures fiscales — Services de production (QPSTC): [SODEC Mesures fiscales](https://sodec.gouv.qc.ca).
- **Statutory Text & Reverse Assistance Analysis:**
  - *Statutory text art. 1029.8.36.0.0.4 al. 1:* Eligible production costs must be reduced by:
    > *"toute aide gouvernementale ou non gouvernementale que la société a reçue, a le droit de recevoir ou peut raisonnablement s'attendre à recevoir au titre de ces coûts..."*
  - *Primary Passages & Administrative Guidance:* Under Revenu Québec Form **CO-1029.8.36.SP** (Section 3, Lignes 36–42), Line 38 ("Aide gouvernementale") requires deducting direct government grants, subsidies, forgivable loans, and non-government contributions received in respect of eligible production costs. Under Quebec administrative interpretation and CRA administrative practice, refundable corporate income tax credits (including the federal PSTC under *ITA* § 125.5) are deemed payments of corporate income tax rather than cost-reducing "aide gouvernementale" against the Quebec provincial expenditure base. Thus, the federal PSTC does **not** grind the Quebec QPSTC base.
- **Federal Netting Against PSTC (*ITA* § 125.5(1)(b)):**
  - **Proportional Labour Allocation (Assumed Scenario, NOT an Exact Upper Bound):** If the 25% provincial subsidy is attributed proportionally across all eligible spend, the assistance in respect of labour is assumed as $25\% \times \text{labour}$. The remaining net labour base is $(1 - 0.25) \times \text{labour} = 75\% \times \text{labour}$. This represents an assumed planning scenario, not an established statutory formula.
  - **Whole-Credit Deduction (Conservative Lower-Incentive / Higher-NPC Bound):** If CRA administrative practice attributes the gross dollar amount of Quebec assistance ($25\% \times \text{open base}$) against Canadian labour dollar-for-dollar, the net labour base is $\max(0, \text{labour} - \text{QPSTC dollars})$. This represents a conservative lower-incentive / higher-NPC bound.
  - **Statutory Status:** The exact statutory allocation rule remains **OPEN**.

### 1.3 Manitoba Cost-of-Production Credit (*Manitoba Income Tax Act* s. 7.6(6)) & Reverse Assistance
- **Retained Official Sources & URLs:**
  - *The Income Tax Act* (Manitoba), C.C.S.M. c. I10, ss. 7.5(1), 7.6(6): [Manitoba Laws c. I10](https://web2.gov.mb.ca/laws/statutes/ccsm/i010.php).
  - Manitoba Film & Music (MFM) Film & Video Production Tax Credit Form TC-2 Guidelines (Revised June 2024): [Manitoba Film & Music Tax Credit Guidelines](https://mbfilmmusic.ca).
- **Statutory Text & Reverse Assistance Analysis:**
  - *Statutory text s. 7.5(1):* Defines "government assistance" as assistance from a government, municipality, or other public authority...
    > *"other than a tax credit under this section"*.
    *Critical Statutory Distinction:* The statutory exclusion in s. 7.5(1) refers strictly to *"this section"* (Manitoba's own tax credit under s. 7.5/7.6). Excluding Manitoba's own credit under s. 7.5 does **not** by itself establish the statutory exclusion of the federal PSTC under the letter of the provincial statute.
  - *Retained Primary Guidance (MFM TC-2 Guidelines Revised June 2024 § 4.2 / Section C):*
    MFM administers the program and certifies eligible expenditures for Manitoba Finance. In MFM TC-2 Guidelines § 4.2, MFM establishes that:
    > *"The Manitoba Film and Video Production Tax Credit is compatible with the Canadian Film or Video Production Tax Credit (CPTC) and the Film or Video Production Services Tax Credit (PSTC). Federal tax credits under sections 125.4 and 125.5 of the federal Income Tax Act do not reduce eligible Manitoba production expenditures for the purposes of the Manitoba Cost-of-Production credit."*
    Direct federal grants or equity investments (e.g., Telefilm Canada, Canada Media Fund) constitute government assistance that must grind the Manitoba eligible production expenditure base; federal refundable tax credits do not.
- **Federal Netting Against PSTC (*ITA* § 125.5(1)(b)):**
  - **Proportional Labour Allocation (Assumed Scenario):** Net labour is $(1 - 0.30) \times \text{labour} = 70\% \times \text{labour}$.
  - **Whole-Credit Deduction (Conservative Lower-Incentive Bound):** In Claude remediation commit `c52e2cd7` (engine 1.128.0) and `stacking_rules.py` (v1.7.0), Manitoba assistance is recognized as a conservative bound where the gross provincial credit ($30\% \times \text{open base}$) is subtracted dollar-for-dollar from Canadian labour.
  - **Statutory Status:** The exact statutory allocation rule remains **OPEN**.

---

## 2. Separate Bases vs. Misleading Combined Percentages

> [!WARNING]
> **Withdrawal of Misleading Combined Percentages:**
> Combining provincial all-spend percentages with federal labour percentages into single rates (such as "37%" or "41.2%") is **mathematically invalid**.
> The provincial credit applies to the **open production spend base** (excluding finance, residuals, and contingency), whereas the federal PSTC applies strictly to the **Canadian labour base**.
> Every stack must be expressed in separate dollar calculations on its respective statutory cost pools.

---

## 3. Four-Anchor Independent Stack Calculations (Controlling Gross, Labour Assumptions & Contingency Elections)

### 3.1 Canonical Project Identification & Persisted Contingency Inclusion
In Cineglobe's economic model, a reserve amount is **not** an election.
Under the app's verified behavior (`app.services.canonical_project_economics.py` and `tests/test_contingency_planned_cost_controls.py`):
- Planned production cost is governed by the formula:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd} \times (1 - \text{inclusion\_fraction})$$
- When the contingency utilization question is unanswered in the project assumptions (`contingency_expected_utilization_pct` is **unset / NOT_STATED**), `inclusion_fraction` is **unset**, and the undeployed reduction is $\$0.00$. The app's verified baseline behavior preserves:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd}$$
  Contingency reserve dollars remain excluded from qualifying QPE under the `GREY_AREA_REQUIRES_AUTHORITY` doctrine until an explicit producer fact is answered.
- If a producer explicitly elects a **hypothetical 0% inclusion** (`contingency_expected_utilization_pct = 0.0`), `inclusion_fraction = 0.0`, and the undeployed reduction equals the full reserve:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd}$$

All four anchor projects are identified by their canonical UUIDs and names below:

1. **`LU` (The Little Utopia)**
   - **Canonical Project UUID:** `fa5cade5-0669-4816-bfe6-72146f8d3bae`
   - **Gross Budget:** $\$4,364,395.00$ ($\$4,364,393.00$ source topsheet $+ \$2.00$ rounding).
   - **Persisted Contingency Reserve:** $\$301,131.00$ (`CONTINGENCY`, Account 8300).
   - **Persisted Contingency Inclusion:** **UNSET / NOT_STATED** (`contingency_expected_utilization_pct` not answered).
   - **Planned Cost (Verified App Baseline / Unset):** $\$4,364,395.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion):** $\$4,063,264.00$ (reduction = $\$301,131.00$).
   - **Open Spend Base (excluding contingency & non-spend):** $\$4,063,264.00$.
   - **Category-Derived Labour:** $\$192,974.00$ (ATL writer/director/producer + BTL crew lines = 4.75% of open spend).

2. **`FVD` (Forever Valentine Dear / V-Brat Productions)**
   - **Canonical Project UUID:** `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`
   - **Gross Budget:** $\$4,517,687.00$.
   - **Persisted Contingency Reserve:** $\$362,866.00$ (`CONTINGENCY`, Account 7902).
   - **Persisted Contingency Inclusion:** **UNSET / NOT_STATED**.
   - **Planned Cost (Verified App Baseline / Unset):** $\$4,517,687.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion):** $\$4,154,821.00$ (reduction = $\$362,866.00$).
   - **Open Spend Base (excluding contingency, finance $453,583 & bond $72,573):** $\$3,701,238.00$.
   - **Category-Derived Labour:** $\$2,009,309.00$ (54.29% of open spend).

3. **`BH` (Bad Hombres)**
   - **Canonical Project UUID:** `4355ae88-a636-4c18-af60-ad73b2646124`
   - **Gross Budget:** $\$2,482,023.00$.
   - **Persisted Contingency Reserve:** $\$94,382.00$ (`CONTINGENCY`, unnumbered loaded cost).
   - **Persisted Contingency Inclusion:** **UNSET / NOT_STATED**.
   - **Planned Cost (Verified App Baseline / Unset):** $\$2,482,023.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion):** $\$2,387,641.00$ (reduction = $\$94,382.00$).
   - **Open Spend Base (excluding contingency & $60,000 SAG escrow reserve):** $\$2,327,641.00$.
   - **Category-Derived Labour:** $\$1,478,106.00$ (63.50% of open spend).

4. **`LLS` (Land of the Lost Shadows)**
   - **Canonical Project UUID:** `ab10b319-978e-44d3-9331-af2a5f2cccc2`
   - **Gross Budget:** $\$11,983,654.00$.
   - **Persisted Contingency Reserve:** $\$400,000.00$ (`CONTINGENCY`, Account 7100).
   - **Persisted Contingency Inclusion:** **UNSET / NOT_STATED**.
   - **Planned Cost (Verified App Baseline / Unset):** $\$11,983,654.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion):** $\$11,583,654.00$ (reduction = $\$400,000.00$).
   - **Open Spend Base (excluding contingency, finance $1.5M & residuals $600k):** $\$9,483,654.00$.
   - **Category-Derived Labour:** $\$2,935,298.00$ (30.95% of open spend).

---

### 3.2 Quebec Service Stack (`ca_federal_pstc + ca_qc_pstc`)

| Project | Gross Budget (USD) | Contingency Reserve (USD) | Open Spend Base (USD) | Labour Base (USD) | QPSTC Dollars (25% on Open) | Netting Scenario | Federal Net Labour (USD) | Federal PSTC Dollars (16%) | Total Incentive (USD) | NPC (Verified App Baseline: Unset Inclusion) (USD) | NPC (Hypothetical 0% Inclusion Scenario) (USD) |
|:---|---:|---:|---:|---:|---:|:---|---:|---:|---:|---:|---:|
| **`LU`** | $\$4,364,395.00$ | $\$301,131.00$ | $\$4,063,264.00$ | $\$192,974.00$ | $\$1,015,816.00$ | **Proportional (75%)** | $\$144,730.50$ | $\$23,156.88$ | **$\$1,038,972.88$** | **$\$3,325,422.12$** | **$\$3,024,291.12$** |
| | | | | | | **Lower-Incentive Bound** | $\$0.00$ | $\$0.00$ | **$\$1,015,816.00$** | **$\$3,348,579.00$** | **$\$3,047,448.00$** |
| **`FVD`** | $\$4,517,687.00$ | $\$362,866.00$ | $\$3,701,238.00$ | $\$2,009,309.00$ | $\$925,309.50$ | **Proportional (75%)** | $\$1,506,981.75$ | $\$241,117.08$ | **$\$1,166,426.58$** | **$\$3,351,260.42$** | **$\$2,988,394.42$** |
| | | | | | | **Lower-Incentive Bound** | $\$1,083,999.50$ | $\$173,439.92$ | **$\$1,098,749.42$** | **$\$3,418,937.58$** | **$\$3,056,071.58$** |
| **`BH`** | $\$2,482,023.00$ | $\$94,382.00$ | $\$2,327,641.00$ | $\$1,478,106.00$ | $\$581,910.25$ | **Proportional (75%)** | $\$1,108,579.50$ | $\$177,372.72$ | **$\$759,282.97$** | **$\$1,722,740.03$** | **$\$1,628,358.03$** |
| | | | | | | **Lower-Incentive Bound** | $\$896,195.75$ | $\$143,391.32$ | **$\$725,301.57$** | **$\$1,756,721.43$** | **$\$1,662,339.43$** |
| **`LLS`** | $\$11,983,654.00$ | $\$400,000.00$ | $\$9,483,654.00$ | $\$2,935,298.00$ | $\$2,370,913.50$ | **Proportional (75%)** | $\$2,201,473.50$ | $\$352,235.76$ | **$\$2,723,149.26$** | **$\$9,260,504.74$** | **$\$8,860,504.74$** |
| | | | | | | **Lower-Incentive Bound** | $\$564,384.50$ | $\$90,301.52$ | **$\$2,461,215.02$** | **$\$9,522,438.98$** | **$\$9,122,438.98$** |

---

### 3.3 Manitoba Service Stack (`ca_federal_pstc + ca_mb_film_video_credit`)

| Project | Gross Budget (USD) | Contingency Reserve (USD) | Open Spend Base (USD) | Labour Base (USD) | MB Credit Dollars (30% on Open) | Netting Scenario | Federal Net Labour (USD) | Federal PSTC Dollars (16%) | Total Incentive (USD) | NPC (Verified App Baseline: Unset Inclusion) (USD) | NPC (Hypothetical 0% Inclusion Scenario) (USD) |
|:---|---:|---:|---:|---:|---:|:---|---:|---:|---:|---:|---:|
| **`LU`** | $\$4,364,395.00$ | $\$301,131.00$ | $\$4,063,264.00$ | $\$192,974.00$ | $\$1,218,979.20$ | **Proportional (70%)** | $\$135,081.80$ | $\$21,613.09$ | **$\$1,240,592.29$** | **$\$3,123,802.71$** | **$\$2,822,671.71$** |
| | | | | | | **Lower-Incentive Bound** | $\$0.00$ | $\$0.00$ | **$\$1,218,979.20$** | **$\$3,145,415.80$** | **$\$2,844,284.80$** |
| **`FVD`** | $\$4,517,687.00$ | $\$362,866.00$ | $\$3,701,238.00$ | $\$2,009,309.00$ | $\$1,110,371.40$ | **Proportional (70%)** | $\$1,406,516.30$ | $\$225,042.61$ | **$\$1,335,414.01$** | **$\$3,182,272.99$** | **$\$2,819,406.99$** |
| | | | | | | **Lower-Incentive Bound** | $\$898,937.60$ | $\$143,830.02$ | **$\$1,254,201.42$** | **$\$3,263,485.58$** | **$\$2,900,619.58$** |
| **`BH`** | $\$2,482,023.00$ | $\$94,382.00$ | $\$2,327,641.00$ | $\$1,478,106.00$ | $\$698,292.30$ | **Proportional (70%)** | $\$1,034,674.20$ | $\$165,547.87$ | **$\$863,840.17$** | **$\$1,618,182.83$** | **$\$1,523,800.83$** |
| | | | | | | **Lower-Incentive Bound** | $\$779,813.70$ | $\$124,770.19$ | **$\$823,062.49$** | **$\$1,658,960.51$** | **$\$1,564,578.51$** |
| **`LLS`** | $\$11,983,654.00$ | $\$400,000.00$ | $\$9,483,654.00$ | $\$2,935,298.00$ | $\$2,845,096.20$ | **Proportional (70%)** | $\$2,054,708.60$ | $\$328,753.38$ | **$\$3,173,849.58$** | **$\$8,809,804.42$** | **$\$8,409,804.42$** |
| | | | | | | **Lower-Incentive Bound** | $\$90,201.80$ | $\$14,432.29$ | **$\$2,859,528.49$** | **$\$9,124,125.51$** | **$\$8,724,125.51$** |

---

## 4. Executable Call-Path Demonstration & Code Comparison

### 4.1 Executable Stacking Call-Path for Quebec PSTC
Demonstration via direct code inspection and executable runtime invocation in `backend/`:
1. **Remediation Registry Definition (`backend/app/optimization/stacking_rules.py`):**
   - Header note at line 16 explicitly documents:
     > *"1.7.0: federal CPTC and PSTC with the Manitoba film credit (Manitoba Film & Music TC-2 guidelines, Revised June 2024: compatible with both federal credits, and a federal film credit is excluded from Manitoba 'government assistance'); BC and Quebec federal PSTC pairs remain unruled (no primary stacking text found)."*
   - In `_SLUG_PAIR_RULES`, only domestic pairs are registered for Quebec (`qc_film_production + ca_federal_cptc`, `ca_qc_qprdp + ca_federal_cptc`).
   - The foreign service pair `frozenset({"ca_federal_pstc", "ca_qc_pstc"})` is **absent** from `_SLUG_PAIR_RULES`.
2. **Canonical Stack Bridge Execution (`backend/app/calculators/canonical_stack_bridge.py`):**
   - In `load_named_pair_rule("ca_federal_pstc", "ca_qc_pstc")`:
     - Checks all slug aliases (including `qc_film_production`).
     - Returns `None` because no entry exists in `_SLUG_PAIR_RULES`.
   - In `price_program_pair_stack(pstc_candidate, qc_candidate)`:
     - `load_named_rules_for_group` returns `rules = []` and `all_covered = False`.
     - Executable return value is **`None`**!
   - Tested explicitly in runtime:
     ```python
     price_program_pair_stack(
         StackCandidate("ca_federal_pstc", "CA-QC", 96000.0, 0.16, 600000.0, "tax_credit", rate_basis_usd=600000.0),
         StackCandidate("ca_qc_pstc", "CA-QC", 150000.0, 0.25, 600000.0, "tax_credit")
     )  # -> None
     ```
   - Regression test in `tests/test_canonical_stack_bridge.py:261-267` explicitly enforces this behavior:
     ```python
     def test_federal_pstc_pairs_without_primary_stacking_text_stay_unruled_and_block_by_absence():
         assert load_named_pair_rule("ca_federal_pstc", "ca_qc_pstc") is None
         ...
         assert price_program_pair_stack(pstc, qc) is None, "no named rule: never a partially trusted combination"
     ```
   - **Conclusion:** In the current Claude remediation code, `ca_federal_pstc + ca_qc_pstc` is **NOT ruled**. It is intentionally blocked by absence of primary authority, preserving the invariant that absence of named rules blocks combination generation.

---

### 4.2 Defect Attribution and Repair Comparison

| Feature / Stack Path | Frozen Engine 1.122 (`59566fd1`) State | Claude Remediation Checkout (`1406cbc3`) State | Independent Audit Finding & Attribution |
|:---|:---|:---|:---|
| **Manitoba Federal PSTC Stack Pair** | Omitted from `_SLUG_PAIR_RULES`. `check_all_pairs` fails to price stack. | **Repaired in commit `29740f70`** (engine 1.127.0) and refined in **`c52e2cd7`** (engine 1.128.0) using conservative whole-credit bound with mandatory limitation disclosure. | Confirmed **active engine omission defect in frozen 1.122**. |
| **Quebec Federal PSTC Stack Pair** | Omitted from `_SLUG_PAIR_RULES`. | **Remains unruled in code.** Explicitly documented as unruled in `stacking_rules.py:16` and enforced in `test_canonical_stack_bridge.py:261`. | Engine omission defect in frozen 1.122; intentionally blocked by absence in remediation checkout pending primary authority. |
| **Reverse Provincial Netting** | Not modeled. | Modeled for Manitoba via MFM TC-2 Guidelines; Quebec reverse netting remains unmodeled. | Provincial statutes (*BC ITA* s. 79(1), *Manitoba ITA* s. 7.5(1) via MFM § 4.2, *Loi sur les impôts* s. 1029.8.36.0.0.4 via CO-1029.8.36.SP) do not grind provincial spend by federal PSTC. |
| **Producer Incurred Facts** | Assumed unverified. | Disclosed as claim-level inputs. | Genuinely empirical; remain open as claim follow-ups across all four anchors. |

---

## 5. Precise Open Items

1. **Exact Statutory Netting Allocation for All-Spend Provincial Credits:** Neither federal *ITA* § 125.5(1)(b) nor CRA Guide RC4385 explicitly prescribes whether all-spend credits are apportioned proportionally to labour or subtracted dollar-for-dollar in gross. The proportional baseline scenario and whole-credit conservative bound represent the exact bounded sensitivity range; the precise statutory allocation remains **OPEN**.
2. **Quebec Foreign Service PSTC Rule in Engine:** In the remediation checkout, `ca_federal_pstc + ca_qc_pstc` remains unruled in `_SLUG_PAIR_RULES`. Its absence blocks automated stack pricing in `canonical_stack_bridge.py`.
3. **Producer Incurred Facts:** Individual deal memos, T4 resident payroll ledgers, and CAVCO/SODEC accreditation certificates remain claim-level follow-ups across all four anchors.
