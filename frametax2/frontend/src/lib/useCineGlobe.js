import { useCallback, useEffect, useRef, useState } from "react";
import {
  getEconomics, getFacts, getLegal, getPackage, getPeople, getProduction,
  getRecommendations, getStructures,
} from "../api";

// One combined fetch of the full backend state — every screen reads
// from this rather than re-deriving anything client-side. Extended to
// include /economics, /people, /facts (previously fetched by nothing in
// this app, despite all three being fully served). refetch() re-runs the
// same combined fetch — call it after any POST /people, POST /facts, or
// POST /economics/controls mutation so the screen reflects the backend's
// own recalculation rather than a client-guessed optimistic update.
export function useCineGlobe() {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const mounted = useRef(true);
  // Re-arm on every mount (not just the initial useRef value) — StrictMode's
  // dev-only mount→cleanup→mount cycle would otherwise leave this stuck
  // false after the first cleanup, permanently dropping every setState.
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const load = useCallback(() => {
    setState((s) => (s.data ? { ...s, loading: true } : s));
    return Promise.all([
      getProduction(), getPackage(), getRecommendations(), getStructures(),
      getLegal(), getEconomics(), getPeople(), getFacts(),
    ])
      .then(([production, pkg, recommendations, structures, legal, economics, people, facts]) => {
        if (!mounted.current) return;
        setState({
          data: { production, pkg, recommendations, structures, legal, economics, people, facts },
          error: null, loading: false,
        });
      })
      .catch((err) => {
        if (!mounted.current) return;
        setState({ data: null, error: err.message || String(err), loading: false });
      });
  }, []);

  useEffect(() => { load(); }, [load]);

  return { ...state, refetch: load };
}
