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

// Activation. `VITE_GLOBE_VISUAL_FIXTURE=true` is the documented method (a
// .env.local line, or inline for one run:
//   VITE_GLOBE_VISUAL_FIXTURE=true npm run dev
// ). The `?globeFixture=1` query parameter is a convenience for driving a
// running dev server from a test harness and is DEV-ONLY.
export function isFixtureActive() {
  try {
    if (import.meta.env?.VITE_GLOBE_VISUAL_FIXTURE === "true") return true;
    if (
      import.meta.env?.DEV &&
      typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).get("globeFixture") === "1"
    ) {
      return true;
    }
  } catch {
    /* import.meta.env unavailable (non-Vite consumer) — stay disabled */
  }
  return false;
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

// Loud, once, in the console as well as on screen: anyone reading a screenshot
// or a console log must know these are not real optimizer conclusions.
export function noteFixtureCounts(counts) {
  if (warned) return;
  warned = true;
  console.warn(
    `[CineGlobe] GLOBE VISUAL FIXTURE ACTIVE — ${FIXTURE_DISCLOSURE} ` +
      `Counts: Recommended ${counts.gold}, Optimized alternative ${counts.jade}, ` +
      `Unlockable opportunity ${counts.amber}, Additional ${counts.silver}.`,
  );
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
