import { IngestionModule, IngestionResult } from './types';

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function runModule(input: {
  sourceId: IngestionResult['sourceId'];
  label: string;
  failRate?: number;
  latencyMs?: number;
}): Promise<IngestionResult> {
  const started = performance.now();
  await wait(input.latencyMs ?? 80);
  const failed = Math.random() < (input.failRate ?? 0.08);
  return {
    sourceId: input.sourceId,
    status: failed ? 'failed' : 'healthy',
    message: failed ? `${input.label} sync failed` : `${input.label} sync complete`,
    lastSyncAt: failed ? null : new Date().toISOString(),
    durationMs: Math.round(performance.now() - started),
  };
}

export const INGESTION_MODULES: IngestionModule[] = [
  {
    id: 'vantage',
    label: 'Vantage Data',
    run: () => runModule({ sourceId: 'vantage', label: 'Vantage Data', latencyMs: 95 }),
  },
  {
    id: 'aie',
    label: 'AIE Data',
    run: () => runModule({ sourceId: 'aie', label: 'AIE Data', latencyMs: 90 }),
  },
  {
    id: 'dod_component',
    label: 'DoD Component Data',
    run: () => runModule({ sourceId: 'dod_component', label: 'DoD Component Data', latencyMs: 105 }),
  },
  {
    id: 'srp_rop_twg_docs',
    label: 'SRP/ROP/TWG Documents',
    run: () => runModule({ sourceId: 'srp_rop_twg_docs', label: 'SRP/ROP/TWG Documents', latencyMs: 110 }),
  },
  {
    id: 'reserve_vacancy',
    label: 'Reserve Vacancy Data',
    run: () => runModule({ sourceId: 'reserve_vacancy', label: 'Reserve Vacancy Data', latencyMs: 88 }),
  },
  {
    id: 'document_center_index',
    label: 'Document Center Indexing',
    run: () => runModule({ sourceId: 'document_center_index', label: 'Document Center Indexing', latencyMs: 120 }),
  },
];
