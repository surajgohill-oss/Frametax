// Shared between Record.jsx and Today.jsx (Recent Activity) — the single
// real, append-only event source for a production: the baseline register
// plus any resolved grey-area authority decisions. Computed once here so
// both surfaces read the identical events, never a duplicated or
// diverging feed.
export function buildRecordRows(data) {
  const { legal, production } = data;
  const rows = [];
  rows.push({
    date: production.as_of_date,
    event: "Baseline register established",
    detail: `${production.jurisdiction_code} qualification register`,
  });
  for (const g of legal.grey_areas_current) {
    if (g.status !== "open") {
      rows.push({
        date: production.as_of_date,
        event: `${g.jurisdiction_code} authority decision received`,
        detail: `${g.resolving_evidence} — Authority Score ${legal.authority_scores[g.graph_rule_id]?.composite ?? "—"} (${legal.authority_scores[g.graph_rule_id]?.confidence ?? ""})`,
        value: g.amount_usd,
      });
    }
  }
  return rows;
}
