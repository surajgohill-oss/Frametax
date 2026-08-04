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
// 1920px, canonical 1600px ≈5.65:1) — the asset's own geometry was the
// problem, not the CSS. A first derivative (a single horizontal band
// cropped from the source) technically avoided the baked title but lost
// the blue-domed church — the village's most identifiable feature — since
// the domes sit well above any band tall enough to also clear the text
// safely and short enough to hit the target ratio.
//
// `little-utopia-hero-banner.png` (1659x308, ratio 5.386:1) is instead a
// TWO-REGION composite of the SAME source photograph, both regions taken
// at native (unscaled, undistorted) pixel resolution so neither is
// stretched: a village panel (x0-460, y150-458 — both domes, the bell
// tower, steps, blue door, flowers, fully clear of the baked title, which
// a row-brightness pixel scan confirmed never reaches past x~480) placed
// beside a coast/sea/sunset panel (x460-1659, y640-948 — cliff, full
// sailboat, sunset reflection, confirmed 72px below the baked subtitle's
// last text row at y568). Both panels are the same real photograph at the
// same native scale, so joining them reads as a continuous wide shot, not
// a collage; the ~16px join is feather-blended only to soften the hard
// pixel edge, not to hide a scale or lighting mismatch. Composed with
// local Pillow only — no generative/outpainting dependency. Zero baked
// typography survives (both source regions are chosen entirely outside
// the text band). See the Asset-Aspect-Ratio and Project Art Derivative
// permanent rules in CAPABILITY_LEDGER.md.
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
