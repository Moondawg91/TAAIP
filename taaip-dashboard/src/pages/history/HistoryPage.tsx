import React, { useCallback, useEffect, useState } from 'react';
import { HistoryTimeline } from '../../components/history/HistoryTimeline';
import { AsyncState } from '../../components/shared/AsyncState';
import { getArchiveEvents } from '../../lib/intelligenceApi';
import { usePeriodStore } from '../../state/periodStore';
import { useRsidStore } from '../../state/rsidStore';

export const HistoryPage: React.FC = () => {
  const { rsid } = useRsidStore();
  const { periodType, periodValue } = usePeriodStore();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await getArchiveEvents({ station_rsid: rsid, limit: 100 });
      setRows((payload.events ?? []) as Array<Record<string, unknown>>);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load archive history');
      setRows([]);
    } finally {
      setIsLoading(false);
    }
  }, [rsid]);

  useEffect(() => {
    void load();
  }, [load, rsid, periodType, periodValue]);

  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3 text-xs text-[#94A3B8]">
        Append-only archive timeline for selected RSID and period context.
      </div>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void load()}>
        <HistoryTimeline rows={rows} />
      </AsyncState>
    </section>
  );
};
