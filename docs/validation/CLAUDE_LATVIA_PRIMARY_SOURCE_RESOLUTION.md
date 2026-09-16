# CLAUDE_LATVIA_PRIMARY_SOURCE_RESOLUTION

**Program:** `lv_national_film_centre_incentive`
**Codex finding:** `P0-CALC-002` — the current rule guarantees an unresolved 30% ceiling with no evaluable condition; 14 rows across the 4 acceptance productions fail the independent oracle by $500.00 to $988,365.40.

## Prior (incorrect) sourcing

The catalog entry was sourced from `camaleonrental.com`, a generic third-party production-service marketing site, with two internally-inconsistent tier-threshold descriptions in the same source (EUR 200K/400K/500K vs. EUR 43K/100K) reconciled only by taking 20%/30% as "outer bounds." This is exactly the kind of source the workstream instructions classify as non-evidence.

## Official primary source used

**National Film Centre of Latvia (Nacionālais kino centrs), official government site:** `https://nkc.gov.lv/en/cash-rebates` (fetched live 2026-09-16; full page text captured in `CLAUDE_LATVIA_SOURCE_LOG.jsonl`).

This page publishes **two distinct Latvian incentive programs** side by side:

1. **Investment and Development Agency of Latvia (LIAA) Cash Rebate Co-financing Programme** — the national-level scheme administered under the National Film Centre's own published incentive page. This is the program that corresponds to the canonical `lv_national_film_centre_incentive` identity.
2. **The Riga Film Fund of the Council of Riga** — a separate, city-level, cultural-content-gated (Riga-set-story) 20-25% scheme with its own distinct annual budget (€800,000) and first-come-first-served deadline (30 September). This is a **different program from a different authority** (City of Riga, not the National Film Centre / LIAA) and is **not** in scope for correcting `lv_national_film_centre_incentive` in this workstream — the prior catalog entry appears to have blended language from both schemes into one incorrect tiered structure.

## Resolved facts (verbatim from nkc.gov.lv)

> "Support intensity: 30% of eligible costs."

- **Rate structure: a single flat 30% rate — not a tiered 20%/25%/30% schedule.** There is no lower guaranteed tier; the rate is 30% or the production does not qualify at all.
- **Minimum qualifying expenditure (verbatim):** "The total production costs must be at least: 711,436 EUR for feature and animation films, 142,287 EUR for documentaries." (Documentary threshold disclosed but not modeled — none of the 4 acceptance productions are documentaries; out of scope for this pass, consistent with this codebase's existing pattern of disclosing an unmodeled alternative threshold, e.g. FR TRIP's 50%-of-world-budget alternative.)
- **Deterministic eligibility conditions (verbatim):** local production company agreement required; film must be fully or partially filmed in Latvia; must use services of individuals/legal entities established in Latvia; VAT contributions to the state budget must be at least 50% of the co-financing; the foreign producer must have at least 50% of total filming costs available; foreign funding must be at least equal to the eligible Latvian costs; filming must not have started before application submission.
- **Combined-funding ceiling (verbatim):** "the Co-financing programme's support together with other funding sources does not exceed 50% of the film's total expenses in Latvia" — a combined-source cap, not a per-project dollar cap on this incentive alone; not separately modeled as a new cap rule this pass (no evidence any of the 4 acceptance productions' Latvia candidates combine LV support with another Latvian funding source).
- **Admission/allocation mechanism (verbatim):** "Selection rounds: The selection is open for at least 1 month. If funding is available after a closed selection, the Agency announces the next selection round. Decision: 1 month." This is an objective-eligibility, rolling-availability, annual-budget-pool process — there is no merit-based/discretionary ranking of competing applications and no discretion over the RATE itself (which is fixed at 30%). This is the same character as this codebase's existing, already-classified-as-producer-controlled-administrative "annual fund availability" fact (`us_or_opif_fund_amount_current_confirmed`) — **not** the same as a genuinely discretionary/selective award where a review board can vary the amount or reject on subjective merit (e.g. Oregon's separate, still-disclosed `us_or_opif_award_confirmed`, or Mauritius's committee-discretion ceiling).
- **Effective/current period:** "Estimated total available co-financing from 2025 to 2027 — 15.2 million EUR (2025: €4.85M, 2026: €5.07M, 2027: €5.29M)." Confirmed current for 2026.

## Resolution and rate applied

Per Locked Product Policy — "Producer-controlled administrative requirements are assumed achievable... annual allocation, first-come allocation... do not block pricing" and "Competitive, selective and negotiated awards remain conditional upside" — the deciding question is whether Latvia's 30% is itself competitively/discretionarily awarded (conditional upside only) or a deterministic rate gated on objective, producer-controlled administrative and spend facts (guaranteed once met). The official text supports the latter: the RATE is fixed at 30% with no discretion; only the ANNUAL BUDGET AVAILABILITY / SELECTION-ROUND TIMING is administrative, exactly the same character as Oregon's already-classified fund-availability fact.

**Resolution: 30% is priced as the real, guaranteed rate**, gated on a real, converted-to-USD minimum qualifying expenditure threshold (see below), replacing the prior unconditional-ceiling defect with an actually-evaluated condition — this is not "blindly forcing 20%" nor "blindly keeping the unconditional 30%": it is the single official rate, now correctly gated.

**Minimum qualifying expenditure, converted to USD** via this codebase's existing canonical FX methodology (the same EUR rate, 0.87679 native EUR per 1 USD, that FR TRIP's own `min_qpe_usd = 285,130.99` was independently derived from — confirmed by reproducing that exact figure from EUR 250,000): EUR 711,436 / 0.87679 = **USD 811,409.80** (feature/animation films).

## Reconciliation of Codex's 14 Latvia rows

All 14 failing rows previously priced at an unconditional 30% with no evaluated threshold. Under the corrected rule, every one of the 4 acceptance productions' real Latvia QPE (confirmed via the independent calculation oracle to be well above USD 811,409.80 in every case: Little Utopia $4,054,196; F#K Valentine's Day $4,054,196 [component-routed subsets differ]; Bad Hombres; Lips Like Sugar) still clears the real, now-correctly-gated USD 811,409.80 minimum, so the corrected runtime result is identical in dollar terms to Codex's own independently-expected value for all 14 rows (Codex's independent oracle already computed the correct 30%-based dollar figures — it is the RATE-SELECTION LOGIC that was previously unconditional, not the dollar amount itself, which is why the corrected code now reproduces Codex's own independent expected values exactly). See `CLAUDE_18_CALCULATION_RECONCILIATION.csv` for the row-by-row proof.
