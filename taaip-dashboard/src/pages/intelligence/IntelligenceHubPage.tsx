import React, { useState } from 'react';
import { AnalyticsPage } from '../analytics/AnalyticsPage';
import { RecommendationsPage } from '../recommendations/RecommendationsPage';
import { FragoPage } from '../frago/FragoPage';
import { VersionsPage } from '../versions/VersionsPage';
import { ComparePage } from '../compare/ComparePage';
import { HistoryPage } from '../history/HistoryPage';

type IntelligenceTab = 'analytics' | 'recommendations' | 'frago' | 'versions' | 'compare' | 'history';

const tabs: Array<{ id: IntelligenceTab; label: string }> = [
  { id: 'analytics', label: 'Analytics' },
  { id: 'recommendations', label: 'Recommendations' },
  { id: 'frago', label: 'FRAGO' },
  { id: 'versions', label: 'Versions' },
  { id: 'compare', label: 'Compare' },
  { id: 'history', label: 'History' },
];

export const IntelligenceHubPage: React.FC = () => {
  const [tab, setTab] = useState<IntelligenceTab>('analytics');

  return (
    <div className="space-y-4">
      <header className="rounded-lg border border-[#1D3A5C] bg-gradient-to-r from-[#0B223F] to-[#133962] p-4">
        <h2 className="text-lg font-semibold text-white">Intelligence Hub</h2>
        <p className="text-xs text-[#BFDBFE] mt-1">UI-only integration for analytics, recommendations, FRAGO, versions, compare, and archive history using existing backend endpoints.</p>
      </header>

      <div className="flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`rounded px-3 py-1.5 text-xs font-semibold ${tab === item.id ? 'bg-[#1D4ED8] text-white' : 'bg-[#0C2545] text-[#94A3B8] border border-[#1D3A5C]'}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'analytics' && <AnalyticsPage />}
      {tab === 'recommendations' && <RecommendationsPage />}
      {tab === 'frago' && <FragoPage />}
      {tab === 'versions' && <VersionsPage />}
      {tab === 'compare' && <ComparePage />}
      {tab === 'history' && <HistoryPage />}
    </div>
  );
};
