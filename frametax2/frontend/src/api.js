// Thin fetch wrapper over the CineGlobe API (app/api/v1/cineglobe.py).
// No business logic here — every value displayed by the app comes from
// this backend call, never computed client-side.

const API_BASE = "http://127.0.0.1:8000/api/v1/cineglobe";

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
