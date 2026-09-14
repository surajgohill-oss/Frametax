# CineGlobe Final Four-Row Wiring Acceptance — Codex

## Verdict

**NOT_ACCEPTED. Four rows accepted: 0/4. Target: `1a4677859efa86927c087d464f4e2507f671bd5b`.**

The remediation contains useful generic work, but it does not satisfy the controlling end-to-end acceptance contract. The decisive failures are independently reproduced production-path defects: incomplete participant blocker aggregation, a Netherlands estimate-as-award pseudo-ledger, South Africa component-label rather than qualifying-line conservation, and an Oregon single-tier calculation where the authoritative formula requires the sum of two disjoint bases.

No production code, canonical program data, project facts, UI, MFNI, reinvestment, or research artifact was modified by this audit.

## Startup and identity gate

- Repository/remote: `surajgohill-oss/Frametax`, `origin=https://github.com/surajgohill-oss/Frametax.git`.
- Shared branch: `claude/audit-frametax-features-NZcX5`.
- Local and remote target at startup: `1a4677859efa86927c087d464f4e2507f671bd5b`.
- Ancestry: `1a46778` descends from both `ea5fc9a2587f6e5659005e04ce437dcd8f98533c` and `67fbc30d9e006663ec739256424dace303d16605`.
- Delta: one Claude commit, 17 changed files, including eight production files, migration `0072`, seven test files, and the Claude closeout.
- Pre-existing shared-worktree files were preserved and excluded: modified `frametax2/backend/tests/test_canonical_economics_integrity_repair.py`; untracked `frametax2/backend/test_four_projects.py`, `frametax2/backend/tests/test_four_projects_print.py`, and repository-root `test_conditional.py`, `test_four_projects.py`, `test_four_projects2.py`, `test_four_projects3.py`.
- Runtime identity: engine `canonical-1.54.0`; ruleset digest `6984b9bae1461caf8ea5f389a375852362b53a8b14300e4a8014f789556bc378`; pricing-source digest `117ad74d64d3c83fac6fca12d0658f2208fe25630ecabcc61db4c10c81d71e9e`; loaded-source/disk mismatches: none.
- FX identity: snapshot `2026-07-13`, freshness `never_refreshed`; MUR 47.053589, EUR 0.87679, GBP 0.74699, CAD 1.4135, CZK 21.238, ZAR 16.3636 per USD.
- Current canonical identity count reported by `all_canonical_identities()`: 218. No identity was added or removed by the remediation.

## Four-row findings

### P0-SEL-ALT-001 — not accepted

What worked:

- `_relocation_completeness()` now requires explicit evidence or explicit non-applicability for travel, FX, local cost, and in-kind dimensions.
- `qualification_state=None`, hard-failing, baseline, and structurally unnormalized stack cases are excluded by the new predicate.
- Verified-winner precedence remains intact for Bad Hombres and Lips Like Sugar.

What fails:

- Component and stack aggregation keeps only `{"state": worst_state}`. It discards each participant's `missing_facts`, `curable_requirements`, rate gates, and reasoning at `canonical_evaluation.py:3218-3225` and `3596-3664`.
- `_blocking_requirements()` can only disclose the discarded aggregate's empty fields plus relocation dimensions. FVD's Greece/Romania conditional therefore omits Greece's real `gr_aggregate` cultural/personnel fact. Little Utopia's Manitoba conditional states `RULE_DATA_INCOMPLETE` but exposes no blocker describing that missing rule data.
- The changed `test_copro_qualification_wiring.py` deliberately filters out minimal aggregate shapes instead of requiring participant detail. That is a weakened oracle aligned to the implementation.

Observed real-project blockers:

- Little Utopia/Manitoba: only `relocation_{travel,fx,local_cost,inkind}_evidenced__CA-MB`.
- FVD/Greece+Romania: only `relocation_{travel,fx,local_cost,inkind}_evidenced__RO`; expected at minimum also includes Greece `gr_aggregate`, plus any applicable participant/rate/administrative gates.

The displayed alternatives are numerically lowest in the currently admitted economic pool, but their admission and complete-blocker predicates are unproven. They are therefore not accepted as the strongest materially distinct conditionals. Script/location fitness remains explicitly outside this audit.

### P0-NL-001 — not accepted

What worked:

- Migration `0072` is additive, nullable, indexed, reversible, and included in the calculation fingerprint.
- Missing company identity causes the Netherlands program to fail closed.
- Native cap validation rejects negative, nonfinite, and over-cap aggregates at the resolver boundary.

What fails:

- There is no canonical award ledger. `_company_period_prior_award_facts()` sums every current `PRICED` `StructureCalculationResult` containing the slug. Those rows are hypothetical candidate estimates, not granted awards. Multiple structures can be counted for one project.
- `target_shoot_year` is reused as award period without an award-period field or provenance.
- A plain company string has no legal-entity evidence/provenance state and is not exposed through the inspected API/schema path.
- A real same-company/year sibling with no current evaluation is skipped. Independent isolated-DB observation: `facts=['nl_nfpi_company_period_identity_known']`, `amounts={}`, `has_other=False`. The cap resolver interprets that absence as no other production and grants the full cap.
- Each stored USD estimate is converted back to EUR using the current project's FX and the remaining cap is converted to USD again. This is not one conversion of a native-EUR award ledger.
- There is no transactional reservation, unique award record, or lock. Concurrent first evaluations can both observe no prior result and each price the full cap; repeated results remain order/staleness dependent.

Claude's four passing Netherlands tests prove sequential behavior only. The test named “wrong company and wrong period” does not provide any wrong-company or wrong-period value; it exercises boolean combinations at the resolver.

### P0-ZA-001 — not accepted

What worked:

- The post-only tier has distinct `post`/`vfx` component metadata.
- Duplicate non-empty line IDs and one-cent over-subtotal values reject.
- The ZAR 25 million cap and canonical FX path continue to work for the existing tested cases.

What fails:

- The traced subtotal filters allocations by jurisdiction and component label only. It does not intersect the qualifying register.
- Independent observation with a `component="post"`, `spend_category="contingency"`, USD400,000 line: `qpe_usd=0`, `excluded_usd=400000`, but `executable=True` and incentive USD100,000.
- A USD200,000 scalar against one USD400,000 qualifying post line is accepted and pays USD50,000 instead of being derived from the line set or rejected as unreconciled.
- Missing line IDs and two duplicate `None` line IDs are accepted because duplicate detection runs only for truthy IDs.
- No production/allocation/participant identity is carried by this conservation check.

This violates the controlling requirement that QSAPPE be derived from or exactly reconciled to qualifying Post/VFX source-line IDs.

### P0-OR-001 — not accepted

What worked:

- The stale coverage veto was lifted consistently for `us_or_opif` and `or_opif`.
- Each rate is correct when probed alone.
- The regional increase is correctly implemented as multiplication of the otherwise allowable incentive by 1.10.
- The 50%-of-fund ceiling is represented as USD10.6 million.

What fails:

- The shared resolver chooses one winning tier. USD2,000,000 payroll plus USD2,000,000 other spend returns USD500,000. Literal required arithmetic is `2,000,000 × 20% + 2,000,000 × 25% = 900,000`.
- The USD1 million program threshold is incorrectly attached to each component fact. USD500,000 payroll plus USD700,000 other spend has USD1.2 million total Oregon spend and should produce USD275,000 before uplift/cap; the runtime returns non-executable. USD1.1 million payroll plus USD100,000 other produces USD220,000 instead of USD245,000.
- No application path derives or reconciles `us_or_payroll_qpe_usd` or `us_or_other_qpe_usd`; repository references are definitions/tests only. Claude's only real-project provisional-economics test skips for exactly this reason.
- Application timing, discretion, allocation, contract execution, fund availability, award, and per-payee exclusion are collapsed into one `us_or_opif_award_confirmed` boolean. The per-payee USD1 million QPE limit is asserted, not applied line by line.
- The cap is fixed without `cap_requires_evidence_fact_key`; the repository's recorded fiscal period says `2026-07-01 to 2026-06-30`, an internally impossible interval. The nominal cap lacks a coherent effective-period binding.
- Greenlight Oregon is mentioned in program requirements but has no tested calculation interaction.
- Reachable parallel records still conflict: `jurisdiction_comparison.py` carries a flat 26.2%; `global_inventory_extended.py` carries 20% goods/10% resident wages and USD750,000 minimum; `fund_economics_model.py` carries a USD14 million typical maximum and flat 20% note.

The authority disposition may remain conditional-formulaic, but the formula, input derivation, explicit gates, and dated-cap terminal behavior are not accepted.

## Migration verdict

**STRUCTURAL_PASS / FEATURE_BINDING_FAIL.**

An isolated task-owned PostgreSQL database was created, upgraded to `0071`, then to `0072`, upgraded to head again (no-op), downgraded to `0071`, and upgraded to head. Results:

- `0071`: column absent.
- `0072`: nullable `varchar(255)`, no default, expected index present.
- Fresh creation and repeat Alembic application reached `0072 (head)`.
- The database was dropped after verification.

The migration itself does not fabricate values and existing rows remain null. It is nevertheless insufficient for P0-NL-001 because it adds neither award-period/provenance nor an award ledger/transactional cap mechanism.

## Original 12-program matrix carry-forward

No row was removed, renamed, or reopened for research.

| Row | Program | Current classification | Accepted |
|---:|---|---|---|
| 1 | `ae_dpip / ae_dxb_dpip` | Identity-control/superseded; Dubai remains closed | YES |
| 2 | `au_location_offset` | Executable/runtime-consumed | YES |
| 3 | `cz_film_incentive / cz_film_incentive_animation` | Executable/runtime-consumed | YES |
| 4 | `fr_trip` | Executable conditional tier | YES |
| 5 | `is_film_reimbursement_scheme` | Executable with unresolved enhanced tier disclosed | YES |
| 6 | `ma_ccm_rebate` | Executable after mandatory gates | YES |
| 7 | `mt_mfc_rebate` | Executable with certificate conditional | YES |
| 8 | `nl_film_production_incentive` | Defective | NO |
| 9 | `th_film_incentive` | Executable after mandatory gates | YES |
| 10 | `us_or_opif` | Defective conditional formula | NO |
| 11 | `us_tx_miip` | Executable conditional on exact award | YES |
| 12 | `za_nfvf_rebate` | Defective post-only basis | NO |

Result: **9/12 accepted, unchanged denominator.** Previously accepted FX, Texas, and Dubai controls passed focused regression checks.

## Four real projects

The serial canonical recomputation returned `EVALUATION_REUSED` for all four at the target runtime. Exact values are in `CINEGLOBE_FINAL_FOUR_PROJECT_RUNTIME_CODEX.csv`.

- Little Utopia: Mauritius anchor, USD573,059.70 incentive, USD3,791,333.30 adjusted NPC; no verified winner; Manitoba reported conditional but blocker completeness not accepted.
- FVD: Greece anchor, USD1,445,659.84 incentive, USD3,072,027.16 adjusted NPC; no verified winner; Greece/Romania reported conditional but Greek/participant blockers are missing.
- Bad Hombres: `us_nm_film_credit` verified winner, USD596,910.25 incentive, USD1,885,112.75 NPC; control passes.
- Lips Like Sugar: `ca_film_30` verified winner, USD3,459,278.90 incentive, USD8,524,375.10 NPC; control passes.

## Focused verification

- Passing focused tests: **83**.
- Skipped: **1** — Oregon real-project provisional-economics test, because no real project derives the new Oregon basis facts.
- Existing focused failures: 0.
- Independent acceptance reproducers: **7 failed checks**, covering incomplete blocker disclosure, Netherlands unknown-sibling handling, Netherlands award/provenance/concurrency semantics, ZA excluded-line pricing, ZA untraced/missing-ID acceptance, Oregon combined-basis arithmetic, and Oregon total-threshold/runtime-gate behavior.
- One collection attempt for `tests/optimization/test_global_data_application_runtime.py` failed because that subdirectory invocation did not inherit the backend import root. It was retried once with the documented causal correction `PYTHONPATH=.` and passed 7/7. Classification: environmental limitation, not a product defect.
- No full backend suite was run.
- No command, file, migration, project recomputation, grouped check, or remote operation exceeded the controlling timeout.

Passing implementation-authored tests do not overcome the independent counterexamples. In particular, Oregon tests evaluate each component separately, and the modified co-production persistence test explicitly avoids the aggregate shape that must carry participant detail.

## Reachable stale or parallel paths

- `frametax2/backend/app/calculators/jurisdiction_comparison.py::_US_OREGON`: flat 26.2% profile.
- `frametax2/backend/app/data/global_inventory_extended.py`: 20% goods/services, 10% resident wages, USD750,000 minimum.
- `frametax2/backend/app/data/fund_economics_model.py`: USD14 million typical maximum and flat 20% note; reachable by coverage/demo fund consumers, though not the canonical segment price kernel.
- Netherlands `StructureCalculationResult` history is reachable as a pseudo-award source and can be stale/multiple/order-dependent.

## Engineering process review

Failure attribution is mixed and evidence-based:

1. **Implementation mistakes:** Oregon represented additive bases as competing tiers; ZA used component labels instead of the qualifying register; Netherlands used scenario estimates as awards; selection reduced participant detail to a scalar state.
2. **Weak/circular test oracles:** Oregon tests assert each limb alone; the real runtime assertion skips; the NL “wrong company/period” test supplies neither; the co-production test was narrowed to avoid the new aggregate; a debug print test with no acceptance assertion was committed in `test_final_formulaic_full_pipeline_consumption.py`.
3. **Incomplete execution instructions:** the prior repair contract demanded the outcomes but did not explicitly prohibit reusing calculation-result rows as an award ledger or require a composite multi-base result type. Those ambiguities contributed, but do not excuse contradiction of explicit concurrency, evidence, and combined-formula gates.
4. **Environmental constraint:** one nested test invocation required `PYTHONPATH=.`. This was a bounded, corrected tooling issue and caused no product finding.

At most five instruction improvements for the next pass:

1. Require one independent end-to-end negative and one composite expected-value oracle per defect before existing tests may be edited.
2. State that projected/candidate economics can never be treated as approved, granted, paid, reserved, or ledgered awards.
3. Require aggregates to retain the union of participant identities, blockers, provenance, and states—not only the worst state.
4. Require disjoint-base programs to return one composite incentive and apply program-level thresholds once; forbid “test each tier separately” as acceptance.
5. Require a non-skipping generic-project runtime test and predeclare `PYTHONPATH`, isolated DB lifecycle, and hard wall-clock controls.

What should be preserved: generic dataclass extensions, explicit per-dimension relocation facts, immutable FX context, native-cap conversion, nullable migration discipline, serial four-project controls, and bounded focused testing.

## Deferred boundary

`SCRIPT_ANALYZER_CURRENTLY_USED_FOR_LOCATION_FIT: NO`.

`LOCATION_FEASIBILITY_NEXT_PHASE: REQUIRED`.

This audit neither approves nor rejects Manitoba, Romania, or any other location for script/facility/personnel/schedule suitability. Incentive-only ordering cannot establish physical feasibility. The future bounded phase remains: script requirements → location/production capabilities → feasible facilities/substitutions → added costs and constraints → canonical eligibility/ranking.

## Acceptance gate

- Four rows accepted: **0/4**.
- Original matrix: **9/12 accepted**.
- Migration: **structural pass; Netherlands feature binding fail**.
- Ready to merge: **NO**.
- MFNI: parked unchanged.
- Reinvestment: parked unchanged.
- UI: unchanged/deferred.
- Next step: run the single replacement Claude prompt in `CINEGLOBE_FINAL_FOUR_ROW_REMEDIATION_CLAUDE_PROMPT.md`, then perform one delta-only Codex re-audit of only the resulting remaining-row commit.

