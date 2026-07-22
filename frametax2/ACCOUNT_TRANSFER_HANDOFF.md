# CineGlobe — Account Transfer Handoff

**Purpose:** hand this repository to a different Claude account that may hold additional CineGlobe engines/artifacts not present here. This document lets that account compare, reconcile, and choose canonical ownership **without prematurely deleting or merging anything**.

> ⚠️ **DO NOT rebuild, delete, merge, or deprecate any engine until the other account's code and artifacts have been inspected.** Nothing here is declared permanently canonical just because it is the only implementation visible in this repo.

---

## 1. Work completed on this account since the prior transfer

- **Qualification / rate authority / economics / legal / travel / FX / people / script / cultural** brought to served, runtime-verified state (earlier sessions — closed, do not re-audit).
- **Executable jurisdiction knowledge**: MU, MT, IE, GR wired (doctrine + statutory rate rules).
- **Grants/funds** connected on `/economics.available_funds`; **stacking** moved to PARTIALLY CONNECTED (real per-jurisdiction relationship edges surfaced, no fabricated dollar figure).
- **Production-structuring audit** (closeout #3): proved the structuring engine already existed in disconnected pieces; corrected the "unbuilt" assumption.
- **Structuring Advisor generalized + connected** (closeout #4): `structuring_advisor.py` de-hardcoded (identity + 4 amounts → params; signal-gated) and connected live via a factory that derives inputs from the real register/facts/rate; served on `/economics.structuring_advisory`; emits `routing_decisions` (allocation seed). 70 original LU tests unchanged + 7 new.
- **Workspace title/economics wiring fix** (Phase "restore"): scenario cards restored to frozen plain-jurisdiction-name titles (no "Relocate to X" — that wording is NOT canonical); all four displayed economics fields wired to the per-scenario canonical object.
- **Optimizer reconciliation**: confirmed `allocated_structures` (account→jurisdiction allocation + multi-register pricing, commit `bfd6364` "keystone") is the single canonical served optimizer; removed the stale unconsumed Phase 7B `global_scenario_ranker` top-level `ranking` (STRUCT-*) output. Discovery-composer (`composition`/PSC-*) retained — it feeds `/recommendations`, not stale.
- **Phase 5 — canonical optimization contract**: ranking/NPC switched from the conservative statutory floor to the **best-supported modeled incentive** (`selected_incentive_usd`); **"conservative" is retired as a product concept** — the floor-rate figure (`npc_conservative_usd`) is now purely a reference/uncertainty field, never the ranked number. Connected the off-budget Mauritius in-kind post (~$625k) as an **NPC-level replacement-cost normalization** (`inkind_replacement_delta_usd`) — never a budget line, never QPE. Result: Mauritius baseline (not Greece) is now the global optimum for Little Utopia.
- **Phase 6 — global discovery engine**: replaced the private jurisdiction-knowledge-only filter with `app/calculators/production_discovery.py`, which examines **every implemented jurisdiction** (211, from `global_inventory.ALL_PROGRAMS` ∪ `jurisdiction_comparison.ALL_PROFILES`) and returns a full reasoned accept/reject audit + metrics — no hard-coded country list.
- **Phase 7 — production-first discovery** (current, most recent): re-oriented discovery to ask "can this production be MADE here?" before "can this jurisdiction be priced?". New `app/calculators/production_requirements.py`: (a) derives structured production requirements (environments/infrastructure) from the existing `physical_requirements` (script + real-budget signals) — no fabrication; (b) an extensible keyword ontology abstracts any literal location string into reusable production categories (broad categories only, **no literal place-name matching**); (c) a jurisdiction **capability profile is kept structurally separate from its incentive profile** (geography/crew/infra fields vs. rate/doctrine fields) and matched against production requirements independent of pricing. Discovery now classifies every jurisdiction into one of three buckets — `incentive_ready` (production-capable AND priceable, enters optimization), `capability_only` (production-capable, incentive model pending — **retained and visible**, never silently discarded), `rejected` (capability mismatch or no data). See §3 below for runtime numbers.

---

## 2. Repository / branch / runtime (frozen)

| Item | Value |
|---|---|
| Repo root | `/Users/Suraj/cineglobe-frametax/frametax2` |
| Branch | `claude/audit-frametax-features-NZcX5` |
| Local HEAD | see git log (Phase 7 production-first discovery closeout, this session) |
| Remote HEAD | matches local (`git ls-remote` via SSH) |
| Working tree | clean |
| Backend path | `frametax2/backend` |
| Frontend path | `frametax2/frontend` |
| Python env | `backend/.venv/bin/python3` = **3.12.13** (bare `python3` = system 3.9, cannot import models — always use venv) |
| Backend port | `8010` (`api.js` → `127.0.0.1:8010/api/v1/cineglobe`) |
| Frontend port | Vite default `5173` |
| Database | Postgres configured but **UNREACHABLE** in this env (no `frametax` role); served pipeline is in-memory, never touches DB |
| Canonical served routes | `/api/v1/cineglobe/{production,package,recommendations,structures,legal,economics,people,facts,scenarios}` |
| Other mounted routers | `optimization.py` (parametric: `/gap-analysis`,`/generate-structures`,`/maximize`,`/recommendations`,`/travel-cost`); `structures.py` (DB-backed `run_full_analysis`, **not runtime-used**) |
| Recovered script/Drive source | "THE LITTLE UTOPIA" Google Drive folder — synopsis + opening scenes + look book (NOT a full page parse); confirmed facts only |
| Budget source | real Movie Magic PDF → `app/data/little_utopia_real_budget.py` (44 accounts) |
| People sources | `app/data/little_utopia_people.py` (writer GB, director AU, lead cast GB, producer UNKNOWN) |
| FX source | `FX_RATE_SNAPSHOTS` in `production_normalization.py` (live + 1M/6M/12M, manual point-in-time snapshot) |
| Travel source | `travel_model.py` (LA/NYC/London/Toronto home bases + fallbacks) |
| Executable (incentive_ready) jurisdictions | **MU, MT, IE, GR** (4 of 211 examined) |
| Capability-only (incentive pending) jurisdictions | **BE, CY, DE, ES, FR, HR, IT** (7) — production-capable, no priceable incentive model yet; retained, never discarded |
| Production-capable total | **11 of 211** examined jurisdictions (Little Utopia requires marine_filming + open_water_filming; HU rejected on genuine capability mismatch) |
| Test result | **2967 passed, 1 skipped** (venv) |

---

## 3. Currently SERVED engine ownership (runtime call graph)

Served pipeline (`little_utopia_state._build_state`, confirmed at runtime this session):
`build_jurisdiction_graph → build_little_utopia_real_register → resolve_program_rate → build_production_package → discover_all_opportunities → compose_production_structures → generate_production_recommendations → compose_candidate_structures → rank_production_structures → LegalEngine → _build_structuring_advisory`.

| Capability | Current runtime owner | Alt implementations in repo | Alt connected? | Unique to alt | Evidence |
|---|---|---|---|---|---|
| Budget ingestion | `app/ingestion/budget_parser.py` (Movie Magic → `little_utopia_real_budget.py`) | — | — | — | 44 accounts in served register |
| Script/package intelligence | `production_package_intelligence.build_production_package` | — | — | — | served `_build_state` |
| Qualification | `qualification_derivation` + `qualification_model.build_little_utopia_real_register` | — | — | — | 44-account register |
| Legal/evidence | `legal_engine.LegalEngine` + `legal_authority_acquisition` | — | — | — | `/legal` |
| Cultural + threshold qualification | `production_recommendation_engine` (relevance + gates) | — | — | — | served `_build_state` |
| Treaty evaluation | `treaty_engine` (+ composer `_treaty_compositions`) | `optimization/structure_generator` (`treaty_coproduction`, parametric) | Yes (parametric router) | parametric co-pro enumeration | `PSC-FR-MU` composes on election |
| Opportunity discovery | `opportunity_discovery.discover_all_opportunities` | `optimization/qualification_gap_engine` | Yes (opt router) | gap analysis view | opp types at runtime |
| Production structuring advice | **`structuring_advisor` (NEW: connected)** | `production_recommendation_engine` (different layer) | Yes (served) | HOW-to-structure (SPV/in-kind/routing) | `/economics.structuring_advisory`, 6 recs |
| Structure enumeration | `production_structure_composer.compose_production_structures` | `optimization/structure_generator`, `enumerate_structures`, `generate_structure_scenarios` | generator/enumerate: yes (opt router); scenarios: **no** | parametric co-pro types; multi-program stacking combos | composer serves `/structures` |
| Account/component routing | **`structuring_advisor.routing_decisions` (NEW)** | — | served | routing seed (component→jurisdiction) | `routing_decisions` at runtime |
| Qualification registers | `qualification_model` (single baseline register) + `build_little_utopia_register_for_jurisdiction` (per-jurisdiction, relocation) | — | — | — | `/economics.alternative_jurisdictions` |
| QPE | register QUALIFIES sum (served) | — | — | — | `verified_cash_qpe_usd` |
| Incentives | `program_rate_rules.resolve_program_rate` | — | — | — | served rate resolution |
| Travel | `production_normalization` + `travel_model` | `optimization` router `/travel-cost` | Yes (opt router) | standalone travel endpoint | `/economics.normalized_structures` |
| FX | `production_normalization.fx_rate_snapshot` | — | — | — | `/economics.fx_horizons` |
| In-kind | `mauritius_economics` in-kind post model | — | — | — | `/economics.inkind_post_options` |
| Grants/funds | `little_utopia_state.build_available_funds` (+ `fund_economics_model`) | `optimization/structure_generator` (`grant_stack`) | Yes (opt router, parametric) | parametric grant stacks | `/economics.available_funds` |
| Stacking | `build_available_funds.stacking_by_jurisdiction` (relationships only) | `optimization/stacking_rules`, `apply_stacking_adjustments`, `generate_structure_scenarios` | rules: opt-pkg internal; adjustments/scenarios: **no** | full stacking math + combos | IE 24 / GR 1 edges served |
| Economics | `mauritius_economics` + `production_normalization` | — | — | — | `/economics` |
| Scenarios | `production_scenario_engine.compose_candidate_structures` | `generate_structure_scenarios` (disconnected), `production_structure_composer` | scenarios file: **no** | 1/2/3-program stack ranking | served `scenario_structures` |
| Ranking | `rank_production_structures` | `optimization/score_structures`, `maximization_engine` | maximize: yes (opt router) | parametric maximization | served `scenario_ranking` |
| Recommendations | `production_recommendation_engine` (139 recs) | `structuring_advisor` (HOW-to), `optimization/recommendation_engine` | advisor: served; opt: yes (opt router) | producer structuring advice; parametric recs | `/recommendations` |
| Explainability | per-object fields (`authority_reference`/`evidence_reference`/`confidence`; composer constraints; advisor `published_support`/`audit_risk`) | — | — | — | runtime-confirmed on `PSC-FR-MU`, advisor recs |
| API serialization | `cineglobe.py` payload builders (+ `_serialize_structuring_advisory` NEW) | `optimization.py`, `structures.py` serializers | Yes (own routers) | parametric/DB payloads | `/economics` serves advisory |

---

## 4. Overlapping engines requiring other-account comparison

Capability matrix (NOT a ranking — each row is a distinct implementation):

| Module | Data model | Served? | Unique capability | Hardcoded/demo | Production-safe parts |
|---|---|---|---|---|---|
| `production_structure_composer.py` | real register + opportunities | **YES** | register-grounded pricing, treaty/fund/stack composition, honest `priceable_pct` | none | whole module |
| `structuring_advisor.py` | generic params (now state-derived) | **YES (new)** | HOW-to-structure advice: SPV, in-kind FMV, routing, EDB rulings, audit risk | prose still LU-specialized (amounts/gating generic) | inputs layer, gating, routing_decisions |
| `production_scenario_engine.py` | register + opportunities | **YES** | candidate-structure scenarios + notes | none | whole module |
| `generate_structure_scenarios.py` | flat line-items + program list | no | all legal 1/2/3-program **stacking combinations**, ranked | needs full input assembly | stacking-combo generator |
| `optimization/structure_generator.py` | parametric (codes + flat budget) | yes (opt router) | co-pro types: `dual_country`/`majority_minority`/`multi_party`/`split` | `budget × rate` only, not register-grounded | structure-type taxonomy |
| `optimization/optimizer.py` | parametric | **no** (no external caller) | end-to-end parametric optimize loop | parametric | orchestration shape |
| `run_full_analysis.py` | **DB rows** | connected via `structures.py` but **DB unreachable** → not runtime-used | full analysis + stacking math persisted | DB-shaped inputs | stacking math |
| `optimization_engine.py` | register + risk cases | **YES** (used by composer + state) | `RiskCase` math, financing bridge | none | whole module |

**Duplicated capabilities across the above:** structure enumeration (composer vs structure_generator vs generate_structure_scenarios), stacking (build_available_funds vs stacking_rules vs generate_structure_scenarios vs apply_stacking_adjustments), recommendations (production_recommendation_engine vs structuring_advisor vs optimization/recommendation_engine), ranking (rank_production_structures vs score_structures vs maximization_engine).

**Incompatible data models:** register-grounded (composer, scenario_engine, optimization_engine) vs parametric flat-budget (optimization/*) vs DB-row (run_full_analysis). Slug-convention mismatch persists in stacking (`mt_mfc_cash_rebate` vs executable `mt_mfc_rebate`).

**Keystone gap (unchanged):** no budget-allocation model → register-grounded co-production/split pricing blocked (`priceable_pct` caps at 0.5). `structuring_advisor.routing_decisions` is the seed but not yet an allocator.

---

## 5. What to check in the OTHER Claude account before choosing canonical ownership

The other account may hold implementations not present here. **Before declaring any engine canonical, inspect there for:**
- **Cloud artifacts** — any published/hosted engine builds or deploys.
- **Old UI artifacts** — earlier single-file JSX prototypes or a different frontend baseline (this repo's baseline is `frametax2/frontend`, React 19; see `UI_HANDOFF.md`).
- **Alternate repositories or branches** — other CineGlobe/FrameTax/TaxFrame/ReelIncentive repos or branches with divergent engines.
- **Unpublished engine modules** — structuring/optimizer/allocation code not committed here (especially a real budget-allocation model, or a fully-generic structuring engine with non-LU prose).
- **Prior architecture documents** — design docs that may already resolve the register-vs-parametric-vs-DB data-model split, or name a canonical structure engine.

---

## 6. Reconciliation procedure

For each overlapping capability, run this before changing anything:

1. **Locate** the other-account implementation and this repo's owner (§3/§4).
2. **Compare capability** — feature-by-feature; note what each does that the other cannot.
3. **Compare data model** — register-grounded vs parametric vs DB-row. A stronger data model usually wins, but confirm at runtime.
4. **Compare runtime use** — which is actually served/exercised (runtime evidence overrides code review).
5. **Preserve strongest proven parts** — keep the components with runtime proof + the richest correct data model; salvage unique capabilities from the others (e.g. stacking combos, co-pro taxonomy, allocation model if the other account has one).
6. **Choose ONE canonical owner** per capability.
7. **Adapt/deprecate alternatives ONLY after verification** — never before both sides are inspected and the canonical choice is runtime-proven.

---

## 7. Explicit warning

**Do not rebuild, delete, merge, or deprecate any engine until the other account's code and artifacts have been inspected and the reconciliation procedure (§6) has been completed.** The absence of an alternative here is not evidence it does not exist elsewhere.
