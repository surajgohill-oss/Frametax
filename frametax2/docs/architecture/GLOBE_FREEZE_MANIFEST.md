# Globe Freeze Manifest

**Frozen:** 2026-08-01 — **Phase 3B GLOBE CLOSEOUT, FINAL, tag `globe-phase3b-freeze`**
- Semantic motion (Co-Production hover illumination incl. beacon
  jurisdictions, category-transition unlock pulse), border z-fighting root
  cause + fix, ocean drift, vertical legend, and the final hover-contract
  rewrite (Program / Maximum Incentive / Modeled Incentive / NPC / Incentive
  per Gross Budget — full dollars, full country names, no misleading rate
  ranges). This is the canonical Globe implementation going forward; Phase 4
  (Overview/broader production UX) has not started. Optimizer-rerun
  investigation and the personnel-facts discrepancy finding are recorded
  below and in `CAPABILITY_LEDGER.md` — no optimizer code was touched.
- See "Batch: Phase 3B — Globe Experience, Semantic Motion & Closeout" below
  for the full record.

**Frozen:** 2026-07-30 — **Phase 3A OPTICAL FINISH, FINAL, tag `globe-phase3a-freeze`**
- Optical reconciliation against the approved reference render, closed out in
  three sequenced batches (foundation → full reconciliation pass → final
  micro-pass). This is the canonical optical baseline; Phase 3B (motion/
  roadmap/production-pathway visualization) has not started.
- See "Batch: Phase 3A — Optical Reconciliation (FINAL)" below for the full
  record — every value changed, why, and what remains open.

**Frozen:** 2026-07-28
- `globe: recover finalize and freeze globe rendering` — recovery + functional freeze
- `globe: premium glass rendering` — rendering architecture (tag `globe-glass-v1`)
- `globe: day/night theme + night visual system` (tag `globe-night-v1`)

**Frozen:** 2026-07-29 — Phase 2 closeout **checkpoint**, tag `globe-phase2-freeze`
- `globe: phase 2 closeout — semantic system, ambient behaviour, hover, freeze`
- An intermediate checkpoint, **preserved**, not final acceptance: post-freeze
  review found sizing/composition regressions and an untrustworthy live
  semantic distribution. See the reconciliation batch below.

**Frozen:** 2026-07-30 — **Phase 2 FINAL, tag `globe-phase2-final-freeze`**
- `globe: phase 2 post-freeze reconciliation — sizing, fixture, final freeze`
- This is the **canonical Globe implementation** future UI work builds around.
  Phase 3 is optical finish only; see the reconciliation batch's explicit
  "may not" list at the end of this file.

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

---

## Batch: Phase 2 POST-FREEZE RECONCILIATION — final functional freeze (tag `globe-phase2-final-freeze`)

**Frozen:** 2026-07-30. `globe-phase2-freeze` (8001db9) is **preserved** as the
intermediate checkpoint it was; this is the final Phase 2 acceptance.

Phase 3 (optical finish against the approved reference render) has **not**
started.

### Canonical runtime proven before any change (Task 1)

| Fact | Value |
|---|---|
| Repository root | `/Users/Suraj/cineglobe-frametax` |
| Branch | `claude/audit-frametax-features-NZcX5` |
| Commit at start | `8001db9` (== tag `globe-phase2-freeze`) |
| Frontend | Vite dev server, port **5173** |
| Backend | uvicorn `app.main:app`, port **8010** |
| Frontend API target | `http://localhost:8010/api/v1/cineglobe` (`frontend/.env`) |
| Production ID | **`LITTLE-UTOPIA`** — "The Little Utopia", MU anchor, $4,364,393, `as_of_date` 2026-07-10 |
| Runtime data source | **No database.** Module-level in-memory state in `little_utopia_state.py` + `lru_cache`; zero `AsyncSession`/`get_db`/`Depends` in `cineglobe.py` or `little_utopia_state.py` |

### Recommendation stability: **VERIFIED STABLE** (Task 2)

Deterministic under identical inputs, proven three ways:

| Check | Result |
|---|---|
| 5 repeated `GET /structures` | **byte-identical** (full-response SHA `59827a02…`, order hash `abd30537…`) |
| Full **backend restart**, then re-read | **byte-identical** — every field, same hashes |
| Ordinary page reload (UI) | deterministic — 177 cards, same order hash `aeeee6fe`, same rank 1 |
| Overlay toggle / day-night / Inspector | inert w.r.t. structures (order hash unchanged) |
| rank 1 | `ALLOC-BASELINE-MU`, NPC **$2,622,262.20** (matches the ledger invariant) |

Ordinary page load does **not** regenerate or reshuffle, so **no containment
was needed** and none was added.

**The two real mechanisms behind the reported "changes between sessions"** —
neither is nondeterminism, and neither is a Globe defect:

1. **`leadingStructureId` is client-only and resets on every full page load.**
   Verified live: set to "Mauritius + Vancouver", reload → back to "Mauritius"
   (backend rank 1 unchanged throughout). Changing it changes what the Globe,
   the Overlay and the LEADING STRUCTURE strip *display*, with no ranking
   change. This is the most likely explanation of the report — including
   because earlier verification batches set it themselves.
2. **Engine inputs are mutable from the UI and are not persisted.** `POST
   /facts`, `/people`, `/economics/controls`, `/locations`,
   `/contingency/deploy` all mutate module-level state and `cache_clear()` the
   LRU. Answering questions legitimately changes the ranking (intended); a
   backend restart silently discards **every** answer and reverts the
   recommendation. Recorded as a **VERIFIED DEFECT — DEFERRED BY PHASE**
   (engine/persistence, not Globe). `POST /scenarios` exists in `api.js` but is
   **called by nothing**, so it is not a source of new entrants.

### Development-only four-state visual fixture (Task 3)

**Why it exists:** live output resolves to 1 Recommended / 84 Optimized
alternative / 0 Unlockable / 1 Additional. That does not exercise the fourth
state, and it is **not credible as a production decision output** — "priced" or
"technically viable" is not "optimized alternative". Globe visual acceptance is
therefore isolated from engine output.

| Aspect | Detail |
|---|---|
| Activation (documented) | `VITE_GLOBE_VISUAL_FIXTURE=true` — e.g. `VITE_GLOBE_VISUAL_FIXTURE=true npm run dev` |
| Activation (dev convenience) | `?globeFixture=1`, additionally gated on `import.meta.env.DEV` |
| Default | **disabled** |
| Production build | **statically eliminated** — verified: neither `VITE_GLOBE_VISUAL_FIXTURE` nor `globeFixture` appears anywhere in `dist/assets/*.js` |
| Writes | none. Presentation-layer only; asserted in tests that the module contains no `fetch(`/`XMLHttpRequest`/`localStorage`/`sessionStorage`/`POST` |
| Disclosure | on-screen amber badge (`GlobeFixtureBadge`) + one `console.warn` |
| Injection point | one — `buildGlobeView()` rewrites the status map, so fill, beacons, pulse eligibility, hover labels and card dots all follow with no second code path |
| Owner split | the fixture supplies **slot names only**; `globeData.js` remains sole owner of what a state looks like, so the fixture can never introduce a colour or a fifth state |

**Assignments (globe keys, deterministic):**
- Recommended (1): `MU`
- Optimized alternative (12): `GB IE ES` · `ZA MA` · `NZ KR TH` · `US-GA CA-BC MX CL`
- Unlockable opportunity (12): `IT PL HR IS` · `EG JO IL` · `MY PH AU` · `US-NY CO`
- Additional: everything else (**61** markers / 81 assigned states)

Measured live: **1 / 12 / 12 / 61** hover markers, all four states present, all
four regions represented in both non-baseline states.

**Cost-a-cycle note:** the first version keyed on the winning structure's
`jurisdiction_code` and `AU-QLD` silently never matched — Australia is not
rendered at admin-1 level, so every `AU-*` code collapses to the globe key
`AU`, whose representative code is whichever won the status upsert. Assignments
are keyed on the **globe key** now, and a test enforces that only `US-*`/`CA-*`
may carry a sub-national suffix.

### Sizing and composition: four measured defects repaired (Task 4)

All numbers below are live measurements, not estimates.

| Defect | Before | After |
|---|---|---|
| **Sphere overflowed its frame.** `DEFAULT_CAMERA_DISTANCE = 225` put the silhouette at `tan(asin(100/225))/tan(25°)` = **106.4%** of the available half-height | 298px radius vs 280px half-height — **18px clipped top and bottom**; **12 European markers** (GB IE IS NO SE DK DE NL BE FR EE FI) projected outside the canvas | computed fit (`fitCameraDistance`), sphere at **80.7%** of half-height, **63px headroom**, **0 clipped** |
| **Globe stage height unbounded.** `height: 100%` on an auto-rows grid is not a bound, so the 177-card rail drove the row | stage **19751px** tall at 1600×900 around a 560px canvas; page scrolled for screens | `grid-template-rows: minmax(0, 1fr)` + rail `overflow-y: auto` → stage **693px**, `scrollHeight === clientHeight` |
| **Ellipse whenever the Inspector was open.** `setViewOffset` scales horizontal world span by `w/(w+px)` while still rendering into `w` pixels, so horizontal scale became `(w+px)/w` × vertical | horizontally stretched sphere for as long as an offset was applied | `camera.aspect` now describes the **virtual** sensor `(w+px)/h` → scales match, shift is a pure pan. Confirmed visually circular, Inspector open and closed |
| **`maxDistance = 460` silently overrode the fit.** OrbitControls clamps on every `update()` | at 1180×820 the fit asked for 935, the ceiling won, **53px of the globe hung off the canvas** and the rest sat under the panel | ceiling **raised, never lowered**: `max(460, fit × 1.02)`. Disc centred in the visible region (669 vs 668), **0 clipped** |

Also fixed: the canvas now tracks **height** as well as width (renderer,
composer, bloom, CSS2D and camera aspect all resize together); `.globe-screen-canvas`
lost its hard `max-width: 980px` (which both left a blank strip and was the
binding constraint at 1600px) in favour of `--globe-stage-max-w`; the stage is a
flex column so the caption is not eaten by `overflow: hidden`.

**Centralized layout tokens** (`tokens.css`): `--globe-rail-w: 300px`,
`--globe-stage-max-w: 1240px`, `--globe-stage-min-h: 420px`. Camera framing is
computed from the resulting box, so these can be changed without reintroducing
clipping.

**Also repaired — back-facing hit targets.** three-globe computes
`isBehindGlobe` for every html element but only acts on it when
`htmlElementVisibilityModifier` is supplied, and it never was. Every jurisdiction
on the far side kept a live 28px click target: a click on apparently empty canvas
could select a country on the opposite side of the world. Now `display: none`
when behind the globe — which also made "is the globe clipped" measurable at all
(the first narrow-viewport check reported 29 phantom clipped markers before this).

### Runtime acceptance matrix — RUNTIME VERIFIED

Driven in Playwright (a genuinely visible page at ~65fps). The in-app browser
pane throttles `requestAnimationFrame` when not compositing — measured **7
frames in 15.9s** — which makes continuous motion unobservable there.

Every cell: **0px clipping on all four edges**, exactly **1 Recommended**
(Mauritius), hover reporting the semantic state with **no money**, **0 console
errors**.

| Viewport | Canvas | Disc R (closed) | Disc R (Inspector open) | Clipping, all cells |
|---|---|---|---|---|
| 1600×900 | 980×650 | 250px | 227px | 0 / 0 / 0 / 0 |
| 1440×900 | 820×650 | 250px | 169px | 0 / 0 / 0 / 0 |
| 1280×800 | 660×560 | 215–221px | 106px | 0 / 0 / 0 / 0 |
| 1180×820 (extra narrow) | 560×570 | 221px | 66px | 0 / 0 / 0 / 0 |

Each viewport verified in **day and night**, Inspector **closed and open**, plus
a **closed-restored** cell confirming the composition returns to baseline.

| Behaviour | Evidence |
|---|---|
| Autorotation at rest | 14px / 3s (Ghana, fresh load); 27px / 3s measured at 1280 earlier |
| Autorotation yields to selection | **0px** while a jurisdiction is selected, both themes |
| Hover | brighten + border emphasis; card reads e.g. "Egypt / Unlockable opportunity / Primary shoot"; clears on mouseleave |
| Selection | camera flight settles, others dim, Inspector opens with full trace, selection survives Inspector close |
| Overlay round trip | 86 → 1 (`["MU"]`) → 86, no stale route |
| Overlay caption | now honest for a single-jurisdiction recommendation: "The recommended structure is single-jurisdiction — no routing to show." (previously always promised routing) |
| Day/night | no remount — `sameCanvasNode: true`, all 86 markers survive, geometry identical |
| Fixture off by default | no badge; live tally returns to 1 / 84 / 1 — **zero contamination** |

**Honest limits of the automated checks.** Circularity was confirmed by
**screenshot**, not by the marker-extent proxy — that proxy showed 3–11% skew
depending on which latitudes happen to carry jurisdictions, so it cannot prove
circularity and is not used as evidence. `prefers-reduced-motion` remains
code-verified only (the harness cannot emulate the media query).

### Regression protection (Task 8)

`frontend/tests/globe-invariants.test.mjs`, run with `npm test` — Node's
built-in `node --test`, **no new dependency**. **20 tests, 20 passing.**

Covers: sphere and beacon containment at all four verification viewports;
portrait frames pulling back rather than clipping; the previously-shipped 225 and
246 distances still *failing* (so a loosened fit is caught); exactly four
semantic states with no `darkRed`/`red`/`charcoal`; no legacy wording in any
label; `PULSE_TIERS == ["gold"]` **and** ≥2 `PULSE_TIERS.has()` call sites in
Globe3D with the old island/city-state predicate absent; `GlobeLegend.jsx` still
deleted and no `.globe-legend*` selector; no `<Money>`/`incentiveUsd`/`npcUsd`
inside any `.globe-tooltip`; fixture disabled by default, deterministic,
canonical-slots-only, network-free, DEV-gated, globe-key-only; `GLOBE_THEME` the
single source with both themes defining identical keys; `THREE.Clock` absent;
ambient motion gated on `prefers-reduced-motion`.

Geometry is in `lib/globeFit.js` — pure, no three.js or DOM — precisely so the
no-clipping property is arithmetic in a test rather than opinion in a review.

**Note:** code-level assertions strip comments first. This codebase deliberately
quotes the defects it replaced, and the first run of the pulse-predicate test
failed on the comment documenting the very fix it guards.

### Approved reference image — NOT RECEIVED

**No image was attached to the reconciliation prompt.** Consequently:
- no reference file was preserved to a design/reference location;
- **no reference path is recorded here**, rather than inventing one.

Phase 3's contractual visual target is therefore still **outstanding input**.
Everything else in this batch was completed. Re-supply the render and it can be
stored and cited in one edit.

### Phase 3 optical gaps (recorded, deliberately NOT addressed)

From the day/night verification, relative to a premium finish:
- **Daytime ocean** reads as a near-black neutral slate against the light
  application shell — the globe looks like a dark inset rather than a lit object.
- **Neutral-country material** is legible but flat; continents separate mainly by
  border stroke rather than by their own tone.
- **Saturation**: the four semantic colours are correct in hue but sit on a very
  dark ground, so Additional in particular reads faint at small sizes.
- **Borders** are still the dominant shape cue in day mode.
- **Atmosphere**: three-globe's own layer stays off (it z-fights the sphere); the
  fresnel shell is a limb, not an atmosphere. No particulate/haze field.
- **Lighting**: single directional key + IBL; no terminator softening.
- **Clearcoat / reflections**: `THREE.sigmaRadians 0.34 will clip` persists — the
  PMREM blur clips to 20 samples, so the environment is a 20-sample
  approximation of the requested blur. Deliberately unchanged: the frozen
  appearance is built on that approximation, so altering sigma is Phase 3's
  optical remit, not a "final calibration only" pass.
- **Optical depth**: jurisdictions are opaque enamel, not translucent mineral
  insets (carried over from `globe-night-v1` — needs a transmission/refraction
  pass).
- **Composition at narrow widths**: a 400px Inspector over a 560px canvas leaves
  a 160px strip, so the fully-visible globe is necessarily small (66px radius at
  1180×820). Compliant, but a narrower or docked Inspector at small widths is a
  Phase 3 UX decision.

### Engine defects recorded for the later optimizer workstream (all DEFERRED BY PHASE)

1. **"Priced" is being treated as "optimized alternative."** 84 of 86 resolve to
   Optimized alternative. An optimized alternative must show a real economic or
   production advantage over the baseline **after** incremental relocation,
   qualification, compliance, travel, legal, entity, payroll, financing and
   operational costs. Not repaired here; no records were relabelled.
2. **Single-jurisdiction coverage is conceptually incomplete.** Every eligible
   single jurisdiction should ordinarily be priced; exclusion should require a
   real production constraint (location impossibility, legal prohibition,
   unavailable capability, scheduling infeasibility, mandatory cultural-test
   failure, or another authoritative gate). Missing knowledge, a missing
   prebuilt scenario, or the absence of a generated record is **not** a valid
   exclusion. Current data: 21 discovery-touched jurisdictions carry no
   structure at all.
3. **Multi-jurisdiction combinations must provide measurable benefit** — post
   uplift, VFX incentive, regional/federal stack, treaty qualification,
   cultural-test uplift, grant/fund access, anchor-component economics,
   labour/cost advantage, or a real qualification pathway — with incremental
   friction and relocation costs included. Do not propose a combination merely
   because two countries can both participate.
4. **Known project attributes are unused for co-production pathways.**
   Australian writer, UK director and UK lead actor should be exercised against
   real co-production / cultural-qualification routes in the engine phase.
5. **Engine inputs are not persisted** (see Task 2 above) — a backend restart
   discards every answered fact and reverts the recommendation.

### Phase 3 may tune constants. It may NOT:

1. reintroduce a fifth semantic state, or a `darkRed`/`red` alias;
2. put a pulse on anything but the recommendation, in **either** code path;
3. re-add a persistent legend or `.globe-legend*` CSS;
4. render money figures in a Globe hover card;
5. re-add a module-level duplicate of any `GLOBE_THEME` value;
6. reintroduce `THREE.Clock`;
7. restore a hardcoded camera distance in place of `fitCameraDistance`, or lower
   `maxDistance` below the computed fit;
8. ship the visual fixture enabled, or let it write anywhere;
9. remove `htmlElementVisibilityModifier` (back-facing markers would become
   clickable again).

---

## Batch: Phase 2 FINAL RECONCILIATION — fixture durability, colour hierarchy, US/CA identity (updates `globe-phase2-final-freeze`)

**2026-07-30, second pass.** Reconciliation-first batch: the runtime was
diagnosed before any code was written, per instruction.

### APPROVED REFERENCE RENDER — received, and it conflicts with Phase 2

The approved render is now the contractual **Phase 3 visual** target. It is
stored as the acceptance target for optical finish only.

**Recorded conflict, unresolved by design.** The render depicts:
- a **persistent six-category legend** — "Leading recommendation / Qualified /
  viable / Conditional / Evaluated / not applicable / No known incentive / Not
  evaluated";
- the heading **"Candidate jurisdictions"**;
- a sidebar **"GLOBE MODE — Production"** control.

The first two are exactly what Phase 2 deleted under explicit instruction (the
legend, and the legacy database-state vocabulary including "No known incentive",
which asserted a verdict the backend never reached). Read literally,
"the render supersedes any previous interpretation" would reinstate a
five/six-state model and the legend.

**Interpretation applied:** the render governs OPTICS — ocean luminosity, land
presence, saturation, contrast, hierarchy, atmosphere, graticule — and does NOT
reinstate the legacy categories, the legacy heading, or the persistent legend.
Grounds: this batch's own brief keeps semantics out of scope, forbids typography
redesign, and says the render should guide "saturation, contrast, hierarchy".
**If that reading is wrong it is a semantic reversal, not a polish item, and
must be commissioned explicitly.**

The render's persistent GLOBE MODE control DID inform this batch: a visible
mode readout is part of the intended design, which is why the fixture indicator
below is a mode indicator rather than debug furniture. Placing one properly in
the shell chrome is Phase 3 layout work.

### Q1 — Why the fixture reverted. VERIFIED CAUSE: **fixture disabled**

Not speculation; the sequence was measured.

| Step | URL | Fixture |
|---|---|---|
| Loaded with `?globeFixture=1` | `/production/globe?globeFixture=1` | **ON** |
| Clicked the "Overview" project tab | `/production/overview` | OFF |
| Clicked back to "Project Globe" | `/production/globe` | **OFF** |

Activation was derived from `window.location.search` alone. The app's project
tabs are react-router `<Link>`s to **bare paths**, so any in-app navigation
discards the query string — and `.env` never set
`VITE_GLOBE_VISUAL_FIXTURE`, so the fragile URL route was the only live gate.

Ruled OUT by this evidence: not wired (it rendered at step 1), overwritten,
cache, hot-reload, routing bug (the app routed correctly), and "production data
replacing fixture" — production rendering is the CORRECT behaviour once the
fixture is off. The fixture simply switched itself off.

**Fix — activation now latches into durable client state:**
1. `VITE_GLOBE_VISUAL_FIXTURE=true` — highest precedence, build-time.
2. `?globeFixture=1` / `=0` — DEV-only, **latches** on/off, so one visit is
   enough and the URL need not be carried around.
3. otherwise the latched value, defaulting to **off**.

`localStorage` is the store — client-side developer state, not a backend write,
and every write path is gated on `import.meta.env.DEV`. Verified: the exact
away-and-back sequence above now keeps the fixture ON with no query string.

### Q2 — The four semantic states, verified per country

| State | Colour | Count | Countries |
|---|---|---|---|
| Recommended | `#f7dc9b` | **1** | Mauritius |
| Optimized alternative | `#55d698` | **12** | British Columbia, Chile, Georgia (US), Ireland, Mexico, Morocco, New Zealand, South Africa, South Korea, Spain, Thailand, United Kingdom |
| Unlockable opportunity | `#eaa93c` | **12** | Australia, Colombia, Croatia, Egypt, Iceland, Israel, Italy, Jordan, Malaysia, New York, Philippines, Poland |
| Additional | `#8c96a4` | **61** | Abu Dhabi, Alabama, Albania, Belgium, … Virginia, Washington |

### B — The Globe was "mostly grey" because the emphasis ladder was INVERTED

A measured ordering error, not a taste matter. Perceived luminance
(0.299R+0.587G+0.114B) of the shipped palette:

| | before | after |
|---|---|---|
| untouched land | 117 | **129** |
| Additional | **177** ← 2nd brightest | **149** |
| Optimized alternative | 137 | **168** |
| Unlockable opportunity | 161 | **176** |
| Recommended | 196 | **221** |

Additional — the lowest-emphasis state and the residual bucket holding 61 of 86
jurisdictions — was rendering BRIGHTER than both actionable states. The Globe
was therefore a field of light grey with the actionable states sitting beneath
it. No material or lighting work could have compensated; the palette order was
wrong. Optimized and Unlockable are deliberately close (168/176): they are peer
states separating by hue, and only Recommended may dominate (+45).

Guarded by `npm test` — the ladder is asserted monotonic, Additional asserted
desaturated and cool, and Recommended asserted to lead by ≥25.

### C — Neutral countries now have presence

`GRAPHITE_HEX` 117 → 129 (day) and night land 85 → 99, and — the substantive
change — **polygon caps gained an emissive floor** (`emissiveIntensity` 0.13
frosted / 0.17 glossy, keyed to each cap's own colour). Emissive is additive and
lighting-independent: it is the same mechanism the ocean body already uses to
avoid reading as a hole on the unlit hemisphere, and land caps had **no floor at
all**, so on the shadowed side of the terminator neutral countries rendered as
voids and the semantic hierarchy flattened entirely. Asserted in tests that land
clears the ocean by ≥55 luminance. The lighting rig is untouched.

### D — Card data source: **PRODUCTION ENGINE**, now labelled

Determined from source, not assumed: the cards colour from
`STATUS_HEX[structureTier(s, rankById)]` over the live allocated structures and
ranking — production engine, in every mode, never fixture and never cached. The
fixture only rewrites the Globe's semantic map, so fixture mode genuinely does
put fixture colours beside production cards. That is now stated on screen:
"Cards below show **production engine** data. The Globe is showing fixture
states — the two will not agree." No card redesign.

### E — US/Canada identity repaired

Nine jurisdictions were labelled with **cities**, which mislabels the incentive
programme itself rather than merely the marker:

`CA-BC` Vancouver→**British Columbia** · `CA-ON` Toronto→**Ontario** ·
`CA-QC` Montreal→**Quebec** · `US-CA` Los Angeles→**California** ·
`US-GA` Atlanta→**Georgia (US)** · `US-LA` New Orleans→**Louisiana** ·
`US-OR` Portland→**Oregon** · `US-TX` Austin→**Texas** ·
`US-WA` Seattle→**Washington** · plus `CA-NL`→**Newfoundland and Labrador**.

Coordinates are unchanged — a city coordinate is a fine marker position inside
its state. Hover and selection already operated on admin-1 polygons; the defect
was purely identity. Runtime confirmed: hover reads "California / Additional /
Primary shoot"; selecting British Columbia opens "JURISDICTION SEGMENT · FULL
RELOCATION TO CA-BC". No city is exposed as a Globe jurisdiction.

**Two defects this fix surfaced, both caught by new tests:**
1. **A collision I introduced** — the country Georgia (`GE`, 41.72/44.79) and the
   US state (`US-GA`, 33.75/−84.39) both became "Georgia". Only the colliding
   entry is qualified: "Georgia (US)".
2. **A pre-existing dead alias** — `AE_AD` duplicates `AE-AD` (same coordinates,
   same name, referenced nowhere, and absent from the backend payload, which
   emits only `AE-AD`). Left in place as harmless; the invariant treats
   same-coordinate entries as aliases, so it flags only genuinely different
   places sharing a label.

### F — Recommendation stability: **VERIFIED STABLE** (re-confirmed)

Re-run after every change in this batch. Five repeated `GET /structures`
byte-identical, and the hashes are **identical to the pre-change baseline** —
`full=59827a0248826ad7`, `order=abd3053723335303`, rank 1 `ALLOC-BASELINE-MU`,
NPC **$2,622,262.20** — proving these frontend-only changes did not perturb the
engine at all.

### Runtime acceptance — all pass

| Item | Evidence |
|---|---|
| fixture mode visibly works | indicator "GLOBE MODE · VISUAL FIXTURE" + counts + activation source + exit control |
| survives in-app navigation | away-and-back with no query string: still ON |
| fixture off returns production | `?globeFixture=0` → latch cleared, no indicator, no card note, tally back to 1/84/1 |
| four semantic colours visible | per-country table above; hierarchy monotonic |
| no production contamination | production tally identical to pre-fixture |
| recommendation stability | byte-identical to baseline |
| US/CA interaction | state/province identity; no cities |
| hover | "California / Additional / Primary shoot", no money, clears on leave |
| selection | province selection opens the correct segment Inspector |
| Inspector | opens/closes; 0px clipping in both states |
| Overlay | 86 → 1 (`MU`) → 86, clean |
| day/night | no remount (`sameCanvasNode: true`), 86 markers, 0 clip, indicator persists |
| console | **0 errors** |
| tests | **27/27** (`npm test`) |
| build | clean |

**A defect introduced and fixed within this batch, recorded for honesty:**
publishing fixture counts synchronously from `noteFixtureCounts` — reached from
`buildGlobeView` inside a `useMemo`, i.e. during render — called `setState` on
the mode indicator while another component was rendering. React reported it and
it is now deferred via `queueMicrotask`. Caught by the console-error acceptance
gate, not by the build.

### Phase 3 optical gaps, measured against the approved render

The Globe is materially closer in hierarchy but remains far from the render's
finish. Outstanding, all explicitly out of scope here:
- **ocean** is near-black; the render's is a luminous deep blue with depth;
- **atmospheric limb glow** absent (three-globe's own layer stays off — it
  z-fights the sphere; the fresnel shell is an edge, not an atmosphere);
- **graticule** (lat/long grid) absent entirely;
- **overall exposure** far below the render — most of the visible hemisphere
  sits in terminator shadow, which is why an emissive floor was needed at all;
- **land material** still flat; the render shows varied, saturated territory;
- **city-light / night-side detail** absent;
- **`THREE.sigmaRadians 0.34 will clip`** persists — the environment blur is a
  20-sample approximation, deliberately unchanged;
- jurisdictions are opaque enamel, not translucent mineral insets;
- a 400px Inspector over a narrow canvas still yields a small (66px radius)
  fully-visible globe at 1180×820.

### Added to the Phase 3 "may not" list

10. reintroduce URL-only fixture activation (it silently switches itself off);
11. invert the emphasis ladder — Additional must never outrank an actionable
    state;
12. remove the polygon emissive floor (neutral land collapses to black);
13. label a US state or Canadian province with a city name;
14. show fixture Globe colours beside unlabelled production cards.

---

## Batch: Phase 3A — Optical Reconciliation (FINAL, tag `globe-phase3a-freeze`)

**Frozen:** 2026-07-30. Closes Phase 3A. Ran as three sequenced batches
against the approved reference render (a screenshot of an earlier build,
provided directly in-conversation): foundation → full reconciliation →
final micro-pass. Owns `Globe3D.jsx`, `globeData.js`, `GlobeLegend.jsx`
(new), `ProjectGlobe.jsx` (one mount line), `screens.css` (legend styling),
`tests/globe-invariants.test.mjs`. Did not touch the Inspector, Overview,
Workspace, Scenarios, Optimizer, or any backend path.

### A real bug found and fixed along the way: PMREM sigma clipping

`pmrem.fromScene(envScene, 0.34)` had been silently clipping since the
premium-glass pass was first written — three.js's `PMREMGenerator` caps the
top mip's blur at 20 samples (`MAX_SAMPLES` in the installed source), and
0.34 radians requests ~166. `THREE.sigmaRadians, 0.34, is too large and will
clip` fired on every mount, every theme, in production, and had been
carried in this manifest's own "Not delivered" list across three prior
freezes as a known-but-deliberately-untouched item. Solved for the actual
clip-free ceiling from the library's own sample-count formula and lowered
to **0.035** — console is now genuinely clean, not just "acceptably noisy."

### Legend restored, then its terminology corrected twice

Phase 2 deleted the persistent legend outright (legacy six-category
model). This batch reinstates it as new, tightly-scoped, tested
`GlobeLegend.jsx` — exactly four states read live from `GLOBE_SEMANTIC`,
visually secondary (10px type, low-contrast chrome), Project Globe only,
production-visible (unlike the dev-only fixture badge). Labels moved twice
in this batch, each an explicit, separate instruction:
`Optimized alternative` → `Unlockable opportunity`/`Additional` → `Opportunity`/`Baseline`
→ final: `Optimized alternative` → `Optimized`. Current canonical set:
**Recommended / Optimized / Opportunity / Baseline.**

**Known minor gap, not fixed (out of this batch's explicit scope):** the
dev-only fixture disclosure (`globeVisualFixture.js`'s console warning and
`GlobeFixtureBadge`'s on-screen text) still say "Optimized alternative" /
"Unlockable" — hardcoded strings, not read from `GLOBE_SEMANTIC`. Both are
DEV-only surfaces, never shipped to production, so this was left for a
follow-up rather than expanding this batch's file list.

### Semantic palette — reconciled twice, both times against real luminance math

First pass sampled the approved render directly for jade/amber richness.
Second pass (this freeze) replaced all four with explicit material
identities given directly: **Recommended** `#e6d3a8` (warm champagne-gold),
**Optimized** `#4cbd97` (richer jade, not pale mint), **Opportunity**
`#d48a49` (restrained amber-copper), **Baseline** `#8494a4` (quiet
blue-grey slate).

**A real mistake made and caught in this same pass:** the first attempt at
these four hexes was luminance-checked using `THREE.Color`'s own `.r/.g/.b`
after `getHSL`/construction — which, under three.js's default colour
management, are **linear-space** values, not the raw sRGB byte values the
test file's `lum()` parses directly from the hex string. Multiplying those
by 255 produced luminance numbers that didn't match reality and the test
failed (`Optimized (164) must outrank Additional (168)`, using the test's
real byte-parsed numbers). Recomputed with a raw hex→byte HSL/luminance
harness matching the test exactly before finalizing: land 131 < Baseline
145 < Optimized 151 < Opportunity 153 < Recommended 212. **Do not use
`THREE.Color` for any future luminance check against this test — parse the
hex bytes directly, the same way the test does.**

### Country material depth — a curvature lever, not a noise lever

Two rounds: first raised the existing `applyLandGrainShader` amplitude
(0.10 → 0.14) and nudged `envBase`/`roughness` once. The final micro-pass
was told explicitly not to add more visible grain — so depth was increased
a second time purely via `roughness` (land 0.58 → 0.52, quiet 0.53 → 0.48)
and `envBase` (0.34 → 0.38, 0.40 → 0.44) instead: lower roughness lets the
existing environment gradient vary more by each polygon's own surface
normal, which reads as curvature in a static frame without touching the
grain shader again.

### Ocean — richer variation via a corrected version of an earlier-abandoned idea

Added a third, finer noise octave to `makeOceanSurfaceTexture` (breakup
grain) and applied the SAME texture as `clearcoatRoughnessMap`, not just
`bumpMap` — the Phase 3A-final batch had tried this for the base
`roughness` channel and abandoned it because the texture's ~0.5 mean would
have halved the average value. This time the base `clearcoatRoughness` was
doubled first (0.28 → 0.56) to compensate, so the sphere-average stays
~0.28 but now genuinely varies per-pixel. `envIntensity` raised modestly in
both themes (0.40→0.44 day, 0.46→0.50 night) alongside it.

### Atmosphere / rim — tightened together, not independently

`ATMOSPHERE_ALTITUDE` pulled in again (0.11 → 0.095) and
`BASE_RIM_INTENSITY`/`uPower` raised in step (0.21→0.24, 3.1→3.4) so the rim
shell carries more of the curvature-reinforcement job as the library
atmosphere shell narrows — two shells with two distinct jobs, not one
shell doing both.

### Reflection shape — one arc attempt, then simplified per explicit instruction

First correction decomposed the single strip light into three shorter
segments on a gentle arc; runtime proof showed this still merged into one
bright spot rather than reading as curved. The final micro-pass explicitly
said to simplify rather than add complexity if the arc didn't work
reliably — reverted to **one** panel, longer and thinner, with a new
`tilt` parameter on `panel()` (rotates it about its own Z axis) so a
straight bar reflected off the sphere's own convex curvature reads as an
angled, soft-edged streak rather than a straight line or a round dot.
Verified close-up: elongated and diagonal, materially better than the
prior round blob, though still a genuinely bright core — recorded honestly
as improved, not eliminated.

### Runtime acceptance — all pass, this freeze

| Item | Evidence |
|---|---|
| Production mode, day | legend "Recommended / Optimized / Opportunity / Baseline"; richer jade/amber/gold visible |
| Production mode, night, comparable orientation | same palette, no remount, no console warning |
| Fixture mode, all four states | Optimized (Mexico, Japan, Thailand…), Opportunity (Philippines, Colombia, Saudi…), Baseline (background majority), Recommended (Mauritius gold beacon, confirmed via close crop next to Madagascar) |
| Production restored after fixture disable | `?globeFixture=0` — no badge, no console disclosure, real production tally back |
| Reflection close-up | angled soft-edged streak, not a round blob (see batch note above) |
| Inspector-open | selection, opening, positioning only — content/layout untouched, confirmed against the frozen Inspector |
| Graticule | absent (never re-enabled) |
| Console | **0 errors, 0 warnings** (fresh navigation) |
| Tests | **28/28** (`npm test`) |
| Build | clean (`vite build`) |

### Phase 3B (not started, explicitly out of scope here)

Motion/roadmap: production-pathway visualization, opportunity-state pulses
beyond the recommendation, optimization-replay animation, transition
effects between structures. None of this batch touched motion beyond the
existing frozen ambient set (env drift, rim breath, gold breath, yielding
autorotation) — all verified still present and untouched.

### Added to the "may not" list

15. use `THREE.Color`'s `.r`/`.g`/`.b` (linear space) to luminance-check a
    semantic hex against the test file's `lum()` (raw sRGB bytes) — parse
    the hex string directly, the same way the test does;
16. reintroduce `pmrem.fromScene`'s sigma above the clip-free ceiling
    (~0.041 against this file's current `_lodMax`) without re-deriving the
    ceiling from the installed three.js source;
17. add a fourth, independent studio-panel segment to "fix" the reflection
    shape — simplify the existing single tilted panel first.

---

### Addendum: Phase 3A final visual correction (moves `globe-phase3a-freeze`)

**2026-07-30, same day, second pass.** Three defects remained visible in
runtime screenshots after the freeze above. All three turned out to be the
SAME lever pushed one step further, not new mechanisms — `Globe3D.jsx` only.

- **Reflection still an isolated blob.** Root cause confirmed: the panel's
  shape was never the limiting factor — `clearcoat`'s near-mirror sampling
  turns even a long thin source into a sharp hotspot at its tangent point.
  Fix: raised `clearcoatRoughness` base 0.56 → 0.68 (avg ~0.28 → ~0.34),
  taller panel (0.07 → 0.16), steeper tilt (`Math.PI/10` → `Math.PI/7`),
  intensity trimmed to compensate (0.95 → 0.78). No new panel added.
- **Ocean texture not visible enough.** Added a compensated `roughnessMap`
  (base `roughness` doubled, 0.38 → 0.76, same texture) alongside the
  existing `bumpMap`/`clearcoatRoughnessMap` — same mean-bias-compensation
  technique already used for clearcoat, now applied to base roughness too.
  `bumpScale` nudged 0.32 → 0.34.
- **Country curvature still flat.** Same curvature lever as the prior batch,
  pushed one more step: `land` roughness 0.52 → 0.47 / envBase 0.38 → 0.42;
  `quiet` roughness 0.48 → 0.43 / envBase 0.44 → 0.48. Grain shader amplitude
  untouched (already at its documented ceiling).
- **Palette**: fixture screenshot re-verified all four states (Recommended
  gold beacon confirmed next to Madagascar, Optimized/Opportunity/Baseline
  all distinct) — no mismatch found, no hex changed this pass.

Verified: 28/28 tests, clean build, 0 console errors/warnings, production
dark/light, fixture all-four-states, production restored, Inspector-open
(selection/positioning only) — all captured as runtime screenshots, not
described. Tag `globe-phase3a-freeze` moved to this commit.

---

### Addendum 2: Phase 3A final closeout — terminology + hover intelligence

**Same day, third pass.** Two remaining Phase 3A items: production-facing
terminology and Globe hover.

**Terminology** (`globeData.js`): labels reconciled a third time to the
production's actual executive vocabulary — `Recommended` (unchanged),
`Optimized`→`Alternatives`, `Opportunity`→`Co-Production Opportunities`
(compact legend form `Co-Pro Opportunities`, added a `fullLabel`/
`STATUS_FULL_LABEL` pair so hover gets the long form and the legend keeps
the short one), `Baseline`→`Excluded`. Same four slots, same hex, same
`state` keys, same logic. The dev-only fixture disclosure (console warning
+ `GlobeFixtureBadge`) was also updated — Phase 3A-final's own manifest had
flagged this exact drift as a known, deliberately-deferred gap; closed now.

**Hover intelligence** (`ProjectGlobe.jsx`, `globeData.js`): the Phase 2
closeout rule "no money in a Globe hover card" is **explicitly reversed**
this batch, by direct user instruction — hover now shows jurisdiction,
category, base incentive program + rate, and estimated NPC, anchored near
the hovered marker (Globe3D's mouseenter now passes the hit-target's own
`getBoundingClientRect()` through) rather than fixed at the panel's top-left.
Every figure is read verbatim from existing fields — `structure.segments[]`
program_slug/rate_floor/rate_ceiling (same fields Inspector.jsx already
renders), `structure.npc_with_adjustments_usd`, and the discovery
examination's own real `reason` string for Excluded jurisdictions — no
second NPC calculation, no fabricated rate or reason. `programDisplay`/
`humanizeToken` were moved out of `format.jsx` into a new plain-`.js`
`programNames.js` (format.jsx re-exports them unchanged) specifically so
`globeData.js` — imported directly by `node --test` with no JSX transform —
can use them without pulling JSX into the test runner.

**A real bug found in runtime verification, not by a test:** the hover
fallback helpers (`baseIncentiveLine`, `npcFallback`) initially checked
`hover.status === "additional"` / `"unlockable"` — those are `semanticState`
values, but `hover.status` is the colour-slot key (`"gold"/"jade"/"amber"/
"silver"`). The check silently never matched, so an Excluded jurisdiction
with an actual (if unpriceable) structure attached — found live on Hungary —
showed the generic "Not available"/"Not priced" fallback instead of its real
backend-generated exclusion reason. Fixed to check `"silver"`/`"amber"`
directly; a regression test now asserts the source checks the colour-slot
keys, not the semantic-state strings.

**Verified live** (Playwright, fresh navigation each time): Recommended
(Mauritius — "EDB Film Rebate · 30% (up to 40%)" / "$2.6M"), Alternatives
(Colombia and California, production data), Co-Production Opportunities
(Egypt, fixture mode), Excluded (Hungary — real reason: "Not
production-capable: the production requires marine_filming,
open_water_filming..." / "Not viable"), US state + Canadian province hover,
hover-vs-click distinction (hover never opens the Inspector; click still
does, content/layout unchanged), light and dark app theme, fixture on/off
round trip, zero console errors/warnings. 30/30 tests, clean build.

---

## Batch: Phase 3B — Globe Experience, Semantic Motion & Closeout

**Frozen 2026-08-01, tag `globe-phase3b-freeze`.** Three sequenced pieces of
work, closed out together: Batch 1 (data-model groundwork — category-diff
engine, hover-format helpers, `STATUS_RANK` export), Batch 2 (border fix,
ocean motion, semantic hover illumination, category-transition pulse — all
under explicit authorization, motion/performance standards enforced), and
the final closeout (optimizer-rerun/data-flow investigation, vertical
legend, hover-contract rewrite, this documentation). No architecture change;
`Globe3D.jsx` remains the single rendering file, `three-globe` 2.45.2 /
three.js 0.185.1 unchanged, no new dependency added.

### Border z-fighting — root cause and fix

`three-globe`'s polygon layer renders each country/state's boundary as its
**own** complete `LineSegments`, scaled to `1 + altitude + 1e-4` (a fixed
relative offset above that feature's own cap). Two same-tier neighbors
(e.g. both "neutral") share the same `altitude`, so their shared border is
drawn **twice at the literal same radius** — coincident-depth GPU z-fighting,
which read as the reported dashed/broken/noisy border appearance. This is a
`three-globe` library behavior, not a bug in this codebase's config.

**Fix:** a deterministic per-feature `altitudeJitter(iso)` (hash of ISO code
→ a value in `[-2e-5, 2e-5)`) added to every branch of `altitudeFn`
(selected/inactive/gold/participating). The jitter is two orders of
magnitude below the smallest real semantic altitude step
(`INACTIVE_POLYGON_ALTITUDE = 0.002`), so the cap/fill is visually
unaffected but two same-tier neighbors no longer land on the exact same
radius. Verified: continuous, non-dashed borders in multiple regions
(Europe, Africa, the Americas), both themes. Regression test asserts every
`altitudeFn` branch includes the jitter term and that the jitter magnitude
stays below the real altitude step.

### Ocean motion

A restrained UV scroll — `oceanSurfaceTexture.offset.x` animated at
`1/2400` per second — on the **same** procedural bump/roughness/clearcoat-
roughness texture already built by `makeOceanSurfaceTexture()` (Phase 3A).
No new shader, no new geometry, no new `requestAnimationFrame` owner: the
step lives inside the existing single `animate()` loop, inside the existing
`ambientMotion`/`prefers-reduced-motion` gate. Land uses a separate
object-space grain shader with no texture, so it is unaffected by design.

### Semantic hover illumination (Co-Production Opportunities)

Hovering an Amber (Co-Production Opportunity) jurisdiction illuminates its
real related jurisdictions, using `structure.participants` (a real backend
field — this production's Co-Production Opportunities are
`component_relocation` structures with blockers, not treaty co-productions;
confirmed live that `reachable_treaty_partners: []` for this production, so
no treaty relationship was fabricated). Illumination uses the existing
`brightenHex()` helper only — no new color system — at two tiers: primary
related jurisdiction (from `structure.primary_jurisdiction`) at 0.22, other
related jurisdictions at 0.14. Ordinary hover stays at 0.30 (unchanged);
the category-transition pulse (below) is 0.45, the strongest of the three,
reserved for a genuine one-shot event.

**Bug found and fixed during this batch:** beacon-rendered jurisdictions
(Mauritius, Malta, Singapore — islands too small for the polygon layer,
rendered via `three-globe`'s separate `pointColorFn`/point-data path) were
not covered by the illumination/pulse logic at all — only the polygon path
(`capColorFn`) had been extended. Fixed by mirroring the same
`illuminatedIsos`/`pulsingIsos` checks into `pointColorFn`, and by adding
`.pointColor(globe.pointColor())` to the repaint-trigger effects (which
previously only re-invoked the four polygon accessors). Verified with a
source-level regression test; the polygon case (Croatia) was additionally
confirmed live.

### Category-transition unlock pulse

Reuses the existing `STATUS_RANK` (now exported from `globeData.js`) to
detect a genuine rank **improvement** (e.g. Excluded → Alternatives) via the
Batch 1 category-diff engine (`globeCategoryDiff.js` — `loadCategorySnapshot`
/`saveCategorySnapshot`/`diffCategories`, localStorage-persisted per
`production_id`, no false positive on first observation). On an improvement,
the affected jurisdiction(s) pulse once at 0.45 brighten for 2.4s, gated on
`prefers-reduced-motion`, with the timer owned by `ProjectGlobe.jsx` (the
caller), not the Globe component itself — consistent with "no duplicate rAF
loops, no new animation owner inside `Globe3D.jsx`."

### Vertical legend

Replaced the prior single-row 10px `.globe-legend-compact` with a vertical,
left-edge, 13px `.globe-legend-vertical` (`GlobeLegend.jsx` + `screens.css`)
using each state's `fullLabel` (long form, matching hover) rather than the
compact chip label. `pointer-events: none` (unchanged behavior — never
intercepts a click meant for the globe). Same four canonical states, same
`GLOBE_SEMANTIC` source of truth, no hand-written duplicate list. Verified
live: full four labels legible, positioned clear of the Inspector's
right-side float and the bottom caption, both themes.

### Hover-contract rewrite (final correction, direct user instruction)

The prior hover framing — `Program: X · Up to 40%` plus a second line
`Modeled Rate: 40% (guaranteed floor 30%)` — was flagged as reading like a
misleading "30–40% range." Rewritten to five clean fields, verbatim from
existing backend fields, no fabrication:

| Field | Source | Example (Mauritius, this production) |
|---|---|---|
| Program | `program_slug` → `programDisplay()` | EDB Film Rebate Scheme |
| Maximum Incentive | `rate_ceiling` (the pricing kernel's own `modeled_rate` — the only rate that funds every downstream dollar figure) | Up to 40% |
| Modeled Incentive | `segmentIncentiveUsd` (`incentive_ceiling_usd`), full dollar, never abbreviated | $1,742,131 |
| NPC | `npc_with_adjustments_usd`, full dollar | $2,622,262 |
| Incentive / Gross Budget | `segmentIncentiveUsd / grossBudgetUsd`, its own top-level line (no longer a sub-line) | 39.9% |

Verified against the live backend (`GET /structures`, `GET /production` for
production `LITTLE-UTOPIA`): `gross_budget_usd=4,364,393`,
`rate_resolution.modeled_rate=0.40`, candidate `PSC-MU` conservative case
`incentive_usd=1,742,130.8`, `net_production_cost_usd=2,622,262.2` — the
five displayed fields compute to exactly the values in the table above
(39.92% rounds to 39.9%). No second NPC calculation, no rate invented. The
Co-Production body's "Potential Uplift" field was renamed to "Co-Production
Potential" (still the honest "Not modeled yet" fallback — the optimizer does
not currently produce this figure; not fabricated).

### Optimizer-rerun and data-flow investigation (report only — no code change)

Traced the full path: `useCineGlobe()` (`getProduction, getPackage,
getRecommendations, getStructures, getLegal, getEconomics, getPeople,
getFacts` — all GET) is used **identically** by Overview, Workspace,
Scenarios, Project Globe, Binder, Record, Settings, Knowledge, and Reports —
one shared data path, no Globe-specific divergent fetch. Backend caching
(`get_state()` → `_build_state(fact_key, people_key)`,
`@lru_cache(maxsize=8)` in `little_utopia_state.py`) means repeated GETs
(page loads, hover, click, zoom, rotate, fixture-switch, Inspector-open) are
cache hits, not fresh optimizer runs — invalidated only by
`apply_fact_answers()`/`reset_fact_answers()`/`apply_people_facts()` (i.e.
POST `/facts`, `/people`). **Finding: the Globe never triggers an optimizer
rerun on load, hover, select, zoom, rotate, fixture-switch, or Inspector-
open.** This was already true of the architecture; no fix was required or
made.

**Personnel-facts discrepancy (reported, not corrected, per the no-
fabrication instruction):** live `GET /people` for this production returns
writer = Clara Salaman, nationality **GB**; director = Kim Farrant,
nationality **AU**; lead cast = "Unannounced Lead Cast", nationality
**unknown** (`missing_inputs: MISSING-NATIONALITY-cast-1`). This is the
opposite of an "Australian writer / UK director / UK lead actor" premise —
and the lead-actor nationality is genuinely unknown, not merely unentered
with a known value. Per the strict one-optimizer-run budget and the
no-fabrication instruction: **zero new optimizer runs were performed**, no
fact was invented or overwritten to match the incorrect premise. This is a
casting/data-entry gap for the production owner to resolve, not a Globe or
optimizer defect.

**Co-production qualification (reported, not built as a separate list):**
`treaty_engine.py`'s `evaluate_bilateral_eligibility()` /
`get_available_bilateral_treaties()` do not take personnel nationality as an
input — nationality/cultural-test wiring into treaty eligibility is a
separate, partially-implemented subsystem (a pre-existing, documented gap,
not new). This production has zero `treaty_coproduction`-type structures
and an empty `reachable_treaty_partners` list for Mauritius — every
"Co-Production Opportunity" shown is a real `component_relocation`
structure with real blockers, not a fabricated treaty relationship. No
Globe-only treaty database was built; the existing Optimizer Overlay arc
infrastructure (`buildOptimizerPathway` in `globeData.js`) was confirmed
already built and already used in served runtime (verified live: toggling
to "Optimizer Overlay" on the single-jurisdiction baseline correctly showed
the Mauritius beacon and the honest caption "The recommended structure is
single-jurisdiction — no routing to show") — reused, not rebuilt.

### Product decisions recorded for a future UX phase (NOT implemented this batch)

1. **Project Library** — a company-level, pre-optimization intake distinct
   from active productions ("one project = one eventual production"),
   holding script/budget/schedule/deck/artwork/notes. The Overview screen's
   "New production" placeholder should eventually become a shortcut into
   this library/intake flow.
2. **Project Art** — the app should search uploaded materials for usable
   key art, and eventually auto-generate artwork if none exists; the
   project library should use visual cards, not a file-folder UI.
3. **Company Knowledge** is explicitly **not** the project file library —
   it is the institutional-learning layer (incentive outcomes, jurisdiction
   performance, vendors, crew, costs, approval timing, audit behavior,
   financing experience, historical assumptions vs. actuals), distinct from
   the per-production record.

These are recorded here as product direction only; no code was written for
any of the three, per explicit instruction.

### Verified live (Playwright, this batch)

Border continuity (multiple regions, both themes); ocean drift motion
(gated correctly, confirmed no land motion); Co-Production hover
illumination (Croatia, polygon path, live; Mauritius/Malta/Singapore beacon
path, source-level regression test after the `pointColorFn` fix — a live
camera angle showing Mauritius simultaneously with a hovered European
country was not chased once the identical underlying mechanism was already
confirmed working and covered by a direct test, per the efficiency
instruction not to chase animation capture when deterministic evidence is
available); category pulse (reduced-motion gated, timer-owned by caller);
vertical legend (all four full labels, both themes, positioned clear of
Inspector and caption); final hover-contract rewrite on Mauritius,
cross-checked against live backend values (`Up to 40%` / `$1,742,131` /
`$2,622,262` / `39.9%`); zero console errors/warnings throughout;
`globeFixture=0` (no fixture artifacts) for every check above. 46/46 tests
passing, clean `vite build`.

### Explicitly deferred (do not start without new authorization)

- Phase 4 (Overview / broader production UX redesign).
- Inspector redesign (Inspector remains the verified-only explanation
  layer; its content/IA was not touched this batch).
- Project Library implementation (recorded above, not built).
- Optimizer nationality / cultural-test logic repair (the personnel-facts
  and treaty-eligibility gaps above are pre-existing and out of scope for
  the Globe).
