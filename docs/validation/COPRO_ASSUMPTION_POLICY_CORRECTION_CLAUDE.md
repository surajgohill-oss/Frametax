# CORRECT_COPRO_ASSUMPTION_AND_PERSONNEL_POLICY

Workstream: `CORRECT_COPRO_ASSUMPTION_AND_PERSONNEL_POLICY`
Repository: `~/cineglobe-frametax` (worktree `/Users/Suraj/cineglobe-frametax-claude-remediation`)
Branch: `claude/audit-frametax-features-NZcX5`
Required starting HEAD: `9e726262e46ca835dd9249dcde462a12efea6033` (confirmed before any edit)

## 1. What the prior status (`COPRO_FACT_WIRING_COMPLETE`) got wrong

The prior workstream (`PRODUCTION_RECORD_TO_OFFICIAL_COPRO_OPTIMIZER_WIRING`, commit `9e72626`)
built a real, correctly-optional `PersonnelRequirement` gate and wired real
`ProjectPerson`/`TalentProfile` facts into it. That mechanism was — and
remains — correct: it never becomes a universal writer/director rule, it
never blocks on a missing rule, and it correctly credits/questions/fails
personnel facts exactly the way the treaty's own (test-proven) rule says to.

Two real defects survived that commit, plus one avoidable but misleading
reporting gap:

1. **Phantom `RULE_DATA_INCOMPLETE` label (Requirement 3).** When a treaty
   carries no researched `personnel_requirement` (every real treaty today),
   `evaluate_treaty_personnel_gate()` returned `QUAL_RULE_DATA_INCOMPLETE`.
   That state means "a real rule exists but this project's own facts can't
   resolve it yet" — the wrong meaning here, since there is no rule at all.
   It never blocked anything (the gate is only consulted when
   `personnel_requirement is not None`), but it surfaced as noise on every
   one of a project's ~25+ treaty opportunities, as if each carried its own
   open data question about the CURRENT project, when none of them do.
2. **The personnel gate was wired into DISCOVERY but not into CONDITIONAL
   PRICING.** `_build_conditional_bilateral_scenario()` — the existing,
   pre-existing-before-either-workstream mechanism that already converts an
   unresolved treaty opportunity into a priced conditional structure — never
   received `personnel_requirement`/`personnel_attachment_facts` at all. A
   treaty whose personnel clause IS researched in the future could have been
   conditionally priced around a genuinely unresolved or failed personnel
   question. Purely latent today (no real treaty has a rule yet), but a real
   structural gap.
3. **Misleading reporting.** The prior FINAL response's
   `CONDITIONAL_LEVERS_GENERATED: 0` conflated "personnel-gate levers" (correctly
   zero — no real treaty has a rule to generate a lever from) with the
   ENTIRELY SEPARATE, pre-existing `_build_conditional_bilateral_scenario()`
   mechanism, which was — and remains — actively generating real, priced
   conditional structures for Little Utopia and the other three projects.
   That existing mechanism already implements almost the entirety of the
   OPTIMIZER ASSUMPTION POLICY for contribution shares; it was simply never
   surfaced or verified in the prior report.

## 2. What this workstream actually changed

### 2a. Personnel gate: `NOT_APPLICABLE`, not `RULE_DATA_INCOMPLETE`, when no rule exists

`app/calculators/canonical_role_qualification_bridge.py`,
`evaluate_treaty_personnel_gate()`: when `requirement is None`, now returns
`QUAL_NOT_APPLICABLE` (already an existing, shared state in
`canonical_qualification_result.py` — no new vocabulary invented) instead of
`QUAL_RULE_DATA_INCOMPLETE`. `missing_facts` is now empty in this branch
(there is no missing PROJECT fact — the gap is in the treaty registry, not
this project's own data). Purely a label correction: the surrounding
blocking logic in `canonical_treaty_bridge.py` already guarded every
blocking check with `personnel_requirement is not None`, so this treaty's
own resolution_state/is_eligible math is byte-identical before and after —
verified by the full regression suite (below) and by the fact that every
real treaty's `total_incentive_value_usd`/`true_net_cost_usd` baseline is
unchanged (Section 5).

### 2b. Personnel gate now reaches conditional pricing too

`app/services/canonical_evaluation.py`, `_build_conditional_bilateral_scenario()`:
gained an optional `personnel_attachment_facts` parameter; internally reads
`treaty.personnel_requirement` from the SAME registry row it already fetches
(no second lookup) and threads both into the same
`evaluate_bilateral_coproduction_opportunity()` call the discovery loop
already uses. Both call sites in `evaluate_project()` (home-anchored and
non-home-anchored bilateral loops) now pass the project's real
`role_attachment_facts`. A treaty with a real, researched personnel rule
now cannot be conditionally priced around a genuinely unresolved or failed
personnel question — proven by
`test_personnel_requirement_is_consumed_by_conditional_pricing_not_only_discovery`
and `test_explicit_locked_personnel_contradiction_blocks_the_conditional_scenario`
(Section 4). When `personnel_requirement is None` (every real treaty
today), this is a no-op — byte-identical to the pre-workstream behavior.

### 2c. `ENGINE_VERSION` bumped `1.57.0` -> `1.58.0`

Forces every cached row to recompute under the corrected label/wiring; no
prior-version row is ever silently reused as current.

### 2d. DB residue from the prior workstream's own test cleaned up

The prior workstream's `test_served_treaty_structure_exposes_the_personnel_gate_contract`
test called the REAL `evaluate_project()` with a synthetic treaty
temporarily registered in the in-memory `te._BILATERAL` dict. Its `finally`
block removed the in-memory registry entry but never deleted the REAL
`ProductionStructure`/`StructureCalculationResult` rows that
`evaluate_project()` persisted to the real database, referencing a treaty
slug (`mu-gb-personnel-served-test-bilateral`) that no longer exists in the
registry once the test ends — permanent orphan rows. This workstream:
  - deleted the 3 orphaned `ProductionStructure` rows (and their 1 remaining
    `StructureCalculationResult` row) already sitting in the real database
    for Little Utopia before any new work began;
  - fixed the test's own `finally` block to delete any rows it creates by
    name, every time, going forward (Section 4).

## 3. The pre-existing conditional-pricing mechanism, verified live

`_build_conditional_bilateral_scenario()` predates BOTH this workstream and
the prior one. It already implements the OPTIMIZER ASSUMPTION POLICY's
contribution-share provision correctly:
  - it reads the treaty's own REAL, registered `majority_min_pct`/
    `minority_min_pct` thresholds (never an invented number);
  - it classifies the resulting split as `assumption_fact_classification:
    "PROPOSED_CHANGE"` — this codebase's existing, pre-established
    vocabulary entry (`FACT_PROPOSED_CHANGE`,
    `canonical_opportunity_bridge.py`) for "a producer-actionable
    assumption, not a verified fact." This IS the policy's own "disclosed as
    MODELED_ASSUMPTION, not VERIFIED_FACT" requirement — no new
    classification constant was needed or invented;
  - it prices the resulting structure through the SAME canonical kernel
    every ordinary candidate uses, generating a real
    `conditional_incentive_usd`/`conditional_npc_usd` and a
    `net_benefit_vs_baseline_usd`;
  - it fails closed ONLY for a genuine cultural/legal hard blocker (an
    explicit, unresolved treaty-mandated cultural test) — exactly the
    policy's own stated exception.

Verified live against Little Utopia's real, unmodified treaty registry
(before any code change in this workstream, to establish it was already
working): of Little Utopia's 26 real `treaty_coproduction` rows at the time
of inspection (25 real + 1 orphaned synthetic-test row, since removed), 22
resolved `CONDITIONAL_PROJECT_FACT_DEPENDENT` (a real, priced conditional
structure) and 3 resolved `USER_DECISION_REQUIRED` for an explicit,
correctly-identified cultural-test blocker (`uk-fr-bilateral`,
`fr-de-bilateral`, `fr-be-bilateral` — each require a cultural test this
engine cannot solve numerically). Zero of the 25 real rows were blocked by
any producer-controlled item (local PSC, banking, crew, entity formation,
application timing, or local-partner attachment) — the ONLY category of
blocker present is the policy's own permitted exception.

## 4. Tests added

All in `tests/test_production_record_copro_wiring_claude.py` (appended to
the existing 15-test file from the prior workstream; 2 of the prior 15 were
updated for the `NOT_APPLICABLE` label change, not removed):

- `test_no_researched_requirement_is_not_applicable_never_a_phantom_incomplete_gate`
  (renamed/rewritten from `test_no_researched_requirement_is_rule_data_incomplete_never_blocking`) —
  proves the gate now returns `QUAL_NOT_APPLICABLE`, never
  `QUAL_RULE_DATA_INCOMPLETE`, and never a missing-fact claim, when no rule
  is registered.
- `test_backward_compatible_no_personnel_requirement_supplied_by_caller` —
  updated to assert `QUAL_NOT_APPLICABLE` for the same reason.
- `test_missing_contribution_shares_default_to_a_priced_modeled_assumption_not_a_permanent_block` —
  proves a treaty with NO ownership facts on file still solves a real,
  treaty-derived minimum split, reaches a priced/eligible conditional
  scenario, and discloses it as `PROPOSED_CHANGE` (modeled assumption), not
  a verified fact.
- `test_personnel_requirement_is_consumed_by_conditional_pricing_not_only_discovery` —
  proves a confirmed, satisfying personnel fact now reaches the conditional
  scenario path (previously silently ignored there).
- `test_explicit_locked_personnel_contradiction_blocks_the_conditional_scenario` —
  proves a real, confirmed WRONG personnel fact (a genuine locked
  contradiction, the policy's own carve-out) correctly keeps the
  conditional scenario at `NOT_FEASIBLE`/`INELIGIBLE`, never silently priced
  around.
- `test_coproduction_contribution_fact_change_invalidates_the_fingerprint` —
  proves the pre-existing `coproduction_facts` fingerprint parameter is live
  (a majority/minority contribution fact converting an assumption into a
  verified fact changes the fingerprint and forces recompute).
- `test_missing_personnel_records_never_block_single_jurisdiction_pricing_or_copro_discovery` —
  end-to-end, real-DB proof against Bad Hombres (zero `ProjectPerson`
  rows): a fresh evaluation still produces single-jurisdiction priced
  candidates AND still discovers real treaty_coproduction opportunities,
  every one of which resolves `personnel_gate_state == QUAL_NOT_APPLICABLE`
  (never a blocking state).

`test_served_treaty_structure_exposes_the_personnel_gate_contract`'s own
`finally` block was extended to delete the `ProductionStructure`/
`StructureCalculationResult` rows it creates, by name, every run (Section
2d) — the residue fix, applied at the source of the leak.

## 5. Regression results

```
PYTHONPATH=. python3 -m pytest -q \
  tests/test_production_record_copro_wiring_claude.py \
  tests/test_canonical_role_qualification_bridge.py \
  tests/test_treaty_coproduction_wiring.py \
  tests/test_canonical_treaty_bridge.py \
  tests/test_canonical_stack_bridge.py \
  tests/test_claude_global_optimizer_p0_remediation.py \
  tests/test_canonical_economics_integrity_repair.py \
  tests/test_copro_conditional_pricing_bridge.py \
  tests/test_copro_conditional_pricing_data_reconnection.py \
  tests/test_copro_qualification_wiring.py \
  tests/test_coproduction_optimizer_preservation.py \
  tests/test_treaty_coproduction.py
```
Result: **264 passed, 0 failed, 0 timeout** (27.6s, foreground).
`tests/test_production_record_copro_wiring_claude.py` alone: **20 passed**
(15 prior + 5 new, 2 updated for the label fix).

## 6. Four-production fresh runtime, verified against the real DB

See `docs/validation/FOUR_PROJECT_COPRO_ASSUMPTION_RUNTIME_CLAUDE.csv` for
the full per-project table. Summary:

- **Every real treaty's `personnel_gate_state` now reads `NOT_APPLICABLE`**
  (was `RULE_DATA_INCOMPLETE`) across all 4 projects — confirmed live, not
  just in the unit tests.
- **22 of 25 (or 27 for F#K Valentine's Day, which also has 2 multilateral
  entries never wired into the personnel gate at all — unchanged, out of
  scope) real treaty opportunities per project resolve to a real, priced
  `CONDITIONAL_PROJECT_FACT_DEPENDENT` conditional structure** — confirmed
  live for all 4 projects, not just Little Utopia.
- **The remaining 3 (or 3, for F#K Valentine's Day too) resolve
  `USER_DECISION_REQUIRED` for an explicit, correctly-identified cultural-
  test blocker** (`uk-fr-bilateral`, `fr-de-bilateral`, `fr-be-bilateral`) —
  the policy's own permitted exception, never a producer-controlled item.
- **Every baseline (`is_baseline=True`) row's economics are byte-identical**
  to every prior workstream's frozen values: Little Utopia
  573059.70/3791333.30, F#K Valentine's Day 1445659.84/3072027.16, Bad
  Hombres 596910.25/1885112.75, Lips Like Sugar 3459278.90/8524375.10.
- **Bad Hombres's and Lips Like Sugar's served winner
  (`project.leading_structure_id`) is unchanged** — still their own
  baseline program, PRICED, at the exact same incentive/NPC. Little
  Utopia's and F#K Valentine's Day's `leading_structure_id` is `None`
  both before and after this workstream (no candidate clears
  `VERIFIED_RECOMMENDATION` for either — a genuinely pre-existing state,
  unrelated to and unchanged by this workstream).
- **Little Utopia's real, confirmed Production Record facts** (writer Clara
  Salaman GB, director Kim Farrant AU, producers Rachel Winter/Max Botkin
  US, all `is_confirmed=True`) reach every treaty opportunity's discovery
  AND conditional-pricing evaluation call — confirmed by the personnel gate
  being consulted (state `NOT_APPLICABLE`, correctly non-blocking) on all
  25 real entries, and by the synthetic-treaty test proving the GATE ITSELF
  correctly reaches `QUALIFIES` for the confirmed GB writer the moment a
  rule exists to consume it.
- **No real treaty pathway was invented and no official co-production
  status was automatically awarded** for Little Utopia or any of the other
  3 projects — every real treaty still correctly shows
  `personnel_gate_state=NOT_APPLICABLE` (no rule exists to award anything
  from), and the 3 genuine cultural-test blockers remain genuinely
  unresolved, not silently cleared.

## 7. What remains a genuine, disclosed hard blocker (not fixed, not fixable without research)

- `uk-fr-bilateral`, `fr-de-bilateral`, `fr-be-bilateral` (present for
  Little Utopia, Bad Hombres, and Lips Like Sugar; F#K Valentine's Day has
  its own analogous 3 cultural-test-gated bilateral treaties) each require
  an explicit cultural test pass this engine cannot compute — a genuine
  cultural/legal threshold per the policy's own exception, not a
  producer-controlled assumption. Left unpriced, honestly disclosed with
  `blocking_reason`.
- No real, registered treaty carries a researched `personnel_requirement`
  yet. This requires primary-source treaty research, explicitly out of
  scope for this workstream (`SCOPE EXCLUSIONS: no external research`).
  The mechanism to consume one the moment it is researched is now fully
  wired and proven (discovery AND conditional pricing both), so a future
  research pass needs only to populate `TreatyData.personnel_requirement`
  entries — no further plumbing work.
- F#K Valentine's Day's 2 multilateral treaty_coproduction entries
  (Eurimages / European Convention) still carry `personnel_gate_state=None`
  (never attempted) rather than `NOT_APPLICABLE` — the personnel gate was
  scoped to bilateral treaties only in the prior workstream and remains so
  here; wiring it into the multilateral evaluator is a distinct, additive
  change not required by this workstream's objective and not attempted
  (guardrail: no unrelated refactor).

## 8. Guardrails honored

No external research, no MFNI/jurisdiction cleanup, no UI redesign, no
reinvestment work, no AG/Codex work, no unrelated refactor. Every command
ran foreground, well under the 180s cap (longest: 27.6s regression batch).
No background jobs, no passive waiting. No test skipped or weakened. No
commit made while a process was still running.
