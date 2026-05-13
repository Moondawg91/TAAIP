import React, { useEffect, useMemo, useState } from 'react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type MissionStatusRow = {
  unit_id: string;
  company_name: string;
  rsid: string;
  market: string;
  area: string;
  mission_assigned: number;
  contracts_ytd: number;
  delta_to_mission: number;
  percent_to_mission: number;
  trend_vs_last_quarter: string;
  status_label: string;
  status_color: string;
};

type MissionImpactRow = {
  impact_item_id: string;
  issue_title: string;
  affected_area: string;
  impact_on_mission: string;
  contracts_at_risk_low: number;
  contracts_at_risk_high: number;
  severity_label: string;
  severity_color: string;
  linked_company_id: string;
};

type MissionRiskRow = {
  risk_id: string;
  risk_title: string;
  risk_category: string;
  likelihood: number;
  impact: number;
  risk_level: string;
  trend_label: string;
  linked_scope: string;
};

type ConstraintRow = {
  constraint_id: string;
  constraint_name: string;
  description: string;
  affected_areas: string;
  mission_impact: string;
  mitigation_considerations: string;
  linked_scope: string;
};

type TakeawayRow = {
  takeaway_id: string;
  summary_text: string;
  linked_scope: string;
  priority_order: number;
};

type CompanyDetail = {
  selected_company_id: string;
  selected_company_name: string;
  selected_rsid: string;
  mission_assigned: number;
  contracts_ytd: number;
  delta_to_mission: number;
  percent_to_mission: number;
  status_label: string;
  trend_vs_last_quarter: string;
  key_insights: string[];
  top_impacted_issues: string[];
  supporting_rsids: string[];
  company_analysis_link: string;
};

type ApiPayload = {
  mission_status_overview: MissionStatusRow[];
  mission_impact_analysis: MissionImpactRow[];
  mission_risk_assessment: MissionRiskRow[];
  constraints: ConstraintRow[];
  key_takeaways: TakeawayRow[];
  company_details: CompanyDetail[];
};

type Filters = {
  timeframe: string;
  company: string;
  rsid: string;
  market: string;
  area: string;
};

const MissionAnalysisDashboard: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({
    status: 'table',
    impact: 'table',
    risk: 'table',
    constraints: 'table',
    takeaways: 'kpi',
  });
  const [filters, setFilters] = useState<Filters>({
    timeframe: 'ytd',
    company: '',
    rsid: '',
    market: '',
    area: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusRows, setStatusRows] = useState<MissionStatusRow[]>([]);
  const [impactRows, setImpactRows] = useState<MissionImpactRow[]>([]);
  const [riskRows, setRiskRows] = useState<MissionRiskRow[]>([]);
  const [constraintRows, setConstraintRows] = useState<ConstraintRow[]>([]);
  const [takeawayRows, setTakeawayRows] = useState<TakeawayRow[]>([]);
  const [companyDetails, setCompanyDetails] = useState<CompanyDetail[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ timeframe: filters.timeframe });
        if (filters.company) params.set('company', filters.company);
        if (filters.rsid) params.set('rsid', filters.rsid);
        if (filters.market) params.set('market', filters.market);
        if (filters.area) params.set('area', filters.area);

        const response = await fetch(`${API_BASE}/api/v2/mission-analysis/locked?${params.toString()}`);
        const data = (await response.json()) as ApiPayload;

        setStatusRows(Array.isArray(data.mission_status_overview) ? data.mission_status_overview : []);
        setImpactRows(Array.isArray(data.mission_impact_analysis) ? data.mission_impact_analysis : []);
        setRiskRows(Array.isArray(data.mission_risk_assessment) ? data.mission_risk_assessment : []);
        setConstraintRows(Array.isArray(data.constraints) ? data.constraints : []);
        setTakeawayRows(Array.isArray(data.key_takeaways) ? data.key_takeaways : []);
        setCompanyDetails(Array.isArray(data.company_details) ? data.company_details : []);
      } catch (e: any) {
        setError(e?.message || 'Failed to load mission analysis data.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [filters]);

  useEffect(() => {
    if (!statusRows.length) {
      setSelectedCompanyId('');
      return;
    }

    const stillExists = statusRows.some((r) => r.unit_id === selectedCompanyId);
    if (!stillExists) {
      setSelectedCompanyId(statusRows[0].unit_id);
    }
  }, [statusRows, selectedCompanyId]);

  const filterOptions = useMemo(() => {
    const companySet = new Set<string>();
    const rsidSet = new Set<string>();
    const marketSet = new Set<string>();
    const areaSet = new Set<string>();

    statusRows.forEach((row) => {
      if (row.company_name) companySet.add(row.company_name);
      if (row.rsid) rsidSet.add(row.rsid);
      if (row.market) marketSet.add(row.market);
      if (row.area) areaSet.add(row.area);
    });

    return {
      companies: Array.from(companySet).sort(),
      rsids: Array.from(rsidSet).sort(),
      markets: Array.from(marketSet).sort(),
      areas: Array.from(areaSet).sort(),
    };
  }, [statusRows]);

  const selectedStatusRow = useMemo(
    () => statusRows.find((row) => row.unit_id === selectedCompanyId) || null,
    [statusRows, selectedCompanyId],
  );

  const selectedDetail = useMemo(() => {
    const fromApi = companyDetails.find((d) => d.selected_company_id === selectedCompanyId);
    if (fromApi) return fromApi;
    if (!selectedStatusRow) return null;

    return {
      selected_company_id: selectedStatusRow.unit_id,
      selected_company_name: selectedStatusRow.company_name,
      selected_rsid: selectedStatusRow.rsid,
      mission_assigned: selectedStatusRow.mission_assigned,
      contracts_ytd: selectedStatusRow.contracts_ytd,
      delta_to_mission: selectedStatusRow.delta_to_mission,
      percent_to_mission: selectedStatusRow.percent_to_mission,
      status_label: selectedStatusRow.status_label,
      trend_vs_last_quarter: selectedStatusRow.trend_vs_last_quarter,
      key_insights: [
        `${selectedStatusRow.company_name} is at ${selectedStatusRow.percent_to_mission}% to mission.`,
        `Delta to mission is ${selectedStatusRow.delta_to_mission} contracts.`,
      ],
      top_impacted_issues: impactRows
        .filter((r) => r.linked_company_id === selectedStatusRow.unit_id)
        .slice(0, 3)
        .map((r) => r.issue_title),
      supporting_rsids: [selectedStatusRow.rsid],
      company_analysis_link: `/mission-analysis/company/${selectedStatusRow.unit_id}`,
    };
  }, [companyDetails, selectedCompanyId, selectedStatusRow, impactRows]);

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  // ── Dark theme helpers ────────────────────────────────────────────────────
  const darkSelect = "bg-[#0E2847] border border-[#1D3A5C] text-[#F3F5F7] text-[13px] rounded px-2 py-1 focus:outline-none focus:border-[#1D4ED8]";
  const darkTable = (headers: string[], body: React.ReactNode) => (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead><tr className="border-b border-[#1D3A5C]">
          {headers.map((h) => <th key={h} className="text-left px-3 py-2 text-[11px] uppercase tracking-[0.07em] text-[#64748B] font-semibold whitespace-nowrap">{h}</th>)}
        </tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
  );
  const emptyRow = (cols: number, msg: string) => (
    <tr><td colSpan={cols} className="px-3 py-5 text-center text-[#64748B]">{msg}</td></tr>
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <h1 className="text-[24px] font-semibold text-[#F3F5F7] uppercase tracking-[0.08em]">Mission Analysis</h1>

      <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      <div className="text-[12px] text-[#64748B]">
        {perspective === 'operational' ? 'Operational perspective prioritizes immediate execution posture and mission attainment.' :
         perspective === 'analytical' ? 'Analytical perspective emphasizes comparative gaps, drivers, and mission leverage points.' :
         perspective === 'geospatial' ? 'Geospatial perspective frames impacts by market-area distribution and scope concentration.' :
         perspective === 'trend' ? 'Trend perspective highlights trajectory changes and projected mission movement.' :
         'Table perspective preserves full mission evidence for traceability and review.'}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 px-4 py-3 bg-[#081B33] border border-[#1D3A5C] rounded-md">
        {[
          { label: 'Timeframe', key: 'timeframe' as keyof Filters, opts: [['ytd','YTD'],['qtr','Current Quarter'],['last_90','Last 90 Days']] },
        ].map(({ label, key, opts }) => (
          <div key={key} className="flex flex-col gap-0.5">
            <label className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</label>
            <select value={filters[key]} onChange={(e) => handleFilterChange(key, e.target.value)} className={darkSelect}>
              {opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
        ))}
        {[
          { label: 'Company', key: 'company' as keyof Filters, opts: filterOptions.companies },
          { label: 'RSID', key: 'rsid' as keyof Filters, opts: filterOptions.rsids },
          { label: 'Market', key: 'market' as keyof Filters, opts: filterOptions.markets },
          { label: 'Area', key: 'area' as keyof Filters, opts: filterOptions.areas },
        ].map(({ label, key, opts }) => (
          <div key={key} className="flex flex-col gap-0.5">
            <label className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</label>
            <select value={filters[key]} onChange={(e) => handleFilterChange(key, e.target.value)} className={darkSelect}>
              <option value="">All</option>
              {opts.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        ))}
      </div>

      {error && <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded p-3 text-[13px] text-[#EF4444]">{error}</div>}
      {loading && <div className="text-[13px] text-[#64748B] bg-[#0E2847] border border-[#1D3A5C] rounded p-3">Loading mission analysis…</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* LEFT: accordion-style sections */}
        <div className="xl:col-span-2 space-y-4">
          {/* Mission Status Overview */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Mission Status Overview</span>
              <VisualModeSwitch value={viewBySection.status} onChange={(value) => setViewBySection((prev) => ({ ...prev, status: value }))} />
            </div>
            {viewBySection.status === 'table' ? darkTable(
              ['Company','RSID','Assigned','Contracts YTD','Delta','% to Mission','Trend','Status'],
              statusRows.length ? statusRows.map((row) => (
                <tr key={row.unit_id} onClick={() => setSelectedCompanyId(row.unit_id)}
                  className={`border-b border-[#152A45] cursor-pointer transition-colors ${row.unit_id === selectedCompanyId ? 'bg-[#1D4ED8]/20' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.company_name}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.rsid}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.mission_assigned}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.contracts_ytd}</td>
                  <td className={`px-3 py-2 ${row.delta_to_mission < 0 ? 'text-[#EF4444]' : 'text-[#10B981]'}`}>{row.delta_to_mission}</td>
                  <td className={`px-3 py-2 ${row.percent_to_mission < 80 ? 'text-[#EF4444]' : row.percent_to_mission < 100 ? 'text-[#F59E0B]' : 'text-[#10B981]'}`}>{row.percent_to_mission}%</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.trend_vs_last_quarter}</td>
                  <td className="px-3 py-2"><span className="px-2 py-0.5 rounded text-[11px] font-medium border bg-[#0E2847]" style={{ color: row.status_color, borderColor: `${row.status_color}44` }}>{row.status_label}</span></td>
                </tr>
              )) : emptyRow(8, 'No mission status data')
            ) : (
              <div className="p-4 space-y-2">
                {statusRows.slice(0, 8).map((row) => (
                  <div key={row.unit_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="flex items-center justify-between text-[13px]">
                      <span className="text-[#F3F5F7] font-semibold">{row.company_name}</span>
                      <span className="text-[#94A3B8]">{row.percent_to_mission}%</span>
                    </div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{row.rsid} | {row.trend_vs_last_quarter} | {row.status_label}</div>
                  </div>
                ))}
                {!statusRows.length && <div className="text-[13px] text-[#64748B]">No mission status data</div>}
              </div>
            )}
          </div>

          {/* Mission Impact Analysis */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Mission Impact Analysis</span>
              <VisualModeSwitch value={viewBySection.impact} onChange={(value) => setViewBySection((prev) => ({ ...prev, impact: value }))} />
            </div>
            {viewBySection.impact === 'table' ? darkTable(
              ['Issue','Affected Area','Impact on Mission','Contracts at Risk (L)','Contracts at Risk (H)','Severity'],
              impactRows.length ? impactRows.map((row) => (
                <tr key={row.impact_item_id} className="border-b border-[#152A45] hover:bg-[#142F52]">
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.issue_title}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.affected_area}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.impact_on_mission}</td>
                  <td className="px-3 py-2 text-[#F59E0B]">{row.contracts_at_risk_low}</td>
                  <td className="px-3 py-2 text-[#EF4444]">{row.contracts_at_risk_high}</td>
                  <td className="px-3 py-2"><span className="px-2 py-0.5 rounded text-[11px] font-medium border" style={{ color: row.severity_color, borderColor: `${row.severity_color}44` }}>{row.severity_label}</span></td>
                </tr>
              )) : emptyRow(6, 'No impact data')
            ) : (
              <div className="p-4 space-y-2">
                {impactRows.slice(0, 8).map((row) => (
                  <div key={row.impact_item_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.issue_title}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{row.affected_area} | Risk {row.contracts_at_risk_low}-{row.contracts_at_risk_high}</div>
                  </div>
                ))}
                {!impactRows.length && <div className="text-[13px] text-[#64748B]">No impact data</div>}
              </div>
            )}
          </div>

          {/* Mission Risk Assessment */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Mission Risk Assessment</span>
              <VisualModeSwitch value={viewBySection.risk} onChange={(value) => setViewBySection((prev) => ({ ...prev, risk: value }))} />
            </div>
            {viewBySection.risk === 'table' ? darkTable(
              ['Risk','Category','Likelihood','Impact','Risk Level','Trend'],
              riskRows.length ? riskRows.map((row) => (
                <tr key={row.risk_id} className="border-b border-[#152A45] hover:bg-[#142F52]">
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.risk_title}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.risk_category}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.likelihood}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.impact}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.risk_level}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.trend_label}</td>
                </tr>
              )) : emptyRow(6, 'No risk data')
            ) : (
              <div className="p-4 space-y-2">
                {riskRows.slice(0, 8).map((row) => (
                  <div key={row.risk_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.risk_title}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{row.risk_category} | L{row.likelihood} / I{row.impact} | {row.risk_level}</div>
                  </div>
                ))}
                {!riskRows.length && <div className="text-[13px] text-[#64748B]">No risk data</div>}
              </div>
            )}
          </div>

          {/* Constraints */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Constraints &amp; Limitations</span>
              <VisualModeSwitch value={viewBySection.constraints} onChange={(value) => setViewBySection((prev) => ({ ...prev, constraints: value }))} />
            </div>
            {viewBySection.constraints === 'table' ? darkTable(
              ['Constraint','Description','Affected Areas','Mission Impact','Mitigation'],
              constraintRows.length ? constraintRows.map((row) => (
                <tr key={row.constraint_id} className="border-b border-[#152A45] hover:bg-[#142F52]">
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.constraint_name}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.description}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.affected_areas}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.mission_impact}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.mitigation_considerations}</td>
                </tr>
              )) : emptyRow(5, 'No constraint data')
            ) : (
              <div className="p-4 space-y-2">
                {constraintRows.slice(0, 8).map((row) => (
                  <div key={row.constraint_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.constraint_name}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{row.mission_impact}</div>
                  </div>
                ))}
                {!constraintRows.length && <div className="text-[13px] text-[#64748B]">No constraint data</div>}
              </div>
            )}
          </div>

          {/* Key Takeaways */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Key Takeaways</span>
              <VisualModeSwitch value={viewBySection.takeaways} onChange={(value) => setViewBySection((prev) => ({ ...prev, takeaways: value }))} />
            </div>
            <div className="p-4 space-y-2">
              {takeawayRows.length
                ? takeawayRows.sort((a, b) => a.priority_order - b.priority_order).map((row) => (
                  <div key={row.takeaway_id} className="bg-[#142F52] border border-[#1D3A5C] rounded px-3 py-2 text-[13px] text-[#F3F5F7]">{row.summary_text}</div>
                ))
                : <div className="text-[13px] text-[#64748B]">No key takeaways</div>}
            </div>
          </div>
        </div>

        {/* RIGHT: Company detail panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Selected Company</div>
            {!selectedDetail && !loading && (
              <div className="text-[13px] text-[#64748B]">Select a company row to view details.</div>
            )}
            {selectedDetail && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selectedDetail.selected_company_name}</div>
                  <div className="text-[12px] text-[#64748B]">RSID: {selectedDetail.selected_rsid}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: '% To Mission', value: `${selectedDetail.percent_to_mission}%`, color: selectedDetail.percent_to_mission >= 100 ? 'text-[#10B981]' : selectedDetail.percent_to_mission >= 80 ? 'text-[#F59E0B]' : 'text-[#EF4444]' },
                    { label: 'Mission Gap', value: String(selectedDetail.delta_to_mission), color: selectedDetail.delta_to_mission >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]' },
                    { label: 'Contracts YTD', value: String(selectedDetail.contracts_ytd), color: 'text-[#F3F5F7]' },
                    { label: 'Assigned', value: String(selectedDetail.mission_assigned), color: 'text-[#F3F5F7]' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</div>
                      <div className={`text-[18px] font-semibold ${color}`}>{value}</div>
                    </div>
                  ))}
                </div>
                <div className="text-[13px]"><span className="text-[#64748B]">Status:</span> <span className="text-[#F3F5F7] ml-1">{selectedDetail.status_label}</span></div>
                <div className="text-[13px]"><span className="text-[#64748B]">Trend:</span> <span className="text-[#F3F5F7] ml-1">{selectedDetail.trend_vs_last_quarter}</span></div>
                {selectedDetail.key_insights.length > 0 && (
                  <div>
                    <div className="text-[11px] uppercase tracking-[0.07em] text-[#64748B] mb-2">Key Insights</div>
                    <ul className="space-y-1 text-[13px] text-[#94A3B8]">
                      {selectedDetail.key_insights.map((ins, i) => <li key={i} className="flex gap-1.5"><span className="text-[#1D4ED8] mt-0.5 flex-shrink-0">›</span>{ins}</li>)}
                    </ul>
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

export default MissionAnalysisDashboard;
