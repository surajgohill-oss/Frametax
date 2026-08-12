# Consolidated Global Remediation — Closeout

Date: 2026-08-12
Branch: `claude/audit-frametax-features-NZcX5`
Canonical remediation input: `docs/validation/GLOBAL_REMEDIATION_INPUT.json` (213 implementation items — 52 pre-distribution + 161 distributed)
Companion artifacts: `CONSOLIDATED_REMEDIATION_PHASE_A_INVENTORY.json`, `GLOBAL_REMEDIATION_DATA_BACKLOG.json`, `CONSOLIDATED_GLOBAL_REMEDIATION_VERIFICATION.json`

## What this pass is

A single implementation pass over the closed, authorized global validation output. No jurisdiction/rule research was reopened. Where the canonical remediation input specifies an exact, actionable structural fix (an exclusion, a candidate-generation gap, a Bridge/NPC consumption bug), it was implemented and runtime-verified. Where it only records *that* a program's data is incomplete/stale and cites source URLs — without a literal replacement rate, cap, or threshold — no value was invented; the item is logged in the disclosed backlog instead.

## Phase A — exact implementation accounting

213 items, one canonical ID and one action each, zero duplicates:

| Action | Count | Layer breakdown |
|---|---:|---|
| CORRECT_DATA | 149 | mostly DATA_ONLY |
| ADD_PROGRAM | 22 | PROGRAM_DATA_AND_CANDIDATE_GATING |
| DISABLE_UNPRICEABLE | 25 | EXCLUDE_FROM_OPTIMIZER (2) / DATA_ONLY |
| EXCLUDE_NON_ECONOMIC | 4 | EXCLUDE_FROM_OPTIMIZER |
| UPDATE_TREATY_DATA | 7 | TREATY_STRUCTURE_LOGIC_AND_DATA |
| MERGE_PROGRAM | 3 | DATA_ONLY |
| SUPERSEDE_PROGRAM | 3 | DATA_ONLY |

## Phase B/C — the 25 unpriceable + 4 non-economic programs

New module `app/data/authority_coverage_registry.py` gives all 29 canonical IDs an explicit, deterministic disposition (`UNPRICEABLE_AUTHORITY_INSUFFICIENT` / `NON_ECONOMIC_CONFIRMED`) with reason, source artifact, and a reactivation note — distinct from the prior *implicit* state (DISCOVERY tier, no `program_slug`). None of the 29 carry a `base_rate`/`rate` field on the registry record itself (no synthetic economics possible from this artifact). Regression-locked by 7 tests confirming none of the 29 have an executable `DoctrineRecord` or appear in `jurisdiction_comparison.ALL_PROFILES` — the two places a program would need to be for pricing/ranking to ever see it.

## Phase D/E — QPE default-inclusion and territoriality

Both rules were already correctly implemented in `qualification_derivation.py`'s decision ladder (`OPEN_DEFAULT_INCLUDE` doctrine; a fact-based territorial-nexus check that runs *before* and independently of payroll-routing). No code change was needed. Two targeted fixtures in `tests/data/test_territoriality_and_qpe_default_inclusion.py` prove it: a line with no explicit rule still qualifies under default-inclusion doctrine, and a labor line physically outside the jurisdiction stays excluded even when `payroll_routing_localized=True` (paid through a local SPV/EOR) — local-SPV payment alone does not manufacture qualifying territorial expenditure.

## Phase G — treaty data

`treaty_engine.py`'s bilateral/multilateral registries were inspected against `GLOBAL_CANONICAL_TREATY_DISPOSITION.json`'s 7 queues; none of the 7 carry literal replacement party/date/contribution data in the canonical input (same finding as the CORRECT_DATA items — logged in the backlog, not fabricated). The registry's existing data (confirmed real, e.g. `ca-fr-bilateral`, `uk-ca-bilateral`) was used as-is to build and verify Phase H.

## Phase H — the real, confirmed candidate-generation gap

Found and fixed a genuine defect distinct from — and not in conflict with — the ledger's prior "proven zero treaty partners for Mauritius" finding: `component_relocation` structures were already auto-enumerated for every executable partner with no producer election required, but `treaty_coproduction` structures were generated **only** when a producer manually set the `treaty_partner_code` fact. A jurisdiction pair with a real, registered treaty instrument could silently never surface a structure unless a user happened to elect it by hand.

Fixed in `app/demo/little_utopia_state.py`: `treaty_coproduction` `StructureSpec`s are now auto-enumerated from the real `treaty_engine` registry (bilateral treaty match, or shared European Convention membership) for every executable partner — the same pattern already used for component-routing. The manual `treaty_partner_code` election remains as a fallback for a pair the auto-enumeration doesn't cover (still returns an honest `UNAVAILABLE` block, never a fabricated price).

For Mauritius specifically this auto-enumeration correctly yields **zero** structures — `treaty_engine` holds no MU bilateral treaty and MU is not a European Convention signatory, exactly as previously proven — so Little Utopia's served candidate set is unaffected (177 structures, MU baseline NPC byte-identical at $3,057,794.90, rank-1 unchanged). The fix is proven general with real registry data for a jurisdiction that does have coverage (Canada ↔ France/Germany correctly selected; Canada ↔ Japan, unregistered, correctly excluded) in `tests/optimization/test_treaty_candidate_generation.py`.

## Phase I/J — NPC/ranking and Bridge

The prior Incentive/Optimizer Core Closeout (commit `21af675`) fixed Bridge's `EconomicsSummary.npc_usd` to source `npc_with_adjustments_usd`, but was verified only against the MU baseline and the 5-jurisdiction pilot. This pass confirmed the fix is general: 20 randomly-sampled non-pilot structures (Croatia, Switzerland, Ukraine, UK, Poland, Jordan, Montenegro, Puerto Rico...) all show `Bridge.economics.npc_usd == served npc_with_adjustments_usd`, 0 mismatches, and the full 149-structure priced ranking list is strictly ascending by that same canonical field. Locked in by `tests/bridge/test_npc_canonical_value_generalized.py`.

## What was deliberately NOT done

**176 of 213 canonical items remain data-incomplete**, logged with full reasoning and preserved source citations in `GLOBAL_REMEDIATION_DATA_BACKLOG.json`. The canonical remediation input records *that* a program is stale/incomplete/incorrect and *where* to look, but for the large majority of items does not itself carry a literal replacement rate, cap, threshold, or treaty term — applying a field-level correction without reading and transcribing from those cited sources would mean reopening primary-authority research, which this task's own instructions close ("the global jurisdiction/rule research phase is CLOSED; do not restart jurisdiction research"). No number was guessed or fabricated anywhere in this pass. A separate 7-item catalog-hygiene backlog (3 merge + 3 supersede + 1 naming duplicate) was confirmed to carry **zero live pricing risk** today (none of those 7 canonical IDs have an executable `DoctrineRecord`) — the remaining action is cosmetic.

One item (`au_location_offset`) was directly verified already correct in code from the prior closeout and needed no change.

## Verification

11/11 targeted runtime checks pass (full detail and evidence in `CONSOLIDATED_GLOBAL_REMEDIATION_VERIFICATION.json`). Full backend suite: **4008 passed, 1 skipped, 1 pre-existing unrelated failure** (a frontend title-formatter guard on a file with zero local diff, already documented as pre-existing in `CAPABILITY_LEDGER.md`). Little Utopia's served baseline is byte-identical throughout: 177 structures, MU NPC $3,057,794.90, rank-1 `ALLOC-BASELINE-MU`.

## Final gate

**`NO_GO_REMEDIATION_NOT_RUNTIME_VERIFIED`** — reflecting incomplete data population (176 items), not an architecture or runtime-correctness failure. Every deterministic-chain repair this task required at the *engine* level (exclusion architecture, QPE/territoriality, candidate generation, NPC/ranking, Bridge) is implemented and runtime-verified. See `CONSOLIDATED_GLOBAL_REMEDIATION_VERIFICATION.json`'s `final_gate_clarification` for the distinction and the master engineer's available options.
