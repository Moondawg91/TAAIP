import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import { usePageExport } from '../../lib/export';

const EXPORT_DEFINITIONS = [
  { id: 'exp-1', product: 'Commander Brief', format: 'PPT', source: 'Command Center + MI + SRP + ROI', status: 'Ready' },
  { id: 'exp-2', product: 'Operational Snapshot', format: 'PDF', source: 'Operations + Field Activities + Budget', status: 'Ready' },
  { id: 'exp-3', product: 'Performance Rollup', format: 'PDF', source: 'Performance + Funnel + DoD Market Share', status: 'Ready' },
];

export const EnterpriseExportEngine: React.FC = () => {
  const { exportPdf, exportPpt, exportCommanderBrief } = usePageExport('enterprise-export', 'Enterprise Export Engine');

  return (
    <Card title="Enterprise Export Engine (PDF / PPT / Commander Brief)">
      <div className="mb-3 flex flex-wrap gap-2">
        <button onClick={() => { void exportPdf({ scope: 'enterprise', product: 'Operational Snapshot' }); }} className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]">Generate PDF</button>
        <button onClick={() => { void exportPpt({ scope: 'enterprise', product: 'Commander Deck' }); }} className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]">Generate PPT</button>
        <button onClick={() => { void exportCommanderBrief({ summary: 'Command posture summary', riskItems: ['Market leakage', 'Reserve gap'], actions: ['Prioritize SRP seniors', 'Shift targeting cycle resources'] }); }} className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]">Generate Commander Brief</button>
      </div>
      <Table
        rows={EXPORT_DEFINITIONS}
        columns={[
          { key: 'product', header: 'Product' },
          { key: 'format', header: 'Format' },
          { key: 'source', header: 'Source' },
          { key: 'status', header: 'Status' },
        ]}
        getRowId={(row) => row.id}
      />
    </Card>
  );
};

export default EnterpriseExportEngine;
