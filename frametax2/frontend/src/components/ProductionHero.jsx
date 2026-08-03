import { Money } from "../lib/format";
import { humanizeToken, jurisdictionName } from "../lib/format";
import heroArt from "../assets/production-art/little-utopia-hero.png";

// Overview-only cinematic replacement for the compact `.project-header`
// bar. Rendered by ProjectHeader.jsx ONLY when the current route is
// /production/overview — every other production route keeps the existing
// compact bar completely untouched (see ProjectHeader.jsx's branch).
//
// Every field below is read from the SAME `data` object ProjectHeader
// already fetches via useCineGlobe() — no new request, no new derivation
// that doesn't already exist elsewhere in the app (recommended-structure
// resolution mirrors Overview.jsx's own `snapshot`/`structure` logic;
// question-count/swing mirrors ProjectHeader's existing compact-bar calc).
//
// The supplied key art (frontend/src/assets/production-art/
// little-utopia-hero.png) has its own title typography baked in. That
// typography is decorative background only — ALL production information
// on screen is live DOM, per instruction. The gradient below is tuned to
// suppress the baked text into pure atmosphere while keeping the
// photography (the Santorini village, the sunset, the sailboat) visible,
// and to guarantee contrast for the real title/metrics sitting on top.
export default function ProductionHero({
  production,
  topStructure,
  stageControl,
  openQuestions,
  swing,
  onBack,
  headerActions,
}) {
  const recommendedJurisdiction = topStructure?.primary_jurisdiction
    ? jurisdictionName(topStructure.primary_jurisdiction)
    : null;
  const recommendedType = topStructure?.structure_type
    ? humanizeToken(topStructure.structure_type)
    : null;

  return (
    <div className="ph-hero" style={{ backgroundImage: `url(${heroArt})` }}>
      <div className="ph-hero-scrim" aria-hidden="true" />
      <div className="ph-hero-topbar">
        <button className="ph-back ph-hero-back" onClick={onBack}>← Today</button>
        {headerActions}
      </div>
      <div className="ph-hero-row">
        <div className="ph-hero-identity">
          <h1 className="serif ph-hero-title">{production?.production_name || "—"}</h1>
          <p className="ph-hero-sub">Feature Film</p>
          {stageControl}
        </div>

        <div className="ph-hero-metrics">
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-value mono">
              {production ? <Money value={production.gross_budget_usd} /> : "—"}
            </span>
            <span className="ph-hero-metric-label">Production Budget</span>
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-value mono">
              {topStructure ? <Money value={topStructure.npc_with_adjustments_usd} /> : "—"}
            </span>
            <span className="ph-hero-metric-label">Net Production Cost</span>
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-value">{recommendedJurisdiction || "—"}</span>
            <span className="ph-hero-metric-label">
              Recommended Structure{recommendedType ? ` · ${recommendedType}` : ""}
            </span>
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-value mono">{openQuestions}</span>
            <span className="ph-hero-metric-label">
              Question{openQuestions === 1 ? "" : "s"} Remaining
              {swing ? ` · ±$${Math.round(swing).toLocaleString()} at stake` : ""}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
