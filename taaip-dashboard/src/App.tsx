import React, { useState } from 'react';
import { 
  Home, Shield, Activity, LineChart, Globe, Target, Clipboard, 
  Briefcase, FileCheck, Map, Menu, ChevronDown, FolderOpen, DollarSign, Users
} from 'lucide-react';
import { HomeScreen } from './components/HomeScreen';
import { TalentAcquisitionTechnicianDashboard } from './components/TalentAcquisitionTechnicianDashboard';
import { RecruitingFunnelDashboard } from './components/RecruitingFunnelDashboard';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import MarketPotentialDashboard from './components/MarketPotentialDashboard';
import MissionAnalysisDashboard from './components/MissionAnalysisDashboard';
import { TargetingDecisionBoard } from './components/TargetingDecisionBoard';
import { ProjectManagement } from './components/ProjectManagement';
import { LeadStatusReport } from './components/LeadStatusReport';
import { EventPerformanceDashboard } from './components/EventPerformanceDashboard';
import { G2ZonePerformanceDashboard } from './components/G2ZonePerformanceDashboard';
import { CalendarSchedulerDashboard } from './components/CalendarSchedulerDashboard';
import { SharePointIntegration } from './components/SharePointIntegration';
import { BudgetTracker } from './components/BudgetTracker';
import { TargetingWorkingGroup } from './components/TargetingWorkingGroup';
import FusionTeamDashboard from './components/FusionTeamDashboard';
import MarketSegmentationDashboard from './components/MarketSegmentationDashboard';
import TargetingMethodologyGuide from './components/TargetingMethodologyGuide';
import { BulkDataUpload } from './components/BulkDataUpload';
import { DynamicDashboard } from './components/DynamicDashboard';

// TAAIP - Talent Acquisition AI Platform
// Optimized for 420T Talent Acquisition Technicians

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | '420t' | 'funnel' | 'analytics' | 'market' | 'mission' | 'targeting' | 'projects' | 'leads' | 'events' | 'g2zones' | 'calendar' | 'sharepoint' | 'budget' | 'twg' | 'fusion' | 'segmentation' | 'methodology' | 'upload' | 'dynamic'>('home');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const menuCategories = [
    {
      name: 'Home',
      items: [
        { id: 'home', label: 'Home Dashboard', icon: <Home className="w-5 h-5" />, category: 'Home' },
      ]
    },
    {
      name: '420T Core Functions',
      items: [
        { id: '420t', label: '420T Command Center', icon: <Shield className="w-5 h-5" />, category: '420T Core' },
        { id: 'funnel', label: 'Recruiting Funnel', icon: <Activity className="w-5 h-5" />, category: '420T Core' },
        { id: 'analytics', label: 'Analytics & Insights', icon: <LineChart className="w-5 h-5" />, category: '420T Core' },
        { id: 'segmentation', label: 'Market Segmentation', icon: <Target className="w-5 h-5" />, category: '420T Core' },
      ]
    },
    {
      name: 'Mission Planning',
      items: [
        { id: 'fusion', label: 'Fusion Team Operations', icon: <Users className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'mission', label: 'Mission Analysis (M-IPOE)', icon: <Target className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'methodology', label: 'Targeting Methodology (D3AE/F3A)', icon: <Clipboard className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'targeting', label: 'Targeting Board', icon: <Clipboard className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'twg', label: 'Targeting Working Group', icon: <Users className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'projects', label: 'Project Management', icon: <Briefcase className="w-5 h-5" />, category: 'Mission Planning' },
      ]
    },
    {
      name: 'Performance Tracking',
      items: [
        { id: 'leads', label: 'Lead Status', icon: <FileCheck className="w-5 h-5" />, category: 'Performance' },
        { id: 'events', label: 'Event Performance', icon: <Activity className="w-5 h-5" />, category: 'Performance' },
        { id: 'g2zones', label: 'G2 Zone Analysis', icon: <Map className="w-5 h-5" />, category: 'Performance' },
      ]
    },
    {
      name: 'Operations',
      items: [
        { id: 'calendar', label: 'Calendar & Scheduler', icon: <Clipboard className="w-5 h-5" />, category: 'Operations' },
        { id: 'market', label: 'Market Potential', icon: <Globe className="w-5 h-5" />, category: 'Operations' },
        { id: 'sharepoint', label: 'SharePoint Files', icon: <FolderOpen className="w-5 h-5" />, category: 'Operations' },
        { id: 'budget', label: 'Budget Tracker', icon: <DollarSign className="w-5 h-5" />, category: 'Operations' },
        { id: 'upload', label: 'Bulk Data Upload', icon: <FileCheck className="w-5 h-5" />, category: 'Operations' },
        { id: 'dynamic', label: 'Smart Visualizations', icon: <LineChart className="w-5 h-5" />, category: 'Operations' },
      ]
    }
  ];

  const menuItems = menuCategories.flatMap(cat => cat.items);

  const currentMenuItem = menuItems.find(item => item.id === activeTab) || menuItems[0];

  const handleMenuItemClick = (tabId: string) => {
    setActiveTab(tabId as any);
    setDropdownOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      {/* Header */}
      <header className="w-full bg-gradient-to-r from-black via-gray-900 to-black border-b-4 border-yellow-500 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-12 h-12 text-yellow-500" />
              <div>
                <h1 className="text-3xl font-bold text-yellow-500 uppercase tracking-wider">TAAIP</h1>
                <p className="text-sm text-gray-400 uppercase tracking-wide">Talent Acquisition Analytics and Intelligence Platform</p>
              </div>
            </div>
            
            {/* Dropdown Navigation (Desktop & Mobile) */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-yellow-500 rounded hover:bg-gray-700"
              >
                <Menu className="w-5 h-5" />
                <span className="uppercase tracking-wide">{currentMenuItem.label}</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-72 bg-gray-900 border-2 border-yellow-500 rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto">
                  {menuCategories.map((category) => (
                    <div key={category.name} className="border-b border-gray-700 last:border-b-0">
                      <div className="px-4 py-2 bg-gray-800 text-yellow-500 font-bold text-xs uppercase tracking-wider">
                        {category.name}
                      </div>
                      {category.items.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleMenuItemClick(item.id)}
                          className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                            activeTab === item.id
                              ? 'bg-yellow-500 text-black font-bold'
                              : 'text-gray-300 hover:bg-gray-800 hover:text-yellow-500'
                          }`}
                        >
                          {item.icon}
                          <span className="text-sm">{item.label}</span>
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'home' ? <HomeScreen onNavigate={(tab) => setActiveTab(tab as any)} /> :
         activeTab === '420t' ? <TalentAcquisitionTechnicianDashboard /> :
         activeTab === 'funnel' ? <RecruitingFunnelDashboard /> :
         activeTab === 'analytics' ? <AnalyticsDashboard /> :
         activeTab === 'market' ? <MarketPotentialDashboard /> :
         activeTab === 'mission' ? <MissionAnalysisDashboard /> :
         activeTab === 'targeting' ? <TargetingDecisionBoard /> :
         activeTab === 'projects' ? <ProjectManagement /> :
         activeTab === 'leads' ? <LeadStatusReport /> :
         activeTab === 'events' ? <EventPerformanceDashboard /> :
         activeTab === 'g2zones' ? <G2ZonePerformanceDashboard /> :
         activeTab === 'calendar' ? <CalendarSchedulerDashboard /> :
         activeTab === 'sharepoint' ? <SharePointIntegration /> :
         activeTab === 'budget' ? <BudgetTracker /> :
         activeTab === 'twg' ? <TargetingWorkingGroup /> :
         activeTab === 'fusion' ? <FusionTeamDashboard /> :
         activeTab === 'segmentation' ? <MarketSegmentationDashboard /> :
         activeTab === 'methodology' ? <TargetingMethodologyGuide /> :
         activeTab === 'upload' ? <BulkDataUpload /> :
         activeTab === 'dynamic' ? <DynamicDashboard dataType="events" /> :
         <HomeScreen onNavigate={(tab) => setActiveTab(tab as any)} />}
      </main>

      {/* Footer */}
      <footer className="w-full py-3 mt-6 bg-black border-t-2 border-yellow-500">
        <div className="max-w-7xl mx-auto px-4 flex justify-between items-center text-xs">
          <span className="text-gray-400">TAAIP v2.0 | Talent Acquisition Analytics and Intelligence Platform</span>
          <span className="text-yellow-500 font-bold uppercase tracking-wider">Proprietary System</span>
        </div>
      </footer>
    </div>
  );
};

export default App;

