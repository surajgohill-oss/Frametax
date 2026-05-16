'use client';
import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { fmt$, fmtDate, fmtDateTime, fmtRelative } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import VenueHeatmap from '@/components/venue/VenueHeatmap';
import PriceHistoryChart from '@/components/charts/PriceHistoryChart';
import SectionPriceBar from '@/components/charts/SectionPriceBar';
import InventoryChart from '@/components/charts/InventoryChart';

type Tab = 'overview' | 'heatmap' | 'history';

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params.id);

  const [event, setEvent] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);
  const [pollLoading, setPollLoading] = useState(false);
  const [marketplace, setMarketplace] = useState<string>('');

  useEffect(() => { loadEvent(); }, [eventId]);
  useEffect(() => { if (event) loadListings(); }, [event, marketplace]);

  async function loadEvent() {
    try {
      const data = await api.events.get(eventId);
      setEvent(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadListings() {
    try {
      const data = await api.listings.byEvent(eventId, marketplace || undefined);
      setListings(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function triggerPoll() {
    setPollLoading(true);
    try {
      await api.poll.trigger(eventId);
      await new Promise(r => setTimeout(r, 3000));
      await loadEvent();
      await loadListings();
    } finally {
      setPollLoading(false);
    }
  }

  async function toggleActive() {
    if (!event) return;
    await api.events.update(eventId, { is_active: !event.is_active });
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

  const stubhubListings = listings.filter((l: any) => l.marketplace_slug === 'stubhub');
  const seatgeekListings = listings.filter((l: any) => l.marketplace_slug === 'seatgeek');
  const lowestStubhub = stubhubListings.length > 0 ? Math.min(...stubhubListings.map((l: any) => l.price_each)) : null;
  const lowestSeatgeek = seatgeekListings.length > 0 ? Math.min(...seatgeekListings.map((l: any) => l.price_each)) : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => router.back()} className="text-sm text-gray-400 hover:text-white mb-2">
            ← Back
          </button>
          <h1 className="text-2xl font-bold text-white">{event.title || 'Unnamed Event'}</h1>
          <p className="text-gray-400 mt-1">
            {event.venue_slug} &bull; {event.event_date ? fmtDate(event.event_date) : 'Date TBD'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={triggerPoll}
            disabled={pollLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg text-sm font-medium"
          >
            {pollLoading ? 'Polling...' : 'Poll Now'}
          </button>
          <button
            onClick={toggleActive}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              event.is_active ? 'bg-gray-700 hover:bg-gray-600' : 'bg-green-700 hover:bg-green-600'
            } text-white`}
          >
            {event.is_active ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-xs text-gray-400 mb-1">StubHub Low</p>
          <p className="text-xl font-bold text-green-400">{fmt$(lowestStubhub)}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">SeatGeek Low</p>
          <p className="text-xl font-bold text-blue-400">{fmt$(lowestSeatgeek)}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">Total Listings</p>
          <p className="text-xl font-bold text-white">{listings.length}</p>
        </Card>
        <Card>
          <p className="text-xs text-gray-400 mb-1">Last Polled</p>
          <p className="text-xl font-bold text-white">
            {event.last_polled_at ? fmtRelative(event.last_polled_at) : 'Never'}
          </p>
        </Card>
      </div>

      <div className="border-b border-gray-700">
        <nav className="flex gap-6">
          {(['overview', 'heatmap', 'history'] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 text-sm font-medium border-b-2 -mb-px capitalize ${
                activeTab === tab ? 'border-indigo-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
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
            {[['', 'All'], ['seatgeek', 'SeatGeek'], ['stubhub', 'StubHub'], ['ticketmaster', 'Ticketmaster'], ['tickpick', 'TickPick'], ['gametime', 'GameTime']].map(([val, label]) => (
              <button
                key={val}
                onClick={() => setMarketplace(val)}
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  marketplace === val ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <SectionPriceBar sections={listings.map((l: any) => ({ display_name: l.section_name, lowest_ask: l.price_each }))} />
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
                {listings.slice(0, 50).map((listing: any) => (
                  <tr key={listing.id} className="hover:bg-gray-750">
                    <td className="px-4 py-2.5 text-white">{listing.section_name || '—'}</td>
                    <td className="px-4 py-2.5 text-gray-300">{listing.row || '—'}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-green-400">{fmt$(listing.price_each)}</td>
                    <td className="px-4 py-2.5 text-right text-gray-300">{listing.quantity}</td>
                    <td className="px-4 py-2.5 space-x-1">
                      <Badge variant={
                        listing.marketplace_slug === 'stubhub'      ? 'indigo'  :
                        listing.marketplace_slug === 'ticketmaster' ? 'green'   :
                        listing.marketplace_slug === 'tickpick'     ? 'orange'  :
                        listing.marketplace_slug === 'gametime'     ? 'yellow'  :
                        'blue'
                      }>
                        {listing.marketplace_slug}
                      </Badge>
                      {listing.market_segment && (
                        <Badge variant="secondary">
                          {listing.market_segment === 'verified_resale' ? 'resale' : listing.market_segment}
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {listings.length === 0 && (
              <p className="text-center py-8 text-gray-400">No listings. Try polling.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'heatmap' && event.venue_slug && (
        <VenueHeatmap venueSlug={event.venue_slug} listings={listings} mode="price" />
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
