export type ExportFormat = 'pdf' | 'pptx' | 'commander-brief';

export interface ExportRequest {
  scopeId: string;
  scopeLabel: string;
  format: ExportFormat;
  payload: Record<string, unknown>;
}

export interface ExportResult {
  requestId: string;
  format: ExportFormat;
  generatedAt: string;
  filename: string;
  status: 'generated';
}
