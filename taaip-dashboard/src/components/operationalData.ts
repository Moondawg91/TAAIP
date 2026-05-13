import { useCallback, useEffect, useState } from 'react';

import { API_BASE } from '../config/api';
import { authFetch } from '../lib/authSession';

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
  const [blockStatus, setBlockStatus] = useState<AnyRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    let lastErrorMessage = 'Unable to load operational dataset';
    let succeeded = false;

    try {
      for (let attempt = 1; attempt <= 2; attempt += 1) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), 6500);

        try {
          const response = await authFetch(
            buildApiUrl(
              `/api/powerbi/operational/command_dataset?scope_type=${encodeURIComponent(scopeType)}&scope_value=${encodeURIComponent(scopeValue)}`,
            ),
            { signal: controller.signal },
          );

          if (!response.ok) {
            throw new Error(`Power BI operational dataset returned ${response.status}`);
          }

          const payload = await response.json();
          if (payload?.status !== 'ok') {
            throw new Error('Operational dataset did not return an ok status');
          }

          const rawData: AnyRecord = payload?.data || {};
          // Extract per-block status for consumers that want it
          const blocks: AnyRecord = {
            diagnostics: { status: (rawData.diagnostics as AnyRecord)?.status ?? 'ok' },
            twg: { status: (rawData.twg as AnyRecord)?.status ?? 'ok' },
            execution: { status: (rawData.execution as AnyRecord)?.status ?? 'ok' },
          };
          // Flatten all block data fields into a single object for backward-compatible screen access
          const flatData: AnyRecord = {
            ...(((rawData.diagnostics as AnyRecord)?.data as AnyRecord) || {}),
            ...(((rawData.twg as AnyRecord)?.data as AnyRecord) || {}),
            ...(((rawData.execution as AnyRecord)?.data as AnyRecord) || {}),
            _meta: rawData._meta,
          };
          setData(flatData);
          setBlockStatus(blocks);
          setError(null);
          succeeded = true;
          return;
        } catch (fetchError) {
          if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
            lastErrorMessage = 'Operational dataset request timed out. Showing latest available data.';
          } else {
            lastErrorMessage = fetchError instanceof Error ? fetchError.message : 'Unable to load operational dataset';
          }
          if (attempt < 2) {
            await new Promise((resolve) => window.setTimeout(resolve, 250));
          }
        } finally {
          window.clearTimeout(timeoutId);
        }
      }
    } catch (fetchError) {
      lastErrorMessage = fetchError instanceof Error ? fetchError.message : lastErrorMessage;
    } finally {
      if (!succeeded) {
        setError(lastErrorMessage);
      }
      setLoading(false);
    }
  }, [scopeType, scopeValue]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, blockStatus, loading, error, refresh };
};
