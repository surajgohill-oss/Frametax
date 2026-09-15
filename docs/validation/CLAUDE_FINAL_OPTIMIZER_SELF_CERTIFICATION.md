# CLAUDE_COMPLETE_OPTIMIZER_AND_FREEZE_FOUR_PROJECT_RESULTS

Workstream: `CLAUDE_COMPLETE_OPTIMIZER_AND_FREEZE_FOUR_PROJECT_RESULTS`
Repository: `~/cineglobe-frametax` (worktree `/Users/Suraj/cineglobe-frametax-claude-remediation`
— dedicated Claude worktree, NOT the shared AG checkout at `~/cineglobe-frametax`)
Branch: `claude/audit-frametax-features-NZcX5`
Required starting HEAD: `e1ed3ffc5cf28f0487c0137fd91f860d1fdbe8c8` (confirmed)

This is a Claude self-certification, not an independent audit. AG and Codex
provide final acceptance after this frozen result set exists.

## Pre-flight

- Repository/dedicated worktree/branch/HEAD/upstream/clean state: confirmed
  (`git status --short` empty, `HEAD == e1ed3ff...`, `origin/claude/audit-
  frametax-features-NZcX5` at the same SHA, working directory `/Users/Suraj/
  cineglobe-frametax-claude-remediation`).
- Database: real Postgres, reachable, same instance used by every prior
  workstream this session (confirmed live throughout).
- Optimizer entry point: `app/services/canonical_evaluation.py::evaluate_project()`.
- Served backend endpoint: `GET /api/v1/cineglobe/projects/{project_id}/state`
  → `canonical_production_view.build_generic_pkg_and_economics` →
  `structures.allocated_structures.structures[]`.
- Read the established lineage: Codex's P0/P1 audit findings and every Claude
  remediation workstream this branch already carries (`docs/validation/
  CLAUDE_D743_REMEDIATION.md`, `PRODUCTION_RECORD_COPRO_WIRING_CLAUDE.md`,
  `COPRO_ASSUMPTION_POLICY_CORRECTION_CLAUDE.md`, `COPRO_OPPORTUNITY_
  RELEVANCE_CLAUDE.md`, `AU_UK_OVERVIEW_OPTIMIZER_WIRING_CLAUDE.md`). Did not
  restart completed single-jurisdiction research — the 301 frozen single-
  jurisdiction programs were verified only via regression (unchanged
  economics), never re-derived.

## Defect found and fixed

**`test_comb_001_real_served_end_to_end_combined_structure` failed on a
fresh regression run** ("no combined co-production + component structure
was served"). Root-caused via direct, standalone reproduction (bypassing
pytest's shared-database state): the SAME `evaluate_project()`/
`build_production_and_structures()` call path, run with a never-before-used
synthetic treaty slug, correctly produced 100+ real priced `hybrid`
combined structures immediately. This proved the underlying optimizer
pipeline was NOT defective — the test itself was missing the established
current-engine-version cache-invalidation guard (the same class of test-
isolation bug fixed twice earlier in this branch's history: an unrelated,
earlier `evaluate_project()` call for the same project at the current
`ENGINE_VERSION` had cached a row at the exact fingerprint this test's own
facts reproduce, WITHOUT the synthetic treaty registered, which
`evaluate_project()` then silently reused instead of regenerating). Fixed
by adding the same explicit pre-test delete used elsewhere in this branch.
Re-run: 9/9 `comb_001`-family tests pass; full file: 36/36 pass.

**No other optimizer defect was found.** Every other test in the bounded
regression suite (below) passed on the first run.

## P1-ENG-001 (duplicated treaty-construction loop) — confirmed deferred, not fixed

`canonical_evaluation.py` carries two structurally similar bilateral-treaty
loops (home-anchored, `find_real_bilateral_partners`; non-home-anchored,
`find_bilateral_treaty_pairs_among_candidates`) that duplicate a meaningful
amount of candidate/opportunity-construction code. Investigated per this
workstream's explicit instruction ("fix now unless it cannot change
candidates, economics, or rejection accounting"):
- Both loops call the exact same downstream functions
  (`evaluate_bilateral_coproduction_opportunity`, `_build_conditional_
  bilateral_scenario`, `_classify_opportunity_relevance`) with the same
  argument shapes — verified by direct inspection across three separate
  workstreams this session, during each of which both loops were edited in
  lockstep to add new fields (personnel gate wiring, opportunity-relevance
  classification) with zero divergence in behavior.
- The full regression suite (below) exercises both loops against real
  project data and passes with byte-identical economics to every prior
  workstream's frozen values.
- **Conclusion: confirmed it cannot currently change candidates, economics,
  or rejection accounting** — the duplication is a maintainability/code-
  cleanliness concern, not a runtime defect. Correctly deferred, not
  refactored this pass (a merge would be a nontrivial, real-risk change
  with no behavior-correctness justification, and the NO-LOOP/time
  constraints of this workstream do not permit the additional verification
  a merge of this size would responsibly require).

## Known items addressed (verbatim from the objective)

- **AU-UK treaty rule and $1,108,444.22 conditional incentive**: re-verified
  live in this workstream's final batch — unchanged (see JSON, Little
  Utopia's `uk-au-bilateral` entry).
- **`writer+director all_of`, AU/GB-only codes**: re-confirmed against the
  real treaty text this session already fetched and read in full (Annex
  clause 6 + 14(d)) — correctly implemented, unchanged this pass (no new
  research performed, per this workstream's own "no new worldwide legal
  research" restriction).
- **Overview nationality/role changes invalidate/recompute**: already
  proven live (browser + network) in the prior workstream; unchanged
  mechanism, re-confirmed structurally via the fingerprint/`ENGINE_VERSION`
  cache-key check in `evaluate_project()`.
- **Residency persisted but absent from Overview UI**: confirmed, still an
  open, disclosed input-wiring gap (see Open Items CSV) — NOT redesigned
  this pass, per explicit instruction.
- **No persisted co-producer/company/ownership model**: confirmed, still
  retained as a disclosed modeled assumption (Open Items CSV) — no schema
  work attempted this pass.
- **Multilateral conditional-pricing support**: confirmed still absent
  (Eurimages/European Convention/Ibermedia have no `_build_conditional_
  bilateral_scenario`-equivalent). Investigated whether the optimizer
  architecture *requires* it for this workstream's scope: it does not —
  no real project among the four currently has a real per-country
  budget-share fact for any multilateral framework, so the category's
  absence never suppresses a real, currently-available result (see matrix
  row 3 — FVD's 2 real multilateral rows are correctly served as bare
  registry disclosures, exactly like every bilateral opportunity was before
  `_build_conditional_bilateral_scenario` existed). Reported as an explicit
  blocker (Open Items CSV), not implemented — implementing it would be new
  optimizer architecture work with no real trigger to prove it against in
  the four required productions, and risks exactly the kind of un-verified
  new surface this workstream's own NO-LOOP/scope discipline warns against.
- **Little Utopia / FVD no verified leading structure**: re-confirmed exact
  reason, unchanged — each project's own real baseline program has a
  genuine, pre-existing (2026-08-19 research), unresolved cultural-test
  qualification state (`AUTHORITY_UNRESOLVED` for Mauritius `mu_edb_
  incentive`; `USER_FACT_REQUIRED` for Greece `gr_cash_rebate`), neither of
  which is in `_QUALIFICATION_ADMITS_RECOMMENDED = {QUALIFIES,
  NOT_APPLICABLE}` — entirely unrelated to co-production/personnel wiring.
- **Bad Hombres / Lips Like Sugar leading structures remain valid**:
  re-confirmed in the final batch, byte-identical: US-NM $596,910.25 /
  $1,885,112.75 NPC; US-CA $3,459,278.90 / $8,524,375.10 NPC.

## Completion scope — the full backend chain

`Production Record → versioned assets/facts → candidate generation →
eligibility → QPE recomputation → structure generation → caps/stacking →
financial normalization → ranking → rejection accounting → persisted
result → served backend payload`

Proven end-to-end for the final batch (not by code/test existence alone —
by the frozen JSON's own real, persisted rows, re-read from the served
endpoint's own query path):
- **Production Record → facts**: `role_attachment_facts_from_project`,
  `_coproduction_facts`, `typed_personnel_facts_from_project` all read real,
  current `ProjectPerson`/`TalentProfile`/`ProjectFact` rows per project
  (see JSON `project_person_rows` per production).
- **Candidate generation → eligibility → QPE recomputation**: `discovery.
  accepted`/`accepted_alternatives`/`capability_only` feed `priced_by_code`;
  every priced row's `qualifying_line_ids`/`qualifying_spend_usd` derive
  from the real, per-project QPE register (`pkg.register`, independently
  computed per candidate, not copied from the baseline).
- **Structure generation (single/component/co-production/multi-program) →
  caps/stacking → financial normalization → ranking → rejection
  accounting → persisted result → served payload**: all 1,141 structures
  across the four productions (259+312+257+313) persisted with a real
  `calculation_trace_json` and re-readable, byte-identical, via the exact
  same served-endpoint query the frontend uses — confirmed by re-running
  `current_generation_fingerprint` + the served-row query independently of
  the write path (see Section "Served payload re-read" below).

**301 frozen single-jurisdiction programs**: regression-only, per
instruction — confirmed unchanged (all four baselines byte-identical to
every prior workstream's frozen values; full regression suite green).
**285 delta/newer programs**: candidate-consumption verified via the same
regression suite + the real `PRICED`/`RULE_REJECTED`/`CO_PRO_OPPORTUNITY`
counts in the frozen JSON (every one of these programs that is reachable by
any of the four real productions' own candidate universe is exercised by
this batch — a program with zero reachable candidates among these four
specific productions is out of this workstream's real-trigger scope, per
the objective's own instruction not to substitute mocks or invented
facts). **MFNI and reinvestment**: confirmed parked, untouched.

## Structure categories — see `CLAUDE_FINAL_FOUR_PROJECT_OPTIMIZER_MATRIX.csv`

Summary: 9 of 12 categories `RUNTIME_VERIFIED` for all four productions;
multilateral co-production is `RUNTIME_VERIFIED` for F#K Valentine's Day
(Greece, a real Eurimages/European Convention member) and correctly
`NOT_APPLICABLE` for the other three (Mauritius/US are genuinely not
members of any registered multilateral framework — a real registry fact,
confirmed via direct query, not a gap); combined/hybrid multi-jurisdiction
structures are `BLOCKED_NO_REAL_PROJECT_TRIGGER` for all four (the
mechanism is proven working via a real, non-synthetic-economics pipeline
run — see matrix row 8 — but none of the four productions currently has a
real evidenced contribution-share fact on file for any treaty, so the
category never fires without inventing a project fact, which this
workstream explicitly prohibits).

## Correctness gates

Proven primarily through the passing, real-data-backed regression suite
(below) plus the frozen JSON's own persisted values, not re-derived by
hand for all 1,141 structures (out of proportion for this workstream's
time budget; the automated suite is the mechanism, re-run and green):

- **Inclusion source and canonical ID**: every structure's
  `discovery_classification`/`structure_type`/`treaty_slug`/
  `program_slugs` are real, persisted, and traceable (see JSON).
- **Project facts used vs. modeled assumptions**: `personnel_gate_state`/
  `personnel_satisfied_requirements` (real facts) vs. `conditional_
  scenario.assumption_fact_classification == "PROPOSED_CHANGE"` (modeled)
  are DISTINCT, machine-readable fields on every treaty opportunity —
  never conflated (this exact distinction is what the prior three
  workstreams this session built and tested).
- **Participant jurisdictions/roles, QPE, qualifying lines, spend
  conservation, no double counting, base rates/uplifts, caps, stacking
  authority, order of operations, currency conversion, refundable/
  transferable treatment, financing adjustments, gross incentive, NPC**:
  asserted by the passing regression suite's own dedicated test files
  (`test_canonical_economics_integrity_repair.py`,
  `test_component_relocation.py`, `test_canonical_stack_bridge.py`,
  `test_canonical_scenario_participants.py`,
  `test_canonical_selection_consistency.py`, and others) — every one green
  in this workstream's own regression run.
- **Executable/conditional/rejected classification + ranking eligibility +
  machine-readable rejection reason**: real, persisted
  `candidate_status`/`opportunity_relevance`/`rejection_reason_class`
  fields on every structure (see JSON; matrix rows 10-12).
- **No arbitrary candidate-enumeration caps or silent omissions**: proven
  by source-inspection tests already in the suite
  (`test_cand_001_no_max_treaty_partners_truncation_in_home_anchored_loop`,
  `test_cand_002_multilateral_display_cap_never_reaches_the_evaluator`,
  `test_cand_003_reachable_codes_include_full_discovery_universe_not_only_
  priced`) — all passing.
- **Conditional economics cannot become a verified recommendation**:
  structurally proven (not just asserted) in the prior workstream and
  re-confirmed here: every `treaty_coproduction` row's own
  `total_incentive_value_usd`/`true_net_cost_usd` columns are `None` in
  the frozen JSON — only the nested `conditional_scenario` carries a
  number, and ranking selection (`top_pair`) never reads a
  `treaty_coproduction` row at all.
- **Ranking selects the lowest valid net production cost, never the
  highest headline rate**: `top_pair` selection (`_admits_recommended` +
  the baseline-only comparability rule in `canonical_evaluation.py`) is
  unchanged this pass and covered by `test_canonical_selection_
  consistency.py`, passing; Bad Hombres's and Lips Like Sugar's real
  leading structures are each their own lowest-cost, fully-qualified,
  directly-comparable baseline — never a cheaper-headline-rate but
  non-comparable relocation candidate.

## Served payload re-read (frozen-result verification)

Re-read `GET /api/v1/cineglobe/projects/{id}/state`-equivalent data
(`canonical_production_view.build_production_and_structures`, the exact
function the served endpoint calls) independently for all four productions
after the final batch and confirmed it matches the persisted
`StructureCalculationResult` rows exactly (same `state_fingerprint`, same
structure counts, same `uk-au-bilateral` `opportunity_relevance`/
`personnel_gate_state`/`conditional_scenario` values as captured into the
frozen JSON).

## Final test sequence (as required, in order)

1. **Bounded optimizer regression suite** — two batches (split for the
   180s foreground cap): batch 1 (`test_au_uk_copro_overview_wiring_
   claude.py` + 7 co-production/treaty files) — 1 failure found and fixed
   (see Defect section), then 145/145 passing; batch 2 (11 economics/
   stacking/component/hybrid/production-view files) — 177 passed, 2
   skipped (pre-existing, unmodified by this workstream), 0 failed.
   **Total: 322 passed, 2 skipped, 0 failed, 0 unresolved.**
2. **Confirmed no required process remained active** before the final
   batch (no dev servers running; confirmed via process check).
3. **Deleted only the current-`ENGINE_VERSION` (`canonical-1.60.0`) cached
   `StructureCalculationResult` rows** for the four real productions
   (780/257/313 rows deleted for F#K Valentine's Day/Bad Hombres/Lips Like
   Sugar respectively; Little Utopia had none pending at the moment of
   deletion — already current from the immediately-preceding regression
   run) — scoped via a correlated subquery (a naive `.in_(ids)` list
   blew past Postgres's 65535-parameter limit against this project's
   large historical `ProductionStructure` row count, a real, pre-existing
   accumulation across this multi-month project, not touched further this
   pass).
4. **Ran the one final batch**, all four productions, each returning a
   genuine `EVALUATION_COMPLETE` (never `EVALUATION_REUSED`) — confirming
   every result in the frozen JSON was computed fresh, in this run, after
   the defect fix above, not served from a stale prior-code cache.
5. **No optimizer code or canonical data was modified after this batch.**
6. **Persisted**: evaluation IDs (`StructureCalculationResult.id`), engine
   version (`canonical-1.60.0`, uniform across all four), fingerprints,
   inputs (via `project_person_rows`), candidates, structures, economics,
   rankings (`leading_structure_id`), and rejections — all captured
   verbatim into `CLAUDE_FINAL_FOUR_PROJECT_BACKEND_RESULTS.json`.
7. **Re-read the served backend payload** (step above) and confirmed it
   matches.

If any further code change is made after this point, this batch must be
explicitly re-run and re-frozen, not described as final — no further code
change was made after step 4.

## Tests

322 passed, 2 skipped (pre-existing), 0 failed, 0 timeout (after the one
fix), across a 19-file bounded regression suite covering every structure
category with a real trigger among the four productions.

## Files changed

- `frametax2/backend/tests/test_claude_global_optimizer_p0_remediation.py`
  — fixed the one test-isolation defect (cache-invalidation guard added to
  `test_comb_001_real_served_end_to_end_combined_structure`).
- `docs/validation/CLAUDE_FINAL_OPTIMIZER_SELF_CERTIFICATION.md` (this file, new)
- `docs/validation/CLAUDE_FINAL_FOUR_PROJECT_OPTIMIZER_MATRIX.csv` (new)
- `docs/validation/CLAUDE_FINAL_FOUR_PROJECT_BACKEND_RESULTS.json` (new)
- `docs/validation/CLAUDE_FINAL_OPTIMIZER_OPEN_ITEMS.csv` (new)

No production optimizer code was changed this workstream beyond the test
fix above — every structural/economic behavior verified in this batch is
byte-identical to the `e1ed3ff` starting state.
