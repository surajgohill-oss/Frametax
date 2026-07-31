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
export function programDisplay(slug) {
  if (!slug) return null;
  return PROGRAM_NAMES[slug] || humanizeToken(slug);
}
