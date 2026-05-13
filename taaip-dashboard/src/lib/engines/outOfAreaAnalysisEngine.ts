import { EngineSummary } from './types';

export interface OutOfAreaRecord {
  homeZip: string;
  contractZip: string;
  branch: string;
}

export function runOutOfAreaAnalysisEngine(rows: OutOfAreaRecord[]): {
  summaries: EngineSummary[];
  leakage: Array<OutOfAreaRecord & { leakage: boolean }>;
} {
  const leakage = rows.map((row) => ({ ...row, leakage: row.homeZip !== row.contractZip }));
  const leakageCount = leakage.filter((row) => row.leakage).length;

  return {
    summaries: [
      { label: 'Out-of-Area Cases', value: leakageCount, signal: leakageCount > 0 ? 'warning' : 'good' },
      { label: 'Total Cases', value: rows.length, signal: 'neutral' },
    ],
    leakage,
  };
}
