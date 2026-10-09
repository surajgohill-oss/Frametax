// Visual tokens shared by the full Globe (components/Globe3D.jsx) and the 80px sidebar globe (CompactSidebarGlobe.jsx), so the
// compact globe is the same product at a smaller scale: same near-black navy stage and bloom, same ocean, land and boundary
// colours, same limb and atmosphere. Moved verbatim out of Globe3D.jsx; edit values here only.
import { GRAPHITE_HEX } from "./globeData";

export const GLOBE_THEME = {
  day: {
    // DEEPENED + SATURATED from #3a4250 (a near-neutral slate that read as
    // flat/near-black once rendered). This is a real saturated deep blue —
    // the "luminous dimensional ocean" the approved render shows is carried
    // mostly by the emissive floor and the sharpened clearcoat highlight
    // below, but the base color itself now has to be a blue an eye would
    // call "ocean" even unlit, not a desaturated gray-blue.
    ocean: "#152a44",
    // Raised in step with the base color so the unlit hemisphere of the
    // ocean still reads as deep blue rather than collapsing toward black —
    // same guaranteed-floor role the land emissive floor plays below.
    oceanEmissive: "#0f1f33",
    land: GRAPHITE_HEX,
    stroke: "#9aa3b0",
    rim: "#b9c1cb",
    // PHASE 3A FINAL CORRECTION: deepened from the pale #8fc6ff, which read
    // as washed-out/whitish once the altitude tightened — a limb glow needs
    // enough of its own saturation to register as colour, not just as more
    // white. Still cool and still close in hue to `rim`, so the two read as
    // one coherent edge treatment rather than competing effects.
    atmosphere: "#6fb4ef",
    backdrop: ["#05080e", "#04070c", "#03050a"],
    bloom: "#143a58",
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
    // PHASE 3B FINAL VISUAL DELTA: 0.50 -> 0.58 — still read as too close to
    // flat at NORMAL zoom (not a crop) on the next runtime pass. Base colour/
    // hue still untouched.
    envIntensity: 0.58,
    // Multiplier on the polygon cap/side materials' own envMapIntensity.
    // Day is the identity by definition — the day render is the frozen,
    // verified baseline and this consolidation must not alter a pixel of it.
    capEnvScale: 1.0,
  },
  night: {
    // Deepened in step with day, keeping the same relative move (a more
    // saturated, less desaturated-gray navy). Still clearly darker than day's
    // ocean — night must stay night — but no longer reads as a flat void.
    ocean: "#0f1d33",
    // Faint internal blue illumination — the "lit from within" quality the
    // art direction calls for, and the guarantee the ocean never collapses.
    oceanEmissive: "#0b182c",
    // Neutral grey land on a navy ocean is precisely what reads as an
    // unfinished or missing asset — the two share no hue family. Night land
    // is a navy-slate: clearly lighter than the ocean, clearly darker than
    // any status colour, and unmistakably part of the same material world.
    //
    // PHASE 3A: hue moved from navy-slate (#586479) to a teal-leaning
    // navy-slate (#4f6870, luminance held ~97 vs the prior ~99), matching the
    // day-mode land's teal-slate move (GRAPHITE_HEX) so both themes carry the
    // same material character, not just the same luminance position.
    land: "#425a62",
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
    backdrop: ["#04070d", "#03060b", "#020409"],
    bloom: "#10324e",
    // Slightly hotter: the surrounding UI is far darker at night, so the
    // same exposure reads dimmer by simultaneous contrast. Raised in the
    // same proportion as day (1.04 -> 1.12).
    exposure: 1.12,
    // Raised in step with day (0.46 -> 0.50), same reasoning.
    // PHASE 3B CLOSEOUT: raised in step with day (0.50 -> 0.56).
    // PHASE 3B FINAL VISUAL DELTA: raised in step with day (0.56 -> 0.64).
    envIntensity: 0.64,
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
