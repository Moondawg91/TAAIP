import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, CheckCircle2, RefreshCw, ShieldAlert } from 'lucide-react';

import { API_BASE } from '../config/api';
import { asNumber, asText } from './operationalData';

interface CommandCenterDashboardProps {
  onNavigate: (tab: string) => void;
}

type AnyRecord = Record<string, any>;

const statusTone = (value: string) => {
  const normalized = value.toLowerCase();
  if (normalized === 'ok' || normalized === 'balanced' || normalized === 'healthy') {
    return 'bg-green-100 text-green-800 border-green-200';
  }
  if (normalized.includes('watch') || normalized.includes('partial') || normalized.includes('degraded')) {
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  }
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const readStatus = (value: unknown): string => {
  if (value && typeof value === 'object' && 'status' in (value as AnyRecord)) {
    return asText((value as AnyRecord).status, 'unknown');
  }
  if (typeof value === 'string') {
    return value;
  }
  return 'unknown';
};

export const CommandCenterDashboard: React.FC<CommandCenterDashboardProps> = ({ onNavigate }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<AnyRecord | null>(null);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/command-center/overview?scope_type=USAREC&scope_value=USAREC`);
      if (!response.ok) {
        throw new Error(`Command Center returned ${response.status}`);
      }
      const payload = await response.json();
      if (payload?.status !== 'ok') {
        throw new Error('Command Center did not return an ok status');
      }
      setSummary((payload?.summary || {}) as AnyRecord);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load Command Center');
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  const phase2 = (summary?.phase2 || {}) as AnyRecord;
  const connectedBlocks = [
    ['Market', phase2.market_engine],
    ['Funnel', phase2.funnel_engine],
    ['School', phase2.school_access],
    ['ROI', phase2.roi_engine],
    ['TWG', phase2.twg_engine],
    ['Board', phase2.targeting_board_engine],
    ['Asset', phase2.asset_engine],
    ['Processing', phase2.flash_to_bang_processing],
    ['Execution', phase2.targeting_execution_tracker],
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-amber-300">Step 1 of 6</p>
            <h1 className="mt-2 text-3xl font-bold">Command Center</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-200">
              This view pulls the live command summary and connected phase-two workflow blocks from the authoritative backend.
            </p>
          </div>
          <button
            onClick={() => void loadOverview()}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-slate-700 shadow-sm">
          Loading the connected command picture.
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-900 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5" />
            <div>
              <h2 className="font-semibold">Command Center unavailable</h2>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && summary && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            {[
              ['Priorities', asNumber(summary.priorities_count)],
              ['LOEs', asNumber(summary.loes_count)],
              ['Alerts', asNumber(summary.alerts_count)],
              ['Behind Units', asNumber(summary.lead_line?.counts?.BEHIND)],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <h2 className="text-xl font-semibold text-slate-900">Connected operational blocks</h2>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {connectedBlocks.map(([label, value]) => {
                const status = readStatus(value);
                return (
                  <div key={label} className="rounded-lg border border-slate-200 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-slate-800">{label}</span>
                      <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${statusTone(status)}`}>
                        {status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-700" />
              <div>
                <h2 className="font-semibold text-amber-900">Next decision layer</h2>
                <p className="mt-1 text-sm text-amber-800">
                  Move directly into Mission Adjustment to turn the current command picture into a commander-ready feasibility call.
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="flex justify-end">
        <button
          onClick={() => onNavigate('mission-adjustment')}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Continue to Mission Adjustment
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default CommandCenterDashboard;
