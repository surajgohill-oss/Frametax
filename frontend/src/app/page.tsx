"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { EventCard } from "@/components/EventCard";
import { useFollowed } from "@/hooks/useFollowed";
import type { Event } from "@/lib/types";

function daysUntil(isoDate: string) {
  return Math.floor((new Date(isoDate).getTime() - Date.now()) / 86_400_000);
}

function sectionize(events: Event[], followed: Set<number>) {
  const assigned = new Set<number>();
  const tonight: any[] = [];
  const mustWatch: any[] = [];
  const yourEvents: any[] = [];
  const comingUp: any[] = [];

  for (const ev of events) {
    const d = daysUntil(ev.event_date);
    if (d === 0) { tonight.push(ev); assigned.add(ev.id); }
  }
  for (const ev of events) {
    if (assigned.has(ev.id)) continue;
    if (daysUntil(ev.event_date) <= 30) { mustWatch.push(ev); assigned.add(ev.id); }
  }
  for (const ev of events) {
    if (assigned.has(ev.id)) continue;
    if (followed.has(ev.id)) { yourEvents.push(ev); assigned.add(ev.id); }
  }
  for (const ev of events) {
    if (!assigned.has(ev.id)) comingUp.push(ev);
  }

  return { tonight, mustWatch, yourEvents, comingUp };
}

interface SectionProps {
  title: string;
  events: Event[];
  followed: Set<number>;
  onFollowToggle: (id: number) => void;
  emptyMessage?: string;
}

function FeedSection({ title, events, followed, onFollowToggle, emptyMessage }: SectionProps) {
  if (events.length === 0 && !emptyMessage) return null;
  return (
    <section>
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">{title}</h2>
      {events.length === 0 ? (
        <p className="text-sm text-slate-600 italic">{emptyMessage}</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {events.map((ev) => (
            <EventCard
              key={ev.id}
              event={ev}
              followed={followed.has(ev.id)}
              onFollowToggle={onFollowToggle}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function FeedPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const { followed, toggle } = useFollowed();

  useEffect(() => {
    api.events.list()
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-slate-500">Loading…</div>;
  }

  const { tonight, mustWatch, yourEvents, comingUp } = sectionize(events, followed);

  return (
    <div className="space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Events</h1>
          <p className="text-slate-400 text-sm mt-1">Your LA concert watchlist</p>
        </div>
        <Link
          href="/events/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
        >
          <Plus size={15} /> Add Event
        </Link>
      </div>

      {events.length === 0 ? (
        <div className="text-center py-24 text-slate-500">
          <p className="mb-3">No events tracked yet.</p>
          <Link href="/events/new" className="text-blue-400 hover:text-blue-300 text-sm">
            Add your first event →
          </Link>
        </div>
      ) : (
        <>
          <FeedSection
            title="Tonight"
            events={tonight}
            followed={followed}
            onFollowToggle={toggle}
          />
          <FeedSection
            title="Must Watch"
            events={mustWatch}
            followed={followed}
            onFollowToggle={toggle}
          />
          <FeedSection
            title="Your Events"
            events={yourEvents}
            followed={followed}
            onFollowToggle={toggle}
            emptyMessage="Follow an event to see it here."
          />
          <FeedSection
            title="Coming Up"
            events={comingUp}
            followed={followed}
            onFollowToggle={toggle}
          />
        </>
      )}
    </div>
  );
}
