import React from 'react';

type AnalyticsPanelProps = {
  rows: Array<Record<string, unknown>>;
};

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ rows }) => {
  const ordered = [...rows].sort((a, b) => {
    const av = String(a.version_number ?? '0');
    const bv = String(b.version_number ?? '0');
    return Number(av) - Number(bv);
  });

  const kpiTotal = ordered.length;
  const kpiLatest = ordered[ordered.length - 1] ?? null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
          <p className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">Snapshots</p>
          <p className="mt-1 text-xl font-semibold text-white">{kpiTotal}</p>
        </div>
        <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3 col-span-1 md:col-span-3">
          <p className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">Latest Snapshot</p>
          <p className="mt-1 text-sm text-[#E2E8F0]">{kpiLatest ? JSON.stringify(kpiLatest).slice(0, 220) : 'No analytics snapshot selected yet.'}</p>
        </div>
      </div>

      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#112B4D] text-[#94A3B8]">
            <tr>
              <th className="px-3 py-2">Version</th>
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">Summary</th>
            </tr>
          </thead>
          <tbody>
            {ordered.map((row, index) => (
              <tr key={`${row.version_number ?? index}`} className="border-t border-[#1D3A5C] text-[#E2E8F0]">
                <td className="px-3 py-2">{String(row.version_number ?? '-')}</td>
                <td className="px-3 py-2">{String(row.timestamp ?? row.created_at ?? '-')}</td>
                <td className="px-3 py-2">{JSON.stringify(row.content ?? row.payload ?? {}).slice(0, 120)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
