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
