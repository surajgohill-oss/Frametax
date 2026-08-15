# Legacy UI Route Cutover — Closeout

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`

## Gate

**`PROJECT_WORKSPACE_ROUTE_CUTOVER_ACCEPTED`**

## The defect, reproduced first (not assumed)

The generic project Workspace built in `ccb24eb` existed and worked, but no *normal* navigation path led to it for Little Utopia. Following the app's own UI — not a hidden URL — every ordinary route into "the production" still landed on the old, Little-Utopia-only `/production/*` experience. Six separate entry points were found, all reachable from normal clicking:

| # | File | What it did |
|---|---|---|
| 1 | `shell/Sidebar.jsx` | The persistent "Productions" row (always visible, every page) navigated to `/production/overview` |
| 2 | `shell/Sidebar.jsx` | The "Settings" link (SYSTEM group) pointed at `/production/settings`, itself a Little-Utopia-only demo page |
| 3 | `screens/company/Today.jsx` | The dashboard's Production Slate row (`route: "/production/overview"`) |
| 4 | `screens/company/Today.jsx` | "View all questions →" navigated to `/production/workspace` |
| 5 | `screens/company/CompanyGlobe.jsx` | Portfolio chip click, globe point click (2nd click), and "Open production →" — all three navigated to `/production/overview` |
| 6 | `screens/company/ProjectRecord.jsx` | Little Utopia's primary CTA, labeled "Open Production →", navigated to `/production/overview` instead of the generic Workspace |

`Today` (the landing page after `/`) and `Sidebar` (rendered on every route) are the two entry points a user hits first and most often — this is exactly the path the reported screenshot came from.

## Route architecture — before and after

**Before:** App.jsx registered 8 individual legacy routes (`/production/overview`, `/production/workspace`, `/production/scenarios`, `/production/globe`, `/production/reports`, `/production/binder`, `/production/knowledge`, `/production/settings`), each rendering its own Little-Utopia-only screen component, each independently reachable from the 6 entry points above.

**After:** One wildcard route, `<Route path="/production/*" element={<LegacyProductionRedirect />} />`, replaces all 8. `LegacyProductionRedirect` (new file, `shell/LegacyProductionRedirect.jsx`) resolves the current production's `project_id` via the existing `getProduction()` call (`/api/v1/cineglobe/production`, the one real mapping from the legacy demo state to the actual `Project` row — same source `Sidebar`/`Today`/`CompanyGlobe` already used) and issues `<Navigate to={\`/projects/${projectId}/workspace\`} replace />`. No project identity is hard-coded in the redirect — if the served production ever changes, the redirect target changes with it automatically. Every one of the 6 entry points above now targets `/projects/${production.project_id}/workspace` directly (skipping the redirect hop where the `project_id` was already in hand) or lands on the redirect (for any URL a user might still have saved/typed).

The 8 legacy screen component files (`screens/production/Overview.jsx` etc.) are **untouched** — not deleted, not modified. They are simply no longer routed to. This satisfies the explicit instruction not to delete large legacy components while still making them unreachable through normal navigation.

## Little Utopia — normal entry, generic Workspace

**Normal route:** `Today` dashboard (landing page) → Production Slate row, or the always-visible Sidebar "Productions" row → generic Workspace, directly, no redirect hop.

Confirmed live:
- Title: **"The Little Utopia"**
- Budget: **$4,364,393**
- Base/winner: **Mauritius (MU)**
- NPC: **$3,057,795** (displayed; the underlying canonical value is $3,057,794.90, unchanged — not recalculated this phase)
- Overview, Script, Budget, World tabs all functional (same as the prior phase's closeout — untouched this phase)
- Refresh / direct URL to `/projects/{id}/workspace` preserves state
- Directly hitting the OLD path `/production/overview` in the address bar (reproducing the original screenshot's URL) now transparently redirects to the same generic Workspace, confirmed live — the old screen never renders, not even for a frame beyond the brief network-resolution loading state
- `/production/binder` and `/production/settings` also confirmed redirecting to the same Workspace

## FVD — normal entry, generic Workspace (regression check)

**Normal route:** Company Library → search/click "F#K Valentine's Day" → Project Record → "Enter Workspace →".

Confirmed live:
- Title: **"F#K Valentine's Day"**
- Budget: **$4,517,687**
- Base: **Greece (GR)**
- Script tab: 99 scenes / 38 characters (SA-1 data, unchanged)
- Budget tab: real budget, unchanged
- World tab: canonical evaluation, unchanged
- Tab navigation (World → Budget) confirmed to preserve `project_id` — stayed on FVD throughout, never fell back to Little Utopia
- Refresh (forced full reload) preserves FVD's state exactly

## Sidebar active-state fix (found during implementation)

`Sidebar.jsx`'s `onProduction` boolean (drives the "Productions" row's active/highlighted styling) was keyed only to `location.pathname.startsWith("/production")`. Since normal navigation no longer visits any `/production/*` path, this would have made the sidebar row permanently un-highlighted even while genuinely viewing Little Utopia's own Workspace. Fixed by also matching the new route: `location.pathname.startsWith(\`/projects/${production.project_id}/workspace\`)`. Verified this is exactly the kind of "exact frontend data-loading/UI defect exposed by the cutover" the task scope permits fixing — it is a direct, mechanical consequence of the routing change itself, not new functionality.

## What was deliberately NOT changed

- **`AppShell.jsx`'s `ProjectHeader` gating** — still keyed to `/production` prefix only. Left unchanged: `ProjectHeader` is the legacy shell's own header component and must not render on `/projects/*/workspace` (which has its own header built into `ProjectWorkspace.jsx`). Since `/production/*` now immediately redirects, `ProjectHeader` is structurally unreachable through normal navigation regardless.
- **The two "Documents →" deep-links** inside `ProjectRecord.jsx`'s `MaterialsPanel` and Documents tab (`onClick={() => navigate("/production/binder")}`, served-production only) — left as literal `/production/binder` calls. They now safely resolve through the wildcard redirect into the generic Workspace (verified — no dead link, no old UI), though the specific promise in their surrounding copy ("Full document management... lives in Documents →") is no longer literally delivered by that click, since the redirect target is the Workspace root, not a documents-specific view. Flagged here rather than silently left, but not rewritten — copy/microcopy changes were out of this task's explicit routing-only scope, and the actual acceptance criterion ("old UI not reachable through normal navigation") is met either way.
- **Backend, canonical evaluation, economics, optimizer, MFNI, SA-2, budget estimation, Script Summary design** — none touched, per the hard rules. No backend file in this batch's diff.

## Focused tests

New: `frametax2/frontend/tests/route-cutover.test.mjs` (6 tests, same `node --test` + source-level-assertion convention as the pre-existing `globe-invariants.test.mjs` — this project has no DOM/browser test harness):

1. `App.jsx routes /production/* through one wildcard redirect, not eight legacy pages`
2. `LegacyProductionRedirect resolves project_id from the API, never hard-codes Little Utopia's UUID`
3. `Sidebar's Productions row navigates by project_id, not a literal legacy path`
4. `CompanyGlobe's three navigation points target the generic Workspace`
5. `Today.jsx's production slate route and question link target the generic Workspace`
6. `ProjectRecord's served-production primary action opens the generic Workspace, not legacy /production/overview`

Full suite (`npm test`): **55 passed, 0 failed** — the pre-existing 49 Globe-invariant tests plus the 6 new ones, confirming no regression in unrelated frontend logic.

## Files changed

- `frametax2/frontend/src/App.jsx` — 8 legacy routes replaced with one `/production/*` wildcard redirect; unused legacy screen imports removed (files themselves untouched)
- `frametax2/frontend/src/shell/LegacyProductionRedirect.jsx` (new) — resolves `project_id`, redirects into the generic Workspace
- `frametax2/frontend/src/shell/Sidebar.jsx` — Productions row navigates by `project_id`; active-state highlight fixed for the new route
- `frametax2/frontend/src/screens/company/CompanyGlobe.jsx` — 3 navigation points fixed
- `frametax2/frontend/src/screens/company/Today.jsx` — 2 navigation points fixed
- `frametax2/frontend/src/screens/company/ProjectRecord.jsx` — served-production primary CTA now opens the generic Workspace directly (relabeled "Enter Workspace →", collapsing the previous duplicate button)
- `frametax2/frontend/tests/route-cutover.test.mjs` (new)

## Remaining legacy accessibility

None through normal navigation. The only way to reach any `/production/*` path at all is by typing it directly into the address bar or having it saved from before this change — and doing so now redirects transparently into the generic Workspace rather than rendering the old UI. The two "Documents →" deep-links (noted above) are the sole remaining spots where old copy references a `/production/*` path; clicking them is safe (redirects, doesn't render legacy UI) but the specific document-management view they used to promise is not yet replicated generically — an honest, disclosed gap, not a defect that leaves old UI reachable.

## Gate detail

Met: normal Little Utopia navigation (Sidebar, Today dashboard, Company Globe, Project Record) uses the generic Workspace; normal FVD navigation (Library → Record → Enter Workspace) uses the generic Workspace; the old Little Utopia UI is not reached through any normal product navigation, confirmed live including a direct hit on the exact legacy URL from the original report; active `project_id` is preserved across tab navigation and full-page refresh for both projects; Little Utopia's budget/base/NPC render unchanged from the canonical served values; FVD's budget/base/script/budget/world render unchanged; zero optimizer/economics files touched; focused tests pass (55/55).
