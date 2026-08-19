# Qualification Optimizer Runtime Acceptance

**Generated:** 2026-08-19 · project economics engine `canonical-1.25.1`

## LU/FVD regression (byte-identical, re-verified after ENGINE_VERSION bump)

| Project | Accepted baseline NPC | Verified this pass |
|---|---:|---:|
| Little Utopia | $3,057,794.90 | $3,057,794.90 |
| FVD | $3,072,027.16 | $3,072,027.16 |

## Real control cases proven (carried from `5935225`, re-verified after this pass's data changes)

1. **Known mandatory role, satisfied** — `ca_federal_cptc` with all-Canadian director/writer/producer/lead_cast → `QUALIFIES`. (`test_canonical_role_qualification_bridge.py`)
2. **Known mandatory role, violated** — LU's real personnel (director AU, writer GB, producer US) → `HARD_FAIL` against `ca_federal_cptc`'s real Canadian-role gate. Proven at the served path on real project data.
3. **Missing user fact** — `ca_federal_cptc` with zero personnel known → `USER_FACT_REQUIRED`.
4. **Point-bearing role never hard-required** — `uk_avec`'s writer/director/etc. are point-bearing; zero people known → `NOT_APPLICABLE`, never `HARD_FAIL`.
5. **Registry presence != qualification** — `ca_federal_cptc` is in the covered-slug registry but still resolves `USER_FACT_REQUIRED`/`HARD_FAIL` depending on facts, never auto-`QUALIFIES`.
6. **Missing rule data != hard failure** — a program with zero rule rows (e.g. `hr_cash_rebate` before this pass's fix, and the ~106 remaining Class-D regimes) resolves `RULE_DATA_INCOMPLETE`, never `HARD_FAIL`.
7. **Spend-only classification correctly resolves NOT_APPLICABLE (new this pass)** — `nz_spg_international` → `NOT_APPLICABLE`, confirmed via real NZFC citation.
8. **Cultural-test data-consumption fix verified** — `hr_cash_rebate.cultural_test_points == 34` (was `None`), `cultural_test_threshold == 12` unchanged.

## Not proven this pass (genuine gaps, not silently skipped)

- No new bilateral/multilateral route was researched, so no NEW official co-production runtime case was added beyond what `5935225` already proved (FVD's real Eurimages membership → `CO_PRO_OPPORTUNITIES`, Mauritius's real zero-treaty-membership → correct proven-zero).
- `AUTHORITY_UNRESOLVED` is defined in the contract but not yet emitted by any live code path — no runtime case exists for it yet.
- No real program in the current universe was found this pass where a cultural test's consequence is confirmed as an UPLIFT/enhancement with a fully-cited numeric structure (Cyprus's `cultural_test_uplift` fact remains explicitly "exact thresholds unconfirmed" per its own existing citation, unchanged this pass).

## Guards confirmed

- Canonical pricing/NPC/ranking mathematics: unchanged (confirmed by byte-identical baselines).
- No legacy 0.1.0 economic path served (unchanged from prior phases' regression tests, all still passing).
- Full backend suite: 4291 passed, 1 pre-existing unrelated frontend failure, 1 skipped.

STOP.
