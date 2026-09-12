# GLOBAL_PROGRAM_BOUNDED_REMEDIATION_CLAUDE

**Workstream:** GLOBAL_CANONICAL_INCENTIVE_BOUNDED_REMEDIATION_CLAUDE
**Base commit:** `9baa3b68c90b81d3819bd29c30ff140812f2ab1b` (Codex adjudication)
**Scope:** the 107-row bounded work-item manifest in `docs/validation/GLOBAL_PROGRAM_CLAUDE_FOLLOWUP_MANIFEST_CODEX.csv`, closing every blocker Codex adjudicated from the prior Claude wiring pass. MFNI parked unchanged; AG idle; no new research, no optimizer redesign, no frontend changes.

---

## 1. Summary of what was implemented

| Work stream | Count | Status |
|---|---|---|
| B1 discretionary rulings (Display-only 13 + Fail-closed 33) | 46/46 | Implemented via B4 gate |
| B2 identity rulings | 6/6 | Implemented |
| Alias cleanups | 13/13 | Implemented |
| Retirement cleanup | 1/1 | Implemented |
| Catalog identity defects | 42/42 | Implemented (Phase A catalog cleanup) |
| B3 outstanding formulaic rules | 12/12 | Implemented/verified |
| B3 rules reaching the real optimizer (consumption proof) | 12/12 | Proven via `tests/test_b3_formulaic_consumption.py` |
| B4 explicit fail-closed gate | PASS | Proven via `tests/test_b4_authority_exhaustion_gate.py` (6 negative + 2 positive controls) |
| Canonical program reconciliation | 586/586 | Carried forward unchanged from the prior Codex-accepted wiring audit; this remediation only closes the 107 follow-up rows layered on top |
| Remaining bounded implementation items | 0/107 | `GLOBAL_PROGRAM_BOUNDED_REMEDIATION_REMAINING_CLAUDE.csv` is empty |

---

## 2. B4 — the central authority-exhaustion gate

Every rate-resolution and stacking entrypoint now runs an explicit refusal check as its **first executable action**, before any rule lookup:

- `app.data.authority_coverage_registry.economic_block_for_program(program_id)` — canonicalizes every known spelling of a program id (itself, `canonical_slug()`, and both directions of `CANONICAL_RUNTIME_SLUG_BINDINGS`) and checks it against:
  1. `_B1_DISCRETIONARY_RULING` — the 46-entry dict transcribed directly from the accepted Codex ruling (13 `DISPLAY_ONLY_ZERO_GUARANTEED`, 33 `FAIL_CLOSED`), asserted at import time to have exactly 46 entries.
  2. `_B4_RETIRED_OR_FAIL_CLOSED_IDENTITIES` — retired/duplicate identities (e.g. the Iceland post-production incentive, `us_ny_post_production_credit`).
  3. Pre-existing `COVERAGE_REGISTRY` blocking states.
- Wired into `program_rate_rules.resolve_program_rate()`, `program_rate_rules.classify_rate_resolution_failure()` (returns the new `RATE_FAILURE_AUTHORITY_EXHAUSTED = "AUTHORITY_EXHAUSTED_FAIL_CLOSED"` reason), and `canonical_stack_bridge.price_program_group_stack()` (covers both pair and group stacking).

**Adversarial proof, not absence-of-evidence.** `tests/test_b4_authority_exhaustion_gate.py` deliberately injects a live, obviously-fake `RateRule` under a fail-closed identity (directly and via a legacy alias) and proves the gate still refuses it; proves a blocked member poisons a pair/group stack; proves a display-only candidate stays discovered but visibly zero-guaranteed; proves an unrelated verified program still prices; and proves a simulated loader re-registration cannot reactivate a blocked identity. 8 tests, all passing.

---

## 3. B2 — identity rulings (6/6)

Three programs were rekeyed to new canonical `program_slug` values, with the old spelling preserved as a `PROGRAM_SLUG_ALIASES` entry so every prior reference (including the locked Lips Like Sugar baseline) still resolves:

| Old canonical spelling | New canonical spelling |
|---|---|
| `us_ca_film_credit` | `ca_film_30` |
| `ca_on_opstc` | `on_opstc` |
| `us_ny_film_credit` | `ny_state_film` |

Every accessor that keys off `program_slug` (`get_rate_rules`, `get_program_requirements`, `get_statutory_amounts`, `get_unknown_fields`, `get_program_doctrine`) gained a canonicalize-then-lookup fallback, so both spellings resolve identically. `jurisdiction_comparison.py`, `program_requirements.py`, `program_spend_rules.py`, `national_cultural_status.py`, and `optimization/stacking_rules.py` were updated to the new canonical spellings at their registration sites.

The highest-risk rekey — California, because it is Lips Like Sugar's locked-corpus winner — was verified byte-identical in economics before and after: `ca_film_30`, $3,459,278.90 / $8,524,375.10.

A bidirectional bug in `canonical_program_identity._aliases_for()` was found and fixed during this work: it only found aliases FOR a canonical slug, not the reverse, which silently broke `canonical_stack_bridge.py`'s alias reconciliation for stacking pairs after the rekey. Fixed by canonicalizing the input first.

---

## 4. B3 — the 12 outstanding formulaic rules

Full detail and per-program consumption-proof references are in `GLOBAL_PROGRAM_FORMULAIC_CONSUMPTION_CLAUDE.csv`. Five required no code change (existing implementation already correct, or the manifest's proposed figure was lower-confidence than an existing sourced citation already in the codebase); seven required real corrections:

- **cz_film_incentive / cz_film_incentive_animation** — added an 80% eligible-QPE-base cap via the existing `QpeCapRule` mechanism (no new mechanism invented).
- **fr_trip** — reclassified the VFX-uplift condition from `discretionary_band` (semantically wrong — it's an objective, uncollected project fact, not a genuine discretionary band) to `project_fact_dependent_uplift`, with a documented, sourced EUR-to-USD threshold conversion.
- **ma_ccm_rebate** — split a bundled spend+shooting-days condition into two independently disclosed conditions.
- **nl_nfpi** — replaced an unsupported 30/40% band with a single sourced 35% flat rate plus explicit conditions.
- **th_film_incentive** — discovered and fixed a **pre-existing mis-registration bug**: Thailand's incentive data had been incorrectly filed under `th_boi_incentive` by an earlier, now-superseded alias pass. Un-merged into its own identity, independent of the separately B1 FAIL_CLOSED `th_boi_incentive`.
- **us_or_opif** — removed a fabricated blended 26.2% rate; replaced with two disclosed component ceilings (20% payroll / 25% other), using the existing floor/ceiling disclosure mechanism rather than a new one, because Oregon's rate is genuinely two-component and neither component alone is a guaranteed floor.
- **us_tx_miip** — added explicit award/allocation and phased-resident-threshold conditions so a determinate program cannot be served as if it had a guaranteed floor when it does not.
- **za_nfvf_rebate** — new `DoctrineRecord`, independent of the separately B1 FAIL_CLOSED `za_dtic_foreign_film`.

**Consumption proof standard applied**: for each of the 12, `tests/test_b3_formulaic_consumption.py` proves reachability through two independent real pipeline paths — `production_discovery.discover_executable_jurisdictions()` (the real STAGE 2 discovery path) and `allocation_pricing.price_segment()` (the real production pricing kernel, via a synthetic `AccountAllocation`) — not merely a catalog/import/slug-resolution check. The four real projects' runtime CSV additionally shows all 12 (plus the other B3 programs) appearing as genuine discovery candidates across Little Utopia (22 considered), F#K Valentine's Day (25), Bad Hombres (22), and Lips Like Sugar (23).

**Data-conflict resolution**: `mt_mfc_rebate` — the manifest states a EUR 50,000 minimum; the existing codebase carries EUR 100,000 sourced from a directly-downloaded, pypdf-extracted 28-page official PDF. The stronger primary source was preserved; the manifest's weaker-sourced figure was not applied. This is a deliberate exception to "implement every manifest row," consistent with "do not invent/fabricate" and "do not reopen closed research with a weaker citation."

---

## 5. Catalog identity defects (42/42) and cleanup (13 aliases + 1 retirement)

Phase A catalog cleanup removed 42 duplicate/defective entries from `global_inventory_manifest_final.py` (164 → 122 entries), resolved 13 alias-only spelling variants into `PROGRAM_SLUG_ALIASES`, and retired 1 identity. `GLOBAL_PROGRAM_FINAL_LEGACY_PATH_GATE_CLAUDE.csv` classifies the disposition of every one of the 107 bounded work items (47 now-blocked stale runtime paths, 43 alias-only, 16 active canonical, 1 retired) and confirms no stale path can be reactivated (verified programmatically against the live `economic_block_for_program` gate, not by inspection).

---

## 6. Two self-inflicted bugs caught and fixed during this remediation

Documented in full for auditability — neither was papered over:

1. **`importlib.reload()` registry corruption (83 cascading test failures).** An early draft of the B4 gate's re-registration negative control used `importlib.reload(authority_coverage_registry)` / `importlib.reload(program_rate_rules)` to simulate a loader reactivating a blocked rule. Module reload re-executes only the reloaded module's body, resetting the global `_RULES_BY_PROGRAM` dict to empty, but does **not** re-trigger the already-cached dependent modules (`program_rate_rules_worldwide.py`, etc.) that populate it via their own module-level `register_rate_rules()` calls — permanently corrupting global state for the rest of the pytest session. Fixed by rewriting the test to use `register_rate_rules()` (the real, safe re-registration mechanism a loader would actually use) instead of `importlib.reload()`, with a `restore_rules_by_program` snapshot/restore fixture.

2. **Stale freshness-fingerprint versions (5 failures masking real fixes as regressions).** `canonical_evaluation._compute_fingerprint()` hashes `PROGRAM_RATE_RULES_VERSION`, `AUTHORITY_COVERAGE_REGISTRY_VERSION`, and `EXECUTABLE_JURISDICTION_REGISTRY_VERSION` to invalidate previously-persisted served evaluations. None had been bumped despite substantial mid-session content changes, so transient intermediate states from earlier edits were permanently cached and never invalidated — surfacing as 5 failures involving stale DB-persisted rows for Lips Like Sugar and F#K Valentine's Day (wrong classification, missing disclosure, wrong counts) even though the underlying functions were correct when called directly. Fixed by bumping all three version constants (`"1.3.0"`/`"1.4.0"`/`"1.2.0"`), forcing full fresh recomputation everywhere.

A third, smaller issue was caught in this closeout pass: `test_qpe_is_derived_from_real_account_universe_not_one_flattened_total` (`tests/test_fvd_canonical_input_assembly_repair.py`) selected its GR/MT/MU comparison structures via `{e["primary_jurisdiction"]: e for e in entries if e["is_fully_priced"]}` — a dict comprehension that silently keeps whichever combo structure happens to be *last* in iteration order for a given jurisdiction code, among many multi-program group/co-production combos that also report that jurisdiction as `primary_jurisdiction` with `program_slug: None`. This was already a coincidental pass before this remediation; the B3 additions enlarged the FVD candidate universe enough to change the "last" entry and break the coincidence (GR and MT resolved to the same combo, both reporting QPE `3701238.0`). Fixed by selecting the actual named single-program structure via `program_slug` instead of jurisdiction-code last-wins — this is what the test's own docstring was actually asserting.

---

## 7. Final verification

- **Focused bounded-remediation tests**: `tests/test_b4_authority_exhaustion_gate.py` (8) + `tests/test_b3_formulaic_consumption.py` (12) = 20/20 passing.
- **Full backend suite**: 4812 passed, 3 skipped, 0 failed (`pytest tests/ -q`), after fixing the one genuine regression found in this closeout pass (§6, item 3). No test was weakened, removed, or had its assertions loosened to obtain this result.
- **Four real projects** (`GLOBAL_PROGRAM_FOUR_PROJECT_FINAL_RUNTIME_CLAUDE.csv`):
  - Little Utopia → no winner (pre-existing, unrelated gate) — unchanged.
  - F#K Valentine's Day → no winner (pre-existing, unrelated gate) — unchanged.
  - Bad Hombres → `us_nm_film_credit`, $596,910.25 / $1,885,112.75 — unchanged.
  - Lips Like Sugar → `ca_film_30`, $3,459,278.90 / $8,524,375.10 — economics preserved across the B2 rekey.
  - All four show the new B3 programs entering their discovery universe (22–25 candidates considered), proving genuine optimizer reach beyond isolated unit tests.

---

## 8. Files changed

**Production code**: `authority_coverage_registry.py`, `program_rate_rules.py`, `program_rate_rules_worldwide.py`, `program_slug_aliases.py`, `canonical_stack_bridge.py`, `canonical_evaluation.py`, `canonical_program_identity.py`, `jurisdiction_comparison.py`, `program_requirements.py`, `program_spend_rules.py`, `national_cultural_status.py`, `stacking_rules.py`, `executable_jurisdiction_registry.py`, `canonical_executable_registry.py`, `global_inventory.py`, `global_inventory_manifest_final.py`.

**Tests**: 2 new files (`test_b4_authority_exhaustion_gate.py`, `test_b3_formulaic_consumption.py`), ~19 existing files updated (SUPERSEDED-documentation pattern for every assertion invalidated by an authorized B1/B2/B3 change; one genuine ordering-fragility fix per §6).

**Validation artifacts** (this remediation, all in `docs/validation/`): `GLOBAL_PROGRAM_BOUNDED_REMEDIATION_CLAUDE.md` (this file), `GLOBAL_PROGRAM_BOUNDED_IMPLEMENTATION_RESULTS_CLAUDE.csv`, `GLOBAL_PROGRAM_FINAL_DATABASE_PARITY_CLAUDE.json`, `GLOBAL_PROGRAM_FINAL_LEGACY_PATH_GATE_CLAUDE.csv`, `GLOBAL_PROGRAM_FORMULAIC_CONSUMPTION_CLAUDE.csv`, `GLOBAL_PROGRAM_FAIL_CLOSED_GATE_CLAUDE.json`, `GLOBAL_PROGRAM_FOUR_PROJECT_FINAL_RUNTIME_CLAUDE.csv`, `GLOBAL_PROGRAM_BOUNDED_REMEDIATION_REMAINING_CLAUDE.csv` (empty).

---

## 9. Next step

This is a Claude-implemented delta against a Codex-adjudicated manifest. Per the controlling authority for this workstream, Claude does not grant final acceptance to its own implementation: **Codex independently audits this Claude delta and performs final runtime acceptance across all four projects.**
