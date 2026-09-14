# CineGlobe Bounded Engineering and Optimizer Delta Acceptance — Codex

## Decision

**NOT_ACCEPTED.** Claude commit `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9` is a clean descendant of controlling Codex audit `c0effcf276f1f8a793ce93ad9bfb74bd23b0ce81`, and its focused group reproduces at **128 passed in 35.17 seconds**. That result does not establish correctness. Independent adverse probes reproduce four economic-safety defects, and the Little Utopia/FVD change only relabels each existing blocked anchor; it does not discover or select a different alternative.

Production code, project/program source facts, database configuration, MFNI, and frontend/UI were not modified by this audit. The only database activity was the authorized canonical recomputation against the established verification environment.

## Startup and scope

- Repository: `surajgohill-oss/Frametax`; branch `claude/audit-frametax-features-NZcX5`.
- Startup local HEAD = remote HEAD = `4ea0fd832ec52d0ae3e152a404395efa3cbfffc9`.
- Merge-base with the controlling audit is exactly `c0effcf276f1f8a793ce93ad9bfb74bd23b0ce81`; ancestry passed.
- Tracked tree was clean. Existing unrelated untracked scripts were preserved.
- PostgreSQL was listening on localhost and the configured database resolved to `frametax2`. No HTTP backend/frontend service was listening; the permitted verification used the real service layer and database directly.
- Claude delta: 17 backend production/test files plus 10 validation artifacts. No frontend or MFNI delta.
- No full suite, browser, global research, or authority-disposition change was performed.

## Engineering delta

| Claimed repair | Codex verdict | Finding |
|---|---|---|
| Canonical FX | **FAIL** | A frozen dataclass wraps a mutable `dict`; NaN/+∞ rates resolve as valid; the fingerprint includes only snapshot date, so a same-date rate/source/freshness change reuses the prior cache identity. |
| Malta certificate/40% | **PASS on its own path** | The certificate now resolves the two discretionary limbs and serves exact 40% economics. The program remains blocked in the 12-program acceptance matrix by shared FX defects. |
| Netherlands company-period cap | **FAIL** | A missing aggregate is silently interpreted as zero prior awards. The scalar fact has no company/period identity and the test merely simulates two projects without binding either to a company or period. |
| Thailand THB150m endpoint | **PASS** | 149,999,999 and 150,000,000 select 20%; 150,000,001 selects a 25% floor. |
| Texas awarded rate | **FAIL** | 24%/28%/31% work, but the authorized range is coded inclusive of 0 and non-finite values are not rejected. Full pricing accepts 0% and accepts NaN with NaN incentive economics. |
| South Africa QSAPPE | **FAIL** | The caller scalar replaces a derivable/validatable post-spend basis without conservation. A $1 allocation plus a $1,000,000 QSAPPE fact prices a $250,000 incentive. |

No project-name or project-ID special case was added to production logic. The failures arise in generic shared paths.

## Exact adverse evidence

1. `CanonicalFXContext.rates` is declared as `dict[str, float]` inside a frozen dataclass (`apply_fx_rates.py:133-148`). `ctx.rates["EUR"] = 9.99` succeeds. `resolve_fx_rate()` checks only `rate <= 0` (`apply_fx_rates.py:195-215`), so NaN and +∞ return `RESOLVED`.
2. `_compute_fingerprint()` hashes `fx_snapshot_date` but not rates, source, or freshness (`canonical_evaluation.py:781-789`). Two contexts with the same date but different EUR rates, sources, and `fresh` versus `stale_fallback` produce the identical fingerprint.
3. Generic persisted numeric-fact parsing accepts anything Python `float()` accepts and has no finite check (`canonical_project_economics.py:278-293`).
4. Netherlands applies the full cap when the prior-award fact is absent (`allocation_pricing.py:331-349`). Missing and explicit zero both produced USD 3,421,571.87 at the frozen EUR rate; EUR 2m prior produced USD 1,140,523.96 remaining.
5. Texas permits `[0, 0.31]` (`program_rate_rules_worldwide.py:6082-6095`) and comparisons do not reject NaN (`program_rate_rules.py:1915-1950`). The real pricing kernel returned `executable=True, incentive=0` for zero and `executable=True, incentive=NaN` for NaN.
6. QSAPPE is read directly from `amount_facts` (`program_rate_rules.py:1963-1974`) and multiplied without reconciling it to the allocated register (`allocation_pricing.py:733-745`). The one-dollar reproducer returned `executable=True` and `$250,000`.

The complete expected/observed inputs are in `CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_CROSSCHECK_CODEX.csv`.

## Repaired-oracle audit

| Oracle | Verdict | Reason |
|---|---|---|
| Malta | PASS | Exact 40% arithmetic is asserted independently and would fail on the previous 30% behavior. |
| Thailand | PASS | Exact boundary and adjacent units are tested with independent expected values. |
| Texas | FAIL | Two sub-ceiling values are useful, but zero and non-finite values are omitted; both reach executable production pricing. |
| South Africa | FAIL | It proves a separate scalar changes the basis but never proves that scalar is derived from or bounded by the allocation. |
| Oregon | BLOCKED, not consumption proof | The rewritten test honestly establishes the real veto. It cannot satisfy priced optimizer consumption and should not be called a repaired consumption oracle. |

The Netherlands test also uses `convert_incentive_cap_to_usd()`—the same production helper—as its cap oracle and “same company” is only a comment plus a manually supplied scalar, not a canonical company-period relationship.

## Original 12-program matrix

**5 accepted / 7 blocked / 0 unverified.** “Blocked” means independently checked and known not to satisfy the controlling acceptance gate; it does not mean unexamined.

| Program | Status | Basis |
|---|---|---|
| `ae_dpip` | BLOCKED | The original denominator targets a Dubai identity with no accepted formulaic economic chain; Abu Dhabi being correctly separate does not create a Dubai pipeline. |
| `au_location_offset` | ACCEPTED | Previously accepted path unaffected. |
| `cz_film_incentive` | BLOCKED | Native cap depends on the defective shared FX context/fingerprint. |
| `fr_trip` | ACCEPTED | Previously accepted path unaffected. |
| `is_film_reimbursement_scheme` | ACCEPTED | Previously accepted path unaffected. |
| `ma_ccm_rebate` | ACCEPTED | Previously accepted path unaffected. |
| `mt_mfc_rebate` | BLOCKED | Certificate repair passes; native threshold still depends on defective shared FX safety/cache identity. |
| `nl_film_production_incentive` | BLOCKED | Missing aggregate defaults to full cap and shared FX is defective. |
| `th_film_incentive` | ACCEPTED | Exact endpoint repaired and independently reproduced. |
| `us_or_opif` | BLOCKED | Correct intentional authority veto; no priced consumption. |
| `us_tx_miip` | BLOCKED | Zero/NaN awards price. |
| `za_nfvf_rebate` | BLOCKED | Unconstrained QSAPPE breaks spend conservation; shared FX also applies to the cap. |

## Little Utopia and FVD selection

Before (`c0effcf...`) and after (`4ea0fd...`) were executed against the same canonical records. Counts, candidates, economics, and `canonical_selected_structure_id=None` are identical. The only selection-visible delta is the additive `leading_conditional_structure`/`recommendation_category` labeling in `canonical_production_view.py`.

### The Little Utopia

- Canonical anchor: Mauritius single-country `mu_edb_incentive`; USD 573,059.70 estimated incentive; USD 3,791,333.30 NPC; `AUTHORITY_UNRESOLVED` cultural-test applicability.
- Fixed evidence: home `MU`; seven stated-outside accounts (`5000, 5100, 5200, 5300, 5400, 5500, 6500`) and no offshore-payroll accounts. No program boolean or amount facts exist.
- Eligible non-baseline alternative: **none**. Every non-baseline row is hard-marked not directly comparable.
- Strongest materially distinct priced review option: **Full relocation to Manitoba**, `ca_mb_film_video_credit`; USD 1,824,388.20 incentive; USD 3,269,304.80 adjusted NPC. Independent arithmetic: `4,364,393 - 1,824,388.20 + 729,300 = 3,269,304.80`. It cannot be recommended because relocation completeness is false and qualification is `RULE_DATA_INCOMPLETE`.
- Reported “leading conditional”: the unchanged Mauritius anchor itself. It is not a new alternative.

### F#K Valentine's Day

- Canonical anchor: Greece single-country `gr_cash_rebate`; USD 1,445,659.84 estimated incentive; USD 3,072,027.16 NPC; `USER_FACT_REQUIRED` for the Greek aggregate cultural/personnel test.
- Fixed evidence: home `GR`; outside-account and offshore-payroll sets are both `UNKNOWN`; no program boolean or amount facts exist. No explicit producer account route/split exists.
- Eligible non-baseline alternative: **none**. Every non-baseline row is hard-marked not directly comparable.
- Strongest materially distinct priced review option: **Greece anchor — post routed to Romania**, `gr_cash_rebate + ro_film_office_cash_rebate`; USD 1,465,850.60 incentive; USD 3,062,526.40 adjusted NPC. Independent arithmetic: `4,517,687 - 1,465,850.60 + 10,690 = 3,062,526.40`, a raw modeled USD 9,500.76 improvement over the anchor. It cannot be recommended because `is_directly_comparable=false`. Its aggregate `role_qualification` is also absent despite the Greek anchor program’s unresolved test, so it is not acceptance-safe to promote.
- Reported “leading conditional”: the unchanged Greece anchor itself. It is not a new alternative.

The first divergence from the controlling version is presentation only: `_is_conditional_eligible()` requires `is_directly_comparable`, while every non-baseline candidate is persisted with `is_directly_comparable=is_baseline`. The engine calculates travel, FX, and local-cost adjustments in `_relocation_normalization()` but then blanket-marks every relocation incomparable; in-kind completeness is not represented as a per-project/per-candidate dimension. The smallest safe repair is a structured normalization-completeness vector plus aggregate qualification across every claimed program, followed by the existing NPC objective over candidates whose required dimensions are complete.

No downstream application consumer reads `leading_conditional_structure`, `unlockable_alternatives`, or `recommendation_category`; repository search finds only their producer service and tests. The new field is therefore not wired beyond the canonical structures payload.

## Oregon

`us_or_opif` remains correctly and intentionally fail-closed. `authority_coverage_registry.py` maps both `or_opif` and runtime slug `us_or_opif` to `UNPRICEABLE_AUTHORITY_INSUFFICIENT`; `resolve_program_rate()` checks that veto before rate rules. Existing accepted artifacts retain a material conflict over identity/program type, formula entitlement versus discretionary treatment, eligibility, QPE, and stackability. The official Oregon Film incentives page confirms the program generally, but the repository record states the exact rate/threshold/cap propositions came from secondary sources and were not reproduced from the official page.

Targeted authority needed (no research performed here): a current Oregon statute/administrative rule or administering-agency guideline that establishes exact payroll/other rates and bases, minimum spend, award/allocation discretion, per-project/program caps, current period, and stacking/assistance treatment. Candidate-list presence is not priced consumption.

## Four-project delta and UI metadata

- Little Utopia: 241 / 124 priced / 117 rejected; no winner; anchor relabeled.
- FVD: 292 / 159 / 133; no winner; anchor relabeled.
- Bad Hombres: 238 / 122 / 116; `us_nm_film_credit`, USD 596,910.25 incentive, USD 1,885,112.75 NPC—exact accepted economics.
- Lips Like Sugar: 294 / 175 / 119; `ca_film_30`, USD 3,459,278.90 incentive, USD 8,524,375.10 NPC—exact accepted economics.

Existing backend metadata is sufficient for the deferred UI classification: `structure_type`, `participants`, `relationship_types`, `primary_jurisdiction`, `anchor_jurisdiction`, `anchor_program`, `stacked_programs`, `component_allocations`, and `treaty_slug` distinguish single-jurisdiction (including local stacks), official co-production, and anchor/component combinations. No new taxonomy is required. UI consumption remains deferred and unchanged.

## Tests, timeout, and resource-leak classification

- Claude focused group: **128 passed, 5 warnings, 35.17s** under a real 900-second process deadline.
- Independent adverse probes: all completed under 120 seconds; four-project recomputations completed serially under individual 300-second deadlines.
- One reporting script completed all four recomputations but failed after computation because the audit queried nonexistent `Project.name`; it was retried once after the causal correction to `Project.title`, then completed. No process timeout occurred.
- Full suite: not run. Claude’s stall at the same ~19–20% point previously recorded by Codex, combined with a clean focused run and no connection-lifecycle production delta, provides no evidence that this commit introduced the known environment/session leak. Root cause remains outside this bounded audit.

Exact remaining rows and prevention oracles are in `CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_DELTA_REMAINING_CODEX.csv`. MFNI is parked unchanged. Frontend/UI is unchanged and deferred.

## Engineering process review

The failed acceptance is not attributable to one cause, and Oregon's continued block is not an implementation failure. The following attribution is limited to evidence reproduced in this audit.

| Cause | Concrete evidence | Attribution |
|---|---|---|
| Implementation mistakes | `CanonicalFXContext` was described as immutable, but its nested `rates` dictionary can be mutated; `resolve_fx_rate()` accepts NaN and positive infinity; `_compute_fingerprint()` ignores rates/source/freshness. Texas accepts zero and NaN awards. South Africa multiplies an unreconciled caller scalar. Netherlands treats an absent company-period aggregate as zero. | These are production implementation defects in Claude's delta. A frozen outer dataclass, successful ordinary-value examples, or a typed result does not enforce the required domain invariants. |
| Implementation mistake in selection behavior | Before/after execution produced identical LU/FVD candidate counts, economics, and no selected structure. The new output chose the existing Mauritius/Greece anchor because the conditional predicate requires direct comparability while every non-baseline structure is persisted as not directly comparable. | Claude added presentation fields without repairing alternative admission. The result satisfies “show a conditional” literally but not the user-required distinct-alternative behavior. |
| Weak test oracles | The Netherlands test computes its expected cap through the production conversion helper and models “same company” only in comments plus a scalar. Texas omits zero and non-finite awards. South Africa proves only that a separate scalar changes the result, not that the scalar is derived from or bounded by routed spend. Oregon proves the veto rather than priced consumption. | These tests allowed the implementation defects to pass. Malta's exact 40% test and Thailand's three-point boundary test are counterexamples that worked and should be preserved. |
| Incomplete acceptance instructions | The prior remaining-items CSV required an explicit FX context but did not enumerate deep immutability, all non-finite values, or a full context fingerprint. Its Netherlands proof said two projects must not exceed the cap but did not require canonical company/period identity or define unknown aggregate behavior. Its South Africa proof required different bases but not allocation conservation. Distinctness of the LU/FVD conditional was made explicit only in this delta audit. | The omissions created room for incomplete implementations. This does not excuse Texas: the prior instruction explicitly required malformed and out-of-range awards to fail closed, so accepting NaN is both an implementation and oracle failure. |
| Environmental constraints and non-Claude audit error | The full suite stalled at the same previously observed ~19–20% point, while the focused set completed 128 tests in 35.17s and the delta contains no connection/session-lifecycle change. Separately, Codex's first four-project reporting script queried nonexistent `Project.name` after calculations completed; one corrected retry using `Project.title` succeeded. | The suite stall prevents a full-suite claim but is not evidence that this delta caused the economic defects. The reporting typo was a Codex audit mistake, had no economic effect, and was handled within the one-retry rule. |

### Five instruction improvements

1. Preserve the bounded defect ledger, but make every row state its domain invariants and adversarial boundaries: missing, explicit zero, negative, minimum/maximum edges, NaN, positive/negative infinity, and values immediately outside the range where applicable.
2. Require expected values to come from literal arithmetic or a deliberately separate oracle. A test may call production code for the observed result, but must not use the same pricing/conversion helper to manufacture its expectation.
3. For caller-supplied aggregates, require identity, period, evidence state, finiteness, range, and conservation against canonical allocated spend. “A different scalar changes the answer” is never sufficient proof.
4. State selection acceptance in behavioral terms: a baseline cannot count as a newly discovered alternative; all program gates must survive aggregation; eligible distinct options use the existing NPC objective; incomplete distinct options remain separately disclosed with exact missing dimensions.
5. Preserve serial database checks and hard process deadlines. Run the smallest focused set first, continue independent checks after a bounded failure, and classify the known full-suite stall separately unless the production delta changes session/resource lifecycle code.

The complete replacement implementation prompt is `CINEGLOBE_BOUNDED_ENGINEERING_OPTIMIZER_REMEDIATION_CLAUDE_PROMPT.md`. It is the sole recommended remediation instruction; the earlier prompts should not be combined with it.
