import React, { useMemo, useState } from 'react';

interface RSIDFilterProps {
  currentRSID?: string | null;
  onFilterChange: (rsid: string | null, level: string | null) => void;
}

export const RSIDFilter: React.FC<RSIDFilterProps> = ({ currentRSID = '', onFilterChange }) => {
  const [rsid, setRsid] = useState(currentRSID || '');
  const [level, setLevel] = useState('all');

  const normalizedLevel = useMemo(() => (level === 'all' ? null : level), [level]);

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">RSID</label>
        <input
          value={rsid}
          onChange={(event) => setRsid(event.target.value)}
          placeholder="Filter by station"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Level</label>
        <select
          value={level}
          onChange={(event) => setLevel(event.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
        >
          <option value="all">All</option>
          <option value="national">National</option>
          <option value="market">Market</option>
          <option value="station">Station</option>
        </select>
      </div>

      <button
        onClick={() => onFilterChange(rsid || null, normalizedLevel)}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
      >
        Apply filter
      </button>
    </div>
  );
};

export default RSIDFilter;
