// Groups the real Little Utopia account register (pkg.register — 44 real
// account-code lines from the parsed Movie Magic budget, each with its own
// qualification state, confidence, and reason) into named Model Rail blocks.
//
// Account codes here are the REAL parsed budget's 4-digit chart-of-accounts
// codes (app.data.little_utopia_real_budget.LITTLE_UTOPIA_REAL_BUDGET_LINES:
// "1000".."8300") — NOT the earlier sanitized-fixture "10-00" scheme this
// file used before the backend moved to the real document. Every account
// code appears in exactly one block below; the mapping was verified against
// the live /package.register account codes at runtime.
const BLOCK_DEFS = [
  { key: "atl", label: "Above the line", codes: ["1000", "1100", "1200", "1300", "1400"] },
  { key: "crew", label: "Production crew", codes: ["2000", "2100", "2800", "2900", "3200"] },
  { key: "art", label: "Art & set", codes: ["2200", "2300", "2400", "2500", "2600", "2700"] },
  { key: "camera", label: "Camera & electrical", codes: ["3000", "3100", "3500", "3800"] },
  { key: "locations", label: "Locations & facilities", codes: ["3400", "3700"] },
  { key: "marine", label: "Marine & special production", codes: ["3300", "4000"] },
  { key: "transport", label: "Transportation", codes: ["3600"] },
  { key: "travel", label: "Travel & living", codes: ["1600", "3900"] },
  { key: "post", label: "Post", codes: ["5000", "5100", "5200", "5300", "5400", "5500"] },
  { key: "music", label: "Music", codes: ["6000"] },
  { key: "vfx", label: "VFX", codes: ["6100"] },
  { key: "admin", label: "Administration & legal", codes: ["6500", "7000", "7800"] },
  { key: "publicity", label: "Publicity & marketing", codes: ["7100", "7300"] },
  { key: "insurance", label: "Insurance & completion bond", codes: ["7200", "8100", "8200"] },
  { key: "contingency", label: "Contingency", codes: ["8300"] },
];

const MOVABLE_STATES = new Set(["structuring_opportunity"]);
const FIXED_HINT_WORDS = ["mauritius", "marine", "location", "special effects"];

function movement(account) {
  if (MOVABLE_STATES.has(account.state)) return "movable";
  const desc = account.description.toLowerCase();
  if (FIXED_HINT_WORDS.some((w) => desc.includes(w))) return "fixed";
  return "unclassified";
}

function lineFrom(a) {
  return {
    key: a.account_code,
    code: a.account_code,
    label: a.description,
    amount: a.amount_usd,
    state: a.state,
    confidence: a.confidence,
    reason: a.reason,
    authorityBasis: a.authority_basis,
    greyReason: a.grey_reason,
    resolvingEvidence: a.resolving_evidence,
    incentiveUpsideUsd: a.incentive_upside_usd,
    movement: movement(a),
  };
}

/**
 * Builds Model Rail blocks from the real per-account register. Each
 * account keeps its own real qualification state, confidence, and
 * reason — nothing here is aggregated away, only grouped for display.
 * Any account code present in the register but not in BLOCK_DEFS lands
 * in a trailing "Other" block rather than silently disappearing.
 */
export function buildAccountBlocks(register) {
  const byCode = Object.fromEntries(register.map((a) => [a.account_code, a]));
  const claimed = new Set();
  const blocks = BLOCK_DEFS.map((def) => {
    const lines = def.codes
      .map((code) => byCode[code])
      .filter(Boolean)
      .map((a) => { claimed.add(a.account_code); return lineFrom(a); })
      .sort((a, b) => b.amount - a.amount);
    const amount = lines.reduce((sum, l) => sum + l.amount, 0);
    return { ...def, lines, amount };
  }).filter((b) => b.lines.length > 0);

  const unclaimed = register.filter((a) => !claimed.has(a.account_code));
  if (unclaimed.length > 0) {
    const lines = unclaimed.map(lineFrom).sort((a, b) => b.amount - a.amount);
    blocks.push({
      key: "other", label: "Other", codes: unclaimed.map((a) => a.account_code),
      lines, amount: lines.reduce((sum, l) => sum + l.amount, 0),
    });
  }
  return blocks;
}
