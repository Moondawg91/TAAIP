import React from 'react';
import { ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react';

import { asArray, asNumber, asText, useOperationalCommandData } from './operationalData';

interface ExecutionWorkflowDashboardProps {
  onNavigate: (tab: string) => void;
}

export const ExecutionWorkflowDashboard: React.FC<ExecutionWorkflowDashboardProps> = ({ onNavigate }) => {
  const { data, loading, error, refresh } = useOperationalCommandData();

  const assetSummary = (data?.asset_summary || {}) as Record<string, any>;
  const processingSummary = (data?.processing_summary || {}) as Record<string, any>;
  const executionSummary = (data?.execution_summary || {}) as Record<string, any>;

  const assetDistribution = asArray<Record<string, any>>(data?.asset_distribution);
  const shifts = asArray<Record<string, any>>(data?.asset_recommended_shifts);
  const processingItems = asArray<Record<string, any>>(data?.processing_items);
  const stalledItems = asArray<Record<string, any>>(data?.processing_stalled_items);
  const executionItems = asArray<Record<string, any>>(data?.execution_items);
  const blockedItems = asArray<Record<string, any>>(data?.blocked_items);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-amber-900 via-amber-800 to-amber-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-amber-200">Step 5 of 6</p>
            <h1 className="mt-2 text-3xl font-bold">Asset, Execution, and Processing</h1>
            <p className="mt-2 max-w-3xl text-sm text-amber-100">
              This execution view keeps feasibility, tracker status, and flash-to-bang processing together so commanders can see the downstream effect of board decisions.
            </p>
          </div>
          <button
            onClick={() => void refresh()}
            className="inline-flex items-center gap-2 rounded-lg border border-amber-500 bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">Loading execution flow.</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm">{error}</div>}

      {!loading && !error && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Asset posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(assetSummary.feasibility_posture)}</p>
              <p className="mt-1 text-sm text-slate-600">Assets {asNumber(assetSummary.total_assets)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Execution posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(executionSummary.execution_posture)}</p>
              <p className="mt-1 text-sm text-slate-600">Tasks {asNumber(executionSummary.total_tasks)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Processing posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(processingSummary.processing_posture)}</p>
              <p className="mt-1 text-sm text-slate-600">Items {asNumber(processingSummary.total_processing_items)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Execution risk</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(assetSummary.execution_risk_level)}</p>
              <p className="mt-1 text-sm text-slate-600">Blocked {asNumber(executionSummary.blocked)}</p>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Asset distribution</h2>
              <div className="mt-3 space-y-3">
                {assetDistribution.length > 0 ? assetDistribution.slice(0, 5).map((item, index) => (
                  <div key={item.asset_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.asset_name || item.asset_id || `Asset ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Status {asText(item.status || item.allocation_status || assetSummary.feasibility_posture)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No asset allocations are active for this scope.</p>}
              </div>

              <div className="mt-4 border-t border-slate-200 pt-4">
                <h3 className="font-medium text-slate-900">Recommended shifts</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {shifts.length > 0 ? shifts.slice(0, 4).map((shift, index) => (
                    <li key={shift.shift_id || index}>{asText(shift.title || shift.recommendation || shift.action)}</li>
                  )) : <li>No asset shifts are currently required.</li>}
                </ul>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Execution tracker</h2>
              <div className="mt-3 space-y-3">
                {executionItems.length > 0 ? executionItems.slice(0, 5).map((item, index) => (
                  <div key={item.task_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.title || item.task_id || `Task ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Status {asText(item.status || executionSummary.execution_posture)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No execution tasks are active for this scope.</p>}
              </div>

              <div className="mt-4 border-t border-slate-200 pt-4">
                <h3 className="font-medium text-slate-900">Blocked items</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {blockedItems.length > 0 ? blockedItems.slice(0, 4).map((item, index) => (
                    <li key={item.task_id || index}>{asText(item.title || item.reason || item.task_id)}</li>
                  )) : <li>No blocked execution items.</li>}
                </ul>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Flash to bang processing</h2>
              <div className="mt-3 space-y-3">
                {processingItems.length > 0 ? processingItems.slice(0, 5).map((item, index) => (
                  <div key={item.processing_item_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.title || item.processing_item_id || `Processing item ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Status {asText(item.status || processingSummary.processing_posture)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No processing items are active for this scope.</p>}
              </div>

              <div className="mt-4 border-t border-slate-200 pt-4">
                <h3 className="font-medium text-slate-900">Stalled items</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {stalledItems.length > 0 ? stalledItems.slice(0, 4).map((item, index) => (
                    <li key={item.processing_item_id || index}>{asText(item.title || item.reason || item.processing_item_id)}</li>
                  )) : <li>No stalled processing items.</li>}
                </ul>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('decision-sync')}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to TWG and Board
        </button>
        <button
          onClick={() => onNavigate('powerbi')}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-700 px-5 py-3 text-sm font-semibold text-white hover:bg-amber-600"
        >
          Continue to Power BI
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default ExecutionWorkflowDashboard;
