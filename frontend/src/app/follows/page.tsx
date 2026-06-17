"use client";

import { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import {
  Users, AlertTriangle, CheckCircle2, Clock, TrendingUp, RefreshCw,
} from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "https://backend-production-509f.up.railway.app";

type MPStatus = "POPULATED" | "PARTIAL_POPULATION" | "NO_ID" | "BLOCKED" | "DEFERRED" | "ERROR" | "UNKNOWN";

interface FollowEvent {
  event_id: number;
  title: string;
  artist: string;
  event_date: string | null;
  status: string;
  hours_until_event: number | null;
  source: string;
  population: {
    overall: string;
    per_marketplace: Record<string, MPStatus>;
    partial_warnings: string[];
  };
  history: {
    hours_tracked: number;
    snap_count: number;
    floor_price: number | null;
  };
  intelligence: {
    eligibility: "eligible" | "partial" | "not_eligible";
    hours_until_eligible: number | null;
    reason: string;
  };
}

interface Follow {
  id: number;
  entity_type: string;
  entity_key: string;
  display_name: string;
  scope_type: string;
  status: string;
}

interface FollowEventsSummary {
  total_events: number;
  fully_populated: number;
  partial_population: number;
  empty: number;
  intelligence_eligible: number;
  intelligence_partial: number;
  intelligence_not_eligible: number;
}

const MP_COLORS: Record<string, string> = {
  POPULATED:         "bg-emerald-900/50 text-emerald-300 border-emerald-700/50",
  PARTIAL_POPULATION: "bg-amber-900/50 text-amber-300 border-amber-700/50",
  NO_ID:             "bg-zinc-800/60 text-zinc-400 border-zinc-700/50",
  BLOCKED:           "bg-red-900/30 text-red-400 border-red-800/50",
  DEFERRED:          "bg-blue-900/30 text-blue-400 border-blue-700/50",
  ERROR:             "bg-red-900/50 text-red-300 border-red-700/50",
  UNKNOWN:           "bg-zinc-800/40 text-zinc-500 border-zinc-700/30",
};

const MP_LABELS: Record<string, string> = {
  gametime: "GT", stubhub: "SH", tickpick: "TP", vividseats: "VS",
};

const ELIG_STYLES: Record<string, string> = {
  eligible:     "text-emerald-400",
  partial:      "text-amber-400",
  not_eligible: "text-zinc-500",
};

function MPChip({ slug, st }: { slug: string; st: MPStatus }) {
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-mono border ${MP_COLORS[st] ?? MP_COLORS.UNKNOWN}`}>
      {MP_LABELS[slug] ?? slug.toUpperCase()}&nbsp;<span className="opacity-70">{st.replace("_", "·")}</span>
    </span>
  );
}

export default function FollowsPage() {
  const [follows, setFollows] = useState<Follow[]>([]);
  const [eventsData, setEventsData] = useState<{ summary: FollowEventsSummary; events: FollowEvent[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acquiring, setAcquiring] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [fRes, eRes] = await Promise.all([
        fetch(`${BASE}/api/follows`, { cache: "no-store" }),
        fetch(`${BASE}/api/follows/events`, { cache: "no-store" }),
      ]);
      if (!fRes.ok) throw new Error(`follows ${fRes.status}`);
      if (!eRes.ok) throw new Error(`follows/events ${eRes.status}`);
      setFollows(await fRes.json());
      setEventsData(await eRes.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function triggerAcquire() {
    setAcquiring(true);
    try {
      await fetch(`${BASE}/api/follows/acquire/sync`, { method: "POST", cache: "no-store" });
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAcquiring(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-500 text-sm pt-8">
        <RefreshCw size={14} className="animate-spin" />
        Loading follows…
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-sm pt-8 flex items-center gap-2">
        <AlertTriangle size={14} />
        {error}
      </div>
    );
  }

  const summary = eventsData?.summary;
  const events  = eventsData?.events ?? [];

  // Group events by artist
  const byArtist: Record<string, FollowEvent[]> = {};
  for (const ev of events) {
    const key = ev.artist ?? ev.title ?? "Unknown";
    if (!byArtist[key]) byArtist[key] = [];
    byArtist[key].push(ev);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users size={16} className="text-slate-400" />
          <h1 className="text-base font-semibold text-slate-200">Follows</h1>
          <span className="text-xs text-slate-500">{follows.length} active</span>
        </div>
        <button
          onClick={triggerAcquire}
          disabled={acquiring}
          className="flex items-center gap-1.5 text-xs text-white/60 hover:text-white bg-white/5 hover:bg-white/10 border border-white/8 rounded-lg px-3 py-1.5 transition-all disabled:opacity-40"
        >
          <RefreshCw size={12} className={acquiring ? "animate-spin" : ""} />
          {acquiring ? "Acquiring…" : "Refresh Acquisition"}
        </button>
      </div>

      {/* Summary chips */}
      {summary && (
        <div className="flex flex-wrap gap-2">
          <SummaryChip label="Total events" value={summary.total_events} color="text-slate-300" />
          <SummaryChip label="Fully populated" value={summary.fully_populated} color="text-emerald-400" />
          <SummaryChip label="Partial population" value={summary.partial_population} color="text-amber-400" />
          <SummaryChip label="Intel eligible" value={summary.intelligence_eligible} color="text-sky-400" />
          <SummaryChip label="Intel partial" value={summary.intelligence_partial} color="text-violet-400" />
          <SummaryChip label="Not eligible" value={summary.intelligence_not_eligible} color="text-zinc-500" />
        </div>
      )}

      {/* Partial population warning banner */}
      {summary && summary.partial_population > 0 && (
        <div className="flex items-start gap-2 bg-amber-950/40 border border-amber-800/40 rounded-lg px-4 py-3">
          <AlertTriangle size={14} className="text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-300">
            <span className="font-medium">{summary.partial_population} event{summary.partial_population !== 1 ? "s" : ""} with partial marketplace coverage.</span>
            {" "}Ingestion is not complete — some marketplaces are NO_ID or BLOCKED. Run acquisition again or check marketplace resolver logs.
          </div>
        </div>
      )}

      {/* Active follows */}
      <div>
        <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Followed Artists / Teams</h2>
        <div className="flex flex-wrap gap-2">
          {follows.map((f) => (
            <div key={f.id} className="bg-white/5 border border-white/8 rounded-lg px-3 py-2 text-xs">
              <span className="text-slate-200 font-medium">{f.display_name}</span>
              <span className="text-slate-500 ml-2">{f.scope_type}</span>
              <span className="text-slate-600 ml-2">{f.entity_type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Events by artist */}
      {Object.entries(byArtist).map(([artist, artistEvents]) => (
        <div key={artist}>
          <h2 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2">
            {artist}
            <span className="text-zinc-600 normal-case font-normal">{artistEvents.length} event{artistEvents.length !== 1 ? "s" : ""}</span>
          </h2>
          <div className="space-y-2">
            {artistEvents.map((ev) => (
              <FollowEventRow key={ev.event_id} ev={ev} />
            ))}
          </div>
        </div>
      ))}

      {events.length === 0 && (
        <div className="text-zinc-600 text-sm text-center py-12">
          No follow-acquired events yet. Add a follow and trigger acquisition.
        </div>
      )}
    </div>
  );
}

function SummaryChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-white/4 border border-white/6 rounded-lg px-3 py-1.5 text-xs">
      <span className={`font-semibold tabular-nums ${color}`}>{value}</span>
      <span className="text-slate-500 ml-1.5">{label}</span>
    </div>
  );
}

function FollowEventRow({ ev }: { ev: FollowEvent }) {
  const overallOk = ev.population.overall === "POPULATED";
  const partialPop = ev.population.overall === "PARTIAL_POPULATION";

  return (
    <div className={`bg-white/3 border rounded-lg px-4 py-3 space-y-2 ${partialPop ? "border-amber-800/30" : "border-white/6"}`}>
      {/* Row 1: title + date + status */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <span className="text-sm text-slate-200 font-medium truncate block">{ev.title}</span>
          {ev.event_date && (
            <span className="text-xs text-slate-500">
              {format(parseISO(ev.event_date), "EEE MMM d, yyyy")}
              {ev.hours_until_event != null && ev.hours_until_event > 0 && (
                <span className="ml-1 text-zinc-600">({Math.round(ev.hours_until_event)}h away)</span>
              )}
              {ev.hours_until_event != null && ev.hours_until_event <= 0 && (
                <span className="ml-1 text-zinc-600">(past)</span>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {overallOk ? (
            <CheckCircle2 size={13} className="text-emerald-400" />
          ) : partialPop ? (
            <AlertTriangle size={13} className="text-amber-400" />
          ) : null}
          {ev.history.floor_price != null && (
            <span className="text-xs text-slate-400 font-mono">${ev.history.floor_price.toFixed(0)} floor</span>
          )}
        </div>
      </div>

      {/* Row 2: marketplace chips */}
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(ev.population.per_marketplace).map(([slug, st]) => (
          <MPChip key={slug} slug={slug} st={st} />
        ))}
      </div>

      {/* Row 3: partial warnings */}
      {ev.population.partial_warnings.length > 0 && (
        <div className="text-[10px] text-amber-500/80">
          {ev.population.partial_warnings.join(" · ")}
        </div>
      )}

      {/* Row 4: intelligence eligibility */}
      <div className="flex items-center gap-2 text-[10px]">
        <TrendingUp size={10} className="text-zinc-500" />
        <span className={ELIG_STYLES[ev.intelligence.eligibility]}>
          {ev.intelligence.eligibility.replace("_", " ")}
        </span>
        <span className="text-zinc-600">·</span>
        <Clock size={10} className="text-zinc-600" />
        <span className="text-zinc-500">{ev.history.hours_tracked}h tracked</span>
        {ev.intelligence.hours_until_eligible != null && ev.intelligence.hours_until_eligible > 0 && (
          <>
            <span className="text-zinc-600">·</span>
            <span className="text-zinc-600">{ev.intelligence.hours_until_eligible}h until eligible</span>
          </>
        )}
      </div>
    </div>
  );
}
