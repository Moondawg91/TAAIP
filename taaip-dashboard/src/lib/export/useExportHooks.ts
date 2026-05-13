import { useCallback } from 'react';
import { buildCommanderBriefPayload, runExport } from './controller';

export function usePageExport(scopeId: string, scopeLabel: string) {
  const exportPdf = useCallback(async (payload: Record<string, unknown>) => {
    return runExport({ scopeId, scopeLabel, format: 'pdf', payload });
  }, [scopeId, scopeLabel]);

  const exportPpt = useCallback(async (payload: Record<string, unknown>) => {
    return runExport({ scopeId, scopeLabel, format: 'pptx', payload });
  }, [scopeId, scopeLabel]);

  const exportCommanderBrief = useCallback(async (summary: {
    summary: string;
    riskItems: string[];
    actions: string[];
  }) => {
    const payload = buildCommanderBriefPayload({
      title: scopeLabel,
      summary: summary.summary,
      riskItems: summary.riskItems,
      actions: summary.actions,
    });
    return runExport({ scopeId, scopeLabel, format: 'commander-brief', payload });
  }, [scopeId, scopeLabel]);

  return { exportPdf, exportPpt, exportCommanderBrief };
}
