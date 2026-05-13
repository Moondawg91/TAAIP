import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Award, AlertCircle } from 'lucide-react';

interface FlashItem {
  id: string;
  title: string;
  body: string;
  category: string;
  source?: string;
  effective_date?: string;
  created_at: string;
}

const STATIC_FALLBACK: FlashItem[] = [
  { id: 'f1', title: 'System Ready', body: 'TAAIP operational — connect to backend for live flash updates.', category: 'INFO', created_at: '' },
];

const categoryIcon = (cat: string) => {
  switch ((cat || '').toUpperCase()) {
    case 'MUST_KNOW': return <AlertCircle className="w-4 h-4 text-red-400" />;
    case 'ACHIEVEMENT': return <Award className="w-4 h-4 text-yellow-500" />;
    case 'TREND': return <TrendingUp className="w-4 h-4 text-green-400" />;
    default: return <Activity className="w-4 h-4 text-blue-400" />;
  }
};

export const LiveUpdatesBanner: React.FC = () => {
  const [items, setItems] = useState<FlashItem[]>(STATIC_FALLBACK);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    fetch('/api/home/flash')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.items?.length) setItems(data.items);
      })
      .catch(() => { /* keep static fallback */ });
  }, []);

  useEffect(() => {
    if (items.length <= 1) return;
    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % items.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [items.length]);

  const current = items[currentIndex];

  return (
    <div className="bg-gradient-to-r from-gray-800 via-gray-900 to-gray-800 border-t-2 border-b-2 border-yellow-500 py-3 px-6 shadow-lg">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 overflow-hidden">
          <div className="flex items-center gap-2 bg-gray-700 px-3 py-1 rounded-lg flex-shrink-0">
            <Activity className="w-4 h-4 text-yellow-500 animate-pulse" />
            <span className="text-yellow-500 font-bold text-sm uppercase tracking-wider">Flash</span>
          </div>
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {categoryIcon(current.category)}
            <span className="text-white text-sm font-semibold truncate">{current.title}</span>
            {current.body && <span className="text-gray-300 text-sm truncate hidden md:block">— {current.body}</span>}
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0 ml-4">
          {items.map((_, idx) => (
            <div key={idx} className={`h-2 rounded-full transition-all ${idx === currentIndex ? 'bg-yellow-500 w-4' : 'bg-gray-600 w-2'}`} />
          ))}
        </div>
      </div>
    </div>
  );
};
