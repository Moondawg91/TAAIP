import { EngineSummary, ZipMarketRecord } from './types';

export function runReserveAlignmentEngine(rows: ZipMarketRecord[]): {
  summaries: EngineSummary[];
  alignmentRows: Array<{ zip: string; reserveVacancies: number; contracts: number; gap: number }>;
} {
  const alignmentRows = rows.map((row) => ({
    zip: row.zip,
    reserveVacancies: row.reserveVacancies,
    contracts: row.contracts,
    gap: row.reserveVacancies - row.contracts,
  }));

  const totalGap = alignmentRows.reduce((sum, row) => sum + row.gap, 0);

  return {
    summaries: [
      { label: 'Reserve Alignment Gap', value: totalGap, signal: totalGap > 0 ? 'warning' : 'good' },
      { label: 'Tracked ZIPs', value: alignmentRows.length, signal: 'neutral' },
    ],
    alignmentRows,
  };
}
