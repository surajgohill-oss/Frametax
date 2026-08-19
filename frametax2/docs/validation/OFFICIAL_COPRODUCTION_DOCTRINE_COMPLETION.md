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
