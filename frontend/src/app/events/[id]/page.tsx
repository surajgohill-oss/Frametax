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
  BaselineResponse, EventSnapshotResponse, VelocityWindowsResponse,
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

function DeltaChip({ pct, abs, size = "sm", invert = false }: {
  pct?: number | null; abs?: number | null; size?: "sm" | "md"; invert?: boolean;
}) {
  const val = pct ?? null;
  if (val == null && abs == null) return <span className="text-slate-600 text-[11px]">—</span>;
  const n = val ?? abs ?? 0;
  const Icon = n > 0 ? TrendingUp : n < 0 ? TrendingDown : Minus;
  const textSize = size === "md" ? "text-sm" : "text-[11px]";
  const label = val != null ? fmtPct(val) : (n > 0 ? `+${n}` : `${n}`);
  // invert=true for price rows: lower price = green (good), higher price = red (bad)
  const isGood = invert ? n < 0 : n > 0;
  const isBad  = invert ? n > 0 : n < 0;
  return (
    <span className={cn(
      "inline-flex items-center gap-0.5 font-bold tabular-nums px-1.5 py-0.5 rounded",
      textSize,
      isGood ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
      : isBad ? "text-red-400 bg-red-500/10 border border-red-500/20"
      : "text-slate-500 bg-white/5 border border-white/10"
    )}>
      <Icon size={size === "md" ? 12 : 9} />
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

/** Safely normalise any marketplace name/slug value to a lowercase, no-space string for matching. */
function normMp(v: unknown): string {
  if (v == null) return "";
  if (typeof v === "string") return v.toLowerCase().replace(/\s+/g, "");
  if (typeof v === "object") {
    const o = v as Record<string, unknown>;
    const s = o.name ?? o.marketplace ?? o.slug ?? "";
    return typeof s === "string" ? s.toLowerCase().replace(/\s+/g, "") : "";
  }
  return "";
}

const MP_META: Record<string, { label: string; short: string; color: string; logoBg: string }> = {
  stubhub:    { label: "StubHub",     short: "SH", color: "#e8704a", logoBg: "#e8704a" },
  tickpick:   { label: "TickPick",    short: "TP", color: "#2dd4bf", logoBg: "#0d9488" },
  gametime:   { label: "Gametime",    short: "GT", color: "#4ade80", logoBg: "#16a34a" },
  vividseats: { label: "Vivid Seats", short: "VS", color: "#a78bfa", logoBg: "#7c3aed" },
};

/** Compact branded logo badge for a marketplace */
function MpLogo({ slug, info, size = 22 }: { slug: string; info: { label: string; short: string; color: string; logoBg: string }; size?: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="rounded flex items-center justify-center font-black text-white flex-shrink-0"
        style={{ width: size, height: size, background: info.logoBg, fontSize: Math.round(size * 0.42) }}>
        {info.short}
      </div>
      <span className="text-[13px] font-bold tracking-tight" style={{ color: info.color }}>{info.label}</span>
    </div>
  );
}

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
            <span className="text-[11px] text-slate-500 mr-0.5">Sort:</span>
            {SECTION_SORTS.map(({ key, label }) => (
              <button key={key} onClick={() => setSort(key)}
                className={cn("text-[11px] px-2 py-0.5 rounded border transition-colors",
                  sort === key ? "border-white/20 bg-white/8 text-slate-200" : "border-white/[0.07] text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                {label}
              </button>
            ))}
          </div>
          {/* Filter pills */}
          <div className="flex items-center gap-1 flex-wrap justify-end">
            <span className="text-[11px] text-slate-500 mr-0.5">Filter:</span>
            <button onClick={() => setFilter("all")}
              className={cn("text-[11px] px-2 py-0.5 rounded border transition-colors",
                filter === "all" ? "border-white/20 bg-white/8 text-slate-200" : "border-white/[0.07] text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
              All
            </button>
            {SECTION_FILTERS.map(({ key, label }) => (
              <button key={key} onClick={() => setFilter(key)}
                className={cn("text-[11px] px-2 py-0.5 rounded border transition-colors",
                  filter === key ? "border-blue-500/40 bg-blue-500/10 text-blue-400" : "border-white/[0.07] text-slate-500 hover:text-slate-300 hover:bg-white/5")}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="rounded-xl border border-white/[0.07] bg-[#161b27] py-6 text-center text-xs text-slate-600">
          No sections match this filter
        </div>
      ) : (
        <div className="rounded-xl border border-white/[0.07] bg-[#161b27] overflow-x-auto">
          <table className="w-full text-xs min-w-[400px]">
            <thead>
              <tr className="border-b border-white/5">
                {["Section", "Listings", "Low", "Median"].map((h) => (
                  <th key={h} className="text-left px-4 py-2 text-[11px] text-slate-500 uppercase tracking-[0.12em] font-medium">{h}</th>
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
          className="mt-1.5 w-full flex items-center justify-center gap-1 text-[11px] text-slate-500 hover:text-slate-400 py-1 transition-colors">
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
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-white/[0.07]">
        <div>
          <p className="text-xs font-semibold text-slate-200">Follow {artist}</p>
          <p className="text-[11px] text-amber-400/70 mt-0.5">Local only — no backend notifications</p>
        </div>
        <button onClick={onClose} className="p-0.5 text-slate-500 hover:text-slate-300"><X size={12} /></button>
      </div>

      <div className="p-3 space-y-3">
        {/* Type toggle */}
        <div className="flex rounded-lg border border-white/[0.07] overflow-hidden text-[11px]">
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
          <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1.5">
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
        className="text-xs text-slate-500 hover:text-slate-200 transition-colors px-2 py-1 rounded-md border border-white/[0.07] hover:border-white/20 font-medium">
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
          <p className="text-[11px] text-slate-600 px-3 py-1.5 border-t border-white/5">Record preserved</p>
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
    <div className="rounded-xl border border-white/[0.07] bg-[#0a0d14] p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em]">{venueName} — Intelligence</h3>
      </div>
      {/* Section-specific fields — populated when section data arrives */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
        {[
          { label: "Section",              value: summary?.name ?? null },
          { label: "Current Inventory",    value: null },
          { label: "Current Low",          value: null },
          { label: "Current Median",       value: null },
          { label: "Price Movement",       value: null },
          { label: "Inventory Movement",   value: null },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white/[0.025] rounded-lg px-3 py-2.5 border border-white/[0.05]">
            <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">{label}</p>
            <p className={value ? "text-[13px] text-slate-200 font-medium" : "text-[13px] text-slate-600 tabular-nums"}>
              {value ?? "—"}
            </p>
          </div>
        ))}
      </div>
      <div className="border-t border-white/[0.05] pt-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {[
            { label: "Marketplace Share" },
            { label: "Section Activity" },
            { label: "Demand / Supply / Trend" },
          ].map(({ label }) => (
            <div key={label} className="bg-white/[0.02] rounded-lg px-3 py-2.5 border border-white/[0.05]">
              <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-1">{label}</p>
              <p className="text-[13px] text-slate-700">—</p>
            </div>
          ))}
        </div>
      </div>
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
        <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em]">Spotify</h2>
        {playlistId && (
          <div className="flex rounded-lg border border-white/[0.07] overflow-hidden text-xs">
            {(["artist", "playlist"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-2.5 py-1 capitalize transition-colors ${tab === t ? "bg-white/10 text-slate-200" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"}`}>
                {t}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="rounded-xl overflow-hidden border border-white/[0.07]">
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
          <p className="text-[11px] text-slate-500 mb-3">
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
            <div className={`mt-2 text-[11px] flex items-center gap-1.5 ${result.accepted ? "text-emerald-400" : "text-red-400"}`}>
              {result.accepted ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
              {result.accepted ? `${result.mp} URL registered — pending backend ingestion` : result.mp}
            </div>
          )}
          <div className="mt-2 pt-2 border-t border-white/6">
            <a href="/url-intake" className="text-[11px] text-slate-500 hover:text-slate-400 transition-colors">
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
  const [customArtworkUrl, setCustomArtworkUrl] = useState<string | null>(null);
  const [artworkUploading, setArtworkUploading] = useState(false);
  const [hero, setHero]           = useState<HeroResponse | null>(null);
  const [market, setMarket]       = useState<MarketResponse | null>(null);
  const [history, setHistory]     = useState<HistoryResponse | null>(null);
  const [sections, setSections]   = useState<SectionsResponse | null>(null);
  const [seller, setSeller]       = useState<SellerResponse | null>(null);
  const [listings, setListings]   = useState<Listing[] | null>(null);
  const [baseline, setBaseline]   = useState<BaselineResponse | null>(null);
  const [historyAll, setHistoryAll] = useState<HistoryResponse | null>(null);
  const [snapshot, setSnapshot]   = useState<EventSnapshotResponse | null>(null);
  const [lifecycle, setLifecycle] = useState<{ summary: Record<string, unknown> } | null>(null);
  const [mpBaselines, setMpBaselines] = useState<import("@/lib/types").MarketplaceBaselinesResponse | null>(null);
  const [velocityWindows, setVelocityWindows] = useState<VelocityWindowsResponse | null>(null);
  const [alerts, setAlerts]       = useState<import("@/lib/types").AlertResponse | null>(null);
  const [marketWindow, setMarketWindow]   = useState<"tracking" | "7d" | "24h" | "12h" | "6h">("tracking");
  const [sellerWindow, setSellerWindow]   = useState<"tracking" | "7d" | "24h" | "12h" | "6h">("tracking");
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

  // Sync customArtworkUrl from loaded eventMeta (initial load)
  useEffect(() => {
    if (eventMeta?.custom_artwork_url !== undefined) {
      setCustomArtworkUrl(eventMeta.custom_artwork_url ?? null);
    }
  }, [eventMeta?.custom_artwork_url]);

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
      api.events.history(id, "all").then(setHistoryAll).catch(() => {}),
      api.events.snapshot(id).then(setSnapshot).catch(() => {}),
      api.events.alerts(id).then(setAlerts).catch(() => {}),
      api.events.lifecycle(id).then(setLifecycle).catch(() => {}),
      api.analytics.marketplaceBaselines(id).then(setMpBaselines).catch(() => {}),
      api.analytics.velocityWindows(id).then(setVelocityWindows).catch(() => {}),
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
  const gradient        = getEventGradient(artist, title);
  const autoArtworkUrl  = useArtistImage(artist, title);
  const artworkUrl      = customArtworkUrl ?? autoArtworkUrl;
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
  // Inventory % change for hero display
  const invCurrent24 = hero?.inventory?.total_listings ?? null;
  const invPrev24    = (invCurrent24 != null && invDelta24 != null) ? invCurrent24 - invDelta24 : null;
  const invPct24h    = (invPrev24 != null && invPrev24 !== 0 && invDelta24 != null) ? (invDelta24 / invPrev24) * 100 : null;
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

  // ── First-tracked snapshot (per-marketplace rollup — project rule: each MP has its own baseline) ─
  const firstTrackedMed  = historyAll?.series?.[0]?.median_ask ?? null;
  const curInvNow        = baseline?.current?.raw_listings ?? hero?.inventory?.total_listings ?? null;
  // Per-marketplace rolled-up inv delta (correct per project rules):
  //   each marketplace's delta = cur - its own first snapshot; then sum across marketplaces
  const invSinceTracking    = mpBaselines?.inv_since_tracking ?? null;
  const firstTrackedInv     = mpBaselines?.event_baseline_total_listings ?? null;
  const invSinceTrackingPct = (firstTrackedInv != null && firstTrackedInv > 0 && invSinceTracking != null)
    ? (invSinceTracking / firstTrackedInv) * 100 : null;
  const medSinceTracking = (firstTrackedMed != null && hero?.price?.median_ask != null)
    ? hero.price.median_ask - firstTrackedMed : null;
  const medSinceTrackingPct = (firstTrackedMed != null && firstTrackedMed > 0 && medSinceTracking != null)
    ? (medSinceTracking / firstTrackedMed) * 100 : null;
  // Removed/added since tracking horizon (24h window is authoritative from market endpoint)
  const removed24h = market?.inventory_movement?.removed_24h ?? null;
  const added24h   = market?.inventory_movement?.new_24h ?? null;
  // Implied sale price from lifecycle (avg last-seen price of disappeared listings)
  const avgImpliedSalePrice = (lifecycle?.summary?.avg_implied_sale_price as number | null) ?? null;
  // gross lifecycle sale events = assumed_sold + sold_after_relist (includes broker repricing churn)
  const impliedSaleCount    = (lifecycle?.summary?.implied_sale_count as number | null) ?? null;
  // assumed_sold = no relist found (most conservative sale estimate)
  const assumedSales        = (lifecycle?.summary?.assumed_sales as number | null) ?? null;
  // net absorbed = first_tracked - current (actual inventory change, churn-neutral)
  const netAbsorbedListings = mpBaselines?.inv_since_tracking ?? null;

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
    const cap      = hero?.market?.capitulation_score ?? null;
    const aggr     = hero?.market?.seller_aggression  ?? null;
    const repriced = seller?.repriced_24h ?? 0;
    const drops    = seller?.price_drops_24h ?? 0;
    const dropRatio = repriced > 0 ? drops / repriced : 0;
    if (cap == null) return "—";
    if (cap > 0.70) return "Seller capitulation increasing";
    if (cap > 0.55 || (aggr != null && aggr > 0.65)) return "Repricing accelerating";
    if (cap > 0.40 || dropRatio > 0.55) return "Aggressive repricing";
    if (cap > 0.25 && dropRatio < 0.3) return "Price cuts slowing";
    if (cap <= 0.20) return "Holding firm";
    return "Stable seller behavior";
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

      {/* Art-derived ambient glow — subtle radial from artwork color, bleeds into page bg */}
      <div aria-hidden="true" className="fixed inset-0 pointer-events-none" style={{
        zIndex: -1,
        background: `radial-gradient(ellipse 75% 55% at 18% 0%, ${gradient[0]}1c 0%, transparent 60%), radial-gradient(ellipse 45% 45% at 82% 80%, ${gradient[1]}0e 0%, transparent 55%)`,
      }} />

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
          SECTION 1 — EVENT HERO
          Cinematic: artwork bleeds full height, large typography, live market on right
          ════════════════════════════════════════ */}
      <section className="rounded-xl overflow-hidden relative"
        style={{ boxShadow: `0 0 140px ${gradient[0]}20, 0 0 0 1px rgba(255,255,255,0.06)` }}>

        {/* Full-bleed artwork background */}
        <div className="absolute inset-0"
          style={{
            backgroundImage: artworkUrl
              ? `url(${artworkUrl})`
              : `linear-gradient(145deg, ${gradient[0]}ee, ${gradient[1]}cc)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center top',
            backgroundRepeat: 'no-repeat',
          }} />

        {/* Cinematic overlay layers */}
        <div className="absolute inset-0" style={{ background: 'rgba(5,6,11,0.52)' }} />
        <div className="absolute inset-0"
          style={{ background: 'linear-gradient(to top, rgba(5,6,11,1) 0%, rgba(5,6,11,0.88) 30%, rgba(5,6,11,0.35) 60%, rgba(5,6,11,0.08) 100%)' }} />
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: `linear-gradient(95deg, ${gradient[0]}20 0%, transparent 50%)` }} />
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'linear-gradient(to left, rgba(5,6,11,0.65) 0%, transparent 45%)' }} />

        {/* Content */}
        <div className="relative flex flex-col justify-end" style={{ minHeight: 380 }}>

          {/* Artwork upload control */}
          <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
            <label className="opacity-0 hover:opacity-100 transition-opacity cursor-pointer" title={artworkUrl ? "Replace artwork" : "Upload artwork"}>
              <input type="file" accept="image/jpeg,image/png,image/webp,image/gif"
                className="sr-only" disabled={artworkUploading}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file || !id) return;
                  setArtworkUploading(true);
                  try {
                    const res = await api.events.setArtwork(id, file);
                    setCustomArtworkUrl(res.custom_artwork_url ?? null);
                  } finally { setArtworkUploading(false); e.target.value = ""; }
                }}
              />
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-black/70 text-white/70 backdrop-blur-sm leading-none select-none">
                {artworkUploading ? "…" : artworkUrl ? "Replace Art" : "Upload Art"}
              </span>
            </label>
            {customArtworkUrl && (
              <button
                className="w-6 h-6 flex items-center justify-center rounded-full bg-black/60 text-white/50 hover:text-white/90 transition-colors text-[11px] font-bold opacity-0 hover:opacity-100"
                title="Revert to auto artwork"
                onClick={async () => {
                  if (!id) return;
                  setArtworkUploading(true);
                  try { await api.events.setArtwork(id, ""); setCustomArtworkUrl(null); }
                  finally { setArtworkUploading(false); }
                }}
              >✕</button>
            )}
          </div>

          {/* Main content: identity + market */}
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-6 items-end px-8 pb-7 pt-16">

            {/* LEFT: Identity */}
            <div className="flex flex-col gap-3">
              {artist && artist !== title && (
                <p className="text-[12px] font-bold text-white/40 uppercase tracking-[0.28em]">{artist}</p>
              )}
              <h1 className="text-[52px] sm:text-[68px] font-black text-white leading-none tracking-tight line-clamp-2"
                style={{ textShadow: '0 2px 40px rgba(0,0,0,0.9)' }}>
                {title}
              </h1>
              <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
                {venue && (
                  <span className="flex items-center gap-1.5 text-[14px] text-white/55">
                    <MapPin size={12} className="opacity-60 flex-shrink-0" />{venue}
                  </span>
                )}
                {dateLabel && (
                  <span className="flex items-center gap-1.5 text-[14px] text-white/80 font-medium">
                    <Calendar size={12} className="opacity-60 flex-shrink-0" />{dateLabel}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {daysOut != null && (
                  <span className="text-[12px] font-bold px-3 py-1 rounded-lg backdrop-blur-sm"
                    style={{ color: aColors.text, background: aColors.bg + "55", border: `1px solid ${aColors.border}55` }}>
                    {isCompleted ? "Event passed" : daysOut < 1 ? "Today" : daysOut < 2 ? "Tomorrow" : `${Math.round(daysOut)}d away`}
                  </span>
                )}
                {isCompleted && (
                  <span className="text-[12px] font-bold uppercase tracking-widest text-white/35 bg-white/[0.07] border border-white/10 rounded-lg px-3 py-1">Completed</span>
                )}
                <span className="text-[12px] font-black px-3 py-1 rounded-lg border backdrop-blur-sm"
                  style={{ color: aColors.text, borderColor: aColors.border + "60", background: aColors.bg + "45" }}>
                  {action}
                </span>
              </div>
            </div>

            {/* RIGHT: Live Market — Median primary per hierarchy spec */}
            <div className="hidden sm:flex flex-col items-end gap-0.5">
              <p className="text-[11px] text-white/30 uppercase tracking-[0.22em] font-semibold mb-1">Median</p>
              <p className="text-[66px] font-black text-white/90 tabular-nums leading-none"
                style={{ textShadow: `0 0 60px ${gradient[0]}50` }}>
                {hero?.price?.median_ask != null ? fmt$$(hero.price.median_ask) : "—"}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {pct24h != null && <DeltaChip pct={pct24h} invert />}
                <span className="text-[11px] text-white/30">24H</span>
              </div>
              <div className="flex items-center gap-5 mt-4 pt-4 border-t border-white/[0.1] w-full justify-end">
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-1">Inventory</p>
                  <p className="text-[24px] font-bold text-blue-300/80 tabular-nums leading-none">
                    {hero?.inventory?.total_listings != null ? fmtNum(hero.inventory.total_listings) : "—"}
                  </p>
                  {invDelta24 != null && (
                    <p className={`text-[11px] tabular-nums mt-0.5 ${invDelta24 > 0 ? "text-red-400" : invDelta24 < 0 ? "text-emerald-400" : "text-slate-500"}`}>
                      {invDelta24 > 0 ? "+" : ""}{fmtNum(invDelta24)}
                      {invPct24h != null ? ` (${invPct24h > 0 ? "+" : ""}${invPct24h.toFixed(1)}%)` : ""}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-1">Duplicate %</p>
                  <p className="text-[24px] font-bold text-violet-300/70 tabular-nums leading-none">
                    {snapshot?.duplicates?.dup_pct != null ? `${snapshot.duplicates.dup_pct.toFixed(1)}%` : "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-1">Low</p>
                  <p className="text-[24px] font-bold text-emerald-300 tabular-nums leading-none">
                    {hero?.price?.low_ask != null ? fmt$$(hero.price.low_ask) : "—"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-white/28 uppercase tracking-wide mb-1">High</p>
                  <p className="text-[24px] font-bold text-white/40 tabular-nums leading-none">
                    {(hero?.price?.high_ask ?? hero?.price?.p75_ask) != null ? fmt$$(hero?.price?.high_ask ?? hero?.price?.p75_ask!) : "—"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Status bar */}
          {(() => {
            const evFreshEntries = (['stubhub', 'tickpick', 'gametime', 'vividseats'] as const)
              .filter(slug => eventMeta?.marketplace_freshness?.[slug]);
            const evFreshCount = evFreshEntries.filter(slug => {
              const s = (eventMeta?.marketplace_freshness?.[slug] as { freshness_status?: string })?.freshness_status;
              return s === "fresh" || s === "late";
            }).length;
            return (
          <div className="border-t border-white/[0.07] px-8 py-3 flex items-center gap-4 flex-wrap bg-black/30 backdrop-blur-sm">
            {trackingSince && (
              <span className="text-[11px] text-white/28 flex items-center gap-1.5">
                <Clock size={10} />
                <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Tracking Since</span>
                <span className="text-white/40">{trackingSince.formatted}</span>
              </span>
            )}
            {freshLabel && (
              <span className="text-[11px] text-white/28 flex items-center gap-1.5">
                <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Last Update</span>
                <span className="text-white/40">{freshLabel}</span>
              </span>
            )}
            {evFreshEntries.length > 0 && (
              <span className="text-[11px] text-white/28 flex items-center gap-1.5">
                <span className="text-white/20 uppercase tracking-[0.1em] text-[10px]">Feeds Fresh</span>
                <span className="text-white/40">{evFreshCount}/{evFreshEntries.length}</span>
              </span>
            )}
            <div className="flex items-center gap-5 ml-auto flex-wrap">
              {eventMeta?.marketplace_freshness
                ? (['stubhub', 'tickpick', 'gametime', 'vividseats'] as const)
                    .filter(slug => eventMeta.marketplace_freshness![slug])
                    .map(slug => {
                      const f = eventMeta.marketplace_freshness![slug] as { freshness_status?: string; age_minutes?: number };
                      const status = f?.freshness_status ?? "no_data";
                      const age = f?.age_minutes;
                      const ageStr = age == null ? null : age < 60 ? `${age}m` : `${Math.round(age / 60)}h`;
                      const dotCls = status === "fresh" ? "bg-emerald-400" : status === "late" ? "bg-amber-400" : status === "dead" ? "bg-red-500" : "bg-white/20";
                      const textCls = status === "fresh" ? "text-emerald-400" : status === "late" ? "text-amber-400" : status === "dead" ? "text-red-400" : "text-white/25";
                      const info = MP_META[slug];
                      return (
                        <div key={slug} className="flex items-center gap-1.5">
                          {info && (
                            <div className="rounded flex items-center justify-center font-black text-white flex-shrink-0"
                              style={{ width: 16, height: 16, background: info.logoBg, fontSize: 7 }}>
                              {info.short}
                            </div>
                          )}
                          <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotCls}`} />
                          <span className="text-[11px] font-medium" style={{ color: info?.color ?? "rgba(255,255,255,0.38)" }}>{info?.label ?? slug}</span>
                          <span className={`text-[11px] tabular-nums ${textCls}`}>{ageStr ?? "—"}</span>
                        </div>
                      );
                    })
                : <p className="text-[11px] text-white/25">No feeds</p>
              }
            </div>
          </div>
            );
          })()}
        </div>
      </section>


      {/* ════════════════════════════════════════
          SECTION 2 — MARKET INTELLIGENCE HERO (~200px)
          Three columns: Current Market | Market Absorption | Seller Behavior
          ════════════════════════════════════════ */}
      <section className="rounded-xl border border-white/[0.07] bg-[#0d1018] overflow-hidden">
        <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/8"
          style={{ gridTemplateColumns: "1.4fr 1.2fr 0.9fr" }}>

          {/* Col 1: Current Market — Median primary, with timeframe toggle */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold">Current Market</p>
              {/* Timeframe toggle */}
              <div className="flex items-center gap-0.5">
                {(["tracking", "24h", "12h", "6h", "7d"] as const).map(w => (
                  <button key={w} onClick={() => setMarketWindow(w)}
                    className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors uppercase",
                      marketWindow === w
                        ? "bg-white/10 text-slate-200 border border-white/15"
                        : "text-slate-600 hover:text-slate-400")}>
                    {w === "tracking" ? "Tracking" : w}
                  </button>
                ))}
              </div>
            </div>

            {/* Movement rows: MEDIAN / LOW / HIGH / INVENTORY / DUPLICATES */}
            {(marketWindow === "12h" || marketWindow === "6h") ? (
              <p className="text-[12px] text-slate-600 italic py-2">Insufficient history for {marketWindow.toUpperCase()} window</p>
            ) : (
              <div className="space-y-0">
                {/* MEDIAN row — first per spec */}
                {(() => {
                  const cur = hero?.price?.median_ask ?? null;
                  // fallback chain: d30 → d14 → h24 so TRACKING mode always shows something
                  const pct = marketWindow === "24h" ? (hero?.changes?.h24?.price_delta_pct ?? null)
                    : marketWindow === "7d" ? (hero?.changes?.d7?.price_delta_pct ?? null)
                    : marketWindow === "tracking"
                      ? (medSinceTrackingPct ?? hero?.changes?.d30?.price_delta_pct ?? hero?.changes?.d14?.price_delta_pct ?? hero?.changes?.h24?.price_delta_pct ?? null)
                    : null;
                  const orig = marketWindow === "tracking" && firstTrackedMed != null
                    ? firstTrackedMed
                    : (cur != null && pct != null) ? Math.round(cur / (1 + pct / 100)) : null;
                  const abs  = (cur != null && orig != null) ? cur - orig : null;
                  return (
                    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                      <span className="text-[12px] text-slate-400 font-semibold w-16 flex-shrink-0">Median</span>
                      <div className="flex items-center gap-1.5 tabular-nums">
                        {orig != null ? <span className="text-[11px] text-slate-600">{fmt$$(orig)} →</span> : null}
                        <span className="text-[13px] font-bold text-white">{cur != null ? fmt$$(cur) : "—"}</span>
                        {abs != null && abs !== 0 && <span className={cn("text-[11px]", abs < 0 ? "text-slate-500" : "text-slate-500")}>{abs > 0 ? `+${fmt$$(abs)}` : fmt$$(abs)}</span>}
                        {pct != null ? <DeltaChip pct={pct} invert /> : <span className="text-[11px] text-slate-700">—</span>}
                      </div>
                    </div>
                  );
                })()}
                {/* LOW row */}
                {(() => {
                  const cur = hero?.price?.low_ask ?? null;
                  // tracking: no floor-tracking-start delta available — show current only
                  const absRaw = marketWindow === "24h"
                    ? (snapshot?.price?.floor_24h_change ?? baseline?.deltas_24h?.low_ask?.absolute ?? null)
                    : marketWindow === "7d" ? (baseline?.deltas_7d?.low_ask?.absolute ?? null)
                    : null;
                  const pct = absRaw != null && cur != null && (cur - absRaw) !== 0
                    ? (absRaw / (cur - absRaw)) * 100 : null;
                  const orig = (cur != null && pct != null) ? Math.round(cur / (1 + pct / 100)) : null;
                  return (
                    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                      <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Low</span>
                      <div className="flex items-center gap-1.5 tabular-nums">
                        {orig != null ? <span className="text-[11px] text-slate-600">{fmt$$(orig)} →</span> : null}
                        <span className="text-[13px] font-semibold text-emerald-300">{cur != null ? fmt$$(cur) : "—"}</span>
                        {absRaw != null && absRaw !== 0 && <span className="text-[11px] text-slate-500">{absRaw > 0 ? `+${fmt$$(absRaw)}` : fmt$$(absRaw)}</span>}
                        {pct != null ? <DeltaChip pct={pct} invert /> : <span className="text-[11px] text-slate-700">—</span>}
                      </div>
                    </div>
                  );
                })()}
                {/* HIGH row — with tracking-start delta from snapshot */}
                {(() => {
                  const cur = snapshot?.price?.high_now ?? hero?.price?.high_ask ?? hero?.price?.p75_ask ?? null;
                  const delta = marketWindow === "24h"
                    ? snapshot?.price?.high_24h_change
                    : marketWindow === "7d"
                    ? snapshot?.price?.high_7d_change
                    : marketWindow === "tracking"
                    ? snapshot?.price?.high_start_change
                    : null;
                  const pct = marketWindow === "tracking" ? snapshot?.price?.high_start_change_pct : null;
                  return (
                    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                      <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">High</span>
                      <div className="flex items-center gap-1.5 tabular-nums">
                        <span className="text-[13px] font-semibold text-slate-400">{cur != null ? fmt$$(cur) : "—"}</span>
                        {delta != null ? (
                          <span className={`text-[11px] font-semibold ${delta < 0 ? "text-emerald-400" : "text-red-400"}`}>
                            {delta > 0 ? "+" : ""}{fmt$$(delta)}{pct != null ? ` (${pct > 0 ? "+" : ""}${pct.toFixed(1)}%)` : ""}
                          </span>
                        ) : <span className="text-[11px] text-slate-700">—</span>}
                      </div>
                    </div>
                  );
                })()}
                {/* INVENTORY row — TRACKING = from first-snapshot baseline (canonical rule) */}
                {(() => {
                  const cur = curInvNow;
                  const abs = marketWindow === "24h"
                    ? (baseline?.deltas_24h?.raw_listings?.absolute ?? hero?.changes?.h24?.inventory_delta ?? null)
                    : marketWindow === "7d"
                    ? (baseline?.deltas_7d?.raw_listings?.absolute ?? hero?.changes?.d7?.inventory_delta ?? null)
                    : marketWindow === "tracking"
                    ? invSinceTracking
                    : null;
                  const absPct = marketWindow === "tracking"
                    ? invSinceTrackingPct
                    : (abs != null && cur != null && (cur - abs) > 0
                      ? (abs / (cur - abs)) * 100 : null);
                  const fromVal = marketWindow === "tracking" && firstTrackedInv != null ? firstTrackedInv : null;
                  return (
                    <div className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                      <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Inventory</span>
                      <div className="flex items-center gap-2 tabular-nums">
                        {fromVal != null && <span className="text-[11px] text-slate-600">{fmtNum(fromVal)} →</span>}
                        <span className="text-[13px] font-semibold text-blue-300/80">{cur != null ? fmtNum(cur) : "—"}</span>
                        {abs != null ? (
                          <span className={cn("text-[11px] font-medium", abs > 0 ? "text-red-400" : abs < 0 ? "text-emerald-400" : "text-slate-500")}>
                            {abs > 0 ? "+" : ""}{fmtNum(abs)}
                            {absPct != null ? ` (${absPct > 0 ? "+" : ""}${absPct.toFixed(1)}%)` : ""}
                          </span>
                        ) : <span className="text-[11px] text-slate-700">—</span>}
                      </div>
                    </div>
                  );
                })()}
                {/* DUPLICATES row — format: current%  ±pp change */}
                <div className="flex items-center justify-between py-1.5">
                  <span className="text-[12px] text-slate-500 w-16 flex-shrink-0">Dup %</span>
                  {snapshot?.duplicates?.dup_pct != null ? (
                    <span className="text-[11px] text-slate-400 tabular-nums">
                      {snapshot.duplicates.dup_pct.toFixed(1)}%
                      {snapshot.duplicates.dup_mirror_pct != null && (
                        <span className="text-slate-600 ml-1">({snapshot.duplicates.dup_mirror_pct.toFixed(1)}% mirror)</span>
                      )}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-700">—</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Col 2: Absorption */}
          <div className="p-4 bg-white/[0.012]">
            <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold mb-3">
              Absorption
            </p>

            {/* Est. Avg Sale Price — from implied sales (listing disappearance) */}
            <div className="mb-3 pb-3 border-b border-white/[0.06]">
              <div className="flex items-center justify-between mb-1">
                <p className="text-[11px] text-slate-500 uppercase tracking-[0.14em]">Est. Avg Sale Price</p>
                {avgImpliedSalePrice != null ? (
                  <span className="text-[15px] font-bold tabular-nums text-emerald-300">{fmt$$(avgImpliedSalePrice)}</span>
                ) : (
                  <span className="text-[12px] text-slate-700">—</span>
                )}
              </div>
              {avgImpliedSalePrice != null && impliedSaleCount != null && (
                <p className="text-[10px] text-slate-600">
                  avg last-seen price · {fmtNum(impliedSaleCount)} lifecycle events{netAbsorbedListings != null ? ` · ${Math.abs(netAbsorbedListings)} net absorbed` : ""}
                </p>
              )}
            </div>

            {/* Inventory Since Tracking — first-snapshot baseline */}
            {(() => {
              const hasData = firstTrackedInv != null && curInvNow != null;
              const maxObs = historyAll?.series?.reduce((m, p) => Math.max(m, p.listings ?? 0), 0) ?? 0;
              const pctBar = hasData && maxObs > 0
                ? Math.min(100, (curInvNow! / maxObs) * 100) : null;
              return (
                <div className="mb-2.5 pb-2.5 border-b border-white/[0.04]">
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em]">Inv Since Tracking</p>
                    {invSinceTracking != null && (
                      <span className={cn("text-[12px] font-bold tabular-nums",
                        invSinceTracking > 0 ? "text-red-400" : invSinceTracking < 0 ? "text-emerald-400" : "text-slate-500")}>
                        {invSinceTracking > 0 ? "+" : ""}{fmtNum(invSinceTracking)}
                        {invSinceTrackingPct != null ? ` (${invSinceTrackingPct > 0 ? "+" : ""}${invSinceTrackingPct.toFixed(1)}%)` : ""}
                      </span>
                    )}
                  </div>
                  {hasData && pctBar != null ? (
                    <>
                      <div className="h-1 w-full rounded-full bg-white/[0.06] overflow-hidden mb-1">
                        <div className="h-full rounded-full bg-blue-400/50 transition-all" style={{ width: `${pctBar.toFixed(1)}%` }} />
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[10px] text-slate-600">{fmtNum(firstTrackedInv!)} start</span>
                        {maxObs > 0 && <span className="text-[10px] text-slate-700">{fmtNum(maxObs)} peak</span>}
                        <span className="text-[10px] text-blue-400/70">{fmtNum(curInvNow!)} now</span>
                      </div>
                    </>
                  ) : (
                    <p className="text-[11px] text-slate-600 italic">Insufficient history</p>
                  )}
                </div>
              );
            })()}

            {/* Movement rows — real data from market + velocity-windows endpoints */}
            {[
              { label: "Sold 24H",      val: velocityWindows?.windows?.["24h"]?.implied_sale_listings != null ? fmtNum(velocityWindows.windows["24h"].implied_sale_listings) : null,
                cls: (() => { const v = velocityWindows?.windows?.["24h"]?.implied_sale_listings ?? null; return v != null && v > 0 ? "text-emerald-400" : "text-slate-700"; })() },
              { label: "Sold 7D",       val: velocityWindows?.windows?.["7d"]?.implied_sale_listings != null ? fmtNum(velocityWindows.windows["7d"].implied_sale_listings) : null,
                cls: (() => { const v = velocityWindows?.windows?.["7d"]?.implied_sale_listings ?? null; return v != null && v > 0 ? "text-emerald-400" : "text-slate-700"; })() },
              { label: "Tickets Sold",  val: velocityWindows?.windows?.since_tracking?.implied_sale_tickets != null ? fmtNum(velocityWindows.windows.since_tracking.implied_sale_tickets) : null,
                cls: (() => { const v = velocityWindows?.windows?.since_tracking?.implied_sale_tickets ?? null; return v != null && v > 0 ? "text-emerald-400" : "text-slate-700"; })() },
              { label: "Removed 24H",   val: removed24h != null ? fmtNum(removed24h) : null,  cls: removed24h != null && removed24h > 0 ? "text-red-400" : "text-slate-700" },
              { label: "Added 24H",     val: added24h   != null ? fmtNum(added24h)   : null,  cls: added24h   != null && added24h > 0   ? "text-emerald-400" : "text-slate-700" },
              { label: "Market Stress", val: market?.market_stress?.composite_score != null
                  ? `${(market.market_stress.composite_score * 100).toFixed(0)}%` : null,
                cls: (() => {
                  const s = market?.market_stress?.composite_score ?? null;
                  return s == null ? "text-slate-700" : s > 0.6 ? "text-red-400" : s > 0.35 ? "text-amber-400" : "text-emerald-400";
                })() },
            ].map(({ label, val, cls }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0">
                <span className="text-[12px] text-slate-500">{label}</span>
                <span className={cn("tabular-nums font-semibold text-[13px]", cls)}>{val ?? "—"}</span>
              </div>
            ))}
          </div>

          {/* Col 3: Seller Behavior — Relist Price Change primary */}
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[11px] text-slate-400 uppercase tracking-[0.18em] font-semibold">Seller Behavior</p>
              <div className="flex items-center gap-0.5">
                {(["tracking", "24h", "12h", "6h", "7d"] as const).map(w => (
                  <button key={w} onClick={() => setSellerWindow(w)}
                    className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded transition-colors uppercase",
                      sellerWindow === w
                        ? "bg-white/10 text-slate-200 border border-white/15"
                        : "text-slate-600 hover:text-slate-400")}>
                    {w === "tracking" ? "Tracking" : w}
                  </button>
                ))}
              </div>
            </div>

            {/* Relist Price Change — dominant primary KPI, tighter */}
            <div className="mb-3 pb-3 border-b border-white/[0.06]">
              <p className="text-[11px] text-slate-500 uppercase tracking-[0.14em] mb-1">Relist Price Chg</p>
              {seller?.median_reprice_delta != null ? (
                <div className="flex items-end gap-1.5">
                  <p className={cn("text-[26px] font-black tabular-nums leading-none",
                    seller.median_reprice_delta < 0 ? "text-red-300"
                    : seller.median_reprice_delta > 0 ? "text-emerald-300"
                    : "text-slate-400")}>
                    {seller.median_reprice_delta > 0 ? "+" : ""}{fmt$$(seller.median_reprice_delta)}
                  </p>
                  <span className="text-[11px] text-slate-500 pb-0.5">median</span>
                </div>
              ) : (
                <p className="text-[26px] font-black text-slate-700 tabular-nums leading-none">—</p>
              )}
            </div>

            {/* Repriced / Price Drops / Churn */}
            {[
              { label: "Repriced 24H",  val: seller?.repriced_24h != null ? fmtNum(seller.repriced_24h) : null,
                cls: seller?.repriced_24h ? "text-amber-400" : "text-slate-600" },
              { label: "Price Drops",   val: seller?.price_drops_24h != null ? fmtNum(seller.price_drops_24h) : null,
                cls: seller?.price_drops_24h ? "text-red-400" : "text-slate-600" },
              { label: "Churn Rate",    val: seller?.churn_rate != null ? `${seller.churn_rate.toFixed(1)}×` : null,
                cls: (() => {
                  const c = seller?.churn_rate ?? null;
                  return c == null ? "text-slate-600" : c > 3 ? "text-red-400" : c > 1.5 ? "text-amber-400" : "text-emerald-400/70";
                })() },
            ].map(({ label, val, cls }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-white/[0.04]">
                <span className="text-[12px] text-slate-400">{label}</span>
                <span className={cn("text-[13px] font-bold tabular-nums", cls)}>{val ?? "—"}</span>
              </div>
            ))}

            {/* Seller Mood — behavioral momentum */}
            <div className="pt-2 mt-0.5">
              <p className="text-[11px] text-slate-500 uppercase tracking-[0.14em] mb-1">Seller Mood</p>
              <p className={cn("text-[13px] font-bold italic leading-snug",
                sellerMood === "Seller capitulation increasing" ? "text-red-300"
                : sellerMood === "Repricing accelerating" ? "text-red-300/80"
                : sellerMood === "Aggressive repricing" ? "text-amber-300"
                : sellerMood === "Price cuts slowing" ? "text-amber-300/70"
                : sellerMood === "Holding firm" ? "text-emerald-300"
                : sellerMood === "Stable seller behavior" ? "text-emerald-300/70"
                : "text-slate-600")}>
                {sellerMood}
              </p>
            </div>
          </div>
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
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em] flex-shrink-0">Marketplace Activity</h2>
          <div className="flex-1 h-px bg-white/[0.06]" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {MP_SLUGS.map(slug => {
            const info    = MP_META[slug]!;
            const mpData  = marketplaces.find(m => normMp(m.name) === slug);
            const bsData  = baseline?.per_marketplace?.find(m => m.marketplace_slug === slug);
            const fresh   = eventMeta?.marketplace_freshness?.[slug] as { freshness_status?: string; age_minutes?: number } | undefined;
            const tracked = eventMeta?.tracked_events?.find(t => t.marketplace_slug === slug);
            const st      = fresh?.freshness_status ?? "unknown";
            const freshDot = st === "fresh" ? "bg-emerald-400" : st === "late" ? "bg-amber-400" : st === "dead" ? "bg-red-500" : "bg-slate-700";
            const inv24   = bsData?.listings_change_24h?.absolute ?? null;
            const mpSeller = seller?.by_marketplace?.find(b => normMp(b.marketplace) === slug || normMp(b.marketplace) === normMp(info.label)) ?? null;
            const isBest  = mpData != null && marketplaces.length > 0 && mpData.low_ask === marketplaces[0].low_ask;
            const mpAction = signalToAction(hero?.signal);
            const mpColors = actionColors(mpAction);

            return (
              <div key={slug} className="rounded-xl border border-white/[0.07] bg-[#0d1018] overflow-hidden flex flex-col"
                style={{ borderTop: `2px solid ${info.color}55` }}>
                <div className="p-4 flex flex-col gap-3 flex-1">

                  {/* Header: branded logo + freshness dot */}
                  <div className="flex items-center justify-between">
                    <MpLogo slug={slug} info={info} size={22} />
                    <div className="flex items-center gap-1.5">
                      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${freshDot}`} />
                      {fresh?.age_minutes != null && (
                        <span className="text-[11px] text-slate-500 tabular-nums">
                          {fresh.age_minutes < 60 ? `${fresh.age_minutes}m` : `${Math.round(fresh.age_minutes/60)}h`}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 8-row data layout: Median first per spec */}
                  <div className="space-y-0">
                    {[
                      {
                        label: "Median",
                        value: fmt$$(mpData?.median_ask) ?? "—",
                        cls: "text-white font-bold text-[13px]",
                        extra: null,
                      },
                      {
                        label: "Inventory",
                        value: mpData?.listings != null ? fmtNum(mpData.listings) : "—",
                        cls: "text-blue-300/80 font-semibold",
                        extra: inv24 != null && inv24 !== 0
                          ? <span className={cn("text-[10px] font-bold ml-1", inv24 < 0 ? "text-emerald-400" : "text-red-400")}>{inv24 > 0 ? "+" : ""}{inv24}</span>
                          : null,
                      },
                      {
                        label: "Dup %",
                        value: snapshot?.duplicates?.dup_pct != null ? `${snapshot.duplicates.dup_pct.toFixed(1)}%` : "—",
                        cls: "text-violet-300/60",
                        extra: null,
                      },
                      {
                        label: "Low",
                        value: fmt$$(mpData?.low_ask) ?? "—",
                        cls: isBest ? "text-emerald-300 font-bold" : "text-emerald-300/80 font-semibold",
                        extra: isBest ? <span className="text-[10px] text-emerald-500 font-medium ml-1">best</span> : null,
                      },
                      {
                        label: "High",
                        value: fmt$$(mpData?.high_ask) ?? "—",
                        cls: "text-slate-400",
                        extra: null,
                      },
                      {
                        label: "Avg Sale",
                        value: "—",
                        cls: "text-slate-700",
                        extra: null,
                      },
                      {
                        label: "Removed 24H",
                        value: mpSeller?.removed_24h != null ? fmtNum(mpSeller.removed_24h) : "—",
                        cls: mpSeller?.removed_24h ? "text-red-400/80 font-semibold" : "text-slate-700",
                        extra: null,
                      },
                      {
                        label: "Relist Chg",
                        value: "—",
                        cls: "text-slate-700",
                        extra: null,
                      },
                    ].map(({ label, value, cls, extra }, i) => (
                      <div key={label} className={cn("flex items-center justify-between py-1.5",
                        i < 7 ? "border-b border-white/[0.04]" : "")}>
                        <span className="text-[11px] text-slate-500">{label}</span>
                        <span className={cn("text-[12px] tabular-nums flex items-center", cls)}>
                          {value}{extra}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Footer: action + view link */}
                  <div className="flex items-center gap-2 mt-auto pt-2.5 border-t border-white/[0.04]">
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded border flex-shrink-0"
                      style={{ color: mpColors.text, borderColor: mpColors.border + "60", background: mpColors.bg + "30" }}>
                      {mpAction}
                    </span>
                    {tracked?.external_url && (
                      <a href={tracked.external_url} target="_blank" rel="noopener noreferrer"
                        className="ml-auto text-[11px] font-semibold text-slate-500 hover:text-slate-200 transition-colors flex items-center gap-0.5">
                        View <ArrowUpRight size={10} />
                      </a>
                    )}
                  </div>
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
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em] flex-shrink-0">Venue Intelligence</h2>
            <div className="flex-1 h-px bg-white/[0.06]" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
            {/* LEFT — Interactive venue map + section details */}
            <div>
              <VenueIntelligence venueSlug={eventMeta.venue_slug} eventId={id} />
            </div>

            {/* RIGHT — Top 5 Moving Sections by activity */}
            <div className="rounded-xl border border-white/[0.07] bg-[#0f1420] overflow-hidden">
              <div className="px-4 py-3 border-b border-white/6 flex items-center justify-between">
                <p className="text-xs font-semibold text-slate-300">Top Sections by Activity</p>
                <p className="text-[11px] text-slate-500">sorted by activity score</p>
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
                          <span className="text-[11px] font-bold text-slate-500 w-4 tabular-nums">{i + 1}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-200 truncate">{s.display_name}</p>
                            <p className="text-[11px] text-slate-500">
                              {s.listings != null ? `${fmtNum(s.listings)} listings` : ""}
                              {s.listings != null && s.low_ask != null ? " · " : ""}
                              {s.low_ask != null ? `from ${fmt$$(s.low_ask)}` : ""}
                            </p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-xs font-bold text-slate-200 tabular-nums">{fmt$$(s.median_ask) ?? "—"}</p>
                            <p className="text-[11px] text-slate-500">median</p>
                          </div>
                          {s.activity_score != null && (
                            <div className="w-1 h-8 rounded-full flex-shrink-0"
                              style={{ background: `rgba(59,130,246,${Math.min(s.activity_score, 1)})` }} />
                          )}
                          <span className="text-[11px] text-slate-500 w-12 text-right tabular-nums flex-shrink-0">
                            {inv24 ?? "—"}
                          </span>
                        </div>
                      );
                    })}
                  <div className="px-4 py-2 border-t border-white/5">
                    <p className="text-[11px] text-slate-600">Activity = listing velocity + price movement. Relist data pending.</p>
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
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em] flex-shrink-0">Market Summary</h2>
          <div className="flex-1 h-px bg-white/[0.06]" />
          {hero?.history_context?.hours_available != null && (
            <span className="text-[11px] text-slate-500 flex items-center gap-1 flex-shrink-0">
              <Clock size={9} />
              {hero.history_context.hours_available > 24
                ? `${Math.round(hero.history_context.hours_available / 24)}d history`
                : "Live data"}
            </span>
          )}
        </div>
        <div className="rounded-xl border border-white/[0.07] bg-[#0b0d16] overflow-hidden">
          {/* Header bar — signal + since-tracking delta */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06]"
            style={{ background: aColors.bg + "18" }}>
            <div className="flex items-center gap-2.5">
              <span className="text-[12px] font-black uppercase tracking-[0.1em]" style={{ color: aColors.text }}>{action}</span>
              <span className="text-[11px] text-slate-500">{signalDescription(hero?.signal ?? "hold")}</span>
            </div>
            {sincePct != null && (
              <div className="flex items-center gap-1.5">
                <DeltaChip pct={sincePct} />
                <span className="text-[11px] text-slate-600">since tracking</span>
              </div>
            )}
          </div>
          {/* Intelligence bullets */}
          <div className="px-5 py-4">
            {bullets.length > 0 ? (
              <ul className="space-y-3">
                {bullets.slice(0, 5).map((b, i) => (
                  <li key={i} className="flex items-start gap-3 leading-relaxed">
                    <span className="mt-[7px] w-1 h-1 rounded-full bg-slate-600 flex-shrink-0" />
                    <span className="text-[13px] text-slate-300">{b}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[13px] text-slate-600 italic">
                Insufficient data for market analysis. Signal accuracy improves as price history accumulates.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          SECTION 7 — HISTORICAL ANALYSIS
          Tabbed: Price | Inventory | Sections | Marketplaces
          ════════════════════════════════════════ */}
      <section>
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-[0.18em] flex-shrink-0">Historical Analysis</h2>
          <div className="flex-1 h-px bg-white/[0.06]" />
        </div>

        {/* Tab bar — TradingView style */}
        <div className="flex border-b border-white/[0.07] mb-4 gap-0 overflow-x-auto">
          {(["Price", "Inventory", "Sections", "Marketplaces"] as const).map(tab => (
            <button key={tab} onClick={() => setActiveHistTab(tab)}
              className={cn(
                "px-5 py-2.5 text-[13px] font-semibold transition-colors border-b-2 -mb-[1px] whitespace-nowrap",
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
              <div className="flex rounded-lg border border-white/[0.07] overflow-hidden text-xs">
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
            <div className="rounded-xl border border-white/[0.07] bg-[#0d1018] overflow-hidden">
              {/* Chart toolbar */}
              {hero && (
                <div className="flex items-center gap-6 px-5 py-3 border-b border-white/[0.05] bg-white/[0.01]">
                  {[
                    { label: "Low",    val: hero.price?.low_ask,    cls: "text-emerald-400" },
                    { label: "Median", val: hero.price?.median_ask, cls: "text-white/70" },
                    { label: "p75",    val: hero.price?.p75_ask,    cls: "text-white/45" },
                    { label: "High",   val: hero.price?.high_ask,   cls: "text-white/35" },
                  ].map(({ label, val, cls }) => (
                    <div key={label} className="flex items-baseline gap-1.5">
                      <span className="text-[11px] text-slate-500 uppercase tracking-[0.12em]">{label}</span>
                      <span className={cn("text-[14px] font-bold tabular-nums", cls)}>{fmt$$(val)}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Chart */}
              <div className="p-4">
                {history?.series?.length
                  ? <PriceHistoryChart series={history.series} window={histWindow} height={240} />
                  : <div className="h-[240px] flex items-center justify-center text-[13px] text-slate-600">Not enough data yet</div>}
              </div>
            </div>
          </div>
        )}

        {/* ── Inventory tab ── */}
        {activeHistTab === "Inventory" && (
          <div className="rounded-xl border border-white/[0.07] bg-[#161b27] p-4 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Total Now",   val: fmtNum(hero?.inventory?.total_listings) },
                { label: "24h Net",     val: invDelta24 != null ? (invDelta24 > 0 ? `+${invDelta24}` : `${invDelta24}`) : null },
                { label: "Added 24h",   val: seller?.new_listings_24h != null ? `+${fmtNum(seller.new_listings_24h)}` : null },
                { label: "Removed 24h", val: seller?.removed_listings_24h != null ? fmtNum(seller.removed_listings_24h) : null },
              ].map(({ label, val }) => (
                <div key={label}>
                  <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-0.5">{label}</p>
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
                    <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-0.5">{label}</p>
                    <p className={cn("text-sm font-bold tabular-nums", cls)}>{val ?? "—"}</p>
                  </div>
                ))}
              </div>
            )}
            {/* Largest price drops detail */}
            {(seller?.largest_price_drops?.length ?? 0) > 0 && seller && (
              <div className="pt-3 border-t border-white/5">
                <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] font-semibold mb-2">Largest Price Drops</p>
                <div className="rounded-lg border border-white/5 overflow-hidden">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/5">
                        {["Section","Was","Now","Drop"].map(h => (
                          <th key={h} className="text-left px-3 py-2 text-[11px] text-slate-500 uppercase tracking-[0.12em] font-medium">{h}</th>
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
              : <div className="rounded-xl border border-white/[0.07] bg-[#161b27] py-8 text-center text-xs text-slate-600">No section data available</div>
            }
            {listings && listings.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Lowest Available Tickets</p>
                <div className="rounded-xl border border-white/[0.07] bg-[#161b27] overflow-x-auto">
                  <table className="w-full text-xs min-w-[480px]">
                    <thead>
                      <tr className="border-b border-white/5">
                        {["#","Price","Section","Row","Qty","Marketplace","Move",""].map(h => (
                          <th key={h} className="text-left px-3 py-2 text-[11px] text-slate-500 uppercase tracking-[0.12em] font-medium first:pl-4">{h}</th>
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
                                  className="text-[11px] text-blue-500 hover:text-blue-400 transition-colors">buy ↗</a>
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
              <div className="rounded-xl border border-white/[0.07] bg-[#161b27] overflow-hidden">
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
              <div className="rounded-xl border border-white/[0.07] bg-[#161b27] py-8 text-center text-xs text-slate-600">
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
                <h3 className="text-[12px] text-slate-500 uppercase tracking-[0.18em] font-bold mb-2">Data Context</h3>
                <div className="rounded-xl border border-white/6 bg-[#161b27] p-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { label: "History Available", val: hero.history_context.hours_available != null ? `${Math.round(hero.history_context.hours_available)}h` : "—" },
                    { label: "Data Depth",        val: (hero.history_context as { data_depth?: string }).data_depth ?? "—" },
                    { label: "Since Tracking",    val: sincePct != null ? fmtPct(sincePct) : "—" },
                  ].map(({ label, val }) => (
                    <div key={label}>
                      <p className="text-[11px] text-slate-500 uppercase tracking-[0.12em] mb-0.5">{label}</p>
                      <p className="text-[13px] font-semibold text-slate-400">{val}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h3 className="text-[12px] text-slate-500 uppercase tracking-[0.18em] font-bold mb-2">Marketplace Status</h3>
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
              <h3 className="text-[12px] text-slate-500 uppercase tracking-[0.18em] font-bold mb-2">Today&apos;s Movement</h3>
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
                      <p className="text-[11px] text-slate-500">{sub}</p>
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
