import React from 'react';

export const PrintButton: React.FC = () => {
  return (
    <button
      onClick={() => window.print()}
      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
    >
      Print
    </button>
  );
};

export default PrintButton;
