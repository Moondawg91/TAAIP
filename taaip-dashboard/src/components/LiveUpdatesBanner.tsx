import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Users, Award } from 'lucide-react';

interface Update {
  id: number;
  type: 'enlistment' | 'lead' | 'event' | 'achievement';
  message: string;
  timestamp: Date;
}

export const LiveUpdatesBanner: React.FC = () => {
  const [updates, setUpdates] = useState<Update[]>([
    { id: 1, type: 'enlistment', message: 'Alpha Company - New contract signed: 11X Infantry', timestamp: new Date() },
    { id: 2, type: 'lead', message: 'Bravo Company - 15 new leads added from campus event', timestamp: new Date() },
    { id: 3, type: 'achievement', message: 'Charlie Company reached 95% mission attainment', timestamp: new Date() },
    { id: 4, type: 'event', message: 'Upcoming: Military Appreciation Day - Fort Liberty', timestamp: new Date() },
  ]);
  
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % updates.length);
    }, 5000); // Change every 5 seconds

    return () => clearInterval(interval);
  }, [updates.length]);

  const getIcon = (type: Update['type']) => {
    switch (type) {
      case 'enlistment':
        return <Award className="w-4 h-4 text-green-500" />;
      case 'lead':
        return <Users className="w-4 h-4 text-blue-500" />;
      case 'event':
        return <Activity className="w-4 h-4 text-purple-500" />;
      case 'achievement':
        return <TrendingUp className="w-4 h-4 text-yellow-500" />;
    }
  };

  const currentUpdate = updates[currentIndex];

  return (
    <div className="bg-gradient-to-r from-gray-800 via-gray-900 to-gray-800 border-t-2 border-b-2 border-yellow-500 py-3 px-6 shadow-lg">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 overflow-hidden">
          <div className="flex items-center gap-2 bg-gray-700 px-3 py-1 rounded-lg">
            <Activity className="w-4 h-4 text-yellow-500 animate-pulse" />
            <span className="text-yellow-500 font-bold text-sm uppercase tracking-wider">Live Updates</span>
          </div>
          
          <div className="flex items-center gap-3 flex-1 animate-fade-in">
            {getIcon(currentUpdate.type)}
            <span className="text-white text-sm font-medium">{currentUpdate.message}</span>
          </div>
        </div>
        
        <div className="flex gap-2">
          {updates.map((_, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full transition-all ${
                idx === currentIndex ? 'bg-yellow-500 w-4' : 'bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
