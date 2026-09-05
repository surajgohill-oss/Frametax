// Hard Restore Frozen Project Globe: current-data compatibility adapter.
//
// bestPricedCandidate was added to lib/globeData.js AFTER the July 30
// freeze (1f98404) — restoring globeData.js to the frozen commit dropped
// it, breaking three callers outside the Globe subsystem itself
// (Overview.jsx, Workspace.jsx, shell/ProjectHeader.jsx) that use it as a
// general "best priced structure" query, unrelated to the Globe's own
// camera/polygon/border/elevation/tooltip/interaction implementation.
//
// Per the restore's own boundary rule ("adapt current data into the frozen
// component contract at the boundary/caller, never edit the frozen
// implementation"), this is extracted to its own small module — the exact
// implementation the pre-restore globeData.js had, byte-for-byte, never
// re-derived — rather than re-added into the now-frozen globeData.js file.
//
// Final non-Globe closeout, Item A (canonical scenario-selection
// consistency): this used to be an independent client-side re-derivation
// of "best priced structure", callable from four places, that could in
// principle disagree with the server's own rank==1 pick or with itself
// across two call sites given the same data. It now reads the ONE
// canonical field the backend computes and serves explicitly
// (allocated.canonical_selected_structure_id — see
// canonical_production_view.py).
//
// Optimizer P0 wiring remediation (2026-09-04), P0-1: the field can be a
// real, legitimate `null` — "no comparable Recommended candidate exists,
// so there is no canonical selection" (Little Utopia and F#K Valentine's
// Day both currently serve this state). The ORIGINAL code here treated a
// falsy field value (including a real `null`) as "field absent" and fell
// through to the local reduce() below, which picks the lowest-NPC
// structure among ALL is_fully_priced candidates regardless of
// comparability — silently re-inventing exactly the non-comparable
// PRICED_LOW_FIT winner (e.g. a Saudi full-relocation candidate) the
// backend fix now correctly refuses to select. Fixed by checking for the
// field's PRESENCE (a real server key, even when its value is null)
// rather than its truthiness: a present-but-null field means "the
// server's own canonical answer is no selection," which must propagate
// as `null` here too, never trigger the legacy fallback. The reduce()
// below now fires ONLY for a payload shape that predates this field
// entirely (the key is genuinely absent) — a real, pre-existing served
// shape, never re-derived, kept solely for that backward-compatibility
// case.
export function bestPricedCandidate(allocated) {
  if (!allocated) return null;
  if (Object.prototype.hasOwnProperty.call(allocated, "canonical_selected_structure_id")) {
    const id = allocated.canonical_selected_structure_id;
    if (!id) return null; // real "no comparable selection" state — never invent one
    const byId = new Map((allocated.structures || []).map((s) => [s.structure_id, s]));
    return byId.get(id) || null;
  }
  const priced = (allocated.structures || []).filter((s) => s.is_fully_priced);
  if (!priced.length) return null;
  return priced.reduce((best, s) => {
    const bn = best?.npc_with_adjustments_usd ?? Infinity;
    const sn = s.npc_with_adjustments_usd ?? Infinity;
    return sn < bn ? s : best;
  }, null);
}
