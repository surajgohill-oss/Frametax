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

  // `tilt` (radians, optional): rotates the panel about its own Z axis.
  // Added for the single strip light below — an axis-aligned bar reflects as
  // a straight streak; tilting it is what lets the sphere's own convex
  // curvature read as curvature in the reflection instead of a straight line.
  const panel = (hex, intensity, pos, scale, tilt = 0) => {
    const m = new THREE.Mesh(
      box,
      new THREE.MeshBasicMaterial({ color: new THREE.Color(hex).multiplyScalar(intensity) }),
    );
    m.position.set(pos[0], pos[1], pos[2]);
    m.scale.set(scale[0], scale[1], scale[2]);
    if (tilt) m.rotation.z = tilt;
    env.add(m);
  };

  // Panel intensities are deliberately LOW. A first calibration ran the key
  // at 2.2 and the strip at 3.0, which mirrored the panels onto the sphere
  // as a discrete blown-white lamp image on the limb — a textbook blown-out
  // hotspot. A premium instrument reflects a soft studio, not a visible
  // bulb, so these stay dim and the map is heavily blurred below.
  //
  // PHASE 3A FINAL CORRECTION: the ocean screenshots showed TWO separate
  // isolated round hotspots, not one directional streak — because there were
  // genuinely two independent bright sources each printing its own
  // reflection. The fix is not "dim everything" (already tried, that's what
  // produced the small-but-still-round spots); it is to give the two panels
  // clearly DIFFERENT jobs so only one of them ever reads as a discrete
  // highlight:
  //   - the softbox is now larger and noticeably dimmer — a broad ambient
  //     WRAP that shapes the sphere's general reflectivity, too large and
  //     too faint to ever print its own point highlight;
  //   - the strip is the ONLY element still meant to be seen as a highlight,
  //     and is now longer and thinner for a more elongated, more clearly
  //     "drawn across the curve" streak, with intensity trimmed slightly to
  //     offset the batch's other reflection-strength increases (deeper
  //     ocean, tighter clearcoatRoughness, raised envMapIntensity).
  // Key softbox, upper front-right — broad ambient wrap only.
  panel("#ffffff", 0.55, [5, 6, 5], [17, 0.2, 17]);
  // PHASE 3A FINAL MICRO-PASS: the three-segment arc (previous pass) still
  // read as a bright spot rather than a curved streak — three short panels
  // at slightly different angles printed three overlapping near-round
  // reflections that merged back into one blob instead of one curve.
  // SIMPLIFIED per this batch's explicit instruction ("simplify rather than
  // add complexity"): back to ONE panel, but longer, thinner, and TILTED
  // (see the new `tilt` param on panel() above) — a straight bar reflected
  // off a convex sphere already reads as curved as long as it is long/thin
  // enough for the curvature to show across its length; tilting it off-axis
  // is what keeps that curve from reading as a simple horizontal streak.
  //
  // PHASE 3A FINAL VISUAL CORRECTION: still printed as an isolated bright
  // spot at normal page scale. The panel's LENGTH was already long enough to
  // curve; the problem was the sharp clearcoat sampling it at near-mirror
  // roughness, which turns even a long source into a small, high-contrast
  // hotspot at its tangent point — the panel shape was never the limiting
  // factor. Fixed by softening the reflector, not by adding a light:
  // clearcoatRoughness raised further below (0.56 -> 0.68 base, still
  // texture-varied) spreads the same energy over a visibly wider, softer
  // patch. Paired with a taller panel (0.07 -> 0.16, same length/intensity
  // otherwise) so the source itself is less needle-thin at its brightest
  // point, and a slightly steeper tilt (Math.PI/10 -> Math.PI/7) so the
  // streak reads as diagonal/curved rather than near-horizontal. Intensity
  // trimmed again (0.95 -> 0.78) to offset the taller panel.
  panel("#ffffff", 0.78, [-2, 7.2, -3], [24, 0.16, 0.8], Math.PI / 7);
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
// ── PHASE 3A: coordinated optical foundation ────────────────────────────
// Land, ocean, atmosphere and exposure are tuned TOGETHER here, not as
// independent passes — that was the explicit correction to this batch's
// plan: perfecting land against the old (near-black, flat) ocean would have
// meant re-doing land the moment ocean changed. Every value below was
// re-verified live as one combined checkpoint (see the freeze manifest for
// the runtime evidence), not derived from the hex alone.
const GLOBE_THEME = {
  day: {
    // DEEPENED + SATURATED from #3a4250 (a near-neutral slate that read as
    // flat/near-black once rendered). This is a real saturated deep blue —
    // the "luminous dimensional ocean" the approved render shows is carried
    // mostly by the emissive floor and the sharpened clearcoat highlight
    // below, but the base color itself now has to be a blue an eye would
    // call "ocean" even unlit, not a desaturated gray-blue.
    ocean: "#1c3350",
    // Raised in step with the base color so the unlit hemisphere of the
    // ocean still reads as deep blue rather than collapsing toward black —
    // same guaranteed-floor role the land emissive floor plays below.
    oceanEmissive: "#16283f",
    land: GRAPHITE_HEX,
    stroke: "#9aa3b0",
    rim: "#b9c1cb",
    // PHASE 3A FINAL CORRECTION: deepened from the pale #8fc6ff, which read
    // as washed-out/whitish once the altitude tightened — a limb glow needs
    // enough of its own saturation to register as colour, not just as more
    // white. Still cool and still close in hue to `rim`, so the two read as
    // one coherent edge treatment rather than competing effects.
    atmosphere: "#6fb4ef",
    backdrop: ["#14161a", "#0f1114", "#0a0c0e"],
    // Raised modestly from 0.95: a first, conservative increment paired with
    // the deepened ocean and the atmosphere re-enable, verified live rather
    // than chased to a target number. The neutral-light-rig ratio (ambient
    // must not dominate the key) is untouched — this is exposure only.
    exposure: 1.02,
    // PHASE 3A FINAL RECONCILIATION: 0.40 -> 0.44 — a small, deliberately
    // modest raise (item 2/5: "reflection breakup", "center-to-limb depth"),
    // paired with the clearcoatRoughnessMap above so the extra reflectivity
    // has genuine per-pixel variation to break up rather than printing a
    // single brighter blob.
    // PHASE 3B CLOSEOUT: 0.44 -> 0.50 — the ocean read as flat/near-black in
    // runtime review; a stronger reflected response, paired with the crisper
    // clearcoatRoughness below, is what makes the surface read as dimensional
    // rather than a flat tint. Base colour/hue untouched (still dark navy).
    envIntensity: 0.50,
    // Multiplier on the polygon cap/side materials' own envMapIntensity.
    // Day is the identity by definition — the day render is the frozen,
    // verified baseline and this consolidation must not alter a pixel of it.
    capEnvScale: 1.0,
  },
  night: {
    // Deepened in step with day, keeping the same relative move (a more
    // saturated, less desaturated-gray navy). Still clearly darker than day's
    // ocean — night must stay night — but no longer reads as a flat void.
    ocean: "#152540",
    // Faint internal blue illumination — the "lit from within" quality the
    // art direction calls for, and the guarantee the ocean never collapses.
    oceanEmissive: "#10203a",
    // Neutral grey land on a navy ocean is precisely what reads as an
    // unfinished or missing asset — the two share no hue family. Night land
    // is a navy-slate: clearly lighter than the ocean, clearly darker than
    // any status colour, and unmistakably part of the same material world.
    //
    // PHASE 3A: hue moved from navy-slate (#586479) to a teal-leaning
    // navy-slate (#4f6870, luminance held ~97 vs the prior ~99), matching the
    // day-mode land's teal-slate move (GRAPHITE_HEX) so both themes carry the
    // same material character, not just the same luminance position.
    land: "#4f6870",
    // Borders soften markedly at night: on a dark ground the same value
    // reads far hotter, and hard white admin lines are the single biggest
    // contributor to the "technical GIS map" impression.
    stroke: "#8290a8",
    // Cool silver-blue limb rather than day's neutral platinum.
    rim: "#9fb6d6",
    // Deepened in step with day (same reasoning: the paler predecessor
    // washed out once the shell tightened). Still cooler and quieter than
    // day's — night reads as a deeper, more concentrated blue at the limb
    // rather than a bright daytime glow.
    atmosphere: "#4f8fd0",
    // Meets --dark-canvas/--dark-surface-0 from the night token layer, so
    // the globe panel and the application shell share one continuous field.
    backdrop: ["#0d1420", "#0a1018", "#070b12"],
    // Slightly hotter: the surrounding UI is far darker at night, so the
    // same exposure reads dimmer by simultaneous contrast. Raised in the
    // same proportion as day (1.04 -> 1.12).
    exposure: 1.12,
    // Raised in step with day (0.46 -> 0.50), same reasoning.
    // PHASE 3B CLOSEOUT: raised in step with day (0.50 -> 0.56).
    envIntensity: 0.56,
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
// PHASE 3A FINAL CORRECTION: raised 0.16 -> 0.21, paired with the tighter
// uPower below (2.4 -> 3.1) and the atmosphere shell pulled in (see
// ATMOSPHERE_ALTITUDE). Three layers now do distinct jobs at the limb: this
// shell is the CRISP curvature edge (tight falloff, close to the silhouette),
// the atmosphere is the SOFT glow beyond it, and the studio IBL still
// supplies the moving specular streak across the body — "layered depth near
// the sphere edge" without any one of the three trying to do all three jobs.
// PHASE 3A FINAL RECONCILIATION: 0.21 -> 0.24, paired with the tightened
// ATMOSPHERE_ALTITUDE above — the rim now carries more of the "curvature
// reinforcement" job (item 4) so the atmosphere can be narrower without the
// limb going bare.
// PHASE 3B CLOSEOUT: 0.24 -> 0.29, in step with the ATMOSPHERE_ALTITUDE raise
// above — the crisp curvature edge needed to lift alongside the softer outer
// taper, or the atmosphere raise alone would have widened a still-faint glow
// rather than making the limb genuinely legible.
const BASE_RIM_INTENSITY = 0.29;
const SELECTED_RIM_INTENSITY = 0.32;
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
// PHASE 3A FINAL CORRECTION: pulled IN from the library default 0.15 -> 0.11.
// At 0.15 the shell was wide enough to read as a soft uniform halo around the
// whole disc ("glowing disc" behaviour, explicitly rejected feedback) rather
// than a limb-concentrated glow. Tighter altitude keeps the glow hugging the
// silhouette, where it reads as atmosphere; the Fresnel shell (BASE_RIM_
// INTENSITY, uPower above) is the crisp inner edge, this is the soft outer
// taper beyond it — two layers with two different jobs, not one wide wash.
// PHASE 3A FINAL RECONCILIATION: pulled in further, 0.11 -> 0.095. Against
// the approved render the atmosphere still read as one wide, fairly uniform
// blue wash rather than a limb reinforcing the sphere's curvature. Tightening
// this shell further and raising BASE_RIM_INTENSITY/uPower (below) in the same
// pass is what turns two shells into two visibly DIFFERENT jobs — a crisp
// curvature edge (rim) and a much narrower soft taper beyond it (atmosphere)
// — instead of one wide glow doing both.
// PHASE 3B CLOSEOUT: 0.095 -> 0.125. Runtime review found the shell had been
// tightened past legibility — at 0.095 the atmosphere was difficult to
// perceive at all, not merely restrained. Nudged partway back toward (not to)
// the library default 0.15, paired with the BASE_RIM_INTENSITY raise below,
// so the limb reads as "the planet has atmosphere" without returning to the
// "one wide uniform wash" failure the two comments above document.
const ATMOSPHERE_ALTITUDE = 0.125;

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
//    percent, reading as atmosphere rather than as a hard glass edge. This
//    shell works ALONGSIDE three-globe's own atmosphere layer (re-enabled
//    Phase 3A — see showAtmosphere below), not instead of it: the rim is the
//    crisp curvature edge, the atmosphere is the soft glow beyond it.
const RIM_BREATH_PERIOD_SEC = 11.0;
const RIM_BREATH_AMOUNT = 0.12; // ±12% of the current base intensity
// 3. Recommendation breath: the gold beacon's glow shell swells slightly on
//    a slow cycle. Paired with the ring pulse (gold-only), this is what
//    makes the recommendation the thing the eye returns to.
const GOLD_BREATH_PERIOD_SEC = 4.4;
const GOLD_BREATH_AMOUNT = 0.16;
// 3b. Ocean drift. PHASE 3B CLOSEOUT: sped up from a ~40-minute full cycle
//    (1/2400) to a ~2.5-minute one — the prior rate was too slow to perceive
//    within a normal runtime observation window, which the brief calls out
//    explicitly ("motion must be visually verified, not merely present in
//    source"). Still slow and restrained by any normal-speed standard (a full
//    cycle takes longer than a minute hand's half-revolution); not a "rolling
//    wave," just a slow specular/bump drift across the existing texture.
const OCEAN_DRIFT_PER_SEC = 1 / 150;
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

// ── Country surface grain (Phase 3A final correction) ───────────────────
// "Countries read too flat" was investigated as a MATERIAL problem first —
// checked whether polygon caps have usable UVs for a texture map the same
// way the ocean got one above. They do not, in the sense that matters:
// `three-conic-polygon-geometry` (verified directly in its installed source,
// v0's `uvs.push(i / (numPoints - 1), v)`) parametrizes U by each polygon's
// OWN perimeter walk index, not by any shared geographic frame — a country
// with 40 boundary points and one with 400 get entirely different U scales,
// and none of it corresponds to longitude/latitude. Mapping a single "world"
// texture through these UVs would not read as geographic richness; it would
// read as incoherent per-country noise at a random scale and orientation —
// arguably worse than the flat cap it would replace.
//
// So this is UV-INDEPENDENT: a per-fragment hash computed from OBJECT-SPACE
// vertex position (every polygon cap sits directly in the scene with no
// extra transform, so object space IS the sphere's own coordinate frame —
// continuous across a country's full extent, with no seam and no texture
// sample, because it is a closed-form function of position, not a lookup).
// This is exactly the "controlled shader variation" the brief's own allowed-
// techniques list names, and it changes no geometry and needs no UVs.
//
// Injected at `#include <dithering_fragment>` — the last standard chunk in
// every MeshPhysicalMaterial fragment shader, present regardless of which
// optional features (envMap, clearcoat, etc.) are compiled in, which is why
// this insertion point was chosen over an earlier, feature-conditional one.
// The amplitude is small (~±5%) and applied as a multiply on the ALREADY-LIT
// colour — it cannot invert the semantic ladder or make Additional compete
// with an actionable state, since it perturbs every tier by the same tiny
// fraction of whatever colour that tier already resolved to.
function applyLandGrainShader(material) {
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = `varying vec3 vArGrainPos;\n${shader.vertexShader}`.replace(
      "#include <begin_vertex>",
      "#include <begin_vertex>\n  vArGrainPos = position;",
    );
    shader.fragmentShader = `varying vec3 vArGrainPos;\n${shader.fragmentShader}`.replace(
      "#include <dithering_fragment>",
      `
      {
        float arN1 = fract(sin(dot(vArGrainPos, vec3(12.9898, 78.233, 45.164))) * 43758.5453);
        float arN2 = fract(sin(dot(vArGrainPos * 2.7, vec3(93.989, 67.345, 12.123))) * 24634.6345);
        // PHASE 3A FINAL RECONCILIATION: 0.10 -> 0.14 — countries still read
        // too flat against the render's internal tonal variation (item 3).
        // Still small enough that it cannot invert the semantic ladder (see
        // this function's own header comment).
        float arGrain = (arN1 * 0.6 + arN2 * 0.4 - 0.5) * 0.14;
        gl_FragColor.rgb *= (1.0 + arGrain);
      }
      #include <dithering_fragment>`,
    );
  };
  // The shader text above never depends on a per-material uniform, so every
  // cap material that runs through this function compiles to byte-identical
  // GLSL — three.js's default program cache key already covers that; no
  // custom cache key is needed.
  material.needsUpdate = true;
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

// ── PHASE 3B BATCH 2: border quality — deterministic altitude tie-break ──
// ROOT CAUSE (confirmed directly in the installed three-globe 2.45.2
// source, `node_modules/three-globe/dist/three-globe.mjs`'s polygon layer):
// every country/state polygon renders its OWN complete boundary stroke as
// an independent `LineSegments` + `LineBasicMaterial` (depthTest enabled,
// three-globe's default). A border shared with a neighbour is therefore
// drawn TWICE — once by each country's own feature — and three-globe scales
// each stroke to `1 + altitude + 1e-4` (see its polygon layer's
// `applyUpdate`), i.e. a FIXED relative offset above that feature's OWN
// cap. Two adjacent countries at the SAME semantic tier share the exact
// same `altitude` input, so their strokes land at the identical final
// radius — a textbook coincident-depth GPU z-fight, undefined per-pixel/
// per-frame winner, which is exactly what reads as "dashed / broken /
// noisy" borders (confirmed visually: internal borders between two
// untouched-land neighbours, the majority case, were the most affected).
//
// FIX: nudge every polygon's altitude by a tiny, DETERMINISTIC (hashed from
// the feature's own ISO code — never random, never per-frame, so the same
// pair of neighbours resolves the same way on every render) amount. Chosen
// far smaller than the smallest real semantic altitude step
// (INACTIVE_POLYGON_ALTITUDE = 0.002; this jitter tops out at 2e-5, two
// orders of magnitude below) so the CAP/fill is visually unaffected, but
// the same order of magnitude as three-globe's own proven stroke-offset
// constant (1e-4) — large enough to reliably separate two coincident lines
// in the depth buffer. No architecture change, no dataset change, no new
// dependency — a one-line addition to the existing altitude accessor.
function altitudeJitter(iso) {
  let h = 0;
  for (let i = 0; i < (iso || "").length; i++) h = (h * 31 + iso.charCodeAt(i)) | 0;
  return (((h >>> 0) % 1000) / 1000) * 4e-5 - 2e-5; // deterministic, in [-2e-5, +2e-5)
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

// ── Procedural ocean surface variation (Phase 3A final correction) ─────
// A real image asset was deliberately avoided — the authorization prefers a
// procedural implementation if it can reach the target safely, and this
// follows the exact same self-contained, no-network-fetch pattern already
// used for the studio environment and the canvas backdrop above (both
// generated to a <canvas> at mount time, nothing shipped or cached).
//
// Applied as `bumpMap` ONLY, not `roughnessMap`. A roughnessMap multiplies
// material.roughness by the texture's green channel; this texture is
// centered on mid-gray (~0.5), so using it as a roughnessMap would roughly
// HALVE the ocean's average roughness — a global material change disguised
// as "adding texture," not the subtle local variation asked for. A perturbed
// NORMAL field (bumpMap) already gives the two things the brief actually
// asked for — "fine roughness variation" reads as broken-up specular, and a
// perturbed normal breaks up reflections exactly that way — without
// double-counting the roughness value the ocean material already declares.
//
// Horizontal seam: the globe body's SphereGeometry UV wraps in U
// (longitude), so every blob drawn near a horizontal edge is ALSO drawn at
// its wrapped position on the opposite edge — a cheap toroidal technique
// that keeps the antimeridian seam from showing, without needing true
// seamless noise math. Vertical (pole) seams are not addressed: poles are
// heavily distorted in any equirectangular mapping regardless, and are never
// a primary viewing angle for a production Globe.
//
// Deterministic PRNG (not Math.random): the Globe's appearance must not
// re-randomize on every mount/reload — same rule the rest of this file
// already follows for every other constant.
function makeOceanSurfaceTexture() {
  const w = 1024, h = 512;
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const ctx = c.getContext("2d");
  // Neutral mid-gray: a bumpMap reads this as "no perturbation" — only
  // deviation from this value raises or lowers the surface.
  ctx.fillStyle = "#808080";
  ctx.fillRect(0, 0, w, h);

  let seed = 1337;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const drawBlob = (x, y, r, delta) => {
    const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
    const mid = Math.round(128 + delta);
    grad.addColorStop(0, `rgba(${mid},${mid},${mid},0.5)`);
    grad.addColorStop(1, "rgba(128,128,128,0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  };
  // Two octaves — broad, faint low-frequency swells plus fine, faint
  // high-frequency grain — is what reads as "depth," rather than one
  // uniform grain size which reads as a flat repeating pattern.
  // PHASE 3A FINAL RECONCILIATION: added a third, finer octave — the two
  // original octaves gave "depth" but the finest detail (240px "reflection
  // breakup" grain the approved render shows in its specular region) was
  // still one size larger than it needed to be. Same deterministic PRNG,
  // same toroidal wrap; only a third scale added, not a new technique.
  const OCTAVES = [
    { count: 90, rMin: 60, rMax: 140, deltaMax: 14 },
    { count: 260, rMin: 8, rMax: 24, deltaMax: 22 },
    { count: 420, rMin: 3, rMax: 9, deltaMax: 26 },
  ];
  for (const { count, rMin, rMax, deltaMax } of OCTAVES) {
    for (let i = 0; i < count; i++) {
      const x = rand() * w;
      const y = rand() * h;
      const r = rMin + rand() * (rMax - rMin);
      const delta = (rand() * 2 - 1) * deltaMax;
      drawBlob(x, y, r, delta);
      if (x < rMax) drawBlob(x + w, y, r, delta);
      if (x > w - rMax) drawBlob(x - w, y, r, delta);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
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
  // PHASE 3B BATCH 2 (objective 5): additional jurisdictions to illuminate
  // alongside `hoveredIso` — used when hovering a Co-Production Opportunity
  // to light up its real related jurisdictions (structure.participants,
  // resolved to globe keys by the caller). `primaryIlluminatedIso`, if one
  // of these, reads slightly stronger — real data (structure.primary_
  // jurisdiction), never an invented preference. Both no-ops when absent,
  // so every non-amber hover is completely unaffected by this prop existing.
  illuminatedIsos = null,
  primaryIlluminatedIso = null,
  // PHASE 3B BATCH 2 (objective 6): jurisdictions currently in their one-
  // time "unlock pulse" window (caller owns the timing — see ProjectGlobe.jsx
  // categoryByIso diff effect). A brief, non-looping brighten distinct from
  // hover/illumination; the caller is responsible for clearing it (setting
  // this back to null) after its own timeout, this component never loops
  // or re-triggers it on its own.
  pulsingIsos = null,
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
  const liveRef = useRef({ polygonColors: null, selectedIso: null, hoveredIso: null, illuminatedIsos: null, primaryIlluminatedIso: null, pulsingIsos: null, pointRadius: null, geoIsoSet: null, strokeColor: null, landColor: null });
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
    // PHASE 3A FINAL RECONCILIATION: 0.34 was silently CLIPPING — three.js's
    // PMREMGenerator caps the top mip's blur at 20 samples, and 0.34 radians
    // requests ~166 (verified against the installed source's own MAX_SAMPLES
    // constant and its `samples = 1 + floor(3 * sigmaRadians / (pi/(2*pixels)))`
    // formula: solving for the top LOD's pixel count puts the clip-free
    // ceiling at ~0.041). The console has been warning on every mount, in
    // every theme, in production, since this was written — never a design
    // choice, a bug. This also directly serves objective 5 (reflection
    // shape): a clipped blur is truncated, not soft, which is part of why the
    // studio panels printed as a harder-edged spot than the "soft directional
    // gradient" this file's own comment says it wants. Below this threshold
    // the finer per-roughness mip chain (below) supplies the actual softness
    // each material samples from — see each MeshPhysicalMaterial's roughness/
    // clearcoatRoughness, not this single scene-level pre-blur.
    const envRT = pmrem.fromScene(envScene, 0.035);
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
    // PHASE 3A FINAL CORRECTION: ambient is UNTOUCHED (protected — "ambient
    // must not dominate the key" is what stops the sphere reading as a flat
    // lit billiard ball; every previous failure in this file that tried to
    // brighten by raising ambient produced exactly that). The fix for "reads
    // like a flat circular map, not a sphere" is a WIDER key:fill ratio, not
    // more ambient — a sharper terminator is what makes a sphere read as a
    // sphere in a single static frame, which is the explicit acceptance bar
    // here (a screenshot, not an animation).
    scene.add(new THREE.AmbientLight(0xffffff, 0.10));
    // Key RAISED 0.30 -> 0.38, fill LOWERED 0.20 -> 0.15: the terminator gap
    // (key minus fill) goes from 0.10 to 0.23, more than doubled, without
    // touching total scene brightness in any global sense — this is a
    // REDISTRIBUTION toward contrast, not an increase in overall exposure,
    // which is exactly what was asked for ("do not solve this by increasing
    // global brightness alone"). The environment still provides exposure;
    // the key now does more of the "which way is the light coming from" work.
    const key = new THREE.DirectionalLight(0xffffff, 0.38);
    key.position.set(200, 120, 200);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0x8890a0, 0.15);
    fill.position.set(-200, -80, -150);
    scene.add(fill);
    // Back/rim gives the sphere mass by separating its dark limb from the
    // dark backdrop. Raised slightly (0.40 -> 0.46, production only) to pair
    // with the tightened Fresnel falloff below — a stronger rim behind a
    // tighter falloff reads as a crisp curvature edge rather than a wash.
    const rim = new THREE.DirectionalLight(0xaeb6c2, isBrand ? 0.24 : 0.46);
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
      if (hovered) return brightenHex(base, 0.30);
      // PHASE 3B BATCH 2 (objective 5): Co-Production Opportunity hover
      // illuminates its real related jurisdictions too — the SAME hue
      // brighten technique as ordinary hover, at two restrained, distinct
      // strengths so the category colour is always preserved (never a
      // generic white/washed highlight) and the illuminated set never reads
      // as identical to a direct hover. The primary jurisdiction (real
      // `structure.primary_jurisdiction`, never invented) reads slightly
      // stronger than the rest of the related set.
      const illuminated = !!iso && liveRef.current.illuminatedIsos?.has(iso);
      if (illuminated) {
        const isPrimary = iso === liveRef.current.primaryIlluminatedIso;
        return brightenHex(base, isPrimary ? 0.22 : 0.14);
      }
      // PHASE 3B BATCH 2 (objective 6): category-transition unlock pulse —
      // deliberately the STRONGEST of the three brighten tiers (hover 0.30,
      // illumination 0.14-0.22, pulse 0.45) so a genuine "this just became
      // available" moment reads as more emphatic than a passive hover, while
      // still preserving the jurisdiction's own hue (same brightenHex
      // mechanism, no new colour). One-shot: the caller (ProjectGlobe.jsx)
      // owns the timer and clears `pulsingIsos` itself; this accessor has no
      // concept of "playing" or "looping", it only reads whatever is
      // currently in liveRef at paint time.
      if (iso && liveRef.current.pulsingIsos?.has(iso)) return brightenHex(base, 0.45);
      return base;
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
      // PHASE 3B BATCH 2 (objective 5): illuminated related jurisdictions
      // get the same border emphasis as a direct hover — a brightened fill
      // with no border change reads as a colour glitch, not a highlighted
      // country.
      if (iso && liveRef.current.illuminatedIsos?.has(iso)) return HOVER_STROKE;
      // PHASE 3B BATCH 2 (objective 6): pulsing jurisdictions get the gold
      // stroke — the Globe's existing "look here" border, reused rather than
      // inventing a new accent colour for a one-shot event.
      if (iso && liveRef.current.pulsingIsos?.has(iso)) return GOLD_STROKE;
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
      const jitter = altitudeJitter(iso);
      if (liveRef.current.selectedIso && iso === liveRef.current.selectedIso) return SELECTED_POLYGON_ALTITUDE + jitter;
      const colors = liveRef.current.polygonColors;
      const hex = colors?.get ? colors.get(iso) : colors?.[iso];
      if (!hex) return INACTIVE_POLYGON_ALTITUDE + jitter;
      if (hex === TIER_HEX.gold) return GOLD_BASELINE_POLYGON_ALTITUDE + jitter;
      return PARTICIPATING_POLYGON_ALTITUDE + jitter;
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
    // ── Restrained per-tier material hierarchy (Phase 3A, step 2) ─────────
    // Three tiers, not four — this is the explicit correction to the original
    // reconciliation plan's per-state table. Optimized alternative and
    // Unlockable opportunity share ONE recipe (`enamel`) and differ ONLY by
    // hue, exactly as the authorization specifies ("same material family as
    // Optimized. Different semantic colour only") — material must never be
    // allowed to overpower what the COLOUR already means. Recommended gets a
    // visibly finer finish (`jewel`) because it is the one state that should
    // draw the eye before any click. Additional (`quiet`) sits much closer to
    // untouched land than to the enamel tier — "close to neutral land, still
    // visibly promoted" — a small clearcoat and roughness step is the whole
    // difference, not a second colour language.
    //
    // Values are anchored at the two tiers already runtime-verified in step 1
    // (`land` = the retuned neutral-land recipe; `enamel` = the untouched
    // pre-3A active-state recipe, which was already correct and is NOT
    // changed here). `quiet` and `jewel` are the only new tiers.
    // PHASE 3A FINAL RECONCILIATION: land/quiet envBase raised slightly
    // (0.30->0.34, 0.36->0.40) and land roughness eased (0.62->0.58) — a
    // small step toward more curvature response on untouched land and
    // Baseline (item 3), stopping well short of the enamel tier so the
    // hierarchy (land < Baseline < enamel < jewel) is unchanged, only richer
    // at each step.
    const CAP_MATERIAL_RECIPES = {
      // PHASE 3A FINAL MICRO-PASS: roughness eased once more (0.58 -> 0.52),
      // envBase raised (0.34 -> 0.38). This is a CURVATURE lever, not a noise
      // lever — lower roughness lets the environment's own gradient vary more
      // by each polygon's surface normal, so a large country visibly follows
      // the sphere from lit to shadowed edge in a static frame, without
      // touching the grain shader's amplitude (already at its ceiling — see
      // applyLandGrainShader — and explicitly not to look like visible noise).
      // PHASE 3A FINAL VISUAL CORRECTION: roughness eased again (0.52 -> 0.47)
      // and envBase raised again (0.38 -> 0.42) — a third increment on the
      // same curvature lever (lower roughness lets the environment gradient
      // vary more by each polygon's surface normal), not a new mechanism.
      land: { roughness: 0.47, clearcoat: 0.12, clearcoatRoughness: 0.65, emissiveIntensity: 0.19, envBase: 0.42 },
      // Additional: roughness/clearcoat sit roughly a third of the way from
      // land toward enamel — enough that hovering/selecting it still reads
      // as "a real thing," not so much that it competes with Optimized or
      // Unlockable for attention.
      quiet: { roughness: 0.43, clearcoat: 0.30, clearcoatRoughness: 0.45, emissiveIntensity: 0.16, envBase: 0.48 },
      // Optimized alternative + Unlockable opportunity, unchanged from the
      // pre-3A "active status" recipe — proven, already reads as premium
      // satin/enamel, and step 1's runtime check confirmed it still holds
      // its place in the hierarchy against the retuned land/ocean.
      enamel: { roughness: 0.30, clearcoat: 1.0, clearcoatRoughness: 0.14, emissiveIntensity: 0.17, envBase: 0.50 },
      // Recommended only. Modest step beyond enamel (lower roughness, tighter
      // clearcoat, a touch more emissive) — restrained, not a different
      // material language: still the same dielectric family, just the finest
      // finish in it.
      jewel: { roughness: 0.22, clearcoat: 1.0, clearcoatRoughness: 0.10, emissiveIntensity: 0.20, envBase: 0.55 },
    };
    // Maps a jurisdiction's CANONICAL (undimmed, unbrightened) semantic hex to
    // its tier. Built from STATUS_HEX rather than hardcoded strings so it can
    // never drift from globeData.js's semantic table. Deliberately keyed on
    // the RAW hex from `polygonColors` (see `activeHex` below), not on the
    // hover/selection-modified colour capColorFn returns — dimming and
    // brightening produce a effectively unbounded number of derived hex
    // strings, and the material TIER must depend only on which of the four
    // canonical states a jurisdiction actually has, never on its momentary
    // on-screen shade.
    const MATERIAL_TIER_BY_HEX = {
      [STATUS_HEX.gold]: "jewel",
      [STATUS_HEX.jade]: "enamel",
      [STATUS_HEX.amber]: "enamel",
      [STATUS_HEX.silver]: "quiet",
    };
    const capMaterialCache = new Map();
    const getCapMaterial = (hex, tier) => {
      const recipe = CAP_MATERIAL_RECIPES[tier] || CAP_MATERIAL_RECIPES.land;
      const cacheKey = `${hex}|${tier}`;
      let m = capMaterialCache.get(cacheKey);
      if (!m) {
        m = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color(hex),
          metalness: 0.0, // dielectric: glass/enamel, never metal
          roughness: recipe.roughness,
          clearcoat: recipe.clearcoat,
          clearcoatRoughness: recipe.clearcoatRoughness,
          ior: 1.5,
          side: THREE.DoubleSide,
          depthWrite: true,
          // GUARANTEED FLOOR so no landmass can collapse to black. Emissive is
          // additive and lighting-independent — exactly the mechanism the ocean
          // body already uses to stop the water reading as a hole on the unlit
          // hemisphere. Keyed to the cap's OWN colour, so the ladder survives
          // into shadow instead of flattening to a single grey.
          emissive: new THREE.Color(hex),
          emissiveIntensity: recipe.emissiveIntensity,
        });
        applyCapEnvScale(m, recipe.envBase);
        // See applyLandGrainShader's own comment: UV-independent surface
        // variation, applied to every tier (including untouched land) so a
        // large country reads as more than one flat fill without altering
        // the semantic colour hierarchy.
        applyLandGrainShader(m);
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
    const capMaterialFn = (feat) => {
      const raw = activeHex(feat);
      const tier = raw ? MATERIAL_TIER_BY_HEX[raw] || "enamel" : "land";
      return getCapMaterial(capColorFn(feat), tier);
    };
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
      // PHASE 3B BATCH 2 (objective 5/6): beacon-rendered jurisdictions
      // (islands/city-states too small for the polygon layer — Mauritius,
      // Malta, Singapore) never went through capColorFn's illumination/pulse
      // branches at all, since they render via this entirely separate point
      // path. Mauritius specifically is the anchor participant of nearly
      // every Co-Production Opportunity in this production, so without this
      // the single most common "related jurisdiction" would silently never
      // illuminate. Same brightenHex tiers as the polygon path, same source
      // of truth (liveRef.current.illuminatedIsos/pulsingIsos) — not a
      // second colour system.
      if (d.iso && liveRef.current.pulsingIsos?.has(d.iso)) return brightenHex(hex, 0.45);
      if (d.iso && liveRef.current.illuminatedIsos?.has(d.iso)) {
        const isPrimary = d.iso === liveRef.current.primaryIlluminatedIso;
        return brightenHex(hex, isPrimary ? 0.22 : 0.14);
      }
      return hex;
    };

    const globe = new ThreeGlobe()
      .showGlobe(true)
      // PHASE 3A: RE-ENABLED. The prior comment here claimed a z-fight
      // between the atmosphere shell and the globe body at "geometry radius
      // 100, scale 1.0 — exactly coincident." That claim does NOT match the
      // installed three-globe 2.45.2 source: `atmosphereAltitude` defaults to
      // 0.15, and its glow geometry is the globe's own sphere extruded
      // outward along vertex normals by `GLOBE_RADIUS * atmosphereAltitude`
      // (= 15 units) — i.e. built at radius ~115, not coincident with the
      // radius-100 body. Re-verified live at multiple camera angles in both
      // themes for this batch with no z-fight reproducing; the old comment
      // most likely described either a stale prior configuration (altitude
      // left at 0 at some point, which WOULD coincide) or a misdiagnosis.
      // Kept deliberately restrained (see ATMOSPHERE_ALTITUDE) — a limb glow,
      // not a halo — and the fresnel shell stays alongside it rather than
      // being replaced: the shell defines the hard glass edge, the
      // atmosphere adds the soft luminous falloff beyond it. If a z-fight is
      // ever found to genuinely reproduce (different GPU/driver, a future
      // three-globe version), the documented fallback is to revert this one
      // line to `false` and instead raise BASE_RIM_INTENSITY on the fresnel
      // shell — do not remove the atmosphere and leave the limb bare.
      .showAtmosphere(true)
      .atmosphereAltitude(ATMOSPHERE_ALTITUDE)
      .atmosphereColor(globeTheme().atmosphere)
      // PHASE 3A FINAL CORRECTION: graticule REMOVED, not restyled. It was
      // enabled with library defaults in the previous pass and read fine in
      // isolation, but against the approved render it was explicit rejected
      // feedback — a lat/long grid reads as cartographic/technical/flat, the
      // opposite of the "premium instrument" character every other change in
      // this batch is working toward. Country and state/province boundaries
      // (polygonStrokeColor below) are the only line-work the Globe carries.
      // Do not re-enable this, in any opacity, without the user explicitly
      // asking for a grid specifically.
      .showGraticules(false)
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
          // PHASE 3A FINAL CLOSEOUT: the hover card now anchors near the
          // hovered jurisdiction instead of sitting fixed at the panel's
          // top-left, so a second argument — this hit-target's own
          // viewport-relative box (the same box the marker itself occupies
          // on screen) — is passed through. The caller converts it to a
          // position relative to its own canvas container; Globe3D has no
          // reason to know that container's identity.
          el.addEventListener("mouseenter", () => onPointHover(d, el.getBoundingClientRect()));
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
    // Generated once per mount, disposed on unmount alongside every other
    // procedural texture in this file (see the cleanup block below).
    const oceanSurfaceTexture = makeOceanSurfaceTexture();
    const material = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(OCEAN_BODY),
      metalness: 0.0, // dielectric — obsidian/glass, never metal
      // PHASE 3A FINAL VISUAL CORRECTION: added a compensated roughnessMap —
      // an earlier pass rejected this for the base `roughness` channel
      // because the texture's ~0.5 mean would have HALVED the average value
      // (see makeOceanSurfaceTexture's comment). Same fix as the
      // clearcoatRoughnessMap below: double the base first (0.38 -> 0.76) so
      // the sphere-average stays ~0.38, but low-frequency reflectivity now
      // genuinely varies per-pixel — this is the "low-frequency tonal
      // variation" the correction batch asked for, using the existing
      // texture, no new asset.
      roughness: 0.76,
      roughnessMap: oceanSurfaceTexture,
      clearcoat: 1.0,
      // PHASE 3A FINAL CORRECTION: restrained procedural surface variation —
      // see makeOceanSurfaceTexture's own comment for why this is bumpMap
      // only, not roughnessMap. bumpScale is deliberately tiny: at anything
      // above ~0.35 the perturbation reads as visible ripples, which the
      // brief explicitly prohibits ("do not add visible animated wave
      // crests, exaggerated distortion"). At this scale it only breaks the
      // clearcoat highlight's edge and adds faint tonal variation — enough
      // to read as "not a flat glossy tint" without reading as water text.
      bumpMap: oceanSurfaceTexture,
      // Raised 0.28 -> 0.32 -> 0.34 across two passes — still under the
      // ~0.35 "visible ripple" line this file documents as the hard ceiling.
      bumpScale: 0.34,
      // The coat is SATIN, not mirror. At 0.16 it behaved as a near-perfect
      // varnish and reflected the studio panels as two discrete white orbs
      // over the Pacific — sharp clearcoat reflects the environment crisply
      // no matter how rough the base layer underneath is, so this value, not
      // `roughness`, is what governs whether reflections read as lamps.
      //
      // PHASE 3A: nudged 0.34 -> 0.28, paired with the deepened ocean colour
      // and the raised envMapIntensity (now theme-driven, see GLOBE_THEME) —
      // together these are what give the ocean "dimensional reflection"
      // rather than a flat tint. A crisper coat alone, without the deeper
      // base colour, would have reproduced the old "two white orbs" failure;
      // it is safe here specifically because the base colour is darker and
      // more saturated than the original satin pass was tuned against.
      //
      // PHASE 3A FINAL RECONCILIATION: added clearcoatRoughnessMap, reusing
      // the same ocean texture instead of a second asset. A roughnessMap (or
      // clearcoatRoughnessMap) multiplies the base value by the texture's
      // green channel; this texture is centred at ~0.5, so the base value
      // below is DOUBLED (0.28 -> 0.56) to compensate — the resulting AVERAGE
      // clearcoat roughness across the sphere is unchanged (~0.28), but it
      // now genuinely varies per-pixel instead of being one flat scalar. This
      // is the correct version of an idea an earlier pass tried and abandoned
      // for the base `roughness` channel without this compensation (see
      // makeOceanSurfaceTexture's own comment) — same texture, same
      // technique, done with the mean bias accounted for this time.
      // PHASE 3A FINAL VISUAL CORRECTION: raised again, 0.56 -> 0.68 (average
      // effective clearcoat roughness ~0.28 -> ~0.34) — see the panel-tilt
      // comment above the studio-environment strip for why: clearcoat, not
      // panel shape, was what kept the reflection reading as a sharp isolated
      // spot regardless of how long/thin the source was made.
      clearcoatRoughnessMap: oceanSurfaceTexture,
      // PHASE 3B CLOSEOUT: 0.68 -> 0.58 (effective sphere-average clearcoat
      // roughness ~0.34 -> ~0.29) — a crisper specular streak, paired with
      // the raised envIntensity above, for visible surface dimensionality.
      // Still well short of the ~0.16 "two white orbs" failure this file
      // documents as the hard ceiling on the other end.
      clearcoatRoughness: 0.58,
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
            // reproducing. uPower raised 1.9 -> 2.4 -> 3.1 (PHASE 3A FINAL
            // CORRECTION): tightened further, paired with the raised
            // BASE_RIM_INTENSITY, so this shell reads as a crisp curvature
            // line right at the silhouette — the atmosphere (a separate,
            // wider shell) is what supplies the soft falloff beyond it now,
            // so this one no longer has to do both jobs at once.
            uColor: { value: new THREE.Color(GLOBE_THEME.day.rim) },
            uIntensity: { value: BASE_RIM_INTENSITY },
            // PHASE 3A FINAL RECONCILIATION: 3.1 -> 3.4, tightened in step
            // with the pulled-in atmosphere altitude above (item 4).
            uPower: { value: 3.4 },
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
        // 4. Ocean drift (Phase 3B Batch 2) — scrolls the SAME procedural
        //    bump/roughness/clearcoat-roughness texture's UV offset, rather
        //    than animating geometry or adding a shader. A single scalar
        //    write, shared by all three material channels because they all
        //    reference the one `oceanSurfaceTexture` object. Deliberately
        //    slow and horizontal-only (longitude direction, matching the
        //    texture's own toroidal wrap — see makeOceanSurfaceTexture) so
        //    it reads as "the water has depth" on close, deliberate
        //    observation without ever looking like a current or wave
        //    travelling in a visible direction. Never touches land: the
        //    land grain shader is a separate, static, object-space effect
        //    (applyLandGrainShader) with no texture and nothing to offset.
        oceanSurfaceTexture.offset.x = (elapsed * OCEAN_DRIFT_PER_SEC) % 1;
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
      // Atmosphere colour is theme-driven the same way rim colour is. Calling
      // .atmosphereColor() re-triggers three-globe's own atmosphere rebuild
      // (see its `update()` — recreates the GlowMesh whenever colour or
      // altitude changes); altitude is left untouched so this is a cheap,
      // infrequent (theme-toggle-only) rebuild, not a per-frame cost.
      if (globeRef.current) globeRef.current.atmosphereColor(t.atmosphere);
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
      oceanSurfaceTexture.dispose();
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
  // PHASE 3B BATCH 2: also reacts to `illuminatedIsos`/`primaryIlluminatedIso`
  // (objective 5, Co-Production Opportunity hover illumination) — same
  // repaint mechanism, no new effect needed. The caller (ProjectGlobe.jsx)
  // memoizes the array so this only actually re-fires on a real hover
  // change, not on every render.
  const illuminatedKey = illuminatedIsos && illuminatedIsos.length ? illuminatedIsos.join(",") : "";
  useEffect(() => {
    const illuminatedSet = illuminatedIsos && illuminatedIsos.length ? new Set(illuminatedIsos) : null;
    if (
      liveRef.current.hoveredIso === hoveredIso
      && liveRef.current.primaryIlluminatedIso === primaryIlluminatedIso
      && illuminatedKey === (liveRef.current.illuminatedIsos ? [...liveRef.current.illuminatedIsos].join(",") : "")
    ) return;
    liveRef.current.hoveredIso = hoveredIso;
    liveRef.current.illuminatedIsos = illuminatedSet;
    liveRef.current.primaryIlluminatedIso = primaryIlluminatedIso;
    const globe = globeRef.current;
    if (!globe) return;
    globe
      .polygonCapColor(globe.polygonCapColor())
      .polygonSideColor(globe.polygonSideColor())
      .polygonCapMaterial(globe.polygonCapMaterial())
      .polygonSideMaterial(globe.polygonSideMaterial())
      .polygonStrokeColor(globe.polygonStrokeColor())
      // PHASE 3B BATCH 2: also re-invoke pointColor — illumination must reach
      // beacon-rendered jurisdictions (Mauritius, Malta, Singapore), which
      // render via the point layer, not the polygon layer, and were
      // otherwise silently skipped by this repaint (caught in runtime
      // verification: Mauritius, the most common related jurisdiction in
      // this production's data, never lit up until this was added).
      .pointColor(globe.pointColor());
  }, [hoveredIso, illuminatedKey, primaryIlluminatedIso]);

  // PHASE 3B BATCH 2 (objective 6): category-transition unlock pulse repaint
  // — a separate effect from hover on purpose, same reasoning as hover being
  // separate from selection: pulse timing is owned entirely by the caller
  // (ProjectGlobe.jsx's own timeout), so this must not get tangled with
  // pointer-driven hover repaints or re-run anything beyond the same four
  // accessors hover already re-invokes.
  const pulsingKey = pulsingIsos && pulsingIsos.length ? pulsingIsos.join(",") : "";
  useEffect(() => {
    const pulsingSet = pulsingIsos && pulsingIsos.length ? new Set(pulsingIsos) : null;
    liveRef.current.pulsingIsos = pulsingSet;
    const globe = globeRef.current;
    if (!globe) return;
    globe
      .polygonCapColor(globe.polygonCapColor())
      .polygonSideColor(globe.polygonSideColor())
      .polygonCapMaterial(globe.polygonCapMaterial())
      .polygonSideMaterial(globe.polygonSideMaterial())
      .polygonStrokeColor(globe.polygonStrokeColor())
      .pointColor(globe.pointColor());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pulsingKey]);

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
