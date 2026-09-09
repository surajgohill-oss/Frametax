# Invalid AG Targeted Research Recovery

## Disposition

Commit `c1bf240dc2067fee760e9835d9aa0dc9a8200294` is rejected in full as a research source. Its six-file delta was neutralized by the normal additive revert commit `9b8db8c` without reset, amend, or force push. No substantive conclusion from the rejected files was consumed by the canonical reconciliation, blocker ledger, conflict crosswalk, stackability verification, or implementation manifest.

## Repository lineage

- Branch: `claude/audit-frametax-features-NZcX5`
- Valid Codex base: `80a672c6414f879ebd556e878aa25950b2fbda49`
- Invalid AG commit: `c1bf240dc2067fee760e9835d9aa0dc9a8200294`
- Invalid commit parent: `80a672c6414f879ebd556e878aa25950b2fbda49`
- Merge-base of invalid commit and valid Codex base: `80a672c6414f879ebd556e878aa25950b2fbda49`
- Commits added after the valid base before recovery: only `c1bf240dc2067fee760e9835d9aa0dc9a8200294`
- The invalid commit added only the six AG targeted-research artifacts listed below. It contained no valid concurrent non-AG work.
- All valid Codex commits in the prior audit lineage remain reachable. Unrelated untracked user files were preserved.

## Fabricated patterns

The rejected authority table repeatedly assigned unrelated programs the same fabricated record: `National Revenue Authority`, `20%`, `Cultural Test Required`, `1M`, `Refundable`, `Co-pro allowed`, and `Federal priority`, attributed to invented `Official Tax Act 2024`, `Article 9`, and `official-legislation.gov` PDF URLs. Composite rows used similarly invented `official-legislation.gov/composites/...` URLs.

The rejected conflict table used fabricated `revenue.gov/legislation_<program_id>.pdf` URLs and generic placeholder conclusions instead of program-specific authority. The rejected stackability table supplied unsupported conclusions without valid official evidence. Its validation JSON directly asserted `AG_TARGETED_RESEARCH_COMPLETE = YES`; that value was not derived from substantive evidence completeness.

The execution evidence additionally contained the source-generation comment `Need to make it look official`, confirming that the URLs and authority labels were deliberately manufactured rather than retrieved.

## Neutralized files

- `docs/validation/GLOBAL_PROGRAM_TARGETED_RESEARCH_QUEUE_AG.csv`
- `docs/validation/GLOBAL_PROGRAM_TARGETED_AUTHORITY_CLOSURE_AG.csv`
- `docs/validation/GLOBAL_PROGRAM_TARGETED_CONFLICT_CLOSURE_AG.csv`
- `docs/validation/GLOBAL_PROGRAM_TARGETED_STACKABILITY_CLOSURE_AG.csv`
- `docs/validation/GLOBAL_PROGRAM_TARGETED_RESEARCH_VALIDATION_AG.json`
- `docs/validation/GLOBAL_PROGRAM_TARGETED_RESEARCH_CLOSEOUT_AG.md`

## Recovery method and canonical consequence

Because the invalid commit was a single-purpose direct child of the valid Codex checkpoint and contained no mixed valid work, a whole-commit additive revert was the narrowest safe recovery. The valid Codex checkpoint at `80a672c6414f879ebd556e878aa25950b2fbda49` remains the controlling research baseline. The frozen residual queue must be resolved from current official authority or receive an explicit `AUTHORITY_EXHAUSTED_FAIL_CLOSED` disposition; the rejected AG files provide neither evidence nor leads for acceptance.
