import React from 'react';

type FragoViewerProps = {
  detail: Record<string, unknown> | null;
  versions: Array<Record<string, unknown>>;
};

export const FragoViewer: React.FC<FragoViewerProps> = ({ detail, versions }) => {
  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
        <h3 className="text-sm font-semibold text-white">FRAGO Detail</h3>
        <pre className="mt-2 max-h-64 overflow-auto text-[11px] text-[#CBD5E1]">{JSON.stringify(detail ?? {}, null, 2)}</pre>
      </section>

      <section className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
        <h3 className="text-sm font-semibold text-white">Version History</h3>
        <ul className="mt-2 space-y-2 text-xs text-[#E2E8F0]">
          {versions.map((row, index) => (
            <li key={`${row.version_id ?? index}`} className="rounded border border-[#1D3A5C] bg-[#0C2545] p-2">
              v{String(row.version_number ?? '-')} - {String(row.timestamp ?? row.created_at ?? '-')}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
