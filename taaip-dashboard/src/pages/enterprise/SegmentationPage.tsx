import React from 'react';
import { Card, Table } from '../../components/shared/ui';
import { MarketSegmentationDashboard } from '../../components/MarketSegmentationDashboard';
import { PLACEHOLDER_MARKET_DATA, runMarketIntelligenceEngine } from '../../lib/engines';

export const SegmentationPage: React.FC = () => {
  const result = runMarketIntelligenceEngine(PLACEHOLDER_MARKET_DATA);

  return (
    <div className="space-y-6">
      <Card title="Segmentation Intelligence">
        <p className="text-sm text-slate-300">
          PRIZM, CBSA, D3AE, and F3A segmentation signals are rendered with raw percentages and traceable values.
        </p>
      </Card>
      <Card title="Market Intelligence Engine - Segmented ZIP Output">
        <Table
          rows={result.segmented}
          columns={[
            { key: 'zip', header: 'ZIP' },
            { key: 'cbsa', header: 'CBSA' },
            { key: 'prizm', header: 'PRIZM Cluster' },
            { key: 'contractRate', header: 'Contract Rate %' },
          ]}
          getRowId={(row) => row.zip}
        />
      </Card>
      <MarketSegmentationDashboard />
    </div>
  );
};

export default SegmentationPage;
