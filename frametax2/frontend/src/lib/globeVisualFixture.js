// ── Globe visual validation fixture (development only) ──────────────────
//
// WHY THIS EXISTS. The Globe's four semantic states cannot be verified
// against live optimizer output, because the live distribution does not
// exercise them: this production resolves to 1 Recommended, 84 Optimized
// alternative, 1 Additional and ZERO Unlockable opportunity. That
// distribution is also not credible as a production decision output — the
// canonical product rule is that "priced" or "technically viable" does NOT
// mean "optimized alternative", and an optimized alternative must show a real
// economic or production advantage over the baseline after incremental
// relocation, qualification, compliance, travel, legal, entity, payroll,
// financing and operational costs. Correcting that is engine work, explicitly
// out of scope for the Globe batch (see CAPABILITY_LEDGER).
//
// So the renderer is validated against a FIXED, HYPOTHETICAL assignment
// instead, which isolates Globe visual acceptance from unstable engine
// output. These are NOT optimizer conclusions and must never be presented as
// such — hence the mandatory on-screen disclosure (GlobeFixtureBadge) and the
// console warning below.
//
// GUARANTEES:
//   • disabled by default — requires an explicit opt-in (see isFixtureActive);
//   • the query-parameter route is additionally gated on import.meta.env.DEV,
//     so it is inert in a production build;
//   • presentation-layer only: it rewrites the client-side semantic state map
//     AFTER the backend response has been parsed. It issues no requests, makes
//     no writes, persists nothing, and cannot reach the optimizer, any
//     scenario record, or any production data;
//   • deterministic: assignment comes from the fixed code lists below, never
//     from randomness, so reloads are byte-identical.

// NOTE ON THE MODULE BOUNDARY: this file deliberately does NOT import
// GLOBE_SEMANTIC. globeData.js imports this module, so importing back would
// create a cycle — and the split is the right one anyway: the fixture decides
// WHICH semantic state a jurisdiction takes, and globeData.js remains the sole
// owner of what each state looks like. The fixture can never introduce a
// colour, or a fifth state.

export const FIXTURE_DISCLOSURE =
  "Visual validation fixture — hypothetical semantic assignments; not optimizer output.";

// ── Activation ──────────────────────────────────────────────────────────
//
// ROOT CAUSE THIS REPLACES (confirmed at runtime, not guessed). The first
// implementation derived activation from `window.location.search` alone. That
// is not durable state: the app's own project tabs are react-router <Link>s to
// bare paths, so clicking "Overview" and back to "Project Globe" walks
//   /production/globe?globeFixture=1  ->  /production/overview  ->  /production/globe
// and the flag is gone. Measured exactly that sequence: badge true, false,
// false. The `VITE_GLOBE_VISUAL_FIXTURE` route that WOULD have persisted was
// never configured in `.env`, so the fragile URL route was the only live gate —
// which is why the Globe "briefly showed fixture colours, then reverted".
// Nothing was overwritten, cached, or replaced by production data: the fixture
// simply switched itself off, and production rendering is the correct behaviour
// once it does.
//
// The fix is to make activation LATCH into durable client-side state:
//   1. `VITE_GLOBE_VISUAL_FIXTURE=true`  — forces on, highest precedence.
//   2. `?globeFixture=1` / `?globeFixture=0` — DEV-only, latches the toggle on
//      or off, so one visit is enough and the URL need not be carried around.
//   3. otherwise the latched value, defaulting to OFF.
//
// localStorage is the store. It is client-side developer state — not a backend
// write, not production data, and unreachable in a production build because
// every write path is gated on `import.meta.env.DEV`.
const STORAGE_KEY = "cineglobe.globeVisualFixture";

function devOnly() {
  try {
    return !!import.meta.env?.DEV;
  } catch {
    return false;
  }
}

function readLatch() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "on";
  } catch {
    return false; // storage blocked (private mode, sandbox) — stay disabled
  }
}

function writeLatch(on) {
  try {
    if (on) window.localStorage.setItem(STORAGE_KEY, "on");
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage blocked — the URL still governs this page view */
  }
}

// Consumed once at module load so a `?globeFixture=` parameter takes effect
// before the first render, and persists after the parameter is gone.
let urlOverride = null;
if (devOnly() && typeof window !== "undefined") {
  try {
    const raw = new URLSearchParams(window.location.search).get("globeFixture");
    if (raw === "1" || raw === "true" || raw === "on") { urlOverride = true; writeLatch(true); }
    else if (raw === "0" || raw === "false" || raw === "off") { urlOverride = false; writeLatch(false); }
  } catch {
    /* malformed URL — fall through to the latched value */
  }
}

export function isFixtureActive() {
  try {
    // Env flag wins outright — it is the documented, build-time method.
    if (import.meta.env?.VITE_GLOBE_VISUAL_FIXTURE === "true") return true;
    if (!devOnly()) return false; // inert in production builds, always
    if (urlOverride !== null) return urlOverride;
    return readLatch();
  } catch {
    return false;
  }
}

// How the fixture came to be on — surfaced in the mode indicator so there is
// never ambiguity about which mechanism is in play.
export function fixtureActivationSource() {
  try {
    if (import.meta.env?.VITE_GLOBE_VISUAL_FIXTURE === "true") return "env";
    if (!devOnly()) return null;
    if (urlOverride === true) return "url";
    if (readLatch()) return "latched";
  } catch {
    /* ignore */
  }
  return null;
}

// Programmatic off-switch, for the indicator's own control and for tests.
export function disableFixture() {
  if (!devOnly()) return;
  urlOverride = false;
  writeLatch(false);
}

// ── Deterministic assignments, keyed by GLOBE KEY ───────────────────────
// These are globeKey() values — the identity the polygon layer itself is keyed
// by — NOT raw jurisdiction codes.
//
// That distinction cost a verification cycle: the first version matched on the
// winning structure's `jurisdiction_code`, and `AU-QLD` silently never matched.
// Australia is not in SUBNATIONAL_COUNTRIES, so every AU-* jurisdiction
// collapses to the single globe key "AU", whose representative code is
// whichever one won the status upsert (AU-NSW here). Matching on the map key
// instead makes assignment independent of that upsert order, which is the only
// way a fixture can claim to be deterministic.
//
// Rule for editing these lists: use a country ISO2 (AU, GB, MU), or a
// sub-national code ONLY for US/CA (US-NY, CA-BC), which are the two countries
// the Globe renders at admin-1 level.
// Chosen for GEOGRAPHIC SPREAD so that several of each state are visible from
// any camera angle — Europe, Africa/Middle East, Asia-Pacific and the Americas
// are each represented in both non-baseline states. A "random-looking"
// distribution is the goal; random assignment is not, because the fixture has
// to be repeatable.
//
// Mauritius stays the single Recommended jurisdiction for continuity with the
// live production and with every screenshot taken in earlier batches.
const RECOMMENDED = ["MU"];

const OPTIMIZED_ALTERNATIVE = [
  // Europe
  "GB", "IE", "ES",
  // Africa
  "ZA", "MA",
  // Asia-Pacific
  "NZ", "KR", "TH",
  // Americas
  "US-GA", "CA-BC", "MX", "CL",
];

const UNLOCKABLE_OPPORTUNITY = [
  // Europe
  "IT", "PL", "HR", "IS",
  // Africa / Middle East
  "EG", "JO", "IL",
  // Asia-Pacific
  "MY", "PH", "AU",
  // Americas
  "US-NY", "CO",
];

// Everything else the production touches falls to Additional — the fourth
// state, and the one that must stay visible and geographically legible rather
// than disappearing into the untouched-land graphite.
const SLOT_BY_CODE = new Map([
  ...RECOMMENDED.map((c) => [c, "gold"]),
  ...OPTIMIZED_ALTERNATIVE.map((c) => [c, "jade"]),
  ...UNLOCKABLE_OPPORTUNITY.map((c) => [c, "amber"]),
]);

export const FIXTURE_EXPECTED_COUNTS = {
  gold: RECOMMENDED.length,
  jade: OPTIMIZED_ALTERNATIVE.length,
  amber: UNLOCKABLE_OPPORTUNITY.length,
  // `silver` is the remainder, so it is asserted as "everything else" rather
  // than a fixed number that would break whenever the dataset changes size.
};

// ── Co-Production relationship (development only) ───────────────────────
//
// WHY THIS EXISTS — a defect found during the Phase 3B ledger reconciliation,
// not a convenience. The Globe's Co-Production hover illumination reads
// `relatedCodes`, which globeData.js derives from the winning structure's
// real `participants` array. Measured against live output for this
// production: `relatedCodes` is EMPTY for all 86 jurisdictions, so the
// illumination has never actually fired at runtime.
//
// The cause is structural, not a bug: two structures exist per partner
// jurisdiction — `ALLOC-RELOC-<X>` (full relocation, participants `[X]`,
// fully priced -> jade) and `ALLOC-COMPONENT-POST-<X>` (component
// relocation, participants `[MU, X]`, carries blockers -> amber).
// `buildCountryStatuses`'s `upsert` keeps whichever has the HIGHER
// STATUS_RANK, and jade (3) outranks amber (2) — so the single-participant
// structure always wins and the two-participant one is never the `best`.
// Live category counts confirm the same thing from the other direction:
// 1 gold / 84 jade / 0 amber / 21 silver — this production has ZERO
// Co-Production Opportunities, so the state cannot be exercised at all.
//
// Whether the ranking should prefer the multi-participant structure is an
// OPTIMIZER/semantics question, explicitly out of scope for the Globe phase
// (see CAPABILITY_LEDGER). This fixture therefore supplies a HYPOTHETICAL
// relationship purely so the RENDERER can be visually validated, on exactly
// the same terms as the slot assignments above: deterministic, dev-only,
// non-persisting, disclosed on screen, and never presented as optimizer
// output.
//
// Anchor chosen for visual demonstrability from the default camera (Europe /
// Africa / Mediterranean, all visible without rotating), and deliberately
// mixed in render path so BOTH illumination code paths are exercised in one
// screenshot: IT/MA/GR are polygon-rendered, MT (Malta) is beacon-rendered
// via the separate pointColorFn path that a previous batch found was missing
// illumination entirely.
const FIXTURE_RELATIONSHIPS = new Map([
  ["EG", { primary: "IT", related: ["IT", "MA", "GR", "MT"] }],
]);

/**
 * Hypothetical related jurisdictions for a GLOBE KEY, or null.
 *
 * Returns raw globe keys only — never a colour, never a status. The caller
 * (globeData.js) remains the sole owner of what illumination looks like, the
 * same boundary the slot assignments above respect.
 */
export function fixtureRelatedFor(globeKeyValue) {
  return FIXTURE_RELATIONSHIPS.get(globeKeyValue) ?? null;
}

/**
 * The semantic slot this fixture assigns to a GLOBE KEY (see globeKey()).
 * Returns one of the four canonical slot names only — never a colour, never a
 * new state. Anything not explicitly listed is Additional, which is what keeps
 * the fourth state populated and visible.
 */
export function fixtureSlotFor(globeKeyValue) {
  return SLOT_BY_CODE.get(globeKeyValue) ?? "silver";
}

let warned = false;
let lastCounts = null;
const countListeners = new Set();

// Loud, once, in the console as well as on screen: anyone reading a screenshot
// or a console log must know these are not real optimizer conclusions.
//
// Also publishes the counts so the GLOBE MODE indicator can be mounted ONCE at
// the shell — the fixture recolours every Globe surface (Overview and Workspace
// as well as Project Globe), so an indicator that only appeared on one screen
// would leave exactly the ambiguity it exists to remove. Same subscribe pattern
// as lib/theme.js.
export function noteFixtureCounts(counts) {
  const changed =
    !lastCounts ||
    ["gold", "jade", "amber", "silver"].some((k) => lastCounts[k] !== counts[k]);
  lastCounts = { ...counts };
  if (changed && countListeners.size) {
    // DEFERRED OUT OF THE RENDER PHASE. This function is reached from
    // buildGlobeView(), which screens call inside a useMemo — i.e. during
    // render. Notifying synchronously called setState on the mode indicator
    // while a different component was rendering, which React reports as
    // "Cannot update a component while rendering a different component".
    // A microtask runs as soon as the current synchronous render work
    // finishes, so the indicator still updates before paint.
    const snapshot = lastCounts;
    queueMicrotask(() => {
      for (const fn of countListeners) fn(snapshot);
    });
  }
  if (warned) return;
  warned = true;
  // PHASE 3A FINAL CLOSEOUT: literal strings updated to match the current
  // production-facing labels (not imported from globeData.js — that module
  // already imports FROM this one, and a back-import would create a cycle).
  console.warn(
    `[CineGlobe] GLOBE VISUAL FIXTURE ACTIVE — ${FIXTURE_DISCLOSURE} ` +
      `Counts: Recommended ${counts.gold}, Alternatives ${counts.jade}, ` +
      `Co-Production Opportunities ${counts.amber}, Excluded ${counts.silver}.`,
  );
}

export function getFixtureCounts() {
  return lastCounts;
}

export function subscribeFixtureCounts(fn) {
  countListeners.add(fn);
  if (lastCounts) fn(lastCounts);
  return () => countListeners.delete(fn);
}

// Read-only count of what the fixture WOULD assign, for the dev diagnostic
// panel and for the regression checks. Takes the live status map so it
// reports what is actually on screen, not what the lists hope for.
export function fixtureCounts(statuses) {
  const counts = { gold: 0, jade: 0, amber: 0, silver: 0 };
  if (!statuses) return counts;
  for (const [, entry] of statuses) {
    if (counts[entry.status] != null) counts[entry.status] += 1;
  }
  return counts;
}
