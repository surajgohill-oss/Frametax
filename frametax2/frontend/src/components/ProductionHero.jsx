import { Money } from "../lib/format";
import { humanizeToken, jurisdictionName } from "../lib/format";
import heroArt from "../assets/production-art/little-utopia-hero-banner.png";

// Shared production identity header — rendered by ProjectHeader.jsx on
// ALL 8 production routes (Overview, Workspace, Scenarios, Project Globe,
// Documents, Record, Knowledge, Reports). One ProductionHero instance,
// one artwork, no per-route crops.
//
// Every field below is read from the SAME `data` object ProjectHeader
// already fetches via useCineGlobe() — no new request, no new derivation
// that doesn't already exist elsewhere in the app (recommended-structure
// resolution mirrors Overview.jsx's own `snapshot`/`structure` logic;
// question-count/swing mirrors ProjectHeader's existing compact-bar calc).
//
// PRODUCTION SHELL CLOSEOUT (asset-level fix): the original key art
// (little-utopia-hero.png, 1659x948, aspect ~1.75:1) could never fit this
// hero's actual rendered shape (measured 4.99:1 at 1440px up to 6.98:1 at
// 1920px, canonical 1600px ≈5.65:1) without either showing a tiny sliver
// of the image or repeatedly re-tuning background-size/position — the
// asset's own geometry was the problem, not the CSS. `little-utopia-
// hero-banner.png` is a purpose-built derivative: a horizontal band
// cropped from the same source (full 1659px width, y640-948, ratio
// 5.386:1 — within the measured target range) chosen by direct pixel
// measurement to sit safely below the baked subtitle text (which a row-
// brightness scan confirmed ends at y568, giving this crop a 72px margin)
// while keeping the full sailboat, the rocky coastline, sunset reflection,
// and enough of the village (steps, blue door, flowers, white walls) that
// the intended village → coast → sea → sunset read survives. No baked
// typography survives in this derivative at all (the crop excludes that
// entire vertical band, not just at one viewport). See the Asset-Aspect-
// Ratio permanent rule in CAPABILITY_LEDGER.md.
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
