/**
 * apply_fx_rates.py converts using a caller-supplied rate table — it has
 * no live-fetch capability wired into this backend today. /economics does
 * serve a real fx_horizons table (current/1m/6m/12m forward points per
 * currency), populated for EUR and GBP; MUR carries only a current spot
 * with no forward curve. Every figure below is that real table — the
 * "commentary" is a plain factual delta between two already-fetched
 * numbers (current → 12m), never a fabricated "consensus" opinion, and it
 * never feeds back into optimizer calculations (those stay on current
 * rates only, per production_structure_default on /economics).
 */
function pctDelta(from, to) {
  if (from == null || to == null || from === 0) return null;
  return ((to - from) / from) * 100;
}

function trendNarrative(code, horizon) {
  const delta = pctDelta(horizon.current, horizon["12m"]);
  if (delta == null) {
    return `No forward curve populated for ${code} — spot only.`;
  }
  const direction = delta > 0 ? "strengthens" : delta < 0 ? "weakens" : "holds flat";
  return `Forward curve implies USD ${direction} against ${code} by ${Math.abs(delta).toFixed(1)}% over 12 months (${horizon.current} → ${horizon["12m"]}).`;
}

export default function FXStrip({ economics }) {
  const horizons = economics?.fx_horizons || {};
  const codes = Object.keys(horizons);

  if (codes.length === 0) {
    return (
      <div className="fx-strip">
        <div className="fx-strip-row">
          <div className="fx-pair">
            <span className="mono fx-pair-code">USD</span>
            <span className="text-tertiary small">single-currency production — no FX pair applies</span>
            <span className="badge charcoal">no live source</span>
          </div>
        </div>
        <p className="text-tertiary small fx-commentary">
          <strong className="text-secondary">Rate:</strong> unavailable — apply_fx_rates.py converts from a
          caller-supplied snapshot table, and none has been populated for this workspace.{" "}
          <strong className="text-secondary">Currency normalization:</strong> not required here — Little
          Utopia's budget is already USD-denominated end to end, so no conversion is applied to any figure
          shown in this workspace.
        </p>
      </div>
    );
  }

  return (
    <div className="fx-strip">
      {codes.map((code) => {
        const h = horizons[code];
        return (
          <div className="fx-strip-row" key={code} style={{ marginBottom: 6 }}>
            <div className="fx-pair">
              <span className="mono fx-pair-code">USD/{code}</span>
              <span className="mono text-secondary small">{h.current}</span>
            </div>
            <div className="fx-history-entries" aria-label={`${code} forward curve`}>
              {["1m", "6m", "12m"].map((k) => (
                <span
                  key={k}
                  className="ghost-action fx-history-chip"
                  title={h[k] == null ? `No ${k.toUpperCase()} forward point populated` : `${k.toUpperCase()} forward: ${h[k]}`}
                >
                  {k.toUpperCase()}{h[k] != null ? ` ${h[k]}` : ""}
                </span>
              ))}
            </div>
          </div>
        );
      })}
      <p className="text-tertiary small fx-commentary">
        {codes.map((code) => trendNarrative(code, horizons[code])).join(" ")}{" "}
        <strong className="text-secondary">Optimizer impact:</strong> none — the allocation and pricing engine
        prices every structure at <em>current</em> rates only; these forward points are commentary, never an
        input to any cost calculation.
      </p>
    </div>
  );
}
