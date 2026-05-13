import { EngineSummary, ZipMarketRecord } from './types';

export function runMarketPotentialEngine(rows: ZipMarketRecord[]): {
  summaries: EngineSummary[];
  opportunities: Array<{ zip: string; potentialRemaining: number; opportunityScore: number }>;
} {
  const opportunities = rows.map((row) => {
    const potentialRemaining = Math.max(Math.round(row.population * 0.02) - row.contracts, 0);
    const opportunityScore = Number(((potentialRemaining / Math.max(row.population, 1)) * 1000).toFixed(2));
    return { zip: row.zip, potentialRemaining, opportunityScore };
  });

  const remaining = opportunities.reduce((sum, row) => sum + row.potentialRemaining, 0);

  return {
    summaries: [
      { label: 'Potential Remaining', value: remaining, signal: remaining > 100 ? 'warning' : 'good' },
      { label: 'Top Opportunity ZIP', value: opportunities.sort((a, b) => b.opportunityScore - a.opportunityScore)[0]?.zip ?? 'N/A', signal: 'neutral' },
    ],
    opportunities,
  };
}
