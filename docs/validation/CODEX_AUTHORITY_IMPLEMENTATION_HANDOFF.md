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

## 2026-09-16 all-program cap-headroom delta

Status: `RESEARCH_INCOMPLETE_FAIL_CLOSED`

The all-program reconciliation now covers 659 physical canonical records / 658 unique economic identities. It confirms 17 programs with at least one official cap rule, but does not authorize any automatic fee gross-up. All unresolved identities remain zero-valued and are enumerated in `CODEX_CAP_HEADROOM_AGENCY_RULING_QUESTIONS.csv`.

Implementation must consume `CODEX_CAP_HEADROOM_CATEGORY_RULES.csv` only as ceilings and gates. It must not set recognized incremental QPE equal to headroom. Canada CPTC and Ireland Section 481 are reviewed paths with express paid-by-deadline rules; their distinct deadlines and all other conditions remain program-specific. Actual-payment programs remain cash-paid-only. Paid-and-reinvested flows must be represented separately and counted once. No recursive credit-on-credit behavior is authorized.

## 2026-09-17 forensic gross-up transaction addendum

Status: `RESEARCH_COMPLETE_WITH_DOCUMENTED_AUTHORITY_GAPS_NOT_IMPLEMENTATION_PERMISSION`

The 658-identity transaction crosswalk is `CODEX_GROSS_UP_AUTHORITY_CROSSWALK.csv`. Ireland Section 481 corrects the earlier Canada-only deadline statement: current Revenue guidance permits deferred fees only when paid no later than four months after completion and describes 15%/10% producer-fee parameters, real-service, actual-cost, related-party, arm’s-length and records requirements. It does **not** confirm the complete paid-then-reinvested, receivable-capitalization, circular-payment or loan-funded gross-up chain.

Implementation remains fail-closed: use fixed-point arithmetic only to disclose theoretical ceiling headroom; never label it QPE or NPC benefit; require real project facts and, for the unresolved complete chain, a written ruling. Preserve every payable, loan and equity flow exactly once.

## 2026-09-17 final labour / stacking / structural authority consolidation

Status: `FINAL_AUTHORITY_RESEARCH_CONSOLIDATED_WITH_DOCUMENTED_RULING_GAPS`

This delta did **not** reopen the completed 658-program gross-up crosswalk. It closed the frozen five stacking questions, reviewed all 31 frozen structural nodes, and added the single permitted labour-basis artifact, `CODEX_EXECUTABLE_LABOUR_BASIS_AUTHORITY_MATRIX.csv`.

### Labour basis

The current executable registry contains **21 labour-affecting programs**: a program is included only when its live formula is labour-only, has a separate labour/payroll rate or uplift, has a labour cap, or uses labour as an eligibility ratio. The matrix records ATL/BTL, residence/citizenship, service location, payee/look-through, payment/deferral, contingent compensation, related-party/FMV, assistance and cap treatment for every one. Seventeen are authority-verified with project-fact gates; four are selective/conditional and must use a written award or agreement. No title, local SPV, payroll-company address, or local payment by itself proves qualifying labour. Person, service location, legal payee/look-through, actual payment and program-specific assistance must all be evaluated.

### Five frozen stacking questions — all resolved

- `ca_federal_cptc::ca_mb_film_video_credit` and `ca_federal_pstc::ca_mb_film_video_credit`: legally coexistent, conditional on each program's eligibility and the Manitoba salary/production-cost election. Manitoba excludes the federal film credit from its assistance definition; the Manitoba/provincial amount is assistance in the federal net base/QCLE. Calculate/estimate the Manitoba claim, allocate assistance, then calculate the federal credit.
- `ca_federal_cptc::ca_ns_production_incentive_fund` and `ca_federal_pstc::ca_ns_production_incentive_fund`: legally coexistent only after a selective Fund award/agreement. The Nova Scotia guidelines permit federal tax credits in the financing plan; a contracted/receivable Fund award is government assistance reducing the applicable federal base. Never price an unawarded Fund amount.
- `ca_federal_cptc::ontario_computer_animation_and_special_effects_tax_credit_ocase`: conditional coexistence. OCASE permits combination with Ontario film credits and excludes federal/provincial film tax credits from the OCASE assistance grind, but CPTC still applies its own assistance rule. Trace the legal OCASE claimant and recipient: a separate VFX service-company credit is not automatically producer assistance or producer financing.

Primary authority: CRA [assistance policy](https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/film-media-tax-credits/film-video-production-services-tax-credit-program/application-policies/application-policy-assistance.html), Manitoba [business credits](https://www.gov.mb.ca/finance/business/ccredits.html) and [Income Tax Act film provisions](https://web2.gov.mb.ca/laws/statutes/archive/i010%282023-05-29%29.php?df=2023-04-03), Nova Scotia [Fund guidelines](https://cch.novascotia.ca/sites/default/files/inline/documents/ftpif/nsfpif-guidelines.pdf), and Ontario Creates [OCASE guidelines](https://www.ontariocreates.ca/tax-incentives/ocase/ocase-guidelines).

### Structural-node result

The 90-node ledger now ends at: **54** positive structural-scope confirmations, **15** authority-silent agency-ruling requirements, **13** selective/conditional overlays, **6** same economic identities and **2** inactive/superseded nodes. Of the frozen 31 gaps, 16 moved to positive or selective/conditional treatment and 15 remain documented ruling gaps:

`ae_dxb_dpip`; `al_cash_rebate`; `ch_pics_national_rebate`; `cr_tax_return_incentive`; `eg_empc_cashback`; `ge_film_rebate`; `gh_film_tax_incentive`; `kz_investment_subsidy`; `me_cash_rebate`; `mk_cash_rebate`; `mn_production_incentive`; `pa_film_rebate`; `se_production_rebate`; `ua_cash_rebate`; `uz_film_rebate`.

Each retained row states the exact administrator question and safe behavior. Search results, secondary summaries, adjacent programs and industry convention were not used to fabricate legal coexistence. These rows remain visible/non-recommended and cannot automatically generate a structure or stack until written authority answers the row's question.

### REG-5 — New York same-jurisdiction treatment

The generic “same cost prohibited / distinct costs allowed” runtime statement is too broad. ESD's Film Tax Credit Program Guidelines say a production-credit claimant may include qualifying New York post costs in the production credit, and expressly prohibit applying for both credits for the **same qualified post-production costs**. The same guidance describes the separate post-production credit as available where the project was filmed predominantly outside New York or was ineligible for the production program. Therefore:

1. same qualified post cost in both credits: `PROHIBITED`;
2. production credit including its own qualifying New York post: `PERMITTED_WITHIN_PRODUCTION_CREDIT`;
3. same project claiming both programs on allegedly disjoint post pools: `AGENCY_RULING_REQUIRED` unless ESD pre-approves the facts.

Authority: ESD [Film Tax Credit Program Guidelines](https://www.esd.ny.gov/sites/default/files/4-Film-Credit-Guidelines-W-Appendix05102023.pdf), pages 5-8. This is an implementation correction requirement, not a production-code change in this research branch.

### HO-009 — NZ / BC / NY component compatibility

`nz_spg_international + ca_bc_dave + us_ny_post_production_credit` is **not** proven merely because the components are in different countries. Each leg is separately possible: NZSPR covers certified QNZPE including PDV; BC DAVE covers eligible DAVE remuneration to BC-based individuals; NY post covers qualified post work performed in New York. But no joint authority confirms the full three-leg allocation, applicant relationships, assistance treatment or absence of contractual whole-project exclusivity for a particular production. HO-009 is therefore `AGENCY_RULING_REQUIRED_FOR_COMBINED_STRUCTURE`: retain each component separately, require a cost/person/vendor allocation that sums once to the project budget, and do not recommend the three-program structure without written administrator/production-counsel confirmation. Authority inputs: [NZFC International Rebate](https://www.nzfilm.co.nz/incentives/rebate-international-nzspr), [BC film and television credit](https://www2.gov.bc.ca/gov/content/taxes/income-taxes/corporate/credits/film-tv), and the ESD guideline above.

### Multi-principal, treaty, fund and dominance rules

- Treaty status supplies national treatment only to the extent of the certified treaty and each co-producer's contribution/share. It does not authorize two full-budget principal claims, a multi-principal structure, or a sum of allocations exceeding 100%. A non-treaty cross-border component is a service allocation, not an official co-production.
- A grant/fund is never formulaically guaranteed. Only an executed award/agreement enters economics, exactly once. Grants, subsidies and forgivable amounts reduce a credit base only where that program's authority says so; assistance order is claimant- and program-specific. A loan, equity contribution or recoupable advance is not free NPC reduction.
- A dominance proof is canonical only inside the same proven feasible set: identical project facts and cost allocation, independently satisfied program eligibility, legally permitted coexistence, correct assistance order, caps, monetization and transaction costs. If any eligibility or coexistence premise is `AGENCY_RULING_REQUIRED`, the dominance result is conditional and cannot support `RECOMMENDED`.

### Implementation boundary

No production code, database row, rule table or optimizer behavior changed. The artifacts are an authority implementation handoff. Implementation must preserve all ruling gaps and the REG-5/HO-009 restrictions above; it may not convert silence into permission.
