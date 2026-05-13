import React, { useCallback, useEffect, useState } from 'react';
import { AnalyticsPanel } from '../../components/analytics/AnalyticsPanel';
import { AsyncState } from '../../components/shared/AsyncState';
import { getArchiveEvents, getAnalyticsVersions } from '../../lib/intelligenceApi';
import { usePeriodStore } from '../../state/periodStore';
import { useRsidStore } from '../../state/rsidStore';

export const AnalyticsPage: React.FC = () => {
  const { rsid } = useRsidStore();
  const { periodType, periodValue } = usePeriodStore();
  const [snapshotId, setSnapshotId] = useState<string>('');
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      let id = snapshotId;
      if (!id) {
        const events = await getArchiveEvents({ entity_type: 'analytics_snapshot', station_rsid: rsid, limit: 1 });
        const first = (events.events[0] ?? {}) as { entity_id?: string };
        id = first.entity_id ?? '';
      }
      if (!id) {
        setRows([]);
        return;
      }
      const payload = await getAnalyticsVersions(id);
      const list = (payload.versions ?? []) as Array<Record<string, unknown>>;
      setRows(list);
      setSnapshotId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
      setRows([]);
    } finally {
      setIsLoading(false);
    }
  }, [snapshotId, rsid]);

  useEffect(() => {
    void load();
  }, [load, rsid, periodType, periodValue]);

  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
        <p className="text-xs text-[#94A3B8]">Contract ROI, Funnel transitions, Market influence, Recruiter effectiveness, Vacancy alignment, School performance, Lead line, and Production pacing are rendered from analytics snapshots for the selected RSID and period context.</p>
      </div>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void load()}>
        <AnalyticsPanel rows={rows} />
      </AsyncState>
    </section>
  );
};
