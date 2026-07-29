# Globe Freeze Manifest

**Frozen:** 2026-07-28
- `globe: recover finalize and freeze globe rendering` — recovery + functional freeze
- `globe: premium glass rendering` — rendering architecture (tag `globe-glass-v1`)

The subsystems listed below are **immutable**. They may not be changed by any
future UI polish, theming, refactor, or "small tweak" pass. Changing any of
them requires the user to **explicitly unlock that exact subsystem by name**
first.

---

## Batch: Premium Glass Rendering — what it owns

This batch owns **only** the production Globe's rendering architecture. It
changed exactly one file (`Globe3D.jsx`) and touched no logic: no optimizer,
routing, selection, Inspector, AppState, ranking, camera or event handling,
and no change to `CompactSidebarGlobe.jsx` or to the status palette in
`globeData.js`.

**Owned and frozen by this batch:**

| Element | Value / approach |
|---|---|
| Lighting model | Image-based (PMREM studio environment) + minimal directional key |
| Environment | Procedural studio scene, `buildStudioEnvironment()`, blurred at sigma 0.34 |
| Globe body material | `MeshPhysicalMaterial`, clearcoat 1.0 / clearcoatRoughness 0.34 |
| Polygon cap materials | `MeshPhysicalMaterial`; frosted vs glossy is a **roughness** difference |
| Tone mapping | `ACESFilmicToneMapping`, exposure 0.95 |
| Post chain | `EffectComposer`: Render → UnrealBloom (0.09 / 0.5 / 0.93) → OutputPass |
| Fresnel rim shell | Retained, cut to 0.16 base / 0.26 selected |

### Why this architecture (do not "simplify" it back)

The Globe previously used Blinn-Phong lit by one directional key and a flat
ambient, with no environment map and no tone mapping. That is a hard ceiling,
not a tuning problem: a dielectric (obsidian, optical glass) derives almost
all of its character from **what it reflects**, and with no environment the
only specular cue available is a single analytic lobe — one dot on an
otherwise flat ball. Reverting to Phong, or removing `scene.environment`,
returns the Globe to looking painted no matter how the parameters are set.

### Non-obvious constraints learned by rendering and looking (all cost a cycle)

1. **`clearcoatRoughness`, not `roughness`, governs whether reflections read
   as lamps.** A sharp clearcoat mirrors the environment crisply however
   rough the base layer beneath it is. At 0.16 it printed two discrete white
   orbs over the Pacific; 0.34 turns them into a soft wash.
2. **Environment panels must be large and dim, not small and bright.** A big
   soft source wraps the curve; a small bright one prints a disc on it.
3. **Blur sigma is the difference between "reflects a studio" and "mirrors a
   lamp."** 0.04 produced a blown-white disc on the limb; 0.34 does not.
4. **Ambient must stay near zero once IBL is present.** Ambient adds a
   constant to every pixel regardless of orientation, which averages out the
   very reflections that make a surface read as glass.
5. **A directional key and an IBL both contribute specular.** Holding the old
   key strength alongside the new environment stacked into a hotspot.
6. **The Fresnel shell is now largely redundant** — the environment defines
   the limb by itself; the two stacked into a white point until the shell was
   cut to 0.16.
7. **Exposure must come DOWN when adding IBL**, not stay flat, or the
   graphite land washes toward white.

### Verified at runtime, this batch

Default view, Africa (ZA), Mediterranean (MT), North America (US-CA), Indian
Ocean (MU), and Optimizer Overlay with a real multi-jurisdiction structure —
consistent material, no blown highlight, no halo, no muddy cast, continents
readable at every angle. Regression: routing arcs, optimizer overlay,
selection, Inspector sync, compact globe, clean console, build and lint all
pass.

**Performance note (honest):** frame rate could not be measured in the test
harness — the browser pane throttles `requestAnimationFrame` when it is not
compositing (8 frames in 55 s), so any FPS number from here would be
fabricated. Structural cost added is one one-time PMREM bake at mount plus a
mip-chain bloom pass per frame at panel resolution.

## Frozen subsystems

| Subsystem | Owner file |
|---|---|
| Production Globe material system (ocean body, polygon cap/side materials) | `frontend/src/components/Globe3D.jsx` |
| Production Globe lighting rig (ambient / key / fill / rim) | `frontend/src/components/Globe3D.jsx` |
| Ocean treatment (diffuse + emissive floor + specular) | `frontend/src/components/Globe3D.jsx` |
| Inactive-land treatment (frosted graphite, lit caps) | `frontend/src/components/Globe3D.jsx` |
| Status base colours (canonical palette) | `frontend/src/lib/globeData.js` (`STATUS_HEX`, `GRAPHITE_HEX`) |
| Admin-1 geometry composition (US states / CA provinces) | `frontend/src/components/Globe3D.jsx` (`loadWorldGeo`) |
| Selection behaviour + one-click A→B transfer | `Globe3D.jsx` + `ProjectGlobe.jsx` |
| Inspector-aware camera auto-fit (`setViewOffset` lens shift) | `frontend/src/components/Globe3D.jsx` |
| Candidate Jurisdiction ↔ Globe synchronisation | `frontend/src/screens/production/ProjectGlobe.jsx` |
| Optimizer route (arc) rendering | `Globe3D.jsx` + `globeData.js` |
| Beacon fallback for island / city-state jurisdictions | `frontend/src/components/Globe3D.jsx` |
| Compact brand Globe (isolated engine) | `frontend/src/components/CompactSidebarGlobe.jsx` |

## Canonical colour source

`frontend/src/lib/globeData.js` is the **single** source for Globe status
colours. `STATUS_HEX` (gold / jade / amber / silver / darkRed) and
`GRAPHITE_HEX` (not-evaluated) are imported by `Globe3D.jsx` and
`GlobeLegend.jsx`. **Do not re-declare these values anywhere else** — both
files previously kept hand-synced duplicates and they drifted.

## Non-obvious constraints (do not "fix" these)

1. **Lights must stay neutral white.** Tinting the light rig was the root
   cause of the muddy-brown Globe: Phong multiplies material × light per
   channel, so any tint contaminates every surface and no material-hex edit
   can undo it. Warmth belongs to the status colours, never the illumination.
2. **Ambient must dominate the key.** A key-dominant rig concentrates a
   bright sub-solar hotspot that swallows geography.
3. **A dark ambient *colour* caps the ambient term** regardless of intensity —
   use white and change intensity instead.
4. **Intensities are set empirically from the render,** not calculated:
   three.js colour management converts sRGB hexes to linear before lighting.
5. **The CSS vignette is painted over the WebGL canvas** and must stay subtle
   and neutral; it previously re-imposed a warm cast on correct pixels.
6. **Inactive land caps must keep a lit material.** Returning `null` makes
   three-globe fall back to unlit `MeshBasicMaterial` — that is what made
   land look flat and undimensional.

## Optimizer arcs — verified working (correcting an earlier false negative)

`arcs.length === 0` is **correct behaviour**, not a defect, whenever the
leading structure is single-jurisdiction: `buildGlobeView` draws arcs for
treaty structures **plus the currently active/leading structure**, and this
production's default leading structure is the Mauritius single-jurisdiction
baseline, which has one participant. The Globe truthfully reports "No
multi-jurisdiction structure is currently priced."

Set a real multi-jurisdiction structure as leading and arcs render
immediately — verified live with "Mauritius + Saudi Arabia" (a genuine
`component_relocation` carrying **no** `treaty_slug`, i.e. exactly the
non-treaty case that must not be suppressed): the caption flips to "Dashed
routes mark this production's real multi-jurisdiction structures", a
directed origin-hue→destination-hue arc renders from the gold Mauritius
beacon to jade-highlighted Saudi Arabia, unrelated jurisdictions recede to
neutral, and the dash pattern advances between successive frames.

**Testing note that cost a full verification cycle:** `leadingStructureId`
lives in in-memory AppState with no persistence. Any *full page load* resets
it to the API default. To test a non-default leading structure you must use
**in-app SPA navigation** (click the router `<a>`), never a browser
navigation — otherwise you are unknowingly testing the default single-
jurisdiction structure and will wrongly conclude arcs are broken.
