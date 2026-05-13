import React from 'react';
import DODBranchComparison from '../../components/DODBranchComparison';
import { Card } from '../../components/shared/ui';
import { TAAIP_DOCTRINE } from '../../config/taaipDoctrine';
import { PLACEHOLDER_MARKET_DATA, runDodComponentBreakdownEngine } from '../../lib/engines';

export const DODMarketSharePage: React.FC = () => {
  const breakdown = runDodComponentBreakdownEngine(PLACEHOLDER_MARKET_DATA);

  return (
    <div className="space-y-6">
      <Card title="DoD Market Share">
        <p className="text-sm text-slate-300">
          Component-level competitive intelligence across {TAAIP_DOCTRINE.dodComponents.join(', ')} with mission-focused ranking,
          conversion analysis, and recruiter productivity.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {breakdown.summaries.map((summary) => (
            <span key={summary.label} className="rounded border border-slate-700 bg-slate-900/40 px-2 py-1 text-xs text-slate-300">
              {summary.label}: {summary.value}
            </span>
          ))}
        </div>
      </Card>
      <DODBranchComparison />
    </div>
  );
};

export default DODMarketSharePage;
