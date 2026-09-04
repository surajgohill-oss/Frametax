# Canonical Budget Parser / Classification Forensic Audit — Codex

**Audit date:** 2026-09-04  
**Mode:** read-only forensic audit  
**Corpus:** exactly the four production budgets named below; no fifth or historical project was admitted  
**Decision:** **NOT CERTIFIED** for canonical semantic integrity. Source extraction and persistence reconcile, but confirmed classification and downstream handoff defects remain.

The companion [line reconciliation](CANONICAL_BUDGET_LINE_RECONCILIATION_CODEX.csv) contains all 158 current persisted source rows. Every row was independently regenerated through the current parser/classifier and matched the persisted row; the findings below concern semantics and downstream consumption, not missing source extraction.

## 1. Locked canonical corpus

| Production | Canonical project ID | Current active budget-document ID | Document-version ID | Source file | Pages | Persisted lines |
|---|---|---|---|---|---:|---:|
| Little Utopia | `fa5cade5-0669-4816-bfe6-72146f8d3bae` | `b06185a9-9f48-41f7-9fa8-182a95926824` | `ee810c4f-8af3-4bdd-ba00-c5989c104172` | Little Utopia production budget PDF | 60 | 44 |
| F#K Valentine's Day | `6c6f1c13-2d49-4bbc-bafb-2a12efa93112` | `29419055-9720-4e77-a673-020e3a87e3c8` | `cf33eae1-aa4e-4e4e-80d2-ce737f5a373e` | `V-BRAT_V8_Greece_041224 TOPSHEET.pdf` | 1 | 34 |
| Bad Hombres | `4355ae88-a636-4c18-af60-ad73b2646124` | `14401d09-eaec-483b-a27d-eed9a7149fe7` | `06791475-82f0-4398-9cf1-19a7234bfce9` | `BadHombresBudget.v2.pdf` | 43 | 34 |
| Lips Like Sugar | `ab10b319-978e-44d3-9331-af2a5f2cccc2` | `6ae1bbec-f8f2-432b-a09f-9d9c8833944b` | `f2333b72-fcf7-4437-943f-4765357fe20e` | Lips Like Sugar production budget PDF | 52 | 46 |

All four named productions resolved to a current active parsed budget. The corpus was then frozen to these IDs.

## 2. Method and acceptance standard

For each locked document I:

1. opened the actual stored PDF and visually inspected the top sheet and relevant detail pages;
2. extracted PDF text with the current ingestion extraction path;
3. reran `parse_budget_from_text` with page boundaries and then `classify_parsed_items`;
4. compared the fresh result field-by-field to every persisted `BudgetLineItem`;
5. reconciled source gross total, persisted line sum, and the canonical economics input produced by `build_project_economic_inputs(..., read_only=True)`;
6. traced account-code/category consumption through canonical economics, production allocation, and allocation pricing.

No database row, production code, rule, or project data was changed. No external research was performed.

## 3. Preservation and total reconciliation

| Production | Source gross total | Fresh parser total | Persisted line sum | Canonical line sum consumed downstream | Result |
|---|---:|---:|---:|---:|---|
| Little Utopia | $4,364,393 | $4,364,393 | $4,364,395 | $4,364,395 | Parser exactly preserves the source's own $2 account-line rounding excess; gross total remains $4,364,393. |
| F#K Valentine's Day | $4,517,687 | $4,517,687 | $4,517,687 | $4,517,687 | Exact. Rebate and net-total rows are correctly excluded from gross spend. |
| Bad Hombres | $2,482,023 | $2,482,023 | $2,482,023 | **$2,387,641** | Parser preserves the total, but downstream canonicalization drops the unnumbered $94,382 contingency. |
| Lips Like Sugar | $11,983,654 | $11,983,654 | $11,983,654 | $11,983,654 | Exact. Tax-incentive and net-total rows are correctly excluded from gross spend. |

Fresh current-parser output matched all 158 persisted lines exactly: Little Utopia 44/44, F#K Valentine's Day 34/34, Bad Hombres 34/34, and Lips Like Sugar 46/46. No fresh parser warning was emitted.

The current computed parser marker is `budget-1.3.0+rules.ad443f926eb8`; all four documents retain `budget-1.3.0+rules.896907b5f1b3`. The marker is stale, although the current output is identical for this corpus.

## 4. Required F#K finance-fee verification

**PASS.** The source contains exactly one line:

`7901 FINANCE FEE : 12.5%` — **$453,583**

It is persisted exactly once as source row 31, classified `finance_costs`, and reproduced exactly once by the fresh parser. Canonical economics reports `source_budget_finance_usd = 453583`. The separate off-budget/scenario financing fact is null and is not used to create or replace this source line. The source finance fee is therefore neither omitted, duplicated, nor confused with scenario financing.

Lips Like Sugar receives the same separation: source accounts 6500, 6600, and 6700 total $1,700,000 of source finance costs, while off-budget/scenario financing remains null.

## 5. Confirmed defects

| ID | Severity | Production / amount | Exact defect | Consequence |
|---|---|---|---|---|
| BPI-001 | High | Bad Hombres — $94,382 | The parser correctly creates the unnumbered `CONTINGENCY` row, but canonical economics requires a leading account code and excludes it from `budget_lines`. | Gross budget is $2,482,023 while allocation/evaluation receives only $2,387,641. This is a downstream handoff defect. |
| BPI-002 | High | Lips Like Sugar — $1,033,615 across two 4900 rows | `spend_category_by_code` is keyed only by account code. The later `4900 MAIN AND END TITLES` row overwrites `4900 Total Fringes`. | The $1,023,115 fringe row can be consumed as `miscellaneous`; both real rows survive, but their shared-code category map is not row-safe. |
| BPI-003 | High | All four — $199,902 | Accounts named `PRODUCTION SOUND` are source Production/BTL accounts but keyword classification changes them to post `sound`. | Source production spend is moved into the post-production component. |
| BPI-004 | High | F#K — $72,573 | `7905 BOND : 2%` is persisted as BTL `miscellaneous`; the bond rule does not recognize bare `BOND`. | Completion-bond spend is routed as general/principal-photography spend. Little Utopia has the same structural defect at account 8200, presently $0. |
| BPI-005 | High | Bad Hombres and Lips Like Sugar — $174,000 | Legal/accounting rows are persisted as BTL `miscellaneous`. The enum/classifier cannot emit `legal_accounting` although downstream maps refer to that string. | Material legal/accounting spend is not semantically identifiable and defaults into principal-photography routing. |
| BPI-006 | High | Bad Hombres and F#K — $819,710 | Producer and director ATL accounts using `PRODUCERS`, `PRODUCERS UNIT`, `DIRECTOR`, or `DIRECTION` default to `miscellaneous`, non-labor, and non-fixed. | ATL role economics are preserved numerically but lose the producer/director and fixed-compensation semantics. Little Utopia has the same structural result on currently zero-value rows. |
| BPI-007 | Medium | Lips Like Sugar — $68,308 | Post-section `5900 Total Fringes` is classified `post_production`, because department text triggers the post rule before the fringe rule. | Payroll/fringe identity is lost. |
| BPI-008 | Medium | Bad Hombres $2,000; Lips Like Sugar $10,500 | Source post accounts `4500 PRODUCTION FILM/LAB/DAILIES` and `4900 MAIN AND END TITLES` are assigned Production/BTL `miscellaneous` from numeric ranges/keywords. | Post costs route outside post; the LLS line also participates in BPI-002. |
| BPI-009 | Medium | All four | Stored parser-version markers use the prior rules digest. | Provenance claims an older classifier version despite identical current output for the locked corpus. |

## 6. Category-by-category conclusions

| Area | Conclusion |
|---|---|
| Finance costs / lender fees / interest | F#K $453,583 and LLS $1,700,000 are preserved and classified correctly as source finance. They remain distinct from scenario financing. Little Utopia's combined zero-value `Finance & Legal` line maps wholly to finance, demonstrating a structural inability to split a mixed account. |
| Contingency | F#K, LLS, and Little Utopia are preserved/classified. Bad Hombres' unnumbered contingency is parsed but dropped downstream (BPI-001). The misspelling `Contigency` in Little Utopia is recognized. |
| Completion bond | LLS `BOND FEE` is correct. F#K's material bare `BOND` is incorrect; Little Utopia's zero-value bare `BOND` is structurally incorrect. |
| Insurance | All material top-sheet insurance rows are preserved and classified as insurance. |
| Legal / accounting | Underclassified where separately material; no canonical `SpendCategory` can represent the downstream `legal_accounting` label. |
| Payroll / fringes | Most explicit fringe rows are identified, but LLS has both the duplicate-code overwrite (BPI-002) and post-fringe precedence defect (BPI-007). Top-sheet department accounts also combine labor, materials, rentals, and fringes into a single row that one category/boolean cannot faithfully express. |
| Travel & Living | Aggregate totals are preserved. Bad Hombres, LLS, and Little Utopia source detail contains airfare, lodging/housing, per diem, vehicles/ground, baggage, and related subcategories, but canonical state retains only aggregate travel rows. F#K's supplied one-page top sheet contains only aggregates, so no finer source classification can be certified there. |
| Subtotals / headers | Department headers and group subtotals are excluded; final account totals are retained. Incentive/rebate and net-total rows are excluded from gross spend. The unnumbered loaded-cost contingency exception is successfully parsed but not successfully consumed. |
| Currency / numeric parsing | Dollar signs, commas, percentages in descriptions, parentheses, and zero values are parsed correctly for this USD-only corpus. Currency is set from ingestion/default metadata rather than proved from the source symbol, so this result does not certify non-USD documents. |
| Account-code parsing | Numbered source accounts are retained, including both legitimate LLS 4900 rows. The downstream category dictionary is not safe for duplicate account codes. |
| Source vs downstream semantics | Numeric extraction is strong, but source section semantics are overwritten by description/range rules and a number of `miscellaneous` rows later default to principal photography. |

## 7. Format-specific fragility

- The parser deliberately selects top-sheet account totals rather than detail subaccounts. This conserves totals, but creates composite rows that cannot distinguish labor, fringes, equipment, supplies, lodging, and per diem within one account.
- Multi-page parsing depends on page boundaries and textual top-sheet sentinels. Current production routing supplies page boundaries correctly; direct calls without them can scan detail text as if it were a top sheet.
- `source_page` provenance is comparatively complete for Bad Hombres and Little Utopia because their detail pages expose `Account Total` in the expected layout. It is largely unavailable for the one-page F#K source and for LLS's different same-line detail format. Values still reconcile, but page provenance is format-sensitive.
- Department inference from numeric ranges can contradict the source section, while later keyword rules can override the inferred department. Production Sound and the two source-post examples prove both failure modes.

## 8. Required remediation before certification

1. Preserve unnumbered parsed rows through canonical economics using stable line identity, not a mandatory account-code regex.
2. Replace account-code-only category lookup with row/line-item identity; duplicate codes must never overwrite one another.
3. Make source section/department authoritative unless an explicit, tested normalization rule proves otherwise.
4. Add canonical categories and classifiers for legal/accounting and explicit producer/director roles; correct bare bond and fringe precedence handling.
5. Decide and document whether canonical budgets are top-sheet economic summaries or detail-level QPE inputs. If QPE needs lodging, per diem, labor, and fringe distinctions, retain or link the relevant detail subaccounts instead of relying solely on composite top-sheet rows.
6. Refresh or explicitly migrate parser-version provenance only after the semantic defects are fixed and the four-budget acceptance corpus is rerun.

## Final gate

**CANONICAL_BUDGET_PARSER_INTEGRITY: FAIL**

- Source total preservation: **PASS**, with Little Utopia's source-authored $2 line-sum discrepancy faithfully retained.
- Line omission/duplication in parser persistence: **PASS** (158/158 exact).
- Semantic classification: **FAIL**.
- Source-to-downstream conservation: **FAIL** (Bad Hombres contingency).
- Duplicate account-code safety: **FAIL** (Lips Like Sugar 4900 collision).
- Source/scenario finance separation: **PASS**.
- Production code changed: **NO**.
- Database/project data changed: **NO**.
