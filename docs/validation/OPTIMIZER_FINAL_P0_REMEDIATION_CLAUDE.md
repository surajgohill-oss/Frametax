# Optimizer Final P0 Remediation

Fixes the final two P0 blockers Codex's broader-corpus optimizer audit found (commit `dcc6dde0a5ef4576ccf6da1582458f5d1354fb41`, full-acceptance audit `8890cc8a0ac949cb77f5a2b21223aeeb8117b80b`, audited application HEAD `cf7bf7cba423ec8edb32afcf46855f1480aec9be`): **P0-SEL-001** (broader-corpus leading-structure divergence) and **P0-PART-001** (non-claiming US anchor contamination). Nothing else was in scope — no new structure families, no MFNI/grants/funds/Globe/SA-2 work, no treaty-logic redesign.

## 1. Executive result

Both P0s fixed generically at their root, verified against the full 14-project optimizer-ready corpus with real runtime/persistence evidence, no regression to P0-3 treaty conservation, program-universe consumption, or either canonical gate. See Section 20 for the final verdict.

## 2. Permission preflight result

Ran the required compact probe batch (repo read/git status, disposable scratch write/edit/delete, one `python3 -c` invocation, one `pytest --collect-only`, one git log/diff). `.claude/settings.local.json` already carries `Bash(*)` — the broadest possible allow rule for this tool — yet the user observed permission dialogs for three of the probe steps (`python3 -c`, `pytest --collect-only`, plain `git status/log/diff`). Per protocol, host-observed prompts are authoritative and implementation was paused pending diagnosis.

Diagnosis: this is the same class of issue found in the prior session for `/tmp` writes — a Desktop-app-level permission layer outside `.claude/settings.local.json`'s control. Since `Bash(*)` is already the broadest rule available at the project-file level, there is no narrower or broader rule that could be written to change this; it cannot be repaired from project files. The user was asked how to proceed and chose to approve prompts manually as they appear for the remainder of this task, rather than pausing further. All subsequent Bash usage reused the same stable command shapes (one script, invoked with different mode arguments, rather than many unique `python -c`/heredoc forms) to keep the number of distinct prompts minimal, per the command-family discipline.

This is disclosed honestly rather than reported as a clean preflight: the gate was not fully clean, and the resolution was user-approved manual acknowledgement, not a repaired rule.

## 3. Audited starting HEAD

Verified before any code change:
- Current branch HEAD: `8890cc8a0ac949cb77f5a2b21223aeeb8117b80b` (local == fetched remote).
- `0f1c8d30ebbd6e926eaad8d198781c3b1a8ae5ef` (Claude's prior P0 remediation head) confirmed as an ancestor of current HEAD via `git merge-base --is-ancestor` — the prior P0-1/P0-2/P0-3 fixes are present and intact in the tree.
- `git status` before staging showed a large number of unrelated untracked files (AG's MFNI/secondary-research scripts and data) — none were touched, staged, or referenced.

## 4. P0-SEL-001 reproduction

Ran the real evaluator + served view against all 14 optimizer-ready projects (`.claude/scratch/repro_p0.py sel`, before the fix):

```
10 Double Zero:        evaluator_top=<some priced relocation id>  leading_structure_id=<same>  served_canonical=None  DIVERGENT=True
Baron Samedi:           ... (same pattern)
Going Places:           ... (same pattern)
Interference:           ... (same pattern)
Rocky Mountain:         ... (same pattern)
The Cure:               ... (same pattern)
The System:             ... (same pattern)
Twilight of the Dead:   ... (same pattern)
Underwater:             ... (same pattern)
Bad Hombres:            evaluator_top=served_canonical=leading_structure_id (all equal)  DIVERGENT=False
Lips Like Sugar:        evaluator_top=served_canonical=leading_structure_id (all equal)  DIVERGENT=False
Little Utopia:          all None, DIVERGENT=False
F#K Valentine's Day:    all None, DIVERGENT=False
5 LBS OF PRESSURE:      all equal, DIVERGENT=False
```

Reproduced exactly the nine named projects with a real, non-comparable persisted `leading_structure_id` diverging from a correctly-`null` served `canonical_selected_structure_id` — matching Codex's Section 7 finding exactly.

## 5. P0-SEL-001 root cause

`canonical_evaluation.py::_summarize_evaluation` has three branches for computing `top_pair`:
1. A priced baseline exists → the baseline wins only if its qualification admits Recommended.
2. A baseline exists but is blocked (never priced) → `top_pair = None` (correctly: no relocation is ever comparable).
3. **No baseline row at all** (neither priced nor blocked) → `top_pair = priced[0] if priced else None` — the cheapest candidate among ALL priced rows, **without checking comparability**.

`relocation_cost_normalized` (the field `canonical_production_view.py`'s own `comparable` pool calls `is_directly_comparable`) is confirmed `True` **only** for the baseline candidate (`is_baseline`) — every generator in `canonical_evaluation.py` that sets this field sets it to `is_baseline` or an equivalent same-jurisdiction check (verified: `grep -n "relocation_cost_normalized"` across the file). With no baseline row present at all, there is therefore **definitionally no comparable candidate** — branch 3's fallback to `priced[0]` was promoting the cheapest non-comparable relocation purely because its raw number was smallest, the exact false-winner pattern branch 2's own reasoning already rejects. `canonical_production_view.build_production_and_structures` was already correct — its `comparable` pool applies the same two gates (`is_directly_comparable` and qualification-admits-Recommended) and correctly finds nothing, serving `null`. The persistence-layer branch 3 was the sole root cause; no other code path writes `Project.leading_structure_id`.

## 6. P0-SEL-001 fix

`canonical_evaluation.py`, branch 3, changed from `top_pair = priced[0] if priced else None` to `top_pair = None`, with a comment explaining the comparability reasoning and naming the nine confirmed real projects. This reuses the SAME authority the other two branches already use (comparability, never a second ranking rule) — no project-specific, jurisdiction-specific, or Saudi-specific exception. The existing `elif project.leading_structure_id is not None: project.leading_structure_id = None` clearing branch (unchanged) already handles clearing any stale non-comparable pointer once `top_pair` is `None`.

## 7. P0-SEL-001 14-project verification

Re-ran the identical reproduction script after the fix, real runtime evaluation + real persisted `Project.leading_structure_id` + real served view, across all 14 optimizer-ready projects:

```
10 Double Zero:        evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
5 LBS OF PRESSURE:      evaluator_top=e4ca83be-... leading_structure_id=e4ca83be-... served_canonical=e4ca83be-... DIVERGENT=False
Bad Hombres:            evaluator_top=3eca66ff-... leading_structure_id=3eca66ff-... served_canonical=3eca66ff-... DIVERGENT=False
Baron Samedi:           evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
F#K Valentine's Day:    evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
Going Places:           evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
Interference:           evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
Lips Like Sugar:        evaluator_top=a34235db-... leading_structure_id=a34235db-... served_canonical=a34235db-... DIVERGENT=False
Rocky Mountain:         evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
The Cure:               evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
The Little Utopia:      evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
The System:             evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
Twilight of the Dead:   evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
Underwater:             evaluator_top=None leading_structure_id=None served_canonical=None DIVERGENT=False
```

**0 divergence, 0 fallback leaders, 0 non-comparable persisted leaders across all 14 projects.** All nine named projects now correctly show `None`/`None`/`None`. Bad Hombres, Lips Like Sugar, and 5 LBS OF PRESSURE — the three real projects with a genuine comparable winner — keep their valid selection byte-identical across evaluator, persisted, and served layers. `evaluate_project()` recomputes `_summarize_evaluation` on every call (it is not itself cached per engine-version/fingerprint the way `StructureCalculationResult` rows are), so this correction is immediate and required no data migration.

## 8. P0-PART-001 reproduction

Ran the full corpus sweep (`.claude/scratch/repro_p0.py part`, before the fix) — independently deriving `expected = {segments with claims_incentive is True}` per `component_relocation` structure and comparing to served `participants`:

```
10 Double Zero:        250 / 250 component rows mismatched
Baron Samedi:           203 / 203
Going Places:           221 / 221
Interference:           205 / 205
Rocky Mountain:         258 / 258
The Cure:               140 / 140
The System:             203 / 203
Twilight of the Dead:   154 / 154
Underwater:             244 / 244
(remaining five projects: 0 mismatches)
TOTAL: 1878 / 2585
```

Exact match to Codex's Section 8 counts, both per-project and in total.

## 9. P0-PART-001 root cause

`canonical_production_view.py::_empty_structure_entry` seeded `_participant_codes = [code] if (code and _home_is_party) else []` **unconditionally for every structure type**, before the component-specific claiming filter ran. `_home_is_party` is a treaty-only signal (`treaty_slug in multilateral set OR len(coproduction_partners) < 2`); for `component_relocation`, `coproduction_partners` is always empty, so `_home_is_party` is always `True` — meaning the primary jurisdiction (`code`) was seeded regardless of whether its OWN segment claims an incentive. For a project whose primary jurisdiction is a real, stated-location-only segment (`claims_incentive=False`, `program_slug=None`), the primary survived in the served participant list purely because of the unconditional seed — the subsequent claiming-segment loop only ever *adds* to this seed, it never removes from it. This is the exact defect the prior P0-2 fix (2026-09-04) left in place: it correctly added missing claiming segments but never revisited the seed itself.

Verified all other structure families' participant construction before editing (per the required investigation): `single_country`/`full_relocation` use the unconditional `[code]` seed only, with no claims filter applied at all (intentionally — the audit's own prior finding, "already correct, do not reopen," since their segments can carry real but incidental out-of-jurisdiction accounts that aren't the structure's own identity); `multi_program` and `treaty_coproduction` use the same seed plus `coproduction_partners`, unaffected by this fix since it only touches the `component_relocation` branch.

## 10. P0-PART-001 fix

`_empty_structure_entry`'s `component_relocation` branch now derives `_primary_claims` — whether `code`'s own segment (if any) has `claims_incentive is True` — and seeds `_participant_codes = [code] if (code and _home_is_party and _primary_claims) else []`, before applying the identical claiming-segment loop as before (unchanged). This is structure-type-specific participant construction (the task's own preferred approach over a generic seed with post-hoc subtraction): the `else` branch for all other structure types keeps the exact original unconditional seed, byte-identical to before. No jurisdiction code, project ID, or project name is referenced in the fix. Non-claiming geography (including a non-claiming primary) remains fully visible in `trace["segments"]` — nothing is deleted; only its membership in the canonical PARTICIPANT list is gated.

## 11. P0-PART-001 full component corpus verification

Re-ran the identical corpus sweep after the fix, across all 14 optimizer-ready projects, all 2,585 current `component_relocation` structures:

```
10 Double Zero:         0 / 250
5 LBS OF PRESSURE:      0 / 0
Bad Hombres:            0 / 135
Baron Samedi:           0 / 203
F#K Valentine's Day:    0 / 206
Going Places:           0 / 221
Interference:           0 / 205
Lips Like Sugar:        0 / 232
Rocky Mountain:         0 / 258
The Cure:               0 / 140
The Little Utopia:      0 / 134
The System:             0 / 203
Twilight of the Dead:   0 / 154
Underwater:             0 / 244
TOTAL: 0 / 2585
EXTRA_NONCLAIMING_PARTICIPANTS: 0
MISSING_CLAIMING_PARTICIPANTS: 0
DUPLICATE_PARTICIPANT_ROWS: 0
BY_TYPE_TOTAL: {'full_relocation': 1730, 'multi_program': 13, 'component_relocation': 2585, 'treaty_coproduction': 325, 'single_country': 6}
```

**0 mismatches, 0 extra non-claiming participants, 0 missing claiming participants, 0 duplicates across the entire current corpus** — exactly matching Codex's own corpus totals (2,585 component rows; 1,730/13/325/6 for the other families). All previously-contaminated 1,878 rows across the nine named projects are corrected. Independently confirmed the previously-existing four-project subset test (`test_component_relocation_participants_include_the_routed_destination`) still passes — FVD and LU's own components already had claiming primaries, so this fix produces no change there.

## 12. Treaty regression

No treaty-pricing code was modified. Focused fixture regression (`test_copro_conditional_pricing_bridge.py`): 14/14 passed, unchanged.

Real runtime sweep across the full corpus (`.claude/scratch/repro_p0.py treaty`):

```
TOTAL_TREATY_ROWS: 325
SOLVABLE(non-UNRESOLVED_FACTS with conditional_scenario): 282
FULLY_PRICED: 123
NON_CONSERVING: 0
```

Exact match to Codex's Section 9 figures (325 total, 282 solvable, 123 fully priced, 0 non-conserving, 0 double-counted). P0-3 conservation is unaffected by either fix in this task.

## 13. Program-consumption regression

No program discovery/authority-coverage code was modified. Lightweight regression (`.claude/scratch/repro_p0.py program`, calling `program_onboarding_conformance.all_optimizer_visible_program_slugs()` directly):

```
OPTIMIZER_VISIBLE_PROGRAM_COUNT: 125
```

Matches Codex's Section 4 count exactly. Codex's full program audit (0 `SILENTLY_EXCLUDED`, 100 `EXECUTED_AND_PRICED`, etc.) was not reopened or re-derived, per the task's explicit instruction that a lightweight count check suffices.

## 14. Canonical gates

**Canonical Budget Integrity Gate** (unaffected, untouched code path): re-run as a regression check — PASS, all four locked-corpus budgets, all 16 invariant families.

**Non-Globe Canonical Integrity Gate**: Codex's Section 23 explicitly found the pre-existing `SELECTION` and `PARTICIPANTS` invariants insufficient — `SELECTION` compared `canonical_selected_structure_id` only against this same call's own served rank 1 (both derived from the identical `comparable` pool, so they could never diverge from each other and missed all nine real divergences); `PARTICIPANTS`'s expected-set logic itself unconditionally seeded `primary_jurisdiction`, reproducing rather than detecting P0-PART-001.

Both strengthened narrowly, in the existing gate (no parallel framework):
- **SELECTION** now additionally fetches the persisted `Project` row and the evaluator's own `econ_status["top_result"]` (from `evaluate_project`, i.e. `_summarize_evaluation`), and asserts all three of {evaluator top, persisted `leading_structure_id`, served `canonical_selected_structure_id`} are identical or all `None` — a real cross-source check, not a self-comparison.
- **PARTICIPANTS**'s expected-set for `component_relocation` is now derived purely from `{seg for seg with claims_incentive is True}` — the unconditional `{primary_jurisdiction}` seed was removed entirely from the gate's own expected-set computation.
- **TREATY ALLOCATION**: unchanged, per the task's explicit instruction — re-run only as a regression.

Full corpus re-run after both strengthenings:

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

CANONICAL INTEGRITY GATE (13 non-Globe invariants): PASS — GLOBE remains separately DEFERRED BY SEQUENCING
```

All 14 projects PASS with the STRENGTHENED assertions actually exercising cross-source comparison — this is real proof, not a gate that would have passed even with the defects present (as the pre-fix versions would have).

## 15. Full suite

`cd frametax2/backend && PYTHONPATH=. python3 -m pytest tests/ -q`, run once:

```
4753 passed, 3 skipped, 12 warnings in 349.25s (0:05:49)
```

0 failures. No frontend source was changed in this task (only backend Python files), so the frontend suite was not re-run, per the task's own conditional instruction.

## 16. Engine version / freshness decision

Neither fix required an `ENGINE_VERSION` bump. Reasoning, evaluated separately for each:

- **P0-SEL-001**: `_summarize_evaluation` recomputes `top_pair` fresh, in pure Python, on every call to `evaluate_project` — it is not itself a cached/fingerprinted value the way `StructureCalculationResult` rows are (only the underlying priced rows are engine-version-gated, at line ~3716, unchanged). The corrected logic self-applies immediately on the very next evaluation of any project, with no stale state possible. Confirmed live: Section 7's verification ran `evaluate_project()` fresh for all 14 projects and every one immediately reflected the fix with no separate migration step.
- **P0-PART-001**: `canonical_production_view.build_production_and_structures` computes `participants` fresh from `calculation_trace_json["segments"]` on every call — there is no separate cached "participants" field anywhere in `StructureCalculationResult`. The corrected logic applies immediately to every served request, confirmed live in Section 11's full-corpus sweep.

Per the task's explicit instruction not to bump the version mechanically when the architecture already recomputes correctly, `ENGINE_VERSION` remains `canonical-1.53.0` (unchanged from the prior P0 remediation).

## 17. Known P1 not fixed

**P1-REJ-001** (component threshold-failed attempts have explicit transient blockers but no persisted/served per-instance rejection row) is explicitly out of scope for this task, per its own instruction. Recorded here as: **KNOWN P1 — DEFERRED TO FINAL CLOSEOUT AFTER P0 ACCEPTANCE.** Not touched, not investigated further, no code changed toward it. The same applies to Codex's other named P1s (`P1-FRESH-001`, `P1-CONF-001`, `P1-GATE-001`) — none were in this task's scope and none were modified.

## 18. Files changed

**Source (2):**
- [`frametax2/backend/app/services/canonical_evaluation.py`](../../frametax2/backend/app/services/canonical_evaluation.py) — P0-SEL-001: no-baseline branch of `_summarize_evaluation` now returns `top_pair = None` instead of `priced[0]`.
- [`frametax2/backend/app/services/canonical_production_view.py`](../../frametax2/backend/app/services/canonical_production_view.py) — P0-PART-001: `_empty_structure_entry`'s `component_relocation` seed now checks the primary's own `claims_incentive` before including it.

**Gate (1):**
- [`frametax2/backend/scripts/canonical_integrity_gate.py`](../../frametax2/backend/scripts/canonical_integrity_gate.py) — SELECTION strengthened to cross-check evaluator/persisted/served; PARTICIPANTS expected-set no longer unconditionally seeds the primary.

**Tests (2):**
- [`frametax2/backend/tests/test_canonical_selection_consistency.py`](../../frametax2/backend/tests/test_canonical_selection_consistency.py) — added the nine-project no-baseline regression and a full-corpus evaluator/persisted/served agreement test.
- [`frametax2/backend/tests/test_canonical_scenario_participants.py`](../../frametax2/backend/tests/test_canonical_scenario_participants.py) — added the nine-project, corpus-wide P0-PART-001 exact-identity regression.

**Docs (1):** this file.

No other file was modified. No frontend, treaty, program-discovery, MFNI, Globe, or SA-2 code was touched.

## 19. Commit / push / remote

Shared-branch-safe delivery: working tree inspected fresh immediately before staging; numerous unrelated untracked files (AG's MFNI/secondary-research scripts) confirmed present and left untouched. Staged exactly the 6 intended files by explicit path — never `git add .`/`git add -A`. Staged diff verified to match exactly those 6 paths before committing.

- **Branch:** `claude/audit-frametax-features-NZcX5`, repo `surajgohill-oss/Frametax`.
- **Commit / push / remote verification:** recorded in the chat response after this artifact was committed (commit hash, push confirmation, and `local HEAD == remote HEAD` check).
- No history rewrite performed. No unrelated concurrent-agent work was staged, modified, or lost.

## 20. Final verdict

All required conditions verified true:
1. P0-SEL-001 fixed generically (Section 6) — no project/jurisdiction exception.
2. All 14 current optimizer-ready projects have zero selection divergence (Section 7).
3. No project persists a non-comparable `leading_structure_id` (Section 7).
4. P0-PART-001 fixed generically (Section 10) — no project/jurisdiction exception.
5. Full current component corpus (2,585 rows) has zero participant mismatches (Section 11).
6. Non-claiming geography remains preserved in trace/segments (Sections 9, 11).
7. Treaty conservation remains clean — 0 non-conserving, 0 double-counted (Section 12).
8. Program-universe consumption remains intact — 125 optimizer-visible programs (Section 13).
9. Canonical gates pass — both Budget Integrity and strengthened Non-Globe Integrity gates, 14/14 projects, 13/13 invariants (Section 14).
10. Final backend suite passes — 4753 passed, 3 skipped, 0 failed (Section 15).
11. Runtime/persistence/served proof exists for both fixes (Sections 7, 11 — real DB-backed evaluation, not unit tests alone).
12. No unrelated scope was modified (Sections 3, 18, 19).

**OPTIMIZER FINAL P0 REMEDIATION — ACCEPTED**

**GO_FOR_CODEX_FINAL_P0_DELTA_REAUDIT**
