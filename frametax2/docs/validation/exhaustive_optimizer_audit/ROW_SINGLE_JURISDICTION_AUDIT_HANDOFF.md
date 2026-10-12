# Four-Anchor Rest-of-World (ROW) Single-Jurisdiction & Same-Jurisdiction Stack Audit — Final Handoff

## 1. Frozen Audit Baseline & Scope

- **Audited Engine Version & Commit (Frozen):**
  - Engine version: `canonical-1.122.0`
  - Frozen commits in `/Users/Suraj/cineglobe-claude-global-optimizer-remediation/frametax2`:
    - `59566fd17463b71e9796d41e8e080bf5d0ac27ea` (`HEAD` of `canonical-1.122.0`)
    - `f5dc6a17858436c0809d7830151696d036aa159b`
    - `f0b042ba039ed41e619217a4ac8758ec6814eed8`
- **Persisted Acceptance Database Baseline (`frametax2_claude_optimizer_acceptance_20260919`):**
  - `LU` (*The Little Utopia*, `fa5cade5-0669-4816-bfe6-72146f8d3bae`): `canonical-1.109.0`, Gross `$4,364,393.00`, Leaf Sum `$4,364,395.00`, Fixed US Outside `$9,068.00` (`5000 EDITORIAL`), Contingency `$301,131.00` (`8300`), Default Contingency Election `100_PCT`.
  - `FVD` (*F#K Valentine's Day*, `6c6f1c13-2d49-4bbc-bafb-2a12efa93112`): `canonical-1.106.0`, Gross `$4,517,687.00`, Contingency `$362,866.00` (`7902`), Default Contingency Election `NOT_STATED`.
  - `BH` (*Bad Hombres*, `4355ae88-a636-4c18-af60-ad73b2646124`): `canonical-1.106.0`, Gross `$2,482,023.00`, Contingency `$94,382.00` (`CONTINGENCY`), Default Contingency Election `NOT_STATED`.
  - `LLS` (*Lips Like Sugar*, `ab10b319-978e-44d3-9331-af2a5f2cccc2`): `canonical-1.110.0`, Gross `$11,983,654.00`, Contingency `$400,000.00` (`7100`), Default Contingency Election `NOT_STATED`.
- **Prospective Relocation Planning Regime Date:** `2026-10-11` (Dated FX Snapshot: `2026-07-13` ECB / `open.er-api.com` rates: `EUR = 0.87679`, `GBP = 0.74699`, `AUD = 1.5219`, `CZK = 21.238`, `ZAR = 16.3636`, `MAD = 9.847`, `THB = 35.612`, `MUR = 47.053589`). Historical award letters and historical home-jurisdiction rates are treated strictly as reference provenance and do not constrain prospective single-jurisdiction relocations.
- **Scope:** All non-US, non-Canada, non-Mexico (`ROW`) national and regional/subnational single-jurisdiction programs and lawful same-jurisdiction combinations. Cross-border multi-country hybrids and bilateral/multilateral treaty co-production structures are excluded from this package. All ROW deliverables are isolated from the `NORTH_AMERICAN_*` files under review.

---

## 2. Committed ROW Evidence Package (Exact File Paths)

1. **Program Universe (`180` ROW Program Universe Entries):**
   - [`docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_PROGRAM_UNIVERSE.csv`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_PROGRAM_UNIVERSE.csv)
2. **Expected-vs.-Audited Coverage Manifest (`772` Reconciled Project Cases, `0` Uncovered):**
   - [`docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST.csv`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST.csv)
   - [`docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST_SUMMARY.json`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST_SUMMARY.json)
3. **Comprehensive Independent Calculation & Engine Comparison Matrix (`376` Individual Evaluations):**
   - [`docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COMPREHENSIVE_MATRIX.csv`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COMPREHENSIVE_MATRIX.csv)
4. **Reproducible Independent Calculator (Offline, Deterministic, `<3s` Runtime):**
   - [`docs/validation/exhaustive_optimizer_audit/independent_row_single_jurisdiction_audit.py`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/independent_row_single_jurisdiction_audit.py)
5. **Discrepancy Register & Root-Cause Adjudication:**
   - [`docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_DISCREPANCY_REGISTER.md`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_DISCREPANCY_REGISTER.md)
6. **Retained Snapshot Input (`14.5 MB`, All 158 Source Budget Lines + Saved DB + `1.122.0` Traces):**
   - [`docs/validation/exhaustive_optimizer_audit/SAVED_ROW_SINGLE_JURISDICTION_SNAPSHOT.json`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/SAVED_ROW_SINGLE_JURISDICTION_SNAPSHOT.json)

---

## 3. Universe & Coverage Reconciliation Denominators

| Universe / Manifest Stratum | Per Project | Across 4 Anchors (`LU`, `FVD`, `BH`, `LLS`) | Disposition Summary |
|---|---:|---:|---|
| **ROW Executable `RateRule` Programs (`program_rate_rules.py` + `program_rate_rules_worldwide.py`)** | `81` | `324` | `100%` individually calculated from 158 source lines (`ROW_SINGLE_JURISDICTION_COMPREHENSIVE_MATRIX.csv`) |
| **ROW Same-Jurisdiction Stack Pairs (`eligible_for_combination = True` in same country)** | `13` | `52` | `100%` individually evaluated (`3` lawful AU Federal+State PDV stacks + `10` statutory mutual exclusions) |
| **Subtotal: Individually Calculated Matrix Evaluations** | **`94`** | **`376`** | **`261` Exact Matches + `100` Active Defect Rows + `3` Stale DB Rows + `8` Disclosed Sub-Cap Rows + `4` Probe/Stack Rows** |
| **Omitted Official National / Subnational Regimes (Primary Statutes)** | `9` | `36` | `4` priceable Spanish regional/foral regimes (`ES-CN`, `ES-PV-BI`, `ES-PV-SS`, `ES-NC`) + `5` domestic/co-pro/series regimes |
| **Non-Rate Canonical Registry Identities (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`, `DEPRECATED_DUPLICATE`, etc.)** | `90` | `360` | `100%` accounted for with explicit rule-backed dispositions (`ROW_SINGLE_JURISDICTION_COVERAGE_MANIFEST.csv`) |
| **Total Reconciled ROW Manifest Cases** | **`193`** | **`772`** | **`772 / 772` Reconciled (`0` Uncovered)** |

---

## 4. Source-Account Expenditure Buckets & Contingency Separation Across the Four Anchors

All independent calculations derive directly from the `158` retained `budget_line_items` (`39` on `LU`, `36` on `FVD`, `38` on `BH`, `45` on `LLS`) in [`docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/FOUR_ANCHOR_SOURCE_DETAIL_EVIDENCE.json) by exact `line_id` and `account_code`:

| Metric / Expenditure Bucket | `LU` (*Little Utopia*) | `FVD` (*F#K Valentine's Day*) | `BH` (*Bad Hombres*) | `LLS` (*Lips Like Sugar*) |
|---|---:|---:|---:|---:|
| **Gross Production Budget (USD)** | `$4,364,393.00` | `$4,517,687.00` | `$2,482,023.00` | `$11,983,654.00` |
| **Fixed Outside-Jurisdiction Spend (`outside_location_allocations`)** | `$9,068.00` (`5000 EDITORIAL` in `US`) | `$0.00` | `$0.00` | `$0.00` |
| **Unallocated Contingency Reserve (`contingency`)** | `$301,131.00` (`8300`) | `$362,866.00` (`7902`) | `$94,382.00` (`CONTINGENCY`) | `$400,000.00` (`7100`) |
| **Finance Costs (`finance_costs`)** | `$0.00` | `$453,583.00` (`7802`) | `$0.00` | `$1,700,000.00` (`6800`) |
| **Residuals Reserve (`residuals_reserve`)** | `$0.00` | `$0.00` | `$60,000.00` (`5200`) | `$400,000.00` (`6900`) |
| **Standard Open-Default-Include Local QPE Floor (USD)** | **`$4,054,196.00`** | **`$3,701,238.00`** | **`$2,327,641.00`** | **`$9,483,654.00`** |
| **80%-Capped Territorial QPE (`DE`, `FR`, `GR`, `HU`, `IE`, `IS`, `IT`, `LV`, `ME`, `RS`, `SK`, `UK`, `UY`)** | **`$3,484,260.00`** | **`$3,614,149.60`** | **`$1,985,618.40`** | **`$9,483,654.00`** (`< 80% * $11.98M`) |
| **Greece KYA 607434 Annex B.3 Post-Share-Cap QPE (`5%` Ins+Bond & `30%` W+D+C)** | **`$3,484,260.00`** | **`$3,037,985.71`** | **`$1,637,011.43`** | **`$9,483,654.00`** |
| **Cyprus Post-30%-ATL-Share-Cap QPE (`cy_film_rebate`)** | **`$4,054,196.00`** | **`$2,463,941.43`** | **`$1,255,341.43`** | **`$9,463,615.71`** |
| **Spain Art. 36.2 LIS Category 2 Technical/Supplier QPE Floor (`es_tax_credit_foreign`)** | **`$3,888,683.00`** | **`$1,724,759.00`** | **`$878,739.00`** (`< EUR 1M`) | **`$6,624,531.00`** |
| **Strict Post / Digital / VFX Component QPE (`ROW_PDV_POST_ONLY_SLUGS`)** | **`$52,500.00`** (`6100`) | **`$166,646.00`** (`4600,5000..5700`) | **`$110,958.00`** (`4300,4600..4800`) | **`$736,762.00`** (`4400..4900,5800,5900`) |

### Contingency Reserve Treatment Across All Scenarios
- **Confirmed QPE Floor:** Unallocated contingency reserve (`8300` `$301,131` on `LU`; `7902` `$362,866` on `FVD`; `CONTINGENCY` `$94,382` on `BH`; `7100` `$400,000` on `LLS`) is excluded from confirmed QPE floor across all deterministic programs.
- **Planned Cost Reduction Applied Once:** Under `0_PCT` utilization, planned cost decreases by `100%` of the reserve (`$4,063,262` on `LU`, `$4,154,821` on `FVD`, `$2,387,641` on `BH`, `$11,583,654` on `LLS`); under `50_PCT` utilization, planned cost decreases by `50%` of the reserve; under `100_PCT` utilization (`and NOT_STATED`), planned cost equals `100%` of gross budget.
- **Bounded Conditional Deployed-Contingency Upside:** Column `conditional_100pct_deployed_contingency_incentive_usd` in [`ROW_SINGLE_JURISDICTION_COMPREHENSIVE_MATRIX.csv`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/docs/validation/exhaustive_optimizer_audit/ROW_SINGLE_JURISDICTION_COMPREHENSIVE_MATRIX.csv) reports the exact conditional incentive ceiling if `100%` of utilized contingency is deployed into qualifying local BTL accounts (subject to each program's `80%` QPE cap and per-project dollar cap).

---

## 5. Summary of Supported Active Defects, Stale DB Rows, and Limitations

### A. Active Code Defects in Frozen Engine `canonical-1.122.0` (`100` Matrix Rows)
1. **`ROW-DEF-001` (`es_tax_credit_foreign`, `4` rows — [`program_spend_rules.py:782-795`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/data/program_spend_rules.py#L782-L795)):** `ES_RULES` omits `miscellaneous`, `production_sound`, and `general_administration` while marking `contingency` as `qualifies=True`. Drops `$899,254.00` of BTL technical spend on `FVD` (causing a **false `STATUTORY_CONDITIONS_UNMET` rejection** on `FVD`, where true Category 2 QPE is `$1,724,759.00 >= $1,140,523.96` and guaranteed credit is **`$488,115.95`**), drops `$2,556,576.00` on `LLS` (understating `LLS` guaranteed credit by **`-$639,144.00`**, `$1,074,014.95` vs **`$1,713,158.95`**), drops `$468,346.00` from the `BH` probe (`$410,393` vs `$878,739`), and on `LU` omits `3200 PRODUCTION SOUND ($69,532)` while adding `$301,131` of unallocated contingency into `qpe_usd`.
2. **`ROW-DEF-002` (`5` ROW PDV/Post-VFX programs, `20` rows — [`program_spend_rules.py:169-172, 254`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/data/program_spend_rules.py#L169-L172)):** `au_pdv_offset`, `au_nsw_pdv_rebate`, `au_qld_pdv_rebate`, `au_sa_pdv_rebate`, and `new_zealand_screen_production_grant_—_international_post_vfx` are classified as `OPEN_DEFAULT_INCLUDE` instead of `POST_VFX_ONLY` and priced on 100% of all-production spend. Causes **13 false eligibilities** (`5/5` on `LU`, `3/5` on `FVD`, `5/5` on `BH`) and **7 gross overstatements** (`2/5` on `FVD` and `5/5` on `LLS`, overstating `LLS` `au_pdv_offset` by **`+$2,624,067.60`**). Also models `au_qld_pdv_rebate` at a stale `10%` rate instead of `15%`.
3. **`ROW-DEF-003` (`ma_ccm_rebate`, `4` rows — [`program_rate_rules.py:3380-3395`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/program_rate_rules.py#L3380-L3395) & [`allocation_pricing.py:524-540`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/allocation_pricing.py#L524-L540)):** `build_discovery_amount_probe` seeds non-currency `ma_ccm_shooting_days_count` with `qpe_usd`, passing preflight while `price_segment` leaves `ma_ccm_shooting_days_count = None` (`priced=True, is_fully_priced=False, selected_incentive_usd=0.0`), and omits Morocco's statutory `90%` QPE cap from `QPE_CAP_RULES`.
4. **`ROW-DEF-004` (`13` ROW Same-Jurisdiction Stack Pairs, `52` rows — [`canonical_stack_bridge.py:258-347`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/canonical_stack_bridge.py#L258-L347)):** `_SLUG_PAIR_RULES` has zero rules for all 13 ROW same-country stack pairs. Falsely rejects the **3 lawful Australia Federal + State PDV stacks on `LLS`** (`au_pdv_offset + au_nsw_pdv_rebate` **`$294,704.80`**, `au_pdv_offset + au_qld_pdv_rebate` **`$331,542.90`**, `au_pdv_offset + au_sa_pdv_rebate` **`$294,704.80`**) as `UNRESOLVED_NO_AUTHORITY`, rejects them for the wrong reason on `LU`/`FVD`/`BH`, and labels `10` statutory mutual exclusions (`40` rows) as `UNRESOLVED_NO_AUTHORITY` instead of `INCOMPATIBLE_MUTUAL_EXCLUSION`.
5. **`ROW-DEF-005` (`cy_film_rebate`, `4` rows — [`program_rate_rules.py:168-273`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/program_rate_rules.py#L168-L273)):** Omits Invest Cyprus's `30%` ATL share cap (overstating `BH` guaranteed rebate by **`+$210,630.50`**, `$650,000.00` vs **`$439,369.50`**) and hardcodes `EUR 650,000` at 1:1 USD (`$650,000.00` instead of `$741,340.57` at `0.87679 EUR/USD`, understating `LU`, `FVD`, and `LLS` capped rebates by **`-$91,340.57`**).
6. **`ROW-DEF-006` (`au_producer_offset`, `4` rows — [`program_rate_rules.py:1395-1431`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/program_rate_rules.py#L1395-L1431)):** Orphan `RateRule` slug not wired to `jurisdiction_comparison.ALL_PROFILES` (`canonical_program_registry.py` registers `proposed_australia_producer_offset_separate_statutory_program` instead), and lacks the mandatory SAC / Official Co-Production gate and `80%` QPE cap.
7. **`ROW-DEF-007` (`lu_filmfund_tax_shelter_rebate`, `no_film_incentive`, `sa_film_commission_rebate`, `tw_bamid_rebate`, `16` rows — [`canonical_evaluation.py:3847-3880`](file:///Users/Suraj/cineglobe-ag-exhaustive-optimizer-audit/frametax2/backend/app/services/canonical_evaluation.py#L3847-L3880)):** `_capability_only_status()` omits `_economic_block_for_program()`, misclassifying 4 `DISPLAY_ONLY_ZERO_GUARANTEED` selective/discretionary programs as `RULE_REJECTED / STATUTORY_CONDITIONS_UNMET` in `evaluation_candidate_aggregates` instead of `FEASIBILITY_REVIEW_REQUIRED` in `structure_calculation_results`.

### B. Stale Saved DB Rows Repaired in `canonical-1.122.0` (`3` Matrix Rows)
- **`ROW-STALE-DB-001` (`gr_cash_rebate` on `FVD` and `BH`, `canonical-1.106.0`):** Saved DB rows (`$1,445,659.84` on `FVD`, `$794,247.36` on `BH`) predate Greece KYA 607434 Annex B.3 share caps (`30%` writer/director/cast and `5%` insurance/bond), which are enforced in `canonical-1.122.0` (`$1,215,194.28` on `FVD`, `$654,804.57` on `BH`).
- **`ROW-STALE-DB-002` (`za_nfvf_rebate` on `LLS`, `canonical-1.110.0`):** Saved DB row (`$1,511,490.41` at `16.54 ZAR/USD`) differs from `canonical-1.122.0` (`$1,527,781.17` at `16.3636 ZAR/USD`) due to FX snapshot update on the `ZAR 25,000,000` cap.

### C. Remaining Genuine Producer-Input & Primary-Authority Limitations (Honest Disclosure)
1. **Producer-Fact Conditional Regimes (`28` Matrix Rows across `7` Slugs):**
   - `ma_ccm_rebate` (`MA`): Requires producer shooting schedule confirming `>= 18` principal photography days in Morocco (`ma_ccm_shooting_days_count`).
   - `nl_film_production_incentive` (`NL`): Requires Netherlands Film Fund points/independence test and format confirmation (`nl_nfpi_points_independence_test_passed`).
   - `gb_iftc_enhanced_avec` (`GB`): Requires BFI British film cultural test or official bilateral/European Convention co-production certification (`uk_bfi_cultural_test_passed`).
   - `cl_corfo_incentive` (`CL`), `ee_film_estonia_rebate` (`EE`), `pe_film_incentive` (`PE`), `si_cash_rebate` (`SI`): Require local-content scoring or investor tax-rate facts to unlock conditional ceilings.
2. **Selective / Discretionary Regimes Without Automatic Statutory Floor (`32` Matrix Rows across `8` Slugs):**
   - `jp_vipo_location_incentive` (`JP`), `kr_kofic_location_incentive` (`KR`), `lu_filmfund_tax_shelter_rebate` (`LU`), `no_film_incentive` (`NO`), `sa_film_commission_rebate` (`SA`), `se_production_rebate` (`SE`), `sg_made_with_singapore_rebate` (`SG`), and `tw_bamid_rebate` (`TW`) are selective/committee-awarded funds with `$0` unconditional guaranteed floor; their maximum statutory rates are reported strictly as conditional upside.
3. **Unavailable Primary Statutory Rate Authority (`8` Matrix Rows across `2` Slugs in `RateRule` + `32` Non-Rate Canonical Slugs):**
   - `cr_tax_return_incentive` (Costa Rica Law No. 10071) and `kz_investment_subsidy` (Kazakhstan Entrepreneurship Code Art. 286 / Kazakhcinema Order No. 79) have enacted enabling statutes whose specific implementing rate schedules/regulations could not be verified from primary government publications (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`). Both are explicitly recorded as unpriced authority limitations rather than forced or estimated calculations.
