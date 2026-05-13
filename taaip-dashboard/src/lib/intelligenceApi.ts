import { API_BASE } from '../config/api';

type Query = Record<string, string | number | undefined | null>;

type CacheEntry<T> = {
  expiresAt: number;
  value: T;
};

const RESPONSE_CACHE = new Map<string, CacheEntry<unknown>>();
const IN_FLIGHT = new Map<string, Promise<unknown>>();
const DEFAULT_TTL_MS = 30_000;

function now(): number {
  return Date.now();
}

function buildQuery(params: Query): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).length > 0) {
      search.set(key, String(value));
    }
  });
  const suffix = search.toString();
  return suffix.length > 0 ? `?${suffix}` : '';
}

async function requestJson<T>(path: string, options?: RequestInit, retries = 1): Promise<T> {
  const method = (options?.method ?? 'GET').toUpperCase();
  const bodyText = typeof options?.body === 'string' ? options.body : '';
  const cacheKey = `${method}:${path}:${bodyText}`;

  if (method === 'GET') {
    const cached = RESPONSE_CACHE.get(cacheKey);
    if (cached && cached.expiresAt > now()) {
      return cached.value as T;
    }
  }

  const inflight = IN_FLIGHT.get(cacheKey);
  if (inflight) {
    return (await inflight) as T;
  }

  const run = async (): Promise<T> => {
    let lastError: unknown = null;
    const startedAt = performance.now();
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        const response = await fetch(`${API_BASE}${path}`, {
          headers: {
            'Content-Type': 'application/json',
          },
          ...options,
        });
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        const value = (await response.json()) as T;
        if (method === 'GET') {
          RESPONSE_CACHE.set(cacheKey, { expiresAt: now() + DEFAULT_TTL_MS, value });
        }
        // eslint-disable-next-line no-console
        console.debug('intelligence_api', { path, method, duration_ms: Math.round(performance.now() - startedAt) });
        return value;
      } catch (err) {
        lastError = err;
        if (attempt === retries) {
          throw lastError;
        }
      }
    }
    throw lastError;
  };

  const promise = run();
  IN_FLIGHT.set(cacheKey, promise);
  try {
    return await promise;
  } finally {
    IN_FLIGHT.delete(cacheKey);
  }
}

export function getArchiveEvents(params: Query): Promise<{ count: number; events: unknown[] }> {
  return requestJson(`/api/v2/intelligence/archive/events${buildQuery(params)}`);
}

export function getRecommendations(params: Query): Promise<unknown[]> {
  return requestJson(`/api/v2/intelligence/recommendations${buildQuery(params)}`);
}

export function getFragoVersion(fragoVersionId: string): Promise<Record<string, unknown>> {
  return requestJson(`/api/v2/intelligence/fragos/${encodeURIComponent(fragoVersionId)}`);
}

export function getFragoVersions(fragoId: string): Promise<Record<string, unknown>> {
  return requestJson(`/api/v2/intelligence/fragos/${encodeURIComponent(fragoId)}/versions`);
}

export function getAnalyticsVersions(snapshotId: string): Promise<Record<string, unknown>> {
  return requestJson(`/api/v2/intelligence/analytics/${encodeURIComponent(snapshotId)}/versions`);
}

export function getRecommendationVersions(recordId: string): Promise<Record<string, unknown>> {
  return requestJson(`/api/v2/intelligence/recommendations/${encodeURIComponent(recordId)}/versions`);
}

export function getVersionDetail(entityType: string, entityId: string, versionNumber: number): Promise<Record<string, unknown>> {
  return requestJson(`/api/v2/intelligence/versions/detail${buildQuery({
    entity_type: entityType,
    entity_id: entityId,
    version_number: versionNumber,
  })}`);
}

export function compareVersions(payload: {
  entity_type: string;
  entity_id: string;
  left_version: number;
  right_version: number;
}): Promise<Record<string, unknown>> {
  return requestJson('/api/v2/intelligence/compare/versions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
