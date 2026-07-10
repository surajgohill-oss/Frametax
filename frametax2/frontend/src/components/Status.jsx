export function Loading() {
  return <p className="status">Loading from backend…</p>;
}

export function ErrorBox({ message }) {
  return (
    <div className="status error">
      <strong>Backend error:</strong> {message}
      <p>Is the backend running? <code>uvicorn app.main:app --reload</code> from <code>frametax2/backend</code>.</p>
    </div>
  );
}

export function Money({ value }) {
  if (value === null || value === undefined) return <span className="muted">—</span>;
  return <span>${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>;
}

export function Pct({ value }) {
  if (value === null || value === undefined) return <span className="muted">—</span>;
  return <span>{(Number(value) * 100).toFixed(0)}%</span>;
}
