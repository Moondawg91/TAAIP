import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(process.cwd(), 'src');
const appSource = fs.readFileSync(path.join(srcRoot, 'App.tsx'), 'utf8');
const homeSource = fs.readFileSync(path.join(srcRoot, 'components', 'HomeScreen.tsx'), 'utf8');

// Restored HomeScreen has no role-based access — all nav open to all users via onNavigate
test('home screen accepts onNavigate prop without role or perspective filtering', () => {
  assert.ok(homeSource.includes('onNavigate'));
  assert.ok(!homeSource.includes('ROLE_TAB_ACCESS'));
  assert.ok(!homeSource.includes('userRole'));
  assert.ok(!homeSource.includes('perspective'));
  assert.ok(!homeSource.includes('allowedTabs'));
  assert.ok(!homeSource.includes('visibleSections'));
});

test('app shell has no role-based tab filter map', () => {
  assert.ok(!appSource.includes('ROLE_TAB_ACCESS'));
  assert.ok(!appSource.includes("operator420t: ["));
  assert.ok(!appSource.includes('PERSPECTIVE_TAB_ACCESS'));
});

test('home screen shows CompanyStandingsLeaderboard for all users', () => {
  assert.ok(homeSource.includes('CompanyStandingsLeaderboard'));
  assert.ok(homeSource.includes('showExpanded'));
});

test('home screen footer shows TAAIP classification banner', () => {
  assert.ok(homeSource.includes('UNCLASSIFIED') || homeSource.includes('FOR OFFICIAL USE ONLY'));
});
