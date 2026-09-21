import { createContext, useCallback, useContext, useState } from "react";
import { MODE_NORMAL } from "../lib/workspaceScenarioMode";

// Shared app-level state: which Inspector content is open, plus the
// production-wide selection state (leading structure / selected
// jurisdiction) that the Production Workspace's synchronized views
// (Globe, Budget Rail, Inspector, Overview, Scenario Manager) all read
// from. Kept deliberately small — this is UI selection state, not
// business logic, and not persisted (Workspace Phase 1: selection sync
// only; persistence is the later User Adjustments phase).
const AppStateContext = createContext(null);

export function AppStateProvider({ children }) {
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
  // without a refresh.
  const [leadingStructureId, setLeadingStructureId] = useState(null);
  // The currently selected jurisdiction code (Globe click, snapshot strip,
  // Budget Rail jurisdiction row). Drives the Globe's Blue "Currently
  // Selected" state and scopes Budget Rail's jurisdiction-allocation view.
  const [selectedJurisdiction, setSelectedJurisdiction] = useState(null);

  // Workspace scenario-mode data wiring: one shared 'normal' | 'optimizer'
  // mode, kept here (not local Workspace.jsx state) so a later Globe
  // wiring pass can read the exact same active mode without a second,
  // independently-maintained copy — see lib/workspaceScenarioMode.js for
  // the canonical family mapping this mode drives.
  const [workspaceMode, setWorkspaceMode] = useState(MODE_NORMAL);
  // Slot 6's producer-chosen override, stored per (project, mode) so
  // switching modes restores each mode's own prior choice instead of
  // leaking one mode's selection into the other, and so it survives a
  // mode round-trip without re-deriving anything. { [projectId]: { normal:
  // structureId|null, optimizer: structureId|null } }. null/absent means
  // "no override — use the canonical rank-5 admissible candidate."
  const [slot6ByProjectMode, setSlot6ByProjectMode] = useState({});
  const getSlot6Selection = useCallback(
    (projectId, mode) => (projectId ? slot6ByProjectMode[projectId]?.[mode] ?? null : null),
    [slot6ByProjectMode],
  );
  const setSlot6Selection = useCallback((projectId, mode, structureId) => {
    if (!projectId) return;
    setSlot6ByProjectMode((prev) => ({
      ...prev,
      [projectId]: { ...prev[projectId], [mode]: structureId || null },
    }));
  }, []);

  const openInspector = useCallback((kind, data) => setInspector({ kind, data }), []);
  const closeInspector = useCallback(() => setInspector(null), []);

  return (
    <AppStateContext.Provider value={{
      inspector, openInspector, closeInspector, docked, setDocked,
      leadingStructureId, setLeadingStructureId,
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
