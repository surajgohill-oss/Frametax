# CineGlobe Canonical Identity, Authority and Active-Delta Cleanup — Claude

Base commit: `3b5c3f5ea7c16358b8fe9ed64f0f5f2181d05ae5`.
Codex audit source (read directly, never merged): `codex/305-program-delta-audit-20260915` @ `35f2553fd00ac0de868bbffa35ce255369e99ef6`.
Branch: `claude/audit-frametax-features-NZcX5`.

## Summary

Bounded cleanup covering the 31 authority-vetoed records, Bulgaria's provenance/manifest
conflict, BC DAVE's missing identity/input binding, Ohio's identity-first verification,
Nevada's missing statutory constraints, and Czech animation's manifest/runtime contradiction.

### Phase 1 — 31 authority-veto reconciliation

Codex's own audit (`CODEX_53_WARNING_CANONICAL_RECONCILIATION.csv`) had already independently
confirmed all 31 requested records as `FALSE_POSITIVE_AUTHORITY_VETOED` /
`AUTHORITY_EXHAUSTED_FAIL_CLOSED` — i.e., their dormant rate/doctrine data correctly does NOT
override the authority fail-closed disposition; no economic candidacy should exist for any of
them. Direct verification against the live `app/data/authority_coverage_registry.py` (both the
`economic_block_for_program` B1/B4 gate and the `COVERAGE_REGISTRY`/`get_coverage_status` gate)
found this **was already true for 28 of the 31** — no code change needed. **Three genuine gaps
were found and fixed**: `ca_bc_pstc`, `ca_federal_pstc`, and `si_cash_rebate` were absent from
BOTH veto mechanisms entirely (only alias entries pointed AT them, with no actual veto ever
registered under any spelling) — meaning these three programs were NOT actually blocked at
runtime despite Codex's own audit, and this workstream's own initial pass, both assuming they
were. Added to `_B1_DISCRETIONARY_RULING` this pass, proven via
`tests/test_canonical_identity_authority_invariants.py`.

See `docs/validation/CANONICAL_31_AUTHORITY_STATE_RECONCILIATION_CLAUDE.csv` for the full
per-record disposition trace.

### Phase 2 — Bulgaria

Confirmed root cause: `bg_film_encouragement_act_rebate`'s doctrine citation (`innovires.com`) is
a secondary aggregator, not a primary/official source — correctly reflected in
`authority_coverage_registry.py`'s `AUTHORITY_UNRESOLVED_NON_PRICEABLE` state (a real,
non-blocking, PROVENANCE-axis disclosure, per that module's own documented two-axis design). The
real defect: this provenance warning was appended as a **text string only** — it never touched
`qualification_state`, so a provenance-unresolved candidate could still reach Recommended/rank-1
as if fully knowledge-verified. Fixed: `canonical_evaluation.py` now downgrades
`qualification_state` to `QUAL_AUTHORITY_UNRESOLVED` (via the same worse-wins merge every other
qualification signal already uses) whenever a program's coverage state is in
`PROVENANCE_DISCLOSURE_STATES` — excluding it from `_QUALIFICATION_ADMITS_RECOMMENDED` until a
human confirms the authority, while the real $500,000 base economics remain unchanged and still
visible/discoverable. `allocation_pricing.SegmentEconomics` gained a matching
`authority_provenance_unresolved` disclosure field, now serialized for backend/future-UI support.

### Phase 3 — BC DAVE

Confirmed root cause: the 16% rate condition only *disclosed* that a narrower qualified-BC-labour
basis was required — it never bound one, so DAVE could never actually price. Fixed using the
**same generic canonical-line reconciliation mechanism** this workstream already built and proved
for South Africa's post/VFX QSAPPE and Oregon's payroll/other split: a new
`component_basis_spend_categories`-gated amount fact deriving the exact qualifying-labour subtotal
directly from real `AccountAllocation` lines (a mismatched caller assertion rejects), plus a real
`required_boolean_fact_key` gate for DAVE-eligible activity. 4/4 new tests pass. No duplicate BC
candidate created (DAVE remains its own distinct component identity, separate from `ca_bc_pstc`);
no automatic stacking inferred.

### Phase 4 — Ohio identity-first verification

Searched the real dev database (0 US-OH jurisdiction rows), every `app/data/*.py` file (no
OH-prefixed doctrine/RateRule/jurisdiction seed anywhere), and
`app/data/global_inventory_manifest_final.py` (exactly one existing Ohio record — a
`DISPLAY_ONLY` informational entry with zero guaranteed economics, the same real-world program at
a different processing stage, not a second candidate). **No executable canonical Ohio program
exists to conflict with, duplicate, or supersede** — and no already-accepted Ohio doctrine/rate
research exists in this repository to implement the proposed identity from (confirmed by the same
search). Per the required sequence's own final clause, implementing one now would require new
jurisdiction research, explicitly out of scope. **No code change made** — the existing
`AUTHORITY_LOCKED` (`UNPRICEABLE_AUTHORITY_INSUFFICIENT`) disposition was already correct.

### Phase 5 — Nevada

Implemented the real, already-accepted **USD6,000,000 per-project cap** (`film.nv.gov`, the same
source already cited in the program's own doctrine record) via the standard
`IncentiveValueCapRule` mechanism — the single most severe open gap (an unbounded incentive).
4/4 new tests pass: cap registered at the real figure; a below-cap case prices its real uncapped
figure; a large qualifying spend clips to exactly $6,000,000; below-minimum-spend rejects. The
$750,000 per-person limit, 60% spend ratio, and 12% nonresident-ATL narrower base are **not**
implemented this pass — each requires new per-payee/per-category component-basis mechanics this
bounded pass did not have time to safely design and test after prioritizing the cap; disclosed
honestly in `CANONICAL_CLEANUP_REMAINING_ITEMS_CLAUDE.csv`.

### Phase 6 — Czech animation

Root cause: `CODEX_12_PROGRAM_FINAL_MATRIX.csv` and `CODEX_53_WARNING_CANONICAL_RECONCILIATION.csv`
disagreed with EACH OTHER, not with the runtime — direct inspection confirmed
`cz_film_incentive_animation`'s actual registered state is `AUTHORITY_UNRESOLVED_NON_PRICEABLE`
(non-blocking), never the `AUTHORITY_EXHAUSTED_FAIL_CLOSED` hard block `CODEX_12`'s FAIL reading
implied. Investigated merging the 35% animation tier physically into `cz_film_incentive`'s own
`DoctrineRecord`: the engine's `production_types` gate is record-level (documented in the existing
code), and the two-record architecture is exercised by an existing, accepted, passing test
(`test_cz_film_incentive_production_type_branch_and_qpe_cap`) — merging would require a
re-architecture beyond this bounded pass's risk budget and would break that accepted test.
Proved instead, directly against the code, that **no double counting is reachable**: `feature_film`
and `animation` are mutually exclusive project-level facts, so no real project can ever receive
both `cz_film_incentive` and `cz_film_incentive_animation` as priced candidates simultaneously.
Reconciled the identity/counting lineage (Czech = one statutory program with an internal
live-action/animation split, for matrix-counting purposes) without touching the preserved,
accepted runtime pricing behavior. See `CANONICAL_CZECH_TIER_RECONCILIATION_CLAUDE.csv`.

### Phase 7 — Prevent recurrence

`docs/validation/CANONICAL_ARTIFACT_PRECEDENCE_CLAUDE.json` establishes the precedence ordering
(live executable registries > implementation-branch CSV/MD > research/audit-branch artifacts,
never merged). `tests/test_canonical_identity_authority_invariants.py` proves 5 bounded
invariants directly against the live registries: aliases resolve before priceability is audited;
historical/source IDs (confirmed this pass) carry no independent rate rules; all 31 reconciled
authority-vetoed records are genuinely blocked at `resolve_program_rate`'s own B4 gate (this test
is what CAUGHT the three real gaps in Phase 1); a program with a missing satisfiable fact (BC
DAVE) stays visible/conditional, never silently excluded; and the four Phase 2–6 reconciled
programs' manifest and runtime states agree.

## Backend status support for later UI

`SegmentEconomics` and its serialization already carry canonical ID, program name, jurisdiction,
`candidate_status`/`rejection_reason_class`, exact reason string, `requirement_trace`/missing
facts, and (this pass) `authority_provenance_unresolved`. This satisfies the required
`VERIFIED_AUTOMATIC` / `VERIFIED_CONDITIONAL_FACTS_REQUIRED` / `DISPLAY_ONLY` /
`AUTHORITY_LOCKED` / `REJECTED_FOR_THIS_PRODUCTION` / `HISTORICAL_OR_SUPERSEDED` distinction at
the data layer; no UI was touched.

## Focused test results

| Suite | Result |
|---|---|
| `tests/test_canonical_identity_authority_invariants.py` (new) | 5 passed |
| `tests/test_ca_bc_dave_component.py` (new) | 4 passed |
| `tests/test_us_nv_film_credit_cap.py` (new) | 4 passed |
| `tests/test_b3_formulaic_consumption.py -k cz_film` (regression) | 1 passed, unchanged |
| Four frozen project controls (direct recomputation) | 4/4 exact, unchanged |

No required test was skipped. The full backend suite, full 12-program matrix, and optimizer
hybrid/co-production/stacking methodology were explicitly not run/audited, per the test boundary.

## Frozen areas — confirmed unchanged

Netherlands, South Africa, Oregon, Malaysia FINAS, the original single-jurisdiction methodology,
MFNI, Reinvestment, hybrid/co-production/stacking methodology, UI/globe, Location feasibility,
Script Analyzer, and the four established project economics: no files under any of these areas
appear in this pass's diff (verified via `git diff --name-only`), and the four project economics
were directly recomputed and confirmed exact/unchanged above.
