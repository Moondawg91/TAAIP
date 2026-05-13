import React from 'react';
import { PeriodType, usePeriodStore } from '../../state/periodStore';

const PLACEHOLDERS: Record<PeriodType, string> = {
  FY: '2026',
  QTR: 'Q2',
  RSM: 'RSM-2026-02',
};

export const PeriodSelector: React.FC = () => {
  const { periodType, periodValue, setPeriodType, setPeriodValue } = usePeriodStore();

  return (
    <div className="grid grid-cols-2 gap-2">
      <div className="space-y-1">
        <label className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">Period Type</label>
        <select
          value={periodType}
          onChange={(event) => setPeriodType(event.target.value as PeriodType)}
          className="w-full rounded-md border border-[#1D3A5C] bg-[#081B33] px-2 py-1.5 text-xs text-[#F8FAFC]"
        >
          <option value="FY">FY</option>
          <option value="QTR">QTR</option>
          <option value="RSM">RSM</option>
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-[10px] uppercase tracking-[0.08em] text-[#94A3B8]">Period Value</label>
        <input
          value={periodValue}
          onChange={(event) => setPeriodValue(event.target.value)}
          placeholder={PLACEHOLDERS[periodType]}
          className="w-full rounded-md border border-[#1D3A5C] bg-[#081B33] px-2 py-1.5 text-xs text-[#F8FAFC]"
        />
      </div>
    </div>
  );
};
