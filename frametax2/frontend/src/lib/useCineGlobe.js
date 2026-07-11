import { useEffect, useState } from "react";
import { getLegal, getPackage, getProduction, getRecommendations, getStructures } from "../api";

// One combined fetch of the full backend state — every screen reads
// from this rather than re-deriving anything client-side.
export function useCineGlobe() {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    Promise.all([getProduction(), getPackage(), getRecommendations(), getStructures(), getLegal()])
      .then(([production, pkg, recommendations, structures, legal]) => {
        if (!cancelled) setState({ data: { production, pkg, recommendations, structures, legal }, error: null, loading: false });
      })
      .catch((err) => {
        if (!cancelled) setState({ data: null, error: err.message || String(err), loading: false });
      });
    return () => { cancelled = true; };
  }, []);

  return state;
}
