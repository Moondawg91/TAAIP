import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import { PLACEHOLDER_MARKET_DATA, runReserveAlignmentEngine } from '../../lib/engines';

const ROWS = [
  { unit: '1A1D', reservePotential: 122, reserveContracts: 31, activeContracts: 45, alignmentGap: 'High', action: 'Increase reserve messaging' },
  { unit: '1A1E', reservePotential: 98, reserveContracts: 14, activeContracts: 52, alignmentGap: 'Medium', action: 'Adjust outreach mix' },
];

export const ReserveAlignmentPage: React.FC = () => {
  const result = runReserveAlignmentEngine(PLACEHOLDER_MARKET_DATA);

  return (
    <div className="space-y-6">
      <Card title="Reserve Alignment">
        <p className="text-sm text-slate-300">Tracks reserve-component opportunity against current contract mix by unit scope and market.</p>
      </Card>
      <Card title="Reserve Alignment Engine">
        <div className="grid grid-cols-2 gap-3 mb-3">
          {result.summaries.map((summary) => (
            <div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
              {summary.label}: {summary.value}
            </div>
          ))}
        </div>
      </Card>
      <Card title="Reserve vs Active Alignment">
        <Table
          rows={ROWS}
          columns={[
            { key: 'unit', header: 'Unit' },
            { key: 'reservePotential', header: 'Reserve Potential' },
            { key: 'reserveContracts', header: 'Reserve Contracts' },
            { key: 'activeContracts', header: 'Active Contracts' },
            { key: 'alignmentGap', header: 'Alignment Gap' },
            { key: 'action', header: 'Recommended Action' },
          ]}
          getRowId={(row) => row.unit}
        />
      </Card>
    </div>
  );
};

export default ReserveAlignmentPage;
