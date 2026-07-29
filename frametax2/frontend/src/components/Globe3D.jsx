import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import ThreeGlobe from "three-globe";

// ══════════════════════════════════════════════════════════════════════
// FROZEN (2026-07-28): production Globe materials, lighting, ocean,
// inactive-land treatment, status base palette application, Admin-1
// geometry composition, selection/camera/Inspector-framing behavior, and
// beacon fallback are all verified working (live click-through of
// California, New York, Georgia, Ontario, Quebec, British Columbia,
// Mauritius, Malta, plus card sync, one-click A->B transfer, and Optimizer
// Overlay arcs — see the closeout report for that session).
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

// Kept in sync with lib/globeData.js STATUS_HEX by hand — three-globe's
// point/beacon accessors run inside this file and have no import path back
// to globeData.js's own module (would create a cycle), so this is the one
// place that duplicate has to live. Brightened together in the 2026-07-28
// regression-lock pass — see STATUS_HEX for the rationale.
const TIER_HEX = {
  gold: "#e8c273",
  jade: "#4bab7f",
  silver: "#b0aca2",
  amber: "#e0a83f",
  red: "#a3453c",
  charcoal: "#4c483f",
};

// ── Visual hierarchy ────────────────────────────────────────────────────
// Deliberate luminance ladder, dark -> light, so each layer separates from
// the one beneath it instead of merging:
//   ocean (deepest, warm blackened glass) < inactive land (lighter frosted
//   graphite) < borders (lightest neutral) < status colours (the only
//   saturated thing here).
// Every hue below is deliberately grounded in the app's own "Dark Luxury
// Glass" tokens (tokens.css --dark-canvas/--dark-surface-0/1/--dark-text-*)
// plus --oxblood and --gold — the Globe previously invented an unrelated
// cold-blue/cyan palette that shared no hue family with the warm ivory /
// charcoal / oxblood / brass application shell around it. Status colours
// (TIER_HEX below) are untouched: they were already warm and are never
// recoloured by this pass.
// Ocean tightened to true neutral obsidian (2026-07-28 closeout pass): the
// previous value read as faintly brown at large sizes. Minimal R/G/B spread
// on purpose — "smoked glass", not a tinted one. Land fill lightened further
// for stronger ocean/land separation, per the same pass. Lifted one notch
// again in the regression-lock pass — #100f0d read as flat pure black in
// screenshots; this keeps the same neutral hue but with enough value to
// still read as "smoked glass" rather than a hole in the sphere.
// Isolated material-correction pass (2026-07-28): the ocean kept reading as
// literal black in rendered screenshots no matter how many times this hex
// alone was nudged — because a dark DIFFUSE colour is bounded above by
// itself under Phong shading (base-colour x light can only ever go darker
// than "lit", never brighter than the base colour on the unlit hemisphere).
// Fixed at the material level below instead: material.emissive now carries
// a real, non-trivial value so the sphere has a GUARANTEED visible floor
// colour independent of camera/light angle, while the diffuse base below
// still provides the lit-hemisphere variation ("internal depth").
const OCEAN_BODY = "#211c15"; // near-neutral obsidian, negligible hue
const NEUTRAL_FILL = "#4a4136"; // frosted graphite, warm taupe — clearly lighter than the ocean
const NEUTRAL_STROKE = "#7d7362"; // == --dark-text-tertiary
const BRAND_NEUTRAL_FILL = "#564d3e"; // higher contrast for the 76px mark
const SELECTED_STROKE = "#f4ecd9"; // == --dark-text-primary
// The leading recommendation gets its own bright perimeter — the single
// strongest "look here" cue on the Globe, present without interaction.
const GOLD_STROKE = "#f7e3ab";

// Fresnel rim strength. Raised on selection to read as "illuminated". The
// rim colour itself is warm brass now (was a cold blue "#4a7fb5") — the
// glass edge should read as gilt trim on a premium instrument, not a sci-fi
// force field.
const BASE_RIM_INTENSITY = 0.34;
const SELECTED_RIM_INTENSITY = 0.5;
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
// Default framing only. minDistance/maxDistance are untouched, so the
// user's own zoom range is exactly as it was. Pulled in from 246 so the
// globe fills more of its panel by default.
const DEFAULT_CAMERA_DISTANCE = 225;

function easeOutQuart(t) {
  return 1 - Math.pow(1 - t, 4);
}

// Blend a status hex toward the neutral fill — used to softly dim
// participating countries other than the current selection. Never used to
// change a SELECTED country's own hue (selection never repaints status).
function dimHex(hex, amount = 0.66) {
  try {
    const c = new THREE.Color(hex);
    const n = new THREE.Color(NEUTRAL_FILL);
    return `#${c.lerp(n, amount).getHexString()}`;
  } catch {
    return hex;
  }
}

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
  const grad = ctx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, "#161310");
  grad.addColorStop(0.55, "#100d0a");
  grad.addColorStop(1, "#070504");
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
  polygonColors = null,
  selectedIso = null,
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
  const liveRef = useRef({ polygonColors: null, selectedIso: null, pointRadius: null, geoIsoSet: null });
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    if (stateRef.current.renderer) return;
    if (!webglAvailable()) { setFailed(true); return; }

    // getBoundingClientRect rather than clientWidth: for a tiny flex-basis
    // container (the 80px sidebar brand mark), clientWidth can still read 0
    // on the very first synchronous measurement if the browser hasn't
    // committed that flex child's layout yet, which set the camera's
    // aspect ratio from the wrong (fallback-to-parent, ~230px-wide sidebar)
    // width — the sphere then rendered squashed/mis-cropped inside the 80px
    // circular mask until a later resize happened to correct it.
    // getBoundingClientRect reflects the actual computed box at call time.
    const width = Math.round(mount.getBoundingClientRect().width) || mount.clientWidth || mount.parentElement?.clientWidth || 600;
    const h = height;

    const scene = new THREE.Scene();
    const oceanTexture = makeOceanBackgroundTexture();
    scene.background = oceanTexture;

    const camera = new THREE.PerspectiveCamera(50, width / h, 0.1, 2000);
    // Default framing only — pulled in so the globe dominates its panel.
    // The OrbitControls min/max below are unchanged, so the user's own
    // zoom range is exactly what it was.
    camera.position.set(0, 0, DEFAULT_CAMERA_DISTANCE);
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
    mount.innerHTML = "";
    mount.style.position = "relative";
    mount.appendChild(renderer.domElement);

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
      vignette.style.background = "radial-gradient(circle at 50% 45%, rgba(0,0,0,0) 52%, rgba(10,7,5,0.55) 100%)";
      mount.appendChild(vignette);
    }

    // Lighting: a warm ivory key, a warm taupe fill, and a brass back/rim
    // opposite the key. The rim is what gives the sphere mass — it separates
    // the dark limb from the dark backdrop instead of letting them fuse.
    // Every colour here is warm now (was a cold blue-grey trio) — this is
    // one of the two biggest levers in pulling the Globe into the same
    // family as the app's warm ivory / oxblood / brass shell.
    scene.add(new THREE.AmbientLight(0x332b22, 0.72));
    const key = new THREE.DirectionalLight(0xf2ead9, 1.12);
    key.position.set(200, 120, 200);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x8a7860, 0.4);
    fill.position.set(-200, -80, -150);
    scene.add(fill);
    const rim = new THREE.DirectionalLight(0xd4a860, isBrand ? 0.3 : 0.62);
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

    const capColorFn = (feat) => {
      const iso = isoOfFeature(feat);
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      if (!hex) return neutralFill;
      const sel = liveRef.current.selectedIso;
      if (sel && iso !== sel) return dimHex(hex);
      return hex;
    };
    const strokeColorFn = (feat) => {
      const iso = isoOfFeature(feat);
      if (liveRef.current.selectedIso && iso === liveRef.current.selectedIso) return SELECTED_STROKE;
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      if (hex === TIER_HEX.gold) return GOLD_STROKE;
      return NEUTRAL_STROKE;
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
        const cap = sel && iso !== sel ? dimHex(hex) : hex;
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
    const capMaterialCache = new Map();
    const getCapMaterial = (hex) => {
      let m = capMaterialCache.get(hex);
      if (!m) {
        m = new THREE.MeshPhongMaterial({
          color: new THREE.Color(hex),
          shininess: 55,
          specular: new THREE.Color("#3a3226"),
          side: THREE.DoubleSide,
          depthWrite: true,
        });
        capMaterialCache.set(hex, m);
      }
      return m;
    };
    const sideMaterialCache = new Map();
    const getSideMaterial = (hex) => {
      let m = sideMaterialCache.get(hex);
      if (!m) {
        m = new THREE.MeshPhongMaterial({
          color: new THREE.Color(hex),
          shininess: 16,
          specular: new THREE.Color("#221c14"),
          side: THREE.DoubleSide,
          depthWrite: true,
        });
        sideMaterialCache.set(hex, m);
      }
      return m;
    };
    const activeHex = (feat) => {
      const iso = isoOfFeature(feat);
      const colors = liveRef.current.polygonColors;
      return colors?.get ? colors.get(iso) : colors?.[iso];
    };
    const capMaterialFn = (feat) => (activeHex(feat) ? getCapMaterial(capColorFn(feat)) : null);
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
    const isRingEligible = (d) => d?.tier === "gold" || isSmallJurisdiction(d);
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
      if (isSmallJurisdiction(d) && liveRef.current.selectedIso && d.iso !== liveRef.current.selectedIso) return dimHex(hex);
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
      .ringColor((d) => (t) => hexWithAlpha(d.color || TIER_HEX.charcoal, 1 - t))
      .ringMaxRadius(2.9)
      .ringPropagationSpeed(0.9)
      .ringRepeatPeriod(2600)
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

    // Deep, neutral smoked-obsidian body — not flat blue, not brown, not
    // flat black. Specular is deliberately BOTH very tight (high shininess)
    // and low-amplitude: at shininess 120 with a bright specular colour the
    // key light's highlight grew into a large washed-out blob whenever the
    // camera lined up with it — most visible in the Optimizer Overlay's
    // pulled-back framing. These values keep a small polished glint at every
    // camera angle instead.
    const material = globe.globeMaterial();
    material.color = new THREE.Color(OCEAN_BODY);
    // Raised from #080706 — that value was too close to zero to guarantee
    // visibility on the unlit hemisphere, which is why the ocean kept
    // reading as literal black regardless of the diffuse base colour above.
    // Emissive is additive and lighting-independent, so this is now a real
    // floor brightness the sphere can never fall below.
    material.emissive = new THREE.Color("#1c170f");
    material.shininess = 300;
    // Specular is kept very dark on purpose (same empirical finding as
    // before — raising shininess alone only shrank the key light's
    // highlight, it did not stop it saturating to white). Now tinted warm
    // brass instead of cold blue-grey so the glint itself reads as metal
    // trim rather than chrome.
    // Darkened one further notch (2026-07-28 freeze pass): at #332619 the
    // key light's highlight was still clipping bright enough at some camera
    // angles (confirmed live, Workspace/Project Globe over North America)
    // to read as a soft blob wider than a restrained glint should be. This
    // keeps the same warm-brass hue, just lower amplitude, so the highlight
    // stays a tight point rather than blooming outward.
    material.specular = new THREE.Color("#241a11");

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
            uColor: { value: new THREE.Color("#c9a15a") },
            uIntensity: { value: BASE_RIM_INTENSITY },
            uPower: { value: 1.9 },
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
    controls.autoRotate = points.length <= 1 && !prefersReducedMotion;
    controls.autoRotateSpeed = 0.22;
    // Unchanged zoom range — only the default position above moved.
    controls.minDistance = 150;
    controls.maxDistance = 460;
    controls.enablePan = false;
    controlsRef.current = controls;

    let frameId;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
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
    const setOffsetPx = (px) => {
      const w = stateRef.current.lastWidth || width;
      if (px > 0.5 && w > px) {
        camera.setViewOffset(w + px, h, px, 0, w, h);
      } else {
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

    const applySize = (w) => {
      if (!w) return;
      stateRef.current.lastWidth = w;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      cssRenderer.setSize(w, h);
      applyViewOffset();
    };

    const resizeObserver = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect?.width;
      if (w) applySize(Math.round(w));
    });
    resizeObserver.observe(mount);

    // Hit-targets only emit mouseleave while they stay under the cursor. If
    // the pointer exits the canvas altogether the last hover card would
    // otherwise stay pinned, so clear it at the container boundary too.
    const clearHover = () => onPointHover && onPointHover(null);
    mount.addEventListener("mouseleave", clearHover);

    stateRef.current = { ...stateRef.current, renderer, controls, frameId, clearHoverListener: clearHover };

    return () => {
      cancelled = true;
      cancelAnimationFrame(frameId);
      if (stateRef.current.cameraTweenCancel) stateRef.current.cameraTweenCancel();
      if (stateRef.current.offsetTweenCancel) stateRef.current.offsetTweenCancel();
      mount.removeEventListener("mouseleave", clearHover);
      resizeObserver.disconnect();
      controls.dispose();
      renderer.dispose();
      oceanTexture.dispose();
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
        globe.ringsData(points.filter((d) => d?.tier === "gold" || small.includes(d)));
        globe.customLayerData(small);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, arcs, pointRadius]);

  useEffect(() => {
    stateRef.current.obscuredRightPx = obscuredRightPx;
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
    // previously came from nudging the atmosphere altitude.
    const rm = stateRef.current.rimMesh;
    if (rm) rm.material.uniforms.uIntensity.value = selectedIso ? SELECTED_RIM_INTENSITY : BASE_RIM_INTENSITY;
    globe.customThreeObjectUpdate(globe.customThreeObjectUpdate());

    if (stateRef.current.cameraTweenCancel) {
      stateRef.current.cameraTweenCancel();
      stateRef.current.cameraTweenCancel = null;
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
    const distance = focusDistance ?? Math.max(camera.position.length(), DEFAULT_CAMERA_DISTANCE - 30);
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

  return <div ref={mountRef} className="globe-canvas" style={{ height }} />;
}
