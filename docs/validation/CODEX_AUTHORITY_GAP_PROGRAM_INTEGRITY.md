# Codex Authority-Gap Program Type / Database Integrity Audit

Date: 2026-08-16

**Final gate: CODEX_AUTHORITY_GAP_INTEGRITY_CLASSIFIED**

## Scope and evidence boundary

This audit classifies the 75-program deduplicated union of the TRUE_AUTHORITY_GAP sets established in CODEX_PRICEABILITY_BLOCKER_RECONCILIATION.md. It uses only existing repository/canonical corpus evidence. No source URL was fetched, no jurisdiction rule was researched, and no program, database, authority, evaluation, optimizer, or UI record was changed.

Evidence used:

- authority_coverage_registry.py and its canonical-to-runtime slug bindings
- CODEX_GLOBAL_INCENTIVE_VALIDATION.json program names, stored types, rates, QPE coverage, territoriality, and validation states
- GLOBAL_CANONICAL_PROGRAM_DISPOSITION.json identity/disposition records
- GLOBAL_REMEDIATION_EXECUTABLE_DATA.json disabled executable payloads and missing literal fields
- the accepted LU/FVD blocker reconciliation for exact project membership

## Central answer

**74 of 75 unique authority-gap programs (98.7%) are traditional or formulaic production incentives. All 74 are CORE_PROGRAM_INCOMPLETE.** The remaining record, Kazakhstan production support, is PROGRAM_TYPE_UNRESOLVED because the corpus does not prove a producer-accessible economic formula. None of the 75 is established by the existing corpus as selective, negotiated, non-economic, financing, superseded, or duplicative.

This is a database completeness problem, not an expected concentration of discretionary funds. The traditional-incentive database integrity gate is **FAIL**.

## Deduplication accounting

| Measure | Count |
|---|---:|
| LU authority-gap programs | 56 |
| FVD authority-gap programs | 75 |
| Programs in both projects | 56 |
| FVD-only programs | 19 |
| Unique union | **75** |
| Affected structure occurrences | 187 |

Canonical/runtime aliases were collapsed with CANONICAL_RUNTIME_SLUG_BINDINGS; no program is double-counted merely because it appears in both projects or under two spellings. All 75 current gap records are not marked superseded; they are disabled pending sufficient authority. A prior STALE validation label means the stored rule record is stale, not that the real program identity is proven superseded.

## Program type and determinism

| Primary type | Count | Determinism treatment |
|---|---:|---|
| TRADITIONAL_TAX_CREDIT | 31 | CONDITIONALLY_DETERMINISTIC |
| TRADITIONAL_CASH_REBATE | 39 | CONDITIONALLY_DETERMINISTIC |
| TRADITIONAL_OFFSET_OR_REFUND | 2 | CONDITIONALLY_DETERMINISTIC |
| AUTOMATIC_FORMULA_GRANT | 2 | CONDITIONALLY_DETERMINISTIC |
| SELECTIVE_OR_DISCRETIONARY | 0 | - |
| NEGOTIATED_INCENTIVE | 0 | - |
| NON_ECONOMIC_PRODUCTION_SUPPORT | 0 | - |
| LOAN_OR_FINANCING_PROGRAM | 0 | - |
| SUPERSEDED_OR_DUPLICATE | 0 | - |
| PROGRAM_TYPE_UNRESOLVED | 1 | UNRESOLVED |
| **Traditional/formulaic total** | **74** | **98.7% of union** |

Conditionally deterministic is deliberate: the stored program type/formula design is enough to distinguish these programs from selective awards, but actual project eligibility still depends on rules that are incomplete. It does not claim any program will price once research starts.

## Database maturity scorecard

| Measure | Count |
|---|---:|
| Unique active incentive programs in gap set | 74 |
| Traditional/formulaic | 74 |
| CORE_PROGRAM_INCOMPLETE | 74 |
| SECONDARY_PROGRAM_INCOMPLETE | 0 |
| APPROPRIATELY_NONDETERMINISTIC | 0 |
| APPROPRIATELY_NON_ECONOMIC | 0 |
| STALE_OR_DUPLICATIVE_RECORD | 0 |
| INSUFFICIENT_METADATA_TO_CLASSIFY | 1 |

**DATABASE INTEGRITY FOR TRADITIONAL INCENTIVES: FAIL**

A material body of ordinary film/TV tax credits, rebates, offsets, and formula grants is currently disabled because the canonical executable authority records are incomplete.

## Missing-rule dimensions

The JSON companion assigns explicit flags to every program. The compact inventory table uses these exact abbreviations:

| Code | Canonical missing-rule dimension |
|---|---|
| RATE | RATE_OR_AWARD_BASIS |
| QPE | QPE_DEFINITION |
| TERR | TERRITORIALITY |
| MIN | MINIMUM_SPEND |
| CAP | CAP |
| TYPE | ELIGIBLE_PRODUCTION_TYPE |
| CULT | CULTURAL_OR_CONTENT_TEST |
| UP | UPLIFT_RULES |
| RES | RESIDENT_NONRESIDENT_TREATMENT |
| PAY | PAYROLL_TREATMENT |
| MON | MONETIZATION |
| REF | REFUNDABILITY |
| XFER | TRANSFERABILITY |
| TIME | APPLICATION_TIMING |
| OTHER | OTHER |

A flag means the current executable canonical record lacks a verified literal rule or a verified authority-silence state. It does not mean the underlying authority necessarily fails to publish the rule, and it does not authorize use of stale/discovery values.

Most frequent flags:

| Missing dimension | Programs |
|---|---:|
| ELIGIBLE_PRODUCTION_TYPE | 75 |
| QPE_DEFINITION | 75 |
| RATE_OR_AWARD_BASIS | 75 |
| TERRITORIALITY | 75 |
| CAP | 74 |
| MINIMUM_SPEND | 74 |
| MONETIZATION | 74 |
| PAYROLL_TREATMENT | 74 |
| RESIDENT_NONRESIDENT_TREATMENT | 74 |
| UPLIFT_RULES | 74 |
| CULTURAL_OR_CONTENT_TEST | 57 |
| APPLICATION_TIMING | 56 |
| OTHER | 39 |
| REFUNDABILITY | 32 |
| TRANSFERABILITY | 31 |

## Database-integrity red flags

- **P0 - 74 well-identified formulaic programs have no usable executable rate/award basis.** 70 retain a stored discovery/stale base or maximum rate, proving the identity is not merely a blank placeholder, but those values were not accepted into the executable authority layer.
- **P0 - 54 programs combine stored rate/max metadata with zero structured QPE categories.** A headline percentage without a defensible QPE base cannot produce reliable NPC.
- **P0 - 74 formulaic programs lack structured territoriality.** A local SPV payment cannot substitute for vendor, residence, performance, use/consumption, incurrence, or payment predicates.
- **P0 - 31 recognizable tax-credit records are still UNPRICEABLE_AUTHORITY_INSUFFICIENT.** Their current executable records also do not establish refundability/transferability sufficiently for monetized value.
- **P0 - 58 records are marked AUTHORITY_CLOSED in the canonical disposition artifact but remain disabled because literal executable rules were not completed.** Research closure and executable database completion are materially different gates.
- **P0 - mainstream examples include GB AVEC, Canada federal PSTC, Spain foreign-production tax credit, France TRIP, Ireland Section 481, Italy foreign-production credit, New Zealand SPG, and major US credits in California, Georgia, Louisiana, and New Mexico.** These are core database records, not peripheral opportunity funds.
- **P1 - Kazakhstan is generated as an incentive candidate while the corpus describes production facilitation and explicitly lacks proof of producer-accessible economics.** Resolve type/economic existence before researching rate mechanics.
- **P1 - the Germany runtime row is named DFFF/GFFF even though existing validation says DFFF must be updated and GMPF added as a distinct identity.** This audit counts the current runtime row once and does not manufacture an additional gap-set candidate.
- Duplicate current programs in the deduplicated gap set: **0**. Superseded programs participating as true authority gaps: **0**.

## Prioritized authority-completion backlog

| Backlog band | Programs | Effect |
|---|---:|---|
| P0-A core formulaic; affects both LU and FVD | 56 | POTENTIALLY_PRICEABLE; still requires rule and project qualification validation |
| P0-B core formulaic; FVD-only | 18 | POTENTIALLY_PRICEABLE; still requires rule and project qualification validation |
| P1 metadata/type resolution | 1 | NOT_STANDARD_PRICEABLE unless producer-accessible economics are first established |

Within P0, both-project and three-structure records precede FVD-only records. The JSON backlog_rank supplies the exact order. No completion is claimed, and no selective award is promoted into guaranteed economics.

## Programs affecting both LU and FVD

Count: **56**. Each affects three structures.

AE-AD/ae_ad_film_rebate, AL/al_cash_rebate, BE/be_tax_shelter, BG/bg_film_encouragement_act_rebate, CA/ca_federal_pstc, CA-BC/ca_bc_pstc, CA-NB/ca_nb_film_tax_credit, CA-NS/ca_ns_production_incentive_fund, CA-ON/ca_on_opstc, CL/cl_corfo_incentive, CO/co_film_in_colombia, CY/cy_film_rebate, DE/de_dfff, DO/do_film_commission_incentive, EE/ee_film_estonia_rebate, ES/es_tax_credit_foreign, FI/fi_business_finland_incentive, FR/fr_trip, GB/uk_avec, HR/hr_cash_rebate, IE/ie_section_481, IS/is_film_reimbursement_scheme, IT/it_tax_credit_foreign, LT/lt_film_centre_cash_rebate, LV/lv_national_film_centre_incentive, MA/ma_ccm_rebate, ME/me_cash_rebate, NL/nl_film_production_incentive, NO/no_film_incentive, NZ/nz_spg_international, PL/pl_pisf_cash_rebate, RO/ro_film_office_cash_rebate, SA/sa_film_commission_rebate, SE/se_production_rebate, SI/si_cash_rebate, TT/tt_production_expenditure_rebate, US-AL/us_al_film_incentive, US-CA/us_ca_film_credit, US-CT/us_ct_film_tax_credit, US-GA/us_ga_film_credit, US-HI/us_hi_film_digital_media_credit, US-IL/us_il_film_production_services_credit, US-KY/us_ky_keiia, US-LA/us_la_film_incentive, US-MA/us_ma_film_tax_credit, US-MD/us_md_film_production_activity_credit, US-MN/us_mn_film_production_credit, US-MS/us_ms_advantage_film_program, US-NC/us_nc_film_entertainment_grant, US-OR/us_or_opif, US-PR/us_pr_film_incentives_act, US-RI/us_ri_film_credit, US-SC/us_sc_film_production_credit, US-TX/us_tx_miip, US-VA/us_va_motion_picture_credit, US-WA/us_wa_motion_picture_competitiveness

## Complete deduplicated inventory

| # | Code | Program / runtime slug | Canonical ID | LU | FVD | Structures | Type | Determinism | Integrity | Corpus status | Disposition | Missing flags | Priority |
|---:|---|---|---|:---:|:---:|---:|---|---|---|---|---|---|---|
| 1 | AE-AD | Abu Dhabi 35++ Production Rebate / ae_ad_film_rebate | proposed_united_arab_emirates_abu_dhabi_abu_dhabi_35_production_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | RECLASSIFIED_UNPRICEABLE_AUTHORITY_INSUFFICIENT | ADD | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 2 | AL | Albanian National Cinema Agency (ANCA) Cash Rebate / al_cash_rebate | al_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 3 | BE | Belgian Tax Shelter / be_tax_shelter | be_tax_shelter | Y | Y | 3 | TRADITIONAL_OFFSET_OR_REFUND | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON | P0 |
| 4 | BG | Bulgarian Film Commission Cash Rebate / bg_film_encouragement_act_rebate | bg_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 5 | CA | Film or Video Production Services Tax Credit (PSTC) / ca_federal_pstc | proposed_canada_film_or_video_production_services_tax_credit_pstc | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | RECLASSIFIED_UNPRICEABLE_AUTHORITY_INSUFFICIENT | ADD | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 6 | CA-BC | BC Production Services Tax Credit / ca_bc_pstc | bc_pstc | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 7 | CA-NB | New Brunswick Film Tax Credit / ca_nb_film_tax_credit | ca_nb_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,REF,XFER,OTHER | P0 |
| 8 | CA-NS | Nova Scotia Film & Television Production Incentive Fund / ca_ns_production_incentive_fund | ca_ns_pif | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,OTHER | P0 |
| 9 | CA-ON | Ontario Production Services Tax Credit / ca_on_opstc | on_opstc | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 10 | CL | Chile Corfo Film Incentive / cl_corfo_incentive | cl_corfo_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 11 | CO | Colombia Film Commission — Film In Colombia / co_film_in_colombia | co_film_colombia | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 12 | CY | Cyprus Film Production Rebate / cy_film_rebate | cy_film_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,OTHER | P0 |
| 13 | DE | German Federal Film Fund (DFFF/GFFF) / de_dfff | de_dfff | Y | Y | 3 | AUTOMATIC_FORMULA_GRANT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,OTHER | P0 |
| 14 | DO | Dominican Republic Film Commission Incentive / do_film_commission_incentive | do_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 15 | EE | Film Estonia Cash Rebate / ee_film_estonia_rebate | ee_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 16 | ES | Spanish Tax Credit for Foreign Productions / es_tax_credit_foreign | es_tax_credit_foreign | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCORRECT | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 17 | FI | Business Finland Film Incentive / fi_business_finland_incentive | fi_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME | P0 |
| 18 | FR | Tax Rebate for International Productions (TRIP) / fr_trip | fr_trip | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,OTHER | P0 |
| 19 | GB | UK Audio Visual Expenditure Credit / uk_avec | uk_avec | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,REF,XFER | P0 |
| 20 | HR | Croatia Cash Rebate / hr_cash_rebate | hr_cash_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT | P0 |
| 21 | IE | Section 481 Film Tax Credit / ie_section_481 | ie_section_481 | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,REF,XFER | P0 |
| 22 | IS | Icelandic Film Reimbursement Scheme / is_film_reimbursement_scheme | is_film_reimbursement | Y | Y | 3 | TRADITIONAL_OFFSET_OR_REFUND | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF | P0 |
| 23 | IT | Italian Tax Credit for Foreign Productions / it_tax_credit_foreign | it_tax_credit_foreign | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 24 | LT | Lithuanian Film Centre Production Cash Rebate / lt_film_centre_cash_rebate | lt_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 25 | LV | National Film Centre of Latvia Production Incentive / lv_national_film_centre_incentive | lv_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 26 | MA | CCM Morocco — Production Rebate / ma_ccm_rebate | ma_ccm_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 27 | ME | Film Centre of Montenegro Production Incentive / me_cash_rebate | me_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 28 | NL | Netherlands Film Production Incentive (NFPI) / nl_film_production_incentive | nl_nfpi | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME | P0 |
| 29 | NO | Norwegian Film Commission Production Incentive / no_film_incentive | no_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME | P0 |
| 30 | NZ | New Zealand Screen Production Grant (International) / nz_spg_international | nz_spg_international | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,OTHER | P0 |
| 31 | PL | Polish Film Institute (PISF) Cash Rebate / pl_pisf_cash_rebate | pl_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,OTHER | P0 |
| 32 | RO | Romanian Film Office Cash Rebate / ro_film_office_cash_rebate | ro_cnc_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 33 | SA | Saudi Film Commission (SFC) — Production Rebate / sa_film_commission_rebate | sa_sfc_rebate | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 34 | SE | Sweden Film Commission Production Rebate / se_production_rebate | se_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME | P0 |
| 35 | SI | Slovenian Film Centre (SFC) Cash Rebate and Production Support / si_cash_rebate | si_film_incentive | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 36 | TT | Trinidad & Tobago Creative Industries Production Incentive / tt_production_expenditure_rebate | tt_film_incentive | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 37 | US-AL | Alabama Film Incentive / us_al_film_incentive | us_al_film_incentive | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 38 | US-CA | California Film & Television Tax Credit Program 3.0 / us_ca_film_credit | ca_film_30 | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER | P0 |
| 39 | US-CT | Connecticut Film Tax Credit / us_ct_film_tax_credit | us_ct_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 40 | US-GA | Georgia Entertainment Industry Investment Act / us_ga_film_credit | georgia_eiia | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCORRECT | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 41 | US-HI | Hawaii Film and Digital Media Income Tax Credit / us_hi_film_digital_media_credit | us_hi_film_tax_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 42 | US-IL | Illinois Film Tax Credit / us_il_film_production_services_credit | us_il_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 43 | US-KY | Kentucky Entertainment Industry Incentive Act (KEIIA) / us_ky_keiia | us_ky_keiia | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 44 | US-LA | Louisiana Motion Picture Production Tax Credit / us_la_film_incentive | la_film_production | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCORRECT | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER | P0 |
| 45 | US-MA | Massachusetts Film Tax Credit / us_ma_film_tax_credit | us_ma_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 46 | US-MD | Maryland Film Production Activity Tax Credit / us_md_film_production_activity_credit | us_md_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 47 | US-MN | Minnesota Film Production Tax Credit / us_mn_film_production_credit | us_mn_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 48 | US-MS | Mississippi Advantage Film Program / us_ms_advantage_film_program | us_ms_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 49 | US-NC | North Carolina Film & Entertainment Grant / us_nc_film_entertainment_grant | us_nc_film_grant | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 50 | US-OR | Oregon Production Investment Fund (OPIF) / us_or_opif | or_opif | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCORRECT | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT | P0 |
| 51 | US-PR | Puerto Rico Film Industry Economic Incentives Act / us_pr_film_incentives_act | us_pr_film_incentive | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 52 | US-RI | Rhode Island Motion Picture Production Tax Credit / us_ri_film_credit | us_ri_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 53 | US-SC | South Carolina Film Production Credit / us_sc_film_production_credit | us_sc_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 54 | US-TX | Texas Moving Image Industry Incentive Program (MIIP) / us_tx_miip | us_tx_miip | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 55 | US-VA | Virginia Motion Picture Production Tax Credit / us_va_motion_picture_credit | us_va_film_credit | Y | Y | 3 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 56 | US-WA | Washington State Motion Picture Competitiveness Program / us_wa_motion_picture_competitiveness | us_wa_mpcp | Y | Y | 3 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 57 | AT | FISA+ Film Production Support Austria / at_fisa_plus | at_fisa_plus | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,OTHER | P0 |
| 58 | CA-AB | Alberta Film and Television Tax Credit (FTTC) / ca_ab_fttc | ca_ab_fttc | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,REF,XFER,OTHER | P0 |
| 59 | CA-MB | Manitoba Film & Video Production Tax Credit / ca_mb_film_video_credit | ca_mb_fvptc | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,REF,XFER,OTHER | P0 |
| 60 | CA-SK | Creative Saskatchewan Film and TV Production Grant / ca_sk_creative_saskatchewan_grant | ca_sk_production_grant | N | Y | 1 | AUTOMATIC_FORMULA_GRANT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME | P0 |
| 61 | CZ | Czech Film Incentive / cz_film_incentive | cz_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | STALE | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 62 | HU | Hungarian Tax Rebate (HIPA) / hu_hipa_rebate | hu_hipa_rebate | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,OTHER | P0 |
| 63 | LU | Film Fund Luxembourg — Tax Shelter & Production Rebate / lu_filmfund_tax_shelter_rebate | lu_film_incentive | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,TIME,REF,XFER | P0 |
| 64 | MK | Macedonian Film Agency (MFA) Cash Rebate / mk_cash_rebate | mk_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 65 | RS | Serbia Film Commission Cash Rebate / rs_film_commission_cash_rebate | rs_film_rebate | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 66 | SK | Slovak Audiovisual Fund (AVF) Production Incentive / sk_avf_production_incentive | sk_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 67 | US-AZ | Arizona Motion Picture Production Program / us_az_motion_picture_production | us_az_film_credit | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 68 | US-CO | Colorado Film Incentive / us_co_film_incentive | us_co_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 69 | US-NM | New Mexico Film Production Tax Credit / us_nm_film_credit | nm_film_production | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCORRECT | CORRECT | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,REF,XFER,OTHER | P0 |
| 70 | US-NV | Nevada Film Incentive Program / us_nv_film_credit | us_nv_film_incentive | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER | P0 |
| 71 | US-OK | Oklahoma Film Enhancement Rebate / us_ok_film_enhancement_rebate | us_ok_ofer | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 72 | US-PA | Pennsylvania Film Production Tax Credit / us_pa_film_production_credit | us_pa_film_credit | N | Y | 1 | TRADITIONAL_TAX_CREDIT | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,REF,XFER,OTHER | P0 |
| 73 | US-TN | Tennessee Film Entertainment Incentives / us_tn_performance_grant | us_tn_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME,OTHER | P0 |
| 74 | US-UT | Utah Motion Picture Incentive Program / us_ut_motion_picture_incentive | us_ut_film_incentive | N | Y | 1 | TRADITIONAL_CASH_REBATE | CONDITIONALLY_DETERMINISTIC | CORE_PROGRAM_INCOMPLETE | INCOMPLETE | AUTHORITY_CLOSED | RATE,QPE,TERR,MIN,CAP,TYPE,UP,RES,PAY,MON,CULT,TIME | P0 |
| 75 | KZ | kz_film_incentive / kz_investment_subsidy | kz_film_incentive | N | Y | 1 | PROGRAM_TYPE_UNRESOLVED | UNRESOLVED | INSUFFICIENT_METADATA_TO_CLASSIFY | UNRESOLVED | UNPRICEABLE_AUTHORITY_INSUFFICIENT | RATE,QPE,TERR,TYPE,OTHER | P1 |

## Classification notes

- Belgium Tax Shelter and the Icelandic reimbursement scheme are TRADITIONAL_OFFSET_OR_REFUND from their stored identities/mechanisms; neither is treated as a selective fund.
- DFFF/GFFF and Creative Saskatchewan are AUTOMATIC_FORMULA_GRANT: the corpus stores grant types, formula/rate metadata, objective gates, and no selection/discretion flag. Their incomplete authority records still prevent pricing.
- Kazakhstan alone remains PROGRAM_TYPE_UNRESOLVED; the corpus explicitly asks for proof of producer-accessible economics.
- The selective Jordan, Japan, and South Korea programs are outside this set because the prior reconciliation correctly classified them outside TRUE_AUTHORITY_GAP.

## Final gate

**CODEX_AUTHORITY_GAP_INTEGRITY_CLASSIFIED**

Every one of the 75 deduplicated programs has a program type, determinism class, database-integrity class, missing-rule dimensions, priority, project impact, and expected completion effect.
