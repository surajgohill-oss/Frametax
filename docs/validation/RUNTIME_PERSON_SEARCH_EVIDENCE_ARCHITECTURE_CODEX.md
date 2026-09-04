# Runtime Person Search and Evidence Architecture — Codex

**Audit date:** 2026-09-04 (America/Los_Angeles)  
**Repository:** `surajgohill-oss/Frametax`  
**Application:** `frametax2/`  
**Branch:** `claude/audit-frametax-features-NZcX5`  
**Mode:** read-only runtime/search and architecture audit; artifact-only change

## Verification legend

- **STATIC VERIFIED** — established from current repository code, configuration names, schema, migrations, tests, or prior accepted audit evidence.
- **RUNTIME VERIFIED** — established by a harmless live call through the application's current client code. No database record was written.
- **BLOCKED** — the requested capability cannot be completed safely by the current architecture.

## Executive answer

**STATIC VERIFIED: CineGlobe cannot perform general web search today.** The active `frametax2` product has two configured and live special-purpose public-network clients: Wikidata person/entity lookup and `open.er-api.com` FX retrieval. Neither can discover or read arbitrary public biography pages.

The Bridge defines `ModelRequest.allow_web_search`, and its requirements workflow sets the flag to `True`, but the Anthropic, OpenAI, and Gemini adapters do not translate it into a provider search tool, grounding setting, or URL-fetch capability. All three Bridge credentials are currently empty. The flag therefore has no runtime effect.

**RUNTIME VERIFIED:** on 2026-09-04, the application resolver matched Lee Jung-jae to Wikidata entity `Q491318` and returned `P27=Q884`, South Korea (`KR`). The application FX client returned a successful USD payload containing 166 currencies from `open.er-api.com`.

**BLOCKED:** safe, automated, multi-source person nationality/citizenship research is not a narrow wiring task. The current resolver searches one structured provider, persists a discovery-grade result into the same untyped `primary_nationality` field consumed by qualification logic, arbitrarily selects the first listed citizenship, and lacks claim-level evidence records. The required repair is **MATERIAL ARCHITECTURE**. No production code was changed.

## 1. Scope and prior evidence

This audit used the current repository/runtime state and treated these prior artifacts as evidence rather than repeating their 50-project research:

- `docs/validation/CREATIVE_IDENTITY_NATIONALITY_PIPELINE_CODEX.md`
- `docs/validation/CREATIVE_IDENTITY_NATIONALITY_ALL_PROJECTS_CODEX.md`

The prior audits establish that useful person evidence is distributed across project documents and diverse public sources, that same-name and alias problems are real, and that the requested acceptance cases require distinctions the current Wikidata-only resolver cannot express.

## 2. Runtime internet/search capability inventory

| Class | Service | Code path | Purpose | Scope | Required configuration | Config present? | Enabled? | Live? | Current consumer |
|---|---|---|---|---|---:|---:|---:|---|
| **A — CONFIGURED + LIVE VERIFIED** | Wikidata MediaWiki search + entity JSON | `frametax2/backend/app/services/talent_nationality_resolution.py` | Name search, occupation corroboration, `P27` citizenship and country `P297` ISO lookup | Special-purpose structured lookup | None; URL, timeout and user-agent are constants | yes | yes | **RUNTIME VERIFIED** | `analyze_project_script()` → `enrich_project_personnel()` for unconfirmed, not-yet-attempted project people |
| **A — CONFIGURED + LIVE VERIFIED** | ExchangeRate-API open endpoint (`open.er-api.com`) | `frametax2/backend/app/services/fx_refresh.py` | Daily USD exchange-rate snapshot | Special-purpose FX | None for the active endpoint | yes | yes | **RUNTIME VERIFIED** | project-state freshness path and persisted `fx_rates` snapshot |
| **C — WIRED BUT NOT CONFIGURED** | Anthropic Messages API | `frametax2/backend/app/bridge/adapters/anthropic_adapter.py` | Bridge review/research model invocation | General LLM, but **no web-search tool wired** | `ANTHROPIC_API_KEY`; `BRIDGE_ANTHROPIC_ENABLED` | key name present; value absent | switch true | not probed: no credential | Bridge dispatch/review workflows, not person resolution |
| **C — WIRED BUT NOT CONFIGURED** | OpenAI Responses API | `frametax2/backend/app/bridge/adapters/openai_adapter.py` | Bridge review/research model invocation | General LLM, but **no web-search tool wired** | `OPENAI_API_KEY`; `BRIDGE_OPENAI_ENABLED` | key name present; value absent | switch true | not probed: no credential | Bridge dispatch/review workflows, not person resolution |
| **C — WIRED BUT NOT CONFIGURED** | Gemini `generate_content` | `frametax2/backend/app/bridge/adapters/gemini_adapter.py` | Bridge review/research model invocation | General LLM, but **no Google Search grounding wired** | `GEMINI_API_KEY` or `GOOGLE_API_KEY`; `BRIDGE_GEMINI_ENABLED` | key names present; values absent | switch true | not probed: no credential | Bridge dispatch/review workflows, not person resolution |
| **D — DEAD / UNUSED in current app** | Browser-side Anthropic API with `web_search_20250305` | repository-root `src/utils.js` and `src/FrameTax.jsx` | Legacy prototype LLM/search calls | General provider web search if a browser key were supplied | caller-supplied Anthropic key | not part of current `frametax2` configuration | no active `frametax2` route/consumer | not probed | repository-root legacy prototype, not `frametax2/frontend` |
| **D — DEAD / UNUSED** | Core Anthropic placeholder | `frametax2/backend/app/core/config.py` | Commented as LLM-assisted extraction | None: no active consumer | `ANTHROPIC_API_KEY` | field present; value absent | no consumer | not applicable | none; Bridge has its own settings/client path |
| **D — DEAD / UNUSED configuration** | Configurable FX URL | `frametax2/backend/app/core/config.py` | Intended FX endpoint selection | Special-purpose FX | `FX_API_URL` | default present | not consumed | not applicable | `fx_refresh.py` uses its own hard-coded `_PROVIDER_URL` instead |
| **E — TEST-ONLY / PLACEHOLDER** | Legal Authority Acquisition connector | `frametax2/backend/app/calculators/legal_authority_acquisition.py` | Defines future connector interface and staged verification lifecycle | No live capability | none | interface only | `MockConnector` only | deterministic `mock://`, no network | tests/manual staging only; never served evaluation |

Additional negative findings, **STATIC VERIFIED**:

- No active `frametax2` integration exists for Wikipedia page search, IMDb/IMDbPro, Google, Bing, Brave, Serper, Tavily, Exa, general URL fetch, browser automation, scraping, geocoding, agency databases, guild databases, or film-institute search.
- URLs stored in program/authority data are provenance strings, not fetch clients.
- The active frontend calls CineGlobe's own backend and loads bundled `/geo/*.geojson`; it has no public person-search client.
- The served evaluation modules are intentionally covered by `test_no_runtime_web_dependency.py`, which forbids network libraries and raw URL/socket calls. Person research must remain outside calculator/evaluation execution.
- S3 fields exist in settings, but no S3 client/consumer is implemented in `backend/app`; they are not a search integration.

### Live-probe record

The probes called the application's existing pure network boundaries and did not invoke persistence:

| Probe | Result |
|---|---|
| `resolve_person_nationality("Lee Jung-jae", "director")` | **RUNTIME VERIFIED:** `resolved`; entity `Q491318`; one citizenship claim, South Korea (`Q884`, `KR`) |
| `fx_refresh._fetch_provider_payload()` | **RUNTIME VERIFIED:** provider result `success`; base `USD`; 166 currencies; provider update timestamp `Fri, 04 Sep 2026 00:02:31 +0000` |
| Bridge providers | **STATIC VERIFIED:** no key configured for Anthropic, OpenAI, or Gemini, so a live call would be invalid and was not attempted |

No configured integration produced a live failure; classification **B** is empty. No material integration remained **F — UNKNOWN** after inspection.

## 3. Core general-search answers

| Question | Answer |
|---|---|
| Can CineGlobe perform general web search itself? | **No — STATIC VERIFIED.** |
| Is it limited to narrow services? | **Yes.** The active person resolver is Wikidata-only; FX is unrelated and special-purpose. |
| Can the resolver search official personal, agency, guild, film-institute, IMDb/industry bios, or arbitrary URLs? | **No.** None of those adapters or a general URL retriever exists. |
| Can it reconcile multiple sources? | **No.** There is one provider and no cross-source claim reconciliation. |
| Can it follow a source hierarchy? | **No.** No source-tier policy is encoded in the resolver. |
| Can it preserve provenance per nationality claim? | **Partially, but insufficiently.** It stores country QID/label/ISO in one JSON list and the matched person QID separately. It does not preserve exact claim wording, statement references, source URLs per claim, ranks/qualifiers, retrieval method per evidence item, publication/effective dates, conflicts, or supersession. |
| Can it distinguish citizenship, nationality, birthplace, residence, and ethnicity/descent? | **No as a canonical contract.** The resolver reads citizenship (`P27`) but writes it to a field named `primary_nationality`; residence is separately stored, while birthplace and ethnicity/descent have no claim model. |
| Can it represent multiple citizenships? | **Only inside a lossy JSON list.** Downstream code receives one arbitrarily selected `primary_nationality`, so the effective answer is **no** for program consumption. |

## 4. Current resolver reach and first unsafe boundary

Current flow:

`script analysis/title-page person` → `ProjectPerson + TalentProfile` → Wikidata name search (limit 5) → role-to-`P106` occupation intersection → require exactly one matching entity → read every `P27` → map countries through `P297` → store JSON evidence → choose first ISO as `primary_nationality` → downstream role qualification reads that code.

Positive controls:

- It does not infer citizenship from a name, appearance, residence, production location, or birthplace.
- It requires occupation corroboration and returns explicit no-match, ambiguous, and lookup-failed states.
- It retains all returned `P27` values in `nationality_evidence` and does not overwrite a producer-confirmed person.
- It is idempotent after the first attempt.

Material limits:

1. name plus broad occupation is insufficient identity proof for many same-name cases; project title, exact credits, aliases, representation and other identity evidence are not searched;
2. the first failed/ambiguous Wikidata attempt permanently prevents automatic retry because `nationality_resolution_status` becomes non-null;
3. Wikidata statement references, qualifiers, rank and exact source wording are discarded;
4. all resolved external claims are labeled `DISCOVERY`, yet one ISO is copied into `primary_nationality`;
5. `canonical_role_qualification_bridge.py` reads `primary_nationality` without reading `nationality_confidence` or claim provenance;
6. one `primary_nationality` is selected by source order, not doctrine, even when multiple citizenships exist;
7. nationality and citizenship are collapsed, and national/cultural descriptors cannot be represented without pretending they are legal citizenship;
8. no multi-source search, hierarchy, conflict state, temporal state, or search-exhaustion record exists.

The first unsafe trust transition is therefore **DISCOVERY-grade Wikidata `P27` → untyped `TalentProfile.primary_nationality` → qualification consumer**.

## 5. Person-first search policy

The runtime research service must enforce this sequence:

`PROJECT EVIDENCE` → `PERSON/ROLE CLAIM` → `IDENTITY RESOLUTION` → `EXTERNAL NATIONALITY/CITIZENSHIP RESEARCH` → `EVIDENCE CLASSIFICATION` → `CANONICAL FACT` → `DOWNSTREAM PROGRAM RULE`

### 5.1 Project evidence and person/role claim

Create a source-backed role claim before any external nationality query. Minimum identity context:

- canonical project ID and source document/version;
- exact credited name and exact source wording;
- role/credit type, including distinctions such as screenplay, story, revisions, creator, director and producer;
- source page/slide/cell/character offsets where available;
- project title and known production companies;
- whether the claim is current, superseded, conflicting, or producer-confirmed.

### 5.2 Identity resolution

Resolve the person using exact name plus role and project title, then corroborate through known credits, professional identity, agency/management, IMDb/industry identifiers, official profiles and evidence-supported aliases. A candidate must explain the project-specific role claim. Name similarity or occupation alone never resolves a collision.

Identity resolution outputs a canonical person ID, external identifiers, supported aliases, matched-credit evidence, confidence and conflict state. If identity is unresolved, nationality research must stop with `UNKNOWN_IDENTITY`; it must not choose the most prominent person sharing the name.

### 5.3 External claim research

After identity is resolved, query for each claim type independently. Reusable patterns include:

- `"[FULL NAME]" nationality`
- `"[FULL NAME]" citizenship`
- `"[FULL NAME]" biography`
- `"[FULL NAME]" official`
- `"[FULL NAME]" agency`
- `"[FULL NAME]" guild`
- `"[FULL NAME]" [director|writer|role] biography`
- `"[FULL NAME]" "[PROJECT TITLE]"`

Use supported aliases and known external IDs to disambiguate. Query wording is discovery input, never evidence. Retrieve the underlying source, preserve its exact wording and classify what that wording actually asserts.

## 6. Source hierarchy

Source tier and claim explicitness are separate dimensions. A Tier 1 biography that says only “born in Los Angeles” is not citizenship evidence.

| Tier | Sources | Treatment |
|---|---|---|
| **TIER_1_AUTHORITATIVE_PRIMARY** | official personal bio; official agency/management bio; official guild bio; government/film-institute/screen-agency bio; official production/company profile; official citizenship record where legitimately available | highest source weight, but only explicit wording supports the stated claim type |
| **TIER_2_STRONG_INDUSTRY** | IMDb/IMDbPro; Variety; Deadline; Hollywood Reporter; Screen Daily; established film archives/institutes | strong professional evidence; conflicts with Tier 1 must remain visible |
| **TIER_3_CORROBORATIVE** | Wikipedia; Wikidata; reputable interviews and profiles | corroboration and discovery; structured claims are not automatically authority proof |
| **TIER_4_DISCOVERY_ONLY** | search snippets; scraped/unsourced bios; unverified databases; uncorroborated social claims | may locate sources or candidates; never creates a consumable canonical nationality/citizenship fact alone |

No model response or agreement among models is a source tier. It may extract or compare evidence, but the underlying retrievable source controls the tier.

## 7. Evidence-tier data contract

### 7.1 Separate claim type from evidence state

Required `claim_type` values:

- `CITIZENSHIP`
- `NATIONALITY_DESCRIPTOR`
- `NATIONAL_IDENTITY_DESCRIPTOR`
- `RESIDENCY`
- `BIRTHPLACE`
- `ETHNICITY_DESCENT`
- `LANGUAGE_AFFILIATION` where needed

Required producer-facing `evidence_state` values:

| State | Meaning | Automatic fact behavior |
|---|---|---|
| **VERIFIED** | resolved identity plus explicit Tier 1 evidence for this exact claim type, current and without material conflict | create/update the canonical typed claim; retain all provenance; doctrine may consume subject to its own threshold |
| **STRONG_VERIFIED** | resolved identity plus explicit, high-quality Tier 2 or exceptionally strong multi-source biographical evidence, without material conflict | create/update the canonical typed claim with tier; doctrine decides whether sufficient |
| **CORROBORATED** | explicit but weaker/secondary evidence, or wording that supports a nationality descriptor but not legal citizenship | persist as visible candidate/corroborative claim; never silently satisfy a strict citizenship rule |
| **UNKNOWN_UNRESOLVED** | unresolved identity, meaningful search exhausted without explicit evidence, or material conflict | persist the resolution/exhaustion/conflict record; create no positive jurisdiction claim |

Machine-readable conflict and lifecycle fields must accompany the state: `CURRENT`, `CONFLICTING`, `SUPERSEDED`, `HISTORICAL`, and `RETRACTED/REJECTED`. A material conflict results in producer-facing `UNKNOWN_UNRESOLVED` until resolved even if one source is strong.

The eventual UI contract is semantic token + text label + provenance access. Literal colors are not prescribed here; existing design-system tokens should be mapped later. Color must never be the only carrier.

### 7.2 Evidence record fields

Every evidence item must preserve:

- evidence ID and canonical person ID;
- project ID and person-role-claim ID that initiated the research;
- claim type and normalized value proposed;
- exact source wording/excerpt;
- source title, publisher, URL or durable source identifier;
- source tier and source type;
- retrieval date and publication/effective date where available;
- document/version/content hash where stored;
- identity confidence and evidence confidence as separate fields;
- extraction/search method and query/run ID;
- current/conflicting/superseded lifecycle state;
- reviewer/producer override metadata, if any.

A bare country code is never sufficient evidence.

## 8. Nationality, citizenship and descriptors

The canonical model must not use `nationality` as a catch-all.

- “Citizen of Canada” supports `CITIZENSHIP=CA`.
- “Canadian filmmaker” supports `NATIONALITY_DESCRIPTOR=CA`; whether a rule accepts that wording is doctrine-specific.
- “Colombian-American filmmaker” must be preserved verbatim and represented as one or more national-identity descriptors. It does **not**, by itself, prove dual Colombian/US citizenship.
- “Born in Los Angeles” supports `BIRTHPLACE`, not citizenship.
- “Lives in London” supports residence only if the statement is sufficiently current; it does not prove British nationality or legal residency status.
- Ethnicity/descent, language, name and appearance never generate citizenship.

Normalization to a jurisdiction code must retain the original wording and interpretation note. Ambiguous adjectives such as “English,” “British,” “Korean-American,” or “from Finland” cannot be silently upgraded to legal citizenship.

## 9. Multiple-citizenship and temporal model

Replace the optimizer-convenience projection with a one-to-many claim model. Minimum conceptual entities:

1. **PersonJurisdictionClaim** — person, claim type, jurisdiction/value, asserted wording, `valid_from`, `valid_to`, current/historical state, evidence state and conflict group;
2. **PersonClaimEvidence** — one row per source/excerpt, linked many-to-one or many-to-many to claims, carrying the provenance fields above;
3. **PersonIdentityEvidence / PersonRoleClaim** — project-specific identity proof kept separate from jurisdiction evidence;
4. an optional backwards-compatible projection for display only, never the legal source of truth.

All concurrent citizenship claims remain active. No arbitrary “primary” is selected. When a program asks whether a person satisfies a rule, the doctrine consumer evaluates every relevant current claim of the required type at the program's effective date and evidence threshold. Historical citizenship is considered only when the program rule and production date make it relevant.

## 10. Downstream evidence-threshold boundary

The search service reports facts and evidence; it never decides program eligibility.

The doctrine contract should request:

`claim_type` + accepted jurisdiction set + minimum evidence state/source tier + relevant date + whether dual/multiple status is allowed + whether nationality, citizenship or residence alternatives are accepted.

Example:

- Search result: `CITIZENSHIP=US`, `STRONG_VERIFIED`.
- Program doctrine: requires `CITIZENSHIP` at `VERIFIED`.
- Result: the fact remains visible, but the gate is `UNRESOLVED_EVIDENCE_THRESHOLD`, not eligible and not false.

The existing `canonical_role_qualification_bridge.py` must eventually consume typed current claims and program-specific thresholds. It must not merge nationality and residence into one untyped country set. That migration touches qualification behavior and is explicitly outside this concurrent audit.

## 11. Search exhaustion rule

One failed Wikidata lookup is never exhaustion. `UNKNOWN_UNRESOLVED` may be returned only when the run records one of these terminal reasons:

- `IDENTITY_UNRESOLVED`: project/role identity could not be safely matched after project-title, known-credit, professional-identity and supported-alias checks;
- `EVIDENCE_NOT_FOUND_AFTER_EXHAUSTION`: identity is resolved; discoverable Tier 1 sources were checked; at least two distinct Tier 2 source families/queries were checked where available; Tier 3 corroborative sources were checked; no explicit evidence for the claim type was found;
- `MATERIAL_CONFLICT`: source assertions cannot be reconciled by source tier, date, identity or supersession;
- `SOURCE_ACCESS_BLOCKED`: likely material sources exist but authentication, robots, outage or inaccessible content prevented a meaningful search;
- `LOOKUP_FAILED_RETRYABLE`: transient provider/network failure; never treated as factual unknown and eligible for retry.

Each run stores attempted providers, normalized queries, URLs inspected, failures, timestamps and the stop reason. Exhaustion should be bounded by source coverage and conflict resolution, not by a fixed result count alone.

## 12. Safe auto-population

| Evidence state | Safe behavior |
|---|---|
| **VERIFIED** | automatically persist the typed canonical claim and evidence; surface provenance; allow doctrine to consume if its threshold and claim type permit |
| **STRONG_VERIFIED** | automatically persist the typed canonical claim with evidence tier; no routine user approval; doctrine decides sufficiency |
| **CORROBORATED** | persist and display as a candidate/corroborative typed claim; do not satisfy strict authority requirements silently |
| **UNKNOWN_UNRESOLVED** | persist search state/conflict/exhaustion only; do not fabricate or assign a country |

Producer intervention is reserved for material conflicts, ambiguous identities, or legal decisions the evidence cannot resolve. Explicit producer corrections have precedence but must be stored as a distinct source/evidence record rather than erasing external evidence.

## 13. Prior-example compatibility

The proposed model represents all required prior cases without loss:

| Project/person | Prior result | Representation in proposed contract |
|---|---|---|
| Lips Like Sugar — Brantley Gutierrez | “Colombian-American”; **CORROBORATED** | exact wording retained as `NATIONAL_IDENTITY_DESCRIPTOR`; CO/US interpretations remain descriptors, not fabricated dual citizenship |
| Lips Like Sugar — Anthony Tambakis | US; **STRONG VERIFIED** | resolved identity; `NATIONALITY_DESCRIPTOR=US`, strong industry evidence items retained independently |
| FVD — Steve Bencich | US; **CORROBORATED** | project role claim linked to screenplay/budget/deck; secondary US descriptor stored without upgrading to legal citizenship |
| FVD — Mark Gantt | US; **STRONG VERIFIED** | project role claim and official/industry identity evidence linked to explicit US descriptor evidence |
| Bad Hombres — John Stalberg Jr. | US; **CORROBORATED** | budget's “John Stalberg” role wording plus identity/alias resolution to John Stalberg Jr.; secondary nationality evidence remains corroborative |
| Little Utopia — Clara Salaman | GB; **STRONG VERIFIED** | “British”/“English” wording preserved as descriptors; no silent citizenship claim |
| Little Utopia — Kim Farrant | AU; **STRONG VERIFIED** | Australian descriptor evidence linked to official Screen Australia identity evidence; migration-seeded value no longer substitutes for provenance |

This is exactly where the current schema loses information: it can store only one country code as the downstream fact and cannot distinguish the claim types or attach multiple independent sources to each interpretation.

## 14. Implementation readiness

**Classification: MATERIAL ARCHITECTURE — BLOCKED from implementation in this task.**

The work crosses persistence, identity ingestion, external-provider orchestration, evidence reconciliation, API contracts and authority-sensitive qualification consumption. A small patch enabling an LLM search tool or adding more URLs would create a second unsafe evidence path while leaving the one-code consumer defect intact. A narrow patch that merely ignores `DISCOVERY` would change qualification outcomes in a file adjacent to Claude's concurrent optimizer/core work and would not supply the missing claim architecture.

Likely files/components:

- `frametax2/backend/app/models/talent.py` — retain person identity, deprecate `primary_nationality` as authority source;
- new models such as `person_role_claim.py`, `person_identity_evidence.py`, `person_jurisdiction_claim.py`, `person_claim_evidence.py`, and a research-run/attempt model;
- a new Alembic migration for typed, multi-claim evidence storage and non-destructive backfill;
- `frametax2/backend/app/services/talent_nationality_resolution.py` — refactor Wikidata into one provider adapter; stop selecting first `P27` as canonical primary;
- new `person_identity_resolution`, `person_external_research`, `person_evidence_reconciliation`, source-tier policy and retry/exhaustion services;
- a configured general-search/discovery adapter plus constrained URL retriever, with provider status, rate limiting, cache, content hashing and allowlist/SSRF protections;
- `frametax2/backend/app/services/script_analysis_service.py` and document-source adapters — initiate person-role claims without making evaluation depend on the web;
- project/person API schemas and routes — expose typed claims, evidence state and provenance;
- later, in a separately controlled phase, `frametax2/backend/app/calculators/canonical_role_qualification_bridge.py` and doctrine schemas — consume typed claims under program-specific evidence thresholds;
- focused unit/integration tests for same-name collision, aliases, source hierarchy, conflict, dual citizenship, time validity, retry/exhaustion, and “no runtime web dependency” preservation for served evaluation.

## 15. Exact recommended next implementation boundary

Implement one isolated **Person Evidence Foundation** phase before any optimizer/qualification integration:

1. add typed `PersonRoleClaim`, `PersonIdentityEvidence`, `PersonJurisdictionClaim`, `PersonClaimEvidence`, and `PersonResearchRun` persistence with lifecycle/conflict fields;
2. define provider-neutral search-result, fetched-source and evidence-extraction interfaces plus the source-tier/evidence-state policy;
3. convert Wikidata into the first adapter and preserve full statement provenance available from it; do not write `primary_nationality` from external discovery;
4. add a general-search provider and safe URL-retrieval boundary only when credentialed, with explicit configured/live status and harmless health probes;
5. implement person-first orchestration, multi-source reconciliation, bounded retry and exhaustion records;
6. expose claims/evidence through project-person APIs without changing any program decision;
7. migrate the seven acceptance examples as fixtures proving exact wording, source tiers, aliases, multiple descriptors and non-citizenship interpretations survive round-trip persistence/reload/API rendering;
8. only after that phase passes, run a separate doctrine-consumer migration for program-specific evidence thresholds and remove `primary_nationality` as a qualification source.

This boundary is intentionally upstream of optimizer, allocation, pricing, scenario identity, Globe, ranking, selection, MFNI and QPE doctrine. It preserves the repository rule that ordinary served evaluation must not depend on live web access: research is asynchronous/explicit, results are durable, and calculators consume only canonical persisted facts.

## 16. Blockers

- no active general-search or arbitrary-public-URL capability;
- no configured Bridge provider credentials, and Bridge search flags are not implemented by adapters;
- no claim-level, multi-source, temporal or conflicting evidence model;
- no complete person-role evidence architecture for all project document types;
- no source hierarchy or search-exhaustion state in runtime code;
- unreviewed Wikidata citizenship can currently flow into the single downstream nationality field;
- program doctrine has no machine-readable per-role claim-type/evidence threshold contract;
- adjacent qualification/core files are under concurrent Claude work and were not touched.

## Final gate

**RUNTIME SEARCH INVENTORY: RUNTIME VERIFIED**  
**GENERAL WEB SEARCH: BLOCKED / NOT PRESENT**  
**EVIDENCE-TIER ARCHITECTURE: STATIC VERIFIED DESIGN; NOT IMPLEMENTED**  
**IMPLEMENTATION READINESS: MATERIAL ARCHITECTURE**  
**PRODUCTION CODE CHANGED: NONE**
