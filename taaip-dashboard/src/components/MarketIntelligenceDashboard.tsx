import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type MarketOverview = {
  total_population: number;
  eligible_population: number;
  hs_seniors: number;
  college_population: number;
  unemployment_rate: number;
  median_income: number;
};

type DemographicRow = {
  segment: string;
  population: number;
  trend: string;
};

type EducationRow = {
  school_name: string;
  type: string;
  population: number;
  grad_rate: number;
  historical_production: number;
  rsid: string;
};

type EconomicFactorRow = {
  factor: string;
  value: string;
  impact: string;
};

type InfluencerRow = {
  type: string;
  name: string;
  impact_level: string;
};

type CompetitorPresenceRow = {
  branch: string;
  presence_level: string;
};

type OpportunityRow = {
  label: string;
  reason: string;
  recommended_focus: string;
};

type RiskRow = {
  label: string;
  reason: string;
  impact: string;
};

type Payload = {
  data_as_of: string;
  market_overview: MarketOverview;
  demographics: DemographicRow[];
  education: EducationRow[];
  economic_factors: EconomicFactorRow[];
  influencers: InfluencerRow[];
  competitor_presence: CompetitorPresenceRow[];
  opportunity_areas: OpportunityRow[];
  risk_areas: RiskRow[];
  companies: string[];
  rsids: string[];
  cbsas: string[];
};

const TIMEFRAMES = ['FY26 Q1', 'FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25'];

const EMPTY_OVERVIEW: MarketOverview = {
  total_population: 0,
  eligible_population: 0,
  hs_seniors: 0,
  college_population: 0,
  unemployment_rate: 0,
  median_income: 0,
};

const fmtNumber = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '0';
  return Math.round(value).toLocaleString();
};

const fmtPct = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '0.0%';
  return `${value.toFixed(1)}%`;
};

const fmtCurrency = (n: number | null | undefined): string => {
  const value = Number(n ?? 0);
  if (!Number.isFinite(value)) return '$0';
  return `$${Math.round(value).toLocaleString()}`;
};

export const MarketIntelligenceDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [panelView, setPanelView] = useState<Record<string, VisualMode>>({
    demographics: 'table',
    education: 'table',
    economics: 'kpi',
    influencers: 'table',
    competitor: 'table',
    opportunities: 'kpi',
    risks: 'kpi',
  });

  const [timeframe, setTimeframe] = useState('');
  const [company, setCompany] = useState('');
  const [rsid, setRsid] = useState('');
  const [cbsa, setCbsa] = useState('');

  const [dataAsOf, setDataAsOf] = useState('');
  const [marketOverview, setMarketOverview] = useState<MarketOverview>(EMPTY_OVERVIEW);
  const [demographics, setDemographics] = useState<DemographicRow[]>([]);
  const [education, setEducation] = useState<EducationRow[]>([]);
  const [economicFactors, setEconomicFactors] = useState<EconomicFactorRow[]>([]);
  const [influencers, setInfluencers] = useState<InfluencerRow[]>([]);
  const [competitorPresence, setCompetitorPresence] = useState<CompetitorPresenceRow[]>([]);
  const [opportunityAreas, setOpportunityAreas] = useState<OpportunityRow[]>([]);
  const [riskAreas, setRiskAreas] = useState<RiskRow[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [rsids, setRsids] = useState<string[]>([]);
  const [cbsas, setCbsas] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeframe) params.set('timeframe', timeframe);
      if (company) params.set('company', company);
      if (rsid) params.set('rsid', rsid);
      if (cbsa) params.set('cbsa', cbsa);

      const res = await fetch(`${API_BASE}/api/v2/market-intelligence/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as Payload;

      setDataAsOf(payload.data_as_of ?? '');
      setMarketOverview(payload.market_overview ?? EMPTY_OVERVIEW);
      setDemographics(payload.demographics ?? []);
      setEducation(payload.education ?? []);
      setEconomicFactors(payload.economic_factors ?? []);
      setInfluencers(payload.influencers ?? []);
      setCompetitorPresence(payload.competitor_presence ?? []);
      setOpportunityAreas(payload.opportunity_areas ?? []);
      setRiskAreas(payload.risk_areas ?? []);
      setCompanies(payload.companies ?? []);
      setRsids(payload.rsids ?? []);
      setCbsas(payload.cbsas ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load market intelligence data');
      setMarketOverview(EMPTY_OVERVIEW);
      setDemographics([]);
      setEducation([]);
      setEconomicFactors([]);
      setInfluencers([]);
      setCompetitorPresence([]);
      setOpportunityAreas([]);
      setRiskAreas([]);
    } finally {
      setLoading(false);
    }
  }, [timeframe, company, rsid, cbsa]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetFilters = (): void => {
    setTimeframe('');
    setCompany('');
    setRsid('');
    setCbsa('');
  };

  const educationRows = useMemo(
    () => [...education].sort((a, b) => b.historical_production - a.historical_production),
    [education],
  );

  // ── Dark-theme KPI card helper ──────────────────────────────────────────────
  const KPICard = ({ label, value, valueClass = 'text-[#F3F5F7]' }: { label: string; value: string; valueClass?: string }) => (
    <div className="bg-[#0E2847] border border-[#1D3A5C] rounded px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] mb-1">{label}</div>
      <div className={`text-2xl font-semibold ${valueClass}`}>{value}</div>
    </div>
  );

  // ── Dark-theme section card ──────────────────────────────────────────────────
  const SectionCard = ({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) => (
    <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
      <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">{title}</span>
        {action}
      </div>
      <div className="p-0">{children}</div>
    </div>
  );

  const DarkTable = ({ cols, rows, empty }: { cols: string[]; rows: (string | number)[][]; empty: string }) => (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead><tr className="border-b border-[#1D3A5C]">
          {cols.map((c) => <th key={c} className="text-left px-3 py-2 text-[11px] uppercase tracking-[0.07em] text-[#64748B] font-semibold whitespace-nowrap">{c}</th>)}
        </tr></thead>
        <tbody>
          {rows.length === 0
            ? <tr><td colSpan={cols.length} className="px-3 py-5 text-center text-[#64748B]">{empty}</td></tr>
            : rows.map((row, i) => (
              <tr key={i} className="border-b border-[#152A45] hover:bg-[#142F52]">
                {row.map((cell, j) => <td key={j} className="px-3 py-2 text-[#F3F5F7]">{cell}</td>)}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-[24px] font-semibold text-[#F3F5F7] uppercase tracking-[0.08em]">Market Intelligence</h1>
        {dataAsOf && <p className="text-[12px] text-[#64748B] mt-0.5">Data as of {dataAsOf}</p>}
      </div>

      <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-end gap-4 px-4 py-3 bg-[#081B33] border border-[#1D3A5C] rounded-md">
        {[
          { label: 'Timeframe', value: timeframe, set: setTimeframe, options: TIMEFRAMES },
          { label: 'Company', value: company, set: setCompany, options: companies },
          { label: 'RSID', value: rsid, set: setRsid, options: rsids },
          { label: 'CBSA', value: cbsa, set: setCbsa, options: cbsas },
        ].map(({ label, value: val, set, options }) => (
          <div key={label} className="flex flex-col gap-0.5">
            <label className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</label>
            <select value={val} onChange={(e) => set(e.target.value)} className="bg-[#0E2847] border border-[#1D3A5C] text-[#F3F5F7] text-[13px] rounded px-2 py-1 focus:outline-none focus:border-[#1D4ED8]">
              <option value="">All</option>
              {(label === 'Timeframe' ? options : options).map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
        ))}
        <button onClick={resetFilters} className="px-3 py-1 text-[13px] bg-[#142F52] border border-[#1D3A5C] text-[#94A3B8] rounded hover:text-[#F3F5F7] transition-colors self-end">Reset</button>
        <button onClick={() => void load()} className="px-3 py-1 text-[13px] bg-[#1D4ED8] border border-[#1D4ED8] text-white rounded hover:bg-[#1e40af] transition-colors self-end flex items-center gap-1.5">
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KPICard label="Total Population" value={fmtNumber(marketOverview.total_population)} />
        <KPICard label="Eligible Population" value={fmtNumber(marketOverview.eligible_population)} valueClass="text-[#60A5FA]" />
        <KPICard label="Unemployment Rate" value={fmtPct(marketOverview.unemployment_rate)} valueClass="text-[#F59E0B]" />
        <KPICard label="Median Income" value={fmtCurrency(marketOverview.median_income)} valueClass="text-[#10B981]" />
      </div>

      {loading && <div className="bg-[#0E2847] border border-[#1D3A5C] rounded p-4 text-[13px] text-[#64748B]">Loading market intelligence…</div>}
      {error && <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded p-4 text-[13px] text-[#EF4444]">{error}</div>}

      {/* Data sections - 2-column grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <SectionCard title="Demographics">
          <div className="p-4 text-[12px] text-[#64748B] border-b border-[#1D3A5C]">
            {perspective === 'operational' ? 'Operational posture by segment population and directional trend.' :
             perspective === 'analytical' ? 'Comparative demographic analysis highlights addressable segments and relative weight.' :
             perspective === 'geospatial' ? 'Segment priorities interpreted for territory placement and coverage decisions.' :
             perspective === 'trend' ? 'Demographic shifts interpreted across sustained temporal patterns.' :
             'Tabular demographic detail for audit and traceability.'}
          </div>
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.demographics} onChange={(value) => setPanelView((prev) => ({ ...prev, demographics: value }))} />
          </div>
          {panelView.demographics === 'table' ? (
            <DarkTable
              cols={['Segment', 'Population', 'Trend']}
              rows={demographics.map((r) => [r.segment, fmtNumber(r.population), r.trend])}
              empty="No demographic data"
            />
          ) : (
            <div className="p-4 space-y-2">
              {demographics.slice(0, 6).map((r) => {
                const max = Math.max(...demographics.map((d) => d.population), 1);
                const width = Math.max(6, Math.round((r.population / max) * 100));
                return (
                  <div key={r.segment}>
                    <div className="flex items-center justify-between text-[12px] text-[#F3F5F7]">
                      <span>{r.segment}</span>
                      <span>{fmtNumber(r.population)}</span>
                    </div>
                    <div className="h-2 rounded bg-[#142F52] mt-1">
                      <div className="h-2 rounded bg-[#1D4ED8]" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
              {!demographics.length && <p className="text-[#64748B] text-[13px]">No demographic data</p>}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Education Targeting">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.education} onChange={(value) => setPanelView((prev) => ({ ...prev, education: value }))} />
          </div>
          {panelView.education === 'table' ? (
            <DarkTable
              cols={['School', 'Type', 'Population', 'Grad Rate', 'Production', 'RSID']}
              rows={educationRows.map((r) => [r.school_name, r.type, fmtNumber(r.population), fmtPct(r.grad_rate), fmtNumber(r.historical_production), r.rsid])}
              empty="No education data"
            />
          ) : (
            <div className="p-4 space-y-2">
              {educationRows.slice(0, 5).map((r) => (
                <div key={`${r.school_name}-${r.rsid}`} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <div className="text-[13px] text-[#F3F5F7] font-semibold">{r.school_name}</div>
                  <div className="text-[12px] text-[#94A3B8]">{r.type} | {r.rsid}</div>
                  <div className="text-[12px] text-[#60A5FA] mt-1">Production {fmtNumber(r.historical_production)} | Grad {fmtPct(r.grad_rate)}</div>
                </div>
              ))}
              {!educationRows.length && <p className="text-[#64748B] text-[13px]">No education data</p>}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Economic Conditions">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.economics} onChange={(value) => setPanelView((prev) => ({ ...prev, economics: value }))} />
          </div>
          <div className="p-4 grid grid-cols-2 gap-3">
            {economicFactors.length > 0
              ? economicFactors.map((r, i) => (
                <div key={i} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                  <div className="text-[11px] uppercase tracking-[0.07em] text-[#64748B]">{r.factor}</div>
                  <div className="text-[18px] font-semibold text-[#F3F5F7] mt-0.5">{panelView.economics === 'kpi' ? r.value : r.impact}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-0.5">{r.impact}</div>
                </div>
              ))
              : <p className="text-[#64748B] text-[13px] col-span-2">No economic data</p>}
          </div>
        </SectionCard>

        <SectionCard title="Influencer Landscape">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.influencers} onChange={(value) => setPanelView((prev) => ({ ...prev, influencers: value }))} />
          </div>
          <div className="p-4 space-y-2">
            {influencers.length > 0
              ? influencers.map((r, i) => (
                <div key={i} className="flex items-center justify-between bg-[#142F52] border border-[#1D3A5C] rounded px-3 py-2">
                  <div>
                    <div className="text-[11px] uppercase tracking-[0.07em] text-[#64748B]">{r.type}</div>
                    <div className="text-[13px] font-medium text-[#F3F5F7]">{r.name}</div>
                  </div>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${r.impact_level === 'High' ? 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30' : r.impact_level === 'Medium' ? 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30' : 'bg-[#1D3A5C] text-[#94A3B8] border-[#1D3A5C]'}`}>{r.impact_level}</span>
                </div>
              ))
              : <p className="text-[#64748B] text-[13px]">No influencer data</p>}
          </div>
        </SectionCard>

        <SectionCard title="Competitive Presence">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.competitor} onChange={(value) => setPanelView((prev) => ({ ...prev, competitor: value }))} />
          </div>
          {panelView.competitor === 'table' ? (
            <DarkTable
              cols={['Branch', 'Presence Level']}
              rows={competitorPresence.map((r) => [r.branch, r.presence_level])}
              empty="No competitor data"
            />
          ) : (
            <div className="p-4 space-y-2">
              {competitorPresence.map((r) => (
                <div key={r.branch} className="bg-[#142F52] border border-[#1D3A5C] rounded px-3 py-2 flex items-center justify-between">
                  <span className="text-[13px] text-[#F3F5F7]">{r.branch}</span>
                  <span className="text-[12px] text-[#94A3B8]">{r.presence_level}</span>
                </div>
              ))}
              {!competitorPresence.length && <p className="text-[#64748B] text-[13px]">No competitor data</p>}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Opportunity Areas">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.opportunities} onChange={(value) => setPanelView((prev) => ({ ...prev, opportunities: value }))} />
          </div>
          <div className="p-4 space-y-2">
            {opportunityAreas.length > 0
              ? opportunityAreas.map((r, i) => (
                <div key={i} className="bg-[#10B981]/10 border border-[#10B981]/20 rounded p-3">
                  <div className="text-[13px] font-semibold text-[#10B981]">{r.label}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-0.5">{r.reason}</div>
                  <div className="text-[12px] text-[#F3F5F7] mt-1">{r.recommended_focus}</div>
                </div>
              ))
              : <p className="text-[#64748B] text-[13px]">No opportunity areas</p>}
          </div>
        </SectionCard>

        <SectionCard title="Risk Areas">
          <div className="px-4 pt-2">
            <VisualModeSwitch value={panelView.risks} onChange={(value) => setPanelView((prev) => ({ ...prev, risks: value }))} />
          </div>
          <div className="p-4 space-y-2">
            {riskAreas.length > 0
              ? riskAreas.map((r, i) => (
                <div key={i} className="bg-[#F59E0B]/10 border border-[#F59E0B]/20 rounded p-3">
                  <div className="text-[13px] font-semibold text-[#F59E0B]">{r.label}</div>
                  <div className="text-[12px] text-[#94A3B8] mt-0.5">{r.reason}</div>
                  <div className="text-[12px] text-[#F3F5F7] mt-1">{r.impact}</div>
                </div>
              ))
              : <p className="text-[#64748B] text-[13px]">No risk areas</p>}
          </div>
        </SectionCard>
      </div>
    </div>
  );
};

export default MarketIntelligenceDashboard;
