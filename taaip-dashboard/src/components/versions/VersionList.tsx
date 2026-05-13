import React from 'react';

type VersionListProps = {
  rows: Array<Record<string, unknown>>;
  onSelect: (versionNumber: number) => void;
};

export const VersionList: React.FC<VersionListProps> = ({ rows, onSelect }) => {
  const sorted = [...rows].sort((a, b) => Number(a.version_number ?? 0) - Number(b.version_number ?? 0));

  return (
    <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] overflow-hidden">
      <table className="w-full text-left text-xs">
        <thead className="bg-[#112B4D] text-[#94A3B8]">
          <tr>
            <th className="px-3 py-2">Version</th>
            <th className="px-3 py-2">Timestamp</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, index) => {
            const versionNumber = Number(row.version_number ?? 0);
            return (
              <tr key={`${row.version_id ?? index}`} className="border-t border-[#1D3A5C] text-[#E2E8F0]">
                <td className="px-3 py-2">{String(row.version_number ?? '-')}</td>
                <td className="px-3 py-2">{String(row.timestamp ?? row.created_at ?? '-')}</td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => onSelect(versionNumber)}
                    className="rounded bg-[#1D4ED8] px-2 py-1 text-[11px] font-semibold text-white"
                  >
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
