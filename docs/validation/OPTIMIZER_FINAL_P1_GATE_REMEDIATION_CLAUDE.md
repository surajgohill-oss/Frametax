# Optimizer Final P1-GATE-001 Integrity-Gate Remediation

Bounded repair of the single remaining optimizer acceptance blocker, `P1-GATE-001`, identified by Codex's independent final acceptance audit ([`OPTIMIZER_FINAL_ACCEPTANCE_CODEX.md`](OPTIMIZER_FINAL_ACCEPTANCE_CODEX.md) / [`OPTIMIZER_FINAL_ACCEPTANCE_MATRIX_CODEX.csv`](OPTIMIZER_FINAL_ACCEPTANCE_MATRIX_CODEX.csv), audit commit `d04a7567e5da5864a49392d3094e06e94bc404d8`, audited application commit `e7574050daa8d76c01d2302abaa8d7b3bd22b039`). No economics, program research, MFNI, jurisdiction doctrine, co-production architecture, UI, or Script Analyzer work was performed. **This artifact does not itself certify acceptance — Codex retains independent acceptance ownership; the classification below is Claude's own resolution reporting, submitted for independent re-verification.**

## 0. Identity gate

- `pwd`: `/Users/Suraj/cineglobe-frametax`
- Repository: `surajgohill-oss/Frametax`, branch `claude/audit-frametax-features-NZcX5`
- Starting HEAD (before this remediation's edits): confirmed an ancestor of, and byte-identical in optimizer/gate/test code to, the audited commit `e7574050daa8d76c01d2302abaa8d7b3bd22b039` — verified via `git merge-base --is-ancestor` and by directly reading the current (pre-edit) `canonical_integrity_gate.py` and confirming it exactly matched Codex's cited line ranges (446–447, 514, 538–540, 248–257) and defect descriptions before making any change.
- Codex audit commit `d04a7567e5da5864a49392d3094e06e94bc404d8`: read directly from the repository at task start (both `.md` and `.csv`), not worked from the task prompt's summary.
- `.claude/settings.local.json` already carries `Bash(*)` — the broadest possible allow rule; no permission changes were made or needed this session (routine workflow proceeded without interruption).

## 1. Reconciliation against the Codex artifact (mid-turn instruction)

Per an explicit mid-turn instruction, before declaring anything resolved: **all five findings were confirmed STILL REPRODUCIBLE in the actual code at the start of this remediation turn** — not assumed stale. This was verified by directly reading `canonical_integrity_gate.py` at the beginning of this turn and confirming:
- The `if not s["is_fully_priced"]: continue` at (then) lines 446–447 still preceded the PARTICIPANTS call (line 514) and the PROGRAM ONBOARDING call (lines 538–540), exactly as Codex described.
- `_check_treaty_allocation_invariant` still computed only `allocated_share_usd * modeled_rate` as an upper bound — no independent recomputation existed.
- `_TESTED_INVARIANTS` still declared exactly 13 families — no FRESHNESS or REJECTION ACCOUNTING entry existed anywhere in the file.

No part of any of the five findings was already resolved by prior committed work before this turn's edits. All five map to **RESOLVED_IN_THIS_DELTA** (Section 9 gives the exact per-finding mapping the user requested).

## 2. Root-cause chain per defect

### Defect #1 — Treaty participant QPE
- **SYMPTOM**: a malformed treaty participant with an implausible `selected_incentive_usd` could pass the gate.
- **ROOT CAUSE**: `_check_treaty_allocation_invariant` bounded each participant's incentive only against `gross_share_of_budget × modeled_rate` — a coarse upper ceiling on the ENTIRE allocated share, not the participant's real *qualifying* spend after exclusions/caps.
- **ORIGINATING CODE PATH**: `canonical_integrity_gate.py::_check_treaty_allocation_invariant`, the `if gross_budget and alloc:` block (pre-existing from the prior P0-3/P1-GATE-001 pass).
- **WHY EXISTING GATE/TEST MISSED IT**: the only negative test exercised a value that exceeded even the loose ceiling (`test_treaty_gate_fails_on_doubled_participant_incentive`) — no test constructed a value that stayed *under* the ceiling while still being wrong relative to real qualifying spend.
- **REPAIR**: new `_independently_recompute_participant_incentive` helper reconstructs the participant's real scaled inputs (same `dataclasses.replace`-based technique `_build_conditional_bilateral_scenario`'s own `_allocated_inputs_for` already uses) and reprices through the SAME canonical kernel, `canonical_evaluation._price_candidate`. The gate now compares the served value against this independently recomputed value directly (2% or $50 tolerance), not merely a ceiling.
- **NEGATIVE TEST**: `test_independent_qpe_recomputation_catches_corrupted_participant_incentive` — reproduces Codex's exact counterexample shape (a corrupted value that stays under the old ceiling), searching across all of Little Utopia's real resolved treaty participants for a genuine, non-fixture-specific margin.
- **PREVENTION**: the check now derives its own answer from raw inputs every time; it can never again be satisfied merely because a fabricated value happens to be numerically small.

### Defect #2 — Nested conditional program conformance
- **SYMPTOM**: a NONCONFORMANT program priced only inside a treaty opportunity's `conditional_scenario` could reach served output undetected by this gate.
- **ROOT CAUSE**: the nested check inside `_check_program_onboarding_invariant` was written correctly, but the CALLER invoked the whole function only after `if not s["is_fully_priced"]: continue` — and a `treaty_coproduction` opportunity row is NEVER top-level `is_fully_priced=True` by construction (real pricing lives entirely in `conditional_scenario`). The nested check was therefore dead code for every real treaty row in the corpus.
- **ORIGINATING CODE PATH**: `canonical_integrity_gate.py::_gate_one_project`, the call-site ordering around the early continue.
- **WHY EXISTING GATE/TEST MISSED IT**: the negative test for this exact case (`test_program_onboarding_fails_on_nonconformant_program_priced_only_in_nested_conditional_scenario`) called the pure function directly — it never went through `_gate_one_project`, so it could not detect that the real integration path never reached the function at all.
- **REPAIR**: moved the `_check_participants_invariant` and `_check_program_onboarding_invariant` calls to before the early continue, applying to every structure unconditionally; `_check_program_onboarding_invariant`'s own top-level sub-check is now internally gated on `s.get("is_fully_priced")` (so it no longer depends on the caller having pre-filtered).
- **NEGATIVE TEST**: `test_gate_one_project_integration_reaches_nested_program_onboarding_check` — calls the REAL `_gate_one_project` (not the isolated pure function) against a real project, with one real nested treaty program poisoned to `NONCONFORMANT`, and confirms the live call path reports it.
- **PREVENTION**: the integration test itself would fail loudly (not vacuously pass) if this call-site ordering ever regresses.

### Defect #3 — Canonical freshness
- **SYMPTOM**: no gate invariant existed to detect a result served from a stale generation.
- **ROOT CAUSE**: `_TESTED_INVARIANTS` never declared a freshness family at all — the gate had zero freshness protection, even though the underlying P1-FRESH-001 fix (`canonical_evaluation.current_generation_fingerprint`) already exists and is used by the served views.
- **ORIGINATING CODE PATH**: `canonical_integrity_gate.py` — an absence, not a bug in existing code.
- **WHY EXISTING GATE/TEST MISSED IT**: no invariant family and no test existed for this class at all.
- **REPAIR**: new `_check_freshness_invariant` pure function, reusing (never duplicating) the existing `current_generation_fingerprint()` reconstruction — compares the reconstructed current fingerprint against the evaluator's own `state_fingerprint` and against the actual set of fingerprints persisted under the current `ENGINE_VERSION`. New `"FRESHNESS"` entry added to `_TESTED_INVARIANTS`.
- **NEGATIVE TEST**: `test_freshness_gate_fails_on_evaluator_reconstruction_mismatch` and `test_freshness_gate_fails_when_reconstructed_fingerprint_not_persisted` — pure-function tests with synthetic mismatched fingerprints (no real-project DB mutation needed, since the check operates on plain fingerprint values).
- **PREVENTION**: any future reintroduction of the P1-FRESH-001 class (a reader using a "newest row" heuristic instead of the true reconstruction) now has a permanent, always-run gate invariant.

### Defect #4 — Rejection accounting
- **SYMPTOM**: no gate invariant existed to detect a candidate silently disappearing from the evaluated universe with no recorded disposition.
- **ROOT CAUSE**: same as Defect #3 — an absence. The underlying P1-REJ-001 disposition fields (`candidate_status`, `rejection_reason_class`) already exist on every served structure, but nothing verified every component row actually carries one.
- **ORIGINATING CODE PATH**: `canonical_integrity_gate.py` — an absence.
- **WHY EXISTING GATE/TEST MISSED IT**: no invariant family and no test existed for this class at all.
- **REPAIR**: new `_check_rejection_accounting_invariant` pure function, reusing the EXISTING disposition model (never a new taxonomy) — every `component_relocation` row must be either genuinely priced (`is_fully_priced=True`, `candidate_status=="PRICED"`) or genuinely rejected (`candidate_status=="RULE_REJECTED"` with a real `rejection_reason_class`); no two rows may share the same `(anchor, target, component, program)` identity. New `"REJECTION ACCOUNTING"` entry added to `_TESTED_INVARIANTS`.
- **NEGATIVE TEST**: `test_rejection_accounting_fails_on_silently_omitted_disposition`, `test_rejection_accounting_fails_on_duplicate_attempt_identity`, and `test_rejection_accounting_fails_on_silent_omission_even_amid_valid_surviving_candidates` (the adversarial combination — a silent omission hiding among otherwise-correct rows).
- **PREVENTION**: deliberately a structural completeness/uniqueness check (not a full re-derivation of the expected candidate universe, which remains the job of a full audit) — proportionate scope for a fast, permanent, generic CI-style gate.

### Defect #5 — Rejected component participant checks
- **SYMPTOM**: a rejected component row's participant field could be corrupted with no detection.
- **ROOT CAUSE**: identical mechanism to Defect #2 — `_check_participants_invariant` was called only after the top-level `is_fully_priced` continue, so a `RULE_REJECTED` component row (P1-REJ-001, `is_fully_priced=False`) never reached the check at all.
- **ORIGINATING CODE PATH**: same call-site ordering as Defect #2.
- **WHY EXISTING GATE/TEST MISSED IT**: the existing PARTICIPANTS negative tests only constructed priced-shaped fixtures.
- **REPAIR**: the same call-site move that fixed Defect #2 also fixes this — `_check_participants_invariant` is internally safe to run unconditionally (a rejected row's expected claiming set is genuinely empty when it has no segments, producing zero false positives on real rejected data).
- **NEGATIVE TEST**: `test_participants_gate_fails_on_corrupted_rejected_component_row` (a rejected row with a corrupted non-empty participants list) alongside `test_participants_gate_passes_on_known_good_rejected_component_row` (the real empty-participants shape) and the integration-level `test_gate_one_project_integration_reaches_rejected_component_participant_check` (proves the real, currently-persisted P1-REJ-001 rejection ledger reaches this check with zero false positives).
- **PREVENTION**: rejection status and integrity validation are now structurally separate — a row's rejected status no longer implies "skip validation."

## 3. Files changed

- `frametax2/backend/scripts/canonical_integrity_gate.py` — all five repairs (357 lines changed).
- `frametax2/backend/tests/test_canonical_integrity_gate_negative.py` — 17 new tests across all five defects, plus one pre-existing test fixed for the new internal `is_fully_priced` gating in `_check_program_onboarding_invariant` (380 lines changed).
- `docs/validation/OPTIMIZER_FINAL_P1_GATE_REMEDIATION_CLAUDE.md` — this file.

No economics, program, authority, MFNI, Globe, or SA-2 file was touched. No parallel/duplicate validation system was created — every repair extends the existing `canonical_integrity_gate.py` and its existing `_TESTED_INVARIANTS`/pure-function-extraction pattern.

## 4. Negative oracles added (17 new tests)

| Defect | Known-good (PASS) | Corrupted (FAIL) |
|---|---|---|
| #1 QPE | `test_independent_qpe_recomputation_matches_known_good_real_treaty_structure` | `test_independent_qpe_recomputation_catches_corrupted_participant_incentive` |
| #2 Nested conformance | `test_program_onboarding_never_fails_on_pathway_specific_program` (nested case) | `test_program_onboarding_fails_on_nonconformant_program_priced_only_in_nested_conditional_scenario`, `test_program_onboarding_nested_check_reachable_when_top_level_never_priced`, integration: `test_gate_one_project_integration_reaches_nested_program_onboarding_check` |
| #3 Freshness | `test_freshness_gate_passes_when_all_sources_agree`, `test_freshness_gate_passes_when_project_has_no_budget_yet` | `test_freshness_gate_fails_on_evaluator_reconstruction_mismatch`, `test_freshness_gate_fails_when_reconstructed_fingerprint_not_persisted` |
| #4 Rejection accounting | `test_rejection_accounting_passes_on_known_good_priced_and_rejected_mix` | `test_rejection_accounting_fails_on_silently_omitted_disposition`, `test_rejection_accounting_fails_on_disagreeing_disposition_fields`, `test_rejection_accounting_fails_on_duplicate_attempt_identity`, `test_rejection_accounting_fails_on_silent_omission_even_amid_valid_surviving_candidates` |
| #5 Rejected participants | `test_participants_gate_passes_on_known_good_rejected_component_row`, integration: `test_gate_one_project_integration_reaches_rejected_component_participant_check` | `test_participants_gate_fails_on_corrupted_rejected_component_row` |

Plus `test_program_onboarding_top_level_check_skipped_when_not_priced` and `test_rejection_accounting_ignores_non_component_structures` (scope-boundary regression guards).

For each FAIL case, the test itself documents (and where applicable, dynamically proves) that the identical corrupted input would have escaped the PRIOR gate — most directly for Defect #1, where the test explicitly constructs a value that stays under the old ceiling before asserting the new check catches it.

## 5. Test results

```
PYTHONPATH=. python3 -m pytest tests/test_canonical_integrity_gate_negative.py -q
30 passed, 5 warnings

PYTHONPATH=. python3 -m pytest tests/test_canonical_generation_freshness.py \
  tests/test_component_rejection_persistence.py tests/test_program_onboarding_conformance.py \
  tests/test_canonical_integrity_gate_negative.py tests/test_canonical_selection_consistency.py \
  tests/test_canonical_scenario_participants.py tests/test_copro_conditional_pricing_bridge.py -q
72 passed, 2 skipped

PYTHONPATH=. python3 scripts/canonical_integrity_gate.py
14 PASS, 0 FAIL, 36 SKIP; all 15 non-Globe invariant families PASS, 0 failures each
(FRESHNESS and REJECTION ACCOUNTING are new; TREATY ALLOCATION, PARTICIPANTS,
PROGRAM ONBOARDING now exercise the deeper/reachable checks)

PYTHONPATH=. python3 scripts/canonical_budget_integrity_gate.py
PASS — all four locked-corpus budgets, all 16 invariant families

PYTHONPATH=. python3 -m pytest tests/ -q
4792 passed, 3 skipped, 12 warnings, 0 failed
```

## 6. Runtime / source identity

- Repository/worktree: `/Users/Suraj/cineglobe-frametax`, branch `claude/audit-frametax-features-NZcX5`.
- Starting commit: verified ancestral to and byte-identical (in optimizer code) with Codex's audited `e7574050daa8d76c01d2302abaa8d7b3bd22b039` (Section 0).
- Loaded runtime: same `.venv`/live DB the prior sessions and Codex's own audit used (`app.db.session.engine`) — the same 14 optimizer-ready projects, same `ENGINE_VERSION=canonical-1.54.0`, confirmed by the gate's own printed per-project fingerprint/engine-version state during every run above.
- Evaluation fingerprint: reconstructed live via `current_generation_fingerprint()` for every project checked; confirmed to match the evaluator's own `state_fingerprint` and to exist among the current-engine persisted rows for all 14 ready projects (the new FRESHNESS invariant itself is this proof, executed and passing).
- Result being validated: the actual current served `canonical_production_view.build_production_and_structures` output for all 14 ready projects, read fresh in every gate run above — never a cached/stale artifact.

**RUNTIME = VERIFIED** (all identity links proven before any economics/gate result was reported).

## 7. Adversarial closeout (Section 11)

Ran all five negative oracles individually (Section 5) and the required combinations:
- Nested conditional + treaty participant: the poisoned program in `test_gate_one_project_integration_reaches_nested_program_onboarding_check` is a real, currently-nested-priced treaty participant program — the same structure exercises both classes at once.
- Stale result + otherwise-valid economics: `test_freshness_gate_fails_on_evaluator_reconstruction_mismatch` / `..._fails_when_reconstructed_fingerprint_not_persisted` — plausible-looking fingerprints, still rejected.
- Rejected component + corrupted participant: `test_participants_gate_fails_on_corrupted_rejected_component_row`.
- Missing rejection accounting + valid surviving candidates: `test_rejection_accounting_fails_on_silent_omission_even_amid_valid_surviving_candidates`.

No fixture was weakened and no existing negative oracle's assertion was loosened to make anything pass.

## 8. Generic propagation (Section 13)

None of the five repairs reference a named project, jurisdiction, or program in the actual gate code:
- `_independently_recompute_participant_incentive` takes `(project_inputs, jurisdiction_code, program_slug, pct)` — works for any future treaty participant.
- `_check_program_onboarding_invariant`'s nested check iterates `conditional.get("priced_components")` generically.
- `_check_freshness_invariant` takes plain fingerprint values — no project-specific logic.
- `_check_rejection_accounting_invariant` iterates any `structures` list, keyed only on structural fields (`structure_type`, `is_fully_priced`, `candidate_status`, `rejection_reason_class`, `component_allocations`).
- `_check_participants_invariant` was already generic (unchanged in this delta beyond the call-site move).

Little Utopia's real project ID is used only as a DATA SOURCE for the DB-backed integration/QPE tests (the same established convention every other real-data test in this suite already follows) — never as a special case inside the repaired gate code itself.

## 9. Finding-to-classification mapping (per the mid-turn reconciliation instruction)

| # | Codex finding | Classification | Evidence |
|---|---|---|---|
| 1 | No independent treaty participant-QPE recomputation | **RESOLVED_IN_THIS_DELTA** | Confirmed still open at turn start (coarse ceiling only); `_independently_recompute_participant_incentive` + comparison added; negative test §4 |
| 2 | Nested conditional-program conformance is bypassed | **RESOLVED_IN_THIS_DELTA** | Confirmed still open at turn start (`continue` at old lines 446–447 preceded onboarding call at 538–540); call-site moved + internal gating; negative + integration tests §4 |
| 3 | No canonical freshness gate/negative oracle | **RESOLVED_IN_THIS_DELTA** | Confirmed absent at turn start (13 declared families, no FRESHNESS); new invariant + 2 negative tests §4 |
| 4 | No rejection-accounting gate/negative oracle | **RESOLVED_IN_THIS_DELTA** | Confirmed absent at turn start; new invariant + 4 negative tests §4 |
| 5 | Rejected component rows bypass participant checks | **RESOLVED_IN_THIS_DELTA** | Confirmed still open at turn start (same `continue` gap as #2); same call-site move; negative + integration tests §4 |

None of the five were already resolved by prior committed work before this turn (`RESOLVED_BY_EXISTING_CURRENT_WORK` — not applicable), none remain open (`STILL_OPEN` — not applicable), and none were based on a stale/incorrect reading of already-fixed code (`SUPERSEDED_WITH_EVIDENCE` — not applicable, Codex's findings were accurate against the code as it stood at turn start).

## 10. Acceptance matrix (Section 12 format)

| REQUIREMENT | EXPECTED | OBSERVED | STATUS |
|---|---|---|---|
| Treaty participant QPE independently recomputed | Recomputation disagreement caught, not merely a ceiling | Independent recomputation implemented; corrupted-value test passes | PASS |
| Nested conditional program cannot bypass conformance | Nested check reachable via real `_gate_one_project` call | Integration test proves live path reaches it | PASS |
| Stale canonical result rejected | Freshness invariant rejects mismatch/missing-provenance | 2 negative tests pass | PASS |
| Silent rejection/disposition omission rejected | Rejection-accounting invariant rejects silent omission | 4 negative tests pass, incl. adversarial combination | PASS |
| Rejected component participant corruption detected | Participant check reaches rejected rows | Negative + integration tests pass | PASS |
| Known-good treaty candidate still passes | 0 false positives on real treaty data | `test_independent_qpe_recomputation_matches_known_good_real_treaty_structure` passes; live gate 14/14 PASS | PASS |
| Known-good conditional/nested candidate still passes | 0 false positives | `test_program_onboarding_never_fails_on_pathway_specific_program` passes; live gate PASS | PASS |
| Known-good component candidate still passes | 0 false positives | Live gate PARTICIPANTS 14/14 PASS on real corpus (2,585 priced + 889 rejected rows) | PASS |
| Relevant regression suite passes | No regression | 72 passed, 2 skipped (focused); 4,792 passed, 3 skipped (full) | PASS |
| Loaded-runtime/source identity proven | Repo/branch/commit/DB/engine/fingerprint chain proven | Section 6 | PASS |
| Future/generic candidate path covered | No fixture-specific branch in repaired code | Section 8 | PASS |

No row is FAIL. No row is a non-tooling UNVERIFIED.

## 11. Git closeout

- `git status --short` (pre-stage): exactly the two intended files modified, plus a large, unrelated set of untracked AG MFNI-research files (left untouched).
- `git diff --check`: clean, no whitespace/conflict-marker issues.
- `git diff --stat`: `canonical_integrity_gate.py` +357/−(part of that), `test_canonical_integrity_gate_negative.py` +380/−(part of that) — reviewed in full during implementation.
- Staged exactly: `frametax2/backend/scripts/canonical_integrity_gate.py`, `frametax2/backend/tests/test_canonical_integrity_gate_negative.py`, `docs/validation/OPTIMIZER_FINAL_P1_GATE_REMEDIATION_CLAUDE.md` — never `git add .`/`git add -A`.
- Commit SHA, push status, and remote HEAD match: recorded in the chat response after this artifact is committed.
- CI: no CI workflow exists in this repository (`.github/workflows/` was checked — not present); no CI status is reported, per the explicit instruction not to claim CI PASS without a workflow.

## 12. Final classification

Per the mid-turn instruction: **Claude does not self-certify optimizer acceptance.** All five `P1-GATE-001` sub-findings are classified `RESOLVED_IN_THIS_DELTA` per Section 9, with full negative-oracle proof (Section 4), a clean full regression suite (Section 5), and a complete acceptance matrix with zero FAIL rows (Section 10).

**P1-GATE-001 is ready for independent Codex re-verification.**
