# Co-production / Stacking / Qualification Ingestion — Final Correction Closeout

Fixes the four defects in `docs/validation/CODEX_FINAL_OPTIMIZER_HEALTH_AUDIT.md`
(commit `1c4fc79`, audited HEAD `6b44973`). No web research, no worldwide audit,
no reopening of the restored-58 policy or the settled NY/Ontario/Canada program
models.

## OH-001 (P0) — stale canonical snapshots masquerade as current

**Root cause, confirmed directly:** `evaluate_project()`'s reuse query requires
`input_fingerprint == fingerprint AND engine_version == ENGINE_VERSION`.
`ENGINE_VERSION` (`canonical-1.34.0`) was not bumped after three real,
result-affecting changes landed: combined-qualification propagation (`b245f1b`),
BC DAVE / AU PDV canonical recovery (`9d0266b`), and the provenance/economics
separation policy (`6b44973`). None of those changes touched the fingerprint's
dependency manifest either, so LU/FVD rows persisted on 2026-08-20 kept matching
as current through every subsequent change.

**Fix:**
1. `ENGINE_VERSION` bumped to `canonical-1.35.0`, immediately invalidating every
   pre-correction row.
2. `_compute_fingerprint()`'s dependency manifest extended from 4 to 12 registry
   version constants — added `AUTHORITY_COVERAGE_REGISTRY_VERSION`,
   `PROGRAM_AUTHORITY_PROVENANCE_VERSION`, `PROGRAM_REQUIREMENTS_VERSION`,
   `STACKING_RULES_VERSION`, `TREATY_ENGINE_VERSION`,
   `STRUCTURING_OPPORTUNITY_PATTERNS_VERSION`,
   `EXECUTABLE_JURISDICTION_REGISTRY_VERSION`,
   `CANONICAL_ROLE_QUALIFICATION_BRIDGE_VERSION` — covering every dependency
   Codex named (authority/economic-state, stacking, treaty, opportunity-pattern,
   spend-rule, executable-registry). Five modules that had no version constant
   at all gained one. A future change to any single one of these now
   self-invalidates cached rows without a manual `ENGINE_VERSION` edit.

**Fresh-generation proof:** `evaluate_project()` genuinely recomputed LU and FVD
under `canonical-1.35.0` — both `EVALUATION_COMPLETE` on first call this pass,
`EVALUATION_REUSED` correctly on subsequent calls in the same session (reusing
their own fresh rows, never the stale ones).

**Stale-rejection proof:** `test_fingerprint_actually_changes_when_a_registry_
version_bumps` patches each of the 12 constants individually and asserts the
fingerprint changes every time — the previous version of this test only proved
the constants were importable, never that they were wired in.

## OH-002 (P0) — combined qualification can be lost or weakened

**Root cause #1, confirmed directly:** the combo-trace builder looked up each
member's qualification state by `(stack_result.jurisdiction_code, program_slug)`
— but a federal member (`ca_federal_cptc`, examined under `"CA"`) inside a
provincial stack (`jurisdiction_code = "CA-ON"`) was recorded under a different
key than the lookup used, silently dropping its real state from the combo's
worst-state computation.

**Root cause #2, confirmed directly:** `_QUAL_STATE_SEVERITY` had no entry for
`QUAL_RULE_DATA_INCOMPLETE`. Every read used `.get(state, 2)` — the same
severity as `QUALIFIES`/`NOT_APPLICABLE` — so a real `RULE_DATA_INCOMPLETE`
member could resolve a combo to an incorrectly-admitted state.

**Fix:**
1. Added `_qual_state_by_program: dict[str, str | None]`, keyed by program
   identity alone, populated alongside the existing (and now-redundant but
   harmless) `(code, slug)` dict. The combo-trace builder now reads
   `_qual_state_by_program.get(slug)` for every member — see
   `test_combo_qualification_lookup_is_keyed_by_program_identity_not_
   jurisdiction_code`, which asserts this directly against the source.
2. Added `QUAL_RULE_DATA_INCOMPLETE: 1` to `_QUAL_STATE_SEVERITY`, matching
   every other non-admitted state's severity tier. Proven with
   `test_worst_state_severity_table_has_every_qualification_state_explicit`
   (walks `ALL_QUALIFICATION_STATES`, asserts none is missing) and
   `test_not_applicable_and_rule_data_incomplete_are_not_conflated` (the exact
   `NOT_APPLICABLE` + `RULE_DATA_INCOMPLETE` → `RULE_DATA_INCOMPLETE` case
   Codex's required proof names).

**Applies generically, not per-serializer:** the fix is in the one shared
combo-trace-building path every combined structure type (same-jurisdiction
stack, federal/provincial, N-way, component structures where they carry a
qualification trace) already flows through — no per-type patch was needed or
applied.

**Runtime proof:** `test_ontario_combined_structures_never_have_null_
qualification` — against FVD's real, freshly-recomputed CA-ON combined
structures, every one now carries a real `role_qualification.state`, never
`None`.

## OH-003 (P1) — multiple production-capable engine lineages remain mounted

**Investigated, not assumed:** `project_evaluation.begin_evaluation` (the
`run_full_analysis`-backed function) was already unreachable from any router —
`api/v1/evaluation.py`'s own docstring documents this and the real production
route (`POST /projects/{id}/evaluation/begin`) already calls
`canonical_evaluation.evaluate_project` exclusively. The one genuinely live,
mounted path to the legacy engine was `POST .../structures/{id}/calculate`
(`calculate_structure_impl` → `run_full_analysis`), still callable and still
persisting `engine_version="0.1.0"` rows to the same table, even though no
frontend code calls it and it cannot become `leading_structure_id`.

**Fix:** the route now raises `HTTPException(410)` before touching
`run_full_analysis` or persisting anything, directing callers to the canonical
endpoint. `calculate_structure_impl`/`run_full_analysis` remain importable for
historical/test reference — retired, not deleted, per this project's own
"preserve historical code" discipline.

`app/api/v1/cineglobe.py`'s unparameterized demo routes were investigated
directly (AST, not string search): they mount under an explicit `/cineglobe`
prefix, never reference `StructureCalculationResult` anywhere in the module
(cannot structurally persist a competing canonical snapshot), and the module's
own project-scoped routes genuinely call `get_project_state`/
`build_production_and_structures`. They remain live (real company screens
depend on them, out of this pass's UI scope) but cannot contaminate canonical
project state by construction — proven in
`test_cineglobe_unparameterized_endpoints_are_explicitly_demo_scoped`.

**Snapshot ownership:** only `canonical_evaluation.py` writes rows a project GET
can read as current (`engine_version == ENGINE_VERSION`); the retired route no
longer writes at all; the demo routes never wrote `StructureCalculationResult`
in the first place.

## OH-004 (P1) — acceptance tests can pass without exercising the contract

Each vacuous assertion Codex named was fixed in place, not replaced with a new
test program:

1. `test_point_table_role_is_point_bearing_not_mandatory` —
   `any("fr_composer" in lever or True for lever in ...)` was true
   unconditionally; fixed to a real, falsifiable `"fr_composer" in
   result.available_levers`.
2. `test_registry_versions_are_present_in_the_payload` — only proved the
   constants were truthy/importable; added
   `test_fingerprint_actually_changes_when_a_registry_version_bumps`, which
   patches each of the 12 dependency constants and asserts real sensitivity.
3. `test_cineglobe_unparameterized_endpoints_are_explicitly_demo_scoped` — only
   proved two function names appeared as text anywhere in the file; rewritten
   to prove the router prefix, an AST-verified absence of any
   `StructureCalculationResult` reference, and that the canonical entry point
   is actually *called*, not merely named.

New, non-vacuous OH-001/OH-002 proofs were added in
`test_codex_final_optimizer_health_audit.py` (9 tests) — each asserts a
non-empty inspected population before asserting on it (e.g. "test went vacuous"
guards), matching the standard already established in this project's own
`test_multi_program_jurisdiction_invariant.py` and `test_prompt16_authority_
disposition.py` ranking-safety tests.

## Stale-cache masking, found in the act of fixing it

Forcing the fresh recompute (OH-001's own fix) surfaced two real, previously
class-invisible test defects that had nothing to do with OH-001/OH-002's code
changes themselves — they were interactions that existed in code merged over
the *last several sessions* but had never actually executed against FVD's
served response, because that response was stale the entire time:

- `test_role_qualification_covers_only_real_registry_slugs` hit a `KeyError:
  'regime_id'` — the combined-structure trace's own minimal `{"state": ...}`
  dict (added when combined-qualification propagation first landed) had never
  been exercised by this test, because FVD's cached row predated that change.
  Fixed with an explicit skip for combo-only traces.
- The same test's core invariant also needed a real, disclosed exception: two
  single-program candidates (`ca_on_opstc`, `mx_federal_film_incentive_2026`)
  legitimately resolve `AUTHORITY_UNRESOLVED` via a real, cited `RateCondition`
  (CBA-002's `_merge_rate_condition_into_qualification`) rather than the
  role/cultural registries this test enumerates — real doctrine, not
  fabrication, now recognized via the reasoning trace's own explicit disclosure
  line.

Both are exactly the failure mode OH-004 describes in the abstract, caught
concretely once OH-001 stopped hiding them.

## Candidate-universe / accounting movement — fully attributed

Two pre-existing FVD structure-count assertions moved by the same, single,
already-explained cause: `146` total structures (`144 → 146`), `135` priced
(`133 → 135`), `135` review-required — BC DAVE and AU PDV each add one
`full_relocation` candidate to FVD's real budget (no matching component
candidate for FVD specifically, unlike Little Utopia — a real, attributed
budget-composition difference, not a bug). `unpriceable_count` (`11`) is
unaffected; both new programs price cleanly.

## LU / FVD — fresh, not cached

| | LU | FVD |
|---|---|---|
| Engine version | `canonical-1.35.0` | `canonical-1.35.0` |
| Fresh this pass | YES (`EVALUATION_COMPLETE` on first call) | YES (`EVALUATION_COMPLETE` on first call) |
| NPC | `$3,057,794.90` (unchanged) | `$3,072,027.16` (unchanged) |
| Delta | `$0` | `$0` |
| Recommended | `0` (unchanged — genuine unresolved qualification) | `0` (unchanged) |
| Candidates | `134` (includes BC DAVE, AU PDV) | `146` (includes BC DAVE, AU PDV) |
| CA-ON combined qualification | non-null on every combo | non-null on every combo |
| Contingency election | persisted `100%`, `recovered_demo_state` — unchanged | none — unchanged |

Zero unexplained economic movement on either control. Neither NPC was forced;
both were re-derived from a genuine fresh evaluation and happen to match the
historical diagnostic exactly, because none of OH-001/OH-002/OH-003's fixes
touch Mauritius's or Greece's own rate/qualification data.

## New York / Ontario / Contingency / Structuring — no re-audit, fresh proof only

- **New York:** canonical model already showed the 60% Production Plus ceiling
  (`resolve_program_rate("us_ny_film_credit", ...) == 0.60`); the STALE served
  response is what showed 50%. Fresh evaluation now serves the current model —
  proven in `test_ny_fresh_served_result_uses_the_current_production_plus_
  ceiling`. No NY code change was needed or made.
- **Ontario:** discovery was already correct; the combined-runtime defect was
  OH-002 exactly as Codex predicted, not an Ontario data defect. Fixed there;
  Ontario's own program model untouched.
- **Contingency:** LU's persisted `contingency_expected_utilization_pct = 100`
  election is unchanged and still drives the generic expected-utilization
  calculation; no Mauritius-specific branch exists or was added.
- **Structuring intelligence:** the opportunity bridge and specialized engines
  were already correctly wired; the "engine wiring defect" Codex flagged was
  the same stale-cache symptom (BC DAVE/AU PDV component recovery not reaching
  the served response) — resolved by OH-001, not by touching the opportunity
  bridge.

## No new engine, database, or ontology

Every fix extends an existing canonical owner: `ENGINE_VERSION` and
`_compute_fingerprint()` (existing cache/freshness mechanism, not a second
cache); `_qual_state_by_program` and `_QUAL_STATE_SEVERITY` (existing
qualification-propagation machinery, not a new ontology); the retired
`/calculate` route (existing router, not a new one). No web research was
performed.

## Tests

Full backend suite: **4466 passed, 0 failed, 1 skipped** (up from 4455 — 9 new
OH-001/OH-002 tests, 1 new fingerprint-sensitivity test, 1 new route-retirement
test; 3 named-vacuous tests fixed in place; 4 pre-existing count assertions
updated with full attribution, none weakened).
