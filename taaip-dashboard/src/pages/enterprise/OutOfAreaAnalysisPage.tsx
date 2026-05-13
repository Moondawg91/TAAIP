import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import { runOutOfAreaAnalysisEngine } from '../../lib/engines';

const ROWS = [
  { contractId: 'OA-1021', homeZip: '30044', contractZip: '30303', rsid: '1A1D', branch: 'Army', impact: 'Potential leakage', recommendation: 'Coordinate with owning RSID' },
  { contractId: 'OA-1039', homeZip: '28202', contractZip: '30022', rsid: '1A1E', branch: 'Navy', impact: 'Competitor gain', recommendation: 'Increase outreach in source ZIP' },
];

export const OutOfAreaAnalysisPage: React.FC = () => {
  const engine = runOutOfAreaAnalysisEngine(
    ROWS.map((row) => ({ homeZip: row.homeZip, contractZip: row.contractZip, branch: row.branch })),
  );

  return (
    <div className="space-y-6">
      <Card title="Out-of-Area Analysis">
        <p className="text-sm text-slate-300">Tracks out-of-area contracts, source ZIP leakage, and competitor branch displacement across assigned markets.</p>
      </Card>
      <Card title="Out-of-Area Analysis Engine">
        <div className="grid grid-cols-2 gap-3">
          {engine.summaries.map((summary) => (
            <div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
              {summary.label}: {summary.value}
            </div>
          ))}
        </div>
      </Card>
      <Card title="Out-of-Area Contract Intelligence">
        <Table
          rows={ROWS}
          columns={[
            { key: 'contractId', header: 'Contract ID' },
            { key: 'homeZip', header: 'Home ZIP' },
            { key: 'contractZip', header: 'Contract ZIP' },
            { key: 'rsid', header: 'RSID' },
            { key: 'branch', header: 'Branch' },
            { key: 'impact', header: 'Operational Impact' },
            { key: 'recommendation', header: 'Recommendation' },
          ]}
          getRowId={(row) => row.contractId}
        />
      </Card>
    </div>
  );
};

export default OutOfAreaAnalysisPage;
