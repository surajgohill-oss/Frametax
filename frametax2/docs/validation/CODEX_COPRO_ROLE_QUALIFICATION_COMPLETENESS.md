# Codex Co-production Role / Cultural Qualification Completeness Audit

Final gate: CODEX_COPRO_ROLE_QUALIFICATION_COMPLETENESS_LOCALIZED

Baseline: shared canonical branch HEAD 4c36b42. Read-only repository/data/authority-lineage audit; no external legal validation.

## Result

Current canonical creative-role optimization is not ready. Across 181 represented regimes, five program rule sets can identify exact gaps at rule-table level, but none reaches canonical served evaluation. The worldwide catalog contributes 129 cultural/co-production rows: 28 map into a structured record and 101 remain flag-only regimes with no dimension-level rules.

Audit universe: 35 bilateral + 3 multilateral + 143 deduplicated program regimes = 181. Ambiguous identities remain catalog IDs rather than being guessed into a slug.

## Direct answers

1. Writer is not a hard requirement in most represented regimes: 4 of 181.
2. Mandatory writer: 4 — ca_cmf, ca_federal_cptc, fr_cnc_production, uk-ca-bilateral.
3. Point-bearing only: 1 — uk_avec.
4. Explicitly not hard-required: 21 (10 optional, 10 N/A, 1 points-only). Another 156 are unknown, not presumed irrelevant.
5. Rule-level sufficient for exact gap suggestions: five (au_producer_offset, ca_federal_cptc, fr_cnc_production, ie_section_481, uk_avec); canonical served path: zero.
6. Complete-enough data simply not wired: 5. Partial existing data: 68.
7. Targeted authority completion required: 176 regimes (108 genuinely missing criteria; 68 partial).
8. Exact propositions are in JSON targeted_research_set and each regime's missing_propositions.
9. Before Script Analyzer, ingestion must collect verified people/entity, nationality/residency, contribution, ownership/control, actual work location and elected route.
10. Script Analyzer later supplies setting, character identity, themes, language, source-material provenance and scene-derived production/VFX scope only.

## Writer treatment

Mandatory: ca_cmf, ca_federal_cptc, fr_cnc_production, uk-ca-bilateral.

Point-bearing only: uk_avec.

Optional/alternative: ca-fr-bilateral, dk_dfi_support, european-convention-coproduction, fi_ses_grants, nl_hbf, no_nfi_grants, pl_pisf_grants, se_goteborg_fund, uk-de-bilateral, uk-fr-bilateral.

N/A in explicit rules: au_producer_offset, de_dfff, eu_eurimages, eu_media_fund, eurimages-multilateral, film_i_vast, ibermedia-multilateral, ibermedia_programme, ie_section_481, nordic_ftvf.

Unknown/not captured: 156; complete list in JSON writer_lists.unknown_not_captured.

## Role coverage counts

| Dimension | M / P / O / N/A / U |
|---|---|
| writer | M 4 / P 1 / O 10 / N/A 10 / U 156 |
| director | M 15 / P 3 / O 10 / N/A 0 / U 153 |
| producer | M 57 / P 3 / O 1 / N/A 0 / U 120 |
| cast | M 5 / P 3 / O 0 / N/A 0 / U 173 |
| composer | M 0 / P 3 / O 0 / N/A 0 / U 178 |
| editor | M 0 / P 2 / O 0 / N/A 0 / U 179 |
| key_creatives | M 37 / P 3 / O 0 / N/A 0 / U 141 |
| story_setting | M 2 / P 6 / O 0 / N/A 0 / U 173 |
| language | M 0 / P 1 / O 0 / N/A 0 / U 180 |
| shooting_location | M 2 / P 2 / O 0 / N/A 0 / U 177 |
| post_vfx | M 0 / P 2 / O 0 / N/A 0 / U 179 |
| ownership_control | M 45 / P 0 / O 0 / N/A 0 / U 136 |
| contribution_rules | M 41 / P 0 / O 0 / N/A 0 / U 140 |
| nationality_residency | M 56 / P 3 / O 0 / N/A 0 / U 122 |
| other | M 132 / P 2 / O 0 / N/A 0 / U 47 |

## Optimizer readiness

- Fully sufficient in canonical served state: 0.
- Exact curable creative-role gap capable in canonical served state: 0.
- User-fact dependent: 181.
- Script-Analyzer dependent under captured rules: 8.
- Rule-data incomplete: 176.
- Numeric-threshold-only disclosures: hr_cash_rebate, hu_hipa_rebate, it_tax_credit_foreign, lt_film_centre_cash_rebate, mt_mfc_rebate; none identifies an exact criterion lever.

## Canonical consumption

- Fully consumed: 0.
- Partially consumed: 32 (26 static bilateral, Eurimages blanket/membership gate, five numeric thresholds).
- Existing but disconnected: 149.

First disconnect: canonical_evaluation._opportunities_for_candidate sends only jurisdiction/program to discover_cultural_test_gap_opportunity. It never calls production_package_to_cultural_test_inputs, production_package_to_role_known_codes, evaluate_program_eligibility, deterministic scorers or generate_cultural_recommendations.

Treaty disconnect: the bilateral bridge receives no majority_pct, minority_pct or cultural_test_passed. Nine migration-0061 treaties are absent from treaty_engine; European Convention and Ibermedia have no canonical bridge; Eurimages is membership-only and unresolved.

Catalog disconnect: global_inventory provides flags/program types, not role rules. A flag cannot establish writer treatment, points, hard gates or a valid lever.

## True residual

- A — EXISTING DATA, NOT WIRED: 5 (au_producer_offset, ca_federal_cptc, fr_cnc_production, ie_section_481, uk_avec).
- B — EXISTING DATA, PARTIAL: 68.
- C — GENUINELY MISSING RULE DATA: 108.

Typical bilateral propositions: WRITER_STATUS_TREATMENT; KEY_CREATIVE_DEFINITION_AND_ALLOCATION; CREATIVE_CONTRIBUTION_PROPORTIONALITY_TEST; CONTRIBUTION_BASE_FINANCE_SPEND_OR_RIGHTS; OWNERSHIP_AND_CONTROL_ALLOCATION_TEST. Flag-only programs require applicability/certification route, full role table, story/language/activity criteria, ownership/contribution gates, complete points/weights/threshold.

## Script Analyzer contract delta

Project metadata facts needed now:

- Elected program/test/treaty and certification route.
- Applicant and each co-producer legal entity, registration, tax/legal residence, accreditation, and member-state status.
- Named writer, director, producer, composer, editor, cast, department heads and key creatives; role, attachment/confirmation status, nationality and legal residency kept separate.
- Cast-day and crew-day totals by qualifying nationality/residency where a test uses percentages.
- Per-country finance contribution, production-spend contribution, rights share, ownership/control, recoupment and territorial exploitation rights.
- Actual/planned principal-photography jurisdictions, shoot days and percentages; actual/planned post, VFX, animation, edit, sound and music work locations.
- Production type, total budget, local qualifying spend, co-producer count, majority/minority election and formal co-production approval status.
- Known cultural-certificate answers supplied by producer/counsel, with source and review status.

Script-derived facts needed later:

- Story setting and geographic/national locus.
- Lead-character identity where the official test scores character nationality/residency (not performer nationality).
- Subject matter, cultural themes, heritage, diversity, identity and artistic/cultural contribution.
- Original dialogue and production-language proportions.
- Underlying work/source-material and rights provenance where a test scores them.
- Scene-derived location, practical-effects, VFX, animation and post-production scope; not the eventual vendor or work location.

Proposed-structure facts, not Script Analyzer facts:

- Proposed attachment/substitution of a qualifying creative role.
- Proposed treaty partner, co-producer count and finance/spend/rights-share rebalance.
- Proposed entity, ownership, control or copyright allocation.
- Proposed relocation of shooting, post, VFX, animation, edit, sound or music.

The current contract misclassifies personnel nationality/residency as script-derived and conflates story setting with actual shooting and script-implied post/VFX scope with actual/proposed work location.

## Per-regime compact matrix

Legend: M mandatory; P point-bearing; O optional; N/A explicitly unused; U unknown. W writer, D director, Pr producer, C cast, Co composer, E editor, K key creatives, S story, L language, Sh shooting, PV post/VFX, Ow ownership, Ct contribution, Nr nationality, Oth other.

| Regime | W | D | Pr | C | Co | E | K | S | L | Sh | PV | Ow | Ct | Nr | Oth | Consumption | Residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| acpfilms_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ar_incaa_incentive | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| at_fisa_plus | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| at_ofi_grants | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| au-de-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| au-fr-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| au-ie-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| au-it-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| au-kr-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| au-nz-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| au_producer_offset | N/A | P | P | P | P | U | U | P | U | U | P | U | U | P | P | disconnected | EXISTING_DATA_NOT_WIRED |
| au_screen_production | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ba_film_centre | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| be_tax_shelter | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| br_ancine_incentive | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca-au-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-be-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-ch-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-cn-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-de-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-es-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-fr-bilateral | O | O | M | U | U | U | M | U | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-ie-bilateral | U | U | M | U | U | U | U | U | U | U | U | M | M | U | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-it-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-mx-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-nz-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca-za-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| ca_ab_fttc | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_cmf | M | M | U | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| ca_federal_cptc | M | M | M | M | P | P | P | U | U | U | U | U | U | M | P | disconnected | EXISTING_DATA_NOT_WIRED |
| ca_mb_film_video_credit | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_nb_film_tax_credit | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_nl_all_spend_credit | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_ns_production_incentive_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_on_ofttc | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_qc_film_production | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ca_sk_creative_saskatchewan_grant | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AM::national-cinema-centre-of-armenia-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AR::incaa-foprocine-development-and-production-grants | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AT::orf-film-fernseh-abkommen-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AU::australian-content-standard-streaming-service-investment-obligations | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AU::melbourne-international-film-festival-miff-premiere-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::AU::screen-australia-talent-and-business-development-programs | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::BF::fespaco-festival-pan-africain-du-cin-ma-et-de-la-t-l-vision-de-ouagadougou | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::BR::ancine-fsa-fundo-setorial-do-audiovisual-development-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CA::bell-fund-broadcast-and-digital-content-development | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CA::crtc-online-streaming-act-bill-c-11-local-content-obligations | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CA::nsi-national-screen-institute-drama-prize-and-development-programs | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CA::telefilm-canada-canada-feature-film-fund-cfff | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CA::telefilm-canada-export-development-program | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CH::bak-swiss-federal-office-of-culture-international-co-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CH::media-desk-switzerland-succ-s-cin-ma-automatic-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CH::swiss-federal-office-of-culture-foc-film-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::CN::china-film-administration-domestic-co-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE-BB::medienboard-berlin-brandenburg-mbb-film-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE-BW::mfg-medien-und-filmgesellschaft-baden-w-rttemberg | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE-HH::film-und-medienstiftung-hamburg-schleswig-holstein | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE-MDM::mitteldeutsche-medienf-rderung-mdm-film-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE::berlinale-world-cinema-fund-wcf-development-and-production-grants | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE::german-films-international-export-and-market-promotion | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE::wdr-ard-film-and-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DE::zdf-das-kleine-fernsehspiel-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DK-CPH::copenhagen-film-fund-regional-co-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::DK::dr-danish-broadcasting-corporation-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::ES-CAT::icec-institut-catal-de-les-empreses-culturals-film-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::ES-EUS::basque-audiovisual-eusko-jaurlaritza-film-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::ES-GAL::agadic-axencia-galega-das-industrias-culturais-film-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::ES::rtve-radio-televisi-n-espa-ola-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::EU::eu-avms-directive-local-content-investment-obligations-streamers | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::EU::torino-film-lab-international-development-and-production-grants | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FI::yle-finnish-broadcasting-company-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FR::arte-france-cin-ma-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FR::canal-obligation-de-contribution-la-production-fran-aise | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FR::chronologie-des-m-dias-svod-investment-obligation-france | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FR::cnc-cr-dit-d-imp-t-animation-et-jeux-vid-o | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::FR::unifrance-international-distribution-and-promotion-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB-LON::film-london-production-finance-market-and-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB-NIR::northern-ireland-screen-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB-YRK::screen-yorkshire-yorkshire-content-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB::bbc-films-co-production-and-development-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB::bfi-international-export-development-and-distribution-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB::channel-4-film-film4-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB::creative-england-production-finance-english-regions | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::GB::screenskills-production-training-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IE::rt-broadcasting-authority-of-ireland-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IE::screen-ireland-development-and-skills-programme | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IN::india-national-film-development-corporation-nfdc-and-state-incentives | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IR::farabi-cinema-foundation-film-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IT::anica-mic-italian-film-international-distribution-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::IT::rai-cinema-co-production-and-acquisition-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::JP::vipo-visual-industry-promotion-organization-animation-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::KR::kocca-korea-creative-content-agency-animation-and-vfx-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::KR::kofic-international-co-production-and-export-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::LB::centre-du-cin-ma-libanais-ccl-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::MA::centre-cin-matographique-marocain-ccm-avance-sur-recettes | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::MX::imcine-instituto-mexicano-de-cinematograf-a-foprocine-fidecine | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::MX::mexico-eficine-article-226-tax-credit-and-procine-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::NL::npo-vpro-dutch-public-broadcaster-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::NO-ROG::vestnorsk-filmsenter-western-norway-regional-film-centre | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::NO-TRO::nord-norsk-filmsenter-northern-norway-regional-film-centre | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::NO::nrk-norwegian-broadcasting-corporation-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::PE::peru-dafo-film-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::PT::ica-instituto-do-cinema-e-audiovisual-international-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::PT::ica-instituto-do-cinema-e-audiovisual-selective-production-grants | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::PT::portugal-film-commission-incentive-iapmei | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::SA-KSA::saudi-film-commission-production-grants-and-selective-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::SE-AB::filmregion-stockholm-m-lardalen-regional-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::SE-SK::film-i-sk-ne-regional-co-production-fund-scania | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::SE::svt-swedish-television-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::SG::imda-digital-media-content-programme-animation-vfx | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::TR::ministry-of-culture-and-tourism-k-lt-r-film-production-grants | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::TR::turkey-cinema-general-directorate-film-production-support | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::TW::taiwan-creative-content-agency-taicca-international-co-production-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| catalog::ZA::department-of-arts-and-culture-dac-nfvf-development-fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| ch_pics_national_rebate | U | U | M | U | U | U | U | U | U | M | U | M | M | U | U | disconnected | EXISTING_DATA_PARTIAL |
| cy_film_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| cz_czech_film_fund | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| cz_film_incentive | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| de-at-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| de-cz-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| de-hu-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| de-pl-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| de_dfff | N/A | P | P | U | U | U | U | U | U | U | U | U | U | P | U | disconnected | EXISTING_DATA_PARTIAL |
| de_fff_bayern | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| de_nrw_filmstiftung | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| dk_dfi_support | O | O | U | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| dk_production_rebate | U | U | U | P | U | U | P | U | U | P | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| es_tax_credit_foreign | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| eu_eurimages | N/A | U | M | U | U | U | U | U | U | U | U | M | M | M | M | disconnected | EXISTING_DATA_PARTIAL |
| eu_media_fund | N/A | O | U | U | U | U | U | U | U | U | U | M | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| eurimages-multilateral | N/A | M | M | M | U | U | M | M | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| european-convention-coproduction | O | M | M | U | U | U | M | U | U | U | U | M | M | M | M | disconnected | EXISTING_DATA_PARTIAL |
| fi_business_finland_incentive | U | U | M | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| fi_ses_grants | O | O | U | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| film_i_vast | N/A | U | M | U | U | U | U | U | U | U | U | M | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| fr-be-bilateral | U | U | M | U | U | U | U | U | U | U | U | M | M | U | M | partially_consumed | EXISTING_DATA_PARTIAL |
| fr-de-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| fr_cnc_production | M | M | M | U | U | U | U | P | U | U | U | U | U | M | M | disconnected | EXISTING_DATA_NOT_WIRED |
| fr_trip | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| gb_bfi_production | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| gb_sct_screen_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| gb_wls_screen_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| gr_gnf_grants | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| hk_film_dev_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| hr_cash_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | partially_consumed | GENUINELY_MISSING_RULE_DATA |
| hu_hipa_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | partially_consumed | GENUINELY_MISSING_RULE_DATA |
| hu_nfi_grants | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| ibermedia-multilateral | N/A | M | M | M | U | U | M | M | U | U | U | M | M | M | M | disconnected | EXISTING_DATA_PARTIAL |
| ibermedia_programme | N/A | U | M | U | U | U | U | U | U | U | U | M | M | M | M | disconnected | EXISTING_DATA_PARTIAL |
| ie_section_481 | N/A | O | O | U | U | U | U | U | U | U | U | M | U | M | M | disconnected | EXISTING_DATA_NOT_WIRED |
| in_nfdc_coproduction | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| it_tax_credit_foreign | U | U | U | U | U | U | M | U | U | U | U | U | U | U | M | partially_consumed | EXISTING_DATA_PARTIAL |
| kr-de-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| kr-fr-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| lt_film_centre_cash_rebate | U | U | M | U | U | U | M | P | U | M | U | U | U | U | M | partially_consumed | EXISTING_DATA_PARTIAL |
| lu_filmfund_tax_shelter_rebate | U | U | U | U | U | U | U | P | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| mt_mfc_rebate | U | U | M | U | U | U | U | P | U | U | U | U | U | U | M | partially_consumed | EXISTING_DATA_PARTIAL |
| my_finas_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| nl_film_production_incentive | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| nl_hbf | O | O | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| no_film_incentive | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| no_nfi_grants | O | O | U | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| nordic_ftvf | N/A | M | M | U | U | U | U | U | U | U | U | M | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| pl_pisf_cash_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| pl_pisf_grants | O | O | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| pt_ica_grants | U | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| pt_scri_pt_cash_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | EXISTING_DATA_PARTIAL |
| qa_dfi_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| se_goteborg_fund | O | M | M | U | U | U | U | U | U | U | U | U | U | M | U | disconnected | EXISTING_DATA_PARTIAL |
| se_production_rebate | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| sg_imda_film_fund | U | U | U | U | U | U | U | U | U | U | U | U | U | U | M | disconnected | GENUINELY_MISSING_RULE_DATA |
| uk-au-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-ca-bilateral | M | M | M | M | U | U | M | U | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-de-bilateral | O | O | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-fr-bilateral | O | O | M | M | U | U | M | U | U | U | U | M | M | M | M | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-ie-bilateral | U | U | M | U | U | U | U | U | U | U | U | M | M | U | U | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-in-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-it-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | disconnected | EXISTING_DATA_PARTIAL |
| uk-nz-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| uk-za-bilateral | U | U | M | U | U | U | M | U | U | U | U | M | M | M | U | partially_consumed | EXISTING_DATA_PARTIAL |
| uk_avec | P | P | P | P | P | P | P | P | P | P | P | U | U | P | M | disconnected | EXISTING_DATA_NOT_WIRED |

## Source inventory

- global_inventory.ALL_PROGRAMS: 303 rows; all 129 cultural/co-production flags included.
- migrations 0048/0049/0061: 35 bilateral and 3 multilateral records.
- treaty_engine: 26 bilateral + 3 multilateral evaluators; no creative-role schema.
- canonical_treaty_bridge: canonical adapters for bilateral and Eurimages only.
- cultural_qualification_model: 24 role/nationality profiles and hard-gate evaluator.
- cultural_test_rules/evaluate_qualification_tests: eight deterministic tests/checklists.
- program_requirements: 71 profiles; 19 cultural flags, one official-co-production gate, five numeric thresholds.
- production_package_intelligence/production_recommendation_engine: role adapters and recommendations outside canonical evaluation.
- canonical_opportunity_bridge/canonical_evaluation: actual canonical served consumer.
- screen_analyzer_fact_contract: deferred contract with the classification defects above.

Production code changed: NO
Canonical data changed: NO
External research: NO
