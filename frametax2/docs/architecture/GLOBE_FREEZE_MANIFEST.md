# Globe Freeze Manifest

**Frozen:** 2026-07-28 · commit `globe: recover finalize and freeze globe rendering`

The subsystems listed below are **immutable**. They may not be changed by any
future UI polish, theming, refactor, or "small tweak" pass. Changing any of
them requires the user to **explicitly unlock that exact subsystem by name**
first.

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
