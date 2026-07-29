import { useEffect, useState } from "react";
import { STATUS_HEX, STATUS_LABEL, GRAPHITE_HEX } from "../lib/globeData";
import { getTheme, subscribeTheme } from "../lib/theme";

// The Globe repaints not-evaluated land to a navy-slate in night mode so it
// shares a hue family with the ocean. The legend swatch must track that, or
// the key stops describing what is actually on screen.
const GRAPHITE_NIGHT_HEX = "#4a5570";

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
  const [theme, setTheme] = useState(getTheme);
  useEffect(() => subscribeTheme(setTheme), []);
  const graphite = theme === "night" ? GRAPHITE_NIGHT_HEX : GRAPHITE_HEX;
  return (
    <div className={`globe-legend ${className}`.trim()}>
      {ORDER.map((s) => (
        <span key={s}>
          <span className="globe-legend-dot" style={{ background: STATUS_HEX[s] }} />
          {STATUS_LABEL[s]}
        </span>
      ))}
      <span>
        <span className="globe-legend-dot" style={{ background: graphite }} />
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
