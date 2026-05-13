import React, { useMemo } from 'react';
import { Calendar, CheckCircle2, Clock, Layers, Target, Users } from 'lucide-react';

type PhaseCode = 'Q-1' | 'Q+0' | 'Q+1' | 'Q+2' | 'Q+3' | 'Q+4';

interface CyclePhase {
  code: PhaseCode;
  name: string;
  requiredActions: string[];
  previousOutputs: string[];
  upcomingActions: string[];
}

interface CalendarItem {
  phase: PhaseCode;
  projection: string;
  events: string[];
}

const PHASES: CyclePhase[] = [
  {
    code: 'Q-1',
    name: 'Assess',
    requiredActions: [
      'Validate market posture and intelligence baselines',
      'Review prior quarter performance and gaps',
      'Confirm input package readiness for execute phase',
    ],
    previousOutputs: [
      'Prior quarter AAR rollup',
      'Last cycle performance scorecard',
      'Updated baseline intelligence picture',
    ],
    upcomingActions: [
      'Feed synchronized targets to execute phase',
      'Finalize risk assumptions for Q+0',
    ],
  },
  {
    code: 'Q+0',
    name: 'Execute',
    requiredActions: [
      'Run synchronized targeting execution plan',
      'Track phase tasks and event delivery against plan',
      'Capture execution deviations and decision triggers',
    ],
    previousOutputs: [
      'Assess phase targeting package',
      'Validated target list and assumptions',
    ],
    upcomingActions: [
      'Prepare execution outcomes for review phase',
      'Compile initial variance report for TWG',
    ],
  },
  {
    code: 'Q+1',
    name: 'Review',
    requiredActions: [
      'Review execution outcomes and conversion indicators',
      'Identify retained, adjusted, and dropped targets',
      'Draft updates for validation cycle',
    ],
    previousOutputs: [
      'Execution results and event outcomes',
      'Variance and issue log',
    ],
    upcomingActions: [
      'Submit recommendation set for validation',
      'Queue resource implications for Q+2',
    ],
  },
  {
    code: 'Q+2',
    name: 'Validate',
    requiredActions: [
      'Validate recommendations and resource assumptions',
      'Reconcile feasibility and constraints by unit',
      'Lock candidate decisions for board approval',
    ],
    previousOutputs: [
      'TWG review recommendations',
      'Updated targeting assumptions',
    ],
    upcomingActions: [
      'Build approval package for Targeting Board',
      'Prepare decision-ready options',
    ],
  },
  {
    code: 'Q+3',
    name: 'Approve',
    requiredActions: [
      'Adjudicate targeting options and approve decisions',
      'Assign implementation ownership and due dates',
      'Publish approved targeting decision set',
    ],
    previousOutputs: [
      'Validated recommendation package',
      'Decision option matrix and impacts',
    ],
    upcomingActions: [
      'Issue board guidance to implementing teams',
      'Transition approved decisions into guidance phase',
    ],
  },
  {
    code: 'Q+4',
    name: 'Guidance',
    requiredActions: [
      'Publish approved targeting guidance',
      'Confirm operational handoff to planning and execution',
      'Set assessment checkpoints for next cycle',
    ],
    previousOutputs: [
      'Approved board decision set',
      'Assigned implementation owners and due dates',
    ],
    upcomingActions: [
      'Launch next cycle assess preparation',
      'Carry forward unresolved dependencies',
    ],
  },
];

const CALENDAR: CalendarItem[] = [
  {
    phase: 'Q-1',
    projection: 'Quarter prep window',
    events: ['Fusion Cell assessment sync', 'Baseline intelligence refresh'],
  },
  {
    phase: 'Q+0',
    projection: 'Current quarter execution',
    events: ['Execution event set', 'Quarter kickoff synchronization'],
  },
  {
    phase: 'Q+1',
    projection: 'Post-execution review',
    events: ['TWG review session', 'Outcome and variance review'],
  },
  {
    phase: 'Q+2',
    projection: 'Validation cycle',
    events: ['Validation working session', 'Resource feasibility sync'],
  },
  {
    phase: 'Q+3',
    projection: 'Decision approval window',
    events: ['Targeting Board approval session', 'Decision publication'],
  },
  {
    phase: 'Q+4',
    projection: 'Guidance release window',
    events: ['Guidance rollout', 'Next-cycle assess checkpoint'],
  },
];

const CURRENT_PHASE: PhaseCode = 'Q+0';

const getFiscalQuarter = (date: Date): string => {
  const month = date.getMonth() + 1;
  if (month >= 10) return 'Q1';
  if (month >= 1 && month <= 3) return 'Q2';
  if (month >= 4 && month <= 6) return 'Q3';
  return 'Q4';
};

export const TargetingCyclePage: React.FC = () => {
  const currentDate = new Date();
  const currentFiscalQuarter = getFiscalQuarter(currentDate);

  const currentPhase = useMemo(
    () => PHASES.find((phase) => phase.code === CURRENT_PHASE) || PHASES[1],
    []
  );

  return (
    <div className="space-y-6">
      <div className="rounded-md border border-slate-200 bg-white p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Targeting Cycle</h1>
            <p className="mt-2 text-sm text-slate-600">
              Full targeting cycle from Assess through Guidance with phase-aligned execution and decision points.
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Current Phase</p>
            <p className="text-lg font-semibold text-slate-900">
              {currentPhase.name} ({currentPhase.code})
            </p>
            <p className="mt-1 text-xs text-slate-500">Current Quarter: {currentFiscalQuarter}</p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-md border border-slate-200 bg-white p-4">
        <div className="flex min-w-[1100px] items-center gap-3">
          {PHASES.map((phase, index) => {
            const active = phase.code === CURRENT_PHASE;
            return (
              <React.Fragment key={phase.code}>
                <div
                  className={`flex-1 rounded-md border p-4 ${
                    active
                      ? 'border-amber-400 bg-amber-50'
                      : 'border-slate-200 bg-slate-50'
                  }`}
                >
                  <p className="text-sm font-semibold text-slate-900">{phase.name} ({phase.code})</p>
                  {active && (
                    <div className="mt-2 inline-flex items-center gap-1 rounded bg-amber-200 px-2 py-0.5 text-[11px] font-semibold text-slate-900">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Current
                    </div>
                  )}
                </div>
                {index < PHASES.length - 1 && (
                  <div className="h-px w-8 bg-slate-300" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-700">Previous Phase Outputs</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
            {currentPhase.previousOutputs.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-md border border-amber-300 bg-amber-50 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-700">Current Phase Required Actions</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-800">
            {currentPhase.requiredActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-700">Upcoming Actions</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
            {currentPhase.upcomingActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-700">Meeting Alignment by Phase</h2>
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-slate-700" />
              <p className="text-sm font-semibold text-slate-900">Fusion Cell</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">Aligned Phase: Assess (Q-1)</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-slate-700" />
              <p className="text-sm font-semibold text-slate-900">TWG</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">Aligned Phases: Execute (Q+0) and Review (Q+1)</p>
          </div>
          <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-slate-700" />
              <p className="text-sm font-semibold text-slate-900">Targeting Board</p>
            </div>
            <p className="mt-2 text-sm text-slate-700">Aligned Phase: Approve (Q+3)</p>
          </div>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-slate-700" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.12em] text-slate-700">Cycle Calendar and Quarterly Projections</h2>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[880px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left">
                <th className="px-3 py-2 font-semibold text-slate-700">Phase</th>
                <th className="px-3 py-2 font-semibold text-slate-700">Projection Window</th>
                <th className="px-3 py-2 font-semibold text-slate-700">Phase-Tied Events</th>
              </tr>
            </thead>
            <tbody>
              {CALENDAR.map((item) => (
                <tr key={item.phase} className="border-b border-slate-100">
                  <td className="px-3 py-2 font-medium text-slate-900">{item.phase}</td>
                  <td className="px-3 py-2 text-slate-700">{item.projection}</td>
                  <td className="px-3 py-2 text-slate-700">
                    {item.events.join(' | ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-md border border-slate-200 bg-white p-5">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Assess</p>
            <p className="mt-1 text-sm text-slate-700">Fusion Cell execution page handles Assess meeting execution details.</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Execute/Review</p>
            <p className="mt-1 text-sm text-slate-700">TWG execution page handles Execute/Review meeting execution details.</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Approve</p>
            <p className="mt-1 text-sm text-slate-700">Targeting Board execution page handles approval decision execution details.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TargetingCyclePage;
