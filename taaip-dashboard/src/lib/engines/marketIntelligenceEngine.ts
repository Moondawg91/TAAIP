import { EngineSummary, ZipMarketRecord } from './types';

export function runMarketIntelligenceEngine(rows: ZipMarketRecord[]): {
  summaries: EngineSummary[];
  segmented: Array<{ zip: string; cbsa: string; prizm: string; contractRate: number }>;
} {
  const totalPopulation = rows.reduce((sum, row) => sum + row.population, 0);
  const totalContracts = rows.reduce((sum, row) => sum + row.contracts, 0);
  const rate = totalPopulation > 0 ? (totalContracts / totalPopulation) * 100 : 0;
  return {
    summaries: [
      { label: 'Total Population', value: totalPopulation, signal: 'neutral' },
      { label: 'Total Contracts', value: totalContracts, signal: 'good' },
      { label: 'Contract Rate %', value: rate.toFixed(2), signal: rate >= 0.8 ? 'good' : 'warning' },
    ],
    segmented: rows.map((row) => ({
      zip: row.zip,
      cbsa: row.cbsa,
      prizm: row.prizm,
      contractRate: row.population > 0 ? Number(((row.contracts / row.population) * 100).toFixed(2)) : 0,
    })),
  };
}
