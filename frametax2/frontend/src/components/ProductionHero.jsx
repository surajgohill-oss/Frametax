import { useState } from "react";
import { Money } from "../lib/format";
import { API_ORIGIN } from "../api";
import heroArt from "../assets/production-art/little-utopia-hero-clean.png";

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
// ART PLATE HERO (2026-10-07, supersedes the Full-Art Hero Rule below at the product owner's request): a
// 160px hero in one row -- back link, a 200x112 landscape art plate (object-fit: cover, edge to edge; same
// proportions as Project Library's art), title + chips, then the budget/questions bay. A dark cinematic bay
// in both app themes, lit per production from getProjectHeroTheme. No full-width image.
//
// (superseded) FULL-ART HERO RULE: the complete
// approved key art fills the entire Hero artwork rectangle, edge to edge,
// with the whole image visible — never letterboxed, never cropped.
// `little-utopia-hero-clean.png` is the SAME master photograph
// (little-utopia-hero.png, 1659x948) with ONLY the baked title/subtitle
// typography removed (inpainted locally with OpenCV's Telea algorithm
// against a precise glyph mask — a classical, non-generative pixel-
// diffusion technique, not AI outpainting — so every other pixel of the
// original composition — both domes, the full village, coastline, sea,
// sailboat, sunset — is byte-for-byte the same photograph, nothing added,
// moved, or invented). `.ph-hero-art` renders it as a plain `<img>` with
// `width/height: 100%` + `object-fit: fill`, so the complete image is
// stretched (modest non-uniform scaling, not cropped) to exactly fill the
// Hero's ~5-7:1 rectangle. This intentionally does NOT preserve the
// source's own 1.75:1 aspect ratio — full-image-visible + full-Hero-fill
// take priority over aspect-ratio preservation, per the Full-Art Hero
// Rule. Do not reintroduce `object-fit: cover`/`contain`, a crop, or a
// composite here; see CAPABILITY_LEDGER.md for why both were tried and
// reverted.
// Hero cinematic bay per production -- MANUALLY CURATED from each project's key art. base is the
// [left, centre, right] gradient; bloom is the localized light behind the art plate; second is a quieter
// light behind the title; accent tints the bottom rule. Dark in both app themes. Matched on the
// production title; a project without key art (Bad Hombres today) gets the neutral slate fallback.
const HERO_THEMES = {
  // F#K Valentine's Day -- deep wine / charcoal, crimson bloom, a restrained warm-cream highlight.
  valentine: { base: ["#24101A", "#141114", "#1A0F12"], bloom: "rgba(196, 34, 48, 0.30)", second: "rgba(246, 226, 200, 0.07)", accent: "rgba(170, 34, 46, 0.6)" },
  // The Little Utopia -- harbour blue / charcoal, sunset-gold bloom, a restrained sea-blue light.
  utopia: { base: ["#10222E", "#121619", "#0F1C24"], bloom: "rgba(228, 166, 72, 0.26)", second: "rgba(64, 136, 178, 0.14)", accent: "rgba(206, 152, 62, 0.5)" },
  // Lips Like Sugar -- blue-black, electric cyan/cobalt bloom, twilight-violet light, a faint red rule.
  sugar: { base: ["#0A1124", "#070A14", "#0D0C1E"], bloom: "rgba(36, 150, 255, 0.26)", second: "rgba(118, 76, 196, 0.15)", accent: "rgba(200, 32, 48, 0.45)" },
};
const DEFAULT_HERO_THEME = { base: ["#161B22", "#101419", "#13171D"], bloom: "rgba(110, 130, 150, 0.14)", second: "rgba(90, 110, 130, 0.07)", accent: null };
function getProjectHeroTheme(title) {
  const t = (title || "").toLowerCase();
  const key = Object.keys(HERO_THEMES).find((k) => t.includes(k));
  return key ? HERO_THEMES[key] : DEFAULT_HERO_THEME;
}

export default function ProductionHero({
  production,
  stageControl,
  openQuestions,
  swing,
  onBack,
  headerActions,
}) {
  // Consolidated UI/ingestion/permission closeout (2026-09-03), Batch 1:
  // the Hero is now BUDGET ONLY — project identity/artwork, Production
  // Budget, Questions Remaining. No scenario economics (Top Priced
  // Candidate, Leading/Recommended Structure, incentive, NPC) belong
  // here; this component no longer accepts or computes topStructure/
  // isGenuineRecommendation/bestPricedCandidate at all — see
  // ProjectHeader.jsx, which still computes them (other consumers read
  // them — the Globe/Workspace/FX-strip active-structure resolution is
  // unchanged) but no longer passes them into this component. That
  // recommendation/leading-structure identity is not relocated anywhere
  // in this pass; Overview's Top Structures cards already carry the
  // real ANCHOR/LEADING/OPTIMIZED roles independently.

  // Visible UI defect fix: the Part G change above made this fetch
  // unconditional for every project, including Little Utopia. Little
  // Utopia's registered master Asset row (little-utopia/utopia.png) is a
  // real deck-cover image with "The Little Utopia / A Feature Film /
  // Mediterranean Drama" baked into the pixels — confirmed by reading the
  // file directly, not assumed. Rendered under this component's own
  // `.ph-hero-title` text, that produced a large duplicated title
  // treatment. `little-utopia-hero-clean.png` (see the Full-Art Hero Rule
  // above) is the ONLY text-free version of this artwork that exists
  // anywhere — every other candidate Asset row for this project is also a
  // deck/lookbook cover with its own baked title. Restoring the exact
  // pre-Part-G source for Little Utopia specifically is therefore the only
  // fix available without generating or substituting new artwork. Every
  // other project (starting with FVD) keeps the generic per-project fetch
  // Part G added — that path is correct and already verified working.
  const LITTLE_UTOPIA_PROJECT_ID = "fa5cade5-0669-4816-bfe6-72146f8d3bae";
  const isLittleUtopia = production?.project_id === LITTLE_UTOPIA_PROJECT_ID;
  const [artworkFailed, setArtworkFailed] = useState(false);
  const artworkUrl = production?.artwork_url && !isLittleUtopia
    ? `${API_ORIGIN}${production.artwork_url}`
    : null;
  // Production Overview Truthfulness: a project with no artwork of its own
  // must fall back to a production-NEUTRAL treatment, never another real
  // production's key art. `heroArt` (little-utopia-hero-clean.png) is
  // Little Utopia's OWN photograph — correct only for isLittleUtopia
  // above, never as the generic "nothing else to show" fallback every
  // other project without artwork was silently inheriting. No neutral
  // hero image asset exists in this repo and generating one is out of
  // scope here, so the fallback is the same flat `--surface-2` neutral
  // surface token the Library grid's own "No artwork yet" card already
  // uses (screens.css .lib-art) — not a new design, not a new asset.
  const showNeutralFallback = isLittleUtopia ? false : (!artworkUrl || artworkFailed);
  const heroSrc = isLittleUtopia ? heroArt : artworkUrl;
  const heroTheme = getProjectHeroTheme(production?.production_name);

  return (
    <div
      className="ph-hero"
      style={{
        "--ph-base-a": heroTheme.base[0],
        "--ph-base-b": heroTheme.base[1],
        "--ph-base-c": heroTheme.base[2],
        "--ph-bloom": heroTheme.bloom,
        "--ph-second": heroTheme.second,
        ...(heroTheme.accent ? { "--ph-accent": heroTheme.accent } : {}),
      }}
    >
      {/* Cinematic lens wash behind the left content (localized behind the art plate; see shell.css ART PLATE HERO block). */}
      <div className="ph-hero-lens" aria-hidden="true" />
      <button className="ph-back ph-hero-back" onClick={onBack}>← Project Library</button>
      {/* Art plate: 200x112, the artwork fills it edge to edge (object-fit: cover). The blurred copy
          underneath only shows while the crisp image loads. */}
      <div className="ph-hero-plate" aria-hidden="true">
        {showNeutralFallback ? (
          <div className="ph-hero-plate-neutral ph-hero-art-neutral" />
        ) : (
          <>
            <img key={`plate-bg-${production?.project_id || "fallback"}`} className="ph-hero-plate-bg" src={heroSrc} alt="" />
            <img
              key={`plate-fg-${production?.project_id || "fallback"}`}
              className="ph-hero-plate-fg"
              src={heroSrc}
              alt=""
              onError={() => setArtworkFailed(true)}
            />
          </>
        )}
      </div>
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
          <span className="ph-hero-metric-label">
            Question{openQuestions === 1 ? "" : "s"} Remaining
          </span>
          <span className="ph-hero-metric-value mono">{openQuestions}</span>
          {!!swing && (
            <span className="ph-hero-metric-caption">±${Math.round(swing).toLocaleString()} at stake</span>
          )}
        </div>
      </div>
      <div className="ph-hero-topbar">{headerActions}</div>
    </div>
  );
}
