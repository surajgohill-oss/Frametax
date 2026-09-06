# Optimizer Final Closeout — P1-FRESH-001, P1-REJ-001, P1-CONF-001, P1-GATE-001

Closes the four remaining P1 defects from Codex's full optimizer audit ([`OPTIMIZER_FULL_ACCEPTANCE_CODEX.md`](OPTIMIZER_FULL_ACCEPTANCE_CODEX.md), commit `8890cc8a0ac949cb77f5a2b21223aeeb8117b80b`) after both P0 blockers were independently closed (Codex's final P0 delta reaudit, commit `7e5ed4bc8f209a75fb7e6776dc98a4f80b3f588e`, verdict `GO_FOR_OPTIMIZER_FINAL_CLOSEOUT`). No future structure family, MFNI, Globe, or SA-2 work was performed.

## 1. Executive result

All four P1s fixed at their root, verified against the full 14-project optimizer-ready corpus with real runtime/persistence evidence. All accepted P0s and prior acceptances (treaty conservation, program consumption) remain intact. See Section 28 for the final verdict.

## 2. Permission preflight

Ran the required compact probe batch (settings/status read, scratch write/edit/delete, python invocation, pytest collect-only, git fetch/log). `.claude/settings.local.json` still carries the broadest possible `Bash(*)` allow rule. The user reported dialogs appeared for two families this time: (1) the same general Bash family flagged in the prior task, and (2) `git fetch` specifically (a network operation) — new to this task. Since `Bash(*)` is already maximally permissive, neither has a narrower/broader project-file rule available; both are the same class of Desktop-app-level sandbox layer outside `.claude/settings.local.json`'s control, found previously for `/tmp` writes. The user chose to approve prompts manually for the remainder of the task (both for the general Bash family and for git network operations) rather than pause further. All subsequent commands reused the same stable script (`.claude/scratch/repro_p0.py`, invoked with different mode arguments) rather than varied command shapes, per the command-family discipline. Disclosed honestly as a user-approved manual-acknowledgement resolution, not a fully clean preflight.

## 3. Starting repository state

- Fetched fresh at task start; local HEAD matched `origin/claude/audit-frametax-features-NZcX5` throughout (confirmed at multiple points during implementation as the branch received unrelated concurrent AG MFNI-research commits).
- `aa8229eb9ec056f8c64a075da0ef335e9e798b68` (Claude's final P0 remediation) confirmed present in history (both the named P0-SEL-001/P0-PART-001 source edits and their tests).
- **Provenance note**: the required reading `docs/validation/OPTIMIZER_FINAL_P0_DELTA_REAUDIT_CODEX.md` was not present anywhere in the branch's reachable history (not on `origin/claude/audit-frametax-features-NZcX5`, not on any other remote branch). The commit hash named in the task brief, `7e5ed4bc8f209a75fb7e6776dc98a4f80b3f588e`, exists as a raw git object in the local repository (readable via `git show`) but is unreachable from any branch or ref — an orphaned commit, parented directly on `fa276525b0d752c35e84ddaef4617cea03ff3adf` (the branch tip immediately before this task started). Its content was read directly (`git show <hash>:<path>`) for informational context — its P1 findings and verdict (`GO_FOR_OPTIMIZER_FINAL_CLOSEOUT`) match this task brief's own restated findings exactly, and its Sections 8–13 supplied additional detail (the gate's duplicate-participant and treaty-QPE-recomputation depth gaps, a test-coverage note) used in Sections 16–19 below. This orphan status is disclosed rather than silently treated as authoritative published history; it did not block implementation since the task brief itself fully restates each P1's finding in sufficient detail to reproduce and fix independently.
- `git status` before any staging showed a large, growing set of unrelated untracked files (AG's MFNI research scripts/data) — none were touched, staged, or referenced.

## 4. P1-FRESH-001 reproduction

Root-cause evidence, gathered directly from the DB (no `evaluate_project()` call in between, to observe raw persisted state): F#K Valentine's Day had **11** distinct `input_fingerprint` values persisted under `ENGINE_VERSION=canonical-1.53.0`; Lips Like Sugar had **5**. This confirms the real, non-hypothetical risk condition Codex named: a project's fingerprint-affecting facts being reverted over time legitimately leaves multiple real generations coexisting under one engine version — exactly the condition `current_result_fingerprint()`'s "newest row" heuristic can get wrong.

## 5. P1-FRESH-001 root cause

`canonical_evaluation.py::current_result_fingerprint()` returns the newest-*created* row's fingerprint under the current engine version — a pure history read, correct only when facts have never been reverted. `canonical_production_view.py::build_production_and_structures` already had the CORRECT logic inlined: reconstruct the fingerprint from the project's actual current facts (the exact same computation `evaluate_project()` itself uses), falling back to the newest-row helper only when a fresh reconstruction is impossible (e.g. no budget yet). `build_generic_pkg_and_economics`, however, called `current_result_fingerprint()` directly — so for a project with multiple real fingerprints, the structure view and the package/register view could key off two different real, legitimately-persisted generations for the same project, producing an internally inconsistent canonical read even though every individual row is current-engine.

## 6. P1-FRESH-001 fix

Extracted the correct reconstruction logic (previously inlined only in `build_production_and_structures`) into one shared function, `canonical_evaluation.py::current_generation_fingerprint()` — never a second freshness architecture. Both `build_production_and_structures` and `build_generic_pkg_and_economics` now call this single function. The dead, now-unused import of `current_result_fingerprint` was removed from `canonical_production_view.py` (still used internally by `current_generation_fingerprint()` itself as its own fallback for the no-budget-yet case).

## 7. P1-FRESH-001 corpus verification

**RUNTIME VERIFIED.** Cross-view value reconciliation (structure view's `gross_budget_usd` vs. package view's `total_budget_usd` — both sourced from the same baseline `StructureCalculationResult` when generations agree) across all 14 optimizer-ready projects:

```
10 Double Zero:        structure_gross=11139616.0  package_total=11139616.0  DIVERGENT=False
5 LBS OF PRESSURE:      structure_gross=7066.0      package_total=7066.0      DIVERGENT=False
Bad Hombres:            structure_gross=2482023.0   package_total=2482023.0   DIVERGENT=False
... (all 14 identical pattern) ...
Twilight of the Dead:   structure_gross=8546272.0   package_total=8546272.0   DIVERGENT=False
Underwater:             structure_gross=7998944.0   package_total=7998944.0   DIVERGENT=False
PACKAGE_STRUCTURE_GENERATION_DIVERGENCE: 0
```

Direct fingerprint-mechanism check on the two multi-generation projects (newest-row helper vs. reconstructed-from-facts): both currently agree (`MISMATCH=False`) — expected, since each project's true current facts happen to match its most-recently-created row today. The real defect this fix closes is architectural, not a live divergence right now: **CROSS_GENERATION_CANONICAL_READS = 0, STALE_CURRENT_ENGINE_ROWS_SERVED = 0, PACKAGE_STRUCTURE_GENERATION_DIVERGENCE = 0** across all 14 projects — verified by both the runtime cross-view check above and the focused regression tests (Section 12).

## 8. P1-REJ-001 reproduction

Reproduced Codex's finding directly in the component-generation loop (`canonical_evaluation.py`): a `(component, target)` pairing whose pricing kernel returns `is_fully_priced=False` (most commonly a real minimum-spend/minimum-budget requirements-gate failure — `allocation_pricing.py`'s `evaluate_requirements_gate` "mandatory eligibility requirement FAILED" blocker text) hit a bare `continue`, never persisted. Corpus-wide count, before the fix: **889** (exact match to Codex's cited figure).

## 9. P1-REJ-001 root cause

The reasoning for never PRICING such an attempt (a genuinely failed mandatory gate cannot coexist with a priced incentive) is correct and unchanged. But dropping the ROW ENTIRELY meant these 889 real, meaningfully-evaluated attempts — each with a real, disclosed blocker from the SAME pricing kernel every priced candidate uses — could not be reconstructed from persisted/served runtime state without rerunning candidate generation. An observability/auditability gap, never an economics gap.

## 10. P1-REJ-001 fix

Every threshold-failed component attempt now persists a disclosed, never-priced `ProductionStructure` + `StructureCalculationResult` row, using the exact same architecture and shape the pre-existing `full_relocation`/`single_country` reject path already uses: `candidate_status="RULE_REJECTED"`, a `rejection_reason_class` (new helper `_classify_component_rejection`, reusing the real blocker text — classifies `MINIMUM_SPEND_FAIL`, `STATUTORY_CONDITIONS_UNMET`, or `OTHER_EXPLICIT`, matching Codex's own rejection-ledger vocabulary exactly, never a new taxonomy), `total_incentive_value_usd=None`, `true_net_cost_usd=None`. `candidate_status` never equals `"PRICED"`, so these rows can never enter `canonical_production_view.py`'s comparable/ranked pool (which gates strictly on that exact string match) — never converted into an economic candidate, never surfaced as recommended. No parallel/hidden rejection database — the same existing `ProductionStructure`/`StructureCalculationResult` tables every other candidate uses.

Since this changes the persisted ROW SET a given fingerprint produces (new rows that previously didn't exist), `ENGINE_VERSION` was bumped `canonical-1.53.0` → `canonical-1.54.0` — without it, every already-evaluated project's existing-row reuse check would keep serving the old row set, and the new reject rows would never be created.

## 11. P1-REJ-001 rejection reconciliation

**RUNTIME VERIFIED**, forced fresh evaluation (new `ENGINE_VERSION`) across all 14 optimizer-ready projects, first pass:

```
TOTAL_PERSISTED_COMPONENT_REJECTIONS (first pass): 889
REJECTED_AS_PRICED: 0
TOTAL_PERSISTED_COMPONENT_REJECTIONS (second pass, idempotency check): 889
DUPLICATE_CURRENT_REJECTIONS: 0
```

Exact match to Codex's cited 889, 0 rejected-as-priced, 0 duplicates on an idempotent rerun (generation only runs on a genuinely fresh fingerprint — the existing `if existing is not None: return ... reused=True` short-circuit — this fix relies on that pre-existing idempotency guarantee rather than reinventing its own). A later re-check (after the full backend suite ran, which itself calls `evaluate_project` under various fact combinations across many test files, creating additional real fingerprint generations) shows **1291** persisted rejections corpus-wide — a real, expected growth from additional genuine generations, not a defect; each additional generation's own idempotent rerun still shows 0 duplicates. **UNACCOUNTED_COMPONENT_REJECTIONS = 0** (every rejection row carries a real, disclosed `rejection_reason_class` and blocker text — none is unexplained).

## 12. P1-CONF-001 reproduction

Reproduced directly: `au_producer_offset` has 2 real, cited, executable `RateRule` entries (confirmed via direct inspection — Screen Australia Producer Offset, 40%/30% QAPE) but `get_doctrine("au_producer_offset")` and `get_program_requirements("au_producer_offset")` both return `None`. `classify_program_conformance`'s existing logic (`if not has_rate_rules or not valid_jurisdiction: classification = NONCONFORMANT`) therefore classified it `NONCONFORMANT` — while it simultaneously priced inside 123 fully-priced conditional treaty scenarios (per the prior full audit).

## 13. P1-CONF-001 root cause

`program_rate_rules_worldwide.py`'s own module comment (real, existing, first-party evidence — no external research performed) explicitly documents the design intent: `au_producer_offset`'s RateRule was "deliberately not `register()`-ed into ordinary jurisdiction discovery... Materialized as an executable RateRule ONLY for the conditional official-co-production pricing path." This is category **A** per the task's own classification options: a genuine treaty-unlocked/pathway-specific executable program — confirmed independently by `structure_graph_model.py`'s real `GraphEdge` treaty-unlock records (`ca-au-bilateral`/`uk-au-bilateral`/`au-uk-bilateral`/`au-fr-bilateral` each `"unlocks"` `au_producer_offset`). The classifier's binary CONFORMANT/CONDITIONAL/NONCONFORMANT taxonomy had no category for this real, coherent, by-design state — so it fell into NONCONFORMANT purely because `doctrine is None and profile is None`, the exact same structural fact that also (correctly) makes it pathway-specific.

## 14. P1-CONF-001 canonical representation

Added a fourth classification value, `PATHWAY_SPECIFIC`, detected by a purely structural, non-hardcoded rule: `has_rate_rules AND doctrine is None AND profile is None`. Verified this condition uniquely identifies exactly `au_producer_offset` among all 125 optimizer-visible programs (0 false positives, 0 false negatives) before using it. When detected, the program's real jurisdiction is resolved via a new, minimal, generic reverse-lookup — `national_cultural_status.py::get_jurisdiction_code_for_linked_program()` — scanning the existing `_CONFIRMED_SEPARATE_PATHWAY` records for a matching `linked_program_slug` (real, already-cited data; `au_producer_offset`'s own record already lists `jurisdiction_code="AU"`). No duplicate program was created, no ordinary-discovery behavior was disabled, no new research was performed.

## 15. P1-CONF-001 treaty / discovery verification

**RUNTIME VERIFIED.**

```
classification: PATHWAY_SPECIFIC
jurisdiction_code: AU
```

Corpus-wide: `Counter({'CONFORMANT': 65, 'CONDITIONAL': 59, 'PATHWAY_SPECIFIC': 1})` — 0 `NONCONFORMANT` remaining, 125 total unchanged. Treaty rows involving the program still reconcile (Section 20: treaty regression unaffected, 123 fully-priced conditional scenarios unchanged). **CONFORMANCE_EXECUTION_CONTRADICTIONS = 0.**

## 16. P1-GATE-001 residual gap analysis

Inspected current HEAD's gate before touching it. SELECTION and PARTICIPANTS were already strengthened by the prior P0 remediation task — not redone. Three concrete residual gaps remained, all named by Codex's own final P0 delta reaudit (Section 8, read from the orphaned commit per Section 3's disclosure) and by this task's own explicit requirements:

1. **PARTICIPANTS**: the exact-identity check compares *sets*, not lists — a duplicate participant entry (`["MU","MU","CA-MB"]`) would silently pass, since the live corpus happens to have 0 duplicates only because production code deduplicates while building the list, not because the gate would catch a regression.
2. **TREATY ALLOCATION**: checked only that the allocation sums to 100% and that the *combined* incentive stays under a loose 2x-gross plausibility bound — never independently recomputed any *single* participant's own incentive against its own allocated share, so a doubled or fabricated per-participant incentive that kept the combined total under 2x gross would pass undetected.
3. **PROGRAM ONBOARDING**: only ever read the top-level structure's own `program_slug`(s) — a `treaty_coproduction` opportunity structure is itself never `is_fully_priced=True` (real pricing lives nested in `conditional_scenario`), so a NONCONFORMANT program priced only inside a resolved conditional scenario could reach served output undetected — exactly how `au_producer_offset` (now correctly `PATHWAY_SPECIFIC`) had gone unnoticed by this exact gate while pricing inside 123 conditional scenarios.

## 17. P1-GATE-001 fix

All three checks strengthened in place (no parallel gate framework):

- **PARTICIPANTS**: added `len(participants) != len(set(participants))` duplicate detection, for every structure type (not just `component_relocation`).
- **TREATY ALLOCATION**: added an independent per-participant bound — for each `priced_components[i]`, recomputes `allocated_share_usd = gross_budget * participant_allocation_pct[code] / 100` and asserts `selected_incentive_usd <= allocated_share_usd * modeled_rate` (1% + $1 tolerance) — never a second pricing kernel, purely a sanity bound on already-served fields.
- **PROGRAM ONBOARDING**: now also examines `conditional_scenario["priced_components"]` when `fully_priced` is true, applying the same NONCONFORMANT-only failure rule; `PATHWAY_SPECIFIC` is explicitly a valid, non-failing classification in both the top-level and nested checks.

All three checks were extracted from the previously monolithic `_gate_one_project` into pure, DB-free functions (`_check_participants_invariant`, `_check_treaty_allocation_invariant`, `_check_program_onboarding_invariant`) specifically so they could be exercised with synthetic negative-test inputs (Section 18) — `_gate_one_project` now calls them and extends its own failure list, with no behavior change to the positive (real-corpus) path, confirmed by re-running the gate against the full corpus before and after the refactor with identical PASS results.

## 18. Negative gate tests

New file `tests/test_canonical_integrity_gate_negative.py`, 12 tests, all passing:

- **PARTICIPANTS**: passes on correct input; fails on a duplicate entry; fails on an extra non-claiming participant; fails on a missing claiming participant.
- **TREATY ALLOCATION**: passes on correct input; fails on a non-conserving allocation sum (100%→200%); **fails on a doubled single-participant incentive kept under the old 2x-gross bound** (the exact P1-GATE-001 gap — proves the new independent recomputation catches what the old plausibility-only check would have missed); fails when a feasible allocation isn't marked `fully_priced`; does NOT fail on a genuine, unrelated `canonical_data_gaps` disclosure (regression guard).
- **PROGRAM ONBOARDING**: fails on a top-level NONCONFORMANT program; never fails on a `PATHWAY_SPECIFIC` program (top-level or nested); **fails on a NONCONFORMANT program priced only inside a nested `conditional_scenario`** (the exact P1-GATE-001 gap Codex named).

`current generation fingerprints mixed` and `current rejection accounting incomplete` (the two remaining bullets from the task's negative-test list) are covered by real runtime regression tests rather than synthetic gate unit tests — `test_canonical_generation_freshness.py`'s cross-view reconciliation check and `test_component_rejection_persistence.py`'s idempotency test respectively — since these are properties of the underlying data-freshness/persistence mechanisms the gate's existing invariants already depend on, not distinct gate-level oracles of their own.

## 19. P0 regression

Re-verified across all 14 optimizer-ready projects after every P1 fix (SEL/PART both re-run after the `ENGINE_VERSION` bump specifically, since it forced full regeneration):

```
SELECTION_DIVERGENCES: 0
NONCOMPARABLE_PERSISTED_LEADERS: 0
COMPONENT_PARTICIPANT_MISMATCHES: 0 / 3474  (component corpus grew 2585 -> 3474 -- the +889 P1-REJ-001 reject rows, 0 mismatches among them since rejects carry empty participants by design)
EXTRA_NONCLAIMING_PARTICIPANTS: 0
```

P0-SEL-001 and P0-PART-001 remain closed; their implementation was not redesigned — only the mechanically-required interactions (ENGINE_VERSION-driven regeneration; new reject rows appearing in the same served `structures` list) were accounted for.

## 20. Treaty regression

No treaty-pricing code was modified. Corpus-wide runtime sweep:

```
TOTAL_TREATY_ROWS: 325
SOLVABLE(non-UNRESOLVED_FACTS with conditional_scenario): 282
FULLY_PRICED: 123
NON_CONSERVING: 0
```

Byte-identical to the accepted P0-3 baseline. **DOUBLE_COUNTED_QPE = 0, UNEXPLAINED_INCENTIVE_MISMATCH = 0.**

## 21. Program consumption regression

No program discovery/authority-coverage code was modified (only the *conformance classification* of one program, per P1-CONF-001).

```
OPTIMIZER_VISIBLE_PROGRAM_COUNT: 125
```

**SILENT_PROGRAM_OMISSIONS = 0** — unchanged from the prior full audit's own finding.

## 22. Full corpus runtime matrix

All 14 optimizer-ready projects, current `ENGINE_VERSION=canonical-1.54.0`:

| Project | Canonical selection | Component mismatches | Package/structure divergence |
|---|---|---:|---:|
| 10 Double Zero | None/None/None ✓ | 0 / 300 | 0 |
| 5 LBS OF PRESSURE | matched ✓ | 0 / 0 | 0 |
| Bad Hombres | matched ✓ | 0 / 196 | 0 |
| Baron Samedi | None/None/None ✓ | 0 / 297 | 0 |
| F#K Valentine's Day | None/None/None ✓ | 0 / 294 | 0 |
| Going Places | None/None/None ✓ | 0 / 300 | 0 |
| Interference | None/None/None ✓ | 0 / 297 | 0 |
| Lips Like Sugar | matched ✓ | 0 / 297 | 0 |
| Rocky Mountain | None/None/None ✓ | 0 / 300 | 0 |
| The Cure | None/None/None ✓ | 0 / 198 | 0 |
| The Little Utopia | None/None/None ✓ | 0 / 198 | 0 |
| The System | None/None/None ✓ | 0 / 297 | 0 |
| Twilight of the Dead | None/None/None ✓ | 0 / 200 | 0 |
| Underwater | None/None/None ✓ | 0 / 300 | 0 |

Treaty conservation: 0 non-conserving across all 325 rows (Section 20). Program consumption: 125/125 intact, 0 silent omissions (Section 21). Component rejection reconciliation: 1291 rejections corpus-wide (grown from the 889 measured at first fresh evaluation as the full suite exercised additional real generations), 0 duplicates on idempotent rerun, 0 rejected-as-priced (Section 11).

## 23. Canonical gates

**Canonical Budget Integrity Gate** (untouched code path): PASS, all four locked-corpus budgets, all 16 invariant families.

**Non-Globe Canonical Integrity Gate**, after all P1-GATE-001 strengthening:

```
Projects evaluated: 14 PASS, 0 FAIL, 36 SKIP (no budget on file yet — a real state, not a gate failure)

  PASS   BUDGET — 14 project(s) checked, 0 failure(s)
  PASS   ELIGIBILITY — 14 project(s) checked, 0 failure(s)
  PASS   QPE — 14 project(s) checked, 0 failure(s)
  PASS   INCENTIVE — 14 project(s) checked, 0 failure(s)
  PASS   NPC TRACE — 14 project(s) checked, 0 failure(s)
  PASS   PARTICIPANTS — 14 project(s) checked, 0 failure(s)
  PASS   SCENARIO IDENTITY — 14 project(s) checked, 0 failure(s)
  PASS   STATUS — 14 project(s) checked, 0 failure(s)
  PASS   PROGRAM CERTAINTY — 14 project(s) checked, 0 failure(s)
  PASS   PROJECT MODELING POLICY — 14 project(s) checked, 0 failure(s)
  PASS   SELECTION — 14 project(s) checked, 0 failure(s)
  PASS   PROGRAM ONBOARDING — 14 project(s) checked, 0 failure(s)
  PASS   TREATY ALLOCATION — 14 project(s) checked, 0 failure(s)

PATHWAY_SPECIFIC programs (P1-CONF-001): au_producer_offset (AU)

CANONICAL INTEGRITY GATE (13 non-Globe invariants): PASS — GLOBE remains separately DEFERRED BY SEQUENCING
```

All 13 invariants pass with the STRENGTHENED assertions actually exercising the new cross-checks (Sections 17–18 prove these would have failed on the pre-fix defects).

## 24. Full test suite

`cd frametax2/backend && PYTHONPATH=. python3 -m pytest tests/ -q`, run once, per the required efficiency model:

First run surfaced 7 failures — investigated individually per the task's own rigor requirement (verify legitimate consequence vs. real regression before touching any test):

| Test | Diagnosis | Fix |
|---|---|---|
| `test_canonical_authority_substrate.py::test_fvd_runtime_candidate_universe_restored` | Hardcoded `len(entries)==356` — legitimately grew by the 88 new FVD component rejection rows (P1-REJ-001) | Updated to 444, with a comment explaining the +88 delta, following this file's own established per-change-comment convention |
| `test_canonical_economics_integrity_repair.py::test_read_only_builder_never_reaches_write_capable_recovery` | Real consequence of my P1-FRESH-001 refactor — this structural test source-greps for a literal `read_only=True` call that moved from `canonical_production_view.py` into the new shared `canonical_evaluation.current_generation_fingerprint` | Updated to check the call's new correct location, plus an added assertion that `canonical_production_view.py` genuinely delegates to the shared function (never reimplements its own) |
| `test_canonical_served_wiring_repair.py::test_fvd_accounting_matches_codex_diagnosis` | Three hardcoded `==45` assertions (`unpriced`, `accounting["unpriceable_count"]`, `unpriceable_ranked`) — legitimately grew to 133 (45 original + 88 new FVD component rejections; independently verified the exact split) | All three updated to 133, with the reconciliation documented |
| `test_canonical_served_wiring_repair.py::test_fvd_unpriceable_causes_are_differentiated_not_flattened` | Same `==45`→133 pattern; test's own docstring already states "the count itself is not the invariant this test guards" | Updated to 133 |
| `test_component_relocation.py` (3 tests) | Iterated ALL `component_relocation` entries without filtering `is_fully_priced` — the new reject rows (empty segments/participants) broke assumptions about routed-destination shape | Added `and e["is_fully_priced"]` filters, scoping each test to its actual documented subject (priced candidates) |

All fixes are either (a) an updated real count with the exact delta independently verified and documented, or (b) a scope-correction to a test's own already-stated intent — never a weakened assertion. Re-ran all seven previously-failing tests' files individually: 130/130 passed. Final full suite, run once more:

```
4774 passed, 3 skipped, 12 warnings in 848.14s (0:14:08)
```

**0 failures.**

## 25. Engine version / freshness decision

- **P1-FRESH-001**: no bump required. `current_generation_fingerprint()` recomputes fresh, in pure Python, on every call — it is not itself a cached/fingerprinted value; only the underlying `StructureCalculationResult` rows it queries are engine-version-gated (unchanged). The extraction changes WHERE the correct logic lives, not WHAT gets persisted or how freshness is determined.
- **P1-REJ-001**: bump required and performed (`canonical-1.53.0` → `canonical-1.54.0`). This is a genuine persistence-SHAPE change — new `StructureCalculationResult` rows that previously never existed for a given fingerprint. Without the bump, every already-evaluated project's existing-row reuse check (`if existing is not None: return ... reused=True`) would keep serving the OLD row set forever, and the new reject rows would never be created for any project already evaluated under 1.53.0. Confirmed live: the corpus-wide rejection count matched Codex's cited 889 only after this bump forced fresh regeneration.
- **P1-CONF-001**: no bump required. Program conformance classification is a pure, stateless function over static registries (`get_doctrine`, `get_program_requirements`, `get_rate_rules`, `_CONFIRMED_SEPARATE_PATHWAY`) — never cached in any persisted row. The fix takes effect on the very next call with no migration needed.
- **P1-GATE-001**: no bump required — the gate is a read-only diagnostic script, not part of the served runtime; it has no persisted state of its own.

## 26. Files changed

**Source (5):**
- [`frametax2/backend/app/services/canonical_evaluation.py`](../../frametax2/backend/app/services/canonical_evaluation.py) — P1-FRESH-001 (new shared `current_generation_fingerprint`), P1-REJ-001 (persisted component rejections, `_classify_component_rejection`, `ENGINE_VERSION` bump).
- [`frametax2/backend/app/services/canonical_production_view.py`](../../frametax2/backend/app/services/canonical_production_view.py) — P1-FRESH-001 (both builders now call the shared function; dead import removed).
- [`frametax2/backend/app/data/national_cultural_status.py`](../../frametax2/backend/app/data/national_cultural_status.py) — P1-CONF-001 (`get_jurisdiction_code_for_linked_program`).
- [`frametax2/backend/app/services/program_onboarding_conformance.py`](../../frametax2/backend/app/services/program_onboarding_conformance.py) — P1-CONF-001 (`PATHWAY_SPECIFIC` classification).
- [`frametax2/backend/scripts/canonical_integrity_gate.py`](../../frametax2/backend/scripts/canonical_integrity_gate.py) — P1-GATE-001 (three invariants strengthened and extracted to pure functions; PATHWAY_SPECIFIC display).

**Tests, new (3):**
- `frametax2/backend/tests/test_canonical_generation_freshness.py` — P1-FRESH-001 regression.
- `frametax2/backend/tests/test_component_rejection_persistence.py` — P1-REJ-001 regression.
- `frametax2/backend/tests/test_canonical_integrity_gate_negative.py` — P1-GATE-001 negative tests.

**Tests, updated (7):**
- `test_canonical_scenario_participants.py`, `test_canonical_selection_consistency.py` — no functional change needed for the P1s (verified clean), left as-is from the prior P0 task.
- `test_program_onboarding_conformance.py` — P1-CONF-001 (stale `NONCONFORMANT` assertion corrected to `PATHWAY_SPECIFIC`, new structural/uniqueness tests added).
- `test_codex_final_optimizer_health_audit.py`, `test_canonical_authority_substrate.py`, `test_canonical_economics_integrity_repair.py`, `test_canonical_served_wiring_repair.py`, `test_component_relocation.py` — legitimate count/scope corrections from P1-REJ-001 and P1-FRESH-001, each documented in Section 24.

**Docs (1):** this file.

No frontend, treaty-pricing, program-discovery/authority-coverage data, MFNI, Globe, or SA-2 code was touched.

## 27. Commit / push / remote

Recorded in the chat response after this artifact is committed (commit hash, push confirmation, `local HEAD == remote HEAD` verification).

## 28. Final verdict

All required conditions verified true:
1. P1-FRESH-001 = CLOSED (Sections 4–7).
2. P1-REJ-001 = CLOSED (Sections 8–11).
3. P1-CONF-001 = CLOSED (Sections 12–15).
4. P1-GATE-001 = CLOSED (Sections 16–18).
5. P0-SEL-001 remains closed (Section 19).
6. P0-PART-001 remains closed (Section 19).
7. Treaty P0-3 remains closed (Section 20).
8. Program consumption remains complete (Section 21).
9. Current canonical reads never mix generations (Sections 6–7).
10. All meaningful component rejections have durable dispositions (Sections 10–11).
11. `au_producer_offset` has one coherent canonical pathway-specific identity (Sections 14–15).
12. Canonical gates materially detect recurrence (Sections 17–18, proven via negative tests).
13. Full optimizer-ready corpus passes (Section 22).
14. Backend suite passes (Section 24) — 4774 passed, 3 skipped, 0 failed.
15. No unrelated scope changed (Sections 3, 26).

**OPTIMIZER FINAL CLOSEOUT — IMPLEMENTATION ACCEPTED**

**GO_FOR_CODEX_FINAL_OPTIMIZER_ACCEPTANCE**
