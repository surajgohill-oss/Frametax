# FVD Canonical Input Assembly Repair

**Status: `FVD_CANONICAL_INPUT_ASSEMBLY_REPAIRED`**

Fixes the input-assembly defect Codex localized in
[`CODEX_CANONICAL_SERVED_WIRING_DIAGNOSIS.md`](CODEX_CANONICAL_SERVED_WIRING_DIAGNOSIS.md)
§E/§K (Defect 1): the FVD evaluator assembled thin canonical inputs —
absent territorial facts silently became empty-known sets, and
`derive_production_requirements({})` was permanently empty regardless of
real, persisted SA-1 script data. This is an input/handoff repair only: no
UI, no Top-6/Workspace/Scenarios ordering, no FX, no MFNI, no global
incentive rule, and the optimizer/rate/threshold corpus is unchanged and
not revalidated.

Engine version: `canonical-1.3.0` (bumped from `canonical-1.2.1` to force
clean regeneration under the new input assembly).

---

## Prior defective input path

- `canonical_project_economics.py::_fact_account_set()` read an absent
  `budget_accounts_outside_base_jurisdiction`/`budget_offshore_payroll_accounts`
  `ProjectFact` as a bare empty `frozenset()`, with no record of whether a
  fact was ever stated at all (a prior repair added `accounts_outside_
  jurisdiction_state`/`offshore_payroll_accounts_state` STATED/UNKNOWN
  disclosure fields, but they were disclosure-only — served results never
  visibly flagged the difference).
- `canonical_evaluation.py::evaluate_project()` called
  `derive_production_requirements({})` unconditionally — every jurisdiction
  therefore appeared "production capable" for any requirement, hard or
  soft, even though FVD has 54 real, evidence-backed
  `ProjectLocationRequirement` rows (including Mediterranean sea-shore,
  secluded-beach, and harbor scenes) and 2 `ProductionRequirement`
  `PERIOD_REFERENCE` rows on file.
- `canonical_project_economics.py::production_facts_for()` always reported
  the project's home jurisdiction code as `ProductionFacts.jurisdiction_code`,
  regardless of which candidate `_price_candidate()` was actually pricing —
  a full-relocation candidate's own register reason text read "...outside
  GR" instead of naming the candidate jurisdiction.
- Net effect: 28 of FVD's 30 priced candidates shared QPE $4,154,821 before
  jurisdiction-specific cap/rate treatment, and every priced result was
  silently presented as though its territorial facts had been confirmed.

## Corrected input path

1. **`canonical_project_economics.py::build_physical_requirements()`** (new) —
   reads SA-1's own persisted `ProjectLocationRequirement` (scripted
   locations) and `ProductionRequirement` (`PERIOD_REFERENCE`) rows
   directly, read-only, no side effects. Deliberately does NOT call
   `CanonicalProductionStateBuilder.build()`: that builder also performs an
   unrelated write-side budget-import fallback and enforces a strict
   `READY_FOR_OPTIMIZER` gate (shoot days, base-jurisdiction assumption)
   this requirements-only read does not need and that would incorrectly
   block FVD's evaluation on unrelated inputs.
2. **`_location_categories_from_descriptions()`** (new, pure function) —
   bridges two vocabularies that already existed in
   `app.calculators.production_requirements` but were never wired
   together: `abstract_location()` (a generic keyword ontology over
   literal location text, defined but never called by any consumer until
   this repair) and `derive_production_requirements()`'s own
   `location_categories` input shape (keyed on a different, LOCATION_
   TAXONOMY-derived slug vocabulary via `_LOCATION_CATEGORY_TO_CAPABILITY`).
   Several of `abstract_location()`'s outputs already equal
   `_LOCATION_CATEGORY_TO_CAPABILITY`'s keys verbatim (`beach_coast`,
   `marine_open_water`, `mediterranean`, `island`); the rest equal its
   capability *values* (e.g. `desert_environments`) rather than its keys
   (`desert`) — a small, explicit, purely mechanical reverse-lookup table
   connects those. Ontology hits with no `location_categories` equivalent
   (`harbor_marina`, `village`, `agricultural`, etc. — including a known
   false-positive "PORT" substring match inside "PORTABELLA'S") are
   dropped, never fabricated into a category that doesn't exist.
3. **`canonical_evaluation.py::evaluate_project()`** now calls
   `derive_production_requirements(await build_physical_requirements(session, project_id))`
   instead of `derive_production_requirements({})`.
4. **`production_facts_for(inputs, jurisdiction_code=None)`** gained an
   explicit override parameter; `_price_candidate()` now passes the
   candidate jurisdiction being priced, not always the home code. This
   changes only reason-text labeling inside the qualification register
   (`jur` is never used for any exclusion/inclusion decision, only for
   human-readable text) — zero effect on any QPE/incentive amount.
5. **UNKNOWN-vs-known-empty disclosure promoted to `has_unverified_inputs`** —
   every priced FVD candidate now carries `has_unverified_inputs=True` and
   an explicit warning ("UNKNOWN, not KNOWN EMPTY...") whenever either
   territorial fact was never stated. The qualification ladder itself is
   unchanged (a `frozenset[str]` membership check has no way to express a
   genuine third state without changing `qualification_derivation.py`,
   outside this repair's file boundary) — what changes is that the served
   result now visibly flags the assumption as provisional/requiring
   confirmation, never silently equivalent to a project that actually
   confirmed no accounts are stated outside its base jurisdiction.

No `qualification_derivation.py`, `program_spend_rules.py`,
`program_rate_rules.py`, `authority_coverage_registry.py`, or jurisdiction
data file was modified. No frontend file was modified.

---

## Before / after candidate accounting

| | Before (`canonical-1.2.1`) | After (`canonical-1.3.0`) |
|---|---:|---:|
| Generated structures (candidates reaching structure generation) | 110 | 89 |
| Priced | 30 | 28 |
| Directly comparable (ranked) | 1 | 1 |
| Priced, review-required | 29 | 27 |
| Unpriceable (with a structure/reason on file) | 80 | 61 |
| Unpriceable breakdown | 75 AUTHORITY_INSUFFICIENT / 3+1 FEASIBILITY_REVIEW_REQUIRED / 1 RULE_REJECTED | 56 AUTHORITY_INSUFFICIENT / 4 FEASIBILITY_REVIEW_REQUIRED / 1 RULE_REJECTED |

The 21 candidates that dropped out of structure generation entirely
(`AT, CA-AB, CA-MB, CA-SK, CZ, HU, KZ, LU, MK, MN, RS, SK, US-AZ, US-CO,
US-NM, US-NV, US-OK, US-PA, US-TN, US-UT, UZ`) are **every one of them
`marine_suitability = NONE`** in the existing, unmodified
`jurisdiction_comparison.ALL_PROFILES` data — genuinely landlocked or
non-coastal jurisdictions that cannot physically host FVD's real,
evidence-backed Mediterranean sea-shore/secluded-beach/harbor scenes. 2 of
the 21 (`MN`, `UZ`) were previously among the 28 flattened-QPE priced
candidates; the other 19 were previously in the unpriceable set for
unrelated authority-insufficient reasons and are now more accurately
rejected on capability instead (`open_water_filming` is a HARD-required
capability; a jurisdiction lacking it is rejected independent of any
incentive, per `production_discovery.py`'s own two-stage design — capability
first, incentive second). No candidate that has real coastal/marine
capability data was affected: GR, MT, MU, AU-QLD, CA-NL, QA, SG all remain
exactly priced, at exactly the same numbers, as before this repair.

**No candidate that reaches structure generation is blocked on a local
SPV/applicant-company/production-service-company requirement.** Verified
directly: nothing in `discover_executable_jurisdictions()` or
`resolve_program_rate()` currently gates on `requires_local_entity` at all
— it is carried only as descriptive `JurisdictionExamination` metadata,
never consulted in the accept/reject branches. The canonical product
assumption ("assume the production establishes the customary local
structure necessary to access an otherwise viable incentive") therefore
requires no active enforcement code today; this was verified empirically
(zero FVD unpriceable reasons mention local entity/SPV/applicant company)
rather than assumed, and is now covered by a regression test
(`test_no_fvd_candidate_is_blocked_on_local_entity_grounds`) so a future
change that *does* introduce such a gate is caught.

---

## Distinct QPE / incentive / NPC counts (after repair)

- **Distinct QPE values: 3** — `$4,154,821.00` (26 candidates, down from
  28), `$3,614,149.60` (GR, 1), `$1,132,056.00` (MU, 1).
- **Distinct selected-incentive values: 9**
- **Distinct NPC values: 9**

## Largest remaining repeated group

**QPE $4,154,821.00, 26 candidates**
(`AU-NSW, AU-QLD, AU-SA, CA-NL, CA-QC, CH, CR, DK, EG, FJ, GE, GH, IL, MT,
MX, MY, PA, PH, PT, QA, SG, TH, TW, UA, US-NY, ZA`)

**Classification: `LEGITIMATELY_EQUAL_UNDER_CANONICAL_RULES`.**

Every candidate in this group shares `OPEN_DEFAULT_INCLUDE` qualification
doctrine and no jurisdiction-specific category exclusion for FVD's actual
budget-category mix, so each independently sums to the identical eligible
pool (full budget minus memo lines, finance-cost category, and the
structural contingency exclusion — `$4,517,687.00 − $362,866.00 =
$4,154,821.00`). This is not `STILL_FLATTENED_BY_INPUT_DEFECT`: the input
assembly now correctly threads the real budget-account universe (Task 4,
verified below) and real SA-1 script requirements (Task 3) into every
candidate; the repeated QPE value is the CORRECT, explainable output of
identical doctrine treatment applied to the same real account set, exactly
as Codex's own diagnosis (§E) classified it before this repair — this
repair did not change that classification, only closed the separate,
genuinely-defective gap (capability matching on `{}`) that WAS silently
flattening candidate *eligibility* (not QPE math).

Within this group, `selected_incentive_usd`/NPC still differ by each
program's own real rate-resolution outcome (floor-vs-ceiling selection,
band-confirmation requirement) — e.g. CA-NL/QA both select `$1,661,928.40`
(their respective 40% floors), SG selects the *same* `$1,661,928.40` via
its own discretionary ceiling rate rather than its 30% floor, and MT
selects `$1,246,446.30` (its 30% floor) — each independently verified
against the real persisted segment, not copied.

**GR (`$3,614,149.60`)** and **MU (`$1,132,056.00`)** remain the two
material QPE differentiators, exactly as before this repair: GR's real
80%-of-eligible-spend statutory cap, and MU's real `HYBRID_CONDITIONAL`
doctrine (13 of FVD's real budget categories genuinely resolve to
`GREY_AREA_REQUIRES_AUTHORITY` under Mauritius's positive-list QPE
structure — verified directly against the persisted `qualification_trace`,
not inferred).

---

## Representative jurisdiction traces

All read directly from the real, persisted `canonical-1.3.0`
`StructureCalculationResult` rows (verified again via
`test_representative_fvd_jurisdiction_traces`).

| Jurisdiction | Program | QPE | Rate floor/ceiling | Band? | Confirmation? | Selected incentive | NPC |
|---|---|---:|---|:-:|:-:|---:|---:|
| **GR** | `gr_cash_rebate` | $3,614,149.60 (after $540,671.40 80%-cap exclusion) | 40% / 40% | No | No | $1,445,659.84 | $3,072,027.16 |
| **CA-NL** | `ca_nl_all_spend_credit` | $4,154,821.00 | 40% / 45% | Yes | Yes | $1,661,928.40 (floor) | $2,855,758.60 |
| **QA** | `qa_screen_production_incentive` | $4,154,821.00 | 40% / 50% | Yes | Yes | $1,661,928.40 (floor) | $2,855,758.60 |
| **SG** | `sg_made_with_singapore_rebate` | $4,154,821.00 | 30% / 40% | Yes | No | $1,661,928.40 (ceiling — own modeled rate) | $2,855,758.60 |
| **MT** | `mt_mfc_rebate` | $4,154,821.00 | 30% / 40% | Yes | Yes | $1,246,446.30 (floor) | $3,271,240.70 |
| **MU** | `mu_edb_incentive` | $1,132,056.00 (13 categories GREY under HYBRID_CONDITIONAL) | 30% / 40% | Yes | Yes | $339,616.80 (floor) | $4,178,070.20 |
| **QLD (AU-QLD)** | `au_qld_pdv_rebate` | $4,154,821.00 | 15% / 15% | No | No | $623,223.15 | $3,894,463.85 |

Key project facts consumed for every row above: FVD's real 34-line budget
(`gross_budget_usd = $4,517,687.00`), each program's own statutory
doctrine/rate rules (unchanged, read-only). **UNKNOWN facts affecting
confidence**: every row above carries `has_unverified_inputs=True` and the
explicit warning that `budget_accounts_outside_base_jurisdiction`/
`budget_offshore_payroll_accounts` were never stated for this project — the
QPE above assumes no accounts are territorially excluded, which is the
only safe input the qualification ladder's set-membership check can be
given, but that assumption is unconfirmed, not verified.

---

## Little Utopia regression

Narrow regression only — LU's optimizer/candidate-generation validation
was not reopened.

`evaluate_project(db, LITTLE_UTOPIA_PROJECT_ID)`: winner **Mauritius**,
`true_net_cost_usd = $3,057,794.90`, `is_baseline = True` — unchanged.

This repair's real effect — `build_physical_requirements()` reading
`ProjectLocationRequirement`/`ProductionRequirement` rows — is a genuine
no-op for Little Utopia through this generic path: LU's own script data
lives in `little_utopia_state.py`'s hand-built Python constants
(`SCRIPT_REQUIREMENTS`, `LOCATION_TAXONOMY`), not in the generic SA-1 DB
tables this function reads, so the query finds nothing new for LU either
way (confirmed: LU's generic-adapter priced/unpriceable counts are
unchanged at 30/80, still including MN/UZ in its own flattened group,
since no marine requirement is derived from empty DB tables). **LU's real
served path is the separate in-memory demo state
(`app.demo.little_utopia_state`) reached through the `is_demo_project`
branch in `get_project_state()`, entirely untouched by this repair** — the
generic-adapter view checked above is not what LU's own UI actually serves.

**LU regression: PASS.**

---

## Scope discipline

- **No UI file changed.** Top-6/Workspace/Scenarios ordering, FX, and MFNI
  are untouched.
- **No global incentive rule changed.** `program_spend_rules.py`,
  `program_rate_rules.py`, `authority_coverage_registry.py`, and every
  jurisdiction data file are unmodified; every number difference in this
  repair traces to candidate *eligibility* (capability matching), never to
  a re-evaluated rate, threshold, or QPE rule.
- **The optimizer was not revalidated.** `discover_executable_jurisdictions()`,
  `derive_qualification_register()`, `derive_account_allocation()`,
  `price_allocated_structure()`, and `rank_allocated_structures()` are
  called exactly as before, unmodified, with better inputs.
- **Files touched**: `canonical_project_economics.py`,
  `canonical_evaluation.py` (the two named in the task's strict file
  boundary), plus targeted tests
  (`test_fvd_canonical_input_assembly_repair.py`, new; two stale
  hardcoded counts updated in the prior
  `test_canonical_served_wiring_repair.py`, since this repair's real,
  legitimate candidate-eligibility change made them factually wrong, not
  because the prior repair's own assertions were incorrect at the time
  they were written).

---

## Tests

`pytest` — 4131 passed, 1 pre-existing unrelated failure (`test_scenarios_
and_workspace_both_use_the_canonical_title_formatter`, `Workspace.jsx` vs
`scenarioDisplay()` — predates this session, outside this repair's file
scope, previously reported, not re-fixed here), 1 skipped.

New: `tests/test_fvd_canonical_input_assembly_repair.py` (11 tests) —
UNKNOWN-vs-known-empty disclosure, the location-category bridge (pure
function, deterministic), real SA-1 requirements reaching discovery,
landlocked-jurisdiction capability rejection, marine-capable jurisdictions
unaffected, real budget-account identity reaching allocation, the
local-entity no-op verification, all seven representative traces, and the
LU narrow regression.

Updated: two hardcoded candidate counts in
`tests/test_canonical_served_wiring_repair.py` (30/1/29/80 →
28/1/27/61) — the prior repair's own numeric assertions on Malta/Mauritius/
Australia-Queensland/Australia-Location-Offset traces and the stale-row
safety tests are unaffected and still pass unchanged.

---

## Final gate

**`FVD_CANONICAL_INPUT_ASSEMBLY_REPAIRED`**

FVD evaluation now uses real, persisted SA-1 canonical project-state
provenance (scripted locations, production requirements) instead of a
permanent `{}`. Absent territorial facts remain visibly UNKNOWN
(`has_unverified_inputs=True` + explicit warning) rather than silently
equivalent to a confirmed empty set. Persisted SA-1 requirements are
consumed for capability matching. The real FVD budget/account universe
reaches allocation (verified: GR's cap and MU's doctrine independently
differentiate QPE from the shared-doctrine group). Ordinary local
production-entity requirements do not falsely block pricing (verified:
zero such blocks exist today). Post-repair QPE/incentive/NPC
differentiation is fully explainable: 26 candidates share $4,154,821 QPE
under identical `OPEN_DEFAULT_INCLUDE` doctrine and identical real-budget
treatment — `LEGITIMATELY_EQUAL_UNDER_CANONICAL_RULES`, not a residual
input defect. No frontend change occurred. No global incentive/rule
change occurred. LU regression remains exact.
