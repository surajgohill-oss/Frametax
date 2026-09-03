// CineGlobe Overview Top Four + Workspace incentive-display unification —
// the ONE compact-rate schema every compact card (Overview Top Four,
// Workspace) uses, reading only canonical per-segment rate_floor/
// rate_ceiling (already resolved by the optimizer — never recalculated
// here). Pure logic, no JSX/React — same separation lib/todayCompute.js
// and lib/productionOptions.js already use, so this stays independently
// unit-testable with plain `node` (format.jsx cannot be — it has real
// JSX and no test runner is installed in this frontend to transpile it).
//
//   A. Deterministic actual rate (floor == ceiling): "30%"
//   B. Deterministic base + a genuine unresolved attainable upside
//      (floor < ceiling): "30% · up to 35%" — both numbers shown, never
//      just the ceiling alone (which would silently drop the guaranteed
//      floor a producer can already count on).
//   C. An uplift that has already resolved to a single confirmed rate is
//      indistinguishable from A at this layer (floor == ceiling once
//      resolved) — no separate visual treatment needed.
//   D/E. A theoretical maximum this structure cannot itself claim, or a
//      genuinely discretionary/competitive award, is never represented
//      by a segment's own rate_floor/rate_ceiling (those only ever carry
//      THIS structure's own resolved incentive) — callers needing to
//      surface an external opportunity (Overview Top Four's Card 4) read
//      a different, explicitly-labeled field (conditional_programs'
//      documented_cap_usd) and must never format it through this
//      function, which would misrepresent it as an earned rate.
// Returns null when the structure has no incentive-claiming segment at
// all (e.g. a real CO_PRO_OPPORTUNITY structure) — never a fabricated
// "0%".
export function compactIncentiveRate(structure) {
  const segments = structure.segments || [];
  const claiming = segments.filter((sg) => sg.claims_incentive);
  const floors = claiming.map((sg) => sg.rate_floor).filter((r) => r != null);
  const ceilings = claiming.map((sg) => sg.rate_ceiling ?? sg.rate_floor).filter((r) => r != null);
  const ceiling = ceilings.length ? Math.max(...ceilings) : null;
  const floor = floors.length ? Math.min(...floors) : null;
  if (ceiling == null) return null;
  const isExactRate = floor != null && Math.round(floor * 10000) === Math.round(ceiling * 10000);
  if (isExactRate) return `${Math.round(ceiling * 100)}%`;
  if (floor == null) return `Up to ${Math.round(ceiling * 100)}%`;
  return `${Math.round(floor * 100)}% · up to ${Math.round(ceiling * 100)}%`;
}
