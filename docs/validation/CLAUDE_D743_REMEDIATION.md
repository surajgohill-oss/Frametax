# CLAUDE_D743_REJECTED_FINDINGS_REMEDIATION

Base commit: `d743fab55622f82fca24f27635344b83c3642900`. Codex acceptance audit read directly
(never merged): `7d30706dfac51e1adfff0a9dabd104313c91dbea` (covers
`3b5c3f5ea7c16358b8fe9ed64f0f5f2181d05ae5...d743fab`, audit contract
`cdaf1968fe38e64af873ac9c4c6da53d03687446`). Worktree
`/Users/Suraj/cineglobe-frametax-claude-remediation`, branch `claude/audit-frametax-features-NZcX5`.

Codex's decision on d743fab was **REMEDIATION_REQUIRED**: P0-COMB-001 rejected (RUNTIME_VERIFIED —
the treaty partner received $0 allocated spend), P1-TRACE-001 rejected (STATIC_VERIFIED —
`max(per_program_qpe)` is a lower bound, not exact unique spend), P1-TEST-500 rejected (the
500-row cap was not evaluation-scoped), P2-HEALTH-HARNESS rejected (event-loop cascade failures).
This document fixes exactly those rejected findings, plus the two Codex-confirmed pre-existing
`ca_bc_pstc` test failures. Every ACCEPT finding from `7d30706` (P0-CAND-001/002/003, P0-QUAL-001,
P0-STACK-001, P1-CLASS-001, frozen economics, the earlier Bulgaria/BC-DAVE/Ohio/Nevada/Czech
cleanup) is untouched by this pass.

## P0-COMB-001 — remediated

**Codex's first-failing-behavior finding**: `_price_combined_coproduction_component_candidate`
supplied only `component_routes`; `ownership_shares`/`account_splits` were empty, so
`derive_account_allocation`'s own precedence rules defaulted every non-component account to the
primary jurisdiction alone. An independent probe found MU=$2.0M, GB=$0, CA-BC=$1.0M — conservation
without a real co-production. Generation was also limited to the single highest-spend component
and the single best remaining target, and post-pricing stacking was attempted on the anchor side
only.

**Fix — real evidenced treaty-side allocation.** The function now takes `majority_pct`/
`minority_pct` (the SAME real, per-treaty, per-participant-scoped facts P0-QUAL-001 already fetches
in the home-anchored loop via `_coproduction_facts` — never invented, never a bare registry guess).
Every non-memo, non-routed-component budget line receives an explicit `spec.account_splits` entry
splitting it between the anchor and the treaty partner by their real evidenced share.
`derive_account_allocation`'s own highest-precedence rule (an explicit producer split beats every
other routing rule, including `component_routes`) means the partner now receives its genuine
contractual share of every account the routed component does not claim; the routed component's own
accounts are deliberately excluded from the split so `component_routes` still sends them entirely
to the component target (a component relocates as a whole — it does not fractionally split between
co-production parties).

**Reject any claimed participant with zero or invalid allocation.** A new
`_InvalidCombinedAllocation` exception is raised — never returns a silently-zeroed participant —
whenever `majority_pct`/`minority_pct` are missing, non-positive, or when the resulting
`allocation.allocated_by_jurisdiction()` gives *any* of the three participants zero dollars. The
caller persists each such rejection as its own retained, machine-readable candidate
(`rejection_reason_class="INVALID_COMBINED_ALLOCATION"`), never a silent skip.

**Canonical component names.** The Codex-flagged `"post_vfx"` (not a real value —
`MOVABLE_COMPONENTS = frozenset({"post", "vfx", "music"})`) never appeared in the production code
path itself (that already used the real `component_for()` derivation); it was only in Claude's own
test fixture, now fixed to use `"vfx"`.

**No longer limited to one component or one target.** `_combined_components` now enumerates every
movable component with real spend > 0 (was: `max(component_spend.items())`, the single highest);
the caller walks the full `_combined_top_targets` list per component (was: `next(...)`, the first
match only).

**Authorized stacks on every allocated side.** A new `_apply_authorized_stacks_to_combined_sides`
helper calls `_authorized_local_stack_for_side` for the anchor, the treaty partner, *and* the
component target — not the anchor alone. Each side's unresolved-but-attempted stack is still
retained as its own separate rejected candidate; a resolved named rule still adds only its
incremental delta, never double-counted.

**A deeper, previously-unexercised kernel bug found and fixed during remediation.** Even with the
allocation fix above, the first attempt at a real fresh combined structure still failed to price:
`allocation_pricing._treaty_requirements` (a shared kernel function, gated for
`structure_type in ("treaty_coproduction", "majority_minority", "multi_party", "hybrid")`) requires
a registered bilateral treaty for *every pair* among *all* structure participants — including the
component target, which is never a co-production party at all. This made every hybrid structure
unconditionally unpriceable regardless of how real the underlying treaty was (no pair including the
component target can ever have a treaty). Confirmed via source search that no caller anywhere in
this codebase constructs a `StructureSpec` with `structure_type` `"treaty_coproduction"`,
`"majority_minority"`, or `"multi_party"` — `"hybrid"` (this remediation's own code) is the *only*
real caller this gate has ever actually run for, so narrowing its scope is safe. Fixed:
participants who receive their allocated spend through an explicit `account_splits` entry (the
genuine co-production side) are the only ones required to have pairwise treaty coverage; a
participant reachable only via `component_routes` is priced independently, exactly like an ordinary
`component_relocation` target (which this gate never applied to in the first place). Falls back to
requiring every participant, byte-identical to the prior behavior, whenever `account_splits` is
empty.

**Real served end-to-end proof (required by Codex; a helper-only unit test is explicitly
insufficient).** A synthetic bilateral treaty (Mauritius/`MU` has no real registered treaty of its
own) between Little Utopia's real home jurisdiction (`MU`) and a real, independently-discovered
candidate partner (`GB`), plus real scoped `ProjectFact` contribution-share facts (70%/30%), was
written against Little Utopia's real, stored project record, and `evaluate_project()` was run for
real. Result: **65 genuinely priced, real, served `hybrid` structures** out of 108 attempted
(component × target combinations), each with real, nonzero allocated spend to every participant —
confirmed directly:

| Participant | Role | Allocated USD |
|---|---|---:|
| MU | anchor / majority (70%) | 3,048,728.90 |
| GB | treaty partner / minority (30%) | 1,306,598.10 |
| (component target, e.g. SK/IS/JO) | routed component | 9,068.00 (post) |

This is `tests/test_claude_global_optimizer_p0_remediation.py::test_comb_001_real_served_end_to_end_combined_structure`
— proven against a real, stored project, not a helper called in isolation. The test writes and
tears down its own throwaway `ProjectFact` rows and monkeypatched treaty entry; Little Utopia's
real frozen baseline economics are read but never written to, and are reconfirmed exact below.

**Why none of the four required canonical productions serve a combined structure.** All four
(Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar) currently have **zero**
`combined_coproduction_component_stack`/`hybrid` structures in their real, fresh runtime — matching
Codex's own d743fab finding exactly ("gated on already-ELIGIBLE treaty facts; the three real
projects have none"). The topology is correctly additive and inert until a project has a real,
evidenced treaty ownership-share fact on file; none of the four does. This is the honest, expected
outcome, not a defect — the end-to-end proof above demonstrates the topology works correctly the
moment such facts exist.

## P1-TRACE-001 — remediated

**Codex's rejection**: `total_qualifying_spend_usd = max(per_program_qpe)` is a lower bound, not
exact unique allocated spend — for partially-overlapping or disjoint program bases, the true union
of unique underlying spend can exceed the maximum single base.

**Fix — exact line-level union.** `StackCandidate` gained a new field, `qualifying_line_ids:
frozenset[str]`, populated at both construction sites directly from
`derive_qualification_register`'s own real `line_id` per account (the register already carried
this; it was simply never threaded through to `StackCandidate`) — real `BudgetLine.line_id`
identities, never the `account_code` classification field a real budget may legitimately reuse
across distinct lines. `total_qualifying_spend_usd` is now computed as the exact union of every
stacked program's own `qualifying_line_ids`, resolved against a real `line_id -> amount_usd` map
built once from the project's actual budget lines — overlapping lines are counted exactly once,
disjoint lines are counted in full, never approximated by `sum()` (double-counts overlap) or
`max()` (understates disjoint/partial-overlap bases). `total_claim_bases_usd` (the honestly-named
sum of reusable, possibly-overlapping claim bases) is unchanged.

**Independent overlap and disjoint-base tests, proven against an independent expected-value
oracle** (never a copy of the production formula):
- Fully disjoint bases: exact union == naive sum == 700,000.00, strictly greater than max() —
  the case max() understated.
- Full overlap (one base a strict subset of the other): exact union == the larger base exactly ==
  330,000+... (700,000.00 in the test), strictly less than naive sum — the case sum() overstated.
- Partial overlap (the general case): exact union (300,000.00) strictly between max() (200,000.00)
  and sum() (400,000.00) — the property neither prior approach satisfied.
- A real, currently-priceable named pair (`on_ofttc`/`ca_federal_cptc`) confirmed to populate real,
  non-empty `qualifying_line_ids` end to end.

## P1-TEST-500 — remediated

**Codex's rejection**: `_current_rows().order_by(created_at.desc()).limit(500)` was not scoped to
engine version, fingerprint, or evaluation/run identity — it could truncate a future generation
above 500 rows and could not prove completeness.

**Fix.** `_current_rows` is replaced by `_current_generation_rows(db, project_id)`, scoped to
*both* the current `ENGINE_VERSION` and the exact fingerprint the project's current inputs resolve
to right now (`current_generation_fingerprint` — the same read-only reconstruction every real
served view already uses to identify "the" current evaluation). This is the true, complete,
**unbounded** set of rows belonging to exactly one evaluation generation — never an approximation
by recency or row count; no `LIMIT` is applied or needed, since one generation is naturally small
(hundreds of rows for a real production) regardless of how many historical generations a project
has accumulated in total. The one legitimate remaining use of a `.limit(1)` is a new, separate
`_stale_engine_version_row_exists()` existence-only probe used by the staleness-detection test — it
answers a yes/no question ("does any stale row exist"), never a completeness claim, so it is not
the arbitrary correctness cap Codex's audit objected to.

## P2-HEALTH-HARNESS — remediated

**Codex's finding**: `test_codex_final_optimizer_health_audit.py` completed 4 passed / 5 failed in
7.97s; failures cascade from a shared `asyncpg` connection attached to a different event loop /
operation already in progress.

**Root cause.** `app.db.session.engine` is a module-level singleton created once at import time;
its connection pool holds `asyncpg` connections bound to whichever event loop was running when
they were opened. `pytest-asyncio`'s `asyncio_mode = "auto"` gives each async test its own, fresh
event loop by default — a pooled connection opened under test N's loop is no longer valid once
test N+1 runs under a different loop.

**Fix.** The file's own `db` fixture now disposes the engine's connection pool in teardown
(`await engine.dispose()` after every test), forcing the next test to open fresh connections under
its own loop rather than reusing a now-invalid pooled one — function-scoped lifecycle isolation
matching pytest-asyncio's own per-test event loop, without touching the shared `app.db.session`
module other test files still import unchanged. Result: **8 passed, 1 legitimate skip** (a program
genuinely not a candidate for current inputs), no cascading failures, 17.71s total. No test was
skipped or weakened to reach this result — every original assertion is intact.

## CA-BC PSTC — the two confirmed pre-existing failures fixed

Both failures traced to the same root cause: a prior, separately-accepted session (the canonical
identity/authority cleanup, already part of the starting HEAD `0c97a6a`) deliberately added
`ca_bc_pstc` to the B1 discretionary-ruling `FAIL_CLOSED` veto list in
`authority_coverage_registry.py`. `resolve_program_rate("ca_bc_pstc", ...)` now returns `None`
unconditionally via `economic_block_for_program`'s own B4 gate (the *first* check in
`resolve_program_rate`, before any tier/QPE logic runs at all) — a genuine, already-accepted
authority decision, not a bug to revert. The two tests were written before that veto existed and
never updated.

**Fix.** Both tests now use `on_opstc` + `ca_federal_cptc` (`CA-ON`) instead of `ca_bc_pstc` +
`ca_federal_cptc` (`CA-BC`) — the real, currently-priceable, analogous `mutually_exclusive` pair
already recorded in `stacking_rules.py` (Ontario's own PSTC-equivalent vs. CPTC is the *identical*
CPTC-vs-foreign-service-track legal logic the BC pair encoded, just for a different province).
Confirmed both programs resolve real rates and the pair produces a genuine `mutually_exclusive`
stack result.

- `test_canonical_stack_bridge.py::test_price_program_pair_stack_mutually_exclusive_zeroes_lower_value` — **fixed, passes**.
- `test_copro_conditional_pricing_bridge.py::test_conditional_scenario_routes_same_jurisdiction_multi_slug_through_stack_engine` — **fixed, passes**.

**DAVE preserved, no unsupported automatic stacking introduced.** No change was made to
`ca_bc_dave` (BC's own separate component identity) or to any stacking-rule data; only the two
test fixtures were repointed to a real, already-registered pair. `price_program_group_stack`'s own
fail-closed "no named rule -> None" behavior (P0-STACK-001) is unchanged and continues to prohibit
any unauthorized/unsupported combination.

**Two other, separately pre-existing `ca_bc_pstc` test failures remain, out of scope.**
`test_canonical_economics_integrity_repair.py::test_programs_declaring_a_narrower_rate_base_do_not_price_off_all_spend`
and `::test_narrower_base_check_scans_every_tier_not_just_the_selected_one` were not named in
Codex's CA-BC-PSTC finding (only the two above were) and are left exactly as found — both fail
identically on unmodified `d743fab`, for the same root cause (the B1 veto), a data/message-format
mismatch rather than an allocation defect, and are outside this bounded workstream's assigned scope.

## `ENGINE_VERSION`

Bumped `canonical-1.55.0` -> `canonical-1.56.0` so every row persisted under the d743fab-era
(rejected) P0-COMB-001/P1-TRACE-001 implementations is treated as stale and regenerated fresh —
never silently served as current under the remediated engine.

## Deferred (per explicit instruction)

P1-ENG-001 (duplicated treaty-construction-loop refactor), Ohio/Bulgaria/Nevada new research, MFNI,
reinvestment, UI, location feasibility, Underwater's bare-`US` baseline issue, and V-BRAT (confirmed
by both this pass and Codex's own audit to be a mislabeled budget-document filename attached to
F#K Valentine's Day, not an independent production — no project created or substituted).

## Focused test results

| Suite | Result |
|---|---|
| `tests/test_claude_global_optimizer_p0_remediation.py` (35 tests, 8 new/rewritten this pass) | 35 passed |
| `tests/test_canonical_stack_bridge.py` + `tests/test_copro_conditional_pricing_bridge.py` (CA-BC PSTC fix) | 29 passed |
| `tests/test_codex_final_optimizer_health_audit.py` (harness fix) | 8 passed, 1 legitimate skip |
| Treaty/copro/stacking/identity/DAVE/NV/engine focused suite (11 files) | 213 passed |
| Optimization contract/inventory/optimizer/page-integrity/import-order/closeout/input-integration (7 files) | 230 passed |
| `tests/test_canonical_economics_integrity_repair.py` | 44 passed, 2 pre-existing (unrelated, out of scope) |
| Four frozen/canonical project controls (direct fresh recomputation) | 4/4 exact, unchanged |

No test was skipped or weakened to reach these results (the one `pytest.skip` in the health-audit
file is a pre-existing, legitimate "this program is not a candidate for current inputs" skip, not
a weakened assertion).
