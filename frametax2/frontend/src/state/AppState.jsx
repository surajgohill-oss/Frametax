import { createContext, useCallback, useContext, useState } from "react";

// Shared app-level state: which Inspector content is open. Kept
// deliberately small — this is UI selection state, not business logic.
const AppStateContext = createContext(null);

export function AppStateProvider({ children }) {
  const [inspector, setInspector] = useState(null); // { kind, data } | null

  const openInspector = useCallback((kind, data) => setInspector({ kind, data }), []);
  const closeInspector = useCallback(() => setInspector(null), []);

  return (
    <AppStateContext.Provider value={{ inspector, openInspector, closeInspector }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
