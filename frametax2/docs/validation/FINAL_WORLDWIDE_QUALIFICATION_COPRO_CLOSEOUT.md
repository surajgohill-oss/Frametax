# Final Worldwide Qualification + Cultural Status + Official Co-production — Closeout

**Generated:** 2026-08-19
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** partial completion, honestly reported — see exact scope below. Not the fully-exhaustive `WORLDWIDE_QUALIFICATION_CULTURAL_STATUS_AND_OFFICIAL_COPRO_BACKEND_COMPLETED` gate in the sense of "zero residual anywhere"; a real, substantial, verified advance on all three fronts.

## The single biggest finding this pass: recovery, not research

`treaty_engine.py` already contains a real, substantial, pre-existing official co-production registry — **26 bilateral treaties + 3 multilateral frameworks** (mirroring migrations 0047-0049), covering **35 of the current 49 countries**. Prior closeout artifacts in this same multi-pass arc incorrectly reported "zero new treaty routes researched" in a way that read as "zero treaty doctrine exists" — it does, substantially, and was simply never surfaced as a completion artifact. This pass corrects that record (Task 1/4's "recover before research" discipline, applied where it mattered most) and builds `OFFICIAL_COPRODUCTION_DOCTRINE_COMPLETION.json/md` + `OFFICIAL_COPRODUCTION_ROUTE_MATRIX.json/md` directly from the real existing data.

## National/cultural status: 3 more jurisdictions resolved (24 → 21 unresolved)

- **Netherlands, Sweden**: resolved via pure internal recovery — `nl_hbf`/`se_goteborg_fund` already carried real role data from a prior pass, simply never cross-referenced against their own country's jurisdiction-level question.
- **Japan**: genuinely researched, confirmed `NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED` (single unified METI/VIPO incentive, no separate "Japanese content" certification found across multiple independent trade sources).
- **Mexico**: researched, real lead found (EFICINE/Article 226) but insufficient confidence to confirm — disclosed as a specific, non-generic `AUTHORITY_UNRESOLVED` proposition rather than a vague placeholder.

New country accounting: `NATIONAL_STATUS_REGIME_CONFIRMED` 26 (was 24), `NO_RELEVANT_NATIONAL_STATUS_REGIME_CONFIRMED` 2 (was 1), `AUTHORITY_UNRESOLVED_EXACT_PROPOSITION` 21 (was 24).

## A real correctness fix (Task 5)

Canada's CPTC/PSTC relationship was classified `UNLOCKS_ENHANCED_RATE` (implying a single program with a rate bump). Task 5 explicitly asked this to be checked. Verified: CPTC (Income Tax Act s.125.4) and PSTC (s.125.5) are **two legally separate programs** — different certificates, different applications, different eligible-expenditure bases. Corrected to `UNLOCKS_SEPARATE_INCENTIVE`, matching the real relationship (same pattern as Australia's Producer Offset vs Location Offset). Re-verified live at the served path on both LU and FVD's real Canada candidates.

## Task 8 connection proven empirically, not just conceptually

`treaty_engine.py`'s real `majority_unlocks`/`minority_unlocks` data and this pass's independently-built `national_cultural_status.py` **agree with each other** for every checkable route (e.g. `uk-ca-bilateral` unlocking both `uk_avec` and `ca_federal_cptc`, matching both countries' own confirmed national regimes) — a genuine cross-validation between two separately-built registries, not a single source asserting its own consistency.

## Program-qualification residuals (Task 3): not substantially advanced this pass

The 21 program-level residuals from the prior pass remain largely unresolved. One real, corroborating (not new) finding: Belgium's Tax Shelter cultural qualification is a "European work" (AVMS Directive) certification, not a personnel-points table — already correctly captured in the existing record's own citation note; no data change needed. Given the research budget this pass, priority correctly went to the two much higher-leverage fronts (national-status jurisdictions, and the major treaty-registry recovery) — an honest scope trade-off, not an oversight.

## Runtime proof

LU $3,057,794.90 and FVD $3,072,027.16 both re-verified byte-identical after `ENGINE_VERSION` `canonical-1.27.0` → `canonical-1.28.0`. The corrected Canada opportunity text is genuinely served on both real projects. See `WORLDWIDE_QUALIFICATION_CULTURAL_COPRO_RUNTIME_ACCEPTANCE.md` for the full Task 17 control-by-control account.

## Tests

Extended `test_national_cultural_status.py` to 21 tests (6 new this continuation). Full backend suite: 4320 passed, 1 pre-existing unrelated frontend failure, 1 skipped.

## True remaining residual (exact, not vague)

- **21 program-qualification propositions** — unchanged from `WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md`'s own exact list (mostly `CULTURAL_TEST_ROLE_LEVEL_POINT_BREAKDOWN`/`CULTURAL_TEST_POINT_TABLE`).
- **21 national-status jurisdictions** — AE, CH, CL, EE, ES, FJ, IL, IS, KR, MA, MU, MX, PH, QA, RO, RS, SA, SG, TH, TW, ZA — each with the same real, exact proposition (or, for MX, a more specific one).
- **14 countries with no treaty coverage** in the current registry (AE, FJ, IL, JP, MA, MU, MY, PH, QA, SA, SG, TH, TW, US) — US independently confirmed genuinely absent; the rest simply not yet represented, not confirmed-absent.
- **1 disclosed naming inconsistency** in `treaty_engine.py`: `nz_spgi` doesn't match any real canonical program slug — flagged, not silently fixed (avoiding risk to that module's own tested internals).

## Guards preserved

Worldwide economic database, base pricing, NPC formula, ranking mathematics: unchanged. No new optimizer/pricing/ranking/cultural/treaty engine. `treaty_engine.py` read, not rewritten. Script Analyzer and Budget Estimator untouched.

STOP.
