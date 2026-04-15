import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(process.cwd(), 'src');
const appSource = fs.readFileSync(path.join(srcRoot, 'App.tsx'), 'utf8');
const homeSource = fs.readFileSync(path.join(srcRoot, 'components', 'HomeScreen.tsx'), 'utf8');

test('role perspective access map is present in app shell', () => {
  assert.ok(appSource.includes('PERSPECTIVE_TAB_ACCESS'));
  assert.ok(appSource.includes("commander: ["));
  assert.ok(appSource.includes("operator420t: ['home', 'command-center', 'diagnostics', 'decision-sync', 'execution', 'powerbi']"));
  assert.ok(appSource.includes("'admin-console'"));
});

test('operator perspective excludes admin console from workflow tabs', () => {
  const operatorSegment = appSource.slice(
    appSource.indexOf('operator420t:'),
    appSource.indexOf('admin:', appSource.indexOf('operator420t:')),
  );

  assert.ok(operatorSegment.includes("'execution'"));
  assert.ok(!operatorSegment.includes("'admin-console'"));
});

test('home screen filters workflow steps by allowed role tabs', () => {
  assert.ok(homeSource.includes('const visibleSteps = workflowSteps.filter((step) => allowed.has(step.id));'));
  assert.ok(homeSource.includes('Admin/maintainer view keeps refresh and maintenance controls separate'));
  assert.ok(homeSource.includes('420T operator view focuses on drill-down evidence'));
});
