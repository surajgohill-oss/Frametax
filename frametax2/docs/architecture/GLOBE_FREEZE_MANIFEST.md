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

## Known non-frozen issue

`arcs.length === 0` for this production's component-relocation structures, so
Optimizer Overlay truthfully renders no route. This **predates** the freeze
(visible in the pre-change baseline as "0 structure routes") and lives in the
locked optimizer/structure-eligibility logic, so it was deliberately not
touched during the rendering pass. It needs its own scoped task.
