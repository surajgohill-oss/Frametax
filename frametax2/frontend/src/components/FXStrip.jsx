/**
 * apply_fx_rates.py converts using a caller-supplied rate table — it has
 * no live-fetch capability wired into this backend today (see engine
 * docstring: "Live fetch populates the table; calculations use
 * snapshots"). No snapshot exists for Little Utopia. Per the "never
 * fabricate a rate" rule, this renders the strip's real state:
 * unavailable, clearly labeled, not a placeholder number.
 */
export default function FXStrip() {
  return (
    <div className="fx-strip">
      <div className="fx-pair">
        <span className="mono fx-pair-code">USD</span>
        <span className="text-tertiary">·</span>
        <span className="badge charcoal">unavailable</span>
      </div>
      <p className="text-tertiary small" style={{ margin: 0 }}>
        No FX rate source configured for this workspace — apply_fx_rates.py converts from a
        caller-supplied snapshot table, and none has been populated. Little Utopia's budget is
        already USD-denominated end to end.
      </p>
    </div>
  );
}
