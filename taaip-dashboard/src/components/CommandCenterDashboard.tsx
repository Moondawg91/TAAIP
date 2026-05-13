import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertCircle, BrainCircuit, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config/api';
import { asNumber, asText } from './operationalData';

interface CommandCenterDashboardProps {
  onNavigate: (tab: string) => void;
}

type AnyRecord = Record<string, any>;
type ViewMode = 'cards' | 'table' | 'summary';
type SectionKey = 'mission' | 'pipeline' | 'market' | 'alerts';
type Tone = 'neutral' | 'good' | 'warn' | 'danger';

type MetricCard = {
  label: string;
  value: string;
  detail?: string;
  tone?: Tone;
};

type TableColumn = {
  key: string;
  label: string;
  align?: 'left' | 'right';
};

type TableRow = Record<string, string | number | null | undefined>;

type SectionModel = {
  title: string;
  subtitle: string;
  cards: MetricCard[];
  tableColumns: TableColumn[];
  tableRows: TableRow[];
  summaryLines: string[];
  sourceLine: string;
  missing: string[];
};

type EndpointResult = {
  data: AnyRecord | AnyRecord[] | null;
  error: string | null;
};

type CommandCenterFeeds = {
  overview: AnyRecord | null;
  commandDataset: AnyRecord | null;
  missionLeadLine: AnyRecord | AnyRecord[] | null;
  funnelMetrics: AnyRecord | null;
  marketSummary: AnyRecord | null;
  marketZips: AnyRecord | null;
  segments: AnyRecord | null;
  schools: AnyRecord | null;
  missionRisk: AnyRecord | null;
  aiRecommendations: AnyRecord | null;
  sourceErrors: string[];
};

const DEFAULT_VIEWS: Record<SectionKey, ViewMode> = {
  mission: 'cards',
  pipeline: 'cards',
  market: 'cards',
  alerts: 'cards',
};

const SECTION_ORDER: SectionKey[] = ['mission', 'pipeline', 'market', 'alerts'];

const toneClass: Record<Tone, string> = {
  neutral: 'border-slate-200 bg-white text-slate-900',
  good: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  warn: 'border-amber-200 bg-amber-50 text-amber-900',
  danger: 'border-rose-200 bg-rose-50 text-rose-900',
};

const toArray = <T,>(value: unknown): T[] => (Array.isArray(value) ? (value as T[]) : []);

const firstPresent = (...values: unknown[]) => values.find((value) => value !== null && value !== undefined);

const formatInteger = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Unavailable';
  return Math.round(value).toLocaleString();
};

const formatPercent = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Unavailable';
  return `${value.toFixed(digits)}%`;
};

const formatDateTime = (value: string | number | Date | null | undefined) => {
  if (!value) return 'Unavailable';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unavailable';
  return date.toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatDateOnly = (value: string | number | Date | null | undefined) => {
  if (!value) return 'Unavailable';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unavailable';
  return date.toLocaleDateString([], {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
};

const formatTimeOnly = (value: string | number | Date | null | undefined) => {
  if (!value) return 'Unavailable';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unavailable';
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const normalizePercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return value <= 1 ? value * 100 : value;
};

const relativeTimeFrom = (value: string | number | Date | null | undefined, nowMs: number) => {
  if (!value) return 'Unavailable';
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unavailable';
  const deltaSeconds = Math.max(0, Math.round((nowMs - date.getTime()) / 1000));
  if (deltaSeconds < 60) return `${deltaSeconds}s ago`;
  const deltaMinutes = Math.round(deltaSeconds / 60);
  if (deltaMinutes < 60) return `${deltaMinutes}m ago`;
  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) return `${deltaHours}h ago`;
  const deltaDays = Math.round(deltaHours / 24);
  return `${deltaDays}d ago`;
};

const normalizeComponentSplit = (value: unknown): Array<{ label: string; value: number | null }> => {
  if (Array.isArray(value)) {
    return value.map((item) => ({
      label: asText((item as AnyRecord)?.label || (item as AnyRecord)?.component || (item as AnyRecord)?.name, 'Unknown'),
      value: firstPresent((item as AnyRecord)?.value, (item as AnyRecord)?.count, (item as AnyRecord)?.total) as number | null,
    }));
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).map(([label, rawValue]) => ({
      label,
      value: typeof rawValue === 'number' ? rawValue : asNumber(rawValue, 0),
    }));
  }

  return [];
};

const summarizeTone = (level: string): Tone => {
  const normalized = level.toLowerCase();
  if (normalized.includes('healthy') || normalized.includes('balanced') || normalized.includes('low') || normalized.includes('on')) {
    return 'good';
  }
  if (normalized.includes('high') || normalized.includes('risk') || normalized.includes('critical') || normalized.includes('behind')) {
    return 'danger';
  }
  if (normalized.includes('monitor') || normalized.includes('watch') || normalized.includes('partial') || normalized.includes('degraded')) {
    return 'warn';
  }
  return 'neutral';
};

const renderCell = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  return String(value);
};

const ViewToggle: React.FC<{
  view: ViewMode;
  onChange: (view: ViewMode) => void;
}> = ({ view, onChange }) => (
  <div className="inline-flex rounded-md border border-slate-200 bg-slate-50 p-1">
    {(['cards', 'table', 'summary'] as ViewMode[]).map((option) => {
      const active = option === view;
      return (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`rounded px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] transition ${
            active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-white'
          }`}
        >
          {option}
        </button>
      );
    })}
  </div>
);

const SectionRenderer: React.FC<{
  section: SectionModel;
  view: ViewMode;
  onViewChange: (view: ViewMode) => void;
}> = ({ section, view, onViewChange }) => {
  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
          <p className="mt-1 text-sm text-slate-600">{section.subtitle}</p>
        </div>
        <ViewToggle view={view} onChange={onViewChange} />
      </div>

      <div className="px-5 py-5">
        {view === 'cards' && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {section.cards.map((card) => (
              <div key={card.label} className={`rounded-lg border p-4 ${toneClass[card.tone || 'neutral']}`}>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{card.label}</p>
                <p className="mt-3 text-2xl font-semibold">{card.value}</p>
                {card.detail && <p className="mt-2 text-sm text-slate-600">{card.detail}</p>}
              </div>
            ))}
          </div>
        )}

        {view === 'table' && (
          <div className="overflow-x-auto">
            {section.tableRows.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
                No table rows available from the current feed set.
              </div>
            ) : (
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.14em] text-slate-500">
                    {section.tableColumns.map((column) => (
                      <th
                        key={column.key}
                        className={`py-3 pr-4 ${column.align === 'right' ? 'text-right' : 'text-left'}`}
                      >
                        {column.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {section.tableRows.map((row, index) => (
                    <tr key={`${section.title}-${index}`} className="border-b border-slate-100 align-top">
                      {section.tableColumns.map((column) => (
                        <td
                          key={column.key}
                          className={`py-3 pr-4 text-slate-700 ${column.align === 'right' ? 'text-right' : 'text-left'}`}
                        >
                          {renderCell(row[column.key])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {view === 'summary' && (
          <div className="space-y-3">
            {section.summaryLines.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
                No summary statements available from the current feed set.
              </div>
            ) : (
              section.summaryLines.map((line) => (
                <div key={line} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {line}
                </div>
              ))
            )}
          </div>
        )}

        <div className="mt-5 flex flex-col gap-2 border-t border-slate-200 pt-4 text-xs text-slate-500">
          <p>{section.sourceLine}</p>
          {section.missing.length > 0 && <p>Feed notes: {section.missing.join(' | ')}</p>}
        </div>
      </div>
    </section>
  );
};

const CommandCenterDashboard: React.FC<CommandCenterDashboardProps> = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clockMs, setClockMs] = useState(Date.now());
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [feeds, setFeeds] = useState<CommandCenterFeeds>({
    overview: null,
    commandDataset: null,
    missionLeadLine: null,
    funnelMetrics: null,
    marketSummary: null,
    marketZips: null,
    segments: null,
    schools: null,
    missionRisk: null,
    aiRecommendations: null,
    sourceErrors: [],
  });
  const [sectionViews, setSectionViews] = useState<Record<SectionKey, ViewMode>>(DEFAULT_VIEWS);

  const fetchEndpoint = useCallback(async (path: string, timeoutMs = 8000): Promise<EndpointResult> => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
      if (!response.ok) {
        return { data: null, error: `${path} returned ${response.status}` };
      }
      const data = await response.json();
      return { data, error: null };
    } catch (requestError) {
      return {
        data: null,
        error: requestError instanceof Error ? `${path}: ${requestError.message}` : `${path}: request failed`,
      };
    } finally {
      window.clearTimeout(timer);
    }
  }, []);

  const loadOverview = useCallback(
    async (showLoading = false) => {
      if (showLoading) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      const [
        overviewResult,
        commandDatasetResult,
        missionLeadLineResult,
        funnelMetricsResult,
        marketSummaryResult,
        marketZipsResult,
        segmentsResult,
        schoolsResult,
        missionRiskResult,
        aiRecommendationsResult,
      ] = await Promise.all([
        fetchEndpoint('/api/command-center/overview?scope_type=USAREC&scope_value=USAREC'),
        fetchEndpoint('/api/powerbi/operational/command_dataset?scope_type=USAREC&scope_value=USAREC'),
        fetchEndpoint('/api/v2/mission/lead-line'),
        fetchEndpoint('/api/v2/recruiting-funnel/metrics'),
        fetchEndpoint('/ops/market/summary'),
        fetchEndpoint('/ops/market/zips?limit=10'),
        fetchEndpoint('/api/v2/analytics/segments'),
        fetchEndpoint('/api/v2/targeting/schools?limit=10'),
        fetchEndpoint('/api/v2/mission-risk/latest?limit=25'),
        fetchEndpoint('/api/v2/ai-lms/recommendations/mission/latest?limit=10'),
      ]);

      const sourceErrors = [
        overviewResult.error,
        commandDatasetResult.error,
        missionLeadLineResult.error,
        funnelMetricsResult.error,
        marketSummaryResult.error,
        marketZipsResult.error,
        segmentsResult.error,
        schoolsResult.error,
        missionRiskResult.error,
        aiRecommendationsResult.error,
      ].filter((value): value is string => Boolean(value));

      const allUnavailable = [
        overviewResult,
        commandDatasetResult,
        missionLeadLineResult,
        funnelMetricsResult,
        marketSummaryResult,
        marketZipsResult,
        segmentsResult,
        schoolsResult,
        missionRiskResult,
        aiRecommendationsResult,
      ].every((result) => result.data === null);

      if (allUnavailable) {
        setError('TAWO Command Center feeds are unavailable. Restore the backend or refresh after services are online.');
      }

      setFeeds({
        overview: (overviewResult.data as AnyRecord | null) || null,
        commandDataset: (commandDatasetResult.data as AnyRecord | null) || null,
        missionLeadLine: missionLeadLineResult.data,
        funnelMetrics: (funnelMetricsResult.data as AnyRecord | null) || null,
        marketSummary: (marketSummaryResult.data as AnyRecord | null) || null,
        marketZips: (marketZipsResult.data as AnyRecord | null) || null,
        segments: (segmentsResult.data as AnyRecord | null) || null,
        schools: (schoolsResult.data as AnyRecord | null) || null,
        missionRisk: (missionRiskResult.data as AnyRecord | null) || null,
        aiRecommendations: (aiRecommendationsResult.data as AnyRecord | null) || null,
        sourceErrors,
      });

      const authoritativeStamp =
        asText((overviewResult.data as AnyRecord | null)?.as_of_utc, '') ||
        asText((marketSummaryResult.data as AnyRecord | null)?.data_as_of, '') ||
        new Date().toISOString();
      setLastUpdated(authoritativeStamp);

      setLoading(false);
      setRefreshing(false);
    },
    [fetchEndpoint],
  );

  useEffect(() => {
    void loadOverview(true);
  }, [loadOverview]);

  useEffect(() => {
    const refreshId = window.setInterval(() => {
      void loadOverview(false);
    }, 60000);
    return () => window.clearInterval(refreshId);
  }, [loadOverview]);

  useEffect(() => {
    const clockId = window.setInterval(() => {
      setClockMs(Date.now());
    }, 30000);
    return () => window.clearInterval(clockId);
  }, []);

  const sections = useMemo<Record<SectionKey, SectionModel>>(() => {
    const summary = feeds.overview?.summary || {};
    const leadLine = summary?.lead_line || {};
    const phase2 = summary?.phase2 || {};
    const diagnostics = feeds.commandDataset?.data?.diagnostics?.data || {};
    const execution = feeds.commandDataset?.data?.execution?.data || {};

    const missionRows = Array.isArray(feeds.missionLeadLine)
      ? feeds.missionLeadLine
      : toArray<AnyRecord>((feeds.missionLeadLine as AnyRecord | null)?.results);

    const hasMissionFeed = missionRows.length > 0;
    const annualMission = missionRows.reduce((sum, row) => sum + asNumber(row?.annual_mission, 0), 0);
    const actualYtd = missionRows.reduce((sum, row) => sum + asNumber(row?.actual_ytd, 0), 0);
    const expectedYtd = missionRows.reduce((sum, row) => sum + asNumber(row?.expected_ytd, 0), 0);
    const remainingMission = annualMission > 0 ? Math.max(annualMission - actualYtd, 0) : null;
    const timeGap = missionRows.length > 0 ? actualYtd - expectedYtd : null;
    const missionStatusCounts = missionRows.reduce<Record<string, number>>((counts, row) => {
      const status = asText(row?.status, 'unknown').toLowerCase();
      counts[status] = (counts[status] || 0) + 1;
      return counts;
    }, {});
    const behindUnits = toArray<AnyRecord>(leadLine?.top_behind).map((item) => asText(item?.unit_rsid || item?.unit || item?.name, 'Unknown'));
    const posture = asText(leadLine?.status || summary?.status, missionRows.length ? 'mixed' : 'unavailable');
    const componentSplit = normalizeComponentSplit(
      firstPresent(
        leadLine?.component_split,
        phase2?.funnel_engine?.summary?.component_split,
        diagnostics?.funnel_engine_summary?.component_split,
        diagnostics?.market_engine_summary?.component_split,
      ),
    ).filter((item) => /(ra|ar|regular|reserve)/i.test(item.label));
    const componentSplitLabel = componentSplit.length
      ? componentSplit
          .map((item) => `${item.label.toUpperCase()}: ${item.value === null ? 'Unavailable' : formatInteger(item.value)}`)
          .join(' | ')
      : 'Unavailable from current mission feed';

    const hasFunnelFeed = Boolean(feeds.funnelMetrics);
    const funnelCounts = feeds.funnelMetrics?.funnel_counts || {};
    const conversionRates = feeds.funnelMetrics?.conversion_rates || {};
    const flashToBang = feeds.funnelMetrics?.flash_to_bang || {};
    const appointmentMetrics = feeds.funnelMetrics?.appointment_metrics || {};
    const lossAnalysis = feeds.funnelMetrics?.loss_analysis || {};
    const hasExecutionFeed = Boolean(execution) && Object.keys(execution).length > 0;
    const processingSummary = execution?.processing_summary || {};
    const processingOverdue = toArray<AnyRecord>(execution?.processing_overdue_items).length;
    const processingStalled = toArray<AnyRecord>(execution?.processing_stalled_items).length;
    const offTrackItems = toArray<AnyRecord>(execution?.off_track_items).length;

    const hasMarketSummaryFeed = Boolean(feeds.marketSummary);
    const marketKpis = feeds.marketSummary?.kpis || {};
    const marketRows = toArray<AnyRecord>(feeds.marketZips?.rows);
    const segmentRows = toArray<AnyRecord>(feeds.segments?.segments);
    const schoolRows = toArray<AnyRecord>(feeds.schools?.schools);
    const marketCategories = toArray<AnyRecord>(feeds.marketSummary?.by_zip_category);
    const totalPotentialRemaining = firstPresent(marketKpis?.total_potential_remaining, diagnostics?.market_qma_summary?.potential_remaining);
    const marketStrength = normalizePercent(firstPresent(marketKpis?.army_share_of_potential, diagnostics?.market_qma_summary?.army_share_of_potential) as number | null | undefined);
    const topZipLine = marketRows.slice(0, 3).map((row) => `${asText(row?.zip, 'Unknown')} (${formatInteger(asNumber(row?.potential_remaining, 0))})`);
    const highPrioritySchools = schoolRows.filter((row) => asText(row?.category, '').toLowerCase() === 'high priority');

    const hasMissionRiskFeed = Boolean(feeds.missionRisk);
    const missionRiskRows = toArray<AnyRecord>(feeds.missionRisk?.results);
    const highMissionRisk = missionRiskRows.filter((row) => asText(row?.risk_level, '').toLowerCase() === 'high');
    const monitorMissionRisk = missionRiskRows.filter((row) => asText(row?.risk_level, '').toLowerCase() === 'monitor');

    const hasAiFeed = Boolean(feeds.aiRecommendations);
    const aiRows = toArray<AnyRecord>(feeds.aiRecommendations?.recommendations);
    const doctrineReferenceCount = aiRows.reduce((count, row) => {
      const doctrineRefs = row?.doctrine_refs || row?.doctrine_refs_json || row?.doctrine_references;
      if (Array.isArray(doctrineRefs) && doctrineRefs.length > 0) return count + 1;
      if (typeof doctrineRefs === 'string' && doctrineRefs.trim().length > 0) return count + 1;
      return count;
    }, 0);

    const alertRows: TableRow[] = [];

    feeds.sourceErrors.forEach((issue) => {
      alertRows.push({
        category: 'Feed Degradation',
        severity: 'monitor',
        alert: issue,
        evidence: 'Refresh after backend feeds are restored.',
      });
    });

    toArray<string>(feeds.overview?.missing_data).forEach((issue) => {
      alertRows.push({
        category: 'Command Feed',
        severity: 'monitor',
        alert: issue,
        evidence: 'Reported by /api/command-center/overview missing_data.',
      });
    });

    toArray<string>(feeds.commandDataset?.partial_blocks || feeds.commandDataset?.data?._meta?.partial_blocks).forEach((issue) => {
      alertRows.push({
        category: 'Operational Dataset',
        severity: 'monitor',
        alert: `${issue} partial`,
        evidence: 'Reported by /api/powerbi/operational/command_dataset partial block metadata.',
      });
    });

    highMissionRisk.slice(0, 5).forEach((row) => {
      alertRows.push({
        category: 'Mission Feasibility',
        severity: asText(row?.risk_level, 'high'),
        alert: `${asText(row?.company_id || row?.unit_rsid || row?.station_id, 'Unit')} risk ${formatPercent(normalizePercent(asNumber(row?.mission_risk_score, 0)), 1)}`,
        evidence: `Confidence ${formatPercent(normalizePercent(asNumber(row?.confidence_score, 0)), 1)}.`,
      });
    });

    if (asNumber(appointmentMetrics?.no_show_rate, 0) > 0) {
      alertRows.push({
        category: 'Pipeline',
        severity: asNumber(appointmentMetrics?.no_show_rate, 0) >= 20 ? 'high' : 'monitor',
        alert: `No-show rate ${formatPercent(asNumber(appointmentMetrics?.no_show_rate, 0), 1)}`,
        evidence: 'Derived from /api/v2/recruiting-funnel/metrics appointment_metrics.',
      });
    }

    if (processingOverdue > 0 || processingStalled > 0 || offTrackItems > 0) {
      alertRows.push({
        category: 'Execution',
        severity: processingOverdue > 0 ? 'high' : 'monitor',
        alert: `${formatInteger(processingOverdue)} overdue | ${formatInteger(processingStalled)} stalled | ${formatInteger(offTrackItems)} off-track`,
        evidence: 'Derived from execution and flash-to-bang processing engines.',
      });
    }

    if (highPrioritySchools.length > 0) {
      const lowConfidenceSchools = highPrioritySchools.filter((row) => asNumber(row?.confidence_score, 0) < 0.5).length;
      if (lowConfidenceSchools > 0) {
        alertRows.push({
          category: 'Market',
          severity: 'monitor',
          alert: `${lowConfidenceSchools} high-priority schools below confidence threshold`,
          evidence: 'Derived from /api/v2/targeting/schools priority and confidence scores.',
        });
      }
    }

    aiRows.slice(0, 5).forEach((row) => {
      alertRows.push({
        category: 'AI Support',
        severity: asText(row?.risk_level || row?.priority || 'monitor', 'monitor'),
        alert: asText(row?.title || row?.recommendation || row?.summary || row?.recommendation_text, 'AI recommendation available'),
        evidence: asText(row?.explanation || row?.why || row?.notes, 'Doctrine and evidence available in AI recommendation feed.'),
      });
    });

    const missionSection: SectionModel = {
      title: 'Mission',
      subtitle: 'Mission pacing, YTD requirement alignment, posture, and mission-feasibility signals.',
      cards: [
        {
          label: 'Mission vs Actual',
          value: hasMissionFeed && annualMission > 0 ? `${formatInteger(actualYtd)} / ${formatInteger(annualMission)}` : 'Unavailable',
          detail: hasMissionFeed && annualMission > 0 ? 'Actual YTD against annual mission.' : 'Mission totals are not available from /api/v2/mission/lead-line.',
          tone: hasMissionFeed && annualMission > 0 && actualYtd >= annualMission ? 'good' : 'neutral',
        },
        {
          label: 'Current Requirement',
          value: remainingMission === null ? 'Unavailable' : formatInteger(remainingMission),
          detail: remainingMission === null ? 'Mission requirement could not be computed.' : 'Remaining contracts to close annual mission.',
          tone: remainingMission === null ? 'warn' : remainingMission > 0 ? 'warn' : 'good',
        },
        {
          label: 'Trend Comparison',
          value: posture.toUpperCase(),
          detail: hasMissionFeed
            ? `${formatInteger(missionStatusCounts.on)} on pace | ${formatInteger(missionStatusCounts.behind)} behind.`
            : 'Mission posture unavailable from current lead-line feed.',
          tone: summarizeTone(posture),
        },
        {
          label: 'RA / AR Split',
          value: componentSplitLabel,
          detail: 'Shown when mission feeds expose Regular Army and Army Reserve breakout.',
          tone: componentSplit.length > 0 ? 'neutral' : 'warn',
        },
        {
          label: 'Time Comparison',
          value: timeGap === null ? 'Unavailable' : `${timeGap >= 0 ? '+' : ''}${formatInteger(timeGap)}`,
          detail: expectedYtd > 0
            ? `${formatInteger(actualYtd)} actual vs ${formatInteger(expectedYtd)} expected YTD.`
            : 'Expected pacing data unavailable.',
          tone: timeGap === null ? 'warn' : timeGap >= 0 ? 'good' : 'danger',
        },
        {
          label: 'Behind Units',
          value: behindUnits.length ? behindUnits.slice(0, 3).join(', ') : 'None reported',
          detail: behindUnits.length ? 'Lead-line top-behind units from command-center overview.' : 'No behind units reported in current summary.',
          tone: behindUnits.length ? 'danger' : 'good',
        },
      ],
      tableColumns: [
        { key: 'metric', label: 'Metric' },
        { key: 'current', label: 'Current' },
        { key: 'assessment', label: 'Assessment' },
        { key: 'note', label: 'Note' },
      ],
      tableRows: [
        {
          metric: 'Mission vs Actual',
          current: annualMission > 0 ? `${formatInteger(actualYtd)} / ${formatInteger(annualMission)}` : 'Unavailable',
          assessment: posture.toUpperCase(),
          note: 'Derived from /api/v2/mission/lead-line actual_ytd and annual_mission.',
        },
        {
          metric: 'Current Requirement',
          current: remainingMission === null ? 'Unavailable' : formatInteger(remainingMission),
          assessment: remainingMission !== null && remainingMission > 0 ? 'Open' : 'Met',
          note: 'Annual mission minus actual YTD.',
        },
        {
          metric: 'Trend Comparison',
          current: missionRows.length ? `${formatInteger(missionStatusCounts.on)} on | ${formatInteger(missionStatusCounts.behind)} behind` : 'Unavailable',
          assessment: posture,
          note: 'Unit pacing from mission lead-line status.',
        },
        {
          metric: 'RA / AR Split',
          current: componentSplitLabel,
          assessment: componentSplit.length > 0 ? 'Available' : 'Unavailable',
          note: 'Only displayed when live mission feeds expose component breakout.',
        },
        {
          metric: 'Time Comparison',
          current: expectedYtd > 0 ? `${formatInteger(actualYtd)} actual | ${formatInteger(expectedYtd)} expected` : 'Unavailable',
          assessment: timeGap === null ? 'Unavailable' : timeGap >= 0 ? 'Ahead / On pace' : 'Behind pace',
          note: 'YTD pacing delta from expected_ytd.',
        },
      ],
      summaryLines: [
        annualMission > 0
          ? `Actual YTD is ${formatInteger(actualYtd)} against an annual mission of ${formatInteger(annualMission)}.`
          : 'Mission totals are currently unavailable from the lead-line feed.',
        expectedYtd > 0
          ? `Time comparison shows ${formatInteger(actualYtd)} actual against ${formatInteger(expectedYtd)} expected YTD.`
          : 'Expected pacing data is not currently available.',
        componentSplit.length > 0
          ? `RA / AR split is available: ${componentSplitLabel}.`
          : 'RA / AR split is not exposed by the current mission feed and remains unavailable rather than inferred.',
        behindUnits.length > 0
          ? `Mission-feasibility watch list includes ${behindUnits.slice(0, 3).join(', ')}.`
          : 'No units are reported in the top-behind mission list.',
      ],
      sourceLine: 'Sources: /api/v2/mission/lead-line, /api/command-center/overview',
      missing: [
        ...(missionRows.length === 0 ? ['mission lead-line rows unavailable'] : []),
        ...(componentSplit.length === 0 ? ['RA / AR split unavailable from current feeds'] : []),
      ],
    };

    const pipelineSection: SectionModel = {
      title: 'Pipeline',
      subtitle: 'Leads through ships with flash-to-bang, losses, and conversion performance retained from live funnel engines.',
      cards: [
        {
          label: 'Leads',
          value: hasFunnelFeed ? formatInteger(asNumber(firstPresent(funnelCounts?.leads, funnelCounts?.total_leads), 0)) : 'Unavailable',
          detail: 'Current lead volume from recruiting-funnel metrics.',
          tone: 'neutral',
        },
        {
          label: 'Appointments',
          value: hasFunnelFeed ? formatInteger(asNumber(funnelCounts?.appointments_made, 0)) : 'Unavailable',
          detail: 'Appointments made.',
          tone: 'neutral',
        },
        {
          label: 'Interviews',
          value: hasFunnelFeed ? formatInteger(asNumber(funnelCounts?.appointments_conducted, 0)) : 'Unavailable',
          detail: 'Appointments conducted mapped to interview completion.',
          tone: 'neutral',
        },
        {
          label: 'Testing / Processing',
          value: hasFunnelFeed || hasExecutionFeed
            ? `${hasFunnelFeed ? formatInteger(asNumber(funnelCounts?.tests, 0)) : 'Unavailable'} / ${hasExecutionFeed ? formatInteger(asNumber(processingSummary?.in_processing || processingSummary?.processing_count, 0)) : 'Unavailable'}`
            : 'Unavailable',
          detail: hasExecutionFeed
            ? `Testing volume with processing queue posture ${asText(processingSummary?.processing_posture || processingSummary?.status, 'unavailable')}.`
            : 'Execution processing posture unavailable.',
          tone: processingOverdue > 0 || processingStalled > 0 ? 'warn' : 'neutral',
        },
        {
          label: 'Contracts',
          value: hasFunnelFeed ? formatInteger(asNumber(funnelCounts?.enlistments, 0)) : 'Unavailable',
          detail: 'Contracts from recruiting-funnel metrics.',
          tone: 'neutral',
        },
        {
          label: 'Ships',
          value: hasFunnelFeed ? formatInteger(asNumber(funnelCounts?.ships, 0)) : 'Unavailable',
          detail: 'Shipments from recruiting-funnel metrics.',
          tone: 'neutral',
        },
        {
          label: 'Loss Points',
          value: hasFunnelFeed ? formatInteger(asNumber(lossAnalysis?.total_losses, 0)) : 'Unavailable',
          detail: hasFunnelFeed ? `Loss rate ${formatPercent(asNumber(lossAnalysis?.loss_rate, 0), 1)} | top reason ${asText(lossAnalysis?.top_loss_reason, 'Unavailable')}.` : 'Loss analysis unavailable.',
          tone: !hasFunnelFeed ? 'warn' : asNumber(lossAnalysis?.total_losses, 0) > 0 ? 'danger' : 'good',
        },
        {
          label: 'Flash-to-Bang',
          value: hasFunnelFeed ? `${formatInteger(asNumber(flashToBang?.avg_lead_to_enlistment_days, 0))} days` : 'Unavailable',
          detail: 'Average lead-to-enlistment duration.',
          tone: asNumber(flashToBang?.avg_lead_to_enlistment_days, 0) > 90 ? 'warn' : 'neutral',
        },
        {
          label: 'Conversion Performance',
          value: hasFunnelFeed ? formatPercent(asNumber(conversionRates?.overall_conversion, 0), 1) : 'Unavailable',
          detail: hasFunnelFeed ? `No-show rate ${formatPercent(asNumber(appointmentMetrics?.no_show_rate, 0), 1)}.` : 'Conversion performance unavailable.',
          tone: !hasFunnelFeed ? 'warn' : asNumber(conversionRates?.overall_conversion, 0) >= 10 ? 'good' : 'warn',
        },
      ],
      tableColumns: [
        { key: 'metric', label: 'Metric' },
        { key: 'value', label: 'Value', align: 'right' },
        { key: 'assessment', label: 'Assessment' },
        { key: 'note', label: 'Note' },
      ],
      tableRows: [
        { metric: 'Leads', value: formatInteger(asNumber(firstPresent(funnelCounts?.leads, funnelCounts?.total_leads), 0)), assessment: 'Volume', note: 'funnel_counts.leads' },
        { metric: 'Appointments', value: formatInteger(asNumber(funnelCounts?.appointments_made, 0)), assessment: 'Appointments made', note: 'funnel_counts.appointments_made' },
        { metric: 'Interviews', value: formatInteger(asNumber(funnelCounts?.appointments_conducted, 0)), assessment: 'Appointments conducted', note: 'Mapped to interview completion' },
        { metric: 'Testing', value: formatInteger(asNumber(funnelCounts?.tests, 0)), assessment: 'Testing volume', note: 'funnel_counts.tests' },
        { metric: 'Processing', value: formatInteger(asNumber(processingSummary?.in_processing || processingSummary?.processing_count, 0)), assessment: asText(processingSummary?.processing_posture || processingSummary?.status, 'Unavailable'), note: 'Execution processing summary' },
        { metric: 'Contracts', value: formatInteger(asNumber(funnelCounts?.enlistments, 0)), assessment: 'Contracts', note: 'funnel_counts.enlistments' },
        { metric: 'Ships', value: formatInteger(asNumber(funnelCounts?.ships, 0)), assessment: 'Ships', note: 'funnel_counts.ships' },
        { metric: 'Loss Points', value: formatInteger(asNumber(lossAnalysis?.total_losses, 0)), assessment: formatPercent(asNumber(lossAnalysis?.loss_rate, 0), 1), note: asText(lossAnalysis?.top_loss_reason, 'Unavailable') },
        { metric: 'Flash-to-Bang', value: `${formatInteger(asNumber(flashToBang?.avg_lead_to_enlistment_days, 0))} days`, assessment: 'Lead to enlistment', note: 'flash_to_bang.avg_lead_to_enlistment_days' },
        { metric: 'Conversion Performance', value: formatPercent(asNumber(conversionRates?.overall_conversion, 0), 1), assessment: formatPercent(asNumber(appointmentMetrics?.no_show_rate, 0), 1), note: 'overall conversion with no-show rate' },
      ],
      summaryLines: [
        `Pipeline currently shows ${formatInteger(asNumber(firstPresent(funnelCounts?.leads, funnelCounts?.total_leads), 0))} leads, ${formatInteger(asNumber(funnelCounts?.appointments_made, 0))} appointments, and ${formatInteger(asNumber(funnelCounts?.enlistments, 0))} contracts.`,
        `Flash-to-bang averages ${formatInteger(asNumber(flashToBang?.avg_lead_to_enlistment_days, 0))} days from lead to enlistment.`,
        `Loss analysis reports ${formatInteger(asNumber(lossAnalysis?.total_losses, 0))} losses with ${asText(lossAnalysis?.top_loss_reason, 'no reason available')} as the top loss point.`,
        `Execution risk shows ${formatInteger(processingOverdue)} overdue items, ${formatInteger(processingStalled)} stalled items, and ${formatInteger(offTrackItems)} off-track items.`,
      ],
      sourceLine: 'Sources: /api/v2/recruiting-funnel/metrics, /api/powerbi/operational/command_dataset',
      missing: [
        ...(feeds.funnelMetrics ? [] : ['recruiting funnel metrics unavailable']),
        ...(!execution || Object.keys(execution).length === 0 ? ['execution processing feed unavailable'] : []),
      ],
    };

    const marketSection: SectionModel = {
      title: 'Market',
      subtitle: 'Top ZIPs, priority markets, market categories, segment strength, and remaining potential from live market and targeting feeds.',
      cards: [
        {
          label: 'Top ZIPs',
          value: topZipLine.length ? topZipLine.join(', ') : 'Unavailable',
          detail: 'Top ZIPs by potential remaining.',
          tone: topZipLine.length ? 'neutral' : 'warn',
        },
        {
          label: 'Priority Markets',
          value: schoolRows.length ? `${formatInteger(highPrioritySchools.length)} high-priority schools` : 'Unavailable',
          detail: highPrioritySchools.length
            ? highPrioritySchools.slice(0, 3).map((row) => asText(row?.school_name, 'Unknown')).join(', ')
            : 'No high-priority schools returned by targeting feed.',
          tone: highPrioritySchools.length ? 'neutral' : 'warn',
        },
        {
          label: 'Market Categories',
          value: marketCategories.length
            ? marketCategories
                .slice(0, 3)
                .map((row) => `${asText(row?.zip_category, 'Unknown')} (${formatInteger(asNumber(row?.potential_remaining, 0))})`)
                .join(', ')
            : 'Unavailable',
          detail: 'Category rollup from ops market summary.',
          tone: marketCategories.length ? 'neutral' : 'warn',
        },
        {
          label: 'Segments',
          value: segmentRows.length
            ? segmentRows.slice(0, 3).map((row) => asText(row?.segment_name, 'Unknown')).join(', ')
            : 'Unavailable',
          detail: 'Highest remaining-potential market segments.',
          tone: segmentRows.length ? 'neutral' : 'warn',
        },
        {
          label: 'Market Value / Strength',
          value: hasMarketSummaryFeed ? `${formatInteger(asNumber(marketKpis?.total_army_potential, 0))} | ${marketStrength === null ? 'Unavailable' : formatPercent(marketStrength, 1)}` : 'Unavailable',
          detail: 'Army potential with Army share of potential when exposed by the market feed.',
          tone: marketStrength !== null && marketStrength >= 50 ? 'good' : 'neutral',
        },
        {
          label: 'Potential Remaining',
          value: hasMarketSummaryFeed ? formatInteger(asNumber(totalPotentialRemaining, 0)) : 'Unavailable',
          detail: 'Total remaining potential from live ops market summary.',
          tone: asNumber(totalPotentialRemaining, 0) > 0 ? 'warn' : 'neutral',
        },
      ],
      tableColumns: [
        { key: 'zip', label: 'ZIP' },
        { key: 'category', label: 'Category' },
        { key: 'remaining', label: 'Potential Remaining', align: 'right' },
        { key: 'strength', label: 'Market Strength', align: 'right' },
        { key: 'segment', label: 'Segment / CBSA' },
      ],
      tableRows: marketRows.slice(0, 10).map((row, index) => ({
        zip: asText(row?.zip, `ZIP ${index + 1}`),
        category: asText(row?.zip_category, 'Unknown'),
        remaining: formatInteger(asNumber(row?.potential_remaining, 0)),
        strength: row?.army_share_of_potential !== null && row?.army_share_of_potential !== undefined
          ? formatPercent(normalizePercent(asNumber(row?.army_share_of_potential, 0)), 1)
          : asText(row?.p2p_band, 'Unavailable'),
        segment: asText(row?.cbsa_code || row?.dma_name, 'Unavailable'),
      })),
      summaryLines: [
        topZipLine.length
          ? `Top ZIPs by potential remaining are ${topZipLine.join(', ')}.`
          : 'Top ZIPs are unavailable because ops market ZIP rows were not returned.',
        marketCategories.length
          ? `Priority market categories are led by ${marketCategories
              .slice(0, 3)
              .map((row) => asText(row?.zip_category, 'Unknown'))
              .join(', ')}.`
          : 'Market category rollup is unavailable.',
        segmentRows.length
          ? `Leading market segments are ${segmentRows.slice(0, 3).map((row) => asText(row?.segment_name, 'Unknown')).join(', ')}.`
          : 'Market segments are unavailable from analytics feed.',
        `Remaining market potential is ${formatInteger(asNumber(totalPotentialRemaining, 0))} with ${highPrioritySchools.length ? formatInteger(highPrioritySchools.length) : 'no'} high-priority schools surfaced by targeting.`,
      ],
      sourceLine: 'Sources: /ops/market/summary, /ops/market/zips, /api/v2/analytics/segments, /api/v2/targeting/schools',
      missing: [
        ...(marketRows.length === 0 ? ['ops market ZIP rows unavailable'] : []),
        ...(segmentRows.length === 0 ? ['analytics segments unavailable'] : []),
        ...(schoolRows.length === 0 ? ['targeting schools unavailable'] : []),
      ],
    };

    const alertsSection: SectionModel = {
      title: 'Alerts / Problems',
      subtitle: 'Mission-feasibility issues, pipeline blockers, market risk, degraded feeds, AI support, and doctrine-linked decision support.',
      cards: [
        {
          label: 'Mission-Feasibility Issues',
          value: hasMissionRiskFeed ? `${formatInteger(highMissionRisk.length)} high | ${formatInteger(monitorMissionRisk.length)} monitor` : 'Unavailable',
          detail: 'From latest mission-risk scores.',
          tone: highMissionRisk.length > 0 ? 'danger' : monitorMissionRisk.length > 0 ? 'warn' : 'good',
        },
        {
          label: 'Funnel Risks',
          value: `${formatInteger(processingOverdue)} overdue | ${formatInteger(asNumber(lossAnalysis?.total_losses, 0))} losses`,
          detail: 'Processing and loss pressure from live funnel and execution feeds.',
          tone: processingOverdue > 0 || asNumber(lossAnalysis?.total_losses, 0) > 0 ? 'danger' : 'good',
        },
        {
          label: 'Market Risks',
          value: schoolRows.length ? `${formatInteger(highPrioritySchools.filter((row) => asNumber(row?.confidence_score, 0) < 0.5).length)} low-confidence high-priority schools` : 'Unavailable',
          detail: 'Targeting-school confidence pressure in priority markets.',
          tone: highPrioritySchools.some((row) => asNumber(row?.confidence_score, 0) < 0.5) ? 'warn' : 'good',
        },
        {
          label: 'Degraded Areas',
          value: formatInteger(feeds.sourceErrors.length + toArray<string>(feeds.overview?.missing_data).length + toArray<string>(feeds.commandDataset?.partial_blocks || feeds.commandDataset?.data?._meta?.partial_blocks).length),
          detail: 'Feed degradation and partial data conditions.',
          tone: feeds.sourceErrors.length > 0 ? 'danger' : 'warn',
        },
        {
          label: 'AI-Driven Support',
          value: hasAiFeed ? formatInteger(aiRows.length) : 'Unavailable',
          detail: 'Latest mission AI recommendations available for review.',
          tone: aiRows.length > 0 ? 'neutral' : 'warn',
        },
        {
          label: 'Doctrine-Driven Interpretation',
          value: doctrineReferenceCount > 0 ? `${formatInteger(doctrineReferenceCount)} linked recommendations` : 'Unavailable',
          detail: 'Doctrine references are shown only when present in the AI recommendation feed.',
          tone: doctrineReferenceCount > 0 ? 'good' : 'warn',
        },
      ],
      tableColumns: [
        { key: 'category', label: 'Category' },
        { key: 'severity', label: 'Severity' },
        { key: 'alert', label: 'Alert / Problem' },
        { key: 'evidence', label: 'Evidence / Action' },
      ],
      tableRows: alertRows.slice(0, 16),
      summaryLines: [
        highMissionRisk.length > 0
          ? `${formatInteger(highMissionRisk.length)} mission-feasibility items are currently high risk.`
          : 'No high mission-feasibility items are currently reported.',
        processingOverdue > 0 || processingStalled > 0 || offTrackItems > 0
          ? `Execution pressure includes ${formatInteger(processingOverdue)} overdue, ${formatInteger(processingStalled)} stalled, and ${formatInteger(offTrackItems)} off-track items.`
          : 'Execution feeds do not currently report overdue, stalled, or off-track items.',
        feeds.sourceErrors.length > 0
          ? `Feed degradation is present across ${formatInteger(feeds.sourceErrors.length)} sources and is surfaced here instead of hidden.`
          : 'No endpoint-level feed degradation is currently reported.',
        aiRows.length > 0
          ? `AI-driven support remains connected with ${formatInteger(aiRows.length)} recommendations${doctrineReferenceCount > 0 ? ` and ${formatInteger(doctrineReferenceCount)} doctrine-linked interpretations` : ''}.`
          : 'AI-driven support is currently unavailable from the mission recommendation feed.',
      ],
      sourceLine: 'Sources: /api/v2/mission-risk/latest, /api/v2/ai-lms/recommendations/mission/latest, /api/v2/recruiting-funnel/metrics, /api/powerbi/operational/command_dataset, /api/command-center/overview',
      missing: [
        ...(missionRiskRows.length === 0 ? ['mission risk feed unavailable or empty'] : []),
        ...(aiRows.length === 0 ? ['mission AI recommendation feed unavailable or empty'] : []),
        ...(alertRows.length === 0 ? ['no live alert rows produced from current feeds'] : []),
      ],
    };

    return {
      mission: missionSection,
      pipeline: pipelineSection,
      market: marketSection,
      alerts: alertsSection,
    };
  }, [feeds]);

  const lastUpdatedLabel = lastUpdated ? formatDateTime(lastUpdated) : 'Unavailable';
  const lastUpdatedDate = lastUpdated ? formatDateOnly(lastUpdated) : 'Unavailable';
  const lastUpdatedTime = lastUpdated ? formatTimeOnly(lastUpdated) : 'Unavailable';
  const lastUpdatedRelative = relativeTimeFrom(lastUpdated, clockMs);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-900 bg-slate-900 px-6 py-5 text-white shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-300">TAWO</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">TAWO Command Center</h1>
            <p className="mt-2 max-w-4xl text-sm text-slate-300">
              Mission, Pipeline, Market, and Alerts / Problems restored as the battalion decision-support surface. Live feeds remain connected to mission feasibility, market intelligence, performance, AI support, and doctrine-linked recommendations.
            </p>
          </div>

          <div className="grid gap-2 rounded-lg border border-slate-700 bg-slate-800/70 p-4 text-sm text-slate-200 sm:grid-cols-2">
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Date Stamp</p>
              <p className="mt-1 font-medium">{lastUpdatedDate}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Time Stamp</p>
              <p className="mt-1 font-medium">{lastUpdatedTime}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Last Updated</p>
              <p className="mt-1 font-medium">{lastUpdatedRelative}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-400">Automation</p>
              <p className="mt-1 font-medium">Auto-refresh every 60s</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Update Control</p>
          <p className="mt-1 text-sm text-slate-600">Authoritative feed stamp: {lastUpdatedLabel}</p>
        </div>
        <button
          type="button"
          onClick={() => void loadOverview(false)}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing' : 'Refresh Now'}
        </button>
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-200 bg-white px-5 py-8 text-sm text-slate-600">
          Loading TAWO Command Center feeds.
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 text-rose-900">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">TAWO Command Center unavailable</p>
              <p className="mt-1 text-sm text-rose-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && feeds.sourceErrors.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-amber-900">
          <div className="flex items-start gap-3">
            <BrainCircuit className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Partial feed degradation detected</p>
              <p className="mt-1 text-sm text-amber-800">
                Some sections are running with live partial data. Missing feeds are surfaced in Alerts / Problems and within each section rather than replaced with fabricated values.
              </p>
            </div>
          </div>
        </div>
      )}

      {!loading && (
        <div className="space-y-6">
          {SECTION_ORDER.map((sectionKey) => (
            <SectionRenderer
              key={sectionKey}
              section={sections[sectionKey]}
              view={sectionViews[sectionKey]}
              onViewChange={(view) => {
                setSectionViews((current) => ({ ...current, [sectionKey]: view }));
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export { CommandCenterDashboard };
export default CommandCenterDashboard;
