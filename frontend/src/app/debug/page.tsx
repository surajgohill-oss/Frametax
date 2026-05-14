'use client';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { fmtRelative } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';

type View = 'errors' | 'memory';

export default function DebugPage() {
  const [view, setView] = useState<View>('errors');
  const [errors, setErrors] = useState<any[]>([]);
  const [memory, setMemory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [testUrl, setTestUrl] = useState('');
  const [testMarketplace, setTestMarketplace] = useState('stubhub');
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => { loadData(); }, [view]);

  async function loadData() {
    setLoading(true);
    try {
      if (view === 'errors') {
        setErrors(await api.debug.errors());
      } else {
        setMemory(await api.debug.memory());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function clearMemory() {
    if (!confirm('Clear all failure memory entries?')) return;
    await api.debug.clearMemory();
    await loadData();
  }

  async function testCollect() {
    if (!testUrl) return;
    setTestLoading(true);
    setTestResult(null);
    try {
      const result = await api.debug.testCollect(testMarketplace, testUrl);
      setTestResult(JSON.stringify(result, null, 2));
    } catch (e: unknown) {
      setTestResult(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setTestLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Debug Console</h1>
        <p className="text-gray-400 mt-1">Scraper error log and failure memory</p>
      </div>

      <div className="bg-gray-800 rounded-xl p-4 space-y-3">
        <h2 className="text-sm font-semibold text-white">Test Collector</h2>
        <div className="flex gap-3">
          <select
            value={testMarketplace}
            onChange={e => setTestMarketplace(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
          >
            <option value="stubhub">StubHub</option>
            <option value="seatgeek">SeatGeek</option>
          </select>
          <input
            type="url"
            value={testUrl}
            onChange={e => setTestUrl(e.target.value)}
            placeholder="Paste event URL..."
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-400"
          />
          <button
            onClick={testCollect}
            disabled={testLoading || !testUrl}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg text-sm font-medium"
          >
            {testLoading ? 'Testing...' : 'Run'}
          </button>
        </div>
        {testResult && (
          <pre className="bg-gray-900 rounded-lg p-3 text-xs text-green-300 overflow-auto max-h-48">{testResult}</pre>
        )}
      </div>

      <div className="flex gap-2">
        {(['errors', 'memory'] as View[]).map(v => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
              view === v ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {v === 'errors' ? 'Error Log' : 'Failure Memory'}
          </button>
        ))}
        {view === 'memory' && memory.length > 0 && (
          <button
            onClick={clearMemory}
            className="ml-auto px-4 py-2 rounded-lg text-sm font-medium bg-red-900 hover:bg-red-800 text-red-200"
          >
            Clear All
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
        </div>
      ) : view === 'errors' ? (
        <div className="bg-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="px-4 py-3 text-left text-gray-400">Time</th>
                <th className="px-4 py-3 text-left text-gray-400">Marketplace</th>
                <th className="px-4 py-3 text-left text-gray-400">Type</th>
                <th className="px-4 py-3 text-left text-gray-400">Message</th>
                <th className="px-4 py-3 text-left text-gray-400">Artifacts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {errors.map((err: any) => (
                <tr key={err.id}>
                  <td className="px-4 py-2.5 text-gray-400 whitespace-nowrap">{fmtRelative(err.created_at)}</td>
                  <td className="px-4 py-2.5"><Badge variant="indigo">{err.marketplace}</Badge></td>
                  <td className="px-4 py-2.5"><Badge variant="secondary">{err.error_type}</Badge></td>
                  <td className="px-4 py-2.5 text-gray-300 max-w-xs truncate">{err.error_message}</td>
                  <td className="px-4 py-2.5 flex gap-2">
                    {err.screenshot_path && <span title={err.screenshot_path}>📷</span>}
                    {err.html_path && <span title={err.html_path}>📄</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {errors.length === 0 && (
            <p className="text-center py-8 text-gray-400">No errors logged. Collectors are healthy.</p>
          )}
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="px-4 py-3 text-left text-gray-400">Marketplace</th>
                <th className="px-4 py-3 text-left text-gray-400">Selector Pattern</th>
                <th className="px-4 py-3 text-right text-gray-400">Failures</th>
                <th className="px-4 py-3 text-left text-gray-400">Last Failure</th>
                <th className="px-4 py-3 text-left text-gray-400">Last Success</th>
                <th className="px-4 py-3 text-left text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {memory.map((entry: any) => (
                <tr key={entry.id}>
                  <td className="px-4 py-2.5"><Badge variant="indigo">{entry.marketplace}</Badge></td>
                  <td className="px-4 py-2.5 font-mono text-gray-300">{entry.selector_pattern}</td>
                  <td className="px-4 py-2.5 text-right">
                    <span className={entry.failure_count >= 3 ? 'text-red-400 font-bold' : 'text-yellow-400'}>
                      {entry.failure_count}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-400">{fmtRelative(entry.last_failure_at)}</td>
                  <td className="px-4 py-2.5 text-gray-400">
                    {entry.last_success_at ? fmtRelative(entry.last_success_at) : '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant={entry.is_active ? 'secondary' : 'success'}>
                      {entry.is_active ? 'skipping' : 'active'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {memory.length === 0 && (
            <p className="text-center py-8 text-gray-400">No failure memory entries.</p>
          )}
        </div>
      )}
    </div>
  );
}
