import React from 'react';
import { Clock, ChevronRight } from 'lucide-react';

interface QuickReferenceProps {
  onNavigate: (tab: string) => void;
  lastVisited?: { id: string; label: string };
}

export const QuickReference: React.FC<QuickReferenceProps> = ({ onNavigate, lastVisited }) => {
  // Default to Analytics Dashboard if no last visited
  const defaultLast = { id: 'analytics', label: 'Analytics Dashboard' };
  const last = lastVisited || defaultLast;

  return (
    <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 p-3">
      <button
        onClick={() => onNavigate(last.id)}
        className="w-full flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-yellow-50 hover:border-yellow-500 border-2 border-gray-200 transition-all group"
      >
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-gray-600 group-hover:text-yellow-600 transition-colors" />
          <div className="text-left">
            <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Last Viewed</div>
            <div className="text-sm font-bold text-gray-800 group-hover:text-gray-900">{last.label}</div>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-yellow-600 transition-colors" />
      </button>
    </div>
  );
};
