import { STATUS_HEX, STATUS_LABEL, GRAPHITE_HEX } from "../lib/globeData";

// The single source of the Globe's status key. Every Globe surface renders
// THIS component rather than its own hand-written colour list, so the
// legend can never drift out of sync with the choropleth or with another
// screen's wording (both of which had happened before this was extracted).
const ORDER = ["gold", "jade", "amber", "silver", "darkRed"];

// Unevaluated landmass carries no status entry at all — it is the neutral
// graphite base the choropleth sits on, kept last after the five real
// production statuses. It now comes from globeData.js's GRAPHITE_HEX, the
// same constant Globe3D.jsx fills the polygon with, so the legend swatch
// and the Globe can no longer drift apart (they previously held separate
// hand-synced copies of this value).

export default function GlobeLegend({ showTreatyPath = false, className = "" }) {
  return (
    <div className={`globe-legend ${className}`.trim()}>
      {ORDER.map((s) => (
        <span key={s}>
          <span className="globe-legend-dot" style={{ background: STATUS_HEX[s] }} />
          {STATUS_LABEL[s]}
        </span>
      ))}
      <span>
        <span className="globe-legend-dot" style={{ background: GRAPHITE_HEX }} />
        Not evaluated
      </span>
      {showTreatyPath && (
        <span>
          <span className="globe-legend-dash" />
          Structure route
        </span>
      )}
    </div>
  );
}
