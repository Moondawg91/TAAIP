import React, { useEffect, useState } from 'react';
import { Edit2, Save, X, RefreshCw } from 'lucide-react';

interface Threshold {
  metric_key: string;
  value: number;
  description: string;
}

export const KPIThresholdAdmin: React.FC = () => {
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<number | string>('');

  useEffect(() => {
    fetchThresholds();
  }, []);

  const fetchThresholds = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/admin/kpi-thresholds');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.status === 'ok' && data.thresholds) {
        const thresholdArray = Object.values(data.thresholds) as Threshold[];
        setThresholds(thresholdArray.sort((a, b) => a.metric_key.localeCompare(b.metric_key)));
      } else {
        setError('Failed to load thresholds');
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (threshold: Threshold) => {
    setEditingKey(threshold.metric_key);
    setEditValue(threshold.value);
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditValue('');
  };

  const saveEdit = async (metric_key: string) => {
    try {
      const numValue = parseFloat(editValue as string);
      if (isNaN(numValue)) {
        setError('Value must be a valid number');
        return;
      }

      const res = await fetch(`/api/v2/admin/kpi-thresholds/${metric_key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: numValue })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      setEditingKey(null);
      setEditValue('');
      await fetchThresholds();
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900">KPI Thresholds</h3>
        <button
          onClick={fetchThresholds}
          className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {loading && <div className="text-gray-600">Loading thresholds...</div>}
      {error && <div className="text-red-600 mb-4 p-3 bg-red-50 rounded">{error}</div>}

      <table className="w-full table-auto border-collapse border border-gray-300">
        <thead className="bg-gray-100">
          <tr>
            <th className="border border-gray-300 px-4 py-2 text-left">Metric</th>
            <th className="border border-gray-300 px-4 py-2 text-left">Description</th>
            <th className="border border-gray-300 px-4 py-2 text-left w-32">Value</th>
            <th className="border border-gray-300 px-4 py-2 text-center w-24">Actions</th>
          </tr>
        </thead>
        <tbody>
          {thresholds.map((threshold) => (
            <tr key={threshold.metric_key} className="hover:bg-gray-50">
              <td className="border border-gray-300 px-4 py-2 font-mono text-sm text-gray-900">
                {threshold.metric_key}
              </td>
              <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">
                {threshold.description}
              </td>
              <td className="border border-gray-300 px-4 py-2">
                {editingKey === threshold.metric_key ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                ) : (
                  <span className="font-semibold text-gray-900">{threshold.value}</span>
                )}
              </td>
              <td className="border border-gray-300 px-4 py-2 text-center">
                {editingKey === threshold.metric_key ? (
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => saveEdit(threshold.metric_key)}
                      className="px-2 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 flex items-center gap-1"
                    >
                      <Save className="w-3 h-3" />
                      Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="px-2 py-1 bg-gray-400 text-white text-sm rounded hover:bg-gray-500 flex items-center gap-1"
                    >
                      <X className="w-3 h-3" />
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => startEdit(threshold)}
                    className="px-2 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 flex items-center gap-1"
                  >
                    <Edit2 className="w-3 h-3" />
                    Edit
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {thresholds.length === 0 && !loading && (
        <div className="text-gray-500 text-center py-8">No thresholds configured</div>
      )}

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-gray-700">
        <strong>Note:</strong> Threshold values are used by the ROI engine to classify metrics as GREEN (meets target), AMBER (within 10%), or RED (exceeds target).
      </div>
    </div>
  );
};

export default KPIThresholdAdmin;
