# Codex Historical Authority Source Cross-Reference

Final gate: `CODEX_HISTORICAL_AUTHORITY_CROSS_REFERENCE_READY`

## Actionable result

This forensic pass found no deleted authority/rule module in repository-wide deletion history. The remaining failure class is live data that is unconsumed or only partly consumed by the committed canonical path, plus superseded evaluators and migration seeds. No external research was performed.

Snapshot: branch `claude/audit-frametax-features-NZcX5`, commit `74d484bf08dd11206e00250942760792fea09c8a`. The concurrent Claude edit to `canonical_program_consolidation.py` was observed but excluded; it had begun importing ProgramRequirements and jurisdiction profiles but had not completed field survival at this snapshot.

- Authority-bearing source families classified: **18**.
- Programs with a primary-current requirements candidate or an explicit source-linked unresolved-type candidate: **104**.
- Historical dimensions with a potentially recoverable structured candidate: **11/14** — RATE_OR_AWARD_BASIS, QPE_DEFINITION, MINIMUM_SPEND, CAP, ELIGIBLE_PRODUCTION_TYPE, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES, MONETIZATION, REFUNDABILITY, TRANSFERABILITY, APPLICATION_TIMING.
- No safe *new* recovery candidate was found for `TERRITORIALITY`, `RESIDENT_NONRESIDENT_TREATMENT`, or `PAYROLL_TREATMENT`; current SpendRules remain the defensible source for those dimensions.
- Explicit unresolved program-type candidates: **45 of 88**; **38** are corroborated by both remediation and live inventory, and **6** additional model-only leads lack adequate provenance.
- Primary-current application-timing candidates: **98 field values across 49 programs**. Seven secondary-profile timing leads are deliberately not closure candidates.

## Source-family cross-reference

| Source family | Classification | Programs | Dimensions/signals | Current survival | Smallest action |
| --- | --- | --- | --- | --- | --- |
| app.data.executable_jurisdiction_registry.DoctrineRecord | CURRENTLY_CONSUMED | 107 | MINIMUM_SPEND, CAP, CULTURAL_OR_CONTENT_TEST, MONETIZATION, REFUNDABILITY, TRANSFERABILITY, RATE_OR_AWARD_BASIS | wired by commit 74d484b into canonical_program_consolidation; Georgia improved 4/14 to 10/14 | none |
| app.data.program_spend_rules | CURRENTLY_CONSUMED | 16 | QPE_DEFINITION, TERRITORIALITY, RESIDENT_NONRESIDENT_TREATMENT, PAYROLL_TREATMENT | canonical consolidation calls get_program_rules and resolve_program_doctrine | none |
| app.data.program_requirements primary/current field set | ORPHANED_VALID_SOURCE | 59 | APPLICATION_TIMING, CAP, CULTURAL_OR_CONTENT_TEST, MINIMUM_SPEND, MONETIZATION, REFUNDABILITY, TRANSFERABILITY | committed HEAD does not consume this registry; concurrent Claude worktree has begun an adapter but had not completed field survival at the forensic snapshot | complete the in-progress field-level adapter with source/status/timing-basis gates; do not import secondary profiles or blanket-promote a profile |
| app.data.program_rate_rules + program_rate_rules_worldwide + QPE_CAP_RULES | PARTIALLY_CONSUMED | 113 | RATE_OR_AWARD_BASIS, MINIMUM_SPEND, CAP, ELIGIBLE_PRODUCTION_TYPE, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES, QPE_DEFINITION | rates, min_qpe_usd, production_types, tier count and QpeCapRule survive; most RateCondition.kind propositions do not receive dimension-specific survival | map only enumerated condition kinds to the dimension they actually prove, retaining confidence and partiality |
| app.calculators.jurisdiction_comparison.ALL_PROFILES | PARTIALLY_CONSUMED | 110 | RATE_OR_AWARD_BASIS, QPE_DEFINITION, MINIMUM_SPEND, CAP, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES, MONETIZATION, REFUNDABILITY, TRANSFERABILITY | canonical identity reads exact profile type/name; committed consolidation reads only resident_labor_uplift_available; DoctrineRecord carries some duplicated fields | adjudicate non-overlapping fields individually; never treat cashflow weeks, payroll burden or generic notes as primary authority |
| app.data.global_inventory.ALL_PROGRAMS | PARTIALLY_CONSUMED | 303 | RATE_OR_AWARD_BASIS, MINIMUM_SPEND, CAP, CULTURAL_OR_CONTENT_TEST, MONETIZATION, REFUNDABILITY, TRANSFERABILITY | discovery fallbacks survive only when an entry has a program_slug binding; the current 303-entry inventory has program_slug=None throughout. Forty-five unresolved identities retain exact historical type evidence through source-linked remediation records and/or unique exact full-name equality, but current identity mapping does not bind those records | bind exact canonical IDs to adjudicated explicit types; do not use lexical name inference |
| historical spend-treatment Alembic seed waves 0017-0041 | DUPLICATE_SOURCE | not normalized | QPE_DEFINITION, TERRITORIALITY, RESIDENT_NONRESIDENT_TREATMENT, PAYROLL_TREATMENT | current static SpendRule registry is the operative equivalent | none; use only to investigate a concrete mismatch against the current static registry |
| historical SourceDocument/profile seed migrations 0010 and 0013 | SUPERSEDED_SOURCE | 5 | RATE_OR_AWARD_BASIS, QPE_DEFINITION, MINIMUM_SPEND, CAP | later RateRule, SpendRule, DoctrineRecord and ProgramRequirements records supersede the usable propositions | none unless a unique quoted proposition is proven absent from all later typed records |
| app.calculators.mediterranean_comparison | SUPERSEDED_SOURCE | 4 | RATE_OR_AWARD_BASIS, QPE_DEFINITION, APPLICATION_TIMING, PAYROLL_TREATMENT | not on served path; current typed registries supersede verified facts and contradict stale assumptions (for example MU 35% project rate and MT 25% base) | do not wire; use only as a conflict locator |
| Little Utopia engines/fixtures: mauritius_economics, qualification_model and QPE traces | PROJECT_SPECIFIC_SOURCE | 5 | QPE_DEFINITION, TERRITORIALITY, RATE_OR_AWARD_BASIS, APPLICATION_TIMING | served only for project economics/validation, not canonical authority closure | never promote project assumptions; trace any apparently general proposition back to its typed source registry |
| Bridge packages pkg_c530..., pkg_e230..., pkg_3c912..., pkg_958a..., pkg_61e5... | PROJECT_SPECIFIC_SOURCE | 5 | QPE_DEFINITION, TERRITORIALITY, RATE_OR_AWARD_BASIS | not canonical input; package response files were not used in this cross-reference | none; use the underlying ProgramRequirements/RateRule/SpendRule sources, not a project trace or AI response |
| CODEX_GLOBAL_INCENTIVE_VALIDATION + GLOBAL_CANONICAL_PROGRAM_DISPOSITION + GLOBAL_REMEDIATION_EXECUTABLE_DATA | VALIDATION_ARTIFACT_ONLY | 285 | RATE_OR_AWARD_BASIS, QPE_DEFINITION, TERRITORIALITY, MINIMUM_SPEND, CAP, ELIGIBLE_PRODUCTION_TYPE, CULTURAL_OR_CONTENT_TEST, UPLIFT_RULES, MONETIZATION, REFUNDABILITY, TRANSFERABILITY, APPLICATION_TIMING | not read by canonical consolidation; 45 exact explicit program-type findings remain unbound, and 23 source-linked remediation records overlap formulaic programs | extract only exact source-linked propositions into a typed registry; never import an artifact or status wholesale |
| GEMINI_GLOBAL_INCENTIVE_VALIDATION and distributed closure summaries | INSUFFICIENT_PROVENANCE | 415 | RATE_OR_AWARD_BASIS, QPE_DEFINITION, MINIMUM_SPEND, CAP | not read by canonical consolidation | do not wire without recovering the underlying official document and exact proposition |
| app.data.cultural_qualification_model + cultural_test_rules + UK hardcoded evaluator table | INSUFFICIENT_PROVENANCE | 24 | CULTURAL_OR_CONTENT_TEST, ELIGIBLE_PRODUCTION_TYPE | used by recommendation/qualification paths, not canonical consolidation | retain as an acquisition lead only until every criteria set has an exact official source/version |
| ProgramAdminDetails schema and Alembic admin seed waves 0016/0019/0020/0023/0027/0030/0033/0036 | INSUFFICIENT_PROVENANCE | not normalized | APPLICATION_TIMING, MONETIZATION, TRANSFERABILITY | not read by canonical consolidation | do not wire; prefer primary/current ProgramRequirements timing fields and use these rows only to locate a question |
| app.data.structure_graph_model + app.optimization.stacking_rules | INSUFFICIENT_PROVENANCE | not normalized | MONETIZATION, RATE_OR_AWARD_BASIS | served by optimizer structure paths but outside the 14-dimension canonical authority contract | do not use for authority closure until source citations exist per legal stacking proposition |
| program_requirements SECONDARY/non-primary profiles | INSUFFICIENT_PROVENANCE | 8 | APPLICATION_TIMING, CULTURAL_OR_CONTENT_TEST, MINIMUM_SPEND, MONETIZATION, REFUNDABILITY, TRANSFERABILITY | not canonical; seven formulaic profiles carry timing leads | retain as leads; do not promote dimensions until primary authority is captured |
| app.data.fund_economics_model program classification/economics registry | CONFLICTING_SOURCE | 243 | MONETIZATION, CAP, TERRITORIALITY | served in fund/demo paths, not canonical consolidation; conflicts with source-linked program-type taxonomy for multiple exact IDs | adjudicate taxonomy versus financing instrument; never choose this uncited classification over a source-linked program identity |

## ProgramRequirements: high-value orphaned fields

`program_requirements.py` contains 71 profiles. Of the 105 formulaic programs in the committed closeout, 67 have profiles: 59 primary-current and 8 secondary. The source family overlaps facts already carried by DoctrineRecord/RateRule, but its application timing and several qualification/compliance fields do not survive the committed canonical path.

The smallest safe action is a field-level adapter. A profile-level primary citation is not proof for every populated field; each promoted field must be supportable by the retained title/URL/authority and must preserve record status and timing basis. Local-entity, audit, bond, and clawback fields also expose a schema gap: they do not map cleanly to any of the present 14 dimensions and should not be hidden inside `ELIGIBLE_PRODUCTION_TYPE`.

## Application timing recovery

The 49 primary-current programs and retained field names are below. Full values, authorities, dates, caveats and URLs are in the JSON artifact.

| Canonical ID | Timing fields | Retained source | URL/provenance |
| --- | --- | --- | --- |
| ae_ad_film_rebate | preapproval_mandatory | 35%++ Cashback Rebate — Abu Dhabi Film Commission (Creative Media Authority) | https://www.film.gov.ae/35-rebate |
| be_tax_shelter | preapproval_mandatory, audit_or_final_certification_deadline, payment_timing | Tax Shelter — audiovisual production | https://finance.belgium.be/en/enterprises/corporation-tax/tax-benefits/tax-shelter-audiovisual-production |
| ca_ab_fttc | preapproval_mandatory, application_deadline | Film and Television Tax Credit (FTTC) — Program Guidelines; Film and Television Tax Credit Act and Regulation (amendments in force 2024-06-07) | https://www.alberta.ca/film-television-tax-credit |
| ca_bc_pstc | preapproval_mandatory, application_deadline | Production services tax credit — Province of British Columbia (official) | https://www2.gov.bc.ca/gov/content/taxes/income-taxes/corporate/credits/production-services |
| ca_federal_pstc | preapproval_mandatory, audit_or_final_certification_deadline | Film or Video Production Services Tax Credit | https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/film-video-production-services.html |
| ca_qc_pstc | preapproval_mandatory | Refundable Tax Credit for Film or Television Production Services — SODEC (fact sheet, March 2026) | https://sodec.gouv.qc.ca/english/credit-film-production-services/ |
| cl_corfo_incentive | preapproval_mandatory | Ministerios de las Culturas, de Economia y Corfo presentan segunda convocatoria del programa IFI Audiovisual 2025 | https://www.cultura.gob.cl/convocatorias/ministerios-de-las-culturas-de-economia-y-corfo-presentan-segunda-convocatoria-del-programa-ifi-audiovisual-2025/ |
| cz_film_incentive | preapproval_mandatory, expenditure_before_approval_qualifies, payment_timing | Production Incentives | https://sfa.gov.cz/production-incentives |
| dk_production_rebate | preapproval_mandatory, application_deadline | The Danish Production Incentive Scheme | https://slks.dk/english/work-areas/media/the-danish-production-incentive-scheme |
| ee_film_estonia_rebate | preapproval_mandatory | Film Estonia cash rebate — Guidelines and how to apply; Estonian Film Institute (Eesti Filmi Instituut) | https://filmestonia.eu/film-estonia-funding/guidelines-and-how-to-apply/ |
| fi_business_finland_incentive | preapproval_mandatory, payment_timing | Production incentive for the audiovisual industry — Business Finland | https://www.businessfinland.fi/en/services/funding/funding-services/Audiovisual-production-incentive |
| fj_film_rebate | preapproval_mandatory, expenditure_before_approval_qualifies, payment_timing | 20% Film Tax Rebate | https://film-fiji.com/incentives-and-legislation/20-film-tax-rebate/ |
| fr_trip | preapproval_mandatory, application_deadline | The Tax Rebate for International Productions (TRIP) | https://www.cnc.fr/web/en/tax-rebate/the-tax-rebate-for-international-productions-trip_190742 |
| gr_cash_rebate | preapproval_mandatory, application_deadline, payment_timing | 40% Cash Rebate | https://filmcommission.gr/cash-rebate/ |
| ie_section_481 | preapproval_mandatory, application_deadline | Film Relief (Section 481 Film Tax Credit) | https://www.revenue.ie/en/companies-and-charities/reliefs-and-exemptions/film-relief/index.aspx |
| il_foreign_production_fund | payment_timing | Information for Foreign Producers — Israel Cash Rebate (NFCT / Ministry of Economy & Industry) | https://nfct.org.il/en/information-for-foreign-producers/ |
| is_film_reimbursement_scheme | preapproval_mandatory, application_deadline | Iceland Film Incentives / How to Apply — Film in Iceland; Icelandic Film Centre reimbursement scheme | https://filminiceland.com/incentives |
| it_tax_credit_foreign | preapproval_mandatory, expenditure_before_approval_qualifies, application_deadline | Tax Credit — Introduzione | https://cinema.cultura.gov.it/cosa-facciamo/sostegni-economici/linee-di-sostegno/tax-credit/introduzione/ |
| lt_film_centre_cash_rebate | preapproval_mandatory | How it works — Lithuanian Film Tax Incentive | https://www.lkc.lt/en/tax-incentives/how-it-works |
| lu_filmfund_tax_shelter_rebate | preapproval_mandatory, application_deadline | Selective Financial Assistance (AFS/SFA) for production — Film Fund Luxembourg | https://filmfund.lu/en/funding/afs-p/ |
| ma_ccm_rebate | preapproval_mandatory, expenditure_before_approval_qualifies, application_deadline, audit_or_final_certification_deadline | CCM Foreign Production incentive — official programme page | https://www.ccm.ma/foreign_production/pe/index.html |
| mt_mfc_rebate | preapproval_mandatory, expenditure_before_approval_qualifies, application_deadline, audit_or_final_certification_deadline, payment_timing | Financial Incentives for the Audiovisual Industry: CASH REBATE GUIDELINES (Official Document, January 2019) | https://stargatestudios.com.mt/wp-content/uploads/2019/06/Financial-Incentives-for-Audiovisual-Industry-Guidelines-Official-Do....pdf |
| mu_edb_incentive | preapproval_mandatory | Film Rebate Scheme — Submission Procedures (Economic Development Board, 31 Jan 2020, citing the EDB (Film Rebate Scheme) Regulation 2018) | no URL retained; exact official title/authority retained |
| mx_federal_film_incentive_2026 | preapproval_mandatory, sunset_date | DECRETO por el que se otorga un estimulo fiscal a la produccion cinematografica y audiovisual (Diario Oficial de la Federacion, 16 February 2026) | https://www.dof.gob.mx/nota_detalle.php?codigo=5780237&fecha=16/02/2026 |
| nl_film_production_incentive | preapproval_mandatory | Netherlands Film Production Incentive — Netherlands Film Fund (Filmfonds) | https://www.filmfonds.nl/en/funding/fund/netherlands-film-production-incentive |
| no_film_incentive | preapproval_mandatory, application_deadline, audit_or_final_certification_deadline | The Norwegian Film Production Incentive — Norsk filminstitutt (NFI) | https://www.nfi.no/en/funding-schemes/insentiv/the-norwegian-film-production-incentive |
| nz_spg_international | preapproval_mandatory, application_deadline, audit_or_final_certification_deadline | New Zealand Screen Production Rebate for International Productions | https://www.nzfilm.co.nz/incentives-co-productions/nzspg-international |
| ph_fdcp_flip | preapproval_mandatory, expenditure_before_approval_qualifies, application_deadline, audit_or_final_certification_deadline | Film Location Incentive Program (FLIP) — official program page | https://fdcp.ph/programs/film-incentives/film-location-incentive-program |
| pt_scri_pt_cash_rebate | preapproval_mandatory, sunset_date | SCRI.PT — Sistema de Incentivos ao Cinema e Audiovisual (RIPAC); Cash Rebate — Portugal Film Commission / ICA | https://portugalfilmcommission.com/en/incentive-to-film-recording-and-production/ |
| ro_film_office_cash_rebate | preapproval_mandatory, sunset_date | Romanian cash rebate state aid scheme — Office for Film and Cultural Investments (OFIC) | https://app.ofic.ro/ |
| rs_film_commission_cash_rebate | preapproval_mandatory, payment_timing | Film Incentives — Film Center Serbia (FCS) / Film in Serbia | https://www.fcs.rs/en/industry-guide/film-incentives/ |
| sa_film_commission_rebate | preapproval_mandatory | Film Saudi Incentive Program — Saudi Film Commission (Ministry of Culture) | https://film.sa/incentive-programs/ |
| th_boi_incentive | preapproval_mandatory | Thailand Incentive Measures Guidelines (2025) — Thailand Film Office (TFO), Department of Tourism | https://tfo.dot.go.th/incentive-measures/ |
| uk_avec | preapproval_mandatory, audit_or_final_certification_deadline | CREC080200 - Claims: introduction | https://www.gov.uk/hmrc-internal-manuals/creative-industries-expenditure-credit-manual/crec080200 |
| us_ca_film_credit | preapproval_mandatory, sunset_date | California Film & Television Tax Credit Program 4.0 — CA Film Commission / FTB | https://film.ca.gov/tax-credit/ |
| us_il_film_production_services_credit | preapproval_mandatory | Illinois Film Production Services Tax Credit — Rules/Requirements & Fact Sheet (DCEO) | https://dceo.illinois.gov/whyillinois/film/filmtaxcredit/rulesandrequirements.html |
| us_ky_keiia | preapproval_mandatory, expenditure_before_approval_qualifies | Title 307 Chapter 1 Regulation 080 (307 KAR 1:080E) — Kentucky Entertainment Incentive Program | https://apps.legislature.ky.gov/law/kar/titles/307/001/080/ |
| us_la_film_incentive | preapproval_mandatory | Motion Picture Production Program — Louisiana Economic Development | https://www.opportunitylouisiana.gov/incentive/motion-picture-production-program |
| us_ma_film_tax_credit | preapproval_mandatory | Massachusetts Film Incentive Tax Credit — Mass.gov (Department of Revenue) and Massachusetts Film Office | https://www.mass.gov/info-details/massachusetts-film-incentive-tax-credit |
| us_md_film_production_activity_credit | preapproval_mandatory, expenditure_before_approval_qualifies, application_deadline, audit_or_final_certification_deadline | Film Production Activity Tax Credit — official program page | https://commerce.maryland.gov/fund/film-production-activity-tax-credit |
| us_mn_film_production_credit | preapproval_mandatory | Film Production Tax Credit — official program page | https://www.revenue.state.mn.us/film-production-credit |
| us_ms_advantage_film_program | preapproval_mandatory, application_deadline | Incentive — Film Mississippi | https://filmmississippi.org/incentive/ |
| us_nc_film_entertainment_grant | preapproval_mandatory | Film Industry Grants — North Carolina Department of Commerce; North Carolina Film Office | https://www.commerce.nc.gov/grants-incentives/film-industry-grants |
| us_or_opif | preapproval_mandatory, expenditure_before_approval_qualifies | Oregon Production Investment Fund (OPIF) | https://oregonfilm.org/article/oregon-production-investment-fund-opif/ |
| us_pa_film_production_credit | preapproval_mandatory | Film Production Tax Credit Guidelines — PA Department of Community & Economic Development (DCED) | https://dced.pa.gov/programs/film-tax-credit-program/ |
| us_pr_film_incentives_act | preapproval_mandatory, payment_timing | Film industry incentives under the Puerto Rico Incentives Code (Act 60-2019), which subsumed the former Film Industry Economic Incentives Act (Act 27-2011) — Puerto Rico Film Commission / DDEC | https://puertoricofilm.ddec.pr.gov/incentives/ |
| us_tx_miip | preapproval_mandatory, application_deadline | Texas Moving Image Industry Incentive Program (TMIIIP) — Production Incentives Overview | https://gov.texas.gov/film/page/incentives_overview |
| us_wa_motion_picture_competitiveness | preapproval_mandatory, application_deadline, audit_or_final_certification_deadline | Production Incentive Program (PIP) Guidelines & Criteria and Fact Sheet (rev. 2025-06-24) — Washington Filmworks; Chapter 43.365 RCW | https://www.washingtonfilmworks.org/wp-content/uploads/2025/06/2025.06.24_WF-Production-Incentive-Program-PIP_GC.pdf |
| za_dtic_foreign_film | preapproval_mandatory | Foreign Film and Television Production and Post-Production Incentive — Programme Guidelines | https://www.thedtic.gov.za/financial-and-non-financial-support/incentives/film-incentive/foreign-film-and-television-production-and-post-production-incentive-foreign-film/ |

Primary-current field count: `{"application_deadline": 18, "audit_or_final_certification_deadline": 10, "expenditure_before_approval_qualifies": 9, "payment_timing": 9, "preapproval_mandatory": 48, "sunset_date": 4}`.

The seven secondary leads are: at_fisa_plus, ch_pics_national_rebate, pl_pisf_cash_rebate, qa_screen_production_incentive, se_production_rebate, sg_made_with_singapore_rebate, tw_bamid_rebate. They remain acquisition leads only.

## Unresolved program-type recovery

The following candidates use exact canonical-ID, exact slug, or a unique exact full-name equality against a structured historical record. No type was inferred from words in a program name.

| Canonical ID | Historical type(s) | Status | Exact source/match |
| --- | --- | --- | --- |
| ar_incaa_incentive | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| au_nsw_screen | cash_rebate, rebate | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| au_qld_screen_qld | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| au_screen_production | direct_grant, equity | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| au_vic_vicscreen | cash_rebate, rebate | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| ba_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| bb_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| bc_interactive_digital_media_tax_credit_idmtc | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| br_ancine_incentive | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| bs_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| by_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| ca_cmf | direct_grant, equity | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| ca_federal_cptc | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| ca_nl_production_fund | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| cr_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| de_fff_bayern | direct_grant, loan | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| de_nrw_filmstiftung | direct_grant, loan | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| dk_film_incentive | direct_grant | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| ec_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| eu_media_fund | co_production_fund, grant | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| film_i_vast | advance, co_production_fund | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| fr_cnc_production | advance, direct_grant | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| gb_bfi_production | direct_grant, equity | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| gb_sct_screen_fund | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| gb_wls_screen_fund | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| gt_film_commission | grant, production_support | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| gy_film_commission | grant, production_support | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| in_national_film | direct_grant | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| in_nfdc_coproduction | co_production_fund | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| jm_film_incentive | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| mx_eficine_incentive | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| new_zealand_screen_production_grant_—_international_post_vfx | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| nl_hbf | development_fund, grant | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| nohfc_production_fund | discretionary_fund, grant | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| nordic_ftvf | co_production_fund, grant | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| on_ofttc | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| ontario_computer_animation_and_special_effects_tax_credit_ocase | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| pa_film_incentive | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| pe_film_incentive | direct_grant | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| pt_film_incentive | cash_rebate, rebate | CONFLICT_REQUIRES_TAXONOMY_ADJUDICATION | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| qc_film_production | tax_credit | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| tourism_ireland___fáilte_ireland_production_support | production_support | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id) |
| us_itvs_fund | development_fund | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| us_sundance_doc | development_fund | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |
| uy_xxi_incentive | cash_rebate | EXPLICIT_RECOVERY_CANDIDATE | GLOBAL_REMEDIATION_EXECUTABLE_DATA.json (exact canonical_id); app.data.global_inventory.ALL_PROGRAMS (unique exact normalized full program_name) |

The six model-only leads that must not close a type are: et_film_commission, mn_film_commission, om_film_commission, ug_film_commission, zm_film_commission, zw_film_commission.

Conflicts are primarily taxonomy-versus-financing-instrument differences. Examples include `au_screen_production` (direct grant vs equity), `ca_cmf` (direct grant vs equity), `de_fff_bayern`/`de_nrw_filmstiftung` (direct grant vs loan), `film_i_vast`/`fr_cnc_production` (fund/grant vs advance), and `gb_bfi_production` (direct grant vs equity). The source-linked identity type must be adjudicated; the uncited FundEconomics classification must not silently win.

## RateCondition survival

Canonical consolidation reads RateRules but does not explicitly interpret most `RateCondition.kind` propositions into the corresponding material dimension. The JSON lists every condition kind, every exact program, instance counts and confidence tiers. High-value kinds include cultural-test gates, minimum-spend percentages, production types, discretionary bands, narrower rate bases, sponsorship exclusions, ATL subcaps, alternative programs, graduated brackets, and sustainability/production-type uplifts.

The wiring must remain narrow: a `material_funding_risk_not_modeled` marker is not a statutory cap, and a `discretionary_band` marker does not prove the objective uplift criteria.

## Old evaluator answer

| Module | Evaluator class | Programs | Rule logic | Provenance | Canonical equivalent |
| --- | --- | --- | --- | --- | --- |
| app.calculators.qpe_calculator | ENGINE_MECHANIC_ONLY | none | sums caller-supplied QPE flags and calculates finance cost; contains no jurisdiction eligibility table | none | not applicable |
| app.calculators.evaluate_qualification_tests generic scorer | ENGINE_MECHANIC_ONLY | none | generic boolean/percentage/count scoring mechanics | none | not applicable |
| app.calculators.mediterranean_comparison | AUTHORITY_BEARING_RULE_LOGIC | mu_edb_incentive, mt_mfc_rebate, gr_cash_rebate, cy_film_rebate | hardcoded ATL/BTL/cast/travel/post/insurance/contingency routing and rate/timing assumptions | mixed profile notes, project assumptions and estimates; not safe authority | mostly superseded by RateRule/SpendRule/Requirements; stale conflicts remain and must not be wired |
| app.calculators.mauritius_economics | AUTHORITY_BEARING_RULE_LOGIC | mu_edb_incentive | 30% floor/40% discretionary ceiling conditions plus explicit project-assumption caveats | partly duplicates RateRule conditions; production-specific SPV/track-record/sponsorship facts are not authority evidence | rate band is in RateRules; project conditions must remain project-specific |
| app.calculators.evaluate_qualification_tests.UK_BFI_RULES_HARDCODED | AUTHORITY_BEARING_RULE_LOGIC | uk_avec | 15 hardcoded BFI cultural-test criteria, 18/31 threshold and C+D minimum | self-labelled hardcoded validation testbed; no official source/version in module | canonical has only a requires-test flag, not the criteria |
| app.calculators.cultural_test_rules | AUTHORITY_BEARING_RULE_LOGIC | fr_cnc_production, ie_section_481, eu_eurimages, ibermedia_programme, ca_federal_cptc, au_producer_offset, uk_avec | eight national/co-production cultural qualification rule sets | no per-set official citation/version in module | canonical generally has flags only; criteria are absent |
| app.data.cultural_qualification_model | AUTHORITY_BEARING_RULE_LOGIC | at_ofi_grants, au_producer_offset, ba_film_centre, ca_cmf, ca_federal_cptc, cz_czech_film_fund, de_dfff, dk_dfi_support, eu_eurimages, eu_media_fund, fi_ses_grants, film_i_vast, fr_cnc_production, gr_gnf_grants, hu_nfi_grants, ibermedia_programme, ie_section_481, nl_hbf, no_nfi_grants, nordic_ftvf, pl_pisf_grants, pt_ica_grants, se_goteborg_fund, uk_avec | role/nationality hard gates and weights for 24 programs | free-text notes without per-row official citation/version; many rows explicitly UNKNOWN | not represented as canonical cultural criteria or eligible-production gates |
| app.calculators.qualification_model Little Utopia constants | AUTHORITY_BEARING_RULE_LOGIC | mu_edb_incentive, mt_mfc_rebate, gr_cash_rebate, uk_avec, au_location_offset | project facts and territorial text used to build served qualification registers | mix of current typed registry derivation and Little Utopia-specific facts | general rules should already come from SpendRule/Doctrine; project facts are not canonical authority |
| legal_authority_acquisition, evidence_graph, conditional_programs and structure evaluators | ENGINE_MECHANIC_ONLY | none | acquisition workflow, evidence state, gating and arithmetic mechanics read caller/registry data | none | not applicable |

Six module/groups contain authority-bearing rule logic. None supplies a safe new canonical source by itself: Mediterranean logic is superseded/mixed, Mauritius economics is project-bound, and cultural criteria lack per-rule official source/version capture. Generic scorers, QPE arithmetic, evidence workflow and structure evaluators are mechanics only.

## Gemini/Codex location and survival

Codex findings persist in `CODEX_GLOBAL_INCENTIVE_VALIDATION.json` (285 records) and were normalized into `GLOBAL_CANONICAL_PROGRAM_DISPOSITION.json` and `GLOBAL_REMEDIATION_EXECUTABLE_DATA.json` (176 records; 155 retain source-document URLs). Gemini findings persist in `GEMINI_GLOBAL_INCENTIVE_VALIDATION.json` (415 records) and distributed summaries.

The canonical path reads none of those artifacts. Findings survive only when separately accepted into a typed runtime registry. The exact non-surviving delta established here is 45 source-linked unresolved program-type findings. In addition, 23 formulaic programs have exact source-linked remediation records; those records must be compared proposition-by-proposition because many facts already survive through RateRule, SpendRule, or DoctrineRecord and the artifacts cannot be imported wholesale.

## Handoff order

1. Finish Claude's in-progress primary/current ProgramRequirements adapter; prioritize the 98 timing values across 49 programs and preserve timing basis.
2. Adjudicate and bind the 45 explicit unresolved program types; resolve the listed taxonomy conflicts.
3. Add a narrow, confidence-preserving RateCondition-kind adapter.
4. Use jurisdiction profiles only for non-estimate, non-duplicated, adequately cited fields.
5. Do not wire FundEconomics, market-knowledge migrations, old Mediterranean assumptions, Gemini placeholders, Bridge responses, or project QPE flags as authority.

## Controls

- Production code changed: **NO**
- Authority data changed: **NO**
- External research performed: **NO**
- Broad tests run: **NO**
- Bridge response files read: **NO**
