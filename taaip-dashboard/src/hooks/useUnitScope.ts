import { useEffect, useMemo, useState } from 'react';
import { API_BASE } from '../config/api';

export type UnitScopeState = {
  isLoading: boolean;
  error: string | null;
  options: string[];
};

export function useUnitScope(rsid: string): UnitScopeState {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function run(): Promise<void> {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}/api/v2/unit-scope/subordinates?rsid=${encodeURIComponent(rsid)}`);
        if (!response.ok) {
          throw new Error(`Unit scope request failed (${response.status})`);
        }
        const payload = (await response.json()) as { rsid?: string; subordinates?: string[] };
        if (!cancelled) {
          const all = [payload.rsid ?? rsid, ...(payload.subordinates ?? [])]
            .filter((value, index, arr) => Boolean(value) && arr.indexOf(value) === index)
            .sort();
          setOptions(all);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unable to load unit scope');
          setOptions([rsid]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [rsid]);

  return useMemo(() => ({ isLoading, error, options }), [isLoading, error, options]);
}
