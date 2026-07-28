import { STATUS_HEX, STATUS_LABEL } from "../lib/globeData";

// The single source of the Globe's status key. Every Globe surface renders
// THIS component rather than its own hand-written colour list, so the
// legend can never drift out of sync with the choropleth or with another
// screen's wording (both of which had happened before this was extracted).
const ORDER = ["gold", "jade", "amber", "silver", "darkRed"];

// Unevaluated landmass carries no status entry at all — it is the neutral
// graphite base the choropleth sits on. It has no STATUS_HEX key because
// it is the absence of a verdict, so it is declared here explicitly and
// kept last, after the five real production statuses.
// Must match Globe3D.jsx's NEUTRAL_FILL exactly — this swatch is a
// duplicate by necessity (the legend has no live reference to the Globe's
// own module-scope constant), not an independent colour choice.
const GRAPHITE_SWATCH = "#4a4136";

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
        <span className="globe-legend-dot" style={{ background: GRAPHITE_SWATCH }} />
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
