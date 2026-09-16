# Codex Gross-Up Authority Exhaustive Closeout

Status: `GROSS_UP_AUTHORITY_RESEARCH_EXHAUSTIVELY_CLOSED_READY_FOR_IMPLEMENTATION`

## Frozen lineage

- Starting SHA: `e7c8c28da5f8977f97e4a571241a9f5e382f5127`
- Branch: `codex/reinvestment-gross-up-authority-research`
- Physical census: **1250** records, unchanged
- Deduplicated authority questions: **400**
- Crosswalk rows: **1250**

## Result

Every physical record maps to exactly one question and one terminal economic disposition. The legacy generic blocker label has been eliminated. Public-authority silence is represented only as `AUTHORITY_SILENT_AGENCY_RULING_REQUIRED`, with program-specific proposed ruling language and safe zero-positive-gross-up behavior.

Question dispositions: `{'AUTHORITY_SILENT_AGENCY_RULING_REQUIRED': 262, 'FINANCING_SOURCE_ONLY': 63, 'QPE_CASH_PAID_ONLY': 11, 'EXCLUDED': 5, 'SELECTIVE_CONDITIONAL_UPSIDE': 56, 'NON_QPE_SUPPORT': 1, 'INACTIVE_OR_SUPERSEDED': 2}`.

No automatic positive QPE/FMV gross-up is authorized by the opened program authorities. Oregon OPIF is cash-paid actual Oregon expense only; California donated items remain excluded; Canadian/Ontario/New York payment-window rules remain cash-paid-only; reinvested incentive proceeds and recursive recalculation remain unsupported unless an administrator issues a written ruling.

## Claude machine-readable instructions

`CODEX_REINVESTMENT_GROSS_UP_RESEARCH_QUESTION_CROSSWALK.csv` owns physical-record inheritance. `CODEX_REINVESTMENT_GROSS_UP_ECONOMIC_DISPOSITIONS.csv` owns the per-record instruction: economic type, QPE/gross-up result, financing offset, NPC handling, assistance, stacking, same-cost, UI disclosure, missing fact and expected implementation area.

Implementation rules:

1. Wire `QPE_CASH_PAID_ONLY` only to actual documented eligible payments; never nominal/FMV support.
2. Keep every `AUTHORITY_SILENT_AGENCY_RULING_REQUIRED` path visible but zero-valued for gross-up and non-recommended.
3. Treat selective funds as conditional upside and only use contracted award amounts.
4. Record nonrepayable support once in financing/NPC; debt, deferrals, equity and recoupable advances are not free NPC reductions.
5. Never recursively credit reinvested incentive proceeds without explicit authority.
6. Split the canonical BC DAVE identity by domestic FIBC versus service PSTC pathway before stacking.
7. Supersede `ca_nb_film_tax_credit`; current LIFT is selective funding, not the obsolete tax credit.
8. Preserve ordinary cash-paid travel rules separately from contributed/subsidized travel.
9. The 53 previously unwired contribution/category paths inherit their crosswalk disposition; none may use the legacy FMV-to-face fallback.

Stacking results: `{'PERMITTED_CONDITIONAL': 12, 'PERMITTED_WITH_FEDERAL_ASSISTANCE_REDUCTION': 5, 'PERMITTED_CONDITIONAL_PATHWAY_SPLIT_REQUIRED': 2, 'AUTHORITY_SILENT_AGENCY_RULING_REQUIRED': 5, 'INACTIVE_OR_SUPERSEDED': 2, 'PERMITTED_WITH_MUTUAL_ASSISTANCE_REDUCTION': 2, 'PROHIBITED_PRODUCTION_TYPE_ELECTION': 2, 'PERMITTED_WITH_QSAPE_REDUCTION_AND_PUBLIC_AID_CAP': 1}`. Structural-node results: `{'AUTHORITY_SILENT_AGENCY_RULING_REQUIRED': 31, 'POSITIVE_STRUCTURAL_SCOPE_CONFIRMED': 42, 'INACTIVE_OR_SUPERSEDED': 2, 'SELECTIVE_OR_CONDITIONAL_OVERLAY': 9, 'SAME_ECONOMIC_IDENTITY': 6}`.

This branch changes validation artifacts and the validator only. No production code, optimizer rule or production database row is modified.
