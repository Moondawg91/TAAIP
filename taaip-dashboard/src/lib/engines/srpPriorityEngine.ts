import { EngineSummary } from './types';

export interface SrpPopulationInput {
  seniors: number;
  juniors: number;
  postSecondary: number;
}

export function runSrpPriorityEngine(input: SrpPopulationInput): {
  summaries: EngineSummary[];
  priorityOrder: Array<{ cohort: 'seniors' | 'juniors' | 'post-secondary'; score: number }>;
} {
  const seniorScore = input.seniors * 1;
  const juniorScore = input.juniors * 0.65;
  const postScore = input.postSecondary * 0.5;
  const priorityOrder = [
    { cohort: 'seniors' as const, score: seniorScore },
    { cohort: 'juniors' as const, score: juniorScore },
    { cohort: 'post-secondary' as const, score: postScore },
  ].sort((a, b) => b.score - a.score);

  return {
    summaries: [
      { label: 'Senior Weight', value: seniorScore.toFixed(1), signal: 'good' },
      { label: 'Junior Weight', value: juniorScore.toFixed(1), signal: 'warning' },
      { label: 'Post-Secondary Weight', value: postScore.toFixed(1), signal: 'neutral' },
    ],
    priorityOrder,
  };
}
