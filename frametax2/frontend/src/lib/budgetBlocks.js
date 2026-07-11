// Groups the real Little Utopia account register (pkg.register — 41
// real account-code lines, each with its own qualification state,
// confidence, and reason) into named Model Rail blocks. Every account
// code appears in exactly one block below; the mapping was verified by
// summing every block against the backend's own total_budget_usd until
// they matched exactly (see PR notes) — this is a display grouping over
// real account codes, not a new financial calculation.
const BLOCK_DEFS = [
  { key: "atl", label: "Above the line", codes: ["10-00", "11-00", "12-00"] },
  { key: "cast", label: "Cast", codes: ["13-00"] },
  {
    key: "crew", label: "Production crew",
    codes: ["20-00", "21-00", "23-00", "24-00", "25-00", "26-00", "27-00", "28-00", "40-00", "41-00", "43-00"],
  },
  { key: "locations", label: "Locations", codes: ["29-00"] },
  { key: "equipment", label: "Equipment", codes: ["22-00"] },
  { key: "travel", label: "Travel & living", codes: ["30-00", "36-00", "37-00", "38-00", "39-00"] },
  { key: "marine", label: "Marine & special production", codes: ["31-00", "32-00", "33-00", "34-00", "35-00", "42-00"] },
  { key: "post", label: "Post", codes: ["50-00", "51-00", "52-00", "55-00"] },
  { key: "vfx", label: "VFX", codes: ["54-00"] },
  { key: "music", label: "Music", codes: ["53-00"] },
  { key: "financing", label: "Financing", codes: ["60-00", "70-00", "71-00", "82-00"] },
  { key: "contingency", label: "Contingency", codes: ["80-00", "81-00"] },
  { key: "inkind", label: "In-kind / off-budget", codes: ["44-00"] },
];

const MOVABLE_STATES = new Set(["structuring_opportunity"]);
const FIXED_HINT_WORDS = ["mauritius", "marine", "location"];

function movement(account) {
  if (MOVABLE_STATES.has(account.state)) return "movable";
  const desc = account.description.toLowerCase();
  if (FIXED_HINT_WORDS.some((w) => desc.includes(w))) return "fixed";
  return "unclassified";
}

/**
 * Builds Model Rail blocks from the real per-account register. Each
 * account keeps its own real qualification state, confidence, and
 * reason — nothing here is aggregated away, only grouped for display.
 */
export function buildAccountBlocks(register) {
  const byCode = Object.fromEntries(register.map((a) => [a.account_code, a]));
  return BLOCK_DEFS.map((def) => {
    const lines = def.codes
      .map((code) => byCode[code])
      .filter(Boolean)
      .map((a) => ({
        key: a.account_code,
        code: a.account_code,
        label: a.description,
        amount: a.amount_usd,
        state: a.state,
        confidence: a.confidence,
        reason: a.reason,
        resolvingEvidence: a.resolving_evidence,
        incentiveUpsideUsd: a.incentive_upside_usd,
        movement: movement(a),
      }))
      .sort((a, b) => b.amount - a.amount);
    const amount = lines.reduce((sum, l) => sum + l.amount, 0);
    return { ...def, lines, amount };
  }).filter((b) => b.lines.length > 0);
}
