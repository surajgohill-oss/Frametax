# Creative Identity and Nationality Pipeline Audit — Codex

**Audit date:** 2026-09-03 (America/Los_Angeles)

**Repository:** `/Users/Suraj/cineglobe-frametax` (`surajgohill-oss/Frametax`)

**Application:** `/Users/Suraj/cineglobe-frametax/frametax2`

**Branch:** `claude/audit-frametax-features-NZcX5`

**Audited HEAD:** `36ce645fd664b3e7d739ac8d1e6b7af2ac072452`

**Remote:** `https://github.com/surajgohill-oss/Frametax.git`

**Mode:** architecture and gap audit; no production-code, database, optimizer, doctrine, or UI changes

## Verification legend

- **STATIC VERIFIED** — established from current repository code, migrations, or immutable project documents.
- **RUNTIME VERIFIED** — established from the current database, service execution, or a direct parser/resolver invocation.
- **BLOCKED** — the current architecture cannot complete the chain without material implementation or stronger evidence.

## Executive conclusion

**STATIC VERIFIED / RUNTIME VERIFIED:** F#K Valentine's Day (FVD) source materials explicitly identify **Steve Bencich** as writer and **Mark Gantt** as director. The current canonical producer-facing state contains neither person.

The first failure is extraction/ingestion, not the API or UI:

1. the script title-page extractor recognizes only a same-line `Written by`, `Screenplay by`, or `Directed by` pattern, while the FVD title page places `by` and `Steve Bencich` on separate lines;
2. the budget parser creates accounting line items but discards document-header identity metadata, including `Director: Mark Gantt` and `Writer: Steve Bencich`;
3. the deck is retained as a binder/document asset but has no text-to-role ingestion path, despite explicit writer and director pages.

When a supported title-page pattern is present, CineGlobe does persist and serve a person through `TalentProfile` + `ProjectPerson`. That path is narrow and does not preserve the evidence structure required here: exact writing-credit type, exact source wording/location, structured confidence, conflicting claims, role status, aliases, or safe cross-role identity resolution. The provenance for generic title-page credits is only free text in `notes`.

**Implementation decision: BLOCKED for lead reconciliation.** A regex-only patch would recover only the FVD writer, leave the independently evidenced director and the budget/deck pathways disconnected, collapse writing-credit semantics, and continue persisting notes-only provenance. A complete generic repair requires a material person-role-evidence and reconciliation boundary plus source adapters. Under the task's implementation gate, no partial production change was made.

## 1. Repository and runtime gate

| Gate | Result | Status |
|---|---|---|
| Canonical repository | `/Users/Suraj/cineglobe-frametax` | STATIC VERIFIED |
| Shared branch | `claude/audit-frametax-features-NZcX5` | STATIC VERIFIED |
| Audited local/remote SHA | `36ce645fd664b3e7d739ac8d1e6b7af2ac072452` | STATIC VERIFIED |
| Database | current application database reachable on `localhost` | RUNTIME VERIFIED |
| Schema revision | Alembic `0071` | RUNTIME VERIFIED |
| Existing worktree state | pre-existing untracked files only; no tracked modification at audit start | STATIC VERIFIED |

The current canonical path was inspected before considering a repair. The relevant components are:

- `ScreenplayDocument` / `DocumentVersion` for screenplay text and versioned source identity;
- `BudgetDocument` / `BudgetLineItem` for parsed accounting data;
- production binder/document records for other uploaded material;
- `TalentProfile` for a role-coupled real-person record and nationality fields;
- `ProjectPerson` for project-to-person role association;
- `ProjectFact` for structured, version-addressable factual provenance;
- `Character` for fictional characters, correctly separate from real people;
- canonical state/evaluation services and the frontend production-details renderer.

No parallel fact or person system was created.

## 2. FVD actual source evidence

### 2.1 Screenplay

| Item | Evidence |
|---|---|
| File | `F#K Valentine's Day- pdf.pdf` |
| SHA-256 | `4caea6619bcadf93f4e392780099b4922d67d71ca0bbc1ad87f2a9fe70009611` |
| Length | 101 pages |
| Document version | `d25b035b-dc6f-471a-a611-6ed397444889` |
| Source location | page 1 / extracted-text opening |
| Exact extracted layout | `F#<K VALENTINE'S DAY` then standalone `by` then `Steve Bencich` |
| Current parser result | `derive_title_page_credits(raw_text) == {'director': [], 'writer': []}` |
| Drop point | `_CREDIT_LINE_RE` requires role label, `by`, and name on the same line |
| Status | STATIC VERIFIED / RUNTIME VERIFIED |

The document is extracted and in `SCRIPT_PARSED` state; its stored raw text is 101,566 characters. This is not an OCR or file-availability failure. It is a title-page pattern limitation.

The screenplay establishes a document byline for **Steve Bencich**. It does not establish the director.

### 2.2 Budget

| Item | Evidence |
|---|---|
| File | `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` |
| SHA-256 | `253e80e987a0aa3c06110dcbc5f6c99fd20042579603a94e29039c1e0a72eaa1` |
| Document version | `cf33eae1-aa4e-4e4e-80d2-ce737f5a373e` |
| Source location | page 1 header |
| Exact extracted values | `Director: Mark Gantt`; `Writer: Steve Bencich` |
| Current parser output | 34 `BudgetLineItem` rows; no writer/director person or fact |
| Drop point | `_route_budget` parses accounting rows only; header identity metadata is not promoted and `BudgetDocument.raw_text` is null |
| Status | STATIC VERIFIED / RUNTIME VERIFIED |

The named header is identity evidence, unlike an unnamed line such as `DIRECTOR $150,000`. The current parser does not distinguish or preserve either case as role evidence.

### 2.3 Deck

| Item | Evidence |
|---|---|
| File | `Fck Valentines Day - - 2.9.24 deck.pdf` |
| SHA-256 | `09913b6899fd743b3d66f249a94381a0294f46ea768fe74eed38da795105413a` |
| Length | 23 pages |
| Document version | `cb0faa80-4a62-4e93-95e1-3f30cc6bda5b` |
| Writer evidence | page 20: `Steve Bencich - writer/producer` |
| Director evidence | page 22: `Mark Gantt - Director` |
| Current parser output | binder/artwork metadata only; no text/role facts |
| Drop point | material routing supports screenplay and budget; deck content is a deliberate no-op |
| Status | STATIC VERIFIED / RUNTIME VERIFIED |

### 2.4 Current structured state

FVD currently has:

- zero `ProjectPerson` rows;
- zero relevant writer/director/nationality `ProjectFact` rows;
- empty people arrays from `build_generic_pkg_and_economics` and the project record;
- four generic missing-input questions: writer name, director name, cast name, and producer name.

**RUNTIME VERIFIED:** The source documents contain both identities, but neither reaches canonical project state.

## 3. Current end-to-end failure chains

### Writer — Steve Bencich

`screenplay page 1 (byline)` → extracted `ScreenplayDocument.raw_text` **passes** → same-line title-credit regex **fails** → `persist_title_page_credits` receives no writer → no `TalentProfile` / `ProjectPerson` / `ProjectFact` → canonical role bridge returns no writer → API state returns no writer → frontend truthfully renders no writer and asks for the missing name.

Independent corroboration exists in the budget header and deck, but neither document type has an identity adapter. Therefore both fallback chains stop before role extraction.

### Director — Mark Gantt

The screenplay has no director credit. The director appears in the budget and deck:

`budget page 1 header` / `deck page 22` → document is stored **passes** → content-to-role extraction for this source type **absent** → no role evidence/reconciliation → no `TalentProfile` / `ProjectPerson` / `ProjectFact` → canonical role bridge returns no director → API state returns no director → frontend truthfully renders no director and asks for the missing name.

The API and UI are not the first or causal failure points.

## 4. Existing canonical person and role architecture

| Entity/path | What it supports | Material limitation |
|---|---|---|
| `TalentProfile` | real-person name, one role, optional IMDb identity, primary nationality, nationality evidence/confidence, residency/guild data | identity is role-coupled; no alias/normalized identity entity; the same person in multiple roles can be duplicated |
| `ProjectPerson` | project association, role, confirmation flag, notes | no structured source/version/location, source wording, confidence, role status, evidence status, uniqueness, or conflict history |
| `ProjectFact` | structured source type, document version, location, confidence, review status; one current row per fact key | flexible and suitable for facts, but generic title-credit persistence does not use it; one-current-row shape alone cannot preserve competing role claims |
| `Character` | fictional character identity | correctly separate; must not be reused for creatives |
| `ProductionAssumption` | schedule/scale/stage/pages-per-day assumptions | not a personnel store |
| `ProjectActivity` | intended immutable project history | current application person edits do not write it |

### Current title-credit behavior

`backend/app/services/script_analysis_service.py`:

- scans the first 2,000 characters;
- recognizes only same-line `Directed by`, `Written by`, and `Screenplay by`;
- maps `Written by` and `Screenplay by` to the same generic `writer` role;
- does not support standalone title-page `by`, `Story by`, `Teleplay by`, or `Based on` taxonomy;
- skips an entire role if any `ProjectPerson` already occupies it;
- creates a new `TalentProfile` and `ProjectPerson` when matched;
- records source provenance only in free-text notes, not a structured source link;
- preserves no conflicting claim.

This is a narrow canonical-and-consumed path, not a general creative-identity evidence pipeline.

## 5. Source extraction matrix

| Source / evidence form | Current result | Correct generic treatment | Classification |
|---|---|---|---|
| Same-line screenplay `Written by NAME` | extracted as generic writer | preserve exact `WRITTEN_BY` wording and map to a canonical writing role | CANONICAL_AND_CONSUMED, but lossy |
| Same-line screenplay `Screenplay by NAME` | extracted as generic writer | preserve `SCREENPLAY_BY` separately from other writing credits | CANONICAL_AND_CONSUMED, but lossy |
| Same-line screenplay `Directed by NAME` | extracted as director | preserve source wording, page/version, and status | CANONICAL_AND_CONSUMED, but provenance-poor |
| Standalone screenplay `by` followed by name | not extracted | title-page adapter with layout-aware evidence | OPTIMIZER_CAPABILITY_MISSING |
| `Story by`, `Teleplay by`, `Based on` | not extracted | distinct credit types; never silently collapse | OPTIMIZER_CAPABILITY_MISSING |
| Named budget header/ATL entry | not extracted | create weaker, named modeled-role evidence with exact source | EXISTS_BUT_DISCONNECTED |
| Unnamed budget role/cost | not extracted | remain non-identity evidence | CORRECT NON-EXTRACTION |
| Explicit deck role page | not extracted | document adapter preserving attachment wording/status | EXISTS_BUT_DISCONNECTED |
| Producer-confirmed person input | served via `ProjectPerson` | retain as high-precedence confirmed evidence without deleting alternatives | CANONICAL_AND_CONSUMED |
| Structured migrated facts | can seed people/facts, as in Little Utopia | retain versioned provenance and reconciliation | CANONICAL_AND_CONSUMED for migrated cases |

## 6. Required evidence reconciliation boundary

Precedence must be role-specific and must choose a current canonical view without destroying evidence. A safe initial policy is:

1. explicit producer-confirmed project person/fact;
2. explicit deck/project metadata describing an attached person;
3. screenplay title-page writing credit for the document's writing-credit claim;
4. named budget ATL/header association as modeled production evidence;
5. machine inference only as an unresolved candidate, never a confirmed fact.

Important qualifications:

- a screenplay title page is strong evidence of that document's writing credit, but not proof of the current contractual credit;
- a deck may be stronger for an attached director than a screenplay that says nothing about direction;
- a budget association may represent a modeled hire rather than an attachment;
- later producer confirmation should supersede the served view but retain earlier source claims;
- material conflicts affecting qualification must be surfaced as `DECISION REQUIRED`, not overwritten.

The missing generic boundary is a structured **project-person-role evidence claim** (or an equivalent extension plus immutable claim history) containing at minimum:

- canonical person identity and safe alias/name normalization;
- project role and exact credit type (`WRITER`, `SCREENWRITER`, `STORY_BY`, `TELEPLAY_BY`, `DIRECTOR`);
- exact source wording;
- source document version and source location;
- status (`ATTACHED`, `ASSUMED/MODELED`, `CONFIRMED`, `UNKNOWN`) only when supported;
- confidence/evidence status and extraction method;
- current/superseded/conflicting disposition;
- reconciliation link to the canonical served person-role.

Simple case folding is appropriate for candidate matching, but `Jane Smith`, `JANE SMITH`, and `Jane A. Smith` must not be merged merely by similarity. Stable external identity, explicit alias evidence, or human resolution is required for ambiguous matches.

## 7. Nationality and citizenship architecture

### Current mechanism

`TalentProfile` contains:

- `primary_nationality`;
- nationality confidence/status fields;
- structured nationality evidence introduced by the current provenance migration;
- residency and guild information.

`talent_nationality_resolution.py` performs a post-identity Wikidata lookup. It requires a role-correlated occupation and reads `P27` (country of citizenship). It does **not** convert birthplace (`P19`) or residence into citizenship. Multiple `P27` values can be retained in evidence, but downstream qualification currently consumes only the single `primary_nationality` value.

### FVD research result

The resolver was invoked read-only for the two evidenced people; nothing was persisted.

| Person | Resolved identity | Claim | Exact source | Claim quality | Canonical audit result |
|---|---|---|---|---|---|
| Steve Bencich | Wikidata `Q7611920` | `P27 = Q30` (United States country of citizenship) | `https://www.wikidata.org/wiki/Q7611920` | normal-rank statement; zero references; no qualifiers | `US — DISCOVERY ONLY` |
| Mark Gantt | Wikidata `Q13365843` | `P27 = Q30` (United States country of citizenship) | `https://www.wikidata.org/wiki/Q13365843` | normal-rank statement; zero references; no qualifiers | `US — DISCOVERY ONLY` |

Retrieval date: 2026-09-03 America/Los_Angeles (resolver UTC timestamps fall on 2026-09-04).

Public biography results describing the people as American are corroborative discovery sources, not authority-locked citizenship proof. The specific Wikidata citizenship statements are unreferenced. Neither claim is sufficient for legal/program eligibility without an acceptable explicit biography, official/agency/guild source, project confirmation, or other authoritative evidence.

Accordingly:

- the truthful current canonical result remains **UNKNOWN / unresolved for authority-locked eligibility**;
- no inference was made from name, appearance, language, birthplace, residence, ethnicity, or cultural identity;
- neither nationality was written to the database;
- the resolver can automatically propose and surface the `US` discovery claim, but it must not silently decide qualification.

### Material nationality gaps

1. Resolver evidence does not preserve statement references, rank/date semantics, source classification, or effective/current citizenship status sufficiently for legal reliance.
2. The canonical role bridge ignores nationality confidence/evidence tier and consumes `primary_nationality` directly.
3. Multiple citizenships may be stored in evidence but only one first-listed ISO code is used downstream.
4. No canonical mechanism models changed citizenship or program-rule-specific citizenship relevance.
5. Identity must first exist; FVD has no person rows, so even discovery does not run through the normal persisted chain.

Any downstream use must be `AUTHORITY LOCKED`: doctrine decides whether and how citizenship matters. An explicit, sufficiently authoritative uncontested claim may be `AUTOMATIC + SURFACE`; discovery-only or conflicting evidence must not alter economics.

## 8. Current downstream consumers

The live canonical registries contain 24 unique program slugs with direct writer/director role-nationality or role-residency consumption.

### Direct role requirements (21)

`at_ofi_grants`, `au_producer_offset`, `ba_film_centre`, `ca_cmf`, `ca_federal_cptc`, `cz_czech_film_fund`, `de_dfff`, `dk_dfi_support`, `eu_media_fund`, `fi_ses_grants`, `fr_cnc_production`, `gr_gnf_grants`, `hu_nfi_grants`, `ie_section_481`, `nl_hbf`, `no_nfi_grants`, `nordic_ftvf`, `pl_pisf_grants`, `pt_ica_grants`, `se_goteborg_fund`, `uk_avec`.

### Cultural point tables with writer/director criteria (3)

`at_fisa_plus`, `fr_trip`, `no_film_incentive`.

The canonical evaluation path reads `ProjectPerson`/`TalentProfile` through `canonical_role_qualification_bridge.py`; personnel participates in the evaluation fingerprint and can create disclosures/recommendation gates. This path is connected for persons that exist.

Legacy/intelligence maps also reference writer/director facts for French, Canadian, Australian, and UK content tests, but they are not counted again as distinct program identities.

### Treaty limitation

The treaty bridge discusses personnel-nationality-discovered candidate jurisdictions, but the current bilateral treaty evaluation entry points do not directly consume project personnel nationality. The freeze manifest records personnel-nationality-to-treaty eligibility as deferred/partially implemented. Therefore direct treaty consumption is **BLOCKED**, not runtime-verified.

## 9. API and producer-facing state

For a person that exists, the active chain is:

`ProjectPerson + TalentProfile` → `canonical_role_qualification_bridge.py` / canonical evaluation → `build_generic_pkg_and_economics` people payload → `GET /projects/{id}/state` → `useCineGlobe.js` → `Overview.jsx` → `ProductionDetails.jsx`.

The frontend renders and edits backend canonical values; it does not independently infer or recompute writer/director identity. The generic project-record people payload is thinner than state and omits some confirmation/provenance detail, but this is not the cause of FVD's absence.

Permission behavior required after repair:

- uncontested explicit role evidence: `AUTOMATIC + SURFACE`;
- producer-confirmed fact: `AUTOMATIC` / canonical current fact;
- material conflicting role evidence affecting economics: `DECISION REQUIRED`;
- discovery-only nationality: surface as unresolved; do not apply to eligibility;
- sufficiently authoritative explicit citizenship: `AUTOMATIC + SURFACE`, with doctrine-controlled use.

## 10. Cross-project verification

| Project | Source pattern | Current result | Status |
|---|---|---|---|
| F#K Valentine's Day | multiline screenplay byline; named budget header; explicit PDF deck role pages | all three source paths fail to produce people; four missing-input questions | RUNTIME VERIFIED failure |
| Little Utopia | scan-only script; lookbook; PPTX deck | script parsing is blocked; lookbook/PPTX explicitly identify writer Clara Salaman and director Kim Farrant, but current people/facts were seeded by migration `0063`, not extracted live | RUNTIME VERIFIED; generic document path not proven |
| Lips Like Sugar | same-line `Directed by Brantley Gutierrez`, `Written by Anthony Tambakis`, plus `Story by ...`; abbreviated named budget headers | same-line director/writer are persisted and served; `Story by` taxonomy is dropped; budget identities are not extracted; nationality remains unresolved | RUNTIME VERIFIED partial pass |

Little Utopia evidence inspected:

- script `The Little Utopia 1_30_26.pdf`, SHA-256 `c5213c9ced713e071a21647a4c08cec7914f18cf6bdd1432c33d4c00ff4038c0`, is scan-only and currently `SCRIPT_PARSE_BLOCKED_SCAN_ONLY`;
- lookbook text identifies screenwriter Clara Salaman and director Kim Farrant;
- slide-deck XML explicitly says `WRITTEN BY Clara Salaman` and `DIRECTED BY Kim Farrant`;
- served people come from the project migration, demonstrating a canonical destination but not a generic deck extractor.

Lips Like Sugar evidence inspected:

- script SHA-256 `c6735c1a3826e6b42e33c0f15b39c66beb9d8163086c4f2c57acb0624dfec318`;
- page 1 has same-line `Directed by Brantley Gutierrez`, `Written by Anthony Tambakis`, and `Story by Brantley Gutierrez & Anthony Tambakis`;
- the runtime extractor returns the director and generic writer only;
- budget SHA-256 `37814d8b33358fd7bf52331bb969f7e3b78dc6e61b49ad363e96bd3a001b8af7` contains abbreviated named headers but does not feed identity.

This cross-project result proves that the served path works only after a narrow match or migration. It does not provide a generic script/budget/deck evidence pipeline.

## 11. Explicit audit answers

1. **Does CineGlobe currently extract screenplay title-page writer credits?**

   **PARTIAL — STATIC/RUNTIME VERIFIED.** Only same-line `Written by` and `Screenplay by`; it misses FVD's multiline `by` and does not preserve writing-credit types.

2. **Where are those facts stored?**

   In a newly created `TalentProfile` plus `ProjectPerson`; source information is only in notes. Generic title-page persistence does not create a structured `ProjectFact`.

3. **Are they actually reaching canonical project state?**

   **YES when matched**, as Lips Like Sugar proves. **NO for FVD** because no match/person is created.

4. **Does CineGlobe currently extract named director/writer ATL budget lines?**

   **NO.** It parses accounting rows, not named header/role identity evidence.

5. **Does it ingest director/writer identities from decks?**

   **NO.** Decks are stored but not routed through content/role extraction.

6. **Is there a canonical real-person/project-role entity or only ad hoc fields?**

   A minimal canonical pair exists: `TalentProfile` + `ProjectPerson`. It is insufficient for source claims, exact credit types, role status, conflicts, aliases, and safe deduplication.

7. **Why is FVD missing writer/director today?**

   The writer's script layout is unsupported; budget-header and deck role adapters do not exist. All three explicit evidence paths stop before canonical persistence.

8. **What failure class is this?**

   Primary: extraction/ingestion failure. Secondary: canonical evidence-schema, source-precedence, and reconciliation limitations. It is not an API or UI consumption failure.

9. **Does nationality/citizenship already exist in the schema?**

   **YES**, including a primary value and provenance/confidence evidence, but multi-citizenship and authority-gating consumption are incomplete.

10. **Which current jurisdiction/program rules require those facts?**

    The exact 24 unique direct consumers are listed in Section 8. Direct treaty-personnel wiring is not complete.

11. **Can explicit nationality facts be automatically populated with provenance?**

    Mechanically yes after person creation, but current Wikidata discovery evidence is not sufficient by itself for authority-locked eligibility. Strong explicit evidence may be `AUTOMATIC + SURFACE`; unknown remains unknown.

12. **What unresolved architecture/code work is required?**

    A structured project-person-role claim/history boundary; exact credit taxonomy; script, budget, and deck adapters; safe person normalization/aliases; role-specific reconciliation; API provenance/conflict exposure; nationality authority/confidence gates; multiple-citizenship consumption; and completed treaty bridging.

13. **How many unnecessary producer questions could this eliminate?**

    FVD currently has four questions. Recovering identity alone replaces two name questions with two nationality questions, so the total remains four. Recovering both identities **and** accepting sufficiently authoritative nationality evidence would reduce the current total from four to two (cast and producer): at most **two eliminated**. The discovery-only claims found in this audit do not meet that acceptance threshold, so the actual runtime count is unchanged.

## 12. Implementation and test decision

**No production implementation was performed.** The complete repair is not small and safely contained in the existing architecture. It requires schema/migration and reconciliation decisions. A partial FVD-friendly regex would produce a false success while leaving director evidence, other document types, credit taxonomy, conflicts, and authority gating broken.

Consequently:

- production code changed: **NO**;
- database/project data changed: **NO**;
- optimizer economics changed: **NO**;
- jurisdiction doctrine changed: **NO**;
- frontend changed: **NO**;
- tests added or run: **NONE** (the task's test section applies if implementation occurs).

Runtime verification consisted of read-only database inspection, canonical service execution, pure title-credit parser invocations, PDF/PPTX text inspection, and read-only nationality resolver/source inspection. No runtime success is claimed for the missing generic architecture.

## 13. Remaining blockers and recommended implementation order

1. Approve a canonical person-role-evidence/history design that extends the existing `TalentProfile` / `ProjectPerson` / `ProjectFact` model without creating a parallel truth system.
2. Preserve writing-credit taxonomy and role/source wording.
3. Add generic screenplay-layout, named-budget, and supported-deck adapters that emit claims, not final truth.
4. Implement role-specific precedence, conflict preservation, and safe alias resolution.
5. Expose current claim, provenance, confidence, and material conflicts through canonical API state.
6. Gate nationality consumption by evidence authority/confidence; preserve and evaluate all documented citizenships.
7. Complete the already-deferred personnel-nationality-to-treaty connection.
8. Then add the focused regressions enumerated in the task, including FVD, Little Utopia, and Lips Like Sugar.

Until those decisions are made, the truthful status is:

- FVD source identity evidence: **RUNTIME VERIFIED**;
- current generic script/budget/deck-to-role pipeline: **BLOCKED / incomplete**;
- FVD nationalities: **discovery-only; authority-locked result UNKNOWN**;
- canonical UI rendering for existing persons: **RUNTIME VERIFIED**;
- complete generic repair: **BLOCKED pending lead architecture reconciliation**.
