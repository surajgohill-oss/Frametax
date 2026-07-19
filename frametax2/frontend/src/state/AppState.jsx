import { createContext, useCallback, useContext, useState } from "react";

// Shared app-level state: which Inspector content is open. Kept
// deliberately small — this is UI selection state, not business logic.
const AppStateContext = createContext(null);

export function AppStateProvider({ children }) {
  const [inspector, setInspector] = useState(null); // { kind, data } | null
  // UI-only layout flag: the Workspace docks the Inspector as its right
  // column (the frozen-artifact interaction) instead of the floating
  // overlay. When docked, the app-level overlay stands down. This is
  // presentation state, never a second copy of the selected data.
  const [docked, setDocked] = useState(false);

  const openInspector = useCallback((kind, data) => setInspector({ kind, data }), []);
  const closeInspector = useCallback(() => setInspector(null), []);

  return (
    <AppStateContext.Provider value={{ inspector, openInspector, closeInspector, docked, setDocked }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
