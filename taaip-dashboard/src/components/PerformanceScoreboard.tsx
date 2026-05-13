import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type Summary = {
  total_leads: number;
  total_engagements: number;
  total_contracts: number;
  conversion_rate: number;
};

type CompanyRow = {
  company: string;
  leads: number;
  engagements: number;
  contracts: number;
  conversion_rate: number;
};

type RsidRow = {
  rsid: string;
  leads: number;
  engagements: number;
  contracts: number;
  conversion_rate: number;
};

type ActivityRow = {
  activity_name: string;
  activity_type: string;
  leads: number;
  engagements: number;
  contracts: number;
  conversion_rate: number;
};

type UnderperformingRow = {
  label: string;
  reason: string;
  metric: string;
};

type Payload = {
  data_as_of: string;
  summary: Summary;
  by_company: CompanyRow[];
  by_rsid: RsidRow[];
  top_activities: ActivityRow[];
  underperforming_areas: UnderperformingRow[];
  companies: string[];
  rsids: string[];
};

const TIMEFRAMES = ['FY26 Q1', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25'];

const EMPTY_SUMMARY: Summary = {
  total_leads: 0,
  total_engagements: 0,
  total_contracts: 0,
  conversion_rate: 0,
};

const formatRate = (value: number | null | undefined): string => {
  const v = Number(value ?? 0);
  if (!Number.isFinite(v)) return '0.0%';
  return `${v.toFixed(1)}%`;
};

export const PerformanceScoreboard: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('analytical');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({
    byCompany: 'table', byRsid: 'table', activities: 'table',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [timeframe, setTimeframe] = useState('');
  const [company, setCompany] = useState('');
  const [rsid, setRsid] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [summary, setSummary] = useState<Summary>(EMPTY_SUMMARY);
  const [byCompany, setByCompany] = useState<CompanyRow[]>([]);
  const [byRsid, setByRsid] = useState<RsidRow[]>([]);
  const [topActivities, setTopActivities] = useState<ActivityRow[]>([]);
  const [underperforming, setUnderperforming] = useState<UnderperformingRow[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [rsids, setRsids] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeframe) params.set('timeframe', timeframe);
      if (company) params.set('company', company);
      if (rsid) params.set('rsid', rsid);

      const res = await fetch(`${API_BASE}/api/v2/performance/locked?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const payload = (await res.json()) as Payload;

      setDataAsOf(payload.data_as_of ?? '');
      setSummary(payload.summary ?? EMPTY_SUMMARY);
      setByCompany(payload.by_company ?? []);
      setByRsid(payload.by_rsid ?? []);
      setTopActivities(payload.top_activities ?? []);
      setUnderperforming(payload.underperforming_areas ?? []);
      setCompanies(payload.companies ?? []);
      setRsids(payload.rsids ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load performance scoreboard');
      setSummary(EMPTY_SUMMARY);
      setByCompany([]);
      setByRsid([]);
      setTopActivities([]);
      setUnderperforming([]);
    } finally {
      setLoading(false);
    }
  }, [timeframe, company, rsid]);

  useEffect(() => {
    void load();
  }, [load]);

  const sortedCompany = useMemo(
    () => [...byCompany].sort((a, b) => b.contracts - a.contracts),
    [byCompany],
  );

  const sortedRsid = useMemo(
    () => [...byRsid].sort((a, b) => b.contracts - a.contracts),
    [byRsid],
  );

  const sortedActivities = useMemo(
    () => [...topActivities].sort((a, b) => b.contracts - a.contracts),
    [topActivities],
  );

  const resetFilters = (): void => {
    setTimeframe('');
    setCompany('');
    setRsid('');
  };

  return (
    <div className="min-h-screen p-6" style={{ background: '#081B33' }}>
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Performance Scoreboard</h1>
        <p className="text-[12px] text-[#64748B] mt-0.5">Production by company, RSID, and activity.{dataAsOf && ` · Data as of ${dataAsOf}`}</p>
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
          {companies.map((c) => (<option key={c} value={c}>{c}</option>))}
        </select>
        <select value={rsid} onChange={(e) => setRsid(e.target.value)} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {rsids.map((r) => (<option key={r} value={r}>{r}</option>))}
        </select>
        <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
        <button onClick={() => void load()} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#60A5FA] inline-flex items-center gap-1"><RefreshCw className="h-3 w-3" /> Refresh</button>
      </div>

      {loading && <div className="mb-4 p-3 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] text-[13px]">Loading performance scoreboard...</div>}
      {error && <div className="mb-4 p-3 rounded border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] text-[13px]">{error}</div>}

      {/* KPI Snapshot */}
      <div className="mb-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Leads', value: String(summary.total_leads), color: '#60A5FA' },
          { label: 'Total Engagements', value: String(summary.total_engagements), color: '#F59E0B' },
          { label: 'Total Contracts', value: String(summary.total_contracts), color: '#10B981' },
          { label: 'Conversion Rate', value: formatRate(summary.conversion_rate), color: '#10B981' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-3">
            <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">{label}</div>
            <div className="text-[20px] font-bold" style={{ color }}>{value}</div>
          </div>
        ))}
      </div>

      <div className="space-y-5">
        {/* By Company */}
        <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
          <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Production By Company</span>
            <VisualModeSwitch value={viewBySection.byCompany} onChange={(v) => setViewBySection((prev) => ({ ...prev, byCompany: v }))} />
          </div>
          {viewBySection.byCompany === 'table' ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Company','Leads','Engagements','Contracts','Conv Rate'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {sortedCompany.length > 0 ? sortedCompany.map((row) => (
                    <tr key={row.company} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.company || 'Unspecified'}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.leads}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.engagements}</td>
                      <td className="px-3 py-2 text-[#10B981]">{row.contracts}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{formatRate(row.conversion_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No company production data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              {sortedCompany.slice(0, 8).map((row) => (
                <div key={row.company} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.company || 'Unspecified'}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-1">Leads: {row.leads} · Contracts: {row.contracts} · {formatRate(row.conversion_rate)}</div>
                </div>
              ))}
              {sortedCompany.length === 0 && <div className="text-[13px] text-[#64748B]">No data for current filters.</div>}
            </div>
          )}
        </div>

        {/* By RSID */}
        <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
          <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Production By RSID</span>
            <VisualModeSwitch value={viewBySection.byRsid} onChange={(v) => setViewBySection((prev) => ({ ...prev, byRsid: v }))} />
          </div>
          {viewBySection.byRsid === 'table' ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['RSID','Leads','Engagements','Contracts','Conv Rate'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {sortedRsid.length > 0 ? sortedRsid.map((row) => (
                    <tr key={row.rsid} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.rsid || 'Unspecified'}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.leads}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.engagements}</td>
                      <td className="px-3 py-2 text-[#10B981]">{row.contracts}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{formatRate(row.conversion_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No RSID production data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              {sortedRsid.slice(0, 8).map((row) => (
                <div key={row.rsid} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.rsid || 'Unspecified'}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-1">Leads: {row.leads} · Contracts: {row.contracts} · {formatRate(row.conversion_rate)}</div>
                </div>
              ))}
              {sortedRsid.length === 0 && <div className="text-[13px] text-[#64748B]">No data for current filters.</div>}
            </div>
          )}
        </div>

        {/* Top Activities */}
        <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
          <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Top Performing Activities</span>
            <VisualModeSwitch value={viewBySection.activities} onChange={(v) => setViewBySection((prev) => ({ ...prev, activities: v }))} />
          </div>
          {viewBySection.activities === 'table' ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-[12px]">
                <thead><tr className="border-b border-[#1D3A5C]">
                  {['Activity Name','Type','Leads','Engagements','Contracts','Conv Rate'].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-[10px] uppercase tracking-[0.08em] text-[#64748B] font-semibold">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {sortedActivities.length > 0 ? sortedActivities.map((row, idx) => (
                    <tr key={`${row.activity_name}-${row.activity_type}-${idx}`} className="border-b border-[#152A45]">
                      <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.activity_name || 'Unnamed Activity'}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.activity_type || 'Unknown'}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.leads}</td>
                      <td className="px-3 py-2 text-[#94A3B8]">{row.engagements}</td>
                      <td className="px-3 py-2 text-[#10B981]">{row.contracts}</td>
                      <td className="px-3 py-2 text-[#60A5FA]">{formatRate(row.conversion_rate)}</td>
                    </tr>
                  )) : <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No executed activity production data for current filters.</td></tr>}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 space-y-2">
              {sortedActivities.slice(0, 8).map((row, idx) => (
                <div key={`${row.activity_name}-${idx}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.activity_name || 'Unnamed Activity'}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-1">{row.activity_type} · Contracts: {row.contracts} · {formatRate(row.conversion_rate)}</div>
                </div>
              ))}
              {sortedActivities.length === 0 && <div className="text-[13px] text-[#64748B]">No data for current filters.</div>}
            </div>
          )}
        </div>

        {/* Underperforming Areas */}
        <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-3">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8] border-b border-[#1D3A5C] pb-2">Underperforming Areas</div>
          {underperforming.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {underperforming.map((item, idx) => (
                <div key={`${item.label}-${item.reason}-${idx}`} className="bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded p-3">
                  <p className="text-[12px] font-semibold text-[#F59E0B]">{item.label}</p>
                  <p className="mt-1 text-[11px] uppercase tracking-wide text-[#F59E0B]/70">{item.reason}</p>
                  <p className="mt-1 text-[12px] text-[#94A3B8]">{item.metric}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[12px] text-[#64748B]">No underperforming areas detected for current filters.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PerformanceScoreboard;
