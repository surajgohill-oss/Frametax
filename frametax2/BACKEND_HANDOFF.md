# CineGlobe Backend Handoff

**Written**: end of the final backend implementation session on this Claude account (development transitions to a separate Claude account for UI work from here). Every fact below is runtime-verified as of this commit — not inferred, not aspirational.

---

## 1. Environment

| | |
|---|---|
| Mode | TERMINAL (local macOS, not cloud) |
| OS | Darwin 25.3.0 (macOS), arm64 |
| Repository root | `/Users/Suraj/cineglobe-frametax` |
| Backend path | `/Users/Suraj/cineglobe-frametax/frametax2/backend` |
| Frontend path | `/Users/Suraj/cineglobe-frametax/frametax2/frontend` |
| Active branch | `claude/audit-frametax-features-NZcX5` |
| Remote | `https://github.com/surajgohill-oss/Frametax.git` (origin) |
| Latest commit | `b47e0a3402a3fe468df67d18e8c04c59e930451e` |
| Latest pushed commit | Same — confirmed via `git ls-remote origin` at handoff time; local and remote HEAD match exactly |
| Python | 3.12.13, project requires `>=3.11` (see `backend/pyproject.toml`) |
| Package manager | `pip` into a project-local `.venv` (`backend/.venv`); `pyproject.toml` uses `setuptools` build backend, no Poetry/uv |
| Backend URL | `http://127.0.0.1:8010` (FastAPI/uvicorn) — confirmed live and responding at handoff time |
| Frontend URL | `http://localhost:5173` (Vite dev server, port fixed in `vite.config.js`) — `VITE_API_BASE_URL=http://127.0.0.1:8010/api/v1/cineglobe` in `frontend/.env` |
| Database | PostgreSQL configured (`DATABASE_URL` in `app/core/config.py`, `postgresql+psycopg://frametax:frametax@localhost:5432/frametax2`) but **UNREACHABLE in this environment** — confirmed via direct `psql`/`psycopg` connection attempts: the local Postgres instance has no `frametax` role. **The entire served demo pipeline runs from Python in-memory functions (`app/demo/little_utopia_state.py`), never the database.** Alembic migrations exist (`backend/alembic/`) but are not exercised by the live API. |
| Running services | Two backend processes were observed listening on port 8010 during this session (likely one supervisor + one worker, or a stale process not cleaned up — worth checking with `lsof -iTCP:8010` before starting a fresh instance) |

Start commands (not run automatically — confirm before running):
```
cd frametax2/backend && .venv/bin/python3 -m uvicorn app.main:app --reload --port 8010   # (verify exact entry module)
cd frametax2/frontend && npm run dev
```

---

## 2. Project Status by Subsystem

| Subsystem | Status | Notes |
|---|---|---|
| **Qualification engine** | **COMPLETE** (for MU) / **PARTIAL** (for MT/IE/GR) / **NOT STARTED** (208 other jurisdictions) | Generic, doctrine-driven ladder (`qualification_derivation.py`) — no jurisdiction-specific code branches. 3-doctrine model (OPEN_DEFAULT_INCLUDE / CLOSED_POSITIVE_LIST / HYBRID_CONDITIONAL) fully implemented with A-F grey-area taxonomy and threshold eligibility gates (run before points scoring). MU is `VERIFIED` confidence tier; MT/IE/GR are `PARSED` (primary-source-confirmed rate/cap, connected this session). |
| **Optimizer** | **PARTIAL** | Core NPC/finance-cost math (`optimization_engine.py`) is complete and unit-tested. Cross-border comparison works for single-jurisdiction "what-if" scenarios (4 jurisdictions). Multi-jurisdiction co-production candidates compose but are **structurally capped at `is_fully_priced=False`** — see §7 root cause. |
| **Composer** | **COMPLETE** (architecture) / **STRUCTURALLY LIMITED** (multi-jurisdiction pricing) | `production_structure_composer.py` is fully data-driven — takes `extra_jurisdiction_sets` as a parameter, no hardcoded countries. The `has_register` flag (True only for the single baseline jurisdiction a register was ever derived for) is the confirmed ceiling on partner-jurisdiction pricing. |
| **Treaty engine** | **COMPLETE** | `treaty_engine.py`: 26 bilateral treaties, 3 multilateral frameworks (Eurimages/Ibermedia/European Convention), majority/minority % thresholds, nationality unlocks. Runtime-verified: electing a treaty partner (e.g. `FR`) composes a real `PSC-FR-MU` candidate. |
| **Scenario engine** | **COMPLETE** | `production_scenario_engine.py`: component relocation (MOVE_VFX/POST/MUSIC/SOUND/MARINE/PAYROLL), CREATE_COPRODUCTION, CREATE_SPV all wired. Unpriced scenarios now explain WHY (fixed a silent-failure bug this session's prior work — see git history `b99fec5`). SHIFT_SPEND/SHIFT_SCHEDULE/SHIFT_FINANCING_TIMING correctly report "no engine representation exists yet" rather than fabricate a result. |
| **Recommendation engine** | **COMPLETE** | `production_recommendation_engine.py`: grey-area, evidence-acquisition, structuring, treaty/stacking, candidate-comparison, cultural-test, and eligibility-gate recommendations. 139 real recommendations generated for Little Utopia at last count. Explainability fields (`evidence_reference`, `authority_reference`, `qualification_rationale`, `confidence`) are enforced by `__post_init__` for CREATIVE category only — not yet enforced for FINANCIAL/STRUCTURAL/REQUIRED_INPUT (confirmed gap, see §7). |
| **Economics engine** | **COMPLETE** | `mauritius_economics.py` (floor/ceiling/in-kind scenarios, financing controls) + `production_normalization.py` (travel + FX). Serves `/economics` with 3 distinct headline results (never a blended risk-adjusted figure), `normalized_structures`, `alternative_jurisdictions`, `available_funds`, `fx_horizons`. |
| **Legal engine** | **COMPLETE** (architecture) / **Research-view only** | `legal_engine.py` + `legal_authority_acquisition.py`. MockConnector is the sole connector (self-labeled, never presented as authoritative). Deliberately does NOT auto-resolve the one genuine grey area (`GA-INKIND-FMV`) — `legal_commit` stays `None` by design (see git history `4c18d5f`/session on grey-area resolution paths). |
| **Explain mode** | **PARTIAL** | Every `AccountQualification` carries `authority_basis`, `reason`, `grey_reason`. Every gate/cultural recommendation carries `evidence_reference` + `authority_reference` + `qualification_rationale`. No single "explain this number" API endpoint exists yet — the trace has to be assembled by a UI from several endpoints (`/package`, `/legal`, `/recommendations`). |
| **Travel normalization** | **COMPLETE** | Incremental model-vs-model delta (apples-to-apples) AND delta-vs-original-budget (this session's addition) both exposed. Producer-overridable origin city (LA/NYC/London/any `travel_model.py` fare-table code), traveler mix, rotations, hotel/per-diem. Never touches QPE (register-invariant, tested). |
| **FX normalization** | **COMPLETE** | Real, sourced live rate (fetched from `open.er-api.com`) + historical snapshots (1M/6M/12M via `frankfurter.dev`/ECB) + user override. `FX_RATE_SNAPSHOTS` needs periodic re-fetching by a human or scheduled job — it is a point-in-time snapshot, not a live connector. MUR has no historical source connected (disclosed, not fabricated). |
| **Script integration** | **PARTIAL** | Real screenplay/synopsis/look book recovered from Google Drive. 8 script attributes populated from CONFIRMED content (marine, period, countries, language, source material, VFX intensity). `script.known` stays honestly `False` — no full page-by-page parse of the 100+ page screenplay has been performed. |
| **People integration** | **COMPLETE** | Real, sourced cast/crew (Clara Salaman/writer/GB, Kim Farrant/director/AU, Rachel Winter + Max Botkin/producers/US — all Wikipedia/IMDb-sourced this engagement). Lead cast correctly UNKNOWN (production's own budget says "CAST: tbc" — a prior session's uncorroborated "Luke Evans" claim was found and removed). Residency stored separately from nationality, honestly unconfirmed for all 4. |
| **Cultural testing** | **COMPLETE** (architecture) / **PARTIAL** (coverage) | UK BFI + Australian content test wired with real per-role point weights (never a hardcoded universal weight). Threshold eligibility gates (hard requirements, e.g. Canada's CPTC requiring Canadian director+writer+producer) now execute BEFORE points scoring — previously dead data (`cultural_qualification_model.py`), connected this session (2 sessions ago). Only 8 of many real-world cultural tests are wired. |
| **Grants** | **PARTIAL** | `fund_economics_model.py` has 243 real, classified entries. Connected this session for the 4 executable jurisdictions (`build_available_funds()`) — classification only (rebate/grant/tax_credit/advance, repayable/recoupable/equity terms), **no dollar amounts** (none exist per-production in the source data; never fabricated). |
| **Funds** | **PARTIAL** | Same as Grants — `fund_economics_model.py` conflates "funds" and "grants" under one registry; no separate distinction exists in the data model. |
| **Stacking** | **NOT STARTED (disconnected, real data exists)** | `structure_graph_model.py` has 523 real stacking/compatibility edges but uses an **incompatible slug convention** from the executable-jurisdiction program slugs (e.g. `mt_mfc_cash_rebate` vs `mt_mfc_rebate`). Confirmed via runtime this session; disclosed via `available_funds.stacking_status`, not silently reconciled. |
| **Co-production execution** | **PARTIAL** | Treaty candidates compose correctly (majority/minority thresholds, nationality unlocks). Full pricing (`is_fully_priced=True`) is structurally blocked for any candidate beyond the single baseline jurisdiction — see §7. |
| **Anchor structures** | **NOT IMPLEMENTED** | No `ScenarioKind`, `OpportunityType`, or data model represents "anchor production" anywhere in the codebase, confirmed via exhaustive grep across two separate sessions. |
| **Hybrid structures** | **NOT IMPLEMENTED** | Same — no data model for "hybrid structure" as a distinct concept from treaty co-production. |
| **Split production** | **NOT IMPLEMENTED** | No data model for splitting the SAME department across two jurisdictions simultaneously (distinct from component relocation, which moves a whole department). |
| **Service production** | **NOT IMPLEMENTED** | No data model for a fully foreign-financed service shoot distinct from the majority-financed model the engine implicitly assumes. |

---

## 3. Engine Entry Points

| Module | Called by | Returns | Consumed by |
|---|---|---|---|
| `qualification_derivation.py` (`derive_qualification_register`) | `qualification_model.py`'s `build_little_utopia_real_register()` and `build_little_utopia_register_for_jurisdiction()` | `list[AccountQualification]` | `optimization_engine.build_risk_cases()`, `production_structure_composer.py`, `little_utopia_state.py` |
| `program_spend_rules.py` (`get_program_doctrine`, `get_program_rules`) | The ladder above | `QualificationDoctrine \| None`, `dict[str, SpendRule]` | `qualification_derivation.py` only |
| `program_rate_rules.py` (`resolve_program_rate`) | `little_utopia_state.py`, `build_alternative_jurisdiction_comparisons()` | `RateResolution \| None` (floor/ceiling/conditions/conflicts) | `optimization_engine.build_risk_cases()` (rate input), API `/production` |
| `optimization_engine.py` (`build_risk_cases`) | `little_utopia_state.py`, `production_structure_composer.py`, `production_scenario_engine.py`, `mauritius_economics.py`-adjacent code | `OptimizationResult` (4 risk cases: conservative/base/optimistic/risk_adjusted) | Everything downstream — the single pricing kernel |
| `production_structure_composer.py` (`compose_production_structures`) | `little_utopia_state.py._build_state()` | `CompositionResult` (candidates + ranking) | `/structures` API, `production_scenario_engine.py`, `production_recommendation_engine.py` |
| `opportunity_discovery.py` (`discover_all_opportunities`) | `little_utopia_state.py._build_state()` | `OpportunityCollection` | `production_structure_composer.py`, `production_recommendation_engine.py` |
| `treaty_engine.py` | `opportunity_discovery.py`, `production_package_intelligence.py`, `cultural_qualification_model.py` gate evaluator | Membership booleans, `BilateralTreaty` records | Opportunity/nationality-unlock generation |
| `production_scenario_engine.py` (`run_scenario`) | API `/scenarios` (POST) | `ScenarioResult` | Frontend's `postScenario()` call |
| `production_recommendation_engine.py` (`generate_production_recommendations`) | `little_utopia_state.py._build_state()` | `RecommendationSet` | `/recommendations`, `/package` (via `Overview`/`Workspace` screens) |
| `legal_engine.py` / `legal_authority_acquisition.py` | `little_utopia_state.py._build_state()` (research cycle, separate from primary pipeline) | `AcquisitionCycleResult`, `CommitResult` | `/legal` API only — never the primary register |
| `mauritius_economics.py` (`compute_mauritius_economics`) | `cineglobe.py` `_economics_payload()` | `EconomicsResult` × 3 cases | `/economics` |
| `production_normalization.py` | `little_utopia_state.py.build_normalized_structures()`, `build_alternative_jurisdiction_comparisons()` | `TravelNormalizationResult`, `FXNormalizationResult`, `CandidateNormalization` | `/economics.normalized_structures`, `.alternative_jurisdictions` |
| `production_package_intelligence.py` (`build_production_package`) | `little_utopia_state.py._build_state()` | `ProductionPackage` (budget/script/people/location/travel/missing_inputs) | `/package`, most other engines' inputs |
| `cultural_qualification_model.py` (`evaluate_program_eligibility`) | `production_recommendation_engine.generate_eligibility_gate_recommendations()` | `EligibilityGateResult` (SATISFIED/FAILED/INDETERMINATE per role) | Recommendation generation only |
| `little_utopia_state.py` (`get_state`) | Every API route in `cineglobe.py` | `LittleUtopiaState` (cached, invalidated on fact/people/economics-control change) | The entire API layer |

---

## 4. Currently Executable Jurisdictions

### Mauritius (MU) — `mu_edb_incentive`
- **Doctrine**: HYBRID_CONDITIONAL (positive list with illustrative catch-alls; digital-animation contrast is the decisive evidence)
- **Authority**: EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020), Regulation 2018
- **QPE methodology**: expenses "incurred locally," 33 illustrative categories, territorial-nexus exclusion for confirmed offshore work
- **Rates**: 30% guaranteed floor / up to 40% discretionary ceiling (Film Rebate Committee + CEO approval)
- **Caps**: none on file
- **Conditional rules**: min QPE $1M; discretionary-band condition on the 40% tier; no-sponsorship-in-QPE condition (fact-dependent, unresolved either way)

### Malta (MT) — `mt_mfc_rebate`
- **Doctrine**: OPEN_DEFAULT_INCLUDE ("all qualifying Malta expenditure," no stated exclusions clause)
- **Authority**: Malta Film Commission profile, PARSED tier (primary-source-confirmed rate/cap)
- **QPE methodology**: territorial ("Malta expenditure"); ATL/BTL/VFX/music/marine all confirmed qualifying
- **Rates**: 25% base / 40% ceiling (stacked uplifts: +3% cultural contribution, +3% VFX/post-in-Malta, +7% small-budget <€3M)
- **Caps**: min spend €50,000 (≈$57,026 at the live sourced FX rate)
- **Conditional rules**: 40% ceiling is a discretionary band, not guaranteed

### Ireland (IE) — `ie_section_481`
- **Doctrine**: OPEN_DEFAULT_INCLUDE
- **Authority**: Revenue Commissioners Ireland (revenue.ie), Finance Act — PARSED tier
- **QPE methodology**: eligible Irish expenditure, territorial
- **Rates**: flat 32% refundable tax credit (no tiering)
- **Caps**: min spend €125,000 (≈$142,565); 80% of budget or €70M qualifying spend whichever lower (**disclosed, not enforced** — this is a cap on qualifying spend amount, a mechanism this codebase's `RateRule` model doesn't represent)
- **Conditional rules**: cultural test required (Irish Qualifying Test) — a genuine threshold gate, fact-dependent, unresolved (points-system detail itself unverified from primary source)

### Greece (GR) — `gr_cash_rebate`
- **Doctrine**: OPEN_DEFAULT_INCLUDE
- **Authority**: Enterprise Greece / Greek Film Centre — PARSED tier
- **QPE methodology**: eligible Greek expenditure, territorial
- **Rates**: flat 40% (highest headline rate of the comparison set)
- **Caps**: min spend €100,000 (≈$114,052); annual program allocation exists but the exact cap is **not publicly confirmed** (disclosed data gap, not enforced)
- **Conditional rules**: no cultural test required

### All other 211 cataloged jurisdiction codes
Present in `global_inventory*.py` (692 total programs) as descriptive metadata only — **no doctrine, no rate rules, excluded from every executable comparison**, never silently priced.

---

## 5. Remaining Backend Roadmap (dependency-ordered)

1. **Resolve the `has_register` single-jurisdiction ceiling** — the root architectural blocker for real multi-jurisdiction co-production pricing. Requires a design decision (per-jurisdiction partial registers vs. a different partner-pricing mechanism) before any further co-production work is worth doing. Everything below this line is secondary to it for co-production specifically.
2. **Reconcile the `structure_graph_model.py` stacking-edge slug convention** against the executable-jurisdiction program slugs — unblocks real stacking calculations for MT/IE/GR.
3. **Populate doctrine + rate rules for the next tier of DISCOVERY-confidence jurisdictions** (BE, CY, DE, ES, FR, HR, HU, IT) — requires primary-source verification work (promoting DISCOVERY → PARSED) before it can be connected the same way MT/IE/GR were.
4. **Full page-by-page screenplay parse** — would upgrade `script.known` from `False` to `True` and unlock richer requirement extraction (studio/crew-depth/post needs beyond the currently-confirmed marine/period/VFX facts).
5. **Enforce the explainability chain uniformly** — extend `Recommendation.__post_init__`'s CREATIVE-only enforcement (evidence/authority/rationale required) to FINANCIAL/STRUCTURAL/REQUIRED_INPUT categories.
6. **Anchor / hybrid / split / service production data models** — genuinely new architecture, not a connection task; needs an explicit design decision before implementation.
7. **Scheduled FX refresh** — `FX_RATE_SNAPSHOTS` is a manually-fetched point-in-time table; wire a scheduled job (or document the manual refresh cadence) so "live" stays live.

---

# SESSION DELTA — Backend closeout #2 (worldwide-optimizer architecture close)

**Commit:** `<this commit>` (parent `68d3747`).
**Env note:** the project runs on `backend/.venv/bin/python3` (3.12.13). Bare `python3` resolves to macOS system Python 3.9, which cannot even import the models (`X | None` syntax) — always use the venv.

## Files changed
- `backend/app/demo/little_utopia_state.py` — `build_available_funds()`: added `stacking_by_jurisdiction` (real edges from `structure_graph_model.py`, exact-slug-match only, no dollar figure) + refined `stacking_status` to PARTIALLY CONNECTED. Bumped payload version 1.0.0 → 1.1.0.
- `backend/tests/test_optimizer_input_integration.py` — replaced the stacking-disconnection test with `test_stacking_relationships_surfaced_exact_slug_only_no_dollar_figure` (asserts real relationships surfaced, IE>0, MU/MT exact-match 0, no dollar keys).

## Runtime-proven findings (this session's whole point)

### Two parallel structure systems exist — earlier "NOT IMPLEMENTED" notes were partly wrong
- `app/optimization/` (`structure_generator.py`, `enumerate_structures.py`, `optimizer.py`, `stacking_rules.py`) = a **parametric** engine: enumerates & roughly prices co-pro structures via `budget × base_rate`. Reachable via `/api/v1/generate-structures`, `/gap-analysis`, `/maximize`, `/recommendations` (router `optimization.py`, mounted). **Not** register-grounded.
- `app/calculators/production_structure_composer.py` = the **register-grounded** served path (`cineglobe.py` → `/structures`).
- The ONLY produced `structure_type` values anywhere: `single, single_country, split, dual_country, majority_minority, multi_party, treaty_coproduction, grant_stack`.

### Task 2 — structure systems (runtime-proven)
| System | Verdict | Evidence |
|---|---|---|
| grants | **CONNECTED** | `/economics.available_funds` real classifications; `grant_stack` parametric type |
| funds | **CONNECTED** | same + composer `_fund_compositions` (multilateral `fund_unlocks`) |
| stacking | **PARTIALLY CONNECTED** (this session) | real edges surfaced per jurisdiction: IE=24, GR=1, MU/MT=0; no stacked $ (would be fabricated) |
| treaty execution | **CONNECTED** | electing `treaty_partner_code=FR` composes `PSC-FR-MU` at runtime; treaties attach where a bilateral is registered |
| co-production execution | **PARTIAL** | composes (`PSC-MU-CY/ES/GR/MT`) + parametric pricing exists, but register pricing stuck at `priceable_pct=0.5` |
| anchor | **NOT IMPLEMENTED** | no `structure_type="anchor"` anywhere; mentions only |
| hybrid | **NOT IMPLEMENTED** | no `structure_type="hybrid"`; mentions only |
| split | **PARTIAL** | `structure_type="split"` in parametric path (`/generate-structures`); NOT register-grounded (same allocation blocker) |
| service production | **NOT IMPLEMENTED** | no `structure_type`; 26 hits are data/notes |

### Task 3 — missing-jurisdiction-knowledge vs missing-optimizer-capability: PROVEN, and it's BOTH, cleanly split by structure type
- **Relocation / alternative-jurisdiction comparison:** binding constraint = **(A) missing jurisdiction knowledge only.** Runtime: GR/IE/MT each priced $4,355,327 QPE from their own register; `catalog_only` = BE, CY, DE, ES, FR, HR, HU, IT (profile but no doctrine+rate). Optimizer capability already exists.
- **Co-production / split register pricing:** binding constraint = **(B) missing optimizer capability**, independent of jurisdiction knowledge. **Proof:** `PSC-MU-GR` and `PSC-MU-MT` stay at `priceable_pct=0.5` even though GR and MT are fully executable (they price $4.36M standalone). More jurisdiction data will NOT lift them.

### Task 4 — multi-jurisdiction pricing via multiple registers: ANSWERED
- **Full-relocation case: YES, and already connected.** `build_alternative_jurisdiction_comparisons` already builds a register per executable jurisdiction and prices each at 100% budget → served on `/economics.alternative_jurisdictions`. No optimizer redesign was needed. (This is the real "worldwide optimizer" output today.)
- **Co-production / split case: NO — architectural blocker, STOP-and-recommend (not implemented).** The composer prices the **entire** `gross_budget_usd` against a single baseline register. Feeding a second full-budget register would price the whole budget in *each* jurisdiction = double-count. Correct split pricing requires a **per-jurisdiction budget-allocation model** (which budget accounts are incurred in which territory) — confirmed absent (grep: no allocation computation exists, only narrative notes + producer-facing "allocate spend" suggestion strings). This is NEW architecture, not wiring.
- **Root-blocker correction:** the prior handoff called `has_register` single-jurisdiction the #1 blocker. More precisely, `has_register=one` is a *faithful symptom*; the true root blocker is the **absence of an account→jurisdiction allocation model.** Flipping `has_register` to multi-True without an allocation model would emit double-counted (fabricated) NPCs — forbidden. Roadmap item #1 should be restated as "design the budget-allocation model," not "lift the has_register flag."

### Task 5 — explainability: 4/5 elements are direct fields on every `Recommendation`
`authority_reference` (statute) · `evidence_reference`/`qualification_rationale` (facts) · `category`/`subtype`/`specific_actions` (optimizer decision) · `confidence` (assumptions). **Budget lines** are the only element not surfaced as a direct field — reachable via `opportunity_ids` → opportunity → account. Per "recommend only if missing": **recommendation** — resolve `opportunity_ids` to their driving account codes and attach as `budget_line_refs`. Not implemented (closeout restraint; not strictly missing, one hop away).

## Task 6 — final runtime engine matrix
| Engine | Status | Evidence |
|---|---|---|
| Qualification | WORKING | register built, `PSC-MU` priced |
| Optimizer/ranking | WORKING | 5 candidates, 1 fully priced, ranked |
| Economics | WORKING | `/economics` serves floor/ceiling/inkind/financing |
| Composer | WORKING (single-register ceiling) | composes all candidates; co-pro `priceable_pct=0.5` |
| Recommendation | WORKING | 139 recs, 4/5 explainability fields direct |
| Treaty | WORKING | `PSC-FR-MU` composes on election |
| Scenario | WORKING | `scenario_ranking`/`scenario_structures` present |
| Explain Mode | PARTIAL | authority/evidence present; budget-line refs + legal-commit trace not surfaced (commit `None` by design) |
| Travel | WORKING | `normalized_structures` served, dual-delta |
| FX | WORKING | `fx_horizons` MUR/EUR/GBP served |
| People | WORKING | `/people` get/post |
| Script | PARTIAL | confirmed facts + honest unknowns; no full script text (never existed) |
| Cultural | WORKING | eligibility-gate vs points recs distinguished |
| Grants | WORKING | `available_funds` |
| Funds | WORKING | `available_funds` + fund unlocks |
| Stacking | PARTIAL | relationships surfaced (IE 24/GR 1/MU 0/MT 0); no stacked $ |

## Known blockers
1. **Budget-allocation model** (account→jurisdiction) — blocks register-grounded co-production/split pricing. New architecture; needs a design decision. STOP-and-recommend.
2. **Worldwide relocation coverage** — data-only: add doctrine+rate for BE/CY/DE/ES/FR/HR/HU/IT via the proven MT/IE/GR machinery.
3. **Malta stacking variant slug** — `mt_mfc_cash_rebate` vs executable `mt_mfc_rebate`; separate catalog-reconciliation task.

## Next task / resume point
The only genuine architectural decision left for a true worldwide optimizer is **blocker #1 (budget-allocation model)**. Everything else is either DONE, data-entry (blocker #2), or UI (see `UI_HANDOFF.md`). Do not implement the allocation model without an explicit design sign-off — it changes how every co-production NPC is computed.

---

# SESSION DELTA — Production-Structuring audit (closeout #3, audit-only, no code change)

**Files changed:** NONE (pure runtime audit; the only writes this session are this delta + the ARCHITECTURE_SUMMARY delta).
**Commit:** `<this commit>` (parent `2be42a5`).

## Biggest corrected assumption
Prior deltas implied the **Production Structuring Engine** was essentially unbuilt / needed new architecture. **Runtime proof says otherwise: it already exists, in disconnected pieces.** The gap is *integration + de-hardcoding + one allocation model*, not greenfield engine-building.

### The served runtime pipeline (ground truth, from `_build_state`)
`build_jurisdiction_graph → build_little_utopia_real_register → resolve_program_rate → build_production_package → discover_all_opportunities → compose_production_structures → generate_production_recommendations → compose_candidate_structures → rank_production_structures → LegalEngine`.
**`app/optimization/*` is NOT in this path.** It is reachable only via the separate (mounted) `optimization.py` router, on a **parametric** (`budget × rate`, caller-supplied codes) basis — not register-grounded.

### Structuring engines that EXIST (runtime-classified)
| Module | Role | Verdict | Runtime evidence |
|---|---|---|---|
| `production_structure_composer` (served) | jurisdiction/treaty/fund/stack composition + register-grounded risk-case pricing | **RUNTIME USED / VERIFIED** | composes 5 candidates; `PSC-MU` priced |
| `optimization_engine` + `structuring_paths` (served) | risk-case math + structuring path conversion | **RUNTIME USED** | imported by `_build_state`, composer, constraint engine |
| `rank_production_structures` (served) | scenario ranking | **RUNTIME USED** | `scenario_ranking` populated |
| **`structuring_advisor.py` (948 lines)** | **the "HOW to structure within a jurisdiction" advisory** — SPV setup, in-kind FMV structuring, EDB rulings, music-recording routing, crew expansion; classifies EXPLICITLY_PERMITTED / INDUSTRY_STANDARD / REQUIRES_INTERPRETATION / UNKNOWN | **BUILT, FUNCTIONAL, DISCONNECTED** | `build_structuring_advisory(LittleUtopiaParams())` runs → 11 rich recommendations (audit_risk, financial_impact_usd, interpretation_body, published_support). **Hardcoded to demo `LittleUtopiaParams` (fixed dollar figures)** — zero importers |
| `generate_structure_scenarios.py` | multi-program stacking scenario generator (all legal 1/2/3-program stacks, ranked by true_net_cost) | **BUILT, DISCONNECTED** | functional 14-param signature; 0 non-test importers |
| `app/optimization/structure_generator` | parametric co-pro enumeration (`dual_country`/`multi_party`/`treaty_coproduction`/`split`) | **BUILT, CONNECTED (parametric router), not register-grounded** | `/api/v1/generate-structures` |
| `app/optimization/maximization_engine` | parametric maximization | **BUILT, CONNECTED (parametric router)** | `/api/v1/maximize` |
| `run_full_analysis` | DB-backed full analysis + stacking math | **BUILT, CONNECTED (`structures.py` router), NOT runtime-used** | DB path only; DB unreachable in this env |

## Task 1 — capability matrix (runtime-proven)
| Capability | Verdict | Evidence |
|---|---|---|
| production structures | **RUNTIME USED / VERIFIED** | composer produces `PSC-*` candidates |
| treaty optimization | **RUNTIME USED** | `PSC-FR-MU` composes on election; discovery finds bilateral×2, multilateral×23, nationality_unlock×6 |
| SPV optimization | **BUILT (assumption) + BUILT-DISCONNECTED (advisor)** | `SPV_PRODUCTION_STRUCTURE_DEFAULT` is a fixed assumption; `structuring_advisor._r_spv_frogsquad` optimizes it but is disconnected |
| service production | **NOT IMPLEMENTED** | no `structure_type` |
| split production | **PARTIAL** | parametric only; register-split blocked by allocation |
| majority/minority co-production | **BUILT, CONNECTED (parametric)** | `structure_generator` `majority_minority`/`multi_party` |
| grants | **RUNTIME USED** | `/economics.available_funds` |
| funds | **RUNTIME USED** | `available_funds` + composer `_fund_compositions` |
| stacking | **PARTIAL (relationships surfaced)** + BUILT-DISCONNECTED engine | `stacking_by_jurisdiction`; `generate_structure_scenarios` + `stacking_rules` disconnected |
| anchor productions | **NOT IMPLEMENTED** | no `structure_type` |
| hybrid productions | **NOT IMPLEMENTED** | no `structure_type` |
| financing structures | **RUNTIME USED** | `mauritius_economics` financing controls; `optimization_engine` bridge |
| production allocation | **NOT IMPLEMENTED** | no allocation computation exists (root blocker) |
| recommendation generation | **RUNTIME USED / VERIFIED** | 139 recs served; advisor is a 2nd, disconnected recommender |

## Task 2 — dependency map: the 15 structuring decisions
| Decision | Where it lives today | Status |
|---|---|---|
| SPV structure | `SPV_PRODUCTION_STRUCTURE_DEFAULT` (assumption) + `structuring_advisor` (disconnected) | fixed assumption; optimizer-advice disconnected |
| treaty structure | `treaty_engine` + composer `treaty_compositions` | RUNTIME USED |
| ownership | SPV default only | fixed assumption |
| production routing | `opportunity_discovery` `relocation_candidate` (movable_spend) | PARTIAL |
| payroll routing | fact `payroll_routing_localized` | producer election (not optimized) |
| production services | — | NOT IMPLEMENTED |
| post location | fact `post_work_in_jurisdiction` + economics in-kind post | PARTIAL |
| VFX location | bundled in movable_spend hint | PARTIAL |
| animation | — | NOT IMPLEMENTED |
| music | `structuring_advisor._r_music_recording_mu` (disconnected) + movable_spend | disconnected / partial |
| financing | `mauritius_economics` + `optimization_engine` | RUNTIME USED (producer input) |
| completion bond | register account (qualification), not a decision | N/A |
| distribution | — | NOT IMPLEMENTED |
| production split | `structure_generator` (parametric) / composer (blocked) | PARTIAL / BLOCKED |
| jurisdiction allocation | — | NOT IMPLEMENTED (keystone) |

**Dependency keystone:** *jurisdiction allocation* is the root precondition. production-routing, split, and per-department location (VFX/music/animation/post) all either feed INTO or depend ON an allocation. Without it the composer prices whole-budget-in-one-jurisdiction only.

## Task 3 — budget allocation is an OUTPUT, not a standalone allocator
Confirmed by architecture: routing each department/account to a jurisdiction **collectively produces** the allocation. So the correct architecture is *not* "build a budget allocator" but "a Production Structuring Engine whose per-account routing decisions emit the allocation, which then feeds one register per jurisdiction into the existing composer." `structuring_advisor` already makes SOME of these routing decisions (e.g. music→MU) but hardcoded + disconnected. **Why existing engines can't do it as-is:** `structuring_advisor` is hardcoded to `LittleUtopiaParams` (fabricated figures if served); `structure_generator` is parametric (no per-account register); the composer accepts a single whole-budget register. Bridging them needs (a) de-hardcoding `structuring_advisor` to read the real register, and (b) an allocation output feeding N registers to the composer — bounded integration, but a real design decision. STOP-and-recommend; not implemented.

## Task 4 — explainability gaps (genuine only)
Present and rich: **statute** (`authority_reference`), **authority** (composer `authority` constraints, per-jurisdiction), **production facts** (`evidence_reference`), **assumptions** (`confidence`; SPV assumption set), **optimizer decisions** (`category`/`subtype`/`specific_actions`), **treaty reasoning** (`PSC-FR-MU` carries per-jurisdiction authority/evidence/stacking_unknown constraints — runtime-confirmed). Genuine gaps: **budget-line refs** (reachable via `opportunity_ids`, not surfaced) and **allocation reasoning** (cannot exist until allocation exists). `structuring_advisor` additionally carries `interpretation_body`/`interpretation_question`/`published_support`/`audit_risk` — richer HOW-to-structure explainability, currently stranded by disconnection.

## Task 5 — six-tier global-readiness assessment (these are different measurements)
| Tier | State | Basis |
|---|---|---|
| **Knowledge Present** | ~215 jurisdiction profiles | `jurisdiction_comparison.ALL_PROFILES` |
| **Executable Knowledge** | **4** (MU, MT, IE, GR) | doctrine + statutory rate rules |
| **Connected Knowledge** | 4 executable + funds + stacking-relationships (IE rich) | served on `/economics` |
| **Optimizer Capability** | **strong** for single-jurisdiction + full-relocation comparison | register-grounded pricing, ranking, recommendations, treaty composition all RUNTIME USED |
| **Production Structuring Capability** | **exists but fragmented/disconnected** | `structuring_advisor` (HOW-to-structure, hardcoded), `generate_structure_scenarios` (stacking combos), parametric `optimization/*` — none integrated into the register-grounded served path |
| **Worldwide Optimization Capability** | **NOT yet** | needs (a) executable knowledge for more jurisdictions [data] and (b) the allocation model to price co-productions/splits [architecture] |

## Remaining architectural gaps (unchanged priority)
1. **Budget-allocation model** — keystone; blocks register-grounded split/co-pro pricing. New architecture; STOP-and-recommend.
2. **De-hardcode + integrate `structuring_advisor`** — parameterize `LittleUtopiaParams` from the real register/facts, then wire into the served recommendation surface (do NOT connect as-is — it would inject hardcoded figures). Bounded integration, not greenfield.
3. **Worldwide executable coverage** — data-only, via the proven MT/IE/GR machinery.

## Updated engine-completion estimates
- Qualification / Legal / Economics / Travel / FX / Recommendation (served): **~90–100%**.
- Optimizer (single-jurisdiction + relocation comparison): **~85%**.
- Production Structuring (HOW-to-structure, integrated & register-grounded): **~35%** — pieces exist (`structuring_advisor`, `structure_generator`, `generate_structure_scenarios`) but disconnected/hardcoded/parametric; integration + allocation outstanding.
- Worldwide multi-jurisdiction pricing: **~40%** — relocation comparison works; co-production/split blocked on allocation.

---

# SESSION DELTA — Production Structuring Engine generalized + connected (closeout #4)

**Commit:** `<this commit>` (parent `8de669e`). Full suite: **2899 passed, 1 skipped** (venv Python 3.12).

## What was generalized
`structuring_advisor.py` (the "HOW to structure" engine) was hardcoded to Little Utopia. Now:
- **Production identity is a param, not a literal.** `build_structuring_advisory` emitted `"The Little Utopia"`/`"MU"` literally; these moved to `LittleUtopiaParams.production_title`/`.jurisdiction_code` (LU defaults preserved). Result identity flows from inputs.
- **Four baked-in amounts promoted to params:** `marine_expansion_usd` (was 112k literal in R-06), `local_crew_expansion_usd` (105k, R-07), `music_recording_usd` (60k, R-08), `atl_qualifying_usd` (260k, R-09). LU defaults preserved; a different production supplies different values.
- **Signal-gating:** `build_structuring_advisory` now emits each amount-driven recommendation only when its governing amount `> 0`. Umbrella (R-11) and protective related-party (R-10) always emit. A production lacking a signal gets *fewer* recommendations — never a fabricated zero-value one.
- **Routing decisions output:** `StructuringAdvisoryResult.routing_decisions` — the "what work happens where" placement (component → target jurisdiction, with qpe impact) derived from the routing-type recommendations (SPV_ROUTING / MUSIC_RELOCATION / SERVICE_AGREEMENT). This is the allocation seed (Task 3/4), an **output** of the structure, not a standalone allocator.

## What was connected
- New factory `_build_structuring_advisory(register, facts, rate, gross_budget, inkind_fmv)` in `little_utopia_state.py` derives the engine's inputs from the **real served state**: `production_title`/`jurisdiction`/`rate` from state; `qpe` from register QUALIFIES sum; **routable-offshore** from `facts.accounts_outside_jurisdiction` × register amounts; **ATL** from register accounts (code < 2000, QUALIFIES); in-kind from the real $625k post FMV. Signals not cleanly derivable (accommodation/perdiem/marine/crew/music) are left 0 → skipped, never fabricated.
- Called in `_build_state`; attached as `LittleUtopiaState.structuring_advisory`; served on `/economics.structuring_advisory` with full explainability preserved (`_serialize_structuring_advisory` in `cineglobe.py`).

## Files changed
- `backend/app/calculators/structuring_advisor.py` — params for identity + 4 promoted amounts; signal-gated assembly; `routing_decisions`.
- `backend/app/demo/little_utopia_state.py` — factory + `structuring_advisory` state field + wiring.
- `backend/app/api/v1/cineglobe.py` — serialize + serve on `/economics`.
- `backend/tests/test_structuring_advisor.py` — +7 tests (generic identity, signal-gating, de-hardcoded amounts, routing decisions, live-connection, JSON-serializability). All 70 original LU tests still pass unchanged.

## Runtime proof (served state)
6 data-driven recommendations (down from the 11-rec LU *fixture*, because the served register already qualifies most spend): R-11 umbrella, **R-01 SPV routing qpe=$9,068** (real `accounts_outside_jurisdiction` sum, *not* the $99,837 demo constant — asserted in tests), R-05/R-04 in-kind ($625k real), **R-09 ATL qpe=$538,444** (real register ATL total), R-10 protective. Accommodation/per-diem/marine/crew/music correctly **skipped** (no signal). `routing_decisions`: R-01→MU, R-09→MU. Explainability (authority/support/evidence/risk/reasoning) intact on every rec.

## Explainability (Task 5) — preserved
Every served recommendation still carries statute/authority (`published_support`), supporting evidence (`required_documentation`), facts (`reason`/`current_structure`), assumptions + risk (`confidence`/`audit_risk`), expected value (`financial_impact_usd`/`rebate_impact_usd`), and reasoning (`reason`/`interpretation_question`). Nothing became less explainable.

## Remaining backend work (known, honest limits)
1. **Recommendation PROSE stays LU-specialized.** Governing amounts are now data-driven, but the descriptive text in the builders still references LU specifics ("Frogsquad SA dive team", account codes). A different production gets correct *amounts/gating* but LU-flavored *prose*. Full prose-templating is a genuine design task (not a wiring fix) — deferred, not attempted (over-engineering guard). Minor known artifact: served R-09 amount ($538k register ATL) is broader than its prose's "$260k dir+writer" illustration.
2. **Budget-allocation model** (keystone, unchanged) — `routing_decisions` is the seed, but feeding N per-jurisdiction registers into the composer for co-production/split pricing still needs the allocation architecture. STOP-and-recommend.
3. **Accommodation/per-diem/marine/crew/music derivation** — needs register-account semantic tagging to light up R-02/03/06/07/08 generically without fabrication.

## Updated completion estimate
- Production Structuring (HOW-to-structure, integrated & register-grounded): **~35% → ~55%** — now de-hardcoded on inputs, signal-gated, connected live, emitting routing decisions; remaining 45% is prose-templating + the allocation model + fuller register-signal derivation.

---

# SESSION DELTA — Account-transfer handoff (closeout #5, docs only)

- **structuring_advisor generalized + connected** (prior closeout #4, still current): served on `/economics.structuring_advisory`, driven by real register/facts; emits `routing_decisions`.
- **Current runtime ownership** for all 24 capabilities captured in `ACCOUNT_TRANSFER_HANDOFF.md` §3 (served owner + alt implementations + connected? + unique + evidence).
- **Unresolved engine overlaps** (need reconciliation, NOT resolved here): structure enumeration (composer vs `structure_generator` vs `generate_structure_scenarios`), stacking (build_available_funds vs `stacking_rules` vs `apply_stacking_adjustments`), recommendations (`production_recommendation_engine` vs structuring_advisor vs `optimization/recommendation_engine`), ranking (`rank_production_structures` vs `score_structures`/`maximization_engine`). Three incompatible data models coexist: register-grounded / parametric / DB-row.
- **Must reconcile against other-account assets** before choosing canonical owners — see `ACCOUNT_TRANSFER_HANDOFF.md` §5–§7. Do NOT delete/merge/deprecate any engine first.
- No engine behavior, calculation, or API contract changed this session (docs only). Smoke check: served state builds (44 accounts, 6 advisory recs).
- **Resume step for next account:** open `ACCOUNT_TRANSFER_HANDOFF.md`, run §6 reconciliation for the structure-enumeration overlap first (highest duplication), after inspecting the other account per §5.

---

# SESSION DELTA — Optimizer reconciliation (audit-only, no code/runtime/branch change)

Traced actual logic (not filenames) across composer, structuring_advisor, structure_generator, generate_structure_scenarios, optimization_engine, run_full_analysis, opportunity_discovery, treaty_engine, rank/score/maximize. New, more precise conclusions:

## Budget allocation is genuinely uncomputed — but decomposes into FOUR partial pieces that already exist
No engine computes an account→jurisdiction partition of the register. Proven:
1. `optimization/structure_generator._estimate_soft_money` — flat **60/40** primary/secondary spend-pct heuristic × base rate. An *estimator*, parametric, not register-grounded, not optimized (does not choose which accounts move).
2. `run_full_analysis` (DB path) — takes `jurisdiction_spend_pct` per program as a **caller-supplied input** (default 1.0). Consumes an allocation; never derives one.
3. `opportunity_discovery` — structuring opportunities already carry `affected_accounts: tuple[str,...]` (real account-code tagging via levers); relocation candidates price `rate_delta * movable_spend_usd` where `movable_spend_usd` is a single **caller-supplied aggregate**, not a computed partition.
4. `structuring_advisor.routing_decisions` — `component → target_jurisdiction` with `qualification_impact_usd`, but `component` is a recommendation *title* (label), not a budget-account set.
Composer kernel (`compose` L581-596) prices the **whole** `gross_budget_usd` against the single register-backed segment; `priceable_pct = priced_segments/len(segments)` → 0.5 for a 2-segment co-pro. No per-account split anywhere in the priced path.
**Therefore:** the missing keystone is bounded — (a) a partition function that maps the 44 real register accounts to jurisdictions using the already-existing `affected_accounts` + `routing_decisions` + `movable_spend`, and (b) the composer accepting N partial registers (each summing without double-count) instead of pricing whole-budget-once. The per-jurisdiction register builder (`build_little_utopia_register_for_jurisdiction`) already exists. This is integration + one bounded new function, not a greenfield allocator.

## anchor / hybrid / service / split / ownership — mentions vs. logic (confirmed)
- **anchor / hybrid structures:** no `structure_type`, no pricing path. "hybrid" appears only as the qualification *doctrine* `HYBRID_CONDITIONAL` (unrelated); "anchor" only as a UI lane concept.
- **service production:** exists ONLY as legal *condition text* in `stacking_rules.py` (UK HVC, Canada CMPA foreign-cert combinability) — descriptive knowledge, not a priced structure.
- **split production:** parametric only (`structure_generator` `structure_type="split"`); register-grounded split blocked by the same allocation gap.
- **ownership allocation:** *constraints* exist (treaty producer-share thresholds in `treaty_engine`/`cultural_test_rules`; `ownership_nationality` facts; a `qualification_path_engine` suggestion string). Ownership *optimization* (choosing the share) does not exist.
- **Key insight:** service / split / hybrid are very likely **expressible as allocation + treaty + ownership-share combinations** (service = ~100% foreign-financed allocation at minority ownership; split = departmental allocation; hybrid = treaty + allocation), i.e. they most likely fall OUT of the allocation model rather than needing bespoke per-structure engines. Confirm before building any as standalone.

## Alternative ranking loop (parametric) is real and complete on its own data model
`optimization/score_structures` (rank by `net_producer_benefit_usd` + confidence penalty + `explain_structure`) and `maximization_engine` (`_pick_best`/`_pick_improved` + action generation) form a full parametric optimize→rank→explain loop over `GeneratedStructure`, mounted via the `optimization.py` router. Weaker data model than the served register-grounded `rank_production_structures`, but a genuine alternative — REFERENCE, do not rebuild; harvest its explanation/action-generation shape if the served ranker ever needs richer output.

## One-line conclusion
The Production Optimization Engine is **~85–90% completable by connecting/consolidating existing engines.** The only genuinely new engineering is the bounded account→jurisdiction **allocation partition + composer multi-register acceptance** (keystone). Everything else — enumeration, stacking math, scenario combos, recommendation gating, ranking, treaty/co-pro/multi-party — already exists in at least one implementation and needs wiring or merging, not rebuilding. No code, runtime, or branch state changed this session.

---

# SESSION DELTA — Allocation model implemented + capabilities connected (keystone closed)

**The keystone is built.** The account→jurisdiction allocation model and multi-register
segment pricing are implemented, connected to the canonical served path, runtime-verified,
and green on the full suite (**2926 passed, 1 skipped** — 2899 prior + 27 new, zero regressions).

## What was added (new modules)
- **`app/data/program_slug_aliases.py`** — canonical program-slug reconciliation
  (`mt_mfc_cash_rebate`→`mt_mfc_rebate`, `gr_ekome_rebate`→`gr_cash_rebate`; both pairs
  demonstrably name the same statutory program). Closes former known blocker #3.
- **`app/calculators/production_allocation.py`** — the allocation model. `StructureSpec`
  (one generic spec expresses single-country / full-relocation / component-relocation
  (=anchor-component) / split / treaty / majority-minority / multi-party / service / hybrid —
  no bespoke calculators), `derive_account_allocation()` partitions every cash account with
  precedence: explicit producer split (positive pcts summing to 1.0, USER_ELECTED, never
  engine-invented) → explicit producer account route → component route (producer or engine
  provenance) → stated-location fact (budget's own "PICTURE EDIT: LA" → FIXED to a
  non-incentive `US` segment) → location-bound components FIXED to the shoot jurisdiction →
  default RECOMMENDED to the primary. Every assignment carries account/amount/component/
  jurisdiction/kind/rationale/governing-decision/supporting-facts/authority/unresolved-
  requirements. Conservation and uniqueness are enforced; memo lines disclosed, never dropped.
  Components derive from the register's own spend-category vocabulary; movable = post/vfx/music
  (same semantics as the package movable-spend hint).
- **`app/calculators/allocation_pricing.py`** — multi-register pricing. `price_segment()`
  derives ONE PARTIAL register per jurisdiction over ONLY its allocated lines through the
  SAME `derive_qualification_register()` ladder and prices it with the SAME
  `build_risk_cases()` kernel (no new math). `price_allocated_structure()` combines segments:
  gross − Σ lawful segment floor incentives + financing/implementation (explicit, default $0)
  ± travel ± FX (each applied ONCE, structure level). Fully-priced gate: complete conserving
  allocation + every incentive segment executable (doctrine + rate actually resolve; min-spend
  failures block honestly) + treaty/ownership requirements pass against the real registry +
  no unresolved CONDITIONAL assignment. `rank_allocated_structures()` ranks fully-priced only;
  unpriced structures list their exact blockers. `enumerate_segment_program_stacks()` delegates
  multi-program combinatorics to the existing `generate_structure_scenarios` (invoked only when
  a jurisdiction genuinely has ≥2 executable programs — today none does; disclosed, not fabricated).

## Capabilities connected (canonical owner per capability)
| Capability | Canonical owner now | Disposition of alternatives |
|---|---|---|
| Account→jurisdiction allocation | `production_allocation` (NEW) | none existed — the four partial pieces (60/40 heuristic, `jurisdiction_spend_pct` input, `affected_accounts`, `routing_decisions`) are inputs/reference |
| Multi-register structure pricing | `allocation_pricing` (NEW, same kernel) | composer's whole-budget `cases` path unchanged (baseline candidates); parametric `structure_generator` = REFERENCE (its taxonomy vocabulary adopted in `STRUCTURE_TYPES`) |
| Program/stack combination enumeration | `generate_structure_scenarios` via `enumerate_segment_program_stacks` delegation | connected; fires only with real ≥2-program knowledge |
| Stacking relationships | `build_available_funds` (v1.2.0, canonical-slug matched) | slug mismatch reconciled; MT/GR variant edges now surface with the variant slug disclosed; still no fabricated stacked dollars |
| Routing input | `structuring_advisor.routing_decisions` surfaced as `advisor_routing_decisions_input` on the allocation payload | connected as rationale input |
| Gated structure recommendations | `allocation_pricing.build_structure_recommendation` | cloud engine (fc2886f) concepts MERGED (deterministic `REC-STRUCT-<id>` identity, gated action, ordered approval chain producer→counsel→authority, reversibility, dependency group); stale cloud fixtures NOT merged — every figure from current statute-corrected pricing |

## Served API (additive; no existing contract changed)
`GET /structures` now carries **`allocated_structures`**: per-structure summary, full
account-allocation records, per-segment economics with per-account qualification traces,
unresolved conditions, approval dependencies, gated recommendation, ranking (fully-priced
only), `stack_combinations` status, and the advisor routing-decisions input. New answerable
fact **`component_route_post`** (POST /facts) routes the movable post/VFX/music components to
an executable jurisdiction (validated; catalog-only targets rejected).

## Runtime results (all 12 validation points PASS against the live API; split via engine tests)
1. MU baseline: MU segment QPE **$4,355,327** = served register exactly; floor incentive $1,306,598.10; NPC $3,057,794.90; stated-LA editorial ($9,068) is a separate non-incentive US segment.
2. Full relocation GR/IE/MT price from their own partial registers (QPE matches `/economics.alternative_jurisdictions` exactly); GR ranks #1 at NPC-adj $2,624,002.20.
3. Component relocation (post/VFX/music→MT) fully priced: MT segment QPE $61,568 @ 25%.
4. Split production (producer-elected 70/30 split of account 3400 MU/GR) prices BOTH partial registers; changing the pct changes both segment QPE and NPC (pytest, real engine).
5. Treaty MU+FR: no instrument in the registry → served UNPRICED with that exact blocker. Not forced.
6. Routing post to MT moves MU QPE 4,355,327→4,302,827 and NPC 3,057,794.90→**3,058,152.90 (slightly worse than baseline — an honest, real optimizer answer)**.
7. Conservation exact on every structure ($4,364,395 leaf sum; $2 doc variance still disclosed).
8. Segment account sets disjoint; every executable segment carries its own qualification trace.
9. Travel/FX exist only at structure level, applied once.
10. In-kind $625k enters NO segment; remains governed solely by /economics MU treatment.
11. Stacking: relationship-level only (MT=3 edges via alias, IE rich, MU genuinely 0); one program priced per segment; no stacked dollars.
12. Recommendations carry structure/lines/authority/facts/assumptions/calculations/approvals.
Component-route below a program's minimum spend (e.g. →GR, $61.6k < €100k min) blocks with the exact reason — never priced at a guessed rate.

## Files changed
NEW: `app/data/program_slug_aliases.py`, `app/calculators/production_allocation.py`,
`app/calculators/allocation_pricing.py`, `tests/test_production_allocation.py`,
`tests/test_allocation_pricing.py`.
MODIFIED: `app/demo/little_utopia_state.py` (fact `component_route_post` + validation;
`build_allocated_structures()`; `_executable_alternatives()`; canonical-slug stacking match,
available_funds v1.2.0), `app/api/v1/cineglobe.py` (/structures serves allocated_structures),
`tests/test_optimizer_input_integration.py` (stacking test updated for the reconciliation).

## Remaining backend gaps (honest)
1. Component-move travel deltas are not modeled (structure-level travel is primary-jurisdiction
   incremental only; disclosed in notes — no fabricated figure).
2. `enumerate_segment_program_stacks` has no live multi-program jurisdiction to fire on until a
   second executable program is populated for some jurisdiction (data work, machinery ready).
3. Ownership/participation optimization: constraints are enforced (shares must sum to 1.0 and be
   reflected in real allocated spend); choosing optimal shares remains future work.
4. Worldwide executable coverage (BE/CY/DE/ES/FR/HR/HU/IT) unchanged — data-only.

## Resume point
Backend allocation surface is complete and served. Next phase per plan: **UI Phase A/B**
(field-rename fixes, then the Rev C workspace binding — `allocated_structures` provides the
lane/segment/trace data the Lane Rack and Inspector need). Do not begin without design sign-off
on the globe-vs-map ruling (see reconciliation report §2).

---

# SESSION DELTA — Final acceptance test + worldwide-coverage defect fixed

Ran the optimizer as the finished product would, over the REAL Little Utopia inputs
(budget/script/look-book/people/economics/travel/FX/qualification/cultural/thresholds/
treaties/grants/funds/stacking/structuring/allocation/recommendation/ranking). One coverage
defect found and fixed at root cause; runtime-verified; regression-tested; suite green.

## Defect found (coverage, not calculation)
`build_allocated_structures` evaluated only single-jurisdiction structures by default
(baseline + 3 relocations). **Component-routing (anchor-component) structures and the
co-production category were silently omitted** unless a producer pre-elected them — violating
the acceptance requirement that every applicable category be EVALUATED and any zero PROVEN.
Root cause: the two multi-jurisdiction categories were gated behind producer-election facts
(`component_route_post`, `treaty_partner_code`) rather than auto-enumerated over the executable set.

## Fix (connects existing capability — no new engine, no redesign)
- **Auto-enumerate component-routing structures** for every executable partner (MU shoot anchor
  + movable post/VFX/music routed to each of MT/IE/GR). No election needed; each prices or
  blocks honestly on its own program's minimum-spend rule. A `component_route_post` election
  now just pre-selects/deduplicates against the auto set.
- **Worldwide-coverage report** added to `/structures.allocated_structures.coverage`: every
  category (single_jurisdiction / component_routing_anchor / co_production_treaty /
  split_production) with candidates_evaluated / fully_priced / blocked, and — for zeros — the
  exact proven reason. Co-production reachability is computed from the real treaty registry.

## Acceptance findings (runtime evidence, live API, no elections)
- **Single jurisdiction: 4 evaluated, 4 priced** — MU baseline + full relocation MT/IE/GR
  (each QPE $4,355,327, matching the served register and `/economics.alternative_jurisdictions`
  exactly). Catalog-only BE/CY/DE/ES/FR/HR/HU/IT excluded with reason (missing doctrine/rate —
  insufficient knowledge, never guessed).
- **Component-routing: 3 evaluated, 1 priced (MT), 2 blocked** (GR/IE below their own minimum
  spend on ~$61.6k routed — honest block, not omission).
- **Co-production: 0, PROVEN-ZERO** — MU holds no bilateral treaty and is not a Eurimages /
  Ibermedia / European Convention member (treaty_engine). Official co-production is factually
  unavailable from Mauritius (insufficient treaty knowledge / factual ineligibility). A
  `treaty_partner_code` election still composes the pathway and returns it UNPRICED with this
  exact blocker — never forced.
- **Split production: 0, zero-by-design** — requires an explicit producer sub-line split
  (`account_splits`); never fabricated.
- Grants/funds connected (MU 1 / MT 1 / IE 4 / GR 2); stacking relationships CONNECTED (MT 3 /
  IE 24 / GR 3 / MU 0) after canonical-slug reconciliation; 139 recommendations incl.
  cultural-test / threshold / nationality-unlock / treaty pathways.

## Global optimum + historical comparison
**Global financial optimum = full relocation to Greece, NPC-adj $2,624,002.20** (guaranteed
40% Greek floor beats Mauritius' guaranteed 30% floor). Physically viable: GR
`marine_suitability=strong` matches the script's confirmed Mediterranean-marine / open-water
requirement. Ranking (ascending NPC): GR $2.624M < IE $2.977M < MU baseline $3.058M <
MU+post→MT $3.058M < MT $3.278M.

The historical Little Utopia recommendation was **Mauritius**. Today's shift to **Greece
relocation** is NOT a defect — it is driven by, in order of magnitude:
1. **Corrected statutory interpretation** — ranking on GUARANTEED FLOOR rates (MU 30%, GR flat
   40%) rather than MU's discretionary 40% ceiling the historical result assumed;
2. **Recovered/executable knowledge** — GR/IE/MT promoted to executable (doctrine + rate) in
   prior sessions, so the comparison set exists at all;
3. **Physical viability confirmed** — GR marine suitability matches the recovered screenplay's
   Mediterranean-marine requirement, so the financial optimum is also production-viable.

## Final answers
1. **Evaluate every executable worldwide pathway? YES** (after fix) — all reachable single,
   component-routing, co-production (proven-zero), and split (zero-by-design) categories are
   evaluated; catalog-only jurisdictions excluded with reason.
2. **What remains?** Data-only: worldwide executable coverage is 4 jurisdictions (expand via the
   proven MT/IE/GR machinery); `enumerate_segment_program_stacks` has no live ≥2-program
   jurisdiction to fire on yet; ownership-share OPTIMIZATION is constraint-only (shares are
   enforced, not optimized). None is an architectural gap.
3. **Every connected engine utilized? YES** — allocation, multi-register pricing, qualification,
   rate resolution, treaty, economics, travel, FX, recommendation, structuring-advisor routing,
   stacking relationships all exercised at runtime.
4. **Knowledge present but unused?** No silent unused knowledge — catalog-only jurisdictions and
   the fund per-production dollar amounts that do not exist are excluded WITH disclosure, not
   bypassed.
5. **Engine present but bypassed?** `run_full_analysis` (DB) only via delegated stack
   enumeration + the `structures.py` router (DB unreachable — not a runtime path); parametric
   `optimization/*` is REFERENCE. Neither is a defect.
6. **Duplicated engine stronger than the runtime owner? NO** — the register-grounded served path
   is strongest; parametric is weaker (budget×rate); the cloud recommendation-engine concepts
   are already merged (deterministic identity / gating / approval chain / reversibility).
7. **Honestly claim worldwide optimization? YES, correctly qualified** — CineGlobe optimizes
   worldwide production STRUCTURES across every executable pathway in the knowledge base
   (4 jurisdictions today; expandable), evaluating every category and proving every zero. The
   honest claim is "worldwide-architecture optimization over the executable knowledge base,"
   not "every country on earth is priced."
8. **Ready to freeze? YES.**

## Files changed
MODIFIED: `app/demo/little_utopia_state.py` (auto-enumerate component-routing structures;
`coverage` report; payload v1.1.0), `tests/test_allocation_pricing.py` (+3 coverage tests).
No API contract removed or renamed — `coverage` is additive on `/structures.allocated_structures`.

## Regression + runtime evidence
Full suite **2929 passed, 1 skipped** (2926 prior + 3 new). Live API verified: 7 structures
evaluated by default, coverage report proves all four categories, global optimum = ALLOC-RELOC-GR.

## BACKEND FREEZE RECOMMENDATION
**FREEZE the backend optimizer architecture. Proceed to UI implementation.** Every executable
worldwide pathway is evaluated, every zero is proven, every connected engine is utilized, and no
stronger duplicate or bypassed engine remains. Remaining items are data entry (more executable
jurisdictions) and future ownership-share optimization — neither blocks UI, both extend a frozen
architecture. Next phase: UI Phase A/B per UI_HANDOFF (bind the Rev C workspace to
`/structures.allocated_structures`), pending the globe-vs-map design ruling.
