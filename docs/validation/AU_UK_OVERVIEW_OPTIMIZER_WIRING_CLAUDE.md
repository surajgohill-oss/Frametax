# PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END

Workstream: `PROJECT_OVERVIEW_TO_AU_UK_COPRO_END_TO_END`
Repository: `~/cineglobe-frametax` (worktree `/Users/Suraj/cineglobe-frametax-claude-remediation`
— NOT the shared AG checkout at `~/cineglobe-frametax`)
Branch: `claude/audit-frametax-features-NZcX5`
Required starting HEAD: `705a02a03343048b76c2dfacb4a99a13f0d4e2c3` (confirmed)

## Pre-flight

- **Repository/branch/HEAD/upstream/clean worktree**: confirmed — `git status
  --short` empty, `HEAD` == `705a02a0...`, branch `claude/audit-frametax-features-NZcX5`
  tracking `origin/claude/audit-frametax-features-NZcX5` at the same SHA.
- **Running local backend/frontend**: started fresh in THIS worktree (never
  the shared AG checkout). `.claude/launch.json` (primary working directory)
  gained two new entries, `cineglobe-remediation-backend` (`python3 -m
  uvicorn app.main:app --port 8010`, this worktree's `frametax2/backend`)
  and `cineglobe-remediation-frontend` (`npm run dev`, this worktree's
  `frametax2/frontend`, `npm install` run first — `node_modules` did not
  exist in this worktree before this workstream). Both verified live and
  serving real data over the real network (see Section D).
- **Project Overview component**: `frametax2/frontend/src/screens/production/Overview.jsx`
  — the "Production facts" left-column panel is
  `frametax2/frontend/src/components/ProductionDetails.jsx`, rendering
  `PERSON_ROLES` (writer/director/producer/lead cast slots/DoP/editor/
  composer) with editable name + nationality.
- **Save endpoint**: `POST /api/v1/cineglobe/projects/{project_id}/people`
  (`postProjectPeople`, `frametax2/frontend/src/api.js`) →
  `app/api/v1/cineglobe.py::post_project_people` — confirmed this is the
  REAL, project-scoped, `ProjectPerson`/`TalentProfile`-backed write path
  (not the legacy singleton-demo-engine `POST /people`).
- **Persistence models**: `app/models/project_person.py::ProjectPerson`
  (`role`, `is_confirmed`, `talent_id` FK) + `app/models/talent.py::TalentProfile`
  (`name`, `primary_nationality`, `known_residencies` JSONB — genuinely
  separate from nationality). No persistence model exists for a
  co-producer/production-company entity (jurisdiction, ownership/control,
  independence) — confirmed by inspection; the only company-shaped field
  anywhere is `Project.production_company_identifier`, a single
  cross-project identity string unrelated to per-country co-producer
  entities. This gap is real and is why the AU/UK co-producer
  company/independence requirement is modeled as a disclosed assumption
  (Section C), never collected as a fact this pass.
- **Optimizer invalidation/recompute path**: `ce.evaluate_project()`
  computes a fingerprint (`_compute_fingerprint`, includes
  `role_attachment_facts`) and short-circuits to a cached row only on an
  exact `(fingerprint, ENGINE_VERSION)` match; `post_project_people`
  itself does not directly call `evaluate_project()` — the frontend's
  `useCineGlobe(projectId)` hook re-fetches `GET /projects/{id}/state`
  after `refetch()`, and that endpoint calls `evaluate_project()`, which
  recomputes automatically the moment the fingerprint has changed. Proven
  live (Section D).
- **Served structure endpoint**: `GET /api/v1/cineglobe/projects/{project_id}/state`
  → `canonical_production_view.build_generic_pkg_and_economics` →
  `structures.allocated_structures.structures[]`, each carrying
  `treaty_slug`, `personnel_gate_state`, `opportunity_relevance`,
  `conditional_scenario`, etc.

No mismatch found; nothing stopped the workstream.

## A. Authoritative AU-UK rule package

Primary sources fetched and read in full (not summarized from a secondary
source):
- `screenaustralia.gov.au/co-production-program/co-production-partner-countries/` —
  confirms the UK is one of Australia's 12 current formal co-production
  treaties (active status, 2026-09).
- `screenaustralia.gov.au/co-production-program/co-production-partner-countries/united-kingdom/` —
  competent authority (BFI) and the real treaty PDF link.
- `screenaustralia.gov.au/wp-content/uploads/2025/08/Agreement-UK.pdf` —
  the REAL, full treaty text (Articles 1-9 + Annex clauses 1-17), fetched
  and read page-by-page. **Films Co-production Agreement between the
  Government of Australia and the Government of the United Kingdom of
  Great Britain and Northern Ireland**, signed Canberra, 12 June 1990.
- `screenaustralia.gov.au/co-production-program/co-production-guidelines/guidelines-step-by-step/` —
  application-process guidance (provisional/final approval sequencing,
  independence requirement restated operationally).
- `bfi.org.uk/apply-british-certification-expenditure-credits/co-production` —
  confirms the treaty's current active status on the UK side and the
  BFI's own application-timing rule ("apply at least 4 weeks before
  principal photography/key animation starts").

**Current status**: active, in force, both sides list it as current
(2026-09-15). No amendment record found on either guidance page; the
treaty's own Article 1(4) "Member State" definition is a 1990 EEC-era
reference, and neither current guidance page restates or modernizes it —
disclosed as a genuine, unresolved interpretive question (Article 1(4)/
Annex clauses 5, 6, 9), never guessed, and not operative for Little
Utopia's own bilateral (no third co-producer) case.

**Implemented in `app/calculators/treaty_engine.py`'s `uk-au-bilateral`
entry** (every clause individually cited in the module-level comment
directly above the registry call — not reproduced in full here):

| Requirement | Real clause | Implementation |
|---|---|---|
| Financial/creative contribution minimum | Annex (8): each co-producer ≥30% | `majority_min_pct=30, minority_min_pct=30, minority_max_pct=70` (was unsourced 20/20/80) |
| Qualifying co-producer status | Annex (4)(a)/(b) | Cited, not independently re-verified against current UK Films Act 1985 text (out of scope) |
| Independence (no common mgmt/ownership/control) | Annex (4)(d); Screen Australia step-by-step guidance | Modeled as a disclosed, producer-controlled assumption (no persistence model exists for it — see Pre-flight) |
| Qualifying formats | Article 1(1)(b): any visual-image sequence, film/TV/animation/documentary | Cited; format-agnostic, no new gate needed (this codebase does not currently gate structure type by production format) |
| Personnel (writer/director/lead cast) | Annex (6) + (14)(d) | `PersonnelRequirement(eligible_roles=("writer","director"), role_mode="all_of", fact_kind="either", eligible_codes=("AU","GB"))` |
| Third-country personnel exception | Annex (6) 1st para: "exceptional circumstances...restricted" | Cited; not modeled as a gate (not operative — LU's writer/director already satisfy the primary test) |
| Third-country location / Mauritius | Annex (6) 2nd para + (5) | Cited: Mauritius citizens may work as crowd/small-role/necessary local crew once competent authorities approve the location — the treaty's own contemplated case, never a blocker |
| Composer | Annex (9) | Cited; not gated (no composer attached for any of the four productions) |
| 90% specially-shot footage | Annex (10) | Cited |
| Ownership/rights/materials/credit | Annex (11), (12) | Cited |
| Application timing/approval | BFI (4 weeks before PP) + Screen Australia (before pre-production; simultaneous submission; final approval on completion); Annex (1), (15) — approval always conditional | Cited; approval status never assumed |
| National-treatment benefit | Article 2 | Basis for `majority_unlocks=["uk_avec"]`/`minority_unlocks=["au_producer_offset"]` (both already real, canonical, unchanged) |

Per the objective's own instruction, the complete treaty was **not** forced
into one personnel field: the structured rule package above spans a
corrected contribution-threshold pair, one real `PersonnelRequirement`,
and a rich, individually-cited registry comment covering every other
clause — future code (a company/entity model, a composer-specific gate,
a format gate) can consume the cited clauses without re-research.

## B. Project Overview input wiring

- **Persists correctly** (proven via the real running app, Section D):
  person name, role (writer/director/producer, fixed by `PERSON_ROLES`),
  nationality, confirmed-on-save (`ProjectPerson.is_confirmed = True`
  set unconditionally by `post_project_people` — "an explicit save here
  is a producer confirmation").
- **Residency**: persistence supports it
  (`TalentProfile.known_residencies`, proven in
  `test_residency_persists_and_is_read_back_by_role_attachment_facts`)
  but the Overview UI deliberately omits a residency control — an
  explicit, pre-existing design decision already documented in
  `ProductionDetails.jsx`'s own comment ("Residency is deliberately
  absent here per the approved design"). Not added: (a) the guardrail is
  "no redesign, no new workflow," and this is a standing, deliberate
  design choice from an earlier session, not an oversight; (b) Little
  Utopia's real GB writer/AU director already satisfy the AU-UK
  personnel gate via NATIONALITY alone (`fact_kind="either"` accepts
  either), so no real acceptance scenario in this workstream requires a
  residency input.
- **Production company / company jurisdiction / ownership-control**:
  persistence does NOT support a per-co-producer company entity (see
  Pre-flight) — there is no "minimum field" to add within the existing
  editor, because the underlying schema itself does not model this
  concept at all. Per the workstream's own OPTIMIZER ASSUMPTION POLICY,
  this is correctly left as a disclosed, modeled assumption (Section C),
  not collected as a fact.
- **Confirmed vs. proposed**: the existing UI's own editing model is
  "confirm on save" — every save through this panel is a producer
  confirmation (`is_confirmed=True`); there is no "propose" state this
  panel can produce (an unconfirmed `ProjectPerson` row, where one
  exists, comes from a different source — e.g. discovery/extraction —
  never from this manual edit panel). This is the existing, approved
  design; not changed.
- **On-save chain** (all 5 required steps proven live, Section D):
  Production Record persisted → prior fingerprint no longer matches (an
  automatic consequence of `role_attachment_facts` changing, already
  hashed into `_compute_fingerprint` since the prior workstream) → no
  stale row is ever re-served (the `(fingerprint, ENGINE_VERSION)` cache
  key requires an exact match) → the existing app flow
  (`useCineGlobe(projectId)`'s `refetch()` → `GET .../state` →
  `evaluate_project()`) triggers a genuinely fresh evaluation
  automatically → the browser received the new structures with no page
  reload and no manual database action.

## C. Modeled co-production structure — Little Utopia

Real Production Record (unmodified, confirmed live): writer Clara Salaman
(GB, confirmed), director Kim Farrant (AU, confirmed), producers Rachel
Winter + Max Botkin (US, confirmed); physical production planned Mauritius;
post-production planned Los Angeles.

- **GB writer + AU director credited**: `personnel_gate_state=QUALIFIES`,
  `personnel_satisfied_requirements=["writer either GB matches an
  eligible party code.", "director either AU matches an eligible party
  code."]` — proven live (Section D) and via
  `test_gb_writer_and_au_director_qualify_under_the_real_uk_au_rule`.
- **US producers do not satisfy AU/UK requirements, and do not block**:
  `"producer"` is not in `personnel_requirement.eligible_roles` at all —
  the gate simply never evaluates producer nationality, so a non-AU/GB
  producer can neither pass nor fail it. Proven live and via
  `test_uk_au_bilateral_producer_role_is_never_gated_by_the_personnel_requirement`
  / `test_little_utopia_producers_do_not_block_the_uk_au_structure`.
- **Independent AU/UK co-producers and production companies**: assumed
  obtainable, disclosed as `PROPOSED_CHANGE` (the codebase's existing,
  pre-established "producer-actionable assumption, never a verified
  fact" vocabulary — same classification the contribution-share
  assumption already uses) — no new company/entity fact is invented or
  collected; the conditional scenario's own `assumption_basis`/citation
  documents this.
  Compliant contribution shares (30%/70%, the treaty's own real minimum)
  are likewise modeled, not collected — same disclosure.
- **Mauritius**: the treaty's own Annex (6) 2nd paragraph directly
  contemplates a location shoot in a country other than the co-producers'
  own (subject to competent-authority approval) and expressly permits
  local (Mauritian) crowd/small-role/necessary-crew employment there —
  Mauritius is the treaty's own contemplated case, never a blocker,
  correctly never modeled as one.
- **Competent-authority approval remains conditional**: never assumed;
  the served `blockers`/`reason` field states plainly that "no project
  fact states each party's real ownership/spend share" and approval is
  disclosed as pending throughout (Annex (1), (15)).
- **Result**: `uk-au-bilateral` upgraded from `AVAILABLE` to
  `CONDITIONAL` for Little Utopia specifically — proven live, with real
  priced economics (Section E) — while remaining `AVAILABLE` (Bad
  Hombres, F#K Valentine's Day, both zero personnel on file — resolves
  `CURABLE_GAP`) or correctly downgraded to a real conditional question
  (`USER_FACT_REQUIRED`, Lips Like Sugar — both attachments unconfirmed)
  for the other three productions, none of which incorrectly upgrades.
  Conditional economics never become a verified recommendation
  (Section E; proven structurally and live).

## D. Live edit/recompute acceptance (real browser + real network)

Backend: `cineglobe-remediation-backend` (`localhost:8010`, this
worktree). Frontend: `cineglobe-remediation-frontend` (`localhost:5173`,
this worktree, fresh `npm install`). Navigated to
`http://localhost:5173/projects/fa5cade5-0669-4816-bfe6-72146f8d3bae/overview`.

1. **Confirmed current state**: Overview's "Production facts" panel
   showed Writer "Clara Salaman" / British 🇬🇧, Director "Kim Farrant" /
   Australian 🇦🇺, Producer(s) "Rachel Winter, Max Botkin" / American 🇺🇸
   (screenshot + accessibility-tree read, matching the real DB exactly).
2. **Recorded the AU-UK structure/fingerprint**: `GET .../state` (live
   network response) showed `computation.version: "canonical-1.60.0"`
   and the real `uk-au-bilateral` structure:
   `opportunity_relevance: "CONDITIONAL"`, `personnel_gate_state:
   "QUALIFIES"`, `conditional_scenario.conditional_incentive_usd:
   1108444.22`, `conditional_npc_usd: 3255948.78`.
3. **Changed one key creative nationality through the UI**: clicked
   "Edit production facts," changed the Director's nationality select
   from Australian to French, clicked Save.
4. **Proved the saved Production Record changed**: the real
   `POST /api/v1/cineglobe/projects/fa5cade5.../people` request body
   (captured from the network layer) showed `"directors":[{...,
   "nationality":"FR","confirmed":true}]` — a genuine write, 200 OK.
5. **Proved a fresh evaluation was created**: `GET .../state`
   (re-fetched automatically, no page reload) still reported
   `canonical-1.60.0` but with GENUINELY new values (not stale/cached).
6. **Proved qualification/relevance changed appropriately**:
   `personnel_gate_state: "HARD_FAIL"`,
   `personnel_failed_requirements: ["director either ('FR',) does not
   match this treaty's eligible party codes ('AU', 'GB')."]`,
   `opportunity_relevance: "AVAILABLE"` (correctly downgraded from
   CONDITIONAL), `conditional_scenario.status: "NOT_FEASIBLE"`.
7. **Restored the original real value through the UI**: re-opened Edit,
   changed the Director's nationality back to Australian, Save.
8. **Proved fresh recomputation restored the expected result**:
   `GET .../state` showed `opportunity_relevance: "CONDITIONAL"`,
   `personnel_gate_state: "QUALIFIES"`,
   `conditional_incentive_usd: 1108444.22` — byte-identical to step 2's
   original recorded value.
9. **Confirmed no database residue**: direct query of `ProjectPerson` ⋈
   `TalentProfile` for Little Utopia after the full edit/restore cycle
   shows exactly the original 4 rows (writer GB, director AU, 2×producer
   US) — no duplicate, no orphan, no synthetic fact.

Additional required checks:
- **Adding/removing a proposed AU/UK co-producer/company**: not
  independently testable through the UI — no such field/panel exists in
  persistence (see Pre-flight/Section B); not attempted (would be
  fabricating a workflow the guardrails explicitly forbid inventing).
- **Confirmed vs. proposed**: proven via the real DB (every save through
  this panel sets `is_confirmed=True`; Lips Like Sugar's real, untouched,
  unconfirmed writer/director rows independently prove the "unconfirmed
  never credited" path — `personnel_gate_state=USER_FACT_REQUIRED`, not
  `QUALIFIES` — in the live-DB test suite).
- **Nationality vs. residency**: proven distinct and never substitutable
  by the pre-existing `fact_kind` mechanism (unit-tested extensively in
  the prior two workstreams; unchanged here).
- **Unrelated Overview edits do not corrupt the treaty result**: the
  live edit cycle touched ONLY the director's nationality field; the
  writer/producer fields and every other real treaty opportunity were
  re-read unchanged after each save (confirmed via the full `/state`
  payload, not just the `uk-au-bilateral` entry).
- **Stale results are never displayed after a material save**: every
  `GET .../state` call after a save returned genuinely new computed
  values (proven by the HARD_FAIL/QUALIFIES flip both directions, never
  a repeat of the pre-save value).

## E. Economic acceptance — Little Utopia's real AU-UK conditional structure

Captured live from the real, running application (`GET .../state`,
`structures.allocated_structures.structures[]` entry for `treaty_slug ==
"uk-au-bilateral"`):

- **Known facts credited**: writer Clara Salaman (GB, confirmed),
  director Kim Farrant (AU, confirmed) — `personnel_satisfied_requirements`.
- **Modeled producer/company attachments**: independent AU and UK
  co-producer/production company, disclosed `PROPOSED_CHANGE`, never a
  verified fact (no such fact could be collected — no persistence model
  exists).
- **Modeled contribution shares**: `assumed_majority_contribution_pct:
  30` (GB), `assumed_minority_contribution_pct: 30` (AU) —
  `participant_allocation_pct: {"AU": 30, "GB": 70}` (AU takes exactly
  its real treaty floor; GB, the majority, takes the complement) — the
  treaty's own real Annex (8) minimum, never invented.
- **Participant QPE / priced components**:
  - `uk_avec` (GB), modeled rate 29.25%, selected incentive **$621,940.70**
  - `au_producer_offset` (AU), modeled rate 40.0%, selected incentive **$486,503.52**
- **Gross combined incentive**: `conditional_incentive_usd = **$1,108,444.22**`
- **Monetization/financing adjustments**: none applied in this conditional
  scenario (no financing-cost/contingency assumption threaded into the
  co-production conditional path — out of scope, unrelated to this
  workstream).
- **Net production cost**: `conditional_npc_usd = **$3,255,948.78**`
  (vs. Little Utopia's real single-jurisdiction baseline NPC of
  $3,791,333.30 — `net_benefit_vs_baseline_usd = $535,384.52`).
- **Unresolved approvals/cultural requirements**: competent-authority
  approval (Annex (1)/(15)) — real, conditional, never assumed; no
  cultural test required for this treaty (`cultural_test_required:
  false`), so nothing else is pending on that front.
- **Exact classification**: `opportunity_relevance: "CONDITIONAL"`,
  `classification: "CONDITIONAL_USER_FACT_REQUIRED"`,
  `candidate_status: "CO_PRO_OPPORTUNITY"`.
- **Why it cannot yet become the verified winner**: `is_baseline: false`,
  `is_directly_comparable: false`, and — structurally, not by
  convention — the `StructureCalculationResult` row's OWN
  `total_incentive_value_usd`/`true_net_cost_usd` columns are `None`;
  only the nested `conditional_scenario` dict carries a number.
  `top_pair`/`leading_structure_id` selection (`canonical_evaluation.py`)
  only ever considers a real `is_baseline` row or a row where
  `true_net_cost_usd is not None` — a treaty_coproduction row is neither,
  by construction, so it can never be promoted, regardless of how
  favorable its modeled economics look. Proven live for Little Utopia
  and structurally proven (source + live DB) for Bad Hombres too.

No economics were invented: every dollar figure above traces to a real,
already-canonical `RateRule` (`uk_avec`, `au_producer_offset`, both
pre-existing, unchanged) applied to a real, sourced treaty percentage
(Annex (8)) against Little Utopia's own real, unmodified gross budget.

## F. Regressions

Freshly verified (fresh evaluation at `canonical-1.60.0`, real DB): every
baseline single-jurisdiction candidate's economics are byte-identical to
every prior workstream's frozen values —

| Production | Baseline incentive (USD) | Baseline NPC (USD) |
|---|---|---|
| Little Utopia | 573,059.70 | 3,791,333.30 |
| F#K Valentine's Day | 1,445,659.84 | 3,072,027.16 |
| Bad Hombres | 596,910.25 | 1,885,112.75 |
| Lips Like Sugar | 3,459,278.90 | 8,524,375.10 |

Only Little Utopia's `uk-au-bilateral` opportunity changed classification
(`AVAILABLE` → `CONDITIONAL`); every other project's `uk-au-bilateral`
entry resolves a real, correctly-non-QUALIFIES personnel state
(`CURABLE_GAP` for Bad Hombres/F#K Valentine's Day — zero personnel on
file; `USER_FACT_REQUIRED` for Lips Like Sugar — both attachments
unconfirmed) and stays `AVAILABLE`. Full per-production detail in
`docs/validation/LITTLE_UTOPIA_AU_UK_UI_RUNTIME_CLAUDE.csv`.

## Tests

New file `tests/test_au_uk_copro_overview_wiring_claude.py` (13 tests, all
passing): the corrected treaty thresholds, the real personnel requirement
and its citation, the producer-role-never-gated proof, the personnel gate
mechanism against Little-Utopia-shaped facts (qualify / hard-fail /
unconfirmed / unattached), the conditional-pricing scenario's real 30/70
split and real priced components, live-DB proof of Little Utopia's served
`uk-au-bilateral` structure (relevance, personnel state, structural
non-promotability), the "producers never block" live proof, a reversible
residency-persistence proof, and a live-DB proof that all four
productions' served personnel facts match their real stored
`ProjectPerson`/`TalentProfile` rows exactly.

Two existing tests (from the prior `COPRO_OPPORTUNITY_RELEVANCE_AND_
CLOSEOUT_VALIDATION` workstream) were updated, not weakened, to reflect
the real, live behavior this workstream deliberately introduces: `uk-au-
bilateral` is now the one documented exception where a globally-
enumerated (non-home-anchored) opportunity correctly upgrades from
`AVAILABLE` to `CONDITIONAL`/carries a rule-consumed `QUALIFIES` state,
via a real researched rule and Little Utopia's own real facts — every
other non-anchored opportunity is asserted unchanged.

Full 15-file regression batch (co-production/treaty/production-view +
this workstream's two new files): **299 passed, 0 failed, 0 timeout**
(91.4s, foreground).

## Guardrails honored

No other treaty populated (only `uk-au-bilateral`'s existing entry was
extended). No MU/GR/US treaty sweep. No Globe output wiring, no broader
UI redesign (Overview's existing component/workflow untouched beyond
what was already wired; no new panel). No MFNI, reinvestment, Ohio,
Nevada, Bulgaria, or Underwater work. No broad optimizer audit. Every
command ran foreground, well under the 180s cap (longest: 129s combined
regression batch, before this file's own test additions; 91s after).
No background jobs. No test skipped, weakened, or truncated. No commit
made while a server or process was still required to be running for
verification (servers were stopped before the final commit/push, per
process hygiene — see the FINAL response for confirmation).
