# Ireland Section 481 — Producer/Vendor Fee Followed by Separate Reinvestment as At-Risk Equity

**Status: `RESEARCH_ONLY_NO_CODE_OR_DATABASE_CHANGE`.** No production code, no database row, no
canonical program value, no rate, no rule table was created, read for merge, or modified for
this memo. This is a standalone legal-research artifact answering one question: *when a genuine
producer/vendor fee is unconditionally earned, paid, and then separately reinvested as at-risk
equity, does Section 481 (Ireland) preserve the fee as eligible expenditure?*

Baseline referenced per the user's instruction: `981d5cab23c5fc5555d97ad78b9da89813c9492d`
(branch `codex/reinvestment-gross-up-authority-research`, not merged into this branch). That
prior pass's own conclusion — `AUTHORITY_SILENT_RULING_REQUIRED` for the complete paid-then-
reinvested chain — is confirmed independently below, refined by structure, and given a full
statutory/regulatory/case-law basis it did not previously cite (it relied on the Revenue manual
alone). Nothing here is authorized to change engine behavior; it is a research answer for human
(and future engine-authorization) use.

## Authorities reviewed (primary, opened and read this pass unless noted)

| # | Authority | Status |
|---|---|---|
| A1 | Revenue Tax and Duty Manual Part 15‑02‑04, *Film Relief* — **document last reviewed August 2026** | Current, primary, opened and read in full |
| A2 | S.I. No. 119/2019, *Film Regulations 2019* | Current, primary, opened and read in full |
| A3 | Revenue *Notes for Guidance*, TCA 1997 Part 15 (Finance Act 2025 edition) — consolidated s.481 | Current, primary, opened and read |
| A4 | TCA 1997 s.481 and s.811C (consolidated, via secondary extraction of primary text) | Current, primary |
| A5 | Revenue *Guidance Note for Section 481 Investment in Film* (July 2016) | Superseded by A1/A2 but consistent on every point checked; opened and read |
| A6 | Office of the Comptroller and Auditor General, *2018 Annual Report*, Ch. 18 *Tax Relief on Film Production* | Official audit of administration, opened and read |
| A7 | European Commission State aid decision SA.53399 (2019/N) | Primary EU authority, opened and read (recitals 1–40) |
| A8 | Screen Ireland, *State Aid Regulations & European Funding* / *Funding Regulations and Limits* pages | Industry-body summary of EU state-aid rule as applied in Ireland |
| A9 | Revenue, *Film Withholding Tax* guidance (s.529B–M TCA 1997) | Current, primary |
| A10 | *McGrath v McDermott* [1988] IESC — Irish Supreme Court | Case law, secondary summary (full judgment not machine-readable this pass) |
| A11 | Codex reinvestment/gross-up research artifacts at `981d5cab2...` (`CODEX_GROSS_UP_AUTHORITY_CROSSWALK.csv`, `CODEX_DEFERMENT_REINVESTMENT_AUTHORITY.csv`, `CODEX_GROSS_UP_TRANSACTION_ARCHETYPES.csv`, `CODEX_GROSS_UP_PRACTICE_EVIDENCE.csv`) | Prior AI research, **not primary authority** — used only as a starting index, independently re-verified against A1–A9 |

Not located despite search: any published Tax Appeals Commission determination naming s.481,
"film relief," or "film corporation tax credit" (`taxappeals.ie` returned HTTP 403 to automated
fetch; web search returned none). A full 2013 Cinema Communication / GBER Art. 54 primary text
and a 2023 Committee on Budgetary Oversight report on s.481 were sought but not retrievable in
readable form this pass — treated as gaps, not as silence supporting any position. **This is a
documented negative search result, not proof no such determination exists.**

## 1. The statutory/regulatory test for eligible expenditure

Eligible expenditure is a **cost-side, payment-point test** applied to the *qualifying company's*
expenditure — it is not a test of what happens to the money afterward in the payee's hands. Three
filters apply in sequence (A1 §3.1, A3):

1. **Qualifying expenditure** (Regulations Part 7): incurred on production, development through
   post-production (Reg. 11), minus non-qualifying items (Reg. 12).
2. **Total cost of production**: qualifying expenditure that was "wholly, exclusively and
   necessarily" incurred to produce the film (s.481(1)) — the long-standing WEN test.
3. **Eligible expenditure** (Regulations Part 8): the portion of (2) expended *in the State* on
   eligible individuals, labour-only services, or goods/services/facilities from an Irish
   "relevant person" (Reg. 13–15).

Two Regulation 12 exclusions govern this fact pattern directly:

> **Reg. 12(f):** "amounts that are paid out of, are dependent on, or arise from rights in, the
> receipts, earnings or profits of the film" — non-qualifying.
>
> **Reg. 12(g):** "fees or other payments deferred unless the payment of such sums is made no
> later than 4 months after completion" — non-qualifying *unless* paid within that window.

Neither exclusion, nor anything else in A1–A3, conditions eligibility on the *payee's subsequent
use* of a fee already paid. Reg. 12(f) tests the *character of the payment into* the qualifying
company's cost base (is the fee itself a disguised profit share), not what the payee later does
with cash already earned. The "costs that will not qualify" list at A1 §3.3.4 (re-charges never
actually incurred by the payer, or in excess of actual cost) is likewise a test on the *payer's*
cost, not the payee's disposition of proceeds.

## 2. Producer fees specifically (A1 §3.3.2, verbatim)

> "Eligible producer-related fees are fees paid for producer services carried out by the producer
> company and included as the total cost of production incurred by the qualifying company... Revenue
> will accept as reasonable and as forming part of the 'eligible expenditure' [fees that] (a) are
> typical or representative of what a producer operating in the relevant market segment would
> normally be expected to do; (b) are performed wholly, exclusively and necessarily for the
> purposes of the film production; and (c) [fall within] 15% of the global budget where eligible
> expenditure is in excess of 80% of the global budget; or ... 10% ... where eligible expenditure is
> less than 80%... the percentages may be higher where it can be substantiated. Regard should be had
> to the arm's length principle in determining what the market rate would be."

This is the operative rate-and-legitimacy test for the fee itself, independent of anything that
happens next. The 15%/10% figures are **not caps** — they are a safe-harbour threshold; higher
amounts are permitted "where it can be substantiated," and lower percentages don't disqualify.
Related-party producer/overhead fees are expressly contemplated and expressly required to be
"substantiated" (A1 §3.3.2 opening line: "Production overheads and producer-related fees are a
common related-party transaction... which should be substantiated").

## 3. Analysis by transaction structure

### 3.A — Unrelated vendor, fee paid, vendor separately reinvests as equity

**Disposition: PERMITTED**, subject to the conditions below.

The fee is tested on its own terms: real services, WEN, paid (not deferred beyond 4 months, A1
§6.1/Reg. 12(g)), not contingent on receipts/profits (Reg. 12(f)), and — since the vendor is
unrelated — no connected-persons disclosure trigger applies (Schedule 5 Tab C(e) of the
Regulations only requires disclosure of connected-party payments ≥30% of the specified amount).
Nothing in A1–A3 makes eligibility contingent on an unrelated third party's later, independent
investment decision. The vendor choosing afterward to subscribe genuine at-risk equity in the
production is, on ordinary principles, a legally and economically separate transaction from the
fee that funded it — money, once earned and no longer subject to any contractual string, is the
vendor's own.

**Conditions that must hold for PERMITTED to survive scrutiny:**
- The fee must be priced at true arm's length for real services *without reference to* the
  reinvestment (A1 §3.3.2's arm's-length principle: "a price... at a level where it would be
  reasonable to consider that the transaction would have been entered into by independent
  parties"). A fee inflated above market specifically to fund the reinvestment fails WEN and
  risks s.481(2A)(f)(i)'s prohibition on "inflated" budgeted expenditure.
- The reinvestment must be genuinely independent — no contract, side letter, term sheet, or
  understanding conditioning the fee, its amount, or its payment on the vendor reinvesting.
  If reinvestment is a condition of or consideration for the fee, this is no longer an unrelated
  arm's-length payment; it is a single integrated financing arrangement dressed as two, and moves
  toward §3.E below (circularity).
- Payment must be real cash movement, evidenced (bank statements are a mandatory record — A1
  §5.8, Schedule 3(d)(iii) of the Regulations) — not a book entry, set-off, or same-day round-trip.

### 3.B — Related-party producer fee, paid, then reinvested as equity into the same production

**Disposition on the fee itself: `PERMITTED_WITH_CONDITIONS`.**
**Disposition on the complete paid-then-reinvested chain: `RULING_REQUIRED`.**

The fee is expressly addressed and can qualify (§2 above), *provided* it is substantiated as real,
WEN, arm's-length-priced, connected-party disclosed (≥30% trigger), and evidenced per Schedule 5
Tab C(e) and Tab D. A1 §3.3.1 cross-references Revenue's Family Wages TDM (04-06-23) principles for
related-party amounts: commercial rate, evidence services were actually performed, excess
disallowed.

No authority — the TDM, the Regulations, the Notes for Guidance, the 2018 C&AG audit, or any
located case law or ruling — addresses what happens when the *same related party*, having just
been paid by the qualifying company, turns around and reinvests that cash **into the very
production that paid it**, as equity. This is exactly the fact pattern the Codex crosswalk (A11)
flagged as `AUTHORITY_SILENT_RULING_REQUIRED` under Archetype C, and independent review of A1–A9
confirms the silence is real, not an artifact of incomplete prior research. Two live risks compound
because the parties are related:

- **s.481(2A)(f)(ii)** bars a claim "if there is no commercial rationale for the corporate
  structure proposed for... financing." A fee-then-reinvest loop involving the same controlling
  party, sized to work as a financing mechanism, is the paradigm case this provision is aimed at.
- **s.811C** (below, §4) — a related-party round-trip is more likely to be characterized as
  "undertaken... primarily to give rise to a tax advantage" than an arm's-length third party's
  independent choice, because the controlling party designs both legs.

Revenue's own audit practice confirms active, specific scrutiny of exactly this line item: the
2018 C&AG report records that "Revenue's review of the compliance report and auditor's report may
involve a request for additional back up for line items from production companies such as a
**producer fee calculation**" (A6 ¶18.37). A related-party paid-then-reinvested structure should
expect that request and should not be implemented, still less relied on as reducing net cost,
without a written Revenue ruling or opinion confirming the fee survives on its own facts
independent of the reinvestment.

### 3.C — Deferred fee, paid within the 4-month window, then reinvested

**Disposition: `PERMITTED_WITH_CONDITIONS`** (same conditions as 3.A or 3.B depending on
relatedness, plus the deferral-specific condition below).

Reg. 12(g) permits deferred fees on their face, "unless the payment of such sums is made no later
than 4 months after completion." The 2018 C&AG audit shows Revenue actively verifies genuine
payment of previously-deferred amounts is not merely claimed: "Revenue commenced monitoring
ineligible expenditure claimed for, **but not paid**, in January 2018. By the end of May 2019, 75
compliance reports had been reviewed... of which €2 million was deemed ineligible" (A6 ¶18.41).
"Payment" for Reg. 12(g) purposes is not defined beyond the ordinary meaning, and no authority
confirms whether a contra/set-off/non-cash settlement satisfies it — the required record
(bank statements, Schedule 3(d)(iii)) points strongly toward Revenue expecting real cash movement.
**Do not treat contribution or capitalization of the fee receivable as "payment"** — no authority
supports that; cash must actually move within the 4-month window, evidenced by bank statements,
before any later reinvestment is contemplated.

### 3.D — Producer-fee structure generally: does reinvestment reduce net eligible cost?

**No authority reduces the ORIGINAL fee's eligibility because of what the payee does with it
afterward** — see §1. The "costs that will not qualify" / rebate-forgiveness-netting rule (A1
§3.3.4) only bites when the cost *to the qualifying company* is reduced or reversed (a credit
note, waiver, or discount flowing back to the payer). A genuinely separate equity subscription —
new consideration (shares/units), investor at risk, subject to the production's profit or loss,
recorded as a capital contribution — is not a rebate and does not reduce the qualifying company's
recorded cost. It also does not create a *second* deduction: financing-side facts (how the film is
funded) and cost-side facts (what was eligibly spent) are decoupled in the statutory scheme — A1
§3.14 excludes financing costs (loan interest) from eligible expenditure precisely because
financing and cost are different questions; nothing suggests an equity contribution derived from a
qualifying fee increases eligible expenditure a second time. There is no "double dip" on the
expenditure side from reinvestment alone.

### 3.E — The real risk: same-cost / circular financing, not double QPE

The one place authority is emphatic is the **non-S.481 funding** requirement for a budgeted claim
(Regulation 7(2), A1 §5.3.2):

> "The funding must be made available by way of a cash contribution, for example, by way of a loan
> or subscription for shares or other cash investment. **It is not acceptable to provide the
> funding in non-cash form by, for example, deferring fees.**" (A1 §5.3.2; verbatim also in A5
> §5.4.1: "It is not acceptable to provide the non-s.481 amounts in non-cash form by, for example,
> deferring fees.")

If the fee just paid out to the vendor/producer is then routed back in as *the same investor's*
"cash contribution" satisfying the finance-agreement / 68%-lodgement requirement (Regulation
7(2)(b), Schedule 1 Tab D "details of the source of all amounts used to finance the entire
production"), this is not incremental capital — it is the qualifying company's own money leaving
and re-entering the production. No authority blesses this as satisfying the financing
requirement, and the structural tests aimed at exactly this (s.481(2A)(f)(ii) commercial
rationale; Schedule 1 Tab N's confirmation that no prohibited financial arrangement exists) point
the other way. **Treat a same-dollar fee-then-reinvest loop used to satisfy financing conditions
as `PROHIBITED`** absent a ruling establishing genuine incremental substance (a real time gap, a
real change in economic exposure, and disclosure that the "new" investment traces to the fee).

## 4. Anti-avoidance overlay (s.811C) and the absence of a general substance-over-form doctrine

s.811C (Ireland's codified GAAR, effective for transactions commenced after 23 October 2014,
confirmed applicable to reliefs and credits by subsection (4)(b)) denies a tax advantage from a
"tax avoidance transaction" — one where (i) it gives rise to a tax advantage, and (ii) it was
**not** undertaken primarily for purposes other than the tax advantage, *unless* it has a bona fide
commercial purpose or does not misuse/abuse the relief. Critically, **Irish courts have declined
to import a general Ramsay/Furniss-style "substance over form" doctrine** outside this specific
statutory test: in *McGrath v McDermott* [1988] IESC, the Supreme Court rejected the "fiscal
nullity" doctrine and held that a taxpayer's liability turns on ordinary statutory interpretation
of the enactments as they apply to the transaction actually entered into, not a judicially
imposed economic-substance override (A10).

**Practical consequence for this memo's fact patterns:** a fee-then-separate-reinvestment
structure that satisfies the literal statutory/regulatory conditions (WEN, arm's length, paid
within any deferral deadline, not contingent on profits, properly disclosed if related-party) is
not automatically recharacterized merely because, viewed broadly, cash ends up back in the
production. It is vulnerable specifically and only where it falls within s.811C's own test — no
bona fide commercial purpose beyond the tax advantage, or misuse/abuse of the relief's purpose —
which is a materially higher bar than "the money moved in a circle," but is squarely met by a
pre-arranged, same-party, package-deal round-trip of the kind flagged in §3.B/3.E.

## 5. EU state aid — a budget-level constraint, not a per-transaction test

Section 481 is EU state aid (A6 ¶18.45; A7 recital 25 onward). Under the 2013 Cinema
Communication as applied by the Commission's approval of the scheme (A7 recital 37, ¶52.2) and as
summarized by Screen Ireland (A8), **cumulative state aid from all sources may not exceed 50% of
the production budget** without a "difficult work" or low-budget derogation. This does not bear on
whether a fee is eligible expenditure, but it bears on the practical ceiling for any gross-up
strategy: to the extent a paid-then-reinvested structure is used to increase the *effective S.481
benefit* relative to a fixed budget (rather than to genuinely finance additional real spend), it
narrows headroom under the 50% cumulative cap and should be checked against total aid (S.481 +
Screen Ireland + Sound & Vision + any other public support) before being relied upon. This is an
independent constraint layered on top of, not a substitute for, the eligible-expenditure analysis
above.

## 6. Withholding — not implicated for a genuine fee to a company

Film Withholding Tax (s.529B–M TCA 1997, A9) applies only to "relevant payments" made to
**non-EU/EEA tax-resident artistes** for artistic services (20%, final), including indirect
payments via loan-out companies — it targets performer payments, not producer or vendor service
fees, and does not apply to Irish- or EEA-resident payees. No withholding obligation arises on a
genuine producer/vendor fee paid to an Irish or EEA company. If a "producer fee" is in substance a
disguised payment for a non-EU/EEA artiste's services, FWT exposure and a Reg. 12(g)/WEN
mischaracterization risk both arise — a further reason the fee must reflect real, substantiated
producer services and not a re-labelled talent payment.

## 7. Summary disposition table

| Structure | Fee eligibility (standing alone) | Complete fee-then-reinvest chain |
|---|---|---|
| Unrelated vendor, genuinely paid, vendor independently reinvests | `PERMITTED` (conditions: arm's-length pricing untainted by reinvestment; no contractual/economic linkage; real cash evidenced by bank statements) | `PERMITTED` if the two legs are genuinely independent; `RULING_REQUIRED` if linked |
| Related producer/overhead fee (TDM §3.3.2), reinvested into the same production | `PERMITTED_WITH_CONDITIONS` (WEN, arm's length, substantiated, ≥30% connected-party disclosure) | `RULING_REQUIRED` — no authority addresses the same-party round-trip; s.481(2A)(f)(ii) and s.811C exposure |
| Deferred fee, paid within 4 months (Reg. 12(g)), then reinvested | `PERMITTED_WITH_CONDITIONS` (genuine cash payment evidenced by bank statement within the 4-month window; not contra/set-off) | Same as the applicable row above by relatedness |
| Same-dollar fee routed back as the "cash contribution" satisfying Reg. 7(2) financing conditions | N/A (financing-side, not cost-side) | `PROHIBITED` absent a ruling establishing genuine incremental economic substance |
| Fee priced above market specifically to fund reinvestment, or reinvestment contractually conditions the fee | `PROHIBITED` — fails WEN/arm's-length and s.481(2A)(f)(i) inflated-expenditure test | `PROHIBITED` |

No authority uses the word "reinvestment." Every disposition above is reached by testing each
statutory/regulatory element the authorities actually impose (WEN, arm's length, payment timing,
non-contingency, connected-party disclosure, corporate-structure commercial rationale, s.811C) —
not by searching for and failing to find that word, and not by inferring permission from silence.
Where the authorities are genuinely silent on an element (the related-party round-trip; whether
non-cash settlement is "payment" for Reg. 12(g)), the disposition is `RULING_REQUIRED`, not
`PERMITTED`.

## 8. What a written ruling request should establish

See companion file `CLAUDE_IRELAND_S481_REINVESTMENT_TRANSACTION_CHECKLIST.csv` for the itemized
document/evidence checklist. At minimum, a ruling request for any related-party or circular-risk
variant of this structure should present: the service contract and deliverables; the fee
calculation and its relation to the 15%/10% parameters or its substantiation if above; independent
market comparison evidence for the rate; the payment date and bank evidence; the equity
subscription documents (shares/units issued, at-risk terms, cap-table effect); the time gap and
any contractual linkage (or its express absence) between the fee and the reinvestment; and the
production's total cumulative state aid position against the 50% ceiling.
