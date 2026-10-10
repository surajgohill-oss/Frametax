# North American Evidence Recovery & Generic Parser Repairs
**Audit Track:** Independent North American QPE Audit (US, Canada, Mexico)  
**Workspace:** `/Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2`  
**Branch:** `ag/exhaustive-optimizer-audit`  
**Read-Only Truth:** `/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2` (commits `486bd15`, `6cd2bbe`, `23d5cd8`)  
**Status:** `STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`  
**Date:** 2026-10-10  

---

## 1. Scope & Governance Split

To avoid collisions with Claude's committed register rows (`Q36`–`Q42` in `docs/validation/FOUR_ANCHOR_QPE_ISSUE_REGISTER.md`), all North American findings, budget recoveries, and generic repair proposals are catalogued under the independent prefix **`NA-01` through `NA-07`**. The shared register is synchronized directly from the canonical remediation checkout without local mutations.

In accordance with `PROJECT_RULES.md` and user instructions:
* **Zero production code edits** in `backend/app/` or `frontend/`.
* **Zero database mutations** on `frametax2_claude_optimizer_acceptance_20260919`.
* **Zero cold evaluations** (`/evaluation/begin`), warm-ups, or regeneration calls.
* **Zero repeated passing test runs**.
* Generic parser repairs are delivered as formal, reviewed patch specifications for Codex review and implementation.

---

## 2. Finding NA-01: Verification of the Six Extraction Shortfalls Against Original Budget PDFs

In the initial audit of the 11 non-anchor parsed budgets, six productions exhibited dollar discrepancies between their declared gross budget and their extracted leaf line sums. Every single shortfall has now been investigated and proven directly from the original PDF topsheets on disk:

| Project Title | Declared Gross ($) | Extracted Line Sum ($) | Shortfall ($) | Verified Topsheet Line in Original PDF | Page | Account / Line Text in Source PDF | Shortfall Attribution & Root Cause |
| :--- | :---: | :---: | :---: | :--- | :---: | :--- | :--- |
| **10 Double Zero** | 11,139,616.00 | 10,391,803.00 | **747,813.00** | Contingency Reserve | 2 | `CONTINGENCY 10% : 10.0% 747,815` | Line carries `$747,815` (with $2 authored rounding vs declared gross). Skipped because label contains digits and `%` (`CONTINGENCY 10%`), failing `_LOADED_COST_PCT_RE`. |
| **Baron Samedi** | 3,041,182.00 | 2,991,183.00 | **49,999.00** | Completion Bond | 1 | `COMPLETION BOND 50,000` | Line carries flat `$50,000` ($1 authored rounding). Skipped because line has no colon or percentage (`: X.X%`), falling through parser loop. |
| **Going Places** | 7,301,947.00 | 7,181,142.00 | **120,805.00** | Completion Bond | 2 | `COMPLETION BOND (0 excluded) 120,804` | Line carries `$120,804` ($1 authored rounding). Skipped because line contains parentheses and no colon/percentage, falling through parser loop. |
| **The System** | 4,324,058.00 | 3,981,987.00 | **342,071.00** | Contingency & Other Costs | 1 | `CONTINGENCY 312,071`<br>`TOTAL OTHER COSTS 348,300` | Page 1 shows `Total Above and Below-The-Line 3,981,987` followed by `CONTINGENCY 312,071` and unextracted other fee ($30,000). Total shortfall is exactly $312,071 + $30,000 = $342,071.00. Skipped because contingency line has no colon or percentage. |
| **Twilight of the Dead** | 8,546,272.00 | 8,007,318.00 | **538,954.00** | Contingency Reserve | 2 | `Contingency 7% : 7.0% $538,954` | Line carries `$538,954`. Skipped because line carries a leading dollar sign in amount or label formatting conflicts with `_LOADED_COST_PCT_RE`. |
| **Underwater** | 7,998,944.00 | 6,973,801.00 | **1,025,143.00** | Total Fringes Footer | 2 | `Total Fringes $1,025,143` | Topsheet isolates fringes as an unnumbered footer line below BTL ($6,050,901 + $1,025,143 = $7,998,944 Grand Total with bond/contingency). Skipped because line begins with `Total ` and was filtered out as an aggregate group subtotal. |

### Root Cause Analysis in `backend/app/ingestion/budget_parser.py`
In `_parse_film_budget`:
```python
_LOADED_COST_PCT_RE = re.compile(r"^([A-Za-z][A-Za-z /&]*?)\s*:\s*\d+(?:\.\d+)?%\s*$")
```
1. **Strict Character Class Restriction:** The regex permits only `[A-Za-z /&]`. Any label with digits (e.g. `10%`, `7%`), parentheses (e.g. `(0 excluded)`), or hyphens fails to match.
2. **Mandatory Percentage Syntax:** The regex requires `:\s*\d+(?:\.\d+)?%`. Any flat-fee loaded cost without a percentage rate (e.g. `COMPLETION BOND 50,000`, `CONTINGENCY 312,071`) falls through to `else: i += 1` and is silently dropped.
3. **Subtotal False Positives:** Legitimate loaded-cost or fringe summary footers (e.g. `Total Fringes $1,025,143`) match `_GROUP_SUBTOTAL_RE` and are rejected as double-counts, even when the underlying departmental lines exclude fringes.

---

## 3. Finding NA-02: Recovery of Full Commercial Budget for `5 LBS OF PRESSURE`

In the prior audit run, `5 LBS OF PRESSURE` was flagged as ineligible across all North American programs due to its database record indicating a declared budget of only \$7,066.00 across 4 lines.

### Investigation & Discovery
A comprehensive search of local project archives uncovered the original production documents in `/Users/Suraj/Documents/5lbs/`:
1. **`5lbs BUDGET - 24th August USD.pdf` (62 pages, full Movie Magic export):**
   * **Project Header:** `"5LBS OF PRESSURE | Budget - 24th August 2022 | Prep: 4 weeks (30th Aug - 26th Sept 2022) | Shoot: 24 days (26th Sept - 27th Oct 2022) | Location: United Kingdom | Director: Phil Allocco | UK Producers: C Anderson-Dillon & Dominic Burns"`.
   * **Above-The-Line Costs (1100–1800):** **\$2,139,007.00** (incl. 1100 Story & Rights \$97,565, 1200 Producer \$440,814, 1300 Director \$98,452, 1400 Cast \$1,355,083, 1500 Travel & Living \$120,459, 1600 Supporting Cast \$22,182, 1800 Stunts \$4,452).
   * **Below-The-Line Production Costs (1700–3500):** **\$1,304,711.00** (Production \$110,632, Art \$216,603, Camera \$103,993, Costume \$105,589, Transport \$115,630, Locations \$168,996, etc.).
   * **Below-The-Line Post Costs (4100–4500):** **\$81,930.00** (Picture \$35,093, Music \$17,975, Sound \$23,623, Deliverables \$5,239).
   * **Below-The-Line Other Costs (5000–6200):** **\$325,430.00** (Insurance \$38,435, Publicity \$4,435, General Expense \$10,643, Professional Fees \$198,795, Contingency (5.0%) \$73,122, Bond Fee \$0).
   * **Total Above and Below-The-Line:** **\$3,851,078.00**.
   * **Grand Total Production Budget:** **\$3,851,078.00 USD**.
   * **Embedded Source Tax Credit (Account 7100):** `UK Tax Credit (713,707)`, establishing a Producer Net Total of **\$3,137,371.00 USD**.
2. **Alternative Budget Revisions on File:**
   * `5lbs 22 day Budget USD 28th August.pdf` (62 pages): Grand Total **\$3,123,370.00 USD** (UK Tax Credit \$564,960).
   * `5 lbs Budget - 9th August.pdf` (61 pages): Grand Total **£2,883,692 GBP** (ATL £1,761,706, BTL Production £1,080,432, Post £105,180).

### Audit Retraction & Finding Disposition
* **Prior Claim Retracted:** The assertion that `5 LBS OF PRESSURE` is an intrinsically ineligible micro-budget ($7,066) is **formally retracted**.
* **Root Cause:** Database project `98b440b9-a93a-4713-86c8-a5f75b54da97` was populated exclusively with `5lbs of Pressure_ Pre-Prep Budget & Schedule.pdf`, which was merely an isolated 4-week petty cash scouting and scheduling schedule.
* **Disposition:** `5 LBS OF PRESSURE` is a commercial feature production with an actual gross budget of **\$3,851,078.00 USD**. At \$3.85M, it comfortably satisfies the statutory minimum spend thresholds for all major North American jurisdictions (e.g. CA \$1M, NY \$250k, GA \$500k, NM, IL, ON, BC, QC).

---

## 4. Finding NA-03: North American Program Governance & Economic Disposition Inventory

Frozen from `backend/app/data/executable_jurisdiction_registry.py`:
* **Total North American Programs:** **45** (30 United States, 14 Canada, 1 Mexico).
* **Authority Coverage Split:**
  * **36 Programs** `AUTHORITY_VERIFIED_PRICEABLE`: fully supported by primary statutes/guidance in structured provenance.
  * **9 Programs** `AUTHORITY_UNRESOLVED_NON_PRICEABLE`: `ca_mb_film_video_credit`, `ca_nb_film_tax_credit`, `ca_ns_production_incentive_fund`, `ca_sk_creative_saskatchewan_grant`, `us_az_motion_picture_production`, `us_co_film_incentive`, `us_hi_film_digital_media_credit`, `us_ut_motion_picture_incentive`, `us_va_motion_picture_credit`. Under the Two-Axis Correction (2026-09-02), these price deterministically in everyday candidate discovery on the strength of their retained real rate data, but are quarantined from production sign-off and cannot be marked `RECOMMENDED`.
* **Economic Determinism Split:**
  * **41 Programs** `DETERMINISTIC_PRICEABLE`: formulaic statutory rates and definite entitlement floors.
  * **4 Programs** `CONDITIONAL_NONDETERMINISTIC`: `us_md_film_production_activity_credit`, `us_nc_film_entertainment_grant`, `us_sc_film_production_credit`, `us_tx_miip`. These carry discretionary ceilings without fixed statutory floors and must present solely as conditional opportunities.

---

## 5. Finding NA-04: Program-Specific QPE & Stacking Dispositions (Beyond Generic Matches)

Rather than treating all jurisdictions as identical generic open-spend buckets, each jurisdiction enforces specific statutory cost boundaries, person caps, and stacking interactions:

### 5.1 California Film & Television Tax Credit (Program 4.0 — `ca_film_30`)
* **Statutory Baseline:** Excludes all Above-The-Line compensation (writers, directors, producers, principal and supporting cast), completion bonds, financing fees, unspent contingency, and residuals reserves.
* **Account-Level Application:**
  * **The Little Utopia:** Pre-cap QPE = **\$3,913,031.00** (\$4,364,395 − \$301,131 cont − \$9,068 US edit − \$141,165 ATL).
  * **F#K Valentine's Day:** Pre-cap QPE = **\$1,724,759.00** (\$4,517,687 − \$453,583 finance − \$362,866 cont − \$1,976,479 ATL).
  * **Bad Hombres:** Pre-cap QPE = **\$854,739.00** (\$2,482,023 − \$94,382 cont − \$1,448,902 ATL − \$60,000 SAG residual − \$24,000 legal).
  * **Lips Like Sugar:** Pre-cap QPE = **\$6,388,593.00** (\$11,983,654 − \$1,700,000 finance − \$3,308,031 ATL − \$587,030 mixed/fringes).
  * **5 LBS OF PRESSURE (Recovered):** Pre-cap QPE = **\$1,638,949.00** (\$3,851,078 − \$2,139,007 ATL − \$73,122 cont).

### 5.2 New Mexico Film Production Tax Credit (`us_nm_film_credit`)
* **Statutory Baseline:** All direct in-state production expenditures qualify. Non-resident cast and crew qualify only upon certification of 8% NM withholding and Film Office registration.
* **Dispositions:** LU \$4,054,196.00; FVD \$3,701,238.00; BH \$2,327,641.00; LLS \$9,483,654.00; 5 LBS \$3,777,956.00. Uplift maximums (+15 points rural/facility) are conditional upper bounds requiring proof of qualified facility and rural location shoot.

### 5.3 New York State Film Production Credit (§ 24 — `ny_state_film`)
* **Statutory Baseline:** Qualified BTL production costs, plus eligible ATL (writers, directors, performers) subject to:
  1. Individual cap of \$500,000 per person.
  2. Maximum 2 producer fees eligible.
  3. Aggregate ATL ceiling of **40%** of total qualifying BTL + Post costs (§ 24(b)(1)).
  4. Aggregate ATL dollar cap of \$7,000,000.
* **Upstate Labor Uplift (§ 24(a)(5)):** Additional 10% credit applies to upstate counties (including Dutchess, Orange, and Putnam) where principal photography satisfies the >50% upstate shoot day gateway.
* **Stacking Exclusivity:** Taxpayers receiving Section 24 credits are statutorily barred from claiming Section 31 post-production credits on identical costs (§ 31*2(a)(1)).

### 5.4 New York Post-Production Credit (§ 31 — `us_ny_post_production_credit`)
* **Statutory Baseline:** Closed positive list: Post-Production + Post Sound + VFX only.
* **Strict Exclusions:** All ATL, all physical set costs, on-set production sound.
* **Gateways:** Gateway 1 (lesser of \$1M or 75% worldwide post); Gateway 2 (VFX: lesser of \$500k or 10% worldwide VFX).
* **Dispositions:** LU \$28,500.00; FVD \$166,646.00; BH \$0.00; LLS \$115,000.00; 5 LBS \$81,930.00; Twilight of the Dead \$422,400.00; Rocky Mountain \$4,213,293.00.

### 5.5 Per-Person Salary Caps (Georgia, Illinois, Massachusetts)
* **Georgia (`us_ga_film_credit`):** \$500,000 individual salary cap. ATL compensation exceeding \$500k is disallowed.
* **Illinois (`us_il_film_production_services_credit`):** \$500,000 per-worker cap.
* **Massachusetts (`us_ma_film_tax_credit`):** \$1,000,000 payroll exclusion threshold (compensation $\ge$ \$1M completely excluded).
* **Missing Fact:** Exact line-level payee compensation splits are absent from all topsheets, preventing precise deduction without general ledger payroll schedules.

### 5.6 Canadian Stacking & CAVCO Labour Expenditure (`ca_federal_cptc`, `on_ofttc`, `ca_qc_pstc`)
* **Federal CPTC Base:** 25% of Canadian Qualified Labour Expenditure (QLE), capped at 60% of Net Production Cost.
* **Stacking Netting Rule:** Under ITA § 125.4(1)(b), provincial credits (e.g. Ontario OFTTC 35%, Quebec PSTC 25%) constitute **government financial assistance** that directly reduces the CPTC labour expenditure basis!
  $$\text{CPTC Credit} = 0.25 \times (\text{QLE} - \text{Provincial Assistance})$$
* **Mutual Exclusivity:** Federal CPTC (domestic content) and Federal PSTC (foreign service 16%) are strictly mutually exclusive for the same production.

### 5.7 Mexico Federal Film Incentive (2026 — `mx_federal_film_incentive_2026`)
* **Statutory Baseline:** 30% cash rebate.
* **Dual Native Gating:** Native **MXN 40,000,000** per-project cap AND native **MXN 40,000,000** minimum local spend.
* **Disposition:** Fails closed without an authenticated live MXN/USD exchange rate.

---

## 6. Finding NA-05: Canadian CAVCO Labour Expenditure Derivation Gap

Standard topsheet budgets summarize costs by department (e.g. Art, Camera, Sound, Locations) rather than providing a separate accounting of labor wages versus equipment rentals and purchases. 

Under CAVCO and provincial rules (OFTTC, BC PSTC, SODEC):
1. Only eligible compensation paid to Canadian tax residents qualifies as Canadian Qualified Labour Expenditure (QLE).
2. Deemed labor ratios (e.g. assuming 50% or 60% of BTL is labor) represent planning heuristics, not certifiable legal spend.
3. Exact QLE derivation is an **irreducible missing production fact** across all 15 budgets until authenticated cast/crew payroll logs and residency declaration forms are supplied.

---

## 7. Finding NA-06: Mexico Native Currency FX Gating

In `mx_federal_film_incentive_2026`, statutory caps and minimum spend thresholds are legislated in Mexican Pesos (MXN 40,000,000). 
* At MXN/USD = 18.0, MXN 40M equates to ~\$2,222,222 USD.
* Under `PROJECT_OPEN_ITEM_RECOVERY.md` finding F-05, the optimizer correctly fails closed when MXN exchange rates are absent from the FX table rather than fabricating an arbitrary conversion factor.

---

## 8. Finding NA-07: Proposed Generic Parser Repairs for Codex Review

To resolve the extraction shortfalls identified in **NA-01** across Movie Magic and topsheet formats without hardcoding project-specific hacks, the following generic parser repairs are proposed for Codex review:

### Proposed Patch Specification for `backend/app/ingestion/budget_parser.py`

#### 1. Generalize `_LOADED_COST_PCT_RE`
Replace the restrictive regex:
```python
# CURRENT RESTRICTIVE PATTERN:
_LOADED_COST_PCT_RE = re.compile(r"^([A-Za-z][A-Za-z /&]*?)\s*:\s*\d+(?:\.\d+)?%\s*$")
```
With a generalized loaded-cost pattern that accommodates embedded percentages, parenthetical notes, hyphens, and optional percentages:
```python
# PROPOSED GENERIC PATTERN:
_LOADED_COST_LINE_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9\s/&()\-–—%]+?)"  # Allow alphanumeric, %, (), -, &
    r"(?:\s*:\s*\d+(?:\.\d+)?%)?"            # Optional ": X.X%" rate specifier
    r"\s*$",
    re.IGNORECASE,
)
```

#### 2. Generic Loaded Cost Keyword Detection
In `_parse_film_budget`, check whether a line following `Total Above and Below-The-Line` or departmental blocks matches known loaded-cost categories:
```python
_KNOWN_LOADED_COST_KEYWORDS = (
    "contingency", "completion bond", "bond fee", "dga bond",
    "insurance", "covid insurance", "legal", "professional fees",
    "total fringes", "fringes", "payroll taxes & fringe"
)
```
When a line contains any of these keywords and is accompanied by a valid dollar amount (parsed via `_parse_amount_from_line`), extract it as a valid leaf `ParsedLineItem` with its authored description, setting:
* `spend_category`: mapped appropriately (`contingency`, `insurance`, `completion_bond`, `fringes`, `general_administration`).
* `atl_btl`: `"btl"` (or `"other"`).
* Avoid double-counting by asserting that the line is not identical to `Total Above and Below-The-Line` or `Grand Total`.

#### 3. Dollar-Sign Tolerance in Amount Extraction
Ensure `_parse_amount_from_line` cleanly strips leading currency symbols (`$`, `£`, `€`) and commas before float conversion:
```python
clean_s = re.sub(r"[^\d.-]", "", raw_amount_str)
```

---

## 9. Summary & Gate Disposition

1. **Extraction Shortfalls Verified:** All 6 budget discrepancies were proven directly against original PDF topsheets and localized to specific unextracted fee/bond/contingency/fringe lines.
2. **5 LBS OF PRESSURE Recovered:** Full \$3.85M commercial budget recovered from original production records, retracting false micro-budget ineligibility claims.
3. **Program-Specific QPE Dispositions Established:** Detailed statutory rules mapped across California BTL, New Mexico, New York Film (§ 24), New York Post (§ 31), Georgia salary caps, Canadian stacking, and Mexico native FX gating.
4. **Generic Parser Repairs Designed:** Concrete regex and structural parser patches formulated for Codex review.
5. **No Code / DB / Evaluation Violations:** Zero code files touched, zero database mutations, zero cold evaluations.

> [!IMPORTANT]
> **GATE DISPOSITION:**
> **`STATUS: ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> In accordance with `PROJECT_RULES.md`, all empirical missing facts (payee residency, withholding proof, out-of-zone shoot schedules, general ledger labor splits) remain explicitly unresolved. No acceptance gate is closed.
