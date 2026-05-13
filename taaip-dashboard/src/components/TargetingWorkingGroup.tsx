import React, { useCallback, useEffect, useState } from 'react';
import { Filter, RefreshCw, Users } from 'lucide-react';
import { API_BASE } from '../config/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Nomination {
  nomination_id: string;
  title: string;
  nomination_type: string;
  status: string;
  status_color: string;
  current_stage: string;
  rsid: string;
  company: string;
  owner: string;
  briefer: string;
  requested_quarter: string;
  source_context: string;
  updated_at: string;
  created_at: string;
}

interface FeasibilityRecord {
  nomination_id: string;
  feasibility_status: string;
  key_constraints: string[];
  resource_requirements: string;
  timeline: string;
  feasibility_notes: string;
}

interface ImpactRecord {
  nomination_id: string;
  projected_impact: string;
  affected_rsids: string[];
  impact_summary: string;
  mission_alignment: string;
  estimated_contracts: number | null;
  impact_notes: string;
}

interface CommentRecord {
  comment_id: string;
  author: string;
  role: string;
  text: string;
  created_at: string;
}

interface NominationDetail {
  nomination_id: string;
  title: string;
  nomination_type: string;
  status: string;
  status_color: string;
  current_stage: string;
  rsid: string;
  company: string;
  owner: string;
  briefer: string;
  requested_quarter: string;
  source_context: string;
  problem_statement: string;
  recommended_next_action: string;
  projected_impact: string;
  observed_pattern: string;
  mission_gap: string;
  updated_at: string;
  created_at: string;
}

interface FilterOptions {
  rsid: string[];
  company: string[];
  nomination_type: string[];
  status: string[];
}

interface TWGPayload {
  status: string;
  timeframe: string;
  filter_options: FilterOptions;
  nominations: Nomination[];
  feasibility_index: Record<string, FeasibilityRecord>;
  impact_index: Record<string, ImpactRecord>;
  comments_index: Record<string, CommentRecord[]>;
  detail_index: Record<string, NominationDetail>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtDate = (s: string | undefined | null): string => {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleDateString();
};

const fmtDateTime = (s: string | undefined | null): string => {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString();
};

// ─── Component ────────────────────────────────────────────────────────────────

export const TargetingWorkingGroup: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // filters
  const [timeframe, setTimeframe] = useState('ytd');
  const [rsidFilter, setRsidFilter] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // data
  const [nominations, setNominations] = useState<Nomination[]>([]);
  const [feasibilityIndex, setFeasibilityIndex] = useState<Record<string, FeasibilityRecord>>({});
  const [impactIndex, setImpactIndex] = useState<Record<string, ImpactRecord>>({});
  const [commentsIndex, setCommentsIndex] = useState<Record<string, CommentRecord[]>>({});
  const [detailIndex, setDetailIndex] = useState<Record<string, NominationDetail>>({});
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({ rsid: [], company: [], nomination_type: [], status: [] });

  // selected nomination drives all detail sections
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedNom: Nomination | null = nominations.find((n) => n.nomination_id === selectedId) ?? null;
  const selectedDetail: NominationDetail | null = selectedId ? (detailIndex[selectedId] ?? null) : null;
  const selectedFeasibility: FeasibilityRecord | null = selectedId ? (feasibilityIndex[selectedId] ?? null) : null;
  const selectedImpact: ImpactRecord | null = selectedId ? (impactIndex[selectedId] ?? null) : null;
  const selectedComments: CommentRecord[] = selectedId ? (commentsIndex[selectedId] ?? []) : [];

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ timeframe });
      if (rsidFilter) params.set('rsid', rsidFilter);
      if (companyFilter) params.set('company', companyFilter);
      if (typeFilter) params.set('nomination_type', typeFilter);
      if (statusFilter) params.set('status', statusFilter);
      const res = await fetch(`${API_BASE}/api/v2/twg/locked?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: TWGPayload = await res.json();
      setNominations(data.nominations ?? []);
      setFeasibilityIndex(data.feasibility_index ?? {});
      setImpactIndex(data.impact_index ?? {});
      setCommentsIndex(data.comments_index ?? {});
      setDetailIndex(data.detail_index ?? {});
      setFilterOptions(data.filter_options ?? { rsid: [], company: [], nomination_type: [], status: [] });
      // auto-select first if nothing selected
      if (!selectedId && (data.nominations ?? []).length > 0) {
        setSelectedId(data.nominations[0].nomination_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load TWG data.');
    } finally {
      setLoading(false);
    }
  }, [timeframe, rsidFilter, companyFilter, typeFilter, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { void load(); }, [load]);

  const resetFilters = () => {
    setTimeframe('ytd');
    setRsidFilter('');
    setCompanyFilter('');
    setTypeFilter('');
    setStatusFilter('');
  };

  const selectNomination = (id: string) =>
    setSelectedId((prev) => (prev === id ? null : id));

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
          <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Targeting Working Group</h1>
          <p className="text-[12px] text-[#64748B] mt-0.5">Nomination review, feasibility analysis, and targeting recommendations</p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[12px] bg-[#0E2847] border border-[#1D3A5C] text-[#94A3B8] hover:text-[#F3F5F7]">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap gap-2">
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="ytd">YTD</option>
          <option value="qtr">Current Quarter</option>
          <option value="last_90">Last 90 Days</option>
        </select>
        <select value={rsidFilter} onChange={(e) => setRsidFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {filterOptions.rsid.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Companies</option>
          {filterOptions.company.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Types</option>
          {filterOptions.nomination_type.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Statuses</option>
          {filterOptions.status.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <button onClick={resetFilters} className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#64748B] hover:text-[#F3F5F7]">Reset</button>
      </div>

      {error && <div className="mb-4 p-3 rounded border border-[#EF4444] bg-[#EF444422] text-[#EF4444] text-[13px]">{error}</div>}
      {loading && <div className="text-[13px] text-[#64748B] mb-4">Loading...</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* LEFT: Nominations table */}
        <div className="xl:col-span-2">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C]">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Nominations ({nominations.length})</span>
            </div>
            {darkTable(
              ['Nomination Title','Type','Proposed By','Status','Last Updated'],
              nominations.length ? nominations.map((n) => (
                <tr key={n.nomination_id} onClick={() => selectNomination(n.nomination_id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedId === n.nomination_id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7] font-medium">{n.title}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{n.nomination_type}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{n.briefer || n.owner}</td>
                  <td className="px-3 py-2"><span style={{ color: n.status_color }}>{n.status}</span></td>
                  <td className="px-3 py-2 text-[#64748B]">{fmtDate(n.updated_at)}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No nominations</td></tr>
              )
            )}
          </div>
        </div>

        {/* RIGHT: Detail panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Nomination Detail</div>
            {!selectedDetail && !loading && (
              <div className="text-[13px] text-[#64748B]">Select a nomination to view details.</div>
            )}
            {selectedDetail && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selectedDetail.title}</div>
                  <div className="text-[12px] text-[#64748B]">{selectedDetail.nomination_type} · Stage: {selectedDetail.current_stage}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Status</div>
                  <span style={{ color: selectedDetail.status_color }} className="text-[13px] font-semibold">{selectedDetail.status}</span>
                </div>
                {selectedDetail.problem_statement && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Problem Statement</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedDetail.problem_statement}</div>
                  </div>
                )}
                {selectedDetail.mission_gap && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Mission Gap</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedDetail.mission_gap}</div>
                  </div>
                )}
                {selectedDetail.recommended_next_action && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Recommended Action</div>
                    <div className="text-[13px] text-[#60A5FA]">{selectedDetail.recommended_next_action}</div>
                  </div>
                )}
                {selectedFeasibility && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Feasibility</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedFeasibility.feasibility_status} · {selectedFeasibility.timeline}</div>
                  </div>
                )}
                {selectedImpact && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-1">Projected Impact</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedImpact.impact_summary}</div>
                    {selectedImpact.estimated_contracts != null && (
                      <div className="text-[13px] text-[#10B981] mt-0.5">Est. Contracts: {selectedImpact.estimated_contracts}</div>
                    )}
                  </div>
                )}
                {selectedComments.length > 0 && (
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B] mb-2">Comments</div>
                    <div className="space-y-2">
                      {selectedComments.map((c) => (
                        <div key={c.comment_id} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                          <div className="text-[11px] text-[#64748B]">{c.author} · {c.role} · {fmtDateTime(c.created_at)}</div>
                          <div className="text-[13px] text-[#F3F5F7] mt-0.5">{c.text}</div>
                        </div>
                      ))}
                    </div>
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

export default TargetingWorkingGroup;
