# Global Program AG–Codex Reconciliation Closeout

**Workstream:** `GLOBAL_PROGRAM_AG_CODEX_CONSOLIDATION`  
**Repository:** `surajgohill-oss/Frametax`  
**Branch:** `claude/audit-frametax-features-NZcX5`  
**Research cutoff:** current repository state at 2026-09-06  
**Mode:** repository reconciliation and read-only runtime assessment; no MFNI, database, rule, optimizer, or application changes

## Verdict

**STATUS: BLOCKED**

The complete selected AG/Gemini and Codex program-research union is accounted for, and every resulting identity has a manifest row and fail-closed treatment where necessary. It is **not safe for Claude implementation as a settled program universe** because 20 material classification conflicts, 22 duplicate AG source rows, a schema-shifted AG canonical-ID column, and 222 canonical programs with `UNKNOWN_FAIL_CLOSED` treatment remain.

The artifacts are safe as an implementation-blocking ledger. They are not permission to implement unresolved rates, eligibility, QPE, stacking, or compound program identities.

## Startup gate

- Git root confirmed: `/Users/Suraj/cineglobe-frametax`.
- Application confirmed: `frametax2/`.
- Remote confirmed: `https://github.com/surajgohill-oss/Frametax.git`.
- Branch and upstream confirmed: `claude/audit-frametax-features-NZcX5` and `origin/claude/audit-frametax-features-NZcX5`.
- Local and remote were equal at reconciliation start.
- `c5331fa9cef448fb96bf08d3e5dcdc3a2e256b4f` and `dcf146cb7cccb8b413b16e31e9f8e6f8f8157ca1` are ancestors.
- Unrelated untracked user files were preserved and excluded.
- No MFNI artifact was read into or used to populate the program manifest.

## Active source union

| Engine/corpus | Artifact | Source records |
|---|---|---:|
| Codex primary | `CODEX_GLOBAL_INCENTIVE_VALIDATION.json` | 285 |
| Codex secondary | `CURRENT_DISCRETIONARY_PROGRAM_INVENTORY_CODEX.md` | 160 |
| AG/Gemini primary | `GEMINI_WORLDWIDE_AUTHORITY_VALIDATION.json` | 287 |
| AG/Gemini secondary | `SECONDARY_PROGRAM_EVIDENCE_CERTIFICATION_FINAL_AG.csv` | 231 |
| **Total** |  | **963** |

The earlier 415-row `GEMINI_GLOBAL_INCENTIVE_VALIDATION.json` is explicitly superseded by the 287-row worldwide artifact and is inventoried but not double-counted. Derived cross-engine closeouts are reconciliation evidence, not independent source records. The artifact inventory records commit chronology and supersession.

All 963 active source records have exactly one source key and map to exactly one manifest identity. The AG secondary artifact contains 22 repeated rows; they remain individually traceable through `duplicate_of` lineage rather than silently disappearing.

## Canonical accounting

| Measure | Count |
|---|---:|
| Union source records | 963 |
| Unique canonical identities after source/runtime normalization | 586 |
| Exact agreements | 145 |
| Non-material differences | 136 |
| AG-only programs | 119 |
| Codex-only/runtime-only programs | 166 |
| Material conflicts | 20 |
| Duplicate records/aliases | 10 |
| Superseded programs | 3 |

Identity matching prioritized stable program IDs, exact canonical slugs, jurisdiction/parent scope, exact official name, current runtime identity, program form, and retained authority. Records were not merged by a fuzzy name-only heuristic. Unmatched and compound AG rows remain independent fail-closed identities.

## Canonical treatments

| Treatment | Count |
|---|---:|
| `AUTOMATIC_FORMULAIC` | 54 |
| `CONDITIONAL_FORMULAIC` | 42 |
| `DISCRETIONARY_DISPLAY_ONLY` | 201 |
| `NON_ECONOMIC_DISPLAY_ONLY` | 53 |
| `UNKNOWN_FAIL_CLOSED` | 222 |
| `INACTIVE_OR_EXPIRED` | 1 |
| `SUPERSEDED_OR_ALIAS` | 13 |
| **Total** | **586** |

No discretionary, non-economic, unknown, inactive, duplicate, or superseded program is authorized for automatic pricing. Formulaic status is accepted only where the current runtime has a real rate rule and is not blocked by its canonical authority-coverage gate; otherwise the manifest uses conditional or fail-closed treatment.

## Read-only runtime/database gap assessment

The current runtime contains 303 catalog entries, 134 conditional opportunity nodes, 125 executable rate-program IDs, 145 authority-coverage records, and 73 program-requirement profiles.

| Status | Count |
|---|---:|
| Database/runtime present | 416 |
| Database/runtime absent | 170 |
| Correctly present and wired | 12 |
| Present but partially wired | 393 |
| Present but misclassified | 2 |
| Present but duplicate or stale | 9 |
| Programs requiring an implementation action | 570 |

“Present” means represented in at least one canonical runtime owner: worldwide catalog, conditional index, executable rate registry, optimizer consumption ledger, or authority-coverage registry. It does not mean fully connected. The manifest separately records eligibility, QPE, rate, uplift, cap, monetization, stackability, treaty, scenario, and automatic-pricing status.

## Material classification conflicts

Twenty identities have a formulaic-versus-selective/grant/discretionary conflict and are set to `UNKNOWN_FAIL_CLOSED`: `ar_incaa_incentive`, `au_qld_screen_qld`, `au_vic_vicscreen`, `cl_corfo_incentive`, `gb_sct_screen_fund`, `gb_wls_screen_fund`, `il_film_incentive`, `jo_rfc_rebate`, `jp_film_incentive`, `kr_film_incentive`, `mt_mfc_rebate`, `mu_edb_incentive`, `nl_nfpi`, `no_film_incentive`, `tn_film_incentive`, `tr_film_incentive`, `us_ky_keiia`, `us_or_opif`, `us_pa_film_credit`, and `us_wa_mpcp`.

These conflicts concern whether a formula is an entitlement/eligible calculation or merely a ceiling within competitive allocation. They cannot be resolved by choosing the later file. The blocker ledger preserves both classifications and requires the current controlling program authority.

## The 39-versus-20 issue

The reported numbers are neither competing canonical-program migration counts nor overlapping sets:

- **39** comes from the Markdown summary of `CODEX_AUTHORITY_DELTA_RECOVERY_CLOSEOUT`, but the paired JSON reproduces only **38 newly recovered items**: 5 source-family dispositions + 24 program-type IDs + 9 RateCondition kinds. The JSON also has 2 `ALREADY_RECOVERED` source-family items. Therefore even the historical 39 is internally inconsistent and is not a 39-program migration manifest.
- **20** comes from `GLOBAL_CANONICAL_PROGRAM_DISPOSITION.json`: it is the `ADD` subset of the 23 missing-program discoveries. Those are net-new additions, not later formulaic reclassifications.
- AG later reports **13** “formulaic reclassifications,” but the cited `SECONDARY_PROGRAM_EVIDENCE_CERTIFICATION_FINAL_AG.csv` does not retain usable canonical IDs for that cohort: its `canonical_program_id` column contains percentages/value labels after a schema shift. Therefore the asserted 13 cannot be handed to Claude as exact IDs.

The exact 20 `ADD` IDs are retained in the canonical disposition artifact and mapped in this manifest. No artificial 39-program or 20-program reclassification set is created.

The 24 actual canonical program IDs inside the 38-item recovery set are: `ar_incaa_incentive`, `au_nsw_screen`, `au_qld_screen_qld`, `au_vic_vicscreen`, `bc_interactive_digital_media_tax_credit_idmtc`, `br_ancine_incentive`, `ca_federal_cptc`, `ca_nl_production_fund`, `dk_film_incentive`, `gb_sct_screen_fund`, `gb_wls_screen_fund`, `in_national_film`, `in_nfdc_coproduction`, `jm_film_incentive`, `mx_eficine_incentive`, `new_zealand_screen_production_grant_—_international_post_vfx`, `on_ofttc`, `ontario_computer_animation_and_special_effects_tax_credit_ocase`, `pe_film_incentive`, `pt_film_incentive`, `qc_film_production`, `us_itvs_fund`, `us_sundance_doc`, and `uy_xxi_incentive`.

The exact 20 later `ADD` identities are: `proposed_canada_film_or_video_production_services_tax_credit_pstc`, `proposed_canada_british_columbia_film_incentive_bc_fibc`, `proposed_canada_quebec_refundable_tax_credit_for_film_production_services`, `proposed_united_states_new_jersey_garden_state_film_and_digital_media_jobs_act_film_credit`, `proposed_united_states_new_york_film_tax_credit_post_production`, `proposed_united_states_new_york_empire_state_independent_film_production_credit`, `proposed_united_states_ohio_ohio_motion_picture_tax_credit`, `proposed_united_states_arkansas_digital_product_and_motion_picture_industry_incentive`, `proposed_united_states_west_virginia_west_virginia_film_production_tax_credit`, `proposed_united_states_missouri_motion_media_production_tax_credit`, `proposed_united_states_montana_media_tax_credit`, `proposed_australia_producer_offset_separate_statutory_program`, `proposed_united_kingdom_enhanced_avec_independent_film_tax_credit_iftc`, `proposed_united_kingdom_uk_global_screen_fund_international_co_production`, `proposed_germany_german_motion_picture_fund_gmpf`, `proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate`, `proposed_colombia_cina_audiovisual_investment_certificate`, `proposed_spain_navarre_navarre_audiovisual_production_tax_credit`, `proposed_netherlands_netherlands_film_production_incentive_high_end_series`, and `th_prd_foreign_digital_content_incentive`.

## Stackability and secondary-program count reconciliation

- The selected AG final secondary artifact reports **0 verified not-stackable rows** and **231 unknown-after-targeted-research source rows**. After removing its 22 duplicate rows, that is 209 distinct AG secondary row identities.
- The later 208-row AG ledger's **195** count means `PRIOR_VERIFIED_NO_NEW_RESEARCH_NEEDED`; it is not a valid unknown-stackability count. Moreover, those 195 appended rows are schema-shifted. The reconciled canonical manifest has **569 programs with unknown stackability**, all retained fail closed.
- Runtime stacking contains 13 mutually-exclusive *pair rules*, not 32 “not-stackable programs.” Four reconciled manifest program IDs participate in at least one such pair. Pair restrictions are not converted into a global per-program `NOT_STACKABLE` label.
- AG's reported **116** secondary non-formulaic/support source rows is a raw taxonomy count (60 grants + 46 selective + 1 discretionary + 1 equity + 1 development-only + 7 facilitation). It includes duplicate/compound source rows and is not the canonical unique-program total. The combined deduplicated manifest contains 201 `DISCRETIONARY_DISPLAY_ONLY` programs and 53 `NON_ECONOMIC_DISPLAY_ONLY` programs.

## Completeness gates

| Gate | Result |
|---|---|
| Every AG/Gemini active source record accounted for | PASS — 518/518 |
| Every Codex active source record accounted for | PASS — 445/445 |
| Every source row maps to a canonical identity or explicit duplicate | PASS |
| AG-only and Codex-only identities explicit | PASS |
| Material conflicts explicit and fail closed | PASS |
| Unresolved values excluded from automatic pricing/stacking | PASS |
| Every canonical identity has one manifest action | PASS — 586/586 |
| Current runtime/catalog records assessed | PASS |
| No MFNI record included | PASS |
| Aggregate counts reproduce from CSVs | PASS |
| Safe for Claude implementation without research | **FAIL** |

## Blocking resolution required

1. Repair or replace the AG secondary artifact with schema-valid stable canonical IDs, particularly the claimed 13 reclassifications.
2. Adjudicate the 20 formulaic-versus-selective material conflicts using current controlling authority.
3. Resolve the 222 `UNKNOWN_FAIL_CLOSED` identities and the 569 unknown stackability statuses to either authoritative priceable rules or explicit display-only/non-priceable treatment.
4. Re-run this deterministic manifest build only after those inputs are settled; Claude must not research around the blockers during implementation.

Until then, the only canonical next step is targeted program-authority/identity closure, not database or optimizer implementation.
