import React from 'react';
import { BarChart3, LineChart as LineChartIcon, Table2, Grid3x3, PieChart as PieChartIcon, TrendingUp } from 'lucide-react';

export type VisualizationType = 'chart' | 'line' | 'table' | 'cards' | 'pie' | 'area';

interface VisualizationControllerProps {
  currentView: VisualizationType;
  onViewChange: (view: VisualizationType) => void;
  availableViews?: VisualizationType[];
  className?: string;
}

export const VisualizationController: React.FC<VisualizationControllerProps> = ({
  currentView,
  onViewChange,
  availableViews = ['chart', 'line', 'table', 'cards', 'pie', 'area'],
  className = ''
}) => {
  const viewOptions = [
    { id: 'chart' as VisualizationType, label: 'Bar Chart', icon: BarChart3, activeClass: 'bg-blue-600', hoverClass: 'hover:bg-blue-100 hover:text-blue-700' },
    { id: 'line' as VisualizationType, label: 'Line Graph', icon: LineChartIcon, activeClass: 'bg-purple-600', hoverClass: 'hover:bg-purple-100 hover:text-purple-700' },
    { id: 'table' as VisualizationType, label: 'Table View', icon: Table2, activeClass: 'bg-green-600', hoverClass: 'hover:bg-green-100 hover:text-green-700' },
    { id: 'cards' as VisualizationType, label: 'Card View', icon: Grid3x3, activeClass: 'bg-yellow-600', hoverClass: 'hover:bg-yellow-100 hover:text-yellow-700' },
    { id: 'pie' as VisualizationType, label: 'Pie Chart', icon: PieChartIcon, activeClass: 'bg-pink-600', hoverClass: 'hover:bg-pink-100 hover:text-pink-700' },
    { id: 'area' as VisualizationType, label: 'Area Chart', icon: TrendingUp, activeClass: 'bg-indigo-600', hoverClass: 'hover:bg-indigo-100 hover:text-indigo-700' },
  ].filter(option => availableViews.includes(option.id));

  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      <span className="text-sm font-semibold text-gray-700 mr-2">Visualization:</span>
      {viewOptions.map(option => {
        const Icon = option.icon;
        const isActive = currentView === option.id;
        return (
          <button
            key={option.id}
            onClick={() => onViewChange(option.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              isActive
                ? `${option.activeClass} text-white shadow-md scale-105`
                : `bg-gray-100 text-gray-700 ${option.hoverClass}`
            }`}
            title={option.label}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
};

// Helper component to render data based on visualization type
interface DataVisualizerProps {
  data: any[];
  visualizationType: VisualizationType;
  renderChart?: () => React.ReactNode;
  renderLine?: () => React.ReactNode;
  renderTable?: () => React.ReactNode;
  renderCards?: () => React.ReactNode;
  renderPie?: () => React.ReactNode;
  renderArea?: () => React.ReactNode;
}

export const DataVisualizer: React.FC<DataVisualizerProps> = ({
  visualizationType,
  renderChart,
  renderLine,
  renderTable,
  renderCards,
  renderPie,
  renderArea,
}) => {
  switch (visualizationType) {
    case 'chart':
      return <>{renderChart?.() || <div className="text-gray-500 p-8 text-center">Bar chart view not available</div>}</>;
    case 'line':
      return <>{renderLine?.() || <div className="text-gray-500 p-8 text-center">Line graph view not available</div>}</>;
    case 'table':
      return <>{renderTable?.() || <div className="text-gray-500 p-8 text-center">Table view not available</div>}</>;
    case 'cards':
      return <>{renderCards?.() || <div className="text-gray-500 p-8 text-center">Card view not available</div>}</>;
    case 'pie':
      return <>{renderPie?.() || <div className="text-gray-500 p-8 text-center">Pie chart view not available</div>}</>;
    case 'area':
      return <>{renderArea?.() || <div className="text-gray-500 p-8 text-center">Area chart view not available</div>}</>;
    default:
      return <>{renderChart?.()}</>;
  }
};
