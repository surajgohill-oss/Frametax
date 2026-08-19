# Canonical Co-production Qualification Reconnection — Closeout

**Generated:** 2026-08-19
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** `CANONICAL_COPRO_QUALIFICATION_RECONNECTED_TRUE_RESIDUAL_LOCALIZED`

Full account in `docs/architecture/CAPABILITY_LEDGER.md`'s matching entry. Summary:

## Control population

Codex's own 181-regime audit (`CODEX_COPRO_ROLE_QUALIFICATION_COMPLETENESS.md`/`.json`, commit `436fe6d`) — used verbatim as the control population, no reconstruction.

## What was reconnected

1. **First shared disconnect (Task 3)** — `canonical_evaluation._opportunities_for_candidate()` never called `cultural_qualification_model.evaluate_program_eligibility()`, never read real project personnel. Fixed via `app/calculators/canonical_role_qualification_bridge.py`, a thin adapter reusing `cultural_qualification_model.py` (24 real program-slug registry, unchanged) and the real, persisted `ProjectPerson`→`TalentProfile` data — no new engine.
2. **One canonical qualification result contract (Task 4)** — `app/calculators/canonical_qualification_result.py`: `QUALIFIES`/`HARD_FAIL`/`CURABLE_GAP`/`USER_FACT_REQUIRED`/`SCRIPT_FACT_REQUIRED`/`RULE_DATA_INCOMPLETE`/`NOT_APPLICABLE`, never collapsed.
3. **Treaty bridge disconnect** — the bilateral and Eurimages call sites in `canonical_evaluation.py` never threaded `majority_pct`/`minority_pct`/`cultural_test_passed` at all (always implicit `None`). Now reads three real `ProjectFact` keys and threads them through. Output unchanged for LU/FVD (neither has these facts on file) — the plumbing is now real, not a behavior change.
4. **Wired disclosure-only** — `role_qualification` attached to every priced single-program candidate's `calculation_trace_json`, passed through `canonical_production_view.py`. Never a pricing/admission/ranking gate (Task 11 preserved).

## Two real bugs found and fixed during this pass (own test suite)

- Empty required-gate list (e.g. `uk_avec`, all point-bearing, none `required`) was being classified `QUALIFIES` (an empty-`all()` truthiness bug) instead of `NOT_APPLICABLE`.
- A program with zero rule rows was classified `NOT_APPLICABLE` via `has_cultural_test()`'s ambiguous `False` (conflating "confirmed spend-only" with "no data recorded yet"). Added `is_spend_only_program()` (one-line, additive) to `cultural_qualification_model.py` to disambiguate; zero-row non-spend-only programs now correctly resolve `RULE_DATA_INCOMPLETE`.

## Runtime proof

LU's real personnel (director AU, writer GB, producer US — `little_utopia_people.py`'s own real facts) genuinely `HARD_FAIL`s `ca_federal_cptc`'s real Canadian-role gate — discovered, not fabricated. Both baselines unchanged: LU $3,057,794.90, FVD $3,072,027.16. 113/137 LU candidates and equivalent FVD candidates now carry a real `role_qualification` result (`RULE_DATA_INCOMPLETE` for the 157 uncovered slugs, `NOT_APPLICABLE`/`USER_FACT_REQUIRED`/`HARD_FAIL` for the 24 covered ones) — no fabricated results anywhere.

## True authority residual

`COPRO_TRUE_AUTHORITY_RESIDUAL.json`/`.md` — mechanical transform of Codex's own audit (no new research): 24 regimes now have their role dimension genuinely consumed (still Class C overall — other dimensions remain partial); 37 bilateral/Eurimages entries have real plumbing but genuinely missing role-level rule data (unchanged Class C); 108 regimes remain Class D (no role-level data anywhere in this codebase — genuine authority research required, propositions preserved from Codex's own `targeted_research_set`).

## Tests

14 new (`test_canonical_role_qualification_bridge.py` 9, `test_copro_qualification_wiring.py` 5). Full suite: 4286 passed (excludes `test_ingestion_phase_f.py`, uncollectable in this environment due to a missing optional `fitz` dependency, unrelated), 1 pre-existing unrelated frontend failure, 1 skipped.

STOP.
