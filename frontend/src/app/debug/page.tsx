"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Trash2, RefreshCw, ChevronDown, ChevronUp, Play } from "lucide-react";
import { fmtRelative } from "@/lib/utils";

type DebugTab = "errors" | "memory";

export default function DebugPage() {
  const [tab, setTab] = useState<DebugTab>("errors");
  const [errors, setErrors] = useState<any[]>([]);
  const [memory, setMemory] = useState<any[]>([]);
  const [summary, setSummary] = useState<any[]>([]);
  const [filterMp, setFilterMp] = useState<string>("all");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [clearingMp, setClearingMp] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [errs, sum, mem] = await Promise.all([
        api.debug.errors(filterMp === "all" ? undefined : filterMp),
        api.debug.errorSummary(),
        api.debug.memory(filterMp === "all" ? undefined : filterMp),
      ]);
      setErrors(errs);
      setSummary(sum);
      setMemory(mem);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterMp]);

  async function handleDeleteMemory(id: number) {
    await api.debug.deleteMemory(id);
    load();
  }

  async function handleClearMemory(mp: string) {
    if (!confirm(`Clear all failure memory for ${mp}?`)) return;
    setClearingMp(mp);
    await api.debug.clearMemory(mp).finally(() => setClearingMp(null));
    load();
  }

  async function handleTestCollect(marketplace: string) {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await api.debug.testCollect(marketplace);
      setTestResult(JSON.stringify(r, null, 2));
    } catch (e: any) {
      setTestResult(`Error: ${e.message}`);
    } finally {
      setTesting(false);
    }
  }

  const marketplaces = ["all", "stubhub", "seatgeek"];

  const errorTypeColor: Record<string, string> = {
    network_error: "bg-red-500/20 text-red-300",
    auth_error: "bg-amber-500/20 text-amber-300",
    selector_error: "bg-orange-500/20 text-orange-300",
    parse_error: "bg-purple-500/20 text-purple-300",
    timeout: "bg-yellow-500/20 text-yellow-300",
    unknown: "bg-slate-500/20 text-slate-300",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Debug Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Scraper error telemetry and failure memory</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e2535] border border-[#2a3145] text-slate-300 text-sm rounded-lg hover:bg-[#2a3145] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Error Summary Cards */}
      {summary.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {summary.map((s: any) => (
            <Card key={`${s.marketplace}-${s.error_type}`} className="p-3">
              <div className="text-xs text-slate-400">{s.marketplace} · {s.error_type}</div>
              <div className="text-xl font-bold text-white mt-1">{s.count}</div>
              <div className="text-xs text-slate-500">errors</div>
            </Card>
          ))}
        </div>
      )}

      {/* Marketplace filter */}
      <div className="flex gap-2">
        {marketplaces.map((mp) => (
          <button
            key={mp}
            onClick={() => setFilterMp(mp)}
            className={`px-3 py-1 text-xs rounded-full border transition-colors ${
              filterMp === mp
                ? "bg-blue-600 border-blue-500 text-white"
                : "border-[#2a3145] text-slate-400 hover:text-white"
            }`}
          >
            {mp === "all" ? "All" : mp}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[#2a3145]">
        {(["errors", "memory"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${
              tab === t
                ? "text-white bg-[#1e2535] border-b-2 border-blue-500"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {t === "errors" ? `Error Log (${errors.length})` : `Failure Memory (${memory.length})`}
          </button>
        ))}
      </div>

      {/* Error Log Tab */}
      {tab === "errors" && (
        <Card>
          {errors.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              No errors recorded. This is a good sign.
            </div>
          ) : (
            <div className="divide-y divide-[#2a3145]">
              {errors.map((err) => (
                <div key={err.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`text-xs px-2 py-0.5 rounded font-mono ${errorTypeColor[err.error_type] ?? errorTypeColor.unknown}`}>
                          {err.error_type}
                        </span>
                        <span className="text-xs text-slate-400">{err.marketplace}</span>
                        {err.event_id && (
                          <span className="text-xs text-slate-500">event: {err.event_id}</span>
                        )}
                        <span className="text-xs text-slate-600">{fmtRelative(err.timestamp)}</span>
                      </div>
                      {err.url && (
                        <div className="text-xs text-slate-500 mt-1 truncate font-mono">{err.url}</div>
                      )}
                      {err.selector && (
                        <div className="text-xs text-slate-500 mt-0.5 font-mono">
                          selector: <span className="text-amber-400">{err.selector}</span>
                        </div>
                      )}
                      {err.http_status && (
                        <div className="text-xs text-slate-500">HTTP {err.http_status}</div>
                      )}
                    </div>
                    <button
                      onClick={() => setExpanded(expanded === err.id ? null : err.id)}
                      className="text-slate-500 hover:text-slate-300 shrink-0"
                    >
                      {expanded === err.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                  {expanded === err.id && (
                    <div className="mt-3 space-y-2">
                      {err.raw_sample && (
                        <div>
                          <div className="text-xs text-slate-500 mb-1">Raw Sample</div>
                          <pre className="text-xs text-slate-300 bg-[#0d1117] border border-[#2a3145] rounded p-3 overflow-x-auto max-h-40 whitespace-pre-wrap">
                            {err.raw_sample}
                          </pre>
                        </div>
                      )}
                      {err.screenshot_path && (
                        <div className="text-xs text-slate-400">
                          Screenshot: <span className="font-mono text-slate-300">{err.screenshot_path}</span>
                        </div>
                      )}
                      {err.html_snapshot_path && (
                        <div className="text-xs text-slate-400">
                          HTML Snapshot: <span className="font-mono text-slate-300">{err.html_snapshot_path}</span>
                        </div>
                      )}
                      {err.extra && (
                        <pre className="text-xs text-slate-400 bg-[#0d1117] border border-[#2a3145] rounded p-3 overflow-x-auto max-h-32 whitespace-pre-wrap">
                          {JSON.stringify(err.extra, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Failure Memory Tab */}
      {tab === "memory" && (
        <div className="space-y-4">
          <div className="flex justify-end gap-2">
            {["stubhub", "seatgeek"].map((mp) => (
              <button
                key={mp}
                onClick={() => handleClearMemory(mp)}
                disabled={clearingMp === mp}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[#1e2535] border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-3 h-3" />
                Clear {mp}
              </button>
            ))}
          </div>

          <Card>
            {memory.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No failure patterns recorded.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#2a3145]">
                      <th className="text-left px-4 py-3 text-slate-400">Pattern</th>
                      <th className="text-left px-4 py-3 text-slate-400">Type</th>
                      <th className="text-left px-4 py-3 text-slate-400">MP</th>
                      <th className="text-right px-4 py-3 text-slate-400">Failures</th>
                      <th className="text-right px-4 py-3 text-slate-400">Successes</th>
                      <th className="text-left px-4 py-3 text-slate-400">Fallback</th>
                      <th className="text-center px-4 py-3 text-slate-400">Skip</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#2a3145]">
                    {memory.map((m) => (
                      <tr key={m.id} className="hover:bg-[#1e2535] transition-colors">
                        <td className="px-4 py-2.5 font-mono text-amber-400 max-w-xs truncate">
                          {m.failed_pattern}
                        </td>
                        <td className="px-4 py-2.5 text-slate-300">{m.error_type}</td>
                        <td className="px-4 py-2.5 text-slate-400">{m.marketplace}</td>
                        <td className="px-4 py-2.5 text-right text-red-400">{m.failure_count}</td>
                        <td className="px-4 py-2.5 text-right text-green-400">{m.fallback_success_count}</td>
                        <td className="px-4 py-2.5 font-mono text-green-400 max-w-xs truncate">
                          {m.fallback_pattern ?? <span className="text-slate-600">—</span>}
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          {m.skip_failed ? (
                            <span className="text-red-400">yes</span>
                          ) : (
                            <span className="text-slate-600">no</span>
                          )}
                        </td>
                        <td className="px-4 py-2.5">
                          <button
                            onClick={() => handleDeleteMemory(m.id)}
                            className="text-slate-600 hover:text-red-400 transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Test Collect Panel */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="font-medium text-white text-sm">Test Collect</div>
            <div className="text-xs text-slate-500">Run a headless test scrape from the UI</div>
          </div>
          <div className="flex gap-2">
            {["stubhub", "seatgeek"].map((mp) => (
              <button
                key={mp}
                onClick={() => handleTestCollect(mp)}
                disabled={testing}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[#1e2535] border border-[#2a3145] text-slate-300 rounded-lg hover:bg-[#2a3145] transition-colors disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                {mp}
              </button>
            ))}
          </div>
        </div>
        {testResult && (
          <pre className="text-xs text-slate-300 bg-[#0d1117] border border-[#2a3145] rounded p-3 overflow-x-auto max-h-48 whitespace-pre-wrap">
            {testResult}
          </pre>
        )}
      </Card>
    </div>
  );
}
