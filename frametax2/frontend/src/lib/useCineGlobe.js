import { useCallback, useEffect, useRef, useState } from "react";
import {
  getEconomics, getFacts, getLegal, getPackage, getPeople, getProduction,
  getProjectState, getRecommendations, getStructures,
} from "../api";

// One combined fetch of the full backend state — every screen reads
// from this rather than re-deriving anything client-side.
//
// Mature UI restoration: pass a project_id to drive this off the generic,
// canonical-evaluation-backed GET /cineglobe/projects/{id}/state (ONE
// request instead of 8) — the same `{production, pkg, recommendations,
// structures, legal, economics, people, facts}` shape, just sourced
// per-project rather than from the single in-memory Little Utopia state.
// Called with NO project_id (Company-level pages not scoped to one
// project), it keeps the ORIGINAL 8-call fetch entirely unchanged — zero
// behavior change for any caller that hasn't been project-scoped.
// refetch() re-runs the same fetch — call it after any POST /people,
// POST /facts, or POST /economics/controls mutation so the screen
// reflects the backend's own recalculation rather than a client-guessed
// optimistic update.
export function useCineGlobe(projectId) {
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
    const fetchState = projectId
      ? getProjectState(projectId)
      : Promise.all([
          getProduction(), getPackage(), getRecommendations(), getStructures(),
          getLegal(), getEconomics(), getPeople(), getFacts(),
        ]).then(([production, pkg, recommendations, structures, legal, economics, people, facts]) => (
          { production, pkg, recommendations, structures, legal, economics, people, facts }
        ));
    return fetchState
      .then((data) => {
        if (!mounted.current) return;
        setState({ data, error: null, loading: false });
      })
      .catch((err) => {
        if (!mounted.current) return;
        setState({ data: null, error: err.message || String(err), loading: false });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  return { ...state, refetch: load };
}
