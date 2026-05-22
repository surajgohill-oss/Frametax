"use client";
import Link from "next/link";
import { MapPin, CalendarDays } from "lucide-react";
import { fmt$, fmtDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { deriveEventState } from "@/lib/types";
import type { EventCardInput, EventState } from "@/lib/types";

interface Props {
  event: EventCardInput;
  followed: boolean;
  onFollowToggle: (id: number) => void;
}

const STATE_BORDER: Record<EventState, string> = {
  POPULATED: "border-emerald-500/50",
  PARTIAL:   "border-yellow-500/50",
  EMPTY:     "border-slate-600",
  BLOCKED:   "border-red-500/50",
};

const STATE_BADGE: Record<EventState, { label: string; variant: "green" | "yellow" | "secondary" | "red" }> = {
  POPULATED: { label: "LIVE",        variant: "green" },
  PARTIAL:   { label: "LIMITED",     variant: "yellow" },
  EMPTY:     { label: "NO DATA",     variant: "secondary" },
  BLOCKED:   { label: "UNAVAILABLE", variant: "red" },
};

const STATE_PRICE_COLOR: Record<EventState, string> = {
  POPULATED: "text-white",
  PARTIAL:   "text-yellow-400",
  EMPTY:     "text-slate-500",
  BLOCKED:   "text-slate-500",
};

export function EventCard({ event, followed, onFollowToggle }: Props) {
  const state = deriveEventState(event);
  const lowestAsk = event.lowest_price ??
    Math.min(event.lowest_ask_stubhub ?? Infinity, event.lowest_ask_seatgeek ?? Infinity);
  const hasPrice = isFinite(lowestAsk);
  const { label: badgeLabel, variant: badgeVariant } = STATE_BADGE[state];

  return (
    <div
      data-testid="event-card"
      data-event-id={event.id}
      data-canonical-id={event.canonical_id}
      data-state={state}
      className={`bg-[#161b27] border ${STATE_BORDER[state]} rounded-xl overflow-hidden hover:border-blue-500/40 transition-colors`}
    >
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-base font-bold text-white leading-snug truncate">{event.title}</h3>
              <Badge variant={badgeVariant} className="shrink-0 text-[10px] px-1.5 py-0">{badgeLabel}</Badge>
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <MapPin size={12} className="shrink-0" />
                {event.venue_name || event.venue_slug}
              </span>
              <span className="flex items-center gap-1">
                <CalendarDays size={12} className="shrink-0" />
                {fmtDate(event.event_date)}
              </span>
            </div>
          </div>
          <button
            onClick={(e) => { e.preventDefault(); onFollowToggle(event.id); }}
            className={`shrink-0 text-xs px-3 py-1.5 rounded-full border transition-colors ${
              followed
                ? "border-blue-500 bg-blue-500/10 text-blue-400"
                : "border-[#2a3145] text-slate-500 hover:border-slate-400 hover:text-slate-300"
            }`}
          >
            {followed ? "Following" : "Follow"}
          </button>
        </div>
        <p className="mt-3 text-sm text-slate-400">
          {hasPrice
            ? <>From <span className={`font-semibold text-base ${STATE_PRICE_COLOR[state]}`}>{fmt$(lowestAsk)}</span></>
            : <span className="text-slate-500 italic">No listings</span>
          }
        </p>
      </div>
      <div className="px-5 pb-5">
        <Link
          href={`/events/${event.id}`}
          className="block w-full text-center py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          View Event
        </Link>
      </div>
    </div>
  );
}
