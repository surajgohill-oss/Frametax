# Codex Final Globe / Workspace / Overview / Ingestion Acceptance

Date: 2026-09-26

Mode: independent read-only acceptance

Final delta verification: 2026-09-29 at `8304c70ec5d8c83f71405e3b82422e9f68f770b7`

Verdict: **CINEGLOBE_GLOBE_WORKSPACE_OVERVIEW_INGESTION_ACCEPTED**

The bounded Overview repair is correct, the locked four-budget ingestion gate is current-valid, and the last independently reproduced cross-surface contradiction is closed. Commit `8304c70e` removes Workspace's gross-normalization override and consumes the shared `qpeOf()` adapter. Little Utopia now renders canonical QPE `$4,364,395` in both Lanes and Split while preserving gross budget `$4,364,393`; Overview, Workspace cards, Inspector, component allocations, and the local API agree.

## 1. Starting and remote-integrity gate

| Check | Evidence | Result |
|---|---|---|
| Repository | `surajgohill-oss/Frametax`; git root `/Users/Suraj/cineglobe-claude-global-optimizer-remediation` | PASS |
| Branch / required start | `claude/global-optimizer-remediation`; local and `origin` both `3efedfd8ab3bd49f9999025231561711357aa153` | PASS |
| Worktree | Only permitted untracked `.backend_gd_wire.log` and `.frontend_gd_wire.log` | PASS |
| Remediation commit scope | Exactly the three frontend implementation files and two focused tests specified by the acceptance prompt | PASS |
| Local/remote blobs | All five remediation blobs identical | PASS |
| Forbidden scope | No backend, database, optimizer, parser, rule, or unrelated UI file in the remediation commit | PASS |
| Runtime | One Vite service on `localhost:5173`; one uvicorn service (supervisor/worker for one bound service) on `127.0.0.1:8010` | PASS |
| Database / organization | `frametax2_claude_optimizer_acceptance_20260919`; `11381771-5b1c-4980-9117-e3e47a4cb354` / Mind The Story Media | PASS |

## 2. Remediation diff and static adapter verification

Commit `3efedfd8` implements the required bounded repair:

- `productionOptions.js:qpeOf()` uses non-empty `segments[].qpe_usd`; otherwise `component_allocations[].allocated_usd`; otherwise zero. It never adds both representations and never substitutes gross, incentive, NPC, project, or jurisdiction values.
- `productionOptions.js:resolveGrossBudget()` uses `structure.gross_budget_usd ?? production.gross_budget_usd ?? null` and derives nothing from QPE, allocations, incentive, or NPC.
- `IncentiveIntelligence.jsx` consumes both helpers, and `Overview.jsx` passes the production gross as the fallback.
- The five-file diff does not touch generation, ranking, ordering, counts, identities, incentive/NPC/savings calculations, thresholds, warnings, conditional funds, Globe, or Workspace.

Classification:

| Repair | Four-project result |
|---|---|
| OAD-001 — Overview optimized QPE | PASS |
| OAD-002 — Overview optimized gross budget | PASS |

## 3. Focused test review

Frontend command: the four explicitly authorized files only. Result: **52 passed, 0 failed**.

The tests contain literal, independent expectations for populated segments, allocation fallback, segments winning when both exist, neither representation, no double counting, structure-gross precedence, production-gross fallback, and both-gross-values absent. The four-project expected values are literals rather than calls back into the production helper.

Parser/classifier command: five focused, non-database test files covering classification, text/PDF extraction, XLSX isolation, FDX extraction isolation, and Movie Magic top-sheet parsing. Result: **80 passed, 0 failed**. No broad frontend or backend suite ran.

## 4. Four-project identity lock and Overview values

| Project | Structure / economic identity | Overview gross / QPE / incentive / NPC / savings | Result |
|---|---|---|---|
| The Little Utopia | `559a49ce-6581-4e78-ad8a-733f424e0b74` / `89f543279d132bcea03c6ce44cde857af6c5a31fdf369938392b36e469bbea05` | `$4,364,393` / `$4,364,395` / `$1,825,390.40` / `$2,539,002.60` / `$1,252,330.70` | PASS |
| Bad Hombres | `da3b394b-152f-4637-a238-a9dcfa9e5eb2` / `bb142bd7a3805991ef3c6f1b0a480ca3aa5fc85d070f43de83a3bb70d24fa5a0` | `$2,482,023` / `$2,482,023` / `$1,068,790.55` / `$1,413,232.45` / `$471,880.30` | PASS |
| F#K Valentine's Day | `dbcf5bda-a4af-4a70-a968-e4e6b19b0ce4` / `f8bced42ee725ccf7daf4196b7bbaea53b4b111f5b30513a267e2f77440ed69a` | `$4,517,687` / `$4,517,687` / `$1,664,547.10` / `$2,853,139.90` / `$218,887.26` | PASS |
| Lips Like Sugar | `601a8a8f-d1b0-42f1-8aef-5934e0422502` / `1e6c80a564510dde3c2fea3cd99b21a5625c63c1ffcb6cb6d5cc3ef6bdd71d02` | `$11,983,654` / `$11,983,654` / `$4,435,305.60` / `$7,548,348.40` / `$976,026.70` | PASS |

Overview card clicks opened the same identities in Inspector with the same participants, three-program stack, component routes, incentive, NPC, savings, and warnings. Anchor and Leading cards remained in their canonical order.

## 5. Cross-surface acceptance matrix

Canonical backend source for every row is `GET /api/v1/cineglobe/projects/{project_id}/state`, served from current canonical production state. The Browser used the local Vite application, not a mock or remote preview.

| Surface | Project | Exact structure / identity | Rendered behavior and independent evidence | Result |
|---|---|---|---|---|
| Overview | Little Utopia | `559a49ce…` / `89f54327…` | Exact five required values; exact route MB `$4,302,827`, NL post `$9,068`, Italy VFX `$52,500` | PASS |
| Overview | Bad Hombres | `da3b394b…` / `bb142bd7…` | Exact five required values; exact route MB `$2,369,065`, NL music `$5,000`, Italy post `$107,958` | PASS |
| Overview | FVD | `dbcf5bda…` / `f8bced42…` | Exact five required values; exact route MB `$4,497,487`, NL music `$10,200`, Italy VFX `$10,000` | PASS |
| Overview | Lips Like Sugar | `601a8a8f…` / `1e6c80a5…` | Exact five required values; exact route MB `$11,736,880`, NL music `$206,774`, Italy VFX `$40,000` | PASS |
| Workspace Lanes card | Little Utopia | `559a49ce…` / `89f54327…` | Card and Inspector show QPE `$4,364,395`; gross remains `$4,364,393` | PASS |
| Workspace Lanes card | Bad Hombres | `da3b394b…` / `bb142bd7…` | Gross/QPE/incentive/NPC/savings and route agree | PASS |
| Workspace Lanes card | FVD | `dbcf5bda…` / `f8bced42…` | Gross/QPE/incentive/NPC/savings and route agree | PASS |
| Workspace Lanes card | Lips Like Sugar | `601a8a8f…` / `1e6c80a5…` | Gross/QPE/incentive/NPC/savings and route agree | PASS |
| Workspace Inspector | All four | Locked identities above | Exact identities, participants, program stack, component routes, incentive, QPE, NPC, savings | PASS |
| Workspace Map | All four | Locked structures above | Optimizer mode retained; canonical participant markers/routes rendered. Existing accepted Map interaction evidence reused because the remediation did not touch Globe/Workspace owners. | PASS (regression) |
| Workspace Split | All four | Locked structures above | Exact optimizer cards, route, Map, mode/selection retained; Little Utopia preserves QPE `$4,364,395` distinct from gross `$4,364,393` | PASS |
| Full Project Globe | All four | Locked structures above | Direct local traversal switched Normal to Optimizer; exact optimized route label, NPC/savings, and CA-MB/CA-NL/IT markers rendered | PASS |
| Globe hover | All four | Locked structures above | Prior independent direct-hover matrix in `CODEX_FINAL_GLOBE_WORKSPACE_ACCEPTANCE.md`; renderer/hover owners are outside the five-file remediation diff, and the current Globe regression retained exact structure/route/markers | PASS (frozen evidence + regression) |
| Normal/Optimizer and Lanes/Map/Split controls | All four | N/A | Direct local interactions succeeded; state did not leak across navigations | PASS |
| Conditional opportunities | All four | N/A | Needs-more-facts opportunities remain separate and do not fabricate guaranteed values | PASS |

### Network and console

- Current browser console: zero errors or warnings attributable to the flow.
- Backend log: every observed canonical project-state request for all four project IDs returned `200 OK`; no failed canonical API request occurred during the run.
- Rendered data came from `127.0.0.1:8010`; no mock/demo payload was used.

## 6. Resolved final defect

### GW-OI-001 — Workspace silently normalized canonical QPE to gross budget — RESOLVED

**Evidence**

For Little Utopia structure `559a49ce…`:

- local canonical API `component_allocations[].allocated_usd`: `$4,302,827 + $9,068 + $52,500 = $4,364,395`;
- Overview Optimized Qualified Spend: `$4,364,395`;
- Workspace Inspector Total QPE: `$4,364,395`;
- Workspace Lanes/Split card Qualified spend: `$4,364,393`.

**Root cause**

In the pre-fix code, `frametax2/frontend/src/screens/production/Workspace.jsx:138-147` correctly summed the component allocations, then passed the result through `normalizeTrivialVariance(qualifiedSpendRaw, gross)`. `frametax2/frontend/src/lib/format.jsx:80-82` replaces any value within `$5` of the reference with the reference. Little Utopia's source-authored `$2` leaf-sum variance therefore became the gross budget only on Workspace cards. That was a duplicate display calculation and directly violated the zero-cross-surface-contradiction and no-alternate-QPE-calculation acceptance conditions.

**Implemented repair and independent delta verification**

- Commit `8304c70ec5d8c83f71405e3b82422e9f68f770b7` changes only `Workspace.jsx` and the new focused regression test.
- `Workspace.jsx:ScenarioCard` now consumes the shared canonical representation adapter `qpeOf(structure)` and does not normalize QPE to gross.
- Independent focused tests: 57 passed, 0 failed, including the literal Little Utopia gross/QPE distinction and all four projects' QPE values.
- Independent local browser: Little Utopia Lanes and Split both show gross `$4,364,393`, QPE `$4,364,395`, incentive `$1,825,390`, NPC `$2,539,003`, and savings `$1,252,331`.
- Independent Inspector: identity `89f543279d132bce…`, QPE `$4,364,395`, and component QPE `$4,302,827 + $9,068 + $52,500` agree exactly.
- Bad Hombres, FVD, and Lips Like Sugar remain `$2,482,023`, `$4,517,687`, and `$11,983,654` respectively in live Workspace Optimizer cards.
- No browser console errors or warnings; all observed canonical state requests returned `200 OK`.
- No backend, database, optimizer, parser, or economic calculation changed.

## 7. Current ingestion/parser acceptance gate

Classification: **CURRENT_VALID**

The repository gate script was inspected but not executed against the shared database because it calls `ensure_current_budget_routed()` twice per project and is therefore write-capable if a version mismatch exists. Its assertions were independently reproduced with direct SQL inside `BEGIN READ ONLY` and with `build_project_economic_inputs(..., read_only=True)` inside a database-enforced read-only transaction.

| Requirement | Independent evidence | Result |
|---|---|---|
| Locked identities | Exact four project, BudgetDocument, and DocumentVersion IDs | PASS |
| 158 lines once each | 44 + 34 + 34 + 46; unique primary keys and source rows | PASS |
| Totals / sums | Exact totals; LU leaf sum preserves the authored `$2` excess | PASS |
| Ledger preservation | Live-vs-locked multiset over project/document/description/amount: 0 missing, 0 extra; every recorded account-code prefix retained | PASS |
| Descriptions / amounts | Zero blank descriptions; zero null amounts; signs, decimals, USD currency retained | PASS |
| Header/subtotal duplication | Exact 158-ledger identity plus focused subtotal/rebate exclusion tests | PASS |
| FVD finance fee | Exactly one `7901 FINANCE FEE  : 12.5%`, `$453,583`, `finance_costs` | PASS |
| Source vs scenario finance | Downstream `source_budget_finance_usd=$453,583`; `financing_cost_usd=null` | PASS |
| BH contingency | Exactly one `$94,382` unnumbered line, downstream `contingency` | PASS |
| Bond / insurance | All bond rows `completion_bond`; all insurance rows `insurance` | PASS |
| Legal/accounting | All positive legal rows `legal_accounting` | PASS |
| ATL roles | Producer/director fixtures correct; art direction not misclassified | PASS |
| Payroll/fringes | All explicit fringe rows `payroll_fringes`; LLS total `$1,346,714` | PASS |
| Sound | Production sound `production_sound`; post sound `sound` | PASS |
| Film/lab/titles | Film/lab/dailies and title fixtures `post_production` | PASS |
| LLS duplicate 4900 | `$1,023,115` fringes and `$10,500` main/end titles both survive independently | PASS |
| Travel & Living | Aggregate source rows retained and classified `travel`/`lodging`; top-sheet aggregation limitation remains disclosed | PASS |
| Source/downstream separation | Persisted source rows unchanged; canonical read-only builder adapts them without mutation | PASS |
| Downstream availability | Builder returns all 44/34/34/46 lines, exact totals, and zero unparsed lines | PASS |
| Parser version | All four store current `budget-1.3.0+rules.eaef9e583fc5` | PASS |
| Later format-path regression | Locked PDF multiset remains byte-for-value identical; focused PDF/text/XLSX/FDX/Movie Magic tests 80/80 | PASS |

## 8. Ownership and final verdict

Overview, Workspace, Inspector, and Globe all read the canonical served project state. The final remediation removes Workspace's second QPE presentation rule and reuses the shared `qpeOf()` adapter. It does not create a second economic engine or alter backend economics. The required zero duplicate display-calculation and zero cross-surface-contradiction gates are met.

- OAD-001: PASS
- OAD-002: PASS
- Ingestion gate: CURRENT_VALID
- Remaining defects: 0
- Final token: **CINEGLOBE_GLOBE_WORKSPACE_OVERVIEW_INGESTION_ACCEPTED**
