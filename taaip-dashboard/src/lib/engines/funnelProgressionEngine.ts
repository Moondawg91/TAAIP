import { EngineSummary } from './types';

export interface FunnelStageCounts {
  leads: number;
  appointments: number;
  interviews: number;
  contracts: number;
}

export function runFunnelProgressionEngine(input: FunnelStageCounts): {
  summaries: EngineSummary[];
  conversionRates: Array<{ stage: string; rate: number }>;
} {
  const leads = Math.max(input.leads, 1);
  const appointmentRate = Number(((input.appointments / leads) * 100).toFixed(2));
  const interviewRate = Number(((input.interviews / Math.max(input.appointments, 1)) * 100).toFixed(2));
  const contractRate = Number(((input.contracts / Math.max(input.interviews, 1)) * 100).toFixed(2));

  return {
    summaries: [
      { label: 'Lead->Appointment %', value: appointmentRate, signal: appointmentRate >= 40 ? 'good' : 'warning' },
      { label: 'Interview->Contract %', value: contractRate, signal: contractRate >= 35 ? 'good' : 'warning' },
    ],
    conversionRates: [
      { stage: 'Lead to Appointment', rate: appointmentRate },
      { stage: 'Appointment to Interview', rate: interviewRate },
      { stage: 'Interview to Contract', rate: contractRate },
    ],
  };
}
