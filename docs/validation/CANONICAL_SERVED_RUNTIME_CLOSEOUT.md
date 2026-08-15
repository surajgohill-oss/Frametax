# Canonical Served Runtime — Cutover Closeout (Phase 2)

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`

## Gate

**`CANONICAL_SERVED_RUNTIME_BLOCKED`** — most of the gate is met and verified live in the browser for both projects. One item is genuinely blocked, for a reason grounded in this session's own hard rules, not effort: the deep served Little Utopia Workspace/Globe/Overlay UI (`/production/*`, `useCineGlobe()`) still reads `build_allocated_structures()`'s detailed per-segment response, and fully replacing that shape generically is "rebuilding the optimizer" (Rule 1) and "redesigning the Workspace" (Part T) — both explicitly out of this phase's scope. See "What remains blocked" below for the precise reasoning and the evidence that ruled out a partial cutover.

## Old served paths (unchanged reference)

- **System A** — `/api/v1/cineglobe/*` → `app/demo/little_utopia_state.py::build_allocated_structures()`. Confirmed in Phase 1 to already use the canonical calculators (`production_allocation`, `allocation_pricing`, `production_discovery`, `qualification_model`) — its defect was DATA (the singleton), not the wrong engine.
- **System B** — `POST /projects/{id}/evaluation/begin` → `app/services/project_evaluation.py` → `run_full_analysis` (ENGINE_VERSION 0.1.0). Proven in bca893a to be the wrong engine: zero canonical-layer references, $1.12M off Little Utopia's accepted NPC.

## Canonical final path (built and served this phase)

```
POST /projects/{id}/evaluation/begin
  -> app/services/canonical_evaluation.py::evaluate_project()
       canonical_project_economics.build_project_economic_inputs()   (Phase 1)
       -> derive_production_requirements() + discover_executable_jurisdictions()  (Phase 6, generic)
       -> per candidate: derive_qualification_register() -> derive_account_allocation()
          -> price_allocated_structure()                              (canonical, generic)
       -> persist ProductionStructure / StructureCalculationResult
       -> read back + rank -> one response model
```

`app/api/v1/evaluation.py` now imports `canonical_evaluation.evaluate_project` exclusively — `project_evaluation.py` / `run_full_analysis` are no longer reachable from the served route (locked in by `test_evaluation_route_no_longer_reaches_run_full_analysis`).

## The "invented savings" finding (new this phase)

Running the full canonical service against Little Utopia surfaced a real bug in the naive design: several real, honestly-priced relocation candidates (e.g. full relocation to CA-NL, `npc_verified_usd = $2,742,714.60`) showed a *lower* cost than the Mauritius baseline — not because they're actually cheaper, but because no generic project has travel/FX/in-kind-replacement data yet, so those costs price as zero. The already-served, already-accepted System A comparison includes exactly these costs for Mauritius's own curated alternatives (`npc_with_adjustments_usd = $4,097,014.60` for the same CA-NL relocation, once travel + $625k in-kind post replacement are included) — which is why Mauritius correctly wins there.

Reproducing that curated data generically would mean fabricating travel/FX assumptions for every other project — a second, worse violation of "no invented local production-cost savings." The fix implemented instead: **the baseline structure — the production's own confirmed base jurisdiction — is the only structure eligible to be the served "winner" in this phase**, since it needs no relocation-cost adjustment by construction (no relocation occurs). Every other PRICED candidate is still computed, persisted, and shown, explicitly labeled with `relocation_cost_normalized: false` and `RELOCATION_COMPARABILITY_NOTE` disclosing why its NPC is not a fair comparison yet. This is the same MFNI-honesty principle from the prior two phases, applied one layer deeper.

`test_relocation_candidates_never_outrank_the_baseline` locks this in directly against Little Utopia's own real data (confirms real cheaper alternatives exist, confirms the baseline still wins).

## Little Utopia result — EXACT, unchanged from Phase 1

- **Winner:** Mauritius
- **NPC:** **$3,057,794.90** — exact, reproduced through the actual served `POST /evaluation/begin` route this time (not just the lower-level calculators as in Phase 1)
- Verified live in the browser: Project Record → Analysis panel now reads "Leading structure: MU — production's current base", "Net production cost: $3,057,795"

## FVD canonical result — NEW, correcting the prior closeout

- **Budget used:** $4,517,687 (unchanged, real)
- **Base jurisdiction:** Greece, from its own budget filename (unchanged, real)
- **NEW canonical NPC: $3,072,027.16** (incentive $1,445,659.84) — **replaces** the `87440df` legacy-engine figure of $3,627,135.60, which is no longer served or displayed anywhere
- **Top result:** Greece's own baseline — same principle as Little Utopia: a real, honestly-priced full relocation to CA-NL/QA/SG shows a lower `npc_verified_usd` ($2,855,758.60) in the live response, correctly excluded from "winner" status by the same relocation-comparability guard

## Old FVD evaluation — invalidated

`Project.leading_structure_id` for FVD no longer points at any `87440df`-era (`run_full_analysis`, `engine_version` unset) structure. The repoint logic in `_summarize_evaluation` checks the *currently pointed-to* result's `engine_version` on every call and repoints whenever it isn't `canonical-1.0.0` — this is what performed the invalidation, verified live (`leading_structure_id` changed from `362ec163…` to `1b817c6f…` on the first canonical run). The four legacy rows are untouched in the database (provenance preserved, never destroyed) but are excluded from `get_project_record`'s `structures_available` count, which is now scoped to the current evaluation's own `input_fingerprint` (110, not the 114 that includes stale rows).

## Overlay / candidate-state / Abu Dhabi — what's real vs. what's blocked

**Genuinely fixed, both projects:** candidate accounting closes completely. Every candidate that reaches structure generation terminates in `PRICED` or `UNPRICEABLE_AUTHORITY_INSUFFICIENT` with its real discovery-derived reason — locked in by `test_unpriceable_candidates_are_accounted_for_not_dropped`. Live FVD response confirms AE-AD lands in `unpriceable` with the exact authority-insufficient reason, matching Little Utopia's own AE-AD classification from Phase 1 — the same correct backend behavior generalizes.

**Blocked — the served overlay/Workspace presentation itself.** Verified live at `/production/globe`: the Optimizer Overlay still renders Abu Dhabi and similar `UNPRICEABLE_AUTHORITY_INSUFFICIENT` structures as ordinary amber "Co-Production Opportunities" — visually identical to a genuinely priced opportunity. This is exactly the presentation defect Part J describes, and the backend truth needed to fix it (`is_fully_priced: false`, `excluded_from_ranking_because`) already exists in System A's own response — but making the frontend's `structureTier()`/`GLOBE_SEMANTIC` distinguish it is a Workspace-UI change, and Part T explicitly reserves that for a dedicated phase ("Do NOT redesign the Project Workspace yet... The new Script Summary page remains the NEXT product UI task after this passes" — a fifth semantic state is exactly this kind of redesign).

**Why a partial data cutover was ruled out, not just deferred.** `globeData.js::activeStructure()` cross-references `allocated.ranking`'s rank-1 `structure_id` against `allocated.structures`'s own id-keyed map. Pointing `ranking` at my canonical service's UUIDs while leaving `structures` sourced from `build_allocated_structures()` (different UUID scheme entirely) would make `byId.get(structure_id)` return `undefined` — the Workspace and Overlay would silently break for every user, not degrade gracefully. Confirmed by reading `globeData.js` in full before attempting anything, not assumed.

## Authoritative budget total

Preserved from Phase 1, verified again this phase for both projects: `BudgetDocument.total_budget_raw` (the document's own declared total) is the canonical gross, never the summed leaf lines. Little Utopia: $4,364,393 declared vs. $4,364,395 leaf sum (disclosed $2 variance, unchanged). FVD: $4,517,687, single source, no variance.

## MFNI limitation

Preserved and now layered: every priced result carries `mfni_limitation` (regional cost normalization not applied) **and**, for every non-baseline candidate, the additional `relocation_comparability_limitation` (relocation-specific travel/FX/in-kind costs not modeled). Neither MFNI nor travel/FX modeling was started this phase.

## Candidate accounting (both projects)

| | Examined | Incentive-ready (priced) | Capability-only (unpriceable) | Rejected (not generated) |
|---|---:|---:|---:|---:|
| Little Utopia | 213 | 30 | 80 | 103 |
| FVD | 213 | 30 | 80 | 103 |

No silent drops: every incentive-ready and capability-only candidate reaches a `ProductionStructure` row with a terminal `candidate_status`; rejected jurisdictions are accounted for via discovery's own metrics (unchanged from Phase 1's own established pattern), never materialized as misleading structures.

## Remaining canonical slug mismatches: 0 — obsolete by construction

Per Part O ("observe whether this problem still exists" before doing anything about it): it doesn't, for a structural reason rather than a fix applied to the old code path. The 26 mismatches in the prior FVD run came from `project_evaluation.py`/`structures.py` crossing from the in-memory discovery catalog (`jurisdiction_comparison.ALL_PROFILES`, `program_rate_rules.py`) into the *separate* DB-backed `incentive_programs`/`qualifying_spend_categories` tables, whose `slug` values aren't 1:1 with the catalog's.

`canonical_evaluation.py` never imports `app.models.incentive` (confirmed by grep) — `_price_candidate` resolves rate and doctrine directly against `program_rate_rules.resolve_program_rate` / `program_spend_rules` for the exact `program_slug` `discover_executable_jurisdictions` already validated, the same in-memory catalog both ends. There is no second registry to disagree with. Live evidence: FVD's `priced_count` is 30 — the *entire* `incentive_ready` set discovery found — with zero silently skipped. No remediation needed; no per-program patching performed.

## Tests

Eight new in `tests/test_canonical_evaluation.py`, all passing against the real, live Little Utopia and FVD projects:

1. `test_little_utopia_canonical_service_reproduces_exact_npc_and_winner`
2. `test_fvd_canonical_service_uses_real_budget_and_greece_baseline`
3. `test_project_leading_structure_points_at_the_canonical_engine`
4. `test_relocation_candidates_never_outrank_the_baseline`
5. `test_unpriceable_candidates_are_accounted_for_not_dropped`
6. `test_mfni_limitation_present_on_every_result`
7. `test_evaluation_route_no_longer_reaches_run_full_analysis`
8. `test_canonical_evaluation_module_reads_no_project_specific_data`

`tests/test_project_library_phase_c.py::test_production_structure_and_leading_selection` updated to reflect the real post-cutover state (was asserting exactly 1 structure and the migration-era NPC snapshot; now asserts >100 structures, the canonical `engine_version`, and the exact accepted NPC read from the *current* leading structure).

Full backend suite run (served economics runtime changed, warranting it): **4102 passed, 1 skipped, 1 pre-existing unrelated failure** (`test_global_discovery.py`'s `Workspace.jsx` formatter check — a frontend file untouched by this phase).

## Browser runtime acceptance

Both traced live, browser → network → backend → persistence → UI:

- **FVD:** Project Record loaded with the pre-cutover state, "Re-run Evaluation" clicked for real, `POST /evaluation/begin` fired and returned `engine_version: "canonical-1.0.0"`, page updated to $3,072,027 / GR baseline / 110 structures, full reload (`force: true`) preserved identical values.
- **Little Utopia:** Project Record confirmed the canonical repoint ($3,057,795 / MU / 110 structures). Served `/production/overview` confirmed unbroken and consistent ("Recommended Structure: Mauritius", "$3,057,795"). Served `/production/globe` confirmed unbroken; Abu Dhabi's amber "Co-Production Opportunities" rendering directly observed, confirming the presentation blocker described above is real, not theoretical.

## Files changed

- `app/services/canonical_evaluation.py` (new) — the canonical served engine
- `app/api/v1/evaluation.py` — routes to it instead of the legacy engine
- `app/api/v1/projects.py` — `structures_available` scoped to the current evaluation's fingerprint
- `tests/test_canonical_evaluation.py` (new), `tests/test_project_library_phase_c.py` (updated for the real post-cutover state)

## Gate detail

Met: canonical runtime built and served for both projects; Little Utopia exact winner/NPC through the real route; FVD re-evaluated with the legacy result invalidated; Project Record (both projects) reads the same response model; candidate accounting closes with no silent drops; MFNI (and the new relocation-comparability) limitation honestly shown; browser acceptance passed for both projects; tests pass.

Not met: the deep served `/production/*` Workspace and Optimizer Overlay still read System A directly rather than the canonical persisted rows, and the Abu Dhabi-type presentation defect (unpriceable shown with the same visual treatment as priced) is unfixed there — both correctly scoped out per Rule 1 / Part T, not abandoned.
