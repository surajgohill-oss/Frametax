# CineGlobe Project Rules

## Canonical knowledge before research

This repository has already completed broad worldwide incentive research. Co-production, stacking, component-routing, and optimizer work must begin from the current canonical knowledge and must not restart jurisdiction research by default.

### Required workflow

1. Search the canonical runtime registries, tests, capability ledger, and Git history before using external research.
2. Classify an apparent gap as exactly one of:
   - `CANONICAL_AND_CONSUMED`
   - `EXISTS_BUT_DISCONNECTED`
   - `CANONICAL_DATA_MISSING`
   - `OPTIMIZER_CAPABILITY_MISSING`
   - `PROVENANCE_INCOMPLETE_EXISTING_RECORD`
3. For co-production/stacking work, solve connection, eligibility, combination, and ranking defects from existing data first. Do not reopen a worldwide jurisdiction audit or use provenance cleanup as a substitute for the requested optimizer exercise.
4. External research is permitted only when the user explicitly requests it or when one specific, decision-critical proposition is absent from every canonical registry and recoverable repository artifact. Research must be bounded to that proposition; never restart the country/program universe.
5. `PROVENANCE_INCOMPLETE_EXISTING_RECORD` means the rule already exists and was previously researched but its retained primary-source metadata is incomplete. It does not block development of generic co-production/stacking mechanics, but it **does block final production acceptance for that program while the program remains priceable**. Before final acceptance, every such program must become either `AUTHORITY_VERIFIED_PRICEABLE` or `AUTHORITY_UNRESOLVED_NON_PRICEABLE`.
6. Validation documents, model reports, comments, and free-text notes are evidence/recovery inputs only. They are never runtime truth. If valid doctrine is found there, migrate it into the appropriate canonical owner and add a recurrence test.
7. Do not create a parallel registry, optimizer, or calculation path. Extend the existing canonical owner and served bridge.
8. Do not treat historical population counts such as 71, 84, or 121 as completion truth. Derive counts from the current live canonical registry and explain any movement by program and structure type.
9. Candidate-count changes must be fully attributed. For a recovered program, identify each added `full_relocation`, `component_relocation`, stack, or co-production candidate and prove why it exists.
10. Broad research, broad validation, and provenance backfill require a separate explicit task. A task may explicitly commission a fixed residual inventory; when it does, that inventory is frozen at task start and must not expand into another worldwide audit.

### Final authority-safety gate

**Two-axis correction (2026-09-02):** economic determinism and structured-provenance completeness are separate axes. A program that already carries a real, previously-adjudicated `RateRule` (rate/base/cap/eligibility mechanics independently established, whatever its citation tier) prices deterministically in everyday optimizer candidacy — discovery, stacking, ranking, and every served comparison — even while its structured-provenance citation trail is still incomplete. Provenance incompleteness is a KNOWLEDGE-QUALITY gate on **production acceptance/sign-off**, never a silent economic block on ordinary use. This corrects an earlier reading of this section that conflated the two and blocked 31 real, rate-bearing programs from all economics on a citation-tier gap alone (see `app/data/authority_coverage_registry.py`'s own two-axis doctrine comment for the full accounting).

1. No program with `PROVENANCE_INCOMPLETE_EXISTING_RECORD` may be marked `RECOMMENDED` or treated as knowledge-verified in a **production-accepted build** (sign-off on a residual-closure pass). This does not withhold its deterministic incentive/stacking economics from everyday candidacy — see workflow rule 5, which already states this distinction: provenance-incomplete "does not block development of generic co-production/stacking mechanics... while the program remains priceable."
2. A residual program has only two acceptable terminal dispositions for **production acceptance**:
   - `AUTHORITY_VERIFIED_PRICEABLE`: every calculation-driving proposition used at runtime is supported by current primary statute/regulation or official administering-agency guidance and stored as structured provenance.
   - `AUTHORITY_UNRESOLVED_NON_PRICEABLE`: authoritative support could not be completed. The program remains visible, discloses the gap as an explicit warning on every served result, and — per the two-axis correction above — still prices deterministically and may enter incentive/NPC/stack economics in everyday candidacy on the strength of its retained real rate data; what it may NOT do is reach production acceptance, be marked `RECOMMENDED`, or be represented as knowledge-verified while in this state.
3. “Reduce residuals to zero” means zero partially supported programs remain in this state at **production acceptance**. It does not mean fabricating positive verification for every program, and it does not mean withholding real economics from a program while its provenance is still being completed.
4. Secondary sources may locate an official source but may not independently justify treating a program as `AUTHORITY_VERIFIED_PRICEABLE` or `RECOMMENDED`.
5. Missing effective dates, inaccessible official pages, conflicting authority, or incomplete rate/base/cap/eligibility mechanics must be recorded precisely. If the missing fact affects economics or eligibility, quarantine the program rather than assume it.
6. The provenance classifier and acceptance tests must inspect substantive fields and source authority, not merely test whether a `SourceProvenance` object is non-null.
7. Overall knowledge-base acceptance is forbidden while the count of priceable partial-provenance programs is greater than zero.

### Persistence and stopping rule for a commissioned closure pass

When a task explicitly commissions a fixed authority-residual closure:

1. Do not stop after inventory, diagnosis, partial batches, access failures, or a report of remaining work.
2. Process every frozen record to one of the two terminal dispositions above.
3. If an official source is unavailable after the task's bounded retrieval/escalation sequence, classify the record `AUTHORITY_UNRESOLVED_NON_PRICEABLE`, implement the disclosure (the record still prices on its retained real rate data; production acceptance remains blocked — see the two-axis correction above), test it, and continue to the next record.
4. One blocked source never blocks the whole pass and never justifies returning early.
5. Do not ask the user to decide routine per-record dispositions. Apply the fail-closed rule.
6. Completion requires runtime enforcement, full inventory accounting, regression tests, the requested commit/push, and remote verification—not merely an MD/JSON report.

### Canonical data ownership map

The knowledge base is consolidated by domain, not forced into one oversized file:

| Domain | Canonical owner / served entry |
|---|---|
| Program identity and rate doctrine | `backend/app/data/executable_jurisdiction_registry.py`, populated by `backend/app/data/program_rate_rules_worldwide.py` and resolved only through `backend/app/data/program_rate_rules.py` |
| QPE category and territorial treatment | `backend/app/data/program_spend_rules.py` |
| Program qualification, timing, compliance, and monetization facts | `backend/app/data/program_requirements.py` |
| Role/nationality and cultural qualification | `backend/app/data/cultural_qualification_model.py` and `backend/app/data/cultural_point_tables.py`, consumed through `backend/app/calculators/canonical_role_qualification_bridge.py` |
| National/cultural status | `backend/app/data/national_cultural_status.py` |
| Treaty and official co-production frameworks | `backend/app/calculators/treaty_engine.py`, consumed through `backend/app/calculators/canonical_treaty_bridge.py` |
| Stacking compatibility and adjustments | `backend/app/optimization/stacking_rules.py`, consumed through `backend/app/calculators/canonical_stack_bridge.py` |
| Economic-candidacy exclusions | `backend/app/data/authority_coverage_registry.py` |
| Structured authority coverage classification | `backend/app/data/program_authority_provenance.py` |
| Served project evaluation and admission | `backend/app/services/canonical_evaluation.py` |
| Served publication/view | `backend/app/services/canonical_production_view.py` |
| Historical decisions and deferred work | `docs/architecture/CAPABILITY_LEDGER.md` — documentary only, never runtime truth |

The recurrence guard is `backend/tests/test_canonical_knowledge_consolidation.py`. Any new canonical program or recovered doctrine must resolve through the existing rate/qualification/served path, carry the best recoverable structured provenance, and remain excluded from deterministic recommendation while required eligibility facts are unresolved.

### Mandatory hard timeout / anti-loop rule

Every command, query, or source-retrieval step run in service of a task has a hard wall-clock ceiling, enforced by a real process alarm/watchdog (e.g. the harness's own process-level timeout, or `SIGALRM`/`subprocess` timeout) — never an output-yield or "still producing text" heuristic, which does not detect a genuinely stalled process:

1. An ordinary command, query, or source retrieval: **120 seconds**.
2. An individual test file: **300 seconds**.
3. A focused, grouped test run (multiple related files run together): **900 seconds**.
4. An individual real-project recomputation: **300 seconds**.
5. A push or remote-verification step: **120 seconds**.

On timeout:

- Preserve all logs and all already-made file changes. Never discard work to "start clean."
- Stop only the process this task itself owns. Never terminate an unrelated process or an unrelated database session — inspect (e.g. `ps`, `pg_stat_activity`) before acting, and act only on the row/process this task's own connection or subprocess created.
- Clean up only this task's own database session/connection (e.g. `ROLLBACK`/close a transaction this task opened). Never touch another session's open transaction.
- Mark the specific step `INCOMPLETE` with the elapsed time and last-observed state, and continue with every other, independent task rather than stopping the whole pass.
- Retry at most once, and only after a documented causal correction (a specific, stated reason the retry will behave differently — a fixed query, a narrower scope, a cleared lock). A bare retry with no causal change is not permitted; a second timeout on the same step is final for that step and must be reported as `INCOMPLETE`, not silently retried again.

Never run the full backend test suite as a substitute for the focused/grouped tests above unless a task explicitly requires it — a full-suite run has no place in this hard-timeout schedule and must not be started speculatively "to be safe."

### LONG-RUNNING PROCESS DISCIPLINE

Applies to every test run, evaluation, or other command that can take minutes, and to anything that can read or write an evaluation generation. It is an addition to, and where the two conflict takes precedence over, the anti-loop rule above: the ceilings above are the defaults for ordinary commands; where a task explicitly grants a long-running test/evaluation invocation, **720 seconds (12 minutes) is the maximum** and is fixed before launch. On timeout inside a sequenced run, the sequence stops -- it does not "continue with independent steps".

1. **Never warm up or cold-evaluate a real production for test preparation.** A missing or stale generation of a real production is not a reason to generate it. Use a minimal isolated fixture (a throw-away project created and deleted by the test) or report the dependency as unmet.
2. **Classify before launch.** Before starting any command, state which it is: *synthetic* (isolated fixture only), *reuse-only* (reads an existing generation; can never generate), or *cold evaluation* (may generate rows).
3. **Cold evaluation of Little Utopia, F#K Valentine's Day, Lips Like Sugar, or Bad Hombres requires explicit user authorization** for that specific run. Earlier authorization does not carry over.
4. **Every test/evaluation command has**: one process only; line-buffered/unbuffered output (`python -u`, `PYTHONUNBUFFERED=1`, `pytest -v` so each node is printed as it runs); a hard 12-minute timeout established before launch by a real process alarm (e.g. `perl -e 'alarm shift; exec @ARGV' 720 <command>`, which keeps it a single process) -- never an output-yield heuristic; and visible current file / test / phase.
5. **Never run overlapping regression or evaluation processes.** One at a time, to completion or timeout, on a given database.
6. **At timeout:** terminate the exact process tree this task started (nothing else); verify with `ps` that no child processes remain and with `pg_stat_activity` that no connection of this task remains; record the last completed test and the timed-out node; and **do not restart automatically.** Then report.
7. **No timeout avoidance.** Never use warm-ups, sleeps, repeated monitors/polling, or broad reruns to get around a timeout. A timeout is a finding to explain, not an obstacle to route around.
8. **Green tests are never rerun.** After a fix, rerun only the failed/timed-out node IDs (identified with `pytest --collect-only -q`) and the tests never previously executed. Re-running an entire completed file requires explicit authorization.
9. **Fail closed on the database before any DB-backed test:** assert the exact isolated DB name (e.g. `engine.url.database == "frametax2_claude_optimizer_acceptance_20260919"`) at session start, before any query. A mismatch aborts the run. Never connect to, or modify, shared `frametax2` or a preserved audit database.
10. **Any reader that could load an evaluation generation must use bounded, current-generation SQL** (the generation summary, generation ordinal keyset pages, the retained-ordinal set). Loading an entire generation -- or the whole rejected/unpriced set -- into ORM memory is prohibited, in services, views, routes, and tests alike. An evaluation generation can exceed 500,000 rows.
11. **A phase is not complete** while any of these holds: an unbounded read path, an unexplained timeout, a background process still running, or incomplete test evidence. Report `BLOCKED` with the specific gap instead.


### PERSISTENCE CARDINALITY RULE

**Enumeration cardinality must never define persistence cardinality. Every high-volume status, including PRICED, requires an explicit bounded retention policy before implementation.**

1. The engine may evaluate every candidate; it persists only the bounded decision set CineGlobe serves. Anything outside that set is COUNTED EXACTLY in aggregate groups, never stored one row per permutation.
2. The current policy (`app/services/candidate_retention.py`, `candidate_aggregation.py`, table `evaluation_candidate_aggregates`): detailed rows for the baseline; the global top-100 and per-`structure_type` top-100 PRICED candidates (verified NPC and risk-adjusted NPC, ties by canonical economic identity); the best single/local-stack candidate per jurisdiction; every DOMINATED_WITH_PROOF row and reviewable/opportunity row (each status capped); and any row a retained proof or recommendation references. Everything else is aggregated by (original status, structure family/type, reason class, primary + participant jurisdiction set, program/component/treaty family) with exact count, min/max NPC and incentive, best economic identity, one representative and the retained dominating reference.
3. **Fail-closed invariant** at commit: `candidates generated == detailed rows persisted + sum(candidate aggregate counts)`. Any mismatch, and any retained proof that references a non-retained candidate, rolls the evaluation back.
4. Introducing a new high-volume candidate status, or a new persisted per-candidate row type, requires stating its retention bound in the same change, with a deterministic synthetic full-enumeration-versus-bounded comparison proving the retained set, rankings, economics and accounting are identical before any real production is evaluated.
5. Served surfaces take exact totals from the generation summary + aggregates, rank and recommend from the retained rows, and paginate retained details and aggregate groups -- never every internal permutation.

### CONFIRMED-DEFECT RULE

A confirmed in-scope code defect may not be deferred merely because its fix invalidates acceptance generations. Fix it, bump the engine, and regenerate the bounded acceptance set once. Do not repeat already-passing tests.
