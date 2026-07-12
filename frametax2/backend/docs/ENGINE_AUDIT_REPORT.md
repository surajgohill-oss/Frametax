# CineGlobe Engine Audit Report

**Phase:** Engine Transparency & Auditability
**Date:** 2026-07-12
**Scope:** Every calculation surfaced by the CineGlobe API (`/api/v1/cineglobe/*`), traced to its formula, sources, authority, confidence, and interpretation steps. No calculation logic was changed in this pass. Verified defects are documented in §9 and were NOT fixed here.

**Companion document:** [EXPLAIN_MODE_SPEC.md](EXPLAIN_MODE_SPEC.md) — the specification for surfacing everything below in the product.

---

## 0. Source-classification vocabulary used throughout

Every input to every calculation is classified as exactly one of:

| Class | Meaning | Example |
|---|---|---|
| `STATUTE` | Read from a government primary source this codebase has on file | EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020), QPE list |
| `GOV_GUIDANCE` | Government-published but sub-statutory | (none currently in the MU chain — the 2020 document is treated as the regulation's own procedures annex) |
| `DERIVED_INTERPRETATION` | A conclusion the engine draws FROM statute text that the text does not state verbatim | "closed 33-item list ⇒ omission = exclusion" |
| `DB_RULE` | Mirrored from an Alembic migration / seeded database row | migration 0021's contingency row (now superseded by STATUTE for MU) |
| `PRODUCTION_FACT` | A fact about this production from the budget source or intake | "post-production is priced outside Mauritius" |
| `USER_ANSWER` | A Question Stack answer (`/facts`) | `payroll_routing_localized=true` |
| `PARSED_BUDGET_LINE` | An amount/description from the parsed budget | 22-00 Camera Dept $185,000 |
| `ENGINEERING_ASSUMPTION` | A constant chosen by engineering with no external authority | `bridge_rate=0.08`, `CONFIDENCE_WEIGHTS` |
| `FALLBACK_DEFAULT` | A default that applies only when no better input exists | `DEFAULT_ACQUISITION_EFFORT=2.0` |
| `UNKNOWN` | Explicitly absent — never silently zero or excluded | music-score QPE category coverage |

Confidence taxonomy (per the task brief), mapped onto the code's tiers:

| Brief term | Code representation |
|---|---|
| Verified Statute | `SpendRule.confidence_tier="VERIFIED"`, `source_ref="EDB-2020-QPE-List"` |
| Government Guidance | `AuthorityTier.OFFICIAL_GUIDANCE` in the Evidence Graph |
| Industry Interpretation | (eliminated from the MU register this week — `CROSS_PROGRAM_CONVENTION` no longer produces any exclusion) |
| Engineering Assumption | named module constants (§7 inventory) |
| Unknown | `qualifies=None` rules → `GREY_AREA_REQUIRES_AUTHORITY`, never `EXCLUDED` |

---

## 1. The core formula chain (Conservative case)

Every headline number is produced by `optimization_engine.build_risk_cases()`
(`app/calculators/optimization_engine.py:185`). Exact formulas, with the live
Little Utopia values (post legal-resolution, as served by the demo state):

```
QPE_conservative = Σ amount(a) for a in register where state == QUALIFIES
                 + Σ amount(a) for executed, evidence-bound structuring accounts
                 + Σ amount(a) for grey accounts resolved RESOLVED_INCLUDE
                 + Σ off-budget grey items resolved RESOLVED_INCLUDE   (in-kind addon)

  Live: 2,846,357 (28 QUALIFIES accounts)
      + 0        (no structuring path executed)
      + 113,000  (70-00 + 71-00, resolved via the demo's mock legal cycle)
      + 0        (in-kind FMV unresolved)
      = 2,959,357

Incentive        = QPE × rate                    = 2,959,357 × 0.40 = 1,183,742.80
Finance cost     = Incentive × bridge_rate × (delay_weeks / 52)
                 = 1,183,742.80 × 0.08 × (39/52) = 71,024.57
Net benefit      = Incentive − Finance cost      = 1,112,718.23
NPC              = Gross budget − Net benefit    = 4,364,393 − 1,112,718.23 = 3,251,674.77
```

**Input classifications:**

| Input | Value | Class | Authority |
|---|---|---|---|
| account amounts | 41 lines | `PARSED_BUDGET_LINE` | `LITTLE_UTOPIA_BUDGET_LINES` (qualification_model.py:153), 1:1 with the sanitized budget fixture |
| account states | derived | see §3 per account | `derive_qualification_register()` ladder |
| `rate = 0.40` | 0.40 | **`DERIVED_INTERPRETATION`, partially unverified** | EDB 2020 doc: "up to 40%" tier for feature films with QPE ≥ $1,000,000 (met: $2.85M). A secondary source adds a "90% of filming in Mauritius" condition **not confirmed in the primary text** — see Defect D2. The constant `MU_RATE = 0.40` (little_utopia_state.py:85) records none of this reasoning. |
| `bridge_rate = 0.08` | 8%/yr | **`ENGINEERING_ASSUMPTION`** | Default parameter, no lender quote, no citation. Propagated as a default through composer/ranker/legal-engine; no production caller overrides it. |
| `delay_weeks = 39` | 39 wks | **`ENGINEERING_ASSUMPTION`** | Same. "Weeks from wrap to rebate receipt" — EDB's actual remittance timing has never been sourced. |
| gross budget | 4,364,393 | `PARSED_BUDGET_LINE` | Budget fixture total |

**Base case** = Conservative + approved-but-not-executed structuring paths (same formulas, `approved_amount` added to QPE).
**Optimistic** = Σ QUALIFIES + Σ all grey + Σ all structuring + in-kind FMV ($625,000) as additive QPE.

---

## 2. Governing Mauritius rule set — original language → interpretation → result

The MU rules (`app/data/program_spend_rules.py`, `MU_EDB_RULES`) are grounded in
one primary document: **EDB "Film Rebate Scheme — Submission Procedures"
(31 Jan 2020), citing the Film Rebate Scheme Regulation 2018** — specifically
its "List of Qualifying Production Expenditures (QPE) for Motion Pictures", a
closed 33-category enumeration. Every interpretation step the engine takes:

| # | Original language (primary source) | Engine interpretation | Result | Class |
|---|---|---|---|---|
| I1 | QPE = expenses "incurred locally" within the listed categories | Territorial gate: category membership alone is insufficient; work performed outside MU fails | Post/VFX/sound accounts (50–55-00) EXCLUDED despite being named categories | `STATUTE` + `PRODUCTION_FACT` |
| I2 | The QPE list is a closed enumeration of 33 categories; no general exclusions clause exists for motion pictures | Omission from the closed list is itself affirmative exclusion authority | Completion bond (80-00) EXCLUDED; contingency (81-00) EXCLUDED (dual ground with I3) | **`DERIVED_INTERPRETATION`** — the document never says "anything not listed is excluded"; the engine infers it from the list's closed structure |
| I3 | "expenses incurred" | An unspent reserve is not incurred cost | Contingency EXCLUDED (structural ground) | `DERIVED_INTERPRETATION` |
| I4 | "Remuneration for cast and crew" / "Labour costs (including non-nationals)" | No ATL/BTL distinction, no above-scale-cast carve-out exists | Writer/Director/Producer/Cast QUALIFY | `STATUTE` (plain reading) |
| I5 | "Travel to Mauritius (flight and marine travel)" | Inbound cross-border travel qualifies by definition; not subject to the I1 territorial exclusion | 39-00 International Travel QUALIFIES | `STATUTE` (plain reading) |
| I6 | "Professional services (such as insurance and accounting services)" | Insurance and accounting are named; "such as" is non-exhaustive, but legal fees are NOT resolved by this text | 60-00 Insurance QUALIFIES; 70-00/71-00 = grey area (fact gap: no $ split of legal vs accounting) | `STATUTE` for insurance; **`UNKNOWN` + missing `PRODUCTION_FACT`** for legal |
| I7 | No category names music composition/scoring/licensing; "Post production services (picture and sound)" may or may not reach a score | Genuinely unresolved — held as `qualifies=None` | 53-00 would be grey on category grounds; moot because it independently fails I1 territorially | `UNKNOWN` |
| I8 | "up to 40%" for feature films with QPE ≥ $1,000,000 (30% general tier) | 0.40 applied because verified QPE $2.85M ≥ $1M | `rate=0.40` throughout | `DERIVED_INTERPRETATION`, **tier conditions not fully verified** (Defect D2) |

**No exclusion anywhere in the register rests on cross-program convention,
absence of citation, or another jurisdiction's rules.** This is enforced by a
regression test (`test_no_account_excluded_on_cross_program_convention`).

---

## 3. Account-by-account provenance (all 41 accounts)

State source: `derive_qualification_register()` — an ordered, generic decision
ladder (memo → finance-cost → structural → territorial → statutory rule →
fact-split/absence escalation). Amounts: all `PARSED_BUDGET_LINE`. The "Fact"
column names the production fact consumed, if any.

| Account | Amount | State | Rule / ground | Authority class | Fact consumed |
|---|---|---|---|---|---|
| 10-00 Story & Screenplay | 85,000 | QUALIFIES | Labour/remuneration category (I4) | STATUTE | — |
| 11-00 Director Fee | 175,000 | QUALIFIES | I4 | STATUTE | — |
| 12-00 Producer Fees | 148,444 | QUALIFIES | I4 | STATUTE | — |
| 13-00 Lead Cast | 130,000 | QUALIFIES | I4 | STATUTE | — |
| 20-00 PM & Staff | 155,000 | QUALIFIES | I4 | STATUTE | — |
| 21-00 DP | 95,000 | STRUCTURING_OPPORTUNITY | No rule bars it; blocked by offshore payroll routing | STATUTE + PRODUCTION_FACT | `LITTLE_UTOPIA_OFFSHORE_PAYROLL` (21/23/42), clearable by user answer `payroll_routing_localized=true` |
| 22-00 Camera & Equip | 185,000 | QUALIFIES | Equipment-hire category | STATUTE | — |
| 23-00 Sound Dept | 65,000 | STRUCTURING_OPPORTUNITY | as 21-00 | STATUTE + PRODUCTION_FACT | offshore payroll |
| 24-00 Lighting | 145,000 | QUALIFIES | I4 | STATUTE | — |
| 25-00 Grip | 82,000 | QUALIFIES | I4 (classified from description) | STATUTE | — |
| 26-00 Art Dept | 168,000 | QUALIFIES | Equipment/premises | STATUTE | — |
| 27-00 Wardrobe | 72,000 | QUALIFIES | category classification | STATUTE | — |
| 28-00 Hair & Makeup | 55,000 | QUALIFIES | I4 | STATUTE | — |
| 29-00 Location Fees (MU) | 95,000 | QUALIFIES | Location-fee category | STATUTE | — |
| 30-00 Transport (MU) | 112,000 | QUALIFIES | Transport category | STATUTE | — |
| 31/32-00 Marine Vessel/Support | 200,000 | QUALIFIES | Marine/vessel category | STATUTE | — |
| 33-00 Frogsquad (SA dive) | 99,837 | QUALIFIES | Marine category; SPV routing executed (precedent) | STATUTE + PRODUCTION_FACT | — |
| 34-00 Marine Equip Rental | 93,163 | QUALIFIES | Equipment-hire | STATUTE | — |
| 35-00 Marine Fuel | 22,000 | QUALIFIES | Marine category | STATUTE | — |
| 36-00 Catering (MU) | 88,000 | QUALIFIES | Catering category | STATUTE | — |
| 37/38-00 Accommodation | 273,913 | QUALIFIES | Accommodation category | STATUTE | — |
| 39-00 Int'l Travel | 143,000 | QUALIFIES | "Travel to Mauritius" (I5) | STATUTE | — |
| 40-00 Extras (MU) | 42,000 | QUALIFIES | I4 | STATUTE | — |
| 41-00 Payroll/PAYE | 68,000 | QUALIFIES | Component of labour cost | STATUTE (derived — fringes as labour component) | — |
| 42-00 Stunts & SFX | 48,000 | STRUCTURING_OPPORTUNITY | as 21-00 | STATUTE + PRODUCTION_FACT | offshore payroll |
| 43-00 Publicist & Stills | 24,000 | QUALIFIES | I4 | STATUTE | — |
| 44-00 Non-recoverable VAT (memo) | 92,439 | NOT_APPLICABLE | Memo line, not a qualification question | PARSED_BUDGET_LINE flag | — |
| 50–52, 54, 55-00 Post/VFX/Deliverables | 308,000 | EXCLUDED | Named QPE categories, but incurred outside MU (I1) | STATUTE + PRODUCTION_FACT | `LITTLE_UTOPIA_ACCOUNTS_OUTSIDE_MU`; flippable by user answer `post_work_in_jurisdiction=true` |
| 53-00 Music Score | 55,000 | EXCLUDED | Territorial (I1); category coverage independently UNKNOWN (I7) | STATUTE + PRODUCTION_FACT | same |
| 60-00 Insurance | 185,000 | QUALIFIES | Professional-services category (I6) | STATUTE | — |
| 70-00 Legal & Accounting | 78,000 | GREY_AREA (FACT_DEPENDENT) | Accounting confirmed; legal unresolved; no $ split | STATUTE + missing PRODUCTION_FACT | resolvable by itemized breakdown |
| 71-00 Audit & Submission Fees | 35,000 | GREY_AREA (FACT_DEPENDENT) | as 70-00 | same | same |
| 80-00 Completion Bond | 145,000 | EXCLUDED | Closed-list omission (I2) | DERIVED_INTERPRETATION from STATUTE | — |
| 81-00 Contingency | 596,597 | EXCLUDED | I2 + I3 (dual ground) | DERIVED_INTERPRETATION from STATUTE | — |
| 82-00 Finance Costs | 0 | NOT_APPLICABLE | Modeled as cashflow, never QPE | engine structural rule | — |

Reconciliation (always enforced, warning emitted if violated —
optimization_engine.py:228): QUALIFIES 2,846,357 + STRUCTURING 208,000 +
GREY 113,000 + EXCLUDED 1,104,597 + N/A 92,439 = **4,364,393 = gross budget**.

---

## 4. Traceability template — every excluded account

Format required by this audit (Budget Line → Rule → Authority → Reason → Effect):

```
81-00 Contingency Reserve, $596,597 (PARSED_BUDGET_LINE)
  → Rule: structural-exclusion ladder step 3 (qualification_derivation.py)
    + SpendRule(contingency, qualifies=False, tier=VERIFIED, source_ref=EDB-2020-QPE-List)
  → Authority: EDB Film Rebate Scheme — Submission Procedures (31 Jan 2020),
    full QPE list for Motion Pictures (closed-list omission) + "expenses incurred" chapeau
  → Reason: an unspent reserve is not incurred cost; contingency appears nowhere
    in the 33 enumerated categories
  → Effect: −$596,597 from every case's QPE; −$238,638.80 potential incentive at 40%
```

The same five-step chain is constructible for every account from fields
already carried on `AccountQualification` (`reason`, `authority_basis`,
`amount_usd`) plus the `SpendRule` row (`notes`, `confidence_tier`,
`source_ref`). **Gap:** the API's `/package` register serialization exposes
`reason` but NOT `authority_basis`, NOT the rule's `source_ref`/tier, and NOT
the fact that fed the ladder — see the Explain-mode spec for the required
additions.

---

## 5. Optimizer & downstream dependency graph

```
PARSED_BUDGET_LINE (41 amounts)          EDB primary source        production facts / user answers
        │                                       │                          │
        └──────────────► derive_qualification_register() ◄─────────────────┘
                                   │  (per-account state + citation)
                                   ▼
                    register ──► legal_engine.apply_resolutions()  ◄── grey-area rulings (evidence-gated)
                                   │
                                   ▼
                          build_risk_cases()  ◄── structuring paths (derived from register)
                                   │             ◄── in-kind FMV (off-budget, additive-only)
                                   │             ◄── bridge_rate/delay_weeks (ENGINEERING_ASSUMPTION)
              ┌────────────┬───────┴──────┬──────────────┐
       CONSERVATIVE      BASE        OPTIMISTIC     RISK_ADJUSTED
              │                                          │
              ▼                                          ▼
   /structures primary figure                 structure ranking order,
   (conservative_npc_usd)                     scenario deltas, candidate-savings recs
```

**Scoring formulas downstream (all deterministic):**

| Output | Formula | Inputs' class |
|---|---|---|
| Structure ranking | Priceable candidates ascending by **Risk-Adjusted NPC**, tie-break `structure_id`; unpriceable appended alphabetically (global_scenario_ranker.py:402) | RA NPC (see §6) |
| Scenario delta | `baseline RA-NPC − scenario RA-NPC` (production_scenario_engine.py:160) | RA NPC |
| Candidate-savings recommendation value | same subtraction (production_recommendation_engine.py:517) | RA NPC |
| Opportunity / recommendation / acquisition-task priority | `(value_at_stake × confidence_gap) / effort` — one shared formula (`compute_priority_score`, legal_authority_acquisition.py:163) | value = real dollars or 0 when unknown (never invented); gap = `1 − CONFIDENCE_WEIGHTS[conf]` or fixed constants (1.0 open grey / 0.6 fact-unknown); effort = `EFFORT_BY_CONNECTOR_CLASS` (1.0–3.0) or `EFFORT_BY_COMPLEXITY` — **all ENGINEERING_ASSUMPTION policy constants, named and centralized** |
| Relocation opportunity upside | `(candidate.max_rate − baseline.max_rate) × movable_spend`, only when both rates known and delta ≥ 0.05 | profile rates = `DB_RULE`-grade PARSED/DISCOVERY data (**Defect D1**); movable_spend = derived from budget categories (engineering classification of which categories are "routable") |
| Authority score | 6 weighted dimensions (30/20/20/10/10/10), strongest-source rule, conflict cap 60, superseded ×0.5, absence ⇒ hard 0.0 (authority_score.py) | weights = ENGINEERING_ASSUMPTION (documented); tier/binding-force maps fixed |
| Structuring path "recommended" | upside/cost ≥ 3.0 AND confidence ≥ MEDIUM (structuring_paths.py:100) | ratio 3.0 = ENGINEERING_ASSUMPTION; cost $8,000 = **labeled placeholder**, no vendor quote |

---

## 6. Risk-Adjusted case — exact derivation and verdict

**Formula** (optimization_engine.py:296–324):

```
RA_incentive = Conservative.incentive
  + Σ over unresolved on-budget grey accounts:
        amount × rate × min(CONFIDENCE_WEIGHTS[acct.confidence], 0.50)
  + Σ over unresolved off-budget grey items (in-kind FMV):
        amount × rate × 0.25                       ← hardcoded LOW weight
  + Σ over non-executed structuring paths:
        (upside_incentive × CONFIDENCE_WEIGHTS[path.confidence]) − implementation_cost
RA_incentive = clamp(RA_incentive, [Conservative.incentive, Optimistic.incentive])
RA_finance   = RA_incentive × 0.08 × (39/52)
RA_NPC       = gross − (RA_incentive − RA_finance)
RA_QPE       = RA_incentive / rate        ← back-derived pseudo-QPE
```

**Variables and their basis:**

| Variable | Value | Basis |
|---|---|---|
| `CONFIDENCE_WEIGHTS` | HIGH 0.90 / MEDIUM 0.60 / LOW 0.25 | ENGINEERING_ASSUMPTION. Presented as "canonical confidence → probability mapping" but calibrated against nothing — no ruling-outcome history, no market data. |
| `GREY_AREA_WEIGHT_CAP` | 0.50 | Stated policy: "absent authority, nothing is more likely than a coin flip." A defensible *policy*, not a measurement. |
| in-kind weight | 0.25 | Hardcoded inline, commented "UNKNOWN authority, treat as LOW". |
| clamp | [Conservative, Optimistic] | Sound structural guarantee. |

**Why it exists:** to give the ranker/scenario engine one scalar that orders
structures with heterogeneous unrealized upside, without waiting for every
grey area to resolve.

**Assessment:**

- *Mathematically:* internally coherent — it is a clamped expected-value
  calculation. But its probability inputs are invented constants, so the
  output is a **heuristic score denominated in dollars**, not an expected
  value in any statistical sense.
- *Legally:* indefensible as a filing or committable figure. `RA_QPE` is a
  fictional spend total (incentive ÷ rate) corresponding to no set of
  accounts; the `CaseResult` even reuses Conservative's
  `included_codes`/`excluded_codes` while carrying the weighted `qpe_usd` —
  the account list and the dollar figure on the same object do not reconcile
  with each other (Defect D3).

**Recommendation (not implemented in this pass):**

1. Keep the computation as an internal ranking heuristic only, renamed in all
   surfaces to something honest — e.g. "weighted-outlook score" — and never
   displayed with a QPE figure. `RA_QPE` should be dropped from serialization
   entirely.
2. Switch structure ranking, scenario deltas, and candidate-savings
   recommendations to **Conservative NPC as the primary ordering**, with
   "weighted remaining upside" shown as a separate, clearly-badged column
   (`ENGINEERING_ASSUMPTION` badge on the weights). `/structures` was already
   moved to conservative-primary this week; the ranker's internal sort key,
   scenario deltas, and REC-CANDIDATE-SAVINGS still use RA and should follow.
3. If the weights are ever to carry meaning, they need a documented
   calibration source (counsel's assessed likelihood per grey area, entered
   as evidence — per-item, not global constants).

---

## 7. Engineering-assumption inventory (complete)

Everything below silently shapes displayed numbers today and must carry an
assumption badge in Explain mode:

| Constant | Value | Where | Affects |
|---|---|---|---|
| `bridge_rate` | 0.08 | build_risk_cases default; every production caller uses the default | every finance cost, net benefit, NPC |
| `delay_weeks` | 39 | same | same |
| `CONFIDENCE_WEIGHTS` | .90/.60/.25 | optimization_engine.py:72 | RA case, confidence gaps in all priority scores |
| `GREY_AREA_WEIGHT_CAP` | 0.50 | :81 | RA case |
| in-kind RA weight | 0.25 | :305 | RA case |
| `RECOMMEND_UPSIDE_TO_COST_RATIO` | 3.0 | :85 | path recommendation flag |
| `REPRESENTATIVE_ROUTING_SETUP_COST_USD` | 8,000 | structuring_paths.py:37 (labeled placeholder) | RA arithmetic, recommendation flag |
| `MATERIAL_RATE_ADVANTAGE` | 0.05 | opportunity_discovery.py:75 | which relocation opportunities exist |
| `EFFORT_BY_CONNECTOR_CLASS` / `EFFORT_BY_COMPLEXITY` / `DEFAULT_ACQUISITION_EFFORT` | 1.0–3.0 / 2.0 | legal_authority_acquisition.py:143 / recommendation engine | every priority ordering |
| `CONFIDENCE_GAP_*` | 1.0 / 0.6 / 1.0 | legal_authority_acquisition.py:158 | same |
| Authority-score weights | 30/20/20/10/10/10, cap 60, ×0.5 | authority_score.py:64 | authority scores |
| `MOVABLE_SPEND_CATEGORIES` | category set | production_package_intelligence.py | movable-spend hint → relocation upside |
| `HIGH_IMPACT_APPROVAL_THRESHOLD_USD` | 50,000 | legal_authority_acquisition.py:397 | which commits need approval |
| `MU_RATE` | 0.40 | little_utopia_state.py:85 | everything (see D2 — interpretation, not pure assumption, but unrecorded) |
| Mediterranean per-program delay weeks | 39/20/26… | mediterranean_comparison.py | legacy comparison module only |

---

## 8. What each screen's numbers are (endpoint → provenance)

| Endpoint value | Comes from | Notes |
|---|---|---|
| `/production.rate` | `MU_RATE` constant | carries no tier reasoning (D2) |
| `/package.register[*]` | derived register | exposes `reason` text but not `authority_basis`, rule tier, `source_ref`, or the consumed fact — Explain-mode gap |
| `/package.budget.*` totals | classification of budget lines | classifier = engineering keyword rules (`classify_budget_line_items`) |
| `/recommendations` | 8-pass recommendation engine | each rec carries `evidence_reference`/`authority_reference`/`source_ref` already — good bones for Explain mode |
| `/structures.candidates[*].cases` | one `build_risk_cases` per candidate | only the register-backed (MU) portion is priced; `priceable_pct` honestly marks the rest |
| `/structures.ranking` | `rank_production_structures` | order = RA NPC (§6 recommendation applies); primary displayed figure = conservative NPC (fixed this week) |
| `/legal` | LegalEngine cycle | verification/approval/commit gates all enforced with evidence; authority scores exposed with full breakdown |
| `/scenarios` delta | RA NPC subtraction | §6 recommendation applies |
| `/facts` | Question Stack store | answers genuinely mutate engine inputs (verified in Phase 1 integration) |

---

## 9. DEFECTS REGISTER — verified, documented, NOT fixed in this pass

### D1 — Contradictory Mauritius rate records drive phantom relocation opportunities (VERIFIED LIVE)
`jurisdiction_comparison.py` `_MAURITIUS` profile: `base_rate=0.35, max_rate=0.35`
("Budget-Evidenced 35%", PARSED, explicitly "NOT verified against EDB statute").
The rest of the engine runs `MU_RATE = 0.40`. Relocation discovery computes
`rate_delta = candidate.max_rate − 0.35`. Live result:
`OPP-JUR-RELOCATE-MU-{BE,GR,IT,MT}` each show delta 0.05 / upside $40,900, and
ES shows delta 0.15 / upside $122,700. **At a 0.40 baseline, the four 0.40
candidates fall below `MATERIAL_RATE_ADVANTAGE` and would not exist at all;
Spain's upside would be $81,800, not $122,700.** These phantom opportunities
propagate into composer candidates (`STRUCT-RELOCATE-MU-BE`…, visible in the
live `/structures` ranking) and recommendations.
*Fix direction (separate change):* single authoritative per-program rate
record consumed by both the pipeline and the comparison profiles; profile
notes updated to the EDB tier structure.

### D2 — `MU_RATE = 0.40` applied without recorded tier verification
The primary source gives 30% general / up to 40% for feature films with QPE ≥
$1M. The QPE condition is met ($2.85M verified). A secondary source claims an
additional "90% of filming in Mauritius" condition that the primary text read
so far does not confirm. The engine applies 0.40 unconditionally and records
none of this. If the unconfirmed condition exists and fails, every incentive
figure is overstated by 25% (0.40 → 0.30).
*Fix direction:* encode the rate as a rule with conditions + citation (like
spend rules); surface "rate tier: conditions" in Explain mode; obtain the
Regulation 2018 text itself to settle the 90% question.

### D3 — Risk-Adjusted `CaseResult` is internally inconsistent
`qpe_usd` = back-derived weighted figure; `included_codes`/`excluded_codes` =
copied from Conservative. The codes do not sum to the QPE on the same object.
Any consumer rendering both misleads. (Currently mitigated at the API layer by
this week's demotion, but the object itself remains contradictory and the
ranker/scenario/recommendation paths still consume it.)

### D4 — Finance-cost constants are invisible assumptions
8% bridge rate × 39-week delay produce the $71,024.57 finance cost inside
every NPC on every screen, with no badge, no source, and no way to see them.
(The jurisdiction profile's own notes estimate "$70K–$77K at 8%/9-month" —
consistent, but equally unsourced.)

### D5 — Legacy Gen-1 optimization API still mounted
`app/main.py` mounts `optimization.py` (`/api/v1/optimization/*`: gap-analysis,
recommendations, generate-structures, maximize, travel-cost) which calls the
old `app/optimization/*` stack and `qpe_calculator/mediterranean_comparison`
lineage — different math, different data vintage, reachable in production
alongside `/cineglobe/*`. Dual source of truth.
*Fix direction:* retire or clearly quarantine the legacy routes.

### D6 — Stale profile prose contradicts the corrected register
`_MAURITIUS.notes` still say "ATL qualifying scope unknown", "EDB Rebate at
35%", "$3.64M QPE" — all superseded by this week's statutory correction. If
any surface displays these notes, it displays misinformation.

### D7 — (Minor) `authority_score=None` vs `0.0` semantics
Discovery sets `authority_score=0.0` for absence-terminus opportunities and
`None` for "not yet scored". Downstream consumers must not conflate them;
`generate_evidence_acquisition_recommendations` keys counsel-approval on
`== 0.0`, which is correct today but fragile — worth a named constant.

---

## 10. What is already good (credit where due)

- The register partition **always reconciles to gross budget** and emits a
  warning if it doesn't; every case carries `reconciles`.
- Unknown ≠ excluded is structurally enforced (grey areas always visible,
  escalated, and gated on evidence to move).
- Every grey-area move requires counsel + bound evidence (enforced with
  raises, covered by tests).
- Authority scores are never shown bare — the six-dimension breakdown is
  mandatory, absence hard-zeros, conflicts cap.
- One shared priority formula everywhere (no competing ranking math).
- Recommendation objects already carry `evidence_reference`,
  `authority_reference`, `source_ref`, `opportunity_ids` — most of the
  Explain-mode wiring for recommendations already exists at the data layer.
