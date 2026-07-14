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
