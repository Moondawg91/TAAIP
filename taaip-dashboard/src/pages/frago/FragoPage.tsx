import React, { useCallback, useState } from 'react';
import { FragoViewer } from '../../components/frago/FragoViewer';
import { AsyncState } from '../../components/shared/AsyncState';
import { getFragoVersion, getFragoVersions } from '../../lib/intelligenceApi';

export const FragoPage: React.FC = () => {
  const [fragoVersionId, setFragoVersionId] = useState('');
  const [fragoId, setFragoId] = useState('');
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [versions, setVersions] = useState<Array<Record<string, unknown>>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [detailPayload, versionPayload] = await Promise.all([
        fragoVersionId ? getFragoVersion(fragoVersionId) : Promise.resolve({}),
        fragoId ? getFragoVersions(fragoId) : Promise.resolve({ versions: [] }),
      ]);
      setDetail(detailPayload);
      setVersions((versionPayload.versions ?? []) as Array<Record<string, unknown>>);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load FRAGO data');
    } finally {
      setIsLoading(false);
    }
  }, [fragoId, fragoVersionId]);

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-xs text-[#94A3B8]">
          FRAGO Version ID
          <input value={fragoVersionId} onChange={(e) => setFragoVersionId(e.target.value)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" placeholder="Enter frago_version_id" />
        </label>
        <label className="text-xs text-[#94A3B8]">
          FRAGO ID
          <input value={fragoId} onChange={(e) => setFragoId(e.target.value)} className="mt-1 w-full rounded border border-[#1D3A5C] bg-[#0C2545] px-3 py-2 text-sm text-white" placeholder="Enter frago_id" />
        </label>
      </div>
      <button onClick={() => void load()} className="rounded bg-[#1D4ED8] px-3 py-2 text-xs font-semibold text-white">Load FRAGO</button>
      <AsyncState isLoading={isLoading} error={error} onRetry={() => void load()}>
        <FragoViewer detail={detail} versions={versions} />
      </AsyncState>
    </section>
  );
};
