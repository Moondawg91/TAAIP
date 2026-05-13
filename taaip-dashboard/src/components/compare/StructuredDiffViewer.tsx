import React from 'react';

type StructuredDiffViewerProps = {
  diff: Record<string, unknown> | null;
};

function renderSection(title: string, value: unknown): React.ReactElement {
  const data = (value ?? {}) as { added?: unknown[]; removed?: unknown[]; changed?: unknown[] };
  return (
    <section className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
      <h4 className="text-sm font-semibold text-white">{title}</h4>
      <div className="mt-2 grid gap-2 text-xs text-[#E2E8F0] md:grid-cols-3">
        <div>
          <p className="text-[#93C5FD] mb-1">Added</p>
          <pre className="overflow-auto">{JSON.stringify(data.added ?? [], null, 2)}</pre>
        </div>
        <div>
          <p className="text-[#FCA5A5] mb-1">Removed</p>
          <pre className="overflow-auto">{JSON.stringify(data.removed ?? [], null, 2)}</pre>
        </div>
        <div>
          <p className="text-[#BFDBFE] mb-1">Changed</p>
          <pre className="overflow-auto">{JSON.stringify(data.changed ?? [], null, 2)}</pre>
        </div>
      </div>
    </section>
  );
}

export const StructuredDiffViewer: React.FC<StructuredDiffViewerProps> = ({ diff }) => {
  if (!diff) {
    return (
      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3 text-sm text-[#94A3B8]">
        No comparison selected.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {renderSection('Analytics', diff.analytics)}
      {renderSection('Recommendations', diff.recommendations)}
      {renderSection('FRAGO', diff.frago)}
      {renderSection('Explanation', diff.explanation)}
    </div>
  );
};
