import { logAuditEvent } from '../audit/controller';
import { pushNotification } from '../notifications/controller';
import { INGESTION_MODULES } from './modules';
import { IngestionResult, IngestionStatus, IngestionSystemSnapshot } from './types';

type IngestionListener = (snapshot: IngestionSystemSnapshot) => void;

const listeners = new Set<IngestionListener>();

let lastSnapshot: IngestionSystemSnapshot = {
  sources: [],
  overallStatus: 'running',
  generatedAt: new Date().toISOString(),
};

function computeOverallStatus(sources: IngestionResult[]): IngestionStatus {
  if (sources.some((source) => source.status === 'failed')) {
    return 'failed';
  }
  if (sources.some((source) => source.status === 'degraded')) {
    return 'degraded';
  }
  if (sources.every((source) => source.status === 'healthy')) {
    return 'healthy';
  }
  return 'running';
}

function emit(): void {
  const snapshot = { ...lastSnapshot, sources: [...lastSnapshot.sources] };
  listeners.forEach((listener) => listener(snapshot));
}

export function subscribeIngestionHealth(listener: IngestionListener): () => void {
  listeners.add(listener);
  listener({ ...lastSnapshot, sources: [...lastSnapshot.sources] });
  return () => listeners.delete(listener);
}

export function getIngestionSnapshot(): IngestionSystemSnapshot {
  return { ...lastSnapshot, sources: [...lastSnapshot.sources] };
}

export async function runIngestionModule(moduleId: IngestionResult['sourceId']): Promise<IngestionResult> {
  const module = INGESTION_MODULES.find((item) => item.id === moduleId);
  if (!module) {
    throw new Error(`Unknown ingestion module: ${moduleId}`);
  }

  const result = await module.run();
  const existing = lastSnapshot.sources.filter((source) => source.sourceId !== moduleId);
  const sources = [result, ...existing];
  const overallStatus = computeOverallStatus(sources);
  lastSnapshot = {
    sources,
    overallStatus,
    generatedAt: new Date().toISOString(),
  };

  logAuditEvent({
    eventType: 'system_config_change',
    actor: 'system.ingestion',
    message: `Ingestion module ${moduleId} completed with ${result.status}`,
    target: moduleId,
  });

  if (result.status === 'failed') {
    pushNotification({
      title: 'Ingestion Failure',
      message: `${module.label} failed during sync run.`,
      category: 'ingestion',
      severity: 'critical',
      source: 'Ingestion Controller',
    });
  }

  emit();
  return result;
}

export async function runAllIngestionModules(): Promise<IngestionSystemSnapshot> {
  const responses = await Promise.all(INGESTION_MODULES.map((module) => module.run()));
  const overallStatus = computeOverallStatus(responses);
  lastSnapshot = {
    sources: responses,
    overallStatus,
    generatedAt: new Date().toISOString(),
  };

  responses
    .filter((item) => item.status === 'failed')
    .forEach((failed) => {
      pushNotification({
        title: 'Ingestion Failure',
        message: `${failed.sourceId} reported failure at ${lastSnapshot.generatedAt}`,
        category: 'ingestion',
        severity: 'critical',
        source: 'Ingestion Controller',
      });
    });

  emit();
  return getIngestionSnapshot();
}
