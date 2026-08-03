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
// little-utopia-hero.png, 1659x948) has its own title typography baked in
// — measured directly (pixel analysis, not eyeballed): "The Little Utopia"
// spans y223-418, the "A FEATURE FILM / MEDITERRANEAN DRAMA" subtitle spans
// y511-568. The crop (see .ph-hero-art in shell.css: `108% auto` /
// `center bottom`) stays clear of that band at every required viewport —
// a plain `cover`+percentage-position attempt regressed at 1440px because
// the vertical crop window's source-pixel size grows as a fixed-height
// container narrows, confirmed by screenshot and fixed by anchoring to
// the image's own bottom edge instead of a percentage of that moving
// window. Still shows the base of the village architecture, the lower
// two-thirds of the sailboat silhouette (y472-947), open sea, and the
// sunset's reflection on the water. The artwork is its OWN
// absolutely-positioned layer (`.ph-hero-art`), independent of the scrim
// and of the text layout — never coupled to hero content geometry.
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
    <div className="ph-hero">
      {/* Artwork layer — absolutely positioned, overflow-clipped by `.ph-hero`,
          scaled/positioned entirely independently of the text layout below.
          `background-position` percentages are resolution-independent (the
          same math as `object-position`), so this crop holds at every
          viewport without a breakpoint of its own. */}
      <div className="ph-hero-art" style={{ backgroundImage: `url(${heroArt})` }} aria-hidden="true" />
      {/* Overlay: directional, not uniform — strongest behind the identity
          block (left) and in a shallow band at the bottom (grounding into
          the tabs), much lighter behind the metrics (right) and near-clear
          through the middle, so the sea/sunset the artwork layer now
          actually shows is not multiplied back into near-black. */}
      <div className="ph-hero-scrim" aria-hidden="true" />
      <div className="ph-hero-topbar">
        <button className="ph-back ph-hero-back" onClick={onBack}>← Today</button>
        {headerActions}
      </div>
      <div className="ph-hero-row">
        <div className="ph-hero-identity">
          <h1 className="serif ph-hero-title">{production?.production_name || "—"}</h1>
          <div className="ph-hero-identity-sub">
            <p className="ph-hero-sub">Feature Film</p>
            {stageControl}
          </div>
        </div>

        <div className="ph-hero-metrics">
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-label">Production Budget</span>
            <span className="ph-hero-metric-value mono">
              {production ? <Money value={production.gross_budget_usd} /> : "—"}
            </span>
            <span className="ph-hero-metric-caption">Total estimated budget</span>
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-label">Net Production Cost</span>
            <span className="ph-hero-metric-value mono">
              {topStructure ? <Money value={topStructure.npc_with_adjustments_usd} /> : "—"}
            </span>
            <span className="ph-hero-metric-caption">After incentives and rebates</span>
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-label">Recommended Structure</span>
            <span className="ph-hero-metric-value">{recommendedJurisdiction || "—"}</span>
            {recommendedType && <span className="ph-hero-metric-caption">{recommendedType}</span>}
          </div>
          <div className="ph-hero-sep" aria-hidden="true" />
          <div className="ph-hero-metric">
            <span className="ph-hero-metric-label">
              Question{openQuestions === 1 ? "" : "s"} Remaining
            </span>
            <span className="ph-hero-metric-value mono">{openQuestions}</span>
            {!!swing && (
              <span className="ph-hero-metric-caption">±${Math.round(swing).toLocaleString()} at stake</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
