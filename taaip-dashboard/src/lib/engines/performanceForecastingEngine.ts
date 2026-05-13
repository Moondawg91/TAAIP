import { EngineSummary } from './types';

export interface PerformanceSeriesPoint {
  period: string;
  contracts: number;
}

export function runPerformanceForecastingEngine(points: PerformanceSeriesPoint[]): {
  summaries: EngineSummary[];
  forecast: Array<{ period: string; projectedContracts: number }>;
} {
  if (points.length === 0) {
    return {
      summaries: [{ label: 'Forecast', value: 'No data', signal: 'warning' }],
      forecast: [],
    };
  }

  const avg = points.reduce((sum, point) => sum + point.contracts, 0) / points.length;
  const trend = points.length > 1 ? points[points.length - 1].contracts - points[0].contracts : 0;
  const increment = trend / Math.max(points.length - 1, 1);

  const last = points[points.length - 1];
  const forecast = [1, 2, 3].map((step) => ({
    period: `P+${step}`,
    projectedContracts: Math.max(Math.round(last.contracts + increment * step), 0),
  }));

  return {
    summaries: [
      { label: 'Average Contracts', value: avg.toFixed(1), signal: 'neutral' },
      { label: 'Trend Delta', value: trend, signal: trend >= 0 ? 'good' : 'warning' },
    ],
    forecast,
  };
}
