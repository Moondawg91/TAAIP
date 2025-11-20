import React from 'react';
import { Clock, ChevronRight } from 'lucide-react';

interface QuickReferenceProps {
  onNavigate: (tab: string) => void;
  recentTabs?: Array<{ id: string; label: string; timestamp: Date }>;
}

export const QuickReference: React.FC<QuickReferenceProps> = ({ onNavigate, recentTabs = [] }) => {
  // Default recent tabs if none provided
  const defaultRecent = [
    { id: 'funnel', label: 'Recruiting Funnel', timestamp: new Date() },
    { id: 'analytics', label: 'Analytics Dashboard', timestamp: new Date() },
    { id: 'leads', label: 'Lead Status Report', timestamp: new Date() },
  ];

  const recent = recentTabs.length > 0 ? recentTabs : defaultRecent;

  return (
    <div className="bg-white rounded-lg shadow-md border-2 border-gray-200 mb-6">
      <div className="px-4 py-3 bg-gray-100 border-b-2 border-gray-200 flex items-center gap-2">
        <Clock className="w-5 h-5 text-gray-700" />
        <span className="font-bold text-sm uppercase tracking-wider text-gray-800">Quick Reference</span>
      </div>
      <div className="p-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {recent.slice(0, 3).map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-yellow-50 hover:border-yellow-500 border-2 border-gray-200 transition-all group"
            >
              <span className="text-sm font-medium text-gray-800 group-hover:text-gray-900">
                {item.label}
              </span>
              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-yellow-600 transition-colors" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
