// Leaf module: jurisdiction code -> Globe key helpers. Moved out of globeData.js (2026-10-08, re-exported there unchanged) so the
// structure-topology module can use them without an import cycle.
// A jurisdiction code's country-level ISO2 — sub-national codes (US-CA,
// CA-BC, AU-NSW, ...) map to their parent country; country-level codes
// (MU, GR, ...) are already ISO2.
export function countryCode(jurisdictionCode) {
  return (jurisdictionCode || "").split("-")[0];
}

// Countries whose sub-national jurisdictions are the real production
// decision unit — a producer shoots in Georgia or British Columbia, not in
// "the United States". For US/CA specifically, the Globe also renders real
// admin-1 polygons (public/geo/admin1-us-ca.geojson) and the country-level
// polygon is suppressed entirely (Globe3D's own SUBNATIONAL_COUNTRY_ISOS —
// a separate, geometry-loading-time constant), so status is never averaged
// across 50 states.
//
// SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): AU added — confirmed live
// (all four acceptance productions) that best_per_jurisdiction genuinely
// carries a country-level "AU" winner AND real distinct "AU-NSW"/"AU-QLD"/
// "AU-SA" winners simultaneously, all four coexisting. Before this,
// globeKey() folded all four onto the single "AU" bucket — buildCountryStatuses'
// upsert() kept only whichever had the highest STATUS_RANK as `best`, so the
// other three real winners had no marker, no hover, and no click target
// anywhere on the Globe (only reachable via the side list's own admissibleForMode
// pool, which never collapses). No admin1 geojson exists for Australian
// states (unlike US/CA) — the AU country polygon is NOT dropped from the
// world set and keeps rendering its own real "AU" winner's colour; AU-NSW/
// AU-QLD/AU-SA get their own real, already-defined JURISDICTION_COORDS
// marker points (Sydney/Brisbane/Adelaide) with no additional polygon
// subdivision, which is the documented, acceptable degradation ("polygon/
// highlight layer where matching geometry exists") — never a reason to
// collapse their marker/hover/click identity back into the country's.
export const SUBNATIONAL_COUNTRIES = new Set(["US", "CA", "AU"]);

// Jurisdiction codes with no admin-1 polygon of their own but a real
// country-level polygon in the world set — Natural Earth models Puerto
// Rico as its own country entity rather than a US state.
const GLOBE_KEY_OVERRIDES = { "US-PR": "PR" };

// The key a jurisdiction code renders under on the Globe: the full
// sub-national code for US/CA (matching admin-1 `iso_3166_2`), otherwise
// the parent ISO2 country code (matching world-110m `ISO_A2`).
export function globeKey(jurisdictionCode) {
  const code = jurisdictionCode || "";
  if (GLOBE_KEY_OVERRIDES[code]) return GLOBE_KEY_OVERRIDES[code];
  const parent = countryCode(code);
  if (SUBNATIONAL_COUNTRIES.has(parent) && code.includes("-")) return code;
  return parent;
}

