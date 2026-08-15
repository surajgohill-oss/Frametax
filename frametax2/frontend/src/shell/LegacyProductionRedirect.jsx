import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getProduction } from "../api";
import { Loading, ErrorBox } from "../components/Async";

// Legacy production route cutover. The bare, unparameterized path
// (Overview/Workspace/Scenarios/ProjectGlobe/Reports/Binder/Knowledge/
// Record/Settings with no project_id) is no longer a normal product
// destination — every legacy sub-route lands here and
// redirects into Little Utopia's OWN restored, project_id-driven mature
// Overview (/projects/{id}/overview) — the SAME component tree every
// other project reaches, just resolved to the one project this bare path
// always meant historically, not a second/different UI.
//
// Resolves project_id from the existing /api/v1/cineglobe/production
// endpoint (the one real mapping from the legacy demo state to the real
// Project row) rather than hard-coding Little Utopia's UUID here.
export default function LegacyProductionRedirect() {
  const [state, setState] = useState({ projectId: null, error: null });

  useEffect(() => {
    let cancelled = false;
    getProduction()
      .then((production) => {
        if (!cancelled) setState({ projectId: production.project_id, error: null });
      })
      .catch((err) => {
        if (!cancelled) setState({ projectId: null, error: err.message || String(err) });
      });
    return () => { cancelled = true; };
  }, []);

  if (state.error) return <div className="screen"><ErrorBox message={state.error} /></div>;
  if (!state.projectId) return <div className="screen"><Loading /></div>;
  return <Navigate to={`/projects/${state.projectId}/overview`} replace />;
}
