import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(process.cwd(), 'src');
const appSource = fs.readFileSync(path.join(srcRoot, 'App.tsx'), 'utf8');
const homeSource = fs.readFileSync(path.join(srcRoot, 'components', 'HomeScreen.tsx'), 'utf8');

// Original TAAIP tabs restored from baseline commit 72c895d + previously disconnected built features
const requiredTabs = [
  '420t',
  'funnel',
  'analytics',
  'market',
  'mission',
  'targeting',
  'projects',
  'leads',
  'events',
  'g2zones',
  'calendar',
  'sharepoint',
  'budget',
  'twg',
  'fusion',
  'segmentation',
  'methodology',
  'universal-upload',
  'data-manager',
  'quarter-assessment',
  'asset-recommend',
  'historical',
  'user-management',
  'powerbi',
  'marketing-engagement',
  'admin-console',
  'admin-query',
  // Restored built features that were disconnected from nav
  'command-center',
  'diagnostics',
  'execution',
  'mission-feasibility',
  'helpdesk',
  'dod-comparison',
  'bulk-upload',
  'data-input',
];

test('app shell includes all original TAAIP platform tabs', () => {
  for (const tab of requiredTabs) {
    assert.ok(appSource.includes(`'${tab}'`), `expected App shell to include tab: ${tab}`);
  }

  // Verify new 8-domain nav structure is in place
  assert.ok(appSource.includes('Schools & Lead Gen'));
  assert.ok(appSource.includes('Mission & Performance'));
  assert.ok(appSource.includes('Targeting & Decisioning'));
});

test('app shell uses original TAAIP nav categories', () => {
  // 8-domain navigation structure
  assert.ok(appSource.includes('Mission & Performance'));
  assert.ok(appSource.includes('Schools & Lead Gen'));
  assert.ok(appSource.includes('Market Intelligence'));
  assert.ok(appSource.includes('Funnel & Production'));
  assert.ok(appSource.includes('Targeting & Decisioning'));
  assert.ok(appSource.includes('Execution & Operations'));
  assert.ok(appSource.includes('Analytics & Optimization'));
  assert.ok(appSource.includes('Data & Admin'));
});

test('app shell has original TAAIP branding without commander shell', () => {
  assert.ok(appSource.includes('Talent Acquisition Analytics and Intelligence Platform'));
  assert.ok(!appSource.includes('Commander Decision Support'));
  assert.ok(!appSource.includes('Commander Workflow'));
  assert.ok(!appSource.includes("'commander'"));
  assert.ok(!appSource.includes('ROLE_TAB_ACCESS'));
  assert.ok(!appSource.includes('PERSPECTIVE_TAB_ACCESS'));
});

test('app shell lazy-imports all original TAAIP components', () => {
  const requiredComponents = [
    'TalentAcquisitionTechnicianDashboard',
    'RecruitingFunnelDashboard',
    'MissionAnalysisDashboard',
    'TargetingDecisionBoard',
    'LeadStatusReport',
    'EventPerformanceDashboard',
    'G2ZonePerformanceDashboard',
    'MarketPotentialDashboard',
    'TargetingWorkingGroup',
    'FusionTeamDashboard',
    'CalendarSchedulerDashboard',
    'BudgetTracker',
    'SharePointIntegration',
    'UserManagement',
    'AdminConsole',
    'PowerBIBundle',
  ];
  for (const comp of requiredComponents) {
    assert.ok(appSource.includes(comp), `expected lazy import for: ${comp}`);
  }
});

test('home screen uses original sidebar layout with CompanyStandingsLeaderboard', () => {
  assert.ok(homeSource.includes('CompanyStandingsLeaderboard'));
  assert.ok(homeSource.includes('LiveUpdatesBanner'));
  assert.ok(homeSource.includes('onNavigate'));
  assert.ok(!homeSource.includes('ROLE_TAB_ACCESS'));
  assert.ok(!homeSource.includes('allowedTabs'));
  assert.ok(!homeSource.includes('visibleSections'));
});

test('home screen sidebar panels are present', () => {
  assert.ok(homeSource.includes('Resources'));
  assert.ok(homeSource.includes('HelpDesk') || homeSource.includes('Help Desk'));
  assert.ok(homeSource.includes('TAAIP v2.0') || homeSource.includes('UNCLASSIFIED'));
});
