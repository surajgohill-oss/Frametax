"use client";

import Link from "next/link";
import { EyeOff, Calendar, Clock } from "lucide-react";
import { format, parseISO, differenceInDays } from "date-fns";
import type { EventSummary } from "@/lib/types";
import { fmt$$, fmtNum, signalToAction, actionColors } from "@/lib/utils";
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
  const isSoFi = venueSlug === "sofi-stadium";

  const action = signalToAction(event.signal);
  const colors = actionColors(action);
  const gradient = getEventGradient(artist, title);

  let daysOut: number | null = null;
  let dateLabel = "";
  if (dateStr) {
    try {
      const d = parseISO(dateStr);
      daysOut = differenceInDays(d, new Date());
      dateLabel = format(d, "EEE MMM d");
    } catch {}
  }

  function handleClick(e: React.MouseEvent) {
    if (onSelect) {
      e.preventDefault();
      onSelect(event.event_id);
    }
  }

  return (
    <div
      className={`group relative rounded-xl border transition-all duration-150 overflow-hidden cursor-pointer ${
        isSelected
          ? "border-white/20 shadow-lg"
          : "border-white/7 hover:border-white/14"
      }`}
      style={isSelected ? { boxShadow: `0 0 0 1px ${colors.border}, 0 4px 24px ${colors.glow}` } : undefined}
    >
      {/* art strip */}
      <div
        className="h-16 w-full relative"
        style={{ background: gradientBg(gradient, "medium") }}
      >
        {/* action badge */}
        <span
          className="absolute top-2 left-3 text-[10px] font-black tracking-widest px-2 py-0.5 rounded-md border"
          style={{ color: colors.text, background: colors.bg, borderColor: colors.border }}
        >
          {action}
        </span>

        {/* hide button */}
        <button
          onClick={(e) => { e.stopPropagation(); e.preventDefault(); onHide(event.event_id); }}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-black/40 text-slate-400 hover:text-white"
        >
          <EyeOff size={11} />
        </button>

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
      <Link href={`/events/${event.event_id}`} onClick={handleClick} className="block p-3 bg-[#161b27]">
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

        {/* price band */}
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-slate-500">
            <span className="text-slate-300 font-medium">{fmt$$(event.price?.low_ask)}</span>
            {" – "}
            <span className="text-slate-400">{fmt$$(event.price?.median_ask)}</span>
          </span>
          <span className="text-slate-600 tabular-nums">{fmtNum(event.inventory?.total_listings)} listings</span>
        </div>

        {/* SoFi venue intelligence chip */}
        {isSoFi && (
          <div className="mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
            <span className="text-[9px] text-emerald-600 font-medium">Venue Intel available</span>
          </div>
        )}
      </Link>
    </div>
  );
}
