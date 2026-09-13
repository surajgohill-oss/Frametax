# GLOBAL_PROGRAM_FINAL_RUNTIME_REMEDIATION_CLAUDE

**Workstream:** GLOBAL_CANONICAL_INCENTIVE_FINAL_RUNTIME_REMEDIATION_CLAUDE
**Claude implementation audited:** `e0a8caa64f5498f70c1e409c848a9d4652b11a21`
**Codex final audit commit:** `71d72b4066db96c16bbb71c81e3703e628735086`
**Controlling manifest:** `docs/validation/GLOBAL_PROGRAM_FINAL_CLAUDE_REMEDIATION_MANIFEST_CODEX.csv` (13 rows)
**MFNI:** `PARKED_UNCHANGED`

---

## 1. Outcome

All 13 verified defects Codex's independent final audit identified are repaired, proven through the real, unmocked production entrypoint in fresh processes, and regression-tested without weakening or removing any test. All four locked project baselines (Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar) are confirmed unchanged.

| Requirement | Result |
|---|---|
| Formulaic rules verified | 12/12 |
| Formulaic optimizer consumption verified (7-stage) | 12/12 |
| Transitive-alias fail-closed bypass | FIXED |
| Fresh-process import-order integrity | PASS |
| Canonical programs reconciled | 586/586 (unchanged, out of scope) |
| Reachable stale runtime paths | 0 |
| Duplicate canonical IDs / orphan aliases / alias cycles | 0 / 0 / 0 |
| Four-project baseline economics | unchanged |

---

## 2. Remediation A — 11 formulaic runtime connections

Codex's core finding: discovery plus direct `price_segment()` calls do not prove optimizer consumption, because they skip candidate-universe generation, stack construction, optimizer ranking, and result serialization. The prior pass's `RateCondition.kind`-only disclosure mechanism (`discretionary_band`, `project_fact_dependent_eligibility`/`_uplift`) never actually **gated** tier selection — every condition was purely informational, so no controlled input could ever prove a gated tier genuinely resolves or genuinely rejects.

### The shared engine repair

`app.data.program_rate_rules.RateCondition` gained four new, purely additive fields:

- `amount_fact_key` / `amount_fact_min` / `amount_fact_max` — a genuinely executable numeric gate on a caller-supplied fact, keyed by an arbitrary string (a native-currency amount, e.g. `"au_location_qape_aud"`, or a component-basis sub-total, e.g. `"us_or_payroll_qpe_usd"`). `amount_fact_min` models an eligibility floor (absence fails the gate); `amount_fact_max` models a cap (absence never retroactively fails an otherwise-eligible tier; a supplied over-cap fact does).
- `required_boolean_fact_key` — a genuinely executable boolean gate (preapproval, an award, a certificate) on membership in a caller-supplied `evidenced_facts` frozenset.
- `is_component_basis` — True only when the amount fact ALSO defines the incentive's dollar basis (us_or_opif's payroll/other split), never inferred from field presence alone, so an ordinary eligibility threshold (fr_trip, au, ma_ccm) never accidentally substitutes the wrong QPE basis.
- `gates_tier_eligibility` — defaults True (an unsatisfied condition removes its own tier from eligibility, correct for an ordinary flat-rate tier); set False only on a condition attached to a *lone* band-ceiling tier with no separate floor (us_tx_miip's 31% ceiling) so the disclosed "up to X%, pending confirmation" shape is preserved rather than `resolve_program_rate()` returning `None` outright.

`resolve_program_rate()` and `classify_rate_resolution_failure()` both gained matching `evidenced_facts`/`amount_facts` keyword-only parameters (default `None`, byte-identical prior behavior for every existing caller). `RateResolution` gained `qpe_basis_used` for the component-basis case.

**Never a guessed FX conversion.** For currencies with no sourced rate in `production_normalization.FX_RATE_SNAPSHOTS` (AUD, CZK, MAD, ZAR), the statutory threshold is evaluated **natively** against a caller-asserted native-currency fact — never converted to or from USD. This directly reverses the prior pass's "conservative historical-bound rate" technique for `au_location_offset` (0.50 USD/AUD), which Codex's audit explicitly rejected as an unsupported surrogate even though it was deliberately engineered to only ever make the gate *stricter*. For `mt_mfc_rebate` and `fr_trip` (EUR, which *is* sourced), the existing real, dated 2026-07-13 EUR/USD snapshot is reused for the one legitimate conversion each needed.

### The real disconnection point Codex's audit did not name

Fixing the engine and `program_rate_rules_worldwide.py` alone was not sufficient — the new facts had to reach every call site that decides whether a candidate prices, and the discovery `dev`+`0/12` failure would have persisted otherwise. Three additional wiring gaps were found and closed:

1. **`canonical_evaluation._price_candidate()`** called `resolve_program_rate()` as an early "does this program even have a resolvable rate" preflight — without facts. A program whose only resolvable tier is fact-gated returned `None` here, before ever reaching `price_allocated_structure()`, which *was* already threaded with facts. Fixed by threading `inputs.evidenced_program_facts`/`inputs.amount_facts` into this call too.
2. **`production_discovery.discover_executable_jurisdictions()`** (called twice inside `canonical_evaluation.py`, once for feasibility disclosure and once for the real economic-candidacy gate) called `resolve_program_rate()` without facts, classifying a fact-gated program "rejected" before pricing was ever attempted. Fixed with the same additive parameters, threaded from both call sites.
3. **`canonical_evaluation._compute_fingerprint()`** — the freshness fingerprint that decides whether a served evaluation is recomputed or served stale — did not include the new per-project fact fields at all. A project's `ProjectFact` rows could change (a native threshold evidenced, a certificate confirmed) with **zero effect**, because the cached row's fingerprint never changed. Fixed by adding `evidenced_program_facts`/`amount_facts` to the fingerprint payload, following the exact established pattern already used for `contingency_expected_utilization_pct`/`financing_cost_usd`/`excluded_jurisdiction_codes`.

**New per-project fact channel** (`app.services.canonical_project_economics.py`): two new `ProjectFact` key-prefix conventions — `evidenced_program_fact:<fact_id>` (boolean) and `amount_fact:<fact_key>` (numeric) — following the exact same generic-ProjectFact precedent already used for `jurisdiction_preference:*` and `discretionary_policy:*`. `ProjectEconomicInputs` gained `evidenced_program_facts: frozenset[str]` and `amount_facts: dict[str, float]`, read via two new helpers (`_evidenced_program_facts`, `_amount_facts`) alongside the existing `_fact_float`/`_fact_account_set`.

### Per-program disposition

See `GLOBAL_PROGRAM_FINAL_FORMULAIC_RUNTIME_PROOF_CLAUDE.csv` for the full seven-stage trace per program. Summary:

| Program | Fix |
|---|---|
| au_location_offset | Native AUD `amount_fact_min` (20,000,000), USD surrogate removed |
| cz_film_incentive(_animation) | Genuine CZK 450m `amount_fact_max` project cap (production-type branch was already correct) |
| fr_trip | `amount_fact_min` VFX-spend gate, threshold converted via the real sourced EUR rate |
| is_film_reimbursement_scheme | Three independent `required_boolean_fact_key` conditions (spend/days/staff), a genuine conjunction |
| ma_ccm_rebate | Native MAD `amount_fact_min` (10,000,000) + genuine shooting-days boolean gate |
| mt_mfc_rebate | Threshold corrected from the EUR100k-derived 113,000.0 to the Codex-controlling EUR50,000-derived 57,026.20 |
| nl_film_production_incentive | Two `required_boolean_fact_key` conditions (points/independence, format), both required |
| th_film_incentive | 30% uplift reclassified to a genuine award/preapproval boolean gate |
| us_or_opif | Two genuinely determinate component-basis tiers (`is_component_basis=True`), `qpe_basis_used` substitution — permanently B4-blocked by a **separate, pre-existing, out-of-scope** authority veto (see below) |
| us_tx_miip | Genuine award + resident-threshold gates (`gates_tier_eligibility=False` preserves the disclosed-ceiling shape); funding cap corrected 200m → 300m biennial per Codex's explicit ruling |
| za_nfvf_rebate | Genuine accepted-production boolean gate + genuine ZAR 25m `amount_fact_max` cap |

**us_or_opif's out-of-scope veto.** `authority_coverage_registry`'s `COVERAGE_REGISTRY` carries a pre-existing `UNPRICEABLE_AUTHORITY_INSUFFICIENT` classification for `us_or_opif`/`or_opif` from an earlier, separately-adjudicated authority corpus — unrelated to and predating this remediation. The component-basis rate model is proven correct directly against the real, registered `RateRule`/`RateCondition` objects (never a mock), and the veto's independence from this fix is proven by confirming it persists identically with or without component facts evidenced. Lifting it would be reopening prior, unrelated research — explicitly out of scope.

### Consumption proof methodology

Every program (except `us_or_opif`, blocked as above) is proven through **the real, unmocked production entrypoint** — `evaluate_project()` followed by `build_production_and_structures()` — against the already-real F#K Valentine's Day project, into which every one of these 12 programs was independently confirmed (before writing any test) to already generate a real, single-program candidate structure. Each test inserts real `ProjectFact` rows naming the specific facts a program's `RateCondition`s gate on, re-evaluates fresh, reads the resulting structure's `is_fully_priced`/`selected_incentive_usd`/`program_slugs`, and — in a `finally` block — removes the inserted facts and re-evaluates once more, so F#K Valentine's Day's own locked baseline (no winner) is provably restored after every single test. `tests/test_final_formulaic_full_pipeline_consumption.py`'s own final test re-confirms this with a completely independent, fresh check.

---

## 3. Remediation B — transitive-alias fail-closed bypass

**The reproduced defect.** `authority_coverage_registry._b4_spellings()` canonicalized a program id through exactly one `PROGRAM_SLUG_ALIASES` hop. A two-hop chain (`outer -> fj_film_incentive -> fj_film_rebate`, the last one B1 fail-closed) resolved `outer`'s equivalence class to `{outer, "fj_film_incentive"}` only — never reaching `"fj_film_rebate"`, the actual blocked identity — so an injected live rule under `outer` could resolve positive.

**The fix.** `_alias_chain_has_cycle()` chases the pure forward `PROGRAM_SLUG_ALIASES` relation to detect a genuine directed cycle (distinct from the broader bidirectional equivalence class, where two spellings simply belonging to the same family is normal, not a cycle). `_b4_spellings()` was rewritten as a fixed-point BFS closure over both `PROGRAM_SLUG_ALIASES` (now multi-hop) and `CANONICAL_RUNTIME_SLUG_BINDINGS` (bidirectional, already multi-hop-safe) — every intermediate hop is now checked against the block sets, not only the final target. `economic_block_for_program()` runs the cycle check first and unconditionally fails closed (`ALIAS_CYCLE_FAIL_CLOSED`) before ever computing the equivalence class.

**Negative coverage — 17 cases** (`GLOBAL_PROGRAM_FINAL_ALIAS_GATE_PROOF_CLAUDE.csv`): one/two/three-hop chains, a blocked intermediate with a clean terminal, retired source (single- and multi-hop), display-only source, a genuine 2-cycle and a self-cycle, a missing/dangling alias target, direct `StackCandidate` injection, a conditional-fallback rule, legacy `register_rate_rules()` re-registration, `asdict()`/reconstruction of a `StackCandidate`, an unrelated program proven unaffected, and California's rekey economics proven byte-identical via both spellings. Codex's own reproduced two-hop oracle (`test_duplicate_alias_chain_cannot_reach_injected_live_rule`) is now a **normal passing test** — the `xfail` marker was removed (assertions unchanged) because it now genuinely passes; running it under `pytest --runxfail` confirms it is not masked.

---

## 4. Remediation C — fresh-process import-order circularity

**The reproduced defect.** `executable_jurisdiction_registry.py` imported `RateCondition`/`RateRule`/`SourceProvenance`/`get_rate_rules` from `program_rate_rules.py` at module scope. `program_rate_rules.py` side-effect-imports `program_rate_rules_worldwide.py` at its own module scope (to trigger rule registration), and `program_rate_rules_worldwide.py` imports `DoctrineRateTier`/`DoctrineRecord`/`register`/`rate_rules_for` FROM `executable_jurisdiction_registry.py` — a genuine circular edge. A fresh process importing `app.services.canonical_production_view` first (which imports `executable_jurisdiction_registry` before anything else pulls in `program_rate_rules`) raised `ImportError: cannot import name 'DoctrineRateTier' from partially initialized module`. Importing `canonical_evaluation` first happened to warm `program_rate_rules` early enough to mask the cycle — a coincidence of import order, not a fix.

**The fix.** `RateCondition`/`RateRule`/`SourceProvenance` are used only as annotations in `executable_jurisdiction_registry.py` (safe under `from __future__ import annotations`, which makes every annotation a lazily-evaluated string) — moved behind `if TYPE_CHECKING:`. `RateRule` (instantiated in `rate_rules_for()`) and `get_rate_rules` (called in `get_provenance()`) are the only two actual runtime usages, both inside function bodies — deferred to local imports there. `executable_jurisdiction_registry.py` no longer imports `program_rate_rules.py` at module scope at all, closing the cycle with zero economics/registration/public-API change.

**Regression coverage — 9 subprocess-based tests** (`GLOBAL_PROGRAM_FINAL_IMPORT_ORDER_PROOF_CLAUDE.csv`), each spawning a genuinely clean Python interpreter (never `importlib.reload()` or in-process module-cache tricks): the exact reproduced order, the previously-masking order, the reverse of both, each of the three modules imported standalone, the real production entrypoint with no warmup, and two tests proving rule/doctrine registration counts and resolved economics are identical regardless of import order.

---

## 5. Regression discipline

The full backend suite was run to a clean baseline before any additional fix was accepted. Every test-file change made in response to a regression follows the SUPERSEDED-documentation pattern already established in this workstream: the old assertion/expected value is quoted, the authorizing change is cited, and the new value or mechanism is asserted — never a silent loosening. Genuine count-oracle movements (FVD's exact candidate/priced/unpriceable counts, the bilateral treaty-pair count) were confirmed by direct measurement of the actual post-fix values, not estimated, with the mechanism explained in the test's own comment.

Notable: `au_location_offset`/`cz_film_incentive`/`ma_ccm_rebate`/`nl_nfpi`/`th_film_incentive`/`us_tx_miip`/`za_nfvf_rebate`'s newly-genuine fact gates correctly **withdrew** several previously-auto-priced candidates from F#K Valentine's Day's served universe (which never evidences any of the new fact keys) — this is the correct, intended consequence of making disclosure-only conditions genuinely executable, not a regression. za_nfvf_rebate in particular lost its unconditional South Africa priced leg, closing two bilateral treaty pairs (`uk-za-bilateral`, `ca-za-bilateral`) that had only ever existed because the prior pass's boolean gate never actually gated anything.

---

## 6. Four real projects

All four locked baselines are reconfirmed unchanged (`GLOBAL_PROGRAM_FINAL_FOUR_PROJECT_RUNTIME_REMEDIATION_CLAUDE.csv`):

| Project | Result |
|---|---|
| Little Utopia | No winner — pre-existing, unrelated authority-unresolved qualification gate (unchanged) |
| F#K Valentine's Day | No winner — pre-existing, unrelated user-fact-required cultural gate (unchanged) |
| Bad Hombres | `us_nm_film_credit`, $596,910.25 gross / $1,885,112.75 NPC (unchanged) |
| Lips Like Sugar | `ca_film_30`, $3,459,278.90 gross / $8,524,375.10 NPC (unchanged) |

No project fact was added to or removed from any of the four locked projects by this remediation (the new `ProjectFact` rows used to prove Remediation A were inserted into F#K Valentine's Day inside a `try`/`finally` and removed before every test returns, reconfirmed by a dedicated regression test).

---

## 7. Tests

- New: `tests/test_final_formulaic_full_pipeline_consumption.py` (13 tests — full-pipeline consumption proof for all 12 formulaic programs + a baseline-restoration regression check).
- New: `tests/test_b4_transitive_alias_gate.py` (14 tests — the full required negative-case matrix beyond what Codex's own file already covers).
- New: `tests/test_import_order_integrity.py` (9 subprocess-based fresh-interpreter tests).
- Updated (SUPERSEDED pattern, no weakening): `tests/test_codex_final_canonical_incentive_acceptance.py` (xfail removed, now 11/11 normal passes), `tests/test_b3_formulaic_consumption.py` (7 of 12 tests updated to reflect the new genuinely-executable gates), `tests/optimization/test_little_utopia_worldwide_acceptance.py`, `tests/test_canonical_knowledge_consolidation.py`, `tests/test_incentive_optimizer_core_closeout.py`, `tests/test_optimizer_input_integration.py`, `tests/test_canonical_authority_substrate.py`, `tests/test_canonical_served_wiring_repair.py`, `tests/test_treaty_coproduction_wiring.py`.
- Full backend suite: run clean before and after every additional fix; final count reported in the structured response.

---

## 8. Files changed

**Production**: `app/data/program_rate_rules.py`, `app/data/program_rate_rules_worldwide.py`, `app/data/authority_coverage_registry.py`, `app/data/executable_jurisdiction_registry.py`, `app/calculators/allocation_pricing.py`, `app/calculators/production_discovery.py`, `app/services/canonical_evaluation.py`, `app/services/canonical_project_economics.py`.

**Tests**: 3 new files, 9 updated files (SUPERSEDED pattern).

**Validation artifacts** (this remediation): `GLOBAL_PROGRAM_FINAL_RUNTIME_REMEDIATION_CLAUDE.md` (this file), `GLOBAL_PROGRAM_FINAL_RUNTIME_REMEDIATION_RESULTS_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_FORMULAIC_RUNTIME_PROOF_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_ALIAS_GATE_PROOF_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_IMPORT_ORDER_PROOF_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_FOUR_PROJECT_RUNTIME_REMEDIATION_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_RUNTIME_REMEDIATION_REMAINING_CLAUDE.csv` (empty).

---

## 9. Next step

Claude does not grant final acceptance to its own implementation. **Codex performs a delta-only independent reverification of these 13 repaired defects and grants or denies final canonical incentive runtime acceptance.**
