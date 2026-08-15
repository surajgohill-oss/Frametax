import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import AppShell from "./shell/AppShell";
import ErrorBoundary from "./shell/ErrorBoundary";
import LegacyProductionRedirect from "./shell/LegacyProductionRedirect";

import Today from "./screens/company/Today";
import ProjectLibrary from "./screens/company/ProjectLibrary";
import ProjectRecord from "./screens/company/ProjectRecord";
import CompanyGlobe from "./screens/company/CompanyGlobe";
import CompanyKnowledge from "./screens/company/CompanyKnowledge";
import OrgReports from "./screens/company/OrgReports";

import ProjectWorkspace from "./screens/project/ProjectWorkspace";

import Overview from "./screens/production/Overview";
import Workspace from "./screens/production/Workspace";
import Scenarios from "./screens/production/Scenarios";
import ProjectGlobe from "./screens/production/ProjectGlobe";
import Reports from "./screens/production/Reports";
import Binder from "./screens/production/Binder";
import Knowledge from "./screens/production/Knowledge";
import Record from "./screens/production/Record";
import Settings from "./screens/production/Settings";

export default function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <ErrorBoundary>
        <AppShell>
          <Routes>
            <Route path="/" element={<Navigate to="/company/today" replace />} />
            <Route path="/company/today" element={<Today />} />
            <Route path="/company/library" element={<ProjectLibrary />} />
            <Route path="/company/library/:projectId" element={<ProjectRecord />} />

            {/* Mature UI restoration: the rich, pre-regression production
                component tree (previously a legacy Little-Utopia-only path)
                generalized by project_id — see canonical_production_view.py
                and useCineGlobe(projectId). This is the normal "enter the
                project" destination for every project. */}
            <Route path="/projects/:projectId/overview" element={<Overview />} />
            <Route path="/projects/:projectId/workspace" element={<Workspace />} />
            <Route path="/projects/:projectId/scenarios" element={<Scenarios />} />
            <Route path="/projects/:projectId/globe" element={<ProjectGlobe />} />
            <Route path="/projects/:projectId/reports" element={<Reports />} />
            <Route path="/projects/:projectId/binder" element={<Binder />} />
            <Route path="/projects/:projectId/knowledge" element={<Knowledge />} />
            <Route path="/projects/:projectId/record" element={<Record />} />
            <Route path="/projects/:projectId/settings" element={<Settings />} />

            {/* The prior phase's stripped-down 4-tab Workspace (Overview/
                Script/Budget/World) is no longer the primary project
                destination (superseded by the restored mature UI above),
                but is kept reachable, not deleted, for its Script-tab SA-1
                display — the only "project-level Script entry" this phase
                is instructed to preserve, not design (Part I). */}
            <Route path="/projects/:projectId/summary" element={<ProjectWorkspace />} />

            <Route path="/company/globe" element={<CompanyGlobe />} />
            <Route path="/company/knowledge" element={<CompanyKnowledge />} />
            <Route path="/company/reports" element={<OrgReports />} />
            {/* Any remaining legacy production link (saved, typed, or from a
                stale bookmark) redirects into Little Utopia's OWN restored
                mature Overview — never the old unrouted screen, never the
                stripped-down Workspace. See LegacyProductionRedirect. */}
            <Route path="/production/*" element={<LegacyProductionRedirect />} />
          </Routes>
        </AppShell>
        </ErrorBoundary>
      </BrowserRouter>
    </AppStateProvider>
  );
}
