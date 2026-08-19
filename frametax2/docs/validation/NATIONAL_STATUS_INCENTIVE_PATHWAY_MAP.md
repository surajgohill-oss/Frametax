# National Status / Incentive Pathway Map

**Generated:** 2026-08-19, updated (resume/finish continuation from `763e766`) · Task 7 — explicit FOREIGN/SERVICE vs NATIONAL/CULTURAL pathway modeling.

**32 jurisdictions** with a confirmed national/cultural status regime (up from 24 at the `763e766` checkpoint).

## Jurisdictions with genuinely SEPARATE foreign/service AND national pathways

### AU

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `au_location_offset` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `au_producer_offset` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** Producer Offset 40% (theatrical feature) / 30% (other formats) of QAPE, a genuinely SEPARATE program from Location Offset (spend-only, no content test) -- confirmed via screenaustralia.gov.au (primary).

**Official co-production relationship:** Confirmed via Screen Australia (primary): 'Official co-productions automatically satisfy the SAC test' -- an explicit, authority-stated relationship, encoded without completing the treaty universe.

### CA

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `ca_federal_pstc` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `ca_federal_cptc` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** CPTC (s.125.4) and PSTC (s.125.5) are two separate federal programs, not one program with an uplifted rate -- CPTC 25% of qualified Canadian labour vs PSTC 16%, confirmed via canada.ca (primary) and corroborated by hellodarwin.com/Saturation.io/truenorthtaxes.ca.

**Official co-production relationship:** A production made under an official Canadian co-production treaty is certified without separately passing the 10-point test (existing treaty_engine.py bilateral registry already carries Canada's real treaty partners) -- confirmed via CAVCO's own CPTC guidelines referencing co-production certificates as an alternate route.

### ES

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `es_tax_credit_foreign` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `(not yet a served record)` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** Confirmed via the official Spanish Ministry of Culture/ICAA page: Art. 36.1 (Spanish productions, requires BOTH a Spanish nationality certificate AND a separate cultural character certificate from ICAA) is a genuinely SEPARATE tax framework from Art. 36.2 (es_tax_credit_foreign, the confirmed no-cultural-test foreign-production rebate) -- same real relationship as Canada CPTC/PSTC and Australia Producer Offset/Location Offset.

### KR

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `kr_kofic_location_incentive` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `(not yet a served record)` | DOMESTIC_NATIONAL_PATHWAY | ENABLES_OFFICIAL_COPRODUCTION_ROUTE |

**Detail:** Korea bases film nationality on corporate registration plus creative/financial contribution for its OWN public-support schemes (distinct from kr_kofic_location_incentive, the confirmed no-personnel-cultural-test foreign-production rebate). KOFIC administers a real, separate Co-production Fund (koreanfilm.or.kr/eng/coProduction/coProdFund.jsp) for productions qualifying under Korea's own real co-production treaty framework.

**Official co-production relationship:** Confirmed via KOFIC's own official treaty list (koreanfilm.or.kr): real bilateral agreements with Canada, UK, Singapore, New Zealand, France (plus China/India/EU outside the current 49-country universe) -- see CoproductionCoverageStatus for KR.

### NL

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `nl_film_production_incentive` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `nl_hbf` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** Recovered from EXISTING internal data (cultural_qualification_model.py already carries real nl_hbf director/writer/producer NationalityRequirement rows -- Task 4 discipline, not re-researched this pass), distinct from nl_film_production_incentive's own confirmed no-cultural-test service pathway.

### NZ

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `nz_spg_international` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `(not yet a served record)` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** A 40% grant is available for New Zealand productions (vs the International rebate's 20% baseline) -- eligibility requires either significant NZ content (points-based test) OR official co-production status. Recovered from this same multi-pass arc's own prior research (nzfilm.co.nz, beehive.govt.nz), not re-researched.

**Official co-production relationship:** Confirmed via NZFC: official co-production status is an explicit ALTERNATIVE route to the points test for the 40% NZ-production grant.

### SE

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `se_production_rebate` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `se_goteborg_fund` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** Recovered from EXISTING internal data (cultural_qualification_model.py already carries real se_goteborg_fund director/writer/producer NationalityRequirement rows -- Task 4 discipline, not re-researched this pass), distinct from se_production_rebate's own confirmed no-cultural-test service pathway.

## Jurisdictions where the base incentive's own cultural test/gate IS the national pathway

| Jurisdiction | Program |
|---|---|
| AT | `at_fisa_plus` |
| BE | `be_tax_shelter` |
| CH | `ch_pics_national_rebate` |
| CY | `cy_film_rebate` |
| CZ | `cz_film_incentive` |
| DE | `de_dfff` |
| DK | `dk_production_rebate` |
| EE | `ee_film_estonia_rebate` |
| FI | `fi_business_finland_incentive` |
| FR | `fr_trip` |
| GB | `uk_avec` |
| GR | `gr_cash_rebate` |
| HR | `hr_cash_rebate` |
| HU | `hu_hipa_rebate` |
| IE | `ie_section_481` |
| IT | `it_tax_credit_foreign` |
| LT | `lt_film_centre_cash_rebate` |
| LU | `lu_filmfund_tax_shelter_rebate` |
| MT | `mt_mfc_rebate` |
| MY | `my_finas_rebate` |
| NO | `no_film_incentive` |
| PH | `None` |
| PL | `pl_pisf_cash_rebate` |
| PT | `pt_scri_pt_cash_rebate` |
| ZA | `za_dtic_foreign_film` |

STOP.
