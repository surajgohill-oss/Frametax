# Official Co-production Doctrine Completion

**Generated:** 2026-08-19

## Forensic finding (Task 1/4 — recover before research)

treaty_engine.py already carries a real, substantial, pre-existing bilateral/multilateral treaty registry (26 bilateral treaties + 3 multilateral frameworks, mirroring migrations 0047-0049) -- this was NOT rebuilt or newly researched from scratch this pass. Prior passes' closeout artifacts incorrectly implied zero official co-production doctrine existed; this was a recovery-before-research failure now corrected (Task 1/4 discipline).

## Summary

| Metric | Count |
|---|---:|
| Bilateral routes | 26 |
| Multilateral frameworks | 3 |
| Countries in current universe | 49 |
| Countries with ANY treaty coverage | 35 |
| Countries with NO treaty coverage | 14 |
| **Fabricated routes** | **0** |

**Countries with no treaty coverage in the current registry:** AE, FJ, IL, JP, MA, MU, MY, PH, QA, SA, SG, TH, TW, US. Independently corroborated this pass for the US (no official co-production treaties with any country in our universe — confirmed via 2 sources); the rest are simply not yet represented in `treaty_engine.py`'s registry, not confirmed-absent.

## Bilateral routes (26)

| Route | Parties | Cultural test | Majority unlocks | Minority unlocks |
|---|---|---|---|---|
| `uk-ca-bilateral` | GB↔CA | False | uk_avec | ca_federal_cptc, ca_cmf |
| `uk-au-bilateral` | GB↔AU | False | uk_avec | au_producer_offset |
| `uk-fr-bilateral` | GB↔FR | True | uk_avec | fr_tax_credit_cinema, fr_cnc_production |
| `uk-de-bilateral` | GB↔DE | False | uk_avec | de_dfff |
| `uk-nz-bilateral` | GB↔NZ | False | uk_avec | nz_spgi |
| `uk-za-bilateral` | GB↔ZA | False | uk_avec | — |
| `uk-in-bilateral` | GB↔IN | False | uk_avec | — |
| `uk-ie-bilateral` | GB↔IE | False | uk_avec | ie_section_481 |
| `ca-fr-bilateral` | CA↔FR | False | ca_federal_cptc, ca_cmf | fr_tax_credit_cinema, fr_cnc_production |
| `ca-au-bilateral` | CA↔AU | False | ca_federal_cptc, ca_cmf | au_producer_offset |
| `ca-de-bilateral` | CA↔DE | False | ca_federal_cptc, ca_cmf | de_dfff |
| `ca-it-bilateral` | CA↔IT | False | ca_federal_cptc, ca_cmf | it_tax_credit_foreign |
| `ca-es-bilateral` | CA↔ES | False | ca_federal_cptc, ca_cmf | — |
| `ca-za-bilateral` | CA↔ZA | False | ca_federal_cptc, ca_cmf | — |
| `ca-ie-bilateral` | CA↔IE | False | ca_federal_cptc, ca_cmf | ie_section_481 |
| `ca-nz-bilateral` | CA↔NZ | False | ca_federal_cptc, ca_cmf | nz_spgi |
| `ca-cn-bilateral` | CA↔CN | False | ca_federal_cptc, ca_cmf | — |
| `ca-ch-bilateral` | CA↔CH | False | ca_federal_cptc, ca_cmf | — |
| `ca-be-bilateral` | CA↔BE | False | ca_federal_cptc, ca_cmf | be_tax_shelter |
| `ca-mx-bilateral` | CA↔MX | False | ca_federal_cptc, ca_cmf | — |
| `au-de-bilateral` | AU↔DE | False | au_producer_offset | de_dfff |
| `au-ie-bilateral` | AU↔IE | False | au_producer_offset | ie_section_481 |
| `au-it-bilateral` | AU↔IT | False | au_producer_offset | it_tax_credit_foreign |
| `au-kr-bilateral` | AU↔KR | False | au_producer_offset | — |
| `fr-de-bilateral` | FR↔DE | True | fr_tax_credit_cinema, fr_cnc_production | de_dfff |
| `fr-be-bilateral` | FR↔BE | True | fr_tax_credit_cinema, fr_cnc_production | be_tax_shelter |

## Multilateral frameworks (3)

### eurimages-multilateral

- **Type:** eurimages
- **Total members:** 44 — in current universe: 28 (AT, BE, CH, CY, CZ, DE, DK, EE, ES, FI, FR, GB, GR, HR, HU, IE, IS, IT, LT, LU, MT, NL, NO, PL, PT, RO, RS, SE)
- **Majority/minority min %:** 10.0 / 10.0
- **Min co-producer countries:** 3
- **Cultural test required:** True
- **Fund unlocks:** eu_eurimages
- **Notes:** Each co-producer independently accesses national incentives on their own spend.

### european-convention-coproduction

- **Type:** european_convention
- **Total members:** 44 — in current universe: 28 (AT, BE, CH, CY, CZ, DE, DK, EE, ES, FI, FR, GB, GR, HR, HU, IE, IS, IT, LT, LU, MT, NL, NO, PL, PT, RO, RS, SE)
- **Majority/minority min %:** 30.0 / 10.0
- **Min co-producer countries:** 2
- **Cultural test required:** True
- **Fund unlocks:** none
- **Notes:** Framework providing European certification enabling national incentive access.

### ibermedia-multilateral

- **Type:** ibermedia
- **Total members:** 21 — in current universe: 4 (CL, ES, MX, PT)
- **Majority/minority min %:** 20.0 / 10.0
- **Min co-producer countries:** 2
- **Cultural test required:** True
- **Fund unlocks:** ibermedia_programme

## Task 8 — CO-PRO → NATIONAL STATUS → PROGRAM cross-reference (real, empirically confirmed)

Independently built registries (`treaty_engine.py`'s real unlocked-slugs data and this pass's `national_cultural_status.py`) agree with each other for every route where a cross-reference was possible:

- `uk-ca-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-ca-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `uk-au-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-au-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `uk-fr-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-de-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-de-bilateral`: DE: treaty unlock 'de_dfff' matches national_cultural_status.py's own confirmed national pathway.
- `uk-nz-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-za-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-in-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-ie-bilateral`: GB: treaty unlock 'uk_avec' matches national_cultural_status.py's own confirmed national pathway.
- `uk-ie-bilateral`: IE: treaty unlock 'ie_section_481' matches national_cultural_status.py's own confirmed national pathway.
- `ca-fr-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-au-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-au-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `ca-de-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-de-bilateral`: DE: treaty unlock 'de_dfff' matches national_cultural_status.py's own confirmed national pathway.
- `ca-it-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-it-bilateral`: IT: treaty unlock 'it_tax_credit_foreign' matches national_cultural_status.py's own confirmed national pathway.
- `ca-es-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-za-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-ie-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-ie-bilateral`: IE: treaty unlock 'ie_section_481' matches national_cultural_status.py's own confirmed national pathway.
- `ca-nz-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-cn-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-ch-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-be-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `ca-be-bilateral`: BE: treaty unlock 'be_tax_shelter' matches national_cultural_status.py's own confirmed national pathway.
- `ca-mx-bilateral`: CA: treaty unlock 'ca_federal_cptc' matches national_cultural_status.py's own confirmed national pathway.
- `au-de-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `au-de-bilateral`: DE: treaty unlock 'de_dfff' matches national_cultural_status.py's own confirmed national pathway.
- `au-ie-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `au-ie-bilateral`: IE: treaty unlock 'ie_section_481' matches national_cultural_status.py's own confirmed national pathway.
- `au-it-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `au-it-bilateral`: IT: treaty unlock 'it_tax_credit_foreign' matches national_cultural_status.py's own confirmed national pathway.
- `au-kr-bilateral`: AU: treaty unlock 'au_producer_offset' matches national_cultural_status.py's own confirmed national pathway.
- `fr-de-bilateral`: DE: treaty unlock 'de_dfff' matches national_cultural_status.py's own confirmed national pathway.
- `fr-be-bilateral`: BE: treaty unlock 'be_tax_shelter' matches national_cultural_status.py's own confirmed national pathway.

## Program identities referenced by treaties but outside the current 71-program served universe (8)

`au_producer_offset`, `ca_cmf`, `ca_federal_cptc`, `eu_eurimages`, `fr_cnc_production`, `fr_tax_credit_cinema`, `ibermedia_programme`, `nz_spgi`

Consistent with the prior passes' own finding (these are the same real programs from `cultural_qualification_model.py`'s 24-slug registry, not yet in `program_requirements.py`). One naming inconsistency found and disclosed (not silently fixed, to avoid touching `treaty_engine.py`'s own tested internals): `nz_spgi` does not match `nz_spg_international` (the real, canonical NZ program slug) or the real NZ national-content grant — likely intended to reference the NZ national pathway this pass's `national_cultural_status.py` confirms exists but does not yet have its own `program_requirements.py` record.

STOP.

## Queue C — per-country coverage resolution (continuation from checkpoint `adc5cba`, 2026-08-19)

Distinct denominator from the route-level table above: per-COUNTRY coverage across the 49-country universe.

| Metric | adc5cba | This continuation |
|---|---:|---:|
| total_countries | 49 | 49 |
| countries_with_bilateral_coverage | 20 | 21 |
| countries_with_multilateral_coverage | 30 | 30 |
| countries_with_both | 9 | 9 |
| confirmed_no_official_route | 2 | 2 |
| genuine_authority_residual | 6 | 5 |
| unexplained | 0 | 0 |

### Newly resolved this continuation

- **TW** (OFFICIAL_COPRO_ROUTE_EXISTS): NZ. A REAL, RATIFIED bilateral economic treaty — the Agreement between New Zealand and the Separate Customs Territory of Taiwan, Penghu, Kinmen and Matsu on Economic Cooperation (ANZTEC), in force 1 December 2013 — contains a dedicated Chapter 18 (Film and Television Co-Production). The Implementing Arrangement to Chapter 18 was read in full: competent authorities are the New Zealand Film Commission (NZFC) and Taiwan's Bureau of Audiovisual and Music Industry Development (BAMID); a two-stage approval process; a required co-producer contract covering IP, cost liability, receipts division, contribution-completion dates, and festival-nationality designation. Materially stronger than the earlier-confirmed France relationship (an MOU) — this is a real, signed, in-force international agreement with a dedicated co-production chapter.

### Queue D — per-route operational-term disclosure (new `partner_contribution_terms` field, additive, `CoproductionCoverageStatus`)

Per the explicit instruction that a confirmed route must never be silently treated as though it doesn't exist merely because one contribution-percentage term is unknown: every route below is `ROUTE_EXISTS`; where the exact term was found it is recorded as a real fact, where it was not it fails closed with an explicit `TERM_UNRESOLVED` marker rather than silent omission.

| Route | Term found this pass |
|---|---|
| KR ↔ CA | **Minimum participation 30% bipartite / 20% multipartite** (Telefilm Canada's official treaty summary; treaty signed 25 April 1995). Maximum not stated. |
| KR ↔ GB | TERM_UNRESOLVED — existence confirmed (Korea-UK FTA Cultural Cooperation Protocol), contribution % not independently retrieved. |
| KR ↔ SG | TERM_UNRESOLVED — existence confirmed (Korea-Singapore FTA), contribution % not independently retrieved. |
| KR ↔ NZ | TERM_UNRESOLVED — existence confirmed (2 agreements), contribution % not independently retrieved. |
| KR ↔ FR | TERM_UNRESOLVED — existence confirmed (2006 agreement), contribution % not independently retrieved. |
| JP ↔ IT | TERM_UNRESOLVED — existence confirmed (signed June 2024, activated August 2024, MOFA-corroborated), contribution % not independently retrieved. |
| PH ↔ FR | TERM_UNRESOLVED — existence confirmed (officially signed, FDCP/news-corroborated), contribution % not independently retrieved. |
| TW ↔ NZ | TERM_UNRESOLVED — route confirmed via the real ANZTEC treaty text (see above); the exact contribution percentage (ANZTEC's own Chapter 18, Article 4) was not located as a separately fetchable document this pass. |

None of these 8 routes were added to `treaty_engine.py`'s own `_BILATERAL` dict this pass (same disclosed connection gap as `adc5cba` — that schema requires numeric percentage fields this pass could not fully verify for most routes, and fabricating them would violate this arc's anti-fabrication discipline). They ARE fully represented, term-by-term, in the new `CoproductionCoverageStatus.partner_contribution_terms` field.

### Newly resolved this continuation (7 of the original 13 uncovered countries)

- **IL** (OFFICIAL_COPRO_ROUTE_EXISTS): FR, DE, IT, GB, AU, NZ, SE. Israel Film Fund's own page confirms 'over 20 co-production treaties, mostly with European countries' (primary-adjacent). Cross-corroborated via Australia's own listed treaty partners (includes Israel) and the UK's own listed treaty partners (includes Israel); France treaty independently dated to 1970. Exact full partner list beyond these 7 real, cited countries not independently enumerated this pass.
- **JP** (OFFICIAL_COPRO_ROUTE_EXISTS): IT. Japan-Italy Film Co-production Treaty, signed June 2024, activated August 2024 -- Japan's second bilateral film treaty (after China, not in the current 49-country universe). Corroborated by Japan's own Ministry of Foreign Affairs (MOFA) page.
- **KR** (OFFICIAL_COPRO_ROUTE_EXISTS): CA, GB, SG, NZ, FR. Official KoBiz/KOFIC treaty list (primary): Canada (Agreement on Cooperation in Audiovisual Coproduction), UK (Korea-UK FTA Cultural Cooperation Protocol), Singapore (Korea-Singapore FTA), New Zealand (2 agreements), France (2006) -- 5 real partners in the current 49-country universe (also lists China/India/EU, not individually in this universe). NOT yet added to treaty_engine.py's own _BILATERAL registry as new entries this pass (a real, disclosed connection gap -- see FINAL closeout) to avoid touching that module's own tested internals without full bilateral-term verification.
- **MA** (OFFICIAL_COPRO_ROUTE_EXISTS): GB. UK's own listed treaty partners include Morocco -- confirmed via secondary aggregation of UK's real treaty list, not Morocco's own CCM (Centre Cinematographique Marocain) site directly.
- **MY** (OFFICIAL_COPRO_ROUTE_EXISTS): AU. Australia's own listed treaty partners include Malaysia; corroborated by a real 2021 Malaysia-Australia film collaboration news report.
- **PH** (OFFICIAL_COPRO_ROUTE_EXISTS): FR. FDCP-France film co-production treaty, officially signed (Philippine news reporting of the signing) -- see also the matching national_cultural_status.py PH record.
- **SG** (OFFICIAL_COPRO_ROUTE_EXISTS): KR. Korea-Singapore FTA cultural-cooperation provisions, confirmed via KOFIC's own official treaty list.
- **TH** (NO_RELEVANT_OFFICIAL_COPRO_ROUTE_CONFIRMED): (none -- confirmed no route). Film Thailand (Thailand's own official film office) directly states Thailand has not entered into any formal co-production treaties, and is currently EVALUATING the possibility -- a genuine, current, primary-sourced confirmed-absent finding, not merely 'not found'.
- **US** (NO_RELEVANT_OFFICIAL_COPRO_ROUTE_CONFIRMED): (none -- confirmed no route). Confirmed (prior continuation, this same arc): the US has negotiated fewer co-production treaties than any other industrialized country and has none with Canada or Mexico; its only treaty (China) is not broad and is not in the current 49-country universe. A genuine, real, primary-adjacent confirmed-absent finding for the countries in our universe, not merely 'not found'.

### Genuine authority residual (5), hard-blocker documented

- **AE**: AE_OFFICIAL_COPRODUCTION_COVERAGE_UNCONFIRMED -- continuation pass performed real further research: the UAE's own MOF International Treaties Dashboard covers only DTAAs/BITs (no film category exists there), UNESCO's Policy Monitoring Platform did not surface UAE, and the one concrete UAE international film arrangement (Abu Dhabi Film Commission / Israel Film Fund, 2020) was confirmed via direct quote to be a goodwill/cultural-exchange cooperation agreement, NOT a formal treaty. Requires: UAE Ministry of Culture's own treaty register, not located in English.
- **FJ**: FJ_OFFICIAL_COPRODUCTION_COVERAGE_UNCONFIRMED -- no bilateral or multilateral route found in treaty_engine.py's existing registry, and no primary/secondary research was performed for this country this pass.
- **MU**: MU_COPRODUCTION_TREATY_CURRENT_STATUS_UNCONFIRMED -- last concrete evidence found is from 2013 (planned, not signed); EDB Mauritius's own 'Bilateral Agreements' page (edbmauritius.org/bilateral-agreements) was found in search results but not independently fetched for content this pass.
- **QA**: QA_OFFICIAL_COPRODUCTION_COVERAGE_UNCONFIRMED -- no bilateral or multilateral route found in treaty_engine.py's existing registry, and no primary/secondary research was performed for this country this pass.
- **SA**: SA_OFFICIAL_COPRODUCTION_COVERAGE_UNCONFIRMED -- no bilateral or multilateral route found in treaty_engine.py's existing registry, and no primary/secondary research was performed for this country this pass.

**TW resolved this continuation** (see above — ANZTEC Chapter 18 with New Zealand).

STOP.
