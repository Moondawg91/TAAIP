import React, { useState } from 'react';
import {
  Home, Globe, Target, Users, LayoutList,
  DollarSign, Zap, Activity, Filter, BarChart3, TrendingUp,
  Database, GraduationCap, Settings, ChevronLeft, ChevronRight,
  Shield, LogOut, User, ChevronDown, BrainCircuit, Building2, Waypoints, School,
} from 'lucide-react';
import { colors, radius, spacing, typography } from '../../theme/tokens';
import { UnitSelector } from './UnitSelector';
import { PeriodSelector } from './PeriodSelector';

export type TabId =
  | 'home-page'
  | 'command-center'
  | 'fusion-cell'
  | 'twg'
  | 'targeting-board'
  | 'operations-page'
  | 'field-activities-page'
  | 'budget-page'
  | 'market-intelligence'
  | 'school-intelligence'
  | 'dod-market-share'
  | 'segmentation'
  | 'reserve-alignment'
  | 'market-potential'
  | 'out-of-area-analysis'
  | 'roi-analysis'
  | 'performance-page'
  | 'funnel-analysis'
  | 'data-document-center'
  | 'training-center'
  | 'admin';

const HOME_ITEM: { id: TabId; label: string; icon: React.ReactNode } = {
  id: 'home-page',
  label: 'Home',
  icon: <Home className="w-4 h-4" />,
};

const NAV_SECTIONS: Array<{
  heading: string;
  items: Array<{ id: TabId; label: string; icon: React.ReactNode }>;
}> = [
  {
    heading: 'Home',
    items: [{ id: 'command-center', label: 'Command Center', icon: <Target className="w-4 h-4" /> }],
  },
  {
    heading: 'Targeting',
    items: [
      { id: 'fusion-cell', label: 'Fusion Cell', icon: <Users className="w-4 h-4" /> },
      { id: 'twg', label: 'TWG', icon: <Waypoints className="w-4 h-4" /> },
      { id: 'targeting-board', label: 'Targeting Board', icon: <LayoutList className="w-4 h-4" /> },
    ],
  },
  {
    heading: 'Execution / Operations',
    items: [
      { id: 'operations-page', label: 'Operations', icon: <Zap className="w-4 h-4" /> },
      { id: 'field-activities-page', label: 'Field Activities', icon: <Activity className="w-4 h-4" /> },
      { id: 'budget-page', label: 'Budget', icon: <DollarSign className="w-4 h-4" /> },
    ],
  },
  {
    heading: 'Intelligence',
    items: [
      { id: 'market-intelligence', label: 'Market Intelligence', icon: <Globe className="w-4 h-4" /> },
      { id: 'school-intelligence', label: 'School Intelligence', icon: <School className="w-4 h-4" /> },
      { id: 'dod-market-share', label: 'DoD Market Share', icon: <LayoutList className="w-4 h-4" /> },
      { id: 'segmentation', label: 'Segmentation', icon: <BrainCircuit className="w-4 h-4" /> },
      { id: 'reserve-alignment', label: 'Reserve Alignment', icon: <Building2 className="w-4 h-4" /> },
      { id: 'market-potential', label: 'Market Potential', icon: <TrendingUp className="w-4 h-4" /> },
      { id: 'out-of-area-analysis', label: 'Out-of-Area Analysis', icon: <Filter className="w-4 h-4" /> },
    ],
  },
  {
    heading: 'Analytics',
    items: [
      { id: 'roi-analysis', label: 'ROI Analysis', icon: <TrendingUp className="w-4 h-4" /> },
      { id: 'performance-page', label: 'Performance', icon: <BarChart3 className="w-4 h-4" /> },
      { id: 'funnel-analysis', label: 'Funnel Analysis', icon: <Filter className="w-4 h-4" /> },
    ],
  },
  {
    heading: 'Knowledge',
    items: [{ id: 'data-document-center', label: 'Data & Document Center', icon: <Database className="w-4 h-4" /> }],
  },
  {
    heading: 'Training',
    items: [{ id: 'training-center', label: 'Training Center', icon: <GraduationCap className="w-4 h-4" /> }],
  },
  {
    heading: 'Administration',
    items: [{ id: 'admin', label: 'Admin', icon: <Settings className="w-4 h-4" /> }],
  },
];

interface SidebarProps {
  activeTab: TabId;
  onNavigate: (tab: TabId) => void;
  fixed?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onNavigate, fixed = false }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <aside
      className={`flex flex-col flex-shrink-0 border-r transition-all duration-200 ${fixed ? 'fixed inset-y-0 left-0 z-30' : ''} ${
        collapsed ? 'w-14' : 'w-[220px]'
      }`}
      style={{
        backgroundColor: colors.primaryNavy,
        borderColor: `${colors.slateGray}55`,
      }}
    >
      {/* Logo / Header */}
      <div
        className={`flex items-center border-b ${collapsed ? 'justify-center' : 'justify-between'}`}
        style={{
          borderColor: `${colors.slateGray}55`,
          paddingLeft: collapsed ? spacing.sm : spacing.lg,
          paddingRight: collapsed ? spacing.sm : spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.md,
        }}
      >
        {!collapsed && (
          <div className="flex items-center gap-2 min-w-0">
            <Shield className="w-6 h-6 flex-shrink-0" style={{ color: colors.warningAmber }} />
            <div className="min-w-0">
              <div style={{ fontSize: typography.body.fontSize, fontWeight: 600, color: colors.warningAmber, letterSpacing: '0.12em' }}>TAAIP</div>
              <div className="uppercase tracking-wide leading-tight truncate" style={{ fontSize: '9px', color: colors.slateGray }}>
                Talent Acquisition Analytics
              </div>
            </div>
          </div>
        )}
        {collapsed && <Shield className="w-5 h-5" style={{ color: colors.warningAmber }} />}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className={`transition-colors flex-shrink-0 ${collapsed ? 'mt-2' : ''}`}
          style={{ color: colors.slateGray }}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto py-2 px-2">
        {!collapsed && (
          <div className="mb-3 space-y-2 px-1">
            <UnitSelector />
            <PeriodSelector />
          </div>
        )}

        <button
          key={HOME_ITEM.id}
          onClick={() => onNavigate(HOME_ITEM.id)}
          title={collapsed ? HOME_ITEM.label : undefined}
          className={`w-full flex items-center transition-colors mb-2 ${
            collapsed ? 'justify-center px-2 py-2.5' : 'gap-2.5 px-3 py-2 text-left'
          }`}
          style={{
            fontSize: typography.body.fontSize,
            fontWeight: 500,
            borderRadius: radius.md,
            backgroundColor: activeTab === HOME_ITEM.id ? colors.accentBlue : 'transparent',
            color: activeTab === HOME_ITEM.id ? colors.white : colors.slateGray,
          }}
        >
          <span className="flex-shrink-0">{HOME_ITEM.icon}</span>
          {!collapsed && <span className="truncate">{HOME_ITEM.label}</span>}
        </button>

        <div className="space-y-3">
          {NAV_SECTIONS.map((section) => (
            <div key={section.heading}>
              {!collapsed && (
                <div
                  className="px-3 mb-1 uppercase"
                  style={{
                    fontSize: '10px',
                    color: colors.slateGray,
                    letterSpacing: '0.08em',
                    opacity: 0.75,
                  }}
                >
                  {section.heading}
                </div>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onNavigate(item.id)}
                      title={collapsed ? item.label : undefined}
                      className={`w-full flex items-center transition-colors ${
                        collapsed ? 'justify-center px-2 py-2.5' : 'gap-2.5 px-3 py-2 text-left'
                      }`}
                      style={{
                        fontSize: typography.body.fontSize,
                        fontWeight: 500,
                        borderRadius: radius.md,
                        backgroundColor: isActive ? colors.accentBlue : 'transparent',
                        color: isActive ? colors.white : colors.slateGray,
                      }}
                    >
                      <span className="flex-shrink-0">{item.icon}</span>
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      {/* Bottom user area */}
      <div className="border-t px-2 py-2 space-y-0.5" style={{ borderColor: `${colors.slateGray}55` }}>
        {!collapsed && (
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen((v) => !v)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded transition-colors"
              style={{
                fontSize: typography.body.fontSize,
                color: colors.slateGray,
                borderRadius: radius.md,
              }}
            >
              <User className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 truncate text-left">Account</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
            </button>
            {userMenuOpen && (
              <div
                className="absolute bottom-full left-0 right-0 mb-1 border rounded shadow-lg z-50"
                style={{
                  backgroundColor: colors.primaryNavy,
                  borderColor: `${colors.slateGray}55`,
                  borderRadius: radius.md,
                }}
              >
                <button
                  onClick={() => { setUserMenuOpen(false); onNavigate('home-page'); }}
                  className="w-full flex items-center gap-2 px-3 py-2 transition-colors"
                  style={{ fontSize: typography.body.fontSize, color: colors.slateGray }}
                >
                  <User className="w-3.5 h-3.5" /> Home
                </button>
                <button
                  onClick={() => { setUserMenuOpen(false); onNavigate('admin'); }}
                  className="w-full flex items-center gap-2 px-3 py-2 transition-colors"
                  style={{ fontSize: typography.body.fontSize, color: colors.slateGray }}
                >
                  <Settings className="w-3.5 h-3.5" /> Settings
                </button>
                <button
                  onClick={() => setUserMenuOpen(false)}
                  className="w-full flex items-center gap-2 px-3 py-2 transition-colors"
                  style={{ fontSize: typography.body.fontSize, color: colors.dangerRed }}
                >
                  <LogOut className="w-3.5 h-3.5" /> Logout
                </button>
              </div>
            )}
          </div>
        )}
        {collapsed && (
          <>
            <button className="w-full flex justify-center px-2 py-2.5 rounded transition-colors" style={{ color: colors.slateGray, borderRadius: radius.md }} title="Account">
              <User className="w-4 h-4" />
            </button>
            <button className="w-full flex justify-center px-2 py-2.5 rounded transition-colors" style={{ color: colors.dangerRed, borderRadius: radius.md }} title="Logout">
              <LogOut className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </aside>
  );
};
