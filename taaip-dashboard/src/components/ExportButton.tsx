import React from 'react';

interface ExportButtonProps {
  data: unknown;
  filename: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ data, filename }) => {
  const onExport = () => {
    const blob = new Blob([JSON.stringify(data ?? [], null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={onExport}
      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
    >
      Export
    </button>
  );
};

export default ExportButton;
