# NY AG bde0fee adjudication — 2026-10-10

Status: AUDIT TOTALS NOT ACCEPTED; confirmed rule discrepancies retained for repair. No production code, project data or evaluation changed. Scope: investigate AG's supplied NY output and compare primary text/source accounts; not full NY implementation or anchor acceptance.

Evidence submission: /Users/Suraj/.codex/attachments/fe20c5fc-4129-41a5-ae19-3fa608b1eaeb/Pasted text.txt. AG reports all four source budgets/158 rows and commit bde0fee. A passing self-authored validator is not independent acceptance.

Primary sources checked 2026-10-10:
- NY Tax Law 24, revision 2025-07-11: https://www.nysenate.gov/legislation/laws/TAX/24
- Correct film post section 31*2, revision 2025-07-11: https://www.nysenate.gov/legislation/laws/TAX/31%2A2 (plain /31 opens a different Excelsior Jobs statute).
- https://esd.ny.gov/new-york-state-film-tax-credit-program-production
- https://esd.ny.gov/new-york-state-film-tax-credit-program-post-production

## Implementation allegations — all retained, with bounded dispositions

| Finding | Investigation result | Owner / next action |
|---|---|---|
| DISC-NY-001 production/post stacking | CONFIRMED rule conflict: film post 31(a)(1) excludes a taxpayer eligible for 24 with respect to that film; existing stacking registry permits distinct-cost pairing. Distinct invoices do not eliminate the film-level bar. | Canonical stacking owner; correct pair and independently verify affected structural paths. No exact persisted blast radius established. |
| DISC-NY-002 post gateway | CONFIRMED source-config conflict: fixed $1m misses lesser-of-$1m-or-75% non-VFX branch. Statute separately admits VFX/animation on lesser of $500k or 10% worldwide VFX/animation. | Canonical requirements/rate owner; implement separate component gateways and temporal selection. All 82 rejection causes and generation provenance still unverified. |
| DISC-NY-003 post rate | CONFIRMED geographic distinction: 30% MCTD, 35% elsewhere; source-config flat35 cannot confirm downstate35. AG omits additional eligible county labour uplift. | Rate/subset owner; test geographic rate and labour subset independently. Actual overpayment not established from an unknown facility county. |
| DISC-NY-004 ATL cap | Source-config explicitly marks ratio unmodeled. Current section24 confirms 40% of OTHER qualified costs, includes composers and excludes background actors without scripted lines from this ATL cap; no more than two producer salaries qualify. | Qualification owner; trace actual enforcement and roles, independently calculate cap on an identical allocation. Exact AG dollar impact rejected pending repaired bases. |
| DISC-NY-005 open doctrine | OPEN_DEFAULT_INCLUDE alone is not proof of a defect: explicit excluded-category rules may still apply. Need per-category and actual allocation/register reproduction. | Spend-rule owner; verify enumerated eligible/excluded expenses against current cost schedules. Do not blanket-change doctrine solely from its label. |
| DISC-NY-006 broad uplift ceiling | Source-config uses whole-program50/60 bands; law supports scoring subset and distinct county labour/non-labour predicates; Production Plus has separate company/application facts. | Subset pricing owner; distinguish disclosed bound from confirmed incentive and correct eligible subset economics. AG's full-upstate assumption can support broader qualifying cost uplift if predicates proven; do not dismiss all40 scenarios. |
| DISC-NY-007 refundability | Reported unknown metadata requires reconciliation with section24(c)/official tax guidance; refund timing separate from classification. | Financial metadata owner; verify complete current payment contract before claiming cashflow impact. |

## Failures in AG's own source/calculation evidence

| ID | Observed failure | Evidence-backed disposition / remaining work |
|---|---|---|
| NY-A01 | LLS source financing dropped | CONFIRMED: retained source accounts6500=$450,000;6600 BRIDGE=$250,000;6700 BANKING FEE=$1,000,000. AG excludes only$450,000 despite claimed financing exclusion, omitting$1.25m. Recalculate qualifying OTHER base and ATL cap, not just subtract from final incentive. Source costs must remain in gross/NPC exactly once. |
| NY-A02 | LU gross/NPC uses leafsum | CONFIRMED: AG table uses$4,364,395; declared controlling gross is$4,364,393. Preserve documented$2 source variance, use declared gross for NPC. |
| NY-A03 | Production sound treated as post | CONFIRMED submitted script selects any SOUND label as post, including source production sound LU$69,532/FVD$26,458/BH$16,845/LLS$87,067. Repair explicit on-set versus post distinction before standalone-post bases/gateways. |
| NY-A04 | BH hybrid versus relocation comparison | CONFIRMED methodological mismatch: persisted NY allocation$2,369,065 compared with all-source gross$2,482,023 full-relocation control. Claimed$367,451.52 overstatement not established. Reconstruct identical selected allocation/components, rules/date/FX and candidate generation first. |
| NY-A05 | Production county definition / day boundary | CONFIRMED against current primary text: specified production county list includes Dutchess/Orange/Putnam despite those counties belonging to MCTD. Production uplift county list differs from post35 geography. ESD says MORE THAN50% days for non-labour expansion; >=50% is insufficient boundary. Labour limb and non-labour limb have different gates. |
| NY-A06 | Post/VFX gateway conflated | CONFIRMED: all-post75% arithmetic fails to isolate VFX10%/$500k and ordinarypost75%/$1m. Rebuild bases then test facility/applicable approval facts. No automatic actual eligibility merely from hypothetical100% relocation. |
| NY-A07 | Post labour uplift omitted | CONFIRMED ESD post page includes additional10% eligible county labour; AG post table stops at30/35 without modeling/disclosing that limb. Missing actual labour/company/facility facts remain conditional. |
| NY-A08 | Current versus 2023 individual cap | UNRESOLVED: AG imports$500k/person2023 rule without a current effective-date analysis; current24 text inspected contains other roles/aggregate rules. Retrieve versioned guidelines and enactments before applying or deleting this cap. |
| NY-A09 | Blankets / role facts / certification | UNRESOLVED: expenses excluded using broad keywords; composer/background/two-producer caps, invoices, facility/shoot days and application facts not fully reconstructed. Counterfactual budgets are planning scenarios, never verified claims. |
| NY-A10 | Generation and rejection provenance | UNRESOLVED: broad historic aggregate queries omit current-generation fingerprint/version and mix different candidate structures. Need bounded reuse-only snapshot per exact candidate and failure reason. Never cold-evaluate solely to find a comparison. |

Owner for NY-A01..A10: Codex adjudication / AG evidence correction. Required next submission: repaired 158-row source-conserving matrix, exact rule/date citations, identical-allocation comparisons, and dollar bridges retaining unsupported remainder. No production totals accepted. Anchor Q08/Q10/Q11/Q15 and Greece residual remain open. NY investigation does not supersede anchor closeout.
