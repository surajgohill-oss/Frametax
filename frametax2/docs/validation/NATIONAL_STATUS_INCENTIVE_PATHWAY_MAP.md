# National Status / Incentive Pathway Map

**Generated:** 2026-08-19 · Task 7 — explicit FOREIGN/SERVICE vs NATIONAL/CULTURAL pathway modeling. Never merged into one card; the optimizer can eventually compare them.

**24 jurisdictions** with a confirmed national/cultural status regime.

## Jurisdictions with genuinely SEPARATE foreign/service AND national pathways (real, cited)

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
| National/Cultural | `ca_federal_cptc` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_ENHANCED_RATE |

**Detail:** CPTC 25% of qualified Canadian labour vs PSTC 16% -- a real, quantified ~9pp rate difference, confirmed via canada.ca (primary) and corroborated by hellodarwin.com/Saturation.io/truenorthtaxes.ca.

**Official co-production relationship:** A production made under an official Canadian co-production treaty is certified without separately passing the 10-point test (existing treaty_engine.py bilateral registry already carries Canada's real treaty partners) -- confirmed via CAVCO's own CPTC guidelines referencing co-production certificates as an alternate route.

### NZ

| | Program | Pathway type | Economic consequence |
|---|---|---|---|
| Foreign/Service | `nz_spg_international` | FOREIGN_SERVICE_PATHWAY | (no cultural status required) |
| National/Cultural | `(not yet a served record)` | DOMESTIC_NATIONAL_PATHWAY | UNLOCKS_SEPARATE_INCENTIVE |

**Detail:** A 40% grant is available for New Zealand productions (vs the International rebate's 20% baseline) -- eligibility requires either significant NZ content (points-based test) OR official co-production status. Recovered from this same multi-pass arc's own prior research (nzfilm.co.nz, beehive.govt.nz), not re-researched.

**Official co-production relationship:** Confirmed via NZFC: official co-production status is an explicit ALTERNATIVE route to the points test for the 40% NZ-production grant.

## Jurisdictions where the base incentive's own cultural test IS the national pathway (no separate program)

| Jurisdiction | Program |
|---|---|
| AT | `at_fisa_plus` |
| BE | `be_tax_shelter` |
| CY | `cy_film_rebate` |
| CZ | `cz_film_incentive` |
| DE | `de_dfff` |
| DK | `dk_production_rebate` |
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
| PL | `pl_pisf_cash_rebate` |
| PT | `pt_scri_pt_cash_rebate` |

STOP.
