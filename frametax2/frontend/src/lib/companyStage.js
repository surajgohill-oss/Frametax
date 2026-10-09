// Company Globe colour = PRODUCTION STAGE, from the existing PROJECT_STATUSES definitions and the existing stage tokens
// (evaluation blue, development silver, production gold, completed jade, archived charcoal). The globe body is dark glass in
// BOTH app themes, so the stage tokens' dark-ground values (tokens.css :root[data-theme="night"]) are used on it; the day-theme
// token values are dark inks that disappear into the graphite land. These are the same tokens, not new colours.
import { PROJECT_STATUSES } from "./useProjectStatus";
import { libraryStageKey } from "./libraryStatus";

export const STAGE_GLOBE_HEX = { blue: "#6FA0D6", silver: "#AFB6C2", gold: "#E8C273", jade: "#5FBF92", charcoal: "#6E7681" };

// Archived projects are not active (never on the Company Globe), so the legend lists the active stages only.
export const ACTIVE_STAGES = PROJECT_STATUSES.filter((s) => s.key !== "archived").map((s) => ({ key: s.key, label: s.label, hex: STAGE_GLOBE_HEX[s.tier] }));

export function stageOf(project) {
  const key = libraryStageKey(project);
  const meta = PROJECT_STATUSES.find((s) => s.key === key) || PROJECT_STATUSES[0];
  return { key: meta.key, label: meta.label, hex: STAGE_GLOBE_HEX[meta.tier] };
}
