# MFNI, TRAVEL, LODGING & BELOW-THE-LINE BOUNDARY SPECIFICATION

**Controlling Directive:** Preservation of Model Boundaries & Statutory Normalization  
**Engine Version:** `canonical-1.105.0`  

---

## 1. ARCHITECTURAL BOUNDARY MANDATE

This document formalizes the boundary between CineGlobe's actively modeled economic friction modules and below-the-line normalization inputs currently held static or unmodeled.

> **CRITICAL RULE:** Unmodeled cost normalization adjustments must NEVER be silently imputed, backfilled, or assumed. Where statutory or market wage differentials are not explicitly implemented, the system strictly outputs:
> `MFNI ADJUSTMENT NOT YET MODELED`

---

## 2. 13-ITEM BELOW-THE-LINE COST OWNERSHIP MATRIX

| # | Cost Item Category | Operational Scope | Current Engine Status | Ownership & Boundary Treatment |
| :- | :--- | :--- | :--- | :--- |
| **1** | **ATL Key Cast Relocation** | Cross-border airfare deltas | **MODELED** | Calculated via `travel_model.py` based on originating residency and shoot location. |
| **2** | **ATL Director & Producer Travel** | Executive travel & per diems | **MODELED** | Governed by `calculate_key_crew_travel.py` with statutory caps applied. |
| **3** | **BTL Crew Relocation** | Department head travel | **STATIC** | Modeled as fixed percentage of BTL spend; subnational mileage held static. |
| **4** | **Local Production Wage Scales** | BTL union/guild daily rates | **UNMODELED** | `MFNI ADJUSTMENT NOT YET MODELED` |
| **5** | **Hotel & Crew Lodging** | Location accommodations | **UNMODELED** | `MFNI ADJUSTMENT NOT YET MODELED` |
| **6** | **Per Diem Allowances** | Meals & incidental rates | **STATIC** | Federal/statutory standard rates applied without seasonal adjustments. |
| **7** | **Equipment Rental Differentials** | Camera, grip, lighting package | **STATIC** | Regional rate multiplier indexed against US-CA baseline. |
| **8** | **Stage & Facility Rentals** | Soundstage daily stage rates | **STATIC** | Square-footage standard rates without peak-demand surcharges. |
| **9** | **Post-Production Facilities** | Editorial & sound mixing rooms | **MODELED** | Component relocation allocator partitions spend to destination stage. |
| **10** | **VFX Vendor Differentials** | Digital visual effects artist hours | **MODELED** | Tracked via dedicated VFX account lines and regional labor incentives. |
| **11** | **Currency Volatility (FX)** | Hedging & exchange drift | **MODELED** | Spot rate conversion with statutory hedging friction applied. |
| **12** | **Financing & Discount Friction** | Production loan interest & bridge | **MODELED** | Evaluated via `financing_interaction_model.py` per jurisdiction risk tier. |
| **13** | **Local Legal & Tax Administration** | CPA audit & entity compliance | **MODELED** | Deducted as structural implementation cost from net benefit. |

---

## 3. PRESERVATION OF PLACEHOLDER INTEGRITY

In accordance with architectural standards:
1. No synthetic cost indexes may be introduced without primary empirical labor surveys.
2. The UI and API contracts explicitly preserve: `MFNI ADJUSTMENT NOT YET MODELED`
