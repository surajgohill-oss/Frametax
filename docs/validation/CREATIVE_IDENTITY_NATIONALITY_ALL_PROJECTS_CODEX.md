# Creative Identity + Nationality Research Pipeline — All-Project Audit

**Audit date:** 2026-09-04 (America/Los_Angeles)

**Repository:** `/Users/Suraj/cineglobe-frametax` (`surajgohill-oss/Frametax`)

**Application:** `/Users/Suraj/cineglobe-frametax/frametax2`

**Branch:** `claude/audit-frametax-features-NZcX5`

**Audited local/remote HEAD at publication gate:** `1dde42ea627ed757477c103eaa32d135320b4f24`

**Remote:** `https://github.com/surajgohill-oss/Frametax.git`

**Database:** PostgreSQL `frametax2`, Alembic `0071`, reachable at audit time
**Mode:** read-only repository/database/document audit plus bounded public-web research; no application, database, doctrine, optimizer, or UI changes

## Verification legend

- **STATIC VERIFIED** — established from current repository code or immutable stored project material.
- **RUNTIME VERIFIED** — established from the current database or a direct read-only parser/query.
- **BLOCKED** — a safe conclusion or served result requires architecture, stronger evidence, or human resolution that is not present.

## Executive conclusion

**STATIC VERIFIED / RUNTIME VERIFIED:** CineGlobe currently contains **50 projects**, **82 current document records**, and **11 `ProjectPerson` rows**. Those rows cover 10 Double Zero, Lips Like Sugar, Rocky Mountain, The Cure, The Little Utopia, and The System. Current materials contain **64 distinct named creative/person candidates** (including exact story/revision/underlying-work/creator distinctions and the two current Little Utopia producers). Forty projects have usable writer and/or director evidence; two more contain only underlying-work/creator evidence; eight contain no usable named writer/director in the material that could be reliably searched.

The database changed concurrently during this audit: five newly derived writer rows appeared after the initial inventory. The final report uses the later, current 82-document/11-person snapshot. Nick Vallelonga, Ice Cube, and James Greer were automatically assigned `US` with `nationality_confidence=DISCOVERY`; Jonathan Bernstein and Dallas Jackson remain `unresolved_no_match`. This is direct runtime proof that the current pipeline can put discovery-grade Wikidata output into `primary_nationality` while downstream has no evidence-tier gate.

The prior audit's FVD diagnosis was correct but its nationality conclusion was too narrow. The live nationality resolver runs only after a person has been canonicalized and uses Wikidata `P27` as its sole automated external path. Most projects never reach that point. Even when a person does exist, the consumer reads one `primary_nationality`, merges it with residence codes in the legacy 24-program path, and does not enforce the stored evidence tier.

Broader identity-resolved research materially changes the result:

- **Lips Like Sugar:** Brantley Gutierrez is explicitly described as **“Colombian-American”**; Anthony Tambakis is explicitly described as **American / United States** by multiple industry sources. The prior `unresolved_no_match` result is a search-method failure, not proof of absence.
- **FVD:** stronger explicit American descriptors exist for Steve Bencich and Mark Gantt, although Steve's evidence remains secondary and neither result is legal proof of citizenship.
- **Little Utopia:** Clara Salaman's British and Kim Farrant's Australian descriptors are strongly corroborated, but their current canonical values were migration-seeded and the live evidence chain is not authority-tier safe.
- **Bad Hombres:** the stored budget identifies director **John Stalberg**; role/title corroboration resolves him as **John Stalberg Jr.**, explicitly described as American in a secondary source. Current canonical state remains empty. The public film credit for Nick Turner and Rex New is an external lead, not a stored-source role claim.

**Implementation decision: BLOCKED for a narrow patch.** The missing generic boundary is a structured project-person-role evidence/reconciliation layer plus diversified, tier-aware nationality research. A regex or per-title patch would perpetuate the same failure. No production code was changed.

## 1. Current project and source inventory

The following is the complete current project set. “Canonical” means current `ProjectPerson`, not a name merely present in a file. Exact credit types are intentionally not collapsed.

| Project | Current source evidence and extraction result | Current canonical state | Gap / result |
|---|---|---|---|
| 10 Double Zero | Screenplay: `Written by Nick Vallelonga and Christian Sesma & Paul Sloan`; budget: director Christian Sesma | Nick Vallelonga writer, US/`DISCOVERY`; Christian/Paul/director absent | parser persisted only one of three writers; director disconnected |
| 5 LBS OF PRESSURE | Script PDF starts at `FADE IN`; PDF metadata says author Phil Allocco; budget says director Phil Allocco | none | director explicit; writer is metadata/model candidate, not title-page credit |
| 97 Minutes | incentive estimate says director Timo Vuorensola | none | named director not ingested |
| Adam & Eve | screenplay: `by Mark Perez` | none | standalone byline unsupported |
| All My Friends Are Dead | screenplay/budget: Josh Sims and Jessica Sarah Flaum; director Marcus Dunstan | none | all claims disconnected |
| Almost Perfect | `Screenplay by Marc Lhormer`; based on *The Wine Forger* by Carrie Regan | none | screenplay and underlying work must remain distinct |
| Artists of Cinema | extractable deck checked; no explicit writer/director | none | genuine source gap |
| Bad Hombres | budget: `Director: John Stalberg` | none | resolved externally to John Stalberg Jr.; public writers are external-only leads |
| Baron Samedi | budget: director Darin Scott; writer Sean Michael Argo; image-heavy deck not fully machine-searchable | none | writer identity resolved; director same-name ambiguity remains |
| Being Britney | extractable deck checked; no explicit writer/director | none | genuine source gap |
| Braking Point | no current documents | none | blocked at source availability |
| David | screenplay: `Written by John Michael Kennedy` | none | name too ambiguous for safe external identity resolution |
| Dead After Dark | screenplay: `Written by Cooper Hefner` | none | claim not ingested |
| Drug Honey | screenplay: `Written by John Michael Kennedy` | none | same unresolved identity as *David* |
| F#K Valentine's Day | screenplay standalone `by / Steve Bencich`; budget `Writer: Steve Bencich`, `Director: Mark Gantt`; deck repeats both | none | three-source evidence; no canonical people |
| Flash Before the Bang | screenplay by Jevon Whetter & Joan Considine Johnson; story by Hayden Roush, Whetter, Johnson, Dave Alan Johnson | none | exact screenplay/story taxonomy absent |
| Gifted | `Written by Robert Leader & Matt Dority` | none | both public identities unresolved |
| Give or Take | written by Gabriel Mizrahi; story by Suzanne Farwell & Gabriel Mizrahi | none | role taxonomy and identities not canonicalized |
| Going Places | budget: director Timo Vuorensola | none | named director not ingested |
| Hightower | `Written by Jonathan Hensleigh` | none | title credit not ingested |
| Interference | budget: `DIRECTOR: Mel Rogriguez III` | none | source spelling/identity unresolved; do not autocorrect |
| Jane Millen | screenplay: `by Cynthia Mort` | none | standalone byline unsupported |
| Lips Like Sugar | same title-page line: `Directed by Brantley Gutierrez Written by Anthony Tambakis`; story by both | both names exist, nationality null, unconfirmed | extraction succeeds; nationality resolver/search quality fails |
| Maggie Moves On | title/author `Lucy Score`; PDF is book/underlying material, not an explicit screenplay credit | none | correct treatment is underlying author only |
| Model Wars | image-heavy deck checked at extractable-text layer; no reliable explicit writer/director | none | visual-content review remains blocked |
| One Night Stand | no current documents | none | blocked at source availability |
| Otherwise Engaged | screenplay/deck: Gabriel Mizrahi & Suzanne Farwell; deck says director Suzanne Farwell | none | multi-source roles not ingested |
| Replacements | written by Jennifer Bosworth; story by Jennifer & Ryan Bosworth | none | exact credit taxonomy absent |
| Rocky Mountain | screenplay: `Written by Ice Cube`; budget director TBD | Ice Cube writer, US/`DISCOVERY` | writer now derived; no director identity exists |
| Rust | legal document explicitly says screenplay written by Joel Souza | none | legal/source adapter absent; unnamed director references are not identity evidence |
| Safehaven | finance workbook only; no explicit writer/director | none | genuine source gap |
| Serpent Girl | screenplay: `by Matthew Carnahan` | none | standalone byline unsupported |
| Sierra Madre | screenplay by Taylor Sheridan; revisions Ian Mackenzie Jeffers; story James Keach & Trevor Alpert | none | screenplay/revision/story distinctions absent |
| Sky Unconditional | screenplay page names director Soyun Song; no writer found | none | director identity cannot be safely resolved externally |
| Spice Route | no current documents | none | blocked at source availability |
| Terezin | original writers Susan Nanus & Emil Sher; revisions Todd Komarnicki; current revisions/deck writer Terence Winter; director TBD | none | version/supersession semantics absent |
| The Arrangement | written by Gaby Allan & Jen Crittenden | none | aliases resolve to Gabrielle Allan and Jennifer Crittenden; not ingested |
| The Cure | written by Jonathan Bernstein & James Greer; budget director Nancy Leopardi | both writers derived; James US/`DISCOVERY`, Jonathan nationality unresolved | director remains disconnected; evidence-tier risk confirmed |
| The Dale | written/current revisions Terence Winter; revisions Our Lady J (now Yona Speidel); deck writer Terence, director TBD | none | alias/version/revision handling absent |
| The Little Utopia | screenplay Clara Salaman; deck/lookbook/budget Clara and director Kim Farrant; producers Max Botkin/Rachel Winter in migrated facts | Clara GB, Kim AU, Max US, Rachel US, confirmed | canonical values exist from migration, not a complete live evidence pipeline |
| The Men We Leave Behind | screenplay/lookbook: directed and written by Lee Jung-jae | none | strong official identity/nationality evidence, no ingestion |
| The Room Below | screenplay written by Kurt Martin; current film sources identify him as writer-director | none | stored writer disconnected; external director role is corroboration only |
| The System | screenplay and budget identify writer/director Dallas Jackson | Dallas Jackson writer, nationality unresolved | director remains disconnected |
| Trail Mates | written by Shawn Vance | none | public identity unresolved |
| Twilight of the Dead | budget director TBD; no named writer/director | none | no identity to ingest |
| Unconditional Love | screenplay uses `Christine Pfieffer` and Dan Stocke; deck uses Christine Stocke/Dan Stocke and director Rachel Winter | none | spelling/alias conflict requires reconciliation; roles disconnected |
| Underwater | screenplay/budget: writer/director Korstiaan Vandiver | none | identity resolved; no explicit nationality evidence sufficient |
| Werewolf | `Created by Stan Lee`; no named writer/director found | none | creator is not silently mapped to writer |
| White Feather | written by Matt Dority & Robert Leader | none | both identities unresolved |
| White Line Highway | written by Terence Winter; deck repeats writer; director TBD | none | repeated writer evidence disconnected |

**RUNTIME VERIFIED:** Only 3 projects lack documents: Braking Point, One Night Stand, and Spice Route. Five other projects have documents but no usable named writer/director: Artists of Cinema, Being Britney, Model Wars, Safehaven, and Twilight of the Dead.

## 2. Person identity and nationality/citizenship matrix

The table reports explicit public descriptors, not inferred citizenship. “UNKNOWN (E)” means the identity was sufficiently resolved but explicit nationality/citizenship evidence remained insufficient after diversified searching. “IDENTITY UNRESOLVED” means nationality assignment was not attempted beyond discovery leads because same-name risk remained.

| Person / role context | Identity support and external ID where established | Explicit nationality/citizenship evidence | Classification | Root cause in CineGlobe |
|---|---|---|---|---|
| Nick Vallelonga — 10DZ writer | project credit + established filmography | secondary biography: “American” | US — CORROBORATED | G/I; now persisted only at DISCOVERY grade |
| Christian Sesma — 10DZ writer/director | project roles + official/industry filmography | first-person interview: “1st gen Mexican American”; secondary biography: American | US — STRONG VERIFIED | A/B/G |
| Paul Sloan — 10DZ writer | project credit + role-correlated filmography | secondary biography: “American” | US — CORROBORATED | A/B/G |
| Phil Allocco — 5 LBS director / metadata author | budget + official bio/representation | no explicit nationality; birthplace/residence not used | UNKNOWN (E) | A/B/E |
| Timo Vuorensola — 97 Minutes / Going Places director | exact project credits + official site | official site says filmmaker “from Finland”; independent festival/industry source says Finnish | FI — STRONG VERIFIED | A/B/G |
| Mark Perez — Adam & Eve writer | project byline + official writer site | official site's “Average American Writer” descriptor is explicit but informal | US — CORROBORATED | A/B/G |
| Josh Sims — AMFAD writer | source name only; searches collide with unrelated reporter/athlete/author | no safe person match | IDENTITY UNRESOLVED | A/B/C |
| Jessica Sarah Flaum — AMFAD writer | official site identifies writer/filmmaker and project context | secondary biography: American | US — CORROBORATED | A/B/G |
| Marcus Dunstan — AMFAD director | exact project/budget + established director identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Marc Lhormer — Almost Perfect screenwriter | source credit + IMDb/project filmography | no explicit nationality; US locations are not nationality | UNKNOWN (E) | A/B/E |
| Carrie Regan — Almost Perfect underlying-work author | source `Based on` credit only | not researched for program role because this is underlying work, not a screenplay/personnel credit | NOT APPLICABLE TO CURRENT WRITER ROLE | correct non-promotion |
| John Stalberg Jr. — Bad Hombres director | budget short form + official film page/IMDb/title match | secondary biography: American | US — CORROBORATED | A/B/G |
| Sean-Michael Argo — Baron Samedi writer | exact unusual name + writer bibliography | only Arkansas origin/location wording | UNKNOWN (E) | A/B/E |
| Darin Scott — Baron Samedi director | source name collides with multiple film people; title corroboration insufficient | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| John Michael Kennedy — David / Drug Honey writer | exact source name but high same-name collision and no reliable title-context biography | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Cooper Hefner — Dead After Dark writer | exact project credit + established identity | secondary/reputable profile: American | US — CORROBORATED | A/B/G |
| Steve Bencich — FVD writer | screenplay, budget, deck + IMDb identity | Wikipedia says American; iQIYI lists United States | US — CORROBORATED | A/B/D/G |
| Mark Gantt — FVD director | budget, deck + official site/IMDb identity | IMDb biography says “American talent”; Wikipedia says American | US — STRONG VERIFIED | A/B/D/G |
| Jevon Whetter — Flash screenwriter | Film Independent profile confirms identity/project | no explicit nationality; residence/work not used | UNKNOWN (E) | A/B/E |
| Joan Considine Johnson — Flash screenwriter | source + IMDb/title context | no explicit nationality; Ohio birthplace not used | UNKNOWN (E) | A/B/E |
| Hayden Roush — Flash story | source + Tribeca project press material | no explicit nationality | UNKNOWN (E) | A/B/E |
| Dave Alan Johnson — Flash story | source + exact producer/writer filmography | AlloCiné/AdoroCinema and another industry database explicitly say American/US | US — STRONG VERIFIED | A/B/G |
| Robert Leader — Gifted / White Feather writer | searches collide and do not securely connect public person to both projects | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Matt Dority — Gifted / White Feather writer | source name; public results insufficiently role/title-specific | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Gabriel Mizrahi — Give or Take / Otherwise Engaged writer | two project sources establish local identity; weak public profile | no explicit nationality | UNKNOWN (E) | A/B/E |
| Suzanne Farwell — Give or Take writer / Otherwise Engaged writer-director | project/deck + official Disney producer bio | no explicit nationality | UNKNOWN (E) | A/B/E |
| Jonathan Hensleigh — Hightower writer | exact source + established screenwriter identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Mel Rogriguez III — Interference director | exact budget spelling; no reliable role/title match and possible typo | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Cynthia Mort — Jane Millen writer | exact source + established writer identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Brantley Gutierrez — LLS director/story | canonical name + project title + official/representation biographies | Moonlight Arts Collective: “Colombian-American” | CO/US cultural-national descriptor — CORROBORATED | D/G/I |
| Anthony Tambakis — LLS writer/story | canonical name + project + official publisher/IMDb identity | Première: `Nationalité Américain`; Apple TV: United States | US — STRONG VERIFIED | D/G/I |
| Lucy Score — Maggie underlying author | title/metadata + official publisher identity | not researched for program role because source is underlying book, not screenplay credit | NOT APPLICABLE TO CURRENT WRITER ROLE | correct non-promotion |
| Jennifer Bosworth — Replacements writer/story | project source + Macmillan official author identity | no explicit nationality | UNKNOWN (E) | A/B/E |
| Ryan Bosworth — Replacements story | project source + Macmillan relationship/context | no explicit nationality and limited independent identity | UNKNOWN (E) | A/B/E |
| Ice Cube — Rocky Mountain writer | exact source + official/major-industry identity | multiple reputable biographies explicitly American | US — STRONG VERIFIED | I; now persisted only at DISCOVERY grade |
| Joel Souza — Rust screenwriter | legal document + IMDb/Tribeca/project identity | AlloCiné, AdoroCinema and secondary biography explicitly American | US — STRONG VERIFIED | A/B/G |
| Matthew Carnahan — Serpent Girl writer | exact source + publisher/IMDb identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Taylor Sheridan — Sierra Madre screenwriter | exact source + official publisher/industry identity | multiple reputable biographies explicitly American | US — STRONG VERIFIED | A/B/G |
| Ian Mackenzie Jeffers — Sierra revisions | source + IMDb/title identity | AlloCiné-family industry page: American | US — CORROBORATED | A/B/G |
| James Keach — Sierra story | source + Cannes/IMDb identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Trevor Alpert — Sierra story | source + FilmFreeway/IMDb role context | project countries and residence are not person nationality | UNKNOWN (E) | A/B/E |
| Soyun Song — Sky director | source name but no reliable project-correlated public identity | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Susan Nanus — Terezin original writer | source + playwright/screenwriter profiles | no explicit nationality in sufficiently reliable source | UNKNOWN (E) | A/B/E |
| Emil Sher — Terezin original writer | source + official site/Canadian theatre encyclopedia | playwright database explicitly Canadian; official bio supplies Canadian career/location context but not citizenship | CA — CORROBORATED | A/B/G |
| Todd Komarnicki — Terezin revisions | source + IMDb/Amazon MGM identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Terence Winter — Terezin/Dale/White Line writer | repeated sources + Television Academy identity | secondary biography: American | US — CORROBORATED | A/B/G |
| Gabrielle “Gaby” Allan — Arrangement writer | source alias + IMDb alias + Television Academy/Atlantic Theater identity | elCinema explicitly says American/US | US — CORROBORATED | A/B/G/H |
| Jennifer “Jen” Crittenden — Arrangement writer | source alias + Television Academy/Atlantic Theater identity | secondary biography: American | US — CORROBORATED | A/B/G/H |
| Jonathan Bernstein — Cure writer | source + IMDb/title/official production identity | FILMSTARTS explicitly American | US — CORROBORATED | D/G/I; canonical identity exists, nationality missed |
| James Greer — Cure writer | source + IMDb/publisher/title identity | Wikipedia and FILMSTARTS explicitly American | US — STRONG VERIFIED | I; now persisted only at DISCOVERY grade |
| Nancy Leopardi — Cure director | budget + official production/IMDb identity | no reliable source explicitly states person nationality; US film origin/birthplace not used | UNKNOWN (E) | A/B/E |
| Our Lady J / Yona Speidel — Dale revisions | source alias + official current site confirms former name and identity | secondary biography: American | US — CORROBORATED; alias change VERIFIED | A/B/G/H |
| Kim Farrant — Little Utopia director | canonical row + deck/lookbook/budget + Screen Australia identity | AlloCiné says Australian; ACMI/Wikipedia describe Australian | AU — STRONG VERIFIED | G/I; current migration source weaker than result |
| Clara Salaman — Little Utopia writer | canonical row + screenplay/deck/lookbook + publisher/IMDb identity | AlloCiné says British; secondary biography says English | GB — STRONG VERIFIED | G/I; current migration source weaker than result |
| Max Botkin — Little Utopia producer | canonical migrated person/fact | existing US claim has secondary project evidence, not re-proven as legal citizenship | US — CORROBORATED CURRENT CLAIM | I/H |
| Rachel Winter — Little Utopia producer / Unconditional director | canonical producer plus deck director role + official company identity | Apple TV explicitly calls her American; secondary biography agrees | US — STRONG VERIFIED | A/B for director; I for current producer claim |
| Lee Jung-jae — Men writer/director | screenplay/lookbook + Korean Film Council identity | Korean Film Council/KOBIZ `Nationality: South Korea` | KR — AUTHORITY VERIFIED | A/B/G |
| Kurt Martin — Room writer / externally corroborated director | screenplay + IMDb/FilmInk/project identity | “living in Australia,” guild membership, education and production country do not prove nationality | UNKNOWN (E) | A/B/E |
| Dallas Wayne Jackson — System writer/director | screenplay/budget + IMDb/title identity | Letterboxd/TMDB-derived profile explicitly says American | US — CORROBORATED | D/G/I for writer; A/B for director |
| Shawn Vance — Trail Mates writer | source name; no sufficiently role/title-correlated public identity | no safe identity match | IDENTITY UNRESOLVED | A/B/C |
| Christine Pfeiffer Stocke — Unconditional writer | screenplay/deck alias + ISA profile ties Christine Pfeiffer Stocke to Dan | no explicit nationality | UNKNOWN (E/H) | A/B/E/H |
| Dan Stocke — Unconditional writer | screenplay/deck + ISA partner context | no explicit nationality | UNKNOWN (E) | A/B/E |
| Korstiaan “Kors” Vandiver — Underwater writer/director | screenplay/budget + IMDb/AFIDFF/VoyageATL identity | Atlanta origin and US residence/work do not prove nationality | UNKNOWN (E) | A/B/E |
| Stan Lee — Werewolf creator, not writer | exact creator credit + official/major-industry identity | multiple reputable biographies explicitly American | US — STRONG VERIFIED; not a current writer/director role | correct role separation |

### Classification totals

Across the 64 distinct names: **1 AUTHORITY VERIFIED, 13 STRONG VERIFIED, 23 CORROBORATED, 17 UNKNOWN after identity-resolved research, 8 IDENTITY UNRESOLVED, and 2 NOT APPLICABLE to a current writer/director role.** These are research classifications, not automatic program-eligibility determinations.

No case was classified `CONFLICTING` on nationality. The material conflicts found are identity/alias/credit-type conflicts (Darin Scott, Mel Rogriguez III, Christine Pfieffer/Pfeiffer Stocke, revision/current-credit status), which must be resolved before nationality can be consumed.

## 3. Source and search audit trail

### Tools available and used

| Tool/path | Used | Purpose / result |
|---|---:|---|
| Repository shell + `rg`, PostgreSQL read-only queries | yes | current code, 50-project inventory, 81 documents, six canonical people, schema and consumer reconciliation |
| `pdftotext` / `pdfinfo` | yes | title pages, budget headers, decks, lookbooks and incentive/legal text where extractable |
| DOCX/XLSX/PPTX ZIP/XML inspection | yes | Rust legal document, Werewolf budget, deck text and document metadata |
| local image rendering / visual inspection | yes | verified representative pages where text extraction/layout was ambiguous |
| macOS Vision OCR attempt | attempted | image-only deck OCR was too slow/non-deterministic; stopped without claiming absence from unreviewed images |
| public web multi-query search | yes | diversified identity-first queries across official sites, agencies, institutes, guild/awards, IMDb, publishers, festivals, established industry databases and corroborative biographies |
| Wikidata/current CineGlobe resolver | inspected/read-only evidence only | documented the current single-path limitation; never treated unreferenced `P27` as sufficient |
| CUA browser automation | no | it is a UI transport to the same public pages, not an independent search/evidence corpus; web retrieval exposed the material pages without authentication barriers |
| Google Drive connector | no | all authoritative project documents are already in canonical local storage; no external Drive corpus was identified by the repository or user |
| IMDbPro/authenticated film-industry connector | unavailable | public IMDb pages were used where accessible; no authenticated IMDbPro connector was installed |
| dedicated film-person/agency third-party connector | unavailable | none exposed in this environment |

### Query method actually applied

For every safely resolved writer/director, searches varied the exact name with `nationality`, `citizenship`, `biography`, role, project title, `official bio`, `agency`, `guild`, and discovered aliases. A discovered country adjective was used only to locate a source; the query term itself was never treated as evidence. Results were checked against role/project context before the nationality wording was accepted.

Representative exact sources supporting the material changes include:

- Brantley Gutierrez identity: [Strange Arcade](https://www.thestrangearcade.com/brantley-gutierrez); explicit wording: [Moonlight Arts Collective](https://moonlightartscollective.com/collections/brantley-gutierrez).
- Anthony Tambakis identity: [Simon & Schuster](https://www.simonandschuster.com/authors/Anthony-Tambakis/403466477); explicit nationality: [Première](https://www.premiere.fr/Star/Anthony-Tambakis); corroboration: [Apple TV](https://tv.apple.com/us/person/anthony-tambakis/umc.cpc.7aaqplqeoscws2o7jiusq2e7z).
- Kim Farrant identity: [Screen Australia](https://www.screenaustralia.gov.au/the-screen-guide/p/kim-farrant/6672); explicit descriptor: [AlloCiné](https://www.allocine.fr/personne/fichepersonne_gen_cpersonne%3D216085.html).
- Clara Salaman explicit descriptor: [AlloCiné](https://www.allocine.fr/personne/fichepersonne_gen_cpersonne%3D885481.html).
- Lee Jung-jae authoritative identity/nationality: [Korean Film Council / KOBIZ](https://www.koreanfilm.or.kr/eng/films/index/peopleView.jsp?peopleCd=10057315).
- Emil Sher identity: [official site](https://emilsher.com/about/); explicit corroborative nationality: [Doollee](https://www.doollee.com/PlaywrightsS/sher-emil.php).
- Gabrielle Allan identity/alias: [IMDb](https://www.imdb.com/name/nm1000302/), [Television Academy](https://www.televisionacademy.com/bios/gabrielle-allan), and [Atlantic Theater](https://atlantictheater.org/bio/gabrielle-allan/); explicit nationality: [elCinema](https://elcinema.com/en/person/2003609/).
- Jennifer Crittenden identity: [Television Academy](https://www.televisionacademy.com/bios/jennifer-crittenden) and [Atlantic Theater](https://atlantictheater.org/bio/jennifer-crittenden/).
- Jonathan Bernstein identity: [IMDb](https://www.imdb.com/name/nm0077080/) and [official production](https://www.showdownproductions.com/thecure); nationality: [FILMSTARTS](https://www.filmstarts.de/personen/79576.html).
- James Greer identity: [IMDb](https://www.imdb.com/name/nm0007079/) and [Grove Atlantic](https://groveatlantic.com/author/james-greer/); nationality: [FILMSTARTS](https://www.filmstarts.de/personen/79578.html).
- Kurt Martin identity: [IMDb](https://www.imdb.com/name/nm6662015/) and [FilmInk](https://www.filmink.com.au/public-notice/blacktop-international-acquires-worldwide-rights-to-kurt-martins-the-room-below/); neither establishes citizenship/nationality.
- Korstiaan Vandiver identity: [AFIDFF](https://afidff.org/en/about/our-team) and [VoyageATL](https://voyageatl.com/interview/meet-korstiaan-vandiver-blue-angel-entertainment-screenwriters-rx/); neither establishes citizenship/nationality.
- Joel Souza identity/nationality: [IMDb](https://www.imdb.com/name/nm3522996/bio/) and [AlloCiné](https://www.allocine.fr/personne/fichepersonne-578242/biographie/).
- Rachel Winter explicit descriptor: [Apple TV](https://tv.apple.com/us/person/rachel-winter/umc.cpc.5s5xsk64t3qijl422xwo1qwdf); identity/company: [Seine Pictures](https://www.seinepictures.com/).
- Our Lady J alias/current identity: [official site](https://ourladyj.com/).

For unresolved identities and `UNKNOWN (E)` cases, the same query family was run across public web results, IMDb where indexed, official-person/company sites, publisher/festival/guild/agency profiles, and project-title combinations. The absence conclusion is deliberately limited to “no sufficient explicit evidence located,” not “the person has no nationality.”

## 4. Mandatory-project findings

### Lips Like Sugar — why the prior search failed

**RUNTIME VERIFIED:** both people already existed, so the current resolver ran and stored `unresolved_no_match`. It relied on a role-correlated Wikidata lookup. It did not fan out to official bios, representation pages, publishers, established industry profiles, or alias/country-adjective query variants.

- **Brantley Gutierrez:** project identity is unambiguous. Moonlight Arts Collective explicitly says “Colombian-American.” Final: **CORROBORATED**, not legal proof of dual citizenship.
- **Anthony Tambakis:** identity is confirmed by his publisher and project filmography. Première explicitly lists American nationality and Apple TV lists United States. Final: **STRONG VERIFIED**.

The precise failure is **D (search too narrow)** followed by **G (found externally but not persisted)** and **I (consumer lacks evidence-tier handling)**. Wikidata silence/no-match was incorrectly treated as the end of research.

### F#K Valentine's Day

Three independent project sources identify Steve Bencich and Mark Gantt, but canonical state has zero people. Steve is **US CORROBORATED**; Mark is **US STRONG VERIFIED**. The first failure remains A/B (evidence not extracted/canonicalized). The broader search improves evidence quality but does not justify silently persisting legal citizenship.

### Little Utopia

Clara Salaman and Kim Farrant are strongly corroborated as British and Australian respectively. Current `ProjectPerson` values are confirmed and served, but were seeded through migration/approved facts, not reproduced by live source extraction plus tiered research. The values are substantively supported; the provenance/consumer path remains architecturally unsafe.

### Bad Hombres

- **Source extraction:** PARTIAL — the budget contains `Director: John Stalberg`; no adapter promotes it.
- **Person resolution:** PASS — exact project/title context resolves John Stalberg Jr.
- **Nationality research:** PASS at CORROBORATED level — explicit American secondary biography.
- **Canonical state:** BLOCKED/empty.
- **Downstream consumption:** BLOCKED because no `ProjectPerson` exists.

Public film credits naming writers Nick Turner and Rex New are useful discovery leads, but the current project document does not contain them. They must not be promoted as source-derived project facts without an explicit external-credit evidence policy.

## 5. Root causes and prior-audit misses

| Code | Finding | Scope |
|---|---|---|
| A — identity not extracted | screenplay layout, standalone byline, budgets, decks, lookbooks, legal files, metadata and revisions lack generic adapters | dominant all-project failure |
| B — identity not canonicalized | 64 names in source/canonical evidence versus 11 current person rows | dominant all-project failure |
| C — wrong-person risk | Darin Scott, John Michael Kennedy, Josh Sims, Robert Leader, Matt Dority, Mel Rogriguez III, Soyun Song, Shawn Vance | eight identities correctly remain unresolved |
| D — search too narrow | current resolver is Wikidata-only; demonstrated materially by both LLS people and FVD | confirmed pipeline defect |
| E — source quality insufficient | 17 safely identified people have only birthplace/residence/descent or no explicit nationality wording | legitimate unresolved cases |
| F — conflicting nationality | none established | not a current driver |
| G — nationality found but not persisted | all researched source-only people; LLS results especially material | architecture/review gap |
| H — schema cannot represent result | aliases, exact credit type, changing name, multiple citizenships, revisions/supersession | material architecture gap |
| I — consumer ignores evidence | 24 direct role consumers accept `primary_nationality` without evidence-tier gate; legacy path mixes residence | confirmed downstream defect |
| J — genuinely unknown | no claim is elevated to metaphysical “genuinely unknown”; only bounded research UNKNOWN is used | avoids false certainty |

The prior audit missed the LLS evidence because it audited the current resolver's output rather than the quality/completeness of its search strategy. It also centered FVD rather than enumerating all 50 projects and every document class.

## 6. Current canonical architecture and required minimum repair

### Current state

- `TalentProfile` stores name, a role, optional IMDb ID, one `primary_nationality`, evidence/status fields, and residencies.
- `ProjectPerson` is a thin project/person/role join with confirmation and notes.
- `ProjectFact` has source/version/location/confidence/review fields and can preserve factual provenance, but generic title-credit persistence does not use it.
- the title-page parser reads only the first 2,000 characters and same-line `Directed/Written/Screenplay by` patterns; it collapses writing credits to `writer`.
- budget/deck/lookbook/legal/metadata adapters do not promote named role claims.
- `talent_nationality_resolution.py` is post-identity and Wikidata-only.

### Minimum generic architecture

Preserve the existing entities, but introduce a structured, immutable project-person-role evidence claim (or an equivalent first-class extension) and one reconciliation service:

`SOURCE DOCUMENT/VERSION` → `EXACT PERSON/ROLE CLAIM` → `IDENTITY CANDIDATES + ALIASES` → `HUMAN/SAFE RESOLUTION` → `ProjectPerson` current view → `TIERED NATIONALITY/CITIZENSHIP CLAIMS` → `review/persistence` → `PROGRAM-SPECIFIC FACT CONSUMPTION`.

Each role claim must preserve document/version, page/location, exact wording, extraction method, exact role/credit type, attachment/model/current/revision status, confidence, canonical identity, and current/conflicting/superseded disposition. Adapters are required for screenplay layout, metadata, named budget headers/ATL lines, decks/lookbooks and legal documents. Unnamed budget roles remain non-identity evidence.

Nationality research should be a provider fan-out with a logged query plan, source-class normalization, explicit-wording capture, deduplication, and review thresholds. It must never infer citizenship from birthplace, residence, ethnicity or query terms.

### Persistence safety

- `AUTHORITY VERIFIED` / `STRONG VERIFIED`: eligible for reviewed canonical persistence.
- `CORROBORATED`: automatically surface with evidence; review before program use.
- `DISCOVERY ONLY`: lead only.
- `CONFLICTING`: explicit unresolved state.
- `UNKNOWN` / identity unresolved: remain unresolved.

Even a strong **nationality descriptor** is not automatically a statutory **citizenship** fact. The consuming program must declare the fact type and accepted evidence authority.

## 7. Multiple nationality/citizenship gap

**STATIC VERIFIED:** `TalentProfile` exposes one `primary_nationality`. Resolver evidence can contain multiple Wikidata `P27` values, but downstream uses only the selected primary. There is no first-class model for multiple citizenships/nationalities, effective dates, renunciation/change, evidence per status, or program-specific applicability.

The legacy role bridge then combines `primary_nationality` and confirmed residency codes into one set. This can make residence look like citizenship/nationality. Point-table paths have typed facts available, but the three writer/director point criteria below are still declared `EITHER`.

Required model: multiple dated `PersonJurisdictionStatusClaim`-equivalent facts with `status_type` (`CITIZENSHIP`, `NATIONALITY_DESCRIPTOR`, `RESIDENCY`, `CULTURAL_IDENTITY`), jurisdiction, effective interval, evidence tier, exact source wording, and conflict/review state. Do not choose an arbitrary primary for optimizer convenience.

## 8. Current downstream writer/director consumers

CURRENT HEAD still has **24 unique program slugs** with direct writer/director nationality/residency consumption: 21 legacy role requirements plus 3 cultural point tables.

| Program | Relevant current role rule | Current fact semantics / defect |
|---|---|---|
| `at_ofi_grants` | AT director required; writer alternative unknown | legacy merged nationality/residence; authority detail incomplete |
| `au_producer_offset` | AU director weighted 3/16; writer nationality not directly scored | registry itself warns writer treatment unknown |
| `ba_film_centre` | BA director required; writer alternative unknown | merged fact; incomplete authority detail |
| `ca_cmf` | CA director and writer required | code says nationality, program may require citizenship/status; no evidence gate |
| `ca_federal_cptc` | director/writer Canadian alternative, each 2/10 | alternative group represented, but single-primary/merged facts unsafe |
| `cz_czech_film_fund` | CZ director; writer alternative unknown | incomplete role scope |
| `de_dfff` | DE director weighted/creative test | exact weight is marked unknown |
| `dk_dfi_support` | DK director or writer alternative | merged fact, no authority-tier gate |
| `eu_media_fund` | EU/EEA director optional | EU membership support remains indeterminate in legacy evaluator |
| `fi_ses_grants` | FI director or writer; exact conjunction unknown | merged fact/incomplete rule detail |
| `fr_cnc_production` | EU/EEA writer/director; at least one French | code notes treaty/third-country uncertainty |
| `gr_gnf_grants` | GR director required | exact scope unknown |
| `hu_nfi_grants` | HU director required | exact scope unknown |
| `ie_section_481` | IE director optional | should not be treated as mandatory eligibility |
| `nl_hbf` | NL/treaty director or writer | elected treaty and exact alternative scope unresolved |
| `no_nfi_grants` | NO director or writer | merged fact, no evidence-tier gate |
| `nordic_ftvf` | Nordic director/producer | `None`/treaty-country semantics remain indeterminate without elected partner |
| `pl_pisf_grants` | PL director or Polish-language screenplay/writer | language and person nationality are materially different facts |
| `pt_ica_grants` | PT director required | exact scope unknown |
| `se_goteborg_fund` | SE director required, writer optional/unknown | regional/national rule detail incomplete |
| `uk_avec` | GB director and writer each 1/31 | accepts weak `primary_nationality` without evidence authority |
| `at_fisa_plus` | director and writer each 2 points, Austrian/EEA/CoE | point-table criterion `fact_kind=EITHER`; incomplete typed distinction |
| `fr_trip` | combined director/screenwriter nationality criterion, 2 points | modeled on director slot only; `EITHER`; writer not separately consumed |
| `no_film_incentive` | combined director/screenwriter/author criterion, 2 points | modeled on director slot only; `EITHER`; writer/author not separately consumed |

All 24 are exposed to weak-evidence risk because the source function does not check nationality evidence status/confidence. The 21 legacy rules additionally mix nationality and residency. Multiple actual citizenships are not faithfully represented. Treaty-person nationality wiring outside this 24-program set remains partial and must not be described as completed by this audit.

## 9. Producer-question impact

The current generic question builder asks for four primary roles (writer, director, producer, lead cast); a named person without nationality produces a nationality question instead of a name question.

**STATIC VERIFIED + RUNTIME DB VERIFIED:** current state yields **195 producer-facing personnel questions**:

- 44 projects with no `ProjectPerson`: 4 each = 176;
- 10 Double Zero: director, producer and cast names = 3;
- Lips Like Sugar: writer nationality, director nationality, producer name, cast name = 4;
- Rocky Mountain: director, producer and cast names = 3;
- The Cure: Jonathan Bernstein nationality plus director, producer and cast names = 4;
- The Little Utopia: cast name only = 1.
- The System: Dallas Jackson nationality plus director, producer and cast names = 4.

Source evidence can safely populate candidates for **35 project writer slots** and **17 project director slots**. Six project writer slots and two director slots are now canonical, so a generic ingestion/reconciliation repair could remove or convert **44 current missing-name questions** (29 writer + 15 director). A name question normally becomes a nationality question until evidence is reviewed; it does not automatically disappear.

At the generic UI-question layer, up to **10 questions** have an `AUTHORITY VERIFIED` or `STRONG VERIFIED` role/person result that could become fully resolved after the architecture, evidence review, and safe persistence are implemented. Corroborated results should surface for review, not suppress a legitimate producer decision. Producer, cast, attachment/current-credit, alias conflict, treaty election and program-specific citizenship questions remain legitimate.

## 10. Remaining blocked items

1. Eight person identities cannot be safely resolved from present source/public context.
2. Seventeen resolved people lack sufficiently explicit nationality/citizenship evidence.
3. Image-heavy decks were not exhaustively visually/OCR audited; no absence claim is made for uninspected images.
4. Current schema cannot safely preserve aliases, exact credit taxonomy, claim conflicts/supersession, multiple citizenships or dated status.
5. Current consumer cannot distinguish nationality, citizenship and residence in the 21-program legacy path.
6. Current nationality resolver has no diversified provider/query strategy and no source-authority threshold.
7. Program-specific evidence standards are not declared, so even strong public nationality descriptors cannot automatically answer legal citizenship gates.
8. The clean direct import of `canonical_production_view` encountered the current `executable_jurisdiction_registry` / `program_rate_rules_worldwide` circular-import order; the 197 count was therefore verified from the exact static question-builder logic plus live DB rows, not represented as a successful end-to-end HTTP invocation.

## Final gate

**ALL PROJECTS AUDITED — RUNTIME VERIFIED**

**IDENTITY/NATIONALITY SEARCH QUALITY DEFECT — CONFIRMED**

**SAFE NARROW IMPLEMENTATION — BLOCKED BY MATERIAL GENERIC ARCHITECTURE**

**PRODUCTION CODE CHANGED — NO**
