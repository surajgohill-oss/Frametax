'use client';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import VenueHeatmap from '@/components/venue/VenueHeatmap';

export default function HeatmapPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [mode, setMode] = useState<'price' | 'inventory'>('price');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.events.list().then(data => {
      setEvents(data);
      if (data.length > 0) setSelectedEventId(data[0].id);
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedEventId) {
      api.listings.byEvent(selectedEventId).then(setListings);
    }
  }, [selectedEventId]);

  const selectedEvent = events.find((e: any) => e.id === selectedEventId);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Venue Heatmap</h1>
        <p className="text-gray-400 mt-1">Visual seat price and inventory map</p>
      </div>

      <div className="flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Event</label>
          <select
            value={selectedEventId ?? ''}
            onChange={e => setSelectedEventId(Number(e.target.value))}
            className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm min-w-[280px]"
          >
            {events.map((event: any) => (
              <option key={event.id} value={event.id}>
                {event.title || `Event #${event.id}`}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Color Mode</label>
          <div className="flex rounded-lg overflow-hidden border border-gray-600">
            {(['price', 'inventory'] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-4 py-2 text-sm capitalize ${
                  mode === m ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
        </div>
      ) : selectedEvent?.venue_slug ? (
        <VenueHeatmap venueSlug={selectedEvent.venue_slug} listings={listings} mode={mode} />
      ) : (
        <div className="text-center py-16 text-gray-400">
          {events.length === 0 ? 'Add events to your watchlist first.' : 'Select an event to view its heatmap.'}
        </div>
      )}
    </div>
  );
}
