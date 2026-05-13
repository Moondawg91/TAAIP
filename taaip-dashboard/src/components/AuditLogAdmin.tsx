import React, { useEffect, useMemo, useState } from 'react';
import { RefreshCw, Filter } from 'lucide-react';

type AuditItem = {
  id: string | number;
  actor: string | null;
  action: string | null;
  entity_type: string | null;
  entity_id: string | null;
  detail: unknown;
  created_at: string | null;
};

export const AuditLogAdmin: React.FC = () => {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [startAt, setStartAt] = useState('');
  const [endAt, setEndAt] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [limit, setLimit] = useState(100);

  const actionOptions = useMemo(() => {
    const set = new Set<string>();
    for (const item of items) {
      if (item.action) set.add(item.action);
    }
    return Array.from(set).sort();
  }, [items]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startAt) params.set('start_at', new Date(startAt).toISOString());
      if (endAt) params.set('end_at', new Date(endAt).toISOString());
      if (userFilter.trim()) params.set('user', userFilter.trim());
      if (actionFilter.trim()) params.set('action', actionFilter.trim());
      params.set('limit', String(limit));
      params.set('offset', '0');

      const res = await fetch(`/api/v2/admin/audit-logs?${params.toString()}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      if (data.status === 'ok') {
        setItems(Array.isArray(data.items) ? data.items : []);
        setTotal(Number(data.total || 0));
      } else {
        setError('Failed to load audit logs');
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-white">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-900">Audit Log Viewer</h3>
        <button
          onClick={fetchLogs}
          className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
        <div>
          <label className="block text-sm text-gray-700 mb-1">Start Date/Time</label>
          <input
            type="datetime-local"
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">End Date/Time</label>
          <input
            type="datetime-local"
            value={endAt}
            onChange={(e) => setEndAt(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">User</label>
          <input
            type="text"
            placeholder="username"
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Action/Event Type</label>
          <input
            type="text"
            list="audit-action-options"
            placeholder="action"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full border border-gray-300 rounded px-2 py-1"
          />
          <datalist id="audit-action-options">
            {actionOptions.map((a) => (
              <option key={a} value={a} />
            ))}
          </datalist>
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Limit</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-full border border-gray-300 rounded px-2 py-1"
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
        </div>
      </div>

      <div className="mb-4">
        <button
          onClick={fetchLogs}
          className="px-3 py-2 bg-gray-800 text-white rounded hover:bg-gray-900 inline-flex items-center gap-2"
        >
          <Filter className="w-4 h-4" />
          Apply Filters
        </button>
        <span className="ml-3 text-sm text-gray-600">Showing {items.length} of {total}</span>
      </div>

      {loading && <div className="text-gray-600">Loading audit logs...</div>}
      {error && <div className="text-red-600 mb-3">{error}</div>}

      <div className="overflow-x-auto border border-gray-200 rounded">
        <table className="min-w-full table-auto">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Timestamp</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">User</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Action</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Entity</th>
              <th className="px-3 py-2 text-left text-xs font-semibold text-gray-700">Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={`${row.id}-${row.created_at || ''}`} className="border-t border-gray-200 align-top">
                <td className="px-3 py-2 text-xs text-gray-800 whitespace-nowrap">{row.created_at || '-'}</td>
                <td className="px-3 py-2 text-xs text-gray-800">{row.actor || '-'}</td>
                <td className="px-3 py-2 text-xs text-gray-800 font-medium">{row.action || '-'}</td>
                <td className="px-3 py-2 text-xs text-gray-800">{row.entity_type || '-'}{row.entity_id ? `:${row.entity_id}` : ''}</td>
                <td className="px-3 py-2 text-xs text-gray-700 max-w-xl break-words">
                  {row.detail == null ? '-' : JSON.stringify(row.detail)}
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-sm text-gray-500">No audit entries match current filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditLogAdmin;
