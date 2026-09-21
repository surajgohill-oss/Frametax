# Codex Frontend Workspace / Globe Runtime Audit

**Verdict: `FRONTEND_WORKSPACE_GLOBE_NOT_ACCEPTED`**

The current backend projections and Globe candidate-pool selectors are materially broader than the Manitoba-only behavior reported by the user, and the rendered scenes do change when a different candidate is selected. Acceptance nevertheless fails because transient selection/Inspector state crosses project boundaries, the Full Globe Inspector does not identify or reconcile the clicked candidate, the shared mode crosses projects, and an existing persisted leading structure is not initialized into the client selection.

## 1. Environment and method

| Item | Verified value |
|---|---|
| Repository / worktree | `surajgohill-oss/Frametax` / `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` |
| Branch | `claude/global-optimizer-remediation` |
| Audited SHA (local = remote before audit commit) | `51a3e302ec925400ef395d4d94e433ef392f171b` |
| Frontend / backend | `http://localhost:5173` / `http://127.0.0.1:8010` (both HTTP 200) |
| Backend database | `frametax2_claude_optimizer_acceptance_20260919` (both uvicorn processes; credentials redacted) |
| Served engine | `canonical-1.93.0` for all four projects |
| Worktree baseline | Clean except intentional untracked `.backend_gd_wire.log` and `.frontend_gd_wire.log` |
| Audit method | One browser session, one pass per project, one bounded read-only projection script, no regeneration or tests |

Evidence classification: served/API projection and source traces are **STATIC_VERIFIED**; observations made in the actual browser are **RUNTIME_VERIFIED**.

## 2. Project identity and freshness

| Project (ID) | Home | Current fingerprint | Persisted leading | Canonical selected |
|---|---:|---|---|---|
| The Little Utopia (`fa5cade5-0669-4816-bfe6-72146f8d3bae`) | MU | `cc66cf525f213e43f2eedb3ab625cd8c8f97440965d4dae897cefaa8da9e582b` | none | none |
| Bad Hombres (`4355ae88-a636-4c18-af60-ad73b2646124`) | US-NM | `29be54c5ca6c65a90c1a5efa33c085804f2b1b54b0ef7e2591a8ad03bcc11a9c` | `32262228-3c58-4c28-b85b-2d4af573a88b` | `4d06829a-6130-40fd-a514-4e9702e0e28b` |
| F#K Valentine's Day (`6c6f1c13-2d49-4bbc-bafb-2a12efa93112`) | GR | `b171ef7c72dd84053582d394b35af10ef7bba33d8497e40a9fae9d3e48389e41` | none | none |
| Lips Like Sugar (`ab10b319-978e-44d3-9331-af2a5f2cccc2`) | US-CA | `bdad763946a0b2fcb2e92c425c2452fca16cd190e7ffd413f577d5816384449f` | `469b6864-7c50-46e6-a51a-342790a9305f` | same as leading |

No project was evaluated or regenerated. All inspected payloads were already-current `canonical-1.93.0` generations.

## 3. Workspace six-card contract

Notation: `jurisdiction/classification · structure-id-prefix · economic-identity-prefix · NPC`.

| Project | Single Jurisdiction: anchor + slots 2–6 | Optimizer: anchor + slots 2–6 |
|---|---|---|
| Little Utopia | MU/SINGLE `543e65ad` `c6cb4a73` $3,791,333.30; CA-ON/STACK `5c2645df` `ef6ace7f` $2,215,669.12; CA-MB/SINGLE `ad05b911` `78fadae5` $3,269,304.80; MT/SINGLE `a1ec6e15` `0f3bc4f8` $3,281,254.20; GR/SINGLE `4908bc28` `00082482` $3,394,127.24; IT/SINGLE `70a0977d` `3d70799e` $3,421,114.60 | MU anchor; CA-MB+CA-NL+IT/HYBRID `559a49ce` `89f54327` $2,539,002.60; CA-NL+CA-MB+IT `4a4a3dc2` `65766bbd` $2,736,462.40; IT+CA-MB+CA-NL `37f99f7d` `7b985e04` $2,736,462.40; GR+CA-MB+CA-NL `b5d9217c` `db4857d1` $2,736,462.40; US-AL+CA-MB+CA-NL `2c51eba9` `25384654` $2,936,547.20 |
| Bad Hombres | US-NM/SINGLE `4d06829a` `1ba0245f` $1,885,112.75; CA-ON/STACK `ad61c591` `ef6ace7f` $1,216,573.27; CA-MB/SINGLE `133a0c5d` `78fadae5` $1,407,584.55; CA-NL/SINGLE `cedde04e` `9e817a34` $1,526,966.60; US-AL/SINGLE `24bb2fe4` `648c8311` $1,646,348.65; US-IL/SINGLE `b628137a` `9095cb46` $1,646,348.65 | US-NM anchor; CA-MB+CA-NL+IT/HYBRID `da3b394b` `bb142bd7` $1,413,232.45; CA-MB+CA-NL+US-NM `357d5712` `7d0d13fc` $1,413,982.45; CA-MB+IT+US-NM `fa53879a` `f9238eb6` $1,413,982.45; CA-MB+CO+US-NM `4bae20a0` `853c1dd6` $1,419,380.35; CA-MB+US-AL+US-NM `32262228` `93061074` $1,419,380.35 |
| F#K Valentine's Day | GR/SINGLE `ccba6d23` `d73dd2fc` $3,072,027.16; CA-ON/STACK `ddb09395` `ef6ace7f` $2,556,030.86; CA-MB/SINGLE `d70d6565` `78fadae5` $3,183,389.90; IT/SINGLE `99fae6b5` `3d70799e` $3,317,551.80; CA-QC/STACK `cb36ffce` `2016f5a7` $3,321,377.62; CA-NL/SINGLE `1f5035b1` `9e817a34` $3,368,451.80 | GR anchor; CA-MB+CA-NL+IT/HYBRID `dbcf5bda` `f8bced42` $2,853,139.90; same participants `93efaa5d` `3f413ea3` $2,859,952.20; same participants `fc2913ed` `c299b7c5` $2,859,962.20; CA-MB+CA-NL+CA-ON+IT `a4a8d8bf` `006dd109` $2,860,962.20; IT+CA-MB+CA-NL `b7676042` `34fcf2d4` $3,029,869.50 |
| Lips Like Sugar | US-CA/SINGLE `469b6864` `e8c60c35` $8,524,375.10; CA-ON/STACK `245fc666` `ef6ace7f` $6,745,317.38; CA-MB/SINGLE `dce97226` `78fadae5` $7,536,009.70; CA-NL/SINGLE `767e0773` `9e817a34` $8,030,192.40; IT/SINGLE `20e2067a` `3d70799e` $8,256,160.67; GR/SINGLE `002b41ff` `00082482` $8,290,761.26 | US-CA anchor; CA-MB+CA-NL+IT/HYBRID `601a8a8f` `1e6c80a5` $7,548,348.40; CA-MB+CA-NL+US-CA `406eaca1` `6c04b126` $7,550,348.40; CA-MB+IT+US-CA `67504c06` `b2915311` $7,550,348.40; CA-MB+CA-NL+US-CA `a16a2b16` `8b36da5b` $7,558,687.10; CA-MB+IT+US-CA `3ca43ffa` `98aeaa8b` $7,558,687.10 |

The Normal racks contain six distinct jurisdiction winners. Optimizer repeats a primary jurisdiction only when the full economic identity and routed component assignment differ. The slot-6 selectors were project-and-mode scoped; slots 1–5 did not change.

## 4. Project × surface × mode runtime matrix

| Project | Workspace rack | Full Project Globe | Workspace Map | Workspace Split |
|---|---|---|---|---|
| Little Utopia | Both modes rendered the exact six above | Single showed 78 jurisdiction winners; Optimizer default `559a49ce` rendered CA-MB/CA-NL/IT. Selecting Alabama changed scene to US-AL/CA-MB/CA-NL, but Inspector described only Manitoba | Same `buildGlobeView` contract; current optimizer scene matched Full Globe | Same points/arcs and selected scenario contract as Map |
| F#K Valentine's Day | Both modes rendered the exact six above | Arrived in leaked Optimizer mode; default `dbcf5bda` rendered CA-MB/CA-NL/IT. Selecting Greece→Romania changed scene to GR/RO | Selected GR/RO candidate persisted; map showed GR/RO, one route, and matching scenario economics | Same GR/RO candidate, points and route as Map |
| Bad Hombres | Both modes rendered the exact six above, but initial UI marked US-NM canonical baseline rather than persisted leading `32262228` | Arrived in leaked Optimizer mode; prior FVD ID was absent, so resolver correctly fell back to BH pool[0] `da3b394b` and rendered CA-MB/CA-NL/IT | Matched Full Globe candidate and scene | Matched Map; stale FVD Inspector remained visible |
| Lips Like Sugar | Both modes rendered the exact six above | Arrived in leaked Optimizer mode; default `601a8a8f` rendered CA-MB/CA-NL/IT | Matched Full Globe candidate and scene | Matched Map; stale FVD Inspector remained visible |

The rendered app proved that a materially different selection changes the active candidate, marker jurisdictions and route endpoints. The principal parity failure is the global Inspector/state overlay, not the scene-data adapter.

## 5. Manitoba diagnosis

Manitoba is genuinely the primary jurisdiction of the first/current lowest-NPC **optimizer-admissible** scenario on all four current productions. It is not merely a camera fallback or a participant mislabeled as primary. `admissibleForMode()` returns the optimizer family pool in canonical order, and `buildOptimizerPathway()` selects a matching `leadingStructureId` or `pool[0]` (`frontend/src/lib/globeData.js:584-612`). The current `pool[0]` is Manitoba-anchored in each production.

The “only Manitoba” impression has two causes:

1. the first four or five optimizer cards often remain Manitoba-primary while changing routed components/economic identities; and
2. the Inspector chooses the first non-primary participant segment and can remain stale across projects, so its label/economics need not identify the active candidate.

It is **not** caused by candidate loss: choosing US-AL on Little Utopia changed the scene to US-AL/CA-MB/CA-NL, and choosing GR→RO on FVD changed it to GR/RO. Full Globe, Workspace Map and Workspace Split consumed the same `buildGlobeView()` data and agreed for the sampled FVD selection.

## 6. Candidate-family coverage

| Project | Bounded page (`SINGLE / STACKED / HYBRID`) | `top_by_structural_family` (`SINGLE / STACKED / HYBRID / OFFICIAL / COMBINED / MULTILATERAL`) | Normal pool | Optimizer pool |
|---|---:|---:|---:|---:|
| Little Utopia | 28 / 2 / 70 | 84 / 3 / 100 / 0 / 0 / 0 | 78 | 70 |
| Bad Hombres | 2 / 2 / 96 | 84 / 5 / 100 / 0 / 0 / 0 | 77 | 96 |
| F#K Valentine's Day | 3 / 4 / 93 | 82 / 5 / 100 / 0 / 0 / 0 | 76 | 93 |
| Lips Like Sugar | 2 / 1 / 97 | 85 / 5 / 100 / 0 / 0 / 0 | 78 | 97 |

Normal uses `best_per_jurisdiction`, not the bounded page. Optimizer uses the page plus the family backstop. No current executable family was lost from the pools. Official treaty, combined co-production and multi-principal/multilateral are genuinely empty for all four served generations; their absence is not a frontend defect. No retained conditional grant/fund candidate was present in the visible current optimizer pools.

## 7. Selection, isolation, overlays and parity

- **Selection changes work:** structure ID, markers and routes changed for LU US-AL and FVD GR/RO samples.
- **Project scene fallback is safe:** when a stale ID is not in the target project pool, `buildOptimizerPathway()` uses that project's `pool[0]`; scenes did not reuse another project's structure.
- **Project transient state is unsafe:** the LU/FVD Inspector survived Project Library and navigation into unrelated productions. Optimizer mode also survived LU→FVD→BH→LLS.
- **Overlay is not candidate-complete:** `selectStructure()` derives `routedTo` as the first participant unequal to `primary_jurisdiction` and opens an `allocation-segment` Inspector. The overlay therefore lacks the clicked candidate's structure ID, economic identity, classification, complete participant/program set, total incentive and NPC. In LU's Alabama sample the Inspector described Manitoba, not the Alabama-primary candidate.
- **Blank classification:** the Ontario stack's single rate is genuinely unavailable for a multi-program stack; the blank allocated-spend field is an adapter/overlay omission because QPE and candidate economics exist.
- **Cross-surface parity:** FVD's selected GR/RO candidate produced equivalent markers, one route, and economics in Full Globe, Workspace Map and Workspace Split. No scene-data divergence was observed. The shared stale Inspector remained the contradiction.

## 8. Defect ledger and remediation instructions

### FG-001 — P1 — Cross-project Inspector and selection-state leak

- **Affected:** all four projects; Project Library, Overview, Workspace Map/Split and Full Project Globe.
- **Expected:** navigation to another `projectId` closes or resolves transient state exclusively against that project.
- **Observed:** LU/FVD Inspector content remained visible through Project Library and BH/LLS; `leadingStructureId` and `selectedJurisdiction` are also global, though invalid leading IDs safely fell back at render time.
- **Responsible code:** `frontend/src/state/AppState.jsx:13-38` stores unscoped scalars; `frontend/src/App.jsx:28-73` mounts one provider above all routes.
- **Smallest correction:** key Inspector, leading ID and selected jurisdiction by project, or clear them in one route-aware effect whenever `projectId` changes.
- **Focused acceptance test:** open a candidate Inspector in LU, SPA-navigate through FVD/BH/LLS, and assert the Inspector closes or resolves to the target project and no source-project ID/jurisdiction remains.

### FG-002 — P1 — Full Globe Inspector is a participant segment, not the clicked candidate

- **Affected:** every multi-participant optimizer candidate on Full Project Globe; visible in LU US-AL+CA-MB+CA-NL.
- **Expected:** selected-card overlay identifies the exact structure/economic identity and reconciles classification, all participants/programs, incentive, QPE and NPC.
- **Observed:** the selected Alabama-primary candidate opened Manitoba's allocation segment. Overall identity/economics were absent.
- **Responsible code:** `frontend/src/screens/production/ProjectGlobe.jsx:198-232`, especially `participants.find(c !== primary)` and `openInspector("allocation-segment", ...)`.
- **Smallest correction:** open a structure-level Inspector payload for the clicked candidate, with nested routed-segment detail; do not infer the candidate's identity from its first non-primary participant.
- **Focused acceptance test:** click two optimizer cards with different economic identities and assert Inspector structure ID, identity, classification, participant/program set, QPE, incentive and NPC exactly match each served candidate and rendered scene.

### FG-003 — P2 — Workspace/Globe mode leaks across projects

- **Affected:** FVD, Bad Hombres and Lips Like Sugar after LU was switched to Optimizer; Workspace and Full Project Globe.
- **Expected:** each project restores its own saved/default mode, not the prior project's transient choice.
- **Observed:** one global `workspaceMode` remained Optimizer through LU→FVD→BH→LLS.
- **Responsible code:** `frontend/src/state/AppState.jsx:33-45`; unlike slot 6, mode is not keyed by project.
- **Smallest correction:** key mode by `projectId`, or reset it explicitly on project navigation.
- **Focused acceptance test:** switch LU to Optimizer, navigate without reload, and assert each target project opens its own default/saved mode while LU restores its previous mode when revisited.

### FG-004 — P2 — Persisted leading structure is not initialized into client selection

- **Affected:** Bad Hombres initially; all production surfaces that use `activeStructure()`.
- **Expected:** initial client selection honors `production.leading_structure_id=32262228-3c58-4c28-b85b-2d4af573a88b`, while disclosing canonical selected separately.
- **Observed:** the Workspace marked New Mexico baseline `4d06829a-6130-40fd-a514-4e9702e0e28b` as “Current leading structure”; `AppState.leadingStructureId` starts null and no frontend reader seeds it from the served production field.
- **Responsible code:** `frontend/src/state/AppState.jsx:21-27`; `frontend/src/lib/globeData.js:72-87` falls back from null to canonical selection. No production-screen source reads `production.leading_structure_id`.
- **Smallest correction:** initialize project-scoped leading selection from the served persisted leading ID on project load, then retain canonical selection as a distinct fallback/label.
- **Focused acceptance test:** load Bad Hombres directly and assert active ID/scene/current-leading badge resolve to `32262228...`; clear the producer override and assert fallback becomes canonical `4d06829a...`.

## 9. Acceptance conclusion

Candidate pools, six-card composition and sampled scene rendering are functioning and disprove a literal Manitoba-only data path. The frontend is not accepted because the selected-candidate truth shown to the producer is not project-isolated or candidate-complete, and an existing persisted leading choice is ignored at initialization.
