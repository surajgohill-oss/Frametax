# CINEGLOBE GLOBE / OPTIMIZER UI REFINEMENT REVIEW

## 1. FROZEN CONTRACT UNDERSTOOD
The design contract mandates the retention of the "Option A - Luxury Glass Globe" with its existing 3D geometry and shell layout (no new visual languages, dashboards, or top-level navigation changes). The core interaction revolves around the existing "Jurisdictions / Optimizer Overlay" toggle:
- **Jurisdictions Mode:** Answers "Where can this operate?" showing single programs and local stacks per jurisdiction without duplicating the jurisdiction card.
- **Optimizer Overlay Mode:** Answers "How can combining locations improve results?" exclusively for multi-jurisdiction structures (Co-pro, Hybrid/Anchor) without losing local stack context inside the participants.
Colors encode economic status (Gold=Leading, Jade=Optimize, Silver=Viable, Amber=Opportunity, Muted/Faded=N/A or No Incentive) and must not be repurposed for structure types. Red is exclusively for rejections/legal blockers. Opportunity denotes actionable pathways, not automatic entitlements or blind assumptions.

## 2. CURRENT OBSERVED IMPLEMENTATION
- **Runtime:** UNAVAILABLE (Local ports 3000/5173/8080 unresponsive).
- **Source Review:** PARTIAL but conclusive via `Workspace.jsx`, `AppShell.jsx`, `Inspector.jsx`, `tokens.css`, and `shell.css`.
- **Layout:** The shell relies on a CSS Grid (`48px/340px | 1fr | 290px` collapsed/expanded) with max-width content capping around 1520px. 
- **Tokens:** The color palette (Gold, Jade, Silver, Amber, Red, Charcoal, Blue, Green, Oxblood) and base text sizing (12.5px/13px) are correctly declared.

## 3. EXACT GAPS FROM THE CONTRACT
1. **Inspector Squeeze:** The current `290px` Narrow Inspector is too tight to securely render 8-digit tabular monetary totals inline with long program names without wrapping, causing layout shifts.
2. **Missing Opportunity Distinction:** The source shows a single `OpportunityMeter`, but lacks a clear visual distinction between "executable economics" and "conditional estimates" (like grey-area reinvestment) without relying on new colors.
3. **Co-Production Creative Context:** The UI handles geographic allocations (routes) but lacks a dedicated state in the wide analysis surface to expose the treaty-specific creative point system (Writer/Director/Cast) effectively.
4. **Data Table Formatting:** `Money` components are currently not strictly tabular/right-aligned in some flex layouts (`Inspector.jsx` uses standard flex gaps).

## 4. PRIORITIZED REFINEMENTS (MAX 8)
1. **Inspector Width Expansion:** Expand the Narrow Inspector column from `290px` to `320px` to safely accommodate tabular `Money` values alongside long jurisdiction/program labels.
2. **Tabular Numerals & Alignment:** Apply `font-variant-numeric: tabular-nums` and strict right-alignment to all `<Money />` and `<Pct />` elements globally to permit rapid vertical scanning.
3. **SVG Flag Integration:** Replace operating system emojis with accessible SVG vector flags for states/provinces (e.g., Ontario, New York) to ensure cross-platform visual consistency.
4. **Anchor Emphasis:** In Optimizer Overlay mode, apply a `2px` solid border using the appropriate token status color (e.g., `--gold`) to the Anchor jurisdiction, while partner routes use a `1px` dashed/bezier line.
5. **Stack Badging:** Apply a subtle internal badge (`var(--surface-cool)`) indicating `[+X Programs]` on jurisdiction cards in Jurisdiction mode, preventing duplicate jurisdiction entries while clearly signaling a stack.
6. **Wide Analysis Layout (Hub & Spoke):** Implement a strict 3-column max-width (`1200px`) layout for the Wide Analysis Spoke: Left (`300px` Alternatives), Center (`1fr` Economics/Allocations), Right (`320px` Rules/Treaty Context).
7. **Opportunity Disclosures:** Use the existing `--amber` and `--surface-conditional` tokens with a distinct icon (e.g., an open checkbox) to denote requirements that block executable economics.
8. **Scroll Ownership:** Ensure `.inspector-table` and `dl.kv-list` scroll vertically while keeping `.inspector-eyebrow` sticky at the top, preventing the user from losing context.

## 5. ANNOTATED SCREENSHOTS
*Note: Conceptual outline due to headless/unverified runtime.*
- **[PROPOSED VIEW: Optimizer Overlay]**
  - **Center Map:** Shows `United Kingdom` (Anchor, 2px Gold Border) connected via a 3D Bezier arc to `Ontario` (Partner, 1px Gold arc).
  - **Left Stack:** Hidden or collapsed to 48px to maximize map.
  - **Right Inspector (320px):** 
    - *Header:* UK/Canada Official Co-production (Gold).
    - *Body:* UK Global Screen Fund + Ontario Film & TV Tax Credit.
    - *Totals:* Right-aligned tabular NPC.

## 6. COMPACT LAYOUT ILLUSTRATION
```text
+---------------------------------------------------------+
| [Header 60px] CineGlobe   [Jurisdictions | OVERLAY]     |
+----+---------------------------------------+------------+
| Q  |                                       | NARROW     |
| U  |                                       | INSPECTOR  |
| E  |       [Option A - Glass Globe]        | (320px)    |
| S  |             1fr min-width: 600px      |            |
| T  |                                       | - Title    |
| I  |        (Anchor: UK) <---- (Partner)   | - Totals   |
| O  |           [Gold]           [Gold]     | - Stacks   |
| N  |                                       | - Details  |
| S  |                                       |            |
+----+---------------------------------------+------------+
```

## 7. INTERACTION / STATE MAPPING
- **Toggle -> Jurisdictions Mode:** Sets `canonical_structure_id` to single locations. Renders local stacks. Optimizer routes disappear.
- **Toggle -> Optimizer Overlay:** Sets `canonical_structure_id` to multi-jurisdiction packages. Local stacks remain nested *inside* the participants in the Inspector.
- **Globe Selection / Click:** Updates global selected context. Narrow Inspector instantly updates to reflect the clicked node (either a single jurisdiction or a routed hybrid structure).
- **"View Analysis" Click:** Transitions from Narrow Inspector (320px) to Wide Analysis Surface (max 1200px). Map dims slightly (no layout shift, just overlay) while preserving state.

## 8. BACKEND PAYLOAD FIELDS VS UNVERIFIED
- **Existing Fields Observed:** `local_entity_required`, `cultural_test_threshold`, `min_total_budget_usd`, `per_project_cap_usd`, `refundable`, `transferable`, `evidence`.
- **Missing/Unverified Frontend Fields:** `creative_quota_points` (for Co-pro writer/director/cast verification), `stacking_mutual_exclusivity_flags`, and `anchor_vs_component_designation`. The UI requires explicit boolean/string flags for anchor vs component to style routes correctly.

## 9. BOUNDED FUTURE UI IMPLEMENTATION RECOMMENDATION
Update `Workspace.jsx` CSS Grid to `gridTemplateColumns: ${!qOpen ? "48px" : "340px"} 1fr 320px`. Modify `<Money />` to apply `font-variant-numeric: tabular-nums; text-align: right;`. Update `Globe3D` materials to explicitly read the `is_anchor` property from the structure payload to assign the `2px` border weight. Do not introduce Redux, do not migrate off Three.js, and do not rebuild the navigation shell.

## 10. UNTOUCHED ELEMENTS
- `Globe3D` base materials, camera, and rotation.
- App shell routing and navigation rail.
- Base color token hex values (Gold, Jade, Silver, Amber, Red).
- The fundamental definitions of Leading, Optimize, Viable, Opportunity.
- Legacy fallback behaviors for older production types.
