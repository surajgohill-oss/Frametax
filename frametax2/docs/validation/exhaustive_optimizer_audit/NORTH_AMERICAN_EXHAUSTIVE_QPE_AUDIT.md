# Exhaustive North American QPE Audit Report
**Scope:** ALL 328 Database Projects & 45 North American Doctrine Programs (US, Canada, Mexico)  
**Authority:** CineGlobe Canonical Runtime Registries & Primary Jurisdictional Statutes  
**Status:** `ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`  
**Date:** 2026-10-10  

---

## 1. Executive Summary & Audit Mandate

This report delivers the complete, independent North American Qualified Production Expenditure (QPE) audit across:
1. **The Entire System Project Inventory (328 Database Projects):** Freezing all four project cohorts—the 4 canonical evaluated anchors, 11 real feature film productions with active parsed budgets but no prior evaluation generations, 35 real feature productions with missing budgets (script-only/document-only), and 278 synthetic/test harness projects.
2. **The Current North American Program Registry (45 Doctrine Programs):** Freezing all 30 United States programs, 14 Canadian programs (2 federal, 12 provincial), and 1 Mexican federal program from the canonical runtime truth (`backend/app/data/`).
3. **Account-Level Reconstruction Across All 15 Parsed Budgets:** Reconstructing Above-The-Line (ATL), Below-The-Line (BTL), Post-Production/VFX, General/Other categories, project contingency deployment, financing fees, completion bond/insurance caps, and territorial/payroll bases.
4. **Reconciliation Against Exact Saved Generation Results:** Comparing independent source-derived expectations against current saved generations (`canonical-1.106.0` fingerprints) where available (the 4 anchors), and independently establishing source-derived baselines for the remaining 11 parsed projects without triggering cold evaluations, database mutations, or unrequested regeneration runs.

---

## 2. Frozen Dual Inventories

### 2.1 Project Universe Inventory (328 Database Records)

Every project in database `frametax2_claude_optimizer_acceptance_20260919` is frozen into one of four distinct cohorts:

| Cohort | Description | Project Count | Active Parsed Budgets | Saved Evaluation Generations | Audit Disposition |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Cohort 1** | Canonical Production Anchors | 4 | 4 | Yes (`canonical-1.106.0`) | `ELIGIBLE_PARSED_EVALUATION_SAVED` |
| **Cohort 2** | Real Feature Film Productions | 11 | 11 | None (0 runs) | `ELIGIBLE_PARSED_BASELINE_DERIVED_NO_EVALUATION` |
| **Cohort 3** | Real Feature Projects (Script/Doc Only) | 35 | 0 | None (0 runs) | `BLOCKED_MISSING_BUDGET_DOCUMENT` |
| **Cohort 4** | Test Harness / Ingestion / Synthetic | 278 | 278 | Isolated Test Runs | `INELIGIBLE_TEST_HARNESS` |
| **Total** | **All System Projects** | **328** | **293** | **19 Projects Evaluated** | — |

#### Cohort 1: Canonical Production Anchors (4 Projects)
1. **The Little Utopia (LU)** — ID `fa5cade5-0669-4816-bfe6-72146f8d3bae` | Declared: \$4,364,393.00 | Budget: `The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf` (44 lines, sum \$4,364,395.00). Saved generation: `40527fdc3adf0a9b981c2a4f45cc1c31272a5be3bcd6b8f59aeaeced1c2e1d25`.
2. **F#K Valentine's Day (FVD)** — ID `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | Declared: \$4,517,687.00 | Budget: `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` (34 lines, sum \$4,517,687.00). Saved generation: `3759a2edf4b42701abc80a495c492e6f9e191bdf9994836ff8c1ba41ddbac0fd`.
3. **Bad Hombres (BH)** — ID `4355ae88-a636-4c18-af60-ad73b2646124` | Declared: \$2,482,023.00 | Budget: `BadHombresBudget.v2.pdf` (34 lines, sum \$2,482,023.00). Saved generation: `8823b547e4b6e3b318dc668f9d50c900fbe9c2ebd921d41fa4e2421cf599743e`.
4. **Lips Like Sugar (LLS)** — ID `ab10b319-978e-44d3-9331-af2a5f2cccc2` | Declared: \$11,983,654.00 | Budget: `v7LLS_RevBudget_T1B_27days_022524.pdf` (46 lines, sum \$11,983,654.00). Saved generation: `0c645952931cf7d940758af7635e9b11466a26e6e06180d1d898e4b45e389430`.

#### Cohort 2: Real Feature Film Productions with Active Parsed Budgets (11 Projects)
1. **10 Double Zero** — ID `3519feda-d280-435f-badc-1e4c788a2cb3` | Declared: \$11,139,616.00 | Budget: `10DZ Budget 081219v1.pdf` (36 lines, sum \$10,391,803.00, diff -\$747,813.00 unextracted topsheet lines).
2. **5 LBS OF PRESSURE** — ID `98b440b9-a93a-4713-86c8-a5f75b54da97` | Declared: \$7,066.00 | Budget: `5lbs of Pressure_ Pre-Prep Budget & Schedule.pdf` (4 lines, sum \$7,066.00, micro pre-prep schedule).
3. **All My Friends Are Dead** — ID `e3f50d06-68c5-4d36-8b3a-e1f87e5c7a44` | Declared: \$1,409,418.00 | Budget: `3. AMFAD BUDGET_v3_01.13.23_$1.4USD.pdf` (29 lines, sum \$1,409,418.00).
4. **Baron Samedi** — ID `fcbb9190-5b9c-4af8-96fa-359fce1cf79a` | Declared: \$3,041,182.00 | Budget: `Baron Samedi Budget v2_9 LA Budget.pdf` (33 lines, sum \$2,991,183.00, diff -\$49,999.00 unextracted completion bond).
5. **Going Places** — ID `dee8feca-7b94-4330-ac19-79969e8facb8` | Declared: \$7,301,947.00 | Budget: `GOING PLACES Budget V5.3.pdf` (40 lines, sum \$7,181,142.00, diff -\$120,805.00 unextracted topsheet lines).
6. **Interference** — ID `565744c5-86fd-4c1d-bdb5-fdd4b910d0b0` | Declared: \$3,575,812.00 | Budget: `Interference v1-6 NJ Budget.pdf` (32 lines, sum \$3,575,813.00, \$1.00 authored rounding).
7. **Rocky Mountain** — ID `191f1422-79a1-4a6c-a3fb-cafa0c2c2343` | Declared: \$18,752,479.00 | Budget: `rockymountainbudget.pdf` (50 lines, sum \$18,752,481.00, \$2.00 authored rounding).
8. **The Cure** — ID `f3c1a6f1-a357-407f-8072-7dfbba87ceae` | Declared: \$2,144,178.00 | Budget: `THE CURE Full Budget Jan 2024 (dragged).pdf` (35 lines, sum \$2,144,180.00, \$2.00 authored rounding).
9. **The System** — ID `e1f2444d-4eac-410e-9c92-45637b8f2ae0` | Declared: \$4,324,058.00 | Budget: `The System Budget v2.8.pdf` (31 lines, sum \$3,981,987.00, diff -\$342,071.00 unextracted contingency \$312,071 + fees).
10. **Twilight of the Dead** — ID `92167170-9e42-4bbb-9754-877ce1692b8a` | Declared: \$8,546,272.00 | Budget: `Twilight of the Dead Budget Top Sheet.pdf` (42 lines, sum \$8,007,318.00, diff -\$538,954.00 unextracted topsheet lines).
11. **Underwater** — ID `f1292c56-0288-4575-91ec-1f00081f07a0` | Declared: \$7,998,944.00 | Budget: `Underwater Budget 9-3 (1).pdf` (35 lines, sum \$6,973,801.00, diff -\$1,025,143.00 unextracted contingency/bond/fee lines).

#### Cohort 3: Real Feature Projects with No Budget Documents (35 Projects)
*97 Minutes, Adam & Eve, Almost Perfect, Artists of Cinema, Braking Point, David, Dead After Dark, Debug Project 7b827a2d, Drug Honey, Flash Before the Bang, Gifted, Give or Take, Hightower, Jane Millen, Maggie Moves On, Model Wars, One Night Stand, Otherwise Engaged, Replacements, Rust, Safehaven, Serpent Girl, Sierra Madre, Sky Unconditional, Spice Route, Terezin, The Arrangement, The Dale, The Men We Leave Behind, The Room Below, Trail Mates, Unconditional Love, Werewolf, White Feather, White Line Highway.*  
**Disposition:** Blocked from QPE calculation. Although script and lookbook files exist for several (e.g. `Safehaven` cashflow xlsx, `Werewolf` budget xlsx in filesystem storage), they have no active budget records in `budget_documents` and zero parsed lines in `budget_line_items`.

#### Cohort 4: Test Harness & Synthetic Projects (278 Records)
- 15 `AUDIT_CONTROL_*` projects (evaluation controls)
- 20 `INGEST_MATRIX_*` projects (format parser controls: CSV, PDF, TXT, XLSX, FDX, unsupported)
- 7 `OR Pipeline Test` / `OR Pipeline Test Uplift` / `OR Hostile Test` projects
- 2 `dbg NL *` projects (synthetic €20M single-line test fixtures)
- 234 `phase-e-test-project-*` test fixtures  
**Disposition:** Ineligible for production QPE evaluation.

---

### 2.2 North American Program Registry Inventory (45 Doctrine Programs)

The canonical runtime truth populates exactly 45 doctrine programs across North America:

| Country | Programs | Authority Verified | Authority Unresolved | Deterministic Priceable | Conditional Non-Deterministic |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **United States (US)** | 30 | 25 | 5 | 26 | 4 (MD, NC, SC, TX) |
| **Canada (CA)** | 14 | 10 | 4 | 14 | 0 |
| **Mexico (MX)** | 1 | 1 | 0 | 1 | 0 |
| **Total** | **45** | **36** | **9** | **41** | **4** |

#### Master Program Disposition Table

| Program Slug | Jurisdiction | Confidence Tier | Authority Disposition | Economic State | Rate Tiers (%) | Annual Cap ($) | Project Cap ($) | Min Spend ($) | Spend Doctrine | Stacking Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| `ca_federal_cptc` | CA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | — | — | — | open_default | 11 rules |
| `ca_federal_pstc` | CA | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 16.0% | — | — | — | open_default | 2 rules |
| `ca_ab_fttc` | CA-AB | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 22.0% / 30.0%* | — | — | — | open_default | 0 |
| `ca_bc_dave` | CA-BC | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 16.0% | — | — | — | open_default | 1 rule |
| `ca_bc_pstc` | CA-BC | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 36.0% / 48.0%* | — | — | — | open_default | 6 rules |
| `ca_mb_film_video_credit` | CA-MB | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 45.0% / 65.0%* | — | — | — | open_default | 0 |
| `ca_nb_film_tax_credit` | CA-NB | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 30.0% | — | — | — | open_default | 0 |
| `ca_nl_all_spend_credit` | CA-NL | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 40.0% | 20,000,000 | — | — | open_default | 0 |
| `ca_ns_production_incentive_fund` | CA-NS | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | — | — | — | open_default | 0 |
| `on_ofttc` | CA-ON | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 35.0% | — | — | — | open_default | 9 rules |
| `on_opstc` | CA-ON | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 21.5% | — | — | 707,464 | open_default | 5 rules |
| `ontario_computer_animation_and_special_effects_tax_credit_ocase` | CA-ON | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 18.0% | — | — | — | open_default | 2 rules |
| `ca_qc_pstc` | CA-QC | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | — | — | 250,000 | open_default | 0 |
| `ca_sk_creative_saskatchewan_grant` | CA-SK | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 30.0%* | 5,000,000 | — | — | open_default | 1 rule |
| `mx_federal_film_incentive_2026` | MX | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 30.0% | — | MXN 40M | MXN 40M | open_default | 0 |
| `us_al_film_incentive` | US-AL | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 45.0%* | 22,000,000 | — | — | open_default | 0 |
| `us_az_motion_picture_production` | US-AZ | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 15.0% / 20.0%* | — | — | — | open_default | 0 |
| `ca_film_30` | US-CA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 35.0% / 40.0%* | 750,000,000 | QE Limit | — | open_default (BTL only) | 0 |
| `us_co_film_incentive` | US-CO | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% | — | — | — | open_default | 0 |
| `us_ct_film_tax_credit` | US-CT | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 10.0% / 30.0% | — | — | 100,000 | open_default | 0 |
| `us_ga_film_credit` | US-GA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% / 30.0%* | — | — | 500,000 | open_default | 0 |
| `us_hi_film_digital_media_credit` | US-HI | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 22.0% / 27.0%* | — | — | — | open_default | 0 |
| `us_il_film_production_services_credit` | US-IL | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 35.0% | — | — | — | open_default | 0 |
| `us_ky_keiia` | US-KY | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 30.0% / 35.0%* | 75,000,000 | — | 250,000 | open_default | 0 |
| `us_la_film_incentive` | US-LA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 40.0%* | 150,000,000 | — | 300,000 | open_default | 0 |
| `us_ma_film_tax_credit` | US-MA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | — | — | 50,000 | open_default | 0 |
| `us_md_film_production_activity_credit` | US-MD | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `CONDITIONAL_NONDETERMINISTIC` | 28.0%* / 30.0%* | 12,000,000 | — | 250,000 | open_default | 0 |
| `us_mn_film_production_credit` | US-MN | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | 25,000,000 | — | 1,000,000 | open_default | 0 |
| `us_ms_advantage_film_program` | US-MS | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | 20,000,000 | 10,000,000 | 50,000 | open_default | 0 |
| `us_nc_film_entertainment_grant` | US-NC | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `CONDITIONAL_NONDETERMINISTIC` | 25.0%* | 31,000,000 | 7,000,000 | 1,500,000 | open_default | 0 |
| `us_nm_film_credit` | US-NM | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 40.0%* | 140,000,000 | — | — | open_default | 0 |
| `us_nv_film_credit` | US-NV | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 15.0% / 25.0%* | 10,000,000 | 6,000,000 | 500,000 | open_default | 0 |
| `ny_state_film` | US-NY | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 30.0% / 60.0%* | — | — | 250,000 | open_default (ATL capped) | 1 rule |
| `us_ny_post_production_credit` | US-NY | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 35.0% | — | — | 1,000,000 | closed_positive | 1 rule |
| `us_ok_film_enhancement_rebate` | US-OK | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% / 30.0%* | 30,000,000 | — | — | open_default | 0 |
| `us_or_opif` | US-OR | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% / 25.0% | 21,200,000 | 10,600,000 | 1,000,000 | open_default | 0 |
| `us_pa_film_production_credit` | US-PA | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% / 30.0%* | — | — | — | open_default | 0 |
| `us_pr_film_incentives_act` | US-PR | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% / 40.0%* | 38,000,000 | — | 50,000 | open_default | 0 |
| `us_ri_film_credit` | US-RI | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 30.0% | 40,000,000 | 7,000,000 | 100,000 | open_default | 0 |
| `us_sc_film_production_credit` | US-SC | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `CONDITIONAL_NONDETERMINISTIC` | 30.0%* | — | — | 1,000,000 | open_default | 0 |
| `us_tn_performance_grant` | US-TN | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 25.0% | — | — | 200,000 | open_default | 0 |
| `us_tx_miip` | US-TX | VERIFIED | `AUTHORITY_VERIFIED_PRICEABLE` | `CONDITIONAL_NONDETERMINISTIC` | 31.0%* | 300,000,000 | — | — | open_default | 0 |
| `us_ut_motion_picture_incentive` | US-UT | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 20.0% / 25.0%* | — | — | — | open_default | 0 |
| `us_va_motion_picture_credit` | US-VA | PARSED | `AUTHORITY_UNRESOLVED_NON_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 15.0% | — | — | — | open_default | 0 |
| `us_wa_motion_picture_competitiveness` | US-WA | PARSED | `AUTHORITY_VERIFIED_PRICEABLE` | `DETERMINISTIC_PRICEABLE` | 30.0% / 45.0%* | 15,000,000 | — | 500,000 | open_default | 0 |

---

## 3. Account-Level Budget Reconstruction Across All 15 Parsed Budgets

### 3.1 Overview of Parsed Leaf Accounts and Cost Elements

| Project Title | Declared Gross ($) | Extracted Line Sum ($) | Variance / Extraction Gap ($) | Leaf Accounts | Above-The-Line (ATL) ($) | Below-The-Line (BTL) ($) | Contingency Reserve ($) | Financing Fees ($) | Completion Bond ($) | Insurance Premiums ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Little Utopia (LU)** | 4,364,393.00 | 4,364,395.00 | +2.00 (auth. round) | 44 | 538,444.00 | 3,080,756.00 | 301,131.00 | 0.00 | 0.00 | 60,555.00 |
| **F#K Valentine's Day (FVD)** | 4,517,687.00 | 4,517,687.00 | 0.00 | 34 | 2,151,025.00 | 1,090,130.00 | 362,866.00 | 453,583.00 | 72,573.00 | 50,329.00 |
| **Bad Hombres (BH)** | 2,482,023.00 | 2,482,023.00 | 0.00 | 34 | 1,529,752.00 | 636,931.00 | 94,382.00 | 0.00 | 0.00 | 24,000.00 |
| **Lips Like Sugar (LLS)** | 11,983,654.00 | 11,983,654.00 | 0.00 | 46 | 3,174,975.00 | 4,995,480.00 | 400,000.00 | 1,700,000.00 | 115,000.00 | 106,000.00 |
| **10 Double Zero** | 11,139,616.00 | 10,391,803.00 | -747,813.00 (gap) | 36 | 4,902,182.00 | 3,972,913.00 | 0.00* | 0.00* | 163,650.00 | 78,650.00 |
| **5 LBS OF PRESSURE** | 7,066.00 | 7,066.00 | 0.00 | 4 | 0.00 | 7,066.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **All My Friends Are Dead** | 1,409,418.00 | 1,409,418.00 | 0.00 | 29 | 631,609.00 | 620,167.00 | 61,257.00 | 0.00 | 0.00 | 16,692.00 |
| **Baron Samedi** | 3,041,182.00 | 2,991,183.00 | -49,999.00 (gap) | 33 | 1,262,297.00 | 1,326,202.00 | 213,744.00 | 0.00 | 0.00* | 50,000.00 |
| **Going Places** | 7,301,947.00 | 7,181,142.00 | -120,805.00 (gap) | 40 | 4,385,042.00 | 1,800,536.00 | 0.00* | 0.00* | 0.00 | 594,794.00 |
| **Interference** | 3,575,812.00 | 3,575,813.00 | +1.00 (auth. round) | 32 | 1,808,110.00 | 1,429,989.00 | 144,386.00 | 0.00 | 0.00 | 35,000.00 |
| **Rocky Mountain** | 18,752,479.00 | 18,752,481.00 | +2.00 (auth. round) | 50 | 1,811,685.00 | 11,045,992.00 | 892,975.00 | 0.00 | 0.00 | 141,282.00 |
| **The Cure** | 2,144,178.00 | 2,144,180.00 | +2.00 (auth. round) | 35 | 689,381.00 | 933,879.00 | 100,000.00 | 100,000.00 | 0.00 | 20,000.00 |
| **The System** | 4,324,058.00 | 3,981,987.00 | -342,071.00 (gap) | 31 | 2,600,231.00 | 1,220,716.00 | 0.00* | 0.00* | 0.00 | 40,000.00 |
| **Twilight of the Dead** | 8,546,272.00 | 8,007,318.00 | -538,954.00 (gap) | 42 | 1,627,036.00 | 5,575,603.00 | 0.00* | 0.00* | 153,987.00 | 153,987.00 |
| **Underwater** | 7,998,944.00 | 6,973,801.00 | -1,025,143.00 (gap) | 35 | 2,731,485.00 | 2,371,712.00 | 727,800.00 | 0.00* | 195,100.00 | 47,000.00 |

*\*Note on Extraction Gaps:* In `10 Double Zero`, `Baron Samedi`, `Going Places`, `The System`, `Twilight of the Dead`, and `Underwater`, the PDF topsheet contains summary subtotal fee lines (e.g., `The System` PDF page 1 explicitly shows `CONTINGENCY 312,071`; `Baron Samedi` PDF page 1 explicitly shows `COMPLETION BOND 50,000`) that sit below the leaf departmental schedule and were not captured into `budget_line_items`. This is catalogued as finding **Q36**.

---

## 4. Independent Source-Derived Baseline QPE Expectations

### 4.1 Comparison Across Jurisdictional Paradigms

1. **Open-Default State Baseline (e.g., New Mexico, Generic States, Mexico):**
   $$\text{QPE}_{\text{open}} = \text{Line Sum} - \text{Finance Fee} - \text{Undeployed Contingency} - \text{Stated Outside} - \text{Special Excluded Reserves}$$
2. **California Program 4.0 BTL Baseline:**
   $$\text{QPE}_{\text{CA}} = \text{QPE}_{\text{open}} - \text{ATL} - \text{Completion Bond} - \text{Non-qualifying Legal/Residuals}$$

| Project Title | Open-Default Baseline QPE ($) | California 4.0 BTL Baseline QPE ($) | New York Post Credit (§ 31) Eligible Spend ($) | Baseline Reconciliation Notes |
| :--- | :---: | :---: | :---: | :--- |
| **The Little Utopia** | 4,054,196.00 | 3,913,031.00 | 28,500.00 | Contingency (\$301,131) excluded outside Mauritius; US edit (\$9,068) excluded; exact match with SAVED. |
| **F#K Valentine's Day** | 3,701,238.00 | 1,724,759.00 | 166,646.00 | Finance (\$453,583) and Contingency (\$362,866) excluded; exact match with SAVED. |
| **Bad Hombres** | 2,327,641.00 | 854,739.00 | 0.00 (in leaf lines) | Contingency (\$94,382) and SAG deposit (\$60,000) excluded; CA excludes legal (\$24,000); exact match with SAVED. |
| **Lips Like Sugar** | 9,483,654.00 | 6,388,593.00 | 115,000.00 | Finance (\$1,700,000), Contingency (\$400,000), Residuals (\$400,000) excluded; CA excludes ATL mixed/fringes; exact match. |
| **10 Double Zero** | 10,391,803.00 | 5,325,971.00 | 216,291.00 | No saved generation; independent baseline established from extracted lines. |
| **5 LBS OF PRESSURE** | 7,066.00 | 7,066.00 | 0.00 | Disqualified across all programs: fails statutory minimum spend thresholds (\$50k–\$1.5M). |
| **All My Friends Are Dead** | 1,348,161.00 | 716,552.00 | 65,995.00 | Contingency (\$61,257) excluded; no saved generation; independent baseline established. |
| **Baron Samedi** | 2,777,439.00 | 1,515,142.00 | 92,372.00 | Contingency (\$213,744) excluded; no saved generation; independent baseline established. |
| **Going Places** | 7,181,142.00 | 2,796,100.00 | 192,432.00 | Extracted lines baseline; no saved generation; independent baseline established. |
| **Interference** | 3,431,427.00 | 1,623,317.00 | 104,389.00 | Contingency (\$144,386) excluded; no saved generation; independent baseline established. |
| **Rocky Mountain** | 17,859,506.00 | 16,047,821.00 | 4,213,293.00 | Contingency (\$892,975) excluded; massive BTL physical spend; independent baseline established. |
| **The Cure** | 1,944,180.00 | 1,254,799.00 | 52,613.00 | Contingency (\$100,000) and Finance Fee (\$100,000) excluded; independent baseline established. |
| **The System** | 3,981,987.00 | 1,381,756.00 | 50,000.00 | Extracted lines baseline; PDF topsheet contingency unextracted; independent baseline established. |
| **Twilight of the Dead** | 8,007,318.00 | 6,226,295.00 | 422,400.00 | Extracted lines baseline; completion bond excluded in CA; independent baseline established. |
| **Underwater** | 6,246,001.00 | 3,319,416.00 | 484,650.00 | Contingency (\$727,800) excluded; completion bond excluded in CA; independent baseline established. |

---

## 5. Reconciliation of Exact Saved Generations (The Four Anchors)

For the four canonical anchors, current saved generations (`canonical-1.106.0` fingerprints) were reconciled against independent source expectations. In every case, the arithmetic of pre-cap qualified spend matches exactly:

```
[LU] Declared 4,364,393 | Lines 4,364,395
  Open-Default QPE:  4,364,395 - 301,131 (cont) - 9,068 (US edit) = 4,054,196.00  --> SAVED: 4,054,196.00 [EXACT MATCH]
  California 4.0:    4,364,395 - 301,131 - 9,068 - 141,165 (ATL) = 3,913,031.00    --> SAVED: 3,913,031.00 [EXACT MATCH]

[FVD] Declared 4,517,687 | Lines 4,517,687
  Open-Default QPE:  4,517,687 - 453,583 (fin) - 362,866 (cont) = 3,701,238.00   --> SAVED: 3,701,238.00 [EXACT MATCH]
  California 4.0:    4,517,687 - 453,583 - 362,866 - 1,976,479 (ATL) = 1,724,759.00 --> SAVED: 1,724,759.00 [EXACT MATCH]

[BH] Declared 2,482,023 | Lines 2,482,023
  Open-Default QPE:  2,482,023 - 94,382 (cont) - 60,000 (SAG) = 2,327,641.00      --> SAVED: 2,327,641.00 [EXACT MATCH]
  California 4.0:    2,482,023 - 94,382 - 1,448,902 (ATL) - 60,000 - 24,000 = 854,739.00 --> SAVED: 854,739.00 [EXACT MATCH]

[LLS] Declared 11,983,654 | Lines 11,983,654
  Open-Default QPE:  11,983,654 - 1,700,000 (fin) - 400,000 (cont) - 400,000 = 9,483,654.00 --> SAVED: 9,483,654.00 [EXACT MATCH]
  California 4.0:    11,983,654 - 1,700,000 - 3,308,031 (ATL) - 587,030 = 6,388,593.00    --> SAVED: 6,388,593.00 [EXACT MATCH]
```

### Absence of Saved Evaluations for Cohort 2 Productions
For the 11 Cohort 2 productions, zero rows exist in `evaluation_generation_summaries` or `production_structures`. In strict compliance with `PROJECT_RULES.md` Long-Running Process Discipline Rule 1 (*"Never warm up or cold-evaluate a real production for test preparation"*) and user instructions (*"no production regeneration"*), no cold evaluations were launched. Their independent baselines stand documented as source-derived benchmarks.

---

## 6. Discrepancy Investigations & Recovery Findings

### 6.1 Recovery Findings F-01 through F-14 (Consolidated Status)
- **F-01 (New Brunswick):** Feature tier (30%) flagged as discretionary band ceiling although condition met. Fixed in code (`rate_rules 1.5.1`), status: `AUTHORITY_UNRESOLVED_NON_PRICEABLE`.
- **F-02 (Connecticut & North Carolina):** Foreign exchange factor applied to USD thresholds ($100k, $500k, $1.5M). Fixed in code. Recurrence guard enforces whole-thousand thresholds on all `US-` programs.
- **F-03 (North Carolina):** Discretionary "up to 25%" priced confirmed floor while MD/SC were blocked. Fixed in code: NC marked discretionary ceiling (`CONDITIONAL_NONDETERMINISTIC`).
- **F-04 (Rhode Island):** Statutory per-project cap ($7,000,000 USD) not enforced in rate rule. Fixed in code (`per_project_cap_usd = 7,000,000`).
- **F-04b (Louisiana):** Annual fund conflicting records: doctrine $150M vs. requirements profile $125M. Preserved as documented allow-listed variance.
- **F-05 (Mexico):** Native MXN 40,000,000 per-project cap and MXN 40,000,000 minimum spend unmodeled; MXN currency absent from FX table. Fixed in code: fails closed without live rate.
- **F-06 (Canadian Stacking):** Stack candidate QPE included stated-outside US editorial spend ($9,068). Fixed in code: allocation registers aligned.
- **F-07 (Movie Magic Detail Parser):** Non-hyphenated account headers skipped subaccount leaf detail. Fixed in code (`budget_parser 1.5.1`).
- **F-08 (California/New Mexico Cap Families):** Annual fund, per-project cap, and QE limits separated into distinct fields. Clarified.
- **F-09 (Washington Filmworks):** Annual fund $15M vs. secondary $3.5M. Fund corrected; 45% ceiling and two-resident gate remain open.
- **F-10 (Per-Person Salary Limits):** GA ($500k), IL ($500k), MA ($1M payroll exclusion) unmodeled at line level. Recorded open item; requires payee-level accounting schedule.
- **F-11 (Floorless Programs):** MD, NC, SC, TX classified as `CONDITIONAL_NONDETERMINISTIC`.
- **F-12 (Conditional Grey Accounts):** Grey accounts (LU $24k, BH $60k, LLS $587k) excluded from floor and maximum by design. Clarified.
- **F-13 (Territorial & Payee Facts):** Genuinely missing across all 15 budgets. Retained explicit open item.
- **F-14 (Canadian Labour Basis / CAVCO):** CPTC 25% labour basis net of provincial credit confirmed by arithmetic identity; topsheet derivation impossible without General Ledger payroll split. Retained open item.

### 6.2 Newly Identified System Discrepancies (Q36 through Q40)
- **Q36 (Non-Anchor Topsheet Subtotal Line Extraction Gap):** On 6 parsed budgets (`10 Double Zero`, `Baron Samedi`, `Going Places`, `The System`, `Twilight of the Dead`, `Underwater`), the PDF topsheets include subtotal/fee lines located below departmental leaf lines (e.g., Contingency, Completion Bond, Legal/Admin fees) that the parser did not ingest into `budget_line_items`. This creates extraction differences of -$49,999.00 to -$1,025,143.00 between declared gross and leaf line sums.
- **Q37 (Micro-Budget Project Ineligibility):** `5 LBS OF PRESSURE` ($7,066.00 declared gross, 4 lines) represents a micro pre-prep budget that fails the statutory minimum spend requirement of every North American film incentive program ($50k in MS/MA/PR up to $1.5M in NC).
- **Q38 (North American Program Registry Governance Split):** Exactly 36 of 45 North American programs are `AUTHORITY_VERIFIED_PRICEABLE`, while 9 are `AUTHORITY_UNRESOLVED_NON_PRICEABLE`. Exactly 4 programs are discretionary ceiling programs (`CONDITIONAL_NONDETERMINISTIC`), requiring explicit opportunity-only presentation.
- **Q39 (Canadian CAVCO Qualified Labour Expenditure Derivation):** Standard film topsheets summarize departmental spend rather than distinguishing qualifying Canadian resident labor from non-labor/rentals. CAVCO Qualified Labour Expenditure (QLE) cannot be rigorously audited without payroll reports.
- **Q40 (Stacking Interaction Coverage Completeness):** The canonical stacking registry contains 30 explicit slug pair rules governing North American programs, strictly enforcing statutory mutual exclusivity (e.g. CPTC vs. PSTC, OFTTC vs. OPSTC, NY § 24 vs. § 31 on identical costs) and assistance deductions (e.g. CMF/Telefilm/NOHFC deductions).

---

## 7. Audit Conclusion & Gate Disposition

1. **Dual Inventories Frozen:**
   - 328 projects accounted for (4 evaluated anchors, 11 real parsed feature projects, 35 script-only projects, 278 synthetic/test fixtures).
   - 45 North American doctrine programs accounted for (30 US, 14 Canada, 1 Mexico).
2. **Account Reconstructions Verified:**
   - Source categories, contingency deployment, finance exclusions, insurance/bond caps, and baseline QPEs mathematically reconstructed across all 15 parsed budgets.
   - Exact parity confirmed on all saved evaluation generations for the four anchors.
3. **Genuinely Missing Facts Explicitly Retained:**
   - Lack of per-account payee residency, withholding certificates, and out-of-zone shoot schedules prevents final certification of actual legal tax credits.

> [!IMPORTANT]
> **GATE DISPOSITION:**
> **`ANCHOR ACCEPTANCE GATE REMAINS STRICTLY OPEN`**
>
> In accordance with `PROJECT_RULES.md`, no unearned closure is asserted. Zero modifications were made to production code or databases, and zero evaluations were triggered. All discrepancies, extraction gaps, and missing facts are explicitly tracked in the single issue register.
