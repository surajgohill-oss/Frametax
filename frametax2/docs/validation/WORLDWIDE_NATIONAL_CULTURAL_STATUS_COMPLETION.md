# Worldwide National/Cultural Status Completion

**Generated:** 2026-08-19 · **Population:** unique ISO2 country codes derived from the current canonical 71-program economic database (sub-national jurisdictions collapsed to their federal country — national/cultural content status is a country-level government concept).

## Ontology correction (Task 1/2)

The prior pass's `cultural_test_required=False` field (48/71 programs) answers ONE question: does THIS PARTICULAR base incentive require a cultural test? It does NOT answer: does this jurisdiction have ANY national/cultural status regime at all? This pass adds that second, jurisdiction-level question as a distinct record (`app/data/national_cultural_status.py`), never conflating the two.

## Terminal accounting

| State | Count |
|---|---:|
| NATIONAL_STATUS_REGIME_CONFIRMED | 24 |
| NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED | 1 |
| AUTHORITY_UNRESOLVED_EXACT_PROPOSITION | 24 |
| **Unexplained** | **0** |

**Total: 49. Zero unexplained unknown.**

## NATIONAL_STATUS_REGIME_CONFIRMED via a SEPARATE pathway (new this pass, real primary/secondary research)

### AU — Significant Australian Content (SAC) test

- **Administering authority:** Screen Australia
- **Legal basis:** Income Tax Assessment Act 1997 (Cth), Producer Offset provisions
- **Foreign/service pathway (already canonical):** `au_location_offset`
- **National pathway:** `au_producer_offset`
- **Economic consequence:** UNLOCKS_SEPARATE_INCENTIVE — Producer Offset 40% (theatrical feature) / 30% (other formats) of QAPE, a genuinely SEPARATE program from Location Offset (spend-only, no content test) -- confirmed via screenaustralia.gov.au (primary).
- **Official co-production relationship:** Confirmed via Screen Australia (primary): 'Official co-productions automatically satisfy the SAC test' -- an explicit, authority-stated relationship, encoded without completing the treaty universe.
- **Sources:** https://www.screenaustralia.gov.au/producer-offset/, https://www.screenaustralia.gov.au/funding-and-support/producer-offset/guidelines/eligibility/significant-australian-content, https://www.ausfilm.com.au/incentives/the-producer-offset-and-co-production-treaties/

### CA — Canadian Content Certification (CAVCO 10-point scale)

- **Administering authority:** Canadian Audio-Visual Certification Office (CAVCO) / Canada Revenue Agency
- **Legal basis:** Income Tax Act (Canada) s. 125.4 (CPTC)
- **Foreign/service pathway (already canonical):** `ca_federal_pstc`
- **National pathway:** `ca_federal_cptc`
- **Economic consequence:** UNLOCKS_ENHANCED_RATE — CPTC 25% of qualified Canadian labour vs PSTC 16% -- a real, quantified ~9pp rate difference, confirmed via canada.ca (primary) and corroborated by hellodarwin.com/Saturation.io/truenorthtaxes.ca.
- **Official co-production relationship:** A production made under an official Canadian co-production treaty is certified without separately passing the 10-point test (existing treaty_engine.py bilateral registry already carries Canada's real treaty partners) -- confirmed via CAVCO's own CPTC guidelines referencing co-production certificates as an alternate route.
- **Sources:** https://www.canada.ca/en/canadian-heritage/services/funding/cavco-tax-credits/canadian-film-video-production.html, https://hellodarwin.com/business-aid/programs/canadian-film-or-video-production-tax-credit, https://grantcompass.ca/grants/canadian-film-or-video-production-tax-credit

### NZ — Significant New Zealand Content points test (New Zealand Production Grant)

- **Administering authority:** New Zealand Film Commission (NZFC) / Ministry for Culture and Heritage
- **Legal basis:** New Zealand Screen Production Grant framework
- **Foreign/service pathway (already canonical):** `nz_spg_international`
- **National pathway:** `(not yet a program_requirements.py record)`
- **Economic consequence:** UNLOCKS_SEPARATE_INCENTIVE — A 40% grant is available for New Zealand productions (vs the International rebate's 20% baseline) -- eligibility requires either significant NZ content (points-based test) OR official co-production status. Recovered from this same multi-pass arc's own prior research (nzfilm.co.nz, beehive.govt.nz), not re-researched.
- **Official co-production relationship:** Confirmed via NZFC: official co-production status is an explicit ALTERNATIVE route to the points test for the 40% NZ-production grant.
- **Sources:** https://www.nzfilm.co.nz/news/new-zealand-screen-production-grant, https://www.beehive.govt.nz/release/incentive-changes-sustainable-nz-screen-industry

## NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED (1)

- **US** — No current federal film tax credit exists at all (each state operates independently, already confirmed cultural_test_required=False for every US program in the canonical universe); no federal 'American content' certification analogous to Canada's CPTC or Australia's Producer Offset was found. A 2026 federal proposal (reported, not enacted) does not change the CURRENT confirmed state. Sources: https://www.wrapbook.com/production-incentives/us/federal, https://reedcorp.tax/helpful-guides/film-production-tax-credits-state/

## NATIONAL_STATUS_REGIME_CONFIRMED via the base incentive's own cultural test (21, mechanically resolved from the prior pass's existing citations)

`AT`, `BE`, `CY`, `CZ`, `DE`, `DK`, `FI`, `FR`, `GB`, `GR`, `HR`, `HU`, `IE`, `IT`, `LT`, `LU`, `MT`, `MY`, `NO`, `PL`, `PT`

Each of these jurisdictions' own served incentive already requires a real, primary/secondary-cited cultural test — that test IS the national/cultural status gate; no separate program exists in the current canonical universe to unlock. See `WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md` for each program's own citation.

## AUTHORITY_UNRESOLVED_EXACT_PROPOSITION (24)

`AE`, `CH`, `CL`, `EE`, `ES`, `FJ`, `IL`, `IS`, `JP`, `KR`, `MA`, `MU`, `MX`, `NL`, `PH`, `QA`, `RO`, `RS`, `SA`, `SE`, `SG`, `TH`, `TW`, `ZA`

Every one carries the same exact, real proposition: `NATIONAL_CULTURAL_STATUS_REGIME_EXISTENCE_UNCONFIRMED_BEYOND_BASE_INCENTIVE_CULTURAL_TEST_FIELD` — this jurisdiction's own served incentive(s) confirmed no cultural test, but no primary-authority research was performed this pass to confirm or deny a SEPARATE national/domestic regime (as genuinely exists for Canada, Australia, and New Zealand). Not "no relevant regime" — genuinely unresolved.

STOP.
