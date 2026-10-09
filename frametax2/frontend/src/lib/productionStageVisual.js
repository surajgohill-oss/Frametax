// CANONICAL PRODUCTION-STAGE VISUAL MAPPING (approved lifecycle colour story). One table, reusable by Company Globe now and by
// Today / Library / the hero in their later UI pass. Deliberately NOT derived from the generic blue/silver/gold/jade tiers.
//   evaluation  cool analytical blue
//   development warm development yellow
//   production  active production green
//   completed   pale yellow-green celadon, with a restrained check
//   archived    quiet graphite (never active, so never on the Company Globe legend)
export const STAGE_VISUAL = {
  evaluation: { key: "evaluation", label: "Evaluation", hex: "#5E86B2", check: false },
  development: { key: "development", label: "Development", hex: "#D4A63F", check: false },
  production: { key: "production", label: "Production", hex: "#3F9A68", check: false },
  completed: { key: "completed", label: "Completed", hex: "#B8C96A", check: true },
  archived: { key: "archived", label: "Archived", hex: "#68717C", check: false },
};
export const ACTIVE_STAGE_ORDER = ["evaluation", "development", "production", "completed"];
export const stageVisual = (key) => STAGE_VISUAL[key] || STAGE_VISUAL.evaluation;
export const activeStageVisuals = () => ACTIVE_STAGE_ORDER.map((k) => STAGE_VISUAL[k]);
