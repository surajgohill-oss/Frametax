# CineGlobe fail-closed authority gate specification (Codex)

Status: **binding implementation specification; not yet runtime acceptance**.

## Required precedence

Create one canonical helper in `backend/app/data/authority_coverage_registry.py`, for example `economic_block_for_program(program_id)`, returning a structured block result. It must canonicalize aliases first and recognize accepted authority-exhausted, display-only, retired, and duplicate identities from runtime-owned data. Documentation CSVs are not runtime inputs.

At the first executable line of `resolve_program_rate()`, before `_RULES_BY_PROGRAM` lookup or condition evaluation, invoke that helper. A blocked identity returns no rate. Add `RATE_FAILURE_AUTHORITY_EXHAUSTED = "AUTHORITY_EXHAUSTED_FAIL_CLOSED"`; `classify_rate_resolution_failure()` must run the identical preflight first and emit that reason rather than `NO_RATE_RULES` or `STATUTORY_CONDITIONS_UNMET`.

The same helper must preflight every member of `price_program_pair_stack()` and `price_program_group_stack()`. If any member is blocked, no automatic stack result is created and the rejection is preserved by `canonical_evaluation.py`. Alias spellings inherit the canonical block. Fail-closed status always outranks a stale `RateRule`, doctrine record, project reference, or stacking edge.

Display-only discretionary programs may remain visible through conditional discovery, but their guaranteed incentive and guaranteed NPC contribution are zero. The current conditional architecture has no separately labelled probability-adjusted economics lane, so expected value must not enter NPC.

## Required negative controls

1. Inject a stale `RateRule` for a fail-closed canonical ID: resolution returns `None` and classification returns `AUTHORITY_EXHAUSTED_FAIL_CLOSED`.
2. Repeat through a legacy alias whose canonical target is blocked.
3. Attempt pair and group stacks containing a blocked identity: both reject with the same explicit reason.
4. Confirm a display-only discretionary candidate remains visible but contributes zero guaranteed value.
5. Confirm an unrelated verified rule still prices.
6. Confirm no loader or registry-import order can reactivate the corrupted rule.

These tests are adversarial state-corruption tests. Absence of a slug is not acceptance evidence.
