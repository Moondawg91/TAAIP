import React, { useState, lazy, Suspense } from 'react';
import { 
  Home, Shield, Activity, LineChart, Globe, Target, Clipboard, 
  Briefcase, FileCheck, Map, Menu, ChevronDown, FolderOpen, DollarSign, Users
} from 'lucide-react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { HomeScreen } from './components/HomeScreen';

// Lazy load dashboard components for code splitting
const TalentAcquisitionTechnicianDashboard = lazy(() => import('./components/TalentAcquisitionTechnicianDashboard').then(m => ({ default: m.TalentAcquisitionTechnicianDashboard })));
const RecruitingFunnelDashboard = lazy(() => import('./components/RecruitingFunnelDashboard').then(m => ({ default: m.RecruitingFunnelDashboard })));
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard').then(m => ({ default: m.AnalyticsDashboard })));
const MarketPotentialDashboard = lazy(() => import('./components/MarketPotentialDashboard'));
const MissionAnalysisDashboard = lazy(() => import('./components/MissionAnalysisDashboard'));
const TargetingDecisionBoard = lazy(() => import('./components/TargetingDecisionBoard').then(m => ({ default: m.TargetingDecisionBoard })));
const ProjectManagement = lazy(() => import('./components/ProjectManagement').then(m => ({ default: m.ProjectManagement })));
const LeadStatusReport = lazy(() => import('./components/LeadStatusReport').then(m => ({ default: m.LeadStatusReport })));
const EventPerformanceDashboard = lazy(() => import('./components/EventPerformanceDashboard').then(m => ({ default: m.EventPerformanceDashboard })));
const G2ZonePerformanceDashboard = lazy(() => import('./components/G2ZonePerformanceDashboard').then(m => ({ default: m.G2ZonePerformanceDashboard })));
const CalendarSchedulerDashboard = lazy(() => import('./components/CalendarSchedulerDashboard').then(m => ({ default: m.CalendarSchedulerDashboard })));
const SharePointIntegration = lazy(() => import('./components/SharePointIntegration').then(m => ({ default: m.SharePointIntegration })));
const BudgetTracker = lazy(() => import('./components/BudgetTracker').then(m => ({ default: m.BudgetTracker })));
const TargetingWorkingGroup = lazy(() => import('./components/TargetingWorkingGroup').then(m => ({ default: m.TargetingWorkingGroup })));
const FusionTeamDashboard = lazy(() => import('./components/FusionTeamDashboard'));
const MarketSegmentationDashboard = lazy(() => import('./components/MarketSegmentationDashboard'));
const TargetingMethodologyGuide = lazy(() => import('./components/TargetingMethodologyGuide'));
const QuarterAssessment = lazy(() => import('./components/QuarterAssessment'));
const AssetRecommendationEngine = lazy(() => import('./components/AssetRecommendationEngine'));
const HistoricalDataArchive = lazy(() => import('./components/HistoricalDataArchive'));
const PowerBIBundle = lazy(() => import('./components/PowerBIEmbed').then(m => ({ default: m.PowerBIBundle })));
const UserManagement = lazy(() => import('./components/UserManagement'));
const AdminConsole = lazy(() => import('./components/AdminConsole'));
const MarketingEngagementDashboard = lazy(() => import('./components/MarketingEngagementDashboard'));
const UniversalDataUpload = lazy(() => import('./components/UniversalDataUpload'));
const DataUploadManager = lazy(() => import('./components/DataUploadManager'));
const AdminQuery = lazy(() => import('./components/AdminQuery'));

// TAAIP - Talent Acquisition AI Platform
// Optimized for 420T Talent Acquisition Technicians

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | '420t' | 'funnel' | 'analytics' | 'market' | 'mission' | 'targeting' | 'projects' | 'leads' | 'events' | 'g2zones' | 'calendar' | 'sharepoint' | 'budget' | 'twg' | 'fusion' | 'segmentation' | 'methodology' | 'universal-upload' | 'data-manager' | 'quarter-assessment' | 'asset-recommend' | 'historical' | 'user-management' | 'powerbi' | 'marketing-engagement' | 'admin-console' | 'admin-query'>('home');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const menuCategories = [
    {
      name: 'Home',
      items: [
        { id: 'home', label: 'Home', icon: <Home className="w-5 h-5" />, category: 'Home' },
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
        { id: 'methodology', label: 'USAREC Targeting Methodology', icon: <Clipboard className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'asset-recommend', label: 'Asset Recommendations', icon: <Target className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'targeting', label: 'Targeting Board', icon: <Clipboard className="w-5 h-5" />, category: 'Mission Planning' },
        { id: 'twg', label: 'Targeting Working Group', icon: <Users className="w-5 h-5" />, category: 'Mission Planning' },
      ]
    },
    {
      name: 'Performance Tracking',
      items: [
        { id: 'quarter-assessment', label: 'Quarter Assessment', icon: <FileCheck className="w-5 h-5" />, category: 'Performance' },
        { id: 'leads', label: 'Lead Status', icon: <FileCheck className="w-5 h-5" />, category: 'Performance' },
        { id: 'events', label: 'Event Performance', icon: <Activity className="w-5 h-5" />, category: 'Performance' },
        { id: 'marketing-engagement', label: 'Marketing Engagement', icon: <Target className="w-5 h-5" />, category: 'Performance' },
        { id: 'g2zones', label: 'G2 Zone Analysis', icon: <Map className="w-5 h-5" />, category: 'Performance' },
        { id: 'historical', label: 'Historical Archive', icon: <FileCheck className="w-5 h-5" />, category: 'Performance' },
      ]
    },
    {
      name: 'Operations',
      items: [
        { id: 'calendar', label: 'Calendar & Scheduler', icon: <Clipboard className="w-5 h-5" />, category: 'Operations' },
        { id: 'market', label: 'Market Potential', icon: <Globe className="w-5 h-5" />, category: 'Operations' },
        { id: 'projects', label: 'Projects', icon: <Briefcase className="w-5 h-5" />, category: 'Operations' },
        { id: 'sharepoint', label: 'SharePoint Files', icon: <FolderOpen className="w-5 h-5" />, category: 'Operations' },
        { id: 'budget', label: 'Budget Tracker', icon: <DollarSign className="w-5 h-5" />, category: 'Operations' },
        { id: 'universal-upload', label: 'Data Upload', icon: <FileCheck className="w-5 h-5" />, category: 'Operations' },
        { id: 'data-manager', label: 'Upload Manager', icon: <FileCheck className="w-5 h-5" />, category: 'Operations' },
        { id: 'powerbi', label: 'Power BI (GCC)', icon: <LineChart className="w-5 h-5" />, category: 'Operations' },
      ]
    },
    {
      name: 'Administration',
      items: [
        { id: 'user-management', label: 'User Management', icon: <Users className="w-5 h-5" />, category: 'Administration' },
        { id: 'admin-console', label: 'Admin Console', icon: <FileCheck className="w-5 h-5" />, category: 'Administration' },
        { id: 'admin-query', label: 'DB Query', icon: <FileCheck className="w-5 h-5" />, category: 'Administration' },
      ]
    }
  ];

  const menuItems = menuCategories.flatMap(cat => cat.items);

  const currentMenuItem = menuItems.find(item => item.id === activeTab) || menuItems[0];

  const handleMenuItemClick = (tabId: string) => {
    setActiveTab(tabId as any);
    setDropdownOpen(false); // Always close dropdown when switching tabs
  };

  // Close dropdown when clicking outside or switching tabs
  React.useEffect(() => {
    if (dropdownOpen) {
      const handleClickOutside = (e: MouseEvent) => {
        const target = e.target as HTMLElement;
        if (!target.closest('.dropdown-menu') && !target.closest('.dropdown-button')) {
          setDropdownOpen(false);
        }
      };
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [dropdownOpen]);

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
                className="dropdown-button flex items-center gap-2 px-4 py-2 bg-gray-800 text-yellow-500 rounded hover:bg-gray-700"
              >
                <Menu className="w-5 h-5" />
                <span className="uppercase tracking-wide">{currentMenuItem.label}</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {dropdownOpen && (
                <div className="dropdown-menu absolute right-0 mt-2 w-72 bg-gray-900 border-2 border-yellow-500 rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto">
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
        <ErrorBoundary>
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
                <p className="mt-4 text-gray-600">Loading dashboard...</p>
              </div>
            </div>
          }>
          {activeTab === 'home' ? <HomeScreen onNavigate={(tab) => setActiveTab(tab as any)} /> :
           activeTab === '420t' ? <TalentAcquisitionTechnicianDashboard /> :
           activeTab === 'funnel' ? <RecruitingFunnelDashboard /> :
           activeTab === 'analytics' ? <AnalyticsDashboard /> :
           activeTab === 'market' ? <MarketPotentialDashboard /> :
           activeTab === 'mission' ? <MissionAnalysisDashboard /> :
           activeTab === 'targeting' ? <TargetingDecisionBoard /> :
           activeTab === 'quarter-assessment' ? <QuarterAssessment /> :
           activeTab === 'asset-recommend' ? <AssetRecommendationEngine /> :
           activeTab === 'historical' ? <HistoricalDataArchive /> :
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
           activeTab === 'universal-upload' ? <UniversalDataUpload /> :
           activeTab === 'data-manager' ? <DataUploadManager /> :
           activeTab === 'admin-query' ? <AdminQuery /> :
           activeTab === 'powerbi' ? (
             <PowerBIBundle reportIds={[
               '898af0e0-6d0c-47a6-b4ff-7690661eacda',
               '2b602aa2-5e21-47eb-b432-3709109af45e',
               'a37d11af-4b1a-42ad-923e-925a9e255fc8',
               '2d52ba6b-91f0-4a09-8e78-234b9e22a508',
               'a9cd9722-3f83-4c53-a9c6-8534a4b79b0f'
             ]} />
           ) :
           activeTab === 'marketing-engagement' ? <MarketingEngagementDashboard /> :
           activeTab === 'admin-console' ? <AdminConsole /> :
           activeTab === 'user-management' ? <UserManagement currentUser={{
             user_id: 'current-user',
             username: 'admin',
             email: 'admin@army.mil',
             position: '420T',
             unit_id: 'bn-houston',
             role: {
               role_id: 'tier-3-admin',
               role_name: '420T System Administrator',
               tier: 'tier-3-admin',
               permissions: ['manage_users', 'assign_roles', 'delegate_permissions', 'view_all_dashboards', 'edit_data', 'approve_events'],
               description: '420T Admin'
             },
             created_at: '2025-01-01',
             is_active: true
           }} /> :
           <HomeScreen onNavigate={(tab) => setActiveTab(tab as any)} />}
          </Suspense>
        </ErrorBoundary>
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

