import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(process.cwd(), 'src');
const appSource = fs.readFileSync(path.join(srcRoot, 'App.tsx'), 'utf8');
const homeSource = fs.readFileSync(path.join(srcRoot, 'components', 'HomeScreen.tsx'), 'utf8');

const commanderTabs = [
  'command-center',
  'mission-adjustment',
  'diagnostics',
  'decision-sync',
  'execution',
  'powerbi',
];

test('app shell keeps the consolidated commander workflow', () => {
  for (const tab of commanderTabs) {
    assert.ok(appSource.includes(`'${tab}'`), `expected App shell to include ${tab}`);
  }

  assert.ok(appSource.includes('Commander Workflow'));
  assert.ok(appSource.includes('Mission Adjustment'));
  assert.ok(appSource.includes('TWG and Targeting Board'));
});

test('home screen exposes the same step sequence', () => {
  for (const tab of commanderTabs) {
    assert.ok(homeSource.includes(`id: '${tab}'`), `expected Home screen card for ${tab}`);
  }

  assert.ok(homeSource.includes('One connected operational sequence'));
});

test('legacy dead-route imports do not return', () => {
  const blockedLegacyReferences = [
    'TalentAcquisitionTechnicianDashboard',
    'RecruitingFunnelDashboard',
    'MarketPotentialDashboard',
    'TargetingDecisionBoard',
    'LeadStatusReport',
    'EventPerformanceDashboard',
    'helpdesk',
    'dod',
  ];

  for (const legacyRef of blockedLegacyReferences) {
    assert.ok(!appSource.includes(legacyRef), `unexpected legacy reference still present: ${legacyRef}`);
  }
});
