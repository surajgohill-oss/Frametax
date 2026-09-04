// Thin fetch wrapper over the CineGlobe API (app/api/v1/cineglobe.py).
// No business logic here — every value displayed by the app comes from
// this backend call, never computed client-side.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010/api/v1/cineglobe";
// /documents and /projects live on sibling routers (app/api/v1/documents.py,
// app/api/v1/projects.py), not under the /cineglobe prefix — same host,
// different top-level path.
const DOCUMENTS_BASE = API_BASE.replace(/\/cineglobe$/, "/documents");
const PROJECTS_BASE = API_BASE.replace(/\/cineglobe$/, "/projects");
const ORGANIZATIONS_BASE = API_BASE.replace(/\/cineglobe$/, "/organizations");
const INGESTION_BASE = API_BASE.replace(/\/cineglobe$/, "/ingestion");

// The backend's own origin (frontend dev server runs on a different
// port) — endpoints that return a path rather than a full URL (project
// artwork, document version files) need this prefixed before use in an
// <img src> or <a href>, or the browser resolves them against the
// frontend's own origin instead.
export const API_ORIGIN = new URL(API_BASE).origin;

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export const getProduction = () => request("/production");
export const getPackage = () => request("/package");
export const getRecommendations = () => request("/recommendations");
export const getStructures = () => request("/structures");
export const getLegal = () => request("/legal");

// Mature UI restoration — the one project-parameterized combined state
// (app/api/v1/cineglobe.py::get_project_state) behind useCineGlobe(projectId).
// Little Utopia's own project_id returns byte-identical data to the 8 calls
// above; any other project returns the canonical, generic adapter's data.
export const getProjectState = (projectId) => request(`/projects/${projectId}/state`);
export const checkConstraints = () => request("/constraints/check");
export const postScenario = (kind, targetJurisdiction) =>
  request("/scenarios", {
    method: "POST",
    body: JSON.stringify({ kind, target_jurisdiction: targetJurisdiction || null }),
  });

// Production economics — floor/ceiling cases, financing, in-kind, travel/FX
// normalization, alternative-jurisdiction comparison, available funds,
// structuring advisory. Never fetched by the frontend before this change.
export const getEconomics = () => request("/economics");
export const postEconomicsControls = (controls) =>
  request("/economics/controls", { method: "POST", body: JSON.stringify(controls) });

// People — writer/director/cast/producer nationality + residency, each
// independently known/unknown.
export const getPeople = () => request("/people");
export const postPeople = (answers) =>
  request("/people", { method: "POST", body: JSON.stringify({ answers }) });
// Project-scoped counterpart (Production Overview Truthfulness): the
// legacy /people write above resolves the single in-memory demo engine's
// project, not whichever project the caller is actually viewing. Every
// project-scoped Overview screen must save through this one instead.
export const postProjectPeople = (projectId, answers) =>
  request(`/projects/${projectId}/people`, { method: "POST", body: JSON.stringify({ answers }) });

// Production Page Integrity: generic producer-controlled project
// assumptions (currently: contingency_expected_utilization_pct) — the
// SAME real ProjectFact write path as postProjectPeople above, just a
// different whitelisted key set. See app/api/v1/cineglobe.py
// post_project_assumptions. A value of null deletes that fact's row.
export const postProjectAssumptions = (projectId, answers) =>
  request(`/projects/${projectId}/assumptions`, { method: "POST", body: JSON.stringify({ answers }) });

// Batched producer-control closeout (2026-09-03) — generic PROJECT-LEVEL
// candidate-jurisdiction inclusion/exclusion election (the SAME real
// ProjectFact write path as postProjectAssumptions above, a different
// whitelisted key shape). See app/api/v1/cineglobe.py
// post_jurisdiction_preference. Works for any jurisdiction code — never
// a Saudi-specific endpoint.
export const postJurisdictionPreference = (projectId, jurisdictionCode, included) =>
  request(`/projects/${projectId}/jurisdiction-preference`, {
    method: "POST",
    body: JSON.stringify({ jurisdiction_code: jurisdictionCode, included }),
  });

// Major-location categories — user-confirmed overrides over the
// script-derived seeds (canonical Production Record; effective values
// feed territory matching / recommendations, which recompute on write).
export const postLocations = (overrides) =>
  request("/locations", { method: "POST", body: JSON.stringify({ overrides }) });

// Production facts — payroll routing, post location, treaty election,
// component routing. Answering one invalidates the cached state; every
// downstream engine (qualification, treaty, structuring, allocation)
// recomputes on the next read.
export const getFacts = () => request("/facts");
export const postFacts = (answers) =>
  request("/facts", { method: "POST", body: JSON.stringify({ answers }) });

// Contingency treatment (Task 91) — undeployed reserve is excluded from
// QPE by default; deploying part of it to a real destination line makes
// that amount inherit the destination's own eligibility treatment. No
// blanket "qualify contingency" switch exists here or on the backend.
export const getContingency = () => request("/contingency");
export const postContingencyDeploy = (deployment) =>
  request("/contingency/deploy", { method: "POST", body: JSON.stringify(deployment) });
export const postContingencyReset = () =>
  request("/contingency/reset", { method: "POST" });

// Real document ingestion (app/api/v1/documents.py) — persists via
// SQLAlchemy to the documents table. The currently-served production state
// (little_utopia_state.py) is a static in-memory demo disconnected from
// that table, so an uploaded file will not appear anywhere in this
// workspace yet — the upload itself is real, not simulated.
export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${DOCUMENTS_BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

// Project Library Phase C — partial update of the real persistent Project
// row (app/models/project.py). Only lifecycle and leading_structure_id are
// wired today; both are user-driven writes, never inferred/triggered by
// this call itself.
export async function patchProject(projectId, changes) {
  const res = await fetch(`${PROJECTS_BASE}/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

// Project Library (Phase D) — every real persisted Project as a grid
// card (artwork + material completeness), the full Project Record for
// one project, and creation. All read the same real tables Phase C
// migrated into; no separate/duplicate project-summary store.
export const getProjects = () => request2(`${PROJECTS_BASE}`);
export const getProjectRecord = (projectId) => request2(`${PROJECTS_BASE}/${projectId}/record`);
export const getOrganizations = () => request2(`${ORGANIZATIONS_BASE}`);
export async function createProject(body) {
  const res = await fetch(PROJECTS_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${errBody}`);
  }
  return res.json();
}

// Thin GET helper for the non-/cineglobe bases above — same error
// convention as request(), just not hardcoded to API_BASE.
async function request2(url) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

// Generic JSON verb helper (POST/PATCH/DELETE) — same error convention,
// used by delete/set-master/ingestion below rather than repeating the
// fetch+error-check boilerplate at each call site.
async function verb(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${errBody}`);
  }
  return res.status === 204 ? null : res.json();
}

// Project deletion (Phase E) — permanent, cascades every record the
// Project owns. Confirmation is the CALLER's job (see the Project Record
// "Delete Project" dialog) — this is the raw operation.
export const deleteProject = (projectId) => verb("DELETE", `${PROJECTS_BASE}/${projectId}`);

// Artwork candidate master-selection (Phase E) — never deletes the
// previous master row, only flips which one is_master.
export const setMasterArtwork = (projectId, assetId) =>
  verb("POST", `${PROJECTS_BASE}/${projectId}/artwork/${assetId}/set-master`);

// Begin Evaluation — the canonical served evaluation runtime
// (app/services/canonical_evaluation.py): discovery -> qualification ->
// allocation -> pricing -> ProductionStructure/StructureCalculationResult,
// for any project. Idempotent per input fingerprint; safe to call again
// after a refresh.
export const beginEvaluation = (projectId) =>
  verb("POST", `${PROJECTS_BASE}/${projectId}/evaluation/begin`);

// Project Workspace — the view adapter (app/services/project_workspace_view.py)
// behind the generic Overview/World/Script/Budget pages. Read-only: never
// triggers evaluation, never computes economics — reshapes what
// beginEvaluation already persisted.
export const getProjectWorkspace = (projectId) => request2(`${PROJECTS_BASE}/${projectId}/workspace`);

// Ingestion (Phase E) — DISCOVER -> CLASSIFY -> ASSOCIATE -> STAGE ->
// REVIEW -> COMMIT. Nothing here is canonical until commitIngestionCandidate.
export const discoverIngestion = (sourcePointer, projectId) =>
  verb("POST", `${INGESTION_BASE}/discover`, { source_type: "local", source_pointer: sourcePointer, project_id: projectId || null });
export const listIngestionCandidates = (status = "pending") =>
  request2(`${INGESTION_BASE}/candidates?status=${encodeURIComponent(status)}`);
export const updateIngestionCandidate = (candidateId, changes) =>
  verb("PATCH", `${INGESTION_BASE}/candidates/${candidateId}`, changes);
export const commitIngestionCandidate = (candidateId) =>
  verb("POST", `${INGESTION_BASE}/candidates/${candidateId}/commit`);
export const ignoreIngestionCandidate = (candidateId) =>
  verb("POST", `${INGESTION_BASE}/candidates/${candidateId}/ignore`);
