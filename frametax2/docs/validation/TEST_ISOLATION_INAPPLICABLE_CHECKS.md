# Checks removed from the default suite as inapplicable to synthetic records

These assertions were written against the four REAL productions (Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar). They
cannot run on synthetic records and may not run against real projects (no real-project reads that evaluate, no writes). They are
**not passes**: they are not executed anywhere, and acceptance does not count them. Originals are recoverable at commit `6f94cfc0`
(`git show 6f94cfc0:frametax2/backend/tests/<file>`) and may be restored only under an explicit per-run authorization.

Why they are inapplicable now, with evidence:

* Their expected numbers are **frozen pre-refresh baselines**. The saved Little Utopia baseline NPC is now 3,065,099.30 while these tests pin
  3,791,333.30 (observed: `assert 3065099.3 == 3791333.3` in `tests/test_canonical_evaluation.py` after the budget refresh; the source-budget
  refresh changed line counts and totals, `PROJECT_OPEN_ITEM_RECOVERY.md`). Running them could only fail for a stale-baseline reason.
* They need the real projects' stored budgets, people and evaluated generations, which exist only in the acceptance database.

| File | Removed check | Frozen real value | Generic invariant now asserted on synthetic records (executed) |
|---|---|---|---|
| `test_final_optimizer_closeout_claude.py` | anchor contract matches the real baseline for all four productions | LU 573,059.70 / 3,791,333.30; FVD 1,445,659.84 / 3,072,027.16; BH 596,910.25 / 1,885,112.75; LLS 3,459,278.90 / 8,524,375.10 | contract equals the persisted baseline row (incentive, NPC, gross, PRICED), two budgets |
| same | no fabricated variance with no supplied incentive (four real) | none of the four has an incentive line | supplied/variance both None without a line; exact variance with one |
| same | LU `AUTHORITY_UNRESOLVED`, FVD `USER_FACT_REQUIRED` | real cultural-test states | contract exposes the baseline's own qualification state verbatim, with and without personnel |
| same | Bad Hombres / Lips Like Sugar leading structures unaffected | 596,910.25 / 3,459,278.90 | served baseline equals persisted row and contract |
| `test_production_page_integrity.py` | composition conserves to gross for the four real budgets | gross 11,983,654 / 2,482,023 / 4,364,393 / 4,517,687; 46 / 34 / 44 / 34 lines | conservation to gross, 3 synthetic budgets |
| same | department breakdown conserves (four real) | same | same test (department totals) |
| same | composition populated without a priced register (Bad Hombres, 34 lines) | 34 lines | populated composition with no pricing |
| same | Bad Hombres `CONTINGENCY : 5.0%` line | 94,382 | contingency line extracted and conserved |
| same | Little Utopia LA item (account 5000, 9,068) excluded from MU QPE | 9,068 | stated-outside account composed, categorized, excluded from QPE |

Not counted anywhere as passes. Acceptance for these invariants rests only on the synthetic equivalents listed in the last column.
