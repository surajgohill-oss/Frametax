"use client";

import Link from "next/link";
import { EyeOff, Calendar, Clock } from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import type { EventSummary } from "@/lib/types";
import { fmt$$, fmtNum, fmtPct, signalToAction, actionColors, signalPhrase } from "@/lib/utils";
import { getEventGradient, gradientBg } from "@/lib/entityimages";
import { venueCity } from "@/lib/venueGeo";
import { useArtistImage } from "@/hooks/useArtistImage";

interface Props {
  event: EventSummary;
  meta?: { title?: string; venue_name?: string; venue_slug?: string; event_date?: string; artist?: string };
  dataDepthDays?: number | null;
  onHide: (id: number) => void;
  isSelected?: boolean;
  onSelect?: (id: number) => void;
  /** Derived matchup context for sports events, e.g. "Seattle Seahawks" (away game) */
  opponent?: string | null;
}

export default function EventCard({ event, meta, dataDepthDays, onHide, isSelected, onSelect, opponent }: Props) {
  const title = event.title;
  const venue = event.venue_name ?? meta?.venue_name;
  const venueSlug = event.venue_slug ?? meta?.venue_slug;
  const dateStr = event.event_date ?? meta?.event_date;
  const artist = event.artist ?? meta?.artist;
  const INTEL_VENUES = new Set(["sofi-stadium", "crypto-arena", "kia-forum", "hollywood-bowl", "greek-theatre"]);
  const hasVenueIntel = INTEL_VENUES.has(venueSlug ?? "");

  const action = signalToAction(event.signal);
  const colors = actionColors(action);
  const gradient = getEventGradient(artist, title);
  const artworkUrl = useArtistImage(artist, title);
  const phrase = signalPhrase(event.signal);

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseISO(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEE MMM d");
    } catch {}
  }

  // Update selected headline — do NOT preventDefault so the Link navigation fires
  function handleClick() {
    if (onSelect) onSelect(event.event_id);
  }

  return (
    <div
      className={`group relative rounded-xl border transition-all duration-200 overflow-hidden ${
        isSelected
          ? "border-white/20"
          : "border-white/8 hover:border-white/16 hover:shadow-xl"
      }`}
      style={isSelected
        ? { boxShadow: `0 0 0 1px ${colors.border}, 0 8px 32px ${colors.glow}` }
        : { boxShadow: "0 2px 12px rgba(0,0,0,0.4)" }}
    >
      {/* Full-card link — wraps both art strip and body */}
      <Link href={`/events/${event.event_id}`} onClick={handleClick} className="block cursor-pointer">
        {/* art strip */}
        <div
          className="h-32 w-full relative overflow-hidden"
          style={{ background: gradientBg(gradient, artworkUrl ? "low" : "high") }}
        >
          {/* real artwork image — covers gradient when available */}
          {artworkUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={artworkUrl}
              alt=""
              className="absolute inset-0 w-full h-full object-cover object-top opacity-65"
              loading="lazy"
              onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          )}
          {/* vignette — heavier at bottom for text legibility */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/15 to-transparent" />

          {/* signal badge */}
          <span
            className="absolute top-2.5 left-3 text-[10px] font-black tracking-widest px-2 py-0.5 rounded border backdrop-blur-sm"
            style={{ color: colors.text, background: colors.bg + "cc", borderColor: colors.border + "80" }}
          >
            {action}
          </span>

          {/* artist name — bottom-left of art strip */}
          {artist && (
            <span className="absolute bottom-2.5 left-3 text-[11px] font-semibold text-white/75 uppercase tracking-widest truncate max-w-[65%] drop-shadow">
              {artist}
            </span>
          )}

          {/* depth chip */}
          {dataDepthDays != null && (
            <span className={`absolute top-2.5 right-2.5 text-[9px] px-1.5 py-0.5 rounded font-semibold backdrop-blur-sm ${
              dataDepthDays >= 7 ? "bg-emerald-500/25 text-emerald-400 border border-emerald-500/30" : "bg-amber-500/25 text-amber-400 border border-amber-500/30"
            }`}>
              {dataDepthDays >= 1 ? `${Math.round(dataDepthDays)}d` : "live"}
            </span>
          )}
        </div>

        {/* card body */}
        <div className="p-4 bg-[#161b27]">
          <h3 className="text-[13px] font-bold text-white leading-tight truncate mb-0.5">
            {title}
            {opponent && <span className="text-white/60 font-semibold"> at {opponent}</span>}
          </h3>
          {venue && (
            <p className="text-[11px] text-slate-500 truncate mb-2">
              {venue}
              {venueCity(venueSlug) && <span className="text-slate-600"> · {venueCity(venueSlug)}</span>}
            </p>
          )}

          {/* date + days */}
          {dateStr && (
            <div className="flex items-center gap-1.5 mb-3 text-[11px] text-slate-500">
              <Calendar size={9} className="flex-shrink-0" />
              <span>{dateLabel}</span>
              {daysOut != null && daysOut >= 0 && (
                <>
                  <span className="text-slate-700">·</span>
                  <span className={daysOut <= 3 ? "text-amber-400/80 font-semibold" : "text-slate-600"}>
                    {daysOut === 0 ? "Today" : `${daysOut}d`}
                  </span>
                </>
              )}
            </div>
          )}

          {/* price grid — 3 cells */}
          <div className="grid grid-cols-3 gap-1.5 mb-3">
            <div className="bg-black/20 rounded-lg px-2.5 py-2 border border-white/5">
              <p className="text-[9px] text-slate-600 uppercase tracking-wide font-medium mb-0.5">Low</p>
              <p className="text-[14px] font-bold text-emerald-300 tabular-nums leading-none">{fmt$$(event.price?.low_ask) ?? "—"}</p>
            </div>
            <div className="bg-black/20 rounded-lg px-2.5 py-2 border border-white/5">
              <p className="text-[9px] text-slate-600 uppercase tracking-wide font-medium mb-0.5">Median</p>
              <p className="text-[13px] font-semibold text-white/75 tabular-nums leading-none">{fmt$$(event.price?.median_ask) ?? "—"}</p>
            </div>
            <div className="bg-black/20 rounded-lg px-2.5 py-2 border border-white/5">
              <p className="text-[9px] text-slate-600 uppercase tracking-wide font-medium mb-0.5">Inv</p>
              <p className="text-[13px] font-semibold text-blue-300/70 tabular-nums leading-none">{fmtNum(event.inventory?.total_listings) ?? "—"}</p>
            </div>
          </div>

          {/* change indicators */}
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-medium ${
              // Buyer perspective: rising prices are bad (red), falling good (green)
              phrase.dir === "up" ? "text-red-500" :
              phrase.dir === "down" ? "text-emerald-500" :
              "text-slate-600"
            }`}>{phrase.text}</span>
            {event.history_hours != null ? (
              <div className="flex items-center gap-2">
                {/* Buyer perspective (matches DeltaChip invert): price DOWN = green, UP = red */}
                {event.changes?.first_tracked?.price_delta_pct != null && (
                  <span className={`tabular-nums font-bold text-[11px] ${
                    event.changes.first_tracked.price_delta_pct < 0 ? "text-emerald-400" :
                    event.changes.first_tracked.price_delta_pct > 0 ? "text-red-400" :
                    "text-slate-500"
                  }`}>
                    {fmtPct(event.changes.first_tracked.price_delta_pct)}
                    <span className="text-[9px] text-slate-600 font-normal ml-0.5">tracked</span>
                  </span>
                )}
                <span className={`tabular-nums text-[10px] font-medium ${
                  (event.changes?.h24?.price_delta_pct ?? 0) < 0 ? "text-emerald-500" :
                  (event.changes?.h24?.price_delta_pct ?? 0) > 0 ? "text-red-500" :
                  "text-slate-600"
                }`}>
                  {event.changes?.h24?.price_delta_pct != null
                    ? fmtPct(event.changes.h24.price_delta_pct) + " 24h"
                    : "—"}
                </span>
              </div>
            ) : (
              <span className="text-slate-600 text-[10px]">Collecting</span>
            )}
          </div>

          {/* Venue intelligence chip */}
          {hasVenueIntel && (
            <div className="mt-2.5 flex items-center gap-1.5 pt-2.5 border-t border-white/5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/80 flex-shrink-0" />
              <span className="text-[10px] text-emerald-500/80 font-medium">Venue Intel</span>
            </div>
          )}
        </div>
      </Link>

      {/* Hide button — outside Link so its click does not trigger navigation */}
      <button
        onClick={(e) => { e.stopPropagation(); e.preventDefault(); onHide(event.event_id); }}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-black/40 text-slate-400 hover:text-white"
      >
        <EyeOff size={11} />
      </button>
    </div>
  );
}
