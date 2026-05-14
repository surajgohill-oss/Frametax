'use client';
import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { api, TrackedEvent, Listing } from '@/lib/api';
import { formatCurrency, formatDateTime, formatRelativeTime } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import VenueHeatmap from '@/components/VenueHeatmap';
import PriceHistoryChart from '@/components/PriceHistoryChart';
import SectionPriceBar from '@/components/SectionPriceBar';
import InventoryChart from '@/components/InventoryChart';

type Tab = 'overview' | 'heatmap' | 'history';

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params.id);

  const [event, setEvent] = useState<TrackedEvent | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [pollLoading, setPollLoading] = useState(false);
  const [marketplace, setMarketplace] = useState<string>('all');

  useEffect(() => {
    loadEvent();
  }, [eventId]);

  useEffect(() => {
    if (event) loadListings();
  }, [event, marketplace]);

  async function loadEvent() {
    try {
      const data = await api.getEvent(eventId);
      setEvent(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadListings() {
    try {
      const mp = marketplace === 'all' ? undefined : marketplace;
      const data = await api.getListings(eventId, mp);
      setListings(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function triggerPoll() {
    if (!event) return;
    setPollLoading(true);
    try {
      await api.triggerPoll(event.id);
      await new Promise(r => setTimeout(r, 3000));
      await loadEvent();
      await loadListings();
    } finally {
      setPollLoading(false);
    }
  }

  async function toggleActive() {
    if (!event) return;
    await api.updateEvent(event.id, { is_active: !event.is_active });
    await loadEvent();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 mb-4">Event not found</p>
        <button onClick={() => router.back()} className="text-indigo-400 hover:text-indigo-300">Go back</button>
      </div>
    );
  }

  const stubhubListings = listings.filter(l => l.marketplace_slug === 'stubhub');
  const seatgeekListings = listings.filter(l => l.marketplace_slug === 'seatgeek');
  const lowestStubhub = stubhubListings.length > 0 ? Math.min(...stubhubListings.map(l => l.price_each)) : null;
  const lowestSeatgeek = seatgeekListings.length > 0 ? Math.min(...seatgeekListings.map(l => l.price_each)) : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => router.back()} className="text-sm text-gray-400 hover:text-white mb-2 flex items-center gap-1">
            ← Back to events
          </button>
          <h1 className="text-2xl font-bold text-white">{event.event?.title || 'Unnamed Event'}</h1>
          <p className="text-gray-400 mt-1">
            {event.event?.venue_name} &bull; {event.event?.event_date ? formatDateTime(event.event.event_date) : 'Date TBD'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={triggerPoll}
            disabled={pollLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {pollLoading ? 'Polling...' : 'Poll Now'}
          </button>
          <button
            onClick={toggleActive}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              event.is_active
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-green-700 hover:bg-green-600 text-white'
            }`}
          >
            {event.is_active ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-xs text-gray-400 mb-1">StubHub Low</p>
          <p className="text-xl font-bold text-green-400">
            {lowestStubhub != null ? formatCurrency(lowestStubhub) : '—'}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">SeatGeek Low</p>
          <p className="text-xl font-bold text-blue-400">
            {lowestSeatgeek != null ? formatCurrency(lowestSeatgeek) : '—'}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">Total Listings</p>
          <p className="text-xl font-bold text-white">{listings.length}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">Last Polled</p>
          <p className="text-xl font-bold text-white">
            {event.last_polled_at ? formatRelativeTime(event.last_polled_at) : 'Never'}
          </p>
        </Card>
      </div>

      <div className="border-b border-gray-700">
        <nav className="flex gap-6">
          {(['overview', 'heatmap', 'history'] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-sm font-medium border-b-2 -mb-px capitalize transition-colors ${
                activeTab === tab
                  ? 'border-indigo-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div className="flex gap-2 mb-4">
            {['all', 'stubhub', 'seatgeek'].map(mp => (
              <button
                key={mp}
                onClick={() => setMarketplace(mp)}
                className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${
                  marketplace === mp
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {mp}
              </button>
            ))}
          </div>
          <SectionPriceBar listings={listings} />
          <div className="bg-gray-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Section</th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Row</th>
                  <th className="px-4 py-3 text-right text-gray-400 font-medium">Price</th>
                  <th className="px-4 py-3 text-right text-gray-400 font-medium">Qty</th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {listings.slice(0, 50).map(listing => (
                  <tr key={listing.id} className="hover:bg-gray-750 transition-colors">
                    <td className="px-4 py-2.5 text-white">{listing.section_name || '—'}</td>
                    <td className="px-4 py-2.5 text-gray-300">{listing.row || '—'}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-green-400">
                      {formatCurrency(listing.price_each)}
                    </td>
                    <td className="px-4 py-2.5 text-right text-gray-300">{listing.quantity}</td>
                    <td className="px-4 py-2.5">
                      <Badge variant={listing.marketplace_slug === 'stubhub' ? 'indigo' : 'blue'}>
                        {listing.marketplace_slug}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {listings.length === 0 && (
              <p className="text-center py-8 text-gray-400">No listings found. Try polling.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'heatmap' && event.event?.venue_slug && (
        <VenueHeatmap venueSlug={event.event.venue_slug} listings={listings} mode="price" />
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          <PriceHistoryChart eventId={eventId} />
          <InventoryChart eventId={eventId} />
        </div>
      )}
    </div>
  );
}
