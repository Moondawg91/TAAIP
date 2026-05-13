import { logAuditEvent } from '../audit/controller';
import { pushNotification } from '../notifications/controller';
import { ExportRequest, ExportResult } from './types';

function makeFilename(scope: string, format: string): string {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  return `${scope}-${stamp}.${format === 'commander-brief' ? 'txt' : format}`;
}

function download(content: string, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function runExport(request: ExportRequest): Promise<ExportResult> {
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const filename = makeFilename(request.scopeId, request.format);
  const generatedAt = new Date().toISOString();

  const content = JSON.stringify(
    {
      title: request.scopeLabel,
      generatedAt,
      format: request.format,
      payload: request.payload,
    },
    null,
    2,
  );

  if (request.format === 'pdf') {
    download(content, filename, 'application/pdf');
  } else if (request.format === 'pptx') {
    download(content, filename, 'application/vnd.openxmlformats-officedocument.presentationml.presentation');
  } else {
    download(content, filename, 'text/plain');
  }

  logAuditEvent({
    eventType: 'system_config_change',
    actor: 'export.controller',
    message: `Export generated for ${request.scopeId} in ${request.format}`,
    target: request.scopeId,
    metadata: { format: request.format },
  });

  pushNotification({
    title: 'Export Ready',
    message: `${request.scopeLabel} export (${request.format}) has been generated.`,
    category: 'system',
    severity: 'success',
    source: 'Export Controller',
  });

  return {
    requestId,
    format: request.format,
    generatedAt,
    filename,
    status: 'generated',
  };
}

export function buildCommanderBriefPayload(input: {
  title: string;
  summary: string;
  riskItems: string[];
  actions: string[];
}): Record<string, unknown> {
  return {
    commanderBrief: {
      title: input.title,
      summary: input.summary,
      riskItems: input.riskItems,
      actions: input.actions,
    },
  };
}
