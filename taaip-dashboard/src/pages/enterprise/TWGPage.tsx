import React from 'react';
import { Card } from '../../components/shared/ui';
import { TargetingWorkingGroup } from '../../components/TargetingWorkingGroup';
import { logAuditEvent } from '../../lib/audit/controller';
import { pushNotification } from '../../lib/notifications/controller';

const CHECKPOINTS = [
  'Commander Priority / Intention Alignment',
  'ROP Alignment',
  'SRP Alignment',
  'Lines of Effort Alignment',
  'Nomination Readiness',
  'Override Justification Required if Failed',
];

export const TWGPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Card title="Targeting Working Group Workflow (Q-Cycle)">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm text-slate-300">
          <div>
            Imported nominations from EMM are validated here before board routing.
          </div>
          <div>
            Failed checkpoints are explicitly flagged with fix requirements; override requires rationale.
          </div>
        </div>
      </Card>

      <Card title="Readiness Checkpoints">
        <ul className="space-y-2 text-sm text-slate-300">
          {CHECKPOINTS.map((c) => (
            <li key={c} className="border border-slate-700 rounded px-3 py-2">{c}</li>
          ))}
        </ul>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => {
              logAuditEvent({
                eventType: 'srp_rop_twg_change',
                actor: 'taaip.engine',
                message: 'TWG readiness override justification submitted',
                target: 'twg-checkpoint',
              });
            }}
            className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
          >
            Log TWG Change
          </button>
          <button
            onClick={() => {
              pushNotification({
                title: 'Targeting Cycle Alert',
                message: 'TWG package deadline is within 24 hours.',
                category: 'targeting',
                severity: 'warning',
                source: 'TWG Workflow',
              });
            }}
            className="rounded border border-[#1D3A5C] bg-[#0B1F3A] px-3 py-1.5 text-xs text-slate-200 hover:bg-[#122A4A]"
          >
            Trigger Deadline Alert
          </button>
        </div>
      </Card>

      <TargetingWorkingGroup />
    </div>
  );
};

export default TWGPage;
