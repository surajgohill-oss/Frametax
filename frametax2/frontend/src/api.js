// Thin fetch wrapper over the CineGlobe API (app/api/v1/cineglobe.py).
// No business logic here — every value displayed by the app comes from
// this backend call, never computed client-side.

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010/api/v1/cineglobe";
// /documents lives on a sibling router (app/api/v1/documents.py), not under
// the /cineglobe prefix — same host, different top-level path.
const DOCUMENTS_BASE = API_BASE.replace(/\/cineglobe$/, "/documents");

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
