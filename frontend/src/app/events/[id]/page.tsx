"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, RefreshCw, TrendingUp, TrendingDown, Minus,
  AlertCircle, Bookmark, Calendar, MapPin, Clock,
  Bell, ChevronDown, ChevronUp, ArrowUpRight, ArrowDownRight,
  Archive, EyeOff, X, Music, Check, Link2, CheckCircle2,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { api } from "@/lib/api";
import type {
  HeroResponse, MarketResponse, HistoryResponse, HistoryWindow,
  SectionsResponse, SectionRow, SellerResponse, EventMeta, Listing,
  BaselineResponse, EventSnapshotResponse,
} from "@/lib/types";
import {
  fmt$$, fmtNum, fmtPct, fmtDelta, cn,
  signalToAction, actionColors, signalDescription,
} from "@/lib/utils";
import { getEventGradient, getSpotifyData } from "@/lib/entityimages";
import { useArtistImage } from "@/hooks/useArtistImage";
import { useWatchlist } from "@/hooks/useWatchlist";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";
import { useArchivedEvents } from "@/hooks/useArchivedEvents";
import { useFollowArtist, type ArtistFollowScope, type TeamFollowScope } from "@/hooks/useFollowArtist";
import PriceHistoryChart from "@/components/charts/PriceHistoryChart";
import VenueIntelligence from "@/components/venue/VenueIntelligence";

// ─── Helpers ────────────────────────────────────────────────────────────────

function DeltaChip({ pct, abs, size = "sm" }: {
  pct?: number | null; abs?: number | null; size?: "sm" | "md";
}) {
  const val = pct ?? null;
  if (val == null && abs == null) return <span className="text-slate-600 text-[11px]">—</span>;
  const n = val ?? abs ?? 0;
  const up = n > 0;
  const Icon = up ? TrendingUp : n < 0 ? TrendingDown : Minus;
  const textSize = size === "md" ? "text-sm" : "text-[11px]";
  const label = val != null ? fmtPct(val) : (n > 0 ? `+${n}` : `${n}`);
  return (
    <span className={cn("inline-flex items-center gap-0.5 font-medium tabular-nums", textSize,
      up ? "text-emerald-400" : n < 0 ? "text-red-400" : "text-slate-500")}>
      <Icon size={size === "md" ? 13 : 10} />
      {label}
    </span>
  );
}

function MetricRow({ label, value, delta, deltaAbs, valueCls }: {
  label: string; value: React.ReactNode;
  delta?: number | null; deltaAbs?: number | null; valueCls?: string;
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-white/6 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className={cn("text-sm font-semibold tabular-nums", valueCls ?? "text-slate-100")}>{value}</span>
        {(delta != null || deltaAbs != null) && <DeltaChip pct={delta} abs={deltaAbs} />}
      </div>
    </div>
  );
}

function buildSignalReason(action: string, hero: HeroResponse | null): { headline: string; bullets: string[] } {
  const pct24h   = hero?.changes?.h24?.price_delta_pct ?? null;
  const pct7d    = hero?.changes?.d7?.price_delta_pct ?? null;
  const invDelta = hero?.changes?.h24?.inventory_delta ?? null;
  const cap      = hero?.market?.capitulation_score ?? null;
  const tight    = hero?.market?.tightness ?? null;

  if (action === "BUY") {
    const bullets: string[] = [];
    if (pct24h != null && pct24h < -2) bullets.push(`Prices dropped ${fmtPct(Math.abs(pct24h))} in the last 24 hours.`);
    if (pct7d  != null && pct7d  < -5) bullets.push(`Down ${fmtPct(Math.abs(pct7d))} over the past 7 days.`);
    if (tight  != null && tight  > 0.6) bullets.push("Inventory is tightening — fewer listings available.");
    if (invDelta != null && invDelta < -20) bullets.push(`Net inventory dropped by ${Math.abs(invDelta)} listings in 24h.`);
    if (bullets.length === 0) bullets.push("Price and inventory indicate a favorable buying window.");
    return { headline: "Now is a good time to buy.", bullets };
  }

  if (action === "WAIT") {
    const bullets: string[] = [];
    if (pct24h != null && pct24h < -1) bullets.push(`Prices fell ${fmtPct(Math.abs(pct24h))} in the last 24 hours — the trend may continue.`);
    if (pct7d  != null && pct7d  < -3) bullets.push(`Down ${fmtPct(Math.abs(pct7d))} this week. Sellers are cutting.`);
    if (invDelta != null && invDelta > 0) bullets.push(`Inventory grew by ${invDelta} listings net — no urgency yet.`);
    if (cap != null && cap > 0.5)       bullets.push("Many sellers are repricing downward — competition is high.");
    if (pct24h == null && pct7d == null) bullets.push("Not enough price history yet to confirm a trend.");
    if (bullets.length === 0) bullets.push("Current signals do not suggest urgency. Prices may fall closer to the event.");
    return { headline: "Prices are falling. Better deals may be ahead.", bullets };
  }

  if (action === "MONITOR") {
    const bullets: string[] = [];
    if (tight != null && tight > 0.4) bullets.push("Inventory is tightening but prices haven't moved yet.");
    else bullets.push("Market is stable — no strong buy or wait signal.");
    bullets.push("Check back daily as the event approaches.");
    return { headline: "No strong signal yet. Keep watching.", bullets };
  }

  return { headline: signalDescription(hero?.signal), bullets: [] };
}

const MP_META: Record<string, { label: string; short: string; color: string }> = {
  stubhub:    { label: "StubHub",     short: "SH", color: "#1c64f2" },
  gametime:   { label: "Gametime",    short: "GT", color: "#0ea5e9" },
  tickpick:   { label: "TickPick",    short: "TP", color: "#7c3aed" },
  vividseats: { label: "Vivid Seats", short: "VS", color: "#059669" },
};

const WINDOWS: { id: HistoryWindow; label: string }[] = [
  { id: "24h", label: "24h" },
  { id: "7d",  label: "7d"  },
  { id: "14d", label: "14d" },
  { id: "30d", label: "30d" },
  { id: "all", label: "All" },
];

// ─── Section Breakdown (extended sort + filter) ───────────────────────────────

type SectionSort = "floor" | "median" | "listings" | "value" | "activity";
type SectionFilter = "all" | "upper" | "lower" | "floor_ga" | "vip";

const SECTION_SORTS: { key: SectionSort; label: string }[] = [
  { key: "floor",    label: "Lowest Price"    },
  { key: "median",   label: "Median"          },
  { key: "listings", label: "Most Inventory"  },
  { key: "value",    label: "Best Value"      },
  { key: "activity", label: "Most Active"     },
];

const SECTION_FILTERS: { key: SectionFilter; label: string; pattern: RegExp }[] = [
  { key: "upper",    label: "Upper Bowl", pattern: /upper|3\d\d|4\d\d|5\d\d|6\d\d|upper.?level|upper.?deck|nosebleed/i },
  { key: "lower",    label: "Lower Bowl", pattern: /lower|1\d\d|2\d\d|lower.?level|club|mezzanine/i                    },
  { key: "floor_ga", label: "Floor / GA",  pattern: /floor|pit|general.?admission|\bga\b/i                             },
  { key: "vip",      label: "VIP / Suite", pattern: /vip|premium|platinum|suite|box|loge|field.?suite/i                },
];

function SectionBreakdown({ sections }: { sections: SectionRow[] }) {
  const [sort, setSort]     = useState<SectionSort>("floor");
  const [filter, setFilter] = useState<SectionFilter>("all");
  const [showAll, setShowAll] = useState(false);

  const filtered = filter === "all"
    ? sections
    : sections.filter(s => {
        const rule = SECTION_FILTERS.find(f => f.key === filter);
        return rule ? rule.pattern.test(s.display_name) : true;
      });

  const sorted = [...filtered].sort((a, b) => {
    if (sort === "floor")    return (a.low_ask   ?? 999999) - (b.low_ask   ?? 999999);
    if (sort === "median")   return (a.median_ask ?? 999999) - (b.median_ask ?? 999999);
    if (sort === "listings") return (b.listings   ?? 0)     - (a.listings   ?? 0);
    if (sort === "value")    return (b.value_score    ?? 0) - (a.value_score    ?? 0);
    if (sort === "activity") return (b.activity_score ?? 0) - (a.activity_score ?? 0);
    return 0;
  });

  const visible = showAll ? sorted : sorted.slice(0, 10);

  return (
    <section>
      <div className="flex items-start justify-between mb-2 flex-wrap gap-2">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-0.5">Section Breakdown</h2>
        <div className="flex flex-col items-end gap-1.5">
          {/* Sort buttons */}
          <div className="flex items-center gap-1 flex-wrap justify-end">
            <span className="text-[9px] text-slate-600 mr-0.5">Sort:</span>
            {SECTION_SORTS.map(({ key, label }) => (
              <button key={key} onClick={() => setSort(key)}
                className={cn("text-[10px] px-2 py-0.5 rounded border transition-colors",
                  sort === key ? "border-white/20 bg-white/8 text-slate-200" : "border-white/7 text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                {label}
              </button>
            ))}
          </div>
          {/* Filter pills */}
          <div className="flex items-center gap-1 flex-wrap justify-end">
            <span className="text-[9px] text-slate-600 mr-0.5">Filter:</span>
            <button onClick={() => setFilter("all")}
              className={cn("text-[10px] px-2 py-0.5 rounded border transition-colors",
                filter === "all" ? "border-white/20 bg-white/8 text-slate-200" : "border-white/7 text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
              All
            </button>
            {SECTION_FILTERS.map(({ key, label }) => (
              <button key={key} onClick={() => setFilter(key)}
                className={cn("text-[10px] px-2 py-0.5 rounded border transition-colors",
                  filter === key ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/7 text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="rounded-xl border border-white/7 bg-[#161b27] py-6 text-center text-xs text-slate-600">
          No sections match this filter
        </div>
      ) : (
        <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-x-auto">
          <table className="w-full text-xs min-w-[400px]">
            <thead>
              <tr className="border-b border-white/5">
                {["Section", "Listings", "Floor", "Median"].map((h) => (
                  <th key={h} className="text-left px-4 py-2 text-[9px] text-slate-500 uppercase tracking-wider font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((s, i) => (
                <tr key={i} className="border-b border-white/4 last:border-0 hover:bg-white/2">
                  <td className="px-4 py-2.5 text-slate-200 font-medium max-w-[160px] truncate">{s.display_name}</td>
                  <td className="px-4 py-2.5 text-slate-400 tabular-nums">{fmtNum(s.listings)}</td>
                  <td className="px-4 py-2.5 text-slate-200 font-semibold tabular-nums">{fmt$$(s.low_ask)}</td>
                  <td className="px-4 py-2.5 text-slate-400 tabular-nums">{fmt$$(s.median_ask)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sorted.length > 10 && (
        <button onClick={() => setShowAll(v => !v)}
          className="mt-1.5 w-full flex items-center justify-center gap-1 text-[10px] text-slate-600 hover:text-slate-400 py-1 transition-colors">
          {showAll
            ? <><ChevronUp size={10} /> Show less</>
            : <><ChevronDown size={10} /> Show all {sorted.length} sections</>}
        </button>
      )}
    </section>
  );
}

// ─── Follow Panel (inline dropdown) ──────────────────────────────────────────

const ARTIST_SCOPES: { key: ArtistFollowScope; label: string }[] = [
  { key: "next3",       label: "Next 3 events"   },
  { key: "next5",       label: "Next 5 events"   },
  { key: "next10",      label: "Next 10 events"  },
  { key: "all_future",  label: "All future events" },
];

const TEAM_SCOPES: { key: TeamFollowScope; label: string }[] = [
  { key: "home",   label: "Home games"  },
  { key: "away",   label: "Away games"  },
  { key: "both",   label: "All games"   },
  { key: "next5",  label: "Next 5 games" },
  { key: "next10", label: "Next 10 games" },
  { key: "season", label: "Full season" },
];

function FollowPanel({
  artist, onClose,
}: { artist: string; onClose: () => void }) {
  const { getFollow, follow, unfollow } = useFollowArtist();
  const existing = getFollow(artist.toLowerCase());
  const isTeam = /nfl|nba|mlb|nhl|49ers|lakers|dodgers|rams|chargers|clippers|galaxy|kings/i.test(artist);

  const [type, setType]   = useState<"artist" | "team">(existing?.type ?? (isTeam ? "team" : "artist"));
  const [scope, setScope] = useState<string>(existing?.scope ?? (type === "artist" ? "next5" : "home"));

  const key = artist.toLowerCase();

  return (
    <div className="absolute right-0 top-full mt-1.5 w-64 z-50 rounded-xl border border-white/12 bg-[#1a2030] shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-white/8">
        <div>
          <p className="text-xs font-semibold text-slate-200">Follow {artist}</p>
          <p className="text-[9px] text-amber-400/70 mt-0.5">Local only — no backend notifications</p>
        </div>
        <button onClick={onClose} className="p-0.5 text-slate-500 hover:text-slate-300"><X size={12} /></button>
      </div>

      <div className="p-3 space-y-3">
        {/* Type toggle */}
        <div className="flex rounded-lg border border-white/8 overflow-hidden text-[10px]">
          {(["artist", "team"] as const).map(t => (
            <button key={t} onClick={() => { setType(t); setScope(t === "artist" ? "next5" : "home"); }}
              className={cn("flex-1 py-1.5 capitalize transition-colors",
                type === t ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300")}>
              {t === "artist" ? "Artist" : "Team"}
            </button>
          ))}
        </div>

        {/* Scope options */}
        <div className="space-y-1">
          <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-1.5">
            {type === "artist" ? "Alert scope" : "Games to follow"}
          </p>
          {(type === "artist" ? ARTIST_SCOPES : TEAM_SCOPES).map(({ key: sk, label }) => (
            <button key={sk} onClick={() => setScope(sk)}
              className={cn("w-full flex items-center justify-between text-left px-2.5 py-1.5 rounded-lg text-[11px] transition-colors",
                scope === sk
                  ? "bg-blue-500/15 border border-blue-500/30 text-blue-300"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200")}>
              {label}
              {scope === sk && <Check size={10} className="text-blue-400" />}
            </button>
          ))}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => {
              if (type === "artist") {
                follow({ type: "artist", key, displayName: artist, scope: scope as ArtistFollowScope });
              } else {
                follow({ type: "team", key, displayName: artist, scope: scope as TeamFollowScope });
              }
              onClose();
            }}
            className="flex-1 text-[11px] py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 hover:bg-blue-500/30 transition-colors font-medium"
          >
            {existing ? "Update follow" : "Follow"}
          </button>
          {existing && (
            <button onClick={() => { unfollow(key); onClose(); }}
              className="px-3 text-[11px] py-1.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-colors">
              Unfollow
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Listing Move Menu (Hidden / Parking) ─────────────────────────────────────

function ListingMoveMenu({ listingId }: { listingId: number }) {
  const [moved, setMoved] = useState<"hidden" | "parking" | null>(null);
  const [open, setOpen]   = useState(false);

  if (moved) {
    return (
      <span className={`inline-flex items-center gap-1.5 text-xs font-medium rounded-md px-2 py-1 border ${
        moved === "hidden"
          ? "text-slate-400 border-slate-500/30 bg-slate-500/10"
          : "text-amber-400 border-amber-500/30 bg-amber-500/8"
      }`}>
        {moved === "hidden" ? <><EyeOff size={10} /> Hidden</> : <>🅿 Parking</>}
        <button onClick={() => setMoved(null)} className="ml-0.5 opacity-50 hover:opacity-100 text-sm leading-none">×</button>
      </span>
    );
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(v => !v)}
        title="Move listing"
        className="text-xs text-slate-500 hover:text-slate-200 transition-colors px-2 py-1 rounded-md border border-white/8 hover:border-white/20 font-medium">
        Move
      </button>
      {open && (
        <div className="absolute left-0 top-8 z-50 rounded-xl border border-white/12 bg-[#1a1f2e] shadow-xl py-1.5 w-36" onClick={() => setOpen(false)}>
          <p className="text-xs text-slate-500 font-semibold px-3 py-1.5 border-b border-white/5 uppercase tracking-wider">Move to</p>
          <button
            onClick={() => { setMoved("hidden"); }}
            className="w-full text-left px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors flex items-center gap-2">
            <EyeOff size={11} className="text-slate-500" /> Hidden
          </button>
          <button
            onClick={() => { setMoved("parking"); }}
            className="w-full text-left px-3 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors flex items-center gap-2">
            <span className="text-xs">🅿</span> Parking
          </button>
          <p className="text-[10px] text-slate-700 px-3 py-1.5 border-t border-white/5">Record preserved</p>
        </div>
      )}
    </div>
  );
}

// ─── Venue Summary Card ───────────────────────────────────────────────────────

const VENUE_SUMMARIES: Record<string, {
  name: string;
  capacity: string;
  buyWindow: string;
  behavior: string;
}> = {
  "sofi-stadium":      { name: "SoFi Stadium",       capacity: "70,000",  buyWindow: "4–8 weeks out",  behavior: "High liquidity; floor rises sharply inside 3 weeks" },
  "crypto-arena":      { name: "Crypto.com Arena",   capacity: "21,000",  buyWindow: "2–6 weeks out",  behavior: "Quick sell-through; premium sections deplete first" },
  "kia-forum":         { name: "Kia Forum",           capacity: "17,500",  buyWindow: "3–6 weeks out",  behavior: "Stable floor; late inventory often appears night-of" },
  "hollywood-bowl":    { name: "Hollywood Bowl",      capacity: "17,500",  buyWindow: "2–4 weeks out",  behavior: "Box seats sell early; lawn holds value closer to show" },
  "greek-theatre":     { name: "Greek Theatre",       capacity: "5,900",   buyWindow: "1–3 weeks out",  behavior: "Small venue premium; limited supply drives floor up late" },
};

function VenueSummaryCard({ venueSlug }: { venueSlug: string }) {
  const summary = VENUE_SUMMARIES[venueSlug];
  const venueName = summary?.name ?? venueSlug.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="rounded-xl border border-white/7 bg-[#161b27] p-4 mb-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg opacity-50">🏟</span>
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">{venueName} — Venue Profile</h3>
        {!summary && (
          <span className="text-[10px] text-amber-500/60 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5 font-bold uppercase tracking-widest ml-auto">
            Pending Intelligence
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {[
          { label: "Venue",              value: venueName },
          { label: "Typical Inventory",  value: summary ? `~${summary.capacity} capacity` : null },
          { label: "Typical Buy Window", value: summary?.buyWindow ?? null },
          { label: "Typical Behavior",   value: summary?.behavior  ?? null },
        ].map(({ label, value }) => (
          <div key={label} className="bg-black/20 rounded-lg px-3 py-3 border border-white/5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1.5">{label}</p>
            {value
              ? <p className="text-sm text-slate-300 font-medium leading-snug">{value}</p>
              : <p className="text-xs text-amber-500/40 italic">Pending data</p>
            }
          </div>
        ))}
      </div>
      {/* Next data slots — always shown, filled when intelligence phase activates */}
      <div className="border-t border-white/5 pt-4">
        <p className="text-xs text-slate-600 uppercase tracking-wider mb-3">Intelligence Board — Pending</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { slot: "Best Value",      icon: "⭐", desc: "Sections with price below tier median" },
            { slot: "Cheapest Now",    icon: "💰", desc: "Current floor section by price" },
            { slot: "Most Active",     icon: "🔥", desc: "Sections with highest seller repricing" },
            { slot: "Opportunity",     icon: "📈", desc: "Rising demand with stable or falling price" },
          ].map(({ slot, icon, desc }) => (
            <div key={slot} className="rounded-lg border border-white/5 border-dashed bg-white/2 px-3 py-3 flex flex-col gap-1">
              <div className="flex items-center gap-1.5">
                <span className="text-sm opacity-40">{icon}</span>
                <span className="text-xs font-semibold text-slate-500">{slot}</span>
              </div>
              <p className="text-[11px] text-slate-700 leading-snug">{desc}</p>
              <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-amber-500/40 mt-0.5">Pending</span>
            </div>
          ))}
        </div>
      </div>
      {/* Trend Panel */}
      <div className="border-t border-white/5 pt-4 mt-4">
        <p className="text-xs text-slate-600 uppercase tracking-wider mb-3">Venue Trend Panel — Pending</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {([
            { slot: "Last Events",    icon: "📅", desc: "Recent event sell-through, floor, and price velocity at this venue." },
            { slot: "Venue Pattern",  icon: "📊", desc: "Seasonal demand patterns, typical ticket release timing, and day-of drop behavior." },
          ] as const).map(({ slot, icon, desc }) => (
            <div key={slot} className="rounded-lg border border-white/5 border-dashed bg-white/2 px-3 py-3">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-sm opacity-40">{icon}</span>
                <span className="text-xs font-semibold text-slate-500">{slot}</span>
                <span className="ml-auto text-[9px] font-bold uppercase tracking-widest text-amber-500/40">Pending</span>
              </div>
              <p className="text-[11px] text-slate-700 leading-snug">{desc}</p>
            </div>
          ))}
        </div>
      </div>
      {summary && (
        <p className="text-xs text-slate-700 mt-3 flex items-center gap-1">
          <span className="text-amber-500/40">⚠</span>
          Typical behavior based on static venue knowledge — dynamic intelligence pending.
        </p>
      )}
    </div>
  );
}

// ─── Spotify Embed ────────────────────────────────────────────────────────────

function SpotifyEmbed({ artistUrl, playlistUrl }: { artistUrl: string | null; playlistUrl: string | null }) {
  const [tab, setTab] = useState<"artist" | "playlist">("artist");
  if (!artistUrl) return null;

  const artistId  = artistUrl.split("/artist/")[1]?.split("?")[0];
  const playlistId = playlistUrl?.split("/playlist/")[1]?.split("?")[0];

  const embedId   = tab === "playlist" && playlistId ? playlistId : artistId;
  const embedType = tab === "playlist" && playlistId ? "playlist" : "artist";
  const embedSrc  = `https://open.spotify.com/embed/${embedType}/${embedId}?utm_source=generator&theme=0`;

  return (
    <section>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Spotify</h2>
        {playlistId && (
          <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
            {(["artist", "playlist"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-2.5 py-1 capitalize transition-colors ${tab === t ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"}`}>
                {t}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="rounded-xl overflow-hidden border border-white/7">
        <iframe
          src={embedSrc}
          width="100%"
          height="152"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          loading="lazy"
          className="block"
          style={{ colorScheme: "normal" }}
        />
      </div>
    </section>
  );
}

// ─── Add Marketplace URL ──────────────────────────────────────────────────────

function AddMarketplaceUrl() {
  const [open, setOpen]   = useState(false);
  const [url, setUrl]     = useState("");
  const [result, setResult] = useState<{ mp: string; accepted: boolean } | null>(null);

  const MP_PATTERNS: [RegExp, string][] = [
    [/stubhub\.com/i,               "StubHub"],
    [/tickpick\.com/i,              "TickPick"],
    [/gametime\.co/i,               "Gametime"],
    [/vividseats\.com/i,            "Vivid Seats"],
    [/ticketmaster\.com|livenation\.com/i, "Ticketmaster"],
  ];

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const raw = url.trim();
    try { new URL(raw); } catch { setResult({ mp: "Invalid URL", accepted: false }); return; }
    const match = MP_PATTERNS.find(([p]) => p.test(raw));
    if (!match) { setResult({ mp: "Marketplace not recognized", accepted: false }); return; }
    setResult({ mp: match[1], accepted: true });
    setTimeout(() => { setOpen(false); setUrl(""); setResult(null); }, 2000);
  }

  return (
    <div className="relative">
      <button onClick={() => { setOpen(v => !v); setResult(null); }}
        className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:border-white/20 transition-all">
        <Link2 size={11} />
        Add URL
      </button>
      {open && (
        <div className="absolute right-0 top-8 z-50 w-80 rounded-xl border border-white/12 bg-[#1a1f2e] shadow-2xl p-4">
          <p className="text-xs font-semibold text-slate-300 mb-1">Add Marketplace URL</p>
          <p className="text-[10px] text-slate-600 mb-3">
            Paste a StubHub, TickPick, Gametime, Vivid Seats, or Ticketmaster listing URL to register it for ingestion.
          </p>
          <form onSubmit={submit} className="flex gap-2">
            <input
              value={url}
              onChange={e => { setUrl(e.target.value); setResult(null); }}
              placeholder="https://www.stubhub.com/..."
              className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-white/20"
              autoFocus
            />
            <button type="submit"
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors flex-shrink-0">
              Add
            </button>
          </form>
          {result && (
            <div className={`mt-2 text-[10px] flex items-center gap-1.5 ${result.accepted ? "text-emerald-400" : "text-red-400"}`}>
              {result.accepted ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
              {result.accepted ? `${result.mp} URL registered — pending backend ingestion` : result.mp}
            </div>
          )}
          <div className="mt-2 pt-2 border-t border-white/6">
            <a href="/url-intake" className="text-[10px] text-slate-600 hover:text-slate-400 transition-colors">
              Open full URL Intake tool →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function EventDetailPage() {
  const params   = useParams();
  const id       = Number(params.id);
  const [histWindow, setHistWindow] = useState<HistoryWindow>("7d");
  const [showFollowPanel, setShowFollowPanel] = useState(false);
  const followRef = useRef<HTMLDivElement>(null);

  const [eventMeta, setEventMeta] = useState<EventMeta | null>(null);
  const [hero, setHero]           = useState<HeroResponse | null>(null);
  const [market, setMarket]       = useState<MarketResponse | null>(null);
  const [history, setHistory]     = useState<HistoryResponse | null>(null);
  const [sections, setSections]   = useState<SectionsResponse | null>(null);
  const [seller, setSeller]       = useState<SellerResponse | null>(null);
  const [listings, setListings]   = useState<Listing[] | null>(null);
  const [baseline, setBaseline]   = useState<BaselineResponse | null>(null);
  const [snapshot, setSnapshot]   = useState<EventSnapshotResponse | null>(null);
  const [loadingAll, setLoadingAll]         = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const { watched, toggle: toggleWatch }     = useWatchlist();
  const { hiddenEvents, toggle: toggleHide } = useHiddenEvents();
  const { archivedEvents, toggle: toggleArchive } = useArchivedEvents();

  const isWatched  = watched.has(id);
  const isHidden   = hiddenEvents.has(id);
  const isArchived = archivedEvents.has(id);

  // Close follow panel on outside click
  useEffect(() => {
    if (!showFollowPanel) return;
    function handleOutside(e: MouseEvent) {
      if (followRef.current && !followRef.current.contains(e.target as Node)) {
        setShowFollowPanel(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [showFollowPanel]);

  useEffect(() => {
    if (!id) return;
    setLoadingAll(true);
    Promise.allSettled([
      api.events.meta(id).then(setEventMeta),
      api.events.hero(id).then(setHero),
      api.events.market(id).then(setMarket),
      api.events.history(id, "7d").then(setHistory),
      api.events.sections(id).then(setSections),
      api.events.seller(id).then(setSeller),
      api.events.listings(id, 10).then(setListings),
      api.analytics.baseline(id).then(setBaseline).catch(() => {}),
      api.events.snapshot(id).then(setSnapshot).catch(() => {}),
    ]).finally(() => setLoadingAll(false));
  }, [id]);

  useEffect(() => {
    if (!id || loadingAll) return;
    setLoadingHistory(true);
    api.events.history(id, histWindow)
      .then(setHistory)
      .finally(() => setLoadingHistory(false));
  }, [id, histWindow]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Derived ─────────────────────────────────────────────────────────────────
  const title      = eventMeta?.title ?? `Event #${id}`;
  const venue      = eventMeta?.venue_name ?? eventMeta?.venue;
  const dateStr    = eventMeta?.event_date;
  const artist     = eventMeta?.artist;
  const gradient   = getEventGradient(artist, title);
  const artworkUrl = useArtistImage(artist, title);
  const spotify    = getSpotifyData(artist);
  const isSports   = /nfl|nba|mlb|nhl|49ers|lakers|dodgers|rams|chargers|clippers|galaxy|kings/i.test(artist ?? "") || /nfl|nba|mlb|nhl/i.test(title ?? "");
  const action     = signalToAction(hero?.signal);
  const aColors    = actionColors(action);
  const daysOut    = hero?.days_until_event ?? null;
  const isCompleted = dateStr ? new Date(dateStr) < new Date() : false;

  let dateLabel = "";
  if (dateStr) {
    try { dateLabel = format(parseISO(dateStr), "EEEE, MMMM d, yyyy"); } catch {}
  }

  const { headline, bullets } = buildSignalReason(action, hero);
  const pct24h      = hero?.changes?.h24?.price_delta_pct ?? null;
  const invDelta24  = hero?.changes?.h24?.inventory_delta ?? null;
  const marketplaces = (market?.marketplaces ?? []).sort((a, b) => (a.low_ask ?? 9999) - (b.low_ask ?? 9999));

  const sincePct = (() => {
    if (!history?.series?.length || history.series.length < 2) return null;
    const first = history.series[0].median_ask ?? history.series[0].low_ask;
    const last  = history.series[history.series.length - 1].median_ask ?? history.series[history.series.length - 1].low_ask;
    if (!first || !last) return null;
    return ((last - first) / first) * 100;
  })();

  // ─── Skeleton ────────────────────────────────────────────────────────────────
  if (loadingAll && !hero && !eventMeta) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500">
            <ArrowLeft size={12} /> Active Markets
          </Link>
        </div>
        <div className="h-[420px] rounded-2xl bg-[#161b27] border border-white/5 animate-pulse mb-4" />
        <div className="h-40 rounded-xl bg-[#161b27] border border-white/5 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-5">

      {/* UI BUILD MARKER — remove after screenshot verification */}
      <div className="fixed top-2 right-2 z-50 text-[9px] font-mono bg-amber-400 text-black px-2 py-0.5 rounded opacity-80 pointer-events-none select-none">
        UI BUILD {new Date().toISOString().slice(0,16).replace("T"," ")}
      </div>

      {/* Back nav + actions */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors">
          <ArrowLeft size={12} /> Active Markets
        </Link>

        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Watch */}
          <button onClick={() => toggleWatch(id)}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isWatched ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <Bookmark size={11} className={isWatched ? "fill-blue-400" : ""} />
            {isWatched ? "Watching" : "Watch"}
          </button>

          {/* Follow (functional dropdown) */}
          {artist && (
            <div className="relative" ref={followRef}>
              <button
                onClick={() => setShowFollowPanel(v => !v)}
                className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
                  showFollowPanel ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:border-white/20")}
              >
                <Bell size={11} />
                Follow
                <ChevronDown size={9} className={cn("transition-transform", showFollowPanel && "rotate-180")} />
              </button>
              {showFollowPanel && (
                <FollowPanel artist={artist} onClose={() => setShowFollowPanel(false)} />
              )}
            </div>
          )}

          {/* Archive */}
          <button onClick={() => toggleArchive(id)}
            title={isArchived ? "Restore from archive" : "Archive event"}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isArchived ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <Archive size={11} />
            {isArchived ? "Archived" : "Archive"}
          </button>

          {/* Hide */}
          <button onClick={() => toggleHide(id)}
            title={isHidden ? "Unhide from dashboard" : "Hide from dashboard"}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isHidden ? "border-slate-500/40 bg-slate-500/10 text-slate-300" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <EyeOff size={11} />
            {isHidden ? "Hidden" : "Hide"}
          </button>

          {/* Spotify link — hidden for sports events */}
          {!isSports && (spotify.spotifyArtistUrl ? (
            <a href={spotify.spotifyArtistUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-[#1db954]/30 bg-[#1db954]/8 text-[#1db954] hover:bg-[#1db954]/15 transition-all">
              <Music size={11} />
              Spotify
            </a>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-dashed border-[#1db954]/20 text-[#1db954]/30">
              <Music size={11} />
              Spotify pending
            </span>
          ))}

          {/* Add Marketplace URL */}
          <AddMarketplaceUrl />
        </div>
      </div>

      {/* Status banners */}
      {isArchived && (
        <div className="flex items-center justify-between px-3 py-2 rounded-lg border border-amber-500/20 bg-amber-500/5 text-xs">
          <span className="text-amber-400/80 flex items-center gap-1.5"><Archive size={11} /> This event is archived</span>
          <button onClick={() => toggleArchive(id)} className="text-amber-600 hover:text-amber-400 transition-colors">Restore</button>
        </div>
      )}
      {isHidden && (
        <div className="flex items-center justify-between px-3 py-2 rounded-lg border border-slate-500/20 bg-slate-500/5 text-xs">
          <span className="text-slate-400 flex items-center gap-1.5"><EyeOff size={11} /> Hidden from dashboard</span>
          <button onClick={() => toggleHide(id)} className="text-slate-500 hover:text-slate-300 transition-colors">Unhide</button>
        </div>
      )}

      {/* ═══════════════ HERO ═══════════════ */}
      <div className="rounded-2xl overflow-hidden border border-white/10 relative" style={{ backdropFilter: "blur(12px)", background: "rgba(14,17,23,0.88)" }}>
        <div className="relative z-10 flex flex-col sm:flex-row min-h-[340px]">

          {/* LEFT — Artwork panel (wider) */}
          <div
            className="relative w-full sm:w-[320px] lg:w-[380px] flex-shrink-0 min-h-[200px] sm:min-h-[380px] overflow-hidden"
            style={{ background: `linear-gradient(145deg, ${gradient[0]} 0%, ${gradient[1]} 60%, ${gradient[0]}88 100%)` }}
          >
            {artworkUrl ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={artworkUrl}
                  alt={artist ?? title}
                  className="absolute inset-0 w-full h-full object-cover object-top"
                  onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
                {/* subtle gradient over photo for readability edge */}
                <div className="absolute inset-0"
                  style={{ background: `linear-gradient(to bottom, rgba(0,0,0,0.15) 0%, transparent 40%, rgba(14,17,23,0.6) 100%), linear-gradient(to right, transparent 70%, rgba(14,17,23,0.7) 100%)` }}
                />
              </>
            ) : (
              <>
                <div className="absolute inset-0 opacity-40"
                  style={{ background: `radial-gradient(ellipse at 40% 35%, rgba(255,255,255,0.25) 0%, transparent 65%)` }} />
                <div className="absolute inset-0 flex flex-col items-center justify-center select-none">
                  <div className="text-7xl font-black leading-none mb-2 opacity-90"
                    style={{ color: "rgba(255,255,255,0.9)", textShadow: "0 2px 20px rgba(0,0,0,0.4)" }}>
                    {(artist ?? title).slice(0, 1).toUpperCase()}
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.25em] opacity-60"
                    style={{ color: "rgba(255,255,255,0.9)" }}>
                    {artist ?? "Event"}
                  </div>
                </div>
              </>
            )}

            {/* Completed badge */}
            {isCompleted && (
              <div className="absolute top-3 left-3">
                <span className="text-[9px] font-bold uppercase tracking-widest bg-white/15 border border-white/20 text-white/70 rounded-full px-2 py-0.5">Completed</span>
              </div>
            )}

            {/* Spotify pill on artwork — hidden for sports */}
            {!isSports && spotify.spotifyArtistUrl && (
              <div className="absolute bottom-3 left-3">
                <a href={spotify.spotifyArtistUrl} target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[9px] font-bold px-2 py-1 rounded-full bg-[#1db954]/90 text-black hover:bg-[#1db954] transition-colors">
                  <Music size={8} />
                  Open in Spotify
                </a>
              </div>
            )}
          </div>

          {/* RIGHT — Event info + signal */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 p-5 pb-3"
              style={{ background: `linear-gradient(to right, ${gradient[0]}18 0%, ${gradient[1]}08 100%)` }}>
              {artist && (
                <p className="text-xs text-white/50 uppercase tracking-widest font-semibold mb-1">{artist}</p>
              )}
              <h1 className="text-3xl sm:text-4xl font-bold text-white leading-tight mb-2">{title}</h1>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-base text-white/60 mb-3">
                {venue    && <span className="flex items-center gap-1"><MapPin   size={10} />{venue}</span>}
                {dateLabel && <span className="flex items-center gap-1"><Calendar size={10} />{dateLabel}</span>}
              </div>
              {daysOut != null && (
                <div className="mb-3">
                  <span className="text-xs font-bold px-2.5 py-1 rounded-full border"
                    style={{ color: aColors.text, background: aColors.bg, borderColor: aColors.border }}>
                    {isCompleted ? "Event passed" : daysOut < 1 ? "Happening today" : daysOut < 2 ? "Tomorrow" : `${Math.round(daysOut)} days away`}
                  </span>
                </div>
              )}

              {/* Signal + explanation */}
              <div className="rounded-xl border p-3 mb-2"
                style={{ borderColor: aColors.border + "60", background: aColors.bg + "30" }}>
                <span className="inline-block text-sm font-black tracking-[0.15em] px-3 py-1 rounded-md border mb-2"
                  style={{ color: aColors.text, background: aColors.bg, borderColor: aColors.border }}>
                  {action}
                </span>
                <p className="text-lg font-semibold text-slate-200 leading-snug mb-2">{headline}</p>
                {bullets.length > 0 && (
                  <ul className="space-y-1">
                    {bullets.map((b, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-sm text-slate-400">
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-500 flex-shrink-0" />
                        {b}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Bottom: 6 key metrics */}
            <div className="px-5 pb-5 pt-4 bg-[#0e1117]/90 border-t border-white/8">
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">Floor</p>
                  <p className="text-3xl font-black text-white tabular-nums">{fmt$$(hero?.price?.low_ask)}</p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">Median</p>
                  <p className="text-3xl font-bold text-slate-200 tabular-nums">{fmt$$(hero?.price?.median_ask)}</p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">High</p>
                  <p className="text-3xl font-semibold text-slate-400 tabular-nums">{fmt$$(hero?.price?.high_ask)}</p>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">24h Δ</p>
                  <div className="mt-0.5">
                    {pct24h != null ? <DeltaChip pct={pct24h} size="md" /> : <span className="text-xl text-slate-600">—</span>}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">7d Δ</p>
                  <div className="mt-0.5">
                    {hero?.changes?.d7?.price_delta_pct != null
                      ? <DeltaChip pct={hero.changes.d7.price_delta_pct} size="md" />
                      : <span className="text-xl text-slate-600">—</span>}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">Inventory</p>
                  <p className="text-3xl font-bold text-slate-200 tabular-nums">{fmtNum(hero?.inventory?.total_listings)}</p>
                  {invDelta24 != null && (
                    <div className="flex items-center gap-0.5 mt-0.5">
                      <span className={cn("text-xs font-medium tabular-nums flex items-center gap-0.5",
                        invDelta24 > 0 ? "text-emerald-400" : "text-red-400")}>
                        {invDelta24 > 0 ? <ArrowUpRight size={10}/> : <ArrowDownRight size={10}/>}
                        {invDelta24 > 0 ? "+" : ""}{invDelta24}
                      </span>
                      <span className="text-xs text-slate-600">24h</span>
                    </div>
                  )}
                </div>
              </div>
              {hero?.history_context?.hours_available != null && (
                <div className="mt-2 pt-2 flex items-center justify-between border-t border-white/5">
                  <span className="text-[10px] text-slate-600 flex items-center gap-1">
                    <Clock size={9} />
                    {hero.history_context.hours_available > 24
                      ? `${Math.round(hero.history_context.hours_available / 24)}d of price history`
                      : "Live data only"}
                  </span>
                  {sincePct != null && (
                    <div className="flex items-center gap-1">
                      <DeltaChip pct={sincePct} />
                      <span className="text-[10px] text-slate-600">since tracking</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════ SPOTIFY EMBED (concerts only) ═══════════════ */}
      {!isSports && spotify.spotifyArtistUrl && (
        <SpotifyEmbed artistUrl={spotify.spotifyArtistUrl} playlistUrl={spotify.spotifyPlaylistUrl} />
      )}

      {/* ═══════════════ TODAY'S MOVEMENT ═══════════════ */}
      <section className="rounded-xl border border-amber-500/15 bg-amber-500/3 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400/60 animate-pulse flex-shrink-0" />
            <h2 className="text-sm font-bold text-amber-300/80 uppercase tracking-wider">Today&apos;s Movement</h2>
          </div>
          {!snapshot && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/50 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5">Pending Intelligence Phase</span>
          )}
        </div>
        <div className="rounded-xl border border-amber-500/10 bg-[#0e1117]/80 divide-y divide-white/4">
          {/* Hourly Floor Movement */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">📉</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Hourly Floor Movement</p>
                <p className="text-[11px] text-slate-500">Floor price change per hour today</p>
              </div>
            </div>
            {snapshot?.price?.floor_24h_change != null
              ? <span className={cn("text-sm font-bold tabular-nums", snapshot.price.floor_24h_change < 0 ? "text-red-400" : "text-emerald-400")}>
                  {snapshot.price.floor_24h_change < 0 ? "-" : "+"}{fmt$$(Math.abs(snapshot.price.floor_24h_change / 24))}/hr
                </span>
              : <span className="text-sm text-amber-500/50 italic font-medium">—</span>
            }
          </div>
          {/* Hourly Median Movement */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">📊</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Hourly Median Movement</p>
                <p className="text-[11px] text-slate-500">Median price change per hour today</p>
              </div>
            </div>
            {snapshot?.price?.median_24h_change != null
              ? <span className={cn("text-sm font-bold tabular-nums", snapshot.price.median_24h_change < 0 ? "text-red-400" : "text-emerald-400")}>
                  {snapshot.price.median_24h_change < 0 ? "-" : "+"}{fmt$$(Math.abs(snapshot.price.median_24h_change / 24))}/hr
                </span>
              : <span className="text-sm text-amber-500/50 italic font-medium">—</span>
            }
          </div>
          {/* Hourly Inventory Change */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">📦</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Hourly Inventory Change</p>
                <p className="text-[11px] text-slate-500">Net listing count change per hour today</p>
              </div>
            </div>
            {snapshot?.inventory?.inventory_24h_change != null
              ? <span className={cn("text-sm font-bold tabular-nums", snapshot.inventory.inventory_24h_change < 0 ? "text-red-400" : "text-emerald-400")}>
                  {snapshot.inventory.inventory_24h_change < 0 ? "" : "+"}{(snapshot.inventory.inventory_24h_change / 24).toFixed(1)}/hr
                </span>
              : <span className="text-sm text-amber-500/50 italic font-medium">—</span>
            }
          </div>
          {/* Tickets Sold */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">🎟</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Tickets Sold (est.)</p>
                <p className="text-[11px] text-slate-500">Estimated purchases based on listing disappearances</p>
              </div>
            </div>
            {seller?.removed_listings_24h != null
              ? <span className="text-sm font-bold tabular-nums text-red-400">{fmtNum(seller.removed_listings_24h)}</span>
              : <span className="text-sm text-amber-500/50 italic font-medium">—</span>
            }
          </div>
          {/* Tickets Added */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">➕</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Tickets Added (est.)</p>
                <p className="text-[11px] text-slate-500">Estimated new inventory entering market today</p>
              </div>
            </div>
            {seller?.new_listings_24h != null
              ? <span className="text-sm font-bold tabular-nums text-emerald-400">+{fmtNum(seller.new_listings_24h)}</span>
              : <span className="text-sm text-amber-500/50 italic font-medium">—</span>
            }
          </div>
          {/* Day-of Buy Window — forecast only, always pending */}
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-lg opacity-50">⏰</span>
              <div>
                <p className="text-sm font-semibold text-slate-300">Day-of Buy Window</p>
                <p className="text-[11px] text-slate-500">Forecast best time to purchase today</p>
              </div>
            </div>
            <span className="text-sm text-amber-500/50 italic font-medium">Pending</span>
          </div>
        </div>
      </section>

      {/* ═══════════════ MARKETPLACE SNAPSHOT ═══════════════ */}
      <section>
        <h2 className="text-base font-bold text-slate-200 uppercase tracking-wider mb-4">Where to Buy</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {marketplaces.length === 0 && (
            <div className="col-span-full rounded-xl border border-white/5 bg-[#161b27] py-8 text-center text-sm text-slate-600">
              No marketplace data available
            </div>
          )}
          {marketplaces.map((mp, i) => {
            const slug = mp.name.toLowerCase().replace(/\s+/g, "");
            const info = MP_META[slug] ?? { label: mp.name, short: mp.name.slice(0, 2).toUpperCase(), color: "#60a5fa" };
            const isCheapest = i === 0;
            const tracked    = eventMeta?.tracked_events?.find(
              t => t.marketplace_slug === slug || t.marketplace_slug.replace(/\s+/g, "") === slug
            );
            const freshness = eventMeta?.marketplace_freshness?.[slug];
            return (
              <div key={i} className={cn("relative rounded-xl border p-5 transition-all",
                isCheapest ? "border-emerald-500/50 bg-emerald-500/6" : "border-white/9 bg-[#161b27]")}>
                {isCheapest && (
                  <div className="absolute -top-2.5 left-4">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-[#0e1117] border border-emerald-500/40 rounded px-2 py-0.5">Best Price</span>
                  </div>
                )}
                {/* Header: marketplace name + freshness */}
                <div className="flex items-center gap-2 mb-4 mt-1">
                  <div className="w-1.5 h-6 rounded-full" style={{ background: info.color }} />
                  <span className="text-sm font-bold text-slate-100">{info.label}</span>
                  {freshness && (
                    <span className={cn("text-xs ml-auto",
                      freshness.freshness_status === "fresh" ? "text-emerald-500" :
                      freshness.freshness_status === "late"  ? "text-amber-400"   : "text-slate-600")}>
                      {freshness.age_minutes != null
                        ? freshness.age_minutes < 60 ? `${freshness.age_minutes}m ago` : `${Math.round(freshness.age_minutes / 60)}h ago`
                        : ""}
                    </span>
                  )}
                </div>
                {/* Price metrics */}
                <div className="space-y-2.5">
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Floor</span>
                    <span className={cn("text-xl font-bold tabular-nums", isCheapest ? "text-emerald-300" : "text-slate-100")}>
                      {fmt$$(mp.low_ask)}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Median</span>
                    <span className="text-base font-semibold text-slate-300 tabular-nums">{fmt$$(mp.median_ask)}</span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Listings</span>
                    <span className="text-sm text-slate-400 tabular-nums">{fmtNum(mp.listings)}</span>
                  </div>
                </div>
                {tracked?.external_url ? (
                  <a href={tracked.external_url} target="_blank" rel="noopener noreferrer"
                    className="mt-4 block w-full text-center text-sm font-bold py-2.5 rounded-xl border transition-all"
                    style={{
                      color: isCheapest ? "#34d399" : info.color,
                      borderColor: isCheapest ? "#34d39950" : info.color + "50",
                      background:  isCheapest ? "#34d39912" : info.color + "12",
                    }}>
                    Buy on {info.label} ↗
                  </a>
                ) : (
                  <div className="mt-4 block w-full text-center text-xs text-slate-600 py-2 rounded-xl border border-white/5">
                    No direct link
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══════════════ MARKET MOVEMENT ═══════════════ */}
      <section>
        <h2 className="text-base font-bold text-slate-200 uppercase tracking-wider mb-4">Market Movement</h2>
        {/* 4-column panel: Tracking Start | 7d | 24h | Now */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Tracking Start */}
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Tracking Start</p>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Floor</p>
                <p className="text-xl font-bold text-slate-300 tabular-nums">{fmt$$(history?.series?.[0]?.low_ask) ?? "—"}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Median</p>
                <p className="text-lg font-semibold text-slate-400 tabular-nums">{fmt$$(history?.series?.[0]?.median_ask) ?? "—"}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Inventory</p>
                <p className="text-base text-slate-400 tabular-nums">{fmtNum(history?.series?.[0]?.listings) ?? "—"}</p>
              </div>
            </div>
          </div>
          {/* 7d Change */}
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">7d Change</p>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Since start</p>
                <div className="text-xl font-bold">{sincePct != null ? <DeltaChip pct={sincePct} size="md" /> : <span className="text-slate-600">—</span>}</div>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Median</p>
                <div className="text-lg">{hero?.changes?.d7?.price_delta_pct != null ? <DeltaChip pct={hero.changes.d7.price_delta_pct} size="md" /> : <span className="text-slate-600 text-sm">—</span>}</div>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Inventory</p>
                <div className="text-base">{hero?.changes?.d7?.inventory_delta != null ? <DeltaChip abs={hero.changes.d7.inventory_delta} size="md" /> : <span className="text-slate-600 text-sm">—</span>}</div>
              </div>
            </div>
          </div>
          {/* 24h Change */}
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">24h Change</p>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Floor</p>
                <div className="text-xl font-bold">
                  {snapshot?.price?.floor_24h_change != null
                    ? <DeltaChip abs={snapshot.price.floor_24h_change} size="md" />
                    : <span className="text-slate-600">—</span>}
                </div>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Median</p>
                <div className="text-lg">{pct24h != null ? <DeltaChip pct={pct24h} size="md" /> : <span className="text-slate-600 text-sm">—</span>}</div>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Inventory</p>
                <div className="text-base">{invDelta24 != null ? <DeltaChip abs={invDelta24} size="md" /> : <span className="text-slate-600 text-sm">—</span>}</div>
              </div>
            </div>
          </div>
          {/* Now */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/4 p-5">
            <p className="text-xs text-emerald-500/70 uppercase tracking-wider mb-3">Now</p>
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Floor</p>
                <p className="text-2xl font-black text-white tabular-nums">{fmt$$(hero?.price?.low_ask) ?? "—"}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Median</p>
                <p className="text-xl font-bold text-slate-200 tabular-nums">{fmt$$(hero?.price?.median_ask) ?? "—"}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-600 mb-0.5">Inventory</p>
                <p className="text-base font-semibold text-slate-300 tabular-nums">{fmtNum(hero?.inventory?.total_listings) ?? "—"}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Inventory flow */}
        {(seller?.new_listings_24h != null || seller?.removed_listings_24h != null) && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            {seller?.new_listings_24h != null && (
              <div className="flex items-center justify-between px-4 py-3 rounded-xl border border-emerald-500/15 bg-emerald-500/4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Added 24h</p>
                  <p className="text-[10px] text-slate-700 italic mt-0.5">gross — includes relists</p>
                </div>
                <span className="text-lg font-bold text-emerald-400 tabular-nums">+{fmtNum(seller.new_listings_24h)}</span>
              </div>
            )}
            {seller?.removed_listings_24h != null && (
              <div className="flex items-center justify-between px-4 py-3 rounded-xl border border-red-500/15 bg-red-500/4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Disappeared 24h</p>
                  <p className="text-[10px] text-slate-700 italic mt-0.5">sold, expired, or delisted</p>
                </div>
                <span className="text-lg font-bold text-red-400 tabular-nums">{fmtNum(seller.removed_listings_24h)}</span>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ═══════════════ MARKETPLACE TRENDS ═══════════════ */}
      <section className="pb-2">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-200 uppercase tracking-wider">Marketplace Trends</h2>
          {!snapshot && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/60 border border-amber-500/25 rounded-lg px-2.5 py-1 bg-amber-500/5">Pending Intelligence Phase</span>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {([
            { slug: "stubhub",    short: "SH", label: "StubHub",     color: "#1c64f2" },
            { slug: "tickpick",   short: "TP", label: "TickPick",    color: "#7c3aed" },
            { slug: "gametime",   short: "GT", label: "Gametime",    color: "#0ea5e9" },
            { slug: "vividseats", short: "VS", label: "Vivid Seats", color: "#059669" },
          ] as const).map(({ slug, short, label, color }) => {
            const mp = snapshot?.per_marketplace_trends?.[slug];
            return (
              <div key={short} className="rounded-xl border border-white/7 bg-[#161b27] p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <span className="w-2 h-8 rounded flex-shrink-0" style={{ background: color }} />
                  <div>
                    <p className="text-sm font-bold uppercase tracking-wide" style={{ color }}>{short}</p>
                    <p className="text-xs text-slate-500">{label}</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Floor Now</span>
                    {mp?.floor_now != null
                      ? <span className="text-xs font-bold text-slate-200 tabular-nums">{fmt$$(mp.floor_now)}</span>
                      : <span className="text-xs text-slate-600">—</span>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Floor 24h</span>
                    {mp?.floor_change_pct != null
                      ? <DeltaChip pct={mp.floor_change_pct} />
                      : <span className="text-xs text-slate-600">—</span>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Inventory 24h</span>
                    {mp?.listings_change != null
                      ? <DeltaChip abs={mp.listings_change} />
                      : <span className="text-xs text-slate-600">—</span>}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Listings</span>
                    {mp?.listings_now != null
                      ? <span className="text-xs text-slate-400 tabular-nums">{fmtNum(mp.listings_now)}</span>
                      : <span className="text-xs text-slate-600">—</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══════════════ MARKETPLACE MOVEMENT ═══════════════ */}
      <section>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Marketplace Movement</h2>
        {baseline?.per_marketplace && baseline.per_marketplace.length > 0 ? (
          <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
            <div className="grid border-b border-white/5 px-4 py-2.5 text-xs text-slate-500 uppercase tracking-wider"
              style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr" }}>
              <div>Marketplace</div>
              <div className="text-right">Floor</div>
              <div className="text-right">Inv</div>
              <div className="text-right">24h</div>
              <div className="text-right">7d</div>
              <div className="text-right">Signal</div>
            </div>
            {baseline.per_marketplace.map((mp) => {
              const inv24 = mp.listings_change_24h?.absolute ?? null;
              const inv7d = mp.listings_change_7d?.absolute ?? null;
              const pct24 = mp.listings_change_24h?.pct ?? null;
              const slug = mp.marketplace_slug;
              const mpInfo = MP_META[slug] ?? { label: slug, short: slug.slice(0, 2).toUpperCase(), color: "#64748b" };
              const direction = inv24 != null ? (inv24 < -5 ? "↓ Tight" : inv24 > 5 ? "↑ Grow" : "Stable") : "—";
              const dirCls = inv24 != null ? (inv24 < -5 ? "text-emerald-400" : inv24 > 5 ? "text-red-400" : "text-slate-500") : "text-slate-600";
              return (
                <div key={slug} className="grid items-center px-4 py-3 border-b border-white/4 last:border-0 hover:bg-white/2"
                  style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr" }}>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: mpInfo.color }} />
                    <span className="text-sm font-bold uppercase tracking-wide flex-shrink-0" style={{ color: mpInfo.color }}>{mpInfo.short}</span>
                    <span className="text-xs text-slate-400 truncate hidden sm:inline">{mpInfo.label}</span>
                  </div>
                  <div className="text-right text-sm font-bold text-white tabular-nums">{fmt$$(mp.current_lowest_ask)}</div>
                  <div className="text-right text-sm text-slate-300 tabular-nums">{fmtNum(mp.current_listings)}</div>
                  <div className="text-right">
                    {inv24 != null
                      ? <span className={`text-sm font-semibold tabular-nums ${inv24 < 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {inv24 > 0 ? "+" : ""}{inv24}
                          {pct24 != null && <span className="text-xs ml-1 opacity-60">({fmtPct(pct24)})</span>}
                        </span>
                      : <span className="text-slate-500 text-sm">—</span>}
                  </div>
                  <div className="text-right">
                    {inv7d != null
                      ? <span className={`text-sm font-semibold tabular-nums ${inv7d < 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {inv7d > 0 ? "+" : ""}{inv7d}
                        </span>
                      : <span className="text-slate-500 text-sm">—</span>}
                  </div>
                  <div className={`text-right text-sm font-semibold ${dirCls}`}>{direction}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-white/7 bg-[#161b27] px-4 py-6 text-center">
            <p className="text-xs text-slate-500">Marketplace history pending.</p>
            <p className="text-[10px] text-slate-700 mt-1">Per-marketplace movement data will appear once baseline tracking accumulates.</p>
          </div>
        )}
      </section>

      {/* ═══════════════ ARTIST INTELLIGENCE ═══════════════ */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Artist Intelligence</h2>
          <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/50 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5">Pending Intelligence Phase</span>
        </div>
        <div className="rounded-xl border border-white/7 bg-[#161b27] divide-y divide-white/5">
          {([
            { label: "Previous City Performance", desc: "Last time this artist played this market — sell-through, price trajectory, and final floor." },
            { label: "Tour Pattern",              desc: "Where this date ranks across all tour stops by demand signal and expected sell-through." },
            { label: "Typical Price Curve",       desc: "Historical median price curve for this artist tier: early-bird, mid-cycle, and final-week." },
            { label: "Typical Inventory Curve",   desc: "How quickly this artist's inventory typically depletes — by section and price tier." },
            { label: "Average Day-Of Drop",       desc: "Average last-minute floor drop percentage for comparable events by this artist." },
          ] as const).map(({ label, desc }) => (
            <div key={label} className="flex items-start justify-between px-4 py-3 gap-4">
              <div>
                <p className="text-xs font-semibold text-slate-400">{label}</p>
                <p className="text-[10px] text-slate-600 mt-0.5 leading-relaxed">{desc}</p>
              </div>
              <span className="text-xs text-amber-500/40 italic font-medium flex-shrink-0 mt-0.5">Pending</span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ CITY INTELLIGENCE ═══════════════ */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">City Intelligence</h2>
          <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/50 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5">Pending Intelligence Phase</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {([
            { city: "Oakland",     abbr: "OAK", color: "#f59e0b" },
            { city: "Los Angeles", abbr: "LA",  color: "#3b82f6" },
            { city: "Phoenix",     abbr: "PHX", color: "#ef4444" },
            { city: "San Diego",   abbr: "SD",  color: "#10b981" },
          ] as const).map(({ city, abbr, color }) => (
            <div key={city} className="rounded-xl border border-white/7 bg-[#161b27] p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-1.5 h-5 rounded-sm flex-shrink-0" style={{ background: color }} />
                <div>
                  <p className="text-xs font-bold" style={{ color }}>{abbr}</p>
                  <p className="text-[10px] text-slate-600">{city}</p>
                </div>
              </div>
              <div className="space-y-2">
                {(["Comparable Events", "Market Demand", "Avg Floor"] as const).map(metric => (
                  <div key={metric} className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-600">{metric}</span>
                    <span className="text-[10px] text-amber-500/40 italic">Pending</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ BUY WINDOW FORECAST ═══════════════ */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Buy Window Forecast</h2>
          <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/50 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5">Pending Intelligence Phase</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {([
            { label: "Expected Floor",    desc: "Predicted floor on the optimal buy date." },
            { label: "Expected Median",   desc: "Predicted median price at optimal buy." },
            { label: "Expected Buy Time", desc: "Days before event to purchase." },
            { label: "Confidence",        desc: "Model confidence in this forecast." },
          ] as const).map(({ label, desc }) => (
            <div key={label} className="rounded-xl border border-white/7 bg-[#161b27] p-4">
              <p className="text-xs font-semibold text-slate-400 mb-1">{label}</p>
              <p className="text-[10px] text-slate-600 leading-relaxed mb-3">{desc}</p>
              <span className="text-lg font-bold text-amber-500/20">—</span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ DUPLICATE / SHARED INVENTORY ═══════════════ */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Duplicate &amp; Shared Inventory</h2>
          <span className="text-[10px] font-bold uppercase tracking-widest text-amber-500/50 border border-amber-500/20 rounded px-2 py-0.5 bg-amber-500/5">Pending Intelligence Phase</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {([
            { label: "Net Listings",    desc: "Deduplicated unique listing count." },
            { label: "Net Tickets",     desc: "Deduplicated unique ticket count." },
            { label: "Shared Listings", desc: "Listings appearing on 2+ marketplaces." },
            { label: "Shared Tickets",  desc: "Tickets in cross-listed inventory." },
            { label: "Duplicate Rate",  desc: "% of inventory that is duplicated." },
          ] as const).map(({ label, desc }) => (
            <div key={label} className="rounded-xl border border-white/7 bg-[#161b27] p-4">
              <p className="text-xs font-semibold text-slate-400 mb-1">{label}</p>
              <p className="text-[10px] text-slate-600 leading-relaxed mb-3">{desc}</p>
              <span className="text-lg font-bold text-amber-500/20">—</span>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ INTELLIGENCE PLACEHOLDERS ═══════════════ */}
      <section>
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Intelligence</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { label: "Buy Timing Intelligence",   icon: "⏱",  desc: "Optimal buy window based on historical price trajectory for this event type and venue." },
            { label: "Artist Trend",              icon: "🎤",  desc: "Demand trajectory across this artist's recent tour legs and comparable markets." },
            { label: "Tour Trend",                icon: "🗺",  desc: "Cross-city pricing comparison: how does this date rank vs. other tour stops?" },
            { label: "City Trend",                icon: "🏙",  desc: "LA market-wide event demand signals and competitive inventory context." },
            { label: "Venue Trend",               icon: "🏟",  desc: "Historical sell-through and price behavior for this specific venue and capacity." },
            { label: "Similar Events",            icon: "🔍",  desc: "Comparable events by artist tier, venue size, and demand profile for calibration." },
            { label: "Ticket Class Forecast",     icon: "🎟",  desc: "Per-section price trajectory — which sections are appreciating vs. softening?" },
            { label: "Sales Intelligence",        icon: "📊",  desc: "Sell-through rate, conversion velocity, and time-to-sell by section." },
            { label: "Inventory Intelligence",    icon: "📦",  desc: "Net inventory flow, relist detection, and seller concentration." },
            { label: "Duplicate Intelligence",    icon: "🔁",  desc: "Cross-marketplace duplicate listing detection and deduplication." },
            { label: "Sell-Through Intelligence", icon: "✅",  desc: "Confirmed purchase signals and section-level sell-through rates." },
          ].map(({ label, icon, desc }) => (
            <div key={label} className="rounded-xl border border-white/5 bg-[#161b27] px-4 py-3 flex items-start gap-3">
              <span className="text-lg opacity-40 flex-shrink-0 mt-0.5">{icon}</span>
              <div>
                <p className="text-xs font-semibold text-slate-400 mb-0.5">{label}</p>
                <p className="text-[10px] text-slate-600 mb-1.5 leading-relaxed">{desc}</p>
                <span className="inline-block text-[9px] font-bold uppercase tracking-widest text-amber-500/60 border border-amber-500/20 rounded px-1.5 py-0.5 bg-amber-500/5">
                  Pending Intelligence Phase
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════ PRICE HISTORY CHART ═══════════════ */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Price History</h2>
          <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
            {WINDOWS.map((w) => (
              <button key={w.id} onClick={() => setHistWindow(w.id)} disabled={loadingHistory}
                className={cn("px-2.5 py-1 transition-colors",
                  histWindow === w.id ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                {w.label}
              </button>
            ))}
            {loadingHistory && <span className="px-2 flex items-center"><RefreshCw size={9} className="animate-spin text-slate-500" /></span>}
          </div>
        </div>
        <div className="rounded-xl border border-white/7 bg-[#161b27]">
          {history?.source && (
            <div className={cn("px-4 py-2.5 border-b border-white/5 flex items-center justify-between",
              history.source === "combined" ? "bg-emerald-500/5" : history.source === "live" ? "bg-amber-500/5" : "")}>
              <span className={cn("text-xs font-medium",
                history.source === "combined" ? "text-emerald-400" :
                history.source === "live"     ? "text-amber-400"   : "text-blue-400")}>
                {history.source === "combined"
                  ? `${Math.round(history.data_depth_days ?? 0)} days of history`
                  : history.source === "live" ? "Live data · limited trend signal" : `${Math.round(history.data_depth_days ?? 0)}d archive`}
              </span>
              <span className="text-[10px] text-slate-600">{history.point_count ?? 0} points</span>
            </div>
          )}
          <div className="p-4">
            {history?.series?.length
              ? <PriceHistoryChart series={history.series} window={histWindow} height={220} />
              : <div className="h-[220px] flex items-center justify-center text-xs text-slate-600">Not enough data yet</div>
            }
          </div>
          {hero && (
            <div className="px-4 pb-3 grid grid-cols-5 gap-2 border-t border-white/5">
              {[
                { label: "Floor",  val: hero.price?.low_ask    },
                { label: "p25",    val: hero.price?.p25_ask    },
                { label: "Median", val: hero.price?.median_ask },
                { label: "p75",    val: hero.price?.p75_ask    },
                { label: "High",   val: hero.price?.high_ask   },
              ].map(({ label, val }) => (
                <div key={label} className="text-center pt-2">
                  <div className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">{label}</div>
                  <div className="text-xs font-semibold text-slate-300 tabular-nums">{fmt$$(val)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════ LOWEST LISTINGS ═══════════════ */}
      {listings && listings.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Lowest Available Tickets</h2>
          <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-x-auto">
            <table className="w-full text-xs min-w-[480px]">
              <thead>
                <tr className="border-b border-white/5">
                  {["#", "Price", "Section", "Row", "Qty", "Marketplace", "Move", ""].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[9px] text-slate-500 uppercase tracking-wider font-medium first:pl-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {listings.map((l, i) => {
                  const slug   = l.marketplace_slug;
                  const mpInfo = MP_META[slug] ?? null;
                  return (
                    <tr key={l.id} className="border-b border-white/4 last:border-0 hover:bg-white/2 transition-colors">
                      <td className="pl-4 pr-2 py-2.5 text-slate-600 tabular-nums">{i + 1}</td>
                      <td className="px-3 py-2.5 font-bold text-slate-100 tabular-nums">{fmt$$(l.price)}</td>
                      <td className="px-3 py-2.5 text-slate-300 max-w-[140px] truncate">{l.section_name ?? l.section ?? "—"}</td>
                      <td className="px-3 py-2.5 text-slate-400">{l.row ?? "—"}</td>
                      <td className="px-3 py-2.5 text-slate-500 tabular-nums">{l.quantity}</td>
                      <td className="px-3 py-2.5">
                        {mpInfo
                          ? <span className="inline-flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full" style={{ background: mpInfo.color }} />
                              <span className="text-slate-400">{mpInfo.short}</span>
                            </span>
                          : <span className="text-slate-500 capitalize">{slug}</span>}
                      </td>
                      {/* Hidden / Parking workflow placeholder */}
                      <td className="px-3 py-2.5">
                        <ListingMoveMenu listingId={l.id} />
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        {l.listing_url && (
                          <a href={l.listing_url} target="_blank" rel="noopener noreferrer"
                            className="text-[10px] text-blue-500 hover:text-blue-400 transition-colors">buy ↗</a>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ═══════════════ SELLER ACTIVITY ═══════════════ */}
      {seller && (
        <section>
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Seller Activity</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { label: "Added 24h",       sublabel: "gross, incl. relists",  value: fmtDelta(seller.new_listings_24h),     cls: "text-emerald-400" },
              { label: "Disappeared 24h", sublabel: "sold/expired/delisted", value: fmtDelta(seller.removed_listings_24h), cls: "text-red-400"     },
              { label: "Repriced 24h",    sublabel: "sellers changed ask",   value: fmtNum(seller.repriced_24h),            cls: "text-amber-400"   },
              { label: "Price drops 24h", sublabel: "ask lowered",           value: fmtNum(seller.price_drops_24h),         cls: "text-red-400"     },
            ].map(({ label, sublabel, value, cls }) => (
              <div key={label} className="rounded-xl border border-white/6 bg-[#161b27] px-3 py-3">
                <p className="text-[9px] text-slate-500 uppercase tracking-wider leading-tight">{label}</p>
                <p className="text-[8px] text-slate-700 mb-1.5 italic">{sublabel}</p>
                <p className={cn("text-lg font-bold tabular-nums", cls)}>{value ?? "—"}</p>
              </div>
            ))}
          </div>
          {seller.largest_price_drops?.length > 0 && (
            <div className="mt-2 rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
              <div className="px-4 py-2 border-b border-white/5 text-[10px] text-slate-500 uppercase tracking-wider font-medium">Largest Price Drops</div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5">
                    {["Section", "Was", "Now", "Drop"].map(h => (
                      <th key={h} className="text-left px-4 py-2 text-[9px] text-slate-600 uppercase tracking-wider font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {seller.largest_price_drops.slice(0, 5).map((d, i) => (
                    <tr key={i} className="border-b border-white/4 last:border-0 hover:bg-white/2">
                      <td className="px-4 py-2 text-slate-300 max-w-[120px] truncate">{d.section}</td>
                      <td className="px-4 py-2 text-slate-500 tabular-nums">{fmt$$(d.old_price)}</td>
                      <td className="px-4 py-2 text-slate-200 font-semibold tabular-nums">{fmt$$(d.new_price)}</td>
                      <td className="px-4 py-2 text-red-400 font-medium tabular-nums">{fmt$$(d.delta)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* ═══════════════ SECTION BREAKDOWN ═══════════════ */}
      {sections?.sections && sections.sections.length > 0 && (
        <SectionBreakdown sections={sections.sections} />
      )}

      {/* ═══════════════ VENUE SUMMARY ═══════════════ */}
      {eventMeta?.venue_slug && (
        <section>
          <VenueSummaryCard venueSlug={eventMeta.venue_slug} />
          <VenueIntelligence venueSlug={eventMeta.venue_slug} eventId={id} />
        </section>
      )}
    </div>
  );
}
