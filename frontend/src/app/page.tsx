"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { fmtDate, fmt$ } from "@/lib/utils";
import { getEntityImage } from "@/lib/entityImages";
import { EntityLogo } from "@/components/ui/EntityLogo";
import { Plus, Calendar, TrendingUp, Activity, ChevronRight, ChevronDown, Ticket, Star, Zap, EyeOff, Eye } from "lucide-react";
import { useMyEvents } from "@/hooks/useMyEvents";
import { useHeroEvent } from "@/hooks/useHeroEvent";
import { useFollowed } from "@/hooks/useFollowed";
import { useHiddenEvents } from "@/hooks/useHiddenEvents";

// ── Entity helpers ─────────────────────────────────────────────────────────────

// Specific full-title overrides (tour/show subtitle → canonical artist name)
const ENTITY_OVERRIDES: Record<string, string> = {
  'My Chemical Romance: The Black Parade': 'My Chemical Romance',
};

// Sports team shorthand → full display name (applied after " at " stripping)
const TEAM_MAP: Record<string, string> = {
  'NFL Preseason: 49ers':    'San Francisco 49ers',
  'NFL Preseason: Chargers': 'Los Angeles Chargers',
  'NFL Preseason: Rams':     'Los Angeles Rams',
  'NFL Preseason: Raiders':  'Las Vegas Raiders',
  'NFL Preseason: Angels':   'Los Angeles Angels',
  'NFL Preseason: Dodgers':  'Los Angeles Dodgers',
  'NFL Preseason: Lakers':   'Los Angeles Lakers',
  'NFL Preseason: Clippers': 'Los Angeles Clippers',
  '49ers':    'San Francisco 49ers',
  'Chargers': 'Los Angeles Chargers',
  'Rams':     'Los Angeles Rams',
  'Raiders':  'Las Vegas Raiders',
  'Angels':   'Los Angeles Angels',
  'Dodgers':  'Los Angeles Dodgers',
  'Lakers':   'Los Angeles Lakers',
  'Clippers': 'Los Angeles Clippers',
};

function getEntityName(title: string): string {
  // 1. Specific full-title overrides
  if (ENTITY_OVERRIDES[title]) return ENTITY_OVERRIDES[title];

  let name = title;

  // 2. Strip " at [venue/opponent]", " vs [team]", " with [opener]"
  const atIdx = name.search(/ at /i);
  if (atIdx > -1) name = name.slice(0, atIdx).trim();
  const vsIdx = name.search(/ vs\.? /i);
  if (vsIdx > -1) name = name.slice(0, vsIdx).trim();
  const withIdx = name.search(/ with /i);
  if (withIdx > -1) name = name.slice(0, withIdx).trim();

  // 3. Sports team normalization (after stripping " at ")
  if (TEAM_MAP[name]) return TEAM_MAP[name];

  // 4. Strip tour subtitle after colon if subtitle contains "Tour"
  //    e.g. "Ariana Grande: Eternal Sunshine Tour" → "Ariana Grande"
  const colonIdx = name.indexOf(': ');
  if (colonIdx > -1 && /\btour\b/i.test(name.slice(colonIdx + 2))) {
    name = name.slice(0, colonIdx).trim();
  }

  // 5. Strip "World Tour" / "Tour" bare suffix
  //    e.g. "BTS World Tour" → "BTS"
  name = name.replace(/\s+World Tour$/i, '').replace(/\s+Tour$/i, '').trim();

  return name;
}

interface EntityTheme {
  gradFrom: string; gradMid: string; gradTo: string;
  accent: string;   accentDim: string; accentRgb: string;
  category: string; initial: string;
}

function getEntityTheme(name: string): EntityTheme {
  const n = name.toLowerCase();
  const isNFL  = /49ers|rams|chargers|raiders|chiefs|cowboys|eagles|packers|bears/.test(n);
  const isMLB  = /rangers|angels|dodgers|giants|padres|yankees|cubs|red sox/.test(n);
  const isNBA  = /lakers|clippers|warriors|celtics|heat|bulls/.test(n);
  const isRock = /metallica|rolling stones|u2|foo fighters|guns n|led zep/.test(n);
  const initial = name[0]?.toUpperCase() ?? "?";
  if (isNFL)  return { gradFrom:"#2A0000", gradMid:"#180000", gradTo:"#0D0000", accent:"#E50914", accentDim:"rgba(229,9,20,0.18)",   accentRgb:"229,9,20",    category:"NFL",   initial };
  if (isMLB)  return { gradFrom:"#1A0E00", gradMid:"#100800", gradTo:"#060200", accent:"#F97316", accentDim:"rgba(249,115,22,0.18)", accentRgb:"249,115,22",  category:"MLB",   initial };
  if (isNBA)  return { gradFrom:"#00101A", gradMid:"#000A12", gradTo:"#000509", accent:"#3B82F6", accentDim:"rgba(59,130,246,0.18)",  accentRgb:"59,130,246",  category:"NBA",   initial };
  if (isRock) return { gradFrom:"#0A0A1A", gradMid:"#060610", gradTo:"#030308", accent:"#A78BFA", accentDim:"rgba(167,139,250,0.18)", accentRgb:"167,139,250", category:"ROCK",  initial };
  return        { gradFrom:"#0D0018", gradMid:"#070010", gradTo:"#040008", accent:"#8B5CF6", accentDim:"rgba(139,92,246,0.18)",   accentRgb:"139,92,246",  category:"MUSIC", initial };
}

interface MarketStatus { label: string; emoji: string; cssClass: string; }
function getMarketStatus(price: number | null): MarketStatus {
  if (!price) return { label:"—",        emoji:"",   cssClass:"status-value"   };
  if (price < 60)  return { label:"Value",   emoji:"✦",  cssClass:"status-value"   };
  if (price < 150) return { label:"Active",  emoji:"◈",  cssClass:"status-active"  };
  if (price < 300) return { label:"Hot",     emoji:"🔥", cssClass:"status-hot"     };
  return                  { label:"Premium", emoji:"★",  cssClass:"status-premium" };
}

function fmtVenue(slug?: string): string {
  if (!slug) return "";
  return slug.replace(/_/g," ").replace(/-/g," ").replace(/\b\w/g, c => c.toUpperCase());
}

function daysUntil(iso: string): number {
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000);
}

interface EventGroup {
  entity: string; theme: EntityTheme; events: any[];
  minPrice: number | null; totalListings: number;
}

function groupEvents(events: any[]): EventGroup[] {
  const map = new Map<string, any[]>();
  for (const ev of events) {
    const entity = getEntityName(ev.title);
    if (!map.has(entity)) map.set(entity, []);
    map.get(entity)!.push(ev);
  }
  const groups: EventGroup[] = [];
  for (const [entity, evs] of map) {
    const prices = evs.map((e:any)=> e.lowest_ask_stubhub ?? e.marketplace_prices?.tickpick ?? e.marketplace_prices?.gametime).filter(Boolean) as number[];
    groups.push({
      entity,
      theme: getEntityTheme(entity),
      events: evs.sort((a:any,b:any)=> new Date(a.event_date).getTime() - new Date(b.event_date).getTime()),
      minPrice: prices.length ? Math.min(...prices) : null,
      totalListings: evs.reduce((s:number,e:any)=> s + (e.total_listings ?? 0), 0),
    });
  }
  return groups.sort((a,b)=>{
    if (b.events.length !== a.events.length) return b.events.length - a.events.length;
    return new Date(a.events[0]?.event_date??"9999").getTime() - new Date(b.events[0]?.event_date??"9999").getTime();
  });
}

// ── Market Tape ────────────────────────────────────────────────────────────────

function MarketTape({ summary, eventCount, groupCount }: { summary:any; eventCount:number; groupCount:number }) {
  const totalListings = summary?.total_listings;
  const avgAsk        = summary?.avg_lowest_ask;

  const cells = [
    { num: String(eventCount),   label:"Events",   accent:"#E50914" },
    { num: totalListings != null ? (totalListings/1000).toFixed(0)+"K" : "—", label:"Listings", accent:"#F97316" },
    { num: avgAsk       != null ? fmt$(avgAsk) : "—",                          label:"Avg Market",accent:"#3B82F6" },
    { num: String(groupCount),   label:"Entities", accent:"#8B5CF6" },
    { num: "Live",               label:"Status",   accent:"#22C55E" },
  ];

  return (
    <div className="grid grid-cols-5 gap-2">
      {cells.map(({ num, label, accent }) => (
        <div
          key={label}
          className="relative rounded-xl px-4 py-3"
          style={{ background:"rgba(255,255,255,0.025)", border:"1px solid rgba(255,255,255,0.06)" }}
        >
          {/* Color top border */}
          <div className="absolute top-0 left-0 right-0 h-[2px] rounded-t-xl" style={{ background: accent }} />
          <div className="text-white font-black text-xl leading-none mt-1" style={{ letterSpacing:"-0.04em" }}>{num}</div>
          <div className="text-[9px] font-bold uppercase tracking-widest mt-1.5" style={{ color:"#6B7280" }}>{label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Featured Hero ──────────────────────────────────────────────────────────────

function FeaturedHero({ event, onClearHero }: { event: any; onClearHero?: () => void }) {
  const [heroImgErr, setHeroImgErr] = useState(false);
  const theme  = getEntityTheme(getEntityName(event.title));
  const price  = event.lowest_ask_stubhub ?? event.marketplace_prices?.tickpick ?? event.marketplace_prices?.gametime;
  const status = getMarketStatus(price);
  const days   = daysUntil(event.event_date);
  const venue  = fmtVenue(event.venue_slug);
  const entity = getEntityName(event.title);
  const subtitle = event.title !== entity ? event.title.replace(entity,"").replace(/^[\s·–—]/,"").trim() : "";
  const isValue  = price != null && price < 100;
  const heroImgUrl = !heroImgErr ? getEntityImage(entity).logo : undefined;

  return (
    <Link href={`/events/${event.id}`} className="block group">
      <div className="hero-card relative overflow-hidden" style={{ minHeight:340 }}>

        {/* === Layer 1: Base gradient === */}
        <div className="absolute inset-0" style={{
          background:`linear-gradient(145deg, ${theme.gradFrom} 0%, ${theme.gradMid} 45%, ${theme.gradTo} 100%)`
        }}/>

        {/* === Layer 2: Triple radial atmospheric glows === */}
        <div className="absolute inset-0" style={{
          background:`
            radial-gradient(ellipse 65% 90% at 18% 55%, rgba(${theme.accentRgb},0.28) 0%, transparent 55%),
            radial-gradient(ellipse 45% 60% at 88% 18%, rgba(${theme.accentRgb},0.14) 0%, transparent 50%),
            radial-gradient(ellipse 35% 45% at 55% 95%, rgba(${theme.accentRgb},0.10) 0%, transparent 45%)
          `
        }}/>

        {/* === Layer 3: Animated breathing orb === */}
        <div
          className="atmosphere-orb absolute rounded-full pointer-events-none"
          style={{
            width:420, height:420,
            top:"-15%", left:"-5%",
            background:`radial-gradient(circle, rgba(${theme.accentRgb},0.12) 0%, transparent 70%)`,
          }}
        />

        {/* === Layer 4: Dot grid texture === */}
        <div className="absolute inset-0 opacity-[0.06]" style={{
          backgroundImage:`radial-gradient(circle, ${theme.accent} 1px, transparent 1px)`,
          backgroundSize:"28px 28px",
        }}/>

        {/* === Layer 5: Bottom fade into page === */}
        <div className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
          style={{ background:"linear-gradient(0deg, rgba(6,0,4,0.6) 0%, transparent 100%)" }}/>

        {/* === Layer 6: Entity image (when available) or large watermark initial === */}
        {heroImgUrl ? (
          <div
            className="absolute right-0 top-0 bottom-0 flex items-center justify-end pointer-events-none select-none"
            style={{ width:"42%", paddingRight:"5%" }}
          >
            {/* Gradient scrim — left edge fade so image doesn't bleed into text */}
            <div className="absolute inset-0" style={{
              background:"linear-gradient(to right, rgba(6,0,4,0.95) 0%, rgba(6,0,4,0.3) 35%, transparent 70%)"
            }}/>
            <img
              src={heroImgUrl}
              alt={entity}
              onError={() => setHeroImgErr(true)}
              style={{
                width:"100%", height:"92%", objectFit:"contain", objectPosition:"center right",
                opacity:0.72, filter:"drop-shadow(0 0 40px rgba(0,0,0,0.6))",
                position:"relative", zIndex:1,
              }}
            />
          </div>
        ) : (
          <div
            className="absolute right-0 top-0 bottom-0 flex items-center pr-8 select-none pointer-events-none"
            style={{
              fontSize:"clamp(140px, 22vw, 260px)", fontWeight:900,
              color:`rgba(${theme.accentRgb}, 0.14)`,
              WebkitTextStrokeWidth:"1.5px",
              WebkitTextStrokeColor:`rgba(${theme.accentRgb}, 0.20)`,
              lineHeight:1, letterSpacing:"-0.06em",
            }}
          >
            {theme.initial}
          </div>
        )}

        {/* Content */}
        <div className="relative z-10 p-8 sm:p-10 flex flex-col justify-between h-full" style={{ minHeight:340 }}>
          {/* Top row: logo + chips + days */}
          <div className="flex items-start justify-between gap-4">
            {onClearHero && (
              <button
                onClick={(e) => { e.preventDefault(); onClearHero(); }}
                className="absolute top-3 right-3 z-20 text-[10px] font-bold px-2 py-1 rounded-md opacity-40 hover:opacity-80 transition-opacity"
                style={{ background: "rgba(0,0,0,0.5)", color: "#fff", border: "1px solid rgba(255,255,255,0.15)" }}
                title="Remove pinned hero"
              >
                ✕ Unpin
              </button>
            )}
            <div className="flex items-center gap-3">
              <EntityLogo entity={entity} initial={theme.initial} accent={theme.accent}
                gradFrom={theme.gradFrom} gradMid={theme.gradMid} size={56} />
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full pulse-live" style={{ background:"#00F2FF" }}/>
                  <span className="section-label" style={{ color:"#00F2FF", opacity:0.8 }}>Live Market</span>
                </div>
                <span className="text-[9px] font-bold tracking-widest px-2 py-0.5 rounded-full w-fit"
                  style={{ background:theme.accentDim, color:theme.accent, border:`1px solid ${theme.accent}44` }}>
                  {theme.category}
                </span>
              </div>
            </div>
            {days > 0 && (
              <div className="days-chip shrink-0"><Calendar size={10}/>{days} {days===1?"day":"days"} away</div>
            )}
          </div>

          {/* Event identity */}
          <div className="mt-6">
            <h2 className="text-white font-black leading-none"
              style={{ fontSize:"clamp(2rem, 5vw, 3.6rem)", letterSpacing:"-0.035em" }}>
              {entity}
            </h2>
            {subtitle && <p className="text-white/35 font-medium mt-1.5 text-sm">{subtitle}</p>}
            <p className="text-white/25 text-sm mt-2">
              {venue}{venue && " · "}{fmtDate(event.event_date)}
            </p>
          </div>

          {/* Bottom: price + metrics + value signal + CTA */}
          <div className="flex items-end justify-between mt-8 gap-4 flex-wrap">
            <div className="flex items-end gap-8 sm:gap-12">
              {/* Price — dominant */}
              <div>
                <div className="font-black leading-none text-white"
                  style={{ fontSize:"clamp(2.4rem, 5vw, 3.2rem)", letterSpacing:"-0.045em" }}>
                  {price != null ? fmt$(price) : "—"}
                </div>
                <div className="stat-label mt-1">Lowest ask</div>
              </div>
              {/* Marketplace coverage */}
              {(() => {
                const mp = event.marketplace_prices || event.all_marketplace_prices || {};
                const count = ['stubhub','tickpick','gametime','vividseats'].filter(k => mp[k] != null).length;
                if (count === 0) return null;
                return (
                  <div className="pb-0.5">
                    <div className="text-white/50 font-bold text-xl" style={{ letterSpacing:"-0.02em" }}>
                      {count}/4
                    </div>
                    <div className="stat-label">Markets</div>
                  </div>
                );
              })()}
            </div>

            {/* Right: value signal + status + CTA */}
            <div className="flex items-center gap-3 shrink-0 flex-wrap justify-end">
              {isValue && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold"
                  style={{ background:"rgba(34,197,94,0.1)", border:"1px solid rgba(34,197,94,0.25)", color:"#22c55e" }}>
                  ↑ Value Buy
                </div>
              )}
              {price != null && !isValue && (
                <span className={`px-3 py-1.5 rounded-xl text-sm font-bold ${status.cssClass}`}>
                  {status.emoji} {status.label}
                </span>
              )}
              <div
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 group-hover:brightness-110 group-hover:scale-[1.02]"
                style={{
                  background:`linear-gradient(135deg, ${theme.accent} 0%, ${theme.accent}CC 100%)`,
                  boxShadow:`0 4px 20px rgba(${theme.accentRgb}, 0.38)`,
                }}
              >
                View Market
                <ChevronRight size={14} className="group-hover:translate-x-0.5 transition-transform"/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

// ── Event Row ──────────────────────────────────────────────────────────────────

function EventRow({ ev, theme, isMyEvent, onToggleMyEvent }: {
  ev: any; theme: EntityTheme;
  isMyEvent?: boolean; onToggleMyEvent?: (id: number) => void;
}) {
  const price  = ev.lowest_ask_stubhub ?? ev.marketplace_prices?.tickpick ?? ev.marketplace_prices?.gametime;
  const status = getMarketStatus(price);
  const venue  = fmtVenue(ev.venue_slug);
  const days   = daysUntil(ev.event_date);

  // Derive the display title (opponent / subtitle / short form)
  let displayTitle = ev.title;
  const vsIdx  = ev.title.search(/ vs\.? /i);
  const atIdx  = ev.title.search(/ at /i);
  const wIdx   = ev.title.search(/ with /i);
  if      (vsIdx > -1) displayTitle = "vs " + ev.title.slice(vsIdx + 4).split(/\s+at\s+/i)[0].trim();
  else if (atIdx > -1) displayTitle = ev.title.slice(0, atIdx).trim();
  else if (wIdx  > -1) displayTitle = ev.title.slice(0, wIdx).trim();

  // Short date (e.g. "Jun 7")
  const d = new Date(ev.event_date);
  const shortDate = d.toLocaleDateString("en-US", { month:"short", day:"numeric" });
  const isValue = price != null && price < 100;

  return (
    <Link
      href={`/events/${ev.id}`}
      className="flex items-center px-5 py-3 hover:bg-white/[0.025] transition-colors group"
      style={{ borderBottom:"1px solid rgba(255,255,255,0.035)" }}
    >
      {/* Entity color tile */}
      <div
        className="w-5 h-5 rounded shrink-0 mr-0 flex items-center justify-center"
        style={{
          background:`linear-gradient(135deg, ${theme.gradFrom} 0%, ${theme.gradMid} 100%)`,
          border:`1px solid rgba(${theme.accentRgb}, 0.25)`,
          boxShadow:`0 0 6px rgba(${theme.accentRgb}, 0.15)`,
        }}
      >
        <span style={{ fontSize:8, fontWeight:900, color:theme.accent, lineHeight:1 }}>
          {theme.initial}
        </span>
      </div>

      {/* Date column */}
      <div className="w-14 shrink-0 ml-2">
        <div className="text-[10px] font-bold text-slate-600 uppercase tracking-wider leading-tight">{shortDate}</div>
        {days > 0 && days <= 60 && (
          <div className="text-[9px] text-slate-700 mt-0.5">{days}d</div>
        )}
      </div>

      {/* Title + venue */}
      <div className="flex-1 min-w-0 px-3">
        <div className="text-[13px] text-slate-300 font-medium truncate group-hover:text-white transition-colors leading-tight">
          {displayTitle}
        </div>
        <div className="text-[10px] text-slate-700 truncate mt-0.5 hidden sm:block">{venue}</div>
      </div>

      {/* Inventory — hidden on small screens */}
      <div className="w-16 shrink-0 text-right hidden lg:block">
        <div className="text-[11px] text-slate-700 tabular-nums">
          {ev.total_listings ? ev.total_listings.toLocaleString() : "—"}
        </div>
      </div>

      {/* Price — floor price + vs historical low + inventory */}
      <div className="w-36 shrink-0 text-right pl-3">
        <div
          className="text-[15px] font-bold leading-none tabular-nums"
          style={{ letterSpacing:"-0.03em", color: price == null ? "#374151" : isValue ? "#22c55e" : "#fff" }}
        >
          {price != null ? fmt$(price) : "—"}
        </div>
        {/* 24h price change if available */}
        {(() => {
          const p24 = ev.price_change_24h ?? ev.marketplace_prices?.price_change_24h;
          if (p24 == null || Math.abs(p24) < 0.5) return null;
          return (
            <div className="text-[9px] tabular-nums mt-0.5 font-medium" style={{ color: p24 <= 0 ? '#22C55E' : '#EF4444' }}>
              {p24 > 0 ? '+' : ''}{p24 > 0 ? fmt$(p24) : `-${fmt$(Math.abs(p24))}`} 24h
            </div>
          );
        })()}
        {/* Price vs historical low */}
        {(() => {
          const hist = ev.historical_lowest_price;
          if (price == null || hist == null || hist === 0) return null;
          const pct = ((price - hist) / hist) * 100;
          if (Math.abs(pct) < 1) return null;
          return (
            <div className="text-[9px] tabular-nums mt-0.5" style={{ color: pct <= 0 ? '#22C55E' : '#F59E0B' }}>
              {pct > 0 ? `+${pct.toFixed(0)}%` : `${pct.toFixed(0)}%`} vs low
            </div>
          );
        })()}
        {/* Inventory count */}
        {ev.total_listings > 0 && (
          <div className="text-[9px] tabular-nums mt-0.5 text-slate-700">
            {ev.total_listings.toLocaleString()} in
          </div>
        )}
      </div>

      {/* Badge */}
      <div className="w-16 shrink-0 text-right pl-2">
        {price != null ? (
          <span className={`text-[9px] font-bold px-2 py-1 rounded-md ${status.cssClass}`}>
            {status.label}
          </span>
        ) : (
          <span className="text-[9px] text-slate-700 px-1">No data</span>
        )}
      </div>

      {/* My Event star toggle */}
      {onToggleMyEvent && (
        <button
          onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggleMyEvent(ev.id); }}
          className="w-7 shrink-0 flex items-center justify-center ml-1 opacity-30 hover:opacity-90 transition-opacity"
          title={isMyEvent ? "Remove from My Events" : "Mark as My Event"}
        >
          <Star
            size={12}
            fill={isMyEvent ? "#F59E0B" : "none"}
            stroke={isMyEvent ? "#F59E0B" : "currentColor"}
            className="text-slate-500"
          />
        </button>
      )}
    </Link>
  );
}

// ── Entity Block ───────────────────────────────────────────────────────────────

function EntityBlock({ group, myEvents, onToggleMyEvent, heroEventId, onSetHero, onHide }: {
  group: EventGroup;
  myEvents: Set<number>;
  onToggleMyEvent: (id: number) => void;
  heroEventId: number | null;
  onSetHero: (id: number) => void;
  onHide: (ids: number[]) => void;
}) {
  const { entity, theme, events, minPrice, totalListings } = group;
  // Multi-event groups start collapsed; single-event groups start expanded
  const [expanded, setExpanded] = useState(events.length === 1);
  const status    = getMarketStatus(minPrice);
  const nextEvent = events[0];
  const days      = nextEvent ? daysUntil(nextEvent.event_date) : null;
  const isValue   = minPrice != null && minPrice < 100;
  const isHot     = minPrice != null && minPrice >= 100 && minPrice < 150;
  const hasMyEvent = events.some((ev: any) => myEvents.has(ev.id));
  const isHero     = events.some((ev: any) => ev.id === heroEventId);

  return (
    <section
      className="relative overflow-hidden rounded-2xl"
      style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.06)" }}
    >
      {/* Left edge accent bar — entity identity color */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[3px]"
        style={{ background:`linear-gradient(180deg, ${theme.accent}, rgba(${theme.accentRgb}, 0.08))` }}
      />

      {/* Entity header — click to expand/collapse */}
      <div
        className="flex items-center gap-4 pl-5 pr-5 py-4 cursor-pointer select-none"
        style={{ borderBottom: expanded ? "1px solid rgba(255,255,255,0.04)" : "none" }}
        onClick={() => setExpanded(v => !v)}
      >
        <EntityLogo
          entity={entity} initial={theme.initial} accent={theme.accent}
          gradFrom={theme.gradFrom} gradMid={theme.gradMid} size={72}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-white font-bold text-[15px] leading-none" style={{ letterSpacing:"-0.02em" }}>
              {entity}
            </h2>
            <span
              className="text-[9px] font-bold tracking-[0.16em] px-2 py-0.5 rounded"
              style={{ background:theme.accentDim, color:theme.accent }}
            >
              {theme.category}
            </span>
            {hasMyEvent && (
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                style={{ background:"rgba(245,158,11,0.12)", color:"#F59E0B", border:"1px solid rgba(245,158,11,0.3)" }}>
                ★ My Event
              </span>
            )}
            {isHero && (
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                style={{ background:"rgba(139,92,246,0.12)", color:"#8B5CF6", border:"1px solid rgba(139,92,246,0.3)" }}>
                ⚡ Hero
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <span className="text-slate-600 text-[11px]">
              {events.length} {events.length===1?"event":"events"}
            </span>
            {minPrice != null && (
              <>
                <span className="text-slate-700 text-xs">·</span>
                <span className="text-slate-500 text-[11px]">
                  from <span className="text-white font-semibold">{fmt$(minPrice)}</span>
                </span>
              </>
            )}
            {days != null && days > 0 && (
              <>
                <span className="text-slate-700 text-xs">·</span>
                <span className="text-slate-600 text-[11px] flex items-center gap-1">
                  <Calendar size={9}/>{days}d away
                </span>
              </>
            )}
            {(() => {
              const slugs = ['stubhub','tickpick','gametime','vividseats'];
              const count = slugs.filter(slug =>
                events.some((ev: any) => {
                  const mp = ev.marketplace_prices || ev.all_marketplace_prices || {};
                  return mp[slug] != null;
                })
              ).length;
              if (count === 0) return null;
              return (
                <>
                  <span className="text-slate-700 text-xs">·</span>
                  <span className="text-[11px]" style={{ color: count >= 3 ? '#4ADE80' : count >= 2 ? '#FB923C' : '#6B7280' }}>
                    {count}/4 markets
                  </span>
                </>
              );
            })()}
          </div>
        </div>

        {/* Status pill + marketplace coverage + Make Hero */}
        <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end" onClick={e => e.stopPropagation()}>
          {/* Marketplace coverage — dots + count */}
          {(() => {
            const markets = [
              { slug: 'stubhub',    dot: '#818CF8', label: 'SH' },
              { slug: 'tickpick',   dot: '#4ADE80', label: 'TP' },
              { slug: 'gametime',   dot: '#FB923C', label: 'GT' },
              { slug: 'vividseats', dot: '#F472B6', label: 'VS' },
            ];
            const covered = markets.filter(({ slug }) =>
              events.some((ev: any) => {
                const prices = ev.marketplace_prices || ev.all_marketplace_prices || {};
                return prices[slug] != null;
              })
            );
            return (
              <div className="flex items-center gap-1.5" title={`${covered.length} of ${markets.length} marketplaces live`}>
                {markets.map(({ slug, dot, label }) => {
                  const hasData = covered.some(m => m.slug === slug);
                  return (
                    <span
                      key={slug}
                      className="inline-block w-1.5 h-1.5 rounded-full"
                      style={{ background: hasData ? dot : 'rgba(255,255,255,0.1)', opacity: hasData ? 0.9 : 0.3 }}
                      title={`${label}: ${hasData ? 'live' : 'no data'}`}
                    />
                  );
                })}
                <span className="text-[9px] font-semibold tabular-nums ml-0.5"
                  style={{ color: covered.length >= 3 ? '#4ADE80' : covered.length >= 2 ? '#FB923C' : '#6B7280' }}>
                  {covered.length}/{markets.length}
                </span>
              </div>
            );
          })()}

          {minPrice != null && (
            <span className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg ${status.cssClass}`}>
              {status.emoji} {status.label}
            </span>
          )}
          {minPrice == null && (
            <span className="text-[9px] font-medium px-2 py-1 rounded-lg text-gray-600"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
              No inventory
            </span>
          )}
          {/* Make Hero: pin next event from this group as the featured hero */}
          <button
            onClick={() => onSetHero(nextEvent.id)}
            title={heroEventId === nextEvent.id ? "Pinned as hero" : "Pin as featured hero"}
            className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all"
            style={heroEventId === nextEvent.id
              ? { background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.4)", color: "#F59E0B" }
              : { background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)", color: "#4B5563" }
            }
          >
            <Zap size={9} fill={heroEventId === nextEvent.id ? "#F59E0B" : "none"}/>
            {heroEventId === nextEvent.id ? "Hero" : "Pin"}
          </button>
          {/* Hide all events in this entity group */}
          <button
            onClick={(e) => { e.stopPropagation(); onHide(events.map((ev: any) => ev.id)); }}
            title={`Hide ${entity} from dashboard`}
            className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all"
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", color: "#374151" }}
          >
            <EyeOff size={9}/>
          </button>
          {/* Expand/collapse chevron */}
          <div className="flex items-center justify-center w-6 h-6 ml-1 pointer-events-none">
            <ChevronDown
              size={13}
              className="transition-transform duration-200"
              style={{ color:"#374151", transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
            />
          </div>
        </div>
      </div>

      {/* Expandable body */}
      {expanded && (
        <>
          {/* Event rows — the table */}
          <div>
            {/* Column header — subtle */}
            <div
              className="flex items-center px-5 py-1.5"
              style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}
            >
              <div className="w-5 shrink-0"/>
              <div className="w-14 shrink-0 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Date</div>
              <div className="flex-1 px-3 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Event</div>
              <div className="w-16 shrink-0 text-right hidden lg:block text-[9px] text-slate-800 uppercase tracking-wider font-bold">Inventory</div>
              <div className="w-28 shrink-0 text-right pl-3 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Price</div>
              <div className="w-16 shrink-0" />
            </div>
            {events.map((ev) => (
              <EventRow
                key={ev.id}
                ev={ev}
                theme={theme}
                isMyEvent={myEvents.has(ev.id)}
                onToggleMyEvent={onToggleMyEvent}
              />
            ))}
          </div>

          {/* Market insight footer — only shown when there's a real signal */}
          {isValue && (
            <div
              className="flex items-center gap-3 pl-6 pr-5 py-2.5"
              style={{ background:"rgba(34,197,94,0.03)", borderTop:"1px solid rgba(34,197,94,0.1)" }}
            >
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background:"#22c55e" }}/>
              <span className="text-[11px] text-slate-600">
                <span className="text-green-400/80 font-semibold">Value signal</span> — lowest ask{" "}
                {fmt$(minPrice!)} is below typical market range for this category
              </span>
            </div>
          )}
          {isHot && (
            <div
              className="flex items-center gap-3 pl-6 pr-5 py-2.5"
              style={{ background:"rgba(249,115,22,0.03)", borderTop:"1px solid rgba(249,115,22,0.08)" }}
            >
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background:"#f97316" }}/>
              <span className="text-[11px] text-slate-600">
                <span className="text-orange-400/80 font-semibold">Watch</span> — market active, price may move before event
              </span>
            </div>
          )}
        </>
      )}
    </section>
  );
}

// ── Quick Filter Bar ──────────────────────────────────────────────────────────

type DashFilter = "all" | "concerts" | "sports" | "myevents" | "following";

function FilterBar({ active, onChange, myCount, followCount }: {
  active: DashFilter;
  onChange: (f: DashFilter) => void;
  myCount: number;
  followCount: number;
}) {
  const chips: { id: DashFilter; label: string; count?: number }[] = [
    { id: "all",       label: "All" },
    { id: "concerts",  label: "Concerts" },
    { id: "sports",    label: "Sports" },
    { id: "myevents",  label: "My Events", count: myCount },
    { id: "following", label: "Following",  count: followCount },
  ];
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {chips.map(({ id, label, count }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          className={`filter-chip ${active === id ? "active" : ""}`}
        >
          {label}
          {count != null && count > 0 && (
            <span className="ml-1.5 text-[9px] opacity-70">{count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

// ── Following Row ─────────────────────────────────────────────────────────────

function FollowingRow({ events, followed, onUnfollow }: {
  events: any[];
  followed: Set<number>;
  onUnfollow: (id: number) => void;
}) {
  const followedEvents = events.filter((e: any) => followed.has(e.id));
  if (followedEvents.length === 0) return null;
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Activity size={13} style={{ color:"#E50914" }}/>
        <span className="section-label">Following</span>
        <span className="text-[10px] text-slate-700 font-semibold">{followedEvents.length}</span>
      </div>
      <div className="scroll-row pb-1" style={{ display:"flex", gap:10, overflowX:"auto", scrollbarWidth:"none" }}>
        {followedEvents.map((ev: any) => {
          const theme = getEntityTheme(getEntityName(ev.title));
          const price = ev.lowest_ask_stubhub ?? ev.marketplace_prices?.tickpick ?? ev.marketplace_prices?.gametime;
          return (
            <Link key={ev.id} href={`/events/${ev.id}`} className="shrink-0 group">
              <div
                className="flex flex-col items-center gap-2 p-3 rounded-xl transition-all"
                style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)", minWidth:76 }}
              >
                <EntityLogo entity={getEntityName(ev.title)} initial={theme.initial} accent={theme.accent}
                  gradFrom={theme.gradFrom} gradMid={theme.gradMid} size={36}/>
                <div className="text-center">
                  <div className="text-[10px] text-slate-400 font-medium truncate max-w-[64px] group-hover:text-white transition-colors">
                    {getEntityName(ev.title)}
                  </div>
                  {price != null && (
                    <div className="text-[9px] text-slate-600 font-mono">{fmt$(price)}</div>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [events,     setEvents]     = useState<any[]>([]);
  const [pastEvents, setPastEvents] = useState<any[]>([]);
  const [summary,    setSummary]    = useState<any>(null);
  const [loading,    setLoading]    = useState(true);
  const [showPast,   setShowPast]   = useState(false);
  const [filter,     setFilter]     = useState<DashFilter>("all");
  const [showHidden, setShowHidden] = useState(false);

  // ── localStorage hooks ────────────────────────────────────────────────────
  const { myEvents, toggle: toggleMyEvent }        = useMyEvents();
  const { heroEventId, setHero, clearHero }         = useHeroEvent();
  const { followed, toggle: toggleFollow }           = useFollowed();
  const { hiddenEvents, hide: hideEvent, unhide }    = useHiddenEvents();

  useEffect(() => {
    Promise.all([
      api.events.list(),
      api.events.list({ include_completed: true }),
      api.analytics.summary(),
    ])
      .then(([evts, allEvts, sum]) => {
        setEvents(evts);
        const activeIds = new Set(evts.map((e:any)=> e.id));
        setPastEvents(allEvts.filter((e:any)=> !activeIds.has(e.id)));
        setSummary(sum);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Filter to events that have at least one non-SeatGeek price signal
  const activeEvents = events.filter((e:any)=> {
    const mp = e.marketplace_prices ?? e.all_marketplace_prices ?? {};
    const hasNonSG = Object.keys(mp).some(k => k !== "seatgeek" && mp[k] != null);
    return hasNonSG || e.is_active !== false;
  });

  // Separate visible and hidden events
  const visibleEvents  = activeEvents.filter((e: any) => !hiddenEvents.has(e.id));
  const hiddenEventList = activeEvents.filter((e: any) => hiddenEvents.has(e.id));

  // Apply quick filter
  const filteredEvents = visibleEvents.filter((e: any) => {
    if (filter === "myevents")  return myEvents.has(e.id);
    if (filter === "following") return followed.has(e.id);
    if (filter === "sports") {
      const n = (e.title || "").toLowerCase();
      return /nfl|nba|mlb|mls|nhl|fifa|soccer|football|basketball|baseball|preseason|chargers|lakers|dodgers|rams|raiders|49ers|angels|clippers/.test(n);
    }
    if (filter === "concerts") {
      const n = (e.title || "").toLowerCase();
      return !/nfl|nba|mlb|mls|nhl|fifa|soccer|football|basketball|baseball|preseason|chargers|lakers|dodgers|rams|raiders|49ers|angels|clippers/.test(n);
    }
    return true;
  });

  const groups = groupEvents(filteredEvents);
  const allGroups = groupEvents(visibleEvents);

  const autoFeaturedEvent = visibleEvents
    .filter((e:any)=> { const d=daysUntil(e.event_date); const p=e.lowest_ask_stubhub??e.marketplace_prices?.tickpick??e.marketplace_prices?.gametime; return d>0 && p!=null; })
    .sort((a:any,b:any)=> new Date(a.event_date).getTime()-new Date(b.event_date).getTime())[0] ?? null;

  const featuredEvent = heroEventId
    ? (visibleEvents.find((e:any) => e.id === heroEventId) ?? autoFeaturedEvent)
    : autoFeaturedEvent;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-5 h-5 border-2 border-[#E50914] border-t-transparent rounded-full animate-spin"/>
          <span className="text-slate-600 text-xs tracking-widest uppercase font-semibold">Loading</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 relative">

      {/* ── Atmospheric background orbs ─────────────────────────────────────── */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
        <div className="atmosphere-orb absolute rounded-full" style={{
          width:700, height:700, top:"-12%", left:"-10%",
          background:"radial-gradient(circle, rgba(229,9,20,0.05) 0%, transparent 65%)",
        }}/>
        <div className="atmosphere-orb-2 absolute rounded-full" style={{
          width:500, height:500, bottom:"5%", right:"-8%",
          background:"radial-gradient(circle, rgba(229,9,20,0.03) 0%, transparent 65%)",
        }}/>
      </div>

      {/* ── Page header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between fade-up">
        <div>
          <div className="section-label mb-2">Live Intelligence</div>
          <h1 className="text-white font-black leading-none"
            style={{ fontSize:"clamp(1.75rem, 3.5vw, 2.5rem)", letterSpacing:"-0.03em" }}>
            My Events
          </h1>
        </div>
        <Link
          href="/events/new"
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-white text-sm font-semibold transition-all duration-200 hover:brightness-115 shrink-0"
          style={{ background:"linear-gradient(135deg, #E50914 0%, #B00010 100%)", boxShadow:"0 4px 20px rgba(229,9,20,0.35)" }}
        >
          <Plus size={14}/>
          <span className="hidden sm:inline">Add Event</span>
          <span className="sm:hidden">Add</span>
        </Link>
      </div>

      {/* ── Market Tape ──────────────────────────────────────────────────────── */}
      {activeEvents.length > 0 && (
        <div className="fade-up-1">
          <MarketTape summary={summary} eventCount={visibleEvents.length} groupCount={allGroups.length}/>
        </div>
      )}

      {/* ── Following Row ────────────────────────────────────────────────────── */}
      {followed.size > 0 && (
        <div className="fade-up-1">
          <FollowingRow events={visibleEvents} followed={followed} onUnfollow={toggleFollow}/>
        </div>
      )}

      {/* ── Featured hero ─────────────────────────────────────────────────────  */}
      {featuredEvent && (
        <div className="fade-up-2">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={13} style={{ color:"#E50914" }}/>
            <span className="section-label">
              {heroEventId && featuredEvent?.id === heroEventId ? "Pinned Hero" : "Featured Event"}
            </span>
          </div>
          <FeaturedHero
            event={featuredEvent}
            onClearHero={heroEventId && featuredEvent?.id === heroEventId ? clearHero : undefined}
          />
        </div>
      )}

      {/* ── Quick filter bar ─────────────────────────────────────────────────── */}
      {activeEvents.length > 0 && (
        <div className="fade-up-2">
          <FilterBar
            active={filter}
            onChange={setFilter}
            myCount={myEvents.size}
            followCount={followed.size}
          />
        </div>
      )}

      {/* ── Empty state ──────────────────────────────────────────────────────── */}
      {groups.length === 0 && activeEvents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-28 gap-5">
          <div className="w-18 h-18 rounded-2xl flex items-center justify-center"
            style={{ background:"rgba(229,9,20,0.07)", border:"1px solid rgba(229,9,20,0.18)" }}>
            <Ticket size={32} style={{ color:"#E50914", opacity:0.45 }}/>
          </div>
          <div className="text-center">
            <p className="text-slate-300 font-semibold text-lg">No events tracked yet</p>
            <p className="text-slate-600 text-sm mt-1.5">Add your first event to start tracking the market</p>
          </div>
          <Link href="/events/new"
            className="px-6 py-2.5 rounded-xl text-white text-sm font-semibold"
            style={{ background:"linear-gradient(135deg, #E50914 0%, #B00010 100%)" }}>
            Get started →
          </Link>
        </div>
      )}

      {/* ── Filter empty state ───────────────────────────────────────────────── */}
      {groups.length === 0 && activeEvents.length > 0 && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <p className="text-slate-500 text-sm">No events match this filter.</p>
          <button onClick={() => setFilter("all")} className="text-xs text-red-500 hover:text-red-400 transition-colors">
            Show all →
          </button>
        </div>
      )}

      {/* ── Entity Groups ────────────────────────────────────────────────────── */}
      {groups.length > 0 && (
        <div className="fade-up-3">
          <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Activity size={13} style={{ color:"#E50914" }}/>
              <span className="section-label">Your Watchlist</span>
              <span className="text-[10px] text-slate-700 font-semibold">{filteredEvents.length} events · {groups.length} entities</span>
            </div>
            {myEvents.size > 0 && (
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <Star size={10} fill="#F59E0B" stroke="#F59E0B"/>
                <span>{myEvents.size} marked as My Event</span>
              </div>
            )}
          </div>
          <div className="space-y-4">
            {groups.map(group => (
              <EntityBlock
                key={group.entity}
                group={group}
                myEvents={myEvents}
                onToggleMyEvent={toggleMyEvent}
                heroEventId={heroEventId}
                onSetHero={setHero}
                onHide={(ids) => ids.forEach(id => hideEvent(id))}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Hidden events strip ──────────────────────────────────────────────── */}
      {hiddenEventList.length > 0 && (
        <div className="section-divider my-2"/>
      )}
      {hiddenEventList.length > 0 && (
        <section>
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowHidden(v => !v)}
              className="flex items-center gap-2 text-[11px] text-slate-700 hover:text-slate-500 transition-colors font-medium"
            >
              <EyeOff size={11}/>
              {hiddenEventList.length} hidden {hiddenEventList.length === 1 ? "event" : "events"}
              <span className="text-[10px]">{showHidden ? "▲" : "▼"}</span>
            </button>
          </div>
          {showHidden && (
            <div className="mt-3 rounded-xl overflow-hidden divide-y divide-white/[0.03]"
              style={{ background:"rgba(255,255,255,0.015)", border:"1px solid rgba(255,255,255,0.05)" }}>
              {hiddenEventList.map((ev: any) => (
                <div key={ev.id} className="flex items-center gap-3 px-4 py-2.5 opacity-40 hover:opacity-70 transition-opacity">
                  <span className="flex-1 text-slate-400 text-xs truncate">{ev.title}</span>
                  <button
                    onClick={() => unhide(ev.id)}
                    className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
                    title="Restore to dashboard"
                  >
                    <Eye size={10}/>
                    Restore
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ── Past Events ──────────────────────────────────────────────────────── */}
      {pastEvents.length > 0 && (
        <section>
          <div className="section-divider my-8"/>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <span className="text-slate-600 font-semibold text-sm">Past Events</span>
              <span className="text-[10px] px-2 py-0.5 rounded text-slate-600 font-semibold"
                style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.07)" }}>
                {pastEvents.length}
              </span>
            </div>
            <button
              onClick={()=> setShowPast(v=>!v)}
              className="text-xs text-slate-700 hover:text-slate-500 transition-colors font-medium"
            >
              {showPast ? "Hide" : "Show"}
            </button>
          </div>

          {showPast && (
            <div className="rounded-xl overflow-hidden divide-y divide-white/[0.04]"
              style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.05)" }}>
              {pastEvents.map(ev => (
                <Link key={ev.id} href={`/events/${ev.id}`}
                  className="flex items-center gap-4 px-4 py-3 hover:bg-white/[0.025] transition-colors opacity-40 hover:opacity-70">
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-300 text-sm truncate">{ev.title}</p>
                    <p className="text-slate-600 text-xs">{fmtVenue(ev.venue_slug)} · {fmtDate(ev.event_date)}</p>
                  </div>
                  <span className="text-slate-700 text-xs shrink-0 capitalize">{ev.status}</span>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
