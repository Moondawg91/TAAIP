import React, { useEffect, useState } from 'react';

export const AdminConsole: React.FC = () => {
  const [backups, setBackups] = useState<Array<{name: string; path: string; created_at?: string}>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBackups = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v2/upload/backups');
      const data = await res.json();
      if (data.status === 'ok' && Array.isArray(data.backups)) setBackups(data.backups);
      else setError('Failed to load backups');
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchBackups(); }, []);

  const createBackup = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v2/upload/backup', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok') await fetchBackups();
      else setError('Failed to create backup');
    } catch (e: any) { setError(e?.message || String(e)); }
    finally { setLoading(false); }
  };

  const restore = async (backupPath: string) => {
    if (!window.confirm('Restore backup? This will overwrite current DB.')) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('backup', backupPath);
      const res = await fetch('/api/v2/upload/restore', { method: 'POST', body: form });
      const data = await res.json();
      if (data.status === 'ok') {
        alert('Restore triggered successfully');
      } else {
        setError('Restore failed');
      }
    } catch (e: any) { setError(e?.message || String(e)); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Admin Console</h2>
      <div className="mb-4">
        <button onClick={createBackup} className="px-3 py-2 bg-yellow-500 text-black rounded font-semibold">Create Backup</button>
        <button onClick={fetchBackups} className="ml-3 px-3 py-2 bg-gray-800 text-yellow-500 rounded">Refresh</button>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div className="text-red-500">{error}</div>}

      <table className="w-full table-auto border-collapse">
        <thead>
          <tr className="text-left">
            <th className="px-2 py-1">Name</th>
            <th className="px-2 py-1">Created</th>
            <th className="px-2 py-1">Actions</th>
          </tr>
        </thead>
        <tbody>
          {backups.map((b) => (
            <tr key={b.path} className="border-t">
              <td className="px-2 py-2">{b.name}</td>
              <td className="px-2 py-2">{b.created_at || '—'}</td>
              <td className="px-2 py-2">
                <button onClick={() => restore(b.path)} className="px-2 py-1 bg-red-600 text-white rounded">Restore</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminConsole;
