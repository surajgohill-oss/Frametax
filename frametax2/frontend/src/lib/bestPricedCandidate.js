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
// canonical_production_view.py) first. The original reduce() below is
// kept ONLY as a defensive fallback for a served payload that predates
// the canonical field (e.g. a stale cached response mid-deploy) — it is
// the exact algorithm the backend field itself now uses, so even if it
// ever fires, it cannot produce a different answer than the canonical
// field would have.
export function bestPricedCandidate(allocated) {
  if (!allocated) return null;
  const byId = new Map((allocated.structures || []).map((s) => [s.structure_id, s]));
  if (allocated.canonical_selected_structure_id && byId.has(allocated.canonical_selected_structure_id)) {
    return byId.get(allocated.canonical_selected_structure_id);
  }
  const priced = (allocated.structures || []).filter((s) => s.is_fully_priced);
  if (!priced.length) return null;
  return priced.reduce((best, s) => {
    const bn = best?.npc_with_adjustments_usd ?? Infinity;
    const sn = s.npc_with_adjustments_usd ?? Infinity;
    return sn < bn ? s : best;
  }, null);
}
