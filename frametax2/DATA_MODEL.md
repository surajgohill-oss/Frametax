# FrameTax 2.0 — Data Model

All tables use UUID primary keys and a `created_at` / `updated_at` timestamp pair
inherited from `Base` in `app/db/base.py`.

---

## Core entities

### organizations
Multi-tenant root. All project data is scoped to an organization.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | String | |
| subscription_tier | String | "free" / "pro" / "enterprise" |

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| organization_id | UUID FK → organizations | |
| email | String unique | |
| role | String | "admin" / "analyst" / "viewer" |

### projects
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| organization_id | UUID FK → organizations | |
| owner_id | UUID FK → users | nullable |
| title | String | |
| home_jurisdiction_id | UUID FK → jurisdictions | Where crew is based |
| total_budget_usd | Numeric | Gross budget estimate |

---

## Jurisdiction hierarchy

### jurisdictions
Self-referential hierarchy: country → state/province → region → city.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| parent_id | UUID FK → jurisdictions | null = top-level |
| name | String | "California" |
| code | String | "US-CA" |
| iso_code | String | ISO 3166-2 |
| level | Enum | country / state / province / region / city |
| currency_code | String | "USD" / "CAD" / "GBP" |
| country_code | String | "US" / "CA" / "GB" |

---

## Incentive programs

### incentive_programs
One row per incentive program. `base_rate=NULL` until verified from source.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| jurisdiction_id | UUID FK → jurisdictions | |
| source_document_id | UUID FK → source_documents | nullable until source ingested |
| name | String | "Georgia Entertainment Industry Investment Act" |
| slug | String unique | "georgia_eiia" |
| program_type | Enum | tax_credit / rebate / grant / loan |
| credit_basis | Enum | qualifying_spend / qualifying_labor |
| base_rate | Numeric | **NULL if not verified** |
| is_refundable | Boolean | |
| is_transferable | Boolean | |
| transferable_value_pct | Numeric | e.g. 0.90 for 90 cents on dollar |
| is_competitive | Boolean | True = allocation capped / not guaranteed |
| requires_cultural_test | Boolean | |
| cultural_test_id | UUID FK → qualification_tests | nullable |
| confidence_tier | Enum | VERIFIED / PARSED / DISCOVERY |
| review_status | Enum | pending / under_review / approved / rejected |

### incentive_rules
Individual rules within a program (min budget, min shoot days, etc.)

### qualifying_spend_categories
Maps spend categories to programs: which spend counts, whether jurisdiction-only.

### program_uplifts
Additional rates triggered by conditions (logo use, VFX percentage, etc.)

### qualification_tests
Point-based tests (e.g. UK BFI Cultural Test: 31 pts available, 18 required).

### qualification_test_rules
Individual scoring criteria for a test.

### legal_stacking_rules
Pairwise rules between programs: ALLOWED / PROHIBITED / CONDITIONAL.

---

## Budget

### budget_documents
An uploaded budget file. `extraction_status`: pending → extracted → imported.

### budget_line_items
Individual line items after parsing. Key classification columns:

| Column | Notes |
|--------|-------|
| atl_btl | ATL / BTL / POST / OTHER |
| spend_category | 35-value enum (btl_crew_labor, atl_director, vfx, …) |
| is_fixed | True for ATL fixed fees; False for BTL variable costs |
| is_labor | True for all crew/talent labor |
| compensation_type | cash / deferred / equity / in_kind |
| qualifying_amount_usd | Set by calculate_qualified_spend |

---

## Production structures

### production_structures
A candidate structure = jurisdiction set + program claims + budget allocation.

| Column | Notes |
|--------|-------|
| jurisdiction_allocations | JSONB: [{jurisdiction_id, shoot_pct, budget_pct}] |
| claimed_program_ids | JSONB: [program_id, …] |
| assumed_jurisdiction_spend_pcts | JSONB: {program_id: pct} — user input |

### structure_calculation_results
Output of one engine run against a structure.

| Column | Notes |
|--------|-------|
| engine_version | Semver of engine that produced this result |
| true_net_cost_usd | fixed_atl + rebase_btl + travel - incentive_economic_value |
| risk_adjusted_net_cost_usd | true_net + risk discounts |
| calculation_trace_json | Full step-by-step audit trace |
| has_unverified_inputs | True if any DISCOVERY-tier program used |
| legal_review_required | True if stacking violation or CONDITIONAL rule found |

---

## Cost benchmarks

### local_cost_benchmarks
Multipliers vs Los Angeles baseline for each cost category.
Used to rebase BTL variable costs when comparing jurisdictions.

| Column | Notes |
|--------|-------|
| jurisdiction_id | |
| effective_from | ISO date |
| crew_labor_multiplier | 1.0 = same as LA; 0.85 = 15% cheaper |
| equipment_multiplier | |
| stage_multiplier | |
| location_multiplier | |
| source_document_id | Must cite source |
| confidence_tier | |

---

## Confidence tier rules

| Tier | Meaning | Risk discount |
|------|---------|--------------|
| VERIFIED | Rate confirmed from primary source document | 0% |
| PARSED | Rate extracted from PDF by LLM, not manually verified | 8% |
| DISCOVERY | Rate not yet confirmed — placeholder only | 25% |

**No rate may be promoted from DISCOVERY to PARSED or VERIFIED
without linking a `source_document_id` and a human review step.**
