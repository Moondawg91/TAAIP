import { useCallback, useEffect, useState } from 'react';

import { API_BASE } from '../config/api';

export type AnyRecord = Record<string, any>;

export const asArray = <T,>(value: T[] | null | undefined): T[] => {
  return Array.isArray(value) ? value : [];
};

export const asNumber = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const asText = (value: unknown, fallback = 'Unavailable'): string => {
  if (value === null || value === undefined || value === '') {
    return fallback;
  }
  return String(value);
};

export const toPercent = (value: unknown): string => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return 'Unavailable';
  }
  const percent = parsed <= 1 ? parsed * 100 : parsed;
  return `${percent.toFixed(1)}%`;
};

export const buildApiUrl = (path: string): string => {
  return `${API_BASE}${path}`;
};

export const useOperationalCommandData = (scopeType = 'USAREC', scopeValue = 'USAREC') => {
  const [data, setData] = useState<AnyRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        buildApiUrl(
          `/api/powerbi/operational/command_dataset?scope_type=${encodeURIComponent(scopeType)}&scope_value=${encodeURIComponent(scopeValue)}`,
        ),
      );

      if (!response.ok) {
        throw new Error(`Power BI operational dataset returned ${response.status}`);
      }

      const payload = await response.json();
      if (payload?.status !== 'ok') {
        throw new Error('Operational dataset did not return an ok status');
      }

      setData((payload?.data || {}) as AnyRecord);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Unable to load operational dataset');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [scopeType, scopeValue]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
};
