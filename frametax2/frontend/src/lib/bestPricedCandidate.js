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
export function bestPricedCandidate(allocated) {
  if (!allocated) return null;
  const priced = (allocated.structures || []).filter((s) => s.is_fully_priced);
  if (!priced.length) return null;
  return priced.reduce((best, s) => {
    const bn = best?.npc_with_adjustments_usd ?? Infinity;
    const sn = s.npc_with_adjustments_usd ?? Infinity;
    return sn < bn ? s : best;
  }, null);
}
