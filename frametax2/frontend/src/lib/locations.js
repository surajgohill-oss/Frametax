// Explicit production locations (NA-RECONCILIATION-24): pure form logic over the served view `production.shoot_locations`.
// Locality is never inferred from a jurisdiction: a location is a row the producer enters (name, jurisdiction, city, county, days, role) plus classifications the system cannot derive yet, each with its source.
// Unknown (blank) is distinct from zero days and from a verified non-qualifying location. Derived classifications (a dataset lookup, an authority determination) are read-only and shown apart from producer-supplied ones.

export const ROLES = [["SELECTED", "Selected planning location"], ["SCHEDULE", "Retained schedule location"]];
export const METHODS = [["PRODUCER_ASSERTED", "Producer-asserted"], ["PRODUCER_MEASURED", "Producer-measured"], ["AUTHORITY_DETERMINATION", "Authority determination"]];
export const CONFIDENCES = [["STATED", "Stated"], ["MEASURED", "Measured"], ["AUTHORITATIVE", "Authoritative"]];
export const BC_ZONES = [["vancouver", "Designated Vancouver area"], ["regional", "Outside it, regional"], ["distant", "Distant location"]];

// the classification inputs a producer may supply, by jurisdiction (only those the engine reads for that jurisdiction)
export const CLASSIFICATIONS = {
  "US-MO": [{ name: "rural_or_blighted", label: "Rural or blighted area", kind: "boolean" }],
  "CA-BC": [{ name: "bc_regional_district", label: "Regional district", kind: "text" }, { name: "bc_municipality", label: "Municipality", kind: "text" }, { name: "bc_zone", label: "Zone (inside Metro Vancouver)", kind: "zone" }],
  "CA-NS": [{ name: "ns_distance_km", label: "Driving distance from Halifax City Hall (km)", kind: "number" }],
  "CA-NB": [{ name: "nb_distance_km", label: "Distance from the nearest NB city hall (km)", kind: "number" }],
  "CA-SK": [{ name: "sk_distance_km", label: "Distance from Regina or Saskatoon (km)", kind: "number" }],
};
const DERIVED_METHODS = new Set(["DATASET_LOOKUP", "AUTHORITY_DETERMINATION", "COMPUTED_DISTANCE"]);
export const isDerivedMethod = (m) => DERIVED_METHODS.has(m);
export const methodLabel = (m) => ({ DATASET_LOOKUP: "Official dataset", COMPUTED_DISTANCE: "Computed lower bound", AUTHORITY_DETERMINATION: "Authority determination", PRODUCER_ASSERTED: "Producer-supplied", PRODUCER_MEASURED: "Producer-supplied (measured)" })[m] ?? "Unknown";

// jurisdiction code of a program slug: us_mo_... -> US-MO, ca_bc_... -> CA-BC (the engine's own convention)
export function jurisdictionOf(slug) {
  const m = /^(us|ca)_([a-z]{2})_/.exec(slug || "");
  return m ? `${m[1].toUpperCase()}-${m[2].toUpperCase()}` : null;
}
export const jurisdictionsOf = (programs) => [...new Set((programs ?? []).map(jurisdictionOf).filter((j) => j && CLASSIFICATIONS[j]))];

const blank = (v) => v === null || v === undefined || String(v).trim() === "";
let seq = 0;
export const newId = () => `loc${Date.now().toString(36)}${(seq += 1)}`;

// a persisted location -> an editable draft (strings only; blank = Unknown)
export function draftFromLocation(l) {
  const attrs = {};
  for (const [k, v] of Object.entries(l.attributes ?? {})) attrs[k] = typeof v === "boolean" ? (v ? "yes" : "no") : String(v);
  const ev = Object.values(l.evidence ?? {})[0] ?? {};
  return {
    id: l.id, label: l.label ?? "", jurisdiction_code: l.jurisdiction_code, role: l.role ?? "SELECTED", city: l.city ?? "", county: l.county ?? "", days: l.days === null || l.days === undefined ? "" : String(l.days),
    attrs, source: ev.source ?? "", method: ev.method ?? "PRODUCER_ASSERTED", confidence: ev.confidence ?? "STATED", version: ev.version ?? "", effective_date: ev.effective_date ?? "",
  };
}

export const draftsFrom = (view) => (view?.locations ?? []).map(draftFromLocation);

export function blankDraft(jurisdiction_code) {
  return { id: newId(), label: "", jurisdiction_code, role: "SELECTED", city: "", county: "", days: "", attrs: {}, source: "", method: "PRODUCER_ASSERTED", confidence: "STATED", version: "", effective_date: "" };
}

function parseAttr(spec, text) {
  if (blank(text)) return { unknown: true };
  if (spec.kind === "boolean") return text === "yes" ? { value: true } : text === "no" ? { value: false } : { unknown: true };
  if (spec.kind === "number") {
    const t = String(text).trim();
    if (!/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(t)) return { error: "Enter a number" };
    const n = Number(t);
    return n >= 0 && n <= 5000 ? { value: n } : { error: "Between 0 and 5000" };
  }
  return { value: String(text).trim() };
}

const norm = (v) => String(v ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
export const identityOf = (d) => [d.jurisdiction_code, d.role, norm(d.city), norm(d.county), norm(d.label)].join("|");

// SELECTED planning locations supersede the SCHEDULE locations of the same jurisdiction: a jurisdiction's days are never counted twice
export function effectiveDrafts(drafts) {
  const selected = new Set(drafts.filter((d) => d.role === "SELECTED").map((d) => d.jurisdiction_code));
  return drafts.filter((d) => d.role === "SELECTED" || !selected.has(d.jurisdiction_code));
}

export function usedDays(drafts) {
  return effectiveDrafts(drafts).reduce((n, d) => n + (blank(d.days) ? 0 : Number(d.days) || 0), 0);
}

// errors keyed by draft id (and "_all" for the conservation check); an empty object means the list can be saved
export function validateDrafts(drafts, totalDays) {
  const errors = {};
  const add = (id, key, msg) => { (errors[id] ??= {})[key] = msg; };
  const seen = new Map();
  for (const d of drafts) {
    if (blank(d.label)) add(d.id, "label", "Name the location");
    if (!/^[A-Z]{2}(-[A-Z0-9]{1,4})?$/.test(d.jurisdiction_code || "")) add(d.id, "jurisdiction_code", "Choose the jurisdiction");
    if (!blank(d.days)) {
      const n = Number(d.days);
      if (!/^\d+$/.test(String(d.days).trim()) || n > 2000) add(d.id, "days", "Whole days between 0 and 2000");
    }
    const key = identityOf(d);
    if (seen.has(key)) { add(d.id, "label", "The same place is already listed in this role: its days would be counted twice"); }
    seen.set(key, d.id);
    let supplied = 0;
    for (const spec of CLASSIFICATIONS[d.jurisdiction_code] ?? []) {
      const p = parseAttr(spec, d.attrs[spec.name]);
      if (p.error) add(d.id, spec.name, p.error);
      else if (!p.unknown) supplied += 1;
    }
    if (supplied && blank(d.source)) add(d.id, "source", "Name the source of the classification you supplied");
  }
  if (totalDays !== null && totalDays !== undefined && usedDays(drafts) > totalDays) {
    (errors._all ??= {}).days = `The locations carry ${usedDays(drafts)} shooting days, more than the shoot total of ${totalDays}`;
  }
  return errors;
}

export const hasErrors = (errors) => Object.keys(errors).length > 0;

// persisted payload: only supplied classifications are sent, each with the entry's source block; blank days stay null (Unknown)
export function payloadFrom(drafts) {
  return drafts.map((d) => {
    const attributes = {};
    const evidence = {};
    for (const spec of CLASSIFICATIONS[d.jurisdiction_code] ?? []) {
      const p = parseAttr(spec, d.attrs[spec.name]);
      if (p.unknown || p.error) continue;
      attributes[spec.name] = p.value;
      evidence[spec.name] = { source: d.source.trim(), method: d.method, confidence: d.confidence, ...(blank(d.version) ? {} : { version: d.version }), ...(blank(d.effective_date) ? {} : { effective_date: d.effective_date }) };
    }
    return {
      id: d.id, label: d.label.trim(), jurisdiction_code: d.jurisdiction_code, role: d.role, city: blank(d.city) ? null : d.city.trim(), county: blank(d.county) ? null : d.county.trim(),
      days: blank(d.days) ? null : Number(d.days), attributes, evidence,
    };
  });
}

export const isDirty = (drafts, view) => JSON.stringify(payloadFrom(drafts)) !== JSON.stringify(payloadFrom(draftsFrom(view)));

// Reset: remove the producer-supplied classifications (and their source) from one location, returning it to derived evidence / Unknown
export function resetProducerClassifications(d) {
  return { ...d, attrs: {}, source: "", version: "", effective_date: "" };
}

// the classifications the system derived or that an authority determined: read-only rows with provenance
export function derivedRows(location) {
  return Object.entries(location.classifications ?? {}).filter(([, v]) => isDerivedMethod(v.method)).map(([k, v]) => ({ key: k, value: v.value, source: v.source, method: v.method, version: v.version, confidence: v.confidence }));
}
export function suppliedRows(location) {
  return Object.entries(location.classifications ?? {}).filter(([, v]) => !isDerivedMethod(v.method)).map(([k, v]) => ({ key: k, value: v.value, source: v.source, method: v.method, version: v.version, confidence: v.confidence }));
}

// aggregate pricing consequences of the effective locations for the selected programs (served `pricing_effects`)
export function consequencesFor(view, programs) {
  const set = new Set(programs ?? []);
  return (view?.pricing_effects ?? []).map((p) => ({ ...p, effects: p.effects.filter((e) => set.has(e.program)) })).filter((p) => p.effects.length);
}
export const STATE_TEXT = { MET: "Met", NOT_MET: "Not met", PARTIAL: "Partly met", UNKNOWN: "Unknown" };
