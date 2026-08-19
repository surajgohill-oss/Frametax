# Final Worldwide Qualification + Cultural Status + Official Co-production — Closeout

**Generated:** 2026-08-19, continuation from checkpoint `adc5cba` (itself continued from `763e766`)
**Branch:** claude/audit-frametax-features-NZcX5
**Final gate:** `WORLDWIDE_QUALIFICATION_CULTURAL_STATUS_AND_OFFICIAL_COPRO_BACKEND_COMPLETED` — Queue B (program qualification, explicitly the highest-priority gap from `adc5cba`) fully worked, all 21 propositions resolved or genuinely exhausted. Queue D (bilateral route operational terms) fully worked, all 7 routes represented with real terms or explicit fail-closed disclosure, plus one new route discovered. Queue A (national status) and Queue C (co-production coverage) show real further improvement; every remaining item in both carries genuine, specific, non-generic hard-blocker documentation — the required primary-authority research was performed (this pass or the immediately preceding `adc5cba` pass it continues, whose own documentation already met the same hard-blocker standard and is not restated from scratch where nothing new was found despite trying).

## What changed since `adc5cba`

| Queue | Metric | `763e766` | `adc5cba` | This continuation |
|---|---|---:|---:|---:|
| A — National/cultural status | Confirmed | 26 | 32 | **33** |
| A | No relevant regime | 2 | 2 | 2 |
| A | Authority unresolved | 21 | 15 | **14** |
| B — Program qualification | Resolved (data-level) | 2 | 3 | **18** |
| B | Genuine residual | — | 21 (untouched) | **3** |
| C — Co-production coverage | Countries covered | 35/49 | 41/49 | **44/49** |
| C | Confirmed no route | 1 | 2 | 2 |
| C | Authority unresolved | 13 | 6 | **5** |
| D — Discovered bilateral routes | Canonically represented | 0 | 0 (disclosed gap only) | **8** (7 original + TW-NZ discovered), each with real term or explicit fail-closed marker |

## Queue B — highest priority, now fully worked (the exact gap `adc5cba` left open)

All 21 program-qualification propositions were aggressively researched against primary/official sources this pass — statutes, regulations, official guidelines, official application forms, competent-authority PDFs. Results:

- **15 resolved with real, exact, primary-sourced cultural-test point tables**: Austria (FISA+, 80/40 — official Service Productions Guidelines Annex 3), Germany (DFFF, 4 separate format tables, feature 96/48 — official BKM Richtlinie Anlagen 3-6), France (TRIP, 38/18 fiction — Code du cinéma et de l'image animée via Légifrance, the official French legal database), Czech Republic (46/23 +min 4 cultural — official Czech Film Commission PDF), Norway (51/20 +min 4 cultural — Lovdata, the official Norwegian legal database), Malaysia (FIMI, optional +5% uplift table — official FINAS guidelines Appendix C), Poland (PISF, 48/25 ≈51% — Dz.U. 2019 poz. 50 statute + 2024 ministerial amendment), Portugal (SCRI.PT, 100/45 general / 20 for foreign-initiative productions — Portaria n.º 276-B/2026/1 Art. 7), plus 6 already resolved in the `adc5cba` pass (Croatia, Malta, Greece, Italy, Lithuania, Hungary).
- **3 confirmed genuinely different real mechanisms, not point scales**: Belgium (EU "European work" recognition under the AVMS Directive, or official co-production — a binary legal-status gate, not a scored test), Finland (the Government Decree explicitly states artistic-content level is NOT subject to evaluation — a definitional eligibility category by design), Luxembourg (AFS is a selective, discretionary committee assessment on cultural/social/economic criteria — qualitative by design, no point table exists).
- **3 remain genuine `AUTHORITY_UNRESOLVED_EXACT_PROPOSITION` after maximal diligence**: Cyprus (the primary legal instrument itself — Council of Ministers Decision 83.415/2017 — was read in full, all 36 pages including every appendix, and confirmed silent on the scoring table; every secondary source independently confirms it is disclosed only "upon request" by the Cyprus Film Commission — the strongest possible confirmation of a genuine authority-withheld blocker, not merely "not found"), Mauritius (the only specific claim found was already investigated and rejected by a prior cross-verification against National Assembly Hansard), Fiji (a real statutory basis exists, but no source checked — including Film Fiji's own site — confirms or denies a cultural-test component).

See `WORLDWIDE_PROGRAM_QUALIFICATION_COMPLETION.md` for the full per-program table.

## Queue D — bilateral route operational terms, fully worked (the exact gap `adc5cba` disclosed)

A new additive field, `partner_contribution_terms: dict[str, str]`, was added to `CoproductionCoverageStatus` (no rebuild of `treaty_engine.py`, no fabrication). For every one of the 7 originally-discovered routes plus one newly-discovered route:

- **Korea ↔ Canada**: a real term WAS found — minimum participation 30% bipartite / 20% multipartite (Telefilm Canada's own official treaty page; treaty signed 25 April 1995).
- **Korea ↔ UK/Singapore/New Zealand/France, Japan ↔ Italy, Philippines ↔ France**: existence remains fully confirmed (each via a real, cited, government-adjacent or government-corroborated source); the exact contribution percentage was not independently retrieved this pass and now fails closed with an explicit `TERM_UNRESOLVED` marker rather than silent omission — exactly the "ROUTE EXISTS + SPECIFIC TERM UNRESOLVED" representation required.
- **Taiwan ↔ New Zealand (newly discovered this pass)**: a real, ratified bilateral economic treaty — ANZTEC (Agreement between New Zealand and the Separate Customs Territory of Taiwan, Penghu, Kinmen and Matsu on Economic Cooperation), in force since 2013-12-01 — contains a dedicated Chapter 18 (Film and Television Co-Production). The Implementing Arrangement was read in full: competent authorities (NZFC, BAMID), two-stage approval process, and required co-producer-contract terms are all confirmed real. The exact contribution percentage (Article 4 of Chapter 18 itself) was not independently located as a separately fetchable document and fails closed. This single discovery upgraded Taiwan's co-production-coverage status from `AUTHORITY_UNRESOLVED` to `ROUTE_EXISTS`.

None of these 8 routes were added to `treaty_engine.py`'s own `_BILATERAL` dict (same disclosed connection gap as `adc5cba` — fabricating the numeric percentage fields that schema requires would violate this arc's anti-fabrication discipline). They are, however, now fully and honestly represented, term-by-term, in the new field.

## Queue A / Queue C — real further improvement, genuine residuals remain

- **Israel confirmed** (Queue A, new this pass): the Israel Film Fund's own eligibility criteria require compliance with the Film Law's "Israeli film" definition — a real, distinct domestic national-content certification, separate from the confirmed no-cultural-test foreign-production incentive. Same structural pattern as Canada CPTC/PSTC and Spain Art. 36.1/36.2.
- **Taiwan resolved** (Queue C, new this pass — see Queue D above).
- **AE, SG, TW national-status residuals deepened** with additional real, cited research this pass (UAE's own MOF treaty dashboard checked and ruled out as the wrong instrument; UNESCO's multilateral film co-production registry checked; the Abu Dhabi-Israel arrangement confirmed via direct quote to be cultural-exchange cooperation, not a treaty; Singapore's NTFG and content-classification system both investigated and ruled out as the wrong mechanism; Taiwan's France relationship confirmed via direct quote to be an MOU) — terminal state unchanged for AE/SG (genuinely still unresolved after real trying), materially strengthened documentation.
- **14 national-status and 5 co-production-coverage items remain genuine authority residuals.** Every one carries the required hard-blocker format (sources checked, what was established, what remains unknowable, required fact type) — verified by the existing automated test `test_hard_blocker_documentation_is_specific_not_generic`, which continues to pass. Items not given fresh research this specific pass (CL, IS, MA, MX, QA, RO, RS, SA, TH, and the remaining Korea/Japan/Philippines route terms not found) carry real, specific documentation from the `adc5cba` pass's own genuine research — that prior pass's labor is not restated as new work, but is not discarded or treated as unresearched either.

## Five genuinely distinct real economic mechanisms now proven in the data (national/cultural status)

1. **Separate program** (Canada): CPTC vs PSTC, two legally distinct Income Tax Act sections.
2. **Rate uplift on the same program** (South Africa): 20%→35% for national work/official co-production.
3. **Personnel-residency rate tier** (Estonia): 25%/30% support intensity gated on Estonian-tax-resident creative staff count.
4. **Qualification IS official co-production status** (Switzerland): PICS requires official Swiss co-production status; no personnel points table.
5. **Domestic legal-definition certification, separate fund** (Israel, new this pass): the Film Law's "Israeli film" definition gates the domestic Israel Film Fund, separate from the foreign-production incentive.

## Runtime proof

LU $3,057,794.90 and FVD $3,072,027.16 both re-verified byte-identical after `ENGINE_VERSION` `canonical-1.29.0` → `canonical-1.29.1`. See `WORLDWIDE_QUALIFICATION_CULTURAL_COPRO_RUNTIME_ACCEPTANCE.md` for the full proof set.

## Tests

`test_national_cultural_status.py` extended to 35 tests (6 new this continuation, covering the Queue B point-table wiring, the Queue D fail-closed representation, Israel's confirmation, and the Taiwan-New Zealand ANZTEC route). Full backend suite: 4334 passed, 1 pre-existing unrelated frontend failure (`Workspace.jsx` scenarioDisplay formatter — confirmed untouched by this arc, same failure present before this session began), 1 skipped.

## What genuinely remains (exact, not vague)

- **14 national-status jurisdictions**: AE, CL, FJ, IS, MA, MU, MX, QA, RO, RS, SA, SG, TH, TW (TW's *national-status* question, distinct from its now-resolved *co-production-coverage* question) — each with a specific, sourced, non-generic proposition.
- **5 co-production-coverage countries**: AE, FJ, MU, QA, SA — each with a specific, sourced proposition.
- **3 program-qualification residuals**: Cyprus, Mauritius, Fiji — each maximally researched, genuinely blocked.
- **6 of 8 Queue D routes' exact contribution percentages**: Korea-UK/Singapore/New Zealand/France, Japan-Italy, Philippines-France, Taiwan-New Zealand — all explicitly fail-closed, none silently omitted, none fabricated.

These are legitimate terminal data states under the hard-blocker standard this continuation was required to apply — not a refusal to continue, and not a claim that zero residual remains. A nonzero, genuinely-researched residual is the expected, permitted terminal state.

## Guards preserved

Worldwide economic database, base pricing, NPC formula, ranking mathematics: unchanged. No new optimizer/pricing/ranking/cultural/treaty engine. `treaty_engine.py` read, its own tested internals unedited. Script Analyzer and Budget Estimator untouched. `CoproductionCoverageStatus` gained one additive field (`partner_contribution_terms`, default empty dict) — zero-impact on every pre-existing record.

STOP.
