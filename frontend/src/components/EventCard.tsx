"use client";

import Link from "next/link";
import { EyeOff, Calendar, Clock } from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import type { EventSummary } from "@/lib/types";
import { fmt$$, fmtNum, fmtPct, signalToAction, actionColors, signalPhrase } from "@/lib/utils";
import { getEventGradient, gradientBg } from "@/lib/entityimages";

interface Props {
  event: EventSummary;
  meta?: { title?: string; venue_name?: string; venue_slug?: string; event_date?: string; artist?: string };
  dataDepthDays?: number | null;
  onHide: (id: number) => void;
  isSelected?: boolean;
  onSelect?: (id: number) => void;
}

export default function EventCard({ event, meta, dataDepthDays, onHide, isSelected, onSelect }: Props) {
  const title = meta?.title ?? event.title;
  const venue = meta?.venue_name;
  const venueSlug = meta?.venue_slug;
  const dateStr = meta?.event_date;
  const artist = meta?.artist;
  const INTEL_VENUES = new Set(["sofi-stadium", "crypto-arena", "kia-forum", "hollywood-bowl", "greek-theatre"]);
  const hasVenueIntel = INTEL_VENUES.has(venueSlug ?? "");

  const action = signalToAction(event.signal);
  const colors = actionColors(action);
  const gradient = getEventGradient(artist, title);
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
      className={`group relative rounded-xl border transition-all duration-150 overflow-hidden ${
        isSelected
          ? "border-white/20 shadow-lg"
          : "border-white/7 hover:border-white/14"
      }`}
      style={isSelected ? { boxShadow: `0 0 0 1px ${colors.border}, 0 4px 24px ${colors.glow}` } : undefined}
    >
      {/* Full-card link — wraps both art strip and body */}
      <Link href={`/events/${event.event_id}`} onClick={handleClick} className="block cursor-pointer">
        {/* art strip */}
        <div
          className="h-20 w-full relative"
          style={{ background: gradientBg(gradient, "medium") }}
        >
          {/* action badge */}
          <span
            className="absolute top-2 left-3 text-[10px] font-black tracking-widest px-2 py-0.5 rounded-md border"
            style={{ color: colors.text, background: colors.bg, borderColor: colors.border }}
          >
            {action}
          </span>

          {/* depth chip */}
          {dataDepthDays != null && (
            <span className={`absolute bottom-2 right-2 text-[9px] px-1.5 py-0.5 rounded font-medium ${
              dataDepthDays >= 7 ? "bg-emerald-500/20 text-emerald-500" : "bg-amber-500/20 text-amber-500"
            }`}>
              {dataDepthDays >= 1 ? `${Math.round(dataDepthDays)}d history` : "live only"}
            </span>
          )}
        </div>

        {/* card body */}
        <div className="p-3 bg-[#161b27]">
          <h3 className="text-xs font-semibold text-slate-100 leading-tight truncate mb-0.5">{title}</h3>
          {venue && <p className="text-[10px] text-slate-500 truncate mb-2">{venue}</p>}

          {/* date + days */}
          {dateStr && (
            <div className="flex items-center gap-1.5 mb-2 text-[10px] text-slate-500">
              <Calendar size={9} />
              <span>{dateLabel}</span>
              {daysOut != null && daysOut >= 0 && (
                <>
                  <span className="text-slate-700">·</span>
                  <Clock size={9} />
                  <span>{daysOut === 0 ? "Today" : `${daysOut}d`}</span>
                </>
              )}
            </div>
          )}

          {/* price band — two labeled cells */}
          <div className="grid grid-cols-2 gap-2 mb-1.5">
            <div>
              <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Lowest Price</p>
              <p className="text-xs font-semibold text-slate-200 tabular-nums">{fmt$$(event.price?.low_ask)}</p>
            </div>
            <div>
              <p className="text-[9px] text-slate-600 uppercase tracking-wide mb-0.5">Median Price</p>
              <p className="text-xs font-semibold text-slate-300 tabular-nums">{fmt$$(event.price?.median_ask)}</p>
            </div>
          </div>

          {/* price movement phrase + 24h delta */}
          <div className="flex items-center justify-between text-[10px] mt-0.5">
            <span className={
              phrase.dir === "up" ? "text-emerald-600 font-medium" :
              phrase.dir === "down" ? "text-red-600 font-medium" :
              "text-slate-600"
            }>{phrase.text}</span>
            {event.history_hours != null ? (
              <span className={
                (event.changes?.h24?.price_delta_pct ?? 0) > 0 ? "text-emerald-500 tabular-nums font-medium" :
                (event.changes?.h24?.price_delta_pct ?? 0) < 0 ? "text-red-500 tabular-nums font-medium" :
                "text-slate-500 tabular-nums"
              }>
                {event.changes?.h24?.price_delta_pct != null
                  ? fmtPct(event.changes.h24.price_delta_pct) + " 24h"
                  : "—"}
              </span>
            ) : (
              <span className="text-slate-600 tabular-nums text-[9px]">Collecting</span>
            )}
          </div>

          {/* Venue intelligence chip */}
          {hasVenueIntel && (
            <div className="mt-2 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
              <span className="text-[9px] text-emerald-600 font-medium">Venue Intel available</span>
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
