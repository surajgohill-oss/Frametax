import { useSyncExternalStore } from "react";
import { getPortfolioGlobe, patchProject } from "../api";
import { resolveLeadingStructure } from "./leadingResolve";
import { buildSelectedStructureRoute } from "./globeData";

export { resolveLeadingStructure };

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
  const userSelected = !!production.leading_selection?.user_selected && !production.leading_selection?.unavailable;
  const { structure, source } = resolveLeadingStructure(allocated, userSelected ? production.leading_structure_id : null);
  entries.set(projectId, {
    structure,
    source,
    homeCode: homeCodeOf(allocated),
    // the principal's served category colour: the same colour the Project Globe draws this structure's route in
    routeColor: structure ? buildSelectedStructureRoute(allocated, structure).color : null,
    baselineCode: production.jurisdiction_code || null,
    selectionKnown: production.leading_selection != null,
    userSelected,
    unavailable: !!production.leading_selection?.unavailable,
    pending: false,
  });
  emit();
}

// ONE aggregate payload for every active project (GET /cineglobe/portfolio/globe): Company Globe and the sidebar
// mini-globe read it; a project's own served state refines the same entry later. Submitted projects are absent.
let portfolio = null;
let portfolioLoad = null;

export const getPortfolio = () => portfolio;

export function usePortfolio() {
  useSyncExternalStore(subscribe, () => version);
  return portfolio;
}

export function loadPortfolio({ force = false } = {}) {
  if (portfolio && !force) return Promise.resolve(portfolio);
  portfolioLoad ||= getPortfolioGlobe()
    .then((payload) => {
      portfolio = payload;
      for (const row of payload.projects || []) {
        if (entries.get(row.project_id)?.pending) continue;
        entries.set(row.project_id, {
          structure: row.leading?.structure || null,
          source: row.leading?.source || "baseline",
          homeCode: row.home_code || null,
          baselineCode: row.baseline_jurisdiction || null,
          selectionKnown: true,
          userSelected: !!row.leading?.user_selected,
          unavailable: !!row.leading?.unavailable,
          pending: false,
        });
      }
      emit();
      return portfolio;
    })
    .finally(() => { portfolioLoad = null; });
  return portfolioLoad;
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
