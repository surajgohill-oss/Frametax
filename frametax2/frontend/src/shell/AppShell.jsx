import { useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import ProjectHeader from "./ProjectHeader";
import Inspector from "./Inspector";
import GlobeFixtureBadge from "../components/GlobeFixtureBadge";

// Matches the restored mature production pages (/projects/{id}/overview,
// /workspace, /scenarios, /globe, /reports, /binder, /knowledge, /record,
// /settings) — NOT /projects/{id}/summary (the stripped-down Workspace,
// which renders its own header) and not any legacy /production path
// (which now only exists as LegacyProductionRedirect's transient loading
// state).
const MATURE_PROJECT_ROUTE = /^\/projects\/[^/]+\/(overview|workspace|scenarios|globe|reports|binder|knowledge|record|settings)(\/|$)/;

export default function AppShell({ children }) {
  const location = useLocation();
  const onProduction = location.pathname.startsWith("/production") || MATURE_PROJECT_ROUTE.test(location.pathname);

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main-col">
        {onProduction && <ProjectHeader />}
        <main className="workspace-main">{children}</main>
      </div>
      <Inspector />
      {/* GLOBE MODE indicator for the development visual fixture. Renders null
          unless the fixture is explicitly enabled, and is impossible to enable
          in a production build. Mounted HERE rather than on the Globe screen
          because the fixture recolours every Globe surface — Overview and
          Workspace carry globes too — so a per-screen indicator would leave
          exactly the ambiguity it exists to remove. Not a shell redesign: one
          fixed-position dev overlay, no layout or navigation change. */}
      <GlobeFixtureBadge />
    </div>
  );
}
