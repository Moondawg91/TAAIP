export type IngestionSourceId =
  | 'vantage'
  | 'aie'
  | 'dod_component'
  | 'srp_rop_twg_docs'
  | 'reserve_vacancy'
  | 'document_center_index';

export type IngestionStatus = 'healthy' | 'degraded' | 'failed' | 'running';

export interface IngestionResult {
  sourceId: IngestionSourceId;
  status: IngestionStatus;
  message: string;
  lastSyncAt: string | null;
  durationMs: number;
}

export interface IngestionModule {
  id: IngestionSourceId;
  label: string;
  run: () => Promise<IngestionResult>;
}

export interface IngestionSystemSnapshot {
  sources: IngestionResult[];
  overallStatus: IngestionStatus;
  generatedAt: string;
}
