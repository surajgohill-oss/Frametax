# MFNI, TRAVEL, LODGING & BELOW-THE-LINE PRODUCTION COST BOUNDARY

**Document Version:** 1.0  
**Date:** October 9, 2026  
**Status:** Canonical Optimizer Architectural Boundary  

---

## 1. PURPOSE AND CANONICAL STATUS

This document defines the strict, non-negotiable boundary between CineGlobe's current production-cost normalization engine and the future Below-The-Line (BTL) Model for Normalized Inflation (MFNI).

Per `PROJECT_RULES.md`:
> Co-production, stacking, component-routing, and optimizer work must begin from current canonical knowledge and must not restart jurisdiction research by default.
> The separate MFNI research branch (`ag/mfni-global-btl-research`) contains research artifacts and is NOT accepted canonical data.

---

## 2. WHERE CURRENT OPTIMIZER ECONOMICS MODEL TRAVEL AND RELOCATION

In the current canonical optimizer (`canonical-1.105.0`), cost adjustments are strictly confined to deterministic relocation frictions and currency differentials:

1. **Travel Incremental Delta (`travel_incremental_delta_usd`):**
   - Applied in `production_adjustment.py` when physical production moves outside the primary home territory.
   - Models direct airfare and freight friction for non-resident keys and core crew.
2. **Foreign Exchange Delta (`fx_delta_usd`):**
   - Currency hedging and conversion cost adjustments based on `fx_rates` database table.
3. **Local Implementation Friction (`implementation_cost_usd`):**
   - Statutory administration, SPV legal formation, and audit fees required to qualify for foreign tax credits.
4. **In-Kind Replacement Delta (`inkind_replacement_delta_usd`):**
   - Monetization discount applied to transferable tax credits sold to third-party corporate sponsors.

---

## 3. WHERE BTL / MFNI COST NORMALIZATION IS CURRENTLY DEFERRED

The following Below-The-Line cost dimensions are NOT dynamically modeled in the current optimizer:

- **Local Crew Labor Wage Rate Differentials:** (e.g. difference between IATSE Local 800 Los Angeles rates vs. Mauritius or Greece crew wage scales).
- **Hotel / Apartment Lodging Rates:** (e.g. per-room-night seasonal variance in regional filming hubs).
- **Per Diem and Catering Costs:** (statutory or union meal penalties and food costs).
- **Studio Stage Rental Inflation:** (per-square-foot grid stage rate normalization).

### The Canonical Preservation Rule
Every economic card in Workspace and Overview explicitly preserves the required placeholder text:
```
MFNI ADJUSTMENT NOT YET MODELED
NPC AFTER MFNI —
Assumptions editing not yet available
```
**Strict Prohibition:** The optimizer engine must NOT silently apply unvetted labor rate multipliers or import AG's 121-jurisdiction research figures into production acceptance databases until a formal BTL consensus is commissioned and approved.
