# FrameTax Feature Audit — SKILL.md Section 3

**Date:** 2026-04-30
**Source audited:** `FrameTax.jsx` (2039 lines)
**Reference:** `SKILL.md` §3 "The 'Looks Built But Isn't' Failure Mode"

---

## Summary

| # | Feature | Status | Verdict |
|---|---|---|---|
| 1 | Library / Save | HALF-BUILT | Inputs saved; analysis snapshot is not. Reload re-runs AI. |
| 2 | Script-based location exclusion | HALF-BUILT | `wouldNotWorkIn` extracted but only soft-prompted; no deterministic pre-filter. |
| 3 | Cultural test scoring | MISSING | LLM-narrated only. No coded rule engine for BFI, Screen Australia, CNC, etc. |
| 4 | Source citations | MISSING | No `sourceUrl`/`lastVerified` in schema or UI. Numbers have no attribution. |
| 5 | FX rates (live API) | MISSING | No API call. Model instructed to "use current rates" and guesses. |
| 6 | Confidence tiers | MISSING | No state field, schema field, or visual indicator on any number. |
| 7 | Cross-budget benchmark database | MISSING | Per-budget BTL rebasing works; cross-project rate aggregation does not exist. |
| 8 | Tax credit monetization | MISSING | No transferable credit calculation, discounting at ~88c, or monetization UI. |

---

## Detailed Findings

---

### 1. Library / Save — HALF-BUILT

**What is saved (lines 948–963):**
- `budgetText` — raw budget text string
- `totalBudget` — single dollar figure
- `answers` — Q&A questionnaire responses
- `pref` — preferred countries list
- `results.overallRecommendation`, `results.budgetOrigin`
- `results.destinations` stripped to: `rank`, `country`, `flag`, `creditRate`, `trueNetCost`, `vsSavings`

**What is lost on save:**
- All qualification analysis per destination (`qualifications[]`)
- `highlights`, `structuringTips`, `costEligibility`, `paceNote`
- Treaty optimizer output (`treatyData`)
- Override / gap analysis data
- Budget breakdown detail (`localCostUSD`, `travelCost`, `exchangeRate`, etc.)

**What happens on reload (lines 979–990):**
The load function restores budget text, answers, and preferences, then routes the user to the "upload" page. They must click "Re-run Analysis" to recover results. A new AI call fires with no guarantee of matching the prior output.

**What it should do:** Save the complete `results` object (or at least every rendered field) so reload restores the full analysis without an AI round-trip.

---

### 2. Script-based location exclusion — HALF-BUILT

**Extraction (line 1089):**
`wouldNotWorkIn` is included in the script schema prompt:
```
"Schema: {\"writerName\":null,...,\"wouldNotWorkIn\":[]}"
```
The AI returns a populated `wouldNotWorkIn` array from the script analysis.

**How it is used:**
It is never read after extraction. The construction of `sNote` (lines 1136–1139) joins `environments` and `climateNeeds` into a natural language string passed to the main analysis prompt. `wouldNotWorkIn` is not referenced anywhere in that path.

**Effect:** If the script is set in the Arctic and `wouldNotWorkIn = ["UAE", "Morocco"]`, those countries can still appear as top-5 destinations because the AI was not explicitly told to exclude them and the instruction is not enforced in code.

**What it should do:** Before building the destination candidate list, filter out any country in `wouldNotWorkIn`. This is a two-line deterministic pre-filter, not an AI judgment call.

---

### 3. Cultural test scoring — MISSING

**Current state:**
The main analysis prompt (line 1164) requests a `qualifications[]` array with fields `{test, status, detail}`. The model returns strings like `"status": "partial"` based on its own judgment. There is no code that computes these.

The override prompt (line 1402) references "Ensure 10 of 31 BFI cultural test points" as a narrative action item. This is not a function call — it is a string passed to the model.

**Display (lines 796–804):**
Qualification status strings are color-coded (green/amber/red) based on their value, but the underlying data is pure LLM output.

**What is missing:**
Deterministic functions for each territory's cultural test:
- BFI Cultural Test: 31 points, must score ≥ 18 for high-end TV or ≥ 16 for film
- Screen Australia: points allocated for Australian elements
- CNC (France): 100-point scale, minimum 18 for eligibility

These are rules with published point tables, not estimates. They should be coded as functions that take script data inputs and return a score with per-criterion breakdown.

---

### 4. Source citations — MISSING

**Schema (lines 1156–1167):**
The fields requested per destination include `creditRate`, `estimatedCredit`, `incentiveProgram`, and many others, but `sourceUrl` and `lastVerified` are absent from the prompt schema entirely.

**UI (lines 765–804):**
The four-column cost grid shows dollar amounts with no attribution. Exchange rate text (line 787) reads "1.28 - Currency risk: moderate" with no source. Qualification details (line 796) show pass/fail with no link to the governing statute or film commission page.

**What is missing:**
1. Add `sourceUrl` and `lastVerified` to the analysis prompt schema.
2. Render a small attribution link or tooltip on each displayed number that carries one.

---

### 5. FX Rates (live API) — MISSING

**Claim in UI (line 1612):**
The hero section lists "applies live FX" as a feature of the analyzer.

**Actual behavior:**
The analysis prompt (line 1155) instructs: `"apply live FX"`. The model returns an `exchangeRate` field as part of its JSON response. No HTTP call to any FX service occurs before, during, or after the AI call.

**Effect:**
Exchange rates are guessed by the model from training data. For major currencies this is usually within a few percent. For exotic currencies or recent moves (post-training cutoff), accuracy is lower. The "live" claim in the UI is inaccurate.

**What is missing:**
A pre-analysis call to an FX API (Open Exchange Rates, ECB, or similar) to fetch real-time rates for the relevant currency pairs, stored in state and injected into the analysis prompt with the actual fetched value.

---

### 6. Confidence Tiers — MISSING

**State (lines 898–931):**
No confidence-related state variables exist.

**Schema:**
The analysis prompt schema contains no confidence, certainty, or data-quality fields.

**Rendering:**
Every number in every destination card, cost grid, and summary is displayed identically regardless of whether the rate is backed by a recently verified statute (high confidence) or an AI estimate of a rarely-cited regional fund (low confidence).

**What is missing:**
A `confidenceTier` field per rate (e.g., `"verified" | "estimated" | "discretionary"`) in the schema, carried through to a visible UI indicator — a badge, color shift, or asterisk — so the producer knows which numbers to verify before committing.

---

### 7. Cross-budget Benchmark Database — MISSING

**What exists:**
Per-budget BTL rebasing (line 1150–1155). For the uploaded production budget, variable below-the-line costs are rebased to local crew and facility rates per destination. This is a within-budget calculation, not a cross-project comparison.

**What the Library stores (lines 948–963):**
One budget's high-level output per save entry. There is no mechanism to aggregate BTL rate data across saves into a searchable index.

**What is missing:**
A database (could begin as a JSON file or localStorage aggregate) that records per-destination BTL rate factors derived from each analysis run, accumulating over time. This would enable prompts like "across 12 previous analyses, UK crew rates averaged 71% of LA rates" — a genuine benchmark rather than a per-analysis estimate.

---

### 8. Tax Credit Monetization — MISSING

**Incentive stacking prompt (line 1190):**
References "tax credits + grants + regional funds + broadcaster co-financing" generically. No distinction between refundable, transferable, or non-transferable credits.

**Override panel (lines 614–622):**
Shows `totalCreditOverride` and `savingsVsHome` as single numbers. No line item for "transferable credit @ 88c on the dollar" or "cash value if monetized vs. held to offset."

**Schema:**
No fields for `creditType` (refundable/transferable/non-transferable), `transferDiscountRate`, or `monetizedValue` in any prompt.

**What is missing:**
The entire feature. Transferable tax credits (common in several US states and a handful of international territories) are worth less than face value when sold — typically 80–92 cents on the dollar depending on market conditions. A producer deciding between a 25% transferable credit and a 20% direct rebate needs this calculation to make an informed choice. None of the schema, calculation, or UI for this exists.

---

## Notes on `FrameTax (1).jsx` (Alternate Version)

A second JSX file (`FrameTax (1).jsx`, 1000 lines) exists in the repo. It appears to be an earlier or stripped-down version of the same tool. It shares the same fundamental architecture and the same absences for features 3–8. The Library implementation in that version saves even less state. It was not the primary audit target but the gap analysis is the same.

---

## Recommended Priority Order

Based on production impact:

1. **Library / Save** — highest pain; losing analysis on every reload erodes trust in the tool.
2. **Script-based location exclusion** — two-line fix, deterministic, high accuracy gain.
3. **Source citations** — schema change + small UI addition; makes every number defensible.
4. **FX rates** — single pre-analysis API call; fixes an active inaccuracy claim in the UI.
5. **Cultural test scoring** — material effort (one function per territory) but high value for qualification accuracy.
6. **Confidence tiers** — enables producer to self-triage which numbers need verification.
7. **Tax credit monetization** — new feature, moderate effort, high financial impact for relevant territories.
8. **Cross-budget benchmark database** — longest horizon; requires persistent storage and enough runs to be meaningful.
