# Location-capability Codex remediation (Claude, 2026-10-07)

This remediates `docs/validation/CODEX_LOCATION_CAPABILITY_FINAL_ACCEPTANCE.md`, which found Natural Earth mis-tiered, Joggins false positives, inconsistent France scope, an unexhausted 235-cell residual, and an incomplete browser matrix.

- **Start:** `611fb72`.
- **Database:** `frametax2_claude_optimizer_acceptance_20260919`.
- **No regeneration:** location capability is served-state data, and the four 1.105.0 generations were reused unchanged.

## Result

| | Before (`de3e8b1` / `611fb72`) | After |
|---|---:|---:|
| Census rows / unique cells | 1,140 / 1,140 | 1,140 / 1,140 |
| AUTHORITY_VERIFIED_SUPPORTED | 819 | **826** |
| AUTHORITY_VERIFIED_NOT_SUPPORTED | 86 | **90** |
| AUTHORITY_UNRESOLVED_NEUTRAL | 235 | **224** |
| generic UNKNOWN / DISCOVERY as verified | 0 / 0 | 0 / 0 |

The counts reconcile as follows:

- **Supported:** 819 − 7 (evidence fixes below) + 14 (official-source research) = 826.
- **Not supported:** 86 + 2 (Joggins NB/NS) + 2 (USGS mountain floor) = 90.
- **Unresolved:** 235 + 5 (cells the evidence fixes reopened) − 16 (resolved by research) = 224.

**Evidence tiers after the fix:**

| Tier | Cells |
|---|---:|
| Intergovernmental | 539 |
| OPEN_GEOSPATIAL_DATASET (Natural Earth) | 165 |
| PEER_REVIEWED_OPEN_DATASET (Köppen-Geiger only) | 162 |
| Government dataset | 33 |
| FILM_COMMISSION_PAGE | 10 |
| Government agency page | 7 |
| None (unresolved) | 224 |

## 1. Natural Earth tier (EVD-001): corrected

- **Tier change.** `NE` and `NE_PP` now carry the tier `OPEN_GEOSPATIAL_DATASET`. They are described as an "open geospatial reference … not peer reviewed, not a government or film-agency source".
- **Peer-reviewed tier.** `KG2023` (Beck et al. 2023, Scientific Data) is the only `PEER_REVIEWED_OPEN_DATASET` source.
- **Tier order.** `ACCEPTED_TIERS` now ranks: intergovernmental > government dataset > government agency page > film commission page > peer reviewed > open geospatial.
- **Strongest-tier selection.** A cell's served tier is its strongest source's tier, so the 165 cells that rest only on Natural Earth now serve and display "open geospatial dataset" in the Workspace, Globe hover and Inspector.

**Proposition audit of the 165 Natural Earth-only cells.** Every proposition states the dataset fact literally:

- "Natural Earth mountain range region(s): …"
- "Natural Earth elevation point … ≥ 1,500 m"
- "Natural Earth populated places … ≥ 300,000"
- island landmass counts

**Weakest class.** Mountain cells supported by a Natural Earth range region alone, with no ≥ 1,500 m elevation point:

| Jurisdiction | Range region |
|---|---|
| AE-DXB | Al Hajar |
| AU-SA | Flinders |
| BE | Ardennes |
| CA-AB | Rockies |
| CA-NB | Appalachians |
| CA-QC | Appalachians / Adirondack / Torngat |
| FI | Kjølen |
| GB | Cambrian / Grampian |
| US-GA | Appalachians / Blue Ridge |
| US-OK | Ouachita |
| UY | Cuchilla Grande |

They remain supported only under the literal open-geospatial proposition, and the tier discloses that.

## 2. Joggins and the general fossil / scope fixes (EVD-002): corrected

Derivation fixes, in `backend/scripts/location_census_derivation/`:

- **`rules.py` (new; shared by `tab.py` and the tests).**
  - A property whose **name** marks it as a fossil or palaeontological site never evidences a present-day environment.
  - A keyword in a sentence with geological-era or fossil wording (Carboniferous, Pleistocene, Quaternary, "million years", "ice age", …) is skipped.
- **`tab.py` and `vec.py`.** Every point (UNESCO component, Natural Earth peak, populated place) belongs to exactly **one** admin-1 unit: the containing polygon, otherwise the nearest one within 0.05°. A subnational jurisdiction counts it only if that unit is the jurisdiction. This replaces the 0.05° buffer that leaked Joggins (Nova Scotia) into New Brunswick.

The buffer fix also corrected these subnational counts without changing any status:

| Jurisdiction | Change |
|---|---|
| CA-ON | cities ≥ 300k 9 → 7 |
| CA-QC | cities ≥ 300k 3 → 2; highest point 1,652 → 1,268 m (Torngat summit now NL) |
| CA-BC | highest point 4,671 → 4,019 m |
| US-TX | cities ≥ 300k 13 → 10 |
| US-IL | cities ≥ 300k 6 → 5 |
| US-NM | cities ≥ 300k 2 → 1 |
| US-OR | cities ≥ 300k 2 → 1 |
| US-PA | cities ≥ 300k 5 → 4 |
| US-VA | cities ≥ 300k 5 → 4 |
| US-CA | cities ≥ 300k 19 → 17 |

Small-town counts in 17 subnationals and the Great Smoky Mountains property, now assigned to NC by its listed coordinate, changed the same way.

**Joggins dispositions:**

| Cell | Before | After | Basis |
|---|---|---|---|
| CA-NS / jungle_rainforest | SUPPORTED (Joggins) | **AUTHORITY_VERIFIED_NOT_SUPPORTED** | Köppen-Geiger: no tropical or temperate class at all (existing dataset negative rule) |
| CA-NB / jungle_rainforest | SUPPORTED (Joggins, buffer spillover) | **AUTHORITY_VERIFIED_NOT_SUPPORTED** | same rule; Joggins no longer assigned to NB |
| CA / jungle_rainforest | SUPPORTED (Joggins) | **AUTHORITY_VERIFIED_SUPPORTED** | Government of British Columbia, Great Bear Rainforest land-use page (present-day temperate rainforest) |

Every other UNESCO keyword hit was re-audited. The fossil and era rules removed:

- desert: Al Ain (AE-AD), Wadi Al-Hitan (EG) and Chankillo (PE). All three keep desert support from Köppen-Geiger and FAO.
- the Pleistocene glaciers at Møns Klint (DK snow). Its present-day beech forests stay.
- the Quaternary glaciation at Talamanca (CR and PA snow).
- the ice-age glaciation in the English Lake District (GB snow).
- Niah's prehistoric rainforest-use record (MY). MY jungle stays supported by Köppen Af/Am.

## 3. France and overseas scope (EVD-003): reconciled

**Canonical scope.**

- `FR` means **metropolitan France including Corsica**: the clipped geometry, the census, the runtime capability profile and the UI label "France".
- `NL` means the **European Netherlands**.
- Every other national code means the Natural Earth admin-0 polygon of that state. That polygon excludes separately listed dependencies: Greenland and the Faroes for DK, British overseas territories for GB, Heard and McDonald for AU, and Puerto Rico for US (a census jurisdiction of its own).

**UNESCO rule.** A UNESCO property now counts for a national jurisdiction only if one of its component points lies inside that territory, with a 0.5° tolerance for near-shore islands such as Robben Island. Geometry and UNESCO evidence therefore share one scope.

Overseas evidence removed by the audit:

| Code | Removed evidence | Status change |
|---|---|---|
| FR | Réunion (jungle, forest, island), Martinique (forest), Marquesas (island), French Austral Lands (snow) | jungle → unresolved; others still supported from metropolitan sources |
| DK | Greenland (Ilulissat, Kujataa, Aasivissuit) | snow → unresolved |
| GB | Gough/Inaccessible, Henderson (island); St George, Bermuda (historic) | none (other evidence) |
| NL | Willemstad, Curaçao (historic) | none |
| AU | Heard and McDonald (island, snow) | none |
| US | La Fortaleza, Puerto Rico (historic) | none (US-PR is its own jurisdiction) |
| UA, RS | Chersonese (Crimea), Kosovo monuments: outside the Natural Earth admin-0 polygon used for geometry | none |

## 4. The residual: 235 Codex cells + 5 reopened = 240, bounded sequence completed

The bounded official-source sequence, run once per source on 2026-10-07:

1. **Repository canonical recovery.** Registries, program records and retained provenance hold no location-capability statements; a search for film-office and locations URLs found none relevant.
2. **Structured datasets.** The sequence already recorded per cell.
3. **Official film-office or agency location pages.** One or two per jurisdiction: 281 URLs fetched once with a 25 s timeout. 180 returned text and 93 failed (DNS, TLS, 403/404); some are client-side rendered.
4. **Government geography.**
   - **National:** the CIA World Factbook. It was sunset on 2026-02-04, and all 67 country URLs returned only the farewell notice.
   - **Targeted second pass**, only where a single government fact is decisive:
     - USGS *Elevations and Distances in the United States*: retrieved;
     - NPS Hawaiʻi Volcanoes: home page only, the Kaʻū Desert page returned 404;
     - Cairngorms National Park Authority: home page only;
     - NParks and VisitScotland: 404.

**How results were judged.** Candidate sentences were found by keyword, then **reviewed by hand**. Only explicit present-tense statements in official body text count:

- navigation-menu labels, film credits, producer testimonials and stand-in claims were rejected and are recorded;
- silence stays neutral.

**New negative rule.** Mountains are not supported when the official highest point is below the 300 m floor of every UNEP-WCMC mountain class (Kapos et al. 2000). This applies to US-LA (Driskill Mountain, 535 ft / 163 m) and US-RI (Jerimoth Hill, 812 ft / 247 m).

**Newly verified cells (16):**

| Cell | Disposition | Official proposition | Source (tier) |
|---|---|---|---|
| AE-AD mountains_alpine | SUPPORTED | Location Guide category "Mountains" | Abu Dhabi Film Commission (film commission page) |
| AU-SA forest_woodland | SUPPORTED | "dense green forests … bushland and forests" | South Australian Film Corporation |
| CA jungle_rainforest | SUPPORTED | Great Bear Rainforest | Government of British Columbia (agency page) |
| CA-BC jungle_rainforest | SUPPORTED | Great Bear Rainforest | Government of British Columbia |
| CA-MB desert_arid | SUPPORTED | "Desert landscape: Spirit Sands … open blowing sand dunes" | Manitoba Film & Music |
| CA-MB small_town_suburban | SUPPORTED | categories "Small Town Look", "Turn of Century Town" | Manitoba Film & Music |
| CA-NS rural_countryside | SUPPORTED | "coastal, rural, urban, historic" | Screen Nova Scotia |
| CA-NS small_town_suburban | SUPPORTED | "small town ambience" | Screen Nova Scotia |
| JO forest_woodland | SUPPORTED | "Ajloun Forest Reserve … 13 sq km" | Royal Film Commission – Jordan |
| JO historic_old_world | SUPPORTED | "Ajloun Castle (Qal'at Ar-Rabad)", "Historical Sites" | Royal Film Commission – Jordan |
| NZ desert_arid | SUPPORTED | "deserts"; "Rangipo Desert" | NZ Film Commission |
| NZ jungle_rainforest | SUPPORTED | "rugged forest and jungles" | NZ Film Commission |
| US-MA rural_countryside | SUPPORTED | "Rural Landscapes – rolling hills, farms, pastoral countryside" | Massachusetts Film Office |
| US-SC jungle_rainforest | SUPPORTED | "sub-tropical jungles" | South Carolina Film Commission |
| US-LA mountains_alpine | NOT_SUPPORTED | highest point 163 m < 300 m UNEP-WCMC floor | USGS (government dataset) |
| US-RI mountains_alpine | NOT_SUPPORTED | highest point 247 m < 300 m UNEP-WCMC floor | USGS |

**Remaining genuine authority silence.** 224 cells stay `AUTHORITY_UNRESOLVED_NEUTRAL`, runtime-neutral, with the exact URLs and outcomes recorded:

- **Silence:** for most, the official sources checked say nothing on the proposition, typically European rainforest, Gulf snow and desert, and small-state mountains.
- **Unavailable source:** for 63, every official fetch failed, and the failure is the recorded outcome.

The full trail, with every URL, check date and outcome, is in `backend/scripts/location_census_derivation/official_source_trail.json`, and per cell in the census CSV column `sources_attempted_if_unresolved`.

## 5. Runtime, semantics and economics (no regeneration)

- **Wiring.** The canonical path is unchanged: one owner (`jurisdiction_comparison.location_capability_cells`) → `jurisdiction_capability_profile` → `production_fit` → served fields → Workspace / Project Globe / hover / Inspector. All 13 controls are still wired (census and wiring tests).
- **Hard/soft semantics** (verified live):
  - hard supported → assessable (LLS Manitoba desert: Workable);
  - hard not supported → Weak / Not Suitable (LLS New Brunswick, Mauritius);
  - hard unresolved → "Location fit unconfirmed" / Conditional (LLS Ontario);
  - soft unresolved → "not assessed (no capability data, non-blocking)" (LU/FVD Newfoundland and Labrador);
  - service-only routes inherit no physical requirement.
- **Economic non-regression.** For all four projects, before/after served snapshots are identical:
  - order-normalized hash over scenario structure IDs, economic identities, verified and adjusted NPC, incentives, floors/maxima and participants;
  - curated counts LU 557 / FVD 646 / BH 275 / LLS 680;
  - the 217-row contract economics, baselines and co-production opportunities (25/27/25/25).

  Texas, Saskatchewan and Saudi Arabia remain visible. Each project keeps exactly one 1.105.0 generation.
- **The one served change is fit for LLS (hard desert).** Manitoba and New Zealand move from conditional to reference: Single-Jurisdiction conditional 51 → 49 and reference 25 → 27. Fit-confirmed scenarios rise from 227 to 325.

## 6. Browser matrix (local implementation evidence; frontend `localhost:5173`, backend `127.0.0.1:8010`, real pointer hovers)

| Project | Supported | Not supported | Unresolved | Workspace row → Inspector | Project Globe polygon hover + click | Map surface hover |
|---|---|---|---|---|---|---|
| LLS | CA-MB desert (Workable) | CA-NB desert (Weak); **Mauritius marker** (Weak) | CA-ON desert (fit unconfirmed) | CA-MB = hover text | CA-MB, CA-NB, CA-ON, MU | CA-MB, CA-NB, CA-ON |
| LU | GR rural (Strong) | AT, CA-MB marine (Weak) | CA-NL rural "not assessed" | CA-NL = hover text | CA-MB, CA-NL | AT, GR |
| FVD | CH / GR rural+urban | AT marine (Weak) | CA-NL rural+urban "not assessed" | CA-NL = hover text | CH | CA-NL, AT, GR |
| BH | — (no requirements on file) | — | GH "Location fit unconfirmed · NO REQUIREMENTS ON FILE" | GH = hover text | GH | GH |

In every case the hover card, the Inspector and the served fields carry identical fit and evidence text. There were no console errors and no failed application requests.

**One wiring defect was found and fixed.** The Workspace Map / Split hover card (`GlobeHoverCard` `RecommendedOrAlternativeBody`) omitted the served production-fit field that the Project Globe shows through its structure story. It now renders the same served `productionFitSummary`, never alongside a story's copy (frontend test added).

UI status: `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION`.

## 7. Tests (each family once)

| Family | Result |
|---|---|
| Census integrity / derivation / evidence tier / overseas scope / fossil rules / 240-cell trail, plus hard/soft (`test_location_capability_census.py`); location and content-gate wiring (`test_location_and_content_gate_wiring.py`) | 57/57 (one overreaching assertion of mine was corrected; that node was rerun) |
| Production-fit ranking and location controls | 25/25 |
| Frontend capability-evidence presentation (+ hover-card fit regression) | 4/4 |
| `vite build` | OK |

## Appendix: terminal disposition and official-source trail for all 240 residual cells

Source outcomes per cell, shown as host (result). Full URLs are in the trail JSON and CSV.

| Code | Category | Disposition | Official sources checked (2026-10-07) | Proposition found / absent |
|---|---|---|---|---|
| AE-AD | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | film.gov.ae (200 text); film.gov.ae (200 text) | no statement on the proposition in any checked official source |
| AE-AD | mountains_alpine | VERIFIED_SUPPORTED | film.gov.ae (200 text); film.gov.ae (200 text) | Abu Dhabi Film Commission Location Guide lists a 'Mountains' location category (alongside City, Coastlines, Middle Eastern Desert, Nature) |
| AE-AD | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | film.gov.ae (200 text); film.gov.ae (200 text) | no statement on the proposition in any checked official source |
| AE-AD | small_town_suburban | AUTHORITY_UNRESOLVED_NEUTRAL | film.gov.ae (200 text); film.gov.ae (200 text) | no statement on the proposition in any checked official source |
| AE-AD | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | film.gov.ae (200 text); film.gov.ae (200 text) | no statement on the proposition in any checked official source |
| AE-DXB | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | dftc.gov.ae (failed: URLError); dubaifilmcommission.ae (failed: URLError) | no statement on the proposition in any checked official source |
| AE-DXB | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | dftc.gov.ae (failed: URLError); dubaifilmcommission.ae (failed: URLError) | no statement on the proposition in any checked official source |
| AE-DXB | small_town_suburban | AUTHORITY_UNRESOLVED_NEUTRAL | dftc.gov.ae (failed: URLError); dubaifilmcommission.ae (failed: URLError) | no statement on the proposition in any checked official source |
| AE-DXB | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | dftc.gov.ae (failed: URLError); dubaifilmcommission.ae (failed: URLError) | no statement on the proposition in any checked official source |
| AL | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | nationalfilmcenter.gov.al (failed: URLError); qkk.gov.al (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| AL | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | nationalfilmcenter.gov.al (failed: URLError); qkk.gov.al (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| AL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | nationalfilmcenter.gov.al (failed: URLError); qkk.gov.al (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| AT | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | locationaustria.at (200 text); austrianfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| AT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | locationaustria.at (200 text); austrianfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| AU-QLD | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | screenqueensland.com.au (failed: HTTPError); screenqueensland.com.au (200 text) | no statement on the proposition in any checked official source |
| AU-SA | forest_woodland | VERIFIED_SUPPORTED | safilm.com.au (200 text); safilm.com.au (200 text) | SAFC Locations: 'From salt lakes to moonscapes and dense green forests to rugged desert ranges'; 'rural settings and dramatic bushland and forests' within 20 minutes of Adelaide |
| AU-SA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | safilm.com.au (200 text); safilm.com.au (200 text) | no statement on the proposition in any checked official source |
| AU-SA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | safilm.com.au (200 text); safilm.com.au (200 text) | no statement on the proposition in any checked official source |
| BE | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | filminflanders.be (failed: URLError); screen.brussels (failed: HTTPError); wallimage.be (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| BE | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminflanders.be (failed: URLError); screen.brussels (failed: HTTPError); wallimage.be (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| BE | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filminflanders.be (failed: URLError); screen.brussels (failed: HTTPError); wallimage.be (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| BG | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | nfc.bg (failed: HTTPError); bulgariafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| BG | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | nfc.bg (failed: HTTPError); bulgariafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| BG | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | nfc.bg (failed: HTTPError); bulgariafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CA-AB | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | albertafilm.ca (200 text); albertafilm.ca (200 text) | no statement on the proposition in any checked official source |
| CA-AB | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | albertafilm.ca (200 text); albertafilm.ca (200 text) | no statement on the proposition in any checked official source |
| CA-BC | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | creativebc.com (failed: HTTPError); creativebc.com (200 text); www2.gov.bc.ca (200 text) | no statement on the proposition in any checked official source |
| CA-BC | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | creativebc.com (failed: HTTPError); creativebc.com (200 text); www2.gov.bc.ca (200 text) | no statement on the proposition in any checked official source |
| CA-BC | jungle_rainforest | VERIFIED_SUPPORTED | creativebc.com (failed: HTTPError); creativebc.com (200 text); www2.gov.bc.ca (200 text) | Government of British Columbia land-use page for the present-day Great Bear Rainforest (West Coast region) |
| CA-BC | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | creativebc.com (failed: HTTPError); creativebc.com (200 text); www2.gov.bc.ca (200 text) | no statement on the proposition in any checked official source |
| CA-MB | desert_arid | VERIFIED_SUPPORTED | mbfilmmusic.ca (200 text); mbfilmmusic.ca (200 text) | Manitoba Film & Music locations, 'Desert landscape': 'Spirit Sands is a four-sq-km tract of open blowing sand dunes that tower 30 m above the surrounding prairie' |
| CA-MB | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | mbfilmmusic.ca (200 text); mbfilmmusic.ca (200 text) | no statement on the proposition in any checked official source |
| CA-MB | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | mbfilmmusic.ca (200 text); mbfilmmusic.ca (200 text) | insufficient: Manitoba Film & Music page: 'Rhode Island' appears only as a film credit, not a Manitoba location |
| CA-MB | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | mbfilmmusic.ca (200 text); mbfilmmusic.ca (200 text) | no statement on the proposition in any checked official source |
| CA-MB | small_town_suburban | VERIFIED_SUPPORTED | mbfilmmusic.ca (200 text); mbfilmmusic.ca (200 text) | Manitoba Film & Music location categories include 'Small Town Look' and 'Turn of Century Town' |
| CA-NB | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | tourismnewbrunswick.ca (200 text); www2.gnb.ca (200 text) | insufficient: Tourism New Brunswick: 'Historic Sites' appears only as a navigation-menu label |
| CA-NB | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | tourismnewbrunswick.ca (200 text); www2.gnb.ca (200 text) | insufficient: Tourism New Brunswick: 'Ferries & Farms' appears only as a road-trip menu label |
| CA-NB | urban_major_city | AUTHORITY_UNRESOLVED_NEUTRAL | tourismnewbrunswick.ca (200 text); www2.gnb.ca (200 text) | insufficient: Tourism New Brunswick: 'Cities & Regions' appears only as a navigation-menu label (no city of the required size is stated) |
| CA-NL | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | nlfdc.ca (failed: URLError); nlfdc.ca (failed: URLError) | no statement on the proposition in any checked official source |
| CA-NL | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | nlfdc.ca (failed: URLError); nlfdc.ca (failed: URLError) | no statement on the proposition in any checked official source |
| CA-NL | urban_major_city | AUTHORITY_UNRESOLVED_NEUTRAL | nlfdc.ca (failed: URLError); nlfdc.ca (failed: URLError) | no statement on the proposition in any checked official source |
| CA-NS | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | screennovascotia.com (200 text); screennovascotia.com (200 text) | no statement on the proposition in any checked official source |
| CA-NS | rural_countryside | VERIFIED_SUPPORTED | screennovascotia.com (200 text); screennovascotia.com (200 text) | Screen Nova Scotia Locations: 'an exceptional variety of distinctive and visually compelling locations - coastal, rural, urban, historic' |
| CA-NS | small_town_suburban | VERIFIED_SUPPORTED | screennovascotia.com (200 text); screennovascotia.com (200 text) | Screen Nova Scotia: 'Urban sophistication, small town ambience, and miles of unspoiled coastline' |
| CA-ON | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | ontariocreates.ca (failed: HTTPError); ontariocreates.ca (200 text) | no statement on the proposition in any checked official source |
| CA-ON | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | ontariocreates.ca (failed: HTTPError); ontariocreates.ca (200 text) | no statement on the proposition in any checked official source |
| CA-ON | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | ontariocreates.ca (failed: HTTPError); ontariocreates.ca (200 text) | no statement on the proposition in any checked official source |
| CA-ON | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | ontariocreates.ca (failed: HTTPError); ontariocreates.ca (200 text) | no statement on the proposition in any checked official source |
| CA-QC | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | qftc.ca (failed: HTTPError); qftc.ca (failed: HTTPError) | no statement on the proposition in any checked official source |
| CA-SK | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | creativesask.ca (200 text); tourismsaskatchewan.com (200 text) | no statement on the proposition in any checked official source |
| CA-SK | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | creativesask.ca (200 text); tourismsaskatchewan.com (200 text) | no statement on the proposition in any checked official source |
| CA-SK | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | creativesask.ca (200 text); tourismsaskatchewan.com (200 text) | no statement on the proposition in any checked official source |
| CA-SK | urban_major_city | AUTHORITY_UNRESOLVED_NEUTRAL | creativesask.ca (200 text); tourismsaskatchewan.com (200 text) | insufficient: Tourism Saskatchewan: 'Prairie Life & City Lights' appears only as a travel-zone menu label |
| CA | jungle_rainforest | VERIFIED_SUPPORTED | www2.gov.bc.ca (200 text); cia.gov (Factbook sunset) | Government of British Columbia land-use page for the present-day Great Bear Rainforest (west coast of BC, Canada) |
| CH | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmlocation.ch (failed: URLError); swissfilms.ch (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CH | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmlocation.ch (failed: URLError); swissfilms.ch (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CR | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmcostarica.com (200 text); procomer.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CR | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | filmcostarica.com (200 text); procomer.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CY | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | investcyprus.org.cy (200 text); cyprusfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CY | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | investcyprus.org.cy (200 text); cyprusfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CY | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | investcyprus.org.cy (200 text); cyprusfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CY | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | investcyprus.org.cy (200 text); cyprusfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| CZ | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.cz (200 text); filmcommission.cz (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DE | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | location-germany.de (200 text); ffa.de (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DE | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | location-germany.de (200 text); ffa.de (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DK | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | dfi.dk (200 text); thedanishfilmcommission.dk (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DK | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | dfi.dk (200 text); thedanishfilmcommission.dk (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DK | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | dfi.dk (200 text); thedanishfilmcommission.dk (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DO | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | dgcine.gob.do (failed: HTTPError); dgcine.gob.do (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| DO | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | dgcine.gob.do (failed: HTTPError); dgcine.gob.do (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| EE | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | filmestonia.eu (200 text); filmestonia.eu (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| EG | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | egyptfilmcommission.com (failed: URLError); egymonuments.gov.eg (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ES | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | shootinginspain.info (failed: HTTPError); shootinginspain.info (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| FI | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filminfinland.com (failed: HTTPError); filminfinland.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| FJ | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | filmfiji.com (200 text); filmfiji.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| FJ | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmfiji.com (200 text); filmfiji.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| FR | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmfrance.net (failed: URLError); filmfrance.net (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| FR | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmfrance.net (failed: URLError); filmfrance.net (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GB | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | britishfilmcommission.org.uk (200 text); screen.scot (failed: URLError); cairngorms.co.uk (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GB | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | britishfilmcommission.org.uk (200 text); screen.scot (failed: URLError); cairngorms.co.uk (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GB | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | britishfilmcommission.org.uk (200 text); screen.scot (failed: URLError); cairngorms.co.uk (failed: HTTPError); cia.gov (Factbook sunset); visitscotland.com (failed: HTTPError); cairngorms.co.uk (200 text) | insufficient: Cairngorms National Park Authority home page fetched: no snow/snow-sport statement; winter-activities and VisitScotland winter-sports pages HTTP 404 |
| GE | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | gnfc.ge (failed: HTTPError); filmingeorgia.ge (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GE | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | gnfc.ge (failed: HTTPError); filmingeorgia.ge (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GH | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | nfa.gov.gh (failed: URLError); visitghana.com (200 text); cia.gov (Factbook sunset) | insufficient: Visit Ghana (Ghana Tourism Authority): 'Mountains' appears only as a navigation-menu label |
| GR | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | ekome.media (failed: URLError); ekome.media (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| GR | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | ekome.media (failed: URLError); ekome.media (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| HR | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmingincroatia.hr (failed: HTTPError); filmingincroatia.hr (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| HU | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | nfi.hu (failed: HTTPError); nfi.hu (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IE | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | screenireland.ie (failed: HTTPError); screenireland.ie (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IE | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | screenireland.ie (failed: HTTPError); screenireland.ie (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IE | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | screenireland.ie (failed: HTTPError); screenireland.ie (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IE | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | screenireland.ie (failed: HTTPError); screenireland.ie (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IL | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | filminisrael.com (200 text); jerusalemfilmfund.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminisrael.com (200 text); jerusalemfilmfund.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IS | forest_woodland | AUTHORITY_UNRESOLVED_NEUTRAL | filminiceland.com (200 text); filminiceland.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IS | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | filminiceland.com (200 text); filminiceland.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IS | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminiceland.com (200 text); filminiceland.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IS | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | filminiceland.com (200 text); filminiceland.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IT | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | italianfilmcommissions.it (200 text); italianfilmcommissions.it (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| IT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | italianfilmcommissions.it (200 text); italianfilmcommissions.it (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| JO | forest_woodland | VERIFIED_SUPPORTED | film.jo (200 text); film.jo (200 text); cia.gov (Factbook sunset) | Royal Film Commission - Jordan location entry 'Ajloun Forest Reserve': 'located in the Ajloun highlands north of Amman and covers 13 sq km' |
| JO | historic_old_world | VERIFIED_SUPPORTED | film.jo (200 text); film.jo (200 text); cia.gov (Factbook sunset) | Royal Film Commission - Jordan location entries 'Ajloun Castle' (Qal'at Ar-Rabad) and the 'Historical Sites' location category |
| JO | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | film.jo (200 text); film.jo (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| JO | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.jo (200 text); film.jo (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| JO | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | film.jo (200 text); film.jo (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| JP | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | japanfc.org (200 text); japanfc.org (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| KR | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | koreanfilm.or.kr (failed: HTTPError); koreanfilm.or.kr (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| KR | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | koreanfilm.or.kr (failed: HTTPError); koreanfilm.or.kr (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| KZ | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | kazakhfilm.kz (failed: HTTPError); kazakhfilm.kz (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| KZ | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | kazakhfilm.kz (failed: HTTPError); kazakhfilm.kz (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LT | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | lkc.lt (200 text); filmlithuania.lt (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LT | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | lkc.lt (200 text); filmlithuania.lt (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LU | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmfund.lu (failed: URLError); filmfund.lu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LU | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmfund.lu (failed: URLError); filmfund.lu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LU | urban_major_city | AUTHORITY_UNRESOLVED_NEUTRAL | filmfund.lu (failed: URLError); filmfund.lu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LV | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | nkc.gov.lv (200 text); filmlatvia.lv (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| LV | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | nkc.gov.lv (200 text); filmlatvia.lv (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MA | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | ccm.ma (200 text); ccm.ma (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | ccm.ma (200 text); ccm.ma (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ME | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | fccg.me (200 text); filmingmontenegro.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ME | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | fccg.me (200 text); filmingmontenegro.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ME | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | fccg.me (200 text); filmingmontenegro.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MK | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmagency.gov.mk (failed: HTTPError); filmagency.gov.mk (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MK | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | filmagency.gov.mk (failed: HTTPError); filmagency.gov.mk (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MK | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmagency.gov.mk (failed: HTTPError); filmagency.gov.mk (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MN | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | filmcouncil.mn (failed: URLError); mongolia.travel (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MT | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | maltafilmcommission.com (failed: HTTPError); maltafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | maltafilmcommission.com (failed: HTTPError); maltafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MT | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | maltafilmcommission.com (failed: HTTPError); maltafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MT | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | maltafilmcommission.com (failed: HTTPError); maltafilmcommission.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MU | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | edbmauritius.org (failed: HTTPError); mauritiusfilm.mu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MU | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | edbmauritius.org (failed: HTTPError); mauritiusfilm.mu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MU | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | edbmauritius.org (failed: HTTPError); mauritiusfilm.mu (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MX | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | comefilm.gob.mx (200 text); imcine.gob.mx (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MY | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filminmalaysia.com (200 text); filminmalaysia.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| MY | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filminmalaysia.com (200 text); filminmalaysia.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| NL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.nl (200 text); filmcommission.nl (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| NL | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.nl (200 text); filmcommission.nl (200 text); cia.gov (Factbook sunset) | insufficient: Netherlands Film Commission locations list 'Saint Pieter mountain' and 'Dutch mountains' (Maastricht hills); not a mountain/alpine environment |
| NL | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.nl (200 text); filmcommission.nl (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| NO | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | norwegianfilm.com (200 text); nfi.no (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| NO | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | norwegianfilm.com (200 text); nfi.no (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| NZ | desert_arid | VERIFIED_SUPPORTED | nzfilm.co.nz (200 text); cia.gov (Factbook sunset) | NZ Film Commission locations: 'coastlines, cities, colonial towns, alpine terrain, forests, deserts, and countryside'; location 'Rangipo Desert - volcanic terrain, stark open plains' |
| NZ | jungle_rainforest | VERIFIED_SUPPORTED | nzfilm.co.nz (200 text); cia.gov (Factbook sunset) | NZ Film Commission locations: 'Denize Bluff, Waikato Cliffs, rugged forest and jungles' |
| PA | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | panamafilmcommission.gob.pa (failed: URLError); dicine.gob.pa (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | panamafilmcommission.gob.pa (failed: URLError); dicine.gob.pa (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PH | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | fdcp.ph (200 text); fdcp.ph (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PL | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.pl (failed: URLError); filmcommission.pl (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PL | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.pl (failed: URLError); filmcommission.pl (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.pl (failed: URLError); filmcommission.pl (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | portugalfilmcommission.com (200 text); portugalfilmcommission.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| PT | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | portugalfilmcommission.com (200 text); portugalfilmcommission.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| QA | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | dohafilm.com (200 text); dohafilm.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| QA | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | dohafilm.com (200 text); dohafilm.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| QA | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | dohafilm.com (200 text); dohafilm.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| QA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | dohafilm.com (200 text); dohafilm.com (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| RO | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | cnc.gov.ro (failed: HTTPError); romaniafilmcommission.ro (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| RO | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | cnc.gov.ro (failed: HTTPError); romaniafilmcommission.ro (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| RO | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | cnc.gov.ro (failed: HTTPError); romaniafilmcommission.ro (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| RS | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminserbia.com (200 text); filminserbia.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SA | forest_woodland | AUTHORITY_UNRESOLVED_NEUTRAL | film.moc.gov.sa (failed: URLError); film.moc.gov.sa (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.moc.gov.sa (failed: URLError); film.moc.gov.sa (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | film.moc.gov.sa (failed: URLError); film.moc.gov.sa (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SE | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filminstitutet.se (200 text); swedishfilmcommission.se (failed: 202); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SE | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminstitutet.se (200 text); swedishfilmcommission.se (failed: 202); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SG | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | imda.gov.sg (200 text); visitsingapore.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SG | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | imda.gov.sg (200 text); visitsingapore.com (200 text); cia.gov (Factbook sunset); nparks.gov.sg (failed: HTTPError) | no statement on the proposition in any checked official source |
| SG | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | imda.gov.sg (200 text); visitsingapore.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SG | small_town_suburban | AUTHORITY_UNRESOLVED_NEUTRAL | imda.gov.sg (200 text); visitsingapore.com (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SI | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | film-center.si (failed: HTTPError); film-center.si (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SI | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | film-center.si (failed: HTTPError); film-center.si (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SI | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | film-center.si (failed: HTTPError); film-center.si (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SI | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film-center.si (failed: HTTPError); film-center.si (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SK | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.sk (failed: HTTPError); filmcommission.sk (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| SK | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmcommission.sk (failed: HTTPError); filmcommission.sk (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TH | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmthailand.org (200 text); filmthailand.org (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TT | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | filmtt.co.tt (failed: HTTPError); filmtt.co.tt (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TT | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | filmtt.co.tt (failed: HTTPError); filmtt.co.tt (failed: HTTPError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TW | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | taipeifilmcommission.org (failed: URLError); tfc.org.tw (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TW | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | taipeifilmcommission.org (failed: URLError); tfc.org.tw (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| TW | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | taipeifilmcommission.org (failed: URLError); tfc.org.tw (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| UA | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | usfa.gov.ua (200 text); ukrainianfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| UA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | usfa.gov.ua (200 text); ukrainianfilmcommission.com (failed: URLError); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| US-AL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | alabamafilm.org (failed: URLError); alabamafilm.org (failed: URLError) | no statement on the proposition in any checked official source |
| US-AL | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | alabamafilm.org (failed: URLError); alabamafilm.org (failed: URLError) | no statement on the proposition in any checked official source |
| US-AZ | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | azcommerce.com (failed: HTTPError); azcommerce.com (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-AZ | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | azcommerce.com (failed: HTTPError); azcommerce.com (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-CA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.ca.gov (failed: HTTPError); film.ca.gov (200 text) | no statement on the proposition in any checked official source |
| US-CO | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | coloradofilm.org (200 text); coloradofilm.org (200 text) | no statement on the proposition in any checked official source |
| US-CT | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | portal.ct.gov (200 text); portal.ct.gov (200 text) | no statement on the proposition in any checked official source |
| US-CT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | portal.ct.gov (200 text); portal.ct.gov (200 text) | no statement on the proposition in any checked official source |
| US-CT | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | portal.ct.gov (200 text); portal.ct.gov (200 text) | no statement on the proposition in any checked official source |
| US-CT | small_town_suburban | AUTHORITY_UNRESOLVED_NEUTRAL | portal.ct.gov (200 text); portal.ct.gov (200 text) | no statement on the proposition in any checked official source |
| US-GA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | georgia.org (failed: HTTPError); georgia.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-GA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | georgia.org (failed: HTTPError); georgia.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-HI | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | filmoffice.hawaii.gov (200 text); nps.gov (failed: HTTPError); nps.gov (failed: HTTPError); nps.gov (200 text) | insufficient: NPS Hawaii Volcanoes Ka'u Desert page not retrievable (HTTP 404); park home page fetched, no desert statement |
| US-IL | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | dceo.illinois.gov (200 text); www2.illinois.gov (200 text) | no statement on the proposition in any checked official source |
| US-KY | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmoffice.ky.gov (200 text); filmoffice.ky.gov (200 text) | no statement on the proposition in any checked official source |
| US-KY | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmoffice.ky.gov (200 text); filmoffice.ky.gov (200 text) | no statement on the proposition in any checked official source |
| US-LA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | louisianaentertainment.gov (200 text); louisianaentertainment.gov (200 text) | no statement on the proposition in any checked official source |
| US-LA | mountains_alpine | VERIFIED_NOT_SUPPORTED | louisianaentertainment.gov (200 text); louisianaentertainment.gov (200 text); pubs.usgs.gov (200 text) | USGS: Louisiana's highest point is Driskill Mountain, 535 ft (163 m), below the 300 m floor of every UNEP-WCMC mountain class |
| US-LA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | louisianaentertainment.gov (200 text); louisianaentertainment.gov (200 text) | no statement on the proposition in any checked official source |
| US-MA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | mafilm.org (200 text); mafilm.org (200 text) | no statement on the proposition in any checked official source |
| US-MA | rural_countryside | VERIFIED_SUPPORTED | mafilm.org (200 text); mafilm.org (200 text) | Massachusetts Film Office: 'Rural Landscapes - Rolling hills, farms, and pastoral countryside scenes' |
| US-MD | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | marylandfilm.org (200 text); marylandfilm.org (200 text) | no statement on the proposition in any checked official source |
| US-MN | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | mnfilmtv.org (failed: HTTPError); mnfilmtv.org (failed: HTTPError); pubs.usgs.gov (200 text) | no statement on the proposition in any checked official source |
| US-MS | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filmmississippi.org (failed: HTTPError); filmmississippi.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-MS | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmmississippi.org (failed: HTTPError); filmmississippi.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-MS | urban_major_city | AUTHORITY_UNRESOLVED_NEUTRAL | filmmississippi.org (failed: HTTPError); filmmississippi.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-NC | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | ncfilm.com (failed: URLError); ncfilm.com (failed: URLError) | no statement on the proposition in any checked official source |
| US-NM | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | nmfilm.com (200 text); nmfilm.com (200 text) | no statement on the proposition in any checked official source |
| US-NV | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | nvfilm.com (failed: 200); nvfilm.com (failed: 200) | no statement on the proposition in any checked official source |
| US-NV | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | nvfilm.com (failed: 200); nvfilm.com (failed: 200) | no statement on the proposition in any checked official source |
| US-NY | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | esd.ny.gov (failed: HTTPError); esd.ny.gov (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-OK | desert_arid | AUTHORITY_UNRESOLVED_NEUTRAL | okfilmmusic.org (200 text); okfilmmusic.org (200 text) | no statement on the proposition in any checked official source |
| US-OK | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | okfilmmusic.org (200 text); okfilmmusic.org (200 text) | no statement on the proposition in any checked official source |
| US-OK | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | okfilmmusic.org (200 text); okfilmmusic.org (200 text) | no statement on the proposition in any checked official source |
| US-OR | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | oregonfilm.org (200 text); oregonfilm.org (200 text) | no statement on the proposition in any checked official source |
| US-PA | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | filminpa.com (failed: HTTPError); filminpa.com (200 text) | no statement on the proposition in any checked official source |
| US-PA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | filminpa.com (failed: HTTPError); filminpa.com (200 text) | no statement on the proposition in any checked official source |
| US-PR | mountains_alpine | AUTHORITY_UNRESOLVED_NEUTRAL | puertoricofilm.com (failed: URLError); investpr.org (failed: HTTPError); pubs.usgs.gov (200 text) | no statement on the proposition in any checked official source |
| US-PR | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | puertoricofilm.com (failed: URLError); investpr.org (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-RI | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.ri.gov (200 text); film.ri.gov (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-RI | mountains_alpine | VERIFIED_NOT_SUPPORTED | film.ri.gov (200 text); film.ri.gov (failed: HTTPError); pubs.usgs.gov (200 text) | USGS: Rhode Island's highest point is Jerimoth Hill, 812 ft (247 m), below the 300 m floor of every UNEP-WCMC mountain class |
| US-RI | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | film.ri.gov (200 text); film.ri.gov (failed: HTTPError) | no statement on the proposition in any checked official source |
| US-RI | small_town_suburban | AUTHORITY_UNRESOLVED_NEUTRAL | film.ri.gov (200 text); film.ri.gov (failed: HTTPError) | insufficient: Rhode Island Film & TV Office: 'the city, the small town, the coastline' appears only inside a producer testimonial, not as the office's own statement |
| US-SC | jungle_rainforest | VERIFIED_SUPPORTED | filmsc.com (200 text); filmsc.com (200 text) | South Carolina Film Commission Locations: locations 'include mountains and the coast, rural settings ... and sub-tropical jungles' |
| US-SC | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | filmsc.com (200 text); filmsc.com (200 text) | no statement on the proposition in any checked official source |
| US-TN | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | tnentertainment.com (200 text); tnentertainment.com (200 text) | insufficient: Tennessee Entertainment Commission: forests 'have stood in for the jungles of Asia' (a stand-in look, not a jungle/rainforest environment) |
| US-TX | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | gov.texas.gov (failed: HTTPError); gov.texas.gov (200 text) | no statement on the proposition in any checked official source |
| US-TX | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | gov.texas.gov (failed: HTTPError); gov.texas.gov (200 text) | no statement on the proposition in any checked official source |
| US-UT | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.utah.gov (200 text); film.utah.gov (200 text) | no statement on the proposition in any checked official source |
| US-UT | rural_countryside | AUTHORITY_UNRESOLVED_NEUTRAL | film.utah.gov (200 text); film.utah.gov (200 text) | no statement on the proposition in any checked official source |
| US-VA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | film.virginia.org (200 text); film.virginia.org (200 text) | no statement on the proposition in any checked official source |
| UY | island_tropical | AUTHORITY_UNRESOLVED_NEUTRAL | icau.mec.gub.uy (200 text); uruguayxxi.gub.uy (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| UY | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | icau.mec.gub.uy (200 text); uruguayxxi.gub.uy (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| UY | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | icau.mec.gub.uy (200 text); uruguayxxi.gub.uy (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| UZ | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | uzbekkino.uz (failed: URLError); uzbektourism.uz (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ZA | historic_old_world | AUTHORITY_UNRESOLVED_NEUTRAL | wesgro.co.za (failed: HTTPError); gfc.co.za (200 text); kwazulunatalfilm.co.za (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ZA | jungle_rainforest | AUTHORITY_UNRESOLVED_NEUTRAL | wesgro.co.za (failed: HTTPError); gfc.co.za (200 text); kwazulunatalfilm.co.za (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |
| ZA | snow_arctic | AUTHORITY_UNRESOLVED_NEUTRAL | wesgro.co.za (failed: HTTPError); gfc.co.za (200 text); kwazulunatalfilm.co.za (200 text); cia.gov (Factbook sunset) | no statement on the proposition in any checked official source |