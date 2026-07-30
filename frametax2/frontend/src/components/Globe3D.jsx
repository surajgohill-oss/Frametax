import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import ThreeGlobe from "three-globe";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { STATUS_HEX, GRAPHITE_HEX, PULSE_TIERS } from "../lib/globeData";
import { CAMERA_FOV_DEG, fitCameraDistance } from "../lib/globeFit";
import { subscribeTheme } from "../lib/theme";

// ── Studio environment (image-based lighting) ───────────────────────────
// THE architectural change in the premium-glass pass. Previously the Globe
// was lit only by a directional key plus a flat ambient, which is why it
// could never look like glass: a dielectric such as obsidian or optical
// crystal derives almost all of its character from what it REFLECTS, and
// with no environment map the only specular cue available is a single
// directional lobe — one dot on an otherwise flat ball. No amount of
// roughness/specular tuning can substitute for an environment.
//
// This builds a small studio "room" — a key softbox, a long thin strip
// light, a cool rim panel and a faint warm bounce — which PMREMGenerator
// converts into a pre-filtered radiance map. Assigning it to
// scene.environment gives every physical material real, angle-varying
// reflections: the elongated highlight that slides across the sphere as it
// rotates is what reads as machined optical glass.
//
// Generated procedurally so it stays self-contained (no external HDRI, no
// network fetch, nothing to ship or cache).
function buildStudioEnvironment() {
  const env = new THREE.Scene();
  const box = new THREE.BoxGeometry(1, 1, 1);
  box.deleteAttribute("uv");

  // Enclosing dark room — keeps reflections from bottoming out to pure
  // black, which is what makes an unlit side read as a hole rather than as
  // a shadowed surface.
  const room = new THREE.Mesh(
    box,
    new THREE.MeshBasicMaterial({ color: new THREE.Color("#0d0f13"), side: THREE.BackSide }),
  );
  room.scale.setScalar(24);
  env.add(room);

  const panel = (hex, intensity, pos, scale) => {
    const m = new THREE.Mesh(
      box,
      new THREE.MeshBasicMaterial({ color: new THREE.Color(hex).multiplyScalar(intensity) }),
    );
    m.position.set(pos[0], pos[1], pos[2]);
    m.scale.set(scale[0], scale[1], scale[2]);
    env.add(m);
  };

  // Panel intensities are deliberately LOW. A first calibration ran the key
  // at 2.2 and the strip at 3.0, which mirrored the panels onto the sphere
  // as a discrete blown-white lamp image on the limb — a textbook blown-out
  // hotspot. A premium instrument reflects a soft studio, not a visible
  // bulb, so these stay dim and the map is heavily blurred below.
  // Key softbox, upper front-right — the broad primary reflection. Kept
  // physically LARGE and dim rather than small and bright: a big soft source
  // wraps the curve, a small bright one prints a disc on it.
  panel("#ffffff", 0.95, [5, 6, 5], [13, 0.2, 13]);
  // Long thin strip — reads as a drawn specular streak across the curve.
  // This single element does most of the "precision-machined" work.
  panel("#ffffff", 1.45, [-2, 7.5, -3], [15, 0.14, 1.3]);
  // Cool rim panel behind-left: separates the limb from the backdrop.
  panel("#cfdaea", 0.7, [-8, 1, -7], [6, 6, 0.2]);
  // Faint warm bounce from below — ties the glass to the app's brass/ivory
  // shell WITHOUT tinting the light rig itself (which is what previously
  // produced the muddy cast).
  panel("#e8d6b8", 0.35, [6, -4.5, 2], [5, 0.2, 5]);

  return env;
}

// ══════════════════════════════════════════════════════════════════════
// FROZEN (2026-07-29, Globe Phase 2 closeout): everything below is the
// canonical Globe implementation that future UI work builds around.
//
// Frozen in this pass, on top of the 2026-07-28 freeze:
//   • the four-state semantic system (GLOBE_SEMANTIC in globeData.js) and
//     its application here — fill, stroke, altitude, beacon, ring;
//   • pulse is RESERVED for the recommendation (PULSE_TIERS), in BOTH the
//     mount path and the data-change path;
//   • the hover response (brighten + border emphasis, instant, no camera
//     or ring side effects) and its separation from selection;
//   • ambient motion: specular drift, limb breath, recommendation breath,
//     yielding autorotation — all gated on prefers-reduced-motion;
//   • day/night calibration, with GLOBE_THEME as the single source for
//     both themes (no module-level duplicate of any day value).
//
// Carried forward from 2026-07-28: materials, lighting, ocean,
// untouched-land treatment, Admin-1 geometry composition,
// selection/camera/Inspector-framing behavior, and beacon fallback (live
// click-through of California, New York, Georgia, Ontario, Quebec, British
// Columbia, Mauritius, Malta, plus card sync, one-click A->B transfer, and
// Optimizer Overlay arcs).
//
// Phase 3 is Globe UX/polish (optical quality, micro-interactions, label
// and typography polish, camera feel). It may tune the constants in this
// file. It may NOT reintroduce a fifth semantic state, put a pulse on
// anything but the recommendation, or re-add a persistent legend.
//
// Do not modify this file for an unrelated UI pass. A change here requires
// the user to explicitly unlock this subsystem first. If you believe the
// render is regressed, verify against a FRESH dev-server restart and a
// hard browser reload before touching any material/lighting constant —
// most "regressions" reported against this file have turned out to be a
// dead dev server or a stale browser tab, not a code defect.
// ══════════════════════════════════════════════════════════════════════

// Cheap, non-leaking probe for WebGL availability. Creates one throwaway
// context and immediately releases it, so it never counts against the
// browser's live-context budget. Returns false when WebGL is unavailable
// (no hardware/driver support, GPU blocklist, or the per-page context
// limit is currently exhausted) — the caller then renders the static
// identity fallback instead of throwing.
function webglAvailable() {
  try {
    const c = document.createElement("canvas");
    const gl = c.getContext("webgl2") || c.getContext("webgl") || c.getContext("experimental-webgl");
    if (!gl) return false;
    const lose = gl.getExtension("WEBGL_lose_context");
    if (lose) lose.loseContext();
    return true;
  } catch {
    return false;
  }
}

// DERIVED, never re-declared. This used to be a hand-synced duplicate of
// globeData.js's STATUS_HEX, justified by a claimed import cycle — there is
// no cycle (globeData.js imports only ./jurisdictions), so the duplicate was
// pure drift risk and is now gone. `charcoal` is this file's internal alias
// for the canonical untouched-landmass graphite.
//
// PHASE 2 CLOSEOUT: the `red` alias is gone with the darkRed state itself.
// The semantic system is exactly four states (see GLOBE_SEMANTIC) and this
// file must not reintroduce a fifth by aliasing one back into existence.
const TIER_HEX = {
  ...STATUS_HEX,
  charcoal: GRAPHITE_HEX,
};

// ── Visual hierarchy ────────────────────────────────────────────────────
// Deliberate luminance ladder, dark -> light, so each layer separates from
// the one beneath it instead of merging:
//   ocean (deepest, warm blackened glass) < inactive land (lighter frosted
//   graphite) < borders (lightest neutral) < status colours (the only
//   saturated thing here).
// ROOT-CAUSE NOTE (2026-07-28 recovery pass). Successive passes tried to
// cure a muddy brown cast by nudging THESE hexes, and could not, because the
// cast was never coming from the materials: every scene light below was
// itself brown-tinted (ambient 0x332b22, fill 0x8a7860, rim 0xd4a860). Phong
// shading multiplies material x light per channel, so a light rig with a
// crushed blue channel forces EVERY surface toward brown no matter what
// colour the material declares. The rig is now neutral (see the lighting
// block), which is what finally lets these values render as written.
//
// Deliberately neutral charcoal with only a restrained midnight undertone —
// the R/G/B spread stays narrow (~13 steps) so it reads as smoked glass, not
// as a blue sphere. Warm/taupe values are prohibited here: they are exactly
// what produced the muddy cast this palette exists to prevent.
// ── Theme-responsive globe palette ──────────────────────────────────────
// Night mode is not a filter over the day render: the ocean moves to a true
// midnight NAVY (day mode's ocean is a neutral slate), the backdrop drops to
// meet the night application canvas so the panel stops reading as a foreign
// inset, and the limb picks up a faint cool illumination. Only these values
// change — the glass ARCHITECTURE (PMREM IBL, MeshPhysical, clearcoat, ACES,
// composer, bloom) is identical in both themes and must stay that way.
//
// CALIBRATION CONSOLIDATION (Phase 2 closeout, objective 8): five of these
// day values previously existed TWICE — once here and once as a module-level
// constant used to initialise the material/renderer before applyTheme() first
// ran (OCEAN_BODY, NEUTRAL_STROKE, the rim shader's uColor, the renderer's
// toneMappingExposure, the ocean's envMapIntensity). Both copies happened to
// agree, so nothing was visibly wrong — but "day and night are calibrated
// consistently" cannot be verified by inspection while the day values live in
// two places, and every previous material pass had to remember to edit both.
// The constants below are now DERIVED from this table, so day is defined
// exactly once and the two themes are structurally guaranteed to differ only
// in the values listed here.
const GLOBE_THEME = {
  day: {
    ocean: "#3a4250",
    oceanEmissive: "#1e242c",
    land: GRAPHITE_HEX,
    stroke: "#9aa3b0",
    rim: "#b9c1cb",
    backdrop: ["#14161a", "#0f1114", "#0a0c0e"],
    exposure: 0.95,
    envIntensity: 0.34,
    // Multiplier on the polygon cap/side materials' own envMapIntensity.
    // Day is the identity by definition — the day render is the frozen,
    // verified baseline and this consolidation must not alter a pixel of it.
    capEnvScale: 1.0,
  },
  night: {
    // Deep navy that still reads as water, never as a black hole.
    ocean: "#2b3956",
    // Faint internal blue illumination — the "lit from within" quality the
    // art direction calls for, and the guarantee the ocean never collapses.
    oceanEmissive: "#16243c",
    // Neutral grey land on a navy ocean is precisely what reads as an
    // unfinished or missing asset — the two share no hue family. Night land
    // is a navy-slate: clearly lighter than the ocean, clearly darker than
    // any status colour, and unmistakably part of the same material world.
    land: "#4a5570",
    // Borders soften markedly at night: on a dark ground the same value
    // reads far hotter, and hard white admin lines are the single biggest
    // contributor to the "technical GIS map" impression.
    stroke: "#8290a8",
    // Cool silver-blue limb rather than day's neutral platinum.
    rim: "#9fb6d6",
    // Meets --dark-canvas/--dark-surface-0 from the night token layer, so
    // the globe panel and the application shell share one continuous field.
    backdrop: ["#0d1420", "#0a1018", "#070b12"],
    // Slightly hotter: the surrounding UI is far darker at night, so the
    // same exposure reads dimmer by simultaneous contrast.
    exposure: 1.04,
    envIntensity: 0.40,
    // Night lifts the LAND/status caps' environment response alongside the
    // ocean's. Previously only the globe body's envMapIntensity was
    // theme-driven, so at night the ocean gained reflectivity while every
    // landmass and status polygon stayed pinned at its day value — the
    // continents visibly flattened out relative to the water they sit in.
    // This is the one calibration asymmetry between the two themes that a
    // reader could not have found from the constants alone.
    capEnvScale: 1.18,
  },
};

function globeTheme() {
  return document.documentElement.getAttribute("data-theme") === "night"
    ? GLOBE_THEME.night
    : GLOBE_THEME.day;
}

// Day-theme derivations — single-sourced from GLOBE_THEME.day above. These
// seed the material/renderer at construction time; applyTheme() then owns
// every subsequent change.
const OCEAN_BODY = GLOBE_THEME.day.ocean; // smoked midnight glass — lit-side diffuse
const NEUTRAL_FILL = GLOBE_THEME.day.land; // frosted graphite (== GRAPHITE_HEX)
const NEUTRAL_STROKE = GLOBE_THEME.day.stroke; // etched border, never a bright GIS line
const BRAND_NEUTRAL_FILL = "#564d3e"; // higher contrast for the 76px mark
const SELECTED_STROKE = "#f4ecd9"; // == --dark-text-primary
// The recommendation gets its own bright perimeter — the single strongest
// "look here" cue on the Globe, present without interaction.
const GOLD_STROKE = "#f7e3ab";
// Hover perimeter. Deliberately between the resting border and
// SELECTED_STROKE: hover must be unmistakable as a response yet never be
// mistaken for a committed selection. Neutral (no hue of its own) so it
// reads identically over all four semantic states and over untouched land.
const HOVER_STROKE = "#dfe4ec";

// Fresnel rim strength. Raised on selection to read as "illuminated". The
// rim colour itself is warm brass now (was a cold blue "#4a7fb5") — the
// glass edge should read as gilt trim on a premium instrument, not a sci-fi
// force field.
// Cut hard in the premium-glass pass. The studio environment now defines
// the limb by itself (a real reflection falls off toward grazing angles),
// so the additive Fresnel shell became a second, redundant edge light —
// the two stacked into a concentrated white point on the left limb. The
// shell is retained only to keep the silhouette from fusing with the
// backdrop when the environment happens to face away.
const BASE_RIM_INTENSITY = 0.16;
const SELECTED_RIM_INTENSITY = 0.26;
// Selection is a substantial physical lift, not a hint — it must become the
// focal point of the scene the moment it is chosen. Raised again ~25% in the
// 2026-07-28 closeout pass (0.15 -> 0.19), on top of the earlier ~2.5x raise
// from the original 0.06 — it must read from across the room.
const SELECTED_POLYGON_ALTITUDE = 0.19;
// The leading recommendation stands permanently proud of every other
// participating jurisdiction, with no interaction required. Raised again in
// the closeout pass (0.05 -> 0.065) on top of the earlier ~2.5x raise from
// 0.02 — Gold was still disappearing against the rest of the choropleth;
// this alone (plus the beacon/point boosts below) is what makes it the
// thing the eye finds first, before any click.
const GOLD_BASELINE_POLYGON_ALTITUDE = 0.065;
const PARTICIPATING_POLYGON_ALTITUDE = 0.01;
const INACTIVE_POLYGON_ALTITUDE = 0.002;
// three-globe tweens polygon altitude/colour over this window. Its easing
// curve is internal to the library (only duration is configurable); the
// camera flight below uses a true easeOutQuart.
const SELECTION_TRANSITION_MS = 500;

// ── Camera fit (Phase 2 post-freeze reconciliation) ─────────────────────
// Framing is now COMPUTED from the live canvas box instead of being a fixed
// distance. The previous `DEFAULT_CAMERA_DISTANCE = 225` (itself "pulled in
// from 246 so the globe fills more of its panel") is the confirmed cause of
// the reported clipping, and it was clipping at BOTH values.
//
// The arithmetic, so nobody has to rediscover it: a sphere of radius R at
// distance d has silhouette half-angle asin(R/d); it fits the frame only if
// tan(asin(R/d)) <= tan(fovY/2) vertically, or <= tan(fovY/2) * aspect
// horizontally. At R=100, d=225, fovY=50 that ratio is
//   tan(asin(100/225)) / tan(25 deg) = 0.4966 / 0.4663 = 1.064
// i.e. the sphere is 106.4% of the available half-height and overflows by
// ~6% on every side. Measured live at 1600x900 before the fix: silhouette
// radius 298px against a 280px half-height — 18px clipped top and bottom,
// with 12 European markers (UK, IE, IS, NO, SE, DK, DE, NL, BE, FR, EE, FI)
// projecting outside the canvas box entirely.
//
// Solving forward instead: pick the content radius that must stay inside the
// frame, then derive d. GLOBE_CONTENT_RADIUS is the sphere PLUS the tallest
// thing standing on it — a recommendation beacon's glow shell reaches ~6
// units above its footprint, that footprint sits at
// GOLD_BASELINE_POLYGON_ALTITUDE, and the whole group is scaled 1.28x when it
// is the recommendation. Framing to the bare sphere (100) is exactly how the
// recommendation marker ended up clipped against the edge.
// The geometry itself lives in lib/globeFit.js — a pure module with no three.js
// or DOM dependency, so the no-clipping property is unit-testable rather than
// eyeballed. See that file for the full derivation and the measured history.
//
// Fallback only, for the brief window before the first real measurement.
const DEFAULT_CAMERA_DISTANCE = 285;
// The producer's zoom range. The floor is fixed; the ceiling is a BASELINE that
// applySize() may raise (never lower) when a narrow frame needs a farther
// camera to keep the whole sphere visible.
const ORBIT_MIN_DISTANCE = 150;
const ORBIT_MAX_DISTANCE = 460;

function easeOutQuart(t) {
  return 1 - Math.pow(1 - t, 4);
}

// Blend a status hex toward the neutral fill — used to softly dim
// participating countries other than the current selection. Never used to
// change a SELECTED country's own hue (selection never repaints status).
// `toward` defaults to the day land colour but callers inside the scene pass
// the LIVE (theme-resolved) land colour. Without that, dimming at night
// blended every unselected jurisdiction toward day's graphite (#6e7681) while
// the land around it was navy-slate (#4a5570) — so selecting anything at
// night tinted the rest of the choropleth to a colour that appeared nowhere
// else in the night scene. A real theme inconsistency, invisible in day mode.
function dimHex(hex, amount = 0.66, toward = NEUTRAL_FILL) {
  try {
    const c = new THREE.Color(hex);
    const n = new THREE.Color(toward);
    return `#${c.lerp(n, amount).getHexString()}`;
  } catch {
    return hex;
  }
}

// Hover response: lift a state colour toward white WITHOUT changing its hue
// family, so a hovered jurisdiction reads as "lit" rather than as a
// different semantic state. Deliberately gentle — hover is a preview cue,
// selection is the commitment, and the two must never be confusable.
//
// This is safe against material sharing: three-globe assigns our overridden
// cap material directly and skips its own shared-material colour mutation
// (verified in dist source, `[!capMaterial && capColor]`), and the material
// cache is keyed by the resolved hex — so a brightened country gets its own
// cached material instead of recolouring every country in the same state.
// It is also instant rather than tweened, which is exactly right for hover:
// only altitude goes through polygonsTransitionDuration.
function brightenHex(hex, amount = 0.24) {
  try {
    const c = new THREE.Color(hex);
    return `#${c.lerp(new THREE.Color("#ffffff"), amount).getHexString()}`;
  } catch {
    return hex;
  }
}

// ── Ambient motion (Phase 2 closeout, objective 4) ──────────────────────
// The Globe must feel ALIVE, not ANIMATED. Everything below is measured in
// tens of seconds and sub-percent amplitudes: the intent is that a producer
// watching a still screen sees the instrument breathe, and never sees it
// perform. No optimizer replay, no evaluation animation — that belongs to
// the Optimizer page.
//
// All of it is gated on prefers-reduced-motion.
//
// 1. Specular drift: the studio environment rotates very slowly, so the
//    strip light's specular streak slides across the sphere even when the
//    camera and globe are both stationary. This is the single most
//    convincing "polished physical object" cue available, and it costs one
//    scalar per frame — no geometry, no extra draw call.
const ENV_DRIFT_RAD_PER_SEC = 0.0125; // ~8.4 min per revolution
// 2. Limb breathing: the fresnel rim shell's intensity oscillates a few
//    percent, reading as atmosphere rather than as a hard glass edge.
//    three-globe's own atmosphere layer stays off (it z-fights the sphere —
//    see showAtmosphere below), so this shell is the only limb we have.
const RIM_BREATH_PERIOD_SEC = 11.0;
const RIM_BREATH_AMOUNT = 0.12; // ±12% of the current base intensity
// 3. Recommendation breath: the gold beacon's glow shell swells slightly on
//    a slow cycle. Paired with the ring pulse (gold-only), this is what
//    makes the recommendation the thing the eye returns to.
const GOLD_BREATH_PERIOD_SEC = 4.4;
const GOLD_BREATH_AMOUNT = 0.16;
// 4. Slow autorotation, and ONLY while the producer is neither inspecting
//    nor driving the camera: any selection or any pointer interaction stops
//    it immediately (see the controls block). A globe that keeps turning
//    under a jurisdiction someone is reading is an irritation, not ambience.
const AMBIENT_AUTOROTATE_SPEED = 0.16;

function hexWithAlpha(hex, alpha) {
  const a = Math.max(0, Math.min(1, alpha));
  const byte = Math.round(a * 255).toString(16).padStart(2, "0");
  return `${hex}${byte}`;
}

// Natural Earth's bundled 110m admin-0 set has a long-documented upstream
// quirk: a handful of countries (France, Norway among them) ship with
// ISO_A2 = "-99" — a sentinel, not a real code — because their overseas-
// territory scope collides with ISO's rules. This file has no ISO_A2_EH
// fallback field, so the fix is the standard workaround: fall back to the
// stable 3-letter ADM0_A3 code for exactly the entries known to hit this.
const ISO_A2_FIX_BY_ADM0_A3 = { FRA: "FR", NOR: "NO" };
function isoOfFeature(feat) {
  // Admin-1 (US state / CA province) features carry iso_3166_2 ("US-GA",
  // "CA-BC") — the same key the optimizer's jurisdiction codes use.
  const sub = feat?.properties?.iso_3166_2;
  if (sub) return sub;
  const raw = feat?.properties?.ISO_A2;
  if (raw && raw !== "-99") return raw;
  return ISO_A2_FIX_BY_ADM0_A3[feat?.properties?.ADM0_A3] || raw;
}

// Canvas backdrop. Deliberately a shade lighter than the globe body so the
// sphere reads as an object sitting in a space, not a hole cut in the page.
// Stops are grounded in the app's own dark-canvas/dark-surface-0/1 tokens —
// a warm studio backdrop, not the cold navy gradient this used to be.
function makeOceanBackgroundTexture() {
  const c = document.createElement("canvas");
  c.width = 2;
  c.height = 256;
  const ctx = c.getContext("2d");
  // Darkened further in the closeout pass — the backdrop was competing with
  // the globe instead of receding behind it. It now exists only to keep the
  // sphere from reading as a hole cut in the page, nothing more.
  // Quiet neutral charcoal. Was a warm near-black ramp (#161310/#100d0a/
  // #070504) which contributed to the overall brown cast and sat too close
  // in hue to the ocean for the sphere to separate from it. Neutral now, and
  // deliberately kept BELOW the ocean's emissive floor so the ocean always
  // reads as lighter than the backdrop it sits in.
  const stops = globeTheme().backdrop;
  const grad = ctx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, stops[0]);
  grad.addColorStop(0.55, stops[1]);
  grad.addColorStop(1, stops[2]);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 2, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.needsUpdate = true;
  return tex;
}

// Two Natural Earth (public-domain) boundary sets, composed into ONE
// polygon layer:
//   • world-110m.geojson  — country outlines, bundled with three-globe and
//     copied verbatim into /public/geo.
//   • admin1-us-ca.geojson — US states + Canadian provinces, filtered from
//     Natural Earth's 50m admin-1 set to just those two countries and
//     trimmed to the properties the Globe reads.
// US and CA country polygons are DROPPED from the composed set: those two
// countries become neutral containers whose sub-national jurisdictions
// carry the status, because a producer shoots in Georgia or British
// Columbia and a country-level fill would average unrelated state verdicts
// into one misleading colour. The admin-1 set tiles both countries
// completely, so no gap is left behind.
// Both are schematic vector outlines — no satellite imagery, no terrain.
// Fetched once and cached across every Globe3D mount so navigation never
// re-parses them.
const SUBNATIONAL_COUNTRY_ISOS = new Set(["US", "CA"]);
let worldGeoPromise = null;
function loadWorldGeo() {
  if (!worldGeoPromise) {
    const grab = (url) => fetch(url).then((r) => (r.ok ? r.json() : { features: [] })).catch(() => ({ features: [] }));
    worldGeoPromise = Promise.all([grab("/geo/world-110m.geojson"), grab("/geo/admin1-us-ca.geojson")])
      .then(([world, admin1]) => {
        const countries = (world.features || []).filter(
          (f) => !SUBNATIONAL_COUNTRY_ISOS.has(isoOfFeature(f)),
        );
        return { features: [...countries, ...(admin1.features || [])] };
      })
      .catch(() => ({ features: [] }));
  }
  return worldGeoPromise;
}

/**
 * The one Globe engine for the whole app — production screens and the
 * sidebar brand mark alike, so the visual language can never fork.
 *
 * `variant`:
 *   "production" (default) — full instrument: fresnel glass edge, status
 *      choropleth, beacons, selection physics, camera flight.
 *   "brand" — the sidebar identity mark. Same sphere and geometry, but no
 *      fresnel shell and no vignette: at 76px those read as a blue halo
 *      around a toy globe rather than as premium branding.
 *
 * Country polygons are the primary visualization: `polygonColors` (a Map or
 * plain object keyed by ISO_A2 / iso_3166_2 -> hex) fills participating
 * jurisdictions with their production status colour; everything else stays
 * neutral graphite with a visible border. `selectedIso` lifts and
 * illuminates one jurisdiction WITHOUT changing its fill colour.
 *
 * three-globe's polygon layer has no native click/hover callback in this
 * version, so `points` (at each jurisdiction's reference coordinate) carry
 * the CSS2D hit-targets wired to `onPointClick`/`onPointHover`. For
 * jurisdictions absent from the polygon set (Mauritius, Malta, Singapore)
 * the same point is promoted to a 3D beacon so a leading recommendation can
 * never disappear because of geography.
 */
export default function Globe3D({
  points = [],
  arcs = [],
  onPointClick,
  onPointHover,
  height = 520,
  // When true the renderer's height tracks the MOUNT's own box instead of the
  // `height` prop, so the Globe can be sized by CSS/layout rather than by a
  // hardcoded pixel number. Opt-in on purpose: the fixed-height call sites
  // (Overview, Workspace Map/Split, the brand mark) keep their exact frozen
  // behaviour, so this cannot regress them. `height` is still used as the
  // pre-measurement fallback and as the CSS min-height.
  autoHeight = false,
  polygonColors = null,
  selectedIso = null,
  // The jurisdiction currently under the cursor. Drives the hover response
  // (slight brighten + border emphasis) on the polygon itself — the hover
  // CARD is the caller's, but the Globe owns the surface reaction, because
  // only the Globe knows which polygon/material a jurisdiction resolved to.
  hoveredIso = null,
  selectedLat = null,
  selectedLng = null,
  // Where the camera should settle. Defaults to the selected jurisdiction;
  // the Optimizer Overlay passes the active structure's primary shoot so
  // the whole production shape frames itself with no clicking.
  focusLat = null,
  focusLng = null,
  focusDistance = null,
  pointRadius = null,
  variant = "production",
  // Pixels of the canvas's right edge covered by a floating (non-docked)
  // Inspector overlay — when set, camera framing shifts left so a selected
  // country's centered point doesn't land under the panel.
  obscuredRightPx = 0,
}) {
  const isBrand = variant === "brand";
  const mountRef = useRef(null);
  const globeRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const stateRef = useRef({});
  // Mutable snapshot the polygon/point accessors read from — the accessors
  // are handed to three-globe once (stable identities), and re-assigning
  // them is how a selection/status change repaints without a remount.
  const liveRef = useRef({ polygonColors: null, selectedIso: null, hoveredIso: null, pointRadius: null, geoIsoSet: null, strokeColor: null, landColor: null });
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    if (stateRef.current.renderer) return;
    if (!webglAvailable()) { setFailed(true); return; }
    // Populated by customThreeObject for pulse-eligible beacons; read by the
    // ambient breath in the animate loop. Initialised before the globe is
    // built so the accessor can never run against an undefined Map.
    stateRef.current.breathingGlows = new Map();

    // getBoundingClientRect rather than clientWidth: for a tiny flex-basis
    // container (the 80px sidebar brand mark), clientWidth can still read 0
    // on the very first synchronous measurement if the browser hasn't
    // committed that flex child's layout yet, which set the camera's
    // aspect ratio from the wrong (fallback-to-parent, ~230px-wide sidebar)
    // width — the sphere then rendered squashed/mis-cropped inside the 80px
    // circular mask until a later resize happened to correct it.
    // getBoundingClientRect reflects the actual computed box at call time.
    const width = Math.round(mount.getBoundingClientRect().width) || mount.clientWidth || mount.parentElement?.clientWidth || 600;
    // In autoHeight mode the mount is sized by CSS; fall back to the `height`
    // prop until the box has been laid out (first synchronous measurement can
    // legitimately read 0, same reason getBoundingClientRect is used above).
    const measuredH = Math.round(mount.getBoundingClientRect().height);
    const h = autoHeight && measuredH > 80 ? measuredH : height;
    stateRef.current.lastWidth = width;
    stateRef.current.lastHeight = h;

    const scene = new THREE.Scene();
    const oceanTexture = makeOceanBackgroundTexture();
    scene.background = oceanTexture;

    const camera = new THREE.PerspectiveCamera(CAMERA_FOV_DEG, width / h, 0.1, 2000);
    // Default framing is COMPUTED so the whole sphere plus its tallest beacon
    // fits this exact canvas box (see fitCameraDistance). OrbitControls'
    // min/max below are untouched, so the producer's own zoom range is
    // unchanged — this only moves where the camera STARTS.
    stateRef.current.fitDistance = fitCameraDistance(width, h);
    camera.position.set(0, 0, stateRef.current.fitDistance);
    cameraRef.current = camera;
    // The camera joins the scene graph so its child sheen light renders.
    scene.add(camera);

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      setFailed(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, h);
    // Filmic tone mapping. The previous rig used NoToneMapping, which clips
    // linearly: any highlight brighter than 1.0 slams to flat white, which
    // is structurally what produced blown-out hotspots — they were being
    // suppressed by dialling specular down until nothing was left, rather
    // than by rolling off. ACES compresses the highlight shoulder, so a
    // bright reflection stays bright AND keeps its hue instead of becoming
    // a white blob. This is what makes real reflections safe to add.
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    // Below 1.0 on purpose: the environment now contributes exposure that
    // the old rig got from a near-unity ambient, so holding the same
    // exposure double-counts and washes the graphite land toward white.
    // Derived from GLOBE_THEME.day (applyTheme() overwrites it immediately
    // below; this is only the pre-first-paint seed).
    renderer.toneMappingExposure = GLOBE_THEME.day.exposure;
    mount.innerHTML = "";
    mount.style.position = "relative";
    mount.appendChild(renderer.domElement);

    // Pre-filter the studio environment into a radiance map once per mount.
    const pmrem = new THREE.PMREMGenerator(renderer);
    const envScene = buildStudioEnvironment();
    // The blur sigma is the difference between "reflects a studio" and
    // "mirrors a lamp". At 0.04 the panels stayed sharp and printed a
    // blown-white disc onto the limb; 0.22 smears them into the soft,
    // directional gradient a real softbox produces.
    const envRT = pmrem.fromScene(envScene, 0.34);
    scene.environment = envRT.texture;

    // CSS2DRenderer: three-globe's htmlElementsData layer (the click/hover
    // hit-targets) renders via CSS2DObject, which needs this second
    // renderer overlaid on the WebGL canvas.
    const cssRenderer = new CSS2DRenderer();
    cssRenderer.setSize(width, h);
    cssRenderer.domElement.style.position = "absolute";
    cssRenderer.domElement.style.top = "0";
    cssRenderer.domElement.style.left = "0";
    cssRenderer.domElement.style.pointerEvents = "none";
    mount.appendChild(cssRenderer.domElement);

    // Vignette — separates the sphere from the panel it sits in. Skipped on
    // the brand mark and on any small embed, where it reads as a smudge.
    let vignette = null;
    if (!isBrand && h >= 200) {
      vignette = document.createElement("div");
      vignette.style.position = "absolute";
      vignette.style.inset = "0";
      vignette.style.pointerEvents = "none";
      // Neutral and much lighter than before. This is a CSS layer painted ON
      // TOP of the WebGL canvas, so it was double-penalising the render: the
      // old rgba(10,7,5,0.55) is a WARM black at 55% opacity covering the
      // outer ~48% of the panel, which both crushed the Globe's periphery
      // (making the sphere look dark and flat however the lights were tuned)
      // and re-imposed a brown tint over pixels the renderer had already
      // produced correctly. It exists only to stop the panel edges glaring —
      // it must stay subtle.
      vignette.style.background = "radial-gradient(circle at 50% 45%, rgba(0,0,0,0) 64%, rgba(8,10,13,0.34) 100%)";
      mount.appendChild(vignette);
    }

    // Lighting — NEUTRAL BY MANDATE. This rig is the single highest-leverage
    // thing in the file and the confirmed root cause of the "brown/muddy
    // Globe": it previously ran a brown ambient (0x332b22), a taupe fill
    // (0x8a7860) and a brass rim (0xd4a860). Because Phong multiplies
    // material x light per channel, that crushed blue everywhere and pushed
    // every surface — ocean, land, jade, silver — toward mud, which no
    // material-hex edit could ever undo.
    //
    // The lights are now essentially neutral, so each material renders as the
    // colour it actually declares: gold reads as true gold, jade as a jewel
    // green, graphite as graphite. Warmth belongs to the STATUS COLOURS, not
    // to the illumination. Do not re-tint these to "warm up" the Globe.
    // Intensities are deliberately restrained. Neutralising the hues (above)
    // removed the mud but, at the previous 0.85/1.05 strengths, the lit
    // hemisphere washed out into a broad pale region that swallowed
    // geography — the same "bright blob" failure in a new colour. Smoked
    // glass needs a LOW overall exposure with a wide dark range.
    // The lights are PURE WHITE and carry no hue whatsoever. Every colour on
    // this Globe now comes from the materials alone, which is the only way to
    // guarantee that gold renders as gold and graphite as graphite. (An
    // intermediate attempt used a dark tinted ambient, 0x3a3d44 — that fails
    // twice over: a dark ambient COLOUR caps how much light the term can ever
    // contribute no matter how high its intensity, so the sphere just went
    // black, and any tint reintroduces a cast.)
    //
    // The AMBIENT:KEY RATIO decides whether this reads as smoked glass or as
    // a lit billiard ball. Ambient-dominant keeps the whole sphere legible
    // and any specular hotspot small; the modest key plus the rim supplies
    // curvature. Do not make the key dominant "for drama" — that is what
    // produced the pale patch that swallowed the Arabian plate.
    // NOTE ON LEVELS: three.js colour management (default since r152)
    // converts every sRGB hex above into LINEAR space before lighting, then
    // converts back on output. Intensities therefore need to be higher than
    // naive sRGB arithmetic suggests — 0.62/0.55 looked correct on paper and
    // rendered as a near-black sphere. These values are set empirically from
    // the rendered result, not calculated.
    // PREMIUM-GLASS PASS: the ambient is now almost gone. The studio
    // environment above supplies the diffuse wrap AND the specular
    // reflections, which a flat AmbientLight cannot do — ambient adds the
    // same value to every pixel regardless of orientation, so a high ambient
    // literally averages out the reflections that make a surface read as
    // glass. Keeping it near zero is what lets the IBL be visible at all.
    // It is retained only as a black-floor guard.
    scene.add(new THREE.AmbientLight(0xffffff, 0.10));
    // The key now only shapes form; the environment provides exposure. Held
    // low because a directional key and an IBL both add specular — at 0.85
    // the two stacked into the hotspot on the limb. This is enough to give
    // the terminator a direction and no more.
    const key = new THREE.DirectionalLight(0xffffff, 0.30);
    key.position.set(200, 120, 200);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x8890a0, 0.20);
    fill.position.set(-200, -80, -150);
    scene.add(fill);
    // Back/rim gives the sphere mass by separating its dark limb from the
    // dark backdrop. Pulled down from 0.62: at that strength, combined with
    // the brass tint, it was producing the bright warm blob visible on the
    // left limb in the failing screenshots.
    const rim = new THREE.DirectionalLight(0xaeb6c2, isBrand ? 0.24 : 0.40);
    rim.position.set(-170, 70, -230);
    scene.add(rim);
    // NOTE: a camera-attached point light was tried here twice to get a
    // "moving glint". Both times it rendered as a broad blown-out blob on
    // the sub-camera point rather than a glint — and tuning it down far
    // enough to stop that also made it invisible. The polished read now
    // comes from the key light's tight specular (shininess 120) plus the
    // fresnel shell below, which is stable at every camera distance.
    // Do not reintroduce a camera-child point light without checking it at
    // the closest zoom, where the artifact is worst.

    const neutralFill = isBrand ? BRAND_NEUTRAL_FILL : NEUTRAL_FILL;
    // Theme-driven inactive land; falls back to the frozen day value.
    const resolvedNeutralFill = () => (isBrand ? BRAND_NEUTRAL_FILL : (liveRef.current.landColor || neutralFill));

    const capColorFn = (feat) => {
      const iso = isoOfFeature(feat);
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      // Untouched land never carries a hover state: hit-targets are created
      // only for jurisdictions this production actually touches (see the
      // htmlElementsData layer), so `hoveredIso` can only ever name one of
      // those. There is deliberately nothing to brighten here.
      if (!hex) return resolvedNeutralFill();
      const sel = liveRef.current.selectedIso;
      const hovered = !!iso && iso === liveRef.current.hoveredIso;
      // Hover on the SELECTED jurisdiction is a no-op: it is already the
      // brightest, most elevated thing on the Globe, and brightening it
      // further would flatten the distinction selection just earned.
      if (sel && iso === sel) return hex;
      // Everything else brightens on hover — INCLUDING when nothing is
      // selected. An earlier revision of this accessor only applied the
      // brighten inside the `sel && iso !== sel` branch, which meant hover
      // did nothing at all on a freshly-loaded Globe (the overwhelmingly
      // common case) and only started working after the producer had already
      // clicked something. Caught in runtime verification, not by the build.
      const base = sel ? dimHex(hex, 0.66, resolvedNeutralFill()) : hex;
      return hovered ? brightenHex(base, 0.30) : base;
    };
    const strokeColorFn = (feat) => {
      const iso = isoOfFeature(feat);
      if (liveRef.current.selectedIso && iso === liveRef.current.selectedIso) return SELECTED_STROKE;
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      // Border emphasis is the second half of the hover response and the
      // half that actually communicates "this is one clickable unit" — a
      // brightened fill alone is ambiguous on a small or fragmented
      // landmass. Ranked BELOW selection (which owns SELECTED_STROKE) and
      // above every resting border.
      if (iso && iso === liveRef.current.hoveredIso) return HOVER_STROKE;
      if (hex === TIER_HEX.gold) return GOLD_STROKE;
      // Theme-driven: night mode softens borders markedly (see GLOBE_THEME).
      return liveRef.current.strokeColor || NEUTRAL_STROKE;
    };
    // Extrusion sidewalls — previously fully transparent (`rgba(0,0,0,0)`
    // for every jurisdiction), which is why elevated status polygons read
    // as flat floating discs with an invisible edge instead of physical
    // enamel blocks. Status-bearing jurisdictions now get a real shadowed
    // sidewall (a darkened tint of their own cap colour, like the shaded
    // face of a glass block); not-evaluated land stays flush/transparent
    // since it barely lifts off the ocean and a wall there would just be a
    // thin dark seam.
    const sideColorFn = (feat) => {
      const iso = isoOfFeature(feat);
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      if (!hex) return "rgba(0,0,0,0)";
      try {
        const sel = liveRef.current.selectedIso;
        let cap = sel && iso !== sel ? dimHex(hex, 0.66, resolvedNeutralFill()) : hex;
        // Sidewalls track the cap's hover brighten, or a raised jurisdiction
        // lights its top face while its cut faces stay dark — which reads as
        // a rendering fault rather than as illumination.
        if (iso && iso === liveRef.current.hoveredIso && iso !== sel) cap = brightenHex(cap, 0.30);
        const c = new THREE.Color(cap).multiplyScalar(0.42);
        return `#${c.getHexString()}`;
      } catch {
        return "rgba(0,0,0,0)";
      }
    };
    const altitudeFn = (feat) => {
      const iso = isoOfFeature(feat);
      if (liveRef.current.selectedIso && iso === liveRef.current.selectedIso) return SELECTED_POLYGON_ALTITUDE;
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      if (!hex) return INACTIVE_POLYGON_ALTITUDE;
      if (hex === TIER_HEX.gold) return GOLD_BASELINE_POLYGON_ALTITUDE;
      return PARTICIPATING_POLYGON_ALTITUDE;
    };

    // ── Isolated material-correction pass (2026-07-28) ────────────────────
    // Verified directly in the installed three-globe 2.45.2 source
    // (node_modules/three-globe/dist/three-globe.js, polygon layer
    // __defaultCapMaterial/__defaultSideMaterial): polygon caps and sides
    // both default to plain `MeshBasicMaterial` — an UNLIT material that
    // ignores every scene light entirely. That is the actual cause of
    // "flat painted polygons": capColorFn/sideColorFn above only ever
    // supplied colour strings, which three-globe was applying to that unlit
    // default, so no amount of light-rig tuning could ever add a specular
    // response. three-globe also exposes real per-polygon material
    // OVERRIDE accessors — `.polygonCapMaterial()` / `.polygonSideMaterial()`
    // — confirmed present and wired the same way as every other public
    // accessor (`index$1(state.polygonCapMaterial)`), so this is a verified,
    // supported API, not an assumption.
    //
    // Applied ONLY to status-bearing (active) jurisdictions, via a small
    // cached pool of MeshPhongMaterial — the same lit material family
    // already used safely for the globe body itself below — keyed by the
    // exact resolved hex string. Not-evaluated land is untouched: its
    // accessor returns null, three-globe falls through to its own default
    // unlit material exactly as before, so the already-correct "quiet,
    // flush, no wall" inactive-land treatment cannot regress.
    // Materials are cached (never allocated per-frame) and disposed on
    // unmount below.
    // PREMIUM-GLASS PASS: MeshPhong -> MeshPhysical. Phong has no roughness
    // and no environment response, so "frosted" vs "glossy" could only ever
    // be faked with colour. Physical makes it a real optical property:
    // active status caps get low roughness + a clearcoat layer (polished
    // enamel under lacquer), not-evaluated land gets high roughness and
    // almost no clearcoat (sandblasted graphite glass). The two now differ
    // by how they scatter the studio environment, which is what the eye
    // actually reads as "material" — and it holds at every camera angle
    // instead of only where the key light happens to point.
    // Base (day) environment response per material, multiplied by the live
    // theme's capEnvScale. Stored on userData so applyTheme() can rescale an
    // already-cached material without needing to know how it was built.
    const applyCapEnvScale = (m, base) => {
      m.userData.arBaseEnvIntensity = base;
      m.envMapIntensity = base * (liveRef.current.capEnvScale ?? 1);
    };
    const capMaterialCache = new Map();
    const getCapMaterial = (hex, frosted) => {
      const cacheKey = `${hex}|${frosted ? "f" : "g"}`;
      let m = capMaterialCache.get(cacheKey);
      if (!m) {
        m = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color(hex),
          metalness: 0.0, // dielectric: glass/enamel, never metal
          roughness: frosted ? 0.80 : 0.30,
          clearcoat: frosted ? 0.12 : 1.0,
          clearcoatRoughness: frosted ? 0.65 : 0.14,
          // Inactive land sits in a narrow band: high enough that continents
          // stay legible by their own tone (not only by their borders), low
          // enough that the graphite base never competes with the status
          // colours. 0.18 combined with the reduced exposure pushed the
          // landmass too dark and leaned on the border strokes again.
          ior: 1.5,
          side: THREE.DoubleSide,
          depthWrite: true,
        });
        applyCapEnvScale(m, frosted ? 0.30 : 0.5);
        capMaterialCache.set(cacheKey, m);
      }
      return m;
    };
    const sideMaterialCache = new Map();
    const getSideMaterial = (hex) => {
      let m = sideMaterialCache.get(hex);
      if (!m) {
        // Extrusion sidewalls are the cut face of the block, not its
        // polished top: rougher, minimal clearcoat, low environment
        // response. That contrast against the glossy cap is what gives a
        // raised jurisdiction believable thickness.
        m = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color(hex),
          metalness: 0.0,
          roughness: 0.62,
          clearcoat: 0.22,
          clearcoatRoughness: 0.5,
          ior: 1.5,
          side: THREE.DoubleSide,
          depthWrite: true,
        });
        applyCapEnvScale(m, 0.28);
        sideMaterialCache.set(hex, m);
      }
      return m;
    };
    const activeHex = (feat) => {
      const iso = isoOfFeature(feat);
      const colors = liveRef.current.polygonColors;
      return colors?.get ? colors.get(iso) : colors?.[iso];
    };
    // Caps are lit for EVERY polygon, including not-evaluated land. This is
    // the second half of the "flat painted land" fix: previously the inactive
    // accessor returned null, so three-globe fell back to its own default
    // MeshBasicMaterial — an UNLIT material — and the entire graphite
    // landmass rendered as a flat colour fill that could not respond to the
    // light rig at all. That is precisely why inactive land "lacked frosted
    // depth" and why its shape was only legible from its border strokes.
    // Giving it a lit material makes it read as frosted graphite glass with
    // real curvature shading. Since the premium-glass pass, "frosted" is a
    // genuine roughness value rather than a darker colour: not-evaluated
    // land scatters the studio environment widely, status jurisdictions
    // reflect it sharply, and that difference survives every camera angle.
    const capMaterialFn = (feat) => getCapMaterial(capColorFn(feat), !activeHex(feat));
    // Sidewalls stay active-only on purpose: not-evaluated land sits almost
    // flush with the ocean (INACTIVE_POLYGON_ALTITUDE), so giving it a wall
    // would just draw a thin dark seam around every country.
    const sideMaterialFn = (feat) => (activeHex(feat) ? getSideMaterial(sideColorFn(feat)) : null);

    // Beacon treatment is for jurisdictions the polygon set genuinely
    // cannot draw (island / city-states). A federal-level US or CA entry
    // also has no polygon now that those render sub-nationally, but it is a
    // nationwide programme, not a pinpoint, so it stays a plain marker.
    const isSmallJurisdiction = (d) => {
      const geoSet = liveRef.current.geoIsoSet;
      if (!geoSet || !d?.iso) return false;
      if (SUBNATIONAL_COUNTRY_ISOS.has(d.iso)) return false;
      return !geoSet.has(d.iso);
    };
    // PULSE IS RESERVED FOR THE RECOMMENDATION (objective 2). This
    // previously read `d.tier === "gold" || isSmallJurisdiction(d)`, which
    // pulsed every island/city-state regardless of its semantic state — so
    // an Optimized alternative in Malta and an Unlockable opportunity in
    // Singapore both pulsed, and the Globe appeared to be recommending three
    // things at once. Beacon geometry is the correct answer to "this
    // landmass is too small to fill"; a pulse is not, because a pulse means
    // something. PULSE_TIERS comes from GLOBE_SEMANTIC, so this can only
    // ever include states declared `pulse: true`.
    const isRingEligible = (d) => !!d?.tier && PULSE_TIERS.has(d.tier);
    const pointRadiusFn = (d) => {
      // Small jurisdictions render as beacons; the point is the footprint
      // disc the beacon stands on.
      if (isSmallJurisdiction(d)) return d.iso === liveRef.current.selectedIso ? 0.62 : 0.5;
      const pr = liveRef.current.pointRadius;
      if (typeof pr === "function") return pr(d);
      if (typeof pr === "number") return pr;
      // Gold's footprint is deliberately larger even at rest — the eye
      // should find the leading recommendation before it clicks anything.
      // Bumped again in the closeout pass (0.62 -> 0.7).
      return d.tier === "gold" ? 0.7 : 0.4;
    };
    const pointAltitudeFn = (d) => {
      if (d.iso && liveRef.current.selectedIso && d.iso === liveRef.current.selectedIso) return SELECTED_POLYGON_ALTITUDE;
      if (d.tier === "gold") return GOLD_BASELINE_POLYGON_ALTITUDE;
      if (isSmallJurisdiction(d)) return PARTICIPATING_POLYGON_ALTITUDE;
      return 0.015;
    };
    const pointColorFn = (d) => {
      const hex = d.color || TIER_HEX[d.tier] || TIER_HEX.charcoal;
      if (isSmallJurisdiction(d) && liveRef.current.selectedIso && d.iso !== liveRef.current.selectedIso) {
        return dimHex(hex, 0.66, resolvedNeutralFill());
      }
      return hex;
    };

    const globe = new ThreeGlobe()
      .showGlobe(true)
      // three-globe's own atmosphere is OFF deliberately. Inspected live via
      // the scene graph: its shader mesh is built at geometry radius 100 with
      // scale 1.0 — exactly coincident with the globe sphere (also radius
      // 100) — so the two z-fight and patches of the atmosphere shader win
      // the depth test and paint a large soft blue blob across the sphere
      // face. It appeared/vanished with camera angle, which is what made it
      // look like a lighting bug for several passes. The fresnel shell below
      // provides the same limb glow correctly at radius 100.4, so the
      // atmosphere is redundant as well as broken here.
      .showAtmosphere(false)
      .polygonCapColor(capColorFn)
      .polygonSideColor(sideColorFn)
      .polygonCapMaterial(capMaterialFn)
      .polygonSideMaterial(sideMaterialFn)
      .polygonStrokeColor(strokeColorFn)
      .polygonAltitude(altitudeFn)
      // Animated selection lift/settle rather than an instant pop.
      .polygonsTransitionDuration(SELECTION_TRANSITION_MS)
      .pointsData(points)
      .pointLat("lat")
      .pointLng("lng")
      .pointColor(pointColorFn)
      .pointAltitude(pointAltitudeFn)
      .pointRadius(pointRadiusFn)
      .pointResolution(24)
      .pointsTransitionDuration(SELECTION_TRANSITION_MS)
      .ringsData([])
      .ringLat("lat")
      .ringLng("lng")
      .ringAltitude(PARTICIPATING_POLYGON_ALTITUDE)
      // SOFT pulse. `(1-t)^1.7` instead of a linear ramp: the ring leaves the
      // marker at nearly full strength and fades early, so what reads is a
      // quiet swell rather than a hard expanding ring travelling to its full
      // radius. A linear falloff is what made this look like a radar sweep.
      .ringColor((d) => (t) => hexWithAlpha(d.color || TIER_HEX.charcoal, Math.pow(1 - t, 1.7)))
      // Tightened and slowed from 2.9 / 2600ms. This is the recommendation
      // breathing, not a notification demanding attention.
      .ringMaxRadius(2.5)
      .ringPropagationSpeed(0.8)
      .ringRepeatPeriod(3200)
      // Beacon layer — island/city-state jurisdictions the 110m polygon set
      // omits. Each gets a real object: a status-coloured luminous head on a
      // slim tapered stem, plus a soft glow shell, so a leading
      // recommendation can never vanish because its landmass is tiny.
      .customLayerData([])
      .customThreeObject((d) => {
        const color = new THREE.Color(d.color || TIER_HEX.charcoal);
        const group = new THREE.Group();
        const stem = new THREE.Mesh(
          new THREE.CylinderGeometry(0.28, 0.7, 3.6, 12),
          new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.5 }),
        );
        stem.position.y = 1.8;
        group.add(stem);
        const head = new THREE.Mesh(
          new THREE.SphereGeometry(1.05, 20, 20),
          new THREE.MeshBasicMaterial({ color }),
        );
        head.position.y = 3.9;
        group.add(head);
        const glow = new THREE.Mesh(
          new THREE.SphereGeometry(2.1, 20, 20),
          new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false }),
        );
        glow.position.y = 3.9;
        group.add(glow);
        // Register the recommendation's glow shell for its ambient breath
        // (see the animate loop). Keyed by datum id, and the loop skips any
        // entry three-globe has since detached (`parent === null`), so this
        // self-prunes as data changes without separate bookkeeping.
        if (d?.tier && PULSE_TIERS.has(d.tier) && d.id) {
          stateRef.current.breathingGlows?.set(d.id, glow);
        }
        return group;
      })
      .customThreeObjectUpdate((obj, d) => {
        const g = globeRef.current;
        if (!g) return;
        const sel = d.iso && d.iso === liveRef.current.selectedIso;
        // Gold beacons (island/city-state jurisdictions like Mauritius that
        // the 110m polygon set can't draw) now match gold POLYGONS' baseline
        // elevation when unselected — previously they sat at the same flat
        // altitude as every other participating beacon, silently dropping
        // the one prominence cue a beacon-only leading recommendation had.
        const alt = sel ? SELECTED_POLYGON_ALTITUDE : d.tier === "gold" ? GOLD_BASELINE_POLYGON_ALTITUDE : PARTICIPATING_POLYGON_ALTITUDE;
        const pos = g.getCoords(d.lat, d.lng, alt);
        obj.position.set(pos.x, pos.y, pos.z);
        obj.lookAt(0, 0, 0);
        obj.rotateX(Math.PI / 2);
        // Gold stands taller even unselected — selection still reads as the
        // strongest state, but the leading recommendation should never need
        // a click to be found. Bumped again in the closeout pass (1.18 -> 1.28).
        const s = sel ? 1.5 : d.tier === "gold" ? 1.28 : 1;
        obj.scale.set(s, s, s);
      })
      .arcsData(arcs)
      .arcColor((d) => d.color || TIER_HEX[d.tier] || TIER_HEX.silver)
      // Higher altitude + thicker default stroke than before: in the
      // Optimizer Overlay these arcs ARE the production-routing story, not a
      // decorative line under a second choropleth — they need to read as
      // the primary graphic, arched clearly above the globe surface.
      .arcAltitude(0.32)
      .arcStroke((d) => (typeof d.strokeWidth === "number" ? d.strokeWidth : 0.35))
      .arcDashLength(0.75)
      .arcDashGap(0.2)
      .arcDashAnimateTime(2600)
      .htmlElementsData(points)
      .htmlLat("lat")
      .htmlLng("lng")
      .htmlAltitude(0.02)
      // Hide hit-targets on the FAR side of the globe. three-globe already
      // computes `isBehindGlobe` for every html element, but it only acts on it
      // when this modifier is supplied — and it was never supplied, so every
      // back-facing jurisdiction kept a live 28px click target projected to an
      // arbitrary screen position. Two consequences, both real: a click on
      // apparently empty canvas could select a country on the opposite side of
      // the world, and any measurement of "is the globe clipped" was polluted by
      // markers that legitimately sit far outside the sphere's projected disc
      // (which is how a narrow-viewport check first reported 29 phantom
      // clipped markers). display:none makes them inert AND zero-size, so both
      // the interaction and the measurement become well-defined.
      .htmlElementVisibilityModifier((el, isVisible) => {
        el.style.display = isVisible ? "" : "none";
      })
      .htmlElement((d) => {
        const el = document.createElement("div");
        el.className = "globe-hit-target";
        el.setAttribute("role", "button");
        el.setAttribute("tabindex", "0");
        el.setAttribute("aria-label", d.name || d.id || "jurisdiction marker");
        el.style.width = "28px";
        el.style.height = "28px";
        el.style.cursor = "pointer";
        el.style.pointerEvents = "auto";
        // RUNTIME BUG (found live 2026-07-28): the app-level floating
        // Inspector's ".inspector-backdrop" is a fixed, full-viewport,
        // z-index:40 layer. These hit-targets had no z-index (auto), so once
        // any jurisdiction was selected and its Inspector opened, EVERY
        // subsequent click anywhere on the globe — including squarely on a
        // different jurisdiction's marker — hit the backdrop first and just
        // closed the Inspector instead of selecting the new jurisdiction.
        // Selection appeared "stuck" because the very click meant to change
        // it was silently consumed one layer up. z-index above 40 lets a
        // jurisdiction click win over the backdrop so selection always
        // transfers in one click, same as when no Inspector is open yet.
        el.style.zIndex = "45";
        if (onPointClick) {
          el.addEventListener("click", (ev) => { ev.stopPropagation(); onPointClick(d); });
          el.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); onPointClick(d); } });
        }
        if (onPointHover) {
          el.addEventListener("mouseenter", () => onPointHover(d));
          el.addEventListener("mouseleave", () => onPointHover(null));
        }
        return el;
      });

    // ── The smoked-obsidian body ───────────────────────────────────────
    // PREMIUM-GLASS PASS: replaced three-globe's default MeshPhongMaterial
    // with MeshPhysicalMaterial. Phong models a highlight as one analytic
    // lobe per light; it has no concept of reflecting a room, so the sphere
    // could only ever show a single glint and read as a painted ball.
    // Physical + the studio environment above gives a real reflection field:
    // the long strip light draws an elongated specular across the curve, and
    // that streak MOVES as the globe rotates, which is the single strongest
    // cue that a surface is polished rather than printed.
    //
    // clearcoat is the piece that sells "precision-machined optical glass":
    // it adds a second, tighter specular layer over the diffuse body — the
    // exact optical behaviour of a coated lens or a lacquered obsidian
    // instrument face. roughness stays low but non-zero, because a perfect
    // mirror reads as chrome, which the brief prohibits.
    //
    // Safe to swap wholesale: three-globe only overwrites globeMaterial.color
    // when the material has NO color property (verified in dist source), and
    // MeshPhysicalMaterial has one.
    const material = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(OCEAN_BODY),
      metalness: 0.0, // dielectric — obsidian/glass, never metal
      roughness: 0.38,
      clearcoat: 1.0,
      // The coat is SATIN, not mirror. At 0.16 it behaved as a near-perfect
      // varnish and reflected the studio panels as two discrete white orbs
      // over the Pacific — sharp clearcoat reflects the environment crisply
      // no matter how rough the base layer underneath is, so this value, not
      // `roughness`, is what governs whether reflections read as lamps.
      clearcoatRoughness: 0.34,
      envMapIntensity: GLOBE_THEME.day.envIntensity,
      ior: 1.52, // ~optical crown glass
      // Emissive is additive and lighting-independent, so it is the sphere's
      // GUARANTEED floor colour on the unlit hemisphere — the thing that
      // stops the ocean collapsing to black at any camera angle. Kept
      // deliberately above the canvas backdrop's top stop (#14161a) so the
      // ocean always reads AS ocean against the panel behind it. Trimmed
      // slightly from #252b34 because the environment now contributes its
      // own ambient floor and the two would otherwise stack into haze.
      emissive: new THREE.Color("#1e242c"),
    });
    globe.globeMaterial(material);

    scene.add(globe);
    globeRef.current = globe;

    // Fresnel rim shell: a slightly larger back-faced sphere whose opacity
    // rises toward grazing angles — the glass edge that gives the sphere
    // curvature. Production only: at brand-mark size it is a blue halo.
    let rimMesh = null;
    if (!isBrand) {
      rimMesh = new THREE.Mesh(
        new THREE.SphereGeometry(globe.getGlobeRadius() * 1.004, 64, 64),
        new THREE.ShaderMaterial({
          uniforms: {
            // Cool platinum, not brass (#c9a15a) — brass here painted a warm
            // ring onto the limb and fed the overall muddy cast. Deliberately
            // NOT blue/cyan either: a saturated cool value here is what
            // produces the "cyan halo" failure mode this shell is banned from
            // reproducing. uPower raised 1.9 -> 2.4 to tighten the falloff
            // hard against the silhouette, so it reads as a glass edge rather
            // than a glow bleeding outward from the sphere.
            uColor: { value: new THREE.Color(GLOBE_THEME.day.rim) },
            uIntensity: { value: BASE_RIM_INTENSITY },
            uPower: { value: 2.4 },
          },
          vertexShader: `
            varying vec3 vNormal;
            varying vec3 vView;
            void main() {
              vNormal = normalize(normalMatrix * normal);
              vec4 mv = modelViewMatrix * vec4(position, 1.0);
              vView = normalize(-mv.xyz);
              gl_Position = projectionMatrix * mv;
            }`,
          fragmentShader: `
            uniform vec3 uColor;
            uniform float uIntensity;
            uniform float uPower;
            varying vec3 vNormal;
            varying vec3 vView;
            void main() {
              float f = pow(1.0 - abs(dot(vNormal, vView)), uPower);
              gl_FragColor = vec4(uColor, f * uIntensity);
            }`,
          side: THREE.BackSide,
          blending: THREE.AdditiveBlending,
          transparent: true,
          depthWrite: false,
        }),
      );
      scene.add(rimMesh);
      stateRef.current.rimMesh = rimMesh;
    }

    let cancelled = false;
    loadWorldGeo().then((geo) => {
      if (cancelled || globeRef.current !== globe) return;
      const features = geo.features || [];
      globe.polygonsData(features);
      liveRef.current.geoIsoSet = new Set(features.map((f) => isoOfFeature(f)).filter(Boolean));
      globe.pointColor(globe.pointColor()).pointAltitude(globe.pointAltitude()).pointRadius(globe.pointRadius());
      globe.ringsData(points.filter(isRingEligible));
      globe.customLayerData(points.filter(isSmallJurisdiction));
    });

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.4;
    // ── Ambient autorotation (objective 4) ─────────────────────────────
    // Previously gated on `points.length <= 1`, i.e. it never ran on a real
    // production Globe — the instrument sat perfectly inert. It now turns
    // slowly by default, and yields permanently the moment the producer
    // does anything: `controls.autoRotate` is cleared on the first drag/zoom
    // (the 'start' event below) and whenever a jurisdiction is selected (the
    // selection effect). Rotation that continues under a jurisdiction
    // someone is reading is an irritation, not ambience — and once someone
    // has taken the camera, it stays theirs for the life of the mount.
    controls.autoRotate = !prefersReducedMotion;
    controls.autoRotateSpeed = AMBIENT_AUTOROTATE_SPEED;
    stateRef.current.userTookControl = false;
    stateRef.current.ambientMotion = !prefersReducedMotion;
    const onControlStart = () => {
      stateRef.current.userTookControl = true;
      controls.autoRotate = false;
    };
    controls.addEventListener("start", onControlStart);
    // Unchanged zoom range — only the default position above moved.
    controls.minDistance = ORBIT_MIN_DISTANCE;
    // Baseline ceiling. applySize() raises this — never lowers it — when the
    // computed fit needs a farther camera than 460 (narrow canvas with the
    // Inspector open); see the note there.
    controls.maxDistance = ORBIT_MAX_DISTANCE;
    controls.enablePan = false;
    controlsRef.current = controls;

    // ── Post chain: render -> restrained bloom -> tone map/output ───────
    // The bloom is deliberately threshold-gated high (0.86) and weak (0.16),
    // so only genuinely bright pixels — the gold recommendation beacon, the
    // crest of a specular streak — pick up a faint halation. Broad glow on
    // the whole sphere is the game-engine look the brief prohibits; this is
    // the optical bloom of a camera lens, which is what makes a highlight
    // read as physically bright rather than merely light-coloured.
    // OutputPass is last and performs the ACES tone map + sRGB conversion
    // for the composer path (the renderer's own toneMapping is not applied
    // to render targets, so without OutputPass the filmic curve is lost).
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, h),
      0.09, // strength — deliberately far below the usual 1.0+ demo values
      0.5,  // radius
      0.93, // threshold — only the very top of the range blooms at all
    );
    composer.addPass(bloomPass);
    composer.addPass(new OutputPass());
    composer.setSize(width, h);
    composer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // ── Ambient motion loop (objective 4) ──────────────────────────────
    // Three sub-percent oscillations plus a slow environment rotation. Each
    // is a scalar write per frame: no geometry is rebuilt, no material is
    // reallocated, nothing is added to the draw call count. The whole block
    // is skipped outright under prefers-reduced-motion, which leaves the
    // previous static render exactly as it was.
    // performance.now() rather than THREE.Clock: Clock is deprecated in
    // three 0.185 (it warns on construction, and this file must stay
    // console-clean), and its replacement THREE.Timer needs a per-frame
    // update() call for no benefit here — every oscillation below is a pure
    // function of absolute elapsed time, not of frame delta.
    const ambientT0 = performance.now();
    let frameId;
    const animate = () => {
      const elapsed = (performance.now() - ambientT0) / 1000;
      if (stateRef.current.ambientMotion) {
        // 1. Specular drift — rotates the pre-filtered studio radiance map,
        //    so the strip light's highlight slides across the sphere even
        //    when both camera and globe are still. `environmentRotation` is a
        //    scene-level Euler (three r163+; this project runs 0.185), which
        //    means the reflection moves without moving any object.
        scene.environmentRotation.y = elapsed * ENV_DRIFT_RAD_PER_SEC;
        // 2. Limb breathing — the fresnel shell's intensity oscillates a few
        //    percent around whatever the current base is, so it keeps
        //    tracking the selection lift instead of overwriting it.
        if (rimMesh) {
          const base = liveRef.current.selectedIso ? SELECTED_RIM_INTENSITY : BASE_RIM_INTENSITY;
          const breath = 1 + RIM_BREATH_AMOUNT * Math.sin((elapsed / RIM_BREATH_PERIOD_SEC) * Math.PI * 2);
          rimMesh.material.uniforms.uIntensity.value = base * breath;
        }
        // 3. Recommendation breath — the gold beacon's glow shell swells on a
        //    slow cycle, paired with (and deliberately slower than) the ring
        //    pulse. Detached objects are skipped so this self-prunes.
        const glows = stateRef.current.breathingGlows;
        if (glows && glows.size) {
          const s = 1 + GOLD_BREATH_AMOUNT * Math.sin((elapsed / GOLD_BREATH_PERIOD_SEC) * Math.PI * 2);
          for (const [id, mesh] of glows) {
            if (!mesh.parent) { glows.delete(id); continue; }
            mesh.scale.setScalar(s);
          }
        }
      }
      controls.update();
      composer.render();
      cssRenderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    // BUG (found live 2026-07-28): setViewOffset(w, h, off, 0, w, h) declared
    // a virtual sensor the SAME width as the requested window — mathematically
    // degenerate (there is no room left to shift into), and produced zero
    // visible pan even though camera.view read back as "enabled". The correct
    // lens-shift form treats the sensor as (w+off) wide and requests only the
    // real w-wide slice starting at x=off — i.e. we're deliberately showing
    // the RIGHT slice of a WIDER frame, which pans the apparent scene content
    // left to clear the obscured region. This is three.js's documented
    // off-center/tiled-rendering technique, applied here for one tile.
    //
    // ELLIPSE BUG (found live in this reconciliation): the lens shift above
    // silently broke circularity. three.js computes the frustum as
    //   height = 2 * near * tan(fov/2);  width = aspect * height;
    //   width *= view.width / view.fullWidth;      // <- offset applied here
    // Vertical is untouched (offsetY 0, view.height == fullHeight), but the
    // horizontal world span is multiplied by w/(w+px) and still rendered into
    // w pixels — so the horizontal scale becomes (w+px)/w times the vertical
    // one and the sphere renders as an ellipse for as long as an offset is
    // applied. `camera.aspect` must therefore describe the VIRTUAL (wider)
    // sensor, not the canvas: with aspect = (w+px)/h the two scales match
    // exactly and the shift is a pure pan.
    const setOffsetPx = (px) => {
      const w = stateRef.current.lastWidth || width;
      const hh = stateRef.current.lastHeight || h;
      if (px > 0.5 && w > px) {
        camera.aspect = (w + px) / hh;
        camera.setViewOffset(w + px, hh, px, 0, w, hh);
      } else {
        camera.aspect = w / hh;
        camera.clearViewOffset();
      }
      camera.updateProjectionMatrix();
      stateRef.current.currentOffsetPx = px;
    };
    // Instant application — used on mount and on real container resizes,
    // where an animated pan would fight the resize instead of tracking it.
    const applyViewOffset = () => setOffsetPx(stateRef.current.obscuredRightPx || 0);
    stateRef.current.applyViewOffset = applyViewOffset;
    // Animated application — used when the Inspector opens/closes, so the
    // globe visibly reframes around it instead of snapping.
    const animateViewOffsetTo = (targetPx) => {
      if (stateRef.current.offsetTweenCancel) {
        stateRef.current.offsetTweenCancel();
        stateRef.current.offsetTweenCancel = null;
      }
      const startPx = stateRef.current.currentOffsetPx || 0;
      if (Math.abs(targetPx - startPx) < 0.5) { setOffsetPx(targetPx); return; }
      const duration = 500;
      const startTime = performance.now();
      let raf;
      const step = (now) => {
        const t = Math.min(1, (now - startTime) / duration);
        setOffsetPx(startPx + (targetPx - startPx) * easeOutQuart(t));
        if (t < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
      stateRef.current.offsetTweenCancel = () => cancelAnimationFrame(raf);
    };
    stateRef.current.animateViewOffsetTo = animateViewOffsetTo;

    // Animated companion to the lens shift. When the Inspector opens, the
    // VISIBLE width shrinks, so the resting fit distance changes (see
    // applySize) — applying that instantly would pop the globe's scale while
    // the pan glided, and closing the Inspector (which fires no selection
    // flight) would pop it back. Same duration and easing as the offset tween
    // so the two read as one movement.
    const animateFitDistanceTo = (targetDistance) => {
      if (stateRef.current.fitTweenCancel) {
        stateRef.current.fitTweenCancel();
        stateRef.current.fitTweenCancel = null;
      }
      const startLen = camera.position.length();
      if (!Number.isFinite(targetDistance) || Math.abs(targetDistance - startLen) < 1) return;
      const duration = 500;
      const startTime = performance.now();
      let raf;
      const step = (now) => {
        const t = Math.min(1, (now - startTime) / duration);
        camera.position.setLength(startLen + (targetDistance - startLen) * easeOutQuart(t));
        if (t < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
      stateRef.current.fitTweenCancel = () => cancelAnimationFrame(raf);
    };

    // Resizes now carry HEIGHT as well as width. Previously only width was
    // tracked, so a layout that changed the panel's height (or any autoHeight
    // container) left the renderer, composer, CSS2D layer and camera aspect
    // all sized to a stale height — which is the other half of how a
    // "technically responsive" canvas could still compose wrongly.
    const applySize = (w, hArg, { animateFit = false } = {}) => {
      if (!w) return;
      const hh = Math.max(80, Math.round(hArg || stateRef.current.lastHeight || h));
      stateRef.current.lastWidth = w;
      stateRef.current.lastHeight = hh;
      // Re-fit the camera to the new box, measured against the VISIBLE width
      // (an open Inspector covers part of the canvas). Only the resting
      // framing is recomputed; a user zoom is respected because the camera is
      // only repositioned when it is still sitting at the previous fit.
      const prevFit = stateRef.current.fitDistance;
      const visibleW = Math.max(120, w - (stateRef.current.obscuredRightPx || 0));
      const nextFit = fitCameraDistance(visibleW, hh);
      stateRef.current.fitDistance = nextFit;
      // OrbitControls clamps distance to [minDistance, maxDistance] on EVERY
      // update(), so a fit farther than maxDistance is silently overridden and
      // the sphere stays too large for its frame. That is exactly what happened
      // with the Inspector open on a narrow canvas: the fit asked for 935, the
      // 460 ceiling won, and 53px of the globe hung off the canvas edge while
      // the rest sat under the panel. Raise the CEILING only — never the floor,
      // and never below the original 460 — so the producer's existing zoom-out
      // range is preserved and merely extended when the layout demands it.
      if (controlsRef.current) {
        controlsRef.current.maxDistance = Math.max(ORBIT_MAX_DISTANCE, nextFit * 1.02);
      }
      const atRestingFraming =
        prevFit == null || Math.abs(camera.position.length() - prevFit) < 1.5;
      if (atRestingFraming) {
        // Instant on a real container resize (animating would fight the
        // resize); animated when the Inspector changed the visible width.
        if (animateFit) animateFitDistanceTo(nextFit);
        else camera.position.setLength(nextFit);
      }

      renderer.setSize(w, hh);
      // The composer owns its own render targets — resizing only the
      // renderer would leave the post chain sampling a stale-sized buffer
      // and the Globe would render soft/stretched after any panel resize.
      composer.setSize(w, hh);
      bloomPass.setSize(w, hh);
      cssRenderer.setSize(w, hh);
      // applyViewOffset() owns camera.aspect + updateProjectionMatrix().
      applyViewOffset();
    };

    const resizeObserver = new ResizeObserver((entries) => {
      const box = entries[0]?.contentRect;
      if (!box?.width) return;
      applySize(Math.round(box.width), autoHeight ? Math.round(box.height) : undefined);
    });
    resizeObserver.observe(mount);
    // Called by the obscuredRightPx effect: same re-fit path as a resize, but
    // triggered by the Inspector changing how much of the canvas is visible.
    stateRef.current.refitForObscuredWidth = () => {
      applySize(stateRef.current.lastWidth || width, stateRef.current.lastHeight || h, { animateFit: true });
    };
    // First measurement: in autoHeight mode the mount's box is only final
    // after layout, so run one explicit fit now rather than waiting for a
    // resize that may never come if the box never changes again.
    applySize(width, h);

    // Hit-targets only emit mouseleave while they stay under the cursor. If
    // the pointer exits the canvas altogether the last hover card would
    // otherwise stay pinned, so clear it at the container boundary too.
    const clearHover = () => onPointHover && onPointHover(null);
    mount.addEventListener("mouseleave", clearHover);

    // ── Live theme response ────────────────────────────────────────────
    // Recolours the existing scene in place. Deliberately NOT a remount:
    // rebuilding on every theme switch would drop and recreate the WebGL
    // context (and with it the PMREM bake), which both costs a visible hitch
    // and risks the context-exhaustion failure this component already
    // guards against. Materials are mutated, `needsUpdate` is not required
    // for colour-only changes on an existing program.
    const applyTheme = () => {
      const t = globeTheme();
      material.color.set(t.ocean);
      material.emissive.set(t.oceanEmissive);
      material.envMapIntensity = t.envIntensity;
      renderer.toneMappingExposure = t.exposure;
      if (rimMesh) rimMesh.material.uniforms.uColor.value.set(t.rim);
      // Rebuild the backdrop ramp; the old texture is disposed so the swap
      // cannot leak a GPU allocation per toggle.
      const nextBackdrop = makeOceanBackgroundTexture();
      const prevBackdrop = scene.background;
      scene.background = nextBackdrop;
      if (prevBackdrop && prevBackdrop !== nextBackdrop) prevBackdrop.dispose();
      stateRef.current.backdropTexture = nextBackdrop;
      // Borders are read through the live accessor, so re-invoking it is
      // what makes three-globe repaint the stroke colour.
      liveRef.current.strokeColor = t.stroke;
      liveRef.current.landColor = t.land;
      // Rescale every already-cached polygon material's environment response
      // so land/status caps track the theme alongside the ocean. Colour-only
      // and scalar changes on an existing program need no `needsUpdate`.
      liveRef.current.capEnvScale = t.capEnvScale ?? 1;
      for (const cache of [capMaterialCache, sideMaterialCache]) {
        for (const m of cache.values()) {
          applyCapEnvScale(m, m.userData.arBaseEnvIntensity ?? m.envMapIntensity);
        }
      }
      if (globeRef.current) {
        globeRef.current
          .polygonStrokeColor(globeRef.current.polygonStrokeColor())
          .polygonCapColor(globeRef.current.polygonCapColor())
          .polygonCapMaterial(globeRef.current.polygonCapMaterial());
      }
    };
    applyTheme();
    const unsubscribeTheme = subscribeTheme(applyTheme);

    stateRef.current = { ...stateRef.current, renderer, controls, frameId, clearHoverListener: clearHover };

    return () => {
      cancelled = true;
      cancelAnimationFrame(frameId);
      if (stateRef.current.cameraTweenCancel) stateRef.current.cameraTweenCancel();
      if (stateRef.current.offsetTweenCancel) stateRef.current.offsetTweenCancel();
      if (stateRef.current.fitTweenCancel) stateRef.current.fitTweenCancel();
      mount.removeEventListener("mouseleave", clearHover);
      resizeObserver.disconnect();
      controls.removeEventListener("start", onControlStart);
      controls.dispose();
      // Post chain + IBL own real GPU allocations (multiple full-size render
      // targets for bloom, a cubemap render target for the environment).
      // Leaking these across route changes is far more expensive than
      // leaking a material, so they are torn down explicitly.
      composer.dispose();
      bloomPass.dispose();
      envRT.dispose();
      pmrem.dispose();
      scene.environment = null;
      material.dispose();
      renderer.dispose();
      unsubscribeTheme();
      oceanTexture.dispose();
      // applyTheme() swaps in a fresh backdrop texture; dispose whichever is
      // current so a theme toggle before unmount cannot leak one.
      if (stateRef.current.backdropTexture && stateRef.current.backdropTexture !== oceanTexture) {
        stateRef.current.backdropTexture.dispose();
      }
      capMaterialCache.forEach((m) => m.dispose());
      sideMaterialCache.forEach((m) => m.dispose());
      if (rimMesh) { rimMesh.geometry.dispose(); rimMesh.material.dispose(); }
      // dispose() frees GPU resources but does NOT release the underlying
      // WebGL context — it lingers on the detached canvas until GC. With a
      // persistent sidebar globe plus route globes mounting/unmounting (and
      // StrictMode's dev double-mount), those zombie contexts accumulate
      // past the browser's hard ~16-context limit, after which every new
      // THREE.WebGLRenderer fails with "Error creating WebGL context".
      try { renderer.forceContextLoss(); } catch { /* context already lost */ }
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      if (mount.contains(cssRenderer.domElement)) mount.removeChild(cssRenderer.domElement);
      if (vignette && mount.contains(vignette)) mount.removeChild(vignette);
      globeRef.current = null;
      cameraRef.current = null;
      controlsRef.current = null;
      stateRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update points/arcs on data change without re-mounting the whole scene.
  useEffect(() => {
    liveRef.current.pointRadius = pointRadius;
    const globe = globeRef.current;
    if (globe) {
      globe.pointsData(points);
      globe.htmlElementsData(points);
      globe.arcsData(arcs);
      globe.pointColor(globe.pointColor()).pointAltitude(globe.pointAltitude()).pointRadius(globe.pointRadius());
      const geoSet = liveRef.current.geoIsoSet;
      if (geoSet) {
        const small = points.filter((d) => d?.iso && !geoSet.has(d.iso) && !SUBNATIONAL_COUNTRY_ISOS.has(d.iso));
        // Pulse stays recommendation-only here too. This branch had its own
        // hand-written copy of the ring predicate (`tier === "gold" ||
        // small.includes(d)`) which re-added the small-jurisdiction pulse on
        // every data change — so the fix in isRingEligible alone would have
        // been undone the moment the producer changed an input.
        globe.ringsData(points.filter((d) => !!d?.tier && PULSE_TIERS.has(d.tier)));
        globe.customLayerData(small);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, arcs, pointRadius]);

  // Hover repaint. Separate from the selection effect on purpose: hover
  // changes at pointer speed and must NOT re-run the camera flight, the
  // rings, or the beacon update that the selection effect performs.
  //
  // Only the cap material, sidewall and stroke accessors are re-invoked.
  // Because a cap material override is in play, three-globe swaps our cached
  // material straight in and skips its own colour tween (verified in dist
  // source), so the brighten lands on the same frame — the snap hover needs —
  // while altitude, which nothing here touches, keeps its 500ms selection
  // easing.
  useEffect(() => {
    if (liveRef.current.hoveredIso === hoveredIso) return;
    liveRef.current.hoveredIso = hoveredIso;
    const globe = globeRef.current;
    if (!globe) return;
    globe
      .polygonCapColor(globe.polygonCapColor())
      .polygonSideColor(globe.polygonSideColor())
      .polygonCapMaterial(globe.polygonCapMaterial())
      .polygonSideMaterial(globe.polygonSideMaterial())
      .polygonStrokeColor(globe.polygonStrokeColor());
  }, [hoveredIso]);

  useEffect(() => {
    stateRef.current.obscuredRightPx = obscuredRightPx;
    // Re-fit to the width that remains VISIBLE once the Inspector covers part
    // of the canvas, so an open Inspector can never crop the sphere. Only the
    // resting framing is adjusted (see applySize); a user zoom is left alone.
    stateRef.current.refitForObscuredWidth?.();
    // Animated reframe when the Inspector opens/closes — a snap here reads
    // as a glitch; a smooth pan reads as the Globe deliberately making room.
    stateRef.current.animateViewOffsetTo?.(obscuredRightPx || 0);
  }, [obscuredRightPx]);

  // Status/selection change: repaint the polygon + point layers in place
  // (three-globe tweens altitude and colour over SELECTION_TRANSITION_MS),
  // raise the glass rim, and fly the camera on an easeOutQuart. Selection
  // NEVER touches the selected jurisdiction's own hue — only elevation,
  // perimeter, rim intensity, and the dimming of the others.
  useEffect(() => {
    liveRef.current.polygonColors = polygonColors;
    liveRef.current.selectedIso = selectedIso;
    const globe = globeRef.current;
    if (!globe) return;
    globe
      .polygonCapColor(globe.polygonCapColor())
      .polygonSideColor(globe.polygonSideColor())
      .polygonCapMaterial(globe.polygonCapMaterial())
      .polygonSideMaterial(globe.polygonSideMaterial())
      .polygonStrokeColor(globe.polygonStrokeColor())
      .polygonAltitude(globe.polygonAltitude())
      .pointColor(globe.pointColor())
      .pointAltitude(globe.pointAltitude())
      .pointRadius(globe.pointRadius());
    // Selection raises the glass rim slightly — the "illuminated" read that
    // previously came from nudging the atmosphere altitude. When ambient
    // motion is active the animate loop recomputes this every frame from the
    // same base, so this assignment only matters under reduced-motion (where
    // the loop is skipped) — it is kept unconditionally so the two paths can
    // never disagree about the resting value.
    const rm = stateRef.current.rimMesh;
    if (rm) rm.material.uniforms.uIntensity.value = selectedIso ? SELECTED_RIM_INTENSITY : BASE_RIM_INTENSITY;
    // Ambient autorotation yields to inspection: a selected jurisdiction must
    // hold still while it is being read. It resumes only if the selection is
    // cleared AND the producer never took the camera themselves.
    const ctl = controlsRef.current;
    if (ctl) {
      ctl.autoRotate = !!stateRef.current.ambientMotion && !stateRef.current.userTookControl && !selectedIso;
    }
    globe.customThreeObjectUpdate(globe.customThreeObjectUpdate());

    if (stateRef.current.cameraTweenCancel) {
      stateRef.current.cameraTweenCancel();
      stateRef.current.cameraTweenCancel = null;
    }
    // The Inspector's fit tween also writes camera.position; the selection
    // flight below supersedes it, so cancel it or the two fight frame by frame.
    if (stateRef.current.fitTweenCancel) {
      stateRef.current.fitTweenCancel();
      stateRef.current.fitTweenCancel = null;
    }
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    const targetLat = focusLat ?? selectedLat;
    const targetLng = focusLng ?? selectedLng;
    if (targetLat == null || targetLng == null || !camera || !controls) return;

    // The globe is about to move under a stationary cursor, so the hovered
    // hit-target will slide away without ever firing mouseleave.
    if (onPointHover) onPointHover(null);

    const dest = globe.getCoords(targetLat, targetLng, 0);
    const dir = new THREE.Vector3(dest.x, dest.y, dest.z).normalize();
    // Floor the flight distance at the computed fit, so selecting a
    // jurisdiction can never leave the sphere clipped. This replaces a
    // hardcoded `DEFAULT_CAMERA_DISTANCE - 30` floor which, at the old
    // distance, was itself inside the clipping range.
    const restingFit = stateRef.current.fitDistance ?? DEFAULT_CAMERA_DISTANCE;
    const distance = focusDistance ?? Math.max(camera.position.length(), restingFit);
    const endPos = dir.multiplyScalar(distance);
    const startPos = camera.position.clone();
    const duration = 700;
    const startTime = performance.now();
    let raf;
    const step = (now) => {
      const t = Math.min(1, (now - startTime) / duration);
      camera.position.lerpVectors(startPos, endPos, easeOutQuart(t));
      camera.lookAt(0, 0, 0);
      if (t < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    stateRef.current.cameraTweenCancel = () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance]);

  // Static identity-globe fallback: a smoked sphere drawn purely in CSS.
  // Preserves the CineGlobe identity when WebGL is unavailable and lets the
  // surrounding page render normally.
  if (failed) {
    return (
      <div className="globe-canvas globe-static" style={{ height }} role="img" aria-label="CineGlobe">
        <div className="globe-static-sphere" />
      </div>
    );
  }

  // autoHeight: the CSS box owns the height (the mount fills its stage, with
  // the `height` prop acting only as a floor). Fixed-height callers keep the
  // exact inline pixel height they had before.
  return (
    <div
      ref={mountRef}
      className="globe-canvas"
      style={autoHeight ? { height: "100%", minHeight: height } : { height }}
    />
  );
}
