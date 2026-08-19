# Reinvestment + Qualification Opportunity Optimization — Closeout

**Generated:** 2026-08-18
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** `REINVESTMENT_AND_QUALIFICATION_OPPORTUNITY_OPTIMIZER_ACCEPTED` (scoped — see "Not reconnected" below)

Full account in `docs/architecture/CAPABILITY_LEDGER.md`'s "Reinvestment + Qualification Opportunity Optimization" entry. Summary:

## Forensic recovery

- `app/data/program_requirements.py` — 71 real, primary-source-cited `ProgramRequirementsProfile` records (ATL/per-person caps, min-local-spend, min-total-budget, cultural-test points/threshold). `EXISTS_BUT_DISCONNECTED`.
- `app/calculators/inkind_contribution.py` — full cash/FMV/deferred QPE-scenario model (Scenarios A-E). `EXISTS_BUT_DISCONNECTED`.
- `opportunity_discovery.py`, `production_recommendation_engine.py`, `optimization_engine.py`, `global_scenario_ranker.py`, `levers.py` — a much larger legacy recommendation system, tightly coupled to the superseded 0.1.0 pipeline's own data model. `LEGACY_ONLY` for this pass — not reconnected, disclosed.

## New adapter

`app/calculators/canonical_opportunity_bridge.py` — one canonical `CanonicalOpportunity` model, four discovery functions (fee/cap headroom, qualification gap, cultural gap disclosure, reinvestment/vendor participation), all reusing the two recovered modules unchanged.

## Runtime proof

Both LU and FVD: real Cyprus (30%) and New York (40%) ATL-cap headroom opportunities discovered; real cultural-test-gap disclosures (Croatia, Hungary, Italy, Lithuania, Malta) all fail-closed (`REQUIRES_SCREEN_ANALYZER_FACT`, zero fabricated scoring); baselines unchanged ($3,057,794.90 / $3,072,027.16). Qualification-gap detection proven correct at the unit level (real `mu_edb_incentive`/`gr_cash_rebate` min-local-spend data) but shows zero live gaps for these two well-funded real productions — a genuine, correct finding, not a missing wire-up.

## Not reconnected this pass

The larger legacy `opportunity_discovery.py`/`production_recommendation_engine.py` system, and live reinvestment auto-detection from real budgets (no project fact currently records deferred vendor consideration terms). Both disclosed with exact reasons, not silently dropped.

## Tests

18 new (13 unit + 5 served-runtime). Full suite: 4284 passed, 1 pre-existing unrelated failure, 1 skipped.

STOP.
