# National/Cultural Status Runtime Acceptance

**Generated:** 2026-08-19 · project economics engine `canonical-1.27.0`

## LU/FVD regression (byte-identical, re-verified after ENGINE_VERSION bump)

| Project | Accepted baseline NPC | Verified this pass |
|---|---:|---:|
| Little Utopia | $3,057,794.90 | $3,057,794.90 |
| FVD | $3,072,027.16 | $3,072,027.16 |

## Runtime proofs (Task 19)

**C. Canada demonstrates separate service vs national-content pathways** — confirmed at the served path on both real projects: every Canada candidate (priced under `ca_federal_pstc`, the service pathway, no cultural test required) now genuinely surfaces a `NATIONAL_STATUS_PATHWAY` opportunity pointing at `ca_federal_cptc` (the real, separate national pathway, 25% vs PSTC's 16%). Verified on LU and FVD's real Canada candidates.

**D. At least one non-Canada national/cultural pathway is surfaced** — Australia (`au_location_offset` → `au_producer_offset`, Significant Australian Content test, 40%/30% QAPE) and New Zealand (`nz_spg_international` → the NZ-production 40% grant's points test) are both confirmed, real, cited `NATIONAL_STATUS_REGIME_CONFIRMED` records with genuinely separate pathways.

**E. At least one cultural/role requirement correctly returns USER_FACT_REQUIRED or SCRIPT_FACT_REQUIRED** — the `NATIONAL_STATUS_PATHWAY` opportunity itself always resolves `REQUIRES_USER_FACT` (personnel/ownership facts genuinely unknown); `discover_cultural_test_gap_opportunity` continues to resolve `REQUIRES_SCREEN_ANALYZER_FACT` where applicable (unchanged from prior passes).

**F. A real economically-meaningful national-status opportunity identifies the specific program/uplift it unlocks** — Canada's opportunity explicitly names `ca_federal_cptc` and discloses the real, cited 25%/16% rate difference in its reasoning trace — never a fabricated number, never a bare "opportunity exists."

**G. A service incentive that does not require cultural status remains available without incorrectly becoming national content** — `ca_federal_pstc`, `au_location_offset`, `nz_spg_international` all continue to price exactly as before (byte-identical baselines); the national-status opportunity is additive disclosure only, never a replacement or gate on the existing candidate.

**H. No unresolved national-status structure enters comparable ranking** — `test_national_status_opportunity_never_contaminates_ranking` confirms `is_directly_comparable` is unaffected by the presence of a `NATIONAL_STATUS_PATHWAY` opportunity on a candidate.

## Control cases (Task 8/9)

1. **Canada** (mandatory) — strict 10-point alternative-group test (CAVCO); UNLOCKS_ENHANCED_RATE (25% vs 16%, same federal lane).
2. **Australia** — holistic/qualitative test ("no single element determinative"); UNLOCKS_SEPARATE_INCENTIVE (a genuinely different program, not a rate bump on the same one); official co-production automatically satisfies the test (explicit authority statement).
3. **New Zealand** — points test OR official co-production as explicit alternatives; recovered from this same multi-pass arc's own prior research (Task 4 discipline — not re-researched).
4. **Ireland** — entity/ownership-based (Irish-resident production company required), not a points test; already fully resolved as the base incentive's own gate (no separate program).
5. **United States** — a genuine, researched `NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED` finding: no current federal film tax credit, no federal "American content" certification analogous to Canada's/Australia's, confirmed via 2 independent sources.

## A real correctness fix verified this pass

CAVCO's real rule is "director OR writer must be Canadian" (2 points each toward a 6/10 minimum) — never both independently mandatory. The prior encoding in `cultural_qualification_model.py` required both unconditionally, a genuine defect. Fixed via a new `alternative_group` mechanism (additive, only affects `ca_federal_cptc`'s director/writer rows — every other of the 24 covered programs' behavior is unchanged). LU's real personnel (director AU, writer GB — both non-Canadian) still correctly `HARD_FAIL`s under the corrected rule; a hypothetical Canadian-writer/foreign-director case now correctly `QUALIFIES` (previously would have incorrectly `HARD_FAIL`ed).

## Guards confirmed

- Canonical pricing/NPC/ranking mathematics: unchanged (confirmed by byte-identical baselines, re-verified after `ENGINE_VERSION` bump).
- No legacy 0.1.0 economic path served.
- No new optimizer/pricing/ranking/cultural engine created — `national_cultural_status.py` is a data registry consumed by the existing `canonical_opportunity_bridge.py` pattern.
- Official co-production treaty-universe research: not performed (explicitly out of scope, per instruction — a separate, later phase). Existing authority-established relationships (Australia/co-pro, New Zealand/co-pro) encoded without fabricating any country-pair eligibility.

STOP.
