import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowLeft, ArrowRight, RefreshCw } from 'lucide-react';

import { API_BASE } from '../config/api';
import { asArray, asNumber, asText, toPercent } from './operationalData';

interface MissionAdjustmentDashboardProps {
  onNavigate: (tab: string) => void;
}

type AnyRecord = Record<string, any>;

const initialForm = {
  org_id: '1A1D',
  period_start: '2026-01-01',
  period_end: '2026-01-31',
};

export const MissionAdjustmentDashboard: React.FC<MissionAdjustmentDashboardProps> = ({ onNavigate }) => {
  const [formState, setFormState] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnyRecord | null>(null);

  const loadAdjustment = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...formState,
        include_evidence: true,
        force_refresh: true,
      };

      let response = await fetch(`${API_BASE}/api/v2/decision-output/mission-adjustment-justification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.status === 404) {
        response = await fetch(`${API_BASE}/api/v2/decision-output/mission-decrease-justification`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      }

      if (!response.ok) {
        throw new Error(`Mission adjustment returned ${response.status}`);
      }

      const body = await response.json();
      const data = body?.data || body;
      if (!data || typeof data !== 'object') {
        throw new Error('Mission adjustment payload was empty');
      }

      setResult(data as AnyRecord);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to generate mission adjustment');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAdjustment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mission = (result?.mission_delta_summary || {}) as AnyRecord;
  const confidence = (result?.confidence || {}) as AnyRecord;
  const signals = (result?.signal_summaries || {}) as Record<string, AnyRecord>;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 p-6 text-white shadow-xl">
        <p className="text-xs uppercase tracking-[0.25em] text-emerald-200">Step 2 of 6</p>
        <h1 className="mt-2 text-3xl font-bold">Mission Feasibility and Adjustment</h1>
        <p className="mt-2 max-w-3xl text-sm text-emerald-100">
          This workflow step stays inside the commander sequence and uses the live mission-adjustment endpoint rather than a standalone mock view.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-4">
          <label className="text-sm font-medium text-slate-700">
            Org ID
            <input
              value={formState.org_id}
              onChange={(event) => setFormState((current) => ({ ...current, org_id: event.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Period start
            <input
              type="date"
              value={formState.period_start}
              onChange={(event) => setFormState((current) => ({ ...current, period_start: event.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Period end
            <input
              type="date"
              value={formState.period_end}
              onChange={(event) => setFormState((current) => ({ ...current, period_end: event.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </label>
          <div className="flex items-end">
            <button
              onClick={() => void loadAdjustment()}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-600"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh justification
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-slate-700 shadow-sm">
          Loading real mission-feasibility output.
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-900 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5" />
            <div>
              <h2 className="font-semibold">Mission adjustment unavailable</h2>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && result && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Current total</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asNumber(mission.current_period?.mission_total).toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Baseline total</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asNumber(mission.baseline_period?.mission_total).toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Delta</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asNumber(mission.delta).toLocaleString()}</p>
              <p className="mt-1 text-sm text-slate-600">{toPercent(mission.delta_pct)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">Confidence</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{asText(confidence.band)}</p>
              <p className="mt-1 text-sm text-slate-600">Score {asNumber(confidence.score).toFixed(2)}</p>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Executive summary</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                {asArray<string>(result.executive_summary).length > 0 ? (
                  asArray<string>(result.executive_summary).slice(0, 5).map((item) => <li key={item}>{item}</li>)
                ) : (
                  <li>No mission summary is available for this scope.</li>
                )}
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Connected evidence signals</h2>
              <div className="mt-3 space-y-3">
                {Object.entries(signals).length > 0 ? (
                  Object.entries(signals).map(([key, value]) => (
                    <div key={key} className="rounded-lg border border-slate-200 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium capitalize text-slate-800">{key.split('_').join(' ')}</span>
                        <span className="text-xs text-slate-500">
                          {asText(value?.source_dataset_name || value?.summary?.overall_status || value?.summary?.overall_market_status, 'connected')}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-600">Rows used: {asNumber(value?.rows_used)}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-600">No connected signals were returned for this scope.</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('command-center')}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Command Center
        </button>
        <button
          onClick={() => onNavigate('diagnostics')}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-600"
        >
          Continue to Diagnostics
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default MissionAdjustmentDashboard;
