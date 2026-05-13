import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCw, AlertTriangle } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

interface Activity {
  activity_id: string;
  activity_name: string;
  activity_type: string;
  event_date: string;
  start_time: string;
  end_time: string;
  company: string;
  rsid: string;
  location: string;
  lead_source: string;
  assigned_recruiters: string[];
  linked_operation_id: string;
  linked_operation_name: string;
  source_nomination_id: string;
  source_board_decision_id: string;
  planned: number;
  executed: number;
  cancelled: number;
  status: 'Planned' | 'Executed' | 'Cancelled';
  turnout_count: number;
  leads_generated: number;
  engagements: number;
  contracts: number;
  notes: string;
  issues: string[];
  activity_gaps: string[];
  created_at: string;
  updated_at: string;
}

interface Summary {
  total_activities: number;
  planned: number;
  executed: number;
  cancelled: number;
}

interface Performance {
  total_leads: number;
  total_engagements: number;
  total_contracts: number;
}

interface GapRow {
  gap: string;
  count: number;
}

interface Payload {
  status: string;
  activities: Activity[];
  summary: Summary;
  performance: Performance;
  activity_gaps: GapRow[];
  companies: string[];
  rsids: string[];
  activity_types: string[];
  data_as_of: string;
}

const TIMEFRAMES = ['FY26 Q1', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25'];

const EMPTY_SUMMARY: Summary = {
  total_activities: 0,
  planned: 0,
  executed: 0,
  cancelled: 0,
};

const EMPTY_PERFORMANCE: Performance = {
  total_leads: 0,
  total_engagements: 0,
  total_contracts: 0,
};

function safePct(value: number, base: number): number {
  if (!base) return 0;
  return Math.round((value / base) * 100);
}

function statusBadge(status: string): string {
  if (status === 'Executed') return 'bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30';
  if (status === 'Cancelled') return 'bg-[#EF4444]/20 text-[#EF4444] border border-[#EF4444]/30';
  return 'bg-[#64748B]/20 text-[#94A3B8] border border-[#64748B]/30';
}

export const FieldActivitiesDashboard: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({ activities: 'table' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [timeframe, setTimeframe] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [rsidFilter, setRsidFilter] = useState('');
  const [activityTypeFilter, setActivityTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [activities, setActivities] = useState<Activity[]>([]);
  const [summary, setSummary] = useState<Summary>(EMPTY_SUMMARY);
  const [performance, setPerformance] = useState<Performance>(EMPTY_PERFORMANCE);
  const [activityGaps, setActivityGaps] = useState<GapRow[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [rsids, setRsids] = useState<string[]>([]);
  const [activityTypes, setActivityTypes] = useState<string[]>([]);
  const [dataAsOf, setDataAsOf] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeframe) params.set('timeframe', timeframe);
      if (companyFilter) params.set('company', companyFilter);
      if (rsidFilter) params.set('rsid', rsidFilter);
      if (activityTypeFilter) params.set('activity_type', activityTypeFilter);
      if (statusFilter) params.set('status', statusFilter);

      const res = await fetch(`${API_BASE}/api/v2/field-activities/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      setActivities(payload.activities ?? []);
      setSummary(payload.summary ?? EMPTY_SUMMARY);
      setPerformance(payload.performance ?? EMPTY_PERFORMANCE);
      setActivityGaps(payload.activity_gaps ?? []);
      setCompanies(payload.companies ?? []);
      setRsids(payload.rsids ?? []);
      setActivityTypes(payload.activity_types ?? []);
      setDataAsOf(payload.data_as_of ?? '');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load field activities');
    } finally {
      setLoading(false);
    }
  }, [timeframe, companyFilter, rsidFilter, activityTypeFilter, statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (activities.length === 0) {
      setSelectedId(null);
      return;
    }
    const stillVisible = selectedId && activities.some((a) => a.activity_id === selectedId);
    if (!stillVisible) {
      setSelectedId(activities[0].activity_id);
    }
  }, [activities, selectedId]);

  const selected = useMemo(
    () => activities.find((a) => a.activity_id === selectedId) ?? null,
    [activities, selectedId],
  );

  const insights = useMemo(() => {
    const executed = activities.filter((a) => a.status === 'Executed');
    const highLow = executed.filter((a) => a.turnout_count >= 10 && a.leads_generated <= 1).length;
    const lowHigh = executed.filter((a) => a.turnout_count <= 4 && a.contracts >= 1).length;
    const followUpGap = executed.filter((a) => a.engagements > 0 && a.contracts === 0).length;
    const misalignedEffort = activities.filter((a) => !a.linked_operation_id).length;

    const typeMap: Record<string, { acts: number; leads: number }> = {};
    activities.forEach((a) => {
      const key = a.activity_type || 'Unknown';
      typeMap[key] = typeMap[key] || { acts: 0, leads: 0 };
      typeMap[key].acts += 1;
      typeMap[key].leads += a.leads_generated || 0;
    });

    let topType = 'None';
    let topRatio = -1;
    Object.entries(typeMap).forEach(([k, v]) => {
      const ratio = v.leads / Math.max(v.acts, 1);
      if (ratio > topRatio) {
        topRatio = ratio;
        topType = k;
      }
    });

    const hotspot = activities.reduce((acc, a) => {
      const key = a.location || 'Unknown';
      acc[key] = (acc[key] || 0) + (a.leads_generated || 0);
      return acc;
    }, {} as Record<string, number>);
    const topHotspot = Object.entries(hotspot).sort((a, b) => b[1] - a[1])[0]?.[0] || 'None';

    return {
      highLow,
      lowHigh,
      followUpGap,
      topType,
      misalignedEffort,
      topHotspot,
    };
  }, [activities]);

  const resetFilters = (): void => {
    setTimeframe('');
    setCompanyFilter('');
    setRsidFilter('');
    setActivityTypeFilter('');
    setStatusFilter('');
  };

  const openLinkedOperation = (operationId: string): void => {
    const qp = new URLSearchParams({ activeTab: 'execution-operations', operation_id: operationId }).toString();
    window.open(`/?${qp}`, '_blank');
  };


  const statusColor = (s: 'Planned' | 'Executed' | 'Cancelled'): string => {
    if (s === 'Executed') return '#10B981';
    if (s === 'Planned') return '#60A5FA';
    return '#EF4444';
  };

  const darkTable = (headers: string[], body: React.ReactNode) => (
    <div className="overflow-x-auto">
      <table className="min-w-full text-[12px]">
        <thead>
          <tr className="border-b border-[#1D3A5C]">
            {headers.map((h) => (
              <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  );

  return (
    <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Field Activities</h1>
        <p className="text-[12px] text-[#64748B] mt-0.5">Execution engagement — events, turnout, lead generation, contract results</p>
      </div>

      {/* Perspective Selector */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap gap-2">
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Timeframes</option>
          {TIMEFRAMES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Companies</option>
          {companies.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={rsidFilter} onChange={(e) => setRsidFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {rsids.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <select value={activityTypeFilter} onChange={(e) => setActivityTypeFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Types</option>
          {activityTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Statuses</option>
          {['Planned', 'Executed', 'Cancelled'].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
      </div>

      {error && <div className="mb-4 p-3 rounded border border-[#EF4444] bg-[#EF444422] text-[#EF4444] text-[13px]">{error}</div>}
      {loading && <div className="text-[13px] text-[#64748B] mb-4">Loading...</div>}

      {/* KPI Row */}
      <div className="mb-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Activities', value: summary.total_activities, color: '#60A5FA' },
          { label: 'Total Leads', value: performance.total_leads, color: '#10B981' },
          { label: 'Total Engagements', value: performance.total_engagements, color: '#F59E0B' },
          { label: 'Total Contracts', value: performance.total_contracts, color: '#10B981' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-3">
            <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">{label}</div>
            <div className="text-[20px] font-bold" style={{ color }}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* LEFT: Activities table */}
        <div className="xl:col-span-2">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Activities ({activities.length})</span>
              <VisualModeSwitch value={viewBySection.activities} onChange={(v) => setViewBySection((prev) => ({ ...prev, activities: v }))} />
            </div>
            {viewBySection.activities === 'table' ? darkTable(
              ['Activity','Type','Date','Status','Leads','Operation Link'],
              activities.length ? activities.map((a) => (
                <tr key={a.activity_id} onClick={() => setSelectedId(a.activity_id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedId === a.activity_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7] font-medium">{a.activity_name}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{a.activity_type}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{new Date(a.event_date).toLocaleDateString()}</td>
                  <td className="px-3 py-2"><span style={{ color: statusColor(a.status) }}>{a.status}</span></td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{a.leads_generated}</td>
                  <td className="px-3 py-2 text-[#60A5FA] underline cursor-pointer" onClick={(e) => { e.stopPropagation(); a.linked_operation_id && openLinkedOperation(a.linked_operation_id); }}>{a.linked_operation_name || '—'}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No activities</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {activities.length > 0 ? activities.map((a) => (
                  <div key={a.activity_id} onClick={() => setSelectedId(a.activity_id)}
                    className={`bg-[#142F52] border rounded p-3 cursor-pointer ${selectedId === a.activity_id ? 'border-[#1D4ED8]' : 'border-[#1D3A5C] hover:border-[#1D4ED8]/50'}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[13px] text-[#F3F5F7] font-semibold">{a.activity_name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${statusBadge(a.status)}`}>{a.status}</span>
                    </div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{a.activity_type} · {new Date(a.event_date).toLocaleDateString()} · Leads: {a.leads_generated}</div>
                  </div>
                )) : <div className="text-[13px] text-[#64748B]">No activities</div>}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Detail panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Activity Detail</div>
            {!selected && (
              <div className="text-[13px] text-[#64748B]">Select an activity to view details.</div>
            )}
            {selected && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selected.activity_name}</div>
                  <div className="text-[12px] text-[#64748B]">{selected.activity_type} · {selected.location}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Status', value: selected.status, color: statusColor(selected.status) },
                    { label: 'Date', value: new Date(selected.event_date).toLocaleDateString(), color: '#F3F5F7' },
                    { label: 'Turnout', value: String(selected.turnout_count), color: '#F3F5F7' },
                    { label: 'Leads', value: String(selected.leads_generated), color: '#10B981' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</div>
                      <div className="text-[13px] font-semibold" style={{ color }}>{value}</div>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">Engagements</div>
                    <div className="text-[13px] font-semibold text-[#F59E0B]">{selected.engagements}</div>
                  </div>
                  <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">Contracts</div>
                    <div className="text-[13px] font-semibold text-[#10B981]">{selected.contracts}</div>
                  </div>
                </div>
                {selected.notes && (
                  <div>
                    <div className="text-[10px] uppercase text-[#64748B] mb-1">Notes</div>
                    <div className="text-[13px] text-[#94A3B8]">{selected.notes}</div>
                  </div>
                )}
              </>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};

export default FieldActivitiesDashboard;
