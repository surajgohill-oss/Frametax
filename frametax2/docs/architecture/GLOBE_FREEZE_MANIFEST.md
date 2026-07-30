# Globe Freeze Manifest

**Frozen:** 2026-07-28
- `globe: recover finalize and freeze globe rendering` — recovery + functional freeze
- `globe: premium glass rendering` — rendering architecture (tag `globe-glass-v1`)
- `globe: day/night theme + night visual system` (tag `globe-night-v1`)

**Frozen:** 2026-07-29 — **Phase 2 closeout, tag `globe-phase2-freeze`**
- `globe: phase 2 closeout — semantic system, ambient behaviour, hover, freeze`
- This is the **canonical Globe implementation**. Phase 3 is UX/polish only;
  see the closeout batch's explicit "may not" list at the end of this file.

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
| Semantic state colours (canonical palette) | `frontend/src/lib/globeData.js` (`GLOBE_SEMANTIC`, `GRAPHITE_HEX`) |
| Admin-1 geometry composition (US states / CA provinces) | `frontend/src/components/Globe3D.jsx` (`loadWorldGeo`) |
| Selection behaviour + one-click A→B transfer | `Globe3D.jsx` + `ProjectGlobe.jsx` |
| Inspector-aware camera auto-fit (`setViewOffset` lens shift) | `frontend/src/components/Globe3D.jsx` |
| Structure card ↔ Globe synchronisation | `frontend/src/screens/production/ProjectGlobe.jsx` |
| Optimizer route (arc) rendering | `Globe3D.jsx` + `globeData.js` |
| Beacon fallback for island / city-state jurisdictions | `frontend/src/components/Globe3D.jsx` |
| Compact brand Globe (isolated engine) | `frontend/src/components/CompactSidebarGlobe.jsx` |

## Canonical colour source

`frontend/src/lib/globeData.js` is the **single** source for Globe semantic
colours. `GLOBE_SEMANTIC` (the four states) plus `GRAPHITE_HEX` (untouched
landmass) are imported by `Globe3D.jsx`; `STATUS_HEX` / `STATUS_LABEL` /
`PULSE_TIERS` are **derived** from `GLOBE_SEMANTIC`, never hand-maintained.
**Do not re-declare these values anywhere else** — multiple files previously
kept hand-synced duplicates and they drifted.

Superseded by the Phase 2 closeout (2026-07-29): the five-value `STATUS_HEX`
(gold / jade / amber / silver / **darkRed**) is gone, and so is
`GlobeLegend.jsx` — see the closeout batch below.

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

---

## Batch: Day/Night Theme + Night Visual System (tag `globe-night-v1`)

**Owns:** the day/night control, the night semantic token layer, and the
Globe's night-mode palette response. Nothing else.

### Phase-1 finding: there was no theme system to restore

The header control shipped `disabled`, titled *"Theme — no dark token set
exists in this app yet"*. No theme state existed in `state/`. `tokens.css`
scoped its `--dark-*` block to "globe canvases and their immediate chrome
ONLY. Never applied to the application shell or content screens." The failure
chain had **no broken link** — the control was an honest placeholder. This
batch built the missing owner on the existing token architecture rather than
as a parallel system.

### Architecture

| Concern | Implementation |
|---|---|
| State owner | `data-theme` attribute on `<html>` — `frontend/src/lib/theme.js` |
| Persistence | `localStorage` (device-level; **not** account-level, per brief) |
| Boot | `initTheme()` in `main.jsx` before first render — no day-palette flash |
| Application theming | `:root[data-theme="night"]` re-binds the **same** semantic token names |
| Globe response | `subscribeTheme()` → in-place material mutation, **no remount** |

**Why an attribute and not React state:** the design system is already CSS
custom properties, so one attribute re-resolves every token at once with no
re-render — and critically, the Globe's WebGL context and its PMREM bake are
never torn down. Verified at runtime: the canvas DOM node is identical before
and after a switch (`globeCanvasSameNode: true`), all 86 hit-targets survive.

### Night Globe palette (day values unchanged)

Ocean → midnight navy `#2b3956` with `#16243c` internal emissive; inactive
land → navy-slate `#4a5570`; borders softened to `#8290a8`; limb to cool
silver-blue; exposure +0.09; envMapIntensity 0.34 → 0.40. **The glass
architecture is untouched** — same PMREM IBL, MeshPhysical, clearcoat, ACES,
composer and bloom in both themes.

**Why land changed hue:** neutral grey land on a navy ocean shares no hue
family and is exactly what read as an "unfinished or missing asset". The
legend's graphite swatch tracks the same value so the key keeps describing
what is actually on screen.

### Verified at runtime
Day↔night in one click each way; icon and `aria-pressed` update; no reload
needed; theme survives SPA navigation and is deterministic on refresh; Globe
stays mounted and interactive through switches; selection, camera flight and
Inspector all work in night mode; console clean; build and lint pass.

### Not delivered by this batch (honest)
Jurisdictions are recoloured for night but are **not yet true translucent
mineral insets** — that needs a transmission/refraction pass on the polygon
caps, which is a material-architecture change and its own batch. The
atmospheric particulate field was likewise not implemented.

---

## Batch: Globe Phase 2 Closeout — semantic system, ambient behaviour, hover (tag `globe-phase2-freeze`)

**Frozen:** 2026-07-29. This is the **canonical Globe implementation that
future UI work builds around.** Phase 3 is Globe UX/polish only.

**Owns:** the Globe's semantic vocabulary, its pulse rules, the hover
response, ambient motion, the Globe↔Inspector division of labour, and the
day/night calibration single-sourcing. It did **not** touch page
architecture, Overview/Workspace/Hero layout, routing, the optimizer, or any
backend path.

### The four-state semantic system (do not add a fifth)

`GLOBE_SEMANTIC` in `globeData.js` is the canonical source. Exactly four
states, each describing **what a producer should do**, not what the database
knows:

| State | Slot key | Colour | Pulse |
|---|---|---|---|
| Recommended | `gold` | `#e8c273` | **yes** — the only pulsing state |
| Optimized alternative | `jade` | `#4bab7f` | no |
| Unlockable opportunity | `amber` | `#d99a34` | no |
| Additional | `silver` | `#a9b2c0` | no |

`STATUS_HEX`, `STATUS_LABEL` and `PULSE_TIERS` are all **derived** from it.

**Why the old model was wrong, not just differently worded.** It shipped five
database-state categories — "Qualified / viable", "Evaluated / not
applicable", "No known incentive". A producer cannot act on "evaluated". And
"No known incentive" asserted a verdict the backend had never reached: per
the discovery audit, 103 of 124 `rejected` records mean *no knowledge-base
entry exists for that jurisdiction*, not *checked and ineligible*. Painting
those as a conclusion turned the instrument into a coverage map.

**What happened to the fifth state.** `darkRed` is deleted outright.
Discovery-examined jurisdictions with no participating structure now fold
into **Additional**. The `has_capability_data` selectivity gate is
**retained** — the 103 no-knowledge-base records still stay off the Globe
entirely; only the 21 rejected on a real capability mismatch against this
production's own requirements reach Additional.

**Two colour corrections, both principled:** amber moved `#e0a83f` →
`#d99a34` (it sat too close to gold in hue *and* luminance, so "conditional"
competed with "recommended" — gold must stay the brightest thing on the
Globe); silver moved `#b0aca2` → `#a9b2c0` (the old value was a **warm
taupe**, the exact hue family this palette's neutral-light-rig rule
prohibits).

### Pulse is reserved for the recommendation

The ring predicate was `d.tier === "gold" || isSmallJurisdiction(d)`, which
pulsed **every** island/city-state regardless of state — so an Optimized
alternative in Malta and an Unlockable opportunity in Singapore both pulsed
and the Globe appeared to recommend three things at once. Beacon *geometry*
is the correct answer to "this landmass is too small to fill"; a pulse is
not, because a pulse means something.

**This predicate existed in TWO places** — the mount path and the
data-change path, the latter with its own hand-written copy. Fixing only one
would have been silently undone the moment a producer changed an input. Both
now read `PULSE_TIERS`.

### Ambient motion — alive, not animated

Four sub-percent oscillations, all gated on `prefers-reduced-motion`, each
one scalar write per frame (no geometry rebuild, no reallocation, no extra
draw call):

| Motion | Mechanism | Rate |
|---|---|---|
| Specular drift | `scene.environmentRotation.y` (three ≥ r163) | ~8.4 min/rev |
| Limb breathing | Fresnel shell `uIntensity` around its live base | 11 s, ±12% |
| Recommendation breath | gold beacon glow shell scale | 4.4 s, ±16% |
| Autorotation | `controls.autoRotate` | 0.16 (~9 px/s) |

**Autorotation yields, permanently.** It was previously gated on
`points.length <= 1` — i.e. it never ran on a real production Globe, which
sat perfectly inert. It now turns by default and stops on **any** selection
(a jurisdiction being read must hold still) and on the **first** user
drag/zoom (`controls` `'start'` event), after which the camera stays the
producer's for the life of the mount.

`THREE.Clock` is **deliberately not used** — it is deprecated in three 0.185
and warns on construction; this file must stay console-clean. Elapsed time
comes from `performance.now()`.

### Hover response

Hover = **slight brighten + border emphasis + Inspector preview**. Selection
= elevation + full-brightness fill + `SELECTED_STROKE` + camera flight. The
two must never be confusable, so hover deliberately does **not** lift a
polygon and is a no-op on the already-selected one.

**Why hover is instant while selection eases.** Verified in the installed
three-globe dist source: when a `polygonCapMaterial` override is present,
three-globe assigns that material directly and **skips** its own
shared-material colour mutation (`[!capMaterial && capColor]`). So a hover
brighten is a cached-material swap landing on the same frame — exactly what
hover needs — while `polygonAltitude`, which hover never touches, keeps its
500 ms selection easing. The material cache is keyed by resolved hex, so a
brightened country gets its own material rather than recolouring every
country in its state.

Hover lives in its **own effect**, separate from selection: it changes at
pointer speed and must not re-run the camera flight, the ring layer, or the
beacon update.

### Globe visualizes, Inspector explains

The persistent legend is **deleted** (`GlobeLegend.jsx` and all
`.globe-legend*` CSS). A Globe that needs a colour key to be read has not
been designed: states are learned by hovering one (which names it) and
opening one (which explains it).

The hover card carries **jurisdiction, semantic state, production role** and
nothing else. It previously also printed incentive and NPC — figures the
Inspector owns *with* their qualification trace, caps, rate ceiling and
citations. Two places showing the same number, one of them without
provenance, is worse than one. `incentiveUsd`/`npcUsd` remain in the hover
payload (real fields, used by the preview path) but no Globe surface may
render them.

The Workspace HUD stays: it is context about the *production* (name,
scenario count, route count), not an explanation of the instrument.

### Day/night calibration single-sourcing

`GLOBE_THEME` is now the **only** definition of either theme. Five day values
previously existed twice — once in `GLOBE_THEME.day` and once as a
module-level constant seeding the material/renderer before `applyTheme()`
first ran (`OCEAN_BODY`, `NEUTRAL_STROKE`, the rim shader's `uColor`,
`toneMappingExposure`, the ocean's `envMapIntensity`). Both copies happened
to agree, so nothing looked wrong — but "day and night are consistently
calibrated" cannot be verified by inspection while day is defined in two
places, and every material pass had to remember to edit both. All five are
now derived.

**Two genuine night-mode asymmetries found and fixed** (neither visible in
day mode, which is why they survived two previous material passes):

1. **`capEnvScale`** — only the globe *body*'s `envMapIntensity` was
   theme-driven. At night the ocean gained reflectivity while every landmass
   and semantic polygon stayed pinned at its day value, so the continents
   visibly flattened relative to the water they sit in. Cap/side materials
   now scale too (day `1.0` by definition — the day render is the frozen
   baseline and this consolidation must not alter a pixel of it; night
   `1.18`).
2. **`dimHex` blended toward the *day* graphite** (`#6e7681`) always. At
   night, selecting anything tinted the rest of the choropleth toward a
   colour that appears nowhere else in the night scene (night land is
   `#4a5570`). It now dims toward the live theme's land colour.

### Verified at runtime, this batch

Measured in **Playwright** (a genuinely visible page at 65 fps), because the
in-app browser pane throttles `requestAnimationFrame` when not compositing —
7 frames in 15.9 s, which makes continuous motion unobservable and produced
one false "autorotation is broken" reading before the cause was identified.
Discrete state changes verify fine in the pane; continuous motion does not.

| Check | Result |
|---|---|
| Semantic distribution across all 86 jurisdictions | **exactly 1** Recommended (Mauritius), 84 Optimized alternative, 1 Additional (Hungary) |
| Legacy states present | **zero** — no darkRed, no legacy wording, on any surface |
| Structure card colours | `#e8c273` / `#4bab7f` / `#d99a34` — new palette, no old amber |
| Legend nodes remaining | **0** on Project Globe and on Workspace Map |
| Hover card | "South Africa / Optimized alternative / Primary shoot" — **no money figures** |
| Hover surface response | fill visibly brighter + border emphasised; clears on mouseleave |
| Autorotation | 8 px / 1.5 s at rest → **0 px** after selection (yields correctly) |
| Selection | camera flight settles, others dim, Inspector opens with full trace |
| Optimizer Overlay | isolates the active structure: chain `["MU","CA-BC"]` for Mauritius + Vancouver, HUD "1 structure route", arc renders |
| Overlay toggle round trip | Jurisdictions 86 → Overlay 2 → Jurisdictions 86, no regression |
| Day/night | navy ocean, navy-slate land, states legible, borders softened, no remount |
| Responsive | viewport 760 px → canvas 688 CSS = 688 attr, all 86 hit-targets survive |
| Console | **0 errors** |
| Build | clean (2176 modules) |

### Not delivered / known open (honest)

- **`THREE.sigmaRadians, 0.34, is too large and will clip`** — pre-existing,
  cosmetic, and deliberately **not** changed here. The PMREM blur clips to 20
  samples, so the actual environment blur is a 20-sample approximation of the
  requested 0.34 rad. The frozen, verified appearance is built on that
  approximation; any sigma change alters the look, which is Phase 3's remit
  (optical quality), not a "final calibration only" pass.
- **`prefers-reduced-motion` is code-verified, not runtime-verified.** The
  gate is a single boolean read at mount feeding `ambientMotion` and
  `autoRotate`; the harness could not emulate the media query.
- **Unlockable opportunity does not appear at country level in this
  dataset** — and that is correct, not a gap. `STATUS_RANK` resolves a
  country to its highest state, so a jurisdiction with both a priced
  structure and a blocked one reads as Optimized alternative: the opportunity
  is not blocked if a viable path exists. It appears on structure cards.
- Jurisdictions are still not true translucent mineral insets (carried over
  from `globe-night-v1` — needs a transmission/refraction pass).

### Phase 3 may tune the constants in `Globe3D.jsx`. It may NOT:

1. reintroduce a fifth semantic state, or re-add a `darkRed`/`red` alias;
2. put a pulse on anything but the recommendation, in either the mount path
   or the data-change path;
3. re-add a persistent legend or `.globe-legend*` CSS;
4. render money figures in a Globe hover card;
5. re-add a module-level duplicate of any `GLOBE_THEME` value;
6. use `setTimeout`-free reasoning to justify `THREE.Clock` coming back.
