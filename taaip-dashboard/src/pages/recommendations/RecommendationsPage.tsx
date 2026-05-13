import React, { useCallback, useEffect, useState } from 'react';
import { RecommendationCards } from '../../components/recommendations/RecommendationCards';
import { AsyncState } from '../../components/shared/AsyncState';
import { getRecommendations } from '../../lib/intelligenceApi';
import { usePeriodStore } from '../../state/periodStore';
import { useRsidStore } from '../../state/rsidStore';

export const RecommendationsPage: React.FC = () => {
  const { rsid } = useRsidStore();
  const { periodType, periodValue } = usePeriodStore();
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await getRecommendations({ scope_type: 'STATION', status: 'draft', limit: 50 });
      setRows((payload as Array<Record<string, unknown>>).filter((row) => {
        const scopeValue = String(row.scope_value ?? '');
        return scopeValue.includes(rsid) || scopeValue.length === 0;
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
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
        Recommendation cards include priority and confidence signals with deterministic ordering for the active RSID and period context.
      </div>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void load()}>
        <RecommendationCards rows={rows} />
      </AsyncState>
    </section>
  );
};
