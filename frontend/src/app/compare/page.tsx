'use client';
import { useState, useEffect } from 'react';
import { api, TrackedEvent } from '@/lib/api';
import { formatCurrency, formatRelativeTime } from '@/lib/utils';
import { Card } from '@/components/ui/Card';

interface CompareRow {
  event: TrackedEvent;
  stubhubLow: number | null;
  seatgeekLow: number | null;
  diff: number | null;
  cheaperOn: 'stubhub' | 'seatgeek' | 'equal' | null;
}

export default function ComparePage() {
  const [rows, setRows] = useState<CompareRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'diff' | 'stubhub' | 'seatgeek'>('diff');

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const events = await api.getEvents();
      const results = await Promise.all(
        events.map(async (event) => {
          const listings = await api.getListings(event.id);
          const stubhub = listings.filter(l => l.marketplace_slug === 'stubhub');
          const seatgeek = listings.filter(l => l.marketplace_slug === 'seatgeek');
          const stubhubLow = stubhub.length > 0 ? Math.min(...stubhub.map(l => l.price_each)) : null;
          const seatgeekLow = seatgeek.length > 0 ? Math.min(...seatgeek.map(l => l.price_each)) : null;
          let diff: number | null = null;
          let cheaperOn: CompareRow['cheaperOn'] = null;
          if (stubhubLow != null && seatgeekLow != null) {
            diff = Math.abs(stubhubLow - seatgeekLow);
            if (stubhubLow < seatgeekLow) cheaperOn = 'stubhub';
            else if (seatgeekLow < stubhubLow) cheaperOn = 'seatgeek';
            else cheaperOn = 'equal';
          }
          return { event, stubhubLow, seatgeekLow, diff, cheaperOn };
        })
      );
      setRows(results);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const sorted = [...rows].sort((a, b) => {
    if (sortBy === 'diff') return (b.diff ?? -1) - (a.diff ?? -1);
    if (sortBy === 'stubhub') return (a.stubhubLow ?? Infinity) - (b.stubhubLow ?? Infinity);
    return (a.seatgeekLow ?? Infinity) - (b.seatgeekLow ?? Infinity);
  });

  const savingsTotal = rows.reduce((acc, r) => {
    if (r.diff != null) acc += r.diff;
    return acc;
  }, 0);

  const stubhubWins = rows.filter(r => r.cheaperOn === 'stubhub').length;
  const seatgeekWins = rows.filter(r => r.cheaperOn === 'seatgeek').length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Marketplace Comparison</h1>
        <p className="text-gray-400 mt-1">StubHub vs SeatGeek lowest ask across your watchlist</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-xs text-gray-400 mb-1">Avg Price Difference</p>
          <p className="text-xl font-bold text-yellow-400">
            {rows.length > 0 ? formatCurrency(savingsTotal / rows.filter(r => r.diff != null).length || 0) : '—'}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">StubHub Cheaper</p>
          <p className="text-xl font-bold text-indigo-400">{stubhubWins} events</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">SeatGeek Cheaper</p>
          <p className="text-xl font-bold text-blue-400">{seatgeekWins} events</p>
        </Card>
      </div>

      <div className="flex gap-2 items-center">
        <span className="text-sm text-gray-400">Sort by:</span>
        {(['diff', 'stubhub', 'seatgeek'] as const).map(s => (
          <button
            key={s}
            onClick={() => setSortBy(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              sortBy === s ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {s === 'diff' ? 'Price Diff' : s === 'stubhub' ? 'StubHub Low' : 'SeatGeek Low'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Event</th>
                <th className="px-4 py-3 text-right text-gray-400 font-medium">StubHub</th>
                <th className="px-4 py-3 text-right text-gray-400 font-medium">SeatGeek</th>
                <th className="px-4 py-3 text-right text-gray-400 font-medium">Difference</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Cheaper On</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Last Polled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {sorted.map(({ event, stubhubLow, seatgeekLow, diff, cheaperOn }) => (
                <tr key={event.id} className="hover:bg-gray-750 transition-colors">
                  <td className="px-4 py-3">
                    <a href={`/events/${event.id}`} className="text-white hover:text-indigo-300">
                      {event.event?.title || `Event #${event.id}`}
                    </a>
                    <p className="text-xs text-gray-500">{event.event?.venue_name}</p>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={cheaperOn === 'stubhub' ? 'text-green-400 font-bold' : 'text-gray-300'}>
                      {stubhubLow != null ? formatCurrency(stubhubLow) : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={cheaperOn === 'seatgeek' ? 'text-green-400 font-bold' : 'text-gray-300'}>
                      {seatgeekLow != null ? formatCurrency(seatgeekLow) : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {diff != null ? (
                      <span className="text-yellow-400">{formatCurrency(diff)}</span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {cheaperOn ? (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        cheaperOn === 'stubhub' ? 'bg-indigo-900 text-indigo-300' :
                        cheaperOn === 'seatgeek' ? 'bg-blue-900 text-blue-300' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {cheaperOn}
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {event.last_polled_at ? formatRelativeTime(event.last_polled_at) : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {sorted.length === 0 && (
            <p className="text-center py-8 text-gray-400">No events in watchlist. Add some events first.</p>
          )}
        </div>
      )}
    </div>
  );
}
