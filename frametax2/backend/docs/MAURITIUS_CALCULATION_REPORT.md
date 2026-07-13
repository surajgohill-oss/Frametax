# Mauritius Calculation Report — The Little Utopia

**Date:** 2026-07-12
**Nature:** First-principles statutory recalculation. No previous QPE totals
were used as inputs or comparison targets; every figure below is derived from
budget + facts + statutory rules only. Where derived figures happen to match
earlier outputs, that is because the same derivation reproduces them — not
because they were carried forward.

**Permanent rate-authority rules now in force** (implemented in
`app/data/program_rate_rules.py`, enforced by `tests/test_program_rate_rules.py`):

1. Budget documents are never authoritative for incentive rates or statutory rules.
2. Incentive percentages in uploaded budgets/financial models are ignored for calculation.
3. Rates come only from the incentive database + cited statutory authority.
4. Cross-border optimization compares jurisdictions on database/statutory rates only.
5. On database-vs-budget disagreement, the database is used and the conflict is reported.

**Rule 5 conflict reported for this production:** the budget's own line
"EDB Rebate at 35%: $(1,275,411)" (also mirrored into migration 0009's
`base_rate=0.35` row) conflicts with the statutory database (30% / up to 40%).
The 35% figure is ignored everywhere and now exists only as
`MU_BUDGET_EVIDENCED_RATES` data feeding this conflict report, served live on
`GET /api/v1/cineglobe/production → rate_resolution.conflicts`.

---

## 1. Governing sources

| # | Source | Standing |
|---|---|---|
| S1 | **EDB "Film Rebate Scheme — Submission Procedures", 31 January 2020** — edbmauritius.org/wp-content/uploads/2022/10/Guideline-Online-Application-FRS.pdf — citing the *Economic Development Board (Film Rebate Scheme) Regulation 2018*. Read in full (pdftotext) this session. | Primary government guidance; the authority for every rate and QPE category below |
| S2 | **MCCI Film Rebate Scheme page** — mcci.org/en/inside-mauritius/incentives-schemes/film-rebate-scheme/ — fetched this session. | Government-adjacent corroboration; matches S1, adds no conditions |
| S3 | identicalpictures.com / trade fixer sites | NOT authority. Their extra claims are disclosed in §6 as unverified |

The *Regulation 2018 text itself* has not been obtained; S1 is the EDB's own
procedures document describing it. Confidence ceiling throughout is therefore
**Government Guidance**, not Verified Statute.

### Verbatim quotes used below (key)

- **Q-QPE**: "Qualifying Production Expenditures (QPE) refer to the expenses
  incurred locally by the company with respect to the list of qualifying
  production categories defined as follows:" *(followed by a closed list of
  33 categories — S1 p.4)*
- **Q-LAB**: "Labour costs (including non-nationals)" and "Remuneration for
  cast and crew" *(S1 p.4, two of the 33 categories)*
- **Q-TRAV**: "Travel to Mauritius (flight and marine travel)" *(S1 p.4)*
- **Q-PROF**: "Professional services (such as insurance and accounting
  services)" *(S1 p.4)*
- **Q-POST**: "Post production services (picture and sound)" *(S1 p.4)*
- **Q-VFX**: "Visual effects services" *(S1 p.4)*
- **Q-EQUIP**: "Rental of camera and lighting equipment", "Rental of marine
  vehicles", "Rental of studio facilities, warehouse and storage facilities
  and workshops", "Rental or purchase of props", "Location fees",
  "Ground transport and facility vehicle services", "Construction",
  "Set dressing", "Catering", "Craft services", "Per diems",
  "Accommodation in Mauritius", "Diving services", "Stunt services",
  "Special effects services", "Security services", "Shipping",
  "Wardrobe rentals" *(S1 p.4 — the operational categories)*
- **Q-30**: "30% rebate will be applicable on Qualifying Production
  Expenditures (QPE) incurred locally and as described further below" *(S1 p.3)*
- **Q-40**: "Up to 40% rebate will be applicable on Qualifying Production
  Expenditures (QPE) incurred locally, and as described further below, by a
  feature film production company, subject to a minimum QPE of USD 1,000,000
  for feature film; and a minimum QPE of USD 150,000 per episode of a drama
  series." *(S1 p.3)*
- **Q-SPON**: "The QPE quantum should not include any forms of sponsorships
  or financial assistance obtained for the Mauritian schedule of the
  project." *(S1 p.3)*
- **Q-CMTE**: "The purpose of the Film Rebate Committee will be to assess
  projects in terms of its economic benefits … and provide recommendations to
  the Chief Executive Officer who shall approve projects." *(S1 p.2)*
- **Q-ELIG**: "The Film Rebate Scheme will be available to production
  companies incorporated or registered in Mauritius, including those with
  100% foreign ownership" and "only applications from producers with a
  successful track record of at least 5 years in film production will be
  entertained" *(S1 p.3)*

**Interpretation register** (every place the engine reads beyond the literal
words — the "how the engine interpreted that language" column below refers here):

- **INT-1 (territorial):** Q-QPE's "incurred locally" is applied as a gate on
  top of category membership — work performed outside Mauritius fails even in
  a named category.
- **INT-2 (closed list):** the 33-category list is exhaustive; omission is
  affirmative exclusion authority. *S1 never states this rule expressly for
  motion pictures* (it does publish an express exclusions list only for
  Digital Animation) — this is the engine's structural reading and is flagged
  as an interpretation, not a quotation.
- **INT-3 (incurred):** an unspent reserve is not an "expense incurred."
- **INT-4 (no ATL carve-out):** Q-LAB names cast/crew remuneration without
  distinction; no above-scale/ATL restriction exists anywhere in S1.
- **INT-5 (inbound travel):** Q-TRAV makes travel *to* Mauritius its own
  category; origin-country airfare is not "work performed abroad."
- **INT-6 ("such as"):** Q-PROF's examples are non-exhaustive; insurance and
  accounting are certain, legal fees are genuinely open.
- **INT-7 (band ceiling):** Q-40's "up to" + Q-CMTE means 40% is the ceiling
  of a discretionary band, not an entitlement; the guaranteed tier is Q-30's 30%.

---

## 2. Account-by-account determination (all 41 accounts)

Status vocabulary: **INCLUDED** (counts in verified QPE), **EXCLUDED**,
**CONDITIONAL** (visible, escalated, not in verified QPE until the named
condition resolves). "Override" = what additional evidence a user can supply
to change the treatment (via `/facts`, the Legal docket, or path approvals).
Confidence: **GG** = Government Guidance (S1 verbatim), **GG+INT** = S1 plus a
flagged interpretation, **FACT** = turns on a production fact.

| Acct | Description | Amount ($) | Status | Basis (quote) | Interpretation | Conf. | Override |
|---|---|---|---|---|---|---|---|
| 10-00 | Story & Screenplay Development | 85,000 | INCLUDED | Q-LAB | INT-4 | GG | — |
| 11-00 | Director Fee | 175,000 | INCLUDED | Q-LAB | INT-4 | GG | — |
| 12-00 | Producer Fees | 148,444 | INCLUDED | Q-LAB | INT-4 | GG | — |
| 13-00 | Lead Cast Agreements | 130,000 | INCLUDED | Q-LAB | INT-4 | GG | — |
| 20-00 | Production Manager & Staff | 155,000 | INCLUDED | Q-LAB | — | GG | — |
| 21-00 | Director of Photography | 95,000 | CONDITIONAL (structuring) | Q-LAB permits; blocked by non-MU payroll routing (production fact) | INT-1 | FACT | Answer `payroll_routing_localized=true` or execute MU EOR/SPV routing with documents |
| 22-00 | Camera Dept & Equipment | 185,000 | INCLUDED | Q-EQUIP ("Rental of camera and lighting equipment") | — | GG | — |
| 23-00 | Sound Department | 65,000 | CONDITIONAL (structuring) | as 21-00 | INT-1 | FACT | as 21-00 |
| 24-00 | Lighting & Electrical | 145,000 | INCLUDED | Q-LAB / Q-EQUIP | — | GG | — |
| 25-00 | Grip Department | 82,000 | INCLUDED | Q-LAB | — | GG | — |
| 26-00 | Art Dept / Production Design | 168,000 | INCLUDED | Q-EQUIP ("Construction", "Set dressing", "Rental or purchase of props") | — | GG | — |
| 27-00 | Wardrobe & Costume | 72,000 | INCLUDED | Q-EQUIP ("Wardrobe rentals") | classifier maps costume spend to the wardrobe category | GG | — |
| 28-00 | Hair & Makeup | 55,000 | INCLUDED | Q-LAB | — | GG | — |
| 29-00 | Location Fees & Permits (MU) | 95,000 | INCLUDED | Q-EQUIP ("Location fees") | — | GG | — |
| 30-00 | Transport & Ground Vehicles (MU) | 112,000 | INCLUDED | Q-EQUIP ("Ground transport and facility vehicle services") | — | GG | — |
| 31-00 | Marine Unit — Vessel Charter | 165,000 | INCLUDED | Q-EQUIP ("Rental of marine vehicles") | — | GG | — |
| 32-00 | Marine Unit — Safety & Support Boats | 35,000 | INCLUDED | Q-EQUIP ("Rental of marine vehicles", "Diving services") | — | GG | — |
| 33-00 | Marine Unit — Frogsquad (SA dive) | 99,837 | INCLUDED | Q-EQUIP ("Diving services") + executed MU SPV routing (production fact/precedent) | INT-1 satisfied via routing | GG+FACT | — |
| 34-00 | Marine Equipment Rental | 93,163 | INCLUDED | Q-EQUIP | — | GG | — |
| 35-00 | Marine Fuel & Consumables | 22,000 | INCLUDED | Q-EQUIP (marine services) | — | GG | — |
| 36-00 | Catering & Craft (MU unit) | 88,000 | INCLUDED | Q-EQUIP ("Catering", "Craft services") | — | GG | — |
| 37-00 | HOD & Int'l Crew Accommodation (MU) | 159,783 | INCLUDED | Q-EQUIP ("Accommodation in Mauritius") | — | GG | — |
| 38-00 | Local Crew Accommodation & Per Diems | 114,130 | INCLUDED | Q-EQUIP ("Accommodation in Mauritius", "Per diems") | — | GG | — |
| 39-00 | International Travel & Airfares | 143,000 | INCLUDED | Q-TRAV | INT-5 | GG | — |
| 40-00 | Supporting Artists (Extras) — MU | 42,000 | INCLUDED | Q-LAB | — | GG | — |
| 41-00 | Payroll Services & PAYE/Employer Contrib. | 68,000 | INCLUDED | Q-LAB (employer contributions as a component of labour cost) | derived: fringes are part of the labour cost the category names | GG+INT | — |
| 42-00 | Stunts & Physical SFX | 48,000 | CONDITIONAL (structuring) | Q-EQUIP ("Stunt services", "Special effects services") permits; blocked by payroll routing | INT-1 | FACT | as 21-00 |
| 43-00 | Unit Publicist & Stills | 24,000 | INCLUDED | Q-LAB | — | GG | — |
| 44-00 | Non-Recoverable VAT @15% (Memo) | 92,439 | NOT A QPE QUESTION | Memo line — embedded VAT reported within gross, not a spend account | — | — | — |
| 50-00 | Editing — Offline Cut | 78,000 | EXCLUDED | Q-POST category exists, but Q-QPE "incurred locally" fails: post is priced outside MU (production fact) | INT-1 | GG+FACT | Answer `post_work_in_jurisdiction=true` (move the work) |
| 51-00 | Color Grading & Mastering | 45,000 | EXCLUDED | as 50-00 | INT-1 | GG+FACT | as 50-00 |
| 52-00 | Sound Design & Final Mix | 62,000 | EXCLUDED | as 50-00 (Q-POST "(picture and sound)") | INT-1 | GG+FACT | as 50-00 |
| 53-00 | Music Score & Licensing | 55,000 | EXCLUDED | territorial (as 50-00); category coverage independently UNKNOWN — no category names music composition/licensing | INT-1; category = open question | GG+FACT | as 50-00 for territory; EDB written confirmation for the category |
| 54-00 | VFX / Digital Effects | 95,000 | EXCLUDED | Q-VFX category exists; "incurred locally" fails | INT-1 | GG+FACT | as 50-00 |
| 55-00 | Deliverables & DCP Mastering | 28,000 | EXCLUDED | as 50-00 | INT-1 | GG+FACT | as 50-00 |
| 60-00 | Production Insurance (E&O + Liability) | 185,000 | INCLUDED | Q-PROF ("such as insurance…") | INT-6 (insurance is a named example — certain) | GG | — |
| 70-00 | Legal & Accounting | 78,000 | CONDITIONAL (fact gap) | Q-PROF names accounting; legal fees not resolved by "such as"; account has no $ split | INT-6 | FACT | Itemized breakdown separating accounting (QPE) from legal (open) |
| 71-00 | Audit & Incentive Submission Fees | 35,000 | CONDITIONAL (fact gap) | Q-PROF covers audit/accounting; submission-fee portion not enumerated; no $ split | INT-6 | FACT | as 70-00 |
| 80-00 | Completion Bond Premium | 145,000 | EXCLUDED | absent from the 33-category list; no category plausibly extends to a bond premium | INT-2 | GG+INT | EDB written ruling that bond premiums fall within a category |
| 81-00 | Contingency Reserve | 596,597 | EXCLUDED | absent from the list AND not an "expense incurred" | INT-2 + INT-3 | GG+INT | Draw-down against real line items converts to those items' treatment |
| 82-00 | Finance Costs / Bridge Interest | 0 | NOT A QPE QUESTION | modeled separately as a financing cashflow, never as spend | — | — | — |

**No account is excluded on industry convention, another jurisdiction's rules,
absence of citation, or a prior register state.** Every EXCLUDED row above
terminates in S1 language plus at most a flagged interpretation (INT-1/2/3)
or a named production fact — enforced by regression test
(`test_no_account_excluded_on_cross_program_convention`).

---

## 3. Totals — exact formulas with substituted numbers

**Verified QPE** (INCLUDED rows only; conditional rows are NOT counted):

```
QPE = 85,000 + 175,000 + 148,444 + 130,000 + 155,000 + 185,000 + 145,000
    + 82,000 + 168,000 + 72,000 + 55,000 + 95,000 + 112,000 + 165,000
    + 35,000 + 99,837 + 93,163 + 22,000 + 88,000 + 159,783 + 114,130
    + 143,000 + 42,000 + 68,000 + 24,000 + 185,000
    = 2,846,357
```

**Conditional (not in verified QPE):** structuring 95,000 + 65,000 + 48,000 =
208,000; fact-gap 78,000 + 35,000 = 113,000.
**Excluded:** 363,000 (post/VFX/music territorial) + 145,000 (bond) +
596,597 (contingency) = 1,104,597. **Non-QPE lines:** 92,439 + 0.

**Reconciliation:**
```
2,846,357 + 208,000 + 113,000 + 1,104,597 + 92,439 = 4,364,393 = Gross Budget ✓
```

**Incentive rate** — resolved from the statutory database only
(`resolve_program_rate`, live on `/production`):
- Tier: "up to 40%" feature-film band (Q-40). Conditions: feature film ✓;
  QPE $2,846,357 ≥ $1,000,000 ✓; band discretion (Q-CMTE) — cannot be
  pre-satisfied; no-sponsorship (Q-SPON) — no contrary evidence, unconfirmed.
- **Modeled rate: 40% (band ceiling). Guaranteed floor: 30% (Q-30).**
- Budget's 35% — ignored, conflict reported (Rule 5).

**At the modeled 40% ceiling:**
```
Incentive      = QPE × rate            = 2,846,357 × 0.40                = 1,138,542.80
Financing cost = Incentive × 0.08 × (39/52)
               = 1,138,542.80 × 0.08 × 0.75                              = 68,312.57
Net benefit    = Incentive − Financing = 1,138,542.80 − 68,312.57        = 1,070,230.23
Net Production Cost = Gross − Net benefit = 4,364,393 − 1,070,230.23     = 3,294,162.77
```

**At the guaranteed 30% floor** (the number that survives if EDB awards the
bottom of the band):
```
Incentive      = 2,846,357 × 0.30                                        = 853,907.10
Financing cost = 853,907.10 × 0.08 × 0.75                                = 51,234.43
Net benefit    = 853,907.10 − 51,234.43                                  = 802,672.67
Net Production Cost = 4,364,393 − 802,672.67                             = 3,561,720.33
```

⚠ **Financing-cost caveat:** the 8% bridge rate and 39-week receipt delay are
**engineering assumptions** — no lender quote, no EDB remittance SLA. (MCCI
states claims are processed "within 30 days" of complete documentation, filed
"within 60 days of completion of filming"; that suggests the 39-week
assumption may be conservative, but neither figure is verified.)

⚠ **Demo-pipeline caveat:** the running demo serves QPE $2,959,357 because its
mock legal cycle auto-"resolves" the 70-00/71-00 fact gap through a
MockConnector. That resolution is a demo artifact, **not evidence** — the
honest verified QPE is $2,846,357 with $113,000 conditional.

---

## 4. Exclusion validation (authority class per exclusion)

| Account(s) | Authority class | Detail |
|---|---|---|
| 50/51/52/54/55-00 ($308,000) | **Government guidance + production fact** | Q-QPE "incurred locally" (statutory territorial requirement) × the fact that post is priced outside MU. Not an interpretation — the requirement is express. Reverses if the work moves. |
| 53-00 ($55,000) | **Government guidance + production fact**, with a disclosed authority gap | Territorial exclusion as above is dispositive today; the separate category question (music) is UNKNOWN, disclosed, and would need EDB confirmation only if the work moved to MU. |
| 80-00 ($145,000) | **Derived interpretation of government guidance (INT-2)** | Closed-list omission. S1 does not expressly say "unlisted = excluded" for motion pictures — flagged honestly as the engine's structural reading. Overridable by EDB ruling. |
| 81-00 ($596,597) | **Government guidance (INT-3) + derived interpretation (INT-2)** | "Expenses incurred" cannot include an unspent reserve (near-literal); closed-list omission is the second, interpretive ground. |

None rest on industry interpretation, engineering assumption, or missing fact
alone. The two INT-2 exclusions are the weakest links and are explicitly
marked overridable.

## 5. Inclusion validation

Every INCLUDED row in §2 cites a named category from S1's list verbatim (see
its Basis column). The only inclusions that go beyond literal category text:

- **41-00 Payroll/PAYE (GG+INT):** employer contributions treated as a
  component of "Labour costs" — a modest derived reading.
- **33-00 Frogsquad (GG+FACT):** category is express ("Diving services");
  "incurred locally" is satisfied through the executed MU SPV routing — a
  production fact with documentary precedent on this production.

## 6. The 40% rate — validation

| Item | Finding |
|---|---|
| Statutory authority | EDB (Film Rebate Scheme) Regulation 2018, as described by S1; 40% band introduced by National Budget 2016-2017 (S1 Introduction, quoted) |
| Government guidance | S1 p.3 (Q-40) + Minimum-QPE table p.6: "Eligible for up to 40% rebate — Feature film (including animation): 1,000,000" |
| Condition: feature film | **SATISFIED** — production fact |
| Condition: minimum QPE USD 1,000,000 | **SATISFIED** — verified QPE $2,846,357 (2.8× the threshold; still ≥ $1M even at the most adverse resolution of every conditional item) |
| Condition: "up to" band discretion (Q-CMTE) | **CANNOT BE PRE-SATISFIED** — the awarded rate within [30%, 40%] is set at EDB approval. 40% is modeled as the ceiling; 30% is the guaranteed floor |
| Condition: no sponsorship/financial assistance in QPE (Q-SPON) | **UNVERIFIED production fact** — nothing in the budget indicates sponsorship, but absence of a record is not confirmation. NB: this clause is also directly relevant to the off-budget $625,000 in-kind post proposal (Q1) — an in-kind contribution may constitute "financial assistance," strengthening the case that it needs an EDB ruling before ever entering QPE |
| Eligibility: MU-incorporated production company (Q-ELIG) | **UNKNOWN production fact** — an MU SPV exists for Frogsquad routing, but the claiming entity's incorporation/registration is not evidenced |
| Eligibility: producer 5-year track record (Q-ELIG) | **UNKNOWN production fact** |
| Secondary claim: "90% of filming in Mauritius" | **NOT FOUND in any government text reviewed** (S1 read in full; MCCI fetched). Appears only on a trade fixer site with no cited regulation. Disclosed via the API as an unverified claim; not applied as a rule either way. Needs EDB written confirmation |
| Secondary claim: foreign cast/crew remuneration ≤ 40% of MU budget | Same status — NOT FOUND in government text; disclosed, not applied |
| Confidence | **Government Guidance** for the band and thresholds (S1 verbatim). Not Verified Statute — the Regulation 2018 text itself has not been obtained |

**Conclusion:** Little Utopia is *eligible for* the up-to-40% band on the
verified conditions. The engine models 40% (ceiling) and now discloses the
30% floor, the discretion condition, both unverified secondary claims, and
the budget-rate conflict on every `/production` response.

## 7. Remaining assumptions (complete list)

1. `bridge_rate = 0.08` and `delay_weeks = 39` (financing cost) — engineering assumptions.
2. Modeled rate = 40% band **ceiling** (INT-7) — the awarded rate could be anywhere in [30%, 40%].
3. Structuring-path setup cost $8,000/account — labeled placeholder, no vendor quote.
4. `CONFIDENCE_WEIGHTS` (0.90/0.60/0.25), grey-area cap 0.50, in-kind weight 0.25 — heuristic ranking constants (risk-adjusted case only).
5. Priority-score effort/gap constants (1.0–3.0 / 0.6–1.0) — policy constants for ordering only.
6. Budget classifier keyword rules assigning uncategorized lines to spend categories (e.g. 27-00 → wardrobe).
7. 30%-tier minimum QPE encoded as the foreign-production feature-film figure ($100,000); local-production and other-format minimums exist in S1's table but aren't yet modeled per-type.

## 8. Remaining unknown production facts

1. $ split of 70-00 and 71-00 between accounting/audit (QPE) and legal/submission fees (open) — $113,000 at stake.
2. MU incorporation/registration of the claiming production entity (Q-ELIG).
3. Producer's 5-year track record documentation (Q-ELIG).
4. Presence/absence of sponsorship or financial assistance in the Mauritian schedule (Q-SPON).
5. Whether post-production could be relocated to MU (would reverse $363,000 of exclusions).
6. Final payroll routing for DP/Sound/Stunts ($208,000 structuring).
7. Actual rebate remittance timing and bridge financing terms (drives the financing-cost assumption).
8. Script-derived facts (content-restriction clause in S1 "Types of films"): no offensive-content assessment has been run against the uploaded script.

## 9. Engineering interpretations still present

1. **INT-2** — closed-list omission = exclusion (bond, contingency). Strong structural reading, but S1 states an express exclusions list only for Digital Animation.
2. **INT-3** — "incurred" excludes unspent reserves (near-literal).
3. **INT-4** — no ATL carve-out (plain reading of Q-LAB; low risk).
4. **INT-5** — inbound travel qualifies wherever purchased (plain reading of Q-TRAV; low risk).
5. **INT-6** — "such as" non-exhaustive; legal fees open (flagged, drives 70/71-00 conditional).
6. **INT-7** — modeling the band ceiling as the rate (now disclosed with floor).
7. Employer payroll contributions as "Labour costs" component (41-00).

## 10. Corrections made this pass (all primary-authority-supported)

1. **MU comparison profile corrected** from budget-evidenced 0.35/0.35 (PARSED) to statutory 0.30/0.40 (VERIFIED, S1-quoted) — this removed four phantom relocation opportunities (BE/GR/IT/MT at $40,900 each existed only against the wrong 0.35 baseline) and corrected Spain's rate delta from 0.15 to 0.10. Audit-report defects D1 and D6 (MU scope) closed.
2. **Rate provenance encoded** (`program_rate_rules.py`): tiers, verbatim conditions, band-ceiling flag, floor rate, unverified secondary claims, budget-rate conflict — resolved at runtime against derived QPE and served on `/production`. Audit defect D2 closed (the rate now records its tier reasoning and its unverified edges).
3. **Stale MU profile prose replaced** with S1-cited notes (ATL/insurance/travel now correct).

**Not corrected (no primary authority yet / out of scope per instructions):**
the 8%/39-week financing constants (need lender + EDB facts, not statute);
the legacy `mediterranean_comparison.py` 0.35 rows (legacy Gen-1 stack, defect
D5 quarantine pending); the risk-adjusted heuristic's ranking role (optimizer
— explicitly out of scope this pass).

---

**Test state after this pass:** 2,784 passed, 1 skipped — including 15 new
tests enforcing Rules 1–5 (`tests/test_program_rate_rules.py`).
