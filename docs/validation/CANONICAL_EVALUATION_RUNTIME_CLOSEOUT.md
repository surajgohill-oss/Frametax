# Canonical Evaluation Runtime — Unification Closeout (Phase 1)

Date: 2026-08-15
Branch: `claude/audit-frametax-features-NZcX5`

## Gate

**`CANONICAL_EVALUATION_RUNTIME_BLOCKED`** — the phase's *specified direction* was
proven wrong by runtime evidence and was inverted with the master engineer's
approval. Phase 1 of the inverted plan is complete and proven; the remaining
gate conditions (served-path cutover, overlay, feasibility model, FVD re-do)
are not yet met and are scoped below.

## The prior two-runtime architecture

| | System A — served Little Utopia | System B — generic DB-backed |
|---|---|---|
| Entry | `/api/v1/cineglobe/*` | `POST /projects/{id}/evaluation/begin` |
| State | `app/demo/little_utopia_state.py` singleton | `CanonicalProductionState` |
| Economics | `build_allocated_structures` chain | `run_full_analysis` |
| Consumers | all 9 `/production/*` screens + optimizer overlay (`useCineGlobe`) | Project Record only |

## The finding that inverted this phase

The prompt specified System B as canonical and System A as the legacy special
case to retire. **Runtime evidence shows the economics are the other way
around.**

`run_full_analysis` is `ENGINE_VERSION = "0.1.0"` and imports
`rank_production_structures` — which `cineglobe.py`'s own docstring names as
part of "the legacy stack `optimization.py` still calls." Its entire call chain
references **zero** canonical layers:

| Canonical layer | References in the `run_full_analysis` chain |
|---|---|
| `program_spend_rules` (QPE doctrine) | 0 |
| `program_rate_rules` (statutory rate resolution) | 0 |
| `authority_coverage_registry` | 0 |
| `qualification_model` (account register) | 0 |
| `production_allocation` / `allocation_pricing` | 0 |
| `production_discovery` | 0 |

Priced against Little Utopia's real 44-line budget in Mauritius it returns:

```
true net cost         : $4,181,808.00
total incentive value : $0.00          ← cannot resolve LU's own MU program
CANONICAL ACCEPTED    : $3,057,794.90
DELTA                 : $1,124,013.10
```

It also reads gross as the leaf sum ($4,364,395) rather than the document's
declared total ($4,364,393). The DB holds **7** `QualifyingSpendCategory` rows
for Mauritius; canonical `MU_EDB_RULES` is the **33-category** closed list from
the primary EDB document.

Gate conditions 3 and 4 were therefore **structurally unreachable** in the
specified direction — not for missing project evidence, but because the target
engine lacks the validated machinery. Migrating LU onto it would have done
exactly what Rule 12 forbids. Direction inverted on approval: **generalize the
canonical engine** rather than migrate LU onto the legacy one.

## Final canonical runtime (target)

```
Project
  -> canonical_project_economics.build_project_economic_inputs()   ← NEW, Phase 1
       BudgetDocument.total_budget_raw   -> authoritative gross
       BudgetLineItem rows               -> BudgetLine(account_code, …)
       BudgetLineItem.spend_category     -> spend_category_by_code
       ProjectFact territorial evidence  -> accounts_outside_jurisdiction
       Project.home_jurisdiction_id      -> base jurisdiction
  -> derive_qualification_register()        (canonical, already generic)
  -> production_discovery                   (canonical, already generic)
  -> derive_account_allocation()            (canonical, already generic)
  -> price_allocated_structure()            (canonical, already generic)
  -> rank_allocated_structures()            (canonical, already generic)
  -> ProductionStructure / StructureCalculationResult
  -> one served API + UI
```

The key discovery that made this tractable: **the canonical calculators were
already fully generic.** `derive_qualification_register`,
`derive_account_allocation` and `price_allocated_structure` take plain data —
not a `LittleUtopiaState`. Only their *input data* was project-specific.
`build_little_utopia_real_register` is a thin data wrapper that already
delegates to the generic `derive_qualification_register`.

## Little Utopia migration result — EXACT

Territorial evidence moved out of the Little-Utopia-specific module constant
`LITTLE_UTOPIA_REAL_ACCOUNTS_OUTSIDE_MU` and into generic persisted
`ProjectFact` rows (Part C — evidence migrated, never calculated outputs):

| Fact key | Value |
|---|---|
| `budget_accounts_outside_base_jurisdiction` | `["5000","5100","5200","5300","5400","5500","6500"]` |
| `budget_offshore_payroll_accounts` | `[]` |

`Project.home_jurisdiction_id` for LU resolved to Mauritius **through the
existing generic filename-evidence deriver** (its budget is
`The Little Utopia Budget Mauritius 3rd June 2025 v1 (1).pdf`) — not set by hand.

Driving the canonical calculators from **only** these generic persisted rows:

```
GENERIC INPUTS FROM DB : 44 lines | authoritative gross $4,364,393.00
register accounts      : 44
is_fully_priced        : True
selected incentive     : $1,306,598.10
NPC (verified)         : $3,057,794.90

ACCEPTED CANONICAL     : $3,057,794.90
DELTA                  : $0.00
```

**Exact LU NPC: $3,057,794.90 — $0.00 delta. Winner: Mauritius.** No economics
were changed to make the migration fit; the accepted figure was reproduced, not
forced.

## FVD result

Unchanged and intact this phase: actual budget **$4,517,687**, Greece baseline
derived from its own budget filename evidence. **However — correction to the
previous closeout:** FVD's $3,627,135.60 was produced by the *legacy* engine
(`run_full_analysis`), so it is **not canonical-grade**. `87440df` reported it
as accepted; that was wrong. FVD must be re-evaluated through the canonical
engine as part of Phase 2.

## UI / overlay data source

Unchanged this phase. Every `/production/*` screen and the optimizer overlay
still read `useCineGlobe()` → 8 `/api/v1/cineglobe/*` endpoints → System A.
The overlay specifically consumes `data.structures.allocated_structures.ranking`.
Cutover is Phase 2.

## Abu Dhabi observed case — VERIFIED ROOT CAUSE

Not a treaty artifact, not stale demo data, not the generic generator.
`ALLOC-RELOC-AE-AD` and `ALLOC-COMPONENT-POST-AE-AD` are generated by the
canonical structure generator because AE-AD is **production-capable**, then
correctly refused pricing by the authority-coverage layer:

```json
{ "rank": null, "is_fully_priced": false,
  "excluded_from_ranking_because": [
    "AE-AD/ae_ad_film_rebate: UNPRICEABLE_AUTHORITY_INSUFFICIENT — Authority is
     insufficient to price deterministically… Excluded from pricing and ranking
     rather than inheriting a stale stored value. This is NOT a validated zero
     benefit." ] }
```

**Disposition: the backend is already correct.** The defect is presentational —
these entries sit in the same served `ranking` array as executable structures,
so the overlay can render them alongside verified ones. This is a UI/feasibility
-state fix, not an economics fix, and it argues *for* the canonical engine:
System B has no authority-coverage layer and would have silently priced AE-AD as
ordinary. **No regional ban was added and none is warranted.**

## Feasibility model

**Not yet implemented** (Parts H–M). Deferred to Phase 2. The canonical engine
already carries the substrate it needs: `is_fully_priced`,
`excluded_from_ranking_because`, and `UNPRICEABLE_AUTHORITY_INSUFFICIENT` are
economic-candidacy states that map onto the required
FEASIBLE / REVIEW_REQUIRED / BLOCKED / UNKNOWN enum without new research.

## Candidate accounting

Unchanged this phase — System A already accounts for every candidate with an
explicit reason and no silent drops (179 ranking entries, each either ranked or
carrying `excluded_from_ranking_because`).

## MFNI limitation

Preserved. Still surfaced on the Project Record Analysis panel, and no ranked
alternative implies localized production-cost normalization. No MFNI work started.

## Defects fixed

1. **Inverted the unification direction** on evidence, preventing a $1.12M
   economics regression against validated LU truth.
2. **Restored LU's `ALLOC-BASELINE-MU` `ProductionStructure` + calc result +
   `leading_structure_id`**, which a diagnostic run of the generic evaluator in
   this session deleted. Restored to migration 0063's exact values, unchanged.
3. Corrected the record on FVD's canonical-grade status (above).

## Tests

Four new in `tests/test_canonical_project_economics.py`:

1. `test_generic_inputs_resolve_from_persisted_project_evidence_only`
2. `test_declared_grand_total_is_the_basis_not_the_leaf_sum`
3. **`test_little_utopia_canonical_npc_reproduced_from_generic_inputs`** — the
   acceptance test for the inversion; asserts $3,057,794.90 and $1,306,598.10 exactly
4. `test_canonical_economics_module_reads_no_project_specific_data` (AST-level
   import guard)

`tests/test_project_library_phase_c.py::test_project_facts_with_provenance`
updated 11 → 13 facts, asserting the two migrated territorial-evidence facts
explicitly rather than just bumping the count.

Full backend suite: **4094 passed, 1 skipped, 1 pre-existing unrelated failure**
(`test_global_discovery.py`'s `Workspace.jsx` formatter check — untouched here).

## Remaining for Phase 2

1. Generic canonical evaluation service (discovery → specs → allocation →
   pricing → rank → persist) on top of this bridge.
2. Re-evaluate FVD through it; retire its legacy-engine result.
3. Cut `useCineGlobe()` and the optimizer overlay onto persisted canonical rows.
4. Feasibility enum + REVIEW_REQUIRED presentation (Abu Dhabi case).
5. Mark `little_utopia_state.py` NON-CANONICAL / TEST-ONLY once unserved.
6. Canonical program identity/alias resolution (the 26 skipped FVD candidates).
