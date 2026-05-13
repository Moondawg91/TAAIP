import { EngineSummary } from './types';

export interface RoiInput {
  spend: number;
  contracts: number;
  qualifiedLeads: number;
}

export function runRoiCostToEffectEngine(input: RoiInput): {
  summaries: EngineSummary[];
  metrics: { costPerContract: number; costPerLead: number; effectiveness: number };
} {
  const costPerContract = input.contracts > 0 ? input.spend / input.contracts : input.spend;
  const costPerLead = input.qualifiedLeads > 0 ? input.spend / input.qualifiedLeads : input.spend;
  const effectiveness = input.spend > 0 ? (input.contracts / input.spend) * 10000 : 0;

  return {
    summaries: [
      { label: 'Cost per Contract', value: costPerContract.toFixed(2), signal: costPerContract <= 900 ? 'good' : 'warning' },
      { label: 'Cost per Lead', value: costPerLead.toFixed(2), signal: 'neutral' },
      { label: 'Effectiveness', value: effectiveness.toFixed(2), signal: effectiveness >= 1.2 ? 'good' : 'warning' },
    ],
    metrics: {
      costPerContract: Number(costPerContract.toFixed(2)),
      costPerLead: Number(costPerLead.toFixed(2)),
      effectiveness: Number(effectiveness.toFixed(2)),
    },
  };
}
