# FrameTax 2.0 — Engine Scope

## What the engine does

The deterministic calculation engine in `app/calculators/` takes structured inputs
and produces auditable financial outputs. Every step is explicit and testable.

### Calculation pipeline (run_full_analysis.py)

```
line_items
    │
    ▼
[1] classify_budget_line_items
    → ATL / BTL / POST / OTHER
    → spend_category (35 values)
    → compensation_type (cash / deferred / equity / in_kind)
    │
    ▼
[2] apply_union_fringes
    → fully-loaded labor cost
    │
    ▼
[3] apply_fx_rates (if non-USD jurisdiction)
    → convert to USD
    │
    ▼
[4a] calculate_qualified_spend (per program)
    → applies jurisdiction_spend_pct assumption
    → applies UK 80% spend cap where applicable
    → per-category breakdown

[4b] apply_caps_and_exclusions
    → ATL cap (% of total budget)
    → individual salary cap
    → program annual cap

[4c] calculate_incentive_value
    → base_rate × qualifying_spend
    → uplifts (conditional, e.g. Georgia logo +10%)
    → economic_value after transfer discount
    │
    ▼
[5] calculate_net_budget
    → rebase_btl = BTL × LocalCostBenchmark multiplier (vs LA baseline)
    → travel_cost = 0 if home jurisdiction, else daily × days × crew
    → true_net = fixed_atl + rebase_btl + travel - incentive_economic_value
    │
    ▼
[6] calculate_risk_adjusted_net
    → DISCOVERY tier: +25% of incentive value as risk
    → PARSED tier: +8%
    → competitive allocation: +30%
    → qualification gaps: +40%
    │
    ▼
[7] evaluate_legal_stacking
    → checks all pairwise PROHIBITED / CONDITIONAL rules
    → sets legal_review_required flag
    │
    ▼
[8] score_qualification_tests
    → point-based scoring (e.g. UK BFI Cultural Test)
    → section minimums (e.g. C+D combined ≥ 4)
    │
    ▼
StructureAnalysisResult
    + full calculation_trace dict
```

---

## What the engine does NOT do

- **No LLM calls.** No `anthropic`, `openai`, or HTTP client imports in `app/calculators/`.
- **No rate lookups.** Rates come from the database, not from the internet.
- **No hallucinated rates.** If `base_rate` is NULL (DISCOVERY tier), the credit
  is calculated as 0. The engine will not substitute assumed values.
- **No probability modeling.** Risk is a deterministic discount, not a simulation.
- **No UI rendering.** The engine returns plain Python dataclasses and dicts.

---

## LLM boundary

```
┌─────────────────────────────────────────────┐
│  app/ingestion/  — LLM MAY be called here  │
│  is_llm_extracted=True marks all LLM output │
└──────────────────────────┬──────────────────┘
                           │ structured dicts
┌──────────────────────────▼──────────────────┐
│  app/calculators/ — LLM NEVER called here  │
│  All inputs are plain Python types          │
└─────────────────────────────────────────────┘
```

The service layer normalizes LLM-extracted values (converting to float, validating
ranges) before they enter the calculator. The calculator trusts its inputs are
valid Python types.

---

## Jurisdiction assumptions

The engine cannot know what fraction of a production's budget will be spent
within a specific jurisdiction — that depends on shooting schedule, crew residency,
and vendor selection.

This value (`jurisdiction_spend_pct`) is a **user input** on each production structure,
stored as `assumed_jurisdiction_spend_pcts` on `ProductionStructure`.

A jurisdiction_spend_pct of 1.0 means 100% of qualifying spend is in-jurisdiction
(conservative overshoot). A value of 0.60 means 60%.

**This is the highest-impact single input in the calculation.**
A change from 0.60 to 0.80 can shift incentive value by 33%.

---

## BTL rebasing

BTL (below-the-line) variable costs are rebased to local jurisdiction rates
using `LocalCostBenchmark` multipliers vs Los Angeles baseline.

Formula:
```
rebase_btl = variable_btl × avg(available_multipliers)
```

If no benchmark data exists for a jurisdiction, multiplier defaults to 1.0
(no adjustment, same cost as LA).

ATL fixed fees (director, writer, lead cast) are NOT rebased — they are
contractually fixed regardless of shooting location.

---

## Competitive programs

Programs with `is_competitive=True` (e.g. California Film 3.0) have annual
allocation caps. The engine:
1. Calculates the credit as if allocation were granted
2. Applies a 30% risk discount to the economic value
3. Adds a WARNING to the calculation trace

The credit is never guaranteed for competitive programs.

---

## Engine versioning

`ENGINE_VERSION = "0.1.0"` in `app/calculators/__init__.py`.
Every `StructureCalculationResult` records the engine version that produced it.
When the calculation logic changes, bump the version.
Old results remain valid and traceable against their engine version.
