import React from 'react';

type RecommendationCardsProps = {
  rows: Array<Record<string, unknown>>;
};

export const RecommendationCards: React.FC<RecommendationCardsProps> = ({ rows }) => {
  const ordered = [...rows].sort((a, b) => {
    const pa = String(a.priority ?? 'zz');
    const pb = String(b.priority ?? 'zz');
    return pa.localeCompare(pb);
  });

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {ordered.map((row, index) => (
        <article key={`${row.id ?? index}`} className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
          <p className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">{String(row.recommendation_type ?? 'recommendation')}</p>
          <p className="mt-1 text-sm font-semibold text-white">{String(row.recommendation_text ?? row.summary ?? 'No summary')}</p>
          <div className="mt-3 flex items-center justify-between text-xs">
            <span className="rounded bg-[#123A62] px-2 py-0.5 text-[#BFDBFE]">Priority: {String(row.priority ?? '-')}</span>
            <span className="text-[#93C5FD]">Confidence: {String(row.confidence ?? row.confidence_score ?? '-')}</span>
          </div>
        </article>
      ))}
    </div>
  );
};
