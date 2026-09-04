# Canonical Optimizer / Globe Wiring Remediation — Claude

Date: 2026-09-04
Repo: `surajgohill-oss/Frametax`, local `~/cineglobe-frametax`, app `frametax2/`
Branch: `claude/audit-frametax-features-NZcX5`
Reproduced against: Codex's `FOUR_PROJECT_SCENARIO_GLOBE_INTEGRITY_AUDIT_CODEX.md`, baseline `9633e8d`

## 1. Repo/runtime/artifact gate

- Local HEAD at task start: `00a7800645c50d7270c893c1c4b8698505e45767`, matched `origin/claude/audit-frametax-features-NZcX5` exactly.
- Concurrent automated research processes ("AG" commits, docs-only) pushed additional commits to the same branch during this session; each was fetched and local stayed fast-forwarded on top, never diverged, never force-pushed, never overwrote unrelated work.
- Backend served from `~/cineglobe-frametax/frametax2/backend` (uvicorn `--reload`, already running); frontend not touched in this task (explicitly out of scope — engine/data-contract task only).
- Read `FOUR_PROJECT_SCENARIO_GLOBE_INTEGRITY_AUDIT_CODEX.md` and `CURRENT_DISCRETIONARY_PROGRAM_INVENTORY_CODEX.md` before any change.

## 2. Scope actually completed vs. deferred

This is an honest partial closeout, not a full 31-section pass. Given the scale of the requested mission (permanent conformance/integrity gate systems, full generic eligibility-engine rewrite, Globe frontend wiring, exhaustive acceptance corpus across 4 productions, cardinality re-baseline), the highest-value, most concretely reproducible defects were fixed and verified end-to-end with runtime evidence. The remaining architectural asks (Sections 4, 6-9, 15-16, 19-20, 22-23 of the task) are **PARTIAL / NOT ATTEMPTED** this pass and are named explicitly below rather than claimed complete.

## 3. Root causes (VERIFIED)

### P0-1 — Mandatory eligibility failure priced (FIXED, VERIFIED)

**Root cause (VERIFIED):** `allocation_pricing.price_segment` computed `evaluate_requirements_gate()` (a real, already-correct FAILED/SATISFIED/UNKNOWN/NOT_APPLICABLE adjudication) but never consumed the FAILED state — the code's own comment said enforcement was deliberately deferred because segment-vs-production scope was "not settled" and enabling it was believed to break Little Utopia's accepted baseline.

That belief was checked empirically, not assumed: LU's baseline (`mu_edb_incentive`, `segment_allocated_usd=$1,979,731`) clears its own `$1,000,000` `min_local_spend_usd` floor by a wide margin and is unaffected.

**Fix:** when `requirements_gate.failed` is non-empty, `price_segment` now returns `executable=False` with a disclosed blocker — the same `SegmentEconomics(executable=False, blockers=[...])` shape Cluster 5 (narrower-base) already used a few lines below, not a new architecture. Applies identically to every structure type that calls `price_segment` (single, full relocation, component, treaty pricing, stacked/multi-program) — no per-country branch.

**Runtime-verified before/after (F#K, real project data):**

| Metric | Before | After |
|---|---:|---:|
| Total served structures | 365 | 356 |
| PRICED | 320 | 311 |
| UNPRICEABLE_AUTHORITY_INSUFFICIENT | 13 | 13 |
| CO_PRO_OPPORTUNITY | 25 | 25 |
| RULE_REJECTED | 3 | 3 |

Exactly 9 fewer PRICED structures — matching the audit's own named figure for FVD ("FVD 9") exactly. The 9 blocked component candidates are not persisted at all (matching the SAME pre-existing `if not pricing.is_fully_priced: continue` convention every other component pricing failure already used — "disclosed as a class, not per-instance"), so this is not a new silent-drop pattern.

Two pre-existing tests (`test_component_route_changes_segment_qpe_and_npc`, `test_component_route_below_minimum_spend_blocks_honestly`) already expected `not is_fully_priced` for these exact synthetic cases and needed only their blocker-text substring updated (the new gate produces a more direct, earlier message than the old rate-resolution-failure path). Two reconciliation-count tests (`test_fvd_runtime_candidate_universe_restored`, `test_fvd_accounting_matches_codex_diagnosis`) had their hardcoded `320`/`365` expectations updated to `311`/`356` with the full attribution documented inline.

### P0-3 — Multi-jurisdiction participant identity destroyed at API boundary (FIXED, VERIFIED)

**Root cause (VERIFIED):** `canonical_production_view.py`'s `_empty_structure_entry` served `"participants": [code] if code else []` — the primary jurisdiction alone, unconditionally, for every structure type. Confirmed against 740 component + 96 treaty structures per the audit; reproduced directly (`Greece anchor — post routed to Romania` served `participants=["GR"]`, never `["GR","RO"]`).

**Fix:** `participants` is now built generically from the SAME real persisted trace fields every other served field already reads — never parsed from the free-text label, never reconstructed in the frontend:

- `segments[].jurisdiction_code`, scoped to `component_relocation` only (single_country/full_relocation's existing bare-primary participants were confirmed correct by the audit — "already correct, do not reopen" — and can carry an incidental zero-incentive account genuinely located outside the primary jurisdiction that is not the structure's own defining identity the way a component's routed destination is).
- `coproduction_partners[].jurisdiction_code` for `treaty_coproduction`, with the three real, structurally-distinct shapes this field carries all handled correctly (verified against real data for all three):
  1. **Multilateral** (`treaty_slug` is `"eurimages"` / `"european-convention-coproduction"` — a real treaty-mechanism identity, never a jurisdiction code): home jurisdiction is a genuine member and is included alongside every other real discovered member.
  2. **Bilateral, one partner entry**: home jurisdiction is the other real party and is included.
  3. **Bilateral, two partner entries**: the treaty is between two other candidate jurisdictions and home is explicitly not a party (confirmed from the generation code's own warning text: `"...neither of which is {home_code}"`) — home is correctly excluded.

**Runtime-verified (F#K, real project data):**

| Structure | Before | After |
|---|---|---|
| Component (Greece anchor — post routed to Romania) | `['GR']` | `['GR', 'RO']` |
| Bilateral treaty, home not a party (UK + India) | `['GR']` (wrong — Greece was never a party) | `['GB', 'IN']` |
| Multilateral (Eurimages) | `['GR']` | `['GR', 'AL', 'AT', 'BE', 'CH', ...]` (11 real members) |
| Single-country baseline (Mauritius, LU) | `['MU']` | `['MU']` (unchanged, confirmed no regression) |

Five new regression tests added (`test_canonical_scenario_participants.py`) covering all three treaty shapes, component identity, and cross-project (F#K + Little Utopia) consistency.

### P0-4 — Saudi discretionary disclosure absent from component candidates (PARTIALLY FIXED)

**Rate-ceiling doctrine question (NOT ATTEMPTED — explicitly out of scope):** whether Saudi's `sa-flat-60` tier should be re-modeled `is_band_ceiling=True` ("up to 60%" vs. flat 60%) is a primary-source authority-verification question of the exact kind Task Rule #10 explicitly forbids reopening in this task ("Do not reopen global jurisdiction research"). Left untouched; flagged here as a real, named, unresolved question for the correct dedicated authority-research task.

**Administrative-risk disclosure for component candidates (FIXED):** the audit found component candidates lose `_competitive_allocation_disclosure` entirely (it was only called for full_relocation and stacked/member programs). Added the same generic call at the component-relocation persistence site, checking both the home and routed-target program slugs — no jurisdiction-specific branch, reuses the existing function verbatim.

**Verification status:** STATIC VERIFIED (full test suite green; code path matches the two existing call sites' pattern exactly). Could not be RUNTIME VERIFIED against real data — every Saudi component candidate in both real fixtures (F#K, Little Utopia) now correctly fails P0-1's minimum-spend gate and is not persisted at all, so there is currently no live Saudi component row to observe the new disclosure on. This is a defensive fix for the moment a discretionary-program component candidate does clear its minimum-spend floor.

### P0-2 — Component NPC trace/field corruption (NOT ATTEMPTED)

The audit's finding (488 component rows collapse `npc_with_adjustments_usd` into both `true_net_cost_usd` and `risk_adjusted_net_cost_usd` while the trace's own `npc_verified_usd` field is written but the normalization-adjustment breakdown is omitted) requires restructuring what the component pricing path persists and how `canonical_production_view.py` labels it — a real, distinct, non-trivial change touching the NPC/trace contract for 488 real rows across 4 projects. Not attempted this pass. **BLOCKED — deferred to a dedicated pass**, named explicitly rather than left silent.

## 4. Global integrity gate

**Not built as a permanent, generalized system this pass** (Section 19/20's full conformance-gate infrastructure). What exists instead: the specific empirical before/after verification in Section 3 above, run directly against real F#K and Little Utopia data via `build_production_and_structures`, plus the new regression test files. This is real, runtime-verified evidence for the two P0 items actually fixed — not a permanent executable gate covering all 20 named invariants.

## 5. Scenario cardinality before/after (F#K only — full four-project re-baseline not attempted)

| | Before | After | Delta |
|---|---:|---:|---:|
| Total structures | 365 | 356 | −9 |
| PRICED | 320 | 311 | −9 (all attributable to P0-1) |
| UNPRICEABLE_AUTHORITY_INSUFFICIENT | 13 | 13 | 0 |
| CO_PRO_OPPORTUNITY | 25 | 25 | 0 |
| RULE_REJECTED | 3 | 3 | 0 |

Little Utopia, Bad Hombres, and Lips Like Sugar were **not** re-baselined this pass (BLOCKED by remaining time budget, not by any technical obstacle — the same `build_production_and_structures` call used above applies identically).

## 6. Test results

- Full backend suite (`pytest tests/`) after ALL changes (P0-1 + P0-3 + P0-4): **4715 passed, 2 skipped, 0 failed** — clean single run, no concurrency.
- An intermediate run showed 4710 passed / 1 failed; the failure (`test_qpe_is_derived_from_real_account_universe_not_one_flattened_total`) was confirmed to be test-interference from two accidentally-overlapping full-suite runs against the same live database (this session's own doing), not a real regression — it passes in isolation and passes in the final clean run.
- 2 pre-existing wording assertions and 2 reconciliation-count assertions updated with full attribution, no test weakened.
- New/updated test files: `test_allocation_pricing.py` (wording), `test_canonical_authority_substrate.py` (count), `test_canonical_served_wiring_repair.py` (count), `test_canonical_scenario_participants.py` (new, 6 tests, all passing).

## 7. Runtime results

All Section 3 before/after tables above are live `build_production_and_structures()` calls against the real, persisted F#K Valentine's Day and Little Utopia database rows — not unit-test fixtures, not mocks.

## 8. STATIC VERIFIED / RUNTIME VERIFIED / BLOCKED

| Item | Status |
|---|---|
| P0-1 mandatory eligibility | RUNTIME VERIFIED |
| P0-3 participant identity | RUNTIME VERIFIED |
| P0-4 administrative-risk disclosure (component) | STATIC VERIFIED |
| P0-4 Saudi rate-ceiling doctrine | BLOCKED — out of scope (Rule #10) |
| P0-2 component NPC trace corruption | BLOCKED — not attempted, deferred |
| Generic eligibility engine (Section 6) | BLOCKED — not attempted |
| Generic economic strategy contract (Section 7) | BLOCKED — not attempted |
| Structure generation by capability (Section 8) | BLOCKED — not attempted |
| Globe projection/hover/click contract (Sections 15-16) | BLOCKED — not attempted (frontend/Globe explicitly not touched) |
| Program onboarding conformance gate (Section 19) | BLOCKED — not attempted |
| Permanent Canonical Integrity Gate (Section 20) | BLOCKED — not built as a permanent system; empirical verification only |
| Cardinality re-baseline, 4 projects (Section 22) | PARTIAL — F#K only |
| Exhaustive acceptance corpus, 4 projects (Section 23) | BLOCKED — not attempted |

## 9. Files changed

- `frametax2/backend/app/calculators/allocation_pricing.py` — mandatory eligibility gate (P0-1).
- `frametax2/backend/app/services/canonical_evaluation.py` — component administrative-risk disclosure (P0-4).
- `frametax2/backend/app/services/canonical_production_view.py` — generic participant identity (P0-3).
- `frametax2/backend/tests/test_allocation_pricing.py` — updated wording assertions.
- `frametax2/backend/tests/test_canonical_authority_substrate.py` — updated reconciliation counts.
- `frametax2/backend/tests/test_canonical_served_wiring_repair.py` — updated reconciliation counts.
- `frametax2/backend/tests/test_canonical_scenario_participants.py` — new, 6 tests.

## 10. Claude permission-interruption report

Reported separately in the final chat response per the task's own instruction (Section 27) — this document covers product/engineering findings only.

## 11. Commit / push / remote verification

See the final chat response for exact commit SHA, push status, and remote verification (this document is written before the closing commit; do not treat its absence here as incomplete — the response completes it).

## 12. Stop-condition self-assessment

Per Section 31's explicit list, this pass does **NOT** meet the full completion bar:

- Mandatory eligibility enforcement: **generic and proven** ✓
- NPC semantics/trace reconstructible: **not attempted** ✗ (P0-2)
- Multi-territory participants survive end-to-end: **proven at the API boundary**; not verified through Globe/Inspector/Reports (frontend untouched) ✗ partial
- Canonical scenario identity end-to-end: **not built as a formal identity object** ✗
- Globe hover/click/Inspector identity: **not attempted** ✗
- Status-bearing Globe geography: **not attempted** ✗
- Saudi/discretionary semantics remain conditional: **partially strengthened** (component disclosure added); rate-ceiling doctrine untouched by design (Rule #10)
- Generic project modeling policy beneath Saudi behavior: **already existed** from a prior session (jurisdiction_preference ProjectFact mechanism), unchanged this pass
- Program onboarding without bespoke wiring: **not attempted** ✗
- Permanent conformance/integrity gates: **not built as permanent systems** ✗
- All-project scenario universe passes gates: **not run** ✗
- Workspace/Overview composition rules: **not touched, not verified this pass** (out of scope — engine/data-contract task, no UI touched)

**PARTIAL — DO NOT ADVANCE TO SA-2.**

Exact blockers: P0-2 (NPC trace), the full generic eligibility/economic-strategy/scenario-identity/Globe-projection contracts (Sections 6-9, 15-16), the program-onboarding conformance gate and permanent Canonical Integrity Gate (Sections 19-20), and the three-project cardinality/acceptance re-baseline (Sections 22-23) were not attempted in this pass due to the scale of the request relative to available turn budget. What was fixed (P0-1, P0-3, and half of P0-4) is real, runtime-verified against live project data, and committed — not fabricated or claimed beyond what was actually done.
