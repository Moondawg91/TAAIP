import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type Summary = {
  total_investment: number;
  total_leads: number;
  total_engagements: number;
  total_contracts: number;
};

type EventRoiRow = {
  event_id: string;
  event_name: string;
  mac_activity_code: string;
  type: string;
  date: string;
  company: string;
  rsid: string;
  fund_source: string;
  cost: number;
  leads: number;
  engagements: number;
  contracts: number;
  cost_per_lead: number;
  cost_per_engagement: number;
  cost_per_contract: number;
  roi_status: string;
  location: string;
  roi_notes: string;
  alerts: string[];
  ts: string;
};

type CategoryRoi = {
  category: string;
  investment: number;
  leads: number;
  engagements: number;
  contracts: number;
  cost_per_lead: number;
  cost_per_engagement: number;
  cost_per_contract: number;
};

type AlertRow = {
  level: string;
  title: string;
  message: string;
};

type OverviewMetrics = {
  total_events: number;
  average_cost_per_lead: number;
  average_cost_per_engagement: number;
  average_cost_per_contract: number;
  lead_to_contract_rate: number;
};

type InvestmentDistribution = {
  fund_source: string;
  investment: number;
};

type RoiByEchelon = {
  echelon: string;
  investment: number;
  leads: number;
  engagements: number;
  contracts: number;
  cost_per_contract: number;
};

type RoiTrend = {
  period: string;
  investment: number;
  leads: number;
  engagements: number;
  contracts: number;
  cost_per_contract: number;
};

type Payload = {
  data_as_of: string;
  summary: Summary;
  event_roi_rows: EventRoiRow[];
  category_roi: CategoryRoi[];
  top_roi_events: EventRoiRow[];
  low_roi_events: EventRoiRow[];
  alerts: AlertRow[];
  overview_metrics: OverviewMetrics;
  investment_distribution: InvestmentDistribution[];
  roi_by_echelon: RoiByEchelon[];
  roi_trend: RoiTrend[];
  companies: string[];
  rsids: string[];
  event_types: string[];
  fund_sources: string[];
};

const EMPTY_SUMMARY: Summary = {
  total_investment: 0,
  total_leads: 0,
  total_engagements: 0,
  total_contracts: 0,
};

const EMPTY_OVERVIEW: OverviewMetrics = {
  total_events: 0,
  average_cost_per_lead: 0,
  average_cost_per_engagement: 0,
  average_cost_per_contract: 0,
  lead_to_contract_rate: 0,
};

const TIMEFRAMES = ['FY26 Q1', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25'];

type Tab = 'event-roi' | 'overview';

const fmtInt = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '0';
  return Math.round(value).toLocaleString();
};

const fmtMoney = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '$0';
  return `$${Math.round(value).toLocaleString()}`;
};

const fmtRate = (n: number | null | undefined): string => {
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

export const ROIDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('event-roi');
  const [perspective, setPerspective] = useState<PerspectiveMode>('analytical');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({
    eventRoi: 'table', category: 'table', topLow: 'kpi',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [timeframe, setTimeframe] = useState('');
  const [company, setCompany] = useState('');
  const [rsid, setRsid] = useState('');
  const [eventType, setEventType] = useState('');
  const [fundSource, setFundSource] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [summary, setSummary] = useState<Summary>(EMPTY_SUMMARY);
  const [eventRows, setEventRows] = useState<EventRoiRow[]>([]);
  const [categoryRows, setCategoryRows] = useState<CategoryRoi[]>([]);
  const [topRows, setTopRows] = useState<EventRoiRow[]>([]);
  const [lowRows, setLowRows] = useState<EventRoiRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [overview, setOverview] = useState<OverviewMetrics>(EMPTY_OVERVIEW);
  const [distributionRows, setDistributionRows] = useState<InvestmentDistribution[]>([]);
  const [echelonRows, setEchelonRows] = useState<RoiByEchelon[]>([]);
  const [trendRows, setTrendRows] = useState<RoiTrend[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [rsids, setRsids] = useState<string[]>([]);
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [fundSources, setFundSources] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeframe) params.set('timeframe', timeframe);
      if (company) params.set('company', company);
      if (rsid) params.set('rsid', rsid);
      if (eventType) params.set('event_type', eventType);
      if (fundSource) params.set('fund_source', fundSource);

      const res = await fetch(`${API_BASE}/api/v2/roi-dashboard/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      const rows = Array.isArray(payload.event_roi_rows) ? payload.event_roi_rows : [];

      setDataAsOf(payload.data_as_of ?? '');
      setSummary(payload.summary ?? EMPTY_SUMMARY);
      setEventRows(rows);
      setCategoryRows(Array.isArray(payload.category_roi) ? payload.category_roi : []);
      setTopRows(Array.isArray(payload.top_roi_events) ? payload.top_roi_events : []);
      setLowRows(Array.isArray(payload.low_roi_events) ? payload.low_roi_events : []);
      setAlerts(Array.isArray(payload.alerts) ? payload.alerts : []);
      setOverview(payload.overview_metrics ?? EMPTY_OVERVIEW);
      setDistributionRows(Array.isArray(payload.investment_distribution) ? payload.investment_distribution : []);
      setEchelonRows(Array.isArray(payload.roi_by_echelon) ? payload.roi_by_echelon : []);
      setTrendRows(Array.isArray(payload.roi_trend) ? payload.roi_trend : []);
      setCompanies(Array.isArray(payload.companies) ? payload.companies : []);
      setRsids(Array.isArray(payload.rsids) ? payload.rsids : []);
      setEventTypes(Array.isArray(payload.event_types) ? payload.event_types : []);
      setFundSources(Array.isArray(payload.fund_sources) ? payload.fund_sources : []);

      setSelectedId((prev) => {
        if (prev && rows.some((r) => r.event_id === prev)) return prev;
        return rows.length > 0 ? rows[0].event_id : null;
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load ROI dashboard data');
      setSummary(EMPTY_SUMMARY);
      setEventRows([]);
      setCategoryRows([]);
      setTopRows([]);
      setLowRows([]);
      setAlerts([]);
      setOverview(EMPTY_OVERVIEW);
      setDistributionRows([]);
      setEchelonRows([]);
      setTrendRows([]);
      setSelectedId(null);
    } finally {
      setLoading(false);
    }
  }, [timeframe, company, rsid, eventType, fundSource]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetFilters = (): void => {
    setTimeframe('');
    setCompany('');
    setRsid('');
    setEventType('');
    setFundSource('');
  };

  const selectedRow = useMemo(() => {
    if (!selectedId) return null;
    return eventRows.find((r) => r.event_id === selectedId) ?? null;
  }, [eventRows, selectedId]);

  return (
    <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">ROI Dashboard</h1>
        <p className="text-[12px] text-[#64748B] mt-0.5">Event-level ROI, category breakdowns, investment distribution.{dataAsOf && ` · Data as of ${dataAsOf}`}</p>
      </div>

      {/* Perspective Selector */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      {/* Tab Switcher */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden inline-flex">
        <button
          className={`px-4 py-2 text-[12px] font-semibold ${activeTab === 'event-roi' ? 'bg-[#1D4ED8] text-white' : 'text-[#94A3B8] hover:text-[#F3F5F7]'}`}
          onClick={() => setActiveTab('event-roi')}
        >Event ROI Analysis</button>
        <button
          className={`px-4 py-2 text-[12px] font-semibold ${activeTab === 'overview' ? 'bg-[#1D4ED8] text-white' : 'text-[#94A3B8] hover:text-[#F3F5F7]'}`}
          onClick={() => setActiveTab('overview')}
        >Overview</button>
      </div>

      {loading && <div className="mb-4 p-3 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] text-[13px]">Loading ROI dashboard...</div>}
      {error && <div className="mb-4 p-3 rounded border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] text-[13px]">{error}</div>}

      {activeTab === 'event-roi' && (
        <div className="space-y-5">
          {/* Event ROI Filters */}
          <div className="flex flex-wrap gap-2 items-center">
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
            <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
              <option value="">All Event Types</option>
              {eventTypes.map((item) => (<option key={item} value={item}>{item}</option>))}
            </select>
            <select value={fundSource} onChange={(e) => setFundSource(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
              <option value="">All Fund Sources</option>
              {fundSources.map((item) => (<option key={item} value={item}>{item}</option>))}
            </select>
            <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
            <button onClick={() => void load()} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#60A5FA] inline-flex items-center gap-1"><RefreshCw className="h-3 w-3" /> Refresh</button>
          </div>

          {/* Summary KPIs */}
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
            {[
              { label: 'Total Investment', value: fmtMoney(summary.total_investment), color: '#F3F5F7' },
              { label: 'Total Leads', value: fmtInt(summary.total_leads), color: '#60A5FA' },
              { label: 'Total Engagements', value: fmtInt(summary.total_engagements), color: '#F59E0B' },
              { label: 'Total Contracts', value: fmtInt(summary.total_contracts), color: '#10B981' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-3">
                <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">{label}</div>
                <div className="text-[20px] font-bold" style={{ color }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Event ROI Table + Detail */}
          <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Event ROI Table</span>
                <VisualModeSwitch value={viewBySection.eventRoi} onChange={(v) => setViewBySection((prev) => ({ ...prev, eventRoi: v }))} />
              </div>
              {viewBySection.eventRoi === 'table' ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-[12px]">
                    <thead><tr className="border-b border-[#1D3A5C]">
                      {['Event','MAC Code','Type','Date','Company','RSID','Fund','Cost','Leads','Engag.','Contracts','$/Lead','$/Engag.','$/Contract','Status'].map((h) => (
                        <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold whitespace-nowrap">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {eventRows.length > 0 ? eventRows.map((row) => (
                        <tr
                          key={row.event_id}
                          className={`border-b border-[#152A45] cursor-pointer ${selectedId === row.event_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}
                          onClick={() => setSelectedId(row.event_id)}
                        >
                          <td className="px-3 py-2 text-[#F3F5F7] font-medium whitespace-nowrap">{row.event_name}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.mac_activity_code}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.type}</td>
                          <td className="px-3 py-2 text-[#94A3B8] whitespace-nowrap">{row.date}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.company}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.rsid}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.fund_source}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost)}</td>
                          <td className="px-3 py-2 text-[#60A5FA]">{fmtInt(row.leads)}</td>
                          <td className="px-3 py-2 text-[#F59E0B]">{fmtInt(row.engagements)}</td>
                          <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_lead)}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_engagement)}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_contract)}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{row.roi_status}</td>
                        </tr>
                      )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={15}>No ROI rows for current filters.</td></tr>}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 space-y-2">
                  {eventRows.slice(0, 10).map((row) => (
                    <div key={row.event_id} onClick={() => setSelectedId(row.event_id)}
                      className={`bg-[#142F52] border rounded p-3 cursor-pointer ${selectedId === row.event_id ? 'border-[#1D4ED8]' : 'border-[#1D3A5C] hover:border-[#1D4ED8]/50'}`}>
                      <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.event_name}</div>
                      <div className="text-[12px] text-[#94A3B8] mt-1">{row.type} · {row.company} · Cost: {fmtMoney(row.cost)} · Contracts: {fmtInt(row.contracts)}</div>
                    </div>
                  ))}
                  {eventRows.length === 0 && <div className="text-[13px] text-[#64748B]">No ROI rows for current filters.</div>}
                </div>
              )}
            </div>

            {/* Event Detail Panel */}
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3 sticky top-4">
              <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Event Detail</div>
              {selectedRow ? (
                <>
                  <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Event Overview</div>
                    <div className="text-[13px] font-semibold text-[#F3F5F7]">{selectedRow.event_name}</div>
                  </div>
                  <div className="text-[12px] text-[#94A3B8] space-y-1">
                    <p><span className="text-[#64748B]">MAC / Activity Code:</span> {selectedRow.mac_activity_code}</p>
                    <p><span className="text-[#64748B]">Date:</span> {selectedRow.date || 'N/A'} {selectedRow.location ? `- ${selectedRow.location}` : ''}</p>
                    <p><span className="text-[#64748B]">Company / RSID:</span> {selectedRow.company} / {selectedRow.rsid}</p>
                    <p><span className="text-[#64748B]">Fund Source:</span> {selectedRow.fund_source}</p>
                    <p><span className="text-[#64748B]">Cost:</span> {fmtMoney(selectedRow.cost)}</p>
                    <p><span className="text-[#64748B]">Leads:</span> <span className="text-[#60A5FA]">{fmtInt(selectedRow.leads)}</span></p>
                    <p><span className="text-[#64748B]">Engagements:</span> <span className="text-[#F59E0B]">{fmtInt(selectedRow.engagements)}</span></p>
                    <p><span className="text-[#64748B]">Contracts:</span> <span className="text-[#10B981]">{fmtInt(selectedRow.contracts)}</span></p>
                  </div>
                  <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Funnel Snapshot</div>
                    <div className="text-[12px] text-[#94A3B8]">Leads {fmtInt(selectedRow.leads)} → Engag. {fmtInt(selectedRow.engagements)} → Contracts {fmtInt(selectedRow.contracts)}</div>
                  </div>
                  <div className="text-[12px] text-[#94A3B8] space-y-1">
                    <p><span className="text-[#64748B]">Cost/Lead:</span> {fmtMoney(selectedRow.cost_per_lead)}</p>
                    <p><span className="text-[#64748B]">Cost/Engagement:</span> {fmtMoney(selectedRow.cost_per_engagement)}</p>
                    <p><span className="text-[#64748B]">Cost/Contract:</span> {fmtMoney(selectedRow.cost_per_contract)}</p>
                  </div>
                  {selectedRow.alerts.length > 0 && (
                    <div className="bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded p-3 space-y-1">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#F59E0B] mb-1">ROI Alerts</div>
                      {selectedRow.alerts.map((a, idx) => (
                        <p key={`${a}-${idx}`} className="text-[12px] text-[#F59E0B] inline-flex items-start gap-1"><AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />{a}</p>
                      ))}
                    </div>
                  )}
                  {selectedRow.roi_notes && (
                    <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">ROI Notes</div>
                      <div className="text-[12px] text-[#94A3B8]">{selectedRow.roi_notes}</div>
                    </div>
                  )}
                </>
              ) : <div className="text-[12px] text-[#64748B]">Select an event row to see event-specific ROI details.</div>}
            </div>
          </div>

          {/* Category ROI + Top/Low */}
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">ROI by Event Category</span>
                <VisualModeSwitch value={viewBySection.category} onChange={(v) => setViewBySection((prev) => ({ ...prev, category: v }))} />
              </div>
              {viewBySection.category === 'table' ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-[12px]">
                    <thead><tr className="border-b border-[#1D3A5C]">
                      {['Category','Investment','Leads','Engag.','Contracts','$/Contract'].map((h) => (
                        <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {categoryRows.length > 0 ? categoryRows.map((row, idx) => (
                        <tr key={`${row.category}-${idx}`} className="border-b border-[#152A45]">
                          <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.category}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.investment)}</td>
                          <td className="px-3 py-2 text-[#60A5FA]">{fmtInt(row.leads)}</td>
                          <td className="px-3 py-2 text-[#F59E0B]">{fmtInt(row.engagements)}</td>
                          <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                          <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_contract)}</td>
                        </tr>
                      )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No category ROI data for current filters.</td></tr>}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 space-y-2">
                  {categoryRows.slice(0, 8).map((row, idx) => (
                    <div key={`${row.category}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                      <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.category}</div>
                      <div className="text-[12px] text-[#94A3B8] mt-1">Invest: {fmtMoney(row.investment)} · Contracts: {fmtInt(row.contracts)} · {fmtMoney(row.cost_per_contract)}/contract</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4">
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Top / Low ROI Events</div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-2">Top ROI</div>
                {topRows.length > 0 ? topRows.map((row) => (
                  <div key={`top-${row.event_id}`} className="bg-[#10B981]/10 border border-[#10B981]/30 rounded p-2 mb-2">
                    <div className="text-[12px] font-semibold text-[#10B981]">{row.event_name}</div>
                    <div className="text-[11px] text-[#94A3B8]">$/Contract: {fmtMoney(row.cost_per_contract)} · Contracts: {fmtInt(row.contracts)}</div>
                  </div>
                )) : <p className="text-[12px] text-[#64748B]">No top ROI events in current scope.</p>}
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-2">Low ROI</div>
                {lowRows.length > 0 ? lowRows.map((row) => (
                  <div key={`low-${row.event_id}`} className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded p-2 mb-2">
                    <div className="text-[12px] font-semibold text-[#EF4444]">{row.event_name}</div>
                    <div className="text-[11px] text-[#94A3B8]">$/Contract: {fmtMoney(row.cost_per_contract)} · Contracts: {fmtInt(row.contracts)}</div>
                  </div>
                )) : <p className="text-[12px] text-[#64748B]">No low ROI events in current scope.</p>}
              </div>
            </div>
          </div>

          {/* Event ROI Alerts */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Event ROI Alerts</div>
            {alerts.length > 0 ? alerts.map((row, idx) => (
              <div key={`${row.title}-${idx}`} className={`rounded-md border p-3 ${alertClasses(row.level)}`}>
                <p className="text-[12px] font-semibold inline-flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{row.title}</p>
                <p className="mt-1 text-[12px]">{row.message}</p>
              </div>
            )) : <p className="text-[12px] text-[#64748B]">No ROI alerts under current filters.</p>}
          </div>
        </div>
      )}

      {activeTab === 'overview' && (
        <div className="space-y-5">
          {/* Overview KPIs */}
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-5">
            {[
              { label: 'Total Events', value: fmtInt(overview.total_events), color: '#F3F5F7' },
              { label: 'Avg Cost/Lead', value: fmtMoney(overview.average_cost_per_lead), color: '#60A5FA' },
              { label: 'Avg Cost/Engag.', value: fmtMoney(overview.average_cost_per_engagement), color: '#F59E0B' },
              { label: 'Avg Cost/Contract', value: fmtMoney(overview.average_cost_per_contract), color: '#F59E0B' },
              { label: 'Lead-to-Contract', value: fmtRate(overview.lead_to_contract_rate), color: '#10B981' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-3">
                <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">{label}</div>
                <div className="text-[18px] font-bold" style={{ color }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Distribution + Echelon */}
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C]">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Investment Distribution</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Fund Source','Investment'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {distributionRows.length > 0 ? distributionRows.map((row, idx) => (
                      <tr key={`${row.fund_source}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.fund_source}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.investment)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={2}>No distribution data for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-[#1D3A5C]">
                <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">ROI by Echelon</span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-[12px]">
                  <thead><tr className="border-b border-[#1D3A5C]">
                    {['Echelon','Investment','Contracts','$/Contract'].map((h) => <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {echelonRows.length > 0 ? echelonRows.map((row, idx) => (
                      <tr key={`${row.echelon}-${idx}`} className="border-b border-[#152A45]">
                        <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.echelon}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.investment)}</td>
                        <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                        <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_contract)}</td>
                      </tr>
                    )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={4}>No echelon ROI data for current filters.</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* ROI Trend */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">ROI Trend</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Period','Investment','Leads','Engagements','Contracts','$/Contract'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {trendRows.length > 0 ? trendRows.map((row, idx) => (
                    <tr key={`${row.period}-${idx}`} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.period}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.investment)}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{fmtInt(row.leads)}</td>
                      <td className="px-3 py-2 text-[#F59E0B]">{fmtInt(row.engagements)}</td>
                      <td className="px-3 py-2 text-[#10B981]">{fmtInt(row.contracts)}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{fmtMoney(row.cost_per_contract)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No trend data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
