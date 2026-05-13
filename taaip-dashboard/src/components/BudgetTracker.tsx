import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, DollarSign, Filter, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';

// ─── Types ────────────────────────────────────────────────────────────────────

type FundSource = 'LAMP' | 'Direct' | 'Mission';
type DecisionState = 'approved' | 'modified' | 'deferred' | 'denied' | 'pending';

interface BudgetRequest {
  chain_id: string;
  title: string;
  nomination_type: string;
  company: string;
  rsid: string;
  fund_source: FundSource;
  budget_category: string;
  requested_budget: number;
  approved_budget: number;
  priority: string;
  roi_snapshot: string;
  status: string;
  decision_state: DecisionState;
  requested_quarter: string;
  projected_impact: string;
  problem_statement: string;
  source_context: string;
  briefer_submitter: string;
  origin: string;
  approved_resources: string;
  ts: string;
}

interface BudgetSummary {
  total_requested: number;
  total_approved: number;
  total_count: number;
  approved_count: number;
  pending_count: number;
  remaining: number;
}

interface CategoryBreakdown {
  category: string;
  requested_total: number;
  approved_total: number;
}

interface FundSourceData {
  allocated: number;
  pending: number;
  approved: number;
  remaining: number;
}

interface ConstraintFlag {
  chain_id: string;
  title: string;
  flag_type: string;
  message: string;
}

interface BudgetPayload {
  status: string;
  data_as_of: string;
  requests: BudgetRequest[];
  summary: BudgetSummary;
  category_breakdown: CategoryBreakdown[];
  fund_source_breakdown: Record<FundSource, FundSourceData>;
  constraint_flags: ConstraintFlag[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtMoney = (value: number | null | undefined): string => {
  if (value == null || !Number.isFinite(value)) return 'Unavailable';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
};

const fmtDate = (value: string): string => {
  if (!value) return '';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString();
};

const decisionBadge = (state: DecisionState): string => {
  if (state === 'approved') return 'bg-green-100 text-green-800';
  if (state === 'modified') return 'bg-blue-100 text-blue-800';
  if (state === 'deferred') return 'bg-yellow-100 text-yellow-800';
  if (state === 'denied') return 'bg-red-100 text-red-800';
  return 'bg-slate-100 text-slate-700';
};

const fsBadge = (fs: FundSource): string => {
  if (fs === 'LAMP') return 'bg-indigo-100 text-indigo-800';
  if (fs === 'Mission') return 'bg-emerald-100 text-emerald-800';
  return 'bg-amber-100 text-amber-800';
};

const flagBadge = (ft: string): string => {
  if (ft === 'exhausted_pool') return 'border-red-300 bg-red-50 text-red-900';
  if (ft === 'over_allocation_risk') return 'border-orange-300 bg-orange-50 text-orange-900';
  if (ft === 'high_cost_low_return') return 'border-yellow-300 bg-yellow-50 text-yellow-900';
  if (ft === 'mission_misalignment') return 'border-purple-300 bg-purple-50 text-purple-900';
  return 'border-slate-300 bg-slate-50 text-slate-800';
};

const FUND_SOURCES: FundSource[] = ['LAMP', 'Direct', 'Mission'];
const CATEGORIES = ['Events', 'Marketing / Advertising', 'Assets', 'Schools', 'Targeting'];
const TIMEFRAMES = ['All', '30d', '90d', 'ytd', 'fy'];

const EMPTY_SUMMARY: BudgetSummary = { total_requested: 0, total_approved: 0, total_count: 0, approved_count: 0, pending_count: 0, remaining: 0 };
const EMPTY_FS: Record<FundSource, FundSourceData> = {
  LAMP: { allocated: 0, pending: 0, approved: 0, remaining: 0 },
  Direct: { allocated: 0, pending: 0, approved: 0, remaining: 0 },
  Mission: { allocated: 0, pending: 0, approved: 0, remaining: 0 },
};

// ─── Component ────────────────────────────────────────────────────────────────

export const BudgetTracker: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [timeframe, setTimeframe] = useState('All');
    const [companyFilter, setCompanyFilter] = useState('All');
    const [rsidFilter, setRsidFilter] = useState('All');
    const [categoryFilter, setCategoryFilter] = useState('All');
    const [fundSourceTab, setFundSourceTab] = useState<'All' | FundSource>('All');

    // Data
    const [allRequests, setAllRequests] = useState<BudgetRequest[]>([]);
    const [summary, setSummary] = useState<BudgetSummary>(EMPTY_SUMMARY);
    const [categoryBreakdown, setCategoryBreakdown] = useState<CategoryBreakdown[]>([]);
    const [fundSourceBreakdown, setFundSourceBreakdown] = useState<Record<FundSource, FundSourceData>>(EMPTY_FS);
    const [constraintFlags, setConstraintFlags] = useState<ConstraintFlag[]>([]);
    const [dataAsOf, setDataAsOf] = useState('');

    // Selection
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const load = useCallback(async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (timeframe !== 'All') params.set('timeframe', timeframe);
        if (companyFilter !== 'All') params.set('company', companyFilter);
        if (rsidFilter !== 'All') params.set('rsid', rsidFilter);
        if (categoryFilter !== 'All') params.set('category', categoryFilter);
        if (fundSourceTab !== 'All') params.set('fund_source', fundSourceTab);

        const res = await fetch(`${API_BASE}/api/v2/budget/locked?${params.toString()}`);
        const json = (await res.json()) as BudgetPayload;

        const reqs = Array.isArray(json.requests) ? json.requests : [];
        setAllRequests(reqs);
        setSummary(json.summary ?? EMPTY_SUMMARY);
        setCategoryBreakdown(Array.isArray(json.category_breakdown) ? json.category_breakdown : []);
        setFundSourceBreakdown(json.fund_source_breakdown ?? EMPTY_FS);
        setConstraintFlags(Array.isArray(json.constraint_flags) ? json.constraint_flags : []);
        setDataAsOf(json.data_as_of ?? '');

        setSelectedId((prev) => {
          if (prev && reqs.some((r) => r.chain_id === prev)) return prev;
          return reqs.length ? reqs[0].chain_id : null;
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unable to load budget data.');
      } finally {
        setLoading(false);
      }
    }, [timeframe, companyFilter, rsidFilter, categoryFilter, fundSourceTab]);

    useEffect(() => { void load(); }, [load]);

    // Dynamic filter options from data
    const companyOptions = useMemo(() => ['All', ...Array.from(new Set(allRequests.map((r) => r.company).filter(Boolean))).sort()], [allRequests]);
    const rsidOptions = useMemo(() => ['All', ...Array.from(new Set(allRequests.map((r) => r.rsid).filter(Boolean))).sort()], [allRequests]);

    // Apply fund-source tab filter locally (data is already filtered server-side, but tab drives the param)
    const visibleRequests = useMemo(() => {
      if (fundSourceTab === 'All') return allRequests;
      return allRequests.filter((r) => r.fund_source === fundSourceTab);
    }, [allRequests, fundSourceTab]);

    // Keep selection valid when filter changes
    useEffect(() => {
      if (!visibleRequests.length) { setSelectedId(null); return; }
      if (!selectedId || !visibleRequests.some((r) => r.chain_id === selectedId)) {
        setSelectedId(visibleRequests[0].chain_id);
      }
    }, [visibleRequests, selectedId]);

    const selectedRow = useMemo(() => visibleRequests.find((r) => r.chain_id === selectedId) ?? null, [visibleRequests, selectedId]);

    // Budget delta: approved vs requested
    const budgetDelta = (req: BudgetRequest): number | null => {
      if (!req.approved_budget) return null;
      return req.approved_budget - req.requested_budget;
    };

    return (
      <div className="min-h-screen bg-gray-50 p-6">
        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div className="mb-6 flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <DollarSign className="h-6 w-6 text-slate-700" />
            <div>
              <h1 className="text-xl font-bold text-slate-900">BUDGET</h1>
              <p className="mt-0.5 text-xs text-slate-500">Funding requests, constraints, and fund-source control.</p>
            </div>
          </div>
          <button
            onClick={() => void load()}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {dataAsOf && (
          <div className="mb-6 rounded-lg border border-slate-200 bg-slate-100 px-4 py-2 text-xs text-slate-700">
            Data as of: <span className="font-semibold">{fmtDate(dataAsOf)}</span>
          </div>
        )}

        {/* ── Filters ────────────────────────────────────────────────────────── */}
        <div className="mb-6 flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <Filter className="h-4 w-4 self-center text-slate-500" />

          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
            Timeframe
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-800"
            >
              {TIMEFRAMES.map((t) => <option key={t} value={t}>{t === 'All' ? 'All Time' : t}</option>)}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
            Company
            <select
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-800"
            >
              {companyOptions.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
            RSID
            <select
              value={rsidFilter}
              onChange={(e) => setRsidFilter(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-800"
            >
              {rsidOptions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-slate-700">
            Category
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-800"
            >
              <option value="All">All Categories</option>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>

          <button
            onClick={() => { setTimeframe('All'); setCompanyFilter('All'); setRsidFilter('All'); setCategoryFilter('All'); setFundSourceTab('All'); }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
          >
            Reset Filters
          </button>
        </div>

        {/* ── Fund Source Tabs ────────────────────────────────────────────────── */}
        <div className="mb-6 flex gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
          {(['All', ...FUND_SOURCES] as const).map((fs) => (
            <button
              key={fs}
              onClick={() => setFundSourceTab(fs)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${fundSourceTab === fs ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              {fs === 'All' ? 'All Funds' : fs}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
        )}

        {loading ? (
          <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500 shadow-sm">
            Loading budget data...
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-4">
            {/* ── Left 3/4 ─────────────────────────────────────────────────── */}
            <div className="space-y-6 xl:col-span-3">

              {/* Section 1 – Summary Metrics */}
              <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {[
                  { label: 'Total Requested', value: fmtMoney(summary.total_requested), color: 'text-slate-900' },
                  { label: 'Total Approved', value: fmtMoney(summary.total_approved), color: 'text-green-700' },
                  { label: 'Remaining', value: fmtMoney(summary.remaining), color: 'text-blue-700' },
                  { label: 'Requests', value: String(summary.total_count), color: 'text-slate-900', sub: `${summary.approved_count} approved · ${summary.pending_count} pending` },
                ].map(({ label, value, color, sub }) => (
                  <div key={label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
                    {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
                  </div>
                ))}
              </section>

              {/* Section 2 – Funding Requests Table */}
              <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h2 className="text-base font-semibold text-slate-900">Funding Requests</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <th className="px-4 py-3">Request / Nomination Name</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Company</th>
                        <th className="px-4 py-3">RSID</th>
                        <th className="px-4 py-3">Fund Source</th>
                        <th className="px-4 py-3">Requested Budget</th>
                        <th className="px-4 py-3">Approved Budget</th>
                        <th className="px-4 py-3">Priority</th>
                        <th className="px-4 py-3">ROI</th>
                        <th className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleRequests.length === 0 ? (
                        <tr>
                          <td colSpan={10} className="px-4 py-6 text-slate-500">No funding requests match the current filters.</td>
                        </tr>
                      ) : (
                        visibleRequests.map((req) => (
                          <tr
                            key={req.chain_id}
                            onClick={() => setSelectedId(req.chain_id)}
                            className={`cursor-pointer border-b border-slate-50 transition-colors hover:bg-slate-50 ${selectedId === req.chain_id ? 'bg-blue-50' : ''}`}
                          >
                            <td className="max-w-[200px] truncate px-4 py-3 font-medium text-slate-900">{req.title}</td>
                            <td className="px-4 py-3 text-slate-700">{req.nomination_type || '—'}</td>
                            <td className="px-4 py-3 text-slate-700">{req.company || '—'}</td>
                            <td className="px-4 py-3 text-slate-700">{req.rsid || '—'}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${fsBadge(req.fund_source)}`}>
                                {req.fund_source}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-slate-700">{fmtMoney(req.requested_budget)}</td>
                            <td className="px-4 py-3 text-slate-700">{req.approved_budget ? fmtMoney(req.approved_budget) : '—'}</td>
                            <td className="px-4 py-3 text-slate-700">{req.priority}</td>
                            <td className="px-4 py-3 text-xs text-slate-700">{req.roi_snapshot}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${decisionBadge(req.decision_state)}`}>
                                {req.decision_state}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Section 3 – Category Spending Breakdown */}
              <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h2 className="text-base font-semibold text-slate-900">Category Spending Breakdown</h2>
                </div>
                <div className="grid grid-cols-1 gap-4 px-5 py-5 md:grid-cols-5">
                  {categoryBreakdown.map((cb) => {
                    const pct = cb.requested_total > 0 ? Math.round((cb.approved_total / cb.requested_total) * 100) : 0;
                    return (
                      <div key={cb.category} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <p className="text-xs font-semibold text-slate-500">{cb.category}</p>
                        <p className="mt-1 text-base font-bold text-slate-900">{fmtMoney(cb.requested_total)}</p>
                        <p className="text-xs text-slate-500">Requested</p>
                        <p className="mt-2 text-sm font-semibold text-green-700">{fmtMoney(cb.approved_total)}</p>
                        <p className="text-xs text-slate-500">Approved</p>
                        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                          <div className="h-full rounded-full bg-green-500" style={{ width: `${Math.min(pct, 100)}%` }} />
                        </div>
                        <p className="mt-1 text-xs text-slate-400">{pct}% approved</p>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Section 4 – Fund Source Breakdown */}
              <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h2 className="text-base font-semibold text-slate-900">Fund Source Breakdown</h2>
                </div>
                <div className="grid grid-cols-1 gap-4 px-5 py-5 md:grid-cols-3">
                  {FUND_SOURCES.map((fs) => {
                    const data = fundSourceBreakdown[fs] ?? { allocated: 0, pending: 0, approved: 0, remaining: 0 };
                    return (
                      <div key={fs} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${fsBadge(fs)}`}>{fs}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div><p className="text-xs text-slate-500">Allocated</p><p className="font-semibold text-slate-900">{fmtMoney(data.allocated)}</p></div>
                          <div><p className="text-xs text-slate-500">Approved</p><p className="font-semibold text-green-700">{fmtMoney(data.approved)}</p></div>
                          <div><p className="text-xs text-slate-500">Pending</p><p className="font-semibold text-amber-700">{fmtMoney(data.pending)}</p></div>
                          <div><p className="text-xs text-slate-500">Remaining</p><p className="font-semibold text-blue-700">{fmtMoney(data.remaining)}</p></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Section 5 – Funding Constraint Flags */}
              <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-4">
                  <h2 className="text-base font-semibold text-slate-900">Funding Constraint Flags</h2>
                </div>
                <div className="px-5 py-5">
                  {constraintFlags.length === 0 ? (
                    <p className="text-sm text-slate-500">No constraint flags detected in the current filter view.</p>
                  ) : (
                    <div className="space-y-3">
                      {constraintFlags.map((flag, idx) => (
                        <div
                          key={`${flag.chain_id}-${idx}`}
                          className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${flagBadge(flag.flag_type)}`}
                        >
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                          <div>
                            <p className="text-sm font-semibold">{flag.title}</p>
                            <p className="text-sm">{flag.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* ── Section 6 – Right-side Detail Panel ─────────────────────── */}
            <div className="xl:col-span-1">
              <div className="sticky top-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-700">Selected Request</h2>
                {!selectedRow ? (
                  <p className="text-sm text-slate-500">Select a request from the table to view details.</p>
                ) : (
                  <div className="space-y-4 text-sm">
                    <div>
                      <p className="font-semibold text-slate-900 leading-snug">{selectedRow.title}</p>
                      <p className="mt-0.5 text-xs text-slate-500">{selectedRow.nomination_type}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                      <div><p className="text-xs text-slate-500">Company</p><p className="font-medium text-slate-800">{selectedRow.company || '—'}</p></div>
                      <div><p className="text-xs text-slate-500">RSID</p><p className="font-medium text-slate-800">{selectedRow.rsid || '—'}</p></div>
                      <div>
                        <p className="text-xs text-slate-500">Fund Source</p>
                        <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${fsBadge(selectedRow.fund_source)}`}>{selectedRow.fund_source}</span>
                      </div>
                      <div><p className="text-xs text-slate-500">Category</p><p className="font-medium text-slate-800">{selectedRow.budget_category}</p></div>
                    </div>

                    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 space-y-2">
                      <p className="text-xs font-semibold text-slate-600 uppercase">Budget Breakdown</p>
                      <div className="flex justify-between"><span className="text-xs text-slate-500">Requested Budget</span><span className="font-semibold">{fmtMoney(selectedRow.requested_budget)}</span></div>
                      <div className="flex justify-between"><span className="text-xs text-slate-500">Approved Budget</span><span className={`font-semibold ${selectedRow.approved_budget ? 'text-green-700' : 'text-slate-500'}`}>{selectedRow.approved_budget ? fmtMoney(selectedRow.approved_budget) : 'Pending'}</span></div>
                      {budgetDelta(selectedRow) !== null && (
                        <div className="flex justify-between">
                          <span className="text-xs text-slate-500">Delta</span>
                          <span className={`font-semibold ${(budgetDelta(selectedRow) ?? 0) >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                            {(budgetDelta(selectedRow) ?? 0) >= 0 ? '+' : ''}{fmtMoney(budgetDelta(selectedRow))}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between"><span className="text-xs text-slate-500">Approved Resources</span><span className="font-medium text-slate-700 text-xs">{selectedRow.approved_resources || '—'}</span></div>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase mb-1">ROI Summary</p>
                      <p className="text-xs text-slate-700">{selectedRow.roi_snapshot}</p>
                    </div>

                    {selectedRow.projected_impact && (
                      <div>
                        <p className="text-xs font-semibold text-slate-600 uppercase mb-1">Projected Impact</p>
                        <p className="text-xs text-slate-700 leading-relaxed">{selectedRow.projected_impact}</p>
                      </div>
                    )}

                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase mb-1">Funding Impact</p>
                      {selectedRow.decision_state === 'approved' ? (
                        <p className="text-xs text-green-800 bg-green-50 rounded p-2">Budget approved — funds committed to {selectedRow.fund_source} pool.</p>
                      ) : selectedRow.decision_state === 'denied' ? (
                        <p className="text-xs text-red-800 bg-red-50 rounded p-2">Denied — {fmtMoney(selectedRow.requested_budget)} returned to {selectedRow.fund_source} pool.</p>
                      ) : selectedRow.decision_state === 'deferred' ? (
                        <p className="text-xs text-yellow-800 bg-yellow-50 rounded p-2">Deferred — budget held pending re-evaluation.</p>
                      ) : (
                        <p className="text-xs text-slate-700 bg-slate-50 rounded p-2">Pending decision — {fmtMoney(selectedRow.requested_budget)} is uncommitted in {selectedRow.fund_source} pool.</p>
                      )}
                    </div>

                    <div className="border-t border-slate-100 pt-3">
                      <p className="text-xs font-semibold text-slate-600 uppercase mb-2">Adjustment Options</p>
                      <div className="space-y-1 text-xs text-slate-500">
                        <p>• Update fund source or category via Targeting Board</p>
                        <p>• Approve / defer / deny via Board Decision</p>
                        <p>• Reallocate to different RSID via TWG</p>
                      </div>
                    </div>

                    {selectedRow.briefer_submitter && (
                      <div>
                        <p className="text-xs text-slate-500">Briefer / Submitter</p>
                        <p className="font-medium text-slate-800">{selectedRow.briefer_submitter}</p>
                      </div>
                    )}
                    {selectedRow.requested_quarter && (
                      <div>
                        <p className="text-xs text-slate-500">Quarter</p>
                        <p className="font-medium text-slate-800">{selectedRow.requested_quarter}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  export default BudgetTracker;
