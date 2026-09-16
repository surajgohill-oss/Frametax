# Correction addendum to CLAUDE_126_EXECUTABLE_PRICING_PROOF.csv

**Added by:** CLAUDE_GENERIC_AMOUNT_GATED_DISCOVERY_REPAIR (2026-09-15)
**Applies to rows:** `au_location_offset` (line 6), `ca_bc_dave` (line 15), `ma_ccm_rebate` (line 60), `th_film_incentive` (line 90)

These four rows' `PRICED_RUNTIME_VERIFIED` category and its reason text ("resolve_program_rate resolved a real tier once the program's own specific producer-controlled evidenced_facts/amount_facts were supplied") describe an **isolated, manually-constructed call to `resolve_program_rate()`**, not a real run of the served evaluation pipeline. A real run of `discover_executable_jurisdictions()`/`_price_candidate()` at the time this row was written would have rejected all four programs before ever reaching a pricing call — their `amount_fact_key` values were never populated anywhere in the real discovery/preflight path (see `CLAUDE_AMOUNT_GATED_DISCOVERY_REPAIR.csv`).

**Corrected disposition, proven via a genuine, fresh, real-pipeline run of the 4 acceptance productions this workstream:**

- `au_location_offset`: correctly `UNPRICED` for all 4 real productions (genuine AUD 20,000,000 threshold shortfall); a controlled candidate now genuinely prices at $5,930,192.40.
- `ca_bc_dave`: now genuinely `PRICED_RUNTIME_VERIFIED` for all 4 real productions via the real served pipeline (was not, before this workstream) — Little Utopia $30,875.84 / F#K Valentine's Day $321,489.44 / Bad Hombres $236,496.96 / Lips Like Sugar $469,647.68.
- `ma_ccm_rebate`: correctly `UNPRICEABLE_AUTHORITY_INSUFFICIENT` for all 4 real productions (genuine missing 18-shooting-day schedule fact, disclosed); a controlled candidate with a real 20-day schedule fact prices at $2,965,096.20.
- `th_film_incentive`: now genuinely `PRICED_RUNTIME_VERIFIED` for all 4 real productions via the real served pipeline — $358,146.15-$2,470,913.50 depending on the tier reached.

Full detail: `CLAUDE_AMOUNT_GATED_RUNTIME_PROOF.csv` and `CLAUDE_AMOUNT_DISCOVERY_REPAIR_CLOSEOUT.md`. The original CSV rows are left unmodified (historical record of what was claimed and when); this addendum is the authoritative correction.
