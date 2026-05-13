import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCw, ShieldCheck } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type DecisionState = 'approved' | 'modified' | 'deferred' | 'denied' | 'pending';

interface BoardItemApi {
  chain_id: string;
  title?: string;
  nomination_type?: string;
  impacted_scope?: string;
  requested_quarter?: string;
  status?: string;
  current_stage?: string;
  briefer_submitter?: string;
  origin?: string;
  requested_funding?: number | null;
  requested_budget?: number | null;
  requested_resources?: string;
  projected_impact?: string;
  source_context?: string;
  problem_statement?: string;
  observed_pattern?: string;
  mission_gap?: string;
  recommended_next_action?: string;
  owner_lead?: string;
  board_notes?: string;
  promoted_to_board_at?: string;
  decision_recorded_at?: string;
  updated_at?: string;
  created_at?: string;
  readiness?: {
    ready?: boolean;
    label?: string;
    missing_fields?: string[];
    blocking_flags?: string[];
  };
}

interface BoardDecisionApi {
  decision_id: string;
  chain_id: string;
  decision?: string;
  decision_reason?: string;
  approved_funding?: number | null;
  approved_budget?: number | null;
  approved_resources?: string;
  commander_notes?: string;
  decided_by?: string;
  decided_at?: string;
  operation_id?: string;
  operation_created_at?: string;
}

interface DecisionWriteResponse {
  status: string;
  decision_id?: string;
  operation_linkage?: {
    status?: string;
    result?: string;
    operation_id?: string;
  };
}

interface FollowOnActionApi {
  action_id: string;
  chain_id: string;
  action_title?: string;
  action_details?: string;
  owner?: string;
  due_date?: string;
  status?: string;
  updated_at?: string;
}

interface ReviewRow {
  nominationId: string;
  nominationName: string;
  nominationType: string;
  rsid: string;
  date: string;
  status: string;
  decisionState: DecisionState;
  requestedFunding: number | null;
  requestedBudget: number | null;
  roiSnapshot: string;
  brieferOrigin: string;
  detail: BoardItemApi;
  decision: BoardDecisionApi | null;
  actions: FollowOnActionApi[];
  roi: RoiMetrics;
}

interface RoiMetrics {
  cost: number | null;
  leads: number | null;
  engagements: number | null;
  contracts: number | null;
  costPerLead: number | null;
  costPerEngagement: number | null;
  costPerContract: number | null;
}

interface BoardPayload<T> {
  status: string;
  items: T[];
}

const quarterOptions = ['All', 'Q+1', 'Q+2', 'Q+3', 'Q+4'] as const;
const decisionOptions = ['All', 'Pending / Awaiting Decision', 'Approved', 'Modified', 'Deferred', 'Denied'] as const;

const asString = (value: unknown): string => {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value).trim();
};

const asNumber = (value: unknown): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string') {
    const cleaned = value.replace(/[^0-9.-]/g, '');
    if (!cleaned) {
      return null;
    }
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

const fmtMoney = (value: number | null): string => {
  if (value === null) {
    return 'Unavailable';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
};

const fmtInt = (value: number | null): string => {
  if (value === null) {
    return 'Unavailable';
  }
  return Math.round(value).toLocaleString();
};

const fmtDate = (value: string): string => {
  if (!value) {
    return 'Unavailable';
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return value;
  }
  return d.toLocaleDateString();
};

const fmtDateTime = (value: string): string => {
  if (!value) {
    return 'Unavailable';
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return value;
  }
  return d.toLocaleString();
};

const decisionBadge = (state: DecisionState): string => {
  if (state === 'approved') return 'bg-green-100 text-green-800';
  if (state === 'modified') return 'bg-blue-100 text-blue-800';
  if (state === 'deferred') return 'bg-yellow-100 text-yellow-800';
  if (state === 'denied') return 'bg-red-100 text-red-800';
  return 'bg-slate-100 text-slate-700';
};

const normalizeDecisionState = (item: BoardItemApi, decision: BoardDecisionApi | null): DecisionState => {
  const decisionText = asString(decision?.decision).toLowerCase();
  const statusText = asString(item.status).toLowerCase();
  const stageText = asString(item.current_stage).toLowerCase();

  if (decisionText.includes('approve')) return 'approved';
  if (decisionText.includes('modify') || decisionText.includes('amend')) return 'modified';
  if (decisionText.includes('defer')) return 'deferred';
  if (decisionText.includes('deny') || decisionText.includes('reject')) return 'denied';

  if (statusText.includes('approved')) return 'approved';
  if (statusText.includes('modified')) return 'modified';
  if (statusText.includes('deferred')) return 'deferred';
  if (statusText.includes('denied')) return 'denied';

  if (stageText.includes('board_decision') || stageText.includes('follow_on_action')) {
    return 'pending';
  }
  return 'pending';
};

const extractMetric = (text: string, keywords: string[]): number | null => {
  const lower = text.toLowerCase();
  for (const keyword of keywords) {
    const idx = lower.indexOf(keyword);
    if (idx === -1) continue;
    const windowStart = Math.max(0, idx - 30);
    const windowEnd = Math.min(lower.length, idx + keyword.length + 30);
    const window = lower.slice(windowStart, windowEnd);
    const match = window.match(/(\d+(?:[\.,]\d+)?)/);
    if (match && match[1]) {
      const n = Number(match[1].replace(/,/g, ''));
      if (Number.isFinite(n)) {
        return n;
      }
    }
  }
  return null;
};

const buildRoi = (item: BoardItemApi): RoiMetrics => {
  const source = `${asString(item.projected_impact)} ${asString(item.problem_statement)} ${asString(item.observed_pattern)}`;
  const cost = asNumber(item.requested_funding);
  const leads = extractMetric(source, ['lead', 'leads']);
  const engagements = extractMetric(source, ['engagement', 'engagements']);
  const contracts = extractMetric(source, ['contract', 'contracts', 'enlistment', 'enlistments']);

  return {
    cost,
    leads,
    engagements,
    contracts,
    costPerLead: cost !== null && leads && leads > 0 ? cost / leads : null,
    costPerEngagement: cost !== null && engagements && engagements > 0 ? cost / engagements : null,
    costPerContract: cost !== null && contracts && contracts > 0 ? cost / contracts : null,
  };
};

const deriveRoiSnapshot = (roi: RoiMetrics): string => {
  const cpl = roi.costPerLead !== null ? `CPL ${fmtMoney(roi.costPerLead)}` : null;
  const cpe = roi.costPerEngagement !== null ? `CPE ${fmtMoney(roi.costPerEngagement)}` : null;
  const cpc = roi.costPerContract !== null ? `CPC ${fmtMoney(roi.costPerContract)}` : null;
  const parts = [cpl, cpe, cpc].filter(Boolean);
  return parts.length ? parts.join(' | ') : 'ROI pending data';
};

export const TargetingBoard: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [boardView, setBoardView] = useState<VisualMode>('table');
  const [detailView, setDetailView] = useState<VisualMode>('kpi');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [quarterFilter, setQuarterFilter] = useState<(typeof quarterOptions)[number]>('All');
  const [decisionFilter, setDecisionFilter] = useState<(typeof decisionOptions)[number]>('All');
  const [typeFilter, setTypeFilter] = useState('All');

  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [selectedNominationId, setSelectedNominationId] = useState<string | null>(null);
  const [dataAsOf, setDataAsOf] = useState('');
  const [decisionSubmitting, setDecisionSubmitting] = useState(false);
  const [decisionFeedback, setDecisionFeedback] = useState<{ message: string; operationId?: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [itemsRes, decisionsRes, actionsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/targeting-pipeline/board/items?limit=300`),
        fetch(`${API_BASE}/api/v2/targeting-pipeline/board/decisions?limit=400`),
        fetch(`${API_BASE}/api/v2/targeting-pipeline/board/actions?limit=400`),
      ]);

      const [itemsJson, decisionsJson, actionsJson] = await Promise.all([
        itemsRes.json() as Promise<BoardPayload<BoardItemApi>>,
        decisionsRes.json() as Promise<BoardPayload<BoardDecisionApi>>,
        actionsRes.json() as Promise<BoardPayload<FollowOnActionApi>>,
      ]);

      const items = Array.isArray(itemsJson?.items) ? itemsJson.items : [];
      const decisions = Array.isArray(decisionsJson?.items) ? decisionsJson.items : [];
      const actions = Array.isArray(actionsJson?.items) ? actionsJson.items : [];

      const latestDecisionByChain = new Map<string, BoardDecisionApi>();
      for (const d of decisions) {
        const chainId = asString(d.chain_id);
        if (!chainId) continue;
        if (!latestDecisionByChain.has(chainId)) {
          latestDecisionByChain.set(chainId, d);
        }
      }

      const actionsByChain = new Map<string, FollowOnActionApi[]>();
      for (const a of actions) {
        const chainId = asString(a.chain_id);
        if (!chainId) continue;
        const list = actionsByChain.get(chainId) || [];
        list.push(a);
        actionsByChain.set(chainId, list);
      }

      const mappedRows: ReviewRow[] = items.map((item) => {
        const nominationId = asString(item.chain_id);
        const decision = latestDecisionByChain.get(nominationId) || null;
        const rowActions = actionsByChain.get(nominationId) || [];
        const roi = buildRoi(item);
        const rowDate =
          asString(item.promoted_to_board_at) ||
          asString(item.decision_recorded_at) ||
          asString(decision?.decided_at) ||
          asString(item.updated_at) ||
          asString(item.created_at);

        return {
          nominationId,
          nominationName: asString(item.title) || nominationId,
          nominationType: asString(item.nomination_type) || 'Nomination',
          rsid: asString(item.impacted_scope) || 'Unavailable',
          date: rowDate,
          status: asString(item.status) || asString(item.current_stage) || 'Pending',
          decisionState: normalizeDecisionState(item, decision),
          requestedFunding: asNumber(item.requested_funding),
          requestedBudget: asNumber(item.requested_budget),
          roiSnapshot: deriveRoiSnapshot(roi),
          brieferOrigin: `${asString(item.briefer_submitter) || 'Unavailable'} / ${asString(item.origin) || asString(item.source_context) || 'Unknown'}`,
          detail: item,
          decision,
          actions: rowActions,
          roi,
        };
      });

      const latest = mappedRows
        .map((r) => r.date)
        .filter(Boolean)
        .sort()
        .slice(-1)[0] || '';

      setRows(mappedRows);
      setDataAsOf(latest);
      setSelectedNominationId((prev) => {
        if (prev && mappedRows.some((r) => r.nominationId === prev)) {
          return prev;
        }
        return mappedRows.length ? mappedRows[0].nominationId : null;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load Targeting Board data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const nominationTypeOptions = useMemo(() => {
    const types = Array.from(new Set(rows.map((r) => r.nominationType).filter(Boolean))).sort();
    return ['All', ...types];
  }, [rows]);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      const quarter = asString(row.detail.requested_quarter).toUpperCase();
      const quarterOk = quarterFilter === 'All' || quarter === quarterFilter.toUpperCase();

      const decisionLabel = row.decisionState === 'pending' ? 'Pending / Awaiting Decision' : `${row.decisionState[0].toUpperCase()}${row.decisionState.slice(1)}`;
      const decisionOk = decisionFilter === 'All' || decisionLabel === decisionFilter;

      const typeOk = typeFilter === 'All' || row.nominationType === typeFilter;

      return quarterOk && decisionOk && typeOk;
    });
  }, [rows, quarterFilter, decisionFilter, typeFilter]);

  useEffect(() => {
    if (!filteredRows.length) {
      setSelectedNominationId(null);
      return;
    }
    if (!selectedNominationId || !filteredRows.some((r) => r.nominationId === selectedNominationId)) {
      setSelectedNominationId(filteredRows[0].nominationId);
    }
  }, [filteredRows, selectedNominationId]);

  const selectedRow = useMemo(
    () => filteredRows.find((r) => r.nominationId === selectedNominationId) || null,
    [filteredRows, selectedNominationId],
  );

  const unresolvedItems = useMemo(() => {
    return filteredRows.flatMap((row) => {
      const issues: { nominationId: string; title: string; reason: string }[] = [];
      const missing = row.detail.readiness?.missing_fields || [];
      const blockers = row.detail.readiness?.blocking_flags || [];
      if (row.decisionState === 'pending') {
        issues.push({ nominationId: row.nominationId, title: row.nominationName, reason: 'Pending / Awaiting Decision' });
      }
      if (row.decisionState === 'deferred') {
        issues.push({ nominationId: row.nominationId, title: row.nominationName, reason: 'Deferred by board for rework' });
      }
      if (missing.length) {
        issues.push({ nominationId: row.nominationId, title: row.nominationName, reason: `Missing: ${missing.join(', ')}` });
      }
      if (blockers.length) {
        issues.push({ nominationId: row.nominationId, title: row.nominationName, reason: `Blocking flags: ${blockers.join(', ')}` });
      }
      return issues;
    });
  }, [filteredRows]);

  const submitDecision = useCallback(
    async (decision: 'approved' | 'modified' | 'deferred' | 'denied') => {
      if (!selectedRow || decisionSubmitting) return;
      setDecisionSubmitting(true);
      setDecisionFeedback(null);
      try {
        const today = new Date();
        const due = new Date(today);
        due.setDate(today.getDate() + 14);
        const payload = {
          chain_id: selectedRow.nominationId,
          decision,
          decision_reason: `${decision} via Targeting Board`,
          approved_funding: selectedRow.requestedFunding,
          approved_budget: selectedRow.requestedBudget,
          approved_resources: selectedRow.detail.requested_resources || 'No changes',
          commander_notes: `${decision} decision recorded from board panel`,
          decided_by: 'Board Recorder',
          decided_at: new Date().toISOString(),
          decision_authority: 'Battalion Commander',
          follow_on_action_title: `Board ${decision} follow-on`,
          follow_on_action_details: selectedRow.detail.recommended_next_action || 'Proceed with board-directed execution actions',
          action_owner: selectedRow.detail.owner_lead || 'Operations Lead',
          action_due_date: due.toISOString().slice(0, 10),
          action_status: 'open',
          created_by: 'board-ui',
          updated_by: 'board-ui',
        };

        const res = await fetch(`${API_BASE}/api/v2/targeting-pipeline/board/decisions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = (await res.json()) as DecisionWriteResponse;
        if (!res.ok || data.status !== 'ok') {
          throw new Error('Unable to record board decision.');
        }

        const linkedOperationId = data.operation_linkage?.operation_id;
        if ((decision === 'approved' || decision === 'modified') && linkedOperationId) {
          setDecisionFeedback({ message: 'Operation created', operationId: linkedOperationId });
        } else {
          setDecisionFeedback({ message: `Decision recorded: ${decision}` });
        }

        await load();
      } catch (e) {
        setDecisionFeedback({ message: e instanceof Error ? e.message : 'Decision submission failed.' });
      } finally {
        setDecisionSubmitting(false);
      }
    },
    [selectedRow, decisionSubmitting, load],
  );


  const decisionColor = (state: DecisionState): string => {
    if (state === 'approved') return '#10B981';
    if (state === 'modified') return '#60A5FA';
    if (state === 'deferred') return '#F59E0B';
    if (state === 'denied') return '#EF4444';
    return '#64748B';
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
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Targeting Board</h1>
          <p className="text-[12px] text-[#64748B] mt-0.5">Board-level review, decisions, and follow-on actions</p>
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
        <select value={quarterFilter} onChange={(e) => setQuarterFilter(e.target.value as typeof quarterFilter)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          {quarterOptions.map((o) => <option key={o} value={o}>{o === 'All' ? 'All Quarters' : o}</option>)}
        </select>
        <select value={decisionFilter} onChange={(e) => setDecisionFilter(e.target.value as typeof decisionFilter)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          {decisionOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          {nominationTypeOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>

      {error && <div className="mb-4 p-3 rounded border border-[#EF4444] bg-[#EF444422] text-[#EF4444] text-[13px]">{error}</div>}
      {loading && <div className="text-[13px] text-[#64748B] mb-4">Loading...</div>}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* LEFT: Nominations table */}
        <div className="xl:col-span-2">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Board Items ({filteredRows.length})</span>
              <div className="flex items-center gap-3">
                {dataAsOf && <span className="text-[11px] text-[#64748B]">As of {fmtDate(dataAsOf)}</span>}
                <VisualModeSwitch value={boardView} onChange={setBoardView} />
              </div>
            </div>
            {boardView === 'table' ? darkTable(
              ['Nomination','Type','Decision','Funding','Priority'],
              filteredRows.length ? filteredRows.map((row) => (
                <tr key={row.nominationId} onClick={() => setSelectedNominationId(row.nominationId)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedNominationId === row.nominationId ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7] font-medium">{row.nominationName}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{row.nominationType}</td>
                  <td className="px-3 py-2">
                    <span style={{ color: decisionColor(row.decisionState) }} className="capitalize">{row.decisionState}</span>
                  </td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{row.requestedFunding != null ? fmtMoney(row.requestedFunding) : row.requestedBudget != null ? fmtMoney(row.requestedBudget) : '—'}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{fmtDate(row.date)}</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No items match current filters</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {filteredRows.slice(0, 12).map((row) => (
                  <div
                    key={row.nominationId}
                    onClick={() => setSelectedNominationId(row.nominationId)}
                    className={`border rounded p-3 cursor-pointer ${selectedNominationId === row.nominationId ? 'bg-[#1D4ED822] border-[#1D4ED8]' : 'bg-[#142F52] border-[#1D3A5C]'}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-[13px] text-[#F3F5F7] font-semibold">{row.nominationName}</div>
                      <div className="text-[12px] capitalize" style={{ color: decisionColor(row.decisionState) }}>{row.decisionState}</div>
                    </div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{row.nominationType} | {row.rsid} | {fmtDate(row.date)}</div>
                  </div>
                ))}
                {!filteredRows.length && <div className="text-[13px] text-[#64748B]">No items match current filters</div>}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Detail + Decision panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2 flex items-center justify-between gap-3">
              <span>Board Decision Panel</span>
              <VisualModeSwitch value={detailView} onChange={setDetailView} />
            </div>
            {!selectedRow && !loading && (
              <div className="text-[13px] text-[#64748B]">Select an item to review.</div>
            )}
            {selectedRow && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selectedRow.nominationName}</div>
                  <div className="text-[12px] text-[#64748B]">{selectedRow.nominationType} · {selectedRow.rsid}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Decision', value: selectedRow.decisionState, color: decisionColor(selectedRow.decisionState) },
                    { label: 'Quarter', value: selectedRow.detail.requested_quarter || '—', color: '#F3F5F7' },
                    { label: 'Funding', value: selectedRow.requestedFunding != null ? fmtMoney(selectedRow.requestedFunding) : '—', color: '#F3F5F7' },
                    { label: 'Budget', value: selectedRow.requestedBudget != null ? fmtMoney(selectedRow.requestedBudget) : '—', color: '#F3F5F7' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</div>
                      <div className="text-[13px] font-semibold capitalize" style={{ color }}>{value}</div>
                    </div>
                  ))}
                </div>
                {selectedRow.detail.problem_statement && (
                  <div>
                    <div className="text-[10px] uppercase text-[#64748B] mb-1">Problem Statement</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedRow.detail.problem_statement}</div>
                  </div>
                )}
                {selectedRow.detail.recommended_next_action && (
                  <div>
                    <div className="text-[10px] uppercase text-[#64748B] mb-1">Recommended Action</div>
                    <div className="text-[13px] text-[#60A5FA]">{selectedRow.detail.recommended_next_action}</div>
                  </div>
                )}
                {/* ROI */}
                <div>
                  <div className="text-[10px] uppercase text-[#64748B] mb-1">ROI Snapshot</div>
                  {detailView === 'table' ? (
                    <div className="text-[12px] text-[#94A3B8]">{selectedRow.roiSnapshot}</div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                        <div className="text-[10px] uppercase text-[#64748B]">CPL</div>
                        <div className="text-[12px] text-[#F3F5F7]">{fmtMoney(selectedRow.roi.costPerLead)}</div>
                      </div>
                      <div className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                        <div className="text-[10px] uppercase text-[#64748B]">CPC</div>
                        <div className="text-[12px] text-[#F3F5F7]">{fmtMoney(selectedRow.roi.costPerContract)}</div>
                      </div>
                    </div>
                  )}
                </div>
                {/* Decision buttons */}
                <div>
                  <div className="text-[10px] uppercase text-[#64748B] mb-2">Record Decision</div>
                  <div className="grid grid-cols-2 gap-2">
                    {(['approved', 'modified', 'deferred', 'denied'] as const).map((d) => (
                      <button key={d} disabled={decisionSubmitting}
                        onClick={() => submitDecision(d)}
                        className="py-1.5 rounded text-[12px] font-semibold border capitalize disabled:opacity-50"
                        style={{ color: decisionColor(d as DecisionState), borderColor: decisionColor(d as DecisionState), background: 'transparent' }}>
                        {d}
                      </button>
                    ))}
                  </div>
                </div>
                {decisionFeedback && (
                  <div className="text-[13px] text-[#10B981] bg-[#10B98122] border border-[#10B981] rounded p-2">
                    {decisionFeedback.message}
                    {decisionFeedback.operationId && <div className="text-[11px] text-[#94A3B8] mt-0.5">Op ID: {decisionFeedback.operationId}</div>}
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

export default TargetingBoard;
