# Proactive Opportunity Discovery Reconciliation — Closeout

**Generated:** 2026-08-18
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** `PROACTIVE_OPPORTUNITY_DISCOVERY_CANONICALLY_RECONNECTED`

Full account in `docs/architecture/CAPABILITY_LEDGER.md`'s "Proactive Opportunity Discovery Reconciliation" entry. Summary:

## Legacy trace (Task 1)

Directly read `opportunity_discovery.py`, `production_recommendation_engine.py`, `optimization_engine.py`, `global_scenario_ranker.py`, `levers.py`. All five import the superseded 0.1.0 data model (`StructuringPath`, `AccountQualification`, `JurisdictionGraph`) — confirmed `REJECT_STALE` for economics/ranking, not inferred from filenames. No reusable, engine-agnostic function exists in any of them; their behavior pattern (proactive, budget-triggered opportunity surfacing) was reproduced fresh against canonical data — classified `PROVEN_ABSENT`.

## New capability

Two new functions in the existing `canonical_opportunity_bridge.py`:
- `discover_potential_reinvestment_candidates()` — proactive, budget-triggered vendor-participation candidates (no known deal terms required), gated to the production's own home jurisdiction to avoid duplicate copies across every alternative-jurisdiction candidate.
- `discover_qualification_lever_opportunities()` — a real movable-component budget amount proposed as a lever to close a real qualification gap, always `PROPOSED_CHANGE`, never auto-applied.

Plus a `fact_classification` vocabulary (Task 8) and `trigger` provenance field on every opportunity, and a Screen Analyzer input contract (`screen_analyzer_fact_contract.py`) expressed against the existing generic `ProjectFact` model — no new table, no migration, Screen Analyzer itself not built.

## Runtime proof

LU: real `POTENTIAL_REINVESTMENT_OPPORTUNITY` for real vfx spend $52,500 (Mauritius baseline). FVD: real one for real post spend $172,904 (Greece baseline). Both `REQUIRES_USER_FACT`, no fabricated cash/deferred split. Neither project has a live qualification gap (both real productions comfortably clear their home thresholds — a genuine zero, proven correct via the function's own unit tests against real Mauritius fixture data). Baselines unchanged: LU $3,057,794.90, FVD $3,072,027.16.

## Not reconnected this pass

`opportunity_discovery.py` and its four siblings remain `LEGACY_ONLY`, re-confirmed by direct trace this phase.

## Tests

6 new (`test_proactive_opportunity_discovery.py`). Full suite: 4272 passed (excludes `test_ingestion_phase_f.py`, uncollectable in this environment due to a missing optional `fitz` dependency — unrelated to this work), 1 pre-existing unrelated frontend failure, 1 skipped.

STOP.
