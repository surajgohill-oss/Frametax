import { GLOBE_SEMANTIC } from "../lib/globeData";

// ── Four-state Globe legend — top-left, chrome-free (Phase 3B closeout) ──
//
// PHASE 3B GLOBE CLOSEOUT: three treatments tried, in order — a 10px
// horizontal chip (too small), a vertical panel with a near-opaque plate
// (read as a UI card), a vertical panel with a quiet translucent plate
// (still read as a container competing with the globe). FINAL: no
// container at all — just dot + label, anchored to the Globe viewport's
// true top-left corner, legible over any background via a text-shadow
// halo (see screens.css) rather than a plate behind it. The four-state
// contract from every prior pass is UNCHANGED and still structurally
// enforced:
//
//   - EXACTLY the four current states (Recommended / Alternatives /
//     Co-Production Opportunities / Excluded), read live from GLOBE_SEMANTIC
//     — never a hand-written duplicate, so it cannot silently drift from the
//     Globe's own choropleth or the fixture badge's counts;
//   - no legacy wording anywhere (no "Qualified/viable", "Conditional", "No
//     known incentive", "Not evaluated", "Candidate jurisdictions" — this
//     component doesn't even have a code path that could reintroduce them,
//     since it only ever iterates GLOBE_SEMANTIC's four keys);
//   - production-visible (unlike the dev-only fixture badge) — this is
//     product chrome, not a debug aid;
//   - `pointer-events: none` (see CSS) so it never intercepts a click meant
//     for the globe underneath or beside it.
//
// Uses `fullLabel` (the same long form hover already uses — "Co-Production
// Opportunities", not the compact chip's old "Co-Pro Opportunities") since a
// vertical stack has the width to spell it out.
export default function GlobeLegend({ className = "" }) {
  const order = ["gold", "jade", "amber", "silver"];
  return (
    <div className={`globe-legend-vertical ${className}`.trim()} role="note" aria-label="Globe status key">
      {order.map((slot) => (
        <span key={slot} className="glv-item">
          <span className="glv-dot" style={{ background: GLOBE_SEMANTIC[slot].hex }} aria-hidden="true" />
          {GLOBE_SEMANTIC[slot].fullLabel}
        </span>
      ))}
    </div>
  );
}
