import React, { useCallback, useEffect, useState } from 'react';
import { Crosshair, Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

// ─── Types ────────────────────────────────────────────────────────────────────

interface MarketSignal {
  signal_id: string;
  market_name: string;
  rsid: string;
  leads: number;
  contracts: number;
  conversion_rate: number;
  trend_label: string;
  flag_label: string;
  flag_color: string;
  linked_scope: string;
}

interface ProblemRow {
  problem_id: string;
  area: string;
  description: string;
  impact: string;
  affected_rsids: string[];
  severity_label: string;
  severity_color: string;
  contracts_at_risk: number;
  conversion_drop_percent: number;
  missed_opportunity: number;
  linked_scope: string;
}

interface TargetGap {
  gap_id: string;
  category: string;
  location: string;
  current_effort: string;
  potential: string;
  gap_value: number;
  impact: string;
  linked_scope: string;
}

interface IntelItem {
  intel_item_id: string;
  category: string;
  summary_text: string;
  affected_area: string;
  linked_scope: string;
}

interface FocusArea {
  focus_id: string;
  focus_area: string;
  why_data_driven: string;
  recommended_direction: string;
  linked_problem_ids: string[];
  linked_scope: string;
  priority_order: number;
}

interface TrendPoint {
  period: string;
  contracts: number;
  leads: number;
}

interface ItemDetail {
  selected_item_id: string;
  selected_item_type: string;
  title: string;
  rsid: string;
  market_name: string;
  area: string;
  overview_text: string;
  performance_snapshot: {
    leads: number;
    contracts: number;
    conversion_rate: number;
    flag: string;
  };
  detail_text: string;
  trend_history: TrendPoint[];
  impact_projection: string;
  supporting_intelligence_results: string[];
  linked_items: string[];
  last_updated: string;
}

interface FusionCellPayload {
  status: string;
  timeframe: string;
  filters: { rsid: string | null; market: string | null; area: string | null };
  market_signals: MarketSignal[];
  problem_identification: ProblemRow[];
  target_gaps: TargetGap[];
  market_intelligence_snapshot: IntelItem[];
  recommended_focus_areas: FocusArea[];
  detail_index: Record<string, ItemDetail>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtNum = (n: number | undefined | null): string =>
  n == null ? '—' : n.toLocaleString();

const fmtPct = (n: number | undefined | null): string =>
  n == null ? '—' : `${n.toFixed(1)}%`;

const fmtDate = (s: string | undefined | null): string => {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleDateString();
};

// ─── Component ────────────────────────────────────────────────────────────────

const FusionTeamDashboard: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({
    signals: 'table',
    problems: 'table',
    gaps: 'table',
    intel: 'table',
    focus: 'kpi',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // filters
  const [timeframe, setTimeframe] = useState('ytd');
  const [rsidFilter, setRsidFilter] = useState('');
  const [marketFilter, setMarketFilter] = useState('');
  const [areaFilter, setAreaFilter] = useState('');

  // data
  const [signals, setSignals] = useState<MarketSignal[]>([]);
  const [problems, setProblems] = useState<ProblemRow[]>([]);
  const [gaps, setGaps] = useState<TargetGap[]>([]);
  const [intel, setIntel] = useState<IntelItem[]>([]);
  const [focusAreas, setFocusAreas] = useState<FocusArea[]>([]);
  const [detailIndex, setDetailIndex] = useState<Record<string, ItemDetail>>({});

  // right-panel selection
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  const selectedDetail: ItemDetail | null =
    selectedItemId && detailIndex[selectedItemId] ? detailIndex[selectedItemId] : null;

  // derived filter options
  const rsidOptions = Array.from(new Set(signals.map((s) => s.rsid).filter(Boolean))).sort();
  const marketOptions = Array.from(new Set(signals.map((s) => s.market_name).filter(Boolean))).sort();
  const areaOptions = Array.from(new Set(problems.map((p) => p.area).filter(Boolean))).sort();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ timeframe });
      if (rsidFilter) params.set('rsid', rsidFilter);
      if (marketFilter) params.set('market', marketFilter);
      if (areaFilter) params.set('area', areaFilter);
      const res = await fetch(`${API_BASE}/api/v2/fusion-cell/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: FusionCellPayload = await res.json();
      setSignals(data.market_signals ?? []);
      setProblems(data.problem_identification ?? []);
      setGaps(data.target_gaps ?? []);
      setIntel(data.market_intelligence_snapshot ?? []);
      setFocusAreas((data.recommended_focus_areas ?? []).sort((a, b) => a.priority_order - b.priority_order));
      setDetailIndex(data.detail_index ?? {});
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load Fusion Cell data.');
    } finally {
      setLoading(false);
    }
  }, [timeframe, rsidFilter, marketFilter, areaFilter]);

  useEffect(() => { void load(); }, [load]);

  const resetFilters = () => {
    setTimeframe('ytd');
    setRsidFilter('');
    setMarketFilter('');
    setAreaFilter('');
  };

  const selectItem = (id: string) =>
    setSelectedItemId((prev) => (prev === id ? null : id));

  // ── Render ────────────────────────────────────────────────────────────────

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
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Fusion Cell</h1>
          <p className="text-[12px] text-[#64748B] mt-0.5">Integrated intelligence — market signals, problem ID, target gaps</p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#0E2847] border border-[#1D3A5C] text-[#94A3B8] hover:text-[#F3F5F7]">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap gap-2">
        <div className="w-full mb-2 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
          <PerspectiveSelector value={perspective} onChange={setPerspective} />
        </div>
        {[
          { label: 'Timeframe', value: timeframe, opts: ['ytd','qtr','last_90'], set: setTimeframe, labels: ['YTD','Current Quarter','Last 90 Days'] },
        ].map(({ label, value, opts, set, labels }) => (
          <select key={label} value={value} onChange={(e) => set(e.target.value)}
            className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
            {opts.map((o, i) => <option key={o} value={o}>{labels[i]}</option>)}
          </select>
        ))}
        <select value={rsidFilter} onChange={(e) => setRsidFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {rsidOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={marketFilter} onChange={(e) => setMarketFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Markets</option>
          {marketOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={areaFilter} onChange={(e) => setAreaFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Areas</option>
          {areaOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
      </div>

      {error && <div className="mb-4 p-3 rounded border border-[#EF4444] bg-[#EF444422] text-[#EF4444] text-[13px]">{error}</div>}
      {loading && <div className="text-[13px] text-[#64748B] mb-4">Loading...</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* LEFT: sections */}
        <div className="xl:col-span-2 space-y-4">

          {/* Market Signals */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Market Signals</span>
              <VisualModeSwitch value={viewBySection.signals} onChange={(value) => setViewBySection((prev) => ({ ...prev, signals: value }))} />
            </div>
            {viewBySection.signals === 'table' ? darkTable(
              ['Market','RSID','Leads','Contracts','Conversion','Trend','Flag'],
              signals.length ? signals.map((s) => (
                <tr key={s.signal_id} onClick={() => selectItem(s.signal_id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedItemId === s.signal_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7]">{s.market_name}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{s.rsid}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtNum(s.leads)}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtNum(s.contracts)}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtPct(s.conversion_rate)}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{s.trend_label}</td>
                  <td className="px-3 py-2"><span style={{ color: s.flag_color }}>{s.flag_label}</span></td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={7}>No market signal data</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {signals.slice(0, 8).map((s) => (
                  <div key={s.signal_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="flex items-center justify-between text-[13px]">
                      <span className="text-[#F3F5F7] font-semibold">{s.market_name}</span>
                      <span className="text-[#94A3B8]">{fmtPct(s.conversion_rate)}</span>
                    </div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{s.rsid} | Leads {fmtNum(s.leads)} | Contracts {fmtNum(s.contracts)}</div>
                  </div>
                ))}
                {!signals.length && <div className="text-[13px] text-[#64748B]">No market signal data</div>}
              </div>
            )}
          </div>

          {/* Problem Identification */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Problem Identification</span>
              <VisualModeSwitch value={viewBySection.problems} onChange={(value) => setViewBySection((prev) => ({ ...prev, problems: value }))} />
            </div>
            {viewBySection.problems === 'table' ? darkTable(
              ['Area','Description','Severity','Contracts at Risk','Conv. Drop'],
              problems.length ? problems.map((p) => (
                <tr key={p.problem_id} onClick={() => selectItem(p.problem_id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedItemId === p.problem_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7]">{p.area}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{p.description}</td>
                  <td className="px-3 py-2"><span style={{ color: p.severity_color }}>{p.severity_label}</span></td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtNum(p.contracts_at_risk)}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtPct(p.conversion_drop_percent)}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No problems identified</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {problems.slice(0, 8).map((p) => (
                  <div key={p.problem_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{p.area}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{p.description}</div>
                  </div>
                ))}
                {!problems.length && <div className="text-[13px] text-[#64748B]">No problems identified</div>}
              </div>
            )}
          </div>

          {/* Target Gaps */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Target Gaps</span>
              <VisualModeSwitch value={viewBySection.gaps} onChange={(value) => setViewBySection((prev) => ({ ...prev, gaps: value }))} />
            </div>
            {viewBySection.gaps === 'table' ? darkTable(
              ['Category','Location','Current Effort','Potential','Gap Value','Impact'],
              gaps.length ? gaps.map((g) => (
                <tr key={g.gap_id} onClick={() => selectItem(g.gap_id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedItemId === g.gap_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7]">{g.category}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{g.location}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{g.current_effort}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{g.potential}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{fmtNum(g.gap_value)}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{g.impact}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={6}>No target gap data</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {gaps.slice(0, 8).map((g) => (
                  <div key={g.gap_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#F3F5F7] font-semibold">{g.category} - {g.location}</div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">Gap value {fmtNum(g.gap_value)} | {g.impact}</div>
                  </div>
                ))}
                {!gaps.length && <div className="text-[13px] text-[#64748B]">No target gap data</div>}
              </div>
            )}
          </div>

          {/* MI Snapshot */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Market Intelligence Snapshot</span>
              <VisualModeSwitch value={viewBySection.intel} onChange={(value) => setViewBySection((prev) => ({ ...prev, intel: value }))} />
            </div>
            {viewBySection.intel === 'table' ? darkTable(
              ['Category','Summary','Affected Area'],
              intel.length ? intel.map((item) => (
                <tr key={item.intel_item_id} className="border-b border-[#152A45] hover:bg-[#142F52]">
                  <td className="px-3 py-2 text-[#60A5FA]">{item.category}</td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{item.summary_text}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{item.affected_area}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={3}>No intel data</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {intel.slice(0, 8).map((item) => (
                  <div key={item.intel_item_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-3">
                    <div className="text-[13px] text-[#60A5FA] font-semibold">{item.category}</div>
                    <div className="text-[12px] text-[#F3F5F7] mt-1">{item.summary_text}</div>
                  </div>
                ))}
                {!intel.length && <div className="text-[13px] text-[#64748B]">No intel data</div>}
              </div>
            )}
          </div>

          {/* Recommended Focus Areas */}
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Recommended Focus Areas</span>
              <VisualModeSwitch value={viewBySection.focus} onChange={(value) => setViewBySection((prev) => ({ ...prev, focus: value }))} />
            </div>
            <div className="p-4 space-y-2">
              {focusAreas.length ? focusAreas.map((fa, i) => (
                <div key={fa.focus_id} className="bg-[#142F52] border border-[#1D3A5C] rounded px-3 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold text-[#1D4ED8] bg-[#1D4ED822] rounded px-1.5 py-0.5">#{i + 1}</span>
                    <span className="text-[13px] font-semibold text-[#F3F5F7]">{fa.focus_area}</span>
                  </div>
                  <div className="text-[12px] text-[#94A3B8]">{fa.recommended_direction}</div>
                </div>
              )) : <div className="text-[13px] text-[#64748B]">No focus areas</div>}
            </div>
          </div>
        </div>

        {/* RIGHT: Item detail panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Selected Item</div>
            {!selectedDetail && !loading && (
              <div className="text-[13px] text-[#64748B]">Click any row to view details.</div>
            )}
            {selectedDetail && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selectedDetail.title}</div>
                  <div className="text-[12px] text-[#64748B]">{selectedDetail.selected_item_type} · {selectedDetail.market_name || selectedDetail.area}</div>
                </div>
                <div className="text-[13px] text-[#94A3B8]">{selectedDetail.overview_text}</div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Leads', value: fmtNum(selectedDetail.performance_snapshot.leads) },
                    { label: 'Contracts', value: fmtNum(selectedDetail.performance_snapshot.contracts) },
                    { label: 'Conv. Rate', value: fmtPct(selectedDetail.performance_snapshot.conversion_rate) },
                    { label: 'Flag', value: selectedDetail.performance_snapshot.flag },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</div>
                      <div className="text-[14px] font-semibold text-[#F3F5F7]">{value}</div>
                    </div>
                  ))}
                </div>
                {selectedDetail.detail_text && (
                  <div className="text-[13px] text-[#94A3B8]">{selectedDetail.detail_text}</div>
                )}
                {selectedDetail.supporting_intelligence_results.length > 0 && (
                  <div>
                    <div className="text-[11px] uppercase tracking-[0.07em] text-[#64748B] mb-2">Supporting Intel</div>
                    <ul className="space-y-1 text-[13px] text-[#94A3B8]">
                      {selectedDetail.supporting_intelligence_results.map((ins, i) => (
                        <li key={i} className="flex gap-1.5"><span className="text-[#1D4ED8] flex-shrink-0">›</span>{ins}</li>
                      ))}
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

export default FusionTeamDashboard;
