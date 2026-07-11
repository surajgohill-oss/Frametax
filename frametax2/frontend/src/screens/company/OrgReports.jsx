export default function OrgReports() {
  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Organization Reports</p>
        <h1 className="screen-title">Generated artifacts</h1>
      </header>
      <div className="region">
        <p className="empty-state">
          No report-generation engine is wired into this workspace yet — this ledger will list
          generated artifacts (type, production, version, status) once one exists. Nothing is
          fabricated here.
        </p>
      </div>
    </div>
  );
}
