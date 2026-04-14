import React from 'react';

export type VisualizationType = 'chart' | 'line' | 'table' | 'cards' | 'pie' | 'area';

interface VisualizationControllerProps {
  currentView: VisualizationType;
  onViewChange: (next: VisualizationType) => void;
  availableViews: VisualizationType[];
}

interface DataVisualizerProps {
  data: unknown[];
  visualizationType: VisualizationType;
  renderChart?: () => React.ReactNode;
  renderLine?: () => React.ReactNode;
  renderPie?: () => React.ReactNode;
  renderArea?: () => React.ReactNode;
  renderTable?: () => React.ReactNode;
  renderCards?: () => React.ReactNode;
}

export const VisualizationController: React.FC<VisualizationControllerProps> = ({ currentView, onViewChange, availableViews }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {availableViews.map((view) => (
        <button
          key={view}
          onClick={() => onViewChange(view)}
          className={`rounded-lg px-3 py-2 text-sm font-semibold ${currentView === view ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}
        >
          {view}
        </button>
      ))}
    </div>
  );
};

export const DataVisualizer: React.FC<DataVisualizerProps> = ({
  data,
  visualizationType,
  renderChart,
  renderLine,
  renderPie,
  renderArea,
  renderTable,
  renderCards,
}) => {
  if (!Array.isArray(data) || data.length === 0) {
    return <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">No visualization data is available for this view.</div>;
  }

  switch (visualizationType) {
    case 'line':
      return <>{renderLine?.() || renderChart?.()}</>;
    case 'pie':
      return <>{renderPie?.() || renderChart?.()}</>;
    case 'area':
      return <>{renderArea?.() || renderChart?.()}</>;
    case 'table':
      return <>{renderTable?.() || renderCards?.() || renderChart?.()}</>;
    case 'cards':
      return <>{renderCards?.() || renderChart?.()}</>;
    case 'chart':
    default:
      return <>{renderChart?.()}</>;
  }
};

export default VisualizationController;
