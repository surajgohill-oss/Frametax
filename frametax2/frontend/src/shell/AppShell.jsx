import PrimaryRail from "./PrimaryRail";
import SecondaryNav from "./SecondaryNav";
import Inspector from "./Inspector";

export default function AppShell({ children }) {
  return (
    <div className="app-shell">
      <PrimaryRail />
      <SecondaryNav />
      <main className="workspace-main">{children}</main>
      <Inspector />
    </div>
  );
}
