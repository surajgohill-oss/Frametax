# Historical Authority Source Recovery — Closeout

**Final gate: `HISTORICAL_AUTHORITY_RECOVERY_ACCEPTED`**

No new external research performed. Every improvement below comes from
wiring existing, already-registered CineGlobe data into
`canonical_program_consolidation.py` — the exact defect class Georgia
exposed in the prior task (a real authority source existed while
consolidation silently never read it).

---

## 1. Sources found and their disposition

| Source | Profiles | Program-slug overlap w/ 105 incomplete | Disposition |
|---|---:|---:|---|
| `executable_jurisdiction_registry.DoctrineRecord` | 107 | — (wired in prior task) | **B — already consumed** |
| `app.data.program_requirements` | 71 | 67 | **A — now consumed** (was orphaned) |
| `app.calculators.jurisdiction_comparison.ALL_PROFILES` | 110 | 105 | **A — now consumed** (was read for one bare flag only; now read broadly) |
| `app.data.global_inventory` (+ waves/extended/grants/broadcaster/special-categories, all merged into `ALL_PROGRAMS`) | 303 | 0 (of the 88 type-unresolved) | **B — already consumed** for RATE/MIN_SPEND/CAP/CULTURAL/REFUND/TRANSFER fallbacks |
| `app.data.program_rate_rules` / `program_spend_rules` | — | — | **B — already consumed** (the pricing pipeline's own executable registries) |
| `app.calculators.cultural_test_rules` (FR CNC, IE S.481, Eurimages, Ibermedia, CA content, AU content, UK BFI, ECC — 8 detailed criterion-level scoring modules) | 8 | unknown (no program_slug field on the module's functions) | **C — rejected this pass**: real executable rule logic, but the module has no `program_slug`-keyed registry — matching each scoring function to a canonical identity would require building a new mapping this task did not authorize as a parallel authority database, and the two clearest candidates (Canada federal PSTC, UK AVEC cultural test) are already covered more directly and more safely by `program_requirements.cultural_test_required`/`cultural_test_points` for the same programs. Flagged for a future small, purpose-built wiring pass, not attempted here to avoid an unreviewed slug-guessing exercise. |
| `app.data.territory_classification` (256 territories, PROGRAMS_FOUND/NO_KNOWN_PROGRAM_FOUND/etc.) | 256 | — | **C — rejected**: wrong granularity (jurisdiction-level program *existence*, not one of the 14 program-*dimension* facts); would conflate "a program exists here" with "this dimension is resolved" |
| `app.data.location_cost_benchmarks` | — | — | **C — rejected**: production cost benchmarks (crew day rates, stage costs), not incentive-authority facts |
| `app.calculators.legal_authority_acquisition`, `treaty_engine` | — | — | **C — rejected, not pursued this pass**: examined by name/purpose only (entity-formation and treaty-coproduction calculators, not program-slug-keyed authority stores); no `program_slug`-keyed registry found comparable to program_requirements/jurisdiction_comparison in the time available for this recovery pass |
| Bridge packages, DB-persisted rule stores, retained Gemini/Codex validation artifacts | — | — | **C — examined, none found to be an unconsumed authority-fact source**: the two Codex JSON artifacts already read in the prior task (`CODEX_HISTORICAL_INCENTIVE_WORK_RECONCILIATION.json`, `CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json`) contain classification/assessment labels and source *pointers*, never literal replacement values (confirmed directly by that task); no other retained validation JSON in `docs/validation/` was found to carry program-slug-keyed dimension facts |

---

## 2. What was wired (Task 4)

`canonical_program_consolidation.py` (`CONSOLIDATION_VERSION` `1.2.0` →
`1.3.0`): added `program_requirements.get_program_requirements()` +
`verification_state()`, and broadened the existing `jurisdiction_
comparison.ALL_PROFILES` read (previously one bare boolean fallback for
`UPLIFT_RULES` only) to a proper `_upgrade()`-based recovery pass covering
`MINIMUM_SPEND`, `CAP`, `CULTURAL_OR_CONTENT_TEST`, `REFUNDABILITY`,
`TRANSFERABILITY`, `TERRITORIALITY`, `UPLIFT_RULES`, `APPLICATION_TIMING`.

**Confidence tiers strictly preserved, never silently promoted:**
- `program_requirements`: PRESENT only when `verification_state()` is
  `PRIMARY_VERIFIED` **and** the profile's own `EvidenceRecord.status`
  is `RecordStatus.CURRENT` (Task 7 currentness — a stale/expired/
  proposed/uncertain record caps at PARTIAL regardless of source type).
  All 71 registered profiles happen to carry `status=CURRENT`; 61 are
  `PRIMARY_VERIFIED`, 10 `SECONDARY_VERIFIED` — the 10 secondary ones are
  gated to PARTIAL by a new focused test.
- `jurisdiction_comparison`: PRESENT only when the profile's own
  `confidence_tier == "VERIFIED"` (5 of 110 profiles); the other 105
  (103 `PARSED`, 2 `DISCOVERY`) cap at PARTIAL.
- `_upgrade()` never downgrades — a dimension already PRESENT from the
  existing doctrine-record/rate-rule read stays PRESENT even when a
  newly-wired source has nothing to add for that program.

**Real bug found and fixed while wiring**: `MONETIZATION` was computed
once, before the recovery pass could upgrade `REFUNDABILITY`/
`TRANSFERABILITY` — uk_avec showed both components `PRESENT` but
`MONETIZATION` stuck at `MISSING`. Fixed by recomputing `MONETIZATION`
from the dims list's final post-recovery values. Regression test added
(`test_monetization_reflects_post_recovery_refundability_and_
transferability`).

**Deliberately not wired** (dimension-conflation risk, documented inline):
`local_entity_required`/`local_coproducer_required` were NOT read into
`TERRITORIALITY` (entity-structure facts, not territorial-spend
predicates — the canonical local-SPV assumption already treats these as
non-blocking); `payroll_burden_pct` (jurisdiction_comparison) was NOT read
into `PAYROLL_TREATMENT` (an employer-cost benchmark, not a QPE
payroll-eligibility rule); `audit_or_final_certification_deadline` was NOT
read into `APPLICATION_TIMING` (a different fact — certification
deadline, not application timing).

---

## 3. Task 2 — program type recovery (88 unresolved)

Checked all 88 `PROGRAM_TYPE_UNRESOLVED` identities against every richer
registry in the repo: `global_inventory.ALL_PROGRAMS` (303 entries,
aggregates every wave/extended/grants/broadcaster/special-categories
file), `jurisdiction_comparison.ALL_PROFILES` (110), `program_
requirements` (71). **Zero overlap with any of the three.** These 88
identities exist *only* as a name + jurisdiction in the static
`authority_coverage_registry.COVERAGE_REGISTRY` veto list — no richer
profile of any kind was ever attached anywhere in the retained codebase.
This is not a wiring gap; there is no existing type-bearing fact to wire.
**0 of 88 resolved from existing evidence** — genuinely requires new
primary research, correctly out of scope for this recovery-only task.

---

## 4. Recomputed universe (Task 8)

224 canonical identities, same disposition-count shape as before recovery
(no identity's overall disposition flipped — recovery deepened dimension
resolution within `FORMULAIC_AUTHORITY_INCOMPLETE`, it did not reclassify
any program):

| Disposition | Before | After |
|---|---:|---:|
| FORMULAIC_AUTHORITY_INCOMPLETE | 105 | 105 |
| PROGRAM_TYPE_UNRESOLVED | 88 | 88 |
| SELECTIVE_OR_DISCRETIONARY | 23 | 23 |
| NON_ECONOMIC_SUPPORT | 5 | 5 |
| SUPERSEDED | 2 | 2 |
| DUPLICATE | 1 | 1 |
| FORMULAIC_AUTHORITY_COMPLETE | 0 | 0 |

**Per-dimension unresolved count, before → after, across the 105
formulaic-incomplete programs:**

| Dimension | Before | After | Recovered |
|---|---:|---:|---:|
| CULTURAL_OR_CONTENT_TEST | 103 | 51 | **52** |
| REFUNDABILITY | 103 | 58 | **45** |
| TRANSFERABILITY | 103 | 61 | **42** |
| MONETIZATION | 103 | 63 | **40** |
| MINIMUM_SPEND | 101 | 85 | **16** |
| APPLICATION_TIMING | 105 | 88 | **17** |
| CAP | 103 | 94 | **9** |
| TERRITORIALITY | 101 | 100 | **1** |
| RATE_OR_AWARD_BASIS | 100 | 100 | 0 |
| QPE_DEFINITION | 101 | 101 | 0 |
| ELIGIBLE_PRODUCTION_TYPE | 100 | 100 | 0 |
| UPLIFT_RULES | 102 | 102 | 0 |
| RESIDENT_NONRESIDENT_TREATMENT | 103 | 103 | 0 |
| PAYROLL_TREATMENT | 103 | 103 | 0 |

**222 individual dimension-resolutions recovered** from existing data
across **59 of 105** previously-incomplete programs (average 2.5
dimensions gained per improved program). **0 programs reached full 14/14**
— every improved program still has real residual gaps in
`RATE_OR_AWARD_BASIS`/`QPE_DEFINITION`/`ELIGIBLE_PRODUCTION_TYPE`
(confidence-tier promotion questions, not missing-source questions — see
below) and/or `RESIDENT_NONRESIDENT_TREATMENT`/`PAYROLL_TREATMENT`
(genuinely absent from every checked source, 103/105 each, unchanged).

**Four controls, before → after** (all remain `AUTHORITY_INCOMPLETE`, as
they must — none are P0-verified-complete programs):

| Program | Before | After |
|---|---:|---:|
| Greece (`gr_cash_rebate`) | 10/14 resolved | 9/14 unresolved → **5/14 unresolved** |
| GB AVEC (`uk_avec`) | 13/14 unresolved | **9/14 unresolved** |
| Canada federal PSTC (`ca_federal_pstc`) | 14/14 unresolved | **13/14 unresolved** |
| US California (`us_ca_film_credit`) | 14/14 unresolved | **12/14 unresolved** |
| US Georgia (`us_ga_film_credit`, reference) | 4/14 unresolved | 4/14 unresolved (unchanged — no program_requirements/jurisdiction_comparison profile adds anything beyond its existing VERIFIED DoctrineRecord) |

---

## 5. True residual authority gaps (Task 8, honest boundary)

After exhausting every identified existing source:

- **RESIDENT_NONRESIDENT_TREATMENT** and **PAYROLL_TREATMENT**: 103/105
  unresolved, unchanged. No checked source (program_requirements,
  jurisdiction_comparison, doctrine records, global_inventory) carries a
  residency-differentiated labor rule or a payroll-fringe QPE-eligibility
  rule for almost any program. Genuinely absent, not unwired.
- **RATE_OR_AWARD_BASIS / QPE_DEFINITION / ELIGIBLE_PRODUCTION_TYPE /
  UPLIFT_RULES**: unchanged (100-102/105). For most of these, real
  `PARSED`/`DISCOVERY`-tier `RateRule`s already exist (proven in the prior
  task) — the residual gap here is a confidence-tier *promotion*
  decision (accepting a cited-but-not-adjudicated rate as executable),
  which is an editorial/verification judgment call this recovery task
  correctly does not make unilaterally, not a missing-source problem.
- **88 PROGRAM_TYPE_UNRESOLVED**: confirmed zero recoverable from any
  existing source (§3) — requires new primary research to even identify
  what kind of program each one is.
- **CAP / MINIMUM_SPEND / APPLICATION_TIMING** (partial residuals: 94, 85,
  88 of 105 respectively): the recovered fraction came from PRIMARY_
  VERIFIED+CURRENT `program_requirements` profiles or VERIFIED
  `jurisdiction_comparison` profiles; the remaining unresolved fraction is
  programs with no registered profile in either source at all, or a
  profile whose relevant field is `None`.

---

## 6. Permanent prevention

`RECOGNIZED_AUTHORITY_SOURCE_MODULES` — a 6-entry tuple constant in
`canonical_program_consolidation.py` naming every module this file is
expected to read, paired with `test_no_recognized_authority_source_is_
orphaned_from_consolidation` (greps the module's own source for each
recognized import). Adding a new authority source to the list without
wiring its import fails this test immediately — the exact defect class
that let Georgia's DoctrineRecord and both sources in this pass sit
unread. Deliberately not a framework: one constant, one grep-based test.

---

## 7. Testing

Focused only: 5 new tests added to `tests/test_canonical_authority_
substrate.py` (source-adapter confidence gating ×2, MONETIZATION
staleness regression, orphan-prevention, one existing test updated to
reflect the genuine APPLICATION_TIMING improvement for uk_avec). **37/37
pass.** Full 4,000+ suite not rerun — no shared pricing/optimizer code
touched (same zero-blast-radius grep confirmation as the prior task:
`canonical_program_consolidation.py`/`canonical_publication_contract.py`/
`canonical_residual_ledger.py` are imported by no pricing/discovery/
optimizer path).

---

## 8. Final gate rationale

**`HISTORICAL_AUTHORITY_RECOVERY_ACCEPTED`**: every named source family
was examined and given an explicit disposition (A/B/C above); the two
disconnected source families (`program_requirements`,
`jurisdiction_comparison`) are now wired with confidence tiers and
currentness strictly preserved; a real staleness bug found during wiring
(MONETIZATION) was fixed with regression coverage; the 88 unresolved
program types were checked against every existing richer source and
honestly confirmed unrecoverable without new research; the full 224-
identity universe was recomputed; no external research was performed; no
optimizer or frontend code was touched; a lightweight, permanent
orphan-prevention check now guards this defect class going forward.

The remaining 105 `FORMULAIC_AUTHORITY_INCOMPLETE` programs (down to an
average 11.5/14 resolved from 11.3/14, with 59 programs concretely
improved and 222 individual dimensions genuinely recovered) now represent
**true residual authority gaps** — confirmed absent from every existing
retained CineGlobe source, not merely unwired — and are the correct input
to a future, explicitly-scoped primary-source research phase.
