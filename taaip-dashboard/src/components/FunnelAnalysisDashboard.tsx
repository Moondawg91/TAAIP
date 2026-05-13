import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type Insight = {
  label: string;
  value: number;
  unit: string;
};

type FunnelSnapshot = {
  total_leads: number;
  total_contacts: number;
  total_appointments: number;
  total_contracts: number;
  overall_conversion_rate: number;
};

type FunnelVisual = {
  leads: number;
  contacts: number;
  appointments: number;
  contracts: number;
};

type StagePerformance = {
  stage: string;
  count: number;
  conversion_from_previous: number;
  loss_count: number;
};

type TrendPoint = {
  period: string;
  leads: number;
  contacts: number;
  appointments: number;
  contracts: number;
  conversion_rate: number;
};

type EchelonRow = {
  echelon: string;
  leads: number;
  contacts: number;
  appointments: number;
  contracts: number;
  conversion_rate: number;
};

type AlertRow = {
  level: string;
  title: string;
  message: string;
};

type StageLossRow = {
  transition: string;
  from_count: number;
  to_count: number;
  loss_count: number;
  loss_rate: number;
};

type SourceRow = {
  source: string;
  leads: number;
  contacts: number;
  appointments: number;
  contracts: number;
  conversion_rate: number;
};

type Velocity = {
  lead_to_contact_days: number;
  contact_to_appointment_days: number;
  appointment_to_contract_days: number;
  overall_cycle_days: number;
};

type RootCause = {
  label: string;
  reason: string;
  impact: string;
};

type Payload = {
  data_as_of: string;
  insights_strip: Insight[];
  funnel_snapshot: FunnelSnapshot;
  funnel_visual: FunnelVisual;
  stage_performance: StagePerformance[];
  conversion_trend: TrendPoint[];
  funnel_by_echelon: EchelonRow[];
  top_performers: EchelonRow[];
  bottom_performers: EchelonRow[];
  alerts: AlertRow[];
  stage_loss_analysis: StageLossRow[];
  lead_source_analysis: SourceRow[];
  funnel_velocity: Velocity;
  expanded_funnel_by_echelon: EchelonRow[];
  root_cause_insights: RootCause[];
  companies: string[];
  rsids: string[];
  sources: string[];
};

const EMPTY_SNAPSHOT: FunnelSnapshot = {
  total_leads: 0,
  total_contacts: 0,
  total_appointments: 0,
  total_contracts: 0,
  overall_conversion_rate: 0,
};

const EMPTY_VISUAL: FunnelVisual = {
  leads: 0,
  contacts: 0,
  appointments: 0,
  contracts: 0,
};

const EMPTY_VELOCITY: Velocity = {
  lead_to_contact_days: 0,
  contact_to_appointment_days: 0,
  appointment_to_contract_days: 0,
  overall_cycle_days: 0,
};

const TIMEFRAMES = ['FY26 Q1', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25'];

type Tab = 'overview' | 'deep';

const fmtInt = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '0';
  return Math.round(value).toLocaleString();
};

const fmtPct = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '0.0%';
  return `${value.toFixed(1)}%`;
};

const alertClasses = (level: string): string => {
  const v = String(level || '').toLowerCase();
  if (v === 'high') return 'border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444]';
  if (v === 'medium') return 'border-[#F59E0B]/30 bg-[#F59E0B]/10 text-[#F59E0B]';
  return 'border-[#1D3A5C] bg-[#0E2847] text-[#94A3B8]';
};

export const FunnelAnalysisDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [perspective, setPerspective] = useState<PerspectiveMode>('analytical');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({
    snapshot: 'kpi', stagePerfomance: 'table', trend: 'table', echelon: 'table', performers: 'table',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [timeframe, setTimeframe] = useState('');
  const [company, setCompany] = useState('');
  const [rsid, setRsid] = useState('');
  const [source, setSource] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [insights, setInsights] = useState<Insight[]>([]);
  const [snapshot, setSnapshot] = useState<FunnelSnapshot>(EMPTY_SNAPSHOT);
  const [visual, setVisual] = useState<FunnelVisual>(EMPTY_VISUAL);
  const [stagePerformance, setStagePerformance] = useState<StagePerformance[]>([]);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [echelonRows, setEchelonRows] = useState<EchelonRow[]>([]);
  const [topPerformers, setTopPerformers] = useState<EchelonRow[]>([]);
  const [bottomPerformers, setBottomPerformers] = useState<EchelonRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [stageLoss, setStageLoss] = useState<StageLossRow[]>([]);
  const [sourceRows, setSourceRows] = useState<SourceRow[]>([]);
  const [velocity, setVelocity] = useState<Velocity>(EMPTY_VELOCITY);
  const [expandedEchelonRows, setExpandedEchelonRows] = useState<EchelonRow[]>([]);
  const [rootCauseRows, setRootCauseRows] = useState<RootCause[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [rsids, setRsids] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeframe) params.set('timeframe', timeframe);
      if (company) params.set('company', company);
      if (rsid) params.set('rsid', rsid);
      if (source) params.set('source', source);

      const res = await fetch(`${API_BASE}/api/v2/funnel-analysis/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      setDataAsOf(payload.data_as_of ?? '');
      setInsights(payload.insights_strip ?? []);
      setSnapshot(payload.funnel_snapshot ?? EMPTY_SNAPSHOT);
      setVisual(payload.funnel_visual ?? EMPTY_VISUAL);
      setStagePerformance(payload.stage_performance ?? []);
      setTrend(payload.conversion_trend ?? []);
      setEchelonRows(payload.funnel_by_echelon ?? []);
      setTopPerformers(payload.top_performers ?? []);
      setBottomPerformers(payload.bottom_performers ?? []);
      setAlerts(payload.alerts ?? []);
      setStageLoss(payload.stage_loss_analysis ?? []);
      setSourceRows(payload.lead_source_analysis ?? []);
      setVelocity(payload.funnel_velocity ?? EMPTY_VELOCITY);
      setExpandedEchelonRows(payload.expanded_funnel_by_echelon ?? []);
      setRootCauseRows(payload.root_cause_insights ?? []);
      setCompanies(payload.companies ?? []);
      setRsids(payload.rsids ?? []);
      setSources(payload.sources ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load funnel analysis');
      setInsights([]);
      setSnapshot(EMPTY_SNAPSHOT);
      setVisual(EMPTY_VISUAL);
      setStagePerformance([]);
      setTrend([]);
      setEchelonRows([]);
      setTopPerformers([]);
      setBottomPerformers([]);
      setAlerts([]);
      setStageLoss([]);
      setSourceRows([]);
      setVelocity(EMPTY_VELOCITY);
      setExpandedEchelonRows([]);
      setRootCauseRows([]);
    } finally {
      setLoading(false);
    }
  }, [timeframe, company, rsid, source]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetFilters = (): void => {
    setTimeframe('');
    setCompany('');
    setRsid('');
    setSource('');
  };

  const funnelStages = useMemo(
    () => [
      { label: 'Leads', value: visual.leads },
      { label: 'Contacts', value: visual.contacts },
      { label: 'Appointments', value: visual.appointments },
      { label: 'Contracts', value: visual.contracts },
    ],
    [visual],
  );

  return (
    <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Funnel Analysis</h1>
        <p className="text-[12px] text-[#64748B] mt-0.5">Leads to contract performance with deep-stage breakdowns.{dataAsOf && ` · Data as of ${dataAsOf}`}</p>
      </div>

      {/* Perspective Selector */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap gap-2 items-center">
        <Filter className="h-4 w-4 text-[#64748B] shrink-0" />
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Timeframes</option>
          {TIMEFRAMES.map((t) => (<option key={t} value={t}>{t}</option>))}
        </select>
        <select value={company} onChange={(e) => setCompany(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Companies</option>
          {companies.map((item) => (<option key={item} value={item}>{item}</option>))}
        </select>
        <select value={rsid} onChange={(e) => setRsid(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {rsids.map((item) => (<option key={item} value={item}>{item}</option>))}
        </select>
        <select value={source} onChange={(e) => setSource(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Sources</option>
          {sources.map((item) => (<option key={item} value={item}>{item}</option>))}
        </select>
        <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
        <button onClick={() => void load()} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#60A5FA] inline-flex items-center gap-1"><RefreshCw className="h-3 w-3" /> Refresh</button>
      </div>

      {/* Tab Switcher */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden inline-flex">
        <button
          className={`px-4 py-2 text-[12px] font-semibold ${activeTab === 'overview' ? 'bg-[#1D4ED8] text-white' : 'text-[#94A3B8] hover:text-[#F3F5F7]'}`}
          onClick={() => setActiveTab('overview')}
        >Overview</button>
        <button
          className={`px-4 py-2 text-[12px] font-semibold ${activeTab === 'deep' ? 'bg-[#1D4ED8] text-white' : 'text-[#94A3B8] hover:text-[#F3F5F7]'}`}
          onClick={() => setActiveTab('deep')}
        >Deep Analysis</button>
      </div>

      {loading && <div className="mb-4 p-3 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] text-[13px]">Loading funnel analysis...</div>}
      {error && <div className="mb-4 p-3 rounded border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] text-[13px]">{error}</div>}

      {activeTab === 'overview' && (
        <div className="space-y-5">
          {/* Insight Strip */}
          {insights.length > 0 && (
            <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
              {insights.map((item, idx) => (
                <div key={`${item.label}-${idx}`} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4">
                  <p className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{item.label}</p>
                  <p className="mt-2 text-[22px] font-bold text-[#F3F5F7]">
                    {item.unit === '%' ? fmtPct(item.value) : `${fmtInt(item.value)}${item.unit}`}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Snapshot KPIs */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Funnel Snapshot</span>
              <VisualModeSwitch value={viewBySection.snapshot} onChange={(v) => setViewBySection((prev) => ({ ...prev, snapshot: v }))} />
            </div>
            <div className="grid gap-0 grid-cols-2 lg:grid-cols-5 divide-x divide-[#1D3A5C]">
              {[
                { label: 'Leads', value: fmtInt(snapshot.total_leads), color: '#60A5FA' },
                { label: 'Contacts', value: fmtInt(snapshot.total_contacts), color: '#F3F5F7' },
                { label: 'Appointments', value: fmtInt(snapshot.total_appointments), color: '#F3F5F7' },
                { label: 'Contracts', value: fmtInt(snapshot.total_contracts), color: '#10B981' },
                { label: 'Conversion', value: fmtPct(snapshot.overall_conversion_rate), color: '#60A5FA' },
              ].map(({ label, value, color }) => (
                <div key={label} className="p-4">
                  <p className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</p>
                  <p className="mt-2 text-[22px] font-bold" style={{ color }}>{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Funnel Visual */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Funnel Visual — Leads → Contracts</span>
            </div>
            <div className="p-4 grid gap-3 grid-cols-2 lg:grid-cols-4">
              {funnelStages.map((s, idx) => (
                <div key={`${s.label}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-4">
                  <p className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{s.label}</p>
                  <p className="mt-2 text-[22px] font-bold text-[#F3F5F7]">{fmtInt(s.value)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Stage Performance */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Stage Performance</span>
              <VisualModeSwitch value={viewBySection.stagePerfomance} onChange={(v) => setViewBySection((prev) => ({ ...prev, stagePerfomance: v }))} />
            </div>
            {viewBySection.stagePerfomance === 'table' ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Stage','Count','Conversion From Prev','Loss Count'].map((h) => (
                      <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {stagePerformance.length > 0 ? stagePerformance.map((row, idx) => (
                      <tr key={`${row.stage}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.stage}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.count)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtPct(row.conversion_from_previous)}</td>
                        <td className="px-3 py-2 text-[#EF4444]">{fmtInt(row.loss_count)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={4}>No stage data for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4 space-y-2">
                {stagePerformance.slice(0, 8).map((row, idx) => (
                  <div key={`${row.stage}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.stage}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">Count: {fmtInt(row.count)} · Conv: {fmtPct(row.conversion_from_previous)} · Loss: {fmtInt(row.loss_count)}</div>
                  </div>
                ))}
                {stagePerformance.length === 0 && <div className="text-[13px] text-[#64748B]">No stage data for current filters.</div>}
              </div>
            )}
          </div>

          {/* Trend */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Conversion Trend</span>
              <VisualModeSwitch value={viewBySection.trend} onChange={(v) => setViewBySection((prev) => ({ ...prev, trend: v }))} />
            </div>
            {viewBySection.trend === 'table' ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Period','Leads','Contacts','Appointments','Contracts','Conv'].map((h) => (
                      <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {trend.length > 0 ? trend.map((row, idx) => (
                      <tr key={`${row.period}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.period}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.leads)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.contacts)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.appointments)}</td>
                        <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                        <td className="px-3 py-2 text-[#60A5FA]">{fmtPct(row.conversion_rate)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No trend data for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4 space-y-2">
                {trend.slice(0, 8).map((row, idx) => (
                  <div key={`${row.period}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.period}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">Leads: {fmtInt(row.leads)} → Contracts: {fmtInt(row.contracts)} · {fmtPct(row.conversion_rate)}</div>
                  </div>
                ))}
                {trend.length === 0 && <div className="text-[13px] text-[#64748B]">No trend data for current filters.</div>}
              </div>
            )}
          </div>

          {/* Performers + Echelon */}
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Top Performers</span>
                <VisualModeSwitch value={viewBySection.performers} onChange={(v) => setViewBySection((prev) => ({ ...prev, performers: v }))} />
              </div>
              {viewBySection.performers === 'table' ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-[12px]">
                    <thead><tr className="border-b border-[#1D3A5C]">
                      {['Echelon','Contracts','Conversion'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                    </tr></thead>
                    <tbody>
                      {topPerformers.length > 0 ? topPerformers.map((row, idx) => (
                        <tr key={`${row.echelon}-${idx}`} className="border-b border-[#152A45]">
                          <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.echelon}</td>
                          <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                          <td className="px-3 py-2 text-[#60A5FA]">{fmtPct(row.conversion_rate)}</td>
                        </tr>
                      )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={3}>No top performers for current filters.</td></tr>}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 space-y-2">
                  {topPerformers.slice(0, 6).map((row, idx) => (
                    <div key={`${row.echelon}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                      <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.echelon}</div>
                      <div className="text-[12px] text-[#94A3B8] mt-1">Contracts: {fmtInt(row.contracts)} · Conv: {fmtPct(row.conversion_rate)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C]">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Bottom Performers</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Echelon','Contracts','Conversion'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {bottomPerformers.length > 0 ? bottomPerformers.map((row, idx) => (
                      <tr key={`${row.echelon}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.echelon}</td>
                        <td className="px-3 py-2 text-[#F59E0B]">{fmtInt(row.contracts)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtPct(row.conversion_rate)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={3}>No bottom performers for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Funnel by Echelon */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Funnel by Echelon</span>
              <VisualModeSwitch value={viewBySection.echelon} onChange={(v) => setViewBySection((prev) => ({ ...prev, echelon: v }))} />
            </div>
            {viewBySection.echelon === 'table' ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Echelon','Leads','Contacts','Appointments','Contracts','Conv'].map((h) => (
                      <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {echelonRows.length > 0 ? echelonRows.map((row, idx) => (
                      <tr key={`${row.echelon}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.echelon}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.leads)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.contacts)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.appointments)}</td>
                        <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                        <td className="px-3 py-2 text-[#60A5FA]">{fmtPct(row.conversion_rate)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No echelon data for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-4 space-y-2">
                {echelonRows.slice(0, 8).map((row, idx) => (
                  <div key={`${row.echelon}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.echelon}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">L:{fmtInt(row.leads)} C:{fmtInt(row.contacts)} A:{fmtInt(row.appointments)} → {fmtInt(row.contracts)} contracts · {fmtPct(row.conversion_rate)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Alerts */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Alerts</div>
            {alerts.length > 0 ? alerts.map((row, idx) => (
              <div key={`${row.title}-${idx}`} className={`rounded-md border p-3 ${alertClasses(row.level)}`}>
                <p className="text-[12px] font-semibold inline-flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{row.title}</p>
                <p className="mt-1 text-[12px]">{row.message}</p>
              </div>
            )) : <p className="text-[12px] text-[#64748B]">No alert conditions under current filters.</p>}
          </div>
        </div>
      )}

      {activeTab === 'deep' && (
        <div className="space-y-5">
          {/* Funnel Stages */}
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
            {funnelStages.map((s, idx) => (
              <div key={`${s.label}-${idx}`} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4">
                <p className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{s.label}</p>
                <p className="mt-2 text-[22px] font-bold text-[#F3F5F7]">{fmtInt(s.value)}</p>
              </div>
            ))}
          </div>

          {/* Stage Loss */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Stage Loss Analysis</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Transition','From','To','Loss','Loss Rate'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                </tr></thead>
                <tbody>
                  {stageLoss.length > 0 ? stageLoss.map((row, idx) => (
                    <tr key={`${row.transition}-${idx}`} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.transition}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.from_count)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.to_count)}</td>
                      <td className="px-3 py-2 text-[#EF4444]">{fmtInt(row.loss_count)}</td>
                      <td className="px-3 py-2 text-[#F59E0B]">{fmtPct(row.loss_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No stage loss data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          {/* Source Analysis */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Source Analysis</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Source','Leads','Contacts','Appointments','Contracts','Conv'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                </tr></thead>
                <tbody>
                  {sourceRows.length > 0 ? sourceRows.map((row, idx) => (
                    <tr key={`${row.source}-${idx}`} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.source}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.leads)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.contacts)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.appointments)}</td>
                      <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{fmtPct(row.conversion_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No source data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          {/* Velocity + Root Cause */}
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Funnel Velocity</div>
              {[
                { label: 'Lead → Contact', value: velocity.lead_to_contact_days },
                { label: 'Contact → Appointment', value: velocity.contact_to_appointment_days },
                { label: 'Appointment → Contract', value: velocity.appointment_to_contract_days },
                { label: 'Overall Cycle', value: velocity.overall_cycle_days },
              ].map(({ label, value }) => (
                <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3 flex justify-between items-center">
                  <span className="text-[12px] text-[#94A3B8]">{label}</span>
                  <span className="text-[14px] font-bold text-[#60A5FA]">{value.toFixed(1)} days</span>
                </div>
              ))}
            </div>

            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Root-Cause Insights</div>
              {rootCauseRows.length > 0 ? rootCauseRows.map((row, idx) => (
                <div key={`${row.label}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <p className="text-[13px] font-semibold text-[#F3F5F7]">{row.label}</p>
                  <p className="mt-1 text-[12px] text-[#94A3B8]">{row.reason}</p>
                  <p className="mt-1 text-[12px] text-[#64748B]">Impact: {row.impact}</p>
                </div>
              )) : <p className="text-[12px] text-[#64748B]">No root-cause insights under current filters.</p>}
            </div>
          </div>

          {/* Expanded Echelon */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Expanded Funnel by Echelon</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Echelon','Leads','Contacts','Appointments','Contracts','Conv'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {expandedEchelonRows.length > 0 ? expandedEchelonRows.map((row, idx) => (
                    <tr key={`${row.echelon}-${idx}`} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.echelon}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.leads)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.contacts)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtInt(row.appointments)}</td>
                      <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{fmtPct(row.conversion_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No echelon details for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          {/* Deep Alerts */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Alerts</div>
            {alerts.length > 0 ? alerts.map((row, idx) => (
              <div key={`${row.title}-${idx}`} className={`rounded-md border p-3 ${alertClasses(row.level)}`}>
                <p className="text-[12px] font-semibold inline-flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{row.title}</p>
                <p className="mt-1 text-[12px]">{row.message}</p>
              </div>
            )) : <p className="text-[12px] text-[#64748B]">No alert conditions under current filters.</p>}
          </div>
        </div>
      )}
    </div>
  );
};
