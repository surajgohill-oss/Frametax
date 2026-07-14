# CineGlobe UI Handoff

**For the next Claude account — UI work only. Do not modify backend logic.** Backend is feature-complete for the scope described in `BACKEND_HANDOFF.md`; this document is the map of what the UI needs to catch up to.

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
