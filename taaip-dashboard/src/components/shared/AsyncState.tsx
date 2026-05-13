import React from 'react';
import { useToast } from './ToastProvider';

type AsyncStateProps = {
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
  children: React.ReactNode;
};

export const AsyncState: React.FC<AsyncStateProps> = ({ isLoading, error, onRetry, children }) => {
  const { pushToast } = useToast();

  React.useEffect(() => {
    if (error) {
      pushToast('error', error);
    }
  }, [error, pushToast]);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[#1D3A5C] bg-[#0B223F] p-4 animate-pulse">
        <div className="h-4 w-40 bg-[#193B63] rounded mb-3" />
        <div className="h-4 w-full bg-[#193B63] rounded mb-2" />
        <div className="h-4 w-5/6 bg-[#193B63] rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-[#7F1D1D] bg-[#3B0F15] p-4">
        <p className="text-sm text-[#FECACA] mb-3">{error}</p>
        {onRetry ? (
          <button
            onClick={onRetry}
            className="rounded-md bg-[#B91C1C] px-3 py-1.5 text-xs font-semibold text-white"
          >
            Retry
          </button>
        ) : null}
      </div>
    );
  }

  return <>{children}</>;
};
