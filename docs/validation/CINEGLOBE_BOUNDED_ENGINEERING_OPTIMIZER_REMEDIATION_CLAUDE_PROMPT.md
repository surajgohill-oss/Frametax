# CINEGLOBE — BOUNDED ENGINEERING AND OPTIMIZER REMEDIATION

**PLATFORM:** Claude Code — existing canonical CineGlobe repository session

**ENGINE:** Strongest available Claude reasoning/coding model

**EFFORT:** High

**MODE:** Implement, verify, commit, push, and remote-verify without stopping between routine phases

## Objective

Close exactly the seven remaining rows from Codex commit `a8a1d43dfb1f6e5d69d8b4144023515357f42242` and no other work:

1. `P0-FX-001`
2. `P0-NL-001`
3. `P0-TX-001`
4. `P0-ZA-001`
5. `P0-SEL-ALT-001`
6. `P0-OR-001`
7. `P0-AE-001`

Use these controlling artifacts:

- `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_DELTA_ACCEPTANCE_CODEX.md`
- `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_DELTA_REMAINING_CODEX.csv`
- `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_FOUR_PROJECT_CODEX.csv`
- `docs/validation/CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_CROSSCHECK_CODEX.csv`
- `PROJECT_RULES.md`

Treat all prior “six repaired” or “all oracle repairs complete” claims as superseded by this exact seven-row ledger. Do not redo the completed audit. Implement the bounded repairs and prove the observed behavior.

## Startup and repository integrity

1. Confirm the repository is `surajgohill-oss/Frametax` and the current branch is `claude/audit-frametax-features-NZcX5`.
2. Fetch without force. Record local HEAD, remote HEAD, merge-base, and ancestry from `a8a1d43dfb1f6e5d69d8b4144023515357f42242`.
3. If the remote advanced, preserve and integrate non-overlapping work. Do not reset, discard, or overwrite newer work.
4. Record tracked and untracked status. Preserve unrelated changes and existing untracked scripts.
5. Read the four controlling Codex artifacts and the exact production/tests named by their code paths before editing.

## Frozen exclusions

Do not:

- Change MFNI, frontend/UI, Script Analyzer, budget ingestion, project source facts, or program authority dispositions except the explicit Oregon/AE terminal handling below.
- Start global program or jurisdiction research.
- Add a parallel registry, evaluator, pricing engine, ranking path, or cache.
- Invent eligibility, rates, spend, company identity, award-period data, or in-kind relocation values.
- Weaken qualification rules, fail-open behavior, or knowledge/provenance gates to create a winner.
- Treat an unchanged baseline as a new alternative.
- Run the full backend suite; it has a known unrelated stall and is not this task's acceptance gate.
- Modify Gemini or Codex audit artifacts except to add a factual Claude closeout artifact.

Use current canonical owners and served paths only. There must be no project-title, project-ID, or one-program hardcoded exception.

## Repair 1 — canonical FX safety and cache identity

Repair `P0-FX-001` through the existing canonical FX context.

Required behavior:

- The context must be deeply immutable after construction; callers cannot mutate a nested rate mapping.
- Every rate and calculation-driving amount must be numeric, finite, and strictly positive where the economic rule requires positive input.
- Missing, zero, negative, NaN, positive infinity, and negative infinity must return a typed fail-closed result before arithmetic.
- Build one frozen context per evaluation. Do not reread mutable global FX state mid-evaluation.
- The evaluation fingerprint/cache identity must include a deterministic digest of every calculation-driving FX field: complete normalized rate mapping, snapshot date, source, freshness/status, and stale-acceptance state if applicable. Same-date changes to any of those fields must invalidate reuse.
- Preserve previously correct ordinary finite conversions and Malta/Thailand behavior.

Independent tests must use literal arithmetic and directly attempt nested mutation. Include same-date contexts with changed rate, source, and freshness and prove different fingerprints.

## Repair 2 — Netherlands company-period cap

Repair `P0-NL-001` without creating a parallel award ledger.

Required behavior:

- A Netherlands prior-award aggregate is usable only when bound to explicit canonical company identity and award period, with an evidence state.
- Missing/unknown aggregate must remain conditional/non-priceable. It must never mean zero.
- Explicit zero is allowed only with the required identity/period/evidence binding.
- Prior award must be finite and within the authoritative native-currency cap range. Reject negative, NaN, infinities, and over-cap values.
- Apply the remaining native EUR cap before the existing frozen FX conversion and before final incentive capping, in the existing canonical order.
- Two projects bound to the same company and period cannot jointly exceed EUR 3,000,000. A different company or period must not consume that cap.

Tests must instantiate canonical economic inputs for at least two projects, not simulate identity in comments. Compute expected EUR remainder and USD conversion from literals, not the production cap helper.

## Repair 3 — Texas awarded rate

Repair `P0-TX-001` through the existing structured amount/rate fact path.

Required behavior:

- Only a finite awarded rate satisfying `0 < rate <= 0.31` can execute.
- Missing, text-malformed, zero, negative, NaN, positive infinity, negative infinity, and values above 0.31 fail closed before multiplication.
- Valid 24%, 28%, and 31% awards price their exact own rate; do not substitute the ceiling.
- Apply the awarded rate to the existing authoritative QPE basis and preserve all existing Texas qualification gates.

Independent full-pricing tests must cover `-epsilon`, `0`, `NaN`, both infinities, `0.24`, `0.28`, `0.31`, and `0.3100001`, with literal expected incentives.

## Repair 4 — South Africa post-production QSAPPE conservation

Repair `P0-ZA-001` without trusting an arbitrary scalar.

Required behavior:

- Prefer deriving post-production QSAPPE from the canonical classified and routed post/VFX line register.
- If an external/evidenced subtotal is still required, bind it to its evidence state and reconcile it exactly to, or conservatively within, the canonical qualifying allocated post register.
- Enforce finite `0 <= QSAPPE <= qualifying allocated post spend <= allocated/project spend` before applying the rate.
- Prevent duplicate use of the same spend across production QSAPE and post QSAPPE branches where the program rules make them mutually exclusive or otherwise constrain them.
- Keep production and post-only bases distinct and preserve the existing official rate/cap order.
- A USD 1 allocation plus a USD 1,000,000 QSAPPE fact must reject, never return a USD 250,000 executable incentive.

Independent tests must cover exact derived subtotal, zero where legally valid, over-allocation, negative, NaN, infinities, duplicated basis, and the one-dollar/million-fact adversarial case. Expected incentives must be literal arithmetic.

## Repair 5 — LU/FVD distinct alternative selection

Repair `P0-SEL-ALT-001` in the existing canonical evaluation and production-view path.

Required behavior:

- Replace the blanket `is_directly_comparable=is_baseline` treatment with a structured per-candidate completeness decision derived from existing project facts and the existing relocation normalization outputs.
- At minimum, track whether all calculation-driving travel, FX, local-cost, in-kind, spend-allocation, and qualification dimensions required by that candidate are known. Do not assume missing values are zero or not applicable.
- Aggregate qualification across every program slug in a structure. A component structure cannot lose the Greece anchor's unresolved cultural/personnel gate or any other participant gate.
- If a distinct non-baseline candidate is fully priced, fully qualified, and normalization-complete, admit it to the same existing `npc_with_adjustments_usd` objective used for verified ranking.
- A blocked anchor must not suppress an eligible distinct alternative.
- If no distinct eligible alternative exists, preserve no winner and say so. Separately disclose the strongest materially distinct conditional option with its exact missing dimensions and economic difference.
- The unchanged Mauritius/Greece baseline may remain the current anchor, but must never be labeled as newly discovered value or returned as the distinct leading conditional alternative.
- Do not fabricate a relocation, co-production, route, person status, or qualification fact.
- Preserve Bad Hombres and Lips Like Sugar accepted economics exactly unless an attributable authorized shared correction genuinely changes them.

Required real-project checks:

- Little Utopia: determine whether any distinct eligible candidate exists from canonical facts. If none exists, surface the Manitoba review candidate or the then-current strongest distinct conditional using the existing objective, with every missing normalization/qualification dimension. Do not promote it unless complete.
- F#K Valentine's Day: determine whether any distinct eligible candidate exists. If none exists, surface the Greece-anchor/Romania-post review candidate or the then-current strongest distinct conditional. Its aggregate result must retain the Greek anchor qualification gate.
- Bad Hombres: `us_nm_film_credit`, incentive USD 596,910.25 and NPC USD 1,885,112.75 unless a proven shared correction explains a delta.
- Lips Like Sugar: `ca_film_30`, incentive USD 3,459,278.90 and NPC USD 8,524,375.10 unless a proven shared correction explains a delta.

Tests must prove: baseline is not the distinct alternative; a complete synthetic distinct relocation can rank; an incomplete one remains conditional with named gaps; all component program gates aggregate; eligible alternatives are not suppressed; hard failures remain excluded; Bad Hombres/Lips retain accepted results.

## Repair 6 — Oregon terminal acceptance semantics

Close `P0-OR-001` honestly.

First use existing canonical evidence and repository research. If one calculation-driving proposition remains absent, research only the exact Oregon proposition using current official Oregon statute, administrative rules, or administering-agency guidance. Do not expand beyond Oregon OPIF.

Acceptable terminal outcomes:

1. If current primary/official authority establishes the exact program identity, rates and bases, minimum spend, allocation/discretion mechanics, caps/current period, and stacking/assistance treatment, store that authority in the existing canonical provenance owner and permit pricing only through the normal authority gate; or
2. If any calculation-driving proposition remains unresolved after the bounded official-source check, retain `UNPRICEABLE_AUTHORITY_INSUFFICIENT`, disclose the exact unresolved proposition, and formally exclude Oregon from any claim of “12/12 formulaic priced consumption.” A vetoed program cannot count as consumed merely because it constructs a candidate.

Do not lift the veto, borrow secondary evidence, or invent facts to pass a count. Add a test for the selected terminal outcome and correct the acceptance denominator/reporting semantics if outcome 2 applies.

## Repair 7 — AE/Dubai identity and denominator semantics

Close `P0-AE-001` from existing canonical identity and authority records first.

Required behavior:

- Keep Dubai `ae_dpip`/`AE-DXB` distinct from the Abu Dhabi rebate.
- Do not copy Abu Dhabi economics to Dubai.
- Determine whether `ae_dpip` is a real formulaic economic program, a composite/discovery identity, or an identity-control row.
- If existing accepted canonical evidence does not establish a deterministic Dubai rate/base/cap/eligibility chain, classify it explicitly and remove it from the formulaic-priced-consumption denominator. Preserve discovery/disclosure as appropriate.
- Research only one specific Dubai proposition if and only if it is absent from all canonical and recoverable repository evidence and is necessary to choose that terminal classification. Do not start UAE or global research.

Tests must prove distinct Dubai/Abu Dhabi identities, no cross-emirate rate leakage, and an explicit denominator classification. Never report Abu Dhabi consumption as Dubai consumption.

## Independent expected-value and regression gate

Create or update focused tests so every failure above would fail against commit `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9` and pass only after the corresponding repair. Expected values must be literal arithmetic or a separate test oracle; do not call the production helper being tested to create the expectation.

Run DB-touching project recomputations serially. Record frozen project IDs, budget totals, FX context, engine version, fingerprints, candidate counts, selected/conditional IDs, program slugs, incentive, NPC, adjustments, and qualification/normalization blockers.

Carry the original 12-row matrix without shrinking or relabeling silently. A formally excluded identity/control or authority-vetoed program remains accounted for, but must not be counted as priced consumption.

## Hard timeouts and anti-loop rules

Enforce actual process deadlines:

- Ordinary command/query: 120 seconds.
- Individual test file: 300 seconds.
- Focused grouped tests: 900 seconds.
- Individual project recomputation: 300 seconds.
- Push or remote verification: 120 seconds.

Use a real process alarm/watchdog, not an output-yield timeout. Keep visible bounded logs.

On timeout or failure:

1. Capture the command, elapsed time, log, and owned process state.
2. Stop only the owned process safely; do not terminate unrelated database sessions.
3. Clean up the owned transaction/session.
4. Retry at most once and only after a documented causal correction.
5. Continue all independent rows/checks that do not depend on the failed task.
6. Mark only the affected verification incomplete. Do not stop the entire remediation because one independent check or official source is unavailable.

Do not run the full suite. The focused suite plus exact adverse cases and four serial project recomputations are the acceptance gate.

## Acceptance conditions

Do not claim completion unless all are true:

- All seven ledger rows have an implemented and tested terminal disposition.
- FX is deeply immutable, finite-safe, and fully represented in cache identity.
- Netherlands unknown aggregate does not become zero and identity/period semantics are exercised by canonical inputs.
- Texas rejects zero and every non-finite award and prices valid awards exactly.
- South Africa enforces post-basis conservation.
- LU/FVD never present the unchanged anchor as the distinct alternative; every structure aggregates all program gates; eligible distinct alternatives rank when complete; otherwise a distinct conditional with exact gaps is disclosed.
- Oregon and AE have honest, explicit priced-consumption denominator semantics with no authority fabrication or identity substitution.
- Bad Hombres and Lips Like Sugar pass the accepted economic regression checks or have an exact authorized attributable explanation.
- No excluded subsystem or unrelated source fact changed.
- Focused tests and all adverse reproductions pass within the hard deadlines.

If a production implementation defect remains, status is `NOT_COMPLETE`; do not commit a “complete” closeout claim. An unresolved Oregon official proposition may close only through the explicit fail-closed/excluded-denominator terminal outcome above.

## Artifacts, commit, push, and remote verification

Write one concise Claude closeout artifact under `docs/validation/` containing:

- exact seven-row before/after disposition;
- changed production/test files;
- independent expected/observed results;
- original 12-row accounting;
- LU/FVD distinct selection outcome;
- four-project economics;
- exact focused test results and timeout ledger;
- frozen exclusions confirmation.

Stage only intended production files, focused tests, and that Claude closeout artifact. Show the staged path list. Commit with:

`fix: close bounded optimizer remediation defects`

Push without force to `origin/claude/audit-frametax-features-NZcX5`.

After push:

- Fetch the remote branch.
- Verify local SHA equals `git ls-remote` SHA.
- Retrieve every committed changed file from the remote commit.
- Verify the remote commit contains exactly the intended paths and each remote file is non-empty and byte-identical to the committed local file.
- Report unrelated preserved untracked files separately; do not delete them.

## Final response — short

Return only:

- status: COMPLETE / NOT_COMPLETE
- seven rows: exact terminal disposition for each
- original 12-program accounting
- LU selection: selected or exact distinct conditional
- FVD selection: selected or exact distinct conditional
- Bad Hombres economics
- Lips Like Sugar economics
- focused tests
- timeouts/incomplete checks
- production files changed
- test files changed
- artifact path
- commit SHA
- branch
- pushed: YES/NO
- remote verification: PASS/FAIL
- excluded areas changed: NONE or exact violation

Stop after remote verification. Do not begin another audit, frontend phase, MFNI workstream, or global research pass.
