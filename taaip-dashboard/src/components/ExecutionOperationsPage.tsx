import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Filter } from 'lucide-react';
import { API_BASE } from '../config/api';
import { PerspectiveMode, PerspectiveSelector, VisualMode, VisualModeSwitch } from './shared/ui';

type OperationStatus = 'On Track' | 'At Risk' | 'Off Track' | 'Completed' | 'Active' | 'Planned';

type LinkedActivity = {
  id: string;
  name: string;
  location: string;
  date: string;
  status: string;
  leadsGenerated?: number;
  engagements?: number;
  contracts?: number;
};

type ActivityResults = {
  totalLeads: number;
  totalEngagements: number;
  totalContracts: number;
};

type Milestone = {
  label: string;
  dueDate: string;
  status: 'Done' | 'In Progress' | 'Pending';
};

type Operation = {
  id: string;
  operationName: string;
  type: string;
  origin: string;
  originType: string;
  sourceNominationId: string;
  sourceBoardDecisionId: string;
  company: string;
  rsid: string;
  status: OperationStatus;
  assignedLead: string;
  startDate: string;
  endDate: string;
  progressPct: number;
  linkedActivities: LinkedActivity[];
  budgetAllocated: number;
  approvedBudget: number;
  fundSource: string;
  roiSnapshot: string;
  overview: string;
  targetingBoardRef: string;
  milestones: Milestone[];
  performanceVsPlan: {
    plannedOutcome: string;
    actualToDate: string;
    delta: string;
  };
  issues: string[];
  executionGaps: string[];
  linkedActivityCount: number;
  activityResults: ActivityResults;
  executionStatusFromActivities: string;
};

type FilterState = {
  timeframe: string;
  company: string;
  rsid: string;
  operationType: string;
  status: string;
};

const OPERATIONS: Operation[] = [
  {
    id: 'op-1001',
    operationName: 'Q2 Urban School Outreach Surge',
    type: 'Engagement Campaign',
    origin: 'Brigade Directive',
    originType: 'Targeting Board',
    sourceNominationId: 'tgt_demo_alpha',
    sourceBoardDecisionId: 'dec_demo_alpha',
    company: 'Alpha Company',
    rsid: 'RSID-1142',
    status: 'On Track',
    assignedLead: 'CPT Rivera',
    startDate: '2026-04-01',
    endDate: '2026-06-20',
    progressPct: 62,
    linkedActivities: [
      { id: 'fa-2101', name: 'Central HS Career Talk', location: 'Springfield', date: '2026-04-16', status: 'Completed' },
      { id: 'fa-2102', name: 'Weekend Parent Forum', location: 'Northgate', date: '2026-04-28', status: 'Scheduled' },
      { id: 'fa-2103', name: 'ASVAB Prep Event', location: 'South Ridge', date: '2026-05-03', status: 'Scheduled' },
    ],
    budgetAllocated: 145000,
    approvedBudget: 145000,
    fundSource: 'LAMP',
    roiSnapshot: 'Projected 2.8x',
    overview: 'Focused urban outreach campaign to increase appointment-to-contract throughput in priority zones.',
    targetingBoardRef: 'TB-2026-ALPHA-042',
    milestones: [
      { label: 'Target List Finalized', dueDate: '2026-04-05', status: 'Done' },
      { label: 'Partner School Coordination', dueDate: '2026-04-25', status: 'In Progress' },
      { label: 'Mid-Cycle Review', dueDate: '2026-05-10', status: 'Pending' },
    ],
    performanceVsPlan: {
      plannedOutcome: '120 qualified leads by end of cycle',
      actualToDate: '74 qualified leads as of 2026-04-24',
      delta: '+6 above pace',
    },
    issues: ['Limited vehicle availability on weekends', 'Two key school calendars shifted by one week'],
    executionGaps: ['Lead handoff lag from field teams', 'Insufficient evening call windows'],
    linkedActivityCount: 3,
    activityResults: { totalLeads: 22, totalEngagements: 14, totalContracts: 4 },
    executionStatusFromActivities: 'active',
  },
  {
    id: 'op-1002',
    operationName: 'Rural Pipeline Stabilization',
    type: 'Territory Recovery',
    origin: 'Market Signal',
    originType: 'Targeting Board',
    sourceNominationId: 'tgt_demo_bravo',
    sourceBoardDecisionId: 'dec_demo_bravo',
    company: 'Bravo Company',
    rsid: 'RSID-2208',
    status: 'At Risk',
    assignedLead: '1LT Monroe',
    startDate: '2026-03-20',
    endDate: '2026-06-01',
    progressPct: 41,
    linkedActivities: [
      { id: 'fa-2220', name: 'County Fair Presence', location: 'Pine Valley', date: '2026-04-11', status: 'Completed' },
      { id: 'fa-2221', name: 'Community College Visit', location: 'Riverton', date: '2026-04-30', status: 'Scheduled' },
    ],
    budgetAllocated: 98000,
    approvedBudget: 98000,
    fundSource: 'Mission',
    roiSnapshot: 'Projected 1.6x',
    overview: 'Recovery operation for low-conversion rural sectors with focus on sustained lead follow-through.',
    targetingBoardRef: 'TB-2026-BRAVO-019',
    milestones: [
      { label: 'Stakeholder Alignment', dueDate: '2026-03-25', status: 'Done' },
      { label: 'Recruiter Rotation Update', dueDate: '2026-04-18', status: 'In Progress' },
      { label: 'Rural Incentive Pilot', dueDate: '2026-05-05', status: 'Pending' },
    ],
    performanceVsPlan: {
      plannedOutcome: '95 qualified leads by cycle midpoint',
      actualToDate: '53 qualified leads as of 2026-04-24',
      delta: '-8 below pace',
    },
    issues: ['Weather-related cancellations impacted two events', 'Delay in regional ad placement approval'],
    executionGaps: ['Low follow-up contact rate within 48 hours'],
    linkedActivityCount: 2,
    activityResults: { totalLeads: 11, totalEngagements: 7, totalContracts: 2 },
    executionStatusFromActivities: 'underperforming',
  },
  {
    id: 'op-1003',
    operationName: 'STEM Talent Conversion Drive',
    type: 'Special Population',
    origin: 'Command Initiative',
    originType: 'Targeting Board',
    sourceNominationId: 'tgt_demo_charlie',
    sourceBoardDecisionId: 'dec_demo_charlie',
    company: 'Charlie Company',
    rsid: 'RSID-3374',
    status: 'Active',
    assignedLead: 'MAJ Bennett',
    startDate: '2026-04-12',
    endDate: '2026-07-10',
    progressPct: 27,
    linkedActivities: [
      { id: 'fa-2331', name: 'Tech Expo Booth', location: 'Metro Center', date: '2026-04-20', status: 'Completed' },
      { id: 'fa-2332', name: 'Engineer Meet & Greet', location: 'Innovation Hub', date: '2026-05-06', status: 'Scheduled' },
    ],
    budgetAllocated: 176000,
    approvedBudget: 176000,
    fundSource: 'Direct',
    roiSnapshot: 'Projected 3.2x',
    overview: 'Pipeline acceleration targeting STEM-qualified prospects in dense metro catchments.',
    targetingBoardRef: 'TB-2026-CHARLIE-031',
    milestones: [
      { label: 'Skill Profile Mapping', dueDate: '2026-04-18', status: 'Done' },
      { label: 'University Partner Cadence', dueDate: '2026-05-02', status: 'In Progress' },
      { label: 'Board Optimization Review', dueDate: '2026-05-20', status: 'Pending' },
    ],
    performanceVsPlan: {
      plannedOutcome: '60 appointments by first 45 days',
      actualToDate: '18 appointments as of 2026-04-24',
      delta: 'On expected pace',
    },
    issues: ['Limited recruiter technical specialization coverage'],
    executionGaps: ['Candidate nurture content not fully localized'],
    linkedActivityCount: 2,
    activityResults: { totalLeads: 8, totalEngagements: 5, totalContracts: 1 },
    executionStatusFromActivities: 'active',
  },
  {
    id: 'op-1004',
    operationName: 'Legacy District Wind-Down',
    type: 'Closure',
    origin: 'Force Realignment',
    originType: 'Targeting Board',
    sourceNominationId: 'tgt_demo_delta',
    sourceBoardDecisionId: 'dec_demo_delta',
    company: 'Delta Company',
    rsid: 'RSID-4410',
    status: 'Completed',
    assignedLead: 'CPT Sloan',
    startDate: '2026-01-10',
    endDate: '2026-04-05',
    progressPct: 100,
    linkedActivities: [
      { id: 'fa-2440', name: 'Final Career Session', location: 'Lakeview', date: '2026-03-28', status: 'Completed' },
      { id: 'fa-2441', name: 'Records Transition', location: 'HQ', date: '2026-04-02', status: 'Completed' },
    ],
    budgetAllocated: 52000,
    approvedBudget: 52000,
    fundSource: 'Mission',
    roiSnapshot: 'Final 1.9x',
    overview: 'Controlled closeout of legacy district operations with transfer to adjacent companies.',
    targetingBoardRef: 'TB-2026-DELTA-004',
    milestones: [
      { label: 'Transition Plan Approved', dueDate: '2026-01-20', status: 'Done' },
      { label: 'Asset Redistribution', dueDate: '2026-03-15', status: 'Done' },
      { label: 'Final Compliance Review', dueDate: '2026-04-05', status: 'Done' },
    ],
    performanceVsPlan: {
      plannedOutcome: 'Complete wind-down with no active backlog',
      actualToDate: 'Completed with 0 unresolved records',
      delta: 'Met plan',
    },
    issues: ['No critical issues'],
    executionGaps: ['None identified'],
    linkedActivityCount: 2,
    activityResults: { totalLeads: 5, totalEngagements: 4, totalContracts: 2 },
    executionStatusFromActivities: 'completed',
  },
];

const HEALTH_LABELS: Array<{ key: OperationStatus; label: string }> = [
  { key: 'Active', label: 'Active' },
  { key: 'On Track', label: 'On Track' },
  { key: 'At Risk', label: 'At Risk' },
  { key: 'Off Track', label: 'Off Track' },
  { key: 'Completed', label: 'Completed' },
];

const GAP_VISIBILITY = [
  { label: 'Resource Gaps', count: 7 },
  { label: 'Schedule Slippages', count: 5 },
  { label: 'Coordination Gaps', count: 4 },
  { label: 'Data Quality Gaps', count: 3 },
];

const MISSION_ALIGNMENT = [
  { label: 'Aligned', count: 9 },
  { label: 'Partially', count: 3 },
  { label: 'Not Aligned', count: 1 },
];

const TIMEFRAMES = ['FY26 Q2', 'FY26 Q3', 'FY26 Q4', 'FY25 Full Year'];

const fmtMoney = (n: number): string => `$${Math.round(n).toLocaleString()}`;

const statusPill = (status: OperationStatus): string => {
  if (status === 'On Track') return 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30';
  if (status === 'At Risk') return 'bg-[#F59E0B]/20 text-[#F59E0B] border-[#F59E0B]/30';
  if (status === 'Off Track') return 'bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30';
  if (status === 'Completed') return 'bg-[#64748B]/20 text-[#64748B] border-[#64748B]/30';
  if (status === 'Active') return 'bg-[#10B981]/20 text-[#10B981] border-[#10B981]/30';
  return 'bg-[#1D4ED8]/20 text-[#60A5FA] border-[#1D4ED8]/30';
};

export const ExecutionOperationsPage: React.FC = () => {
  const [perspective, setPerspective] = useState<PerspectiveMode>('operational');
  const [viewBySection, setViewBySection] = useState<Record<string, VisualMode>>({ operations: 'table' });
  const [apiOperations, setApiOperations] = useState<Operation[]>([]);
  const [filters, setFilters] = useState<FilterState>({
    timeframe: '',
    company: '',
    rsid: '',
    operationType: '',
    status: '',
  });

  const [selectedOperationId, setSelectedOperationId] = useState<string>(OPERATIONS[0]?.id ?? '');
  const [showAddActivity, setShowAddActivity] = useState(false);
  const [addSubmitting, setAddSubmitting] = useState(false);
    const [addError, setAddError] = useState<string | null>(null);
  const [addForm, setAddForm] = useState({
    activity_name: '',
    activity_type: '',
    event_date: '',
    start_time: '',
    end_time: '',
    company: '',
    rsid: '',
    location: '',
    lead_source: '',
    assigned_recruiters: '',
    notes: '',
  });

  useEffect(() => {
    const qp = new URLSearchParams(window.location.search);
    const opId = qp.get('operation_id');
    if (opId) {
      setSelectedOperationId(opId);
    }
  }, []);

  const loadOperations = useCallback(async (): Promise<void> => {
    try {
      const params = new URLSearchParams();
      if (filters.timeframe) params.set('timeframe', filters.timeframe);
      if (filters.company) params.set('company', filters.company);
      if (filters.rsid) params.set('rsid', filters.rsid);
      if (filters.operationType) params.set('operation_type', filters.operationType);
      if (filters.status) params.set('status', filters.status);
      const query = params.toString();
      const res = await fetch(`${API_BASE}/api/v2/operations/locked${query ? `?${query}` : ''}`);
      if (!res.ok) return;
      const payload = (await res.json()) as { operations?: Array<Record<string, unknown>> };
      const rows = Array.isArray(payload.operations) ? payload.operations : [];
      const mapped: Operation[] = rows.map((row) => {
        const opId = String(row.op_id || row.id || '');
        const progress = Number(row.progress_pct || 0);
        const approved = Number(row.approved_budget || 0);
        const budgetUsed = Number(row.budget_used || 0);
        const linkedActivitiesRaw = Array.isArray(row.linked_activities)
          ? (row.linked_activities as Array<Record<string, unknown>>)
          : [];
        const linkedActivities: LinkedActivity[] = linkedActivitiesRaw.map((a) => ({
          id: String(a.activity_id || ''),
          name: String(a.activity_name || ''),
          location: String(a.location || ''),
          date: String(a.event_date || ''),
          status: String(a.status || ''),
          leadsGenerated: Number(a.leads_generated || 0),
          engagements: Number(a.engagements || 0),
          contracts: Number(a.contracts || 0),
        }));
        const activityResultsRaw = (row.activity_results as Record<string, unknown>) || {};
        return {
          id: opId || `op-${Math.random().toString(16).slice(2)}`,
          operationName: String(row.operation_name || 'Unnamed Operation'),
          type: String(row.operation_type || 'Operation'),
          origin: String(row.origin_title || row.origin_type || 'Targeting Board'),
          originType: String(row.origin_type || 'Targeting Board'),
          sourceNominationId: String(row.source_nomination_id || ''),
          sourceBoardDecisionId: String(row.source_board_decision_id || ''),
          company: String(row.company || ''),
          rsid: String(row.rsid || ''),
          status: (String(row.status || 'Planned') as OperationStatus),
          assignedLead: String(row.briefer || row.assigned_personnel || 'Unassigned'),
          startDate: String(row.created_at || '').slice(0, 10),
          endDate: String(row.timeline || row.updated_at || '').slice(0, 10),
          progressPct: Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0,
          linkedActivities,
          budgetAllocated: approved > 0 ? approved : budgetUsed,
          approvedBudget: approved,
          fundSource: String(row.fund_source || ''),
          roiSnapshot: String(row.real_roi || 'ROI pending data'),
          overview: String(row.objective || ''),
          targetingBoardRef: String(row.source_board_decision_id || row.source_nomination_id || ''),
          milestones: [],
          performanceVsPlan: {
            plannedOutcome: String(row.expected_outcome || 'Planned outcome not specified'),
            actualToDate: String(row.actual_outcome || 'Actual outcome pending'),
            delta: String(row.variance || 'Variance pending'),
          },
          issues: Array.isArray(row.issues) ? row.issues.map((x) => String(x)) : [],
          executionGaps: Array.isArray(row.execution_gaps) ? row.execution_gaps.map((x) => String(x)) : [],
          linkedActivityCount: Number(row.linked_activity_count || linkedActivities.length || 0),
          activityResults: {
            totalLeads: Number(activityResultsRaw.total_leads || 0),
            totalEngagements: Number(activityResultsRaw.total_engagements || 0),
            totalContracts: Number(activityResultsRaw.total_contracts || 0),
          },
          executionStatusFromActivities: String(row.execution_status_from_activities || 'no_activities'),
        };
      });
      setApiOperations(mapped);
    } catch {
      // Keep static data fallback if API is unavailable.
    }
  }, [filters]);

  useEffect(() => {
    void loadOperations();
  }, [loadOperations]);

  const operations = apiOperations.length ? apiOperations : OPERATIONS;

  const companies = useMemo(() => Array.from(new Set(operations.map((op) => op.company))), [operations]);
  const rsids = useMemo(() => Array.from(new Set(operations.map((op) => op.rsid))), [operations]);
  const operationTypes = useMemo(() => Array.from(new Set(operations.map((op) => op.type))), [operations]);
  const statuses = useMemo(() => Array.from(new Set(operations.map((op) => op.status))), [operations]);

  const filteredOperations = useMemo(() => {
    return operations.filter((op) => {
      if (filters.company && op.company !== filters.company) return false;
      if (filters.rsid && op.rsid !== filters.rsid) return false;
      if (filters.operationType && op.type !== filters.operationType) return false;
      if (filters.status && op.status !== filters.status) return false;
      return true;
    });
  }, [filters, operations]);

  const selectedOperation = useMemo(() => {
    const found = filteredOperations.find((op) => op.id === selectedOperationId);
    if (found) return found;
    return filteredOperations[0] ?? null;
  }, [filteredOperations, selectedOperationId]);

  const healthSnapshot = useMemo(
    () =>
      HEALTH_LABELS.map((item) => ({
        label: item.label,
        count: filteredOperations.filter((op) => op.status === item.key).length,
      })),
    [filteredOperations],
  );

  const openActivityDetail = (activityId: string): void => {
    window.open(`/operations/activity-detail/${activityId}`, '_blank');
  };

  const createFieldActivity = async (): Promise<void> => {
    if (!selectedOperation) return;
    setAddSubmitting(true);
    setAddError(null);
    try {
      const payload = {
        ...addForm,
        company: selectedOperation.company || addForm.company,
        rsid: selectedOperation.rsid || addForm.rsid,
      };
      const res = await fetch(`${API_BASE}/api/v2/operations/${encodeURIComponent(selectedOperation.id)}/field-activities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || data.status !== 'ok') {
        throw new Error(data?.detail || 'Unable to create field activity.');
      }
      setShowAddActivity(false);
      setAddForm({
        activity_name: '',
        activity_type: '',
        event_date: '',
        start_time: '',
        end_time: '',
        company: '',
        rsid: '',
        location: '',
        lead_source: '',
        assigned_recruiters: '',
        notes: '',
      });
      await loadOperations();
      setSelectedOperationId(selectedOperation.id);
    } catch (e) {
      setAddError(e instanceof Error ? e.message : 'Unable to create field activity.');
    } finally {
      setAddSubmitting(false);
    }
  };

  const openTargetingBoard = (targetingBoardRef: string): void => {
    const safeRef = encodeURIComponent(targetingBoardRef || 'placeholder');
    window.open(`/targeting-board?decision_id=${safeRef}`, '_blank');
  };

  const openRoiDashboard = (operation: Operation): void => {
    const query = new URLSearchParams({
      company: operation.company,
      rsid: operation.rsid,
      operation_id: operation.id,
    }).toString();
    window.open(`/roi-dashboard?${query}`, '_blank');
  };


  const statusColor = (s: OperationStatus): string => {
    if (s === 'On Track') return '#10B981';
    if (s === 'At Risk') return '#F59E0B';
    if (s === 'Off Track' || s === 'Completed') return '#EF4444';
    return '#60A5FA';
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
        <h1 className="text-[18px] font-bold tracking-[0.04em] uppercase text-[#F3F5F7]">Execution Operations</h1>
        <p className="text-[12px] text-[#64748B] mt-0.5">Board-approved operations and execution status</p>
      </div>

      {/* Perspective Selector */}
      <div className="mb-5 bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
        <PerspectiveSelector value={perspective} onChange={setPerspective} />
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap gap-2">
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select value={filters.company} onChange={(e) => setFilters({ ...filters, company: e.target.value })}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All Companies</option>
          {companies.map((c: string) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={filters.rsid} onChange={(e) => setFilters({ ...filters, rsid: e.target.value })}
          className="text-[12px] px-2 py-1.5 rounded border border-[#1D3A5C] bg-[#0E2847] text-[#F3F5F7]">
          <option value="">All RSIDs</option>
          {rsids.map((r: string) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* LEFT: Operations table */}
        <div className="xl:col-span-2">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md overflow-hidden">
            <div className="px-4 py-2 border-b border-[#1D3A5C] flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94A3B8]">Operations ({filteredOperations.length})</span>
              <VisualModeSwitch value={viewBySection.operations} onChange={(v) => setViewBySection((prev) => ({ ...prev, operations: v }))} />
            </div>
            {viewBySection.operations === 'table' ? darkTable(
              ['Operation','Type','Company','Status','Progress'],
              filteredOperations.length ? filteredOperations.map((op) => (
                <tr key={op.id} onClick={() => setSelectedOperationId(op.id)}
                  className={`border-b border-[#152A45] cursor-pointer ${selectedOperationId === op.id ? 'bg-[#1D4ED822]' : 'hover:bg-[#142F52]'}`}>
                  <td className="px-3 py-2 text-[#F3F5F7] font-medium">{op.operationName}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{op.type}</td>
                  <td className="px-3 py-2 text-[#94A3B8]">{op.company}</td>
                  <td className="px-3 py-2"><span style={{ color: statusColor(op.status) }}>{op.status}</span></td>
                  <td className="px-3 py-2 text-[#F3F5F7]">{op.progressPct}%</td>
                </tr>
              )) : (
                <tr><td className="px-3 py-4 text-[#64748B]" colSpan={5}>No operations</td></tr>
              )
            ) : (
              <div className="p-4 space-y-2">
                {filteredOperations.length > 0 ? filteredOperations.map((op) => (
                  <div key={op.id} onClick={() => setSelectedOperationId(op.id)}
                    className={`bg-[#142F52] border rounded p-3 cursor-pointer ${selectedOperationId === op.id ? 'border-[#1D4ED8]' : 'border-[#1D3A5C] hover:border-[#1D4ED8]/50'}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[13px] text-[#F3F5F7] font-semibold">{op.operationName}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${statusPill(op.status)}`}>{op.status}</span>
                    </div>
                    <div className="text-[12px] text-[#94A3B8] mt-1">{op.type} · {op.company} · {op.progressPct}%</div>
                  </div>
                )) : <div className="text-[13px] text-[#64748B]">No operations</div>}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Detail panel */}
        <aside className="xl:col-span-1">
          <div className="bg-[#0E2847] border border-[#1D3A5C] rounded-md p-4 space-y-4 sticky top-4">
            <div className="text-[11px] uppercase tracking-[0.08em] text-[#64748B] border-b border-[#1D3A5C] pb-2">Operation Detail</div>
            {!selectedOperation && (
              <div className="text-[13px] text-[#64748B]">Select an operation to view details.</div>
            )}
            {selectedOperation && (
              <>
                <div>
                  <div className="text-[15px] font-semibold text-[#F3F5F7]">{selectedOperation.operationName}</div>
                  <div className="text-[12px] text-[#64748B]">{selectedOperation.type} · {selectedOperation.rsid}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Status', value: selectedOperation.status, color: statusColor(selectedOperation.status) },
                    { label: 'Lead', value: selectedOperation.assignedLead, color: '#F3F5F7' },
                    { label: 'Progress', value: `${selectedOperation.progressPct}%`, color: '#F3F5F7' },
                    { label: 'Fund Source', value: selectedOperation.fundSource, color: '#F3F5F7' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-[#142F52] border border-[#1D3A5C] rounded p-2">
                      <div className="text-[10px] uppercase tracking-[0.07em] text-[#64748B]">{label}</div>
                      <div className="text-[13px] font-semibold" style={{ color }}>{value}</div>
                    </div>
                  ))}
                </div>
                {selectedOperation.overview && (
                  <div>
                    <div className="text-[10px] uppercase text-[#64748B] mb-1">Overview</div>
                    <div className="text-[13px] text-[#94A3B8]">{selectedOperation.overview}</div>
                  </div>
                )}
                {selectedOperation.milestones.length > 0 && (
                  <div>
                    <div className="text-[10px] uppercase text-[#64748B] mb-2">Milestones</div>
                    <div className="space-y-1 text-[12px]">
                      {selectedOperation.milestones.map((m, i) => (
                        <div key={i} className="flex justify-between items-center p-1 rounded bg-[#142F52] border border-[#1D3A5C]">
                          <span className="text-[#94A3B8]">{m.label}</span>
                          <span style={{ color: m.status === 'Done' ? '#10B981' : m.status === 'In Progress' ? '#F59E0B' : '#64748B' }} className="text-[11px]">{m.status}</span>
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

export default ExecutionOperationsPage;
