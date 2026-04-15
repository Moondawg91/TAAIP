import React from 'react';
import {
  ArrowRight,
  BarChart3,
  ClipboardList,
  LineChart,
  PanelLeft,
  Shield,
  Users,
  Workflow,
} from 'lucide-react';

interface HomeScreenProps {
  perspective: 'commander' | 'operator420t' | 'admin';
  allowedTabs: string[];
  onNavigate: (tab: string) => void;
}

const workflowSteps = [
  {
    id: 'command-center',
    step: '01',
    title: 'Command Center',
    description: 'Start with the live command picture, alerts, LOEs, and connected operational blocks.',
    icon: PanelLeft,
    tone: 'from-slate-900 to-slate-700',
  },
  {
    id: 'mission-adjustment',
    step: '02',
    title: 'Mission Adjustment',
    description: 'Move directly from command picture to feasibility and adjustment justification.',
    icon: ClipboardList,
    tone: 'from-emerald-800 to-emerald-600',
  },
  {
    id: 'diagnostics',
    step: '03',
    title: 'Market to ROI Diagnostics',
    description: 'Review market, funnel, school, and ROI drivers using the connected backend outputs.',
    icon: BarChart3,
    tone: 'from-blue-800 to-blue-600',
  },
  {
    id: 'decision-sync',
    step: '04',
    title: 'TWG and Targeting Board',
    description: 'Carry the diagnostic picture into decision sync, board posture, and downstream tasking.',
    icon: Users,
    tone: 'from-violet-800 to-violet-600',
  },
  {
    id: 'execution',
    step: '05',
    title: 'Asset, Execution, and Processing',
    description: 'Validate feasibility, task execution, and flash-to-bang health in one view.',
    icon: Workflow,
    tone: 'from-amber-700 to-amber-500',
  },
  {
    id: 'powerbi',
    step: '06',
    title: 'Power BI Export Surface',
    description: 'Finish on the export-facing operational surface for reporting and briefing.',
    icon: LineChart,
    tone: 'from-slate-700 to-slate-500',
  },
] as const;

export const HomeScreen: React.FC<HomeScreenProps> = ({ perspective, allowedTabs, onNavigate }) => {
  const allowed = new Set(allowedTabs);
  const visibleSteps = workflowSteps.filter((step) => allowed.has(step.id));

  const perspectiveMessage =
    perspective === 'admin'
      ? 'Admin/maintainer view keeps refresh and maintenance controls separate from commander decision flow.'
      : perspective === 'operator420t'
        ? '420T operator view focuses on drill-down evidence and execution surfaces without admin controls.'
        : 'Commander view keeps the full decision sequence from command picture through export surfaces.';

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-black via-slate-900 to-black p-8 text-white shadow-xl">
        <div className="flex items-center gap-4">
          <Shield className="h-12 w-12 text-amber-400" />
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-amber-300">Commander workflow</p>
            <h1 className="mt-2 text-3xl font-bold">One connected operational sequence</h1>
            <p className="mt-3 max-w-4xl text-sm text-slate-200">
              Duplicate standalone workflow views have been consolidated into a single commander-ready path that consumes the completed backend system without recreating its logic in the frontend.
            </p>
            <p className="mt-2 max-w-4xl text-sm text-amber-200">{perspectiveMessage}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleSteps.map((step) => {
          const Icon = step.icon;
          return (
            <button
              key={step.id}
              onClick={() => onNavigate(step.id)}
              className="group overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg"
            >
              <div className={`bg-gradient-to-r ${step.tone} p-4 text-white`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-[0.25em] text-slate-100">STEP {step.step}</span>
                  <Icon className="h-6 w-6" />
                </div>
                <h2 className="mt-3 text-xl font-bold">{step.title}</h2>
              </div>
              <div className="p-4">
                <p className="text-sm text-slate-600">{step.description}</p>
                <div className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-slate-900">
                  Open step
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">What changed in this pass</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
          <li>Command Center now leads the workflow instead of leaving Mission Adjustment isolated.</li>
          <li>Market, funnel, school, and ROI diagnostics are grouped into one operational decision layer.</li>
          <li>TWG and Targeting Board now sit together as the next commander action step.</li>
          <li>Asset, execution, and processing are presented as one downstream execution surface.</li>
          <li>Admin-only maintenance controls stay isolated from commander and 420T workflow views.</li>
        </ul>
      </div>
    </div>
  );
};
