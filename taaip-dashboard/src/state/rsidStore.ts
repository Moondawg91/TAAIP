import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

type RsidContextValue = {
  rsid: string;
  setRsid: (next: string) => void;
};

const RsidContext = createContext<RsidContextValue | undefined>(undefined);

function readInitialRsid(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get('rsid') ?? 'USAREC';
}

function writeRsidToUrl(rsid: string): void {
  const params = new URLSearchParams(window.location.search);
  params.set('rsid', rsid);
  const next = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState({}, '', next);
}

export const RsidProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [rsid, setRsidState] = useState<string>(() => readInitialRsid());

  useEffect(() => {
    writeRsidToUrl(rsid);
  }, [rsid]);

  const value = useMemo<RsidContextValue>(() => ({
    rsid,
    setRsid: setRsidState,
  }), [rsid]);

  return React.createElement(RsidContext.Provider, { value }, children);
};

export function useRsidStore(): RsidContextValue {
  const ctx = useContext(RsidContext);
  if (!ctx) {
    throw new Error('useRsidStore must be used within RsidProvider');
  }
  return ctx;
}
