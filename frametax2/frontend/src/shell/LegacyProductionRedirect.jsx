import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getProduction } from "../api";
import { Loading, ErrorBox } from "../components/Async";

// Legacy /production/* route cutover — the old, Little-Utopia-only
// CineGlobe UI (Overview/Workspace/Scenarios/ProjectGlobe/Reports/Binder/
// Knowledge/Record/Settings) is no longer a normal product destination.
// Every sub-route under /production/* lands here and redirects into the
// SAME generic project Workspace (app/services/project_workspace_view.py,
// screens/project/ProjectWorkspace.jsx) every other project reaches by
// project_id — not a second, Little-Utopia-specific redirect target.
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
  return <Navigate to={`/projects/${state.projectId}/workspace`} replace />;
}
