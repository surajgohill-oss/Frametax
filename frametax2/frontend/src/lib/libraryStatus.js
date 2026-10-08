// PROJECT LIBRARY STAGE (2026-10-08). The persisted owner is Project.lifecycle (EVALUATION -> DEVELOPMENT -> PRODUCTION
// -> COMPLETED -> ARCHIVED, see useProjectStatus.js). "Submitted" is not a stored stage: it is an Evaluation-lifecycle
// project the backend does not yet serve a COMPLETE, CURRENT canonical generation for (`is_served_production`, the same
// predicate every current-evaluation reader uses). Derived, never hardcoded per title/id; the Library and Company Globe
// only read the list endpoint and never evaluate.
export function libraryStageKey(project) {
  const key = (project?.lifecycle || "evaluation").toLowerCase();
  return key === "evaluation" && !project?.is_served_production ? "submitted" : key;
}

export function libraryStageLabel(project, meta) {
  return meta.key === "evaluation" && !project?.is_served_production ? "Submitted" : meta.label;
}

// Active = Evaluation and every later workflow stage; Submitted (not yet evaluated) and Archived (closed) are not.
export const isActiveProject = (project) => {
  const key = libraryStageKey(project);
  return key !== "submitted" && key !== "archived";
};

// Filter ids: "active" (default), "submitted", "all", plus the established per-stage ids (evaluation = evaluated only).
export const libraryFilterMatches = (filter, project) => {
  if (filter === "all") return true;
  if (filter === "active") return isActiveProject(project);
  return libraryStageKey(project) === filter;
};

const FILTER_KEY = "cineglobe:library-filter";
export function readLibraryFilter() {
  try { return sessionStorage.getItem(FILTER_KEY) || "active"; } catch { return "active"; }
}
export function writeLibraryFilter(filter) {
  try { sessionStorage.setItem(FILTER_KEY, filter); } catch { /* storage unavailable: filter just resets */ }
}
