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
            <Route path="/projects/:projectId/workspace" element={<ProjectWorkspace />} />
            <Route path="/company/globe" element={<CompanyGlobe />} />
            <Route path="/company/knowledge" element={<CompanyKnowledge />} />
            <Route path="/company/reports" element={<OrgReports />} />
            {/* Legacy CineGlobe UI cutover: the old Little-Utopia-only
                /production/* experience (Overview/Workspace/Scenarios/
                ProjectGlobe/Reports/Binder/Knowledge/Record/Settings) is no
                longer a normal product destination. Every sub-route
                redirects into the SAME generic project Workspace every
                other project uses — component files untouched, just no
                longer routed to. See LegacyProductionRedirect. */}
            <Route path="/production/*" element={<LegacyProductionRedirect />} />
          </Routes>
        </AppShell>
        </ErrorBoundary>
      </BrowserRouter>
    </AppStateProvider>
  );
}
