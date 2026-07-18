import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import AppShell from "./shell/AppShell";
import ErrorBoundary from "./shell/ErrorBoundary";

import Today from "./screens/company/Today";
import CompanyGlobe from "./screens/company/CompanyGlobe";
import CompanyKnowledge from "./screens/company/CompanyKnowledge";
import OrgReports from "./screens/company/OrgReports";

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
            <Route path="/company/globe" element={<CompanyGlobe />} />
            <Route path="/company/knowledge" element={<CompanyKnowledge />} />
            <Route path="/company/reports" element={<OrgReports />} />
            <Route path="/production/overview" element={<Overview />} />
            <Route path="/production/workspace" element={<Workspace />} />
            <Route path="/production/scenarios" element={<Scenarios />} />
            <Route path="/production/globe" element={<ProjectGlobe />} />
            <Route path="/production/reports" element={<Reports />} />
            <Route path="/production/binder" element={<Binder />} />
            <Route path="/production/knowledge" element={<Knowledge />} />
            <Route path="/production/record" element={<Record />} />
            <Route path="/production/settings" element={<Settings />} />
          </Routes>
        </AppShell>
        </ErrorBoundary>
      </BrowserRouter>
    </AppStateProvider>
  );
}
