# Qualification Optimizer Runtime Acceptance

**Generated:** 2026-08-19 (updated, same-day continuation) · project economics engine `canonical-1.26.0`

## LU/FVD regression (byte-identical, re-verified after ENGINE_VERSION bump)

| Project | Accepted baseline NPC | Verified this pass |
|---|---:|---:|
| Little Utopia | $3,057,794.90 | $3,057,794.90 |
| FVD | $3,072,027.16 | $3,072,027.16 |

## Real control cases proven

1. **Known mandatory role, satisfied** — `ca_federal_cptc` with all-Canadian director/writer/producer/lead_cast → `QUALIFIES`. (`test_canonical_role_qualification_bridge.py`)
2. **Known mandatory role, violated** — LU's real personnel (director AU, writer GB, producer US) → `HARD_FAIL` against `ca_federal_cptc`'s real Canadian-role gate. Proven at the served path on real project data.
3. **Missing user fact** — `ca_federal_cptc` with zero personnel known → `USER_FACT_REQUIRED`.
4. **Point-bearing role never hard-required** — `uk_avec`'s writer/director/etc. are point-bearing; zero people known → `NOT_APPLICABLE`, never `HARD_FAIL`.
5. **Registry presence != qualification** — `ca_federal_cptc` is in the covered-slug registry but still resolves `USER_FACT_REQUIRED`/`HARD_FAIL` depending on facts, never auto-`QUALIFIES`.
6. **Missing rule data != hard failure** — a program with zero rule rows resolves `RULE_DATA_INCOMPLETE`, never `HARD_FAIL`.
7. **Spend-only classification correctly resolves NOT_APPLICABLE** — `nz_spg_international` → `NOT_APPLICABLE`, confirmed via real NZFC citation.
8. **Cultural-test data-consumption fix verified** — `hr_cash_rebate.cultural_test_points == 34` (was `None`), `cultural_test_threshold == 12` unchanged.
9. **`AUTHORITY_UNRESOLVED` now live, runtime-proven (new this pass)** — `mu_edb_incentive` (LU's own real home program) and `fj_film_rebate` both genuinely resolve `AUTHORITY_UNRESOLVED` at the served path, each carrying its exact researched proposition (`evaluate_role_qualification` → `_authority_unresolved_result`), distinct from the generic `RULE_DATA_INCOMPLETE` branch. Confirmed on real LU/FVD candidates, not just unit fixtures.
10. **A real cultural-test base-eligibility case newly unlocked** — `gr_cash_rebate` (FVD's own real home program) now genuinely surfaces a `CULTURAL_TEST_GAP` opportunity (`REQUIRES_SCREEN_ANALYZER_FACT`) that did not exist before this pass's research confirmed its real 20/50 point structure — proven on FVD's actual served candidates.
11. **Confirmed-`False` programs correctly resolve `NOT_APPLICABLE` at the role-gate layer** — `ca_federal_pstc`, `us_or_opif`, `us_ny_post_production_credit`, `kr_kofic_location_incentive` all now carry real citations backing their `cultural_test_required=False` classification.

## Not proven this pass (genuine gaps, not silently skipped)

- No new bilateral/multilateral route was researched (explicitly out of scope this pass per instruction) — no new official co-production runtime case beyond what `5935225` already proved.
- No real program in the current 71-program universe was confirmed this pass where a cultural test's consequence is an UPLIFT/enhancement with a fully-cited numeric structure (Cyprus's `cultural_test_uplift` fact remains explicitly "exact thresholds unconfirmed").
- Role-level (personnel) point/weight breakdowns remain unresolved for 21 programs — see `WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md`'s exact-proposition table; each has a specific, non-generic missing proposition, never a vague "needs research."

## Guards confirmed

- Canonical pricing/NPC/ranking mathematics: unchanged (confirmed by byte-identical baselines, re-verified after `ENGINE_VERSION` bump forced full recompute).
- No legacy 0.1.0 economic path served (unchanged from prior phases' regression tests, all still passing).
- No stale/rejected claim reintroduced: the Mauritius 90%-filming claim, previously investigated and REJECTED by a prior Codex/Gemini cross-verification, was found again this pass via a secondary source and correctly NOT re-applied — regression-tested (`test_mauritius_prior_rejected_claim_not_reintroduced`).
- Full backend suite: see closeout for the exact count from this pass's final run.

STOP.
