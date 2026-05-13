import React, { useEffect, useState } from 'react';

type GovernanceBackup = {
  backup_id: string;
  file: string;
  created_at?: string;
  size_bytes?: number;
};

const formatBytes = (size?: number): string => {
  if (!size || size <= 0) return '0 B';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

export const GovernanceDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backups, setBackups] = useState<GovernanceBackup[]>([]);
  const [selectedBackupId, setSelectedBackupId] = useState<string>('');

  const loadBackups = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/governance/backups');
      const data = await res.json();
      if (data.status === 'ok' && Array.isArray(data.backups)) {
        setBackups(data.backups);
        if (data.backups.length > 0 && !selectedBackupId) {
          setSelectedBackupId(data.backups[0].backup_id || '');
        }
      } else {
        setError('Failed to load governance backups');
      }
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBackups();
  }, []);

  const createBackup = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/governance/backup', { method: 'POST' });
      const data = await res.json();
      if (data.status !== 'ok') {
        setError(data.detail || data.message || 'Governance backup failed');
      }
      await loadBackups();
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const restoreBackup = async () => {
    if (!selectedBackupId) {
      setError('Select a backup first');
      return;
    }
    if (!window.confirm('Restore selected governance backup? This replaces the live database.')) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/governance/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_id: selectedBackupId }),
      });
      const data = await res.json();
      if (data.status !== 'ok') {
        setError(data.detail || data.message || 'Governance restore failed');
      }
      await loadBackups();
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Governance Controls</h2>
        <p className="text-sm text-gray-600">
          Managed governance backup and controlled restore operations.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={createBackup}
          disabled={loading}
          className="px-3 py-2 rounded bg-yellow-500 text-black font-semibold disabled:opacity-50"
        >
          Create Governance Backup
        </button>
        <button
          onClick={loadBackups}
          disabled={loading}
          className="px-3 py-2 rounded bg-gray-800 text-yellow-500 font-semibold disabled:opacity-50"
        >
          Refresh
        </button>
        <button
          onClick={restoreBackup}
          disabled={loading || !selectedBackupId}
          className="px-3 py-2 rounded bg-red-600 text-white font-semibold disabled:opacity-50"
        >
          Restore Selected Backup
        </button>
      </div>

      {error && <div className="p-2 rounded bg-red-50 text-red-700 border border-red-200">{error}</div>}
      {loading && <div className="text-sm text-gray-600">Processing...</div>}

      <div className="bg-white rounded border border-gray-200 overflow-hidden">
        <table className="w-full table-auto text-sm">
          <thead className="bg-gray-100 text-gray-700">
            <tr>
              <th className="text-left px-3 py-2">Select</th>
              <th className="text-left px-3 py-2">Backup File</th>
              <th className="text-left px-3 py-2">Created</th>
              <th className="text-left px-3 py-2">Size</th>
            </tr>
          </thead>
          <tbody>
            {backups.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-4 text-gray-500">No governance backups found.</td>
              </tr>
            ) : (
              backups.map((b) => (
                <tr key={b.file} className="border-t border-gray-100">
                  <td className="px-3 py-2">
                    <input
                      type="radio"
                      name="governance-backup"
                      checked={selectedBackupId === b.backup_id}
                      onChange={() => setSelectedBackupId(b.backup_id)}
                    />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{b.file}</td>
                  <td className="px-3 py-2">{b.created_at || 'Unknown'}</td>
                  <td className="px-3 py-2">{formatBytes(b.size_bytes)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GovernanceDashboard;
