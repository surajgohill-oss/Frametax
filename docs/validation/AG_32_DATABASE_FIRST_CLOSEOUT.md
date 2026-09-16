# AG 32 PROGRAM DATABASE-FIRST RECONCILIATION

## Methodology
The existing canonical data substrates (`frametax2/backend/app/data/authority_coverage_registry.py` and `program_rate_rules_worldwide.py`) were manually scanned for all 32 requested program IDs.

## Substrate Findings
- `authority_coverage_registry.py`: Primary tracker for program capability boundaries.
- `program_rate_rules_worldwide.py`: Primary economic rules registry.
Many programs (such as `au_pdv_offset`) were discovered perfectly preserved in the existing `DoctrineRecord` definitions. For these, fields like `min_spend_usd=None` and `annual_cap_usd=None` were specifically documented as gaps, rather than replaced with generic defaults.
Programs like `ag-us-pr-puerto-rico-film-industry-economic-incentives-act` exist only as keys in the coverage registry and lack full rule definitions, marking all their material economic fields as gaps.

## Manual Checks
1. Verified `au_pdv_offset`: Confirmed present in `program_rate_rules_worldwide.py`, with exact missing `min_spend_usd` accurately flagged as a targeted gap.
2. Verified `ca_sk_production_grant`: Confirmed missing from rate rules entirely; marked as requiring full resolution.
3. Verified `us_wa_mpcp`: Has conflicts/gaps recorded safely without generating generic assumptions.
4. Verified `mx_federal_film_incentive_2026`: Mapped properly to existing repository records (via aliases/coverage).
5. All classification changes manually verified to be un-fabricated.

## Strict Anti-Fabrication Adherence
Because Firecrawl/authenticated PDF parsing was unavailable or failed to execute reliably on government domains, no assumed facts were inserted for the targeted web gaps. Instead, exact remaining unresolved fields are securely recorded in `AG_32_UNRESOLVED_FIELDS.csv`.

## Handoff
Reconciliation against the canonical substrates is complete. All 32 IDs have a database disposition and an explicit queue of exact gaps.
