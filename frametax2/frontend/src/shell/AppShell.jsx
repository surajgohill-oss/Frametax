import { useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import ProjectHeader from "./ProjectHeader";
import Inspector from "./Inspector";

export default function AppShell({ children }) {
  const location = useLocation();
  const onProduction = location.pathname.startsWith("/production");

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main-col">
        {onProduction && <ProjectHeader />}
        <main className="workspace-main">{children}</main>
      </div>
      <Inspector />
    </div>
  );
}
