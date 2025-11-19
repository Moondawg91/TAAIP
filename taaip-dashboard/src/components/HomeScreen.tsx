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
        {/* Top Controls Row */}
        <div className="mb-6 flex gap-3">
          {/* Mission Dashboards Dropdown */}
          <button
            onClick={() => setShowMissionMenu(!showMissionMenu)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-yellow-500 rounded-lg hover:bg-gray-700 transition-colors border border-yellow-500"
          >
            <Clipboard className="w-4 h-4" />
            <span className="font-semibold uppercase text-sm">Mission Dashboards</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${showMissionMenu ? 'rotate-90' : ''}`} />
          </button>

          {/* Resources Dropdown */}
          <button
            onClick={() => setShowResources(!showResources)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-yellow-500 rounded-lg hover:bg-gray-700 transition-colors border border-yellow-500"
          >
            <BookOpen className="w-4 h-4" />
            <span className="font-semibold uppercase text-sm">Resources</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${showResources ? 'rotate-90' : ''}`} />
          </button>

          {/* Help Desk Dropdown */}
          <button
            onClick={() => setShowHelpDesk(!showHelpDesk)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-yellow-500 rounded-lg hover:bg-gray-700 transition-colors border border-yellow-500"
          >
            <Shield className="w-4 h-4" />
            <span className="font-semibold uppercase text-sm">Help Desk</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${showHelpDesk ? 'rotate-90' : ''}`} />
          </button>
        </div>
          
        {/* Mission Dashboards Dropdown Content */}
        {showMissionMenu && (
          <div className="mb-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 bg-gray-50 p-4 rounded-lg border border-gray-300">
            {menuItems.flatMap(cat => cat.items).map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onNavigate(item.id);
                  setShowMissionMenu(false);
                }}
                className="flex items-center gap-2 p-2 bg-white border border-gray-300 rounded hover:border-yellow-500 hover:bg-yellow-50 transition-all text-left text-sm"
                title={item.description}
              >
                <div className="text-gray-700">{item.icon}</div>
                <span className="font-medium text-gray-800">{item.title}</span>
              </button>
            ))}
          </div>
        )}

        {/* Resources Dropdown Content */}
        {showResources && (
          <div className="mb-6 bg-white p-4 rounded-lg border-2 border-gray-300 shadow">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
              <a href="/docs/420t-quick-start.pdf" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="Complete guide for Talent Acquisition Technicians">
                <FileCheck className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">420T Quick Start</span>
              </a>
              <a href="/docs/recruiting-ops-manual.pdf" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="SOPs and best practices">
                <FileCheck className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Recruiting Ops Manual</span>
              </a>
              <a href="https://training.taaip.army.mil/videos" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="Video tutorials on using TAAIP">
                <Activity className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Platform Training</span>
              </a>
              <a href="/docs/mission-analysis-guide.pdf" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="M-IPOE framework and targeting">
                <Target className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Mission Analysis</span>
              </a>
              <a href="/docs/access-control-policy.pdf" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="User roles and permissions">
                <Shield className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Access Policy</span>
              </a>
              <a href="/templates/data-entry-templates.zip" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="Excel and CSV templates">
                <Database className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Data Templates</span>
              </a>
              <a href="/docs/leadership-guide.pdf" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="Analytics for leadership">
                <Users className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Leadership Guide</span>
              </a>
              <a href="https://recruiting.army.mil" className="flex items-center gap-3 p-3 bg-gray-50 rounded hover:bg-yellow-50 hover:border-yellow-500 border border-gray-200 transition-colors" title="External Army resources" target="_blank" rel="noopener noreferrer">
                <Globe className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">Army Portal</span>
              </a>
            </div>
          </div>
        )}

        {/* Help Desk Dropdown Content */}
        {showHelpDesk && (
          <div className="mb-6 bg-white p-4 rounded-lg border-2 border-gray-300 shadow">
            <p className="text-xs text-gray-600 mb-3">Submit requests for support, access, or features</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Request access level upgrade"
              >
                <Shield className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Access Request</span>
              </button>
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Suggest new features"
              >
                <TrendingUp className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Feature Request</span>
              </button>
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Request system upgrades"
              >
                <Activity className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Upgrade Request</span>
              </button>
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Report technical issues"
              >
                <AlertCircle className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Bug Report</span>
              </button>
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Request training"
              >
                <Users className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Training Request</span>
              </button>
              <button
                onClick={() => onNavigate('helpdesk')}
                className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded hover:bg-yellow-50 hover:border-yellow-500 transition-colors text-left"
                title="Other support"
              >
                <HelpCircle className="w-4 h-4 text-gray-700 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900">Other Support</span>
              </button>
            </div>
          </div>
        )}

        {/* Centered Company Standings Leaderboard */}
        <div className="max-w-5xl mx-auto">
          <CompanyStandingsLeaderboard />
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
