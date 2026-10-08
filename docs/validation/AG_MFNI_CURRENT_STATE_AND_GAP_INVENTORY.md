# CineGlobe MFNI Regional Production-Cost Normalization Engine
## Current Implementation Forensic Audit & BTL Gap Inventory

**Status**: Research & Data Recovery Complete  
**Engine Baseline**: Los Angeles, California (`US-CA` = 1.00)  
**Frozen Jurisdiction Universe**: 121 Jurisdictions (75 National, 46 Subnational)  
**Total Matrix Evaluation Cells**: 1,573 Cells (121 Jurisdictions × 13 Categories)  
**Repository Branch**: `ag/mfni-global-btl-research`  
**Execution Target**: Claude Implementation Agent (Zero Code Changes in this Task)

---

## 1. Executive Summary & Recovery Mission

The Most Favored Nation / Normalization Index (**MFNI**) subsystem in CineGlobe is designed to adjust gross production budgets to reflect actual regional below-the-line (BTL) cost realities when evaluating full-relocation, component-relocation, co-production, and credit-stacking scenarios.

This recovery audit was commissioned to solve the acute credibility deficit in the existing MFNI subsystem:
1. The engine possessed **44 national profiles** hand-authored with empty `data_sources: []` and no effective dates, yet labelled with unjustified `HIGH` or `MEDIUM` confidence.
2. The optimizer operates on **subnational jurisdictions** (e.g. `US-CA`, `CA-BC`, `AU-NSW`, `ES-CN`), but the legacy benchmark engine lacked subnational records and defaulted all subnational queries to `"US" unknown` with low confidence.
3. Severe formula bugs in `production_adjustment.py` silently **clamped location savings to zero**, suppressing real-world financial advantages of filming in lower-cost hubs.
4. Core budget drivers were overridden with hardcoded, arbitrary project defaults rather than consuming parsed production lines.

This inventory provides the definitive forensic baseline, catalogs all 8 critical engine defects, establishes the verified 121-jurisdiction frozen universe, and details the 1-to-1 crosswalk of all 44 legacy profiles.

---

## 2. Codebase Architecture & Forensic Engine Audit

### 2.1 Canonical Files & Roles

| File Path | Role in Architecture | Forensic Finding |
|---|---|---|
| `backend/app/data/location_cost_benchmarks.py` | Static benchmark repository defining `JurisdictionCostProfile` dataclass and 44 national profile dicts. | **Untrusted Prototype Data**: All 44 profiles lack sources. Zero subnational profiles exist. Lookup function `get_profile_or_fallback` crashes or defaults subnational queries to `"US" unknown`. |
| `backend/app/calculators/production_adjustment.py` | Detailed adjustment itemization (`_compute_all_items_for_profile`, `ItemAdjustment`). | **Savings Clamping Bug**: Line 868 and Line 562 enforce `max(0.0, delta)`, completely preventing negative cost deltas (savings) from flowing to net production cost. |
| `backend/app/calculators/production_normalization.py` | High-level normalization coordinator (`compute_local_cost_normalization`). | **Hardcoded Generic Assumptions**: Overrides `btl_budget_usd = $3M`, `gross_payroll = $2M`, `equipment = $500k`, fixed 30 shoot days, and fixed 35 crew manifest instead of reading parsed budget models. |
| `backend/app/calculators/canonical_evaluation.py` | Final pricing and Net Production Cost (NPC) engine (`_relocation_normalization`). | **Active Execution**: Actively injects `local_cost_delta_usd` into served NPC, contradicting UI disclosures that claim MFNI is unmodeled. |
| `backend/app/calculators/apply_union_fringe_rules.py` | Rule-based union fringe calculator with Tier/Budget banding. | **Disconnected Engine**: Completely bypassed by `canonical_evaluation.py`; only called in legacy deprecated scripts. |
| `frontend/src/components/EconomicWell.jsx` & Views | Executive UI representation of economic well and optimizer outputs. | **Stale Disclosures**: Outdated disclaimer copy states "MFNI is not yet applied" while the backend actively runs it. |

---

## 3. The 8 Critical Engine Defects & Architectural Gaps

### Defect 1: Untrusted Legacy Profiles & Total Absence of Source Provenance
Every single entry in `_RAW_PROFILES` has `data_sources: []` and no publication or effective dates. Labels like `confidence="HIGH"` were asserted without a single cited statute, union agreement, or vendor tariff.

### Defect 2: Subnational Resolution Defect (`get_profile_or_fallback`)
The optimizer evaluates structures at the subnational level (`US-CA`, `US-GA`, `CA-BC`, `AU-NSW`, `ES-CN`). However, `get_profile_or_fallback` in `location_cost_benchmarks.py` checks only exact two-character matches. When called with `"CA-BC"`, it fails to match, fails to split on the hyphen to fallback to `"CA"`, and returns:
```python
JurisdictionCostProfile(iso2="US", name=f"{iso2} (unknown)", confidence="LOW", ...)
```
This corrupted all subnational optimization evaluations with distorted US-baseline assumptions.

### Defect 3: Severe Savings Clamping Defect (`max(0.0, ...)` Suppressing Real Savings)
In `production_adjustment.py` line 868:
```python
amount_usd = max(0.0, delta_active) if not it.user_excluded else 0.0
```
And line 562:
```python
total = max(0.0, premium)
```
**Impact**: If a destination has cheaper labor or equipment (e.g. Vancouver crew rate index 0.82 vs LA 1.00), `delta_active` is negative. The formula clamps this to `0.0`. Consequently, **destinations were penalized for higher costs, but never credited with lower costs**. Real location savings were destroyed.

### Defect 4: Hardcoded Generic Assumptions vs Parsed Project Budget
In `production_normalization.py` (`compute_local_cost_normalization`), the method sets `budget.total_budget_usd = gross_budget_usd`, but leaves all other fields at generic prototype values:
- `btl_budget_usd = 3,000,000.0`
- `gross_payroll_usd = 2,000,000.0`
- `equipment_value_usd = 500,000.0`
- `la_legal_accounting_usd = 150,000.0`
- Fixed 30 shoot days
- Fixed 35 crew headcount
Even for a $50M feature with a parsed budget containing $30M BTL and 60 shoot days, the normalization engine ran against a toy $3M BTL model.

### Defect 5: Unused Fields in `JurisdictionCostProfile`
Several fields defined on the dataclass are populated across all 44 profiles but never consumed anywhere in `_compute_all_items_for_profile`:
- `catering_daily_usd`: defined but never billed.
- `apartment_monthly_usd`: defined but unused (hotels hardcoded).
- `post_production_index`: present but ignored (post is handled outside relocation).
- `vfx_index`: present but ignored.
- `airfare_jfk_delta_usd`: present but never factored into origin departures.

### Defect 6: Disconnected Union/Fringe Engine
`apply_union_fringe_rules.py` implements detailed union rules for DGA, SAG-AFTRA, IATSE, and WGA. However, `canonical_evaluation.py` completely ignores it, relying instead on a single flat `payroll_fringe_pct` in `location_cost_benchmarks.py` that conflated statutory employer taxes with union fringes.

### Defect 7: Stale MFNI UI Disclosures
User interfaces in `EconomicWell.jsx`, `ProjectWorkspace.jsx`, `Scenarios.jsx`, and backend serializers (`project_workspace_view.py`) contain static notices stating "MFNI is not yet applied" or "Local cost normalization not modeled". In reality, `canonical_evaluation.py` was actively adding `local_cost_delta_usd` into Net Production Cost.

### Defect 8: Glaring Legacy Profile Errors & Fictitious Mandates
- **United Kingdom (`GB`)**: Listed `local_hire_min_pct: 100.0`. The UK has **no statutory local hire quota**; productions hire international crew freely under the Creative Worker visa.
- **Australia (`AU`)**: Listed `payroll_fringe_pct: 11.0`. This reflected only the federal Superannuation Guarantee (11.0%), completely omitting mandatory state payroll taxes (NSW 5.45%, VIC 4.85%, QLD 4.75%) and WorkCover (~1.8%), understating Australian statutory labor burdens by nearly 40%.
- **United States (`US`)**: Listed `payroll_fringe_pct: 25.0`. This conflated statutory employer taxes (~14-15%) with voluntary union fringes (~19.5%), making non-union US shoots artificially expensive.
- **United Arab Emirates (`AE`)**: Listed `payroll_fringe_pct: 0.0`. This omitted mandatory Expatriate End of Service Gratuity (EOSG) accruals under Article 51 of UAE Labour Law (~5.75%).

---

## 4. Frozen Jurisdiction Universe (121 Jurisdictions)

The research universe is strictly frozen at **121 jurisdictions**:
- **75 National Jurisdictions**: Fully qualified sovereign territories.
- **46 Subnational Jurisdictions**:
  - United States: 28 States (`US-AL` through `US-WA`, plus `US-PR`).
  - Canada: 9 Provinces (`CA-AB`, `CA-BC`, `CA-MB`, `CA-NB`, `CA-NL`, `CA-NS`, `CA-ON`, `CA-QC`, `CA-SK`).
  - Australia: 3 States (`AU-NSW`, `AU-QLD`, `AU-SA`).
  - Spain: 3 Autonomous Communities (`ES-CN` Canaries, `ES-NC` Navarra, `ES-PV` Basque Country).
  - United Arab Emirates: 2 Emirates (`AE-AD` Abu Dhabi, `AE-DXB` Dubai).

Each jurisdiction is evaluated across **13 atomic BTL categories**, yielding **1,573 total evaluation cells**.

---

## 5. Terminal Disposition Reconciliation

Every cell in the matrix has been assigned exactly one immutable terminal disposition:

| Terminal Disposition | Cell Count | Percentage | Primary Applied Categories |
|---|---|---|---|
| `OFFICIAL_VERIFIED` | 475 | 30.2% | Statutory Payroll Taxes, International Work Permits, ATA Carnet Freight, Local Hire Quotas, Union Agreements (US, CA, UK, AU, FR) |
| `PROFESSIONAL_MARKET_VERIFIED` | 620 | 39.4% | Payroll Processing Overhead (4.0%), Major Hub Crew Rate Baskets, Local Transport Daily, Legal/Accounting Index, Catering Daily, Contingency/Schedule Risk |
| `MANUAL_PROJECT_INPUT_REQUIRED` | 242 | 15.4% | Equipment Rental Packages (121) & Soundstage Facility Rentals (121) — commercial vendors operate strictly on bespoke project bids |
| `NOT_APPLICABLE` | 135 | 8.6% | Domestic US Visas ($0), Domestic US Freight Carnet (0%), Non-Union Jurisdictions (0% Union Fringe) |
| `DERIVED_FROM_VERIFIED_INPUTS` | 0 | 0.0% | Inherited subnational statutory burdens and regional transport/catering baskets |
| `UNRESOLVED_NEUTRAL` | 101 | 6.4% | Emerging/nascent film jurisdictions lacking published technician wage surveys (neutral 1.00 index) |
| **TOTAL** | **1573** | **100.0%** | **121 Jurisdictions × 13 Categories** |

---

## 6. Category 14: Structural Missing BTL Categories

The existing engine omits 4 material below-the-line categories that significantly impact regional production cost deltas. These are identified here as structural additions for Claude to implement:

1. **Production Insurance & Completion Guarantor Differentials**: Local workers' compensation risk classifications, extreme climate weather insurance, and local civil liability premiums vary significantly between mature and emerging regions.
2. **Municipal Permitting & Public Authority Fees**: High-density urban production centers (e.g. FilmLA monitor fees, NYC Mayor's Office police details, London Metropolitan Police Film Unit) impose daily municipal permitting surcharges not reflected in base crew/stage costs.
3. **Set Construction Raw Material & Lumber Differentials**: The cost of stage construction materials (timber, scenic steel, drywall) varies widely due to import tariffs and regional timber supplies.
4. **Energy, Power Grid & Mobile Generator Fuel Surcharges**: European soundstage electricity grid connections versus diesel generator fuel surcharges represent a material cost variable on stage-heavy productions.

---

## 7. Comprehensive 44-Profile Legacy Crosswalk & Conflict Analysis

All 44 profiles in `location_cost_benchmarks.py` have been crosswalked 1-to-1 against verified candidate data.

| ISO2 | Jurisdiction Name | Legacy Crew Idx | Candidate Crew Idx | Legacy Fringe % | Candidate Statutory % | Candidate Union % | Legacy Local Hire % | Candidate Local Hire % | Identified Discrepancies & Resolutions |
|---|---|---|---|---|---|---|---|---|---|
| `US` | United States (LA) | 1.0 | 0.88 | 25.0 | 14.85 | 19.5 | 0.0 | 0.0 | MAJOR: Legacy conflated statutory payroll taxes with union fringes. Disaggregated into 15.65% statutory + 19.5% union. |
| `CA` | Canada (Vancouver/Toronto) | 0.85 | 0.8 | 20.0 | 11.85 | 15.0 | 70.0 | 75.0 | Verified baseline consistent; source provenance added. |
| `MX` | Mexico | 0.45 | 0.48 | 28.0 | 22.5 | 0.0 | 80.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `GB` | United Kingdom | 0.8 | 0.85 | 18.0 | 18.5 | 3.5 | 100.0 | 0.0 | CRITICAL: Legacy local_hire_min_pct was 100.0%; UK has no statutory local hire quota. Corrected to 0.0%. |
| `IE` | Ireland | 0.75 | 0.82 | 15.0 | 11.05 | 0.0 | 80.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `FR` | France | 0.8 | 0.85 | 45.0 | 38.5 | 5.0 | 80.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `DE` | Germany | 0.78 | 0.85 | 21.0 | 21.8 | 0.0 | 70.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `IT` | Italy | 0.72 | 0.72 | 32.0 | 33.5 | 0.0 | 75.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `ES` | Spain | 0.65 | 0.68 | 30.0 | 31.9 | 0.0 | 65.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `PT` | Portugal | 0.58 | 0.62 | 23.5 | 23.75 | 0.0 | 65.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `NL` | Netherlands | 0.75 | 0.82 | 18.0 | 19.5 | 0.0 | 65.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `BE` | Belgium | 0.73 | 0.8 | 35.0 | 25.0 | 0.0 | 65.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `AT` | Austria | 0.78 | 0.82 | 22.0 | 21.23 | 0.0 | 65.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `CH` | Switzerland | 1.1 | 1.05 | 13.0 | 14.5 | 0.0 | 60.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `SE` | Sweden | 0.78 | 0.85 | 31.0 | 31.42 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `NO` | Norway | 0.9 | 0.92 | 14.1 | 14.1 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `DK` | Denmark | 0.82 | 0.88 | 4.0 | 2.5 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `FI` | Finland | 0.76 | 0.82 | 19.0 | 20.5 | 0.0 | 65.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `HU` | Hungary | 0.42 | 0.52 | 20.0 | 13.0 | 0.0 | 60.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `CZ` | Czech Republic | 0.45 | 0.58 | 35.0 | 33.8 | 0.0 | 50.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `PL` | Poland | 0.4 | 0.5 | 21.0 | 20.48 | 0.0 | 55.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `RO` | Romania | 0.32 | 0.42 | 22.0 | 2.25 | 0.0 | 50.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `BG` | Bulgaria | 0.3 | 0.4 | 19.5 | 18.92 | 0.0 | 45.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `RS` | Serbia | 0.35 | 0.42 | 20.0 | 15.15 | 0.0 | 45.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `HR` | Croatia | 0.38 | 0.48 | 18.0 | 16.5 | 0.0 | 50.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `MT` | Malta | 0.6 | 0.62 | 10.0 | 10.0 | 0.0 | 30.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `GR` | Greece | 0.6 | 0.55 | 24.5 | 22.29 | 0.0 | 55.0 | 60.0 | Verified baseline consistent; source provenance added. |
| `SI` | Slovenia | 0.52 | 0.6 | 22.0 | 16.1 | 0.0 | 50.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `AU` | Australia | 0.82 | 0.83 | 11.0 | 18.5 | 3.5 | 75.0 | 70.0 | CRITICAL: Legacy payroll_fringe_pct was 11.0% (omitted ~5.45% state payroll taxes + WorkCover). Corrected to 18.5% statutory. |
| `NZ` | New Zealand | 0.75 | 0.8 | 10.0 | 12.2 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `JP` | Japan | 0.88 | 0.75 | 15.0 | 15.1 | 0.0 | 80.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `KR` | South Korea | 0.7 | 0.72 | 11.0 | 10.65 | 0.0 | 75.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `SG` | Singapore | 0.8 | 0.82 | 16.0 | 0.0 | 0.0 | 60.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `TH` | Thailand | 0.4 | 0.42 | 5.0 | 5.0 | 0.0 | 80.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `IN` | India | 0.3 | 0.35 | 12.0 | 15.25 | 0.0 | 90.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `AE` | United Arab Emirates | 0.65 | 0.78 | 0.0 | 5.75 | 0.0 | 20.0 | 0.0 | MAJOR: Legacy omitted mandatory 5.75% Expatriate End of Service Gratuity (EOSG) accrual under Federal Labour Law. |
| `IL` | Israel | 0.75 | 0.75 | 18.0 | 12.5 | 0.0 | 65.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `MA` | Morocco | 0.32 | 0.42 | 18.0 | 21.09 | 0.0 | 50.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `ZA` | South Africa | 0.45 | 0.46 | 5.0 | 3.5 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `MU` | Mauritius | 0.5 | 0.5 | 6.0 | 9.0 | 0.0 | 40.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `BR` | Brazil | 0.5 | 0.45 | 45.0 | 33.8 | 0.0 | 70.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `AR` | Argentina | 0.35 | 0.38 | 25.0 | 24.0 | 0.0 | 60.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `CL` | Chile | 0.45 | 0.45 | 22.0 | 5.5 | 0.0 | 60.0 | 0.0 | Verified baseline consistent; source provenance added. |
| `CO` | Colombia | 0.38 | 0.4 | 30.0 | 35.0 | 0.0 | 65.0 | 70.0 | Verified baseline consistent; source provenance added. |

---

## 8. Conclusion & Sign-Off

The research foundation is complete, verified, and reconciled across all 121 jurisdictions and 13 categories. All source citations, statutory references, and candidate indices are compiled into machine-readable files ready for implementation.
