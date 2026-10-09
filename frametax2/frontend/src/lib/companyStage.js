// Company Globe colour = PRODUCTION STAGE, from the existing PROJECT_STATUSES definitions and the existing canonical stage
// tokens the lifecycle UI already uses (Library stage dot, status badges): evaluation --blue, development --silver,
// production --gold, completed --jade (archived --charcoal, never active). Tokens are read from the live theme, so the
// legend, side list, territories, markers, routes and labels all follow the same token.
import { PROJECT_STATUSES } from "./useProjectStatus";
import { libraryStageKey } from "./libraryStatus";

const TIER_TOKEN = { blue: "--blue", silver: "--silver", gold: "--gold", jade: "--jade", charcoal: "--charcoal" };
const FALLBACK = { blue: "#2C5580", silver: "#6B6860", gold: "#A17A2E", jade: "#2E6B4E", charcoal: "#A6A296" };

export const tokenHex = (tier) => {
  const css = typeof document !== "undefined" ? getComputedStyle(document.documentElement).getPropertyValue(TIER_TOKEN[tier]).trim() : "";
  return css || FALLBACK[tier] || "#8c96a4";
};

// Archived projects are not active (never on the Company Globe), so the legend lists the four active stages.
export const activeStages = () => PROJECT_STATUSES.filter((s) => s.key !== "archived").map((s) => ({ key: s.key, label: s.label, hex: tokenHex(s.tier) }));

export function stageOf(project) {
  const key = libraryStageKey(project);
  const meta = PROJECT_STATUSES.find((s) => s.key === key) || PROJECT_STATUSES[0];
  return { key: meta.key, label: meta.label, hex: tokenHex(meta.tier) };
}

// Re-render signal for the app theme switch (the tokens change with it).
export const themeKey = () => (typeof document !== "undefined" ? document.documentElement.getAttribute("data-theme") || "day" : "day");
