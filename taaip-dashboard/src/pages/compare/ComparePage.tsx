import React, { useCallback, useState } from 'react';
import { StructuredDiffViewer } from '../../components/compare/StructuredDiffViewer';
import { AsyncState } from '../../components/shared/AsyncState';
import { compareVersions } from '../../lib/intelligenceApi';

type EntityType = 'analytics_snapshot' | 'recommendation_record' | 'frago_order';

export const ComparePage: React.FC = () => {
  const [entityType, setEntityType] = useState<EntityType>('analytics_snapshot');
  const [entityId, setEntityId] = useState('');
  const [leftVersion, setLeftVersion] = useState(1);
  const [rightVersion, setRightVersion] = useState(2);
  const [diff, setDiff] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await compareVersions({
        entity_type: entityType,
        entity_id: entityId,
        left_version: leftVersion,
        right_version: rightVersion,
      });
      setDiff(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare versions');
      setDiff(null);
    } finally {
      setIsLoading(false);
    }
  }, [entityType, entityId, leftVersion, rightVersion]);

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <label className="text-xs text-[#94A3B8]">
          Entity Type
          <select value={entityType} onChange={(e) => setEntityType(e.target.value as EntityType)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white">
            <option value="analytics_snapshot">analytics_snapshot</option>
            <option value="recommendation_record">recommendation_record</option>
            <option value="frago_order">frago_order</option>
          </select>
        </label>
        <label className="text-xs text-[#94A3B8]">
          Left
          <input type="number" value={leftVersion} onChange={(e) => setLeftVersion(Number(e.target.value))} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" />
        </label>
        <label className="text-xs text-[#94A3B8]">
          Right
          <input type="number" value={rightVersion} onChange={(e) => setRightVersion(Number(e.target.value))} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" />
        </label>
        <label className="text-xs text-[#94A3B8]">
          Entity ID
          <input value={entityId} onChange={(e) => setEntityId(e.target.value)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" />
        </label>
      </div>
      <button onClick={() => void load()} className="rounded bg-[#1D4ED8] px-3 py-2 text-xs font-semibold text-white">Compare</button>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void load()}>
        <StructuredDiffViewer diff={diff} />
      </AsyncState>
    </section>
  );
};
