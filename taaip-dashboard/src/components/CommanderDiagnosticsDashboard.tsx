import React from 'react';
import { ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react';

import { asArray, asNumber, asText, toPercent, useOperationalCommandData } from './operationalData';

interface CommanderDiagnosticsDashboardProps {
  onNavigate: (tab: string) => void;
}

export const CommanderDiagnosticsDashboard: React.FC<CommanderDiagnosticsDashboardProps> = ({ onNavigate }) => {
  const { data, loading, error, refresh } = useOperationalCommandData();

  const market = (data?.market_engine_summary || {}) as Record<string, any>;
  const funnel = (data?.funnel_engine_summary || {}) as Record<string, any>;
  const school = (data?.school_plan_summary || {}) as Record<string, any>;
  const roi = (data?.roi_summary || {}) as Record<string, any>;
  const accountability = (data?.accountability || {}) as Record<string, any>;
  const schools = asArray<Record<string, any>>(data?.school_plan_prioritized_schools);
  const events = asArray<Record<string, any>>(data?.roi_prioritized_events);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="mt-2 text-3xl font-bold">Market, Funnel, ROI &amp; Targeting Diagnostics</h1>
            <p className="mt-2 max-w-3xl text-sm text-blue-100">
              Market potential, funnel conversion, school access, ROI scoring, and targeting diagnostic signals from the live backend.
            </p>
          </div>
          <button
            onClick={() => void refresh()}
            className="inline-flex items-center gap-2 rounded-lg border border-blue-500 bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">Loading connected diagnostic signals.</div>}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 shadow-sm">{error}</div>}

      {!loading && !error && (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Market posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(market.overall_market_status)}</p>
              <p className="mt-1 text-sm text-slate-600">Capability {asNumber(market.market_capability_score).toFixed(1)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Funnel posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(funnel.overall_funnel_status)}</p>
              <p className="mt-1 text-sm text-slate-600">Lead to contract {toPercent(funnel.lead_to_contract_rate)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">School posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(school.overall_school_status)}</p>
              <p className="mt-1 text-sm text-slate-600">Priority schools {asNumber(school.priority_school_count)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">ROI posture</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asNumber(roi.total_events_scored)}</p>
              <p className="mt-1 text-sm text-slate-600">Average ROI {asNumber(roi.avg_roi_score).toFixed(2)}</p>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">School recruiting plan</h2>
              <div className="mt-3 space-y-3">
                {schools.length > 0 ? schools.slice(0, 5).map((item, index) => (
                  <div key={item.school_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.school_name || item.school_id || `School ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">Station {asText(item.station_rsid)} · Priority {asNumber(item.priority_score).toFixed(1)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No priority school actions are active for this scope.</p>}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">ROI and event effectiveness</h2>
              <div className="mt-3 space-y-3">
                {events.length > 0 ? events.slice(0, 5).map((item, index) => (
                  <div key={item.event_id || index} className="rounded-lg border border-slate-200 p-3">
                    <p className="font-medium text-slate-800">{asText(item.event_name || item.event_id || `Event ${index + 1}`)}</p>
                    <p className="mt-1 text-sm text-slate-600">ROI {asNumber(item.roi_score).toFixed(2)} · Leads {asNumber(item.leads_generated || item.total_leads)}</p>
                  </div>
                )) : <p className="text-sm text-slate-600">No scored events are active for this scope.</p>}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Accountability signal</h2>
            <p className="mt-3 text-sm text-slate-700">
              Classification: <span className="font-semibold text-slate-900">{asText(accountability.classification)}</span>
            </p>
            <p className="mt-1 text-sm text-slate-700">
              Recommended next action: <span className="font-semibold text-slate-900">{asText(accountability.recommended_next_action)}</span>
            </p>
          </div>
        </>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('mission')}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Mission Analysis
        </button>
        <button
          onClick={() => onNavigate('twg')}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-600"
        >
          Continue to TWG
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default CommanderDiagnosticsDashboard;
