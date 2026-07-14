# CineGlobe — Architecture Summary

One-page map of the full pipeline: what's connected end-to-end, and what's built but not wired to a consumer. Detail lives in `BACKEND_HANDOFF.md` (backend) and `UI_HANDOFF.md` (frontend); this file is the connective diagram between them.

---

## Pipeline

```
BUDGET (real Little Utopia line items, source-document dollar amounts)
   │
   ▼
QUALIFICATION  (qualification_derivation.py + program_spend_rules.py doctrine ladder)
   │  per-jurisdiction register: build_little_utopia_register_for_jurisdiction()
   │  doctrine: OPEN_DEFAULT_INCLUDE / CLOSED_POSITIVE_LIST / HYBRID_CONDITIONAL
   │  4 executable jurisdictions: MU, MT, IE, GR (real statutory rate rules)
   │  211 catalog-only jurisdictions: profile exists, no doctrine/rate → never priced
   ▼
OPTIMIZER  (optimization_engine.py)
   │  ranks candidates by conservative_npc_usd
   ▼
COMPOSER  (production_structure_composer.py)
   │  builds JurisdictionSegment per candidate structure
   │  ⚠ has_register=True ONLY for the single baseline jurisdiction (always MU)
   │     → structurally caps priceable_pct<1.0, is_fully_priced=False for
   │       every multi-jurisdiction / co-production / treaty candidate
   │       (CONFIRMED ARCHITECTURAL CEILING — see roadmap #1 in BACKEND_HANDOFF.md)
   ▼
TREATY ENGINE (treaty_engine.py) ──── connected, produces real candidates
   │  e.g. PSC-FR-MU when treaty_partner_code elected via POST /facts
   │  same has_register ceiling applies — never reaches is_fully_priced=True
   ▼
SCENARIO ENGINE (production_scenario_engine.py) ──── connected
   │  POST /scenarios — real .notes explaining unpriced pathways
   ▼
ECONOMICS ENGINE  (mauritius_economics.py + production_normalization.py)
   │  floor/ceiling cases, financing, in-kind, travel (dual-delta), FX (live+historical)
   │  served on GET /economics, controlled via POST /economics/controls
   │  ⚠ NOT CALLED by frontend api.js — zero UI surface today
   ▼
RECOMMENDATION ENGINE  (production_recommendation_engine.py) ──── connected
   │  eligibility_gate_failed (hard threshold) vs cultural_test_gap (points, low-conf)
   │  evidence_reference / authority_reference / qualification_rationale per rec
   ▼
LEGAL ENGINE  (legal_engine.py / legal_authority_acquisition.py) ──── connected
   │  grey_area.grey_kinds + resolution_paths (6 concrete producer actions)
   │  legal_commit / committed_rule_id: permanently None by design
   │    (mock auto-resolution of GA-INKIND-FMV deliberately disabled — a real fix,
   │     not a bug: a demo must never silently resolve a genuine grey area)
   ▼
API LAYER  (app/api/v1/cineglobe.py, FastAPI)
   │  /production  /package  /recommendations  /structures  /legal
   │  /economics  (NEW: + available_funds, alternative_jurisdictions)
   │  /people  /facts  /scenarios
   ▼
FRONTEND  (frametax2/frontend, React 19 + Vite)
   │  src/api.js calls: getProduction, getPackage, getRecommendations,
   │                     getStructures, getLegal, checkConstraints, postScenario
   │  ⚠ NEVER CALLS: /economics, /people, /facts
   │  ⚠ BREAKING: Overview.jsx / Workspace.jsx read risk_adjusted_npc_usd,
   │     renamed to conservative_npc_usd — renders undefined today
   │  ⚠ STALE: FXStrip.jsx claims "FX unavailable" (false — live FX exists)
   │  ⚠ STALE: EconomicsTrace.jsx assumes legal_commit resolves (it never will)
   │  ⚠ STALE: Workspace.jsx caption claims "no treaty routes" (false — PSC-FR-MU exists)
```

---

## Connected end-to-end (backend → API → frontend, verified this session or prior)

| Subsystem | Status |
|---|---|
| Qualification (4 executable jurisdictions) | ✅ backend → API; frontend renders via `/package` |
| Optimizer / ranking | ✅ backend → API; frontend reads `/structures` (with the field-rename bug) |
| Recommendation engine | ✅ full chain, `RecommendationsList.jsx` renders it |
| Legal engine (grey area disclosure) | ✅ backend → API → `EconomicsTrace.jsx` (shows "pending" correctly, richer data unused) |
| Scenario engine | ✅ `postScenario` wired in `api.js`; `.notes` rendering unconfirmed |

## Built and backend-connected, but NOT reaching the UI (zero or partial frontend surface)

| Subsystem | Backend state | Frontend gap |
|---|---|---|
| Economics engine (floor/ceiling/financing/in-kind/travel/FX) | ✅ fully served, `/economics` | `api.js` never calls it — **no screen exists** |
| Jurisdiction comparison (4 executable, real QPE/NPC/rate) | ✅ `/economics.alternative_jurisdictions` | no comparison view exists |
| Grants/funds | ✅ `/economics.available_funds`, real classifications, no fabricated $ | no panel exists |
| People / cast-crew nationality | ✅ `GET/POST /people` | no editor exists |
| Treaty election | ✅ `treaty_engine.py` composes real candidates via `POST /facts` | no election control exists |
| FX (live + historical) | ✅ `/economics.fx_horizons` | `FXStrip.jsx` hardcoded to say it doesn't exist |

## Confirmed architectural ceiling (not a bug — a scoped, undecided redesign)

**`has_register` single-jurisdiction limit** in `production_structure_composer.py`: every multi-jurisdiction candidate (co-production, treaty, split, hybrid) is structurally prevented from reaching `is_fully_priced=True`, regardless of how much real statutory data exists for the partner jurisdiction, because a qualification register is only ever built for one baseline jurisdiction per pipeline run. This is the #1 item on the backend roadmap in `BACKEND_HANDOFF.md` and requires a producer-facing architecture decision (build N registers per candidate? merge registers? something else) before it can be fixed — not attempted this session per "preserve existing architecture unless a genuine architectural defect exists" + "requires an architecture decision."

## Not implemented at all (confirmed via exhaustive search, no code exists under any name)

Anchor structures, service productions, hybrid structures, split productions, component relocation — zero data model, zero doctrine entries, zero rate rules. Real work, not a wiring gap.

## Known data-integration gap (disclosed, not silently reconciled)

Stacking: `structure_graph_model.py` has 523 real edges, but Malta's edges use slug `mt_mfc_cash_rebate` while the executable program is `mt_mfc_rebate` — two independently-built catalogs, no shared vocabulary. Disclosed via `stacking_status` string on `/economics.available_funds`, not force-matched.

---

## One-line takeaway

**Backend is well ahead of frontend.** Every economics/people/treaty/FX capability described above exists, is real, is sourced, and is served — the primary UI work is not building new backend features, it's building the ~6 missing screens/controls that expose what already runs, plus fixing 2-3 concrete rename/staleness bugs. See `UI_HANDOFF.md` §5 for the prioritized list.

---

## SESSION DELTA — closeout #2

**Two structure systems (both real):** `app/optimization/*` is a **parametric** generator (`budget × rate`; co-pro types `dual_country`/`multi_party`/`treaty_coproduction`/`split`/`grant_stack`) reachable via `/api/v1/generate-structures`. `app/calculators/production_structure_composer.py` is the **register-grounded** served path. Both mounted; they are complementary, not duplicate.

**Corrected root blocker for multi-jurisdiction pricing:** NOT the `has_register` flag. The true blocker is the **absence of a budget-allocation model** (which accounts are spent in which territory). Register-per-jurisdiction pricing already works for **full relocation** (`/economics.alternative_jurisdictions`, GR/IE/MT each priced from own register). It cannot extend to **co-production splits** without allocation — that would double-count. New architecture; STOP-and-recommend.

**Stacking:** moved DISCONNECTED → **PARTIALLY CONNECTED** — real per-jurisdiction relationships now surfaced on `/economics.available_funds.stacking_by_jurisdiction` (IE 24 / GR 1 / MU 0 / MT 0), no stacked dollar figure (would be fabricated).

**NOT IMPLEMENTED (proven, no `structure_type`):** anchor, hybrid, service production. **PARTIAL:** split & co-production (compose + parametric price; register price blocked by allocation).

---

## SESSION DELTA — Production-Structuring audit (closeout #3, audit-only)

**Corrected assumption:** the Production Structuring Engine is **not unbuilt** — it exists in disconnected pieces.
- **`structuring_advisor.py` (948 lines)** = the "HOW to structure within a jurisdiction" advisory (SPV, in-kind FMV, EDB rulings, music routing, crew). **Functional standalone (11 rich recommendations), but DISCONNECTED and hardcoded to `LittleUtopiaParams`.** This is the single most important stranded engine.
- `generate_structure_scenarios.py` = multi-program stacking scenario generator. BUILT, DISCONNECTED.
- `app/optimization/*` (`structure_generator`, `maximization_engine`) = parametric, CONNECTED via `optimization.py` router, not register-grounded.
- `run_full_analysis` = DB-backed, CONNECTED via `structures.py` router, NOT runtime-used (DB unreachable).

**Served path** (`_build_state`) uses only: `production_structure_composer` + `optimization_engine` + `structuring_paths` + `rank_production_structures` + recommendation/legal engines.

**Structuring decisions (15):** treaty/financing = RUNTIME USED; routing/post/VFX/music/split = PARTIAL or disconnected; SPV/ownership = fixed assumption; payroll/post = producer fact inputs; services/animation/distribution/**jurisdiction-allocation** = NOT IMPLEMENTED.

**Budget allocation is an OUTPUT of structuring, not a standalone allocator** — per-account routing decisions collectively emit the allocation, which then feeds N registers into the existing composer. Building it requires de-hardcoding `structuring_advisor` + an allocation output; bounded integration, not greenfield — but a real design decision. STOP-and-recommend.

**Six-tier readiness:** Knowledge Present ~215 · Executable 4 · Connected 4+funds+stacking · Optimizer strong (single-jur + relocation) · **Production Structuring exists-but-fragmented (~35%)** · Worldwide Optimization not-yet (needs data + allocation model).

No code changed this session — pure runtime audit.

---

## SESSION DELTA — Structuring Engine generalized + connected (closeout #4)

`structuring_advisor.py` moved from **disconnected + hardcoded** to **connected + data-driven**:
- **Generalized inputs:** production identity + four previously-baked amounts (marine/crew/music/ATL) are now params; signal-gated so absent signals skip their recommendation (never fabricated).
- **Connected live:** new factory in `little_utopia_state.py` derives inputs from the real register/facts/rate (routable-offshore from `accounts_outside_jurisdiction`; ATL from register codes<2000; in-kind from real $625k); attached to state; served on `/economics.structuring_advisory`.
- **Routing decisions** (`routing_decisions`) emitted as the allocation seed — "what work happens where" — an OUTPUT of the structure, not a standalone allocator (Task 3/4).
- **Explainability preserved** end-to-end; **all 70 original LU tests pass** + 7 new; suite 2899 passed.

Pipeline addition: `... → compose_production_structures → generate_production_recommendations → _build_structuring_advisory (NEW, register-driven) → serve /economics.structuring_advisory`.

Remaining: recommendation **prose** still LU-specialized (amounts/gating are generic); budget-allocation model still the keystone for co-production/split pricing. Structuring capability **~35% → ~55%**.

---

## SESSION DELTA — Account-transfer handoff (closeout #5, docs only)

New doc `ACCOUNT_TRANSFER_HANDOFF.md` freezes state and maps **current runtime ownership** of all 24 capabilities, plus the **overlapping engines** that need reconciliation against the other Claude account before any canonical choice: structure enumeration (composer / `structure_generator` / `generate_structure_scenarios`), stacking, recommendations, ranking — across three incompatible data models (register-grounded / parametric / DB-row). **Warning carried forward:** do not rebuild/delete/merge/deprecate any engine until the other account's code + artifacts are inspected. No behavior/calculation/API change this session.

---

## SESSION DELTA — Allocation model + multi-register pricing (keystone closed)

The confirmed architectural ceiling (single-register whole-budget pricing) is resolved:

```
ALLOCATION  (production_allocation.py — NEW)
   │  StructureSpec (generic: single/relocation/component/split/treaty/
   │  majority-minority/multi-party/service/hybrid — no bespoke calculators)
   │  derive_account_allocation(): every cash account partitioned exactly once
   │  (explicit producer splits only — never invented percentages)
   ▼
MULTI-REGISTER PRICING  (allocation_pricing.py — NEW, same kernels)
   │  one PARTIAL register per jurisdiction segment via the SAME
   │  derive_qualification_register() ladder + build_risk_cases() kernel
   │  gross − Σ lawful segment incentives ± travel(once) ± FX(once) = NPC
   │  fully-priced gate: complete allocation + executable segments +
   │  treaty/ownership requirements pass; else unpriced with exact blockers
   ▼
API: /structures.allocated_structures  (additive; nothing existing changed)
```

Connected this session: `generate_structure_scenarios` (delegated per-segment program-stack
enumeration), stacking relationships after canonical slug reconciliation
(`program_slug_aliases.py` — Malta/Greece variant edges now surface, no dollar figures),
`structuring_advisor.routing_decisions` as routing input, and the recovered cloud
recommendation-engine concepts (deterministic identity, gated actions, approval chain,
reversibility, dependency groups) on allocated-structure recommendations.

Runtime-proven on Little Utopia: baseline MU (QPE $4,355,327 — matches the served register
exactly), full relocations (match /economics.alternative_jurisdictions exactly), component
relocation to MT (priced; honestly slightly worse than baseline), split production
(producer-elected split prices both partial registers), treaty MU+FR (correctly UNPRICED —
no instrument registered; never forced), conservation exact everywhere. Suite: 2926 passed.

Legacy dispositions: parametric `app/optimization/*` = REFERENCE (taxonomy adopted);
DB-backed `run_full_analysis` = engine behind delegated stack enumeration + REFERENCE.
