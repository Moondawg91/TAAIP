import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

type ToastKind = 'error' | 'success' | 'info';

type ToastItem = {
  id: string;
  kind: ToastKind;
  message: string;
};

type ToastContextValue = {
  pushToast: (kind: ToastKind, message: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [items, setItems] = useState<ToastItem[]>([]);

  const pushToast = useCallback((kind: ToastKind, message: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const next: ToastItem = { id, kind, message };
    setItems((prev) => [...prev, next].slice(-4));
    window.setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 3500);
  }, []);

  const value = useMemo<ToastContextValue>(() => ({ pushToast }), [pushToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-[120] space-y-2">
        {items.map((item) => {
          const color = item.kind === 'error' ? 'border-[#7F1D1D] bg-[#3B0F15] text-[#FECACA]' : item.kind === 'success' ? 'border-[#14532D] bg-[#052E16] text-[#BBF7D0]' : 'border-[#1E3A8A] bg-[#0C2545] text-[#BFDBFE]';
          return (
            <div key={item.id} className={`pointer-events-auto rounded border px-3 py-2 text-xs shadow ${color}`}>
              {item.message}
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return ctx;
}
