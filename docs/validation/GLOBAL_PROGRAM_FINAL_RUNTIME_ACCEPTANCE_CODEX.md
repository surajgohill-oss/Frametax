# Global Program Final Runtime Acceptance — Codex

**Workstream:** `CODEX_FINAL_CANONICAL_INCENTIVE_RUNTIME_ACCEPTANCE`
**Verdict:** `NOT_ACCEPTED`
**Claude commit audited:** `e0a8caa64f5498f70c1e409c848a9d4652b11a21`
**Controlling Codex adjudication:** `9baa3b68c90b81d3819bd29c30ff140812f2ab1b`
**Accepted research base:** `a5958b1211ac6e8071f40811a4781166466ef768`
**MFNI:** `PARKED_UNCHANGED`

## Outcome

Claude's delta is not ready for final canonical incentive/runtime acceptance. The complete backend suite passes, the four real projects preserve their expected topline outcomes, the six identity rulings are sound, and the 47 rows Claude called “stale runtime paths” are protected, unreachable legacy references in the current unmutated registry state. Those successes do not close the controlling acceptance standard.

Two independent P0 blockers remain:

1. Eleven of the twelve B3 formulaic specifications are not implemented end to end. Discovery plus direct `price_segment()` calls are not optimizer-consumption proof. Native-currency thresholds/caps, component bases, award/project facts, and controlled rejection paths are absent or replaced by USD surrogates. Only the Dubai/Abu Dhabi fail-closed identity correction conforms as written; strict optimizer-consumption proof is `0/12` because no row proves all seven required stages.
2. The B4 refusal boundary is one-hop only. A two-hop `PROGRAM_SLUG_ALIASES` chain terminating in a blocked identity can evade `economic_block_for_program()` and resolve an injected 99% rule. The independent strict-xfail test reproduces this deterministically.

A current P1 import-order defect also remains: importing `canonical_production_view` first in a fresh process raises a partially-initialized-module error; importing `canonical_evaluation` first masks it.

## Independent recomputation

- Canonical adjudication matrix: **586 rows / 586 unique IDs / 0 duplicates**.
- Follow-up implementation rows: **95/107 closed**; 11 B3 rows and the B4 gate row remain open.
- B1 decisions: **46/46 directly refused** in the current registry (13 display-only, 33 fail-closed).
- B2 identity rulings: **6/6 represented correctly**.
- Alias cleanups: **13/13 accepted cleanup rows represented**; current runtime alias map has 11 surviving compatibility aliases, 0 cycles, 0 orphan targets.
- Catalog-identity corrections: **42/42 represented**.
- Retirement: **1/1 represented**.
- Current reachable stale pricing paths: **0**.
- Raw rule keys protected by B4: **50**. The 47 Claude-labeled rows are a subset and must be called protected unreachable references, not stale runtime paths.

## B2 identity result

`ca_film_30` is the authorized California canonical identity. `us_ca_film_credit` is the historical compatibility alias pointing toward it. Only `ca_film_30` owns the executable rule and fresh optimizer output. Lips Like Sugar remains exactly $3,459,278.90 gross incentive and $8,524,375.10 NPC. New York's main credit canonicalizes to `ny_state_film` while its post-production identity remains distinct and fail-closed. Ontario `on_opstc` and `on_ofttc` remain distinct and have an explicit `mutually_exclusive` pair rule.

## Four-project runtime

| Project | Universe | Priced / rejected | Result |
|---|---:|---:|---|
| Little Utopia | 251 | 132 / 119 | Deterministic no-winner: existing authority-unresolved qualification gate |
| F#K Valentine's Day | 306 | 169 / 137 | Deterministic no-winner: existing user-fact-required cultural gate |
| Bad Hombres | 248 | 130 / 118 | `us_nm_film_credit`; $596,910.25 incentive; $1,885,112.75 NPC |
| Lips Like Sugar | 308 | 185 / 123 | `ca_film_30`; $3,459,278.90 incentive; $8,524,375.10 NPC |

All four use `canonical-1.54.0`; current fingerprints match the persisted current generation and candidate accounting balances exactly.

## Tests

- Claude focused B3/B4 tests: **20 passed**.
- Named global/optimizer/conditional/treaty/stack/integrity groups: **512 passed**.
- Entire backend before adding the audit-only corruption test: **4,812 passed, 3 skipped, 0 failed**.
- Independent corruption test: **10 passed, 1 strict xfail**, the xfail being the reproduced two-hop alias bypass.

No modified existing test was found to have a materially weakened oracle. Claude's new B3 test is nevertheless an acceptance false positive: it proves discovery/direct calculator reach, not the seven-stage optimizer-consumption contract. Claude's new B4 test is useful but incomplete because it omits transitive alias corruption.

## Exact bounded remediation

The only authorized next implementation work is the 13-row `GLOBAL_PROGRAM_FINAL_CLAUDE_REMEDIATION_MANIFEST_CODEX.csv`: eleven B3 program rows, the transitive B4 alias refusal, and the import-order P1. No research restart, MFNI work, frontend change, optimizer redesign, or unrelated cleanup is authorized.
