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
      <div className="fx-strip-row">
        <div className="fx-pair">
          <span className="mono fx-pair-code">USD</span>
          <span className="text-tertiary small">single-currency production — no FX pair applies</span>
          <span className="badge charcoal">no live source</span>
        </div>
        <div className="fx-history-entries" aria-label="Historical FX range — unavailable">
          {["1M", "6M", "12M"].map((label) => (
            <span key={label} className="ghost-action fx-history-chip" title="No historical FX snapshot table is populated for this workspace">
              {label}
            </span>
          ))}
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
