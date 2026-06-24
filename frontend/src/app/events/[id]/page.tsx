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
import { useNflAudio } from "@/hooks/useNflAudio";
import { isNflEvent } from "@/lib/audioConfig";
import NflAudioControl from "@/components/NflAudioControl";
import {
  fmt$$, fmtNum, fmtPct, fmtDelta, cn,
  signalToAction, actionColors, signalDescription, parseEventDate,
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
                {["Section", "Listings", "Low", "Median"].map((h) => (
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
  const [activeHistTab, setActiveHistTab] = useState<"Price" | "Inventory" | "Sections" | "Marketplaces">("Price");
  const [diagOpen, setDiagOpen] = useState(false);
  const followRef = useRef<HTMLDivElement>(null);
  const nflAudio = useNflAudio();

  const [eventMeta, setEventMeta] = useState<EventMeta | null>(null);
  const [hero, setHero]           = useState<HeroResponse | null>(null);
  const [market, setMarket]       = useState<MarketResponse | null>(null);
  const [history, setHistory]     = useState<HistoryResponse | null>(null);
  const [sections, setSections]   = useState<SectionsResponse | null>(null);
  const [seller, setSeller]       = useState<SellerResponse | null>(null);
  const [listings, setListings]   = useState<Listing[] | null>(null);
  const [baseline, setBaseline]   = useState<BaselineResponse | null>(null);
  const [snapshot, setSnapshot]   = useState<EventSnapshotResponse | null>(null);
  const [alerts, setAlerts]       = useState<import("@/lib/types").AlertResponse | null>(null);
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
      api.events.alerts(id).then(setAlerts).catch(() => {}),
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
  const isCompleted = dateStr ? new Date(dateStr).getTime() + 24 * 3600 * 1000 < Date.now() : false;

  let dateLabel = "";
  if (dateStr) {
    try { dateLabel = format(parseEventDate(dateStr), "EEEE, MMMM d, yyyy"); } catch {}
  }

  const { headline, bullets } = buildSignalReason(action, hero);
  const pct24h      = hero?.changes?.h24?.price_delta_pct ?? null;
  // Use canonical baseline for inventory delta (accurate) instead of hero listing_snapshots (fallback bug)
  const invDelta24  = baseline?.deltas_24h?.raw_listings?.absolute ?? hero?.changes?.h24?.inventory_delta ?? null;
  const marketplaces = (market?.marketplaces ?? []).sort((a, b) => (a.low_ask ?? 9999) - (b.low_ask ?? 9999));

  // Tracking since — from event created_at
  const trackingSince = (() => {
    const ca = eventMeta?.created_at;
    if (!ca) return null;
    try {
      const d = parseISO(ca);
      const days = Math.round((Date.now() - d.getTime()) / 86400000);
      return { formatted: format(d, "MMM d, yyyy"), days };
    } catch { return null; }
  })();
  const marketsCount = Object.keys(eventMeta?.marketplace_freshness ?? {}).filter(
    k => (eventMeta?.marketplace_freshness?.[k] as { freshness_status?: string } | undefined)?.freshness_status !== "dead"
  ).length;
  const feedsCount = eventMeta?.tracked_events?.filter(t => t.is_active).length ?? 0;

  // True if this event has no marketplace data at all (no prices, no freshness entries, no listings)
  // Indicates the event was never tracked — e.g. completed before URLs were configured.
  const hasNoMarketplaceData = eventMeta != null
    && Object.keys(eventMeta.all_marketplace_prices ?? {}).length === 0
    && Object.keys(eventMeta.marketplace_freshness ?? {}).length === 0
    && (market?.marketplaces?.length ?? 0) === 0;

  const sincePct = (() => {
    if (!history?.series?.length || history.series.length < 2) return null;
    const first = history.series[0].median_ask ?? history.series[0].low_ask;
    const last  = history.series[history.series.length - 1].median_ask ?? history.series[history.series.length - 1].low_ask;
    if (!first || !last) return null;
    return ((last - first) / first) * 100;
  })();

  // Freshness label for Section 2
  const freshLabel = (() => {
    const entries = Object.values(eventMeta?.marketplace_freshness ?? {});
    if (!entries.length) return null;
    const ages = entries.map((e: unknown) => ((e as { age_minutes?: number }).age_minutes ?? 0)).filter(Boolean);
    if (!ages.length) return null;
    const maxAge = Math.max(...ages);
    return maxAge < 60 ? `${maxAge} minutes ago` : `${Math.round(maxAge / 60)} hours ago`;
  })();

  const MP_SLUGS: Array<keyof typeof MP_META> = ["stubhub", "tickpick", "gametime", "vividseats"];

  // ── NFL audio: auto-trigger on NFL event page load ──────────────────────────
  // (effect runs after eventMeta loads; requires user-gesture priming from homepage)
  const nflAudioTriggered = useRef(false);
  useEffect(() => {
    if (!eventMeta || nflAudioTriggered.current) return;
    if (isNflEvent(eventMeta.title ?? "", eventMeta.artist)) {
      nflAudioTriggered.current = true;
      nflAudio.triggerFromUserAction();
    }
  }, [eventMeta]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Derived: seller mood from capitulation + signal ────────────────────────
  const sellerMood = (() => {
    const cap = hero?.market?.capitulation_score ?? null;
    if (cap == null) return "—";
    if (cap > 0.65) return "Cutting prices";
    if (cap > 0.35) return "Mixed";
    return "Holding firm";
  })();

  // ─── Skeleton ────────────────────────────────────────────────────────────────
  if (loadingAll && !hero && !eventMeta) {
    return (
      <div className="max-w-7xl mx-auto space-y-4 pb-8">
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500">
          <ArrowLeft size={12} /> Active Markets
        </Link>
        <div className="h-36 rounded-xl bg-[#161b27] border border-white/5 animate-pulse" />
        <div className="h-52 rounded-xl bg-[#161b27] border border-white/5 animate-pulse" />
        <div className="h-40 rounded-xl bg-[#161b27] border border-white/5 animate-pulse" />
      </div>
    );
  }

  const isNfl = isNflEvent(title, artist);

  return (
    <div className="max-w-7xl mx-auto space-y-4 pb-8">

      {/* UI BUILD MARKER */}
      <div className="fixed top-2 right-2 z-50 text-[9px] font-mono bg-amber-400 text-black px-2 py-0.5 rounded opacity-80 pointer-events-none select-none">
        UI BUILD {new Date().toISOString().slice(0,16).replace("T"," ")}
      </div>

      {/* Back nav + actions row */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors">
          <ArrowLeft size={12} /> Active Markets
        </Link>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button onClick={() => toggleWatch(id)}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isWatched ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <Bookmark size={11} className={isWatched ? "fill-blue-400" : ""} />
            {isWatched ? "Watching" : "Watch"}
          </button>
          {artist && (
            <div className="relative" ref={followRef}>
              <button onClick={() => setShowFollowPanel(v => !v)}
                className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
                  showFollowPanel ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:border-white/20")}>
                <Bell size={11} />
                Follow
                <ChevronDown size={9} className={cn("transition-transform", showFollowPanel && "rotate-180")} />
              </button>
              {showFollowPanel && <FollowPanel artist={artist} onClose={() => setShowFollowPanel(false)} />}
            </div>
          )}
          <button onClick={() => toggleArchive(id)}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isArchived ? "border-amber-500/40 bg-amber-500/10 text-amber-400" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <Archive size={11} />
            {isArchived ? "Archived" : "Archive"}
          </button>
          <button onClick={() => toggleHide(id)}
            className={cn("inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all",
              isHidden ? "border-slate-500/40 bg-slate-500/10 text-slate-300" : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300 hover:border-white/20")}>
            <EyeOff size={11} />
            {isHidden ? "Hidden" : "Hide"}
          </button>
          {!isSports && (spotify.spotifyArtistUrl ? (
            <a href={spotify.spotifyArtistUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-[#1db954]/30 bg-[#1db954]/8 text-[#1db954] hover:bg-[#1db954]/15 transition-all">
              <Music size={11} /> Spotify
            </a>
          ) : null)}
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
      {hasNoMarketplaceData && (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-slate-500/20 bg-white/[0.02] text-xs text-slate-500">
          <span className="flex-shrink-0 text-slate-600">◎</span>
          {isCompleted
            ? "No market data was collected for this event — it completed before marketplace tracking was configured."
            : "No marketplace URLs configured. Add a StubHub, TickPick, Gametime, or Vivid Seats URL to begin tracking."}
        </div>
      )}
      {alerts && alerts.alerts.filter(a => a.severity === "RED").length > 0 && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/8 px-4 py-3">
          <div className="flex items-start gap-2.5">
            <span className="text-red-400 font-black mt-0.5 flex-shrink-0">⚠</span>
            <ul className="space-y-0.5">
              {alerts.alerts.filter(a => a.severity === "RED").map((a, i) => (
                <li key={i} className="text-red-300/80 text-xs leading-snug">
                  {a.marketplace ? <span className="font-semibold text-red-300 capitalize">{a.marketplace}: </span> : null}
                  {a.message.split("\n")[0].slice(0, 140)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════
          SECTION 1 — EVENT HEADER (compact, ~130px)
          Three columns: artwork | event info | tracking stats
          ════════════════════════════════════════ */}
      <section className="rounded-xl border border-white/8 bg-[#0f1420] p-4">
        <div className="flex items-center gap-4">

          {/* LEFT — Artwork 96×96 */}
          <div className="flex-shrink-0 w-24 h-24 rounded-xl overflow-hidden"
            style={{ background: `linear-gradient(145deg, ${gradient[0]}, ${gradient[1]})` }}>
            {artworkUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={artworkUrl} alt={artist ?? title}
                className="w-full h-full object-cover object-top"
                onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-3xl font-black text-white/70 select-none">
                {(artist ?? title).slice(0, 1).toUpperCase()}
              </div>
            )}
          </div>

          {/* CENTER — Event identity */}
          <div className="flex-1 min-w-0">
            {/* Only show artist label when it differs from the event title (prevents "Kid Cudi / Kid Cudi") */}
            {artist && artist !== title && (
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-0.5 truncate">{artist}</p>
            )}
            <h1 className="text-lg sm:text-xl font-bold text-white leading-tight line-clamp-1">{title}</h1>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1 text-xs text-slate-400">
              {venue     && <span className="flex items-center gap-1"><MapPin size={10} className="opacity-60 flex-shrink-0" /><span className="truncate">{venue}</span></span>}
              {dateLabel && <span className="flex items-center gap-1"><Calendar size={10} className="opacity-60 flex-shrink-0" />{dateLabel}</span>}
            </div>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              {daysOut != null && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                  style={{ color: aColors.text, background: aColors.bg + "50", border: `1px solid ${aColors.border}` }}>
                  {isCompleted ? "Event passed" : daysOut < 1 ? "Happening today" : daysOut < 2 ? "Tomorrow" : `${Math.round(daysOut)}d away`}
                </span>
              )}
              {isCompleted && (
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 bg-white/5 border border-white/10 rounded-full px-2 py-0.5">Completed</span>
              )}
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                style={{ color: aColors.text, borderColor: aColors.border + "80", background: aColors.bg + "30" }}>
                {action}
              </span>
            </div>
          </div>

          {/* RIGHT — Tracking stats (wireframe: Tracking Since / Last Update / Markets / Feeds) */}
          <div className="hidden sm:flex flex-col gap-2.5 text-right flex-shrink-0 min-w-[110px]">
            {trackingSince && (
              <div>
                <p className="text-[9px] text-slate-600 uppercase tracking-wider">Tracking Since</p>
                <p className="text-xs font-semibold text-slate-200">{trackingSince.formatted}</p>
                <p className="text-[9px] text-slate-600">({trackingSince.days} days)</p>
              </div>
            )}
            {freshLabel && (
              <div>
                <p className="text-[9px] text-slate-600 uppercase tracking-wider">Last Update</p>
                <p className="text-xs font-semibold text-slate-200">{freshLabel}</p>
              </div>
            )}
            <div className="flex items-start gap-4 justify-end">
              <div>
                <p className="text-[9px] text-slate-600 uppercase tracking-wider">Markets</p>
                <p className="text-sm font-bold text-slate-200">{marketsCount || "—"}</p>
              </div>
              <div>
                <p className="text-[9px] text-slate-600 uppercase tracking-wider">Feeds</p>
                <p className="text-sm font-bold text-slate-200">{feedsCount || "—"}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          SECTION 2 — MARKET INTELLIGENCE HERO (~200px)
          Three columns: Current Market | Market Absorption | Seller Behavior
          ════════════════════════════════════════ */}
      <section className="rounded-xl border border-white/8 bg-[#0f1420] overflow-hidden">
        <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/8"
          style={{ gridTemplateColumns: "1fr 1.2fr 1fr" }}>

          {/* Col 1: Current Market */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">Current Market</p>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded border border-white/10 text-slate-500 bg-white/3">24H ▾</span>
            </div>
            <div className="space-y-0">
              {[
                { label: "Low",    val: fmt$$(hero?.price?.low_ask),                            cls: "text-emerald-300" },
                { label: "Median", val: fmt$$(hero?.price?.median_ask),                          cls: "text-white" },
                { label: "High",   val: fmt$$(hero?.price?.high_ask ?? hero?.price?.p75_ask),   cls: "text-slate-300" },
              ].map(({ label, val, cls }) => (
                <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                  <span className="text-xs text-slate-400">{label}</span>
                  <span className={cn("text-sm font-bold tabular-nums", cls)}>{val ?? "—"}</span>
                </div>
              ))}
              <div className="flex items-center justify-between py-1.5">
                <span className="text-xs text-slate-400">Inventory</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-bold text-slate-200 tabular-nums">
                    {fmtNum(baseline?.current?.raw_listings ?? hero?.inventory?.total_listings) ?? "—"}
                  </span>
                  {invDelta24 != null && (
                    <span className={cn("text-[11px] font-semibold tabular-nums",
                      invDelta24 > 0 ? "text-emerald-400" : "text-red-400")}>
                      ({invDelta24 > 0 ? "+" : ""}{invDelta24})
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Col 2: Market Absorption — primary emphasis */}
          <div className="p-4 bg-white/[0.02]">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-3">Absorption</p>
            {/* Est. Avg Sale Price — primary metric */}
            <div className="mb-3 pb-3 border-b border-white/8">
              <p className="text-[10px] text-slate-500 mb-0.5">Estimated Avg Sale Price</p>
              <p className="text-xl font-black text-amber-300 tabular-nums">—</p>
              <p className="text-[10px] text-amber-600/60 italic">Tracking</p>
            </div>
            <div className="space-y-0">
              {[
                { label: "Tickets Sold",   val: null as string | null },
                { label: "24H Sold",       val: null as string | null },
                { label: "7D Sold",        val: null as string | null },
                { label: "Since Tracking", val: null as string | null },
              ].map(({ label, val }) => (
                <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
                  <span className="text-xs text-slate-400">{label}</span>
                  <span className="text-[11px] text-slate-600">{val ?? "—"}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Col 3: Seller Behavior */}
          <div className="p-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-3">Seller Behavior</p>
            <div className="space-y-0">
              <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                <span className="text-xs text-slate-400">Relist Price Change</span>
                <span className="text-[11px] text-slate-600">—</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                <span className="text-xs text-slate-400">Price Drops</span>
                <span className={cn("text-sm font-bold tabular-nums", seller?.price_drops_24h ? "text-red-400" : "text-slate-500")}>
                  {seller?.price_drops_24h != null ? fmtNum(seller.price_drops_24h) : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                <span className="text-xs text-slate-400">Repriced Listings</span>
                <span className={cn("text-sm font-bold tabular-nums", seller?.repriced_24h ? "text-amber-400" : "text-slate-500")}>
                  {seller?.repriced_24h != null ? fmtNum(seller.repriced_24h) : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-xs text-slate-400">Seller Mood</span>
                <span className="text-sm font-bold text-slate-300">{sellerMood ?? "—"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Freshness bar */}
        <div className="border-t border-white/6 px-4 py-2 flex items-center gap-3 flex-wrap bg-white/[0.01]">
          {freshLabel && (
            <span className="text-[10px] text-slate-600 flex items-center gap-1">
              <Clock size={9} /> Updated {freshLabel}
            </span>
          )}
          {MP_SLUGS.map(slug => {
            const f    = eventMeta?.marketplace_freshness?.[slug] as { freshness_status?: string; age_minutes?: number } | undefined;
            const info = MP_META[slug];
            if (!info) return null;
            const st  = f?.freshness_status ?? "unknown";
            const cls = st === "fresh" ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/8"
                      : st === "late"  ? "text-amber-400 border-amber-500/30 bg-amber-500/8"
                      : st === "dead"  ? "text-red-500 border-red-500/30 bg-red-500/8"
                      : "text-slate-600 border-white/8 bg-white/3";
            return (
              <span key={slug} className={`text-[10px] font-bold px-2 py-0.5 rounded border ${cls}`}>
                {info.short} {st === "fresh" ? "✓" : st === "late" ? "~" : st === "dead" ? "✗" : "—"}
              </span>
            );
          })}
        </div>
      </section>

      {/* ════════════════════════════════════════
          SECTION 3 — ARTIST CONTEXT / SPOTIFY
          Directly below the hero.
          ════════════════════════════════════════ */}
      {!isSports && spotify.spotifyArtistUrl && (
        <SpotifyEmbed artistUrl={spotify.spotifyArtistUrl} playlistUrl={spotify.spotifyPlaylistUrl} />
      )}

      {/* ════════════════════════════════════════
          SECTION 4 — MARKETPLACE ACTIVITY (moved above venue intel per wireframe)
          ════════════════════════════════════════ */}
      <section>
        <p className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-3">Marketplace Activity</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {MP_SLUGS.map(slug => {
            const info    = MP_META[slug]!;
            const mpData  = marketplaces.find(m => m.name.toLowerCase().replace(/\s+/g, "") === slug);
            const bsData  = baseline?.per_marketplace?.find(m => m.marketplace_slug === slug);
            const fresh   = eventMeta?.marketplace_freshness?.[slug] as { freshness_status?: string; age_minutes?: number } | undefined;
            const tracked = eventMeta?.tracked_events?.find(t => t.marketplace_slug === slug);
            const st      = fresh?.freshness_status ?? "unknown";
            const freshDot = st === "fresh" ? "bg-emerald-400" : st === "late" ? "bg-amber-400" : st === "dead" ? "bg-red-500" : "bg-slate-700";
            const inv24   = bsData?.listings_change_24h?.absolute ?? null;
            const isBest  = mpData != null && marketplaces.length > 0 && mpData.low_ask === marketplaces[0].low_ask;
            const mpAction = signalToAction(hero?.signal);
            const mpColors = actionColors(mpAction);

            return (
              <div key={slug} className="rounded-xl border border-white/8 bg-[#0f1420] p-3 flex flex-col gap-2.5">
                {/* Card header: name + freshness dot */}
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold" style={{ color: info.color }}>{info.label}</span>
                  <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${freshDot}`} />
                </div>

                {/* Low / Median */}
                <div className="grid grid-cols-2 gap-1.5">
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Low</p>
                    <p className={cn("text-sm font-black tabular-nums", isBest ? "text-emerald-300" : "text-white")}>
                      {fmt$$(mpData?.low_ask) ?? "—"}
                      {isBest && <span className="text-[8px] text-emerald-500 font-bold ml-0.5">B</span>}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Median</p>
                    <p className="text-sm font-bold text-slate-200 tabular-nums">{fmt$$(mpData?.median_ask) ?? "—"}</p>
                  </div>
                </div>

                {/* Inventory / Sold */}
                <div className="grid grid-cols-2 gap-1.5 pt-2 border-t border-white/5">
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Inventory</p>
                    <p className="text-xs font-bold text-slate-300 tabular-nums">
                      {mpData?.listings != null ? fmtNum(mpData.listings) : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Sold (24H)</p>
                    <p className={cn("text-xs font-bold tabular-nums", inv24 != null && inv24 < 0 ? "text-emerald-400" : "text-slate-500")}>
                      {inv24 != null && inv24 < 0 ? Math.abs(inv24) : "—"}
                    </p>
                  </div>
                </div>

                {/* Est Sale / Relist */}
                <div className="grid grid-cols-2 gap-1.5">
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Est. Sale</p>
                    <p className="text-xs text-slate-600">—</p>
                  </div>
                  <div>
                    <p className="text-[9px] text-slate-500 mb-0.5">Relist</p>
                    <p className="text-xs text-slate-600">—</p>
                  </div>
                </div>

                {/* BUY chip + View link */}
                <div className="flex items-center gap-1.5 mt-auto pt-1.5 border-t border-white/5">
                  <span className="text-[9px] font-black px-1.5 py-0.5 rounded border flex-shrink-0"
                    style={{ color: mpColors.text, borderColor: mpColors.border + "60", background: mpColors.bg + "25" }}>
                    {mpAction}
                  </span>
                  {tracked?.external_url && (
                    <a href={tracked.external_url} target="_blank" rel="noopener noreferrer"
                      className="ml-auto text-[9px] font-semibold text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-0.5">
                      View <ArrowUpRight size={8} />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ════════════════════════════════════════
          SECTION 5 — VENUE INTELLIGENCE (moved below marketplace per wireframe)
          Two-column: map left, top sections right.
          ════════════════════════════════════════ */}
      {eventMeta?.venue_slug && (
        <section>
          <p className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-3">Venue Intelligence</p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
            {/* LEFT — Interactive venue map + section details */}
            <div>
              <VenueIntelligence venueSlug={eventMeta.venue_slug} eventId={id} />
            </div>

            {/* RIGHT — Top 5 Moving Sections by activity */}
            <div className="rounded-xl border border-white/8 bg-[#0f1420] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/6 flex items-center justify-between">
                <p className="text-xs font-semibold text-slate-300">Top Sections by Activity</p>
                <p className="text-[10px] text-slate-600">sorted by activity score</p>
              </div>
              {sections?.sections && sections.sections.length > 0 ? (
                <div>
                  {[...sections.sections]
                    .sort((a, b) => (b.activity_score ?? 0) - (a.activity_score ?? 0))
                    .slice(0, 5)
                    .map((s, i) => {
                      const inv24 = null; // per-section 24h not in SectionRow
                      return (
                        <div key={i} className="flex items-center gap-3 px-4 py-3 border-b border-white/5 last:border-0 hover:bg-white/2 transition-colors">
                          <span className="text-[10px] font-bold text-slate-600 w-4 tabular-nums">{i + 1}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-slate-200 truncate">{s.display_name}</p>
                            <p className="text-[10px] text-slate-600">
                              {s.listings != null ? `${fmtNum(s.listings)} listings` : ""}
                              {s.listings != null && s.low_ask != null ? " · " : ""}
                              {s.low_ask != null ? `from ${fmt$$(s.low_ask)}` : ""}
                            </p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-xs font-bold text-slate-200 tabular-nums">{fmt$$(s.median_ask) ?? "—"}</p>
                            <p className="text-[10px] text-slate-600">median</p>
                          </div>
                          {s.activity_score != null && (
                            <div className="w-1 h-8 rounded-full flex-shrink-0"
                              style={{ background: `rgba(59,130,246,${Math.min(s.activity_score, 1)})` }} />
                          )}
                          <span className="text-[10px] text-slate-600 w-12 text-right tabular-nums flex-shrink-0">
                            {inv24 ?? "—"}
                          </span>
                        </div>
                      );
                    })}
                  <div className="px-4 py-2 border-t border-white/5">
                    <p className="text-[10px] text-slate-700">Activity = listing velocity + price movement. Relist data pending.</p>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-600">Section data not yet available</div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ════════════════════════════════════════
          SECTION 6 — MARKET SUMMARY
          Max 5 concise bullets.
          ════════════════════════════════════════ */}
      <section>
        <p className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-3">Market Summary</p>
        <div className="rounded-xl border border-white/8 bg-[#0f1420] p-4">
          <ul className="space-y-2">
            {bullets.slice(0, 5).map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300 leading-relaxed">
                <span className="mt-2 w-1.5 h-1.5 rounded-full bg-slate-500 flex-shrink-0" />
                {b}
              </li>
            ))}
            {bullets.length === 0 && (
              <li className="text-sm text-slate-600">Insufficient data for market summary. Check back as data accumulates.</li>
            )}
          </ul>
          {hero?.history_context?.hours_available != null && (
            <p className="mt-3 pt-3 border-t border-white/6 text-[10px] text-slate-600 flex items-center gap-1.5">
              <Clock size={9} />
              {hero.history_context.hours_available > 24
                ? `${Math.round(hero.history_context.hours_available / 24)}d of price history`
                : "Live data only — limited trend signal"}
              {sincePct != null && (
                <span className="ml-2 flex items-center gap-1">
                  <DeltaChip pct={sincePct} />
                  <span className="text-slate-600">since tracking</span>
                </span>
              )}
            </p>
          )}
        </div>
      </section>

      {/* ════════════════════════════════════════
          SECTION 7 — HISTORICAL ANALYSIS
          Tabbed: Price | Inventory | Sections | Marketplaces
          ════════════════════════════════════════ */}
      <section>
        <p className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-3">Historical Analysis</p>

        {/* Tab bar */}
        <div className="flex border-b border-white/8 mb-4 gap-0 overflow-x-auto">
          {(["Price", "Inventory", "Sections", "Marketplaces"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveHistTab(tab)}
              className={cn(
                "px-4 py-2.5 text-sm font-semibold transition-colors border-b-2 -mb-[1px] whitespace-nowrap",
                activeHistTab === tab
                  ? "border-blue-500 text-blue-300"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              )}>
              {tab}
            </button>
          ))}
        </div>

        {/* ── Price tab ── */}
        {activeHistTab === "Price" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex rounded-lg border border-white/7 overflow-hidden text-xs">
                {WINDOWS.map(w => (
                  <button key={w.id} onClick={() => setHistWindow(w.id)} disabled={loadingHistory}
                    className={cn("px-2.5 py-1 transition-colors",
                      histWindow === w.id ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                    {w.label}
                  </button>
                ))}
                {loadingHistory && <span className="px-2 flex items-center"><RefreshCw size={9} className="animate-spin text-slate-500" /></span>}
              </div>
              {history?.source && (
                <span className={cn("text-xs font-medium",
                  history.source === "combined" ? "text-emerald-400" : history.source === "live" ? "text-amber-400" : "text-blue-400")}>
                  {history.source === "combined"
                    ? `${Math.round(history.data_depth_days ?? 0)}d of history`
                    : history.source === "live" ? "Live · limited signal" : `${Math.round(history.data_depth_days ?? 0)}d archive`}
                </span>
              )}
            </div>
            <div className="rounded-xl border border-white/7 bg-[#161b27]">
              <div className="p-4">
                {history?.series?.length
                  ? <PriceHistoryChart series={history.series} window={histWindow} height={220} />
                  : <div className="h-[220px] flex items-center justify-center text-xs text-slate-600">Not enough data yet</div>}
              </div>
              {hero && (
                <div className="px-4 pb-3 grid grid-cols-4 gap-2 border-t border-white/5">
                  {[
                    { label: "Low",    val: hero.price?.low_ask    },
                    { label: "p25",    val: hero.price?.p25_ask    },
                    { label: "Median", val: hero.price?.median_ask },
                    { label: "p75",    val: hero.price?.p75_ask    },
                  ].map(({ label, val }) => (
                    <div key={label} className="text-center pt-2">
                      <div className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">{label}</div>
                      <div className="text-xs font-semibold text-slate-300 tabular-nums">{fmt$$(val)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Inventory tab ── */}
        {activeHistTab === "Inventory" && (
          <div className="rounded-xl border border-white/7 bg-[#161b27] p-4 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Total Now",   val: fmtNum(hero?.inventory?.total_listings) },
                { label: "24h Net",     val: invDelta24 != null ? (invDelta24 > 0 ? `+${invDelta24}` : `${invDelta24}`) : null },
                { label: "Added 24h",   val: seller?.new_listings_24h != null ? `+${fmtNum(seller.new_listings_24h)}` : null },
                { label: "Removed 24h", val: seller?.removed_listings_24h != null ? fmtNum(seller.removed_listings_24h) : null },
              ].map(({ label, val }) => (
                <div key={label}>
                  <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">{label}</p>
                  <p className="text-sm font-bold text-slate-300 tabular-nums">{val ?? "—"}</p>
                </div>
              ))}
            </div>
            {seller && (
              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-white/5">
                {[
                  { label: "Repriced 24h",    val: fmtNum(seller.repriced_24h),    cls: "text-amber-400" },
                  { label: "Price Drops 24h", val: fmtNum(seller.price_drops_24h), cls: "text-red-400" },
                ].map(({ label, val, cls }) => (
                  <div key={label}>
                    <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-0.5">{label}</p>
                    <p className={cn("text-sm font-bold tabular-nums", cls)}>{val ?? "—"}</p>
                  </div>
                ))}
              </div>
            )}
            {/* Largest price drops detail */}
            {(seller?.largest_price_drops?.length ?? 0) > 0 && seller && (
              <div className="pt-3 border-t border-white/5">
                <p className="text-[10px] text-slate-600 uppercase tracking-wider font-semibold mb-2">Largest Price Drops</p>
                <div className="rounded-lg border border-white/5 overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/5">
                        {["Section","Was","Now","Drop"].map(h => (
                          <th key={h} className="text-left px-3 py-2 text-[9px] text-slate-600 uppercase tracking-wider font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {seller.largest_price_drops.slice(0, 5).map((d, i) => (
                        <tr key={i} className="border-b border-white/4 last:border-0">
                          <td className="px-3 py-2 text-slate-300 max-w-[120px] truncate">{d.section}</td>
                          <td className="px-3 py-2 text-slate-500 tabular-nums">{fmt$$(d.old_price)}</td>
                          <td className="px-3 py-2 text-slate-200 font-semibold tabular-nums">{fmt$$(d.new_price)}</td>
                          <td className="px-3 py-2 text-red-400 font-medium tabular-nums">{fmt$$(d.delta)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Sections tab ── */}
        {activeHistTab === "Sections" && (
          <div className="space-y-4">
            {sections?.sections && sections.sections.length > 0
              ? <SectionBreakdown sections={sections.sections} />
              : <div className="rounded-xl border border-white/7 bg-[#161b27] py-8 text-center text-xs text-slate-600">No section data available</div>
            }
            {listings && listings.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Lowest Available Tickets</p>
                <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-x-auto">
                  <table className="w-full text-xs min-w-[480px]">
                    <thead>
                      <tr className="border-b border-white/5">
                        {["#","Price","Section","Row","Qty","Marketplace","Move",""].map(h => (
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
                            <td className="px-3 py-2.5"><ListingMoveMenu listingId={l.id} /></td>
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
              </div>
            )}
          </div>
        )}

        {/* ── Marketplaces tab ── */}
        {activeHistTab === "Marketplaces" && (
          <div>
            {baseline?.per_marketplace && baseline.per_marketplace.length > 0 ? (
              <div className="rounded-xl border border-white/7 bg-[#161b27] overflow-hidden">
                <div className="grid border-b border-white/5 px-4 py-2 text-xs text-slate-500 uppercase tracking-wider"
                  style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr" }}>
                  {["Marketplace","Low","Inv","24h Δ","7d Δ","Signal"].map(h => <div key={h}>{h}</div>)}
                </div>
                {baseline.per_marketplace.map((mp) => {
                  const inv24 = mp.listings_change_24h?.absolute ?? null;
                  const inv7d = mp.listings_change_7d?.absolute ?? null;
                  const slug  = mp.marketplace_slug;
                  const mpInfo = MP_META[slug] ?? { label: slug, short: slug.slice(0,2).toUpperCase(), color: "#64748b" };
                  const direction = inv24 != null ? (inv24 < -5 ? "↓ Tight" : inv24 > 5 ? "↑ Grow" : "Stable") : "—";
                  const dirCls = inv24 != null ? (inv24 < -5 ? "text-emerald-400" : inv24 > 5 ? "text-red-400" : "text-slate-500") : "text-slate-600";
                  return (
                    <div key={slug} className="grid items-center px-4 py-2.5 border-b border-white/4 last:border-0 hover:bg-white/2"
                      style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr" }}>
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full" style={{ background: mpInfo.color }} />
                        <span className="text-xs font-bold uppercase" style={{ color: mpInfo.color }}>{mpInfo.short}</span>
                      </div>
                      <div className="text-xs font-bold text-white tabular-nums">{fmt$$(mp.current_lowest_ask)}</div>
                      <div className="text-xs text-slate-300 tabular-nums">{fmtNum(mp.current_listings)}</div>
                      <div className="text-xs">
                        {inv24 != null
                          ? <span className={inv24 < 0 ? "text-emerald-400" : "text-red-400"}>{inv24 > 0 ? "+" : ""}{inv24}</span>
                          : <span className="text-slate-600">—</span>}
                      </div>
                      <div className="text-xs">
                        {inv7d != null
                          ? <span className={inv7d < 0 ? "text-emerald-400" : "text-red-400"}>{inv7d > 0 ? "+" : ""}{inv7d}</span>
                          : <span className="text-slate-600">—</span>}
                      </div>
                      <div className={`text-xs font-semibold ${dirCls}`}>{direction}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-xl border border-white/7 bg-[#161b27] py-8 text-center text-xs text-slate-600">
                Marketplace comparison data not yet available
              </div>
            )}
          </div>
        )}
      </section>

      {/* ════════════════════════════════════════
          NFL AUDIO CONTROL
          ════════════════════════════════════════ */}
      {isNfl && nflAudio.mounted && (
        <NflAudioControl
          playing={nflAudio.playing}
          muted={nflAudio.muted}
          blocked={nflAudio.blocked}
          errorMsg={nflAudio.errorMsg}
          onPlay={nflAudio.play}
          onPause={nflAudio.pause}
          onStop={nflAudio.stop}
          onToggleMute={() => nflAudio.setMuted(!nflAudio.muted)}
        />
      )}

      {/* ════════════════════════════════════════
          DIAGNOSTICS (collapsed)
          ════════════════════════════════════════ */}
      <section className="border-t border-white/6 pt-4">
        <button onClick={() => setDiagOpen(v => !v)}
          className="flex items-center gap-2 text-xs text-slate-600 hover:text-slate-400 transition-colors py-1 w-full">
          {diagOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          <span className="uppercase tracking-widest font-semibold">Diagnostics</span>
          {!diagOpen && <span className="text-slate-700 normal-case tracking-normal font-normal ml-1">— internal data, market movement, pending intelligence</span>}
        </button>

        {diagOpen && (
          <div className="mt-4 space-y-5">
            {hero?.history_context && (
              <div>
                <h3 className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-2">Data Context</h3>
                <div className="rounded-xl border border-white/6 bg-[#161b27] p-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { label: "History Available", val: hero.history_context.hours_available != null ? `${Math.round(hero.history_context.hours_available)}h` : "—" },
                    { label: "Data Depth",        val: (hero.history_context as { data_depth?: string }).data_depth ?? "—" },
                    { label: "Since Tracking",    val: sincePct != null ? fmtPct(sincePct) : "—" },
                  ].map(({ label, val }) => (
                    <div key={label}>
                      <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-0.5">{label}</p>
                      <p className="text-sm font-semibold text-slate-400">{val}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h3 className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-2">Marketplace Status</h3>
              {eventMeta?.marketplace_freshness
                ? <div className="rounded-xl border border-white/6 bg-[#161b27] overflow-hidden">
                    {Object.entries(eventMeta.marketplace_freshness).map(([slug, f]: [string, unknown]) => {
                      const fr = f as { freshness_status?: string; age_minutes?: number };
                      const info = MP_META[slug] ?? { label: slug, short: slug.slice(0,2).toUpperCase(), color: "#64748b" };
                      const st = fr.freshness_status ?? "unknown";
                      const freshCls = st === "fresh" ? "text-emerald-400" : st === "late" ? "text-amber-400" : "text-slate-600";
                      return (
                        <div key={slug} className="flex items-center justify-between px-4 py-2.5 border-b border-white/4 last:border-0">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full" style={{ background: info.color }} />
                            <span className="text-xs text-slate-400">{info.label}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className={`text-xs font-semibold ${freshCls}`}>{st}</span>
                            <span className="text-xs text-slate-600">
                              {fr.age_minutes != null
                                ? fr.age_minutes < 60 ? `${fr.age_minutes}m ago` : `${Math.round(fr.age_minutes / 60)}h ago`
                                : "—"}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                : <p className="text-xs text-slate-700">No freshness data</p>
              }
            </div>
            <div>
              <h3 className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-2">Today&apos;s Movement</h3>
              <div className="rounded-xl border border-white/6 bg-[#161b27] divide-y divide-white/4">
                {[
                  { label: "Disappeared 24h",   sub: "Sold, pulled, or expired",  val: seller?.removed_listings_24h != null ? fmtNum(seller.removed_listings_24h) : null },
                  { label: "New Listings 24h",  sub: "Added (incl. relists)",      val: seller?.new_listings_24h != null ? `+${fmtNum(seller.new_listings_24h)}` : null },
                  { label: "Hourly Floor Δ",    sub: "Floor change per hour",      val: snapshot?.price?.floor_24h_change != null ? `${snapshot.price.floor_24h_change < 0 ? "-" : "+"}${fmt$$(Math.abs(snapshot.price.floor_24h_change / 24))}/hr` : null },
                  { label: "Hourly Median Δ",   sub: "Median change per hour",     val: snapshot?.price?.median_24h_change != null ? `${snapshot.price.median_24h_change < 0 ? "-" : "+"}${fmt$$(Math.abs(snapshot.price.median_24h_change / 24))}/hr` : null },
                ].map(({ label, sub, val }) => (
                  <div key={label} className="flex items-center justify-between px-4 py-2.5">
                    <div>
                      <p className="text-xs text-slate-400 font-medium">{label}</p>
                      <p className="text-[10px] text-slate-600">{sub}</p>
                    </div>
                    <span className="text-sm font-bold text-slate-300 tabular-nums">{val ?? "—"}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>

    </div>
  );
}
