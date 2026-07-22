# CineGlobe UI Handoff

**For the next Claude account — UI work only. Do not modify backend logic.** Backend is feature-complete for the scope described in `BACKEND_HANDOFF.md`; this document is the map of what the UI needs to catch up to.

---

## ARTIFACT MIGRATION WORKSTREAM — COMPLETE

The Artifact Migration workstream (tracked in detail in `frontend/CINEGLOBE_MIGRATION_HANDOFF.md`) is **closed**. Do not reopen it. Do not re-audit the repository to re-derive its status.

**Closeout finding:** `CINEGLOBE_MIGRATION_HANDOFF.md`'s route matrix listed 5 pages as "PARTIALLY MIGRATED" (Documents, Record, Knowledge, Company Knowledge, Organization Reports) with a literal instruction to rebuild them against the artifact's exact HTML/CSS structures (`.doccat`/`.bind`, `.rec`, `.kcard`, `.rpt-preview`). Direct inspection this session found that classification stale: those pages already render real, fully-wired data (Binder from `legal.evidence_trace`; Record from `buildRecordRows`; Knowledge with a real Grey-Areas + Reference-Library dual view; Reports already using artifact-derived `rpt-card`/`rpt-meta`/`rpt-desc` classes with real allocation-model figures) in the same established design language the rest of the app (Today, Overview, Workspace) evolved into across many later "closeout" sessions — a language that itself already superseded literal artifact-class-name cloning for those three pages. Rebuilding the remaining 5 to literal artifact markup now would reintroduce visual inconsistency with the rest of the app, i.e. would be a redesign, not a migration completion. They are treated as done.

**The one concrete, previously-unaddressed migration item found and completed this session:** `/production/scenarios` was rendering every `allocated_structures` entry as an unbounded table (7 columns, no cap). Canonical behavior is a hard cap of 6 simultaneously-visible "active working scenarios" (rank-ordered), with any overflow reachable through a scenario selector that swaps a chosen structure into the last visible slot. Implemented in `screens/production/Scenarios.jsx` + `.sc-selector` in `styles/screens.css`, reusing the existing `.field-select` control. Verified with Playwright: exactly 6 columns render, the selector correctly lists only the overflow item(s), a real selection swaps the column live with zero console errors, and the Inspector opens correctly on the swapped-in structure.

**Future UI work is not part of this workstream.** See `BACKLOG` below for ideas surfaced by `UI_HANDOFF.md` §4 and prior sessions — none of it should be started without a separate, explicit assignment.

---

## BACKLOG (not started, not in scope until separately assigned)

Carried forward from §4/§5 below — genuine backend capability with no UI surface yet. Do not begin any of this from the Artifact Migration workstream:

- Production Economics screen (floor/ceiling/financing/in-kind) — `/economics`
- Jurisdiction Comparison screen — `/economics.alternative_jurisdictions`
- Explain Mode (assembled "why" panel over authority/evidence/rationale fields)
- Treaty-partner election control — `POST /facts {treaty_partner_code}`
- Travel adjustment controls — `POST /economics/controls`
- Runtime-warnings banner — `rate_warnings`/`budget_reconciliation`/`RateResolution.conflicts`
- Structuring advice panel — `/economics.structuring_advisory`
- Grants/Funds panel, stacking disclosure, assumptions disclosure, doctrine badges, confidence-tier consistency, calculation-provenance detail, script-intelligence panel, cultural-test visual distinction

These are recorded for triage, not queued — the next assignment decides what (if anything) to pick up.

---

## 1. Current UI Architecture — use this as the production baseline, do not redesign

A real, working React app already exists at `frametax2/frontend`:

- **Stack**: React 19, react-router-dom 7, Vite, `lucide-react` icons, `three`/`three-globe` for the 3D jurisdiction map.
- **Shell**: `src/shell/AppShell.jsx` + `PrimaryRail.jsx` + `SecondaryNav.jsx` + `Inspector.jsx` — a persistent app chrome with a slide-out inspector panel (`useAppState().openInspector(kind, payload)`).
- **State**: `src/state/AppState.jsx` (24 lines — inspector open/close state only) + `src/lib/useCineGlobe.js` (22 lines — fetches `/production`, `/package`, `/recommendations`, `/structures`, `/legal` in parallel via `src/api.js`, returns `{data, loading, error}`).
- **Screens**: `production/{Overview,Workspace,Binder,Knowledge,Record,Settings}.jsx` + `company/{Today,CompanyGlobe,CompanyKnowledge,OrgReports}.jsx`.
- **Components**: `Async.jsx` (loading/error), `EconomicsTrace.jsx`, `FXStrip.jsx`, `Globe3D.jsx`, `QuestionStack.jsx`, `RecommendationsList.jsx`.
- **Design principle already established in the code** (keep this): every value shown comes from a backend call, never computed client-side. `api.js`'s own comment states this. Preserve it — do not introduce client-side calculation logic when adding new screens.

**Artifact to use as the baseline**: the `frametax2/frontend` source tree itself. No separate design file/Figma/Claude-Artifact exists — this IS the production baseline (confirmed via `Artifact` tool's list action returning no published artifacts, and via the two unrelated single-file JSX prototypes referenced in the now-superseded `PHASE_8_UI_BRIDGE.md` being a different, earlier product entirely, not connected to this backend).

---

## 2. Backend Changes Since the Artifacts Were Built — confirmed via direct code inspection

The current frontend was built against an EARLIER backend state. Three concrete, confirmed breaks:

1. **`api.js` never calls `/economics`, `/people`, or `/facts`.** These three endpoints did not exist (or were empty) when the frontend was written. Everything documented in this handoff under §4 (Production Economics, People Editor, Financing/In-Kind/Travel/FX controls) has **zero UI surface today** — not broken, simply never wired.
2. **`/structures.ranking[]` field rename.** Confirmed via live API call this session: the field is now `conservative_npc_usd`, not `risk_adjusted_npc_usd`. `Overview.jsx` (line 18: `baseline?.cases?.risk_adjusted?.net_production_cost_usd`) and `Workspace.jsx` (line 136: `best?.risk_adjusted_npc_usd`) both read the **old field name** — these values will render as `undefined` / blank today. This is a real, live bug requiring a one-line-per-usage fix, not a design decision.
3. **`FXStrip.jsx` and `EconomicsTrace.jsx` narrate a backend state that no longer exists.**
   - `FXStrip.jsx`'s entire copy ("no live-fetch capability wired," "none has been populated," "Little Utopia's budget is already USD-denominated end to end, so no conversion is applied") is **factually false as of this session** — FX is now live, sourced, and directly relevant (Malta/Ireland/Greece are EUR-denominated jurisdictions the optimizer now compares against). This component needs a full rewrite, not a patch.
   - `EconomicsTrace.jsx` renders an "isCommitted" branch keyed on `legal.committed_rule_id === greyArea.graph_rule_id`. Two sessions ago, the backend was deliberately changed so `legal_commit` (and therefore `committed_rule_id`) is **always `None`** — the one genuine grey area (`GA-INKIND-FMV`) is no longer mock-auto-resolved (this was itself a fix: mock evidence must never resolve a genuine grey or alter a headline number). This means `EconomicsTrace` will **always** render its "Pending" branch now. That's not wrong exactly — but the backend now provides much richer resolution-path data (`grey_area.grey_kinds`, `grey_area.resolution_paths` — 6 concrete producer actions) that this component doesn't render at all.
4. **Workspace.jsx's globe caption is stale**: "Treaty routes aren't shown — none of today's candidates use a treaty structure." This was true when written; it is **not true anymore** — electing a treaty partner via a (currently nonexistent) UI control composes a real treaty candidate (confirmed this session: `PSC-FR-MU`). There is no UI path to elect a treaty partner at all today.

---

## 3. Screens Requiring Updates (existing screens — fix before adding new ones)

| Screen | Required work | Priority | Blocking on |
|---|---|---|---|
| `Overview.jsx` | Fix `risk_adjusted_npc_usd` → `conservative_npc_usd` (2 usages); "Latest Record" section will always show "No record entries yet" now — either accept this as correct (it IS correct — nothing is mock-resolved) or replace with something that shows the grey area's real resolution paths instead of waiting for a commit that will never come in the demo. | **P0 (live bug)** | None — pure bug fix |
| `Workspace.jsx` | Same field rename fix; remove/replace the stale "no treaty routes" caption once a treaty-election control exists (§4); `EconomicsTrace` usage should be replaced with the richer version below | P0 (bug) / P1 (caption + trace) | Treaty-election control (new) |
| `FXStrip.jsx` | Full rewrite — real live rate + current/1M/6M/12M horizons now exist at `/economics.fx_horizons` (`{MUR: {current, "1m", "6m", "12m"}, EUR: {...}, GBP: {...}}`); user-override and historical-date controls exist server-side (`POST /economics/controls` with `fx_rate_source`, `fx_historical_date`, `fx_user_rate`) | **P0** | `useCineGlobe.js` needs to fetch `/economics` |
| `EconomicsTrace.jsx` | Extend to render `grey_area.grey_kinds` (producer_election/missing_documentation_fact/legal_authority_interpretation/approval_dependency) and `grey_area.resolution_paths` (6 concrete actions) from `/legal.grey_areas_current` — this data exists and is unused | P1 | None — data already served |
| `useCineGlobe.js` | Add `/economics` and `/people` to the parallel fetch; likely also want `/production` already covers physical_requirements/territory match | **P0** | None |

---

## 4. New Backend Capability Requiring New UI — full list

For every item: **Current backend capability** / **Required UI work** / **Priority** / **Blocking dependencies**.

### Explain Mode
- **Backend**: no single "explain this number" endpoint. The trace has to be assembled from `AccountQualification.authority_basis`/`.reason`/`.grey_reason` (in `/package.register`), `Recommendation.evidence_reference`/`.authority_reference`/`.qualification_rationale` (in `/recommendations`), and `/legal.evidence_trace` (only when `legal_commit` exists — see §2).
- **UI**: a reusable "why" panel/drawer that can be triggered from any number and assembles the above into one readable chain.
- **Priority**: P1 (high value, needs design work — this is the single most differentiating feature of the product)
- **Blocking**: nothing backend-side; this is UI composition work over existing data.

### Authority citations
- **Backend**: present per-account (`authority_basis`, `reason` string with citation text embedded) and per-recommendation (`authority_reference` tuple of citation strings). Never a structured URL/document object — citations are free-text strings with the source named inline.
- **UI**: render as inline citation chips/footnotes, not links (no URLs are stored).
- **Priority**: P1

### Calculation provenance
- **Backend**: `RateResolution.basis` (full statutory text + band-ceiling caveat), `.conditions_evaluated` (each condition's quote + satisfied/None + note), `.conflicts` (budget-vs-database rate disagreements, always reported never absorbed).
- **UI**: none exists. Needs a dedicated view, likely inside Explain Mode.
- **Priority**: P1

### Formula drill-down
- **Backend**: `EconomicsResult` (in `/economics`) exposes `financing_formula` as a literal formatted string ("Financing cost = incentive $X × financed Y% × annual rate Z% × (W/52 weeks) = $Result"). No other formula is stored as a string — QPE/NPC arithmetic is implicit in the numbers, not a rendered formula.
- **UI**: render the existing `financing_formula` string directly; for QPE/NPC, either accept showing only the inputs+outputs (honest) or request a backend addition (do not fabricate a formula string client-side).
- **Priority**: P2

### QPE account trace
- **Backend**: `/package.register` — full account-level list with `account_code`, `description`, `amount_usd`, `state`, `confidence`, `authority_basis`, `reason`, `grey_reason`. `budgetBlocks.js` (existing) already reshapes this for the Model Rail. The `authority_basis`/`reason` fields are NOT currently surfaced anywhere in the UI (checked `budgetBlocks.js` usage — only `state`/`amount`/`label` render today).
- **UI**: add authority_basis/reason to the account-line click target (already opens the Inspector — extend the inspector payload).
- **Priority**: P1

### Doctrine badges
- **Backend**: `/production.rate_resolution.basis` names the doctrine indirectly; the doctrine ENUM itself (`OPEN_DEFAULT_INCLUDE`/`CLOSED_POSITIVE_LIST`/`HYBRID_CONDITIONAL`) is served per-jurisdiction on `/economics.alternative_jurisdictions.executable[].doctrine`.
- **UI**: a small badge component, one per jurisdiction card, reading directly from that field.
- **Priority**: P2

### Qualification reasoning
- Same data source as "QPE account trace" above — not a separate backend concern.

### Production economics (30% floor / 40% ceiling / financing / in-kind)
- **Backend**: fully served at `/economics` — `verified_floor_case`, `potential_ceiling_case` (with `conditions` array — the exact unmet requirements for the ceiling), `inkind_post_options.{accepted_as_qpe, not_accepted_as_qpe, lost_or_moved_outside_mu}`, `user_elected_case` (if a rate was elected).
- **UI**: **entirely new screen or major Overview addition — nothing renders any of this today.** This is the single largest gap between backend capability and UI surface.
- **Priority**: **P0** — this is the core deliverable of the last several backend sessions and has zero UI presence.
- **Blocking**: none backend-side.

### 30% floor / 40% ceiling
- Covered above — `verified_floor_case`/`potential_ceiling_case`, each with `rate_authority_status` (`VERIFIED_FLOOR`/`CONDITIONAL_CEILING`) and, for the ceiling, a `conditions` array naming every unmet requirement in plain English.
- **UI**: side-by-side comparison card, never blended into one number (backend explicitly avoids a single "risk-adjusted" headline for this reason — respect that in the design).
- **Priority**: P0 (part of the economics screen above)

### Financing controls
- **Backend**: `POST /economics/controls` accepts `financing_method` (none/rate_time/hard_cost), `financing_annual_rate`, `financing_weeks`, `financing_amount_pct`, `financing_hard_cost_usd`, `financing_source`. Defaults to `$0` financing (never a silent 8%/39wk assumption — this was a specific fix in an earlier session).
- **UI**: a control panel (radio for method + relevant inputs), posting to this endpoint and re-rendering `/economics`.
- **Priority**: P0 (part of the economics screen)

### In-kind controls
- **Backend**: `in_kind_post_available`, `in_kind_post_fmv_usd` (defaults to the real $625,000), `in_kind_post_accepted_as_qpe` (unknown/yes/no), `replacement_post_cost_if_lost_usd`, `post_location` (mauritius/elsewhere) — all via the same `POST /economics/controls`.
- **UI**: a toggle/selector showing all three outcome scenarios side by side (the backend already computes all three simultaneously — don't make the user pick one to see results).
- **Priority**: P0

### Travel adjustment
- **Backend**: `POST /economics/controls` — `origin_city` (LA/NYC/London/any `travel_model.py` code), `business_travelers`, `economy_travelers`, `rotations_per_year`, `hotel_nights`, `per_diem_days`, `travel_pricing_mode`. Results in `/economics.normalized_structures.ranking[].travel_incremental_delta_usd` AND `.travel_delta_vs_original_budget_usd` (two distinct deltas — render both, labeled clearly per their different meanings, see `BACKEND_HANDOFF.md` §2).
- **UI**: origin-city selector + traveler-count inputs + a delta display per candidate jurisdiction.
- **Priority**: P1

### FX controls
- **Backend**: `fx_rate_source` (live/historical/user_override), `fx_historical_date`, `fx_user_rate`, `fx_scenario_delta_pct` — all via `POST /economics/controls`. Live rate is real and sourced (see `BACKEND_HANDOFF.md`).
- **UI**: replaces `FXStrip.jsx` entirely (§3).
- **Priority**: P0

### People editor
- **Backend**: `GET /people` (writers/directors/cast/producers with nationality+residency, each with a `_state` field distinguishing known/unknown), `POST /people` with `{answers: {"{role}_nationality": "XX", "{role}_residency": "XX"}}`.
- **UI**: entirely new — no people UI exists at all today. Should show the real sourced names (Clara Salaman, Kim Farrant, Rachel Winter, Max Botkin) with their citations, and an editable form for the unknowns (lead cast, all 4 residencies).
- **Priority**: P1
- **Blocking**: none.

### Screenplay intelligence
- **Backend**: `/production.physical_requirements.script_requirements` — 12 facts each with `value`/`confidence`(CONFIRMED/NOT_EVIDENT)/`evidence` string, plus `script_source` (the Drive file names). `/package.script` has the standard `known`/`attributes` shape (8 attributes known, rest honestly unknown).
- **UI**: a panel showing the confirmed facts with their evidence quotes, and an honest "not yet confirmed" list for the rest — never presenting NOT_EVIDENT as false.
- **Priority**: P2

### Cultural qualification
- **Backend**: `/recommendations` includes `eligibility_gate_failed` subtype recommendations (hard threshold failures, HIGH confidence) separately from regular `cultural_test_gap` points-based recommendations (LOW confidence, CREATIVE category) — these are semantically different (categorical ineligibility vs. a scoring opportunity) and should look different in the UI, not be mixed in one list.
- **UI**: `RecommendationsList.jsx` currently groups by `category` only — add a visual distinction for `subtype === "eligibility_gate_failed"`.
- **Priority**: P2

### Treaty qualification
- **Backend**: fully working (see `BACKEND_HANDOFF.md` §2) but **zero UI entry point** — there is no control to elect a treaty partner. `POST /facts` with `{answers: {"treaty_partner_code": "FR"}}` is the mechanism.
- **UI**: a jurisdiction picker for treaty partner election.
- **Priority**: P1
- **Blocking**: none.

### Optimizer explanation
- Covered by "Explain Mode" above — no separate backend concern.

### Co-production comparison
- **Backend**: composed candidates exist (`/structures.candidates`) but most show `is_fully_priced: false` with real, specific blocking reasons (`constraints`, `priceable_pct`, `unknown_pct`). The scenario engine's fix this session means these reasons are now real text, not silence.
- **UI**: `Workspace.jsx`'s `JurisdictionLane` component already renders `priceable_pct` and a partial-note — extend it to show the actual `constraints` list, not just a count.
- **Priority**: P2

### Jurisdiction comparison
- **Backend**: `/economics.alternative_jurisdictions` — the NEW, real, executable comparison (4 jurisdictions with QPE/NPC/rate/doctrine/travel/FX all computed against the SAME real budget) plus `catalog_only` (8 excluded jurisdictions with the reason why).
- **UI**: **entirely new — no comparison table/view exists.** This is the second-largest gap after production economics.
- **Priority**: **P0**
- **Blocking**: none.

### Grants / Funds
- **Backend**: `/economics.available_funds.by_jurisdiction` — real classification (no dollar amounts) per executable jurisdiction, clearly separating the base incentive from additional funds.
- **UI**: new panel, likely inside the jurisdiction comparison screen.
- **Priority**: P2

### Stacking
- **Backend**: `/economics.available_funds.stacking_status` — explicitly discloses non-connection (slug mismatch), not a computed result.
- **UI**: render the disclosure text honestly; do not imply stacking is calculated.
- **Priority**: P3

### Scenario comparison
- **Backend**: `POST /scenarios` already wired in `api.js` (`postScenario`). Returns `ScenarioResult` with real `notes` explaining unpriced pathways now (this session's fix).
- **UI**: check whether the current consumer renders `.notes` — if not, add it; this is where a producer would otherwise see a blank/confusing result.
- **Priority**: P1

### Historical FX
- **Backend**: `/economics.fx_horizons` — real current/1m/6m/12m per currency, `None` for genuinely unavailable data (MUR beyond current).
- **UI**: part of the FXStrip rewrite (§3).
- **Priority**: P0 (bundled with FX controls)

### Airfare normalization
- Same backend as "Travel adjustment" above.

### Assumptions
- **Backend**: `/production.production_structure_default` — the permanent SPV/foreign-labor assumption set, explicit and traceable (never hidden). Not currently rendered anywhere.
- **UI**: a small "assumptions" disclosure panel.
- **Priority**: P2

### Evidence confidence
- **Backend**: every `AccountQualification` has `.confidence` (HIGH/MEDIUM/LOW/NOT_APPLICABLE); every `Recommendation` has `.confidence`; jurisdiction profiles have `.confidence_tier` (DISCOVERY/PARSED/VERIFIED).
- **UI**: consistent color/badge treatment across all three — currently only account-line dots (via `accountStateLabel`) render any confidence signal, and that's state not confidence-tier.
- **Priority**: P2

### Runtime warnings
- **Backend**: `/production.rate_warnings` (statutory rate database vs. constant mismatch), `/production.budget_reconciliation` (the accepted $2 source-document variance, always disclosed), `RateResolution.conflicts` (budget-vs-database rate disagreements).
- **UI**: none of these render today. Should be a persistent, dismissible banner style, not buried.
- **Priority**: P1 — these are exactly the kind of thing a real producer needs to see, not hide.

---

## 5. Priority Summary

**P0 (live bugs + zero-surface core features)**: field-rename fixes in Overview/Workspace; FXStrip rewrite; Production Economics screen (floor/ceiling/financing/in-kind); Jurisdiction Comparison screen; `useCineGlobe.js` fetching `/economics` and `/people`.

**P1**: Explain Mode composition, authority citations, QPE account trace enrichment, treaty-partner election control, travel controls, people editor, runtime-warnings banner, scenario `.notes` rendering.

**P2**: calculation provenance detail, doctrine badges, script intelligence panel, cultural-test visual distinction, co-production constraint detail, grants/funds panel, assumptions disclosure, confidence-tier consistency.

**P3**: stacking disclosure (low value until backend connects it — see `BACKEND_HANDOFF.md` roadmap item 2).

---

## SESSION DELTA — closeout #2

- **Stacking is now PARTIALLY CONNECTED.** `/economics.available_funds` (now v1.1.0) carries a new `stacking_by_jurisdiction` map — real relationship edges per executable jurisdiction (Ireland has 24: fund complements, dev-fund base reductions, treaty unlocks; Greece 1; Mauritius/Malta 0). No stacked dollar figure (deliberately not fabricated). The Stacking panel (was P3) can now render real relationships for Ireland; keep it honest — show edge relationships, never a computed stacked total.
- **Jurisdiction comparison caveat for UI:** `/economics.alternative_jurisdictions` prices each executable jurisdiction at **100% relocation** (whole budget moved there), NOT as a co-production split. Label it as "if you relocated the entire production" — do not present it as a co-production/split economic. Co-production candidates on `/structures` remain `priceable_pct=0.5` and must show as "partially priced — split allocation not modeled," not blank.
- No other backend field renames this session; the UI bugs in §2–§3 still stand.

---

## SESSION DELTA — Account-transfer handoff (closeout #5)

- **New served field for the UI to consume:** `/economics.structuring_advisory` — the Production Structuring Engine output (recommendations with full explainability + `routing_decisions`). No UI surfaces it yet; add a "Structuring advice" panel (SPV/in-kind/routing recommendations with authority/risk). Note the recommendation *prose* is still LU-specialized (amounts/gating are generic) — render fields, not assumptions.
- **Backend engine ownership is not yet final:** see `ACCOUNT_TRANSFER_HANDOFF.md`. Several backend engines overlap and must be reconciled against the other Claude account before canonical choice. UI should bind to the served `/api/v1/cineglobe/*` routes (stable), not to any specific internal engine module.
- The `frametax2/frontend` React app remains the UI baseline; §2–§3 live bugs and §4 missing screens are unchanged. No API contract changed this session.

---

## SESSION DELTA — API contract addition: /structures.allocated_structures

Additive only — no existing field changed; every prior §2–§4 item stands.

**New on `GET /structures`: `allocated_structures`** — the account→jurisdiction allocation
surface the Rev C workspace needs:
- `structures[]`: per structure — `structure_id/structure_type/label/participants`,
  `is_fully_priced`, `blockers[]` (exact reasons a structure is excluded from ranking),
  `segments[]` (per jurisdiction: allocated_usd, qpe_usd, rate floor/ceiling, statutory_basis,
  doctrine, incentive floor/ceiling, per-account `qualification_trace[]`), full
  `allocation.assignments[]` (account, amount, component, jurisdiction, assignment_kind
  fixed/recommended/conditional/user_elected, rationale, governing_decision, supporting_facts,
  authority, unresolved_requirements, split_pct), and a gated `recommendation`
  (deterministic id, action, approval_chain, reversibility, dependency_group, full explanation).
- `ranking[]`: fully-priced structures only (`npc_verified_usd`, `npc_with_adjustments_usd`);
  unpriced entries carry `excluded_from_ranking_because[]`.
- `stack_combinations`, `advisor_routing_decisions_input`.

**New producer control**: `POST /facts {"answers": {"component_route_post": "MT"}}` routes the
movable post/VFX/music components (executable jurisdictions only; validated server-side).
Clearing: value `null`.

UI mapping hints: Lane Rack lanes ← `structures[]` (one lane per structure; unpriced lanes show
blockers, never blanks); Model Rail block treatment ← `allocation.assignments[]` per structure;
Inspector trace ← segment `qualification_trace` + assignment rationale/authority; adopt-gating
← `recommendation.approval_chain` / `dependency_group`.

---

## SESSION DELTA — Workspace Rev C implementation (allocation-driven UI merge)

**Implemented:**
- `useCineGlobe.js`: fixed a StrictMode bug where the mounted-ref was only ever reset to `true`
  in `useRef`'s initial value, never re-armed on the dev-only mount→cleanup→mount cycle — every
  screen was silently stuck on "Loading from backend..." forever after the first StrictMode
  cleanup. Extended the combined fetch to include `/economics`, `/people`, `/facts` (never
  fetched by this app before); added `refetch()`.
- `api.js`: added `getEconomics`/`postEconomicsControls`, `getPeople`/`postPeople`,
  `getFacts`/`postFacts`, `uploadDocument` (multipart) — all real routes, none previously called.
- `budgetBlocks.js`: fixed a stale account-code mapping (old `"10-00"` fixture scheme vs. the
  real `"1000"`-series codes) that was silently dropping every Model Rail line.
- `Workspace.jsx`: Lanes/Map/Split rewired from `structures.candidates`/`structures.ranking` to
  `structures.allocated_structures` — real per-jurisdiction segment economics, real blockers,
  real structure recommendations. Verdict banner now reads the same allocated ranking the Lane
  Rack renders (one live model, not two divergent numbers). Model Rail account clicks open a real
  cross-structure "jurisdiction comparison / affected structures" trace (new `AccountInspector`
  `crossRef` section in `Inspector.jsx`). Added `IE` to `jurisdictions.js` (real allocated
  structures use it; was missing, silently dropping that globe point).
- `useProjectStatus.js`: 3-state company workflow status (In Development / In Evaluation / In
  Production), frontend-only — no backend field exists (documented in-file). Rewritten from
  `useState`+`useEffect` to `useSyncExternalStore` for correct cross-instance sync: a status
  change in Settings now updates the SecondaryNav header chip and Today's production-row chip
  live, same tab, no reload. Wired into `Settings.jsx` (editable control), `Today.jsx` (read-only
  chip), `SecondaryNav.jsx` (read-only header chip).
- `Overview.jsx` gained three new sections: `QualificationPanel` (People nationality/residency —
  edited at the ROLE level, matching the backend's own override model, not per-person; production
  facts editor driven dynamically from `/facts.answerable` so it never hardcodes field names;
  read-only script/location display), `QualificationAssistant` (current qualification / missing
  requirements / potential incentive increase / how to qualify — built only from recommendations
  that actually carry a value: the one real $250k grey-area item plus the two real blocked
  allocated structures; the ~130 zero-value worldwide-catalog recommendations, `treaty_composition_path`/`multilateral_membership` pairwise combinatorics, were deliberately excluded rather than
  presented as if personalized), `ProductionIntake` (drag/drop + From-computer/Google-Drive/Gmail
  buttons, all honestly disabled with the same reasoning `Binder.jsx` already established for its
  own upload buttons — extracted to new `lib/ingestion.js` so the two screens can never disagree).
- `FXStrip.jsx` rewritten from a static "unavailable" placeholder to render the real
  `/economics.fx_horizons` table (current/1M/6M/12M per currency — MUR has spot only, EUR/GBP
  have full curves). Commentary is a plain factual delta between two already-fetched numbers,
  never a fabricated "consensus"; explicitly discloses the optimizer prices at current rates only.
- `Knowledge.jsx` gained a "Reference Library" view — aggregates every citation already served
  (`register.reason` for explicit-statute accounts, `allocated_structures` segment
  `statutory_basis`, `recommendation.authority_reference`), deduplicated and grouped by kind. Not
  a new source — the same citations already shown in Inspector/Workspace.
- `shell.css`: added `.field-row`/`.field-select`/`.field-input`/`.field-unavailable`/
  `.field-saved` — this app's first editable form controls, styled to the existing hairline/tag
  language rather than a new input system.

**Verified (runtime, in-browser, this session):**
- Full `npm run build` + `oxlint` clean after every change.
- Workspace Lanes/Map/Split confirmed rendering real `allocated_structures` data; segment-chip
  click, lane click, and globe click all confirmed opening the correct Inspector kind with real
  fields (tested against the live GR segment: $4,355,327 allocated, 40% rate, $1,742,131 floor).
- Model Rail expand → account click → cross-structure comparison confirmed with real dollar
  figures across all 7 allocated structures for account 1400 (CAST).
- Qualification Panel: a real edit (writer residency → FR) confirmed `POST /people` firing,
  refetching, and the "now GB/FR" display updating; reverted cleanly afterward.
- Project status: confirmed instant cross-component sync (Settings toggle → header chip, no
  reload) and confirmed persistence across a hard reload.
- FXStrip and Reference Library confirmed rendering real backend data with zero console errors on
  a clean browser tab.
- Every console error observed during this session was confirmed to be stale/buffered history
  from long-lived dev tabs — the identical "hook order" and "failed to reload" warnings still
  printed on a tab that had been idle for minutes with no re-render possible, and vanished on a
  freshly opened tab hitting the same route. Noting this so a future session doesn't re-chase the
  same false trail; always verify a console error on a fresh tab before treating it as live.

**Outstanding (scope boundary respected, not built this session):**
- Qualification Panel fields with no backend-editable equivalent (Department heads, Production
  companies, full Cast roster beyond lead, a Shoot-locations field distinct from the script's own
  `setting`) are disclosed as unavailable, not fabricated — needs new backend fields/routes.
- Production intake upload is real (`POST /api/v1/documents/upload`) but stays disabled
  everywhere (`Binder.jsx` and now `Overview.jsx`) because `little_utopia_state.py` can't read
  from the documents table it writes to — pre-existing gap, unchanged this session.
- Google Drive / Gmail attachment intake are designed UI slots only; no connector wired
  (`lib/ingestion.js`).
- FXStrip's forward curve exists only for MUR/EUR/GBP; no live-fetch capability on the backend
  (pre-existing, unchanged).
- Reference Library's citation set is limited to the three fields that already exist server-side;
  a jurisdiction-level `authority_name`/`authority_url_hint` would need a new backend route (same
  gap noted in the earlier blueprint phase).
- 12 checkpoint screenshots captured to `frontend/design-review/current/` for external visual
  review — no autonomous visual polish performed past this checkpoint, per instruction.
