// Phase 3B Batch 1 — category-state diff engine. Produces transition
// information ONLY: {iso, prevCategory, currCategory} for jurisdictions
// whose semantic category actually changed since the last snapshot. NOTHING
// in this file animates, renders, or touches the Globe's visual output —
// later Phase 3B batches consume this data to drive one-time signals; this
// batch only establishes it.
//
// "Survives refresh": category history is a real state, not a render
// artifact — a page reload must not read every jurisdiction as "newly
// changed" just because in-memory state reset. Persisted to localStorage,
// same pattern already used for theme (lib/theme.js) and fixture
// activation (lib/globeVisualFixture.js). Keyed per production so two
// productions' histories never collide or leak into each other.
//
// "No false positives": a jurisdiction with NO prior snapshot entry is
// FIRST OBSERVATION, not a change — diffCategories only reports isos present
// in BOTH the previous and current snapshot with a different value.

const STORAGE_PREFIX = "cineglobe.globeCategoryHistory.";

function storageKey(productionId) {
  return `${STORAGE_PREFIX}${productionId || "default"}`;
}

export function loadCategorySnapshot(productionId) {
  try {
    const raw = localStorage.getItem(storageKey(productionId));
    if (!raw) return new Map();
    const parsed = JSON.parse(raw);
    return new Map(Object.entries(parsed));
  } catch {
    // Corrupt/unavailable storage is treated as "no prior snapshot" —
    // never throws, never blocks rendering.
    return new Map();
  }
}

export function saveCategorySnapshot(productionId, statusByIso) {
  try {
    const obj = Object.fromEntries(statusByIso);
    localStorage.setItem(storageKey(productionId), JSON.stringify(obj));
  } catch {
    // Storage unavailable (private browsing, quota) — snapshotting is a
    // convenience for future animation batches, not required for the
    // Globe to render correctly, so this fails silently.
  }
}

// Pure diff: no I/O, easily unit-tested. `prevSnapshot` and `currStatuses`
// are both Map<iso, categoryKey> ("gold"/"jade"/"amber"/"silver").
export function diffCategories(prevSnapshot, currStatuses) {
  const changes = [];
  for (const [iso, currCategory] of currStatuses) {
    if (!prevSnapshot.has(iso)) continue; // first observation, not a change
    const prevCategory = prevSnapshot.get(iso);
    if (prevCategory !== currCategory) {
      changes.push({ iso, prevCategory, currCategory });
    }
  }
  return changes;
}
