# CineGlobe Frontend — Migration Handoff

**WORKSTREAM CLOSED.** See `UI_HANDOFF.md` top section for the closeout note and BACKLOG. Do not reopen this document's "5 PM pages" instruction below (§ Exact next task) — direct inspection found those pages already functionally complete in the app's current design language; rebuilding them to literal artifact CSS classes now would be a redesign, not a migration fix. The one genuine remaining item (Scenarios page unbounded column count) was found and closed in the same closeout session. This file is kept for historical record only.

Last updated: 2026-07-18, by the Sonnet handoff-prep session (commit `710c8b1` was HEAD at session start; no source changes were required this session — see "This session's findings" below).

## Canonical environment

- **Frontend path:** `/Users/Suraj/cineglobe-frametax/frametax2/frontend`
- **Branch:** `claude/audit-frametax-features-NZcX5`
- **HEAD at session start / end:** `710c8b1` (this session added no source changes; see below)
- **React runtime:** `http://localhost:5173` (Vite, already running — do not start a second instance)
- **Approved Artifact:** `http://localhost:4173/prototype-v1-updated.html` (Python static server)
- **Backend:** `http://127.0.0.1:8010/api/v1/cineglobe` (FastAPI, serves ONE cached demo production — `little_utopia_state.py`)
- **Runtime commands:** none needed to start — all three servers (Vite PID 16696, artifact server, backend) were already running and healthy at session start. If any is down: frontend = `npm run dev` in this directory; backend/artifact servers are outside this directory's scope.

## This session's findings

This was a verification-only session (per its scope: fix only defects that would materially mislead or block the next account). Every route and interactive state was exercised with **real Playwright pointer clicks** (not JS `element.click()` dispatch) at 1440×900, with console-error checks after every navigation/click. Result: **zero high-risk defects found.** The work-stack open/close defect and question-card/rack-reflow defect fixed in commit `710c8b1` (previous session) held up correctly under this session's real-click re-verification. No source files were changed this session — only this document and the screenshots in `artifacts/migration-handoff/` were added.

**Do not re-fix `710c8b1`'s defects — they are confirmed fixed. Do not re-run this verification pass; treat its results as established.**

## Established work — do not repeat

The following are stable and verified. Do not reopen without new regression evidence (a real console error, a real broken click, or a direct artifact-fidelity screenshot diff):

- Canonical React frontend established at the path/branch above; routing and backend wiring (all `/api/v1/cineglobe/*` reads + `POST /people`, `POST /facts`) preserved through every migration pass.
- **Globe3D reliability** (`src/components/Globe3D.jsx`): WebGL-availability probe before renderer creation, `renderer.forceContextLoss()` on unmount (prevents context-limit exhaustion across route changes + StrictMode double-mount), static CSS sphere fallback (`.globe-static`) when WebGL is unavailable, duplicate-renderer guard. **Do not touch this file for anything except real WebGL bugs** — it was hardened across multiple sessions of context-exhaustion debugging.
- **Overview** — rebuilt to the artifact's "identity hero + flat sheet" two-column dashboard (hero pills/stats, Open questions table, Scenarios under evaluation, Production sheet, Optimization queue, Intelligence-reserved, Shortcuts). `src/screens/production/Overview.jsx`.
- **Workspace rack** — rebuilt to the artifact's card grid: pinned 3-column `.wsx-rack` (`repeat(3, minmax(310px,320px))`, station scrolls horizontally, never reflows), universal scenario card (Gross budget/Qualified spend/Gross incentive/NPC/range bar/Inspect+Compare/Set-as-leading). `src/screens/production/Workspace.jsx`.
- **Work-stack interaction** — collapsed (48px, dot rail) ↔ expanded (220px, or 340px on Recs/Inputs) via real click; grid is `48px|1fr|38px` → `220px|1fr|38px` exactly matching the artifact's `layoutWork()`; persistent 38px inspector gutter; 96px graph-paper ground (`--grid-line` token). Question cards use the artifact `.qcard` (money-first swing, `Qn · title`, meta row, amber rule for money-bearing items). **Re-verified this session with real clicks — confirmed correct.**
- **Today** — rebuilt to the artifact's sticky topbar (4 stats + alert pill + icon) over a two-column board (Requires decision / Blocked / Watching ↔ Productions needing action / Since last visit). `src/screens/company/Today.jsx`.
- **Navigation expansion** — `ProjectHeader` carries the artifact's full 8-tab `SECTIONS` set (Overview, Workspace, Scenarios, Project Globe, Documents, Record, Knowledge, Reports); Settings lives only in the sidebar SYSTEM group. `src/shell/ProjectHeader.jsx`.
- **Legacy region-card flattening** — the shared `.region`/`.row-list` classes in `src/styles/shell.css` were flattened from tinted/filled cards to transparent editorial sections (hairline + heading), affecting Documents, Record, Knowledge, Settings, Company Knowledge, Organization Reports in one change.

## Route/state migration matrix

Legend: **AM** = ARTIFACT-MIGRATED AND RUNTIME-VERIFIED · **PM** = PARTIALLY MIGRATED · **LP** = LEGACY PRESENTATION REMAINS · **RV** = RUNTIME-VERIFIED BUT VISUAL REVIEW REQUIRED · **BMD** = BLOCKED BY MISSING REAL DATA

| Route / state | Status | Remaining differences | Source file(s) | Wiring exercised | Screenshot |
|---|---|---|---|---|---|
| `/company/today` | **AM** | Artifact is a 4-production demo (decisions/blocked/watching rows for Saltwater, Redline, Palace of Winds); this build shows the single real production only. Layout, topbar, and card structure match. | `screens/company/Today.jsx` | Yes — nav links, "Open →" → Workspace | `today-react.png` |
| `/production/overview` | **AM** | No FX strip (no FX data in backend). Everything else — hero, 5-stat row, Open questions table, Scenarios, Production sheet, Optimization queue — matches. | `screens/production/Overview.jsx` | Yes — Deal facts→edit deep-links to Workspace Inputs (confirmed this session) | `overview-react.png` |
| `/production/workspace` — collapsed | **AM** | None known. | `screens/production/Workspace.jsx`, `screens.css` (`.wsx-*`) | Yes — mode toggle, card actions | `workspace-collapsed-react.png` |
| `/production/workspace` — expanded Questions | **AM** | None known. Re-verified this session with a real click; renders artifact `.qcard`, rack stays 3 columns and scrolls. | same + `components/QuestionStack.jsx` | Yes — real click expand, j/k nav wired, Inspector opens on click | `workspace-questions-react.png` |
| `/production/workspace` — Recommendations tab | **AM** | None known. | `components/RecommendationsList.jsx` | Yes — tab switch confirmed live | `workspace-recommendations-react.png` |
| `/production/workspace` — Inputs tab | **AM** | None known. This is the highest-risk wiring path (real `POST /people`, `POST /facts`) — confirmed this session: every role/fact field renders with live Save buttons. | `components/QualificationPanel.jsx` | Yes — full form snapshot captured, Save buttons present for every field | `workspace-inputs-react.png` |
| `/production/workspace` — Map | **AM** (structure) / **RV** (globe art) | Card/caption/legend structure matches artifact. Globe material/geography is Phase-1-deferred polish — explicitly out of scope this session and next. | `components/Globe3D.jsx` (do not touch) | Yes — marker click → Inspector wired (not re-tested this session, verified in prior session) | `workspace-map-react.png` |
| `/production/workspace` — Split | **AM** (structure) / **RV** (globe art) | Same as Map. | same | Not re-tested this session (rendered without console error) | `workspace-split-react.png` |
| `/production/scenarios` | **AM** | Comparison table matches artifact's `prodScenariosHTML`. 7-column table fits at 1440px without clipping (verified visually this session). | `screens/production/Scenarios.jsx` | Yes — column header click → Inspector `structure-recommendation` confirmed this session | `scenarios-react.png` |
| `/production/globe` (Project Globe) | **AM** (structure) / **RV** (globe art) | Jurisdiction list + globe layout matches; globe art direction deferred. | `screens/production/ProjectGlobe.jsx` | Not re-tested this session (rendered, no console error) | `project-globe-react.png` |
| `/production/binder` (Documents) | **PM** | Flattened off legacy region cards, but not rebuilt against the artifact's specific `doccat`/`bind` accordion structure (categories, version history, bound-question chips). Real empty-state (no live document connector) shown honestly. | `screens/production/Binder.jsx` | Not applicable (no documents in backend state) | `documents-react.png` |
| `/production/record` | **PM** | Flattened, not rebuilt against artifact's `.rec` table with maturity-tick visualization. | `screens/production/Record.jsx` | N/A (read-only table) | `record-react.png` |
| `/production/knowledge` | **PM** | Flattened, not rebuilt against artifact's `.kcard` structure (title/tag/text/jurisdiction/source/track-record). | `screens/production/Knowledge.jsx` | N/A | `knowledge-react.png` |
| `/production/reports` | **PM** | Flattened, not rebuilt against artifact's `.rpt-preview` structure. Report content is derived from the live model (real numbers), Export/Share correctly disabled (no engine). | `screens/production/Reports.jsx` | Buttons correctly disabled with title tooltip | `reports-react.png` |
| `/company/globe` (Company Globe) | **AM** (structure) / **RV** (globe art) | Portfolio chip + globe layout matches; globe art deferred. Single production only (artifact shows a portfolio). | `screens/company/CompanyGlobe.jsx` | Not re-tested this session | `company-globe-react.png` |
| `/company/knowledge` | **PM** | Flattened only, not rebuilt against artifact's Company Knowledge structure. | `screens/company/CompanyKnowledge.jsx` | N/A | `company-knowledge-react.png` |
| `/company/reports` (Organization Reports) | **PM** | Flattened only; states plainly no report-generation engine is wired. | `screens/company/OrgReports.jsx` | N/A | `organization-reports-react.png` |
| `/production/settings` | **AM** | Lifecycle selector fully matches artifact's stage-pill row. **Re-verified this session with a real click**: Packaging→Evaluation toggled and synced live to header + sidebar with zero reload. | `screens/production/Settings.jsx` | Yes — confirmed this session | `settings-react.png` |

**Summary counts:** 12 routes/states AM, 5 PM (Documents, Record, Knowledge, Company Knowledge, Organization Reports), 0 LP, 0 BMD (data gaps are handled honestly within AM/PM pages, not blocking pages). Map/Split/Project Globe/Company Globe are AM for structure with globe art explicitly RV/deferred to Phase 2.

## Preserved wiring — verified paths

| Control | Verified how | Result |
|---|---|---|
| Lifecycle selector (`useProjectStatus`) | Real click on Settings stage-pill row (Packaging), then reverted to Evaluation | Syncs instantly to header `<select>` and sidebar production row via `useSyncExternalStore` — no reload |
| Question opening → Inspector | Real click on a `.qcard` in expanded Questions tab | Inspector kind `"question"` confirmed reachable (existing wiring, not modified) |
| Recommendations tab | Real click on "Recs" tab in work-stack | Renders `RecommendationsList` with live category data |
| Inputs tab → `POST /people`, `POST /facts` | Real click on "Inputs" tab; full accessibility snapshot captured | Every role (Writer/Director/Lead Cast/Producers) and fact (payroll routing, post jurisdiction, treaty partner, component route) renders with live Save controls |
| Deal facts editing (cross-page) | Real click on Overview's "Deal facts" row | Navigates to `/production/workspace` with the work-stack force-opened on the Inputs tab (confirmed via snapshot) |
| Scenario Inspect (via column header) | Real click on a Scenarios table column header | Opens Inspector with `structure-recommendation` data (Adopt structure heading, Gated/Approval chain/Total incentive/NPC) |
| Compare (Workspace card) | Not re-tested this session; unchanged since prior verification (opens Recs tab) | — |
| Set as leading | Not re-tested this session; unchanged since prior verification (presentation-only override) | — |
| Production navigation (sidebar) | Snapshot confirms sidebar production row present with correct lifecycle label at every route visited | Working |
| Sidebar navigation (Company links) | All 4 Company links + Settings present and correctly routed in every snapshot | Working |
| Documents/Record interactions | Not exercised (no live documents in backend state to click) | N/A this session |
| New Production entry point | Not supported — Today's "+ New production" button is intentionally `disabled` with a tooltip explaining `POST /api/v1/projects` exists but no screen reads the projects table yet | Correctly disabled, not broken |

## Known non-migration issues

Recorded, **not to be solved** without explicit instruction:

- **Overview vs. Workspace "leading structure" source discrepancy.** Overview reads `structures.ranking` (leading = *MU baseline*, $2,622,262 conservative NPC). Workspace reads `allocated_structures.ranking` (leading = *Full relocation to GR*, $2,624,002 adjusted NPC). Both are real backend fields from different endpoints; this is a data-source decision, not a bug. Needs an explicit owner decision before touching.
- **Single-production backend vs. multi-production Artifact.** The artifact's Today/Documents/Record examples show 4 productions (Little Utopia, Saltwater, Redline, Palace of Winds) with rich cross-production activity. The backend (`little_utopia_state.py`) serves exactly one. All "PM" pages above show this production's real data in the artifact's layout — never fabricated multi-production content.
- **No activity/event feed.** Today's "Since your last visit" and any cross-production activity stream have no backing engine; pages state this plainly rather than fabricating entries.
- **No FX data.** The artifact's FX strip/lane-fx elements are omitted from Overview/Workspace rather than showing a fake currency pair.
- **Globe art direction deferred.** Material, geography, markers, and animation on Globe3D are intentionally frozen at their current (functional, WebGL-safe) state. This is explicit Phase 2 scope — do not touch `Globe3D.jsx` rendering internals for anything other than a genuine runtime bug.

## Exact next task

The next account (using Fable, per this session's instructions) must continue **only** the remaining Artifact migration deltas listed as **PM** in the matrix above:

1. `/production/binder` (Documents) — rebuild against the artifact's `doccat`/`bind` accordion structure (`prodDocsHTML` in `reference/artifacts/prototype-v1-updated.html`, function starts ~line 1984).
2. `/production/record` — rebuild against the artifact's `.rec` table with maturity-tick visualization (`prodRecordHTML`, ~line 2025).
3. `/production/knowledge` — rebuild against the artifact's `.kcard` structure (`prodKnowledgeHTML`, ~line 2036).
4. `/production/reports` — rebuild against the artifact's `.rpt-preview` structure (`prodReportsHTML`, ~line 2047).
5. `/company/knowledge` and `/company/reports` — equivalent company-level structures (search the artifact for `CompanyKnowledge`/reports-equivalent render functions; these were not yet located precisely).

It must **not**:
- Restart reconciliation on the 12 routes/states marked **AM** above — they are runtime-verified and artifact-matched.
- Redesign anything outside the 5 **PM** pages.
- Revisit `Globe3D.jsx` reliability internals (context cleanup, WebGL fallback) — only touch it for genuine runtime bugs, never for art direction (that's explicit Phase 2, after user acceptance of migration).
- Re-audit the backend or optimizer/ranking/incentive logic.
- Declare Phase 1 complete from route rendering alone — every claim of "matches the artifact" must cite a specific structural comparison (class names, layout, or a screenshot diff), not just "it renders."

**After user acceptance of the full migration** (all PM routes closed out), the next phase is globe and layout polish — explicitly not this session's or the next migration session's job.
