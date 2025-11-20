import React from 'react';
import { 
  BarChart3, TrendingUp, Target, Briefcase, Activity, 
  Globe, Award, FileCheck, Clipboard, Calendar, Map, Users,
  Database, ChevronRight, Shield, BookOpen, AlertCircle, HelpCircle
} from 'lucide-react';
import { CompanyStandingsLeaderboard } from './CompanyStandingsLeaderboard';

interface HomeScreenProps {
  onNavigate: (tab: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  const [showMissionMenu, setShowMissionMenu] = React.useState(false);
  const [showResources, setShowResources] = React.useState(false);
  const [showHelpDesk, setShowHelpDesk] = React.useState(false);
  const [showExpanded, setShowExpanded] = React.useState(false);

  // Close all dropdowns when switching between them
  const handleToggleDropdown = (dropdown: 'mission' | 'resources' | 'helpdesk') => {
    if (dropdown === 'mission') {
      setShowMissionMenu(!showMissionMenu);
      setShowResources(false);
      setShowHelpDesk(false);
    } else if (dropdown === 'resources') {
      setShowResources(!showResources);
      setShowMissionMenu(false);
      setShowHelpDesk(false);
    } else if (dropdown === 'helpdesk') {
      setShowHelpDesk(!showHelpDesk);
      setShowMissionMenu(false);
      setShowResources(false);
    }
  };

  const menuItems = [
    {
      category: 'Core Analytics',
      items: [
        { 
          id: 'funnel', 
          icon: <TrendingUp className="w-8 h-8" />, 
          title: 'Recruiting Funnel', 
          description: 'Track lead progression and conversion rates',
          color: 'from-yellow-600 to-yellow-700'
        },
        { 
          id: 'analytics', 
          icon: <BarChart3 className="w-8 h-8" />, 
          title: 'Analytics Dashboard', 
          description: 'CBSA, schools, segments, and contracts analysis',
          color: 'from-gray-700 to-gray-800'
        },
        { 
          id: 'market', 
          icon: <Map className="w-8 h-8" />, 
          title: 'Market Potential', 
          description: 'Geographic market analysis and prioritization',
          color: 'from-yellow-600 to-yellow-700'
        },
      ]
    },
    {
      category: 'Mission Planning',
      items: [
        { 
          id: 'mission', 
          icon: <Target className="w-8 h-8" />, 
          title: 'Mission Analysis', 
          description: 'Strategic mission planning and M-IPOE framework',
          color: 'from-gray-700 to-gray-800'
        },
        { 
          id: 'twg', 
          icon: <Users className="w-8 h-8" />, 
          title: 'Targeting Decision Board', 
          description: 'TWG decisions and strategic targeting',
          color: 'from-yellow-600 to-yellow-700'
        },
        { 
          id: 'projects', 
          icon: <Briefcase className="w-8 h-8" />, 
          title: 'Project Management', 
          description: 'Event planning, tasks, and milestones',
          color: 'from-gray-700 to-gray-800'
        },
      ]
    },
    {
      category: 'Performance Tracking',
      items: [
        { 
          id: 'leads', 
          icon: <Activity className="w-8 h-8" />, 
          title: 'Lead Status Report', 
          description: 'Real-time lead tracking and status updates',
          color: 'from-yellow-600 to-yellow-700'
        },
        { 
          id: 'events', 
          icon: <Award className="w-8 h-8" />, 
          title: 'Event Performance', 
          description: 'Event metrics, ROI, and effectiveness',
          color: 'from-gray-700 to-gray-800'
        },
        { 
          id: 'g2zones', 
          icon: <Globe className="w-8 h-8" />, 
          title: 'G2 Zone Performance', 
          description: 'Zone-level recruiting performance analysis',
          color: 'from-yellow-600 to-yellow-700'
        },
      ]
    },
    {
      category: 'Operations',
      items: [
        { 
          id: 'calendar', 
          icon: <Calendar className="w-8 h-8" />, 
          title: 'Calendar & Scheduler', 
          description: 'Event scheduling and status reports (EMM)',
          color: 'from-gray-700 to-gray-800'
        },
        { 
          id: 'dod', 
          icon: <FileCheck className="w-8 h-8" />, 
          title: 'DOD Branch Comparison', 
          description: 'Cross-service recruiting comparison',
          color: 'from-yellow-600 to-yellow-700'
        },
        { 
          id: 'dashboard', 
          icon: <Clipboard className="w-8 h-8" />, 
          title: 'Market Segments', 
          description: 'Demographic and psychographic segmentation',
          color: 'from-gray-700 to-gray-800'
        },
        { 
          id: 'input', 
          icon: <Database className="w-8 h-8" />, 
          title: 'Data Input Forms', 
          description: 'Manual data entry and survey collection',
          color: 'from-yellow-600 to-yellow-700'
        },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Hero Section - Vantage Style */}
      <div className="bg-gradient-to-b from-black to-gray-900 text-white py-6 px-8 border-b-2 border-yellow-500 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-10 h-10 text-yellow-500" />
              <div>
                <h1 className="text-3xl font-bold tracking-wide text-yellow-500">TAAIP</h1>
                <p className="text-base text-gray-300 mt-1 font-semibold">Talent Acquisition Analytics & Intelligence Platform</p>
                <p className="text-xs text-gray-400 mt-1">Strategic Decision Support System</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-yellow-500 font-semibold">CLASSIFICATION: UNCLASSIFIED</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-[1600px] mx-auto py-8 px-8">
        {/* Main Grid - Sidebar + Leaderboard */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          {/* Left Sidebar - Quick Access Panels */}
          <div className="lg:col-span-1 space-y-4">
            {/* Resources Panel */}
            <div className="bg-white rounded-lg shadow-md border-2 border-gray-200">
              <button
                onClick={() => handleToggleDropdown('resources')}
                className="w-full px-4 py-3 bg-gray-800 text-yellow-500 rounded-t-lg font-bold text-sm uppercase tracking-wider hover:bg-gray-700 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  Resources
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${showResources ? 'rotate-90' : ''}`} />
              </button>
              {showResources && (
                <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
                  <a href="/docs/420t-quick-start.pdf" className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-sm">
                    <FileCheck className="w-4 h-4 text-gray-700 flex-shrink-0" />
                    <span className="font-medium text-gray-800">420T Quick Start</span>
                  </a>
                  <a href="/docs/recruiting-ops-manual.pdf" className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-sm">
                    <FileCheck className="w-4 h-4 text-gray-700 flex-shrink-0" />
                    <span className="font-medium text-gray-800">Ops Manual</span>
                  </a>
                  <a href="https://training.taaip.army.mil/videos" className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-sm">
                    <Activity className="w-4 h-4 text-gray-700 flex-shrink-0" />
                    <span className="font-medium text-gray-800">Training Videos</span>
                  </a>
                  <a href="/docs/mission-analysis-guide.pdf" className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-sm">
                    <Target className="w-4 h-4 text-gray-700 flex-shrink-0" />
                    <span className="font-medium text-gray-800">Mission Analysis</span>
                  </a>
                  <a href="/templates/data-entry-templates.zip" className="flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-sm">
                    <Database className="w-4 h-4 text-gray-700 flex-shrink-0" />
                    <span className="font-medium text-gray-800">Data Templates</span>
                  </a>
                </div>
              )}
            </div>

            {/* Mission Dashboards Panel */}
            <div className="bg-white rounded-lg shadow-md border-2 border-gray-200">
              <button
                onClick={() => handleToggleDropdown('mission')}
                className="w-full px-4 py-3 bg-gray-800 text-yellow-500 rounded-t-lg font-bold text-sm uppercase tracking-wider hover:bg-gray-700 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Dashboards
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${showMissionMenu ? 'rotate-90' : ''}`} />
              </button>
              {showMissionMenu && (
                <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
                  {[
                    { id: 'funnel', icon: <TrendingUp className="w-4 h-4" />, title: 'Funnel' },
                    { id: 'analytics', icon: <BarChart3 className="w-4 h-4" />, title: 'Analytics' },
                    { id: 'market', icon: <Map className="w-4 h-4" />, title: 'Market' },
                    { id: 'mission', icon: <Target className="w-4 h-4" />, title: 'Mission' },
                    { id: 'twg', icon: <Users className="w-4 h-4" />, title: 'TWG' },
                    { id: 'projects', icon: <Briefcase className="w-4 h-4" />, title: 'Projects' },
                    { id: 'leads', icon: <Activity className="w-4 h-4" />, title: 'Leads' },
                    { id: 'events', icon: <Award className="w-4 h-4" />, title: 'Events' },
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => { onNavigate(item.id); handleToggleDropdown('mission'); }}
                      className="w-full flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-left text-sm"
                    >
                      <div className="text-gray-700">{item.icon}</div>
                      <span className="font-medium text-gray-800">{item.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Help Desk Panel */}
            <div className="bg-white rounded-lg shadow-md border-2 border-gray-200">
              <button
                onClick={() => handleToggleDropdown('helpdesk')}
                className="w-full px-4 py-3 bg-gray-800 text-yellow-500 rounded-t-lg font-bold text-sm uppercase tracking-wider hover:bg-gray-700 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-5 h-5" />
                  Help Desk
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${showHelpDesk ? 'rotate-90' : ''}`} />
              </button>
              {showHelpDesk && (
                <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
                  {[
                    { icon: <Shield className="w-4 h-4" />, title: 'Access Request' },
                    { icon: <TrendingUp className="w-4 h-4" />, title: 'Feature Request' },
                    { icon: <AlertCircle className="w-4 h-4" />, title: 'Bug Report' },
                    { icon: <Users className="w-4 h-4" />, title: 'Training' },
                    { icon: <HelpCircle className="w-4 h-4" />, title: 'Support' },
                  ].map((item) => (
                    <button
                      key={item.title}
                      onClick={() => { onNavigate('helpdesk'); handleToggleDropdown('helpdesk'); }}
                      className="w-full flex items-center gap-2 p-2 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors text-left text-sm"
                    >
                      <div className="text-gray-700">{item.icon}</div>
                      <span className="font-medium text-gray-800">{item.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Side - Leaderboard */}
          <div className="lg:col-span-3">
            <CompanyStandingsLeaderboard showExpanded={showExpanded} setShowExpanded={setShowExpanded} />
          </div>
        </div>

        {/* Dashboard Grid Cards (Below Leaderboard) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {menuItems.flatMap(cat => cat.items).slice(0, 8).map((item) => (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`bg-gradient-to-br ${item.color} text-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-all border-2 border-transparent hover:border-yellow-400 text-left`}
            >
              <div className="flex items-center justify-between mb-3">
                {item.icon}
                <ChevronRight className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg mb-1">{item.title}</h3>
              <p className="text-xs text-gray-200">{item.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-black text-white py-4 px-8 border-t-2 border-yellow-500">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center text-xs">
            <div>
              <p className="text-gray-400">
                TAAIP v2.0 | Talent Acquisition Analytics and Intelligence Platform
              </p>
              <p className="text-gray-500 mt-1">
                Proprietary System • Strategic Decision Support
              </p>
            </div>
            <div className="text-right">
              <p className="text-yellow-500 font-bold uppercase tracking-wider">
                UNCLASSIFIED
              </p>
              <p className="text-gray-500 mt-1">
                FOR OFFICIAL USE ONLY
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
