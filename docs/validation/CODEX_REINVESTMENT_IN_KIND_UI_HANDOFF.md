# CineGlobe Reinvestment / In-Kind Opportunity UI Handoff

Status: `RESEARCH_ARTIFACT_READY_NO_PRODUCTION_CHANGE`

This handoff reconciles the existing Codex gross-up, cap-headroom, deferment, contribution and authority artifacts at commit `981d5cab23c5fc5555d97ad78b9da89813c9492d` with the Ireland transaction analysis in `claude/global-optimizer-remediation@ddfceb3efc078fe144a8c872b6a0628f3707c5eb`. It does not reopen the completed 658-program search and does not authorize a new calculation path.

## Inventory

The companion ledger contains **46 mutually exclusive candidate records**:

| Classification | Count | Meaning |
|---|---:|---|
| `SUPPORTED_OPPORTUNITY` | 2 | Authority supports the mechanism, but only actual evidenced project spend/transactions enter economics. |
| `CONDITIONAL_OPPORTUNITY` | 21 | The category/path exists; project facts, payment, award, cap and relationship conditions must be satisfied. Manual proposed opportunity starts at $0. |
| `RULING_OR_COUNSEL_REQUIRED` | 8 | A material transaction element is not answered by authority. Keep visible at $0 and show the exact question. |
| `MANUAL_ONLY` | 12 | Informational cap utilization or non-QPE replacement-cost support. It never changes guaranteed incentive automatically. |
| `PROHIBITED` | 3 | The asserted QPE/financing treatment is expressly excluded or structurally invalid on the stated facts. |

Actionable supported/conditional programs are: `ny_state_film` (US-NY), `hu_hipa_rebate` (Hungary), `mt_mfc_rebate` (Malta), `cy_film_rebate` (Cyprus), `us_ga_film_credit` (Georgia), `us_il_film_production_services_credit` (Illinois), `tw_bamid_rebate` (Taiwan), `uk_avec` (United Kingdom VFX), `ca_federal_cptc` (Canada), `it_tax_credit_foreign` (Italy), and `ie_section_481` (Ireland).

## Required UI behavior

Render a distinct **Opportunities & Contributions** section. Do not fold these records into guaranteed incentive, Recommended ranking or canonical NPC.

Every row/card must show:

- program and jurisdiction;
- mechanism and eligible category/cap;
- authority classification and risk colour;
- conditions and missing project facts;
- payment/deferment deadline;
- arm's-length/related-party rule;
- in-kind/FMV treatment;
- authority links;
- separate amounts for `eligible_qpe`, `financing_contribution`, and `npc_replacement_cost_benefit`;
- the explanation of why later investment does or does not affect the original expense.

Input rules:

1. `manual_opportunity_amount` defaults to `$0` for `CONDITIONAL_OPPORTUNITY`, `RULING_OR_COUNSEL_REQUIRED` and `MANUAL_ONLY`.
2. A `SUPPORTED_OPPORTUNITY` still does not invent spend. It may calculate from already-evidenced canonical budget facts, otherwise it remains $0.
3. `RULING_OR_COUNSEL_REQUIRED` cannot be promoted by a user toggle. Require a ruling/counsel evidence attachment and human acceptance workflow before any future implementation considers economics.
4. `PROHIBITED` has no amount control for QPE or incentive. A separate manual replacement-cost disclosure may exist only where the ledger expressly allows it.
5. Selective programs require an award/agreement amount; headline maximums are never default values.

## Canonical accounting model

The three economic axes must remain separate:

| Axis | Permitted value | Never do |
|---|---|---|
| Eligible QPE | Actual authority-compliant cost, after payment, territoriality, relationship, assistance and cap rules | Treat cap headroom, donated FMV, a payable, or reinvested proceeds as spend |
| Financing contribution | Actual cash/equity/grant/support received, with debt and recoupment preserved | Count the same cash as both cost and free financing; erase a loan liability |
| NPC replacement-cost benefit | User-evidenced nonrepayable support/avoided cash cost, once, with assistance effects | Add the same support to QPE or recursively credit the incentive it generates |

Invariant: each real cost, cash flow, payable, liability and support item is represented once. Credit proceeds can finance later real spend, but the proceeds themselves are not QPE. No fixed-point or credit-on-credit calculation is authorized.

## Ireland Section 481 correction

The old blanket `AUTHORITY_SILENT_RULING_REQUIRED` treatment for every paid-then-reinvested fee is superseded by a tiered transaction test:

- **Supported:** an unrelated vendor earns an arm's-length fee for real services, receives genuine cash payment, and only afterward makes a genuinely independent at-risk equity subscription. The original fee remains tested as a cost; the subscription is financing. There must be no contract, side letter, understanding or price inflation linking the legs.
- **Conditional:** a deferred genuine fee can qualify when genuinely paid no later than four months after completion. A book entry, set-off or receivable capitalization is not treated as payment. Apply the unrelated/related test after payment.
- **Ruling/counsel required:** a related-party producer/overhead fee followed by reinvestment into the same production. The fee itself may qualify under WEN, arm's-length, 15%/10% parameter and connected-party disclosure rules, but the complete chain raises s.481(2A)(f)(ii) and s.811C issues not resolved by published authority.
- **Prohibited on stated facts:** the same fee proceeds are recycled as the required non-S481 cash contribution, or the fee is inflated/contractually conditioned on reinvestment. Timing alone does not cure circularity.
- **Ruling required:** donated/in-kind goods or services asserted at FMV. Current authority supports actual incurred cost, not nominal FMV.

The 15%/10% producer-fee percentages are reasonableness parameters, not automatic spend and not absolute caps; higher fees may be substantiated. State-aid cumulation remains a separate budget-level constraint.

Primary/recovered authority chain: Revenue TDM Part 15-02-04 (reviewed August 2026), Film Regulations 2019, TCA 1997 sections 481 and 811C, C&AG 2018 Report Chapter 18, EC Decision SA.53399, and the source/evidence checklist in the two Claude artifacts at `ddfceb3efc078fe144a8c872b6a0628f3707c5eb`.

## Cap-headroom rule

Cap headroom is a planning diagnostic only:

`unused_headroom = max(0, applicable_category_cap - actual_authority_compliant_cost)`

It means additional genuine expenditure might fit under a ceiling. It is never itself QPE, an incentive, financing or NPC benefit. The UI must pair every headroom figure with the real-service/payment facts required to use it.

## In-kind, sponsorship, discounts and loaned facilities

- Where authority says actual paid cost only, an in-kind item's tax-credit QPE is zero. The UI may show a separate replacement-cost estimate, default $0, if the support is real and nonrepayable.
- Vendor discounts, rebates, credits, waivers and forgiveness reduce actual cost/QPE. They do not create FMV headroom.
- California Program 4.0 donated items are expressly non-qualified.
- For the six high-value unresolved programs in the ledger (`bc_pstc`, `georgia_eiia`, `la_film_production`, `nm_film_production`, `or_opif`, `qc_film_production`), keep the possible support visible but at zero QPE until the stated administrator question is answered.
- A loaned facility or barter arrangement has no generic FMV rule. Treat it exactly like in-kind support unless the selected program has an express valuation rule.

## Acceptance checks for implementation

An eventual implementation is acceptable only if tests prove:

1. all 46 rows are reachable in the opportunity UI;
2. classification is single-valued and one of the five allowed values;
3. conditional/manual/ruling-required defaults are exactly $0;
4. no such default affects guaranteed incentive, Recommended rank or canonical NPC;
5. actual eligible QPE, financing and replacement-cost benefit remain separate fields;
6. the same transaction ID cannot be counted in more than one axis without an explicit offset/reconciliation entry;
7. Ireland exercises all five tiered outcomes above;
8. authority links, conditions and missing facts are displayed;
9. prohibited rows cannot enter economics;
10. no recursive calculation uses incentive proceeds as QPE.

## Research boundary

Targeted reconciliation was limited to the cross-branch Ireland memo/checklist and the already-retained primary authorities/evidence IDs for the 29 cap-category rows and high-value in-kind candidates. No jurisdiction-wide or 658-program research was repeated. The ledger retains **8** candidate-level `RULING_OR_COUNSEL_REQUIRED` records; they are intentional, documented authority gaps rather than unfinished inventory work.
