# Independent North American Hybrid & Multi-Program Audit Handoff (`FVD`, `BH`, `LU`, `LLS`)

**Audit Track:** North American Hybrid, Multi-Program & Component-Relocation Independent Audit  
**Frozen Canonical Engine Baseline:** `canonical-1.122.0`  
**Frozen Claude Remediation Commits:** `f5dc6a17858436c0809d7830151696d036aa159b` (`f5dc6a17`), `f0b042ba039ed41e619217a4ac8758ec6814eed8` (`f0b042ba`), `59566fd17463b71e9796d41e8e080bf5d0ac27ea` (`59566fd1`)  
**Saved Database Under Comparison:** `frametax2_claude_optimizer_acceptance_20260919` (`canonical-1.106.0` .. `canonical-1.110.0`)  
**Coverage Matrix Deliverable:** `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` (**1,601 rows**: 9 explicit LLS Manitoba–California artifact & contingency-election rows + 1,590 saved NA rows across all four budgets)  
**Gate Status:** `STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`

---

## 1. Executive Summary & Audit Methodology

In accordance with `PROJECT_RULES.md`, `docs/architecture/CAPABILITY_LEDGER.md`, and Codex's `CODEX_CA_GATE_REVIEW_20261011.md`, `CODEX_LLS_NA_HYBRID_LOAD_REVIEW_20261011.md`, and `CODEX_NY_CANADA_CHANGED_PATH_REVIEW_20261011.md`, this audit independently reconstructs every North American hybrid, multi-program stack, component relocation, and treaty co-production candidate across all four anchor projects (`The Little Utopia` [`LU`], `F#K Valentine's Day` [`FVD`], `Bad Hombres` [`BH`], and `Lips Like Sugar` [`LLS`]) outside the engine from retained Movie Magic budget lines (`docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json`) and dated primary statutory authority.

### Core Methodological Controls Enforced
1. **Independent Expectation First (Zero Circularity):** Every segment allocation, eligibility gate, QPE/labour base, statutory cap, uplift, government assistance deduction, line overlap (`0` shared `line_id`s across all saved hybrids), contingency treatment, and Net Production Cost (NPC) was calculated from primary statute/guidelines before comparing against `canonical-1.122.0` (`59566fd1`) and stale saved PostgreSQL rows (`1.106.0`–`1.110.0`).
2. **No Inferred Statutory Exclusion from an Absent Engine Rule:** Where `program_spend_rules.py` lacks a program-specific contingency rule (specifically `ca_mb_film_video_credit`), the engine's fallback exclusion of deployed contingency when no line-level `ContingencyAllocation` is supplied is documented as an **engine implementation behavior (`NA-HYB-DEF-04`)**, never mischaracterized as a statutory exclusion under Manitoba law.
3. **Gross Preservation & Single Adjustment Application:** Gross budget is preserved on every scenario; undeployed contingency (`planned_cost_reduction_usd`) is subtracted once from planned cost (`effective_planned_cost_usd`); and guaranteed floor credits are strictly separated from conditional upside.
4. **Claim Follow-Ups vs. Planning Scenarios:** Missing empirical claim documents (CAVCO certificates, itemized Canadian resident payroll ledgers, individual talent deal memos, hotel folio splits) prevent exact post-hoc claim verification, not explicitly labeled prospective relocation planning scenarios or deterministic statutory gate checks.

---

## 2. Priority 1 Deep-Dive: Independent Reconstruction of `LLS` Manitoba–California (`CA-MB` Principal + `US-CA` VFX)

### 2.1 Exact Saved Database Row Identities Across Generations

| Generation Label | Engine Version | Input Fingerprint | `scr.id` | `structure_id` | Saved Status | Saved CA-MB Alloc ($) | Saved US-CA Alloc ($) | Saved CA-MB Credit ($) | Saved US-CA Credit ($) | Saved Total Credit ($) | Saved True NPC ($) |
| :--- | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`LLS_110b`** (Latest) | `canonical-1.110.0` | `78ed9f199c4e5eb0...` | `914a47c0-9b1e-4d47-867f-425e6d4792fa` | `9656c441-881e-4667-bec1-8841387408ce` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |
| **`LLS_110a`** (Codex Ref) | `canonical-1.110.0` | `0ac00210e593261b...` | `51680824-eb85-4920-b124-04d0b6fce131` | `268917e8-6749-4730-9399-5a686a3f1086` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |
| **`LLS_106`** (Historical) | `canonical-1.106.0` | `0c6459528b797538...` | `0338ace0-e929-42aa-89df-fd1fe7ff629c` | `110ce2e4-f121-433b-a9ff-591ee4718b77` | `PRICED` | 11,943,654.00 | 40,000.00 | 4,249,644.30 | 14,000.00 | 4,263,644.30 | 7,720,009.70 |

* **Line Conservation & Zero Overlap Proof:** Across all three saved rows, `LLS` (`doc_id = 6ae1bbec-f8f2-432b-a09f-9d9c8833944b`, **46 active budget lines**, gross **`$11,983,654.00`**) is partitioned into **45 lines (`$11,943,654.00`)** allocated to `CA-MB` (`principal_production`) and **1 line (`4400 VISUAL EFFECTS`, `line_id = f942e378-4679-4f6f-bcb9-e5a2a210b55f`, `$40,000.00`)** allocated to `US-CA` (`vfx`). Set intersection of `line_ids` is empty (**`overlap_count = 0`**), and `$11,943,654.00 + $40,000.00 = $11,983,654.00` (`$0.00` unallocated variance).

### 2.2 Independent Statutory Analysis of the California `vfx` Leg (`$40,000.00`)

* **Dated Primary Authority:**
  1. **Prospective Relocation Rule — California Film & Television Tax Credit Program 4.0 Guidelines (California Film Commission, effective January 1, 2026; applies to allocation letters dated on or after July 1, 2025), Section II.A.1 (PDF p. 3):** A feature film (`$1,000,000` minimum production budget) is eligible **only if EITHER at least 75% of the total production budget is spent in California OR at least 75% of principal photography days occur wholly in California**.
  2. **Historical Reference Input — California Program 3.0 (Cal. Rev. & Tax. Code § 17053.98(b)(3)(A) & Cal. Code Regs. tit. 10, § 5520(a); LLS CFC Allocation Letter dated March 6, 2023):** Imposes the identical **75% California budget OR 75% California principal photography days** threshold (the 2023-03-06 letter approved LLS for a full California shoot with `$5,990,260` estimated QPE and `$1,198,052` credit at 20%, not a standalone `$40,000` VFX slice).
* **Spend Branch Evaluation:**
  $$\text{California Spend Share} = \frac{\$40,000.00}{\$11,983,654.00} = 0.00333788 \; (0.3338\%) < 75.0\%$$
  The spend branch fails by 74.67 percentage points (and `$40,000.00` is also below the `$1,000,000` minimum budget threshold if evaluated standalone).
* **Principal-Photography-Days Branch & Evidence Discipline (`CODEX_CA_GATE_REVIEW_20261011.md`):**
  - Dollar shares never establish shooting days.
  - **In this explicit modeled hybrid scenario** (`principal_production` placed in `CA-MB`, only `vfx` placed in `US-CA`), 100% of modeled principal photography is placed outside California (`0% < 75%`), so the California leg fails the project eligibility gate (**`PROJECT_ELIGIBILITY_GATE_FAILED`**; `$0.00` credit).
  - **Mixed / Unmodeled Shoot Distinction:** If a structure does not model principal photography placement (or splits principal photography without day counts) and lacks producer-stated `ca_principal_photography_days_in_california_pct`, the gate is **`CONDITIONAL`** (`$0.00` guaranteed floor; conditional upside requires producer day confirmation), never a false pass.
  - **VFX Uplift Distinction (CFC Program 4.0 Guidelines § III.B.1):** Even if the project gate were satisfied, the `+5%` VFX uplift requires either $\ge \$10,000,000$ in California VFX QPE or $\ge 75\%$ of worldwide VFX costs incurred in California (`$40,000 / $40,000 = 100%` of VFX, which is a conditional subset uplift on top of a valid base credit, never a substitute for the Section II.A.1 project eligibility gate).

### 2.3 Independent Statutory Analysis of the Manitoba `principal_production` Leg (`$11,943,654.00`)

* **Dated Primary Authority:**
  - **Manitoba Income Tax Act (C.C.S.M. c. I10, ss. 7.5–7.9, current from July 1, 2026 to October 8, 2026)** and **Manitoba Film & Video Production Tax Credit Guidelines (Manitoba Film & Music, June 2024)**.
* **Account-by-Account Classification of the 45 Manitoba Budget Lines (`$11,943,654.00`):**
  1. **Statutorily Excluded Financing Costs (`$1,700,000.00`):** `6500 FINANCING FEES` (`$450,000.00`) + `6600 BRIDGE` (`$250,000.00`) + `6700 BANKING FEE` (`$1,000,000.00`) = **`$1,700,000.00`** (`finance_costs`, statutorily excluded under s. 7.5(1)).
  2. **Unconfirmed Residuals Reserve (`$400,000.00` — Distinct from `7100 Contingency`):** `6800 RESIDUALS RESERVE` (`line_id = 57f49d6e-62f6-4bb6-8fb6-48bfee057a79`, **`$400,000.00`**, `residuals_reserve`). Excluded from the confirmed QPE floor (`GREY_AREA_REQUIRES_AUTHORITY`) until actual residual payments are incurred; **never part of the user contingency utilization election (`inputs.contingency_reserve_usd`)**.
  3. **Contingency Reserve (`$400,000.00`):** `7100 Contingency` (`line_id = 6f18b074-bc09-466f-a40b-52c79bde9be3`, **`$400,000.00`**, `contingency`, `inputs.contingency_reserve_usd = $400,000.00`). Undeployed reserve is statutorily excluded under Manitoba ITA s. 7.5(1)(g)–(h); deployed contingency actually spent on eligible Manitoba production costs is statutorily eligible under s. 7.5(1).
  4. **Remaining Manitoba Production Cost Pool (`$9,443,654.00` across 40 lines; `$9,483,654.00` if `4400 VISUAL EFFECTS` `$40,000.00` is retained in Manitoba):**
     - **ATL Accounts (`1100–1400` + `1900` Fringes = `$3,114,414.00`):** `1100 SCRIPT` (`$314,153`), `1200 PRODUCERS` (`$1,414,198`), `1300 DIRECTION` (`$267,384`), `1400 CAST` (`$863,388`), `1900 Total Fringes` (`$255,291`). Under Manitoba ITA s. 7.5(1), under the 30% Cost-of-Production stream, non-resident ATL fees qualify only to the extent they are eligible service contract expenditures for services performed in Manitoba or deemed eligible non-resident salaries (technical crew with Manitoba trainees).
     - **ATL Travel & Living (`1500 ATL TRAVEL & LIVING = $60,561.00`):** Admitted in the engine's `$9,443,654.00` `OPEN_DEFAULT_INCLUDE` base; statutorily under Manitoba ITA s. 7.5(1) (`"eligible accommodation expenditure"`), accommodation in Manitoba is capped at **`$300.00` per night** per unit and requires Manitoba travel/hotel folios. Excluding `$60,561.00` pending hotel folios yields a strict physical/local Manitoba base of **`$9,383,093.00`** (`30%` credit = **`$2,814,927.90`**, `-$18,168.30`).
     - **BTL Production, Post-Production, Music, Legal (`6300 $150,000`), Insurance (`6400 $200,000`), and Completion Bond (`7200 $115,000`):** Total **`$6,268,679.00`** (`$9,443,654.00` combined with ATL).
* **Two-Stream Statutory Calculation & Comparison (Manitoba ITA s. 7.6(2)–(6)):**
  - **Stream A — 30% Cost-of-Production Credit (Manitoba ITA s. 7.6(6)):**
    $$\text{Credit}_{\text{Stream A}} = 0.30 \times A + 0.08 \times B$$
    where $A$ is eligible Manitoba production costs (`$9,443,654.00` on the 45-line hybrid allocation; `$9,483,654.00` on the 46-line all-Manitoba allocation) and $B$ equals $A$ **only if** the film is co-produced with an eligible Manitoba production corporation that owns voting shares (`s. 7.6(6)`).
    * **Guaranteed 30% Base (Artifact 2, 45 lines):** $0.30 \times \$9,443,654.00 = \mathbf{\$2,833,096.20}$ (Strict base excluding `$60,561` unsplit ATL travel = **`$2,814,927.90`**).
    * **Conditional +8% Manitoba Co-Producer Upside:** $0.08 \times \$9,443,654.00 = \mathbf{+\$755,492.32}$ (38% ceiling = **`$3,588,588.52`**; requires Manitoba co-producer voting-share agreement).
    * **Statutory Corporate Prerequisite (`s. 7.5(1)(d)`):** Stream A requires an eligible corporation where at least **25% of T4 salaries and wages** paid for work on the eligible film are paid to eligible Manitoba employees.
  - **Stream B — 45% Cost-of-Salaries Credit (Manitoba ITA s. 7.6(2)–(5)):**
    $$\text{Credit}_{\text{Stream B}} = (0.45 + \underbrace{0.10}_{\text{Frequent}} + \underbrace{0.05}_{\text{MB Producer}} + \underbrace{0.05}_{\text{Rural/North}}) \times (L_{\text{MB resident}} + L_{\text{deemed non-resident}})$$
    where deemed non-resident technical labour is capped at **30%** of resident salaries (if $\ge 2$ Manitoba resident trainees are employed per non-resident department) or **10%** (if $1$ trainee is employed) under `s. 7.5(1)(d)`, and the `+10%`/`+5%`/`+5%` bonuses apply to the entire eligible salary base including deemed non-resident salaries.
    * In `canonical-1.122.0`, lines mapped to `component_basis_spend_categories` (`1100` `$314,153` + `1200` `$1,414,198` + `1300` `$267,384` + `1400` `$863,388` + `3100 MAKEUP & HAIR` `$76,175`) sum to **`$2,935,298.00`** $\to$ 45% base = **`$1,320,884.10`** (65% ceiling = **`$1,907,943.70`**), because BTL department accounts (`2000–3900` except `3100`) are classified as `miscellaneous` / `payroll_fringes` (`NA-HYB-DEF-03`).
    * Even if 100% of identifiable direct BTL labor + fringes (`$1,998,678.00`) plus ATL (`$3,114,414.00`) = `$5,113,092.00` were Manitoba resident salaries, $0.45 \times \$5,113,092.00 = \$2,300,891.40 < \$2,833,096.20$. Thus **Stream A (30% Cost-of-Production = `$2,833,096.20`) governs the planning floor**.
  - **Why the Stale Saved DB Row (`$4,249,644.30` MB / `$4,263,644.30` Total) Was Wrong:**
    * In `canonical-1.106.0` and `canonical-1.110.0`, the engine multiplied the **45% Cost-of-Salaries rate** against the **all-spend Cost-of-Production base** (`0.45 × $9,443,654.00 = $4,249,644.30`) and added an ineligible `$14,000.00` California VFX credit (`0.35 × $40,000.00`), overstating the credit by **`+$1,430,548.10`** against Artifact 2 (`$2,833,096.20`) and **`+$1,418,548.10`** against Artifact 3 (`$2,845,096.20`).

### 2.4 Separation of the Three Distinct `LLS` Manitoba–California Artifacts

| Artifact ID & Name | Structure Type | Jurisdiction Allocation | Eligibility / Status | Confirmed QPE Floor ($) | Guaranteed Credit Floor ($) | Conditional Credit Upside ($) | Unadjusted NPC at `NOT_STATED` ($) | Variance vs Stale DB (`$4,263,644.30`) |
| :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: |
| **Artifact 1: Retained Hybrid** (`CA-MB` Principal + `US-CA` VFX) | `hybrid` (`ordinary_component_hybrid`) | `CA-MB`: `$11,943,654.00` (45 lines)<br>`US-CA`: `$40,000.00` (1 line `4400`) | **`GATE_REJECTED`** (`PROJECT_ELIGIBILITY_GATE_FAILED` on `US-CA` leg) | 0.00 | **0.00** | 0.00 | **11,983,654.00** | **+4,263,644.30** (Stale row invalidly priced) |
| **Artifact 2: Same-Allocation Manitoba Leg Sensitivity** (`CA-MB` on 45 lines; `US-CA` VFX earns `$0`) | `hybrid_leg_sensitivity` | `CA-MB`: `$11,943,654.00` (45 lines)<br>`US-CA`: `$40,000.00` (uncredited `$0`) | **`PRICED`** (Manitoba 30% Stream A) | 9,443,654.00 | **2,833,096.20** | +755,492.32 (`+8%` co-prod)<br>+120,000.00 (`30%` of `$400k` cont.) | **9,150,557.80** | **+1,430,548.10** (`$4,249,644.30` MB leg + `$14k` CA leg) |
| **Artifact 3: Relocated All-Manitoba Single-Jurisdiction Alternative** (`100%` in `CA-MB` incl. `$40,000` VFX) | `single_country` (`full_relocation`) | `CA-MB`: `$11,983,654.00` (all 46 lines incl. `4400 VFX`) | **`PRICED`** (Manitoba 30% Stream A) | 9,483,654.00 | **2,845,096.20** | +758,692.32 (`+8%` co-prod)<br>+120,000.00 (`30%` of `$400k` cont.) | **9,138,557.80** | **+1,418,548.10** (vs `$4,263,644.30` hybrid) / **+1,422,548.10** (vs `$4,267,644.30` stale all-MB row) |

### 2.5 Four-Election Contingency Matrix (`NOT_STATED`, `0%`, `50%`, `100%` on `7100 Contingency = $400,000.00`)

> [!IMPORTANT]
> **Statutory vs. Engine Contingency Distinction (Correcting Claude's `LLS_MB_CA_RECONSTRUCTION_20261011.md` Line 21):**
> Claude's reconstruction note stated: *"Manitoba has no program-specific contingency rule, so the 400,000 contingency line is excluded from Manitoba QPE under every election."* That statement describes **only** the engine's current code in `qualification_derivation.py` (line 490) and `program_spend_rules.py` (which has no `SpendRule` for `ca_mb_film_video_credit`, causing `contingency_allowance_pct` to remain `None` when line-level `ContingencyAllocation` is not passed). **It is NOT a statutory exclusion under Manitoba law.**
> Under **Manitoba Income Tax Act s. 7.5(1)**:
> 1. **Undeployed contingency reserve** (`$400,000` at `0%`, `$200,000` at `50%`, `$0` at `100%`) is not incurred/paid and is statutorily excluded from QPE (`s. 7.5(1)(g)–(h)`), while reducing planned production cost once (`planned_cost_reduction_usd`).
> 2. **Deployed contingency actually spent on eligible Manitoba production costs** (`$200,000` at `50%`, `$400,000` at `100%`) **IS statutorily eligible** under Manitoba ITA s. 7.5(1), generating **`+$60,000.00`** credit at `50%` (`$2,893,096.20` on Artifact 2; `$2,905,096.20` on Artifact 3) and **`+$120,000.00`** credit at `100%` (`$2,953,096.20` on Artifact 2; `$2,965,096.20` on Artifact 3). This missing engine rule is logged as active defect **`NA-HYB-DEF-04`**.

| Contingency Election (`7100` = `$400,000`) | Deployed Contingency ($) | Planned Cost Reduction (`planned_cost_reduction_usd`) ($) | Effective Planned Cost ($) | Artifact 2 Engine Floor QPE / Credit / NPC ($) | Artifact 2 Statutory Deployed-to-Eligible QPE / Credit / NPC ($) | Artifact 3 Engine Floor QPE / Credit / NPC ($) | Artifact 3 Statutory Deployed-to-Eligible QPE / Credit / NPC ($) | Conditional Contingency Upside ($) |
| :--- | ---: | ---: | ---: | :--- | :--- | :--- | :--- | ---: |
| **`NOT_STATED`** | 0.00 | 0.00 | **11,983,654.00** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **9,150,557.80** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **9,150,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **9,138,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **9,138,557.80** | 120,000.00 |
| **`0%`** | 0.00 | 400,000.00 | **11,583,654.00** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **8,750,557.80** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **8,750,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **8,738,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **8,738,557.80** | 0.00 |
| **`50%`** | 200,000.00 | 200,000.00 | **11,783,654.00** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **8,950,557.80** | QPE: 9,643,654.00<br>Inc: **2,893,096.20**<br>NPC: **8,890,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **8,938,557.80** | QPE: 9,683,654.00<br>Inc: **2,905,096.20**<br>NPC: **8,878,557.80** | 0.00 |
| **`100%`** | 400,000.00 | 0.00 | **11,983,654.00** | QPE: 9,443,654.00<br>Inc: **2,833,096.20**<br>NPC: **9,150,557.80** | QPE: 9,843,654.00<br>Inc: **2,953,096.20**<br>NPC: **9,030,557.80** | QPE: 9,483,654.00<br>Inc: **2,845,096.20**<br>NPC: **9,138,557.80** | QPE: 9,883,654.00<br>Inc: **2,965,096.20**<br>NPC: **9,018,557.80** | 0.00 |

---

## 3. Priority 2: Full Four-Anchor North American Hybrid & Multi-Program Coverage (`LU`, `FVD`, `BH`, `LLS`)

### 3.1 Movable Component Slices Across the Four Anchor Budgets (Source-Line Verified)

| Project | Controlling Gross Budget ($) | `post` Only (`post_production` excl. Music) ($) | `vfx` (`4400`/`4600`/`6100`) ($) | `music_package` (`4600`/`5100`/`6000`) ($) | `post_vfx_package` (`post + vfx`) ($) | `post_vfx_music_package` (`post + vfx + music`) ($) | `contingency` Reserve ($) | Other Excluded / Grey Lines ($) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **`LU`** | 4,364,393.00<br>*(Leaf: 4,364,395.00)* | 9,068.00<br>*(`5000 EDITORIAL`, stated outside in LA)* | 52,500.00<br>*(`6100 VFX DEPT`)* | 0.00<br>*(`6000 MUSIC = $0`)* | 61,568.00<br>*(or `9,068.00` when `vfx` split)* | 61,568.00 | 301,131.00<br>*(`8300`, 100% stated)* | `1600` ATL Travel `$397,279`; `3900` BTL Travel `$438,254`; `7000` Admin `$297,593`; `7100` Publicity `$24,348`; `7200/8100` Ins. `$60,555` |
| **`FVD`** | 4,517,687.00 | 146,446.00<br>*(`5000, 5200, 5400, 5600, 5700`)* | 10,000.00<br>*(`4600 VISUAL EFFECTS`)* | 10,200.00<br>*(`5100 MUSIC`)* | 156,446.00<br>*(or `146,446.00` when `vfx` split)* | 166,646.00<br>*(or `156,646.00` when `vfx` split)* | 362,866.00<br>*(`7902 CONTINGENCY`)* | `7901` Finance `$453,583` (`EXCLUDED`); `1500` ATL Travel `$100,000`; `7100` Legal `$50,000`; `7200` Ins. `$100,000`; `7905` Bond `$65,000` |
| **`BH`** | 2,482,023.00 | 107,958.00<br>*(`4300, 4500, 4700, 4800`)* | 0.00 | 5,000.00<br>*(`4600 MUSIC`)* | 107,958.00 | 112,958.00 | 94,382.00<br>*(`CONTINGENCY`)* | `6700` Legal `$15,000`; `6800` Ins. `$45,000`; `1500` ATL Travel `$54,000`; `6600` Gen. Expense `$83,850` |
| **`LLS`** | 11,983,654.00 | 611,230.00<br>*(`3700, 4500, 4700, 4800, 4900, 5800`)* | 40,000.00<br>*(`4400 VISUAL EFFECTS`)* | 206,774.00<br>*(`4600 MUSIC`)* | 651,230.00<br>*(or `611,230.00` when `vfx` split)* | 858,004.00<br>*(or `818,004.00` when `vfx` split)* | 400,000.00<br>*(`7100 Contingency`)* | `6500-6700` Financing `$1,700,000` (`EXCLUDED`); `6800` Residuals Reserve `$400,000` (`GREY_AREA`); `7200` Bond `$115,000`; `6300` Legal `$150,000`; `6400` Ins. `$200,000` |

### 3.2 Saved Database NA Row & Aggregate Inventory by Generation

| Generation | Engine Version | Saved NA `scr` Rows | `PRICED` Hybrids | `PRICED` Multi-Program Stacks | `PRICED` Component Relocations | `DOMINATED_WITH_PROOF` Hybrids | `CO_PRO_OPPORTUNITY` Treaty Rows | `evaluation_candidate_aggregates` Groups | Total NA Candidates Represented in Aggregates |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`LU`** | `canonical-1.109.0` | **180** | 75 | 3 | 0 | 102 | 0 | 156 | 79,566 (`PRICED`: 70,401; `RULE_REJECTED`: 9,165) |
| **`LU_106`** | `canonical-1.106.0` | **190** | 79 | 3 | 0 | 108 | 0 | 163 | 87,220 (`PRICED`: 77,334; `RULE_REJECTED`: 9,886) |
| **`FVD`** | `canonical-1.109.0` | **477** | 148 | 5 | 0 | 324 | 0 | 517 | 485,544 (`PRICED`: 100,133; `RULE_REJECTED`: 385,411) |
| **`BH`** | `canonical-1.109.0` | **368** | 141 | 3 | 58 | 141 | 25 | 706 | 2,361 (`PRICED`: 2,283; `RULE_REJECTED`: 78) |
| **`LLS_110b`** | `canonical-1.110.0` | **553** | 166 | 3 | 48 | 311 | 25 | 448 | 470,299 (`PRICED`: 469,701; `RULE_REJECTED`: 598) |
| **`LLS_110a`** | `canonical-1.110.0` | **555** | 166 | 5 | 48 | 311 | 25 | 478 | 471,137 (`PRICED`: 470,509; `RULE_REJECTED`: 628) |
| **`LLS_106`** | `canonical-1.106.0` | **570** | 171 | 5 | 49 | 320 | 25 | 491 | 499,373 (`PRICED`: 498,729; `RULE_REJECTED`: 644) |

### 3.3 Disposition Breakdown of All 662 Saved `PRICED` NA Rows (`LU`, `FVD`, `BH`, `LLS_110b` + Historical `PRICED` Extras)

| Audit Disposition Classification | Row Count | Description & Reconciliation Summary |
| :--- | ---: | :--- |
| `REPAIRED_IN_1122_STALE_IN_DB (RULE_REJECTED)` | **485** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `LEGACY_COMPONENT_RELOCATION_SUPERSEDED_BY_ORDINARY_HYBRID` | **107** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `REPAIRED_IN_1122_STALE_IN_DB (GATE_REJECTED)` | **46** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `NOT_ESTABLISHED_EMPIRICAL_GAP (MISSING_CANADIAN_PAYROLL_AND_OCASE_VFX_LABOUR_SPLIT)` | **6** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `OPEN_CODE_DEFECT (UNLAWFUL_CPTC_DOMESTIC_PLUS_QC_PSTC_SERVICE_STACK)` | **4** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `REPAIRED_ASSISTANCE_FORMULA_PENDING_CAVCO_AND_PAYROLL (NA-HYB-DEF-03 / NA-HYB-DEF-05)` | **4** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `REPAIRED_IN_1122_STALE_IN_DB (ANCHOR_OR_COMPONENT_RATE_UPDATED)` | **4** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `REPAIRED_IN_1122_STALE_IN_DB (BC_DAVE_LABOUR_BASIS_REQUIRES_VFX_LABOUR_LINES)` | **4** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `OPEN_CODE_DEFECT (NA-HYB-DEF-01 (US-AL $500k Min Spend Omitted & 35% Resident Payroll Rate Applied to All Spend))` | **1** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `OPEN_CODE_DEFECT (NA-HYB-DEF-01 (US-HI $100k/$200k Min Spend Omitted))` | **1** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `OPEN_CODE_DEFECT (NA-HYB-DEF-01 (US-MN $1M Min Spend Omitted))` | **1** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| `OPEN_CODE_DEFECT (NA-HYB-DEF-01 (US-PA 60% Total Production Expense Gate Omitted))` | **1** | Reconciled in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv` with exact saved IDs, `1.122.0` comparison, and statutory basis. |
| **Total Saved `PRICED` NA Rows Audited** | **664** | Plus **928** `DOMINATED_WITH_PROOF` / `CO_PRO_OPPORTUNITY` rows and **9** explicit `LLS` MB–CA artifact/contingency rows = **1,601 total matrix rows**. |

---

## 4. Reconciliation of Verified `canonical-1.122.0` Repairs vs. Active Hybrid Code Defects

### 4.1 Verified Repairs in `canonical-1.122.0` (`f5dc6a17` / `f0b042ba` / `59566fd1`) (Stale in Saved DB)

1. **`US-CA` (`ca_film_30`) 75% Project Eligibility Gate (`project_eligibility_gates.py`):**
   - Saved DB rows (`1.106.0`–`1.110.0`) priced standalone California `vfx`, `music_package`, and `post_vfx_package` slices (`$5,000` on `BH`, `$9,068` on `LU`, `$10,000`/`$10,200` on `FVD`, `$40,000`/`$206,774` on `LLS`, `$107,958` on `BH`) at 35% when 100% of principal photography was modeled outside California.
   - In `canonical-1.122.0` (`f5dc6a17` / `f0b042ba`), `evaluate_project_gate` rejects all such modeled hybrid scenarios with `PROJECT_ELIGIBILITY_GATE_FAILED`, distinguishes mixed/unmodeled shoots as `CONDITIONAL` (`$0` floor), and respects producer-stated `ca_principal_photography_days_in_california_pct`.
2. **`CA-ON` (`on_ofttc`) & `CA-NS` (`ca_ns_production_incentive_fund`) Labour-Only Component Bases (`program_rate_rules_worldwide.py`):**
   - Saved DB rows priced `on_ofttc` at 35% and `ca_ns_production_incentive_fund` at 25% on 100% of non-labour `vfx`, `music_package`, and `post_vfx_package` slices, and on 100% of anchor spend.
   - In `canonical-1.122.0` (since `1.115.0`), both restrict their base to `component_basis_spend_categories` (labour-only), so non-labour routed components fail closed (`executable=False`, `$0` labour).
3. **`CA-NB` (`ca_nb_film_tax_credit`), `MX` (`mx_federal_film_incentive_2026`), & `US-NC` (`us_nc_film_entertainment_grant`) Discretionary Ceilings:**
   - Saved DB rows priced `CA-NB` (at 25%/30% floor) and `MX`/`US-NC` (in `1.106.0` at 30%/25% floor) as guaranteed hybrid anchors and routed components.
   - In `canonical-1.122.0` (`1.107.0`–`1.120.0`), all three are floorless discretionary ceilings (`executable=False` without confirmed award), and `MX` enforces its native `MXN 40,000,000` (`~$2.29M USD`) minimum spend.
4. **`CA-MB` (`ca_mb_film_video_credit`) Two-Stream Comparison (30% Cost-of-Production vs. 45% Cost-of-Salaries):**
   - Saved DB rows multiplied the 45% salary rate by the all-spend production cost base (`$4,249,644.30` on `LLS` MB–CA).
   - In `canonical-1.122.0` (`1.117.0`/`1.120.0`), Manitoba anchor legs compare the 45% salary stream (`$1,320,884.10` on `LLS`) against the 30% Cost-of-Production stream (`$2,833,096.20` on `LLS` when `$40k` VFX is routed out; `$2,783,064.00` when `$206.77k` music is routed out; `$2,771,064.00` when music+VFX are routed out; `$2,649,727.20` when post+VFX are routed out; `$2,587,695.00` when post+VFX+music are routed out).
5. **Canadian Federal CPTC Assistance Deduction (`canonical_stack_bridge.py`):**
   - Saved DB rows deducted provincial credits (`on_ofttc`, `ca_qc_pstc`) directly from CPTC labour. Repaired in `1.119.0` so provincial assistance reduces the production cost base that sets the 60% cap (`0.60 × (G_net - Assistance)` per CRA Form T1131 lines 421–430).

### 4.2 Active Code Defects Verified in `canonical-1.122.0` (`59566fd1`) on North American Hybrids

| Defect ID | Affected Programs & Files | Statutory Authority Violated | Exact Mechanism & Dollar Impact on Four Anchor Budgets |
| :--- | :--- | :--- | :--- |
| **`NA-HYB-DEF-01`** | **Unmodeled Statutory Minimum Spend & Project-Share Gates on US State Routed Components**<br>(`US-MN`, `US-PA`, `US-MA`, `US-RI`, `US-AL`, `US-CO`, `US-HI`, `US-OK`, `US-UT`, `US-VA`, `US-AZ`)<br>`program_rate_rules_worldwide.py` & `project_eligibility_gates.py` | • **MN:** Minn. Stat. § 116U.27 (`$1M` min spend)<br>• **PA:** 72 P.S. § 8712-D(b) (`>=60%` of total production expenses in PA)<br>• **MA:** M.G.L. c. 62 § 6(l) (`>75%` budget or days for non-payroll Production Expense Credit)<br>• **RI:** R.I. Gen. Laws § 44-31.2-2(9) (`>=51%` principal photography in RI + `$100k` min)<br>• **AL:** Ala. Code § 41-7A-43 (`$500k` min spend; 35% only on resident payroll, 25% on general spend)<br>• **CO/HI/OK/UT/VA/AZ:** Statutory minimums (`$100k`–`$1M`) | In `canonical-1.122.0`, routing small standalone components (`$5,000` BH music, `$9,068` LU post, `$10,000` FVD VFX, `$10,200` FVD music, `$40,000` LLS VFX, `$107,958` BH post, `$206,774` LLS music) **still prices (`executable=True`)** in these US states because `min_qpe_usd=None` in `program_rate_rules_worldwide.py` and PA/MA/RI are omitted from `project_eligibility_gates.py`. Furthermore, `us_al_film_incentive` has `is_band_ceiling=False` and `is_component_basis=False` on `us-al-resident-payroll-35`, applying **35%** (resident payroll rate) instead of **25%** to 100% of non-payroll spend on both anchor and routed component legs! |
| **`NA-HYB-DEF-02`** | **Unreachable Manitoba 30% Cost-of-Production Election When Segment `atl_*`/`btl_*` Labour is `$0`**<br>(`ca_mb_film_video_credit`)<br>`allocation_pricing.py` L1357 vs L1759 | Manitoba ITA s. 7.6(6) (30% Cost-of-Production stream) & s. 7.5(1)(d) (25% Manitoba T4 corporate wage test) | In `allocation_pricing.py`, `_ALTERNATIVE_ELECTION_PROGRAMS["ca_mb_film_video_credit"]` (30% Cost-of-Production election at line 1759) is placed **after** the `resolve_program_rate` gate at line 1357 (`ca-mb-base-45`, which requires `ca_mb_qualified_labour_usd >= 0.01` from `atl_*`/`btl_*` categories). Whenever a segment has `$0` in `atl_*`/`btl_*` categories (e.g. a post/VFX segment), `price_segment` exits with `executable=False` at line 1365 before reaching line 1759. |
| **`NA-HYB-DEF-03`** | **BTL Department Labour Misclassified as `miscellaneous` / `payroll_fringes` Omitted from Labour-Only Bases**<br>(`ca_federal_cptc`, `ca_federal_pstc`, `on_ofttc`, `ca_bc_pstc`, `ca_ns_production_incentive_fund`, `ca_mb_film_video_credit` 45% stream)<br>`canadian_labour_basis.py` & `classify_budget_line_items.py` | ITA §§ 125.4, 125.5; Ontario Taxation Act § 43; Manitoba ITA s. 7.6(2) | Across `LU`, `FVD`, `BH`, and `LLS`, physical BTL crew department accounts (`2000 PRODUCTION STAFF`, `2200 ART DIRECTION`, `3200 ELECTRIC`, `3300 CAMERA`, etc.) are classified as `miscellaneous` and `1900/4900/5900` as `payroll_fringes`. `component_basis_spend_categories` includes only `atl_*` and `btl_crew_labor` (`3100 MAKEUP & HAIR` on LLS), admitting 100% of non-resident ATL while omitting BTL crew accounts unless line-level labour facts (`line_fact:{line_id}:*`) are supplied. |
| **`NA-HYB-DEF-04`** | **Absent Manitoba Contingency Rule in `program_spend_rules.py` Excludes Deployed Contingency at `50%`/`100%`**<br>(`ca_mb_film_video_credit`)<br>`program_spend_rules.py` & `qualification_derivation.py` L490 | Manitoba ITA s. 7.5(1) (`"eligible production costs"`) | Because `program_spend_rules.py` has no `SpendRule` for `ca_mb_film_video_credit`, `contingency_allowance_pct` is `None`. When a producer sets `contingency_expected_utilization_pct` to `50%` or `100%` without a line-level `ContingencyAllocation`, `qualification_derivation.py` (line 490) keeps 100% of deployed contingency `EXCLUDED`, understating the statutory Manitoba 30% credit by **`-$60,000.00`** at `50%` and **`-$120,000.00`** at `100%` on `LLS` (and **`-$90,339.30`** on `LU` where `100%` utilization is persisted). |
| **`NA-HYB-DEF-05`** | **Inconsistent CPTC 60% Production-Cost Cap Base Between `price_segment` (`0.60 × Gross`) and `canonical_stack_bridge` (`0.60 × Net`) & Unlawful `ca_federal_cptc + ca_qc_pstc` Stack**<br>`allocation_pricing.py` L1318 & `canonical_stack_bridge.py` L378 | ITA § 125.4(1) (60% of net production cost) & Quebec Taxation Act (QPRDP domestic vs PSTC service regime) | (1) `price_segment` sets CPTC's 60% cap to `0.60 × gross_budget_usd` (`$1,489,213.80` on `BH`, including `$94,382` unspent contingency and `$60,000` excluded legal/insurance), whereas `canonical_stack_bridge.py` sets `production_cost_usd` to `allocated - excluded - unresolved` (`$2,327,641.00` on `BH`, `0.60 × net = $1,396,584.60`). On `BH` (`L = $1,478,106`), this causes `price_segment` to overstate standalone CPTC by **`+$20,380.35`** (`$369,526.50` vs `$349,146.15`) and causes `canonical_stack_bridge` to misattribute that `$20,380.35` to provincial assistance `stacking_reduction_usd` (`$97,980.91` on `CA-ON`, `$107,666.89` on `CA-QC`). (2) `ca_federal_cptc` (domestic) + `ca_qc_pstc` (foreign/service credit) is an unlawful cross-regime stack still priced in `1.122.0`. |
| **`NA-DEFECT-01`** | **New York § 24(b)(1) 40% Aggregate ATL Ceiling Omitted on NY Hybrid Anchors**<br>(`ny_state_film`)<br>`program_spend_rules.py` L193 | NY Tax Law § 24(b)(1) (eligible ATL cannot exceed 40% of other qualified production costs) | Affects all 26 saved `US-NY` anchor hybrids across `LU`, `FVD`, `BH`, and `LLS`. Even when post/VFX/music components are routed out of NY, the remaining NY `principal_production` anchor admits 100% of uncapped ATL without applying the 40% aggregate BTL+Post cap. |

---

## 5. Disclosed Planning Conditions & Remaining Production Evidence Follow-Ups

In accordance with `PROJECT_RULES.md`, the following empirical items are documented as **statutory claim follow-ups** (required to substantiate a post-hoc tax credit filing) and **disclosed planning conditions** (never used as an excuse to halt deterministic rule checks or fabricate inputs):

1. **Manitoba Co-Producer & Corporate/Residency Schedules (`ca_mb_film_video_credit`):**
   - **30% Cost-of-Production Stream (`s. 7.6(6)` & `s. 7.5(1)(d)`):** Requires an eligible Manitoba corporation paying $\ge 25\%$ of T4 salaries/wages to eligible Manitoba employees, hotel folios for `1500 ATL TRAVEL & LIVING` (`$60,561.00` on `LLS`) to enforce the `$300/night` accommodation cap (`s. 7.5(1)`), and Manitoba service-contract/place-of-performance documentation for non-resident ATL fees. The `+8%` Manitoba Co-Producer bonus (`+$755,492.32` on Artifact 2; `+$758,692.32` on Artifact 3) remains conditional on an executed Manitoba co-producer voting-share agreement.
   - **45% Cost-of-Salaries Stream (`s. 7.6(2)–(5)`):** Requires itemized Manitoba resident payroll ledgers and Manitoba trainee logs (1 trainee for 10% deemed non-resident cap; $\ge 2$ trainees for 30% cap under `s. 7.5(1)(d)`).
2. **California Shooting-Day Evidence (`ca_film_30`):**
   - Under CFC Program 4.0 Guidelines (Jan 1, 2026) § II.A.1, any hybrid structure spending $< 75\%$ of its total budget in California requires $\ge 75\%$ of principal photography days in California (`ca_principal_photography_days_in_california_pct >= 75.0`). Where modeled principal photography is placed outside California (such as `LLS` Manitoba–California), the scenario is deterministically `GATE_REJECTED`.
3. **Canadian CAVCO Certification & Resident Payroll Schedules (`ca_federal_cptc`, `on_ofttc`, `ca_federal_pstc`, `on_opstc`, `ca_bc_pstc`, `ca_bc_dave`, `ocase`):**
   - CAVCO Part A/B certificates and itemized Canadian/provincial resident payroll schedules remain claim follow-ups; planning scenarios must use line-level labour facts rather than raw topsheet category defaults.
4. **US Per-Person Salary Schedules (`ny_state_film`, `us_ga_film_credit`, `us_il_film_production_services_credit`, `us_ma_film_tax_credit`) & `LU` Travel/Lodging Split:**
   - Individual deal memos (`$500k` cap in NY/GA/IL, `$1M` cap in MA, 2-producer limit in NY) and `LU` Account `3900` (`$438,254.00`) in-state lodging vs. foreign airfare schedules remain claim follow-ups.

> [!IMPORTANT]
> **HANDOFF CONCLUSION:**
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
> All four anchor budgets (`LU`, `FVD`, `BH`, `LLS`) have been independently audited across all 1,590 saved North American hybrid, multi-program, component-relocation, and treaty rows plus the 9 explicit `LLS` Manitoba–California artifact and contingency-election scenarios (**1,601 rows** in `NORTH_AMERICAN_HYBRID_COVERAGE_MATRIX.csv`). No Rest-of-World (ROW) expansion has been started.
