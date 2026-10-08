# Economic card interior hierarchy (Overview + Workspace)

Status: implemented 2026-10-08 (Ledger Item 11). The Gemini V2 document was design input only; this file is the controlling record and
overrides its dimensions, scrolling, percentages, repeated budget and MFNI claims.

## Locked structure
Overview: four cards (Current Location, Leading Jurisdiction, Optimized Structure, Conditional Upside), selection unchanged. Workspace: six
cards, 320px wide, 439px tall, 3 -> 2 -> 1 reflow unchanged. No horizontal scroll. One shared interior: `frontend/src/components/EconomicWell.jsx`.

## Field order (both cards)
1. Title (up to two lines, full title in the tooltip).
2. Existing structural category (ANCHOR, LEADING, REFERENCE ALTERNATIVE, LOW-LOCATION-FIT REFERENCE, ...). A structure is never labelled CONDITIONAL.
3. Maximum-potential NPC: the dominant figure (28px Workspace, 24px / 20px Overview).
4. Confirmed NPC: the clear secondary comparison.
5. Confirmed incentive and maximum-potential incentive in dollars.
6. Confirmed-versus-potential bar.
7. MFNI placeholder.
8. Attainability headline plus one requirement.
9. Existing actions (Workspace: Inspect / Compare / Set as leading; Overview: Exclude where it applies).
Workspace only: Qualified spend as quiet subordinate context after the well, never before NPC. Gross Budget appears in no card; Overview prints
it once above its grid ("Production Budget $X USD"). Qualified spend is omitted from Overview. No rate, yield or percentage is on a card face.

## Bar
One full-width track. Jade = confirmed incentive / maximum-potential incentive; amber = the unconfirmed delta / maximum (the remainder); one 1px
separator between them. Confirmed equals maximum: all jade. Confirmed zero with a positive maximum: all amber. No maximum: neutral empty
track. Labels: the confirmed dollar amount and the additional potential delta (served `potential_upside_usd`) only. Never scaled against Gross Budget.

## Attainability (served facts only, `lib/incentivePotential.js attainability()`)
`Maximum confirmed from known facts` | `Maximum requires 1 approval` | `Maximum requires N facts` | `Maximum requires 1 approval and 2 facts` |
`Maximum not established from known facts`. The requirement is the first clause of the first served missing fact with any rate removed; two lines,
then `+N more in Inspector`. "Locked", "guaranteed" and "statutory entitlement" are not used. `Not Suitable` is reserved for a confirmed fit mismatch.

## MFNI placeholder (not calculated)
Stable reserved rows: `MFNI ADJUSTMENT NOT YET MODELED`, `NPC AFTER MFNI —`, and `Assumptions editing not yet available`. Future data turns these into
`MFNI ADJUSTMENT −$X` / `NPC AFTER MFNI $Y`. No assumptions surface for MFNI exists today (Overview's contingency / finance-cost lines are budget
assumptions, not MFNI), so no button is shown. Next MFNI task: define the served MFNI field and wire an assumptions editor.

## Typography
Existing families only (`--font-sans`, `--font-serif` titles, `--font-mono` figures), tabular lining numerals, sentence-case labels at 11-13px, fixed
row heights so equivalent rows align across cards. Overview narrows by container query below 170px (the 1280px layout).
