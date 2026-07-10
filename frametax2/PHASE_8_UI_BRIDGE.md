# Phase 8 UI Bridge — Backend Readiness & Implementation Blueprint

Status: backend intelligence platform complete (Phases 4–8's Legal Engine). This
document is the bridge deliverable requested before UI implementation begins. It
maps every engine's output to a UI destination, confirms interface stability,
documents the presentation adapters added, and lays out the Phase 8 roadmap
without performing it.

**No engine logic changed. No UI built. No API routes added.** One new file,
`app/calculators/ui_presentation.py`, was added — pure, read-only reshaping of
already-computed outputs (see §2).

---

## 0. Important finding before anything else

**No React/frontend project currently exists against this backend.**
`frametax2/` has no `frontend/`, no `package.json`, no `src/` UI tree. Two
unrelated single-file JSX prototypes exist elsewhere on this machine
(`~/dev/Frametax/FrameTax.jsx`, `~/Projects/frametax/FrameTax.jsx`) — per their
own build-discipline skill, these are browser-only calculators bundled with
esbuild into a static HTML file, with **zero network calls and zero connection
to this backend's API**. They are a different, earlier product iteration, not
Phase 8's target.

This changes nothing about the mapping or roadmap below — the backend is
equally ready either way — but it means task 6 ("smallest number of
React/frontend changes") has no existing pages to enrich yet. Section 4 gives
the minimal *new* page plan this implies, still scoped as tightly as if pages
already existed.

---

## 1. Complete backend → UI mapping

Grouped by the pipeline order the demo script (`scripts/run_production_demo.py`)
already exercises end-to-end.

### 1.1 Intake

| Engine | Outputs | Key data objects | Public interface | UI destination |
|---|---|---|---|---|
| **Production Package Intelligence** | Structured intake summary | `ProductionPackage`, `BudgetIntelligence`, `ScriptIntelligence`, `PackageIntelligence`, `LocationIntelligence`, `TravelIntelligence` | `build_production_package()` | **Intake** wizard — single entry screen |
| **Budget Intelligence** | ATL/BTL/POST totals, category breakdown, opportunity signals | `BudgetIntelligence`, `OpportunityHint` | `build_budget_intelligence()` | **Budget Insights** card (within Intake or a dedicated tab) |
| **Script Intelligence** | 23 script attributes (language/period/marine/VFX-intensity/…), locations mentioned | `ScriptIntelligence`, `AttributeFact` | `build_script_intelligence()`, `derive_likely_cultural_test_categories()` | **Script Insights** card (within Intake) |
| **Question Engine** | Ranked list of missing facts, blocking vs. non-blocking, discovery hints | `MissingInput`, `DiscoveryHook` | `generate_missing_inputs()` (called inside `build_production_package`) | **Missing Information Wizard** — a guided follow-up flow, not a new top-level page |

### 1.2 Qualification & Discovery

| Engine | Outputs | Key data objects | Public interface | UI destination |
|---|---|---|---|---|
| **Creative Qualification Engine** | Pass/fail per cultural test, minimal paths to qualify, non-creative alternative | `CreativeQualificationAnalysis`, `QualificationPath` | `analyze_creative_qualification_paths()` | **Qualification Panel** |
| **Cultural Test framework** | Per-criterion scored results | `QualificationTestResult`, `CriterionResult` | `cultural_test_rules.score_*_test()` (7 tests) | Feeds the Qualification Panel directly |
| **Opportunity Discovery** | Ranked candidate optimization paths (jurisdiction/treaty/stacking/structuring/reinvestment/normalization/grey-area) | `Opportunity`, `OpportunityCollection` | `discover_all_opportunities()` | **Opportunity Explorer** — supporting detail view, one level under Recommendation Center |

### 1.3 Structuring & Optimization

| Engine | Outputs | Key data objects | Public interface | UI destination |
|---|---|---|---|---|
| **Production Structure Composer** | Multi-jurisdiction candidates, treaties/stacks/funds attached, constraints, priced/unpriced % | `ProductionStructureCandidate`, `CompositionResult` | `compose_production_structures()` | **Structure Comparison** grid |
| **Global Scenario Ranker** | Baseline + relocation structures, ranked by Risk-Adjusted NPC | `ProductionStructure`, `StructureRankingResult` | `compose_candidate_structures()`, `rank_production_structures()` | Feeds Structure Comparison's ranked table |
| **Production Scenario Engine** | Named "what-if" comparisons (move VFX/post/music, create SPV/co-production) | `ProductionScenario`, `ScenarioResult` | `run_scenario()` | **Scenario Explorer** |
| **Production Constraint Engine** | Compatible/incompatible candidates against producer-fixed decisions | `ProductionConstraint`, `ConstraintCheckResult` | `filter_candidates_by_constraints()` | Filter controls on Structure Comparison |
| **Optimization Engine** | Conservative/Base/Optimistic/Risk-Adjusted NPC per structure | `CaseResult`, `OptimizationResult` | `build_risk_cases()` (called by Composer) | The 4-case table on every structure card |
| **Travel model / FX** | Travel cost estimate, net-incentive-after-travel; USD↔local conversion | `TravelCostEstimate`, `FXConversionResult` | `travel_model.estimate_travel_cost()`, `apply_fx_rates.convert_to_usd()` | **Travel Optimization** card, **FX Optimization Card** — both secondary widgets on a structure's detail view |

### 1.4 Recommendations & Legal

| Engine | Outputs | Key data objects | Public interface | UI destination |
|---|---|---|---|---|
| **Recommendation Engine** | Ranked, gated recommendations (financial/structural/creative/required-input) | `Recommendation`, `RecommendationSet` | `generate_production_recommendations()` | **Recommendation Center** |
| **Legal Engine** | Auto-detected legal questions, acquisition cycle status, commit/score results | `LegalQuestion`, `AcquisitionCycleResult`, `CommitResult`, `RerunResult` | `LegalEngine.detect_open_questions()` / `.run_acquisition_cycle()` / `.commit_and_score()` / `.rerun()` | **Legal Workspace** |
| **Evidence Graph** | Full Rule ⟶ Evidence ⟶ Citation ⟶ AuthoritySource ⟶ DocumentVersion chain, or an AbsenceOfAuthority | `trace_rule()` / `trace_recommendation()` output | `EvidenceGraph.trace_rule()` | **Evidence Drawer** — slide-out from any recommendation or structure card |
| **Authority Score** | 0–100 composite + 6-dimension breakdown + confidence band | `AuthorityScore`, `AuthorityScoreBreakdown` | `score_rule()`, `score_recommendation()` | **Confidence Indicators** — small badge inline everywhere a Rule-backed figure appears |
| **Grey Areas** (`qualification_model`) | Open items requiring authority, quantified upside, LAAE task ref | `GreyAreaItem` | `build_little_utopia_grey_areas()`-style builders | **Legal Issues Panel** — a filtered view inside Legal Workspace |
| **LAAE** | Prioritized acquisition docket | `AcquisitionTask`, `AcquisitionDocket` | `build_docket()` (wrapped by Legal Engine) | Legal Workspace's docket list |

**One explicit legacy note:** `structuring_advisor.py`, `mediterranean_comparison.py`, `generate_structure_scenarios.py`, and `rank_production_structures.py` are the pre-Phase-4 (Phase D/F) equivalents of Levers, Opportunity Discovery, the Scenario Engine, and the Global Scenario Ranker respectively. The current `api/v1/optimization.py` routes (`/recommendations`, `/generate-structures`, `/maximize`) call the *legacy* stack, not the Phase 4–8 engines above. This is a real gap for Phase 8A to close (route the API to the new engines) — not something to fix here, since it requires new API routes, which are out of scope for this bridge task.

---

## 2. Stable interface confirmation

All 18 Phase 4–8 calculator modules import cleanly and expose substantial,
already-public top-level surfaces (verified by direct import + `dir()` this
session — no leading-underscore-only modules, no missing exports):

`opportunity_discovery` (44), `production_structure_composer` (30),
`global_scenario_ranker` (21), `production_recommendation_engine` (48),
`production_package_intelligence` (58), `creative_qualification_engine` (15),
`production_constraint_engine` (14), `production_scenario_engine` (21),
`legal_engine` (46), `legal_authority_acquisition` (61), `evidence_graph` (18),
`authority_score` (30), `jurisdiction_graph` (29), `qualification_model` (32),
`optimization_engine` (24), `levers` (21), `cultural_test_rules` (26).

Every dataclass mentioned in §1 is a plain Python `@dataclass` (or
`@dataclass(frozen=True)`) — no ORM coupling, no hidden mutable state, no
network calls on construction. **No engine requires a change to be UI-ready.**

## 3. Presentation adapters added

One new file: `app/calculators/ui_presentation.py` (4 functions, 1 constant
table, zero conditionals that decide a fact — only presence/absence
formatting). Added because three shapes recur across engines and are
genuinely awkward for JSON/UI consumption without a translation step:

| Adapter | Problem it solves | Business logic added |
|---|---|---|
| `case_dict_to_display(cases)` | `dict[RiskCase, CaseResult]` — enum keys don't round-trip through JSON | None — re-keys by `RiskCase.value`, copies fields verbatim |
| `attribute_fact_to_display(fact)` | `AttributeFact` (state/confidence/discovery-sources) needs unpacking at every call site (person nationality, entity jurisdiction, location jurisdiction, travel origin/destination) | None — reads existing `state`/`is_actionable`/`confidence` fields |
| `evidence_chain_to_display(chain)` | `EvidenceGraph.trace_rule()` returns `list[dict]` whose *values* are dataclass instances (Evidence, Citation, AuthoritySource, DocumentVersion, Document) — not directly serializable | None — flattens to primitive fields, preserves the graph's own order |
| `group_recommendations_by_category(recs)` | UI needs all 4 categories grouped for a tabbed view; `RecommendationSet.of_category()` only returns one at a time | None — groups only, preserves rank order within each group |
| `AUTHORITY_TIER_LABELS` | `AuthorityTier.OFFICIAL_GUIDANCE` → UI needs "Official Guidance", not the enum name | None — static `.title()` reformat of the 14 existing tier names |

All four functions were runtime-verified against real Little Utopia output
this session (`case_dict_to_display` against a fully-priced composer
candidate, `attribute_fact_to_display` against known/unknown/
verification-required facts, `evidence_chain_to_display` against a real
committed Legal Engine chain, `group_recommendations_by_category` against 142
real recommendations) and confirmed JSON-serializable via `json.dumps()`.
22 new tests added (21 passing, 1 correctly skipped — no unpriced candidate
existed in that particular composition run to exercise the empty-dict path).

**No other adapter was needed.** Every other engine's output (`Opportunity`,
`ProductionStructureCandidate`'s non-`cases` fields, `Recommendation`,
`MissingInput`, `LegalQuestion`, `AuthorityScore`, `GreyAreaItem`, `QPEAccount`,
`TravelCostEstimate`, `FXConversionResult`) is already a flat-enough dataclass
of primitives/tuples/single-level nesting that a generic
`dataclasses.asdict()` + enum-`.value` pass (a five-line utility any API
serialization layer will need regardless) handles without a bespoke adapter
per engine. Building one anyway would be exactly the "unnecessary
abstraction" the standing rules forbid.

---

## 4. Minimal React implementation plan

Since no frontend exists yet, "smallest number of changes" means: the fewest
*pages*, each backed directly by the interfaces in §1 with no engine-side
prerequisite work.

**5 screens cover the entire mapping** (not 15 — several §1 rows are cards
*within* a screen, not separate pages):

1. **Intake** — Production Package form → Budget/Script Insights cards inline
   → Missing Information Wizard triggered from the same screen when
   `ProductionPackage.blocking_missing_inputs` is non-empty.
2. **Qualification Panel** — Creative Qualification results per relevant
   cultural test, with the lowest-impact path and non-creative alternative
   both shown side by side (never one presented as "the" answer, per the
   Creative Qualification Engine's own design).
3. **Structure Comparison** — Composer candidates as cards, 4-case table via
   `case_dict_to_display()`, constraint filter toggle, Scenario Explorer as a
   drawer off this screen (not a separate page — a "what if" modal is a
   smaller change than a new route).
4. **Recommendation Center** — `group_recommendations_by_category()` feeds
   4 tabs directly; Evidence Drawer and Confidence Indicator open from any
   recommendation card.
5. **Legal Workspace** — Legal Engine's docket, acquisition cycle status, the
   two human gates (verify/approve) as explicit UI actions, Legal Issues
   Panel as a filtered sub-view (open grey areas only), Evidence Drawer
   reused from screen 4.

Cross-cutting, not separate screens: **Evidence Drawer** and **Confidence
Indicator** are components reused from screens 4 and 5 everywhere a
Rule-backed figure appears — building them once and reusing them is the
single highest-leverage frontend decision available, and it's already implied
by `evidence_chain_to_display()`'s and `AUTHORITY_TIER_LABELS`' existence.

## 5. Ordered Phase 8 roadmap (prepared, not performed)

**Phase 8A — Surface existing intelligence.**
Wire the 5 screens above to the Phase 4–8 engines (via new, thin API routes —
out of scope for this bridge task, but the natural next PR). Route
`api/v1/optimization.py` off the legacy stack and onto
`opportunity_discovery` / `production_structure_composer` /
`production_recommendation_engine` / `legal_engine`. No new intelligence; pure
exposure.

**Phase 8B — UI polish.**
Loading/empty/error states per screen, Confidence Indicator visual treatment,
Evidence Drawer transitions, form validation on Intake matching
`ProductionPackage`'s known/unknown/verification-required states.

**Phase 8C — Workflow refinement.**
Missing Information Wizard sequencing (blocking questions first), the
Legal Workspace's two-gate approval flow as a guided sequence, Scenario
Explorer comparison UX (baseline vs. scenario side-by-side), constraint
builder UX.

**Phase 8D — Visual refinement.**
Design system application, responsive layout, accessibility pass, print/export
views. No engine or data-shape work remains by this point.

## 6. Confirmation

**Backend changes were not necessary for UI implementation to begin.** Every
engine already exposed a stable, importable, dataclass-based public interface;
the one addition (`ui_presentation.py`) is a convenience layer for 3
genuinely awkward shapes, not a prerequisite — a frontend/API team could have
started against the raw engine outputs directly, just with a few more lines
of client-side reshaping per call site.

**CineGlobe's backend is ready for Phase 8A.** The single non-engine gap
identified (§1, legacy note) — `api/v1/optimization.py` calling the
pre-Phase-4 stack instead of the current engines — is an API-routing task for
Phase 8A itself, not a backend readiness blocker.
