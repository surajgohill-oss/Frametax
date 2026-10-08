import { useSyncExternalStore } from "react";
import { patchProject } from "../api";
import { activeStructure } from "./globeData";

// PROJECT-SCOPED LEADING SELECTION (2026-10-08). One in-memory snapshot per project of the structure that currently
// leads it: the producer's persisted "Set as Leading" choice (Project.leading_structure_id) when one exists, else the
// canonical leader the served state resolves. Written from exactly two places -- a served project state load
// (useCineGlobe) and commitLeadingStructure() below -- and read by Company Globe and the sidebar mini-globe, so a
// commit reaches every surface immediately without another request and without any evaluation. Never persisted here:
// the backend Project row stays the only durable owner.
const entries = new Map();
const listeners = new Set();
let version = 0;
const emit = () => { version += 1; listeners.forEach((l) => l()); };

const subscribe = (l) => { listeners.add(l); return () => listeners.delete(l); };

export const getLeadingSelection = (projectId) => (projectId ? entries.get(projectId) || null : null);

export function useLeadingSelection(projectId) {
  return useSyncExternalStore(subscribe, () => getLeadingSelection(projectId));
}

// Re-renders on any project's change (Company Globe reads every active project).
export function useLeadingSelectionsVersion() {
  return useSyncExternalStore(subscribe, () => version);
}

// Same home-jurisdiction rule buildSelectedStructureRoute uses for relocation routes.
const homeCodeOf = (allocated) => {
  const baseline = (allocated?.structures || []).find((x) => x.is_baseline || x.structure_type === "single_country");
  return baseline?.primary_jurisdiction ?? allocated?.jurisdiction_accounting?.home_jurisdiction ?? null;
};

// Called with every served project state. Ignored while a commit for that project is still being written, so an
// in-flight refetch can never put the previous selection back on screen.
export function publishServedLeading(projectId, state) {
  if (!projectId || !state) return;
  if (entries.get(projectId)?.pending) return;
  const allocated = state?.structures?.allocated_structures || null;
  const production = state?.production || {};
  const structure = activeStructure(allocated, production.leading_structure_id || null);
  entries.set(projectId, {
    structure,
    homeCode: homeCodeOf(allocated),
    baselineCode: production.jurisdiction_code || null,
    selectionKnown: production.leading_selection != null,
    userSelected: !!production.leading_selection?.user_selected,
    unavailable: !!production.leading_selection?.unavailable,
    pending: false,
  });
  emit();
}

// "Set as Leading": publish first (every surface updates now), then persist project-scoped. Presentation/portfolio
// state only -- PATCH /projects/{id} writes the row and never evaluates. On failure the previous entry is restored.
export function commitLeadingStructure(projectId, structure) {
  if (!projectId || !structure) return Promise.resolve();
  const previous = entries.get(projectId) || null;
  entries.set(projectId, { ...(previous || {}), structure, selectionKnown: true, userSelected: true, unavailable: false, pending: true });
  emit();
  return patchProject(projectId, { leading_structure_id: structure.structure_id })
    .then(() => {
      entries.set(projectId, { ...entries.get(projectId), pending: false });
      emit();
    })
    .catch((err) => {
      if (previous) entries.set(projectId, previous); else entries.delete(projectId);
      emit();
      console.error("[leadingSelection] failed to persist the leading structure:", err);
    });
}
