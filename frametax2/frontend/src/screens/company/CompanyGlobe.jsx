import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { JURISDICTION_COORDS } from "../../lib/jurisdictions";
import { Money } from "../../lib/format";

export default function CompanyGlobe() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  const [preview, setPreview] = useState(null);
  const [focused, setFocused] = useState(false);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production } = data;
  const coord = JURISDICTION_COORDS[production.jurisdiction_code];
  const points = coord
    ? [{ lat: coord.lat, lng: coord.lng, tier: "gold", name: production.production_name, id: production.production_id }]
    : [];

  return (
    <div className="globe-screen">
      <div className="globe-screen-context">
        <p className="screen-eyebrow">Company Globe</p>
        <h1 className="serif" style={{ fontSize: 20 }}>Portfolio</h1>
        <p className="text-tertiary small">
          One production is currently active in this workspace. Hover the marker for a preview,
          click to focus, click again (or Open) to enter the production.
        </p>
        <div className="portfolio-chip" onClick={() => navigate("/production/overview")}>
          <span className="dot gold" />
          <div>
            <div className="row-title">{production.production_name}</div>
            <div className="row-sub">{production.jurisdiction_code} · <Money value={production.gross_budget_usd} /></div>
          </div>
        </div>
      </div>

      <div className="globe-screen-canvas">
        <Globe3D
          points={points}
          height={560}
          onPointHover={(pt) => setPreview(pt)}
          onPointClick={(pt) => {
            if (focused) navigate("/production/overview");
            else setFocused(true);
          }}
        />
        {preview && (
          <div className="globe-tooltip">
            <strong>{preview.name}</strong>
            <div className="text-tertiary small">Click to focus · click again to open</div>
          </div>
        )}
      </div>

      {focused && (
        <div className="globe-screen-inspector">
          <p className="inspector-eyebrow">Production preview</p>
          <h3>{production.production_name}</h3>
          <dl className="kv-list">
            <div><dt>Baseline jurisdiction</dt><dd>{production.jurisdiction_code}</dd></div>
            <div><dt>Gross budget</dt><dd><Money value={production.gross_budget_usd} /></dd></div>
            <div><dt>Incentive rate</dt><dd className="mono">{(production.rate * 100).toFixed(0)}%</dd></div>
          </dl>
          <button className="primary-action" onClick={() => navigate("/production/overview")}>Open production →</button>
        </div>
      )}
    </div>
  );
}
