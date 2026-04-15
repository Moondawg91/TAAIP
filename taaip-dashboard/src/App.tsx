import React, { useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  ChevronDown,
  ClipboardList,
  Home,
  LineChart,
  Menu,
  PanelLeft,
  Shield,
  Users,
  Workflow,
} from 'lucide-react';

import { ErrorBoundary } from './components/ErrorBoundary';
import { HomeScreen } from './components/HomeScreen';
import CommandCenterDashboard from './components/CommandCenterDashboard';
import MissionAdjustmentDashboard from './components/MissionAdjustmentDashboard';
import { CommanderDiagnosticsDashboard } from './components/CommanderDiagnosticsDashboard';
import { TargetingWorkingGroup } from './components/TargetingWorkingGroup';
import { ExecutionWorkflowDashboard } from './components/ExecutionWorkflowDashboard';
import { PowerBIBundle } from './components/PowerBIEmbed';
import { AdminConsole } from './components/AdminConsole';

type TabId =
  | 'home'
  | 'command-center'
  | 'mission-adjustment'
  | 'diagnostics'
  | 'decision-sync'
  | 'execution'
  | 'powerbi'
  | 'admin-console';

type UserPerspective = 'commander' | 'operator420t' | 'admin';

const PERSPECTIVE_STORAGE_KEY = 'taaip_perspective';

export const PERSPECTIVE_TAB_ACCESS: Record<UserPerspective, TabId[]> = {
  commander: [
    'home',
    'command-center',
    'mission-adjustment',
    'diagnostics',
    'decision-sync',
    'execution',
    'powerbi',
  ],
  operator420t: ['home', 'command-center', 'diagnostics', 'decision-sync', 'execution', 'powerbi'],
  admin: [
    'home',
    'command-center',
    'mission-adjustment',
    'diagnostics',
    'decision-sync',
    'execution',
    'powerbi',
    'admin-console',
  ],
};

function normalizePerspective(value: string | null | undefined): UserPerspective {
  const raw = (value || '').trim().toLowerCase();
  if (raw === 'admin' || raw === 'maintainer' || raw === 'system_admin') {
    return 'admin';
  }
  if (raw === '420t' || raw === 'operator' || raw === 'operator420t' || raw === '420t_admin') {
    return 'operator420t';
  }
  return 'commander';
}

function resolvePerspective(): UserPerspective {
  if (typeof window === 'undefined') {
    return 'commander';
  }
  const queryPerspective = normalizePerspective(new URLSearchParams(window.location.search).get('role'));
  const storedPerspective = normalizePerspective(window.localStorage.getItem(PERSPECTIVE_STORAGE_KEY));

  const perspective = queryPerspective !== 'commander' || window.location.search.includes('role=')
    ? queryPerspective
    : storedPerspective;

  window.localStorage.setItem(PERSPECTIVE_STORAGE_KEY, perspective);
  return perspective;
}

function perspectiveLabel(perspective: UserPerspective): string {
  switch (perspective) {
    case 'admin':
      return 'Admin / Maintainer';
    case 'operator420t':
      return '420T Operator';
    case 'commander':
    default:
      return 'Commander / Command Team';
  }
}

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('home');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [perspective] = useState<UserPerspective>(() => resolvePerspective());

  const menuCategories = useMemo(
    () => {
      const allowedTabs = new Set(PERSPECTIVE_TAB_ACCESS[perspective]);
      const categories = [
      {
        name: 'Commander Workflow',
        items: [
          { id: 'home' as TabId, label: 'Workflow Home', icon: <Home className="h-5 w-5" /> },
          { id: 'command-center' as TabId, label: 'Command Center', icon: <PanelLeft className="h-5 w-5" /> },
          { id: 'mission-adjustment' as TabId, label: 'Mission Adjustment', icon: <ClipboardList className="h-5 w-5" /> },
          { id: 'diagnostics' as TabId, label: 'Market to ROI Diagnostics', icon: <BarChart3 className="h-5 w-5" /> },
          { id: 'decision-sync' as TabId, label: 'TWG and Targeting Board', icon: <Users className="h-5 w-5" /> },
          { id: 'execution' as TabId, label: 'Asset, Execution, Processing', icon: <Workflow className="h-5 w-5" /> },
        ],
      },
      {
        name: 'Support Views',
        items: [
          { id: 'powerbi' as TabId, label: 'Power BI', icon: <LineChart className="h-5 w-5" /> },
          { id: 'admin-console' as TabId, label: 'Admin Console', icon: <Shield className="h-5 w-5" /> },
        ],
      },
      ];

      return categories
        .map((category) => ({
          ...category,
          items: category.items.filter((item) => allowedTabs.has(item.id)),
        }))
        .filter((category) => category.items.length > 0);
    },
    [perspective],
  );

  const menuItems = menuCategories.flatMap((category) => category.items);
  const currentMenuItem = menuItems.find((item) => item.id === activeTab) || menuItems[0];

  useEffect(() => {
    if (!menuItems.some((item) => item.id === activeTab) && menuItems.length > 0) {
      setActiveTab(menuItems[0].id);
    }
  }, [activeTab, menuItems]);

  useEffect(() => {
    if (!dropdownOpen) {
      return;
    }
    const onDocumentClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.dropdown-menu') && !target.closest('.dropdown-button')) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('click', onDocumentClick);
    return () => document.removeEventListener('click', onDocumentClick);
  }, [dropdownOpen]);

  const renderActiveView = () => {
    switch (activeTab) {
      case 'command-center':
        return <CommandCenterDashboard onNavigate={(tab) => setActiveTab(tab as TabId)} />;
      case 'mission-adjustment':
        return <MissionAdjustmentDashboard onNavigate={(tab) => setActiveTab(tab as TabId)} />;
      case 'diagnostics':
        return <CommanderDiagnosticsDashboard onNavigate={(tab) => setActiveTab(tab as TabId)} />;
      case 'decision-sync':
        return <TargetingWorkingGroup onNavigate={(tab) => setActiveTab(tab as TabId)} />;
      case 'execution':
        return <ExecutionWorkflowDashboard onNavigate={(tab) => setActiveTab(tab as TabId)} />;
      case 'powerbi':
        return (
          <PowerBIBundle
            reportIds={[
              '898af0e0-6d0c-47a6-b4ff-7690661eacda',
              '2b602aa2-5e21-47eb-b432-3709109af45e',
              'a37d11af-4b1a-42ad-923e-925a9e255fc8',
            ]}
          />
        );
      case 'admin-console':
        return <AdminConsole />;
      case 'home':
      default:
        return (
          <HomeScreen
            perspective={perspective}
            allowedTabs={PERSPECTIVE_TAB_ACCESS[perspective]}
            onNavigate={(tab) => setActiveTab(tab as TabId)}
          />
        );
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      <header className="w-full border-b-4 border-amber-500 bg-gradient-to-r from-black via-slate-900 to-black shadow-2xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-4">
            <Shield className="h-12 w-12 text-amber-400" />
            <div>
              <h1 className="text-3xl font-bold uppercase tracking-wider text-amber-400">TAAIP</h1>
              <p className="text-sm uppercase tracking-wide text-slate-300">
                Commander Decision Support Workflow
              </p>
              <p className="text-xs uppercase tracking-wide text-amber-300">
                Perspective: {perspectiveLabel(perspective)}
              </p>
            </div>
          </div>

          <div className="relative">
            <button
              onClick={() => setDropdownOpen((current) => !current)}
              className="dropdown-button flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-amber-400 hover:bg-slate-700"
            >
              <Menu className="h-5 w-5" />
              <span className="uppercase tracking-wide">{currentMenuItem.label}</span>
              <ChevronDown className="h-4 w-4" />
            </button>

            {dropdownOpen && (
              <div className="dropdown-menu absolute right-0 z-50 mt-2 max-h-96 w-80 overflow-y-auto rounded-lg border-2 border-amber-500 bg-slate-900 shadow-2xl">
                {menuCategories.map((category) => (
                  <div key={category.name} className="border-b border-slate-700 last:border-b-0">
                    <div className="bg-slate-800 px-4 py-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                      {category.name}
                    </div>
                    {category.items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveTab(item.id);
                          setDropdownOpen(false);
                        }}
                        className={`flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors ${
                          activeTab === item.id
                            ? 'bg-amber-500 font-bold text-black'
                            : 'text-slate-200 hover:bg-slate-800 hover:text-amber-300'
                        }`}
                      >
                        {item.icon}
                        <span>{item.label}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex-1 w-full max-w-7xl px-4 py-6">
        <ErrorBoundary>
          {renderActiveView()}
        </ErrorBoundary>
      </main>

      <footer className="mt-6 w-full border-t-2 border-amber-500 bg-black py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 text-xs">
          <span className="text-slate-400">TAAIP v2.0 | Connected commander workflow</span>
          <span className="font-bold uppercase tracking-wider text-amber-400">Operational use only</span>
        </div>
      </footer>
    </div>
  );
};

export default App;

