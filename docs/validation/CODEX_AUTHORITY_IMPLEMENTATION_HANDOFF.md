# Codex Authority Implementation Handoff

Status: `GROSS_UP_AUTHORITY_RESEARCH_COMPLETE_WITH_DOCUMENTED_GAPS`

## Frozen provenance

- RESOLVED_SOURCE_SHA: `600deb64dfe18fc339839de91a461c561274a29f`
- CODEX_BRANCH: `codex/reinvestment-gross-up-authority-research`
- HEAD_BEFORE: `600deb64dfe18fc339839de91a461c561274a29f`
- Corrected stacking oracle: `940ef8f78bb69bb343a954e34f6e9c2151489fd0`
- Retrieval date: 2026-09-16

## Outcome

The census contains **1250** individually preserved records: {'QPE_CATEGORY': 136, 'SPEND_TREATMENT': 1000, 'FUND_ECONOMICS': 103, 'STATIC_CODE_RECORD': 10, 'ZERO_ROW_TABLE_ASSERTION': 1}. It contains 1278 retrieval rows, including 28 primary official retrievals. No current record is authorized for automatic positive QPE gross-up. This is a negative safety conclusion, not proof that every program permanently prohibits all contributed value.

The machine-readable per-record implementation instruction is `CODEX_REINVESTMENT_GROSS_UP_ECONOMIC_DISPOSITIONS.csv`. It specifies economic type, gross-up/QPE treatment, valuation, financing/NPC offset, assistance/stacking/same-cost treatment, conditionality, disclosure, missing fact, evidence and expected implementation area for every census row.

## Locked calculation handoff

When a future authority-supported record is enabled: (1) add only authority-recognized incurred/paid cash or FMV to gross production cost; (2) include only the expressly eligible portion in QPE; (3) calculate incentive once; (4) record the funding/contribution as financing or support exactly once; (5) do not treat a debt or deferral as free support; (6) do not recursively credit incentive proceeds; and (7) keep travel/logistics outside QPE unless the program expressly includes it.

The live bridge currently exposes zero-valued, user-fact-required opportunities. The legacy calculator's FMV-to-face fallback is not an authority-backed valuation rule. `production_contributions` contains zero rows, so no live project economics were altered.

## Authority outcomes

- Economic dispositions: {'AUTHORITY_BLOCKED': 1127, 'FINANCING_SOURCE_ONLY': 51, 'NON_QPE_NPC_REDUCTION_ONLY': 5, 'CONDITIONAL_NPC_REDUCTION': 56, 'DISCLOSURE_ONLY': 10, 'INACTIVE': 1}
- Positive automatic reinvestment gross-up: 0
- Positive automatic in-kind gross-up: 0
- Corrected stacking interactions: 31 rows; every oracle interaction preserved. Pair-specific Canadian gaps remain blocked rather than inferred from a generic federal assistance rule.
- Structural nodes: 90 rows; every node classified. `AUTHORITY_RESEARCH_REQUIRED` remains an explicit classification, not silent omission.
- Manual checks: 1250 rows.

## Material resolved rules

- NSW excludes service-provider payments offset by reinvestment or another financial contribution from qualifying NSW PDV spend.
- Canadian federal credit bases are reduced by applicable assistance; CPTC/PSTC labour is subject to incurred/paid rules.
- Ontario deferrals reduce claims and sponsorship may be assistance absent an FMV exchange.
- California Program 4.0 expressly labels donated items and financing fees non-qualified.
- New York accepts only paid costs by the applicable completion date; travel is location-conditional.
- Georgia expressly includes only specified travel/living items under territorial/vendor rules.
- South African public support is subject to the documented QSAPE reduction and 80% public-funding ceiling.

## Documented gaps and implementation gate

The unresolved ledger is deliberate. No generic gross-up permission was found for the 11 database programs carrying `in_kind`, `reinvestment`, or `deferment` categories. The current database exclusion rows therefore remain implementation inputs but are not all re-certified as authoritative. Claude must not turn an `AUTHORITY_BLOCKED`, `FINANCING_SOURCE_ONLY`, or `NON_QPE_NPC_REDUCTION_ONLY` row into positive QPE without new official authority and a valuation/payment rule.

Travel/logistics records without a linked express official rule stay presumed non-QPE for contribution-support gross-up. Existing ordinary-budget QPE rules are not modified by this research branch.

## Scope integrity

This branch creates validation artifacts and a validator only. It does not modify application code, optimizer rules, production data, database rows, projects, or served economics.
