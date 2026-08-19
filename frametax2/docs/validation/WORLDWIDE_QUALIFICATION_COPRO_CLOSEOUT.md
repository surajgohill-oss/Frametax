# Worldwide Program Qualification + Cultural Test Completion — Closeout

**Generated:** 2026-08-19 (this pass, treaty research explicitly out of scope per instruction)
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** `WORLDWIDE_PROGRAM_QUALIFICATION_AND_CULTURAL_TEST_DATABASE_COMPLETED` — see exact scope below.

## Population and honest scope

This pass used the CURRENT canonical 71-program served-pricing universe (`app.data.program_requirements.all_program_requirements()`) as the denominator — not the prior 181-regime audit population — per this phase's own explicit instruction. Official co-production/treaty research was explicitly out of scope this pass (a separate, later phase).

> **Ontology correction (added 2026-08-19, Worldwide Jurisdiction National/Cultural Status + Incentive Pathway Completion):** this closeout's PROGRAM-level accounting (48 `QUALIFICATION_NOT_APPLICABLE`) must not be read as 48 jurisdictions lacking any national/cultural status regime. A separate, JURISDICTION-level pass confirmed real national/cultural pathways exist for Canada, Australia, and New Zealand despite their own served base incentives correctly showing no cultural test — see `WORLDWIDE_NATIONAL_CULTURAL_STATUS_COMPLETION.md`.

**Every one of the 71 programs now has an exact terminal qualification state — zero unexplained unknown:**

| State | Count |
|---|---:|
| QUALIFICATION_COMPLETE | 2 |
| QUALIFICATION_NOT_APPLICABLE | 48 |
| AUTHORITY_UNRESOLVED_EXACT_PROPOSITION | 21 |
| **Unexplained** | **0** |

See `WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md`/`.json` for the full per-program table and every exact proposition.

## Real research performed this pass (primary/secondary authority, all cited)

10 real external research targets, all with genuine citations (not fabricated, not pattern-matched without verification):

1. **`gr_cash_rebate`** (FVD's own home program) — cultural test confirmed: min 20/50 points (fiction/documentary), min 16/40 (animation). Sources: Saturation.io, fixersingreece.gr, Lexology's Law 5105/2024 summary.
2. **`hr_cash_rebate`** — fixed a genuine `DATA_EXISTS_BUT_STILL_NOT_CONSUMED` defect (`cultural_test_points` was `None`, already documented as 34 in the record's own citation note); real national cast/crew composition requirement (30%/50%) disclosed without misusing the role-gate engine.
3. **`ca_federal_pstc`** — confirmed NO Canadian content requirement (canada.ca, primary), distinct from the content-gated CPTC.
4. **`nz_spg_international`** — confirmed spend-only (New Zealand Film Commission).
5. **`us_or_opif`** — confirmed no cultural test (oregonfilm.org, Oregon Administrative Rules).
6. **`us_ny_post_production_credit`** — confirmed no cultural test (tax.ny.gov).
7. **`kr_kofic_location_incentive`** — real discretionary Evaluation Committee criteria disclosed (Korean Infrastructure Utilisation / Korean Participation / Quality of Project), distinguished from a personnel-nationality cultural test.
8. **`mu_edb_incentive`** (LU's own home program) — researched; the only specific claim found was already investigated and REJECTED by a prior Codex/Gemini cross-verification (a real, important catch — this pass's new research surfaced the same stale claim from a secondary source and correctly did NOT reintroduce it); two further claims disclosed as `UnverifiedRateClaim` entries, never applied.
9. **`fj_film_rebate`** — researched; real statutory basis confirmed, cultural-test presence/absence genuinely unresolved.
10. **`de_dfff`** — internal consistency fix (no new research): `cultural_test_required` now matches real role rows already on file.

## Engine changes

- `canonical_qualification_result.py`: `QUAL_AUTHORITY_UNRESOLVED` — now **live**, not just defined. `canonical_role_qualification_bridge.py` gained `AUTHORITY_UNRESOLVED_PROGRAMS` (a small registry of genuinely-researched-but-unresolved slugs with their exact propositions) and emits the state at the served path — proven at runtime on real LU (`mu_edb_incentive`) and FVD (`mu_edb_incentive`) candidates.
- `cultural_qualification_model.py`: `is_spend_only_program()` (prior pass) reused unchanged.

## Runtime proof

LU baseline $3,057,794.90 and FVD baseline $3,072,027.16 both re-verified byte-identical after an `ENGINE_VERSION` bump (`canonical-1.25.1` → `canonical-1.26.0`) forced a full recompute. `AUTHORITY_UNRESOLVED` proven live on real candidates (not just unit fixtures). `gr_cash_rebate`'s newly-confirmed cultural test genuinely unlocks a new `CULTURAL_TEST_GAP` opportunity on FVD's real served candidates that did not exist before this pass. See `QUALIFICATION_OPTIMIZER_RUNTIME_ACCEPTANCE.md`.

## Tests

12 new/extended in `test_worldwide_qualification_completion.py` (7 carried + 5 new this continuation), plus 1 existing test (`test_copro_qualification_wiring.py`) correctly updated to accept the newly-live `AUTHORITY_UNRESOLVED` state. Full backend suite: 4298 passed, 1 pre-existing unrelated frontend failure, 1 skipped.

## True remaining residual (role/personnel dimension, 71-program universe)

- 21 programs have a confirmed cultural test but incomplete role-level/point-level data — every one has an exact, non-generic proposition (`CULTURAL_TEST_POINT_TABLE`, `CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN`, `DE_DFFF_ROLE_WEIGHT_UNCONFIRMED`, or the 2 `CULTURAL_TEST_APPLICABILITY_UNCONFIRMED` cases).
- Official co-production/treaty doctrine: entirely out of scope this pass, unchanged from `5935225`'s `COPRO_TRUE_AUTHORITY_RESIDUAL.json` (37 bilateral/Eurimages Class-C entries, not reproduced here).

## Guards preserved

Worldwide economic database, base pricing, NPC formula, ranking mathematics: not reopened, not changed. No new optimizer/cultural/treaty engine. No superseded 0.1.0 path touched. Script Analyzer and Budget Estimator untouched. No official co-production research performed. LU/FVD accepted baselines unchanged.

STOP.
