import React from 'react';
import { ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react';

import { asArray, asNumber, asText, useOperationalCommandData } from './operationalData';

interface TargetingWorkingGroupProps {
  onNavigate: (tab: string) => void;
}

export const TargetingWorkingGroup: React.FC<TargetingWorkingGroupProps> = ({ onNavigate }) => {
  const { data, loading, error, refresh } = useOperationalCommandData();

  const twgSummary = (data?.twg_summary || {}) as Record<string, any>;
  const boardSummary = (data?.board_summary || {}) as Record<string, any>;
  const twgItems = asArray<Record<string, any>>(data?.twg_prioritized_items);
  const boardItems = asArray<Record<string, any>>(data?.board_prioritized_items);
  const boardTasks = asArray<Record<string, any>>(data?.board_downstream_tasks);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-violet-900 via-violet-800 to-violet-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-violet-200">Step 4 of 6</p>
            <h1 className="mt-2 text-3xl font-bold">TWG and Targeting Board</h1>
            <p className="mt-2 max-w-3xl text-sm text-violet-100">
              Decision synchronization is consolidated here so commanders can move from diagnostics into tasking without losing the workflow thread.
            </p>
          </div>
          <button
            onClick={() => void refresh()}
            className="inline-flex items-center gap-2 rounded-lg border border-violet-500 bg-violet-700 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-600"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">Loading the decision-sync layer.</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm">{error}</div>}

      {!loading && !error && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              ['TWG items', asNumber(twgSummary.total_items)],
              ['TWG board elevations', asNumber(twgSummary.board_elevation_count)],
              ['Board items', asNumber(boardSummary.total_items)],
              ['Board resource shifts', asNumber(boardSummary.resource_shift_count)],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">TWG priorities</h2>
              <div className="mt-3 space-y-3">
                {twgItems.length > 0 ? twgItems.slice(0, 6).map((item, index) => (
                  <div key={item.item_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.title || item.item_id || `TWG item ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Priority: {asText(item.priority || item.priority_band || twgSummary.overall_twg_status)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No TWG items are available for the current scope.</p>}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Targeting Board directives</h2>
              <div className="mt-3 space-y-3">
                {boardItems.length > 0 ? boardItems.slice(0, 6).map((item, index) => (
                  <div key={item.board_item_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.title || item.board_item_id || `Board item ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Posture: {asText(item.status || boardSummary.overall_board_posture)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No board-directed items are active for this scope.</p>}
              </div>

              <div className="mt-4 border-t border-slate-200 pt-4">
                <h3 className="font-medium text-slate-900">Downstream tasks</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {boardTasks.length > 0 ? boardTasks.slice(0, 5).map((task, index) => (
                    <li key={task.task_id || index}>{asText(task.title || task.task_id || task.action)}</li>
                  )) : <li>No downstream tasking has been emitted yet.</li>}
                </ul>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('diagnostics')}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Diagnostics
        </button>
        <button
          onClick={() => onNavigate('execution')}
          className="inline-flex items-center gap-2 rounded-lg bg-violet-700 px-5 py-3 text-sm font-semibold text-white hover:bg-violet-600"
        >
          Continue to Asset and Execution
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default TargetingWorkingGroup;
