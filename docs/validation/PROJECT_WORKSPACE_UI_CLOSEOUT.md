# Project Workspace UI Cutover — Closeout

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`

## Gate

**`PROJECT_WORKSPACE_UI_RUNTIME_ACCEPTED`**

## Prior UI architecture (before this phase)

- The main Workspace/Globe/Optimizer-Overlay experience (`/production/*`, driven by `useCineGlobe()`) called eight fixed `/api/v1/cineglobe/*` endpoints with **no `project_id` parameter at all** — it was implicitly Little Utopia, not project-driven. `ProjectRecord.jsx` detected this (`project.is_served_production`, comparing `project.title` against `little_utopia_state.PRODUCTION_NAME`) and routed only Little Utopia's "Open Production →" button there.
- Every other project (including FVD, after Phase 2's canonical evaluation cutover) had a working Project Record page but **no Workspace to enter at all** — "Begin Evaluation" ran and persisted real results, but there was nowhere in the UI to see them beyond the Project Record's own compact Analysis panel.
- `Overview.jsx` / `Workspace.jsx` / `ProjectGlobe.jsx` (the rich `/production/*` pages) consume a much deeper shape than the canonical evaluation persists — an account-level QPE register (`pkg.register`), `economics` controls, `production.physical_requirements`, per-structure `.segments[]` — none of which any generically-ingested project (FVD included) has. Force-fitting that shape generically was ruled out as unachievable without either crashing on missing fields or fabricating data (forbidden by Part D).

## Final architecture (built this phase)

One new, genuinely generic view adapter and one new route, added alongside (not replacing) the existing `/production/*` pages:

```
GET /projects/{project_id}/workspace
  -> app/services/project_workspace_view.py::build_project_workspace_view()
       reads Project, ProductionStructure / StructureCalculationResult
       (scoped to the leading structure's own input_fingerprint — the
       current canonical evaluation, from Phase 2's evaluate_project()),
       BudgetDocument / BudgetLineItem, the existing SA-1 script pipeline
       (resolve_active_screenplay + Scene/Character)
       -> ONE response: { project, evaluation, budget, script }
```

`app/api/v1/workspace.py` is a thin route wrapper: it never triggers evaluation and never computes economics, only reshapes what `evaluate_project()` already committed — the same "adapter, not a second engine" boundary as `optimizer_handoff.py` and `canonical_project_economics.py`.

Frontend: one new file, `frontend/src/screens/project/ProjectWorkspace.jsx`, mounted at `/projects/:projectId/workspace`. Four tabs — Overview / Script / Budget / World — all driven by `project_id` from the URL, all rendering only what the adapter actually returns (no fabricated fields). Built from the same CSS classes already proven generic in `ProjectRecord.jsx` (`.rec-screen`, `.rec-idband`, `.rec-tabs`, `.ovx-sec`, `.stat`, `.rec-cols`, `.chip`) rather than force-fitting the old `/production/*` component tree — no new visual language introduced.

## Candidate UI status — the generic Abu Dhabi presentation fix

Derived from two fields `canonical_evaluation.py` already persists on every `StructureCalculationResult` (`candidate_status`, `relocation_cost_normalized`) — never a new judgment, never a per-jurisdiction rule:

```
candidate_status=PRICED,  relocation_cost_normalized=True   -> COMPARABLE
candidate_status=PRICED,  relocation_cost_normalized=False  -> REVIEW_REQUIRED
candidate_status=UNPRICEABLE_AUTHORITY_INSUFFICIENT          -> UNPRICEABLE
```

Mapped onto the **existing** four-state Globe visual system (`GLOBE_SEMANTIC`/`STATUS_HEX` from `lib/globeData.js`) rather than inventing a fifth state: `COMPARABLE -> gold`, `REVIEW_REQUIRED -> amber`, `UNPRICEABLE -> silver`. Same rule, same component, every project — confirmed live for both FVD and Little Utopia (identical 1/29/80 comparable/review-required/unpriceable split on both).

**Abu Dhabi (`AE-AD`), specifically:** classified `UNPRICEABLE_AUTHORITY_INSUFFICIENT` by the backend (unchanged from Phase 2 — no jurisdiction research or rule change made this phase). Confirmed live in the World tab: it renders under **"Unavailable" / "Needs validation"**, not under "Comparable" and not as a ranked recommendation — the presentation defect Phase 2 explicitly reported as unresolved is now fixed, generically, for every project.

One real bug found and fixed while verifying this: unpriceable candidates never get a `jurisdiction_allocations` row built (no allocation is computed for an authority-insufficient jurisdiction), so `jurisdiction_code` resolved to `null` for 3 of 110 candidates on each project — including Abu Dhabi — meaning they were correctly listed but silently absent from the Globe itself (`WorldTab` skips plotting a candidate with no code). Fixed with a display-only fallback: when the DB-resolved code is unavailable, parse it from the structure's own name (`"Full relocation to AE-AD"` — text already present, no new data, no economics). Verified live: Abu Dhabi's `jurisdiction_code` now resolves to `"AE-AD"`.

## Little Utopia — same Workspace, not a separate one

`ProjectRecord.jsx`'s action row now shows **both** buttons for Little Utopia: the existing "Open Production →" (unchanged, still goes to the richer legacy `/production/*` experience) and a new "Enter Workspace →" (goes to `/projects/{id}/workspace`, the same generic route FVD uses). Confirmed live: Little Utopia's generic Workspace renders through the identical component tree as FVD's — same tabs, same CSS, same adapter — with its own real data:

- Budget: **$4,364,393** ✓ (unchanged)
- Base jurisdiction: **MU** ✓
- Leading structure / NPC: **$3,057,795** ✓ (exact accepted value, unchanged from Phase 2)
- Candidate accounting: 1 comparable / 29 review-required / 80 unpriceable — identical distribution shape to FVD, proving the classification rule is genuinely project-agnostic
- Script tab: honestly empty (`"structural breakdown not yet available"` — Little Utopia's screenplay has not been SA-1 parsed). **Not fabricated** — the adapter reports what's actually there, per Part D.
- Budget tab: Little Utopia's own real 44-line budget document, correctly totaling $4,364,393.

There is no `LittleUtopiaWorkspace` vs `FVDWorkspace` component split anywhere in the new code. One `ProjectWorkspace.jsx`, parameterized by `project_id`.

## Part P — special-path audit

Searched the new/changed files for identity-based branching (`if project === Little Utopia`). Found one: `project_workspace_view.py` carried an `is_served_production` field (`project.title == little_utopia_state.PRODUCTION_NAME`, via an inline `__import__`) in the generic workspace response. **It was never read by the frontend** (`ProjectWorkspace.jsx` never references it) — dead, but exactly the kind of hard-coded-identity logic Part P asks to remove. Deleted, along with the now-unused import.

The **only** remaining `isServedProduction` check in the touched surface is `ProjectRecord.jsx`'s existing, pre-existing (not introduced this phase) routing of the legacy "Open Production →" button — which correctly reflects that the deep `/production/*` experience genuinely only has Little Utopia's curated demo data wired up (Phase 2's own explicitly-deferred blocker, Rule 1 out of scope to reopen here). It no longer gates anything about the **new** generic Workspace, which every project reaches identically by `project_id`.

## FVD pages — status

| Page | Status | Evidence |
|---|---|---|
| Overview | **PASS** | Title, budget $4,517,687, base GR, "Evaluation complete", leading structure GR $3,072,027, incentive $1,445,660, candidate accounting 1/29/80 |
| Script | **PASS** | `F#K Valentine's Day- pdf.pdf`, 99 scenes, 38 speaking characters, 55 locations — real SA-1 output, functional route, placeholder presentation as instructed (full redesign deferred) |
| Budget | **PASS** | `V-BRAT_V8_Greece_041224 TOPSHEET.pdf`, 34 real line items, total $4,517,687 matching the source document exactly |
| World / Evaluation | **PASS** | Globe renders via the existing `Globe3D` component; comparable/review-required/unpriceable lists match the Overview's candidate accounting exactly (same `evaluation` object, no second data source); Abu Dhabi confirmed under Unavailable |
| Documents | **Reused, not duplicated** | `ProjectRecord.jsx`'s existing Documents tab already lists FVD's 4 real materials (artwork/budget/deck/screenplay) generically — the new Workspace's "← Project Record" link (top of every tab) reaches it in one click. Building a second Documents surface inside the new Workspace would duplicate a page that already works, which Part J explicitly says not to do ("do not invent empty pages... retain existing generic pages that already work") |
| Optimizer overlay | **PASS** | Same `evaluation.comparable/review_required/unpriceable` arrays drive both the Overview counts and the World tab's Globe + candidate lists — one source, confirmed by code (no second fetch in `WorldTab`) |

No Little Utopia data appeared anywhere in the FVD flow (title, budget, jurisdiction, NPC, candidate list all FVD-specific throughout).

## Little Utopia — regression pass

| Check | Status |
|---|---|
| Title | **PASS** — "The Little Utopia" |
| Budget | **PASS** — $4,364,393 |
| Base jurisdiction | **PASS** — MU |
| NPC | **PASS** — $3,057,795 (exact accepted value) |
| Same Workspace components as FVD | **PASS** — identical route, identical tab set, identical CSS classes |
| Canonical evaluation consumed | **PASS** — same adapter, same `evaluate_project()` persistence layer |
| Optimizer overlay canonical | **PASS** — same `evaluation` object as Overview |
| Navigation unbroken | **PASS** — Project Record → Enter Workspace → tabs → back to Project Record, all functional; legacy "Open Production →" untouched and still works |

## Entry flow (Part L)

Company Library → Project Record (FVD or Little Utopia) → Begin/Re-run Evaluation → **"Enter Workspace →"** button appears once `analysis.evaluation_begun` is true → generic Workspace → Overview/Script/Budget/World tabs, all preserving `project_id` in the URL. No hidden URL, no manual DB action. Confirmed live for both projects, including direct-URL navigation (`/projects/{id}/workspace`, the refresh-equivalent case) — both load correctly with no dependency on prior client-side navigation state.

## Tests

New: `tests/test_project_workspace_view.py` (4 tests, all passing against the real, live FVD and Little Utopia projects — no fixtures, no giant validation suite, per Part Q):

1. `test_unknown_project_returns_not_found`
2. `test_fvd_workspace_view_is_correct_and_self_contained` — title, budget, base jurisdiction, no `is_served_production` field, script/budget totals
3. `test_little_utopia_workspace_view_uses_the_same_adapter` — same shape, LU's own real values, honest empty script state
4. `test_candidate_classification_is_generic_not_per_jurisdiction` — locks in the Abu Dhabi fix: `AE-AD` must be `UNPRICEABLE` on every project, never `COMPARABLE`/`REVIEW_REQUIRED`; count fields match list lengths exactly

Re-ran the pre-existing canonical evaluation/economics suites (`test_canonical_evaluation.py`, `test_canonical_project_economics.py`, `test_project_evaluation.py` — 16 tests) to confirm the `is_served_production` removal and the jurisdiction-code fallback caused no regression in the layers below the new adapter: all pass.

No backend economics files changed (only the new view adapter, which computes nothing) — no full backend suite rerun, per Part Q ("backend tests only if backend changed... no global optimizer validation rerun").

## Browser runtime acceptance

Traced live for both projects, including a defect found and fixed mid-verification (the `jurisdiction_code` gap above):

- **FVD:** Company Library → search → Project Record (budget $4,517,687, base GR, 110 structures, NPC $3,072,027 all confirmed) → "Enter Workspace →" clicked → Overview/Script/Budget/World all confirmed with real, correct, non-fabricated data → direct-URL reload confirmed identical state → Abu Dhabi confirmed under Unavailable, not ranked.
- **Little Utopia:** Project Record confirmed unchanged ($4,364,393 / MU / $3,057,795) → both "Open Production →" and new "Enter Workspace →" present → generic Workspace confirmed rendering through the same component tree with LU's own data → Script tab's honest empty state confirmed → Budget tab's real 44-line document confirmed → World tab confirmed rendering the same Globe/overlay pattern as FVD.

## Files changed

- `app/services/project_workspace_view.py` (new) — the view adapter
- `app/api/v1/workspace.py` (new) — thin route wrapper
- `app/main.py` — registers the new router
- `frontend/src/api.js` — `getProjectWorkspace()`
- `frontend/src/screens/project/ProjectWorkspace.jsx` (new) — the generic Overview/Script/Budget/World Workspace
- `frontend/src/App.jsx` — `/projects/:projectId/workspace` route
- `frontend/src/screens/company/ProjectRecord.jsx` — "Enter Workspace →" action, shown once evaluation has begun (both served and non-served projects)
- `tests/test_project_workspace_view.py` (new)

## Gate detail

Met: one project-driven Workspace (not per-project component split); FVD Workspace header/Overview/Script/Budget/World/Documents(via reuse)/optimizer-overlay all functional and correct; canonical evaluation consumed exclusively (never `build_allocated_structures()`); Abu Dhabi/unpriceable presentation corrected generically; Little Utopia renders through the identical Workspace with its NPC/budget preserved exactly; the one discovered identity-based special-case (`is_served_production`) removed; browser verification passed for both projects including refresh/direct-URL cases; focused tests pass.

Deferred, as explicitly instructed (STOP conditions honored): full Script Summary page design, SA-2, MFNI, budget estimation. The existing richer `/production/*` Little-Utopia-only experience is untouched and still reachable via its own button — not redesigned, not removed, not regressed.
