import React from 'react';

type HistoryTimelineProps = {
  rows: Array<Record<string, unknown>>;
};

export const HistoryTimeline: React.FC<HistoryTimelineProps> = ({ rows }) => {
  const ordered = [...rows].sort((a, b) => {
    const ad = String(a.created_at ?? '');
    const bd = String(b.created_at ?? '');
    return ad.localeCompare(bd);
  });

  return (
    <ol className="space-y-3">
      {ordered.map((row, index) => (
        <li key={`${row.archive_event_id ?? index}`} className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
          <p className="text-[11px] uppercase tracking-[0.08em] text-[#93C5FD]">{String(row.entity_type ?? '-')} v{String(row.version_number ?? '-')}</p>
          <p className="mt-1 text-xs text-[#E2E8F0]">{String(row.created_at ?? '-')}</p>
          <p className="mt-2 text-xs text-[#CBD5E1] break-all">{String(row.payload_hash ?? '-')}</p>
        </li>
      ))}
    </ol>
  );
};
