import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { MODE_NORMAL } from "../lib/workspaceScenarioMode";

// Shared app-level state: which Inspector content is open, plus the
// production-wide selection state (leading structure / selected
// jurisdiction) that the Production Workspace's synchronized views
// (Globe, Budget Rail, Inspector, Overview, Scenario Manager) all read
// from. Kept deliberately small — this is UI selection state, not
// business logic, and not persisted (Workspace Phase 1: selection sync
// only; persistence is the later User Adjustments phase).
const AppStateContext = createContext(null);

// CODEX_FG-001/FG-003 (2026-09-21, Codex Frontend Workspace/Globe Runtime
// Audit): every field below except slot6 (already project-scoped) used to
// be a single flat scalar shared across the WHOLE app regardless of which
// project's route the producer is currently on. Confirmed live: an
// Inspector opened on one project stayed visible after navigating to a
// different project through Project Library; Optimizer mode chosen on one
// project silently applied to every other project visited afterward,
// through React Router's own normal behavior (a route param changing does
// NOT remount the matched component, so AppStateProvider — mounted once,
// above every route — never saw a natural "project changed" boundary to
// reset against).
//
// Fix: derive the current project id directly from the URL via
// `useLocation()` (works anywhere inside `<BrowserRouter>`, unlike
// `useParams()` which only resolves for a component that IS a matched
// route element — there is no single shared layout route today for every
// `/projects/:projectId/*` screen to hang a `useParams()`-based effect
// off). The instant that derived id changes, transient/global state resets;
// workspaceMode and (via CODEX_FG-004) leadingStructureId are additionally
// re-seeded from that NEW project's own remembered/persisted state, never
// left blank or carried over from the project just left.
function currentProjectIdFromPath(pathname) {
  return /^\/projects\/([^/]+)/.exec(pathname)?.[1] ?? null;
}

export function AppStateProvider({ children }) {
  const location = useLocation();
  const projectId = currentProjectIdFromPath(location.pathname);

  const [inspector, setInspector] = useState(null); // { kind, data } | null
  // UI-only layout flag: the Workspace docks the Inspector as its right
  // column (the frozen-artifact interaction) instead of the floating
  // overlay. When docked, the app-level overlay stands down. This is
  // presentation state, never a second copy of the selected data.
  const [docked, setDocked] = useState(false);

  // The producer's chosen leading structure_id (Workspace "Set as leading",
  // or a Scenarios/Overview selection). null = no override, every view
  // falls back to the optimizer's own rank #1. Shared across every
  // Production Workspace view so choosing a leading structure anywhere
  // updates Globe / Budget Rail / Inspector / Overview / Scenario Manager
  // without a refresh. CODEX_FG-001: reset on project change (below).
  // CODEX_FG-004: seeded once per project from its own served
  // `production.leading_structure_id` — see initLeadingStructureId.
  const [leadingStructureId, setLeadingStructureIdRaw] = useState(null);
  // The currently selected jurisdiction code (Globe click, snapshot strip,
  // Budget Rail jurisdiction row). Drives the Globe's Blue "Currently
  // Selected" state and scopes Budget Rail's jurisdiction-allocation view.
  const [selectedJurisdiction, setSelectedJurisdiction] = useState(null);

  // Workspace scenario-mode data wiring: 'normal' | 'optimizer', now kept
  // PER PROJECT (CODEX_FG-003) so switching mode on one project can never
  // leak into another, and each project restores whatever mode it was last
  // left in when revisited — see lib/workspaceScenarioMode.js for the
  // canonical family mapping this mode drives.
  const [workspaceModeByProject, setWorkspaceModeByProject] = useState({});
  const workspaceMode = (projectId && workspaceModeByProject[projectId]) || MODE_NORMAL;
  const setWorkspaceMode = useCallback((mode) => {
    if (!projectId) return;
    setWorkspaceModeByProject((prev) => ({ ...prev, [projectId]: mode }));
  }, [projectId]);

  // Slot 6's producer-chosen override, stored per (project, mode) so
  // switching modes restores each mode's own prior choice instead of
  // leaking one mode's selection into the other, and so it survives a
  // mode round-trip without re-deriving anything. { [projectId]: { normal:
  // structureId|null, optimizer: structureId|null } }. null/absent means
  // "no override — use the canonical rank-5 admissible candidate."
  const [slot6ByProjectMode, setSlot6ByProjectMode] = useState({});
  const getSlot6Selection = useCallback(
    (pid, mode) => (pid ? slot6ByProjectMode[pid]?.[mode] ?? null : null),
    [slot6ByProjectMode],
  );
  const setSlot6Selection = useCallback((pid, mode, structureId) => {
    if (!pid) return;
    setSlot6ByProjectMode((prev) => ({
      ...prev,
      [pid]: { ...prev[pid], [mode]: structureId || null },
    }));
  }, []);

  // CODEX_FG-004: which project's persisted leading_structure_id has
  // already been seeded into `leadingStructureId` this visit — guards
  // against re-seeding on a later data refetch (e.g. after the producer
  // explicitly clears their own override, which must stick, never get
  // silently reverted the next time useCineGlobe reloads).
  const initializedLeadingForProject = useRef(null);
  const lastResetProjectId = useRef(projectId);

  // CODEX_FG-001: the one project-boundary-crossing reset. Fires exactly
  // when the URL's own project id changes (never on a same-project
  // sub-route navigation, e.g. Workspace -> Globe for the SAME project,
  // which must keep sharing selection as it always has).
  useEffect(() => {
    if (lastResetProjectId.current === projectId) return;
    lastResetProjectId.current = projectId;
    setInspector(null);
    setSelectedJurisdiction(null);
    setLeadingStructureIdRaw(null);
    initializedLeadingForProject.current = null;
  }, [projectId]);

  const setLeadingStructureId = useCallback((id) => {
    // A producer's own explicit choice always wins going forward — mark
    // this project's persisted-leading seed as already "used" so a later
    // refetch never overwrites an explicit clear/override with the
    // original served value again.
    if (projectId) initializedLeadingForProject.current = projectId;
    setLeadingStructureIdRaw(id);
  }, [projectId]);

  // CODEX_FG-004: seed leadingStructureId from a project's own served,
  // persisted leading structure exactly once per project visit. Called
  // from useCineGlobe once `production.leading_structure_id` is known.
  // Never invents a value; never re-applies after the producer's own
  // choice for this same visit.
  const initLeadingStructureId = useCallback((forProjectId, persistedId) => {
    if (!forProjectId || !persistedId) return;
    if (initializedLeadingForProject.current === forProjectId) return;
    initializedLeadingForProject.current = forProjectId;
    if (forProjectId === projectId) setLeadingStructureIdRaw(persistedId);
  }, [projectId]);

  const openInspector = useCallback((kind, data) => setInspector({ kind, data }), []);
  const closeInspector = useCallback(() => setInspector(null), []);

  return (
    <AppStateContext.Provider value={{
      inspector, openInspector, closeInspector, docked, setDocked,
      leadingStructureId, setLeadingStructureId, initLeadingStructureId,
      selectedJurisdiction, setSelectedJurisdiction,
      workspaceMode, setWorkspaceMode, getSlot6Selection, setSlot6Selection,
    }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
