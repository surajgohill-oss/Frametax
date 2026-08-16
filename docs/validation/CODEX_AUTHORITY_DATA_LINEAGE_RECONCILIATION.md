# Codex Authority Data Lineage / Runtime Source Reconciliation

Date: 2026-08-16

Final gate: **CODEX_AUTHORITY_LINEAGE_RECONCILED**

## Executive finding

All 74 `CORE_PROGRAM_INCOMPLETE` programs were traced. Every program has a current runtime profile and at least one rate rule, but no program has a complete accepted internal rule set across rate, QPE, territoriality, qualification, caps, monetization and timing. The common primary root cause is therefore **`PARTIAL_DATA_ONLY`**, not a wiring-only recovery.

The important distinction is:

- the current engine contains old/PARSED fragments for all 74;
- accepted validation artifacts contain some corrected summaries and source links;
- `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` deliberately replaced indispensable economics with `DISABLED_UNPRICEABLE` placeholders because the accepted corpus did not contain complete literal rules;
- `authority_coverage_registry.py` is the served veto, so those old fragments cannot price;
- no complete 74-program payload was found in tracked Git history, the tracked artifacts, migration/seed files, or the local database asset.

Primary root-cause accounting:

| Root class | Programs |
|---|---:|
| `DATA_EXISTS_AND_NOT_WIRED` | 0 |
| `DATA_EXISTS_BUT_WRONG_VERSION_SELECTED` | 0 |
| `DUPLICATE_RECORD_SPLIT` | 0 |
| `SLUG_OR_IDENTITY_BINDING_DEFECT` | 0 |
| `SERIALIZATION_OR_MIGRATION_LOSS` | 0 |
| `PARTIAL_DATA_ONLY` | **74** |
| `GENUINELY_MISSING_AUTHORITY` | 0 |
| `OTHER_VERIFIED` | 0 |

This one-primary-class accounting does not deny secondary lineage defects. Literal rate/cap summaries were flattened into generic disabled payloads for several programs, and canonical/runtime IDs are split for many records. Those are secondary symptoms. They are not the primary cause because the missing essential dimensions were never captured completely in any accepted internal asset; repairing the flattening or binding alone would still not make a program priceable.

## Scope and evidence boundary

No web research, source addition, program-data mutation, runtime change, test run, UI inspection, or optimizer work was performed. The program universe is exactly the 74 P0 records in `CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json`.

Internal assets checked include the global Codex validation, global canonical disposition, remediation input/backlog/completion/executable payloads, distributed/P0-P1 closeouts, the authority registry, slug aliases, jurisdiction profiles, doctrine/rate/QPE/requirements registries, evaluator/discovery/pricing call paths, Git history, model/migration definitions, and the local DB asset. The local `backend/frametax.db` is zero bytes and local PostgreSQL is not running; therefore no recovery credit is assigned to an uninspected external/live database. Accepted FVD artifacts establish that historical calculation generations exist, but calculation-result rows are outputs, not authoritative rule records.

The code references `docs/validation/CODEX_FINAL_RULE_RESOLUTION.md`, but `git log --all` shows that path was never tracked on the available refs. Its alleged contents cannot be treated as recoverable project data.

## A. Current source-of-truth path

For every one of the 74 programs, the currently served decision path is:

`jurisdiction_comparison.ALL_PROFILES` → runtime slug → `program_slug_aliases.canonical_slug()` → `authority_coverage_registry` → **block** (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`).

Only if that gate does not block does the engine continue to `program_spend_rules.resolve_program_doctrine()`, `program_rate_rules.resolve_program_rate()`, QPE-cap handling, and segment pricing. `canonical_executable_registry.py` is reporting/gap analysis only and is not imported by optimizer paths. `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` is not dynamically loaded by the evaluator; its dispositions were hand-transcribed into `authority_coverage_registry.py`.

Common per-program record locations:

- accepted validation: `CODEX_GLOBAL_INCENTIVE_VALIDATION.json` and `GLOBAL_CANONICAL_PROGRAM_DISPOSITION.json`;
- remediation: `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` (`DISABLED_UNPRICEABLE` for all 74);
- served veto: `backend/app/data/authority_coverage_registry.py`;
- runtime identity/profile: `backend/app/calculators/jurisdiction_comparison.py`;
- runtime rate/doctrine: `backend/app/data/program_rate_rules.py`, `program_rate_rules_worldwide.py`, and `executable_jurisdiction_registry.py`;
- QPE/qualification fragments: `program_spend_rules.py` and `program_requirements.py`;
- evaluator lookup: `production_discovery.py` / `allocation_pricing.py`, then `canonical_evaluation.py` for canonical persistence/serving;
- DB rule row: none demonstrated in the available local DB.

### Per-program lineage and primary root

| Jurisdiction | Canonical ID | Runtime slug | Accepted record | Runtime fragments | Root |
|---|---|---|---|---|---|
| AE-AD | `proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate` | `ae_ad_film_rebate` | MISSING; ADD | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| AL | `al_film_incentive` | `al_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| AT | `at_fisa_plus` | `at_fisa_plus` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| BE | `be_tax_shelter` | `be_tax_shelter` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| BG | `bg_film_incentive` | `bg_film_encouragement_act_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CA-AB | `ca_ab_fttc` | `ca_ab_fttc` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| CA-BC | `bc_pstc` | `ca_bc_pstc` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| CA | `proposed_canada_film_or_video_production_services_tax_credit_pstc` | `ca_federal_pstc` | MISSING; ADD | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| CA-MB | `ca_mb_fvptc` | `ca_mb_film_video_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CA-NB | `ca_nb_film_credit` | `ca_nb_film_tax_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CA-NS | `ca_ns_pif` | `ca_ns_production_incentive_fund` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CA-ON | `on_opstc` | `ca_on_opstc` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| CA-SK | `ca_sk_production_grant` | `ca_sk_creative_saskatchewan_grant` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CL | `cl_corfo_incentive` | `cl_corfo_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| CO | `co_film_colombia` | `co_film_in_colombia` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| CY | `cy_film_rebate` | `cy_film_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| CZ | `cz_film_incentive` | `cz_film_incentive` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| DE | `de_dfff` | `de_dfff` | STALE; CORRECT | profile, rate, doctrine-record, QPE-doctrine, QPE-rules:1, requirements | `PARTIAL_DATA_ONLY` |
| DO | `do_film_incentive` | `do_film_commission_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine | `PARTIAL_DATA_ONLY` |
| EE | `ee_film_incentive` | `ee_film_estonia_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| ES | `es_tax_credit_foreign` | `es_tax_credit_foreign` | INCORRECT; CORRECT | profile, rate, QPE-doctrine, QPE-rules:27, requirements | `PARTIAL_DATA_ONLY` |
| FI | `fi_film_incentive` | `fi_business_finland_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| FR | `fr_trip` | `fr_trip` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, requirements | `PARTIAL_DATA_ONLY` |
| HR | `hr_cash_rebate` | `hr_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| HU | `hu_hipa_rebate` | `hu_hipa_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| IE | `ie_section_481` | `ie_section_481` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| IS | `is_film_reimbursement` | `is_film_reimbursement_scheme` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| IT | `it_tax_credit_foreign` | `it_tax_credit_foreign` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| LT | `lt_film_incentive` | `lt_film_centre_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| LU | `lu_film_incentive` | `lu_filmfund_tax_shelter_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| LV | `lv_film_incentive` | `lv_national_film_centre_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| MA | `ma_ccm_rebate` | `ma_ccm_rebate` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| ME | `me_film_incentive` | `me_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| MK | `mk_film_incentive` | `mk_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| NL | `nl_nfpi` | `nl_film_production_incentive` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| NO | `no_film_incentive` | `no_film_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| NZ | `nz_spg_international` | `nz_spg_international` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| PL | `pl_film_incentive` | `pl_pisf_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| RO | `ro_cnc_rebate` | `ro_film_office_cash_rebate` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| RS | `rs_film_rebate` | `rs_film_commission_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| SA | `sa_sfc_rebate` | `sa_film_commission_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| SE | `se_film_incentive` | `se_production_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| SI | `si_film_incentive` | `si_cash_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| SK | `sk_film_incentive` | `sk_avf_production_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, QPE-doctrine | `PARTIAL_DATA_ONLY` |
| TT | `tt_film_incentive` | `tt_production_expenditure_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| GB | `uk_avec` | `uk_avec` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-AL | `us_al_film_incentive` | `us_al_film_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-AZ | `us_az_film_credit` | `us_az_motion_picture_production` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-CA | `ca_film_30` | `us_ca_film_credit` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-CO | `us_co_film_incentive` | `us_co_film_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-CT | `us_ct_film_credit` | `us_ct_film_tax_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-GA | `georgia_eiia` | `us_ga_film_credit` | INCORRECT; CORRECT | profile, rate, doctrine-record, QPE-doctrine, QPE-rules:1, requirements | `PARTIAL_DATA_ONLY` |
| US-HI | `us_hi_film_tax_credit` | `us_hi_film_digital_media_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-IL | `us_il_film_credit` | `us_il_film_production_services_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-KY | `us_ky_keiia` | `us_ky_keiia` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-LA | `la_film_production` | `us_la_film_incentive` | VERIFIED; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-MA | `us_ma_film_credit` | `us_ma_film_tax_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-MD | `us_md_film_credit` | `us_md_film_production_activity_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-MN | `us_mn_film_credit` | `us_mn_film_production_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-MS | `us_ms_film_credit` | `us_ms_advantage_film_program` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-NC | `us_nc_film_grant` | `us_nc_film_entertainment_grant` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-NM | `nm_film_production` | `us_nm_film_credit` | INCORRECT; CORRECT | profile, rate, doctrine-record, QPE-doctrine, requirements | `PARTIAL_DATA_ONLY` |
| US-NV | `us_nv_film_incentive` | `us_nv_film_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-OK | `us_ok_ofer` | `us_ok_film_enhancement_rebate` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-OR | `or_opif` | `us_or_opif` | VERIFIED; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-PA | `us_pa_film_credit` | `us_pa_film_production_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-PR | `us_pr_film_incentive` | `us_pr_film_incentives_act` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-RI | `us_ri_film_credit` | `us_ri_film_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-SC | `us_sc_film_credit` | `us_sc_film_production_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-TN | `us_tn_film_incentive` | `us_tn_performance_grant` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-TX | `us_tx_miip` | `us_tx_miip` | STALE; CORRECT | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |
| US-UT | `us_ut_film_incentive` | `us_ut_motion_picture_incentive` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-VA | `us_va_film_credit` | `us_va_motion_picture_credit` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record | `PARTIAL_DATA_ONLY` |
| US-WA | `us_wa_mpcp` | `us_wa_motion_picture_competitiveness` | INCOMPLETE; AUTHORITY_CLOSED | profile, rate, doctrine-record, requirements | `PARTIAL_DATA_ONLY` |

## B. Field-by-field lineage

Codes:

- `A` — `PRESENT_IN_ACCEPTED_INTERNAL_DATA` and consumed by the served economic path;
- `S` — `PRESENT_ONLY_IN_OLD_OR_STALE_DATA` (includes PARSED/runtime fragments rejected or superseded by the later authority closeout);
- `W` — `PRESENT_BUT_NOT_WIRED` (an accepted literal/narrative exists, but the served authority gate does not consume it);
- `X` — `ABSENT_EVERYWHERE` as an explicit implementable predicate in tracked internal assets;
- `N` — `NOT_APPLICABLE` established by authority.

No `A` appears because all 74 terminate at the authority gate. No `N` is asserted: authority silence or an empty list is not proof that a dimension is legally inapplicable. `S` means a fragment exists, not that the field is complete enough to execute.

Columns: `R` rate/award basis; `Q` QPE definition; `T` territoriality; `Min` minimum spend; `Cap` cap; `Type` eligible production type; `Cult` cultural/content test; `Up` uplift rules; `Res` resident/nonresident treatment; `Pay` payroll treatment; `Mon` monetization form; `Ref` refundability; `Xfer` transferability; `Time` application timing.

| Program | R | Q | T | Min | Cap | Type | Cult | Up | Res | Pay | Mon | Ref | Xfer | Time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ae_ad_film_rebate` | W | X | X | X | X | S | S | W | X | X | W | S | S | S |
| `al_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `at_fisa_plus` | S | X | X | X | X | S | S | S | X | X | S | S | S | S |
| `be_tax_shelter` | S | S | X | X | X | S | S | S | X | X | S | X | X | S |
| `bg_film_encouragement_act_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `ca_ab_fttc` | S | X | X | X | X | S | S | S | X | X | S | S | S | S |
| `ca_bc_pstc` | W | X | X | X | X | S | S | W | X | X | S | S | S | S |
| `ca_federal_pstc` | W | X | X | X | W | S | S | X | X | X | W | W | X | S |
| `ca_mb_film_video_credit` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `ca_nb_film_tax_credit` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `ca_ns_production_incentive_fund` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `ca_on_opstc` | S | X | X | S | X | S | S | X | X | X | S | S | S | X |
| `ca_sk_creative_saskatchewan_grant` | S | X | X | X | S | S | S | S | X | X | S | X | S | X |
| `cl_corfo_incentive` | S | X | X | S | X | S | S | X | X | X | S | S | S | S |
| `co_film_in_colombia` | S | X | X | X | S | S | S | S | X | X | S | S | S | X |
| `cy_film_rebate` | S | S | X | S | S | S | S | S | X | X | S | S | X | S |
| `cz_film_incentive` | W | X | X | X | W | S | S | W | X | X | S | S | S | S |
| `de_dfff` | W | S | S | X | W | S | S | X | X | X | S | S | X | S |
| `do_film_commission_incentive` | S | S | X | S | X | S | S | X | X | X | S | S | S | X |
| `ee_film_estonia_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | S |
| `es_tax_credit_foreign` | W | S | S | S | S | S | S | X | S | S | S | S | X | S |
| `fi_business_finland_incentive` | S | X | X | S | X | S | S | X | X | X | S | S | S | S |
| `fr_trip` | W | X | X | W | S | S | S | W | X | X | S | S | X | S |
| `hr_cash_rebate` | S | S | X | S | X | S | S | S | X | X | S | S | X | S |
| `hu_hipa_rebate` | S | S | X | X | X | S | S | S | X | X | S | S | X | S |
| `ie_section_481` | S | S | X | S | S | S | S | X | X | X | S | S | S | S |
| `is_film_reimbursement_scheme` | W | X | X | X | X | S | S | W | X | X | S | S | S | S |
| `it_tax_credit_foreign` | S | S | X | X | S | S | S | X | X | X | S | S | S | S |
| `lt_film_centre_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | X | X | S |
| `lu_filmfund_tax_shelter_rebate` | S | X | X | X | X | S | S | S | X | X | S | S | S | S |
| `lv_national_film_centre_incentive` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `ma_ccm_rebate` | W | X | X | W | X | S | S | X | X | X | S | S | S | S |
| `me_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `mk_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `nl_film_production_incentive` | W | X | X | W | W | S | S | W | X | X | S | S | S | S |
| `no_film_incentive` | S | X | X | X | X | S | S | X | X | X | S | S | S | S |
| `nz_spg_international` | S | X | X | X | X | S | S | S | X | X | S | S | X | S |
| `pl_pisf_cash_rebate` | S | X | X | X | X | S | S | S | X | X | S | S | S | S |
| `ro_film_office_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | S |
| `rs_film_commission_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | S |
| `sa_film_commission_rebate` | W | W | W | W | W | W | W | X | W | X | W | S | S | W |
| `se_production_rebate` | S | X | X | S | X | S | S | X | X | X | S | S | S | S |
| `si_cash_rebate` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `sk_avf_production_incentive` | S | S | X | X | X | S | S | X | X | X | S | S | S | X |
| `tt_production_expenditure_rebate` | S | X | X | S | S | S | S | S | X | X | S | X | X | X |
| `uk_avec` | S | X | X | X | W | S | W | S | X | X | S | S | S | W |
| `us_al_film_incentive` | S | X | X | X | X | S | S | S | X | X | S | X | X | X |
| `us_az_motion_picture_production` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `us_ca_film_credit` | W | X | X | X | S | S | S | W | X | X | S | S | S | S |
| `us_co_film_incentive` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `us_ct_film_tax_credit` | S | X | X | X | X | S | S | X | X | X | S | X | S | X |
| `us_ga_film_credit` | S | S | S | S | S | S | S | S | X | X | S | S | S | X |
| `us_hi_film_digital_media_credit` | S | X | X | X | X | S | S | S | X | X | S | X | X | X |
| `us_il_film_production_services_credit` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |
| `us_ky_keiia` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |
| `us_la_film_incentive` | W | X | X | S | S | S | S | S | X | X | W | W | W | S |
| `us_ma_film_tax_credit` | S | X | X | S | S | S | S | X | X | X | S | S | S | S |
| `us_md_film_production_activity_credit` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |
| `us_mn_film_production_credit` | S | X | X | S | S | S | S | X | X | X | S | X | S | S |
| `us_ms_advantage_film_program` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |
| `us_nc_film_entertainment_grant` | S | X | X | S | S | S | S | X | X | X | S | S | S | S |
| `us_nm_film_credit` | S | S | X | X | S | S | S | S | X | X | S | S | X | X |
| `us_nv_film_credit` | S | X | X | S | S | S | S | S | X | X | S | S | S | X |
| `us_ok_film_enhancement_rebate` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `us_or_opif` | W | X | X | S | S | S | S | X | X | X | W | W | S | S |
| `us_pa_film_production_credit` | S | X | X | X | S | S | S | S | X | X | S | S | S | S |
| `us_pr_film_incentives_act` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |
| `us_ri_film_credit` | S | X | X | S | S | S | S | X | X | X | S | X | X | X |
| `us_sc_film_production_credit` | S | X | X | S | S | S | S | S | X | X | S | X | X | X |
| `us_tn_performance_grant` | S | X | X | X | X | S | S | X | X | X | S | S | S | X |
| `us_tx_miip` | W | X | X | W | S | S | S | W | X | X | S | S | S | S |
| `us_ut_motion_picture_incentive` | S | X | X | X | X | S | S | S | X | X | S | S | S | X |
| `us_va_motion_picture_credit` | S | X | X | X | X | S | S | X | X | X | S | X | X | X |
| `us_wa_motion_picture_competitiveness` | S | X | X | S | S | S | S | S | X | X | S | S | S | S |

The matrix explains the uniform primary class: rate/profile fragments are widespread, but complete territoriality, resident/nonresident treatment, payroll treatment and authoritative QPE predicates are not. Even the richest records retain material gaps.

## C. What `AUTHORITY_CLOSED` actually meant

There are 58 P0 programs with that disposition. None is fully captured.

- 57 are `SOURCE_IDENTIFIED_ONLY`: their canonical closeout contains only an authority URL plus “Standard rules confirmed” (33) or “Standard European rules confirmed via primary authority” (24), without literal implementable rules.
- Saudi Arabia is `RESEARCH_ATTEMPTED_BUT_INCOMPLETE`: a substantive narrative was preserved, but it still does not close the full rate-selection, QPE, payroll, cap and monetization model.
- `RESEARCH_COMPLETE_AND_RULES_CAPTURED`: **0**.

| Program | Actual meaning | Evidence |
|---|---|---|
| `al_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `at_fisa_plus` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `be_tax_shelter` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `bg_film_encouragement_act_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `ca_ab_fttc` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ca_mb_film_video_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ca_nb_film_tax_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ca_ns_production_incentive_fund` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ca_on_opstc` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ca_sk_creative_saskatchewan_grant` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `cl_corfo_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `co_film_in_colombia` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `cy_film_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `do_film_commission_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `ee_film_estonia_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `fi_business_finland_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `fr_trip` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `hr_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `hu_hipa_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `ie_section_481` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `it_tax_credit_foreign` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `lt_film_centre_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `lu_filmfund_tax_shelter_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `lv_national_film_centre_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `me_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `mk_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `no_film_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `nz_spg_international` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `pl_pisf_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `rs_film_commission_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `sa_film_commission_rebate` | RESEARCH_ATTEMPTED_BUT_INCOMPLETE | Substantive narrative exists, but rate-selection, full QPE, payroll, cap and monetization fields are not complete. |
| `se_production_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `si_cash_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `sk_avf_production_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `tt_production_expenditure_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `uk_avec` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard European rules confirmed via primary authority. |
| `us_al_film_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_az_motion_picture_production` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_co_film_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ct_film_tax_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_hi_film_digital_media_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_il_film_production_services_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ky_keiia` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ma_film_tax_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_md_film_production_activity_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_mn_film_production_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ms_advantage_film_program` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_nc_film_entertainment_grant` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_nv_film_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ok_film_enhancement_rebate` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_pa_film_production_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_pr_film_incentives_act` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ri_film_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_sc_film_production_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_tn_performance_grant` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_ut_motion_picture_incentive` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_va_motion_picture_credit` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |
| `us_wa_motion_picture_competitiveness` | SOURCE_IDENTIFIED_ONLY | Generic closeout text only: Standard rules confirmed. |

Conclusion: **`AUTHORITY_CLOSED` was used too broadly.** It often meant “a source was identified and a generic jurisdictional close sentence was added,” not “all executable rule fields were captured.”

## D. Split stores and engine paths

| Store/path | Purpose | Served | Authoritative for | Overlap / divergence risk |
|---|---|---:|---|---|
| Global validation/disposition artifacts | Research findings and adjudication | NO | Audit provenance and accepted findings | Richer summaries than remediation payload; not loaded at runtime |
| `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` | Intended executable handoff | NO | Canonical remediation disposition | Literal fields are mostly disabled placeholders; diverges from hard-coded rules |
| `authority_coverage_registry.py` | Deterministic priceability veto | YES | Whether a program may enter economics | Overrides rate/QPE fragments; hand-maintained from artifact |
| `jurisdiction_comparison.ALL_PROFILES` | Runtime program identity and production capability | YES | Discovery identity/capability | Duplicates doctrine fields and can retain stale values |
| `executable_jurisdiction_registry.py` | Doctrine/rate source for newer programs | YES, after gate | Rate tiers, thresholds, citations | Six legacy programs remain outside this registry by design |
| `program_rate_rules.py` + worldwide module | Rate resolution and QPE caps | YES, after gate | Executable rates/caps | Contains richer/PARSED data that blocked programs never reach |
| `program_spend_rules.py` | QPE doctrine and category treatment | YES, after gate | QPE inclusion/exclusion | Sparse: only 12/74 have doctrine and only 3/74 have explicit category rows |
| `program_requirements.py` | Qualification, timing and monetization facts | YES, after gate | Structured requirements | 48/74 profiles; fields frequently unknown or estimate-only |
| Little Utopia special runtime | LU state/build/allocation path | YES for LU | LU project inputs and allocation | Separate project-specific construction from persisted generic path |
| Canonical evaluator + calculation persistence | Generic/FVD evaluation and serving | YES for FVD | Calculated results, not rule authority | Results can outlive rule versions; historical generations are outputs |
| DB program/rule models and migrations | Intended persistent data model | Not demonstrated locally | Schema only in this workspace | Local SQLite is empty; PostgreSQL unavailable; no recovery claim |
| `canonical_executable_registry.py` | Cross-registry reporting | NO optimizer use | Accounting only | Its “canonical” label can be mistaken for a served source |

**More than one effective rule source of truth: YES.** The exact overlapping effective sources are the authority veto, profile/doctrine/rate/QPE/requirements registries, and the separate LU versus canonical/persisted project paths. The validation/remediation artifacts add a second governance truth but are not runtime-loaded. There is no single record from which identity, validation status, rate, QPE, territoriality and qualification are all served.

## E. Five priceable controls

These are controls for the successful *current wiring path*, not a claim that every control has equal authority maturity. Only Mauritius is fully VERIFIED across its rate and detailed QPE rows; the other four expose the current default-priceable behavior (absence from the authority veto plus a PARSED rate/profile).

| Control | Authority/data → runtime path | Accepted priced result |
|---|---|---:|
| `mu_edb_incentive` | VERIFIED EDB evidence → 2 rate tiers + hybrid doctrine + 27 QPE rows + requirements → profile → no authority veto → `price_segment` | $1,306,598.10 floor on $4,355,327 QPE |
| `ca_nl_all_spend_credit` | accepted PARSED doctrine/profile → 2 rate tiers → profile → no authority veto → `price_segment` | $24,627.20 floor on $61,568 QPE |
| `sg_made_with_singapore_rebate` | accepted PARSED doctrine/profile + requirements → 2 rate tiers → no authority veto → `price_segment` | $18,470.40 floor on $61,568 QPE |
| `qa_screen_production_incentive` | accepted PARSED doctrine/profile + requirements → 2 rate tiers → no authority veto → `price_segment` | $24,627.20 floor on $61,568 QPE |
| `eg_empc_cashback` | accepted PARSED doctrine/profile → flat rate tier → no authority veto → `price_segment` | $18,470.40 on $61,568 QPE |

Five representative P0 divergences:

| P0 program | Same path through | Divergence point |
|---|---|---|
| `uk_avec` | profile + rate tiers + requirements + QPE cap | authority veto fires first; QPE categories, UK-use territoriality and monetization remain incomplete |
| `ca_federal_pstc` | profile + 16% rate + requirements | authority veto fires; accepted ADD summary was not converted into complete QPE/territorial predicates |
| `es_tax_credit_foreign` | profile + bracketed rate + 27 QPE rows + requirements | authority veto fires; accepted validation says the old record is INCORRECT and key territorial/monetization fields remain unresolved |
| `us_ga_film_credit` | VERIFIED rate/doctrine + one exclusion row + requirements | authority veto fires; complete category, payroll, resident/nonresident and timing rules are absent |
| `us_la_film_incentive` | VERIFIED validation summary + profile/rates/requirements | authority veto fires; authoritative QPE and territoriality are still absent |

## F. Recovery potential

| Recovery bucket | Programs | Interpretation |
|---|---:|---|
| Recoverable by wiring/migration only | **0** | No complete accepted rule set exists to wire |
| Recoverable by version/identity fix only | **0** | Runtime identity resolves for all 74; richer versions remain incomplete/stale |
| Partially recoverable from existing data | **74** | Existing rate/profile/requirements fragments should be consolidated before research |
| Requiring genuinely new authority research to become complete | **74** | Each has at least one essential rule dimension absent or only stale |

`GENUINELY_MISSING_AUTHORITY = 0` is not inconsistent with “74 require research.” The root class is reserved for programs with no usable internal authority data at all. Here every program has fragments, but fragments are insufficient for complete execution.

Potential unlock without new research, without overstating priceability:

- LU programs: **0**; therefore LU structures unlocked: **0**.
- FVD programs: **0**; therefore FVD structures unlocked: **0**.

Consolidation can reduce the future research workload, but it cannot defensibly remove any current authority veto by itself.

## G. Mainstream-program check

| Program | Accepted internal rule data | Runtime uses richest record? | Root | New research required |
|---|---|---|---|---|
| GB AVEC | PARTIAL | NO — veto supersedes richer rate/cap fragments | `PARTIAL_DATA_ONLY` | PARTIAL |
| Canada federal PSTC | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| Spain foreign-production incentive | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| France TRIP | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| Ireland Section 481 | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| Italy foreign-production credit | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| New Zealand SPG | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| US California | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| US Georgia | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| US Louisiana | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |
| US New Mexico | PARTIAL | NO | `PARTIAL_DATA_ONLY` | PARTIAL |

Summary: **11/11 have partial internal data; 0/11 are complete; 0/11 are using a complete richest accepted record; all 11 need targeted, not from-scratch, authority completion.**

## H. Smallest repair plan (not implemented)

### A. No-research recovery first

1. **Freeze a single canonical program identity map (74 programs).** Reconcile canonical ID, runtime slug and jurisdiction code in one generated manifest; preserve aliases only when statutory identity is proven. Affects 74; likely stores: disposition/remediation artifacts, slug aliases, authority registry. No external research.
2. **Build a field-level consolidation ledger.** Import literal accepted findings and separately label old/PARSED runtime facts; never promote stale data. Affects 74; likely stores: global validation, doctrine/rate/QPE/requirements registries. No external research.
3. **Generate exact residual authority questions.** For each `X` and unresolved `S`, identify the missing official rule and effective-version requirement. Affects 74. No external research.
4. **Define one atomic publication contract.** A program cannot leave the authority veto until identity, effective date, rate, QPE, territoriality, caps/gates and monetization are published together with field-level provenance. Affects the canonical data/application layer. No external research.
5. **Do not remove any current veto yet.** The current no-research priceability gain is zero.

### B. True research backlog

6. **Run targeted authority completion against the residual ledger, mainstream programs first.** This is not a re-audit: research only the missing/old fields, current version and conflicts surfaced by steps 1–3. Affects 74, with the 11 mainstream programs first. External research required.
7. **Publish, then wire, one complete versioned record per program.** Only after authority completion should the coverage state change and program-specific acceptance checks run. External research required for the rule content; implementation is a later task.

## I. Closeout assessment

1. **Was prior global authority validation truly complete? NO.** It was a useful partial inventory and source-identification effort, but not an executable program-rule closeout.
2. **Was `AUTHORITY_CLOSED` used too broadly? YES.** Fully captured: 0/58; overstated/incomplete: 58/58.
3. **Cause of current executable incompleteness: BOTH.** There is a data-lineage/governance split, and there are genuine residual research gaps.
4. **One canonical rule source of truth? NO.**
5. **Should new research start now? NO.** First perform the no-research identity and field consolidation steps so the new work is limited to exact residual questions and does not re-research already captured facts. Then start the targeted 74-program backlog.

## Final accounting

- P0 programs: 74
- root-classified: 74
- precisely identified internal boundary: live/external DB unavailable; no recovery credit assigned
- `AUTHORITY_CLOSED`: 58; fully captured 0; incomplete/overstated 58
- programs recoverable without new research: 0
- programs requiring targeted new research for completeness: 74
- multiple effective rule-source paths: YES
- final gate: **CODEX_AUTHORITY_LINEAGE_RECONCILED**
