import { buildFxItems, buildLeaderFxItems } from "../lib/todayCompute";
import { flagEmoji } from "../lib/format.jsx";

// CineGlobe Overview FX Strip + Vertical Scrolling closeout — the ONE
// shared FX strip engine. Workspace.jsx used to carry its own inline copy
// of this exact render (`.wsx-fxstrip`/`.wsx-fx-*`, styled in
// screens.css, unchanged here); Overview never had a live one at all
// (its FXStrip import was removed in an earlier batch, deliberately
// deferring the compact-placement design rather than shipping a second
// engine — see Overview.jsx's own history comment). This component is
// now that placement, reused verbatim by both screens: one FX engine,
// one render path, generic across every production and screen that
// mounts it.
//
// `economics`: the real per-project economics payload — fx_horizons
// (current/1m/6m/12m per currency, ECB via frankfurter.dev / open.er-
// api.com — production_normalization.py's FX_RATE_SNAPSHOTS, never a
// live browser fetch), jurisdiction_currency, fx_source, fx_horizon_dates
// and fx_snapshot_version. The latter three already existed on the
// served payload (canonical_production_view.py) but were dropped before
// reaching any screen — repaired here, not invented: every currency pair
// shown is the SAME snapshot the optimizer's own FX normalization
// (production_normalization.compute_fx_normalization) consumes, so
// DISPLAYED FX == MODEL-CONSUMED FX by construction (one shared table,
// no second lookup).
// `structure`: the production's current Leading structure, or — when
// none is manually set and no canonical rank-1 exists — the same
// bestPricedCandidate(allocated) fallback the Hero/Budget Rail already
// use. Never a second "best" computation.
// `structureIsLeading`: true when `structure` is a real producer
// selection, false when it is the Top Priced fallback — drives the cell
// tag text only.
export default function FXStrip({ economics, structure, structureIsLeading }) {
  const dynamicLabel = structureIsLeading ? "LEADING" : (structure ? "TOP PRICED" : null);
  // buildLeaderFxItems lives in lib/todayCompute.js, a pure "no React, no
  // DOM" module (independently testable with plain `node`) — it returns
  // each leader item's raw `jurisdiction` rather than a resolved flag, and
  // this presentation layer resolves the flag via the one shared
  // flagEmoji() implementation. The fixed trio's flags come from
  // buildFxItems' own static FX_FLAGS map (no jurisdiction to resolve).
  const fxItems = [
    ...buildFxItems(economics?.fx_horizons),
    ...buildLeaderFxItems(economics, structure, dynamicLabel).map((it) => ({
      ...it, flag: it.jurisdiction ? flagEmoji(it.jurisdiction) : it.flag,
    })),
  ];

  const asOf = economics?.fx_horizon_dates?.current || null;
  const source = economics?.fx_source || null;

  return (
    <section className="wsx-fxstrip">
      <div className="wsx-fx-row">
        {fxItems.map((it) => (
          <div className={`wsx-fx-item ${it.isLeader ? "leader" : ""}`} key={`${it.code}-${it.isLeader ? "leader" : "fixed"}`}>
            <div className="wsx-fx-head">
              <span className="wsx-fx-flag" aria-hidden="true">{it.flag}</span>
              <span className="wsx-fx-code">{it.code}</span>
              {it.isLeader && it.leaderLabel && <span className="wsx-fx-tag">{it.leaderLabel === "LEADING" ? "Leading" : "Top Priced"}</span>}
              {it.available && it.deltaPct != null && (
                <span className={`wsx-fx-delta ${it.deltaPct > 0 ? "up" : "down"}`} title={`12-month move on USD/${it.code}`}>
                  {it.deltaPct > 0 ? "▲" : "▼"} {Math.abs(it.deltaPct).toFixed(1)}%
                </span>
              )}
            </div>
            {it.noConversion ? (
              <div className="wsx-fx-rates">
                <span className="l2 text-tertiary small">No conversion applies — already {it.code}-denominated.</span>
              </div>
            ) : (
              <div className="wsx-fx-rates">
                <div className="wsx-fx-pair">
                  <span className="l2">USD / {it.code}</span>
                  <span className={`wsx-fx-val mono ${it.available ? "" : "wsx-fx-unavailable"}`}>
                    {it.available ? it.current : "rate unavailable"}
                  </span>
                </div>
                <div className="wsx-fx-pair">
                  <span className="l2">{it.code} / USD</span>
                  <span className={`wsx-fx-val mono ${it.available ? "" : "wsx-fx-unavailable"}`}>
                    {it.available ? it.reverse : "rate unavailable"}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      <p className="text-tertiary small wsx-fx-note">
        {source ? `Source: ${source}.` : "Source: unavailable this pass."}{" "}
        {asOf ? `As of ${asOf}.` : "As-of date unavailable this pass."}{" "}
        Reverse pairs derive from the same rate; the optimizer prices at current rates, not forward movement.
      </p>
    </section>
  );
}
