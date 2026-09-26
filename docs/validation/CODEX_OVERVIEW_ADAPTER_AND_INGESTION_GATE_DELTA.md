# Codex Overview Adapter and Ingestion-Gate Delta

## Final delta verdict

**READY FOR ONE BOUNDED REMEDIATION PASS.** The exhaustive four-production Overview check found exactly two producer-visible adapter defects, both confined to the `OPTIMIZED` card: qualified spend is falsely rendered as `$0`, and gross budget is falsely rendered as `—`. The canonical backend structures and every other inspected producer-visible value are correct and agree with Workspace, Inspector, Full Project Globe, and Globe hover. The ingestion gate is **STALE_REQUIRES_REVERIFICATION**: the current four-budget corpus contains the documented remediation, but no independent post-remediation Codex certification covers the current parser/ingestion lineage.

No evaluation, database mutation, service restart, production/test-file edit, broad regression run, or authority research was performed.

## 1. Starting gate

| Gate | Result |
|---|---|
| Repository / worktree | PASS — `surajgohill-oss/Frametax`; `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` |
| Branch | PASS — `claude/global-optimizer-remediation` |
| Required starting SHA | PASS — local and `origin/claude/global-optimizer-remediation` both `afa171042cfafcdf7728c29524e583ae375bf6f2` after fetch |
| Worktree | PASS — only permitted untracked runtime logs `.backend_gd_wire.log` and `.frontend_gd_wire.log` |
| Frontend | PASS — one Vite service at `http://localhost:5173` (PID 96132) |
| Backend | PASS — one uvicorn reload service at `http://127.0.0.1:8010` (supervisor/worker PIDs 5993/65052) |
| Database | PASS — `frametax2_claude_optimizer_acceptance_20260919` |
| Organization | PASS — `11381771-5b1c-4980-9117-e3e47a4cb354`, Mind The Story Media |

The prior accepted scope in `CODEX_FINAL_GLOBE_WORKSPACE_ACCEPTANCE.md` was not reopened. This audit used current served state, current frontend code, direct local-browser interaction, repository lineage, and focused tests only.

## 2. Exact four-project Overview reconciliation

For each project, `recommended_optimizer_options[0]`, Overview Project Globe/Top Structures, Workspace optimizer card, Workspace Inspector, Full Project Globe recommendation, and Globe hover resolved to the same `structure_id` and economic identity. Each canonical optimizer structure is fully priced, `RECOMMENDED`, `ADVANCED_MULTI_JURISDICTION`, `hybrid`, has three participants, has `segments=[]`, and has three populated `component_allocations`.

| Project | Canonical structure / economic identity | Label and route | Canonical gross / component QPE | Incentive / NPC / savings vs Current | Overview result |
|---|---|---|---:|---:|---|
| The Little Utopia | `559a49ce-6581-4e78-ad8a-733f424e0b74` / `89f543279d132bcea03c6ce44cde857af6c5a31fdf369938392b36e469bbea05` | Manitoba principal `$4,302,827`; Newfoundland & Labrador post `$9,068`; Italy VFX `$52,500` | `$4,364,393` / `$4,364,395` | `$1,825,390.40` / `$2,539,002.60` / `$1,252,330.70` | All identity, status, route, warnings, incentive, NPC, and savings fields PASS. Gross `—` and QPE `$0` FAIL. |
| Bad Hombres | `da3b394b-152f-4637-a238-a9dcfa9e5eb2` / `bb142bd7a3805991ef3c6f1b0a480ca3aa5fc85d070f43de83a3bb70d24fa5a0` | Manitoba principal `$2,369,065`; Newfoundland & Labrador music `$5,000`; Italy post `$107,958` | `$2,482,023` / `$2,482,023` | `$1,068,790.55` / `$1,413,232.45` / `$471,880.30` | All identity, status, route, warnings, incentive, NPC, and savings fields PASS. Gross `—` and QPE `$0` FAIL. |
| F#K Valentine's Day | `dbcf5bda-a4af-4a70-a968-e4e6b19b0ce4` / `f8bced42ee725ccf7daf4196b7bbaea53b4b111f5b30513a267e2f77440ed69a` | Manitoba principal `$4,497,487`; Newfoundland & Labrador music `$10,200`; Italy VFX `$10,000` | `$4,517,687` / `$4,517,687` | `$1,664,547.10` / `$2,853,139.90` / `$218,887.26` | All identity, status, route, warnings, incentive, NPC, and savings fields PASS. Gross `—` and QPE `$0` FAIL. |
| Lips Like Sugar | `601a8a8f-d1b0-42f1-8aef-5934e0422502` / `1e6c80a564510dde3c2fea3cd99b21a5625c63c1ffcb6cb6d5cc3ef6bdd71d02` | Manitoba principal `$11,736,880`; Newfoundland & Labrador music `$206,774`; Italy VFX `$40,000` | `$11,983,654` / `$11,983,654` | `$4,435,305.60` / `$7,548,348.40` / `$976,026.70` | All identity, status, route, warnings, incentive, NPC, and savings fields PASS. Gross `—` and QPE `$0` FAIL. |

All four carry the same three program identities appropriate to their routes: `ca_mb_film_video_credit`, `ca_nl_all_spend_credit`, and `it_tax_credit_foreign`. Participant names, flags, program names, the three-participant count, recommendation status, practicality tier, route labels, and the administrative-allocation-risk disclosure reconcile to the canonical record. There is no conditional/fact-gated state on these four selected structures.

The Anchor and two Leading cards on every project reconciled without a null, false zero, stale value, independent economic re-derivation, label error, or unexpected rounding difference. The conditional fund/opportunity fallback is not active for this corpus because a real canonical optimizer projection exists; its focused tests confirm that it exposes names/count only and does not fabricate a dollar value. No separate Alternative card is selected while a recommended optimizer exists. Thus the two failures below affect the selected Optimized card only and do not imply an optimizer-generation defect.

## 3. Complete confirmed defect list

### OAD-001 — Optimized qualified spend falsely collapses to zero

- **Affected projects/identities:** all four exact structures and identities in the matrix above.
- **Backend source:** `component_allocations[].allocated_usd`; expected sums are `$4,364,395`, `$2,482,023`, `$4,517,687`, and `$11,983,654` respectively. `segments` is legitimately empty.
- **Overview path:** `frontend/src/components/IncentiveIntelligence.jsx:OptionCard` calls `frontend/src/lib/productionOptions.js:qpeOf()`.
- **Rendered value:** `$0` on all four Optimized cards.
- **Reproduction:** open a production Overview, locate Top Structures -> `OPTIMIZED`, compare Qualified Spend with the same structure in Workspace or Inspector.
- **Root cause:** `qpeOf()` only reduces `segments[].qpe_usd` and interprets the absence of that storage representation as economic zero. Workspace `ScenarioCard` correctly uses segments when present and otherwise sums `component_allocations[].allocated_usd`.
- **Smallest repair:** make the shared `qpeOf()` use the same mutually exclusive segment-first/component-allocation fallback.
- **Independent oracle:** assert both representations independently, including empty segments plus allocations, populated segments plus allocations (segments win; never add both), and neither representation.

### OAD-002 — Optimized gross budget falsely collapses to missing

- **Affected projects/identities:** all four exact structures and identities in the matrix above.
- **Backend source:** each optimizer structure has `gross_budget_usd=null`; the same state response carries the canonical project-wide `production.gross_budget_usd` values `$4,364,393`, `$2,482,023`, `$4,517,687`, and `$11,983,654`.
- **Overview path:** `frontend/src/components/IncentiveIntelligence.jsx:OptionCard` reads only `structure.gross_budget_usd`; `IncentiveIntelligence` does not receive production gross. `Overview.jsx` already has the canonical value and passes it to `buildGlobeView`, but not to `IncentiveIntelligence`.
- **Rendered value:** `—` on all four Optimized cards.
- **Reproduction:** open a production Overview, locate Top Structures -> `OPTIMIZED`, compare Gross Budget with the production budget and the same Workspace structure.
- **Root cause:** a structure-level null erases an available, legitimately project-wide value at this one consumer.
- **Smallest repair:** pass `data.production.gross_budget_usd` through `Overview` -> `IncentiveIntelligence` -> `OptionCard`, with structure value first and project value only as fallback.
- **Independent oracle:** prove `structure.gross_budget_usd` wins when populated, production gross fills only null/undefined structure gross, and both absent render `—`.

No third Overview adapter defect was reproduced. In particular, incentive, NPC, savings, canonical identity, classification, participants, jurisdiction/program labels, route summary, warnings, and card selection/order are served and rendered consistently.

## 4. Exact one-pass implementation manifest

### Required changes

1. **`frametax2/frontend/src/lib/productionOptions.js:qpeOf`**
   - If `segments` contains one or more real rows, return the sum of `segments[].qpe_usd`.
   - Otherwise, if `component_allocations` contains rows, return the sum of `component_allocations[].allocated_usd`.
   - Otherwise return zero under the existing fully-priced display contract.
   - Share this helper with any consumer needing the same canonical display rule; do not create a second Overview formula. The required precedence is the existing Workspace `ScenarioCard` rule.

2. **`frametax2/frontend/src/components/IncentiveIntelligence.jsx:IncentiveIntelligence` and `OptionCard`**
   - Accept a `grossBudgetUsd` prop and pass it to every option card.
   - Render gross from `structure.gross_budget_usd ?? grossBudgetUsd`; render `—` only when both are null/undefined.
   - Continue to render QPE through corrected shared `qpeOf()` only when `structure.is_fully_priced` is true.

3. **`frametax2/frontend/src/screens/production/Overview.jsx:Overview`**
   - Pass `data?.production?.gross_budget_usd ?? null` to `IncentiveIntelligence`, using the same served production field already passed to `buildGlobeView`.

### Prohibited calculations or scope expansion

- Do not add segment QPE and component allocation amounts; they are alternate canonical representations and doing so can double count.
- Do not infer gross budget from QPE, incentive, NPC, allocation totals, or route components.
- Do not mutate optimizer structures to inject a project gross value.
- Do not change backend payloads, optimizer generation, scenario selection/order, identities, economics, recommendation thresholds, warning rules, labels, or conditional opportunity behavior.
- Do not add project- or jurisdiction-specific branches.

### Focused tests required

- Extend the production-options/Overview focused tests with numeric expected-value assertions for both `qpeOf` representations and their precedence.
- Extend the `IncentiveIntelligence` contract test to prove structure-gross precedence, production-gross fallback, and genuine missing behavior.
- Add a pure four-project fixture asserting the exact gross/QPE expected pairs in the matrix, independent of the implementation formula.
- Preserve and rerun `overview-anchor-scenarios.test.mjs`, `fvd-economic-invariants.test.mjs`, and `producer-optimizer-projection-ui.test.mjs`. At this starting SHA they pass **31/31**, demonstrating the current oracle gap: none rejects OAD-001 or OAD-002.

### Browser acceptance

For each of the four projects, open Overview and confirm the selected `OPTIMIZED` card shows the matrix's gross and QPE. Click the card and reconcile structure ID/economic identity, label, participants, programs, incentive, NPC, savings, warning, status, tier, and route with Inspector, Workspace, Full Project Globe, and hover. Recheck every Anchor and Leading card for unchanged values and ordering. Confirm no console error or failed request.

### Acceptance and stop conditions

Accept only when all four Optimized cards show exact expected gross and QPE, focused tests include independent numeric oracles and pass, all already-correct fields/cards remain unchanged, and the diff is confined to the three named frontend locations plus focused tests. Stop without broadening the repair if a served payload differs from the identities/values above, the runtime DB/organization changes, or the change would require backend/optimizer economics.

## 5. Ingestion-gate status and evidence

**Classification: STALE_REQUIRES_REVERIFICATION.**

The independent Codex artifact `CANONICAL_BUDGET_PARSER_INTEGRITY_AUDIT_CODEX.md` locks the exact same four projects and budget documents and verifies all 158 monetary lines. It passes extraction/persistence, source totals, exact-once preservation, and source/scenario-finance separation, but its final gate is explicitly `CANONICAL_BUDGET_PARSER_INTEGRITY: FAIL` because BPI-001 through BPI-009 remained at that audit commit.

`CANONICAL_BUDGET_PARSER_REMEDIATION_CLAUDE.md` documents repairs for BPI-001 through BPI-009 and a 16-family self-verification gate. Current read-only database inspection is consistent with that remediation:

| Project | Project ID | Active BudgetDocument / version | Lines | Source total / line sum | Current parser version |
|---|---|---|---:|---:|---|
| The Little Utopia | `fa5cade5-0669-4816-bfe6-72146f8d3bae` | `b06185a9-9f48-41f7-9fa8-182a95926824` / `ee810c4f-8af3-4bdd-ba00-c5989c104172` | 44 | `$4,364,393` / `$4,364,395` | `budget-1.3.0+rules.eaef9e583fc5` |
| F#K Valentine's Day | `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | `29419055-9720-4e77-a673-020e3a87e3c8` / `cf33eae1-aa4e-4e4e-80d2-ce737f5a373e` | 34 | `$4,517,687` / `$4,517,687` | `budget-1.3.0+rules.eaef9e583fc5` |
| Bad Hombres | `4355ae88-a636-4c18-af60-ad73b2646124` | `14401d09-eaec-483b-a27d-eed9a7149fe7` / `06791475-82f0-4398-9cf1-19a7234bfce9` | 34 | `$2,482,023` / `$2,482,023` | `budget-1.3.0+rules.eaef9e583fc5` |
| Lips Like Sugar | `ab10b319-978e-44d3-9331-af2a5f2cccc2` | `6ae1bbec-f8f2-432b-a09f-9d9c8833944b` / `f2333b72-fcf7-4437-943f-4765357fe20e` | 46 | `$11,983,654` / `$11,983,654` | `budget-1.3.0+rules.eaef9e583fc5` |

The current imported parser constant equals every stored parser version. Read-only spot checks also show the remediated semantics: F#K's `7901 FINANCE FEE : 12.5%` is preserved exactly once at `$453,583` as `finance_costs`; its bare bond is `completion_bond`; Bad Hombres' unnumbered `$94,382` contingency survives downstream; production sound is distinct from post sound; legal/accounting, producer/director, payroll/fringes, film/lab/dailies, and titles use their repaired categories; and both Lips Like Sugar `4900` rows remain separately present and correctly classified.

That is strong evidence that the remediation is present, but it is not a current independent acceptance certificate. After the failed Codex audit, parser/ingestion behavior changed again in later branch lineage, including material-incompleteness fail-closed and XLSX work (`5dcdc50`) and subsequent upload/dedup/free-text/FDX/failure-status repairs. The only complete post-remediation PASS artifact is the implementer's own report. Therefore the old independent audit does not certify current state, while the existence of the locked audit, remediation, gate, IDs, and current corpus means the acceptance is stale rather than missing.

## 6. Remaining acceptance sequence

Perform one independent, read-only/rollback-isolated ingestion acceptance after the Overview repair; do not ingest a fifth project and do not alter the shared database:

1. Lock the four project, BudgetDocument, and version IDs above and confirm 158/158 source monetary rows exactly once, including Little Utopia's source-authored `$2` aggregate discrepancy.
2. Reconcile source totals, account codes, descriptions, numeric/currency parsing, duplicate identities, subtotal/header handling, and format-specific parsing against the existing Codex line ledger.
3. Re-prove BPI-001 through BPI-009, specifically F#K's `$453,583` finance fee and source/off-budget separation, Bad Hombres contingency, F#K bond, legal/accounting, ATL, production/post sound, all fringe rows, and both distinct Lips Like Sugar `4900` rows.
4. Prove insurance and Travel & Living classifications, source-vs-downstream semantic separation, current parser-version identity, downstream availability, and exact conserved canonical sums.
5. In an isolated rollback/temp context only, rerun the committed four-budget integrity gate and focused parser/classifier tests, then verify current parse reproducibility/idempotence. Do not run the broad suite or persist a reparse.
6. Account explicitly for the later XLSX/FDX/upload/dedup/free-text changes and prove they did not regress the locked real PDF corpus.
7. Issue a new independent artifact that either promotes the gate to `CURRENT_VALID` or lists exact remaining failures. Current database presence or successful optimizer evaluation alone is not acceptance.

## 7. Closure condition

One implementation pass may repair OAD-001 and OAD-002 together. Final Globe/Workspace/Overview acceptance still requires the four-project browser matrix after that repair. Canonical ingestion acceptance remains a separate, bounded independent re-verification because its present classification is `STALE_REQUIRES_REVERIFICATION`; no new ingestion or jurisdiction research is required.

**CODEX_FINAL_DELTA_READY_FOR_ONE_REMEDIATION_PASS**
