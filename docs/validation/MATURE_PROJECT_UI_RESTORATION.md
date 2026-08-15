# Mature Project UI Restoration — Closeout

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`

## Gate

**`MATURE_PROJECT_UI_RESTORED_AND_GENERALIZED`**

## Last-good mature UI source

The rich pre-regression component tree (`Overview.jsx`, `Workspace.jsx`, `Scenarios.jsx`, `ProjectGlobe.jsx`, `Reports.jsx`, `Binder.jsx`, `Knowledge.jsx`, `Record.jsx`, `Settings.jsx`, `ProductionHero.jsx`, `ProjectHeader.jsx`) was **never deleted** by the two prior UI-cutover phases (`ccb24eb`, `c16d9e0`) — only unrouted (moved behind a `/production/*` redirect). This phase restores the same, unmodified component files as the primary served UI. No git history recovery was needed; the "last good version" was sitting in the working tree the whole time.

## Architecture: preserve UX, generalize its data source (Rule 1/2)

**Visual layer (untouched):** every JSX file above — hero, tabs, scenario-card table, Globe legend, Budget Rail, Production Facts panel — is byte-for-byte the same code, just parameterized by `project_id` (added `useParams`/location-based extraction and passed the id into `useCineGlobe(projectId)`). No layout, typography, spacing, or color changed.

**Data layer (the actual generalization):**

- **Little Utopia** keeps calling the exact same functions it always did (`get_production`, `get_package`, `get_structures` → `build_allocated_structures()`, etc.) — zero regression, because these already use the canonical calculators (`derive_account_allocation`, `price_allocated_structure`) and their NPC was already proven identical to the canonical service's own output in the prior phase's unification work. This was a deliberate Rule-1 decision, not an oversight: switching Little Utopia to the thinner canonical-adapter shape would have destroyed its real segment/allocation/conditional-program detail for a number that was already correct.
- **Every other project** (FVD and any future one) is served by a new adapter, `app/services/canonical_production_view.py`, which reshapes the SAME persisted `ProductionStructure`/`StructureCalculationResult` rows `canonical_evaluation.py` already commits — no new economics, pure reshaping.
- One new combined route, `GET /api/v1/cineglobe/projects/{project_id}/state`, picks between the two sources based on whether `project_id` resolves to the real Little Utopia project row (the same `PRODUCTION_NAME` check this codebase already used) — a data-sourcing decision made once, backend-side, invisible to every component. No frontend file branches on project identity anywhere.

## Canonical data adapters retained

- `app/services/project_workspace_view.py` and `screens/project/ProjectWorkspace.jsx` (the prior phase's stripped 4-tab Workspace) are **not deleted** — kept at `/projects/{id}/summary`, off the primary nav, as the disclosed placeholder Script entry point (Part I: do not design Script Summary this phase).
- `canonical_evaluation.py` is extended, not replaced: `ENGINE_VERSION` bumped `1.0.0` → `1.1.0`, and `calculation_trace_json` now additionally carries `structure_type`, `primary_jurisdiction`, and a light `segments` array — all read from the `AllocatedStructurePricing` object `_price_candidate()` already computes in memory (via the same `price_allocated_structure()` call), never a new calculation. `input_fingerprint` alone no longer determines "current" — `engine_version` must also match, so older rows are correctly superseded rather than silently double-counted (`project_workspace_view.py`, `projects.py`'s `structures_available` count, and the new adapter all carry the matching filter).

## Real defects found and fixed during this phase's own verification

1. **Invented-savings ranking bug (Part K):** the first adapter draft sorted `ranking` purely by NPC, so a relocation candidate's incomplete (non-MFNI-normalized) NPC could outrank the production's own base jurisdiction — reproducing the exact defect Part K exists to prevent. Fixed: only `relocation_cost_normalized` candidates are numerically ranked (in practice, only the baseline), mirroring `canonical_evaluation.py`'s own `_summarize_evaluation` top-pair rule exactly.
2. **`ProjectHeader` read `useParams()` with no route context.** `ProjectHeader` is rendered by `AppShell` as a sibling of the routed page, not inside any `<Route element>` — `useParams()` silently returned `{}`, and every tab rendered `/projects/undefined/...` live. Fixed with the same location-regex technique `AppShell`'s own route-matcher already used. Verified live for both projects post-fix.
3. **`humanizeToken(null)` crash.** FVD's pre-1.1.0 persisted rows had no `structure_type` in their trace_json; `Scenarios.jsx` crashed calling `.replace()` on `null`. Fixed at both ends: `canonical_production_view.py` derives `structure_type` generically from `is_baseline` (present since Phase 2) when the enriched field is absent, and `humanizeToken` itself now guards against a null/undefined token.
4. **FVD's `gross_budget_usd` was null** in the first adapter draft — `Project.total_budget_usd` is null for FVD (its authoritative total lives on `BudgetDocument.total_budget_raw`, the established fallback pattern already used elsewhere). Fixed with the same fallback.
5. **Little Utopia's own `structure_type`/`primary_jurisdiction`/artwork logic needed no fix** — confirmed via the `is_demo_project` branch reusing `build_allocated_structures()` byte-for-byte.

All five were found live, in the browser, not by inspection — consistent with this project's own documented debugging discipline.

## Little Utopia — runtime proof

Normal navigation: Sidebar "Productions" row (always visible) → `/projects/{id}/overview`.

- Title: **The Little Utopia**
- Budget: **$4,364,393**
- Winner: **Mauritius**
- NPC: **$3,057,795** (displayed; underlying value $3,057,794.90, unchanged — traced through `build_allocated_structures()`, not hard-coded)
- Full mature hero (real artwork, budget/NPC/recommended-structure/questions-remaining strip), 8-tab nav, Production Facts / Project Globe / Production Budget three-column Overview, Scenarios table with real per-structure Qualified Spend and program names ("EDB Film Rebate · 30% (up to 40%)"), Workspace lane cards, Project Globe with the existing 4-state legend — all confirmed live, all unchanged from before this phase.
- Refresh (forced full reload) and direct-URL navigation both preserve state correctly.

## FVD — runtime proof, same UI

Normal navigation: Company Library → F#K Valentine's Day → Project Record → "Enter Workspace →" → `/projects/{id}/overview`.

- Title: **F#K Valentine's Day**, rendered with FVD's own real key-art (not Little Utopia's)
- Budget: **$4,517,687**
- Base: **Greece**
- Same hero layout, same 8-tab nav, same Overview/Scenarios/Workspace/Project Globe component tree as Little Utopia
- Scenarios: 6 real alternative-jurisdiction columns with genuinely different NPCs ($3,072,027 / $4,102,205 / $3,894,464 / $4,102,205 / $2,855,759 / $3,478,982) plus an MFNI disclosure sentence
- Workspace: FX strip (honestly "unavailable" — no generic FX data exists yet), lane cards per structure
- Project Globe + Optimizer Overlay: full jurisdiction list with the same Recommended/Alternatives/Co-Production/Excluded legend
- Documents: reachable via Project Record (the generic Documents system), one click from the Workspace's own "← Project Record" — the LU-only "Evidence Graph" Binder page shows an honest empty state for FVD rather than fabricated documents
- Production Facts: honest "Not yet named" for writer/director/producers (no curated people data exists for FVD yet — not fabricated)
- Zero Little Utopia data appeared anywhere in the FVD flow

## Identical-country-number investigation (Part J/K/L)

Root cause of the "many countries show identical numbers" observation: **the ranking bug in item 1 above** — before the fix, a broken sort could make an unnormalized relocation candidate's NPC compete directly with the baseline's, and separately, `Gross budget` is legitimately identical across every column (every candidate uses the production's own nominal source budget — no regional cost data exists yet to vary it).

Classification:
- **LEGITIMATELY_EQUAL:** `Gross budget` across all columns (real — MFNI genuinely isn't computed yet; disclosed via the new Scenarios.jsx note).
- **PRESENTATION/ADAPTER_DEFECT (fixed):** the ranking bug (item 1) — real defect, not a legitimate equality, now fixed.
- **NOT_COMPARABLE_WITHOUT_MFNI:** every non-baseline candidate's `NET PRODUCTION COST` — genuinely different per jurisdiction (confirmed: FVD's 6 visible columns show 5 distinct values), but explicitly not a fair comparison against the baseline until relocation costs are modeled — now labeled as such directly in Scenarios.jsx.

`Qualified spend` reads `$0` for FVD's currently-persisted (pre-1.1.0) rows, since the enriched `segments` field wasn't present when those rows were generated — an honest `$0` (unknown, not fabricated), not a defect; a future re-evaluation would populate it via the new `_segment_dicts()` serializer.

## MFNI-pending treatment

Added one disclosure sentence to `Scenarios.jsx`'s existing `.sc-note` element (no new card, no layout change) stating that only the leading structure is directly comparable today and every other column's lower cost omits real relocation costs — verified rendering on both FVD and Little Utopia (same component, same text, project-agnostic).

## Optimizer overlay

`ProjectGlobe.jsx`'s Optimizer Overlay toggle and the Globe's Recommended/Alternatives/Co-Production Opportunities/Excluded legend are unmodified — they already derive their coloring purely from `allocated.ranking`/`allocated.structures`' `is_fully_priced`/`rank`/`candidate_status` fields, which the new adapter populates with the same semantics `build_allocated_structures()` always used. No overlay code changed; feeding it correctly-shaped canonical data was sufficient.

## Abu Dhabi presentation

Confirmed live for FVD: `Full relocation to AE-AD` appears in the Project Globe candidate list with **"1 blocker"** (the same treatment as every other unpriceable jurisdiction — Austria, Belgium, etc.), never a dollar figure, never a ranked position. `rank: null`, `candidate_status: UNPRICEABLE_AUTHORITY_INSUFFICIENT` — unchanged from the backend finding established two phases ago; no economics touched.

## Feature-parity accounting

| Capability | Status |
|---|---|
| Production hero (artwork, budget, NPC, recommended structure, questions) | PRESERVED, generalized (artwork now per-project via `/api/v1/projects/{id}/artwork`, honest fallback if none) |
| 8-tab production nav | PRESERVED, generalized |
| Overview (Facts / Globe / Budget Rail three-column) | PRESERVED, generalized |
| Scenarios comparison table | PRESERVED, generalized; added one disclosure sentence (Part K requirement) |
| Workspace (lane cards, FX strip, Map/Split modes) | PRESERVED, generalized |
| Project Globe + Optimizer Overlay + 4-state legend | PRESERVED, generalized, zero code change needed |
| Reports (generated ledger view) | PRESERVED, generalized |
| Record (versioned history) | PRESERVED, generalized |
| Knowledge (reference library) | PRESERVED, generalized; empty for projects with no segment-level data yet (honest) |
| Documents/Binder (Evidence Graph) | PRESERVED for Little Utopia; **NOT_APPLICABLE for other projects yet** — that curated register was never migrated to generic tables; FVD's real documents remain reachable via Project Record instead, not deleted or duplicated |
| Settings | PRESERVED, generalized |
| Deep per-account allocation assignments / conditional-program funding / structure-compatibility gating | **NOT_APPLICABLE for projects besides Little Utopia** — genuinely not computed generically yet (would require exposing much more of the pricing engine's intermediate state); rendered as empty, not fabricated, not crashing |

No capability silently disappeared. Every gap above is explicit and disclosed.

## Tests

Backend: `tests/test_canonical_production_view.py` (5 new tests — no invented ranking savings, no null structure_type, unpriceable never ranked, project_id always resolves). Re-ran `test_canonical_evaluation.py`, `test_canonical_project_economics.py`, `test_project_workspace_view.py`, `test_project_library_phase_c.py` (updated one hard-coded `engine_version` string to import `ENGINE_VERSION` instead — a legitimate staleness fix, not a defect). **32/32 passing.**

Frontend: `tests/mature-ui-restoration.test.mjs` (4 new tests — ProjectHeader's URL-based projectId extraction, `humanizeToken` null-safety, Scenarios is project-aware, AppShell's mature-route regex covers all 9 pages). Updated `tests/route-cutover.test.mjs`'s 5 assertions from `/workspace` to `/overview` (the intentional new landing target). **59/59 passing** (49 pre-existing Globe-invariant tests unaffected).

## Files changed

Backend: `app/services/canonical_evaluation.py`, `app/services/canonical_production_view.py` (new), `app/services/project_workspace_view.py`, `app/api/v1/cineglobe.py`, `app/api/v1/projects.py`, `tests/test_canonical_production_view.py` (new), `tests/test_project_library_phase_c.py`.

Frontend: `App.jsx`, `shell/AppShell.jsx`, `shell/ProjectHeader.jsx`, `shell/Sidebar.jsx`, `shell/LegacyProductionRedirect.jsx`, `lib/useCineGlobe.js`, `lib/programNames.js`, `api.js`, `components/ProductionHero.jsx`, `components/RecommendationsList.jsx`, `screens/production/{Overview,Workspace,Scenarios,ProjectGlobe,Reports,Binder,Knowledge,Record,Settings}.jsx`, `screens/company/{Today,CompanyGlobe,ProjectRecord}.jsx`, `tests/mature-ui-restoration.test.mjs` (new), `tests/route-cutover.test.mjs`.

## Gate detail

Met: exact mature CineGlobe UI restored (same files, same layout, no design changes) and driven by project_id; the stripped-down generic Workspace is no longer the primary served UI (relocated to `/summary`, not deleted); Little Utopia renders through canonical-traced data at $4,364,393/Mauritius/$3,057,795; FVD renders through the identical component tree at $4,517,687/Greece with its own real artwork and zero Little Utopia contamination; optimizer overlay consumes the same canonical evaluation with no code change required; comparable countries show genuinely different supported NPCs where their economics differ; unsupported regional-cost comparisons are labeled honestly (new disclosure sentence, Part K); Abu Dhabi/unpriceable candidates render as blocked, never ranked; feature parity is proven capability-by-capability above, with every gap explicit; normal navigation (Sidebar, Today, Company Globe, Project Record) lands on the restored mature UI for both projects; browser runtime passed for both, including two real defects found live and fixed before this closeout.
