# Codex LU vs FVD Topline NPC Path Trace

**Gate:** `CODEX_LU_FVD_NPC_PATH_LOCALIZED`

**Mode:** read-only runtime/code trace; no optimizer, authority, or implementation audit

**Observed:** 2026-08-17

## Conclusion

There is no LU-vs-FVD NPC formula defect. Both evaluations ultimately call
`allocation_pricing.price_allocated_structure()` and use the same formula.
The apparent arithmetic difference has two concrete causes:

1. LU is title-routed to a project-specific, cached in-memory builder that
   supplies travel, FX, Mauritius in-kind replacement, and local-cost deltas.
   Its served `npc_with_adjustments_usd` includes those deltas. FVD is served
   from persisted generic evaluator rows whose current caller supplies zero
   travel, in-kind, and local-cost deltas and no FX delta. For FVD, therefore,
   `npc_with_adjustments_usd` presently collapses to budget minus incentive.
2. The scenario table displays gross budget, QPE, `selected_incentive_usd`,
   and `npc_with_adjustments_usd`, but omits the adjustment fields between
   incentive and adjusted NPC. It even deliberately hides FX. An LU relocation
   card therefore cannot be reconciled from the visible rows alone.

There is also a separate field-selection defect: the hero always renders the
optimizer's rank-1 structure. It does not use the AppState/persisted leading
structure selected in Scenarios or Workspace. The hero and cards use the same
NPC *field*, but may use different structure records after a selection.

## End-to-end paths

| Step | Little Utopia | F#K Valentine's Day | Classification |
|---|---|---|---|
| Project/budget source | `LittleUtopiaState.gross_budget_usd`, built from `MU_GROSS_BUDGET_USD` / the real LU budget module; served value $4,364,393 | latest `BudgetDocument.total_budget_raw` feeds `ProjectEconomicInputs.gross_budget_usd`; the view uses `Project.total_budget_usd` or falls back to latest `BudgetDocument.total_budget_raw`. FVD currently takes the fallback: $4,517,687 | `DIFFERENT_PATH` |
| State source | `cineglobe.get_project_state()` recognizes the exact title `The Little Utopia`, then calls `get_production()` / `get_structures()` over cached `get_state()` | same endpoint calls `canonical_production_view.build_production_and_structures()` | `LEGACY_PATH` for LU; `DIFFERENT_PATH` |
| Evaluator | `little_utopia_state.build_allocated_structures()` payload version 1.1.0, using `allocation_pricing` 1.0.0 | `canonical_evaluation` engine `canonical-1.12.0`, using the same `allocation_pricing.price_allocated_structure()` kernel | `DIFFERENT_PATH`, then `SAME_PATH` at pricing kernel |
| Fresh/persisted | Generated from an `lru_cache`-backed in-process LU state; not read from `StructureCalculationResult` for this API response | API GET reads already persisted `ProductionStructure` + `StructureCalculationResult` rows selected by the leading result's fingerprint/version | `LEGACY_PATH` vs persisted path |
| QPE/incentive | Per-segment QPE; `selected_incentive_usd` is the sum of each confirmed ceiling or, where confirmation is required, its floor | same calculation when the row is produced; persisted as `total_incentive_value_usd`, then mapped back to `selected_incentive_usd` | `SAME_PATH` |
| NPC stored/served | builder serializes `npc_verified_usd` and `npc_with_adjustments_usd` directly | evaluator persists verified NPC in `true_net_cost_usd` and adjusted NPC in `risk_adjusted_net_cost_usd`; adapter maps them to the same two served field names | `SAME_PATH` semantics; `DIFFERENT_PATH` storage |
| API payload | `structures.allocated_structures.structures[*].selected_incentive_usd` and `.npc_with_adjustments_usd` from LU builder | same JSON paths from persisted-row adapter | `SAME_PATH` |
| Hero resolution | `ProjectHeader` resolves rank 1 and passes that structure to `ProductionHero` | identical | `SAME_PATH`; selection is a `FIELD_MAPPING_DEFECT` for both |
| Hero field | `topStructure.npc_with_adjustments_usd` | identical | `SAME_PATH` |
| Scenario field | `s.selected_incentive_usd`; `s.npc_with_adjustments_usd` | identical | `SAME_PATH` |
| Frontend calculation | no NPC recomputation; only the separate “Vs current/base” difference is computed client-side | identical | `NO_DEFECT` |

## Exact formula

`allocation_pricing.price_allocated_structure()` defines:

```text
selected_incentive = sum(segment confirmed ceiling, otherwise segment floor)

npc_verified = gross_budget
             - selected_incentive
             + financing_cost
             + implementation_cost

npc_with_adjustments = npc_verified
                     + travel_incremental_delta
                     + fx_delta
                     + inkind_replacement_delta
                     + local_cost_delta
```

All nullable deltas are treated as zero. The canonical hero/ranking/scenario
field is `npc_with_adjustments_usd`, not `npc_verified_usd`.

### LU runtime proof

The in-memory builder returned:

| Scenario | Gross | Selected incentive | Verified NPC | In-kind delta | Local-cost delta | Adjusted/served NPC |
|---|---:|---:|---:|---:|---:|---:|
| MU baseline | $4,364,393.00 | $1,306,598.10 | $3,057,794.90 | $0 | $0 | $3,057,794.90 |
| Full relocation to SA | $4,364,393.00 | $2,432,517.60 | $1,931,875.40 | $625,000 | $729,300 | $3,286,175.40 |
| MU shoot + post routed to SA | $4,364,393.00 | $1,327,788.90 | $3,036,604.10 | $625,000 | $0 | $3,661,604.10 |

Thus LU alternatives do start with total project budget minus displayed
`selected_incentive_usd`; they then add the served adjustment fields. The SA
relocation example reconciles exactly:
`4,364,393 - 2,432,517.60 + 625,000 + 729,300 = 3,286,175.40`.

Mauritius has no separate NPC formula. It is treated differently only by the
inputs to the shared formula: an MU-anchored structure that keeps post in MU
gets zero in-kind replacement; a structure that routes that work out of MU
gets the modeled $625,000 replacement cost. Jurisdiction-specific travel, FX,
and local-cost normalizations can also be supplied.

### FVD runtime proof

The current leading persisted row is `canonical-1.12.0`, created
2026-08-17, fingerprint
`bb48c6e76623545f7718ebff65cfd14bfd8ff47ea4c6cbd07ec6a5b7473ae79f`:

```text
gross budget                $4,517,687.00
QPE                         $3,614,149.60
selected incentive          $1,445,659.84
true_net_cost_usd           $3,072,027.16
risk_adjusted_net_cost_usd  $3,072,027.16
```

The FVD evaluator explicitly passes travel `0.0`, FX `None`, in-kind `0.0`,
and local cost `0.0`; financing and implementation retain their zero defaults.
Therefore `4,517,687 - 1,445,659.84 = 3,072,027.16`. The API GET reuses this
persisted current-engine row; it does not recalculate on read. No stale-engine
value was observed.

## Selection/topline behavior

- `Scenarios` and `Workspace` put a user choice in
  `AppState.leadingStructureId` and attempt to PATCH `leading_structure_id`.
- `ProjectHeader` does not consume either value. It always finds
  `allocated.ranking.find(rank === 1)`.
- `ProductionHero` renders that record's `npc_with_adjustments_usd`.
- Scenario cards render each card record's `npc_with_adjustments_usd`.

So the hero and cards share the exact NPC field, but the hero is not the
selected card unless the selection is rank 1. This is more visible for LU,
whose specialized builder marks normalized alternatives directly comparable;
FVD's generic evaluator marks only the baseline directly comparable and its
current leading persisted structure is that baseline.

## First divergence and classification

The first divergence is
`backend/app/api/v1/cineglobe.py::get_project_state()`: the exact-title check
at `is_demo_project = project.title == PRODUCTION_NAME` sends LU to
`get_state()` / `build_allocated_structures()`, while FVD goes to
`canonical_production_view.build_production_and_structures()` and persisted
calculation rows.

- LU title fork/state source: `LEGACY_PATH`
- FVD persisted current-engine source: `NO_DEFECT` (not stale in the observed row)
- Shared incentive and NPC kernel: `SAME_PATH`, `NO_DEFECT`
- Adjustment inputs: `DIFFERENT_PATH`
- API field names after mapping: `SAME_PATH`, `NO_DEFECT`
- Frontend NPC recomputation: none, `NO_DEFECT`
- Missing LU adjustment reconciliation in the visible scenario rows:
  `FIELD_MAPPING_DEFECT` (presentation omission, not arithmetic corruption)
- Hero ignoring selected/leading structure: `FIELD_MAPPING_DEFECT`
- Formula defect: none observed

## Smallest repair surface (not performed)

1. `frontend/src/screens/production/Scenarios.jsx::Scenarios`: expose the
   travel, FX, in-kind replacement, local-cost, financing, and implementation
   bridge between displayed incentive and `npc_with_adjustments_usd`.
2. `frontend/src/shell/ProjectHeader.jsx::ProjectHeader`: resolve the hero
   structure through the same active/leading-structure selection used by the
   production screens instead of hard-coding rank 1.
3. `frontend/src/components/ProductionHero.jsx::ProductionHero`: if adjusted
   NPC remains the hero metric, make the caption disclose that it can include
   more than incentives/rebates.

No backend formula change is supported by this trace. Converging LU onto the
generic persisted path would be a larger architecture migration, not the
smallest repair for the observed arithmetic/selection presentation.
