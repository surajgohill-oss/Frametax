export function Loading() {
  return <p className="empty-state">Loading from backend…</p>;
}

export function ErrorBox({ message }) {
  return (
    <div className="region region-blocker">
      <p style={{ color: "var(--red)", margin: 0 }}><strong>Backend error.</strong> {message}</p>
      <p className="text-tertiary small">Is the backend running? <code>uvicorn app.main:app --reload</code> from <code>frametax2/backend</code>.</p>
    </div>
  );
}
