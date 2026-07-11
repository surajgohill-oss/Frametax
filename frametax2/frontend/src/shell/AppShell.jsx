import PrimaryRail from "./PrimaryRail";
import SecondaryNav from "./SecondaryNav";
import Inspector from "./Inspector";
import { useAppState } from "../state/AppState";

export default function AppShell({ children }) {
  const { inspector } = useAppState();
  return (
    <div className="app-shell">
      <PrimaryRail />
      <SecondaryNav />
      <main className={`workspace-main ${inspector ? "with-inspector" : ""}`}>{children}</main>
      <Inspector />
    </div>
  );
}
