import { GLOBE_SEMANTIC } from "../lib/globeData";

// ── Four-state Globe legend (restored, explicit reversal of Phase 2) ────
//
// Phase 2's closeout deleted the persistent legend outright — the model at
// the time was six legacy database-state categories, and "learn the four
// states by hovering" was a reasonable bar for that smaller, corrected set.
// This authorization explicitly reinstates a legend, scoped tightly to
// prevent it becoming the old six-category panel again:
//
//   - EXACTLY the four current states (Recommended / Optimized alternative /
//     Unlockable opportunity / Additional), read live from GLOBE_SEMANTIC —
//     never a hand-written duplicate, so it cannot silently drift from the
//     Globe's own choropleth or the fixture badge's counts;
//   - no legacy wording anywhere (no "Qualified/viable", "Conditional", "No
//     known incentive", "Not evaluated", "Candidate jurisdictions" — this
//     component doesn't even have a code path that could reintroduce them,
//     since it only ever iterates GLOBE_SEMANTIC's four keys);
//   - visually secondary: small type, low-contrast chrome, positioned to sit
//     with the Globe rather than compete with it;
//   - production-visible (unlike the dev-only fixture badge) — this is
//     product chrome, not a debug aid.
export default function GlobeLegend({ className = "" }) {
  const order = ["gold", "jade", "amber", "silver"];
  return (
    <div className={`globe-legend-compact ${className}`.trim()} role="note" aria-label="Globe status key">
      {order.map((slot) => (
        <span key={slot} className="glc-item">
          <span className="glc-dot" style={{ background: GLOBE_SEMANTIC[slot].hex }} aria-hidden="true" />
          {GLOBE_SEMANTIC[slot].label}
        </span>
      ))}
    </div>
  );
}
