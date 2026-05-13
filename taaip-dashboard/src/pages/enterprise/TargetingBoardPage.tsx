import React, { useState } from 'react';
import { Card, Tabs } from '../../components/shared/ui';
import TargetingBoard from '../../components/TargetingBoard';

type Stage = 'Q-1 Assess' | 'Q+0 Execute' | 'Q+1 Validate' | 'Q+2 Review' | 'Q+3 Approve' | 'Q+4 Guidance';

const STAGE_ITEMS = [
  { id: 'Q-1 Assess', label: 'Q-1 Assess' },
  { id: 'Q+0 Execute', label: 'Q+0 Execute' },
  { id: 'Q+1 Validate', label: 'Q+1 Validate' },
  { id: 'Q+2 Review', label: 'Q+2 Review' },
  { id: 'Q+3 Approve', label: 'Q+3 Approve' },
  { id: 'Q+4 Guidance', label: 'Q+4 Guidance' },
];

export const TargetingBoardPage: React.FC = () => {
  const [stage, setStage] = useState<Stage>('Q+3 Approve');

  return (
    <div className="space-y-6">
      <Card title="Targeting Board Commander Decision Support">
        <div className="text-sm text-slate-300">Current FY/QTR board cycle with agenda, notes, tasks, historical archive, board packet export, and commander brief generation.</div>
      </Card>

      <Card title="Cycle Stages" noPad>
        <Tabs tabs={STAGE_ITEMS} active={stage} onChange={(id) => setStage(id as Stage)} />
      </Card>

      {stage === 'Q+3 Approve' ? (
        <TargetingBoard />
      ) : (
        <Card title={`${stage} Workspace`}>
          <div className="text-sm text-slate-300 space-y-2">
            {stage === 'Q-1 Assess' && <p>AAR, lessons learned, completed events, ROI impact, funnel impact, and archive.</p>}
            {stage === 'Q+0 Execute' && <p>Approved nominations in execution, event status, operational issues, notes, and tasks.</p>}
            {stage === 'Q+1 Validate' && <p>One-quarter-out readiness validation, support gaps, budget feasibility, and field activity readiness.</p>}
            {stage === 'Q+2 Review' && <p>Two-quarters-out strategic review, market updates, and resource feasibility refinement.</p>}
            {stage === 'Q+4 Guidance' && <p>Commander future guidance: targeting priorities, market focus, resource guidance, and strategic direction.</p>}
          </div>
        </Card>
      )}
    </div>
  );
};

export default TargetingBoardPage;
