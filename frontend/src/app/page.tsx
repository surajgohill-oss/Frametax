"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { fmtDate, fmt$ } from "@/lib/utils";
import { getEntityImage } from "@/lib/entityImages";
import { EntityLogo } from "@/components/ui/EntityLogo";
import { Plus, Calendar, TrendingUp, Activity, ChevronRight, Ticket } from "lucide-react";

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
    const prices = evs.map((e:any)=> e.lowest_ask_stubhub ?? e.lowest_ask_tickpick).filter(Boolean) as number[];
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
          <div className="text-[9px] font-bold uppercase tracking-widest mt-1.5" style={{ color:"#2a2a2a" }}>{label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Featured Hero ──────────────────────────────────────────────────────────────

function FeaturedHero({ event }: { event: any }) {
  const theme  = getEntityTheme(getEntityName(event.title));
  const price  = event.lowest_ask_stubhub ?? event.lowest_ask_tickpick;
  const status = getMarketStatus(price);
  const days   = daysUntil(event.event_date);
  const venue  = fmtVenue(event.venue_slug);
  const entity = getEntityName(event.title);
  const subtitle = event.title !== entity ? event.title.replace(entity,"").replace(/^[\s·–—]/,"").trim() : "";
  const isValue  = price != null && price < 100;

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

        {/* === Layer 6: Large watermark initial === */}
        <div
          className="absolute right-0 top-0 bottom-0 flex items-center pr-8 select-none pointer-events-none"
          style={{
            fontSize:"clamp(140px, 22vw, 260px)", fontWeight:900,
            color:`rgba(${theme.accentRgb}, 0.05)`,
            WebkitTextStrokeWidth:"1.5px",
            WebkitTextStrokeColor:`rgba(${theme.accentRgb}, 0.085)`,
            lineHeight:1, letterSpacing:"-0.06em",
          }}
        >
          {theme.initial}
        </div>

        {/* Content */}
        <div className="relative z-10 p-8 sm:p-10 flex flex-col justify-between h-full" style={{ minHeight:340 }}>
          {/* Top row: logo + chips + days */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <EntityLogo entity={entity} initial={theme.initial} accent={theme.accent}
                gradFrom={theme.gradFrom} gradMid={theme.gradMid} size={44} />
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
              {event.total_listings > 0 && (
                <div className="pb-0.5">
                  <div className="text-white/50 font-bold text-xl" style={{ letterSpacing:"-0.02em" }}>
                    {event.total_listings.toLocaleString()}
                  </div>
                  <div className="stat-label">Listings</div>
                </div>
              )}
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

function EventRow({ ev, theme }: { ev: any; theme: EntityTheme }) {
  const price  = ev.lowest_ask_stubhub ?? ev.lowest_ask_tickpick;
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
      {/* Date column */}
      <div className="w-14 shrink-0">
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

      {/* Listings — hidden on small screens */}
      <div className="w-16 shrink-0 text-right hidden lg:block">
        <div className="text-[11px] text-slate-700">
          {ev.total_listings ? ev.total_listings.toLocaleString() : "—"}
        </div>
      </div>

      {/* Price */}
      <div className="w-18 shrink-0 text-right pl-3">
        <div
          className="text-[15px] font-bold leading-none"
          style={{ letterSpacing:"-0.03em", color: isValue ? "#22c55e" : "#fff" }}
        >
          {price != null ? fmt$(price) : "—"}
        </div>
      </div>

      {/* Badge */}
      <div className="w-16 shrink-0 text-right pl-2">
        {price != null && (
          <span className={`text-[9px] font-bold px-2 py-1 rounded-md ${status.cssClass}`}>
            {status.label}
          </span>
        )}
      </div>
    </Link>
  );
}

// ── Entity Block ───────────────────────────────────────────────────────────────

function EntityBlock({ group }: { group: EventGroup }) {
  const { entity, theme, events, minPrice, totalListings } = group;
  const status    = getMarketStatus(minPrice);
  const nextEvent = events[0];
  const days      = nextEvent ? daysUntil(nextEvent.event_date) : null;
  const isValue   = minPrice != null && minPrice < 100;
  const isHot     = minPrice != null && minPrice >= 100 && minPrice < 150;

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

      {/* Entity header */}
      <div
        className="flex items-center gap-4 pl-6 pr-5 py-4"
        style={{ borderBottom:"1px solid rgba(255,255,255,0.04)" }}
      >
        <EntityLogo
          entity={entity} initial={theme.initial} accent={theme.accent}
          gradFrom={theme.gradFrom} gradMid={theme.gradMid} size={40}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5">
            <h2 className="text-white font-bold text-[15px] leading-none" style={{ letterSpacing:"-0.02em" }}>
              {entity}
            </h2>
            <span
              className="text-[9px] font-bold tracking-[0.16em] px-2 py-0.5 rounded"
              style={{ background:theme.accentDim, color:theme.accent }}
            >
              {theme.category}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1.5">
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
          </div>
        </div>

        {/* Status pill */}
        {minPrice != null && (
          <span className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg shrink-0 ${status.cssClass}`}>
            {status.emoji} {status.label}
          </span>
        )}
      </div>

      {/* Event rows — the table */}
      <div>
        {/* Column header — subtle */}
        <div
          className="flex items-center px-5 py-1.5"
          style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}
        >
          <div className="w-14 shrink-0 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Date</div>
          <div className="flex-1 px-3 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Event</div>
          <div className="w-16 shrink-0 text-right hidden lg:block text-[9px] text-slate-800 uppercase tracking-wider font-bold">Listings</div>
          <div className="w-18 shrink-0 text-right pl-3 text-[9px] text-slate-800 uppercase tracking-wider font-bold">Price</div>
          <div className="w-16 shrink-0" />
        </div>
        {events.map((ev, i) => (
          <EventRow
            key={ev.id}
            ev={ev}
            theme={theme}
          />
        ))}
      </div>

      {/* Market insight footer — only shown when there's a real signal */}
      {isValue && (
        <div
          className="flex items-center gap-3 pl-6 pr-5 py-2.5"
          style={{
            background:"rgba(34,197,94,0.03)",
            borderTop:"1px solid rgba(34,197,94,0.1)",
          }}
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
          style={{
            background:"rgba(249,115,22,0.03)",
            borderTop:"1px solid rgba(249,115,22,0.08)",
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background:"#f97316" }}/>
          <span className="text-[11px] text-slate-600">
            <span className="text-orange-400/80 font-semibold">Watch</span> — market active, price may move before event
          </span>
        </div>
      )}
    </section>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [events,     setEvents]     = useState<any[]>([]);
  const [pastEvents, setPastEvents] = useState<any[]>([]);
  const [summary,    setSummary]    = useState<any>(null);
  const [loading,    setLoading]    = useState(true);
  const [showPast,   setShowPast]   = useState(false);

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

  const activeEvents = events.filter((e:any)=> {
    const te:any[] = e.tracked_events ?? [];
    return te.some((t:any)=> t.marketplace_slug !== "seatgeek" && t.is_active === true);
  });

  const groups = groupEvents(activeEvents);

  const featuredEvent = activeEvents
    .filter((e:any)=> { const d=daysUntil(e.event_date); const p=e.lowest_ask_stubhub??e.lowest_ask_tickpick; return d>0 && p!=null; })
    .sort((a:any,b:any)=> new Date(a.event_date).getTime()-new Date(b.event_date).getTime())[0] ?? null;

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
          <MarketTape summary={summary} eventCount={activeEvents.length} groupCount={groups.length}/>
        </div>
      )}

      {/* ── Featured hero ─────────────────────────────────────────────────────  */}
      {featuredEvent && (
        <div className="fade-up-2">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={13} style={{ color:"#E50914" }}/>
            <span className="section-label">Featured Event</span>
          </div>
          <FeaturedHero event={featuredEvent}/>
        </div>
      )}

      {/* ── Empty state ──────────────────────────────────────────────────────── */}
      {groups.length === 0 && (
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

      {/* ── Entity Groups — Concept C entity blocks ──────────────────────────── */}
      {groups.length > 0 && (
        <div className="fade-up-3">
          <div className="flex items-center gap-2 mb-5">
            <Activity size={13} style={{ color:"#E50914" }}/>
            <span className="section-label">Your Watchlist</span>
          </div>
          <div className="space-y-4">
            {groups.map(group => (
              <EntityBlock key={group.entity} group={group}/>
            ))}
          </div>
        </div>
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
