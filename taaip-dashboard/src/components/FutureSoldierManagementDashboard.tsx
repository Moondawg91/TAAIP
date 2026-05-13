import React from 'react';
import { Users, Clock, ShieldCheck } from 'lucide-react';

export const FutureSoldierManagementDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="rounded-md border border-slate-200 bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Future Soldier Management</h1>
        <p className="mt-2 text-sm text-slate-600">
          This page owns Future Soldier readiness, engagement cadence, and ship-date discipline.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Readiness</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Track contracted Future Soldiers by readiness state and validate preparation plans.
          </p>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Engagement</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Maintain orientation, check-ins, and event participation timelines to prevent attrition.
          </p>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-slate-700" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Ship Discipline</h2>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Confirm blockers, waivers, and timeline risks to protect projected ship dates.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FutureSoldierManagementDashboard;
