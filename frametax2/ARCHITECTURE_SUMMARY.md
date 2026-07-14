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
