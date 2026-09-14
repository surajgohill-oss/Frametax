PLATFORM: Claude Code — existing canonical CineGlobe repository session
ENGINE: strongest available Claude coding/reasoning engine
EFFORT: High

WORKSTREAM: CINEGLOBE_FINAL_FOUR_ROW_REMEDIATION_CLAUDE

MODE

Implement the remaining defects from Codex's delta-only audit of commit:

`1a4677859efa86927c087d464f4e2507f671bd5b`

Read completely before changing anything:

- `PROJECT_RULES.md`
- `docs/validation/CINEGLOBE_FINAL_FOUR_ROW_ACCEPTANCE_CODEX.md`
- `docs/validation/CINEGLOBE_FINAL_FOUR_ROW_MATRIX_CODEX.csv`
- `docs/validation/CINEGLOBE_FINAL_FOUR_ROW_REMAINING_CODEX.csv`
- `docs/validation/CINEGLOBE_FINAL_FOUR_PROJECT_RUNTIME_CODEX.csv`

OBJECTIVE

Repair all and only the remaining in-scope defects for:

1. `P0-SEL-ALT-001`
2. `P0-NL-001`
3. `P0-ZA-001`
4. `P0-OR-001`

Do not stop after helper changes or passing existing tests. Continue until every independent expected-value, adversarial, migration, concurrency, and real-runtime gate below passes, or until a genuine external blocker is documented with the exact failed operation and evidence. A pre-existing architectural limitation is not an acceptable reason to omit a required formula; make the smallest generic extension needed.

FROZEN EXCLUSIONS

Do not:

- Research jurisdictions again or modify authoritative findings.
- Add/remove/reclassify programs outside the four rows.
- Modify project-specific facts or insert title/ID exceptions.
- Change UI/globe, Script Analyzer, ingestion, MFNI, reinvestment, or location-feasibility logic.
- Re-audit accepted programs or run the full backend suite.
- Merge or force-push.
- Treat candidate construction, a helper-only test, or a skipped test as runtime acceptance.
- Treat projected/scenario/calculation results as approved, allocated, contracted, granted, paid, reserved, or evidenced awards.

STARTUP GATE

1. Fetch without force and record repository, branch, local HEAD, remote HEAD, merge-base, ancestry, and all tracked/untracked worktree changes.
2. Preserve unrelated work exactly. Do not reset, stash, overwrite, delete, or commit it.
3. Confirm `1a46778` and the Codex audit commit are reachable before editing.
4. Identify the actual backend/database and migration head.
5. Work on `claude/audit-frametax-features-NZcX5`; push normally only after all gates pass.

REPAIR A — COMPLETE CONDITIONAL PARTICIPANT AGGREGATION

Replace state-only component/stack/treaty aggregation with one generic structured aggregate that retains, for every participant and claimed program:

- canonical participant/jurisdiction ID;
- canonical program slug;
- qualification state and route;
- missing facts, curable requirements, failed requirements;
- applicable rate, authority, allocation, identity, timing, and administrative gates;
- reasoning/provenance references;
- relocation/normalization dimensions for the actual target.

The aggregate state remains the worst state, but the union of blockers must never be discarded. Conditional-pool admission must prove that the complete retained blocker set is unresolved/curable. One hard authority/legal/identity/retired/superseded participant blocks the whole structure. `None` never proves eligibility. Baseline/alternative distinctness must use stable canonical IDs, never labels; changing only a label cannot create an alternative. A complete eligible alternative enters normal comparable ranking; a conditional never displaces a verified winner.

Required independent tests:

- Component, stack, and treaty fixtures with at least two participants and one hard failure.
- Exact blocker equality, not subset-only assertions.
- FVD Greece+Romania must include Greece `gr_aggregate`, every applicable Romanian/program/allocation gate, and the four RO normalization dimensions.
- Little Utopia Manitoba must disclose the actual `RULE_DATA_INCOMPLETE` reason as a blocker, not only relocation facts.
- Label mutation leaves identity/distinctness unchanged.
- Bad Hombres and Lips Like Sugar verified winners remain unchanged and suppress competing conditionals.

Do not weaken `test_copro_qualification_wiring.py` to select only full single-program shapes. Assert the aggregate contract directly.

REPAIR B — NETHERLANDS CANONICAL AWARD LEDGER

Do not read `StructureCalculationResult` or any candidate/scenario output as a prior award.

Add the smallest canonical, normalized persistence needed for:

- stable production-company legal-entity identity with evidence/provenance state;
- explicit award period/year distinct from `target_shoot_year`;
- exact canonical program slug;
- native-EUR approved/granted award amount;
- award status and evidence/provenance;
- explicit evidenced zero where appropriate;
- transactional uniqueness/locking/reservation semantics sufficient to prevent two concurrent evaluations from both consuming the same remaining EUR3 million cap.

Only qualifying approved/granted ledger states may reduce the cap. A sibling project without award evidence remains unresolved; it does not become zero. Missing/wrong company, period, program, amount, evidence, or status fails conditional/non-priceable. Sum native EUR once; compute EUR remaining; perform one dated EUR→USD conversion. Do not convert stored USD estimates back to EUR.

Expose the canonical identity/award inputs through the established schema/service path rather than a DB-only field no producer workflow can set. Add a migration from the actual head using existing conventions. Existing projects remain null/unknown; no defaults or inferred values.

Required independent tests in an isolated database:

- Same company/period, two actual approved native-EUR awards jointly never exceed EUR3 million.
- Different company, period, or program remains isolated.
- Sibling project with no ledger row is unresolved.
- Explicit evidenced zero is distinct from absence.
- Negative, nonfinite, over-cap, wrong-company, wrong-period, wrong-program, unapproved, and unevidenced rows reject.
- Multiple candidate structures for one project have zero effect on the ledger.
- Reversed/repeated evaluation order is stable.
- Two concurrent database sessions cannot both obtain the full remaining cap; prove with a real transaction test, not sequential local variables.
- Migration upgrade from prior head, fresh-head creation, no-op repeat, downgrade/upgrade, model mapping, and null preservation.

REPAIR C — SOUTH AFRICA QUALIFYING POST/VFX LINE CONSERVATION

The post-only QSAPPE basis must be derived from, or exactly reconciled to, the canonical qualifying register rows—not component labels alone.

Require every contributing row to have stable source-line, project, allocation, participant/jurisdiction, and category identity. Include only `QUALIFIES` Post/VFX rows for the correct project and ZA participant. Excluded, unresolved, memo, duplicate, missing-ID, wrong-project, wrong-participant, and wrong-jurisdiction rows cannot enter the subtotal. If a supplied QSAPPE aggregate is retained, require exact equality with the derived subtotal and an evidence state; smaller as well as larger mismatches reject. Prefer deriving the amount and eliminating the free scalar.

Required literal tests:

- Production-only and zero-post allocations reject.
- A `component=post` line classified as excluded contingency yields QSAPPE/incentive zero and rejects the post-only claim.
- Missing and duplicate `None` IDs reject.
- Smaller and one-cent-larger scalar mismatches reject.
- Exact qualifying post+VFX source-line subtotal pays exactly 25%.
- ZAR25 million cap applies after rate and one project-selected FX conversion.
- General-production branch remains byte-identical.

REPAIR D — OREGON COMPOSITE CONDITIONAL FORMULA

Implement one shared composite disjoint-base result:

`gross = payroll_QPE × 20% + other_Oregon_QPE × 25%`

Apply the USD1 million actual-Oregon-spend threshold once to the combined qualifying Oregon spend, not separately to each component. Derive/reconcile both bases from the canonical qualifying line register. Apply the USD1 million per-individual/company QPE limitation line/payee-wise before the rates; this is not the final award cap.

Then apply, in this order:

1. summed base incentive;
2. evidenced regional multiplier 1.10 when applicable;
3. dated 50%-of-current-fund final project cap.

Bind the USD21.2 million fund amount to a coherent explicit fiscal/effective period and authoritative evidence already in the repository. Correct the impossible `2026-07-01 to 2026-06-30` interval without new research by using the settled evidence's actual recorded period; if the repository does not contain a coherent period, retain conditional/non-priceable cap state and document the missing fact instead of inventing a date. Missing/stale fund data never means unlimited.

Represent application timing, agency discretion/selection, allocation, contract execution, fund availability/current amount, award status, and per-payee compliance as distinct machine-readable gates. Do not bundle them into one boolean. Before all terminal facts, serve provisional formula economics labeled conditional and exclude rank 1. After every fact is independently evidenced, demonstrate the authorized terminal state without bypassing any gate.

Reconcile directly reachable Oregon aliases/parallel records so no runtime/catalog consumer can serve flat 26.2%, 20%/10%, USD750,000 minimum, or USD14 million maximum as the canonical OPIF formula. Do not broaden to unrelated programs. Explicitly model or fail-closed/disclose the Greenlight labor-only interaction so it cannot double-count labor or invent calculation order.

Required independent values:

- USD2,000,000 payroll + USD2,000,000 other = USD900,000 before uplift/cap.
- USD500,000 payroll + USD700,000 other = USD275,000 because total Oregon spend exceeds USD1 million.
- USD1,100,000 payroll + USD100,000 other = USD245,000.
- Regional case multiplies the complete otherwise-allowable amount by 1.10.
- Per-payee limit: exact boundary and one-cent over, with excluded excess never entering either base.
- Missing/stale fund period remains conditional and capped/fail-closed, never unlimited.
- Greenlight affects only the authorized labor base and never duplicates OPIF labor.
- A brand-new generic project reaches provisional Oregon formula economics with no skip; each missing gate is served; full evidence reaches the intended terminal state.

SHARED CORRECTNESS

- Use canonical shared paths; no project/jurisdiction outcome branches in service logic.
- Every calculation-driving identity, ledger revision, line set, gate, amount, evidence state, fund period, and FX choice must enter the fingerprint/cache identity.
- Bump the appropriate engine/schema/version identity when persisted semantics change.
- No stale result may be reused after any relevant ledger or evidence change.
- Preserve current Texas, immutable FX, Dubai identity separation, and all accepted rows.

FOCUSED VERIFICATION ONLY

Run only:

- New independent tests for these four rows.
- Directly affected existing tests.
- Migration tests.
- FX, Texas, alias/authority/import-order controls.
- Serial recomputation of Little Utopia, FVD, Bad Hombres, and Lips Like Sugar.

Do not run the full backend suite.

Expected controls unless a valid shared correction is explicitly attributed:

- Little Utopia: Mauritius; USD573,059.70 incentive; USD3,791,333.30 NPC.
- FVD: Greece; USD1,445,659.84 incentive; USD3,072,027.16 NPC.
- Bad Hombres: `us_nm_film_credit`; USD596,910.25; USD1,885,112.75.
- Lips Like Sugar: `ca_film_30`; USD3,459,278.90; USD8,524,375.10.

TIMEOUT / ANTI-LOOP

Enforce hard wall-clock limits, not output-yield waits:

- Ordinary command: 120 seconds.
- Individual test file: 300 seconds.
- Migration verification: 300 seconds.
- Individual project: 300 seconds.
- Focused group: 900 seconds.
- Push/remote verification: 120 seconds.

On timeout, terminate only the owned process/session, capture elapsed time/log/process state, clean owned DB state, mark that check incomplete, continue independent work, and retry once only after a documented causal correction. Predeclare `PYTHONPATH=.` for backend tests. No indefinite polls, unchanged retries, broad-suite substitution, or stopping while independent work remains.

ACCEPTANCE / STOP CONDITIONS

Do not claim completion unless:

- Every four-row negative and positive oracle above passes.
- No test is skipped.
- The Netherlands concurrency test uses two real sessions and a canonical award ledger.
- Oregon one-call combined formula returns all three literal expected values.
- ZA excluded-line and missing-ID cases reject.
- FVD/LU expose exact complete blocker unions.
- Migration verification passes in a fresh isolated DB.
- Four project controls and focused regressions pass.
- Diff contains only the bounded implementation, migration, focused tests, and one closeout artifact.

If an acceptance item cannot be completed, do not print an accepted gate. Document the exact unresolved item, leave the branch unclaimed, and still finish every independent item not blocked by it.

PUBLISH

Create one closeout artifact:

`docs/validation/CINEGLOBE_FINAL_FOUR_ROW_REMEDIATION_CLOSEOUT_CLAUDE.md`

Commit only task-owned changes with:

`fix: complete final four-row wiring remediation`

Push normally to `origin/claude/audit-frametax-features-NZcX5`. Never force-push. Verify local SHA equals remote SHA and retrieve the closeout plus every changed migration/test artifact from the remote commit.

RETURN SHORT

- status
- four rows closed: x/4
- files changed
- migration result
- focused tests
- four project controls
- commit SHA
- branch
- pushed YES/NO
- remote verified YES/NO
- unrelated work preserved YES/NO
- ready for Codex delta re-audit YES/NO

STOP after the bounded implementation, verification, commit, push, and remote proof. Do not start another phase.

