import React, { useCallback, useMemo, useState } from 'react';
import { VersionList } from '../../components/versions/VersionList';
import { AsyncState } from '../../components/shared/AsyncState';
import { getAnalyticsVersions, getRecommendationVersions, getFragoVersions, getVersionDetail } from '../../lib/intelligenceApi';

type EntityType = 'analytics_snapshot' | 'recommendation_record' | 'frago_order';

export const VersionsPage: React.FC = () => {
  const [entityType, setEntityType] = useState<EntityType>('analytics_snapshot');
  const [entityId, setEntityId] = useState('');
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVersions = useMemo(() => {
    if (entityType === 'analytics_snapshot') {
      return getAnalyticsVersions;
    }
    if (entityType === 'recommendation_record') {
      return getRecommendationVersions;
    }
    return getFragoVersions;
  }, [entityType]);

  const loadList = useCallback(async () => {
    if (!entityId) {
      setRows([]);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const payload = await fetchVersions(entityId);
      setRows((payload.versions ?? []) as Array<Record<string, unknown>>);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions');
      setRows([]);
    } finally {
      setIsLoading(false);
    }
  }, [entityId, fetchVersions]);

  const loadDetail = useCallback(async (versionNumber: number) => {
    try {
      const payload = await getVersionDetail(entityType, entityId, versionNumber);
      setDetail(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load version detail');
    }
  }, [entityType, entityId]);

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <label className="text-xs text-[#94A3B8]">
          Entity Type
          <select value={entityType} onChange={(e) => setEntityType(e.target.value as EntityType)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white">
            <option value="analytics_snapshot">analytics_snapshot</option>
            <option value="recommendation_record">recommendation_record</option>
            <option value="frago_order">frago_order</option>
          </select>
        </label>
        <label className="text-xs text-[#94A3B8] md:col-span-2">
          Entity ID
          <input value={entityId} onChange={(e) => setEntityId(e.target.value)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" placeholder="Enter entity_id" />
        </label>
      </div>
      <button onClick={() => void loadList()} className="rounded bg-[#1D4ED8] px-3 py-2 text-xs font-semibold text-white">Load Versions</button>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void loadList()}>
        <VersionList rows={rows} onSelect={(versionNumber) => void loadDetail(versionNumber)} />
      </AsyncState>
      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-3">
        <h3 className="text-sm font-semibold text-white">Version Detail</h3>
        <pre className="mt-2 max-h-72 overflow-auto text-[11px] text-[#CBD5E1]">{JSON.stringify(detail ?? {}, null, 2)}</pre>
      </div>
    </section>
  );
};
