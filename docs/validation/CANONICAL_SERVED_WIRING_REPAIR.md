# Canonical Served Wiring Repair

**Status: `CANONICAL_SERVED_WIRING_REPAIRED`**

Implements the repair sequence specified against
[`CODEX_CANONICAL_SERVED_WIRING_DIAGNOSIS.md`](CODEX_CANONICAL_SERVED_WIRING_DIAGNOSIS.md)
(commit `6d3a44b`), which independently localized five verified defects
between the validated canonical economics engine and the served project UI.
This is a data-validation / served-wiring closeout, not a new audit: the
diagnosis is treated as authoritative and its defect chain / repair sequence
is implemented as specified. No optimizer redesign, no rule/threshold/rate
changes, no UI redesign, no MFNI implementation.

Project: **F#K Valentine's Day** (`6c6f1c13-2d49-4bbc-bafb-2a12efa93112`, "FVD")
Regression oracle: **The Little Utopia** (`fa5cade5-0669-4816-bfe6-72146f8d3bae`, "LU")
Engine version: `canonical-1.2.1` (bumped twice this session — `1.1.0` → `1.2.0`
for the new classification/serialization logic, then `1.2.0` → `1.2.1` after a
real bug was found and fixed in that logic, to force clean regeneration
rather than reuse stale buggy rows under a matching fingerprint).

---

## Defect-by-defect

### Defect 1 — thin canonical inputs, absent territorial facts as empty sets

**Status: partially repaired, with a disclosed residual gap.**

`canonical_project_economics.py::build_project_economic_inputs()` now queries
real `ProjectFact` and `ProductionRequirement` rows and populates three new
honest fields on `ProjectEconomicInputs`:
`accounts_outside_jurisdiction_state`, `offshore_payroll_accounts_state`
(`STATED` when a fact row exists, `UNKNOWN` otherwise — never inferred), and
`production_requirements_on_file` (a real count). These are surfaced to the
frontend via a new `economics.production_requirements_disclosed` field.

**What was not done, and why:** `derive_production_requirements({})` still
receives an empty dict. SA-1's `ProductionRequirement.requirement_key`
vocabulary (`SCRIPTED_LOCATION`, `CHARACTER`, `EXPLICIT_VEHICLE`, etc.) has no
safe, non-inventive mapping into the `physical_requirements` dict shape
(`script_requirements` / `location_categories` / `marine_required` / etc.)
that only `little_utopia_state.py`'s own hand-built fixture currently
produces. Building that mapping would require new interpretive judgment
about what a requirement key implies territorially — exactly the kind of
invention the task rules forbid ("NO territoriality/facts invention"). FVD's
100+ real `ProductionRequirement` rows are disclosed via the new field above
instead of being silently dropped or fabricated into the wrong shape. This
is a genuine, disclosed architectural gap between the SA-1 subsystem and the
canonical evaluation engine — not fixed in this repair beyond making it
visible and honestly labeled, per the task's own instruction not to hide
this by inventing a mapping.

### Defect 2 — PRICED and COMPARABLE conflated

**Status: fixed.**

`canonical_production_view.py::_ranking_entry()` was rewritten to never
overwrite `is_fully_priced`. A new, explicit `is_directly_comparable` field
(alias-serialized from `canonical_evaluation.py`'s `is_baseline`/
`relocation_cost_normalized` fact) gates the numeric ranking bucket
separately from priceability:

- **Comparable** (ranked, shown as table columns): `is_fully_priced=True AND
  is_directly_comparable=True` — only the production's own base jurisdiction,
  by construction (no generic travel/in-kind/FX-normalized comparison exists
  yet for relocation candidates).
- **Review / Needs Validation** (real economics, excluded from rank):
  `is_fully_priced=True AND is_directly_comparable=False` — keeps real
  QPE/incentive/NPC on the ranking entry, with
  `excluded_from_ranking_because` explaining regional-normalization pending.
- **Unpriceable**: `is_fully_priced=False`.

`frontend/src/lib/productionOptions.js` gained `isDirectlyComparable(entry)`,
used by both `selectTopOptions()` (Overview's Production Options cards) and
`Scenarios.jsx`'s comparable/review split. **Critical LU-regression guard**:
`isDirectlyComparable()` falls back to `is_fully_priced` when
`is_directly_comparable` is absent, because `little_utopia_state.py`'s own
`rank_allocated_structures()` never sets this new field at all — LU's rich
per-structure pricing already includes real travel/FX/in-kind deltas, so its
existing `is_fully_priced` already meant "comparable." Without this fallback,
LU's Scenarios/Overview pages would have shown zero comparable columns (see
Runtime Verification below — confirmed working, not just unit-tested).

`Workspace.jsx` and `globeData.js` were **not modified** — both were
confirmed, by reading, to already consume structure-level `is_fully_priced`
directly (never the corrupted ranking-level field), matching Codex's own
diagnosis (§J) that these two surfaces were not part of the conflation.

### Defect 3 — rich `SegmentEconomics` trace discarded before persistence

**Status: fixed.**

`canonical_evaluation.py::_segment_dicts()` now serializes the full field set
little_utopia_state.py's own `_seg_dict` already serializes:
`unresolved_usd`, `is_band_ceiling`, `statutory_basis`,
`incentive_floor_usd`, `incentive_ceiling_usd`, `ceiling_requires_confirmation`,
`qpe_cap_applied_usd`, `qualification_trace` (the full register trace,
renamed from the internal `register_trace`), and `notes`. Nothing new is
computed — this is pure serialization of fields `SegmentEconomics` and the
pricing register already produced and previously discarded.

### Defect 4 — unpriceable causes flattened to one generic reason

**Status: fixed.**

A new `_capability_only_status()` in `canonical_evaluation.py` reads
`authority_coverage_registry.coverage_state(program_slug)` (an already-
completed, already-persisted audit result — never re-evaluated) and the
existing `JurisdictionExamination` fields (`has_doctrine`, `has_rate_rules`,
`resolves_for_production`) to classify each capability-only candidate into
its real terminal cause:

- `coverage_state() == "UNPRICEABLE_AUTHORITY_INSUFFICIENT"` →
  `UNPRICEABLE_AUTHORITY_INSUFFICIENT`
- `coverage_state()` not `PRICEABLE_VALIDATED` (i.e. `NON_GUARANTEED_SELECTIVE`,
  `SUPERSEDED`, `NON_ECONOMIC`, `DUPLICATE`) →
  `FEASIBILITY_REVIEW_REQUIRED`
- `has_doctrine AND has_rate_rules AND NOT resolves_for_production` →
  `RULE_REJECTED` / `STATUTORY_CONDITIONS_UNMET` (the AU Location Offset case)
- everything else → `UNPRICEABLE_AUTHORITY_INSUFFICIENT`

A parallel path in the `pricing is None` branch calls the new
`program_rate_rules.classify_rate_resolution_failure()` (a read-only mirror
of `resolve_program_rate()`'s own eligibility filter) to distinguish "no rate
rules exist at all" from "rules exist but none are eligible for this
production_type/QPE" — the exact substitution point that previously
collapsed both into the same generic `None`.

`program_slug` is preserved on every terminal candidate (`examination.
program_slug` for capability-only candidates, the resolving `program_slug`
for pricing-blocked ones) — never dropped, so AU Location Offset's identity
survives all the way to the ranking entry.

**A real classification bug was found and fixed during this repair** (see
Verification & Debugging below): the first implementation mapped every
non-`PRICEABLE_VALIDATED` `coverage_state()` to `FEASIBILITY_REVIEW_REQUIRED`,
which — because `coverage_state()` can itself return the literal string
`"UNPRICEABLE_AUTHORITY_INSUFFICIENT"` — misclassified all 75 of LU's
genuinely authority-insufficient candidates. Fixed with an explicit
early-return branch; re-verified against real data to match Codex's reported
75/3/1/1 breakdown exactly (see LU verification below).

### Defect 5 — generic pkg/economics/people/facts replaced with empty shapes

**Status: fixed.**

New `canonical_production_view.py::build_generic_pkg_and_economics()`:

- **pkg.register**: reuses the leading structure's own already-persisted
  `segments[].qualification_trace` (restored by Defect 3) — no new query or
  calculation, purely an adapter.
- **pkg.budget**: real `total_budget_usd` from the leading
  `StructureCalculationResult` (falling back to the `BudgetDocument`), real
  `line_item_count` from `BudgetLineItem`.
- **economics.production_requirements_disclosed**: the Defect 1 disclosure
  field.
- **people**: real `ProjectPerson` + `TalentProfile` rows, bucketed by the
  same `PERSON_ROLES` vocabulary `personRoles.js` already uses.
- **facts**: real `ProjectFact` rows.
- **legal / recommendations**: remain the honest `EMPTY_*` constants — no
  generic evidence-graph or recommendation engine exists for any project
  outside the LU demo state, and none was built here.

`cineglobe.py::get_project_state()` now calls this function for non-demo
projects and threads its sections through, instead of substituting the
empty constants unconditionally.

**FVD, checked directly against the database before this fix:** genuinely
has zero `ProjectPerson` rows (all 4 rows in the entire database belong to
LU) — the empty `people` bucket for FVD is the honest correct state, not a
residual bug. `pkg.register` and `pkg.budget.total_budget_usd`, by contrast,
now show FVD's real data (verified below).

---

## FVD accounting — before / after

| | Before (per Codex diagnosis) | After (verified 2026-08-16) |
|---|---|---|
| Priced (comparable) | 30 candidates shown only as "Greece" on Overview/Scenarios | 1 (Greece — the base jurisdiction) |
| Priced, not directly comparable | conflated into the above / into Workspace-Globe divergence | 29 |
| Unpriceable | 80, all `UNPRICEABLE_AUTHORITY_INSUFFICIENT` | 80, split: 75 `UNPRICEABLE_AUTHORITY_INSUFFICIENT`, 3 `NON_GUARANTEED_SELECTIVE`→`FEASIBILITY_REVIEW_REQUIRED`, 1 `SUPERSEDED`→`FEASIBILITY_REVIEW_REQUIRED`, 1 `RULE_REJECTED` (AU Location Offset) |
| Total candidates | 110 | 110 (unchanged — no candidate generation touched) |

Verified live via `build_production_and_structures()` against the current
`canonical-1.2.1` rows (2026-08-16):

```
priced structures:            30
comparable (ranked) entries:   1
review-required entries:      29
unpriceable entries:          80
```

Matches Codex's reported 30 priced / 1 comparable / 29 review / 80
unpriceable exactly.

---

## Representative jurisdiction traces (FVD, verified live)

**Greece (GR) — the priced, directly comparable baseline:**
`program_slug=gr_cash_rebate`, `QPE=$3,614,149.60`,
`qpe_cap_applied_usd=$540,671.40`, `incentive_floor_usd=incentive_ceiling_usd=
$1,445,659.84` (flat 40% rate, `is_band_ceiling=False`,
`ceiling_requires_confirmation=False`), full `statutory_basis` and
34-entry `qualification_trace` intact. Ranking entry:
`is_fully_priced=True`, `is_directly_comparable=True`,
`candidate_status=PRICED`.

**Malta (MT) — priced, band-ceiling, not directly comparable:**
`program_slug=mt_mfc_rebate`, `QPE=$4,154,821.00`,
`incentive_floor_usd=$1,246,446.30` (30%), `incentive_ceiling_usd=
$1,661,928.40` (40%), `is_band_ceiling=True`,
`ceiling_requires_confirmation=True` — the confirmation-required state is
retained, not silently resolved. Ranking entry: `is_fully_priced=True`,
`is_directly_comparable=False` (real economics shown in Scenarios' Review
section, not dropped).

**Mauritius (MU) — priced, band-ceiling, not directly comparable:**
`program_slug=mu_edb_incentive`, `QPE=$1,132,056.00`,
`is_band_ceiling=True`, `ceiling_requires_confirmation=True`. Same
comparable/review treatment as Malta.

**Australia Queensland (AU-QLD) — priced, flat rate, not directly comparable:**
`program_slug=au_qld_pdv_rebate`, `QPE=$4,154,821.00`,
`incentive_floor_usd=incentive_ceiling_usd=$623,223.15` (flat 15%,
`is_band_ceiling=False`, no confirmation required) — the 15% treatment is
retained exactly, not renormalized. Priced-but-review, same as MT/MU.

**Australia Location Offset — the Defect 4 acceptance case:**
`program_slug=au_location_offset` preserved end to end,
`candidate_status=RULE_REJECTED`,
`rejection_reason_class=STATUTORY_CONDITIONS_UNMET`,
`is_fully_priced=False`, `is_directly_comparable=False` — real statutory
rules exist and were evaluated, but do not resolve for this production's
QPE. This is the exact terminal state Codex specified; it does not fall into
the generic `UNPRICEABLE_AUTHORITY_INSUFFICIENT` bucket every other
capability-only candidate without doctrine/rate data at all correctly
reaches.

All five traces are asserted with exact numeric values in
[`test_canonical_served_wiring_repair.py`](../../frametax2/backend/tests/test_canonical_served_wiring_repair.py)
(STEP 8 contract fixture, see Tests below).

---

## Cross-screen consistency

Verified by browser (2026-08-16) that Overview, Scenarios, Workspace, and
World/Globe — the four served surfaces reading the one
`build_production_and_structures()` / `get_project_state()` response — all
agree on FVD's status per structure: Greece as the sole comparable/leading
structure; Malta/Mauritius/AU-QLD/the other 26 priced-but-review structures
showing their real QPE/incentive/NPC numbers in Review/Needs Validation
(Scenarios) and the equivalent non-ranked treatment on Workspace/World,
never silently promoted into "ranked" and never shown as blank/unpriced.

**Overview / Workspace / Scenarios / World consistent: YES.**

---

## Little Utopia regression (Step 9)

**Narrow regression only — LU's optimizer/candidate-generation validation
was not reopened.**

Verified live (2026-08-16), via `evaluate_project()` and browser walk of all
four screens:

- Winner: **Mauritius** (`is_baseline=True`, `candidate_status=PRICED`)
- NPC: **$3,057,795** (displayed; exact persisted value
  `$3,057,794.90` — asserted in
  `test_canonical_evaluation.py::test_little_utopia_canonical_service_reproduces_exact_npc_and_winner`)
- Scenarios: 6 comparable columns shown (Mauritius Current/Base + 5
  Hybrid/Component structures), matching the state from the prior Scenarios
  UI Contract phase exactly — QPE/incentive/NPC numbers unchanged.
- Overview: same 6 Production Options cards, same numbers.
- Workspace: lanes/scenario selector render normally, currency rail intact.
- World/Globe: candidate structures list renders normally (Mauritius
  single-jurisdiction baseline, hybrid structures), unaffected — this
  surface reads structure-level `is_fully_priced` directly, never the
  ranking-level field this repair touched.
- Review / Needs Validation: 129 real capability-only entries, each with a
  differentiated real cause (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`,
  `SUPERSEDED`, etc.) — confirming Defect 4's fix applies correctly to LU's
  own 129-candidate universe too, not only FVD's.

**A near-regression was found and fixed before it reached the served path**:
an early version of the `Scenarios.jsx`/`productionOptions.js` change read
`is_directly_comparable` directly with no fallback. `little_utopia_state.py`'s
own `rank_allocated_structures()` never sets this field (only
`is_fully_priced`) — without a fallback, LU's Scenarios/Overview would have
shown zero comparable columns, dumping its entire ranked universe into
Review. Caught by re-reading `allocation_pricing.py` before any browser
verification; fixed with `isDirectlyComparable()`'s
`?? is_fully_priced` fallback (see Defect 2 above), with two dedicated
regression tests, and confirmed working against LU's real served JSON in the
browser walk above — not just against hand-built unit-test mocks.

**LU regression: PASS.**

---

## Verification & debugging notes

- **Stale-row test caching**: an early implementation's test failures were
  traced to pytest reusing rows persisted under `ENGINE_VERSION=
  canonical-1.2.0` by a prior run of the (then-buggy) code, since fingerprint
  + version matched on rerun. Fixed by bumping to `canonical-1.2.1`, forcing
  clean regeneration — not by weakening the test.
- **Real Defect-4 classification bug**: found via a direct
  `Counter(coverage_state(e.program_slug) for e in capability_only)` diagnostic
  against LU's real 80-candidate capability-only set — `{'UNPRICEABLE_
  AUTHORITY_INSUFFICIENT': 75, 'NON_GUARANTEED_SELECTIVE': 3, 'SUPERSEDED': 1,
  'PRICEABLE_VALIDATED': 1}` — which showed the first `_capability_only_status()`
  implementation was silently misrouting 75 genuinely authority-insufficient
  candidates into `FEASIBILITY_REVIEW_REQUIRED`. Fixed with an explicit
  early-return branch; re-verified to match exactly.
- **FVD people-section false alarm**: initially suspected a bug (empty
  `people` bucket); a direct raw-SQL query confirmed all 4 `ProjectPerson`
  rows in the database belong to LU, not FVD — the empty result for FVD is
  correct, not a defect. No code change was made for this.

---

## Unrelated pre-existing defect (reported, not fixed, per task rule 20)

`tests/test_global_discovery.py::TestRecommendationTitles::
test_scenarios_and_workspace_both_use_the_canonical_title_formatter` fails:
`Workspace.jsx` never calls `scenarioDisplay(` (it uses
`compactScenarioIdentity()` instead). Confirmed via `git log`/`git status`
that `Workspace.jsx` was not modified in this repair and the failing test
file predates this session (2026-08-14). This is an unrelated, pre-existing
defect — reported here per the task's explicit instruction, not fixed,
since `Workspace.jsx` is outside this repair's allowed-file scope and the
fix (reconciling two title-formatting helpers) is unrelated to any of the
five Codex defects.

---

## Scope discipline

- **No economic-rule changes**: no rate table, threshold, cap, QPE doctrine,
  or candidate-generation logic was touched. Every change in this repair is
  classification, serialization, or view-adapter code operating on values
  the existing engine/discovery/rate-resolution layers already computed.
- **No MFNI implemented**: `mfni_limitation` messaging and the "regional
  cost normalization not yet applied" language are unchanged; no
  region-differential estimation was added.
- **No UI redesign**: the existing four-classification taxonomy
  (Current/Base, Full Relocation, Hybrid/Component, Official Treaty
  Co-Production) and the existing comparable/review section layout in
  `Scenarios.jsx` are unchanged in structure — only the field driving the
  comparable/review split changed (from an overloaded `is_fully_priced` to
  the new explicit `is_directly_comparable`), and one new disclosure field
  (`production_requirements_disclosed`) was added to `economics`.
- **Files touched**: exactly the allowed-file list —
  `canonical_project_economics.py`, `canonical_evaluation.py`,
  `canonical_production_view.py`, `api/v1/cineglobe.py`,
  `lib/productionOptions.js`, `screens/production/Scenarios.jsx`, plus
  `data/program_rate_rules.py` (the read-only failure-classification helper
  Defect 4 required), and targeted tests
  (`test_canonical_evaluation.py`, `tests/overview-options.test.mjs`, and
  the new `test_canonical_served_wiring_repair.py`). `Workspace.jsx` and
  `globeData.js` were read but not modified — confirmed unnecessary by
  code inspection (Defect 2) and by the unrelated-defect note above.

---

## Tests

- **Backend**: `pytest` — 4120 passed, 1 pre-existing unrelated failure
  (reported above), 1 skipped. Includes the STEP 8 bounded contract fixture
  (`tests/test_canonical_served_wiring_repair.py`, 9 tests: FVD accounting,
  the five jurisdiction traces above, unpriceable-cause differentiation,
  pkg/economics disclosure, and stale-engine-row exclusion for both FVD and
  LU) and the updated `test_canonical_evaluation.py` (Defect 4's status set).
- **Frontend**: `node --test` — 77/77 passed. Includes the
  `isDirectlyComparable()` LU-fallback regression tests and the
  priced-but-not-comparable Top-6-exclusion test in
  `tests/overview-options.test.mjs`; `tests/scenarios-ui-contract.test.mjs`
  passes unchanged (reviewed, no update needed).
- **Runtime**: full browser walk, Project Library → FVD → Overview →
  Workspace → Scenarios → World, and the equivalent LU walk, both described
  above.

---

## Final gate

**`CANONICAL_SERVED_WIRING_REPAIRED`**

All five Codex defects addressed (Defect 1 with a disclosed, deliberate
residual gap — no safe non-inventive fix exists without building new
interpretive logic the task rules forbid). FVD accounting matches exactly
(30 priced / 1 comparable / 29 review / 80 unpriceable). All four served
surfaces agree. Stale rows excluded. LU regression passes narrowly (winner
Mauritius, NPC $3,057,794.90) without reopening optimizer validation. No
MFNI, no UI redesign, no economic-rule changes.
