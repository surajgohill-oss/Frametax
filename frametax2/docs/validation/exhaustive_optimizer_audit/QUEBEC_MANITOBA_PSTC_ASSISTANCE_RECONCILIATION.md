# Quebec & Manitoba Federal PSTC Assistance Netting: Four-Anchor Independent Audit

**Frozen Engine Baseline:** `canonical-1.122.0` (`59566fd1`).  
**Remediation Checkout Baseline:** Commit `23c9dae5` (incorporating `c52e2cd7`, `29740f70`, `3a8f7370`, `60c3a3fa`, and `ec7574ef`).  
**Document Purpose:** Establishes the independent calculation and reconciliation of Quebec and Manitoba provincial stacks with the federal Film or Video Production Services Tax Credit (`ca_federal_pstc`), expressing incentives on separate expenditure bases, reconciling findings read-only against the current remediation checkout (`23c9dae5`), examining reverse provincial netting from primary authorities, and classifying all four-anchor calculations by value provenance.

---

## 1. Statutory Authorities & Dual Assistance Netting Rules

### 1.1 Federal PSTC Netting Rule (*Income Tax Act* § 125.5(1)(b))
Under subsection 125.5(1)(b) of the Canadian *Income Tax Act* (R.S.C. 1985, c. 1 (5th Supp.)):
- The federal PSTC is 16% of the **qualified Canadian labour expenditure (QCLE)**.
- QCLE is defined as Canadian labour expenditure less:
  > *"the total of all amounts, each of which is an amount of assistance that can reasonably be considered to be in respect of amounts included in [Canadian labour expenditure]..."*
- Assistance is defined via paragraph 12(1)(x) and includes provincial film tax credits.
- **Critical Distinction:** When a provincial program subsidizes only labour (like Ontario OPSTC or BC PSTC), 100% of the provincial assistance is attributable to labour. When a provincial program subsidizes **all production expenditures** (like Quebec QPSTC or Manitoba Cost-of-Production), the statute does not prescribe a mechanical formula for how assistance is allocated between labour and non-labour components.

### 1.2 Quebec QPSTC (*Loi sur les impôts*, RLRQ c. I-3, art. 1029.8.36.0.0.4) & Reverse Assistance Adjudication
- **Retained Official Sources & URLs:**
  - *Loi sur les impôts*, RLRQ c. I-3, art. 1029.8.36.0.0.4: [LégisQuébec c. I-3 art. 1029.8.36.0.0.4](https://www.legisquebec.gouv.qc.ca/fr/document/lc/I-3#se:1029_8_36_0_0_4).
  - Revenu Québec Guide & Formulaire **CO-1029.8.36.SP** (*Crédit d'impôt pour services de production cinématographique ou télévisuelle*, versions 2024-09 / 2024-11): [Revenu Québec CO-1029.8.36.SP](https://www.revenuquebec.ca/fr/services-en-ligne/formulaires-et-publications/details-courants/co-1029-8-36-sp/).
  - SODEC Direction générale des mesures fiscales — *Crédit d'impôt pour services de production cinématographique ou télévisuelle (CISP)*, Fact Sheet (March 2026): [SODEC Mesures fiscales](https://sodec.gouv.qc.ca).
- **Exact Retained Statutory Passage, Form Line & Note Text:**
  - *Statutory text art. 1029.8.36.0.0.4 al. 1:* Eligible production costs must be reduced by:
    > *"toute aide gouvernementale ou non gouvernementale que la société a reçue, a le droit de recevoir ou peut raisonnablement s'attendre à recevoir au titre de ces coûts..."*
  - *Official Form Instructions (CO-1029.8.36.SP, Section 4, Ligne 38):*
    Line 38 (*Aide gouvernementale et aide non gouvernementale*) deducts assistance in respect of eligible production costs.
  - *Exact Form Note (CO-1029.8.36.SP, Note 7):*
    > *"Les sommes reçues au titre du crédit d'impôt du Québec pour services de production cinématographique ou télévisuelle, du crédit d'impôt du Canada pour services de production cinématographique ou vidéo (crédit d'impôt fédéral pour services de production) ou du crédit d'impôt du Canada pour production cinématographique ou magnétoscopique canadienne (crédit d'impôt fédéral pour production canadienne) ne constituent pas de l'aide gouvernementale ou non gouvernementale et, par conséquent, elles ne réduisent ni les frais de production, ni le coût de la main-d'œuvre."*
  - **Reverse Assistance Adjudication:** The current canonical statement that the federal PSTC does **not** reduce the Quebec service credit is **fully supported** by Revenu Québec Form CO-1029.8.36.SP Note 7 and Line 38 instructions. Under Quebec authority, federal PSTC deemed tax paid under Part I is not cost-reducing assistance against the QPSTC spend base.
- **Separation of Verified Reverse Treatment from Assumed Forward Allocation:**
  - *Verified Reverse Treatment:* Federal PSTC does **not** grind or reduce Quebec eligible production costs (CO-1029.8.36.SP Note 7). This reverse treatment is fully verified and authority-supported.
  - *Assumed Forward Allocation (*ITA* § 125.5(1)(b)):* In the other direction, the Quebec QPSTC is an all-spend credit (25% on all eligible spend). Subsection 125.5(1)(b) reduces federal labour by assistance reasonably in respect of labour, but neither CRA RC4385 nor the federal statute specifies a formula. Deducting $25\% \times \text{labour}$ is an **assumed allocation scenario** (disclosing the whole-credit deduction as a conservative lower-incentive bound in `disclosed_limitations`). The precise statutory allocation rule remains **OPEN**.

### 1.3 Manitoba Cost-of-Production Credit (*Manitoba Income Tax Act* s. 7.5(1), 7.6(6)) & Quotation Correction
- **Retained Official Sources & URLs:**
  - *The Income Tax Act* (Manitoba), C.C.S.M. c. I10, ss. 7.5(1), 7.6(6): [Manitoba Laws c. I10](https://web2.gov.mb.ca/laws/statutes/ccsm/i010.php).
  - Manitoba Film & Music (MFM) Film & Video Production Tax Credit Form TC-2 Guidelines (Revised June 2024), Sections C & I: [Manitoba Film & Music Tax Credit Guidelines](https://mbfilmmusic.ca/programs/film-video-tax-credit/).
- **Exact Retained Statutory Passage & Primary Authority:**
  - *Statutory text s. 7.5(1) definition of "government assistance":*
    > *"'government assistance' means assistance from a government, municipality or other public authority in any form, including a grant, subsidy, forgivable loan, deduction from tax and investment allowance, other than a tax credit under this section;"*
  - **Manitoba Quotation Correction & Unsupported Wording Locations:**
    1. The statutory carve-out in s. 7.5(1) refers strictly and exclusively to *"other than a tax credit under this section"* (Manitoba's own tax credit under s. 7.5/7.6). Excluding Manitoba's own credit does **not** prove statutory exclusion of federal film credits under the text of the provincial Act.
    2. Prior engine comments, test docstrings, migrations, and audit drafts attributing language to Manitoba authority stating that Manitoba "government assistance" excludes *"any film and video production tax credit under this Act or under the federal Act"*, or claiming an explicit statutory exclusion of federal credits, are **FORMALLY WITHDRAWN AS UNSUPPORTED QUOTATIONS**. No such wording exists in s. 7.5(1) or MFM TC-2 guidelines.
    3. **Exact Current-Remediation Wording That Claude Must Repair:**
       - `backend/app/optimization/stacking_rules.py:541-542`:
         `Manitoba's own "government assistance" excludes "any film and video production tax credit under this Act or under the federal Act", so the federal credits do not reduce the Manitoba credit.`
       - `backend/alembic/versions/0083_manitoba_federal_stacking_rules.py:4-6`:
         `and Manitoba's own "government assistance" excludes any film and video production tax credit under the Manitoba or federal Act.`
       - `docs/architecture/CAPABILITY_LEDGER.md:4728`:
         `and a federal film credit is excluded from Manitoba "government assistance".`
       - `backend/tests/test_canonical_stack_bridge.py:260`:
         `# Manitoba Film & Music TC-2 guidelines (June 2024): compatible with the CPTC and the PSTC; the federal credits are not assistance to the Manitoba credit.`
  - **Supported Manitoba Administrative Guidance:**
    Notwithstanding the unsupported quotation, supported Manitoba Film & Music administrative guidance (TC-2 Guidelines Revised June 2024, Sections C and I) still affirmatively establishes:
    1. *Compatibility:* The Manitoba Cost of Production Tax Credit "is compatible with the Canadian Film or Video Production Tax Credit (CPTC) and the Film or Video Production Services Tax Credit (PSTC)" (TC-2 Section I).
    2. *Federal Credits Do Not Reduce Manitoba Credit:* In administrative certification practice under TC-2 Section C, MFM certifies eligible production expenditures alongside federal tax credits without grinding the base by deemed federal Part I tax installments.
    3. *Manitoba Credit Reduces Federal PSTC Labour:* In the forward direction under *ITA* § 125.5(1)(b), the Manitoba credit constitutes assistance reducing federal PSTC only to the extent reasonably attributable to labour.
  - **Separation of Legal Tiers & Economic Impact:**
    - *Statutory Text:* s. 7.5(1) excludes only Manitoba's own credit; silence on federal tax credits.
    - *Administrative Practice:* MFM TC-2 Sections C and I administer certification without grinding by federal credits.
    - *Assumed Federal Allocation:* The $30\% \times \text{labour}$ deduction is an assumed planning allocation, with the whole-credit deduction disclosed as a conservative lower bound.
    - *Economic Invariant:* **The economic result does NOT change.** The pricing logic in `canonical_stack_bridge.py` and the calculated NPC values for Manitoba remain economically identical because MFM administrative practice does not grind Manitoba spend by federal credits, and federal labour netting uses the assumed allocation with whole-credit lower bound disclosure.

---

## 2. Separate Bases vs. Misleading Combined Percentages

> [!WARNING]
> **Withdrawal of Misleading Combined Percentages:**
> Combining provincial all-spend percentages with federal labour percentages into single rates (such as "37%" or "41.2%") is **mathematically invalid**.
> The provincial credit applies to the **open production spend base** (excluding finance, residuals, and contingency), whereas the federal PSTC applies strictly to the **Canadian labour base**.
> Every stack must be expressed in separate dollar calculations on its respective statutory cost pools.

---

## 3. Four-Anchor Independent Stack Calculations (Controlling Gross, Labour Assumptions & Contingency Elections)

### 3.1 Canonical Project Identification & Persisted Contingency Inclusion (Read-Only)
In Cineglobe's economic model, a reserve amount is **not** an election.
Under the app's verified behavior (`app.services.canonical_project_economics.py:320-350` and `tests/test_contingency_planned_cost_controls.py:46-88`):
- Planned production cost is governed by the formula:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd} \times (1 - \text{inclusion\_fraction})$$
- When the contingency utilization question is unanswered in the project assumptions (`contingency_expected_utilization_pct` is **unset / NOT_STATED**), `inclusion_fraction` is **unset**, and the undeployed reduction is $\$0.00$. The app's verified baseline behavior preserves:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd}$$
  Contingency reserve dollars remain excluded from qualifying QPE under the `GREY_AREA_REQUIRES_AUTHORITY` doctrine until an explicit producer fact is answered.
- If a producer explicitly elects a **hypothetical 0% inclusion** (`contingency_expected_utilization_pct = 0.0`), `inclusion_fraction = 0.0`, and the undeployed reduction equals the full reserve:
  $$\text{planned\_cost\_usd} = \text{gross\_budget\_usd} - \text{contingency\_reserve\_usd}$$
- **Contingency Behavior Confirmation:** The current remediation code (`backend/app/services/canonical_project_economics.py:320-350`, `contingency_planning_view`) and focused test controls (`backend/tests/test_contingency_planned_cost_controls.py`) already preserve this verified behavior byte-for-byte. There is zero contradiction, and the behavior is firmly established.

All four anchor projects were queried from the database without writes and are identified by their canonical UUIDs and names:

1. **`LU` (The Little Utopia)**
   - **Canonical Project UUID:** `fa5cade5-0669-4816-bfe6-72146f8d3bae`
   - **Canonical Name in Database:** `The Little Utopia`
   - **Gross Budget:** $\$4,364,395.00$ ($\$4,364,393.00$ source topsheet $+ \$2.00$ rounding).
   - **Persisted Contingency Reserve:** $\$301,131.00$ (`CONTINGENCY`, Account 8300).
   - **Persisted Contingency Inclusion Percentage (Read-Only DB):**
     - In runtime database `frametax2`: **UNSET / NOT_STATED** (no `project_facts` row).
     - In acceptance database `frametax2_claude_optimizer_acceptance_20260919`: `100.0%` (legacy `recovered_demo_state` fact).
   - **Planned Cost (Verified App Baseline: Unset / 100% Inclusion):** $\$4,364,395.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion Sensitivity):** $\$4,063,264.00$ (reduction = $\$301,131.00$).
   - **Open Spend Base (excluding contingency & non-spend):** $\$4,063,264.00$.
   - **Category-Derived Labour:** $\$192,974.00$ (ATL writer/director/producer + BTL crew lines = 4.75% of open spend).

2. **`FVD` (F#K Valentine's Day)**
   - **Canonical Project UUID:** `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`
   - **Canonical Name in Database:** `F#K Valentine's Day` (topsheet titled *V-Brat Productions* / *Forever Valentine Dear*).
   - **Gross Budget:** $\$4,517,687.00$.
   - **Persisted Contingency Reserve:** $\$362,866.00$ (`CONTINGENCY`, Account 7902).
   - **Persisted Contingency Inclusion Percentage (Read-Only DB):** **UNSET / NOT_STATED** (0 rows in `project_facts` in both databases).
   - **Planned Cost (Verified App Baseline: Unset):** $\$4,517,687.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion Sensitivity):** $\$4,154,821.00$ (reduction = $\$362,866.00$).
   - **Open Spend Base (excluding contingency, finance $453,583 & bond $72,573):** $\$3,701,238.00$.
   - **Category-Derived Labour:** $\$2,009,309.00$ (54.29% of open spend).

3. **`BH` (Bad Hombres)**
   - **Canonical Project UUID:** `4355ae88-a636-4c18-af60-ad73b2646124`
   - **Canonical Name in Database:** `Bad Hombres`
   - **Gross Budget:** $\$2,482,023.00$.
   - **Persisted Contingency Reserve:** $\$94,382.00$ (`CONTINGENCY`, unnumbered loaded cost).
   - **Persisted Contingency Inclusion Percentage (Read-Only DB):** **UNSET / NOT_STATED** (0 rows in `project_facts` in both databases).
   - **Planned Cost (Verified App Baseline: Unset):** $\$2,482,023.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion Sensitivity):** $\$2,387,641.00$ (reduction = $\$94,382.00$).
   - **Open Spend Base (excluding contingency & $60,000 SAG escrow reserve):** $\$2,327,641.00$.
   - **Category-Derived Labour:** $\$1,478,106.00$ (63.50% of open spend).

4. **`LLS` (Lips Like Sugar)**
   - **Canonical Project UUID:** `ab10b319-978e-44d3-9331-af2a5f2cccc2`
   - **Canonical Name in Database:** `Lips Like Sugar`
   - **Gross Budget:** $\$11,983,654.00$.
   - **Persisted Contingency Reserve:** $\$400,000.00$ (`CONTINGENCY`, Account 7100).
   - **Persisted Contingency Inclusion Percentage (Read-Only DB):** **UNSET / NOT_STATED** (0 rows in `project_facts` in both databases).
   - **Planned Cost (Verified App Baseline: Unset):** $\$11,983,654.00$ (reduction = $\$0.00$).
   - **Planned Cost (Hypothetical 0% Inclusion Sensitivity):** $\$11,583,654.00$ (reduction = $\$400,000.00$).
   - **Open Spend Base (excluding contingency, finance $1.5M & residuals $600k):** $\$9,483,654.00$.
   - **Category-Derived Labour:** $\$2,935,298.00$ (30.95% of open spend).

---

### 3.2 Classification of Four-Anchor Table Values
To prevent presentation of hypothetical sensitivities or assumptions as actual anchor results, every figure in the four-anchor tables below is classified into one of five rigorous tiers:
1. **[V-IN] Verified Retained Project Input:** Primary project data persisted in the database (UUIDs, names, topsheet gross budgets, reserve lines, read-only unset utilization state, open spend base, and category labour base).
2. **[E-OUT] Current Engine Output:** Output from the current remediation engine at HEAD `23c9dae5` (`canonical_stack_bridge.py`), which models `spend_reduction` by pricing the assumed labour-share allocation in `per_program_adjusted_usd` and disclosing the whole-credit lower bound in `disclosed_limitations`.
3. **[I-AR] Independent Arithmetic:** Mathematical evaluation of statutory rate equations ($25\% \text{ QPSTC}$, $30\% \text{ Manitoba}$, $16\% \text{ PSTC}$) against verified bases.
4. **[H-SEN] Hypothetical Sensitivity:** Exploratory scenarios (hypothetical 0% contingency utilization, or conservative whole-credit netting bounds). These are **not** actual baseline anchor results.
5. **[S-OUT] Stale-Checkout Output:** Findings from frozen 1.122.0 (`59566fd1`) or intermediate checkout `1406cbc3` where Quebec was reported "blocked by absence of named rule". Superseded in `23c9dae5`.

---

### 3.3 Quebec Service Stack (`ca_federal_pstc + ca_qc_pstc`)

| Project | Gross Budget [V-IN] | Contingency Reserve [V-IN] | Open Spend Base [V-IN] | Labour Base [V-IN] | QPSTC Dollars (25%) [I-AR/E-OUT] | Netting Scenario [Provenance] | Federal Net Labour [I-AR] | Federal PSTC Dollars (16%) [I-AR/E-OUT] | Total Incentive (USD) [I-AR/E-OUT] | NPC (Verified Baseline: Unset Inclusion) [I-AR/E-OUT] | NPC (Hypothetical 0% Inclusion Sensitivity) [H-SEN] |
|:---|---:|---:|---:|---:|---:|:---|---:|---:|---:|---:|---:|
| **`LU`** | $\$4,364,395.00$ | $\$301,131.00$ | $\$4,063,264.00$ | $\$192,974.00$ | $\$1,015,816.00$ | **Assumed Allocation (75%) [E-OUT]** | $\$144,730.50$ | $\$23,156.88$ | **$\$1,038,972.88$** | **$\$3,325,422.12$** | *$\$3,024,291.12$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$0.00$ | $\$0.00$ | **$\$1,015,816.00$** | **$\$3,348,579.00$** | *$\$3,047,448.00$* |
| **`FVD`** | $\$4,517,687.00$ | $\$362,866.00$ | $\$3,701,238.00$ | $\$2,009,309.00$ | $\$925,309.50$ | **Assumed Allocation (75%) [E-OUT]** | $\$1,506,981.75$ | $\$241,117.08$ | **$\$1,166,426.58$** | **$\$3,351,260.42$** | *$\$2,988,394.42$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$1,083,999.50$ | $\$173,439.92$ | **$\$1,098,749.42$** | **$\$3,418,937.58$** | *$\$3,056,071.58$* |
| **`BH`** | $\$2,482,023.00$ | $\$94,382.00$ | $\$2,327,641.00$ | $\$1,478,106.00$ | $\$581,910.25$ | **Assumed Allocation (75%) [E-OUT]** | $\$1,108,579.50$ | $\$177,372.72$ | **$\$759,282.97$** | **$\$1,722,740.03$** | *$\$1,628,358.03$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$896,195.75$ | $\$143,391.32$ | **$\$725,301.57$** | **$\$1,756,721.43$** | *$\$1,662,339.43$* |
| **`LLS`** | $\$11,983,654.00$ | $\$400,000.00$ | $\$9,483,654.00$ | $\$2,935,298.00$ | $\$2,370,913.50$ | **Assumed Allocation (75%) [E-OUT]** | $\$2,201,473.50$ | $\$352,235.76$ | **$\$2,723,149.26$** | **$\$9,260,504.74$** | *$\$8,860,504.74$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$564,384.50$ | $\$90,301.52$ | **$\$2,461,215.02$** | **$\$9,522,438.98$** | *$\$9,122,438.98$* |

---

### 3.4 Manitoba Service Stack (`ca_federal_pstc + ca_mb_film_video_credit`)

| Project | Gross Budget [V-IN] | Contingency Reserve [V-IN] | Open Spend Base [V-IN] | Labour Base [V-IN] | MB Credit Dollars (30%) [I-AR/E-OUT] | Netting Scenario [Provenance] | Federal Net Labour [I-AR] | Federal PSTC Dollars (16%) [I-AR/E-OUT] | Total Incentive (USD) [I-AR/E-OUT] | NPC (Verified Baseline: Unset Inclusion) [I-AR/E-OUT] | NPC (Hypothetical 0% Inclusion Sensitivity) [H-SEN] |
|:---|---:|---:|---:|---:|---:|:---|---:|---:|---:|---:|---:|
| **`LU`** | $\$4,364,395.00$ | $\$301,131.00$ | $\$4,063,264.00$ | $\$192,974.00$ | $\$1,218,979.20$ | **Assumed Allocation (70%) [E-OUT]** | $\$135,081.80$ | $\$21,613.09$ | **$\$1,240,592.29$** | **$\$3,123,802.71$** | *$\$2,822,671.71$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$0.00$ | $\$0.00$ | **$\$1,218,979.20$** | **$\$3,145,415.80$** | *$\$2,844,284.80$* |
| **`FVD`** | $\$4,517,687.00$ | $\$362,866.00$ | $\$3,701,238.00$ | $\$2,009,309.00$ | $\$1,110,371.40$ | **Assumed Allocation (70%) [E-OUT]** | $\$1,406,516.30$ | $\$225,042.61$ | **$\$1,335,414.01$** | **$\$3,182,272.99$** | *$\$2,819,406.99$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$898,937.60$ | $\$143,830.02$ | **$\$1,254,201.42$** | **$\$3,263,485.58$** | *$\$2,900,619.58$* |
| **`BH`** | $\$2,482,023.00$ | $\$94,382.00$ | $\$2,327,641.00$ | $\$1,478,106.00$ | $\$698,292.30$ | **Assumed Allocation (70%) [E-OUT]** | $\$1,034,674.20$ | $\$165,547.87$ | **$\$863,840.17$** | **$\$1,618,182.83$** | *$\$1,523,800.83$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$779,813.70$ | $\$124,770.19$ | **$\$823,062.49$** | **$\$1,658,960.51$** | *$\$1,564,578.51$* |
| **`LLS`** | $\$11,983,654.00$ | $\$400,000.00$ | $\$9,483,654.00$ | $\$2,935,298.00$ | $\$2,845,096.20$ | **Assumed Allocation (70%) [E-OUT]** | $\$2,054,708.60$ | $\$328,753.38$ | **$\$3,173,849.58$** | **$\$8,809,804.42$** | *$\$8,409,804.42$* |
| | | | | | | **Whole-Credit Lower Bound [H-SEN]** | $\$90,201.80$ | $\$14,432.29$ | **$\$2,859,528.49$** | **$\$9,124,125.51$** | *$\$8,724,125.51$* |

---

## 4. Executable Call-Path Demonstration & Code Comparison

### 4.1 Reconciliation of Current Remediation Implementation (`23c9dae5`)
Direct inspection of the active remediation checkout (`/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2` at HEAD `23c9dae5`) resolves the status of the Quebec PSTC pair:
1. **Explicit Rule Definition (`backend/app/optimization/stacking_rules.py:568-578`):**
   `_SLUG_PAIR_RULES` explicitly defines `ca_qc_pstc + ca_federal_pstc`:
   ```python
   frozenset({"ca_qc_pstc", "ca_federal_pstc"}): {
       "rule_type": "spend_reduction",
       "condition_text": (
           "Quebec film production services tax credit (SODEC fact sheet, March 2026: 25% of all-spend production costs incurred in Quebec) "
           "is not reduced by the federal PSTC (Revenu Québec CO-1029.8.36.SP note 7). The Quebec credit is assistance to the federal PSTC "
           "to the extent reasonably in respect of Canadian labour (ITA 125.5(1); CRA RC4385): it is computed on labour and qualified "
           "properties, so the labour share is its rate x the PSTC labour basis (bounded by the credit); the whole-credit figure is "
           "disclosed as the lower bound."
       ),
   }
   ```
2. **Canonical Stack Bridge Execution (`backend/app/calculators/canonical_stack_bridge.py`):**
   - `_SPEND_REDUCTION_DIRECTION[frozenset({"ca_federal_pstc", "ca_qc_pstc"})] = "ca_qc_pstc"` (line 95).
   - `PSTC_ASSISTING_SLUGS` and `PSTC_APPORTIONED_SLUGS` include `ca_qc_pstc` (lines 225, 241, 243).
   - `canonical_stack_bridge.py` prices the Quebec labour-assistance share as an explicitly assumed allocation: rate $\times$ labour basis, bounded by credit ($25\% \times \text{labour}$), and discloses the whole-credit lower bound in `disclosed_limitations`.
3. **Focused Control Assertion (`backend/tests/test_canonical_stack_bridge.py:275-288`):**
   ```python
   def test_the_federal_pstc_with_the_bc_and_quebec_credits_now_have_named_rules_and_net_the_labour_portion():
       for other in ("ca_bc_pstc", "ca_qc_pstc"):
           rule = load_named_pair_rule("ca_federal_pstc", other)
           assert rule is not None and rule["rule_type"] == "spend_reduction", other
       ...
       # Quebec: 25% of all-spend cost 1,000,000 = 250,000; labour portion = 25% x 600,000 = 150,000 -> PSTC 96,000 - 24,000 = 72,000; the whole-credit lower bound (56,000) is disclosed.
       qc = StackCandidate("ca_qc_pstc", "CA-QC", 250_000.0, 0.25, 1_000_000.0, "tax_credit")
       qc_result = price_program_pair_stack(StackCandidate("ca_federal_pstc", "CA-QC", 96_000.0, 0.16, 600_000.0, "tax_credit", rate_basis_usd=600_000.0), qc)
       assert qc_result.per_program_adjusted_usd == {"ca_federal_pstc": 72_000.0, "ca_qc_pstc": 250_000.0}
       assert any("Apportionment assumption" in n and "$56,000" in n for n in qc_result.disclosed_limitations)
   ```
4. **Stale Claim Withdrawn:** The prior AG audit claim that the Quebec PSTC pair is "blocked by absence of named rule" in the current remediation checkout is **FORMALLY WITHDRAWN AS STALE**. That finding was true of the older frozen checkout (`59566fd1`) and intermediate checkout `1406cbc3`, but was resolved by Claude in commit `60c3a3fa` / migration 0084 and verified active in HEAD `23c9dae5`.

---

### 4.2 Defect Attribution and Repair Comparison

| Feature / Stack Path | Frozen Engine 1.122 (`59566fd1`) State | Current Remediation Checkout (`23c9dae5`) State | Independent Audit Finding & Attribution |
|:---|:---|:---|:---|
| **Manitoba Federal PSTC Stack Pair** | Omitted from `_SLUG_PAIR_RULES`. `check_all_pairs` fails to price stack. | **Repaired in commit `29740f70`** (engine 1.127.0), refined in `c52e2cd7` (engine 1.128.0) and migration 0083 with mandatory limitation disclosure. | Active engine omission defect in frozen 1.122. **Repaired in remediation.** |
| **Quebec Federal PSTC Stack Pair** | Omitted from `_SLUG_PAIR_RULES`. Returns `None`. | **Repaired in commit `60c3a3fa`**, migration 0084, and rules 1.8.0 as `spend_reduction`. Prices assumed allocation ($25\% \times \text{labour}$) and discloses whole-credit bound. | Active engine omission defect in frozen 1.122. **Repaired in remediation.** Stale AG claim of engine block withdrawn. |
| **Reverse Provincial Netting** | Not modeled. | Modeled for BC (*BC ITA* s. 79(1)), QC (CO-1029.8.36.SP Note 7), and MB (MFM TC-2 Section C). | Supported by retained authority; provincial credits are not ground by federal PSTC. |
| **Producer Incurred Facts** | Assumed unverified. | Disclosed as claim-level inputs. | Genuinely empirical; remain open as claim follow-ups across all four anchors. |

---

## 5. Precise Open Items

1. **Exact Statutory Netting Allocation for All-Spend Provincial Credits (*ITA* § 125.5(1)(b)):** Neither federal *ITA* § 125.5(1)(b) nor CRA Guide RC4385 explicitly prescribes a mathematical formula for allocating an all-spend provincial credit between labour and non-labour expenditures. The current engine implementation uses an assumed allocation scenario ($rate \times \text{labour}$) and discloses the whole-credit deduction as a conservative lower-incentive bound. The definitive statutory allocation rule remains genuinely **OPEN**.
2. **Unsupported Manitoba Wording in Remediation Source Text:** Current remediation text carrying the unsupported attribution to Manitoba authority (`under this Act or under the federal Act`) must be cleaned up in `backend/app/optimization/stacking_rules.py:541-542`, `backend/alembic/versions/0083_manitoba_federal_stacking_rules.py:4-6`, `docs/architecture/CAPABILITY_LEDGER.md:4728`, and `backend/tests/test_canonical_stack_bridge.py:260`.
3. **Producer Incurred Facts:** Individual deal memos, T4 resident payroll ledgers, and CAVCO/SODEC accreditation certificates remain claim-level follow-ups across all four anchors.
