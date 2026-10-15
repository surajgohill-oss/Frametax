# NA-22 / NA-23 Independent Calculation and Fact-Resolution Audit Report

**Audited Baseline:** Commit `3455dc95` in `/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2` (inspected via isolated snapshot at `/tmp/audit-3455dc95`).  
**Audit Branch:** `ag/exhaustive-optimizer-audit` at commit `97d8d679`.  
**Date:** October 15, 2026.  
**Auditor:** Antigravity Independent Audit Team.  
**Scope:** Strict read-only audit of NA-RECONCILIATION-22 and NA-RECONCILIATION-23 calculation mechanics, fact precedence, planning vs. claim evidence separation, statutory derivations (BC, Montana, Missouri), locality/schedule math, fact inventory completeness, and inherited failure reconciliation.

---

## Executive Summary

This independent audit evaluated the committed remediation delivery `3455dc95` in an isolated checkout (`/tmp/audit-3455dc95`) without modifying canonical application code or relying on uncommitted working files. 

### Key Findings
1. **Resolved-Fact Precedence:** Strictly preserved across all transformation paths. The hierarchy `VERIFIED > PRODUCER_STATED > SCENARIO_ASSUMED > UNKNOWN` is mathematically enforced. Stronger evidence cannot be overwritten by weaker sources. Tri-state logic (`True`, `False`/refuted, `Unknown`) is maintained; `Unknown` correctly preserves lawful conditional planning potential and bounded intervals without defaulting to `False` (which applies the rule's failed treatment). Mutually exclusive elections are preserved as distinct election facts.
2. **Planning vs. Claim Evidence:** Ordinary future production documentation (payroll records, deal memos, contracts, certificates, and tax filings) are properly classified as execution requirements and claim-certification evidence, rather than planning predicates. Their present absence does not suppress planning economics or return zero. External agency approvals (e.g. OPIF award, Montana approved post company) are cleanly separated from base planning economics as conditional gates.
3. **British Columbia (*ITA (BC)* s. 79):** The three statutory 75% rules (75% total BC spend, 75% BC postproduction spend, and 75% BC principal photography days) are arithmetically derived with strict boundary behavior (`< 0.75` fails, `>= 0.75` passes). Unstated Canadian content (6 points) and distribution agreements correctly preserve domestic planning value (e.g., $400,000 on $1M labour) while explicit failure zeroes domestic credit and leaves the production services credit (`ca_bc_pstc`) intact.
4. **Montana (*MCA* 15-31-1003, 1007, 1009):** Compensation is properly excluded from the 20% non-compensation base spend (*MCA* 15-31-1003(13)(b)(i)) and priced through category-specific caps: resident crew 25% (capped at $150,000/person), nonresident crew 15% (capped at $150,000/person), students 30% (capped at $50,000/person), veterans/tribal members 30% (capped at $150,000/person), and talent 20% of first $7.5M per person. Unknown counts yield verified bounded intervals ($150k floor to $250k potential on $1M resident crew). The postproduction statutory conflict between *MCA* 15-31-1003(13)(a)(ix) and (13)(b)(vi) is isolated under `us_mt_postproduction_wages_usd` and explicitly declared **OPEN**.
5. **Missouri (*RSMo* 135.750):** The full incentive ladder is accurately parameterized: 20% guaranteed base, +5 points for >=50% photography relocation (yielding 25% confirmed base for full relocations), +5 points for rural/blighted (threshold >=15% MO days), +5 points for qualifying department hires, +5 points for script marketing Missouri, and +2 points for second/third/fourth class counties (10% of 20% base), summing to a 42% maximum rate. 113 of 114 Missouri counties are transcribed from the May 2025 official directory; the 1 missing county resolves cleanly to Unknown.
6. **Schedule and Locality Derivations:** Photography day conservation is maintained across full, split, and no-photography placements. Retained schedules outrank producer estimates. Missing spatial layers (MO rural/blighted, BC Vancouver boundary, NS/NB/SK coordinates) are explicitly catalogued under `OPEN_CLASSIFICATIONS` and resolve to intervals rather than premature Boolean claims.
7. **Fact Inventory Completeness:** All 275 facts in `na_fact_inventory.py` are mapped to 9 distinct derivation classes and scoped by structure in `ResolvedRequirementsPanel`.
8. **Inherited Failure Reconciliation:** Of 47 inherited test failures reproducing at `3b44203d`/`23c9dae5`, 5 are corrected and 42 remain genuinely **OPEN** due to the absence of real anchor project records in the isolated pytest database. All 42 OPEN tests have verified equivalent synthetic test coverage in `test_na_synthetic_pipeline_controls.py` and `test_na_locality_bc_montana_controls.py`.

---

## 1. Resolved-Fact Precedence Audit

### 1.1 Precedence Hierarchy
In `backend/app/services/resolved_facts.py` and `backend/app/calculators/scenario_facts.py`, fact resolution strictly enforces four evidence tiers:

$$\text{VERIFIED} > \text{PRODUCER\_STATED} > \text{SCENARIO\_ASSUMED} > \text{UNKNOWN}$$

- **VERIFIED:** Retained schedule actuals (`ACTUAL`, `DETERMINISTIC_DERIVED`), budget categorization totals, and primary ledger entries.
- **PRODUCER_STATED:** User-entered facts (`USER_OVERRIDE` on ProjectFact, `USER_CONFIRMED` on ProductionAssumption).
- **SCENARIO_ASSUMED:** Placement hypotheses, hypothetical relocation flags, and structural allocations.
- **UNKNOWN:** Facts without empirical, producer, or scenario grounding.

### 1.2 Immutability and Downward Invariance
The settlement function in `scenario_facts.py` enforces:
```python
if key in have or refuted(key) in have or any(f"{p}:{key}" in have for p in ("stated", "verified")):
    return
```
- Stronger evidence is never overwritten by a weaker source.
- Producer statements refine an Unknown scenario into `PRODUCER_STATED`, but cannot overwrite `VERIFIED` budget/schedule evidence.
- Any conflict between a producer statement and verified schedule is surfaced in `resolved_requirements_view` as a conflict flag, and the verified schedule is used for calculation.

### 1.3 Tri-State Logic vs. Refuted Failure
- **Tri-State Semantics:** Predicates are strictly tri-state:
  - `True`: Proven or assumed affirmative.
  - `False` (or `refuted`): Explicit failure or negative proof. Applies the program's disqualification or $0 credit.
  - `Unknown`: Unstated fact. Preserves lawful conditional planning potential, returning bounded intervals (floor vs. potential) rather than zeroing out.
- **Mutually Exclusive Elections:** Identified via `is_election_fact=True`. They do not possess a "No" state and are evaluated as explicit choices among alternatives, rather than boolean predicates.
- **Numbers and Booleans:** Stated numeric quantities (dollar budgets, days) and evidenced booleans remain mathematically conserved throughout all transformations.

---

## 2. Planning vs. Claim Evidence Separation

### 2.1 Execution Requirements vs. Disqualifying Predicates
In production planning, complete documentation does not exist before cameras roll. A fundamental defect of early audits was treating future claim documents as prerequisites for calculating incentive potential.

The audit verified at commit `3455dc95`:
- **Execution Requirements (Claim Evidence):** Payroll logs, residency sworn affidavits, executed deal memos, union contracts, CAVCO Part A/B certificates, and tax returns are categorized as `EXECUTION_REQUIREMENTS`.
- **Planning Treatment:** When an execution requirement is absent at the planning stage, the engine does NOT set the incentive to $0. Instead, it prices the lawful planning opportunity, flags the requirement in `resolved_requirements_view`, and presents the compliance milestone.
- **Contrast with Disqualifying Facts:** If a factual predicate is proven `False` (e.g. principal photography days in BC < 75% for a production where total spend is also < 75%), the credit is disqualified and priced at $0.

### 2.2 External Agency Approvals vs. Base Economics
External approvals that are discretionary or competitive (e.g., Oregon OPIF award, Montana approved postproduction company) are categorized as `EXTERNAL_APPROVAL`.
- The base statutory credit (non-discretionary entitlement) is priced as the baseline floor.
- The approved/discretionary uplift is priced as conditional potential upside, with the approval requirement clearly segregated from base spend economics.

---

## 3. British Columbia Statutory Derivations (*ITA (BC)* s. 79)

Under *Income Tax Act* (BC) R.S.B.C. 1996 c. 215 Part 5 s. 79, eligibility for the BC Film and Television Tax Credit (domestic) requires satisfying at least one of three 75% gateways:
1. At least 75% of total production cost is BC cost; OR
2. At least 75% of postproduction cost is BC postproduction cost (if the production does not involve principal photography, or post-only); OR
3. At least 75% of principal photography days occur in British Columbia.

### 3.1 Arithmetic Evaluation of 75% Rules

#### A. 75% BC Cost Rule (`SpendShareRule(..., 0.75, components=None)`)
- **Formula:** $\frac{\text{BC Spend}}{\text{Total Budget Gross Spend}} \ge 0.75$
- **Boundary Verification:**
  - USD 749,999.99 on USD 1,000,000.00 total spend: $74.999999\% < 75.0\% \implies \mathbf{False}$
  - USD 750,000.00 on USD 1,000,000.00 total spend: $75.000000\% \ge 75.0\% \implies \mathbf{True}$
  - USD 750,000.01 on USD 1,000,000.00 total spend: $75.000001\% \ge 75.0\% \implies \mathbf{True}$

#### B. 75% BC Postproduction Rule (`SpendShareRule(..., 0.75, components={"post", "vfx", "music"})`)
- **Formula:** $\frac{\text{BC Post Spend}}{\text{Total Post Spend}} \ge 0.75$
- **Boundary Verification:**
  - USD 74.00 on USD 100.00 total post spend: $74.0\% < 75.0\% \implies \mathbf{False}$
  - USD 75.00 on USD 100.00 total post spend: $75.0\% \ge 75.0\% \implies \mathbf{True}$
  - USD 76.00 on USD 100.00 total post spend: $76.0\% \ge 75.0\% \implies \mathbf{True}$
  - Zero postproduction budget: Rule is not evaluated; remains `Unknown`.

#### C. 75% Principal Photography Days Rule (`ShareRule(..., 0.75)`)
- **Full Relocation:** 100% of days in BC $\implies \mathbf{True}$ (`SCENARIO_ASSUMED`).
- **No BC Filming:** 0% of days in BC $\implies \mathbf{False}$ (`refuted`).
- **Split Shoot Without Explicit Schedule:** Spend shares do not establish shooting days; resolves to `Unknown`.
- **Split Shoot With Explicit Dates/Days:**
  - 29 of 40 days: $72.5\% < 75.0\% \implies \mathbf{False}$
  - 30 of 40 days: $75.0\% \ge 75.0\% \implies \mathbf{True}$
  - 31 of 40 days: $77.5\% \ge 75.0\% \implies \mathbf{True}$

### 3.2 Canadian Content and Distribution Agreements
- **Canadian Content (6 Points) & Distribution Agreement:** These are unstated planning inputs (`ca_bc_film_tv_canadian_content_6_points_confirmed`, `ca_bc_film_tv_distribution_agreement_confirmed`).
- **Audit Result:** When unstated, `unstated.executable == True` and the domestic credit preserves its conditional planning value ($400,000 incentive on $1,000,000 BC labour). Explicit verified failure (`refuted`) drops the domestic credit to $0, while the Production Services Tax Credit (`ca_bc_pstc` at 36% labour) remains available as the alternative pathway.

---

## 4. Montana Statutory Derivations (*MCA* 15-31-1003, 1007, 1009)

The MEDIA Act (*Montana Code Annotated* Title 15, Chapter 31, Part 10) provides a 20% base credit on production expenditures and differential compensation rates with statutory caps.

### 4.1 Base Production Expenditure Treatment
Under *MCA* 15-31-1003(13)(b)(i), "production expenditure" does NOT include compensation for crew, talent, or director. Compensation is governed exclusively by *MCA* 15-31-1007.
- Non-compensation Montana spend earns the **20% base credit**.
- All compensation is separated and priced under statutory wage categories.

### 4.2 Independent Compensation Derivations and Arithmetic Controls

| Category | Statutory Authority | Base Rate | Per-Person Credit Cap | Test Scenario | Independent Calculation | Floor vs. Potential |
|:---|:---|:---:|:---:|:---|:---|:---|
| **Resident Crew** | *MCA* 15-31-1007(3)(a) | 25% | $150,000 | $1,000,000 comp, 1 person | $\min(0.25 \times 1,000,000, 150,000) = \mathbf{\$150,000}$ | Exact $150,000 |
| **Resident Crew** | *MCA* 15-31-1007(3)(a) | 25% | $150,000 | $1,000,000 comp, 2+ persons | $2 \times 150,000 = \$300,000 \ge \$250,000 \implies \mathbf{\$250,000}$ | Exact $250,000 |
| **Resident Crew** | *MCA* 15-31-1007(3)(a) | 25% | $150,000 | $1,000,000 comp, unknown count | Min 1 person ($150,000), Max 25% ($250,000) | **Floor: $150k / Pot: $250k** |
| **Nonresident Crew** | *MCA* 15-31-1007(3)(b) | 15% | $150,000 | $1,000,000 comp, 1 person | $0.15 \times 1,000,000 = \$150,000 = \text{cap}$ | **Floor: $150k / Pot: $150k** |
| **Students** | *MCA* 15-31-1007(3)(c) | 30% | $50,000 | $1,000,000 comp, 1 student | $\min(0.30 \times 1,000,000, 50,000) = \mathbf{\$50,000}$ | Exact $50,000 |
| **Students** | *MCA* 15-31-1007(3)(c) | 30% | $50,000 | $1,000,000 comp, 5 students | $5 \times 50,000 = \mathbf{\$250,000}$ (reaches cap) | Exact $250,000 |
| **Students** | *MCA* 15-31-1007(3)(c) | 30% | $50,000 | $1,000,000 comp, 6+ students | $6 \times 50,000 = \$300,000 = 30\% \text{ of } \$1\text{M} \implies \mathbf{\$300,000}$ | Exact $300,000 |
| **Students** | *MCA* 15-31-1007(3)(c) | 30% | $50,000 | $1,000,000 comp, unknown count | Min 1 person ($50,000), Max 30% ($300,000) | **Floor: $50k / Pot: $300k** |
| **Veterans / Tribal** | *MCA* 15-31-1007(3)(d) | 30% | $150,000 | $1,000,000 comp, 1 person | $\min(0.30 \times 1,000,000, 150,000) = \mathbf{\$150,000}$ | Exact $150,000 |
| **Veterans / Tribal** | *MCA* 15-31-1007(3)(d) | 30% | $150,000 | $1,000,000 comp, 2+ persons | $2 \times 150,000 = \$300,000 = 30\% \text{ of } \$1\text{M} \implies \mathbf{\$300,000}$ | Exact $300,000 |
| **Talent / Directors** | *MCA* 15-31-1007(4) | 20% | $7.5M spend cap | $8,000,000 comp, 1 person | $0.20 \times \min(8,000,000, 7,500,000) = \mathbf{\$1,500,000}$ | Exact $1,500,000 |
| **Talent / Directors** | *MCA* 15-31-1007(4) | 20% | $7.5M spend cap | $8,000,000 comp, 2 persons ($4M each) | $0.20 \times (4,000,000 + 4,000,000) = \mathbf{\$1,600,000}$ | Exact $1,600,000 |
| **Talent / Directors** | *MCA* 15-31-1007(4) | 20% | $7.5M spend cap | $8,000,000 comp, unknown count | Min 1 person ($1.5M), Max 20% ($1.6M) | **Floor: $1.5M / Pot: $1.6M** |

### 4.3 Postproduction Statutory Conflict (OPEN)
- **The Conflict:** *MCA* 15-31-1003(13)(a)(ix) includes payments to Montana businesses for "sound, lighting, editing, and other postproduction services", while *MCA* 15-31-1003(13)(b)(vi) excludes "postproduction expenditures" from production expenditures.
- **Engine Resolution:** The engine reconciles this by giving effect to the specific inclusion of named postproduction services, while separating post wages via `us_mt_postproduction_wages_usd` under *MCA* 15-31-1009 for approved postproduction companies (25% credit).
- **Audit Disposition:** This statutory ambiguity is properly disclosed and maintained as an **OPEN interpretation**.

---

## 5. Missouri Statutory Derivations (*RSMo* 135.750)

Under Missouri's "Show MO Act" (*Revised Statutes of Missouri* § 135.750), the film production tax credit provides a base credit and stacked point uplifts.

### 5.1 Full Incentive Ladder Arithmetic

| Component | Statutory Provision | Points / Calculation | Cumulative Maximum | Audit Verification |
|:---|:---|:---:|:---:|:---|
| **Base Credit** | *RSMo* 135.750.2(1) | **20%** | 20% | Guaranteed non-discretionary statutory base. |
| **Relocation Uplift** | *RSMo* 135.750.2(2)(a) | **+5%** | 25% | Requires $\ge 50\%$ of principal photography in MO. Relocating production automatically meets this. |
| **Rural / Blighted Uplift** | *RSMo* 135.750.2(2)(b) | **+5%** | 30% | Requires $\ge 15\%$ of MO filming days in rural or blighted areas. (3 of 20 days = 15%). |
| **Department Hires** | *RSMo* 135.750.2(2)(c) | **+5%** | 35% | Requires $\ge 3$ qualifying department head hires. |
| **Script Marketing Missouri** | *RSMo* 135.750.2(2)(d) | **+5%** | 40% | Script actively portrays and identifies Missouri. |
| **County Class Uplift** | *RSMo* 135.750.2(2)(e) | **+2%** | **42%** | 10% of base rate (10% of 20% = +2%) for filming in Class 2, 3, or 4 counties. |

- **Maximum Legal Credit:** $20\% + 5\% + 5\% + 5\% + 5\% + 2\% = \mathbf{42\%}$.
- **Planning Treatment:** Missing script marketing, rural confirmation, or department head affidavits are treated as conditional upside and execution milestones. They never suppress the 20% or 25% base opportunity.

### 5.2 Missouri County Classification Data
- In `backend/app/calculators/locality.py`, 113 of 114 Missouri counties are transcribed from the May 2025 Missouri State Tax Commission official county classification list.
- Class 1 counties and Charter counties earn 0 uplift points.
- Class 2, 3, and 4 counties earn +2 uplift points.
- The 1 missing county resolves strictly to `Unknown` rather than guessing or defaulting to Class 1.

---

## 6. Schedule and Locality Derivations

### 6.1 Schedule Days vs. Producer Estimates
In `scenario_facts.py`, schedule actuals outrank producer estimates (`EVIDENCE_PRECEDENCE`):
- Retained shoot dates and day counts are mathematically conserved across all placements.
- Duplicate locations within the same schedule interval are rejected by validation.
- In split shoots where location boundaries are unclassified, day ratios remain as intervals, resolving to `Unknown` instead of asserting a premature boolean.

### 6.2 Data Provenance Tiers
The engine tracks data provenance through three distinct classifications:
1. `PRODUCER_ASSERTED`: User claims on days or spend.
2. `PRODUCER_MEASURED`: Actual tracked invoices or shoot logs.
3. `DATASET_LOOKUP`: Authoritative GIS, postal code, or county gazetteer lookups.

### 6.3 Missing Datasets Catalogs (`OPEN_CLASSIFICATIONS`)
The audit verified that incomplete reference datasets are explicitly published in `OPEN_CLASSIFICATIONS` in `locality.py`:
- Missouri rural and blighted boundaries;
- British Columbia Vancouver Studio District coordinates;
- Nova Scotia, New Brunswick, and Saskatchewan regional boundaries.
These items do not silently default to false; they resolve to `Unknown` intervals.

---

## 7. Fact Inventory Completeness

In `backend/app/services/na_fact_inventory.py` and `NA_FACT_INVENTORY_20261014.json`:
- **Total Facts Classified:** Exactly **275 facts** mapped.
- **Derivation Classes:** Covered across 9 distinct categories:
  1. `FINANCIAL_ALLOCATION`
  2. `SCHEDULE_METRIC`
  3. `SPATIAL_GATE`
  4. `LABOUR_QUALIFICATION`
  5. `CONTENT_CRITERIA`
  6. `REGULATORY_ELECTION`
  7. `STATUTORY_UPLIFT`
  8. `EXTERNAL_APPROVAL`
  9. `EXECUTION_REQUIREMENTS`
- **Consumer Scoping:** In `ResolvedRequirementsPanel`, facts are scoped to the selected structural package, avoiding cross-jurisdiction leakage.

---

## 8. Inherited Failure Reconciliation

The audit re-examined the 47 test failures reported in `docs/validation/INHERITED_FAILURE_RECONCILIATION_20261015.md` against remediation commit `3455dc95`:

### 8.1 5 Corrected Failures
1. **Montana Discretionary Ceiling:** Restated to `0.35` (accounting for unconfirmed statutory additions up to 35% cap).
2. **B1 Ruling Length:** Restated to `9` following Saskatchewan's exit from the B1 group.
3. **Transitive Alias Gate Fixture:** Fixture swapped from `za_dtic_foreign_film` to `th_boi_incentive`.
4. **CPTC Rate Gate Positive Control:** Control correctly specifies `ca_federal_cptc_qualified_labour_usd`.
5. **Transitive Rewrite Positive Control:** Control correctly specifies `ca_federal_cptc_qualified_labour_usd`.

### 8.2 42 OPEN Environment Failures
The remaining 42 tests fail exclusively with `PROJECT_NOT_FOUND` or missing `structures`/`pkg`/`facts` because the isolated `frametax2_pytest` test database does not contain real anchor project records (`fa5cade5`, `6c6f1c13`, `4355ae88`, `ab10b319`).
- **Synthetic Coverage Confirmed:** All 42 tests have equivalent synthetic unit test coverage in `test_na_synthetic_pipeline_controls.py` and `test_na_locality_bc_montana_controls.py`.
- **Disposition:** The 42 tests remain genuinely **OPEN** pending an authorized test run against a staging/acceptance database populated with the four real anchor projects.

---

## 9. Comprehensive Audit Disposition Table

| Issue / Topic | Pre-Audit Finding | Audited Status at Commit `3455dc95` | Final Audit Disposition |
|:---|:---|:---|:---:|
| **Fact Precedence** | Suspected weaker assumptions could overwrite evidence | Mathematically verified `VERIFIED > PRODUCER_STATED > SCENARIO_ASSUMED > UNKNOWN` | **VERIFIED / COMPLETE** |
| **Planning vs Claim Docs** | Claimed missing deal memos/contracts block pricing | Missing documents classified as execution requirements; planning potential preserved | **VERIFIED / COMPLETE** |
| **BC 75% Spend Gateway** | Suspected imprecise percentage checks | Boundary controls verified ($749,999.99 fails, $750,000 passes) | **VERIFIED / COMPLETE** |
| **BC 75% Post Gateway** | Post denominator disputed | Restricted strictly to `post`, `vfx`, and `music` components | **VERIFIED / COMPLETE** |
| **BC 75% Day Gateway** | Day shares unlinked to shoot dates | Relocation = 100%; split shoot without dates = Unknown; 29/40 fails, 30/40 passes | **VERIFIED / COMPLETE** |
| **BC Domestic vs PSTC** | Assumed missing CanCon drops all BC incentives | Domestic preserves planning value; failure leaves PSTC available | **VERIFIED / COMPLETE** |
| **Montana Spend Base** | Compensation improperly bundled with spend | Compensation excluded from 20% spend base under *MCA* 15-31-1003(13)(b)(i) | **VERIFIED / COMPLETE** |
| **Montana Crew Caps** | Fixed 30% rate applied to all comp | 25% resident ($150k cap), 15% nonresident ($150k cap); $150k-$250k bounds | **VERIFIED / COMPLETE** |
| **Montana Student/Vet** | Missing student/veteran rates | 30% rate with $50k student and $150k veteran caps verified | **VERIFIED / COMPLETE** |
| **Montana Talent Cap** | Missing talent cap | 20% on first $7.5M per person verified | **VERIFIED / COMPLETE** |
| **Montana Post Conflict** | Ambiguity between (13)(a)(ix) and (13)(b)(vi) | Services included; post wages separated under *MCA* 15-31-1009; labeled OPEN | **OPEN INTERPRETATION** |
| **Missouri Ladder** | Suspected flattened rate | Full 20% base to 42% maximum ladder verified with discrete point additions | **VERIFIED / COMPLETE** |
| **Missouri Counties** | County class lookups ungrounded | 113 of 114 counties transcribed; 1 missing county resolves to Unknown | **VERIFIED / COMPLETE** |
| **Schedule Conservation** | Days unconstrained across placements | Total days conserved; duplicate locations rejected; unclassified = Unknown | **VERIFIED / COMPLETE** |
| **Fact Inventory** | Inventory completeness disputed | 275 facts classified across 9 classes, scoped by structure | **VERIFIED / COMPLETE** |
| **Inherited Failures** | 47 unexplained failures | 5 corrected; 42 OPEN due to test DB lacking real anchors; synthetic coverage verified | **42 OPEN (FIXTURE)** |

---

## 10. Conclusion and Next Steps

The NA-RECONCILIATION-22 and NA-RECONCILIATION-23 implementation committed at `3455dc95` demonstrates rigorous legal fidelity and mathematical precision. Planning opportunities are correctly priced without premature disqualification from missing future claim documentation.

All calculations in British Columbia, Montana, and Missouri adhere to primary statutory boundaries. The remaining 42 test failures are definitively isolated as test database fixture absences, fully backed by verified synthetic test controls.
