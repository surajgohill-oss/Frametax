// PROJECT LIBRARY EVALUATION STATUS (2026-10-01): a project in the Evaluation lifecycle stage reads
// "Evaluated" only when the backend serves a COMPLETE, CURRENT canonical generation for it
// (`is_served_production`: current engine_version + freshly recomputed input fingerprint, the same
// predicate every other current-evaluation reader uses); otherwise it reads "Submitted". Derived,
// never hardcoded per title/id; the Library only reads the list endpoint and never evaluates.
export function libraryStageLabel(project, meta) {
  if (meta.key !== "evaluation") return meta.label;
  return project.is_served_production ? "Evaluated" : "Submitted";
}
