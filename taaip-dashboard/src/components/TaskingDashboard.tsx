import React from 'react';
import { CheckSquare, CalendarClock, AlertTriangle } from 'lucide-react';

export const TaskingDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="rounded-md border border-slate-200 bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Tasking</h1>
        <p className="mt-2 text-sm text-slate-600">
          This page owns execution tasking status, assignment accountability, and completion discipline.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <CheckSquare className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Assigned Tasks</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Review tasks by owner, unit, and priority to ensure clear ownership.
          </p>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Due Timeline</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Track due dates and milestone windows to keep execution on timeline.
          </p>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">At-Risk Work</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Surface blocked and overdue tasking so command can resolve bottlenecks quickly.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TaskingDashboard;
