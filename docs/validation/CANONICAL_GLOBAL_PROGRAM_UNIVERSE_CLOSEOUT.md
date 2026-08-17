# Canonical Global Program Universe — Completion Closeout

**Final gate: `CANONICAL_GLOBAL_PROGRAM_UNIVERSE_BLOCKED`**

---

## What this phase covered

Classified every canonical program identity in the shared incentive dataset
(`all_canonical_identities()`), assigned each one exactly one disposition,
fixed a real mechanical bug that was silently discarding already-available
authority data, and quantified — honestly, without fabricating primary-source
answers — how much of the universe is genuinely authority-complete versus
how much requires further primary-authority research that is out of
responsible scope for a single session.

No optimizer, discovery, pricing, frontend, or authority-data file was
touched. LU and FVD are structurally unaffected (see §5).

---

## 1. Final accounting

**Total canonical identities: 224**

| Disposition | Count |
|---|---:|
| FORMULAIC_AUTHORITY_INCOMPLETE | 105 |
| PROGRAM_TYPE_UNRESOLVED | 88 |
| SELECTIVE_OR_DISCRETIONARY | 23 |
| NON_ECONOMIC_SUPPORT | 5 |
| SUPERSEDED | 2 |
| DUPLICATE | 1 |
| FORMULAIC_AUTHORITY_COMPLETE | 0 |
| NEGOTIATED | 0 |
| FINANCING_ONLY | 0 |
| OTHER_VERIFIED | 0 |

Every one of the 224 identities has exactly one explicit disposition in
`CANONICAL_GLOBAL_PROGRAM_UNIVERSE_CLOSEOUT.json`. Identity uniqueness
verified — zero duplicate `canonical_slug` collisions across all 224 rows.

**Known 74 P0 programs** (from
`docs/validation/CODEX_AUTHORITY_GAP_PROGRAM_INTEGRITY.json`, 75-row set,
1 of which — Kazakhstan — is itself `PROGRAM_TYPE_UNRESOLVED`, correctly
excluded from the formulaic set): 74 of 74 formulaic P0 programs are
`FORMULAIC_AUTHORITY_INCOMPLETE`. 0 are complete.

**Additional formulaic-incomplete programs discovered beyond the known 74**
(Phase D — the dataset must serve the full universe, not just the known
gap set): 31, for a total of 105 `FORMULAIC_AUTHORITY_INCOMPLETE`.

---

## 2. The real bug fixed this phase

`canonical_program_consolidation.py`'s `consolidate()` never consulted
`app/data/executable_jurisdiction_registry.py`'s `DoctrineRecord` /
`get_doctrine()` — a data source already populated for 107 programs, some
at `VERIFIED` confidence, with real statute-cited answers for
`is_refundable`, `is_transferable`, `min_spend_usd`, `annual_cap_usd`, and
`requires_cultural_test`. This caused false `MISSING` classifications for
seven dimensions (`MINIMUM_SPEND`, `CAP`, `CULTURAL_OR_CONTENT_TEST`,
`UPLIFT_RULES`, `MONETIZATION`, `REFUNDABILITY`, `TRANSFERABILITY`) on any
program with a real `DoctrineRecord` but no separate `global_inventory`
entry — proven concretely for `us_ga_film_credit` (Georgia), a genuinely
`VERIFIED`-confidence record citing O.C.G.A. § 48-7-40.26.

**Fix**: `consolidate()` now reads `get_doctrine(slug)` and promotes those
seven dimensions to `PRESENT` when the doctrine record is `VERIFIED`, or
`PARTIAL` (still correctly unresolved) when it is only `PARSED`/
`DISCOVERY` — cited but not yet authority-adjudicated. A bare `None` field
on a doctrine record (e.g. Georgia's `annual_cap_usd=None`) is never
inferred as a confirmed absence; it stays `MISSING` unless a primary
source has explicitly confirmed the absence.

**Verified impact**: Georgia went from 4/14 to 10/14 dimensions resolved
(`MINIMUM_SPEND`, `CULTURAL_OR_CONTENT_TEST`, `UPLIFT_RULES`,
`REFUNDABILITY`, `TRANSFERABILITY`, `MONETIZATION` all flipped from false
`MISSING` to correctly-sourced `PRESENT`). All four control programs
(Greece, GB AVEC, Canada federal PSTC, US California) remain
`AUTHORITY_INCOMPLETE`, as expected — this was a fidelity correction, not a
completion of any control. `CONSOLIDATION_VERSION` bumped
`1.1.0` → `1.2.0`. All 32 existing focused tests in
`tests/test_canonical_authority_substrate.py` pass unchanged.

This fix is real, mechanical completion work — reusing already-available
authority data that a prior task's own bug had made invisible — not new
primary-source research.

---

## 3. Why `FORMULAIC_AUTHORITY_INCOMPLETE = 0` is not achievable this phase

Per-dimension frequency across the 105 `FORMULAIC_AUTHORITY_INCOMPLETE`
programs, after the doctrine-record fix above:

| Dimension | Unresolved / 105 |
|---|---:|
| APPLICATION_TIMING | 105 (100%) |
| CAP | 103 |
| CULTURAL_OR_CONTENT_TEST | 103 |
| RESIDENT_NONRESIDENT_TREATMENT | 103 |
| PAYROLL_TREATMENT | 103 |
| MONETIZATION | 103 |
| REFUNDABILITY | 103 |
| TRANSFERABILITY | 103 |
| UPLIFT_RULES | 102 |
| QPE_DEFINITION | 101 |
| TERRITORIALITY | 101 |
| MINIMUM_SPEND | 101 |
| RATE_OR_AWARD_BASIS | 100 |
| ELIGIBLE_PRODUCTION_TYPE | 100 |

**This is not 105 separate research problems — it is a structural gap.**
`APPLICATION_TIMING` has **no runtime registry field anywhere** that
captures application/preapproval timing, for any program, including the
`VERIFIED`-tier ones (confirmed: even Georgia, the most complete control,
shows `APPLICATION_TIMING = MISSING`). `RESIDENT_NONRESIDENT_TREATMENT`
and `PAYROLL_TREATMENT` are similarly almost never populated — they depend
on `program_spend_rules.get_program_rules()` category rules
(`btl_resident_labor`/`btl_nonresident_labor`/`payroll_fringes`) that exist
for only a handful of programs.

Resolving these honestly requires either (a) adding real, cited primary-
authority answers per program — genuine tax/legal research across up to
105 jurisdictions' statutes, regulations, and administering-agency
guidance, most of which involves fields (application timing windows,
resident/non-resident payroll treatment) that no existing registry in this
codebase has ever captured for any program — or (b) discovering that a
richer source already exists and simply wiring it in, the way this
phase's `get_doctrine()` fix did. A second wiring pass was checked: no
other unconsulted rich data source (comparable to
`executable_jurisdiction_registry`) was found for these three specific
dimensions. They are a genuine, currently-unfilled data gap, not a wiring
oversight.

Per the task's own explicit design: *"if any remain, they must have a
genuinely unresolved primary-authority boundary that cannot be
responsibly resolved in this phase — avoidable incompleteness is not
acceptable, but genuinely unresolvable-in-this-phase incompleteness is
explicitly tolerated."* `APPLICATION_TIMING` at 105/105 and six further
dimensions at ~103/105 are exactly this: a structural, universe-wide gap
whose responsible remedy is a dedicated multi-jurisdiction primary-source
research program, not a mechanical fix achievable in this phase. Producing
fabricated values to force `AUTHORITY_COMPLETE` across 105 programs would
violate the task's explicit no-fabrication instruction and the QPE
doctrine's own provenance requirements.

**Unresolved programs list**: all 105 `FORMULAIC_AUTHORITY_INCOMPLETE`
programs, with their exact per-dimension unresolved set, are in
`CANONICAL_GLOBAL_PROGRAM_UNIVERSE_CLOSEOUT.json` (`unresolved_material_
dimensions` field per program). Not reproduced inline here — 105 programs
× up to 14 dimensions is not usefully readable as prose.

---

## 4. What was and was not done

**Done this phase:**
- Phase A: all 224 canonical identities classified, one disposition each.
- Phase B: `FORMULAIC_AUTHORITY_COMPLETE` programs re-confirmed without
  redundant re-research (none currently qualify — see §3).
- The doctrine-record wiring fix (§2) — real completion work reusing
  existing, already-cited authority data across the full 107-program
  `DoctrineRecord` registry, not scoped to the known 74.
- Phase D discovery: 31 additional `FORMULAIC_AUTHORITY_INCOMPLETE`
  programs identified beyond the known 74 P0 set.
- Duplicate/superseded/type-unresolved identification (1 duplicate, 2
  superseded, 88 program-type-unresolved — see note below).

**Not done this phase, and why:**
- Fresh primary-authority research (new web/statute research) for
  individual programs' `TERRITORIALITY`, `RESIDENT_NONRESIDENT_TREATMENT`,
  `PAYROLL_TREATMENT`, `APPLICATION_TIMING`, or upgrading `PARSED`/
  `DISCOVERY` doctrine records to `VERIFIED` (e.g. GB AVEC, Canada federal
  PSTC, US California) — genuinely out of scope for one session across
  105 programs; see §3.
- Resolving the 88 `PROGRAM_TYPE_UNRESOLVED` identities' underlying
  program type — these are real named programs (e.g. NSW Government
  Screen Incentive, Canada Media Fund, Danish Film Institute Production
  Support) present only in the static `authority_coverage_registry` veto
  list with no richer profile ever attached anywhere. Determining whether
  each is formulaic, selective, or non-economic is itself primary research,
  not mechanical classification — correctly reported as unresolved rather
  than guessed.

**Note on the 88 `PROGRAM_TYPE_UNRESOLVED` count**: an earlier internal
pass at this classification incorrectly asserted `OTHER_VERIFIED` (a
positive claim of confirmed non-formulaic type) for these 88 programs,
reasoning "no formulaic type found → not formulaic." That was corrected
in this same session before any artifact was produced: absence of type
data is not evidence of a non-formulaic type, so these are honestly
`PROGRAM_TYPE_UNRESOLVED`, not `OTHER_VERIFIED`. No artifact reflecting the
incorrect classification was ever published.

---

## 5. Runtime / regression verification

- `canonical_program_consolidation.py`, `canonical_publication_contract.py`,
  and `canonical_residual_ledger.py` are confirmed, by grep across the
  entire `app/` tree, to be imported by **no pricing, discovery, or
  optimizer code path** — only referenced in comments. LU and FVD are
  structurally unaffected by every change in this phase; no live
  re-evaluation was needed to establish this (zero blast radius, not
  "unlikely to matter").
- `tests/test_canonical_authority_substrate.py`: 32/32 pass, unchanged
  assertions, after the doctrine-record fix.
- Full 4,000+ backend suite intentionally **not** run, per this task's
  explicit minimal-testing instruction — no shared pricing/optimizer code
  was touched.

---

## 6. Integrity checks

| Check | Result |
|---|---|
| Every active canonical identity has exactly one disposition | **PASS** (224/224) |
| Duplicate/current identity integrity | **PASS** — 0 duplicate `canonical_slug` values; 1 program correctly flagged `DUPLICATE`, 2 correctly flagged `SUPERSEDED` via `authority_coverage_registry.coverage_state` |
| Currentness integrity | **PASS** — `current_or_superseded_state` read directly from `canonical_program_identity`, no synthetic merging of old/new program versions performed or found |
| Residual ledger integrity | **PASS** — `authority_completeness()`'s `unresolved_material_dimensions` is produced by the same `UNRESOLVED_FOR_AUTHORITY_COMPLETENESS` set the residual ledger consumes; no drift possible by construction (shared frozenset, not duplicated logic) |
| Generic future-project universe | **PASS** — nothing in this phase's fix or classification is project-specific; `get_doctrine()`/`consolidate()`/`authority_completeness()` take only a `program_slug` and serve LU, FVD, all Company Library projects, and any future New Project ingestion identically |
| Optimizer changed | **NO** (expected) |
| Frontend changed | **NO** (required) |

---

## 7. Final gate rationale

**`CANONICAL_GLOBAL_PROGRAM_UNIVERSE_BLOCKED`** — not `ACCEPTED`, because
105 of 224 canonical identities remain `FORMULAIC_AUTHORITY_INCOMPLETE`,
and honest per-dimension analysis (§3) shows this is a genuine, structural
primary-authority research gap — most acutely `APPLICATION_TIMING`, unresolved
for literally every one of the 105 programs because no registry in this
codebase has ever captured that dimension for any program — not a wiring
defect this phase could responsibly close. The one wiring defect that
existed (the doctrine-record gap, §2) was found and fixed. What remains
requires a dedicated multi-jurisdiction primary-source research program,
correctly out of scope for this phase per the task's own design, which
explicitly tolerates genuinely-unresolvable-in-this-phase incompleteness
over fabricated completeness.

All 224 identities are classified. The dataset is a strictly more complete
and more honest source of truth than before this phase — zero identities
are unclassified, one real data-visibility bug is fixed, and the residual
research gap is precisely quantified rather than hidden or guessed away.
