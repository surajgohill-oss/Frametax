# CineGlobe Explain Mode — Specification

**Status:** Specification only. No UI or engine changes in this pass.
**Basis:** [ENGINE_AUDIT_REPORT.md](ENGINE_AUDIT_REPORT.md) — every trace this
spec describes was verified constructible from data the engines already carry
(or names the exact gap where it is not).

**Goal:** no value appears anywhere in CineGlobe without an explainable
provenance. A producer clicks any number and sees where it came from, why
things were included/excluded, what was assumed, what evidence supports it,
and what would change it.

---

## 1. The core data structure: `ExplanationNode`

One recursive JSON shape explains every value in the product. Emitted by the
backend, rendered by the UI as an expandable calculation tree.

```jsonc
{
  "value": 3251674.77,
  "unit": "USD",
  "label": "Conservative Net Production Cost",
  "formula": {
    "symbolic": "gross_budget − (incentive − finance_cost)",
    "substituted": "4,364,393.00 − (1,183,742.80 − 71,024.57)",
    "engine_ref": "optimization_engine.build_risk_cases"   // module.function, clickable for engineers
  },
  "inputs": [ /* ExplanationNode[] — recurse until leaves */ ],
  "source": {                       // present on LEAF nodes
    "class": "STATUTE",             // vocabulary from audit report §0
    "citation": {
      "document": "EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020)",
      "pinpoint": "List of Qualifying Production Expenditures for Motion Pictures",
      "original_language": "Professional services (such as insurance and accounting services)",
      "url_hint": "edbmauritius.org"
    },
    "evidence_graph_refs": ["RULE-…", "ABS-…"]   // when applicable
  },
  "interpretation": {               // ONLY when the engine drew a conclusion the text doesn't state
    "original_language": "…the 33-item QPE list…",
    "engine_reading": "Omission from the closed list is affirmative exclusion authority.",
    "reading_class": "DERIVED_INTERPRETATION"
  },
  "confidence": "verified_statute", // verified_statute | government_guidance |
                                    // industry_interpretation | engineering_assumption | unknown
  "assumptions": [                  // every ENGINEERING_ASSUMPTION leaf that fed this node
    { "name": "bridge_rate", "value": 0.08, "basis": "No lender quote — engineering default.",
      "sensitivity": "±1pt rate ⇒ ∓$8,878 NPC" }
  ],
  "would_change_if": [              // the actionable levers
    { "kind": "fact",     "ref": "post_work_in_jurisdiction", "effect": "+$308,000 QPE if post moves to MU" },
    { "kind": "evidence", "ref": "GA-LEGAL-ACCOUNTING-SPLIT", "effect": "±$113,000 QPE on itemized breakdown" },
    { "kind": "approval", "ref": "SP-21-00", "effect": "+$95,000 QPE on executed MU payroll routing" }
  ]
}
```

Rules:

- **Leaves must terminate in a `source`.** Permitted terminal classes:
  `STATUTE`, `GOV_GUIDANCE`, `DB_RULE`, `PRODUCTION_FACT`, `USER_ANSWER`,
  `PARSED_BUDGET_LINE`, `ENGINEERING_ASSUMPTION`, `FALLBACK_DEFAULT`,
  `UNKNOWN`. A tree with a source-less leaf is a build error — this is the
  structural enforcement of "no silent assumptions."
- `UNKNOWN` is a first-class terminal (mirrors AbsenceOfAuthority): it renders
  as an "Unknown — escalated, not excluded" badge, never as zero.
- `formula.substituted` always shows real numbers, so "QPE = $2.85M" is never
  shown without "= 10-00 (85,000) + 11-00 (175,000) + …" one click away.

## 2. API surface

### 2.1 Embedded summary + on-demand tree

Every existing response value that is money, a rate, a rank, or a
classification gains a sibling `explain_ref`:

```jsonc
"cases": { "conservative": { "qpe_usd": 2959357.0, "explain_ref": "xp:case:PSC-MU:conservative:qpe" } }
```

New endpoint:

```
GET /api/v1/cineglobe/explain/{explain_ref}   → ExplanationNode (full tree)
```

Refs are deterministic path strings (state is already cached per fact-set in
`get_state()`; explanation trees are built lazily from the same objects — no
new computation, only exposition). `?depth=N` limits recursion for previews.

### 2.2 Register serialization additions (closes the audit §4 gap)

`/package.register[*]` adds:

```jsonc
{
  "authority_basis": "explicit_statute",        // already on AccountQualification, currently dropped
  "rule": {                                      // from program_spend_rules.SpendRule
    "spend_category": "insurance",
    "confidence_tier": "VERIFIED",
    "source_ref": "EDB-2020-QPE-List",
    "citation_text": "Professional services (such as insurance and accounting services)"
  },
  "facts_consumed": ["accounts_outside_jurisdiction"],   // which ladder facts fired
  "ladder_step": "statutory_rule",                       // memo|cashflow|structural|territorial|statutory_rule|fact_split|absence
  "explain_ref": "xp:register:60-00"
}
```

### 2.3 Assumption registry endpoint

```
GET /api/v1/cineglobe/assumptions
```

Returns the audit report §7 inventory as data: every named engineering
constant, its value, where it applies, and which displayed values it touches.
The UI's global "Assumptions" panel renders this; each entry deep-links to
the values it affects.

## 3. UI specification

### 3.1 Interaction model

- **Every traced value is clickable** (subtle dotted underline on hover; no
  visual noise by default).
- Click → right-side **Explain drawer** with three stacked sections:
  1. **Calculation** — the formula with substituted numbers, inputs as an
     expandable tree (indent = recursion depth). Each input row shows its
     source chip and confidence badge inline.
  2. **Authority** — for statute-backed nodes: the quoted original language,
     document + pinpoint, and (when interpretation occurred) the
     *Original language → Engine reading → Result* triplet rendered as three
     distinct blocks. This is mandatory whenever
     `interpretation` is present — an interpretation may never be displayed
     as if it were quoted text.
  3. **What would change this** — the `would_change_if` levers, each with its
     dollar effect and a direct action: fact levers link to the Question
     Stack item, evidence levers to the Legal docket task, approval levers to
     the recommendation approval flow.
- Drawer breadcrumb supports drill-down (NPC → incentive → QPE → account →
  rule → citation) with back-navigation.

### 3.2 Badge taxonomy (global, consistent everywhere)

| Badge | Applies to | Visual intent |
|---|---|---|
| `Verified statute` | VERIFIED-tier rule leaves | strongest; quiet green |
| `Government guidance` | OFFICIAL_GUIDANCE evidence | green-adjacent |
| `Interpretation` | any node with `interpretation` | amber; always expandable to the triplet |
| `Assumption` | ENGINEERING_ASSUMPTION / FALLBACK_DEFAULT leaves | amber, distinct glyph; hover shows value + basis + sensitivity |
| `Fact` | PRODUCTION_FACT / USER_ANSWER leaves | neutral; hover shows who/what supplied it |
| `Unknown` | UNKNOWN leaves, open grey areas | violet; never red (unknown is a work item, not an error) |
| `Heuristic` | any value whose tree contains CONFIDENCE_WEIGHTS or priority-score constants (rankings, weighted outlook) | explicit "ranking heuristic — not a filing figure" tooltip |

Confidence badges (HIGH/MEDIUM/LOW) render beside source chips wherever the
underlying object carries `QualificationConfidence`.

### 3.3 Screen-by-screen requirements

- **Overview / verdict:** the headline NPC must be the Conservative figure
  with its full tree. If a weighted-outlook figure is shown at all, it carries
  the `Heuristic` badge and never appears larger than Conservative.
- **Register (Package):** each row gets its ladder-step label, authority chip,
  and citation popover. Excluded rows show the five-step trace
  (Budget line → Rule → Authority → Reason → Effect) verbatim from audit §4.
- **Structures/Scenarios:** ranking column header itself is clickable —
  explains the ordering rule ("ascending conservative NPC; heuristic outlook
  shown separately"). Per the audit §6 recommendation, once ranking moves to
  Conservative-primary, the Explain tree for a rank shows both figures and
  their difference decomposed into weighted grey/structuring terms.
- **Recommendations:** each card renders `Evidence → Constraint → Calculation
  → Expected value → Confidence → Source` in that order, from fields the
  Recommendation object already carries (`evidence_reference`,
  `constraints`/`blocking_requirements`, `estimated_value_usd` + formula,
  `confidence`, `source_ref`).
- **Legal:** authority scores always render the six-dimension breakdown bars
  (never the bare composite) — data already exposed.
- **Facts/Questions:** every answerable fact lists the values it will change,
  with pre-computed deltas (already derivable: rerun `get_state()` under the
  hypothetical answer, diff the cases — the fact-store cache key mechanism
  supports this today).

### 3.4 Assumptions panel (global)

A persistent, low-key "Assumptions (14)" affordance in the workspace header
opens the registry from §2.3. Each entry: name, value, plain-language basis,
"affects" list with deep links, and a sensitivity line where computable
(finance-cost constants, confidence weights). This panel is the antidote to
D4 — assumptions stop being invisible without cluttering every screen.

## 4. Coverage matrix (acceptance criteria)

Explain mode ships when every cell below resolves to a working trace:

| Value | Tree depth | Terminal sources |
|---|---|---|
| QPE (any case) | 3 (case → accounts → rules/facts) | STATUTE, PRODUCTION_FACT, PARSED_BUDGET_LINE |
| Incentive | 4 (adds rate node) | + rate tier interpretation (D2 must be encoded as a condition-bearing rule first) |
| Finance cost / NPC | 5 | + 2 ENGINEERING_ASSUMPTION leaves (bridge, delay) |
| Any exclusion | 2 | STATUTE or DERIVED_INTERPRETATION + fact |
| Grey area | 2 | UNKNOWN + the missing fact/evidence request |
| Structuring path | 3 | STATUTE + PRODUCTION_FACT + assumption (setup cost) |
| Opportunity upside | 3 | profile rates (D1 must be unified first) + movable-spend derivation |
| Recommendation value | 3 | underlying case/opportunity trace |
| Rank position | 2 | ordering rule + the compared NPC traces |
| Scenario delta | 3 | two candidate traces + subtraction |
| Authority score | 2 | six dimension leaves (weights = assumption leaves) |
| Cultural test result | 2 | rule rows + production inputs |

## 5. Build order (suggested, not started)

1. **Blockers from the defect register:** D1 (unify MU rate records) and D2
   (rate-as-conditioned-rule) — otherwise Explain mode would faithfully
   display wrong/unexplainable numbers.
2. `ExplanationNode` dataclass + builders for the register (leverages existing
   `AccountQualification` + `SpendRule` fields; §2.2).
3. Case-level builders (QPE/incentive/finance/NPC trees) + `/explain`
   endpoint + assumption registry.
4. UI drawer + badges + register/structures screens.
5. Recommendations/scenarios/legal screens; facts-delta precomputation.
6. Retire RA from ranking order (audit §6) or badge it `Heuristic` everywhere
   it remains.
