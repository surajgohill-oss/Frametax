# Optimizer P0 Wiring Remediation

Repairs the exactly three P0 defects Codex's independent optimizer wiring/capability audit found blocking `NO_GO_FOR_OPTIMIZER_BEHAVIORAL_ACCEPTANCE` — see [`OPTIMIZER_WIRING_CAPABILITY_AUDIT_CODEX.md`](OPTIMIZER_WIRING_CAPABILITY_AUDIT_CODEX.md) (Codex audit commit `dcc6dde0a5ef4576ccf6da1582458f5d1354fb41`) and [`OPTIMIZER_STRUCTURE_CAPABILITY_MATRIX_CODEX.csv`](OPTIMIZER_STRUCTURE_CAPABILITY_MATRIX_CODEX.csv). No missing structure family (non-treaty splits, majority/minority/multi-party co-production, service-production, grants/funds, hybrid, reinvestment, in-kind) was implemented — those remain explicitly `NOT_IMPLEMENTED`, per the audit's own required boundary.

## 1. Scope

Exactly three P0 defects, root-caused and fixed:

1. **P0-1 — Canonical selection divergence**
2. **P0-2 — Component participant contamination**
3. **P0-3 — Treaty conditional budget double-counting**

Accepted baselines (non-Globe canonical core, Canonical Budget Parser, AG global research, permission process) were not reopened. Globe, MFNI integration, grants/funds implementation, and SA-2 were not touched.

## 2. Codex P0 inventory

| ID | File(s)/function(s) | Real-project evidence |
|---|---|---|
| P0-1 | `canonical_evaluation.py::_summarize_evaluation`; `canonical_production_view.py::build_production_and_structures`; `globeData.js::activeStructure`; `bestPricedCandidate.js` | LU/FVD: `leading_structure_id=null`, `comparable_count=0`, yet canonical selection was each production's own Saudi `PRICED_LOW_FIT` full-relocation candidate |
| P0-2 | `canonical_production_view.py::_empty_structure_entry` | LU component `8172eb82-c2cc-4816-a331-beffddab5199`: served participants `['MU','CA-MB','US']`, real economic participants `['MU','CA-MB']` — all 134 current LU component candidates affected |
| P0-3 | `canonical_evaluation.py::_build_conditional_bilateral_scenario`; `canonical_treaty_bridge.solve_bilateral_minimum_contribution`; `_price_candidate` | LU GB/IE: gross $4,364,393; 20%/20% minimums; combined QPE priced at $8,126,528 (186.2% of gross) while `fully_priced=true` |

## 3. P0-1 root cause

`canonical_evaluation.py::_summarize_evaluation` correctly returns no `top_result` and clears `Project.leading_structure_id` when no candidate is both `is_directly_comparable` and qualification-admits-Recommended. `canonical_production_view.py`'s own `canonical_selected_structure_id` field (added in the prior non-Globe closeout pass) independently fell back, in that exact state, to **the lowest-NPC structure among ALL `is_fully_priced` structures** — including non-comparable `PRICED_LOW_FIT` candidates. This directly contradicted the evaluator's own deliberate "no winner" state and let a candidate the evaluator never selected become served project truth. The frontend (`bestPricedCandidate.js`) additionally re-implemented the SAME defective fallback client-side, so fixing only the backend would not have closed the gap.

## 4. P0-1 fix

`canonical_production_view.py`: `canonical_selected_structure_id = comparable[0]["structure_id"] if comparable else None` — the non-comparable fallback is removed entirely. `comparable` already applies the exact same two gates (`is_directly_comparable` and qualification-admits-Recommended) `_summarize_evaluation` uses, so this is not a second ranking system — it reads the evaluator's own accepted semantics.

`bestPricedCandidate.js`: fixed to check the field's **presence** (a real server key, even when `null`) rather than its truthiness — a present-but-`null` field now correctly propagates as "no selection," instead of falling through to the client's own defensive reduce() (which still implemented the dangerous lowest-NPC-among-all-priced logic). `globeData.js::activeStructure`'s own fallback (`ranking.find(r => r.rank === 1)`) was audited and found already safe — rank is only ever assigned to `comparable` entries, so it was already structurally equivalent to the corrected backend behavior.

## 5. P0-1 real-project evidence

**RUNTIME VERIFIED**, all four locked-corpus productions, current HEAD:

| Project | `leading_structure_id` | `top_result` | `canonical_selected_structure_id` | `comparable_count` |
|---|---|---|---|---:|
| Little Utopia | `MU` (base jurisdiction) | `None` | **`None`** (was Saudi `c57272cc-c0ac-4aa6-a3ea-4791372b98a9`) | 0 |
| F#K Valentine's Day | `GR` | `None` | **`None`** (was Saudi `ea7abc5c-cd3c-46d7-b838-93775b54da97`) | 0 |
| Bad Hombres | `US-NM` | `{'structure_id': 'c123cf6e-d7b4-4fb0-8fca-8c0061c0b230', ...}` | `c123cf6e-...` — **exact match**, unchanged | 1 |
| Lips Like Sugar | `US-CA` | `{'structure_id': '5a5934d5-748f-4f85-a98a-d015fcbfe505', ...}` | `5a5934d5-...` — **exact match**, unchanged | 1 |

Frontend (`npm test`): 169/169 passing after the `bestPricedCandidate.js` fix — no regression.

## 6. P0-2 root cause

`canonical_production_view.py::_empty_structure_entry`, for `component_relocation` structures, appended **every** `segments[].jurisdiction_code` to the canonical `participants` list unconditionally — including a segment with no `program_slug` at all (a stated-location fact: spend is physically located there, but no incentive is claimed). The codebase already carries the exact structural signal for this distinction — `allocation_pricing.py::SegmentEconomics.claims_incentive` (`False` exactly when `program_slug is None`) — but it was never consulted here.

## 7. P0-2 fix

The `component_relocation` participant loop now includes a segment's jurisdiction only when `seg.get("claims_incentive") is True`. The non-claiming segment's full geography remains visible in `trace["segments"]` — never deleted, only excluded from the canonical PARTICIPANT list. Generic: no jurisdiction code, project ID, or structure ID is referenced in the fix itself.

## 8. P0-2 real-project evidence

**RUNTIME VERIFIED.** LU structure `8172eb82-c2cc-4816-a331-beffddab5199`: `participants` now `['MU', 'CA-MB']` (was `['MU', 'CA-MB', 'US']`); its real `US` segment remains present in `trace.segments` with `claims_incentive=False, program_slug=None`. FVD structure `adcbeb4f-42f9-44fa-8118-854dcb86896c` (Greece anchor + Romania post): `['GR', 'RO']`, both segments `claims_incentive=True`.

**Full-corpus sweep** (every `component_relocation` structure, all four locked productions, `participants == {primary} ∪ {claims_incentive=True segments}` checked exactly):

| Project | Component structures | Mismatches |
|---|---:|---:|
| Little Utopia | 134 | **0** |
| F#K Valentine's Day | 206 | **0** |
| Bad Hombres | 135 | **0** |
| Lips Like Sugar | 232 | **0** |

**Cross-project regression** (structure types outside the fix's scope, unaffected): `single_country` structures still serve `[primary]` alone (LU: `['MU']`, FVD: `['GR']`); `treaty_coproduction` structures still serve their full real party list (LU GB/IE: `['GB','IE']`; FVD Eurimages: 11 real members) — byte-identical to before.

## 9. P0-3 root cause

`canonical_evaluation.py::_price_candidate` — the SAME kernel single/full-relocation candidates use — was called **once per treaty participant** with the **unscaled, full** `inputs.budget_lines`. Each call built a `StructureSpec` treating that ONE jurisdiction as if it received the **entire** production budget (`participants=(jurisdiction_code,)`, full `derive_account_allocation` over the whole budget). `solve_bilateral_minimum_contribution`'s own real treaty thresholds (e.g. GB/IE 20%/20%, summing to only 40%) were used only for **eligibility**, never for actually **allocating** the budget before pricing — so both participants were priced against 100% of the same dollars independently.

## 10. P0-3 fix

`_build_conditional_bilateral_scenario` now constructs a real, conserved allocation before pricing:

- **Minority** takes exactly its treaty-recorded minimum contribution (no fact justifies more).
- **Majority** takes the arithmetic **complement** (`1 − minority_pct`) — the definitionally-correct remaining share, not a second invented number.
- **Feasibility check**: if the majority's complement share would fall below the majority's *own* recorded minimum, no allocation can be constructed from known facts — the scenario fails closed (`fully_priced=False`, `status="USER_DECISION_REQUIRED"`, explicit `blocking_reason`), exactly mirroring the existing `deterministically_solvable=False` pattern.
- Each participant is then priced (via the SAME `_price_candidate` kernel, unmodified) against a **scaled copy** of `inputs` (`dataclasses.replace`, every budget line multiplied by that participant's own allocated fraction) — never the full budget twice.
- The served scenario now discloses `participant_allocation_pct` explicitly, so the allocation is auditable, not merely correct-and-invisible.

`ENGINE_VERSION` bumped (`canonical-1.52.0` → `canonical-1.53.0`) — a pure code change with no fingerprint-input difference; without this, `evaluate_project`'s own existing-row reuse would have kept serving the old, double-counted `trace_json` forever.

## 11. P0-3 real-project evidence

**RUNTIME VERIFIED — primary case, LU GB/IE** (European Convention on Cinematographic Co-Production):

| | Before | After |
|---|---:|---:|
| Participant allocation | *(not modeled)* | `GB: 80.0%`, `IE: 20.0%` — sums to exactly 100.0% |
| GB priced program | `uk_avec`, full $4,364,393 budget | `uk_avec`, its own $3,491,514.40 (80%) allocated share |
| IE priced program | `ie_section_481`, full $4,364,393 budget | `ie_section_481`, its own $872,878.60 (20%) allocated share |
| Combined QPE | $8,126,528 (**186.2%** of gross) | verified via direct kernel call: **$4,063,264.00 (93.1%** of gross) |
| Combined incentive | $2,185,829.43 | **$970,257.91** |
| Conditional NPC | $2,178,563.57 | **$3,394,135.09** (= gross − incentive, reconciles exactly) |
| `fully_priced` | `true` (incorrectly) | `true` (correctly — allocation is complete, no data gaps) |

**Second real treaty pathway** (Lips Like Sugar, UK/Ireland bilateral, structure `d138d556-482e-43eb-821b-22e8e6cd91ed`, gross $11,983,654): allocation `GB: 80.0%, IE: 20.0%` (sums to 100.0%); GB `uk_avec` incentive $1,955,732.33; IE `ie_section_481` incentive $632,553.86; combined incentive $2,588,286.19; NPC $9,395,367.81 = gross − incentive exactly. No double-counting.

**Full-corpus sweep**, current `ENGINE_VERSION` rows only, all four locked productions: 21 (LU) + 20 (FVD) + 20 (Bad Hombres) + 21 (Lips Like Sugar) = **82 resolved conditional bilateral scenarios, 0 with a non-100%-summing allocation.**

**Genuine data-gap case preserved, not regressed**: FVD's Canada/Mexico bilateral (`d667ec31...`) still correctly reports `fully_priced=False` — not because of the P0-3 fix, but because `ca_cmf` genuinely has no canonical `RateRule` on file (`canonical_data_gaps=['ca_cmf']`), exactly as before. The gate's own new invariant (Section 13) explicitly distinguishes this real, unrelated disclosure from an actual allocation defect.

## 12. Regression tests

- **`test_canonical_selection_consistency.py`** — rewritten. Codex's own critique ("encodes the fallback instead of asserting evaluator/served-selection equivalence") addressed directly: asserts `None` (never a non-comparable fallback) when no comparable rank-1 exists, verified across all four locked productions; a dedicated test locks in the exact LU/FVD real-project regression case.
- **`test_canonical_scenario_participants.py`** — extended. Codex's own critique ("only requires at least two participants and misses exact identity") addressed with a new exact-identity check (`participants == {primary} ∪ claiming segments}`) across every LU/FVD component structure, plus the exact named LU regression structure (`8172eb82...`), plus a cross-check that single-country/treaty participant construction is untouched.
- **`test_copro_conditional_pricing_bridge.py`** — extended. Codex's own critique ("checks positive arithmetic but not allocation/share conservation") addressed with: a synthetic conservation proof (allocation sums to exactly 100%, no participant's incentive can exceed its own allocated share, combined incentive stays well under the one real budget); an infeasible-split-fails-closed test; and a real-project control assertion against LU's own GB/IE data.
- All new/updated tests use real persisted project IDs where the acceptance criteria require real-project proof (per this suite's own established convention); synthetic fixtures are used only where genericity itself is the property under test (per governing spec precedent already established in this test file).

## 13. Canonical gate results

**Canonical Budget Integrity Gate** (unaffected by this task — no budget classification code touched): re-run as a regression check.

```
CANONICAL BUDGET INTEGRITY GATE: PASS — all four locked-corpus budgets, all 16 invariant families
```

**Non-Globe Canonical Integrity Gate**: the pre-existing `SELECTION` invariant itself encoded the P0-1 defect as expected behavior — fixed to match the corrected semantics. The pre-existing `PARTICIPANTS` invariant only checked a count floor for `component_relocation` — strengthened to exact claiming-participant-set identity (mirroring the new regression tests). A new, narrow **`TREATY ALLOCATION`** invariant family was added (Codex's own instruction: "If the existing gate does not detect one of these P0 classes, add the narrowest appropriate permanent invariant") — asserts a resolved conditional bilateral scenario's `participant_allocation_pct` sums to exactly 100%, `fully_priced` is true only when that allocation is complete AND no real `canonical_data_gaps` exist, and combined incentive never implausibly exceeds the gross budget.

Re-run across all 50 discovered library records:

```
Projects evaluated: 14 PASS, 0 FAIL, 36 SKIP (no budget on file yet — a real state, not a gate failure)

  PASS   BUDGET — 14 project(s) checked, 0 failure(s)
  PASS   ELIGIBILITY — 14 project(s) checked, 0 failure(s)
  PASS   QPE — 14 project(s) checked, 0 failure(s)
  PASS   INCENTIVE — 14 project(s) checked, 0 failure(s)
  PASS   NPC TRACE — 14 project(s) checked, 0 failure(s)
  PASS   PARTICIPANTS — 14 project(s) checked, 0 failure(s)
  PASS   SCENARIO IDENTITY — 14 project(s) checked, 0 failure(s)
  PASS   STATUS — 14 project(s) checked, 0 failure(s)
  PASS   PROGRAM CERTAINTY — 14 project(s) checked, 0 failure(s)
  PASS   PROJECT MODELING POLICY — 14 project(s) checked, 0 failure(s)
  PASS   SELECTION — 14 project(s) checked, 0 failure(s)
  PASS   PROGRAM ONBOARDING — 14 project(s) checked, 0 failure(s)
  PASS   TREATY ALLOCATION — 14 project(s) checked, 0 failure(s)

CANONICAL INTEGRITY GATE (13 non-Globe invariants): PASS — GLOBE remains separately DEFERRED BY SEQUENCING
```

(Note: the gate discovers 14 productions with real optimizer structures — one more than the 13 from the prior closeout pass, incidental to this task and not investigated further, consistent with this task's exact-three-P0 scope lock.)

## 14. Full suite

Result recorded after this document was drafted — see the chat response for the exact final count (`pytest tests/ -q`, run once, per the required efficiency model).

## 15. Files changed

**Source (2):**
- `frametax2/backend/app/services/canonical_evaluation.py` — P0-3 (allocation-conserving treaty pricing, `ENGINE_VERSION` bump).
- `frametax2/backend/app/services/canonical_production_view.py` — P0-1 (canonical selection fix), P0-2 (participant claiming-identity fix).

**Frontend (1):**
- `frametax2/frontend/src/lib/bestPricedCandidate.js` — P0-1 (presence-check fix for the served `null`).

**Gate (1):**
- `frametax2/backend/scripts/canonical_integrity_gate.py` — SELECTION invariant corrected; PARTICIPANTS invariant strengthened to exact identity; new TREATY ALLOCATION invariant family added.

**Tests (3):**
- `frametax2/backend/tests/test_canonical_selection_consistency.py` — rewritten for corrected P0-1 semantics.
- `frametax2/backend/tests/test_canonical_scenario_participants.py` — extended for exact P0-2 identity; import-order fix (Codex P2 finding) applied.
- `frametax2/backend/tests/test_copro_conditional_pricing_bridge.py` — extended with P0-3 conservation/infeasibility/real-project tests.

**Docs (1):** this file.

## 16. Permission / process note

Permission preflight was re-run at the start of this task per explicit instruction, surfacing one real, unresolved gap: writes to `/tmp`/`/private/tmp` still prompt despite the correctly-configured `.claude/settings.local.json` rule, traced to a Desktop-app-level workspace sandbox outside that file's control. Resolved by switching to an in-repo, gitignored scratch directory (`~/cineglobe-frametax/.claude/scratch/`) for the remainder of this task — verified clean (no dialogs) before proceeding. No further routine permission interruption occurred during the optimizer P0 implementation itself. Diagnostic investigation used a stable, repeated `python3 -c "..."` invocation shape throughout (not varied per question), consistent with the standing command-family discipline.

## 17. Commit / push / remote

See the chat response for the final commit SHA, push confirmation, and remote HEAD verification.
