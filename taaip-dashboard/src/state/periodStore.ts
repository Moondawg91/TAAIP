import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type PeriodType = 'RSM' | 'QTR' | 'FY';

export type PeriodState = {
  periodType: PeriodType;
  periodValue: string;
  setPeriodType: (t: PeriodType) => void;
  setPeriodValue: (v: string) => void;
};

const PeriodContext = createContext<PeriodState | undefined>(undefined);

function readInitialType(): PeriodType {
  const params = new URLSearchParams(window.location.search);
  const raw = (params.get('period_type') ?? 'FY').toUpperCase();
  if (raw === 'RSM' || raw === 'QTR' || raw === 'FY') {
    return raw;
  }
  return 'FY';
}

function readInitialValue(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get('period_value') ?? String(new Date().getFullYear());
}

function writePeriodToUrl(periodType: PeriodType, periodValue: string): void {
  const params = new URLSearchParams(window.location.search);
  params.set('period_type', periodType);
  params.set('period_value', periodValue);
  const next = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, '', next);
}

export const PeriodProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [periodType, setPeriodType] = useState<PeriodType>(() => readInitialType());
  const [periodValue, setPeriodValue] = useState<string>(() => readInitialValue());

  useEffect(() => {
    writePeriodToUrl(periodType, periodValue);
  }, [periodType, periodValue]);

  const value = useMemo<PeriodState>(() => ({
    periodType,
    periodValue,
    setPeriodType,
    setPeriodValue,
  }), [periodType, periodValue]);

  return React.createElement(PeriodContext.Provider, { value }, children);
};

export function usePeriodStore(): PeriodState {
  const ctx = useContext(PeriodContext);
  if (!ctx) {
    throw new Error('usePeriodStore must be used within PeriodProvider');
  }
  return ctx;
}
