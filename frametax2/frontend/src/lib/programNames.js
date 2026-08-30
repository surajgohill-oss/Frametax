// Pure string helpers, deliberately kept out of format.jsx (which contains
// real JSX) — globeData.js needs `programDisplay` for the Globe hover card,
// and globeData.js is imported directly by `node --test` under plain Node
// ESM (no JSX transform), so anything it imports must parse as plain
// JavaScript. format.jsx re-exports both names unchanged, so every existing
// caller (`from "../lib/format"`) keeps working with no import-site changes.

// Formats a raw snake_case engine/module name for secondary metadata —
// e.g. "production_recommendation_engine" -> "Production recommendation".
// Pure string formatting, never invents which engines are affected.
export function humanizeToken(token) {
  if (!token) return "";
  const words = token.replace(/_/g, " ").replace(/\b(engine|model|discovery)\b/g, "").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

// Producer-facing incentive-program names — the frozen artifact's
// terminology contract (ui-baseline-v1) for the four executable programs.
// Presentation vocabulary only: never a rate, cap, or economic value.
// Unknown slugs fall back to plain humanization, never invented names.
const PROGRAM_NAMES = {
  mu_edb_incentive: "EDB Film Rebate",
  mt_mfc_rebate: "Malta Cash Rebate",
  ie_section_481: "Section 481",
  gr_cash_rebate: "Greece Cash Rebate",
};
// preferredName: the real canonical program name when the caller has one
// (structure.program_display_name, sourced from the backend's own
// executable_jurisdiction_registry doctrine — never a frontend map).
// Takes priority over the legacy hardcoded PROGRAM_NAMES table, which
// stays only as a fallback for the four original programs and for any
// older served row that predates the backend field.
export function programDisplay(slug, preferredName) {
  if (preferredName) return preferredName;
  if (!slug) return null;
  return PROGRAM_NAMES[slug] || humanizeToken(slug);
}
