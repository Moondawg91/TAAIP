import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import MarketPotentialDashboard from '../../components/MarketPotentialDashboard';
import { PLACEHOLDER_MARKET_DATA, runMarketPotentialEngine } from '../../lib/engines';

export const MarketPotentialPage: React.FC = () => {
  const potential = runMarketPotentialEngine(PLACEHOLDER_MARKET_DATA);

  return (
    <div className="space-y-6">
      <Card title="Market Potential">
        <p className="text-sm text-slate-300">Army vs DoD remaining potential and achievable capacity by CBSA, RSID, and ZIP drilldown.</p>
      </Card>
      <Card title="Market Potential Engine">
        <div className="grid grid-cols-2 gap-3 mb-3">
          {potential.summaries.map((summary) => (
            <div key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-3 py-2 text-xs text-slate-300">
              {summary.label}: {summary.value}
            </div>
          ))}
        </div>
        <Table
          rows={potential.opportunities}
          columns={[
            { key: 'zip', header: 'ZIP' },
            { key: 'potentialRemaining', header: 'Potential Remaining' },
            { key: 'opportunityScore', header: 'Opportunity Score' },
          ]}
          getRowId={(row) => row.zip}
        />
      </Card>
      <MarketPotentialDashboard />
    </div>
  );
};

export default MarketPotentialPage;
