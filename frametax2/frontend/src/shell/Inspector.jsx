import { X } from "lucide-react";
import { useAppState } from "../state/AppState";
import { Money, Pct, YesNo, TimingFactValue, tierBadgeClass, recommendationHeadline, questionStatusLabel, humanizeToken, structureLabel, accountStateLabel } from "../lib/format";

// Final Global Discovery phase: the "Requirements & Timing" section of a
// jurisdiction segment — extends the existing AllocationSegmentInspector
// (below) rather than introducing a new surface. Reads
// data.requirements verbatim from GET /structures; renders nothing when
// the backend sent null (a program not yet covered by the Production
// Requirements Database — "Not stated", never a guessed value).
function RequirementsSection({ requirements }) {
  if (!requirements) return null;
  const r = requirements;
  const additional = Object.entries(r.additional_facts || {});
  return (
    <div className="inspector-sect">
      <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Requirements &amp; timing</p>
      <dl className="kv-list">
        <div><dt>Local entity required</dt><dd><YesNo value={r.local_entity_required} /></dd></div>
        <div><dt>Cultural test required</dt><dd><YesNo value={r.cultural_test_required} /></dd></div>
        {r.cultural_test_threshold != null && (
          <div><dt>Cultural test threshold</dt><dd className="mono">{r.cultural_test_threshold} points</dd></div>
        )}
        {r.min_total_budget_usd != null && (
          <div><dt>Minimum total budget</dt><dd className="mono"><Money value={r.min_total_budget_usd} /></dd></div>
        )}
        {r.min_local_spend_usd != null && (
          <div><dt>Minimum local spend</dt><dd className="mono"><Money value={r.min_local_spend_usd} /></dd></div>
        )}
        {r.per_project_cap_usd != null && (
          <div><dt>Per-project cap</dt><dd className="mono"><Money value={r.per_project_cap_usd} /></dd></div>
        )}
        {r.per_person_cap_usd != null && (
          <div><dt>Per-person cap</dt><dd className="mono"><Money value={r.per_person_cap_usd} /></dd></div>
        )}
        {r.atl_cap_pct_of_other_costs != null && (
          <div><dt>ATL cap</dt><dd className="mono"><Pct value={r.atl_cap_pct_of_other_costs} /> of other costs</dd></div>
        )}
        {r.annual_program_cap_usd != null && (
          <div><dt>Annual program cap</dt><dd className="mono"><Money value={r.annual_program_cap_usd} /></dd></div>
        )}
        <div><dt>Application deadline</dt><dd><TimingFactValue fact={r.application_deadline} /></dd></div>
        <div><dt>Audit / final certification</dt><dd><TimingFactValue fact={r.audit_or_final_certification_deadline} /></dd></div>
        <div><dt>Payment timing</dt><dd><TimingFactValue fact={r.payment_timing} /></dd></div>
        {r.sunset_date && <div><dt>Sunset date</dt><dd className="mono">{r.sunset_date}</dd></div>}
        <div><dt>Refundable</dt><dd>{r.refundable === null ? <span className="text-tertiary">Not stated</span> : (r.refundable ? "Yes" : "No")}</dd></div>
        <div><dt>Transferable</dt><dd>{r.transferable === null ? <span className="text-tertiary">Not stated</span> : (r.transferable ? "Yes" : "No")}</dd></div>
      </dl>
      {additional.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {additional.map(([key, val]) => (
            <p key={key} className="text-secondary small" style={{ margin: "3px 0" }}>
              <strong className="text-secondary" style={{ textTransform: "capitalize" }}>{key.replace(/_/g, " ")}:</strong> {val}
            </p>
          ))}
        </div>
      )}
      {r.evidence && (
        <p className="text-tertiary small" style={{ marginTop: 10 }}>
          <strong className="text-secondary">Source:</strong> {r.evidence.source_title} ({r.evidence.issuing_authority}) —{" "}
          {r.evidence.source_type === "primary" ? "primary source" : "secondary source"}, {r.evidence.status}
          {r.evidence.notes ? ` · ${r.evidence.notes}` : ""}
        </p>
      )}
    </div>
  );
}

// Task 91 (contingency treatment): shows any contingency line whose
// account_code appears in this segment, reading `contingencyByAccount`
// verbatim from the top-level GET /structures `contingency` key (see
// Workspace.jsx). Renders nothing when the segment has no contingency
// account, or when the account is on file but fully undeployed (that
// state is already visible in the qualification trace below as a plain
// "excluded"/"qualifies" row — this section exists to surface the
// DEPLOYMENT audit trail, not to duplicate the trace).
function ContingencySection({ accountCodes = [], contingencyByAccount = {} }) {
  const entries = accountCodes
    .map((code) => contingencyByAccount[code])
    .filter((c) => c && c.deployments.length > 0);
  if (entries.length === 0) return null;
  return (
    <div className="inspector-sect">
      <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Contingency deployment</p>
      {entries.map((c) => (
        <div key={c.source_account_code} style={{ marginBottom: 10 }}>
          <dl className="kv-list">
            <div><dt>Reserve</dt><dd>{c.source_description}</dd></div>
            <div><dt>Original</dt><dd className="mono"><Money value={c.original_amount_usd} /></dd></div>
            <div><dt>Deployed</dt><dd className="mono"><Money value={c.deployed_amount_usd} /></dd></div>
            <div><dt>Undeployed (excluded)</dt><dd className="mono"><Money value={c.undeployed_amount_usd} /></dd></div>
          </dl>
          {c.deployments.map((d, i) => (
            <p key={i} className="text-secondary small" style={{ margin: "4px 0" }}>
              <Money value={d.amount_usd} /> → {d.destination_description} ({d.destination_spend_category}) —{" "}
              {d.note} · {d.deployed_by}, {d.deployed_at.slice(0, 10)}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}

function AccountInspector({ data }) {
  const state = accountStateLabel(data.state);
  return (
    <>
      <p className="inspector-eyebrow">Budget account {data.code}</p>
      <h3>{data.label}</h3>
      <dl className="kv-list">
        <div><dt>Amount</dt><dd className="mono"><Money value={data.amount} /></dd></div>
        <div><dt>Qualification state</dt><dd><span className={`badge ${state.tier}`}>{state.label}</span></dd></div>
        <div><dt>Confidence</dt><dd style={{ textTransform: "capitalize" }}>{data.confidence}</dd></div>
        {data.movement !== "unclassified" && (
          <div><dt>Movement</dt><dd style={{ textTransform: "capitalize" }}>{data.movement}</dd></div>
        )}
        {data.incentiveUpsideUsd != null && (
          <div><dt>Incentive upside (at modeled rate)</dt><dd className="mono"><Money value={data.incentiveUpsideUsd} /></dd></div>
        )}
      </dl>
      {data.reason && <p className="text-secondary small" style={{ marginTop: 4 }}>{data.reason}</p>}
      {data.resolvingEvidence && (
        <p className="text-tertiary small" style={{ marginTop: 8 }}>
          <strong className="text-secondary">Resolving evidence needed:</strong> {data.resolvingEvidence}
        </p>
      )}
      {data.crossRef?.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Jurisdiction comparison — affected structures</p>
          <div className="row-list">
            {data.crossRef.map((c) => (
              <div className="row-item" key={c.structureId} style={{ cursor: "default" }}>
                <div className="row-main">
                  <div className="row-title small">{c.structureLabel}</div>
                  <div className="row-sub">
                    {c.jurisdictionCode}
                    {c.claimsIncentive
                      ? ` · QPE ${Math.round(c.qpeUsd).toLocaleString()}`
                      : " · no incentive claimed here"}
                    {c.blockers?.length > 0 ? ` · ${c.blockers[0]}` : ""}
                  </div>
                </div>
                <div className="row-value mono small">
                  {c.claimsIncentive ? <Money value={c.incentiveFloorUsd} /> : "—"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function RecommendationInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">{data.category} recommendation</p>
      <h3>{recommendationHeadline(data)}</h3>
      <p className="text-secondary">{data.description}</p>
      <dl className="kv-list">
        <div><dt>Estimated value</dt><dd className="mono"><Money value={data.estimated_value_usd} /></dd></div>
        <div><dt>Confidence</dt><dd>{data.confidence}</dd></div>
        <div><dt>Producer approval</dt><dd>{data.requires_producer_approval ? "Required" : "Not required"}</dd></div>
        <div><dt>Counsel approval</dt><dd>{data.requires_counsel_approval ? "Required" : "Not required"}</dd></div>
        {data.creative_impact && <div><dt>Creative impact</dt><dd>{data.creative_impact}</dd></div>}
        {data.trade_off_framing && <div><dt>Trade-off</dt><dd>{data.trade_off_framing}</dd></div>}
        {data.evidence_reference?.length > 0 && (
          <div><dt>Evidence needed</dt><dd>{data.evidence_reference.join("; ")}</dd></div>
        )}
        {data.authority_reference?.length > 0 && (
          <div><dt>Authority reference</dt><dd className="mono small">{data.authority_reference.join(", ")}</dd></div>
        )}
      </dl>
    </>
  );
}

function CandidateInspector({ data }) {
  const cases = data.cases || {};
  return (
    <>
      <p className="inspector-eyebrow">Structure candidate</p>
      <h3>{structureLabel(data.participating_jurisdictions)}</h3>
      <dl className="kv-list">
        <div><dt>Priceable now</dt><dd><Pct value={data.priceable_pct} /></dd></div>
        <div><dt>Open requirements</dt><dd>{data.constraints?.length || 0}</dd></div>
      </dl>
      {data.is_fully_priced && Object.keys(cases).length > 0 ? (
        <table className="inspector-table">
          <tbody>
            {["conservative", "base", "optimistic", "risk_adjusted"].filter((k) => cases[k]).map((k) => (
              <tr key={k}>
                <td style={{ textTransform: "capitalize" }}>{k.replace("_", " ")}</td>
                <td className="mono"><Money value={cases[k].net_production_cost_usd} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <>
          <p className="text-tertiary small">
            Only {Math.round(data.priceable_pct * 100)}% of this structure can currently be priced. A full cost
            comparison isn't available until the open requirements below are resolved.
          </p>
          {data.informational_upside_usd != null ? (
            <dl className="kv-list" style={{ marginTop: 10 }}>
              <div><dt>Estimated routing opportunity</dt><dd className="mono"><Money value={data.informational_upside_usd} /></dd></div>
            </dl>
          ) : (
            <p className="text-tertiary small" style={{ marginTop: 6 }}>
              No quantifiable rate advantage identified for this jurisdiction against the Mauritius baseline in
              current program data.
            </p>
          )}
        </>
      )}
      {data.constraints?.length > 0 && (() => {
        const unique = [...new Set(data.constraints.map((c) => c.description))];
        return (
          <div className="inspector-actions" style={{ flexDirection: "column", alignItems: "stretch" }}>
            {unique.slice(0, 4).map((desc) => (
              <p key={desc} className="text-secondary small" style={{ margin: "4px 0" }}>{desc}</p>
            ))}
            {unique.length > 4 && <p className="text-tertiary small">+{unique.length - 4} more requirement type(s)</p>}
          </div>
        );
      })()}
    </>
  );
}

function QuestionInspector({ data }) {
  const isGreyArea = "authority_to_ask" in data;
  const status = isGreyArea ? questionStatusLabel(data.status) : null;
  return (
    <>
      <p className="inspector-eyebrow">{isGreyArea ? "Grey area" : "Open question"}</p>
      <h3>{isGreyArea ? data.resolving_evidence : data.question}</h3>
      {isGreyArea ? (
        <dl className="kv-list">
          <div><dt>Status</dt><dd><span className={`badge ${status.tier}`}>{status.label}</span></dd></div>
          <div><dt>Amount at stake</dt><dd className="mono"><Money value={data.amount_usd} /></dd></div>
          <div><dt>Authority to ask</dt><dd>{data.authority_to_ask}</dd></div>
          {data.account_codes?.length > 0 && <div><dt>Affected accounts</dt><dd className="mono">{data.account_codes.join(", ")}</dd></div>}
        </dl>
      ) : (
        <dl className="kv-list">
          <div><dt>Why it matters</dt><dd>{data.why_it_matters}</dd></div>
          <div><dt>Decision required</dt><dd>{data.blocking ? "Yes" : "No"}</dd></div>
          <div><dt>Affects</dt><dd>{data.downstream_engines?.map(humanizeToken).join(", ")}</dd></div>
          <div><dt>Priority</dt><dd>{data.optimizer_value}</dd></div>
        </dl>
      )}
      <div className="inspector-actions">
        {["Resolve", "Escalate", "Attach document", "Assign", "Convert to assumption", "Promote to grey area"].map((label) => (
          <button key={label} className="ghost-action" disabled title="Not yet wired to a backend mutation">
            {label}
          </button>
        ))}
      </div>
    </>
  );
}

// The three renderer kinds below back the allocation / multi-register
// pricing surface (GET /structures -> allocated_structures). Every
// field is read verbatim from that payload — nothing here derives a
// number client-side.

function AllocationSegmentInspector({ data }) {
  const trace = data.qualification_trace || [];
  return (
    <>
      <p className="inspector-eyebrow">Jurisdiction segment{data.structureLabel ? ` · ${data.structureLabel}` : ""}</p>
      <h3>{data.jurisdiction_code}{data.program_slug ? ` — ${data.program_slug}` : ""}</h3>
      <dl className="kv-list">
        <div><dt>Allocated spend</dt><dd className="mono"><Money value={data.allocated_usd} /></dd></div>
        {data.claims_incentive ? (
          <>
            <div><dt>QPE</dt><dd className="mono"><Money value={data.qpe_usd} /></dd></div>
            <div><dt>Excluded</dt><dd className="mono"><Money value={data.excluded_usd} /></dd></div>
            <div><dt>Rate</dt><dd className="mono">{data.rate_floor != null ? `${Math.round(data.rate_floor * 100)}%` : "—"}{data.is_band_ceiling ? ` (up to ${Math.round(data.rate_ceiling * 100)}%)` : ""}</dd></div>
            <div><dt>Incentive (floor)</dt><dd className="mono"><Money value={data.incentive_floor_usd} /></dd></div>
          </>
        ) : (
          <div><dt>Incentive</dt><dd>None claimed here</dd></div>
        )}
      </dl>
      {data.statutory_basis && <p className="text-secondary small" style={{ marginTop: 8 }}>{data.statutory_basis}</p>}
      {data.blockers?.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Why this segment isn't priced</p>
          {data.blockers.map((b, i) => <p key={i} className="text-secondary small" style={{ margin: "4px 0" }}>{b}</p>)}
        </div>
      )}
      <RequirementsSection requirements={data.requirements} />
      <ContingencySection accountCodes={data.account_codes} contingencyByAccount={data.contingencyByAccount} />
      {trace.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Account qualification trace ({trace.length})</p>
          <div className="row-list">
            {trace.slice(0, 12).map((t) => (
              <div className="row-item" key={t.account_code} style={{ cursor: "default" }}>
                <div className="row-main">
                  <div className="row-title small">{t.account_code} · {t.description}</div>
                  <div className="row-sub">{accountStateLabel(t.state).label} · {t.reason}</div>
                </div>
                <div className="row-value mono small"><Money value={t.amount_usd} /></div>
              </div>
            ))}
            {trace.length > 12 && <p className="text-tertiary small" style={{ marginTop: 6 }}>+{trace.length - 12} more accounts in this segment</p>}
          </div>
        </div>
      )}
    </>
  );
}

function AllocationAssignmentInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">Budget account routing</p>
      <h3>{data.account_code} · {data.description}</h3>
      <dl className="kv-list">
        <div><dt>Amount</dt><dd className="mono"><Money value={data.amount_usd} /></dd></div>
        <div><dt>Component</dt><dd style={{ textTransform: "capitalize" }}>{(data.component || "").replace(/_/g, " ")}</dd></div>
        <div><dt>Routed to</dt><dd className="mono">{data.jurisdiction_code}</dd></div>
        <div><dt>Assignment</dt><dd style={{ textTransform: "capitalize" }}>{(data.assignment_kind || "").replace(/_/g, " ")}</dd></div>
        {data.split_pct != null && <div><dt>Split share</dt><dd className="mono">{Math.round(data.split_pct * 100)}%</dd></div>}
      </dl>
      <p className="text-secondary small" style={{ marginTop: 8 }}>{data.rationale}</p>
      {data.authority && <p className="text-tertiary small" style={{ marginTop: 8 }}><strong className="text-secondary">Authority:</strong> {data.authority}</p>}
      {data.supporting_facts?.length > 0 && (
        <p className="text-tertiary small" style={{ marginTop: 8 }}><strong className="text-secondary">Supporting facts:</strong> {data.supporting_facts.join(" ")}</p>
      )}
      {data.unresolved_requirements?.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Unresolved requirements</p>
          {data.unresolved_requirements.map((r, i) => <p key={i} className="text-secondary small" style={{ margin: "4px 0" }}>{r}</p>)}
        </div>
      )}
    </>
  );
}

function StructureRecommendationInspector({ data }) {
  const exp = data.explanation || {};
  return (
    <>
      <p className="inspector-eyebrow">Structure recommendation · {data.reversibility === "hard_to_reverse" ? "hard to reverse" : "reversible before execution"}</p>
      <h3>{data.action}</h3>
      <dl className="kv-list">
        <div><dt>Gated</dt><dd>{data.gated ? "Yes" : "No"}</dd></div>
        <div><dt>Approval chain</dt><dd style={{ textTransform: "capitalize" }}>{(data.approval_chain || []).join(" → ")}</dd></div>
      </dl>
      {exp.calculations && (
        <dl className="kv-list" style={{ marginTop: 8 }}>
          <div><dt>Total incentive (floor)</dt><dd className="mono"><Money value={exp.calculations.total_incentive_floor_usd} /></dd></div>
          <div><dt>NPC (verified)</dt><dd className="mono"><Money value={exp.calculations.npc_verified_usd} /></dd></div>
          <div><dt>NPC (with adjustments)</dt><dd className="mono"><Money value={exp.calculations.npc_with_adjustments_usd} /></dd></div>
        </dl>
      )}
      {data.dependency_group?.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Dependencies / blockers</p>
          {data.dependency_group.map((d, i) => <p key={i} className="text-secondary small" style={{ margin: "4px 0" }}>{d}</p>)}
        </div>
      )}
      {exp.assumptions?.length > 0 && (
        <div className="inspector-sect">
          <p className="inspector-eyebrow" style={{ marginTop: 12 }}>Assumptions</p>
          {exp.assumptions.map((a, i) => <p key={i} className="text-tertiary small" style={{ margin: "4px 0" }}>{a}</p>)}
        </div>
      )}
    </>
  );
}

function JurisdictionInspector({ data }) {
  return (
    <>
      <p className="inspector-eyebrow">Jurisdiction</p>
      <h3>{data.code}</h3>
      <span className={`badge ${tierBadgeClass(data.tier)}`}>{data.tierLabel}</span>
      {data.candidate && (
        <dl className="kv-list" style={{ marginTop: 12 }}>
          <div><dt>Priceable</dt><dd><Pct value={data.candidate.priceable_pct} /></dd></div>
          <div><dt>Risk-Adjusted NPC</dt><dd className="mono"><Money value={data.candidate.cases?.risk_adjusted?.net_production_cost_usd} /></dd></div>
        </dl>
      )}
    </>
  );
}

const RENDERERS = {
  recommendation: RecommendationInspector,
  candidate: CandidateInspector,
  question: QuestionInspector,
  jurisdiction: JurisdictionInspector,
  account: AccountInspector,
  "allocation-segment": AllocationSegmentInspector,
  "allocation-assignment": AllocationAssignmentInspector,
  "structure-recommendation": StructureRecommendationInspector,
};

// Shared inspector body — the selected item's detail. Used by BOTH the
// floating overlay (below) and the Workspace docked column, so the two
// presentations never fork the render logic or the data.
export function InspectorBody({ inspector }) {
  const Renderer = RENDERERS[inspector.kind];
  return Renderer ? <Renderer data={inspector.data} /> : <p className="text-tertiary">No inspector view for this item.</p>;
}

export default function Inspector() {
  const { inspector, closeInspector, docked } = useAppState();
  // When the Workspace docks the Inspector into its right column, the
  // app-level floating overlay stands down (single presentation at a time).
  if (!inspector || docked) return null;

  return (
    <>
      <div className="inspector-backdrop" onClick={closeInspector} />
      <aside className="inspector">
        <button className="inspector-close" onClick={closeInspector} aria-label="Close inspector">
          <X size={16} />
        </button>
        <InspectorBody inspector={inspector} />
      </aside>
    </>
  );
}
