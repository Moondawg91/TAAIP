import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  CalendarDays,
  Clock3,
  RefreshCw,
  School,
  Target,
  Users
} from 'lucide-react';
import { UniversalFilter, FilterState } from './UniversalFilter';
import { API_BASE } from '../config/api';

type ViewMode = 'cards' | 'table' | 'summary';
type TargetFilter = 'all' | 'targeted' | 'non-targeted';
type SchoolTypeFilter = 'all' | 'high-school' | 'college';

type SchoolTarget = {
  school_id: string;
  name: string;
  type: string;
  location: string;
  assigned: boolean;
  zone_valid: boolean;
  alrl_milestones: number;
  sasvab_tests: number;
  leads: number;
  conversions: number;
  priority: string;
  roi_score?: number | null;
  roi_label?: string;
};

type SchoolCoverageRow = {
  id?: string;
  school_name?: string;
  name?: string;
  school_type?: string;
  city?: string;
  state?: string;
  zip_code?: string;
};

type SchoolEventRow = {
  id: string;
  name?: string;
  event_date?: string;
  org_unit_id?: string;
  location_name?: string;
  status?: string;
};

type SchoolMilestoneRow = {
  id: string;
  school_id?: string;
  milestone_type?: string;
  milestone_date?: string;
  created_at?: string;
};

type RecruitingOpsPlan = {
  plan_id: string;
  unit_type: string;
  unit_name: string;
  status: string;
  last_updated: string;
  compliance_score: number;
};

type FeedState<T> = {
  rows: T[];
  error: string | null;
  loading: boolean;
  lastUpdated: string | null;
};

function nowStamp(): string {
  return new Date().toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function safeNumber(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function safeText(value: unknown, fallback = 'Unknown'): string {
  const t = String(value ?? '').trim();
  return t || fallback;
}

function isHighSchool(typeValue: string): boolean {
  const t = typeValue.toLowerCase();
  return t.includes('high') || t.includes('secondary') || t.includes('hs');
}

function isCollege(typeValue: string): boolean {
  const t = typeValue.toLowerCase();
  return t.includes('college') || t.includes('university') || t.includes('post-secondary') || t.includes('postsecondary');
}

function isTargetedSchool(row: SchoolTarget): boolean {
  const priority = String(row.priority || '').toLowerCase();
  return priority.includes('must win') || priority.includes('must keep') || row.conversions > 0;
}

function opportunitySignal(row: SchoolTarget): number {
  const base = safeNumber(row.leads) + safeNumber(row.alrl_milestones) + safeNumber(row.sasvab_tests);
  const friction = (row.assigned ? 0 : 4) + (row.zone_valid ? 0 : 2);
  const produced = safeNumber(row.conversions) * 2;
  return Math.max(0, base + friction - produced);
}

export const TalentAcquisitionTechnicianDashboard: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({ rsid: '', zipcode: '', cbsa: '' });
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [targetFilter, setTargetFilter] = useState<TargetFilter>('all');
  const [schoolTypeFilter, setSchoolTypeFilter] = useState<SchoolTypeFilter>('all');

  const [targetsFeed, setTargetsFeed] = useState<FeedState<SchoolTarget>>({ rows: [], error: null, loading: true, lastUpdated: null });
  const [coverageFeed, setCoverageFeed] = useState<FeedState<SchoolCoverageRow>>({ rows: [], error: null, loading: true, lastUpdated: null });
  const [eventsFeed, setEventsFeed] = useState<FeedState<SchoolEventRow>>({ rows: [], error: null, loading: true, lastUpdated: null });
  const [milestonesFeed, setMilestonesFeed] = useState<FeedState<SchoolMilestoneRow>>({ rows: [], error: null, loading: true, lastUpdated: null });
  const [opsPlansFeed, setOpsPlansFeed] = useState<FeedState<RecruitingOpsPlan>>({ rows: [], error: null, loading: true, lastUpdated: null });

  const fetchSchoolRecruitingData = useCallback(async () => {
    const params = new URLSearchParams();
    if (filters.rsid) params.append('rsid', filters.rsid);
    if (filters.zipcode) params.append('zipcode', filters.zipcode);
    if (filters.cbsa) params.append('cbsa', filters.cbsa);
    const query = params.toString();
    const stamp = nowStamp();

    setTargetsFeed((prev) => ({ ...prev, loading: true }));
    setCoverageFeed((prev) => ({ ...prev, loading: true }));
    setEventsFeed((prev) => ({ ...prev, loading: true }));
    setMilestonesFeed((prev) => ({ ...prev, loading: true }));
    setOpsPlansFeed((prev) => ({ ...prev, loading: true }));

    const [targetsResp, coverageResp, eventsResp, milestonesResp, opsResp] = await Promise.allSettled([
      fetch(`${API_BASE}/api/v2/420t/school-targets${query ? `?${query}` : ''}`),
      fetch(`${API_BASE}/api/v2/school/coverage`),
      fetch(`${API_BASE}/api/v2/school/events`),
      fetch(`${API_BASE}/api/v2/school/milestones`),
      fetch(`${API_BASE}/api/v2/420t/recruiting-ops-plans${query ? `?${query}` : ''}`)
    ]);

    if (targetsResp.status === 'fulfilled') {
      try {
        const payload = await targetsResp.value.json();
        const rows = Array.isArray(payload?.schools) ? payload.schools : [];
        setTargetsFeed({ rows, error: targetsResp.value.ok ? null : `HTTP ${targetsResp.value.status}`, loading: false, lastUpdated: stamp });
      } catch {
        setTargetsFeed({ rows: [], error: 'No school target data returned', loading: false, lastUpdated: stamp });
      }
    } else {
      setTargetsFeed({ rows: [], error: 'School target feed unavailable', loading: false, lastUpdated: stamp });
    }

    if (coverageResp.status === 'fulfilled') {
      try {
        const payload = await coverageResp.value.json();
        const rows = Array.isArray(payload?.rows) ? payload.rows : [];
        const error = payload?.status === 'not_loaded' ? 'School ownership feed unavailable' : null;
        setCoverageFeed({ rows, error, loading: false, lastUpdated: stamp });
      } catch {
        setCoverageFeed({ rows: [], error: 'No school ownership data returned', loading: false, lastUpdated: stamp });
      }
    } else {
      setCoverageFeed({ rows: [], error: 'School ownership feed unavailable', loading: false, lastUpdated: stamp });
    }

    if (eventsResp.status === 'fulfilled') {
      try {
        const payload = await eventsResp.value.json();
        const rows = Array.isArray(payload?.rows) ? payload.rows : [];
        setEventsFeed({ rows, error: eventsResp.value.ok ? null : `HTTP ${eventsResp.value.status}`, loading: false, lastUpdated: stamp });
      } catch {
        setEventsFeed({ rows: [], error: 'No school event data returned', loading: false, lastUpdated: stamp });
      }
    } else {
      setEventsFeed({ rows: [], error: 'School events feed unavailable', loading: false, lastUpdated: stamp });
    }

    if (milestonesResp.status === 'fulfilled') {
      try {
        const payload = await milestonesResp.value.json();
        const rows = Array.isArray(payload?.rows) ? payload.rows : [];
        const error = payload?.status === 'not_loaded' ? 'ALRL/school milestone feed unavailable' : null;
        setMilestonesFeed({ rows, error, loading: false, lastUpdated: stamp });
      } catch {
        setMilestonesFeed({ rows: [], error: 'No milestone data returned', loading: false, lastUpdated: stamp });
      }
    } else {
      setMilestonesFeed({ rows: [], error: 'Milestone feed unavailable', loading: false, lastUpdated: stamp });
    }

    if (opsResp.status === 'fulfilled') {
      try {
        const payload = await opsResp.value.json();
        const rows = Array.isArray(payload?.plans) ? payload.plans : [];
        setOpsPlansFeed({ rows, error: opsResp.value.ok ? null : `HTTP ${opsResp.value.status}`, loading: false, lastUpdated: stamp });
      } catch {
        setOpsPlansFeed({ rows: [], error: 'No school execution plan data returned', loading: false, lastUpdated: stamp });
      }
    } else {
      setOpsPlansFeed({ rows: [], error: 'School execution plan feed unavailable', loading: false, lastUpdated: stamp });
    }
  }, [filters.rsid, filters.zipcode, filters.cbsa]);

  useEffect(() => {
    fetchSchoolRecruitingData();
    const interval = setInterval(fetchSchoolRecruitingData, 60000);
    return () => clearInterval(interval);
  }, [fetchSchoolRecruitingData]);

  const schoolTypeOptions = useMemo(
    () => [
      { value: 'all' as SchoolTypeFilter, label: 'All schools' },
      { value: 'high-school' as SchoolTypeFilter, label: 'High school' },
      { value: 'college' as SchoolTypeFilter, label: 'College' }
    ],
    []
  );

  const filteredSchools = useMemo(() => {
    return targetsFeed.rows.filter((row) => {
      const typeValue = safeText(row.type, 'School');
      const matchesType =
        schoolTypeFilter === 'all' ||
        (schoolTypeFilter === 'high-school' && isHighSchool(typeValue)) ||
        (schoolTypeFilter === 'college' && isCollege(typeValue));
      const targeted = isTargetedSchool(row);
      const matchesTarget = targetFilter === 'all' || (targetFilter === 'targeted' ? targeted : !targeted);
      return matchesType && matchesTarget;
    });
  }, [targetsFeed.rows, schoolTypeFilter, targetFilter]);

  const filteredSchoolIdSet = useMemo(() => {
    return new Set(filteredSchools.map((s) => safeText(s.school_id, '')));
  }, [filteredSchools]);

  const filteredSchoolNameTokens = useMemo(() => {
    return filteredSchools
      .map((s) => safeText(s.name, '').toLowerCase())
      .filter((name) => name.length > 3);
  }, [filteredSchools]);

  const filteredCoverageRows = useMemo(() => {
    if (filteredSchools.length === 0) {
      return [];
    }
    return coverageFeed.rows.filter((c) => {
      const n = safeText(c.school_name || c.name, '').toLowerCase();
      if (!n) {
        return false;
      }
      return filteredSchoolNameTokens.some((token) => n.includes(token) || token.includes(n));
    });
  }, [coverageFeed.rows, filteredSchools.length, filteredSchoolNameTokens]);

  const filteredEventRows = useMemo(() => {
    if (filteredSchools.length === 0) {
      return [];
    }
    return eventsFeed.rows.filter((e) => {
      const haystack = `${safeText(e.name, '')} ${safeText(e.location_name, '')}`.toLowerCase();
      if (!haystack.trim()) {
        return false;
      }
      return filteredSchoolNameTokens.some((token) => haystack.includes(token));
    });
  }, [eventsFeed.rows, filteredSchools.length, filteredSchoolNameTokens]);

  const filteredMilestoneRows = useMemo(() => {
    if (filteredSchools.length === 0) {
      return [];
    }
    return milestonesFeed.rows.filter((m) => {
      const schoolId = safeText(m.school_id, '');
      return schoolId ? filteredSchoolIdSet.has(schoolId) : false;
    });
  }, [milestonesFeed.rows, filteredSchools.length, filteredSchoolIdSet]);

  const schoolMetrics = useMemo(() => {
    const source = filteredSchools;
    const highSchools = source.filter((r) => isHighSchool(safeText(r.type, ''))).length;
    const colleges = source.filter((r) => isCollege(safeText(r.type, ''))).length;
    const assigned = source.filter((r) => r.assigned).length;
    const unassigned = source.filter((r) => !r.assigned).length;
    const targeted = source.filter((r) => isTargetedSchool(r)).length;
    const nonTargeted = source.length - targeted;
    const accessReady = source.filter((r) => r.assigned && r.zone_valid).length;
    const accessNeedsWork = source.length - accessReady;

    const eventsCount = filteredEventRows.length;
    const milestoneCount = filteredMilestoneRows.length;
    const totalLeads = source.reduce((sum, r) => sum + safeNumber(r.leads), 0);
    const totalContracts = source.reduce((sum, r) => sum + safeNumber(r.conversions), 0);
    const totalTests = source.reduce((sum, r) => sum + safeNumber(r.sasvab_tests), 0);
    const totalAlrl = source.reduce((sum, r) => sum + safeNumber(r.alrl_milestones), 0);
    const totalOpportunity = source.reduce((sum, r) => sum + opportunitySignal(r), 0);

    return {
      schools: source.length,
      highSchools,
      colleges,
      assigned,
      unassigned,
      targeted,
      nonTargeted,
      accessReady,
      accessNeedsWork,
      eventsCount,
      milestoneCount,
      totalLeads,
      totalContracts,
      totalTests,
      totalAlrl,
      totalOpportunity
    };
  }, [filteredSchools, filteredEventRows.length, filteredMilestoneRows.length]);

  const schoolsNeedingTargeting = useMemo(() => {
    return filteredSchools
      .filter((r) => !isTargetedSchool(r))
      .map((r) => ({
        ...r,
        opportunity: opportunitySignal(r)
      }))
      .sort((a, b) => b.opportunity - a.opportunity)
      .slice(0, 15);
  }, [filteredSchools]);

  const schoolsOpportunityList = useMemo(() => {
    return filteredSchools
      .map((r) => ({
        ...r,
        opportunity: opportunitySignal(r),
        targeted: isTargetedSchool(r)
      }))
      .sort((a, b) => b.opportunity - a.opportunity)
      .slice(0, 20);
  }, [filteredSchools]);

  const feedIssues = [
    targetsFeed.error,
    coverageFeed.error,
    eventsFeed.error,
    milestonesFeed.error,
    opsPlansFeed.error
  ].filter(Boolean) as string[];

  const renderCardsView = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">School Ownership / Inventory</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{schoolMetrics.schools}</p>
          <p className="text-xs text-slate-600 mt-1">High Schools: {schoolMetrics.highSchools} | Colleges: {schoolMetrics.colleges}</p>
          <p className="text-xs text-slate-600">Assigned: {schoolMetrics.assigned} | Unassigned: {schoolMetrics.unassigned}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Targeted Schools</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{schoolMetrics.targeted}</p>
          <p className="text-xs text-slate-600 mt-1">Non-targeted: {schoolMetrics.nonTargeted}</p>
          <p className="text-xs text-slate-600">Should target: {schoolsNeedingTargeting.length}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Access / Engagement</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{schoolMetrics.accessReady}</p>
          <p className="text-xs text-slate-600 mt-1">Access ready schools</p>
          <p className="text-xs text-slate-600">Events: {schoolMetrics.eventsCount} | Milestones: {schoolMetrics.milestoneCount}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Outcomes / Opportunity Remaining</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{schoolMetrics.totalContracts}</p>
          <p className="text-xs text-slate-600 mt-1">Contracts from schools</p>
          <p className="text-xs text-slate-600">Opportunity signal remaining: {schoolMetrics.totalOpportunity}</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h3 className="font-semibold text-slate-900">Targeted Schools</h3>
        {filteredSchools.filter((s) => isTargetedSchool(s)).length === 0 ? (
          <p className="text-sm text-slate-500 mt-3">No targeted schools returned for this filter scope.</p>
        ) : (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {filteredSchools
              .filter((s) => isTargetedSchool(s))
              .slice(0, 9)
              .map((s) => (
                <div key={s.school_id} className="border border-slate-200 rounded-md p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-slate-900">{safeText(s.name, 'Unknown School')}</p>
                      <p className="text-xs text-slate-600 mt-1">{safeText(s.type, 'School')} | {safeText(s.location, 'No location')}</p>
                    </div>
                    <span className="text-[11px] px-2 py-1 rounded bg-amber-100 text-amber-800 uppercase font-medium">{safeText(s.priority, 'Monitor')}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
                    <div>
                      <p className="text-slate-500">Leads</p>
                      <p className="font-semibold text-slate-900">{safeNumber(s.leads)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Contracts</p>
                      <p className="font-semibold text-slate-900">{safeNumber(s.conversions)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">ALRL</p>
                      <p className="font-semibold text-slate-900">{safeNumber(s.alrl_milestones)}</p>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h3 className="font-semibold text-slate-900">Schools That Should Be Targeted</h3>
        <p className="text-xs text-slate-600 mt-1">Ranked by school opportunity signal (leads + ALRL + tests with access gaps and low production).</p>
        {schoolsNeedingTargeting.length === 0 ? (
          <p className="text-sm text-slate-500 mt-3">No non-targeted schools with opportunity signal returned.</p>
        ) : (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            {schoolsNeedingTargeting.slice(0, 8).map((s) => (
              <div key={s.school_id} className="border border-slate-200 rounded-md p-3 flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-slate-900">{safeText(s.name, 'Unknown School')}</p>
                  <p className="text-xs text-slate-600">{safeText(s.type, 'School')} | {safeText(s.location, 'No location')}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Opportunity</p>
                  <p className="font-semibold text-slate-900">{s.opportunity}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderTableView = () => (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">School Recruiting Roster</h3>
          <p className="text-xs text-slate-600">Targeted vs non-targeted, ownership/access, engagement, outcomes, ALRL, and opportunity signal</p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-3 py-2 text-left">School</th>
              <th className="px-3 py-2 text-left">Type</th>
              <th className="px-3 py-2 text-left">Targeted</th>
              <th className="px-3 py-2 text-left">Ownership / Access</th>
              <th className="px-3 py-2 text-right">Leads</th>
              <th className="px-3 py-2 text-right">Contracts</th>
              <th className="px-3 py-2 text-right">ASVAB Tests</th>
              <th className="px-3 py-2 text-right">ALRL</th>
              <th className="px-3 py-2 text-right">Opportunity Signal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {schoolsOpportunityList.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-slate-500" colSpan={9}>No school data returned for this selection.</td>
              </tr>
            ) : (
              schoolsOpportunityList.map((s) => {
                const targeted = isTargetedSchool(s);
                const accessLabel = s.assigned && s.zone_valid ? 'Owned / Access Ready' : s.assigned ? 'Owned / Access Review' : 'Unassigned';
                return (
                  <tr key={s.school_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-900">{safeText(s.name, 'Unknown School')}</td>
                    <td className="px-3 py-2 text-slate-700">{safeText(s.type, 'School')}</td>
                    <td className="px-3 py-2">
                      <span className={`text-[11px] px-2 py-1 rounded uppercase font-medium ${
                        targeted ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {targeted ? 'Targeted' : 'Non-targeted'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-700">{accessLabel}</td>
                    <td className="px-3 py-2 text-right text-slate-900">{safeNumber(s.leads)}</td>
                    <td className="px-3 py-2 text-right text-slate-900">{safeNumber(s.conversions)}</td>
                    <td className="px-3 py-2 text-right text-slate-900">{safeNumber(s.sasvab_tests)}</td>
                    <td className="px-3 py-2 text-right text-slate-900">{safeNumber(s.alrl_milestones)}</td>
                    <td className="px-3 py-2 text-right font-semibold text-slate-900">{s.opportunity}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <h3 className="font-semibold text-slate-900">School Engagement Activity</h3>
          {filteredEventRows.length === 0 ? (
            <p className="text-sm text-slate-500 mt-3">No school events found for selected filters.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {filteredEventRows.slice(0, 8).map((e) => (
                <div key={e.id} className="border border-slate-200 rounded p-2">
                  <p className="text-sm font-medium text-slate-900">{safeText(e.name, 'School Event')}</p>
                  <p className="text-xs text-slate-600 mt-1">{safeText(e.event_date, 'Date unavailable')} | {safeText(e.status, 'Status unavailable')}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-4">
          <h3 className="font-semibold text-slate-900">ALRL / School Milestones</h3>
          {filteredMilestoneRows.length === 0 ? (
            <p className="text-sm text-slate-500 mt-3">No ALRL milestones found for selected filters.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {filteredMilestoneRows.slice(0, 8).map((m) => (
                <div key={m.id} className="border border-slate-200 rounded p-2">
                  <p className="text-sm font-medium text-slate-900">{safeText(m.milestone_type, 'Milestone')}</p>
                  <p className="text-xs text-slate-600 mt-1">School ID: {safeText(m.school_id, 'Unknown')} | {safeText(m.milestone_date, 'Date unavailable')}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderSummaryView = () => (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h3 className="font-semibold text-slate-900">School Recruiting Summary / Briefing</h3>
        <div className="mt-3 space-y-2 text-sm text-slate-700">
          <p>
            School ownership inventory currently tracks <span className="font-semibold text-slate-900">{schoolMetrics.schools}</span> schools
            ({schoolMetrics.highSchools} high schools, {schoolMetrics.colleges} colleges) with
            <span className="font-semibold text-slate-900"> {schoolMetrics.assigned}</span> assigned and
            <span className="font-semibold text-slate-900"> {schoolMetrics.unassigned}</span> unassigned.
          </p>
          <p>
            Targeted school status shows <span className="font-semibold text-slate-900">{schoolMetrics.targeted}</span> targeted schools and
            <span className="font-semibold text-slate-900"> {schoolMetrics.nonTargeted}</span> non-targeted schools,
            with <span className="font-semibold text-slate-900">{schoolsNeedingTargeting.length}</span> schools flagged as high school-opportunity candidates.
          </p>
          <p>
            School engagement and relationship indicators report <span className="font-semibold text-slate-900">{schoolMetrics.eventsCount}</span> school events and
            <span className="font-semibold text-slate-900"> {schoolMetrics.milestoneCount}</span> ALRL/school milestones in current feeds.
          </p>
          <p>
            School outcomes and opportunity metrics report <span className="font-semibold text-slate-900">{schoolMetrics.totalContracts}</span> contracts,
            <span className="font-semibold text-slate-900"> {schoolMetrics.totalLeads}</span> leads, and
            <span className="font-semibold text-slate-900"> {schoolMetrics.totalOpportunity}</span> remaining school opportunity signal.
          </p>
          <p className="text-xs text-slate-600 pt-2 border-t border-slate-200">
            Opportunity signal is a transparent school-specific indicator derived from leads, ALRL milestones, tests, access friction, and current production.
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h3 className="font-semibold text-slate-900">School Ownership / Access Validation</h3>
        {filteredCoverageRows.length === 0 ? (
          <p className="text-sm text-slate-500 mt-3">No school ownership rows found for selected filters.</p>
        ) : (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
            {filteredCoverageRows.slice(0, 10).map((c, idx) => (
              <div key={`${safeText(c.id, 'row')}-${idx}`} className="border border-slate-200 rounded p-2">
                <p className="text-sm font-medium text-slate-900">{safeText(c.school_name || c.name, 'Unknown School')}</p>
                <p className="text-xs text-slate-600 mt-1">
                  {safeText(c.school_type, 'Type unavailable')} | {safeText(c.city, '')}{c.city && c.state ? ', ' : ''}{safeText(c.state, '')} {safeText(c.zip_code, '')}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h3 className="font-semibold text-slate-900">School-Specific Execution Plans</h3>
        {opsPlansFeed.rows.length === 0 ? (
          <p className="text-sm text-slate-500 mt-3">No school execution plans returned for the current scope.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {opsPlansFeed.rows.slice(0, 8).map((p) => (
              <div key={p.plan_id} className="border border-slate-200 rounded p-2 flex items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-slate-900">{safeText(p.unit_name, 'Unit')}</p>
                  <p className="text-xs text-slate-600">{safeText(p.unit_type, 'Unit')} | Updated: {safeText(p.last_updated, 'Unavailable')}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-800 font-medium">{safeNumber(p.compliance_score)}% compliance</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const showLoading = targetsFeed.loading && !targetsFeed.lastUpdated;

  return (
    <div className="space-y-5">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div className="flex items-start gap-3">
          <School className="w-8 h-8 text-amber-600 mt-0.5" />
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">School Recruiting</h1>
            <p className="text-sm text-slate-600 mt-1">School ownership, targeted schools, access and engagement, school outcomes, ALRL milestones, and school opportunity.</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <UniversalFilter onFilterChange={setFilters} showRSID={true} showZipcode={true} showCBSA={true} />
          <button
            onClick={fetchSchoolRecruitingData}
            className="flex items-center gap-2 px-3 py-2 bg-amber-400 text-slate-950 font-semibold rounded-md hover:bg-amber-300 transition-colors text-xs uppercase tracking-[0.1em]"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-4">
        <div className="flex flex-col xl:flex-row gap-3 xl:items-center xl:justify-between">
          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span>Updated: {targetsFeed.lastUpdated || 'Pending first fetch'}</span>
            <span>{new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-600">School Type</span>
            <select
              value={schoolTypeFilter}
              onChange={(e) => setSchoolTypeFilter(e.target.value as SchoolTypeFilter)}
              className="px-2 py-1 border border-slate-300 rounded text-xs"
            >
              {schoolTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>

            <span className="text-xs text-slate-600 ml-2">Target Filter</span>
            {(['all', 'targeted', 'non-targeted'] as TargetFilter[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setTargetFilter(mode)}
                className={`px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wide ${
                  targetFilter === mode ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                }`}
              >
                {mode}
              </button>
            ))}

            <span className="text-xs text-slate-600 ml-2">View</span>
            {(['cards', 'table', 'summary'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wide ${
                  viewMode === mode ? 'bg-amber-500 text-slate-950' : 'bg-slate-100 text-slate-700'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>

      {feedIssues.length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-md p-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-amber-700 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-amber-900">Data unavailable for one or more school feeds</p>
              <ul className="text-xs text-amber-800 mt-2 list-disc list-inside">
                {feedIssues.map((issue, idx) => (
                  <li key={`${issue}-${idx}`}>{issue}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {showLoading ? (
        <div className="flex items-center justify-center h-64 bg-white border border-slate-200 rounded-md">
          <RefreshCw className="w-7 h-7 animate-spin text-amber-600" />
          <span className="ml-3 text-slate-700">Loading School Recruiting data...</span>
        </div>
      ) : viewMode === 'cards' ? (
        renderCardsView()
      ) : viewMode === 'table' ? (
        renderTableView()
      ) : (
        renderSummaryView()
      )}
    </div>
  );
};

export default TalentAcquisitionTechnicianDashboard;
