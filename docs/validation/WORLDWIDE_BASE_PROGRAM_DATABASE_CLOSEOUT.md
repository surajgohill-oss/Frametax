# Worldwide Base Program Database + Pricing Closeout

**Generated:** 2026-08-17
**Final gate:** `WORLDWIDE_BASE_PROGRAM_DATABASE_AND_PRICING_ACCEPTED`
**Full structured data:** [`WORLDWIDE_BASE_PROGRAM_DATABASE_CLOSEOUT.json`](WORLDWIDE_BASE_PROGRAM_DATABASE_CLOSEOUT.json)

Implements the final-19 committee's settled determinations: 8 Codex AGREE + 11 Codex CORRECT (all 11 independently confirmed by Gemini). No new research performed — every treatment below consumes the committee's own conclusion.

## What changed

**6 new canonicalized programs**, all VERIFIED/PARSED tier with structured `SourceProvenance`, all `PROJECT_FACT_DEPENDENT` priceability:
- `ca_federal_cptc` (Canada, 25% Canadian labour)
- `in_national_film` (India, 30% base + two conditional +5% uplifts, 40% max — corrected from Claude's mistaken 50%-ceiling reading)
- `new_zealand_screen_production_grant_—_international_post_vfx` (NZ PDV, 20% baseline + conditional +5%, 25% max — corrected from a stale 20%/18% bracket)
- `pe_film_incentive` (Peru CIPA — corrected from Claude's NON_ECONOMIC; the credit is enacted and regulated, not pending)
- `pt_scri_pt_medium_budget` (Portugal's second RIPAC track, new sibling to the existing `pt_scri_pt_cash_rebate` large-scale track — the two are never combined)
- `uy_tax_credit_2026` (Uruguay's real July 2026 tax credit — replacing the misnamed `uy_xxi_incentive`, which never administered anything)

**3 confirmed duplicate aliases**, bound via `CANONICAL_RUNTIME_SLUG_BINDINGS`, never re-registered:
- `ca_nl_production_fund` → `ca_nl_all_spend_credit` (existing program, cap corrected $10M stale → CAD$20M current)
- `qc_film_production` → `ca_qc_pstc` (existing program, promoted DISCOVERY → VERIFIED, min spend added)
- `pt_film_incentive` → `pt_scri_pt_cash_rebate` (the large-scale RIPAC track)

**7 stay non-priceable with real mechanisms preserved**, reclassified from generic `UNPRICEABLE_AUTHORITY_INSUFFICIENT` to accurate states (`NON_GUARANTEED_SELECTIVE` / `NON_ECONOMIC`): the four Australian state funds, Denmark, Scotland, Wales — all genuinely competitive/discretionary despite several carrying a headline rate.

**2 reclassified from NON_ECONOMIC to FINANCING_SUPPORT** per Codex's direct correction: `br_ancine_incentive` (ANCINE's real 70% withholding-tax-reduction investor mechanism) and `jm_film_incentive` (Jamaica's PAYE tax credit + duty relief, not a QPE rebate).

**2 stay genuinely non-economic/out-of-scope, unchanged**: `ar_incaa_incentive` (INCAA itself administers nothing; Buenos Aires City's real rebate deliberately not merged into this identity) and `bc_interactive_digital_media_tax_credit_idmtc` (real credit, wrong production type for this engine).

**1 unchanged on purpose**: `mx_eficine_incentive` stays blocked — genuinely distinct from EFICA, no confirmed primary rate, not merged per Codex's explicit instruction.

## A real data-integrity gap found and fixed along the way

`discover_executable_jurisdictions()`'s capability gate defaults to `production_capable=False` when a jurisdiction has **no** `jurisdiction_comparison.py` profile at all — not merely "unknown," but an outright rejection, contradicting the module's own "unknowns do not reject" docstring. This was silently rejecting India, Peru, and Uruguay even after their doctrines were canonicalized. Fixed by adding minimal, honestly-disclosed capability profiles for all three (general geographic/industry knowledge, not primary-sourced infrastructure data) — a data gap closed, not a discovery-logic change (explicitly out of scope this task).

## Runtime verification

LU's Mauritius baseline and FVD's Greece baseline are **byte-identical** to before this task ($3,057,794.90 and $3,072,027.16). All 6 new programs price correctly through the same canonical engine and reconcile exactly (budget − incentive = NPC, zero residual). Browser-verified live: FVD's Scenarios page shows India, Peru, Uruguay, two New Zealand entries (general + PDV), two Portugal entries (large + medium), and two Canada entries (PSTC + CPTC) as independently priced, distinct candidates.

## Current worldwide database

- 115 total DoctrineRecords registered
- 113 executable jurisdictions (up from 110 — India, Peru, Uruguay capability profiles added)
- Coverage registry: 117 rows, zero unclassified/unexplained
- FVD representative evaluation: 121 candidate structures, 113 priced, 8 unpriceable — every unpriceable candidate carries an exact terminal reason, never a generic bucket

## Tests

4228 passed, 1 pre-existing out-of-scope failure (frontend title-formatter test, unrelated), 1 skipped. All count/rate assertions that legitimately shifted were updated with an explanation, never silently weakened.

## Deferred, untouched this pass

Optimizer/stacking restoration for grants, financing support, official co-production/cultural mechanisms, split/component, hybrid/anchor, in-kind, and reinvestment — all real data preserved in each program's `SourceProvenance`/citation for that later work. Three explicit mutual-exclusivity facts disclosed for the optimizer to consume later: Portugal's two tracks, Uruguay's two instruments, and New Zealand's PDV-vs-general-rebate relationship.

STOP.
