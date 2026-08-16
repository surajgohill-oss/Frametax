# Codex Priceability Blocker Reconciliation

Date: 2026-08-16

Committed universe reviewed: `6d3a44b3b040fd5a11988a31bb8178b503983b58`

Final gate: **CODEX_PRICEABILITY_BLOCKERS_RECONCILED**

## Scope and method

This is a diagnosis of the existing accepted Little Utopia (LU) and F#K Valentine's Day (FVD) universes. It does not change a rate, threshold, QPE doctrine, authority disposition, optimizer, UI, or production record.

The reconciliation used only existing CineGlobe material:

- `docs/validation/LITTLE_UTOPIA_WORLDWIDE_ACCEPTANCE.json`
- the LU `build_allocated_structures()` output at committed HEAD
- `authority_coverage_registry.py`, `production_discovery.py`, and the accepted rate registries at committed HEAD
- FVD's persisted `canonical-1.1.0` generation, scoped to its current fingerprint
- existing program-requirement metadata and persisted FVD project facts/requirements

Claude was concurrently changing production wiring in the shared worktree. None of those working-copy files was used as the classification authority. A frozen committed backend snapshot independently reproduced FVD's exact 30/80 discovery split. The later persisted wiring generations were used only as a cross-check; they agree with the frozen committed registry classification.

## Executive result

| Primary class | LU rejected structures | FVD unpriceable structures |
|---|---:|---:|
| `TRUE_AUTHORITY_GAP` | 112 | 75 |
| `DISCRETIONARY_OR_SELECTIVE` | 6 | 3 |
| `PRODUCTION_SPECIFIC_FAIL` | 9 | 1 |
| `PROJECT_FACT_NEEDED` | 0 | 0 |
| `CANONICAL_ASSUMPTION_SHOULD_SATISFY` | 0 | 0 |
| `ENGINE_OR_HANDOFF_DEFECT` | 0 | 0 |
| `PROGRAM_NON_ECONOMIC` | 0 | 0 |
| `SUPERSEDED_OR_DUPLICATE` | 2 | 1 |
| `OTHER_VERIFIED` | 0 | 0 |
| **Total non-priceable** | **129** | **80** |

Every current non-priceable structure has an explicit primary class. There is no unresolved terminal-cause trace boundary.

The local-entity assumption does not increase either current priceable count. Local-entity requirements exist as non-terminal metadata on 22 LU rejected structures and 13 FVD unpriceable structures, but every one remains blocked by a separate authority, selective, or minimum-spend cause.

## A. Little Utopia reconciliation

Accepted accounting: **177 generated = 48 priced + 129 rejected**.

### A1. True authority gaps: 112 structures

Each jurisdiction/program below creates two rejected structures: one `full_relocation` and one `component_relocation`. The exact terminal state is `UNPRICEABLE_AUTHORITY_INSUFFICIENT`; its source is the authoritative-program-rule layer because the completed canonical corpus has no defensible current deterministic rate/award basis for that runtime program.

| Jurisdiction | Program slug | Structure count |
|---|---|---:|
| AE-AD | `ae_ad_film_rebate` | 2 |
| AL | `al_cash_rebate` | 2 |
| BE | `be_tax_shelter` | 2 |
| BG | `bg_film_encouragement_act_rebate` | 2 |
| CA | `ca_federal_pstc` | 2 |
| CA-BC | `ca_bc_pstc` | 2 |
| CA-NB | `ca_nb_film_tax_credit` | 2 |
| CA-NS | `ca_ns_production_incentive_fund` | 2 |
| CA-ON | `ca_on_opstc` | 2 |
| CL | `cl_corfo_incentive` | 2 |
| CO | `co_film_in_colombia` | 2 |
| CY | `cy_film_rebate` | 2 |
| DE | `de_dfff` | 2 |
| DO | `do_film_commission_incentive` | 2 |
| EE | `ee_film_estonia_rebate` | 2 |
| ES | `es_tax_credit_foreign` | 2 |
| FI | `fi_business_finland_incentive` | 2 |
| FR | `fr_trip` | 2 |
| GB | `uk_avec` | 2 |
| HR | `hr_cash_rebate` | 2 |
| IE | `ie_section_481` | 2 |
| IS | `is_film_reimbursement_scheme` | 2 |
| IT | `it_tax_credit_foreign` | 2 |
| LT | `lt_film_centre_cash_rebate` | 2 |
| LV | `lv_national_film_centre_incentive` | 2 |
| MA | `ma_ccm_rebate` | 2 |
| ME | `me_cash_rebate` | 2 |
| NL | `nl_film_production_incentive` | 2 |
| NO | `no_film_incentive` | 2 |
| NZ | `nz_spg_international` | 2 |
| PL | `pl_pisf_cash_rebate` | 2 |
| RO | `ro_film_office_cash_rebate` | 2 |
| SA | `sa_film_commission_rebate` | 2 |
| SE | `se_production_rebate` | 2 |
| SI | `si_cash_rebate` | 2 |
| TT | `tt_production_expenditure_rebate` | 2 |
| US-AL | `us_al_film_incentive` | 2 |
| US-CA | `us_ca_film_credit` | 2 |
| US-CT | `us_ct_film_tax_credit` | 2 |
| US-GA | `us_ga_film_credit` | 2 |
| US-HI | `us_hi_film_digital_media_credit` | 2 |
| US-IL | `us_il_film_production_services_credit` | 2 |
| US-KY | `us_ky_keiia` | 2 |
| US-LA | `us_la_film_incentive` | 2 |
| US-MA | `us_ma_film_tax_credit` | 2 |
| US-MD | `us_md_film_production_activity_credit` | 2 |
| US-MN | `us_mn_film_production_credit` | 2 |
| US-MS | `us_ms_advantage_film_program` | 2 |
| US-NC | `us_nc_film_entertainment_grant` | 2 |
| US-OR | `us_or_opif` | 2 |
| US-PR | `us_pr_film_incentives_act` | 2 |
| US-RI | `us_ri_film_credit` | 2 |
| US-SC | `us_sc_film_production_credit` | 2 |
| US-TX | `us_tx_miip` | 2 |
| US-VA | `us_va_motion_picture_credit` | 2 |
| US-WA | `us_wa_motion_picture_competitiveness` | 2 |

Arithmetic: 56 program destinations x 2 structure types = **112**.

### A2. Discretionary/selective: 6 structures

| Jurisdiction/program | Structure types | Existing terminal status | Exact blocker | Origin |
|---|---|---|---|---|
| JO / `jo_rfc_rebate` | full + component | `NON_GUARANTEED_SELECTIVE` | benefit requires a selective/competitive award | selective/discretionary nature |
| JP / `jp_vipo_location_incentive` | full + component | `NON_GUARANTEED_SELECTIVE` | headline half-subsidy is not guaranteed absent selection | selective/discretionary nature |
| KR / `kr_kofic_location_incentive` | full + component | `NON_GUARANTEED_SELECTIVE` | benefit requires a selective/competitive award | selective/discretionary nature |

These six must remain outside guaranteed optimizer economics.

### A3. Production-specific minimum-spend/QPE failures: 9 structures

| Structure | Program | LU segment QPE | Accepted minimum-QPE rule | Exact result |
|---|---|---:|---:|---|
| `ALLOC-RELOC-AU` | `au_location_offset` | $4,054,196 | $10,000,000 conservative USD bound | fails |
| `ALLOC-COMPONENT-POST-AU` | `au_location_offset` | $61,568 | $10,000,000 | fails |
| `ALLOC-COMPONENT-POST-FJ` | `fj_film_rebate` | $61,568 | $110,000 | fails |
| `ALLOC-COMPONENT-POST-GR` | `gr_cash_rebate` | $61,568 | $228,104.80 | fails |
| `ALLOC-COMPONENT-POST-MT` | `mt_mfc_rebate` | $61,568 | $113,000 | fails |
| `ALLOC-COMPONENT-POST-MY` | `my_finas_rebate` | $61,568 | $1,000,000 | fails |
| `ALLOC-COMPONENT-POST-PA` | `pa_film_rebate` | $61,568 | $500,000 | fails |
| `ALLOC-COMPONENT-POST-TH` | `th_boi_incentive` | $61,568 | $1,400,000 | fails |
| `ALLOC-COMPONENT-POST-US-NY` | `us_ny_post_production_credit` | $61,568 | $1,000,000 | fails |

The existing terminal text says the statutory rate did not resolve because minimum-spend or eligibility conditions were unmet. The accepted LU artifact classifies all nine as minimum-spend/QPE gates, and each encoded QPE is below the committed minimum. Primary class: `PRODUCTION_SPECIFIC_FAIL`; origin: threshold/minimum spend.

### A4. Superseded: 2 structures

AE-DXB / `ae_dxb_dpip` produces one full and one component structure. Both carry `SUPERSEDED`: the program was replaced and must not price as current. Primary class: `SUPERSEDED_OR_DUPLICATE`; origin: superseded status.

### A5. LU accounting proof

`112 + 6 + 9 + 2 = 129` rejected. No LU row is assigned `PROJECT_FACT_NEEDED`, `CANONICAL_ASSUMPTION_SHOULD_SATISFY`, `ENGINE_OR_HANDOFF_DEFECT`, `PROGRAM_NON_ECONOMIC`, or `OTHER_VERIFIED` as its primary terminal blocker.

## B. FVD reconciliation

Current accounting: **110 generated = 30 priced + 80 unpriceable**. Every unpriceable candidate is a `full_relocation` structure.

FVD's accepted `canonical-1.1.0` persistence flattened all 80 candidate-status fields to `UNPRICEABLE_AUTHORITY_INSUFFICIENT`. The underlying committed discovery reason was not flat: it independently reproduces 75 authority gaps, 3 selective programs, 1 superseded program, and 1 statutory-condition failure.

### B1. True authority gaps: 75 structures/programs

Each explicit pair below is one full-relocation structure with committed coverage state `UNPRICEABLE_AUTHORITY_INSUFFICIENT`:

- AE-AD/`ae_ad_film_rebate`; AL/`al_cash_rebate`; AT/`at_fisa_plus`; BE/`be_tax_shelter`; BG/`bg_film_encouragement_act_rebate`.
- CA/`ca_federal_pstc`; CA-AB/`ca_ab_fttc`; CA-BC/`ca_bc_pstc`; CA-MB/`ca_mb_film_video_credit`; CA-NB/`ca_nb_film_tax_credit`; CA-NS/`ca_ns_production_incentive_fund`; CA-ON/`ca_on_opstc`; CA-SK/`ca_sk_creative_saskatchewan_grant`.
- CL/`cl_corfo_incentive`; CO/`co_film_in_colombia`; CY/`cy_film_rebate`; CZ/`cz_film_incentive`; DE/`de_dfff`; DO/`do_film_commission_incentive`; EE/`ee_film_estonia_rebate`; ES/`es_tax_credit_foreign`; FI/`fi_business_finland_incentive`; FR/`fr_trip`; GB/`uk_avec`; HR/`hr_cash_rebate`; HU/`hu_hipa_rebate`; IE/`ie_section_481`; IS/`is_film_reimbursement_scheme`; IT/`it_tax_credit_foreign`.
- KZ/`kz_investment_subsidy`; LT/`lt_film_centre_cash_rebate`; LU/`lu_filmfund_tax_shelter_rebate`; LV/`lv_national_film_centre_incentive`; MA/`ma_ccm_rebate`; ME/`me_cash_rebate`; MK/`mk_cash_rebate`; NL/`nl_film_production_incentive`; NO/`no_film_incentive`; NZ/`nz_spg_international`; PL/`pl_pisf_cash_rebate`; RO/`ro_film_office_cash_rebate`; RS/`rs_film_commission_cash_rebate`; SA/`sa_film_commission_rebate`; SE/`se_production_rebate`; SI/`si_cash_rebate`; SK/`sk_avf_production_incentive`; TT/`tt_production_expenditure_rebate`.
- US-AL/`us_al_film_incentive`; US-AZ/`us_az_motion_picture_production`; US-CA/`us_ca_film_credit`; US-CO/`us_co_film_incentive`; US-CT/`us_ct_film_tax_credit`; US-GA/`us_ga_film_credit`; US-HI/`us_hi_film_digital_media_credit`; US-IL/`us_il_film_production_services_credit`; US-KY/`us_ky_keiia`; US-LA/`us_la_film_incentive`; US-MA/`us_ma_film_tax_credit`; US-MD/`us_md_film_production_activity_credit`; US-MN/`us_mn_film_production_credit`; US-MS/`us_ms_advantage_film_program`; US-NC/`us_nc_film_entertainment_grant`; US-NM/`us_nm_film_credit`; US-NV/`us_nv_film_credit`; US-OK/`us_ok_film_enhancement_rebate`; US-OR/`us_or_opif`; US-PA/`us_pa_film_production_credit`; US-PR/`us_pr_film_incentives_act`; US-RI/`us_ri_film_credit`; US-SC/`us_sc_film_production_credit`; US-TN/`us_tn_performance_grant`; US-TX/`us_tx_miip`; US-UT/`us_ut_motion_picture_incentive`; US-VA/`us_va_motion_picture_credit`; US-WA/`us_wa_motion_picture_competitiveness`.

Primary class: `TRUE_AUTHORITY_GAP`; origin: authoritative program rule/corpus. A local company, more project facts, or a wiring change cannot defensibly produce economics while that coverage state remains.

### B2. Other five FVD blockers

| Jurisdiction/program | Existing 1.1 status | Recovered terminal cause | Primary class | Exact blocker/origin |
|---|---|---|---|---|
| JO / `jo_rfc_rebate` | flattened authority-insufficient | `NON_GUARANTEED_SELECTIVE` | `DISCRETIONARY_OR_SELECTIVE` | award/committee selection required |
| JP / `jp_vipo_location_incentive` | flattened authority-insufficient | `NON_GUARANTEED_SELECTIVE` | `DISCRETIONARY_OR_SELECTIVE` | competitive subsidy, not guaranteed |
| KR / `kr_kofic_location_incentive` | flattened authority-insufficient | `NON_GUARANTEED_SELECTIVE` | `DISCRETIONARY_OR_SELECTIVE` | award/committee selection required |
| AE-DXB / `ae_dxb_dpip` | flattened authority-insufficient | `SUPERSEDED` | `SUPERSEDED_OR_DUPLICATE` | replaced by a current program |
| AU / `au_location_offset` | flattened authority-insufficient | statutory conditions unmet | `PRODUCTION_SPECIFIC_FAIL` | $4,517,687 discovery input and $4,154,821 modeled QPE are both below the accepted $10,000,000 minimum-QPE bound |

### B3. FVD accounting proof

`75 + 3 + 1 + 1 = 80` unpriceable. No FVD row is assigned `PROJECT_FACT_NEEDED`, `CANONICAL_ASSUMPTION_SHOULD_SATISFY`, `ENGINE_OR_HANDOFF_DEFECT`, `PROGRAM_NON_ECONOMIC`, or `OTHER_VERIFIED` as its primary terminal blocker.

## C. Local production entity assumption test

### Terminal finding

**Current blockers caused solely by a local entity/SPV/producer/service-company/registration requirement: 0 LU, 0 FVD.**

No terminal blocker text in either universe cites an absent local entity. The committed discovery gate stops these rows earlier for authority, selectivity, supersession, or QPE threshold.

### Non-terminal local-entity metadata

The following rejected rows do carry a local-entity or local-co-producer requirement in existing metadata:

| Universe | Rows | Programs | Current terminal cause | Should canonical assumption clear the entity mechanic? | Priceability consequence now |
|---|---:|---|---|---|---|
| LU | 18 | AE-AD, BE, EE, FI, IT, LT, NL, SA, US-KY; each full + component | authority gap | YES | remains blocked by authority; gain 0 |
| LU | 2 | JP; full + component | selective | YES | remains selective; gain 0 |
| LU | 2 | FJ component, MT component | minimum QPE | YES | remains below minimum; gain 0 |
| FVD | 12 | AE-AD, BE, CA-AB, EE, FI, IT, LT, LU, NL, RS, SA, US-KY | authority gap | YES | remains blocked by authority; gain 0 |
| FVD | 1 | JP | selective | YES | remains selective; gain 0 |

`LT` is recorded as requiring a local co-producer; the other listed rows use local-entity/company requirements. Under the stated product assumption, those ordinary engagement/incorporation mechanics should be treated as satisfiable. That assumption must not erase their independent substantive blockers.

## D. Engine/handoff test

### Little Utopia

No terminal handoff defect was found among the 129 rejected structures. LU's budget geography, offshore payroll, production requirements, and structure allocation facts are present in the accepted runtime path.

### FVD: known but not handed off

FVD already stores:

- 20 script-derived `ProjectFact` rows;
- 127 `ProductionRequirement` rows: 38 characters, 8 explicit animals, 10 minors, 11 vehicles, 4 weapons, 2 period references, and 54 scripted locations.

The accepted `canonical-1.1.0` evaluator instead calls `derive_production_requirements({})`. This is a verified **known-but-not-handed-off** boundary. It affects capability matching and the quality of production comparisons, but it is not the terminal cause of any of the 80 unpriceable program rows. Correcting it has an expected current priceable-count gain of **0**; it may properly remove physically unsuitable candidates rather than add them.

### FVD: genuinely unknown

- zero `ProductionAssumption` rows;
- all 54 scripted-location rows lack a confirmed production location;
- all 54 lack a confirmed stage/practical production approach;
- no `budget_accounts_outside_base_jurisdiction` fact;
- no `budget_offshore_payroll_accounts` fact.

These are genuine project/producer decisions or territorial facts and must remain unknown until supported. They explain comparison/provisional limitations, not the 80 terminal authority/selectivity/threshold blocks.

### Out-of-universe canonical identity defects

The existing global application artifact identifies three `CANONICAL_DATA_HANDOFF_DEFECT` records: BC FIBC, German GMPF, and India NFDC. They are not program identities in the current LU 177 or FVD 110 generated sets; the generated CA-BC and DE rows represent different programs, and no IN row is generated. They therefore contribute **0** to the requested 129/80 classifications and **0 proven current-universe gain**. Adding their distinct identities is safe without new authority research, but claiming an additional priceable project structure would still require generation plus project-specific qualification.

## E. Maximum defensible priceability

| Universe | Generated | Current priceable | `CANONICAL_ASSUMPTION_SHOULD_SATISFY` blockers | `ENGINE_OR_HANDOFF_DEFECT` blockers | Maximum defensibly priceable within current generated universe |
|---|---:|---:|---:|---:|---:|
| Little Utopia | 177 | 48 | 0 | 0 | **48** |
| FVD | 110 | 30 | 0 | 0 | **30** |

The maximum does not rise merely because entity mechanics are assumed. Every entity-flagged rejected row has another independent primary blocker. Authority gaps, selective awards, actual threshold failures, and superseded programs are deliberately excluded from the maximum.

## F. Priority repair list

| Priority | Blocker class | Affected current blocker count | Expected current priceable gain | Likely module/layer | Safe without new research? |
|---:|---|---:|---:|---|---|
| 1 | `CANONICAL_ASSUMPTION_SHOULD_SATISFY` | 0 terminal; 35 metadata-only rows | 0 | eligibility/project-assumption fact resolution | YES, as an explicit non-terminal assumption only |
| 2 | `ENGINE_OR_HANDOFF_DEFECT` | 0 terminal; FVD has 127 requirements not handed off | 0 | canonical project economics -> discovery handoff | YES; preserve UNKNOWN and do not invent facts |
| 2a | out-of-universe program identity handoff | 3 canonical records, 0 current rows | 0 proven current-universe gain | runtime program identity/profile binding | YES for distinct identity only; qualification still required |
| 3 | project facts derivable from uploaded material | 0 terminal; 20 facts and 127 requirements already derived | 0 | script/budget canonical state | YES for deterministic extraction; producer decisions stay unknown |
| 4 | `TRUE_AUTHORITY_GAP` | LU 112 rows / 56 programs; FVD 75 rows / 75 programs | indeterminate | authority corpus, then rule encoding | **NO** under this task; requires authority completion |

No code repair within the allowed no-research scope can legitimately increase the current 48/30 counts. The highest-volume remaining opportunity is authority completion, but pricing any of it without that work would violate the accepted safety rule.

Selective programs should remain conditional opportunities; minimum-spend failures should remain project-specific failures; superseded programs should remain excluded.

## G. Product status language

| Internal class | Recommended producer-facing label |
|---|---|
| `TRUE_AUTHORITY_GAP` | Program details need authoritative verification before savings can be calculated |
| `DISCRETIONARY_OR_SELECTIVE` | Selective opportunity - not included in guaranteed savings |
| `PRODUCTION_SPECIFIC_FAIL` | This production does not meet the program's spend or eligibility threshold |
| `PROJECT_FACT_NEEDED` | Project information needed to test eligibility |
| `CANONICAL_ASSUMPTION_SHOULD_SATISFY` | Standard local production setup assumed |
| `ENGINE_OR_HANDOFF_DEFECT` | Existing project data needs calculation refresh |
| `PROGRAM_NON_ECONOMIC` | No calculable production incentive |
| `SUPERSEDED_OR_DUPLICATE` | Replaced or duplicate program - not modeled separately |
| `OTHER_VERIFIED` | Use the exact verified reason; do not collapse it into a generic label |

Avoid presenting all unavailable rows as “Authority insufficient.” FVD's old persistence label obscured selective awards, a superseded program, and an actual Australian threshold failure.

## Final gate

**CODEX_PRICEABILITY_BLOCKERS_RECONCILED**

All 129 LU rejected structures and all 80 FVD unpriceable structures have an explicit primary classification and exact existing reason. Local-entity mechanics and handoff limitations were tested separately and do not create a defensible priceable-count increase in either current generated universe.
