"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  BarChart2,
  Clock,
  Database,
  Users,
  EyeOff,
  RotateCcw,
  Info,
  ParkingCircle,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { api } from "@/lib/api";
import type {
  HeroResponse,
  MarketResponse,
  HistoryResponse,
  HistoryWindow,
  SectionsResponse,
  SellerResponse,
  EventMeta,
  BaselineResponse,
} from "@/lib/types";
import {
  fmt$$, fmtNum, fmtPct, fmtDelta, cn,
  signalToAction, actionColors, signalDescription, lifecycleContext,
  CONSUMER_LABELS,
} from "@/lib/utils";
import { getEventGradient, gradientBg } from "@/lib/entityimages";
import ActionSignal from "@/components/ui/ActionSignal";
import PriceHistoryChart from "@/components/charts/PriceHistoryChart";
import { useExclusions } from "@/hooks/useExclusions";
import VenueIntelligence from "@/components/venue/VenueIntelligence";

// ── Shared micro-components ───────────────────────────────────────────────────
function ScoreMeter({
  label,
  value,
  color = "#60a5fa",
  note,
}: {
  label: string;
  value: number | null | undefined;
  color?: string;
  note?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value ?? 0) * 100));
  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1.5">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 tabular-nums font-medium">
          {value != null ? (value > 1 ? value.toFixed(1) : (value * 100).toFixed(0) + "%") : "—"}
        </span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.min(pct, 100)}%`, background: color }}
        />
      </div>
      {note && <p className="text-[10px] text-slate-600 mt-1">{note}</p>}
    </div>
  );
}

function InventoryTrendMeter({
  delta,
  total,
}: {
  delta?: number | null;
  total?: number | null;
}) {
  const noData = delta == null;
  const isShrinking = !noData && delta! < 0;
  const isGrowing  = !noData && delta! > 0;
  const pct = noData
    ? 0
    : Math.min((Math.abs(delta!) / Math.max(total ?? 100, 1)) * 5 * 100, 100);
  const color = isShrinking ? "#f87171" : isGrowing ? "#34d399" : "#60a5fa";

  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1.5">
        <span className="text-slate-400">Inventory Trend</span>
        <span
          className="font-medium tabular-nums"
          style={{ color: noData ? undefined : color }}
        >
          {noData
            ? "—"
            : `${delta! > 0 ? "+" : ""}${delta!.toLocaleString("en-US")} 24h`}
        </span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      {!noData && (
        <p className="text-[10px] text-slate-600 mt-1">
          {isShrinking ? "Inventory tightening" : "Inventory growing"}
        </p>
      )}
    </div>
  );
}

function DeltaChip({ pct, size = "sm" }: { pct: number | null | undefined; size?: "sm" | "md" }) {
  if (pct == null) return <span className="text-slate-600 text-[11px]">—</span>;
  const up = pct > 0;
  const Icon = up ? TrendingUp : pct < 0 ? TrendingDown : Minus;
  const textSize = size === "md" ? "text-sm" : "text-[11px]";
  return (
    <span className={cn("inline-flex items-center gap-0.5 font-medium", textSize,
      up ? "text-emerald-400" : pct < 0 ? "text-red-400" : "text-slate-500")}>
      <Icon size={size === "md" ? 13 : 10} />
      {fmtPct(pct)}
    </span>
  );
}

function StatCard({ label, value, sub, accent }: {
  label: string; value: React.ReactNode; sub?: string; accent?: string;
}) {
  return (
    <div className="rounded-xl bg-white/4 px-3 py-3">
      <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</div>
      <div className={cn("text-sm font-semibold", accent ?? "text-slate-100")}>{value}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

// ── Tabs config ───────────────────────────────────────────────────────────────
type Tab = "overview" | "market" | "history" | "sections" | "seller" | "venue";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "overview",  label: "Overview",   icon: TrendingUp },
  { id: "market",    label: "Market",     icon: BarChart2 },
  { id: "history",   label: "History",    icon: Clock },
  { id: "sections",  label: "Sections",   icon: Database },
  { id: "seller",    label: "Sellers",    icon: Users },
  { id: "venue",     label: "Venue",      icon: Info },
];

const WINDOWS: { id: HistoryWindow; label: string; minDays: number }[] = [
  { id: "24h",  label: "24 Hours",  minDays: 0 },
  { id: "7d",   label: "7 Days",    minDays: 3 },
  { id: "14d",  label: "14 Days",   minDays: 7 },
  { id: "30d",  label: "30 Days",   minDays: 14 },
  { id: "all",  label: "All Data",  minDays: 0 },
];

// ── Main page ─────────────────────────────────────────────────────────────────
export default function EventDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [tab, setTab] = useState<Tab>("overview");
  const [histWindow, setHistWindow] = useState<HistoryWindow>("7d");

  const [eventMeta, setEventMeta] = useState<EventMeta | null>(null);
  const [hero, setHero] = useState<HeroResponse | null>(null);
  const [market, setMarket] = useState<MarketResponse | null>(null);
  const [baseline, setBaseline] = useState<BaselineResponse | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [sections, setSections] = useState<SectionsResponse | null>(null);
  const [seller, setSeller] = useState<SellerResponse | null>(null);

  const [loading, setLoading] = useState<Partial<Record<string, boolean>>>({});
  const [errors, setErrors]   = useState<Partial<Record<string, string>>>({}); // eslint-disable-line

  // Venue intelligence is rendered lazily in VenueIntelligence component — no extra state needed here

  // Exclusion workflow (localStorage — see useExclusions.ts for backend dependency note)
  const { exclude, restore, isExcluded, items: excludedItems, mounted: exclMounted } = useExclusions(id);

  const setLoad = (k: string, v: boolean) => setLoading((p) => ({ ...p, [k]: v }));
  const setErr  = (k: string, v: string | null) => setErrors((p) => ({ ...p, [k]: v ?? undefined }));

  useEffect(() => {
    if (!id) return;
    setLoad("hero", true);
    setLoad("meta", true);
    Promise.all([
      api.events.hero(id).then(setHero).catch((e) => setErr("hero", String(e))).finally(() => setLoad("hero", false)),
      api.events.meta(id).then(setEventMeta).catch(() => {}).finally(() => setLoad("meta", false)),
    ]);
  }, [id]);

  const loadTab = useCallback(async (t: Tab) => {
    if (!id) return;
    setLoad(t, true);
    setErr(t, null);
    try {
      if (t === "market") {
        const [m, b] = await Promise.allSettled([api.events.market(id), api.analytics.baseline(id)]);
        if (m.status === "fulfilled") setMarket(m.value);
        if (b.status === "fulfilled") setBaseline(b.value);
      }
      if (t === "history")  setHistory(await api.events.history(id, histWindow));
      if (t === "sections") setSections(await api.events.sections(id));
      if (t === "seller")   setSeller(await api.events.seller(id));
    } catch (e) {
      setErr(t, String(e));
    } finally {
      setLoad(t, false);
    }
  }, [id, histWindow]);

  useEffect(() => {
    if (tab !== "overview") loadTab(tab);
  }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (tab !== "history" || !id) return;
    setLoad("history_win", true);
    api.events.history(id, histWindow)
      .then(setHistory)
      .catch((e) => setErr("history", String(e)))
      .finally(() => setLoad("history_win", false));
  }, [histWindow, id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Derived values ──────────────────────────────────────────────────────────
  const title     = eventMeta?.title ?? `Event #${id}`;
  const venue     = eventMeta?.venue_name ?? eventMeta?.venue;
  const dateStr   = eventMeta?.event_date;
  const artist    = eventMeta?.artist;
  const gradient  = getEventGradient(artist, title);
  const action    = signalToAction(hero?.signal);
  const aColors   = actionColors(action);

  const daysOut: number | null = hero?.days_until_event ?? null;
  let dateLabel = "";
  if (dateStr) {
    try { dateLabel = format(parseISO(dateStr), "EEEE, MMMM d, yyyy"); } catch {}
  }

  // ── Hero ────────────────────────────────────────────────────────────────────
  function renderHero() {
    return (
      <div
        className="rounded-2xl overflow-hidden border border-white/8 mb-6"
        style={{ background: gradientBg(gradient, "high") }}
      >
        <div
          className="relative"
          style={{
            background: "linear-gradient(to right, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.45) 45%, rgba(0,0,0,0.75) 100%)",
          }}
        >
          <div className="flex flex-col sm:flex-row items-stretch p-6 gap-6">

            {/* LEFT — event identity */}
            <div className="flex-1 flex flex-col justify-center">
              {artist && (
                <p className="text-[11px] text-white/45 uppercase tracking-widest font-semibold mb-1">{artist}</p>
              )}
              <h1 className="text-xl font-bold text-white leading-tight mb-2">{title}</h1>
              {venue && <p className="text-sm text-white/55 mb-1">{venue}</p>}
              {dateLabel && <p className="text-sm text-white/45">{dateLabel}</p>}
              {daysOut != null && (
                <div className="mt-3 flex items-center gap-2">
                  <span
                    className="text-xs font-semibold px-2.5 py-1 rounded-full border"
                    style={{ color: aColors.text, background: aColors.bg, borderColor: aColors.border }}
                  >
                    {daysOut < 1 ? "Today" : daysOut < 2 ? "Tomorrow" : `${Math.round(daysOut)} days away`}
                  </span>
                </div>
              )}
            </div>

            {/* CENTER — action signal */}
            <div className="flex flex-col items-center justify-center flex-shrink-0 px-2">
              {loading.hero ? (
                <div className="w-36 h-20 rounded-2xl bg-white/5 animate-pulse" />
              ) : (
                <ActionSignal
                  action={action}
                  size="lg"
                  description={signalDescription(hero?.signal)}
                />
              )}
            </div>

            {/* RIGHT — prices + inventory */}
            <div className="flex flex-col justify-center gap-4 flex-shrink-0">
              {/* price band */}
              <div>
                <p className="text-[10px] text-white/35 uppercase tracking-wider mb-2">Price Range</p>
                <div className="space-y-1">
                  {[
                    { label: "Low",    val: hero?.price?.low_ask,    bold: true  },
                    { label: "Median", val: hero?.price?.median_ask, bold: false },
                    { label: "High",   val: hero?.price?.high_ask,   bold: false },
                  ].map(({ label, val, bold }) => (
                    <div key={label} className="flex items-baseline justify-between gap-6">
                      <span className="text-[10px] text-white/35 w-10">{label}</span>
                      <span className={cn("tabular-nums", bold ? "text-lg font-bold text-white" : "text-sm text-white/65")}>
                        {fmt$$(val)}
                      </span>
                    </div>
                  ))}
                </div>
                {hero?.changes?.h24?.price_delta_pct != null && (
                  <div className="mt-1.5">
                    <DeltaChip pct={hero.changes.h24.price_delta_pct} size="md" />
                    <span className="text-[10px] text-white/35 ml-1">24h</span>
                  </div>
                )}
              </div>

              {/* inventory */}
              <div className="border-t border-white/10 pt-3">
                <p className="text-[10px] text-white/35 uppercase tracking-wider mb-1">Inventory</p>
                <p className="text-sm font-semibold text-white/80">
                  {fmtNum(hero?.inventory?.total_listings)} listings
                </p>
                {hero?.changes?.h24?.inventory_delta != null && (
                  <p className={cn("text-[11px] mt-0.5 tabular-nums font-medium",
                    (hero.changes.h24.inventory_delta ?? 0) > 0 ? "text-emerald-400" : "text-red-400"
                  )}>
                    {fmtDelta(hero.changes.h24.inventory_delta)} in 24h
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* below-hero: Deal Score · Seller Pressure · Inventory Trend */}
          {hero && (
            <div className="px-6 pb-5 grid grid-cols-3 gap-3">
              <ScoreMeter
                label={CONSUMER_LABELS.opportunity_score}
                value={hero.opportunity_score}
                color={aColors.text}
              />
              <ScoreMeter
                label={CONSUMER_LABELS.seller_aggression}
                value={hero.market?.seller_aggression}
                color="#fb923c"
              />
              <InventoryTrendMeter
                delta={hero.changes?.h24?.inventory_delta}
                total={hero.inventory?.total_listings}
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Tabs ────────────────────────────────────────────────────────────────────
  function renderOverview() {
    if (loading.hero) return <Spinner />;
    if (errors.hero) return <ErrBox msg={errors.hero} />;
    if (!hero) return null;

    const changes = hero.changes ?? {};
    const lifecycleTxt = lifecycleContext(daysOut, hero.signal, changes.h24?.inventory_delta);

    return (
      <div className="space-y-6">
        {lifecycleTxt && (
          <div className="rounded-xl border border-white/7 bg-[#161b27] px-4 py-3">
            <p className="text-xs text-slate-400 leading-relaxed">{lifecycleTxt}</p>
          </div>
        )}

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">What Changed</h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <StatCard
              label="Price (24h)"
              value={<DeltaChip pct={changes.h24?.price_delta_pct} size="md" />}
              sub={changes.h24?.price_delta != null ? `${fmtDelta(Math.round(changes.h24.price_delta))} median` : undefined}
            />
            <StatCard
              label="Inventory (24h)"
              value={
                <span className={cn("text-sm font-semibold",
                  (changes.h24?.inventory_delta ?? 0) > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {fmtDelta(changes.h24?.inventory_delta)}
                </span>
              }
              sub="listings added/removed"
            />
            <StatCard label="Lowest Price"  value={fmt$$(hero.price?.low_ask)} />
            <StatCard label="Median Price" value={fmt$$(hero.price?.median_ask)} />
          </div>
        </div>

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Price Distribution</h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { label: "Lowest",  val: hero.price?.low_ask },
              { label: "25th %",  val: hero.price?.p25_ask },
              { label: "Median",  val: hero.price?.median_ask },
              { label: "75th %",  val: hero.price?.p75_ask },
              { label: "Highest", val: hero.price?.high_ask },
            ].map(({ label, val }) => (
              <StatCard key={label} label={label} value={fmt$$(val)} />
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Price Changes Over Time</h3>
          <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/5">
                  {["Window", "Price Change", "Inventory Change"].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(["h24", "d7", "d14", "d30"] as const).map((w) => {
                  const c = changes[w];
                  const labels: Record<string, string> = { h24: "24 Hours", d7: "7 Days", d14: "14 Days", d30: "30 Days" };
                  return (
                    <tr key={w} className="border-b border-white/4 last:border-0 hover:bg-white/2">
                      <td className="px-4 py-2.5 text-slate-400 font-medium">{labels[w]}</td>
                      <td className="px-4 py-2.5"><DeltaChip pct={c?.price_delta_pct} /></td>
                      <td className="px-4 py-2.5">
                        <span className={cn("text-[11px] tabular-nums font-medium",
                          c?.inventory_delta == null ? "text-slate-600" :
                          (c.inventory_delta ?? 0) > 0 ? "text-emerald-400" : "text-red-400"
                        )}>
                          {fmtDelta(c?.inventory_delta)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Market Intelligence</h3>
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-4 space-y-3.5">
            <ScoreMeter label={CONSUMER_LABELS.tightness}          value={hero.market?.tightness}          color="#f87171" />
            <ScoreMeter label={CONSUMER_LABELS.seller_aggression}  value={hero.market?.seller_aggression}  color="#fb923c" />
            <ScoreMeter label={CONSUMER_LABELS.capitulation_score} value={hero.market?.capitulation_score} color="#34d399" />
            <ScoreMeter label={CONSUMER_LABELS.velocity}           value={
              hero.market?.velocity != null ? Math.min(hero.market.velocity / 50, 1) : null
            } color="#60a5fa" />
            <ScoreMeter label={CONSUMER_LABELS.reprice_rate}       value={hero.rates?.reprice_rate}        color="#a78bfa" />
          </div>
        </div>

        {hero.history_context?.data_note && (
          <p className="text-[11px] text-slate-600 italic">{hero.history_context.data_note}</p>
        )}
      </div>
    );
  }

  function renderMarket() {
    if (loading.market) return <Spinner />;
    if (errors.market) return <ErrBox msg={errors.market} />;
    if (!market) return null;

    const dist = market.price_distribution;
    const move = market.inventory_movement;

    return (
      <div className="space-y-5">
        {/* Market overview summary strip */}
        {(market.trends?.price_change_24h_pct != null || market.inventory_movement?.net_change_24h != null) && (
          <div className="grid grid-cols-2 gap-2">
            {market.trends?.price_change_24h_pct != null && (
              <div className="rounded-xl border border-white/7 bg-[#161b27] px-4 py-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Price (24h)</p>
                <div className="flex items-center gap-1.5">
                  {market.trends.price_change_24h_pct > 0
                    ? <TrendingUp size={14} className="text-emerald-400" />
                    : market.trends.price_change_24h_pct < 0
                    ? <TrendingDown size={14} className="text-red-400" />
                    : <Minus size={14} className="text-slate-500" />}
                  <span className={cn("text-sm font-semibold tabular-nums",
                    market.trends.price_change_24h_pct > 0 ? "text-emerald-400" :
                    market.trends.price_change_24h_pct < 0 ? "text-red-400" : "text-slate-400"
                  )}>
                    {market.trends.price_change_24h_pct > 0 ? "+" : ""}
                    {market.trends.price_change_24h_pct.toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-slate-600">overall</span>
                </div>
              </div>
            )}
            {market.inventory_movement?.net_change_24h != null && (
              <div className="rounded-xl border border-white/7 bg-[#161b27] px-4 py-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Inventory (24h)</p>
                <div className="flex items-center gap-1.5">
                  {(market.inventory_movement.net_change_24h ?? 0) > 0
                    ? <TrendingUp size={14} className="text-emerald-400" />
                    : <TrendingDown size={14} className="text-red-400" />}
                  <span className={cn("text-sm font-semibold tabular-nums",
                    (market.inventory_movement.net_change_24h ?? 0) > 0 ? "text-emerald-400" : "text-red-400"
                  )}>
                    {fmtDelta(market.inventory_movement.net_change_24h)}
                  </span>
                  <span className="text-[10px] text-slate-600">listings</span>
                </div>
              </div>
            )}
          </div>
        )}

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Marketplaces</h3>
          {/* Marketplace cards */}
          <div className="space-y-2">
            {(market.marketplaces ?? []).map((mp, i) => {
              const sharePct = mp.share_of_inventory != null ? mp.share_of_inventory * 100 : null;
              // merge baseline listings_change_24h for this marketplace
              const mpSlug = mp.name.toLowerCase().replace(/\s+/g, "");
              const bLine = baseline?.per_marketplace?.find(
                (b) => b.marketplace_slug === mpSlug || b.marketplace_slug.replace(/\s+/g, "") === mpSlug
              );
              const listDelta = bLine?.listings_change_24h?.absolute;
              return (
                <div key={i} className="rounded-xl border border-white/7 bg-[#161b27] p-3">
                  <div className="flex items-center justify-between mb-2.5">
                    <span className="text-sm font-semibold text-slate-200">{mp.name}</span>
                    <div className="flex items-center gap-2">
                      {listDelta != null && (
                        <span className={cn("text-[10px] tabular-nums font-medium",
                          listDelta > 0 ? "text-emerald-500" : listDelta < 0 ? "text-red-500" : "text-slate-600"
                        )}>
                          {listDelta > 0 ? "+" : ""}{listDelta} 24h
                        </span>
                      )}
                      {sharePct != null && (
                        <span className="text-[10px] text-slate-500 tabular-nums">{sharePct.toFixed(0)}% of market</span>
                      )}
                    </div>
                  </div>
                  {/* Share bar */}
                  {sharePct != null && (
                    <div className="h-0.5 bg-white/5 rounded-full mb-3 overflow-hidden">
                      <div className="h-full bg-blue-500/50 rounded-full" style={{ width: `${Math.min(sharePct, 100)}%` }} />
                    </div>
                  )}
                  <div className="grid grid-cols-4 gap-3">
                    <div>
                      <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Lowest Price</p>
                      <p className="text-xs font-semibold text-slate-200 tabular-nums">{fmt$$(mp.low_ask)}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Median Price</p>
                      <p className="text-xs font-semibold text-slate-200 tabular-nums">{fmt$$(mp.median_ask)}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Highest Price</p>
                      <p className="text-xs text-slate-400 tabular-nums">{fmt$$(mp.high_ask)}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Listings</p>
                      <p className="text-xs text-slate-400 tabular-nums">{fmtNum(mp.listings)}</p>
                    </div>
                  </div>
                  {mp.liquidity_score != null && (
                    <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px]">
                      <span className="text-slate-600">Coverage Score</span>
                      <span className="text-slate-500 tabular-nums">{mp.liquidity_score.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Marketplace Coverage — freshness status per marketplace */}
        {eventMeta?.marketplace_freshness && Object.keys(eventMeta.marketplace_freshness).length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Marketplace Coverage</h3>
            <div className="rounded-xl border border-white/7 bg-[#161b27] p-3 space-y-2">
              {(["stubhub", "gametime", "tickpick", "vividseats"] as const).map((slug) => {
                const f = eventMeta.marketplace_freshness?.[slug];
                const tracked = eventMeta.tracked_events?.find((t) => t.marketplace_slug === slug);
                const displayName = slug === "stubhub" ? "StubHub" : slug === "gametime" ? "Gametime" : slug === "tickpick" ? "TickPick" : "Vivid Seats";
                if (!f) return null;
                const freshColor = f.freshness_status === "fresh" ? "text-emerald-400" : f.freshness_status === "late" ? "text-amber-400" : "text-red-400";
                const freshDot = f.freshness_status === "fresh" ? "bg-emerald-400" : f.freshness_status === "late" ? "bg-amber-400" : "bg-red-400";
                const ageLabel = f.age_minutes != null ? (f.age_minutes < 60 ? `${f.age_minutes}m ago` : `${Math.round(f.age_minutes / 60)}h ago`) : null;
                return (
                  <div key={slug} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${freshDot}`} />
                      <span className="text-xs text-slate-300">{displayName}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {ageLabel && <span className="text-[10px] text-slate-600">{ageLabel}</span>}
                      <span className={`text-[10px] font-medium capitalize ${freshColor}`}>{f.freshness_status}</span>
                      {tracked?.external_url && (
                        <a href={tracked.external_url} target="_blank" rel="noopener noreferrer"
                          className="text-[10px] text-blue-500 hover:text-blue-400 transition-colors">
                          View ↗
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
              {/* Add URL placeholder */}
              <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between">
                <span className="text-[10px] text-slate-600">Add marketplace URL</span>
                <span className="text-[10px] text-slate-700 italic">Coming soon</span>
              </div>
            </div>
          </div>
        )}

        {dist && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Price Distribution</h3>
            <div className="rounded-xl border border-white/7 bg-[#161b27] p-4">
              <div className="grid grid-cols-5 gap-2">
                {(["p10","p25","p50","p75","p90"] as const).map((k) => (
                  <div key={k} className="text-center">
                    <div className="text-[10px] text-slate-500 mb-1 uppercase">{k}</div>
                    <div className="text-xs font-semibold text-slate-200">{fmt$$(dist[k])}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Inventory Movement (24 Hours)</h3>
          <div className="grid grid-cols-3 gap-2">
            <StatCard label="New Listings"  value={<span className="text-emerald-400">{fmtDelta(move?.new_24h)}</span>} />
            <StatCard label="Removed"       value={<span className="text-red-400">{fmtDelta(move?.removed_24h)}</span>} />
            <StatCard
              label="Net Change"
              value={
                <span className={cn((move?.net_change_24h ?? 0) > 0 ? "text-emerald-400" : "text-red-400")}>
                  {fmtDelta(move?.net_change_24h)}
                </span>
              }
            />
          </div>
        </div>

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Market Heat</h3>
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-4 space-y-3">
            <ScoreMeter label="Overall Heat"              value={market.market_stress?.composite_score} color="#fb923c" />
            <ScoreMeter label={CONSUMER_LABELS.tightness} value={market.market_stress?.tightness}       color="#f87171" />
            <ScoreMeter label="Price Cutting Activity"    value={market.market_stress?.capitulation}    color="#34d399" />
          </div>
        </div>
      </div>
    );
  }

  function renderHistory() {
    const isLoading = !!(loading.history || loading.history_win);
    if (loading.history && !history) return <Spinner />;
    if (errors.history) return <ErrBox msg={errors.history} />;

    const src = history?.source;
    const depthDays = history?.data_depth_days ?? 0;
    const latest = history?.series?.slice(-1)[0];
    const first  = history?.series?.[0];
    const priceDeltaPct = (latest?.median_ask && first?.median_ask && first.median_ask > 0)
      ? ((latest.median_ask - first.median_ask) / first.median_ask) * 100
      : null;

    return (
      <div className="space-y-4">
        <div className={cn(
          "rounded-xl border px-4 py-3 flex items-center justify-between",
          src === "combined"
            ? "bg-emerald-500/8 border-emerald-500/20"
            : src === "live"
            ? "bg-amber-500/8 border-amber-500/20"
            : "bg-blue-500/8 border-blue-500/20"
        )}>
          <div>
            <p className={cn("text-sm font-semibold",
              src === "combined" ? "text-emerald-400" :
              src === "live" ? "text-amber-400" : "text-blue-400"
            )}>
              {src === "combined"
                ? `${Math.round(depthDays)} days of history`
                : src === "live"
                ? "Live data only"
                : `${Math.round(depthDays)} days of archive data`}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {src === "combined"
                ? "Archive history combined with live data"
                : src === "live"
                ? "Limited trend signal — collecting history"
                : "Historical archive data"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] text-slate-500">{history?.point_count ?? 0} data points</p>
            {history?.bucket_size && (
              <p className="text-[10px] text-slate-600">{history.bucket_size} intervals</p>
            )}
          </div>
        </div>

        {latest && (
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Lowest Price",  val: latest.low_ask,    delta: null as number | null },
              { label: "Median Price",  val: latest.median_ask, delta: priceDeltaPct },
              { label: "Highest Price", val: latest.high_ask,   delta: null as number | null },
            ].map(({ label, val, delta }) => (
              <div key={label} className="rounded-xl bg-white/4 border border-white/5 px-3 py-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
                <p className="text-lg font-bold text-slate-100">{fmt$$(val)}</p>
                {delta != null && (
                  <div className="mt-1">
                    <DeltaChip pct={delta} />
                    <span className="text-[10px] text-slate-600 ml-1">over window</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
            {WINDOWS.map((w) => {
              const unavail = depthDays > 0 && depthDays < w.minDays;
              return (
                <button
                  key={w.id}
                  onClick={() => setHistWindow(w.id)}
                  disabled={isLoading}
                  className={cn(
                    "px-3 py-1.5 transition-colors whitespace-nowrap",
                    histWindow === w.id
                      ? "bg-white/10 text-slate-200"
                      : unavail
                      ? "text-slate-700 cursor-default"
                      : "text-slate-500 hover:text-slate-300 hover:bg-white/5",
                  )}
                >
                  {w.label}
                </button>
              );
            })}
          </div>
          {isLoading && <RefreshCw size={12} className="animate-spin text-slate-500" />}
        </div>

        {history?.series?.length ? (
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-4">
            <PriceHistoryChart series={history.series} window={histWindow} height={280} />
          </div>
        ) : (
          !isLoading && (
            <div className="rounded-xl border border-white/7 bg-[#161b27] flex items-center justify-center h-48 text-slate-600 text-sm">
              No data for this window
            </div>
          )
        )}
      </div>
    );
  }

  function renderSections() {
    if (loading.sections) return <Spinner />;
    if (errors.sections) return <ErrBox msg={errors.sections} />;
    if (!sections?.sections?.length) return <ErrBox msg="No section data available." />;

    const allRows = sections.sections;
    // Partition into active / excluded (exclusion state hydrates from localStorage on mount)
    const activeRows  = exclMounted ? allRows.filter((s) => !isExcluded(s.display_name)) : allRows;
    const excludedRows = exclMounted ? allRows.filter((s) =>  isExcluded(s.display_name)) : [];

    const byValue  = [...activeRows].filter(s => s.value_score != null).sort((a, b) => (b.value_score ?? 0) - (a.value_score ?? 0)).slice(0, 3);
    const byDemand = [...activeRows].filter(s => s.activity_score != null).sort((a, b) => (b.activity_score ?? 0) - (a.activity_score ?? 0)).slice(0, 3);
    const byEntry  = [...activeRows].filter(s => s.low_ask != null && s.low_ask > 0).sort((a, b) => (a.low_ask ?? 999999) - (b.low_ask ?? 999999)).slice(0, 3);
    const byActive = [...activeRows].sort((a, b) => b.listings - a.listings).slice(0, 3);

    const MODULE_CLS = "rounded-xl border border-white/7 bg-[#161b27] p-3";

    function SectionModule({ title, items, accessor }: {
      title: string;
      items: typeof activeRows;
      accessor: (s: typeof activeRows[0]) => React.ReactNode;
    }) {
      return (
        <div className={MODULE_CLS}>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-2">{title}</p>
          <div className="space-y-2">
            {items.map((s, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-xs text-slate-300 truncate flex-1 mr-2">{s.display_name}</span>
                <span className="text-xs font-semibold text-slate-200 flex-shrink-0">{accessor(s)}</span>
              </div>
            ))}
            {items.length === 0 && <p className="text-xs text-slate-600">No data</p>}
          </div>
        </div>
      );
    }

    const TIER_COLORS: Record<string, string> = {
      floor: "text-amber-400", lower: "text-blue-400",
      upper: "text-slate-400", ga: "text-emerald-400", vip: "text-purple-400",
    };

    return (
      <div className="space-y-5">
        {/* backend dependency notice */}
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-blue-500/15 bg-blue-500/6">
          <Info size={12} className="text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="text-[11px] text-blue-400/80 leading-relaxed">
            Excluded sections are removed from this view.{" "}
            <span className="text-slate-600">
              Backend wiring required to exclude from intelligence calculations and hero metrics.
            </span>
          </p>
        </div>

        {/* exclusion count badge */}
        {excludedRows.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-amber-400 font-medium">
              {excludedRows.length} section{excludedRows.length !== 1 ? "s" : ""} excluded
            </span>
            <button
              onClick={() => excludedRows.forEach((s) => restore(s.display_name))}
              className="text-[10px] text-slate-600 hover:text-slate-400 underline"
            >
              Restore all
            </button>
          </div>
        )}

        {/* quick insight modules (active only) */}
        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Quick Insights</h3>
          <div className="grid grid-cols-2 gap-3">
            <SectionModule
              title="Best Value"
              items={byValue}
              accessor={(s) => <span className="text-emerald-400">{fmt$$(s.low_ask)}</span>}
            />
            <SectionModule
              title="Highest Demand"
              items={byDemand}
              accessor={(s) => <span className="text-red-400">{s.activity_score?.toFixed(1) ?? "—"}</span>}
            />
            <SectionModule
              title="Best Entry Price"
              items={byEntry}
              accessor={(s) => <span className="text-blue-400">{fmt$$(s.low_ask)}</span>}
            />
            <SectionModule
              title="Most Active"
              items={byActive}
              accessor={(s) => <span className="text-slate-300">{fmtNum(s.listings)}</span>}
            />
          </div>
        </div>

        {/* full active table */}
        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">
            All Sections
            <span className="text-slate-700 ml-2 font-normal normal-case">
              hover row to exclude
            </span>
          </h3>
          <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-x-auto">
            <table className="w-full text-xs min-w-[640px]">
              <thead>
                <tr className="border-b border-white/5">
                  {["Section", "Tier", "Listings", "Low", "Median", "High", "Value", "Activity", "", ""].map((h) => (
                    <th key={h} className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium last:w-8">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeRows.map((s, i) => {
                  const tierKey = (s.tier ?? "").toLowerCase();
                  return (
                    <tr key={i} className="group border-b border-white/4 last:border-0 hover:bg-white/2">
                      <td className="px-3 py-2 text-slate-200 font-medium max-w-[140px] truncate">{s.display_name}</td>
                      <td className={cn("px-3 py-2 capitalize text-[11px]", TIER_COLORS[tierKey] ?? "text-slate-500")}>
                        {s.tier ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-slate-400 tabular-nums">{fmtNum(s.listings)}</td>
                      <td className="px-3 py-2 text-slate-300 tabular-nums">{fmt$$(s.low_ask)}</td>
                      <td className="px-3 py-2 text-slate-300 tabular-nums">{fmt$$(s.median_ask)}</td>
                      <td className="px-3 py-2 text-slate-400 tabular-nums">{fmt$$(s.high_ask)}</td>
                      <td className="px-3 py-2 tabular-nums">
                        <span className={cn("font-medium",
                          (s.value_score ?? 0) > 7 ? "text-emerald-400" :
                          (s.value_score ?? 0) > 4 ? "text-blue-400" : "text-slate-500"
                        )}>
                          {s.value_score != null ? s.value_score.toFixed(1) : "—"}
                        </span>
                      </td>
                      <td className="px-3 py-2 tabular-nums">
                        <span className={cn("font-medium",
                          (s.activity_score ?? 0) > 5 ? "text-red-400" :
                          (s.activity_score ?? 0) > 2 ? "text-amber-400" : "text-slate-500"
                        )}>
                          {s.activity_score != null ? s.activity_score.toFixed(1) : "—"}
                        </span>
                      </td>
                      {/* exclude action — visible on row hover */}
                      <td className="px-2 py-2">
                        <button
                          onClick={() => exclude(s.display_name, "user_excluded")}
                          title="Exclude this section"
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/8 text-slate-600 hover:text-amber-400"
                        >
                          <EyeOff size={11} />
                        </button>
                      </td>
                      {/* parking action — visible on row hover */}
                      <td className="px-2 py-2">
                        <button
                          onClick={() => exclude(s.display_name, "parking")}
                          title="Move to Parking (exclude from analysis)"
                          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/8 text-slate-600 hover:text-blue-400"
                        >
                          <ParkingCircle size={11} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* excluded sections — audit trail */}
        {excludedRows.length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Excluded Sections</h3>
            <div className="rounded-xl border border-amber-500/15 bg-amber-500/5 overflow-hidden">
              <table className="w-full text-xs">
                <tbody>
                  {excludedRows.map((s, i) => {
                    const rec = excludedItems.find((e) => e.key === s.display_name);
                    return (
                      <tr key={i} className="border-b border-white/4 last:border-0">
                        <td className="px-3 py-2 text-slate-500 line-through">{s.display_name}</td>
                        <td className="px-3 py-2 text-slate-700 text-[10px]">
                          {rec?.reason ?? "excluded"}
                          {rec?.timestamp && (
                            <span className="ml-1 text-slate-800">
                              · {new Date(rec.timestamp).toLocaleDateString()}
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button
                            onClick={() => restore(s.display_name)}
                            className="inline-flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-300 transition-colors"
                          >
                            <RotateCcw size={9} />
                            Restore
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderSeller() {
    if (loading.seller) return <Spinner />;
    if (errors.seller) return <ErrBox msg={errors.seller} />;
    if (!seller) return null;

    const capScore = seller.capitulation_score ?? 0;
    const aggScore = seller.seller_aggression ?? 0;
    const churnVal = seller.churn_rate ?? 0;

    let sellerSummary = "";
    if (capScore > 0.7) sellerSummary = "Sellers are actively cutting prices. This is a buyer's market right now.";
    else if (aggScore > 0.6) sellerSummary = "Sellers are holding firm on pricing. Limited discounting activity.";
    else if (churnVal > 5) sellerSummary = "High listing turnover — inventory is moving quickly.";
    else sellerSummary = "Seller behavior is typical for this stage of the market.";

    return (
      <div className="space-y-5">
        <div className="rounded-xl border border-white/7 bg-[#161b27] px-4 py-3">
          <p className="text-xs text-slate-400 leading-relaxed">{sellerSummary}</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <StatCard label="New Listings (24h)"  value={<span className="text-emerald-400">{fmtDelta(seller.new_listings_24h)}</span>} />
          <StatCard label="Removed (24h)"       value={<span className="text-red-400">{fmtDelta(seller.removed_listings_24h)}</span>} />
          <StatCard label="Repriced (24h)"      value={fmtNum(seller.repriced_24h)} />
          <StatCard label="Price Drops"         value={<span className="text-emerald-400">{fmtNum(seller.price_drops_24h)}</span>} />
          <StatCard label="Price Increases"     value={<span className="text-red-400">{fmtNum(seller.price_gains_24h)}</span>} />
          <StatCard
            label="Median Price Change"
            value={
              seller.median_reprice_delta != null ? (
                <span className={seller.median_reprice_delta > 0 ? "text-emerald-400" : "text-red-400"}>
                  {fmtDelta(Math.round(seller.median_reprice_delta))}
                </span>
              ) : "—"
            }
          />
        </div>

        <div>
          <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">Seller Behavior</h3>
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-4 space-y-3.5">
            <ScoreMeter
              label={CONSUMER_LABELS.seller_aggression}
              value={seller.seller_aggression}
              color="#f87171"
              note={aggScore > 0.6 ? "Sellers holding on pricing" : undefined}
            />
            <ScoreMeter
              label="Price Cutting Activity"
              value={seller.capitulation_score}
              color="#34d399"
              note={capScore > 0.7 ? "Active discounting underway" : undefined}
            />
            <ScoreMeter
              label={CONSUMER_LABELS.churn_rate}
              value={seller.churn_rate != null ? Math.min(seller.churn_rate / 10, 1) : null}
              color="#fb923c"
            />
            <ScoreMeter label={CONSUMER_LABELS.seller_confidence} value={seller.seller_confidence} color="#60a5fa" />
            <ScoreMeter label={CONSUMER_LABELS.reprice_rate}      value={seller.reprice_rate}       color="#a78bfa" />
          </div>
        </div>

        {seller.largest_price_drops?.length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Largest Price Drops</h3>
            <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5">
                    {["Section", "Was", "Now", "Drop"].map((h) => (
                      <th key={h} className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {seller.largest_price_drops.slice(0, 10).map((row, i) => (
                    <tr key={i} className="border-b border-white/4 last:border-0 hover:bg-white/2">
                      <td className="px-3 py-2 text-slate-300 max-w-[160px] truncate">{row.section}</td>
                      <td className="px-3 py-2 text-slate-500 tabular-nums">{fmt$$(row.old_price)}</td>
                      <td className="px-3 py-2 text-slate-300 tabular-nums font-medium">{fmt$$(row.new_price)}</td>
                      <td className="px-3 py-2 text-red-400 tabular-nums font-semibold">-{fmt$$(Math.abs(row.delta))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {seller.largest_price_gains?.length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Largest Price Increases</h3>
            <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5">
                    {["Section", "Was", "Now", "Increase"].map((h) => (
                      <th key={h} className="text-left px-3 py-2.5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {seller.largest_price_gains.slice(0, 10).map((row, i) => (
                    <tr key={i} className="border-b border-white/4 last:border-0 hover:bg-white/2">
                      <td className="px-3 py-2 text-slate-300 max-w-[160px] truncate">{row.section}</td>
                      <td className="px-3 py-2 text-slate-500 tabular-nums">{fmt$$(row.old_price)}</td>
                      <td className="px-3 py-2 text-slate-300 tabular-nums font-medium">{fmt$$(row.new_price)}</td>
                      <td className="px-3 py-2 text-emerald-400 tabular-nums font-semibold">+{fmt$$(row.delta)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {seller.aggressive_sections?.length > 0 && (
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Most Active Sections</h3>
            <div className="flex flex-wrap gap-2">
              {seller.aggressive_sections.slice(0, 12).map((s, i) => (
                <span key={i} className="px-2.5 py-1 rounded-lg bg-red-500/8 border border-red-500/15 text-red-400 text-[11px] font-medium">
                  {s.section}
                  {s.score != null && <span className="text-red-600 ml-1">{Number(s.score).toFixed(1)}</span>}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderVenue() {
    return (
      <VenueIntelligence
        eventId={id}
        venueSlug={eventMeta?.venue_slug}
        venueName={venue}
      />
    );
  }

  return (
    <div>
      <div className="mb-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft size={12} />
          Watchlist
        </Link>
      </div>

      {renderHero()}

      <div className="flex gap-0.5 mb-5 border-b border-white/5 overflow-x-auto">
        {TABS.map(({ id: tid, label, icon: Icon }) => {
          // Only show Venue tab when we know the venue (optimistic: show it always, VenueIntelligence handles fallback)
          return (
            <button
              key={tid}
              onClick={() => setTab(tid)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-colors -mb-px",
                tab === tid
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-600",
              )}
            >
              <Icon size={12} />
              {label}
              {/* Venue tab: show a subtle dot when SoFi */}
              {tid === "venue" && eventMeta?.venue_slug === "sofi-stadium" && (
                <span className="w-1 h-1 rounded-full bg-emerald-500 ml-0.5" />
              )}
            </button>
          );
        })}
      </div>

      <div>
        {tab === "overview"  && renderOverview()}
        {tab === "market"    && renderMarket()}
        {tab === "history"   && renderHistory()}
        {tab === "sections"  && renderSections()}
        {tab === "seller"    && renderSeller()}
        {tab === "venue"     && renderVenue()}
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <RefreshCw size={18} className="animate-spin text-slate-500" />
    </div>
  );
}

function ErrBox({ msg }: { msg: string }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
      <AlertCircle size={14} className="flex-shrink-0" />
      {msg}
    </div>
  );
}
