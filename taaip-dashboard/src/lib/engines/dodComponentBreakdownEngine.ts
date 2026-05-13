import { EngineSummary, ZipMarketRecord } from './types';

export function runDodComponentBreakdownEngine(rows: ZipMarketRecord[]): {
  summaries: EngineSummary[];
  componentShare: Array<{ component: string; share: number }>;
} {
  const total = rows.reduce((sum, row) => sum + row.contracts, 0) || 1;
  const army = rows.reduce((sum, row) => sum + Math.round(row.contracts * 0.56), 0);
  const navy = rows.reduce((sum, row) => sum + Math.round(row.contracts * 0.17), 0);
  const marines = rows.reduce((sum, row) => sum + Math.round(row.contracts * 0.12), 0);
  const airForce = Math.max(total - army - navy - marines, 0);

  return {
    summaries: [
      { label: 'Army Share %', value: ((army / total) * 100).toFixed(1), signal: 'good' },
      { label: 'Navy Share %', value: ((navy / total) * 100).toFixed(1), signal: 'neutral' },
      { label: 'Air Force Share %', value: ((airForce / total) * 100).toFixed(1), signal: 'neutral' },
    ],
    componentShare: [
      { component: 'Army', share: Number(((army / total) * 100).toFixed(1)) },
      { component: 'Navy', share: Number(((navy / total) * 100).toFixed(1)) },
      { component: 'Marines', share: Number(((marines / total) * 100).toFixed(1)) },
      { component: 'Air Force', share: Number(((airForce / total) * 100).toFixed(1)) },
    ],
  };
}
