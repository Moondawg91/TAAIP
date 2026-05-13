import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const srcRoot = path.resolve(process.cwd(), 'src');
const missionSource = fs.readFileSync(path.join(srcRoot, 'components', 'MissionAdjustmentDashboard.tsx'), 'utf8');
const powerbiSource = fs.readFileSync(path.join(srcRoot, 'components', 'PowerBIEmbed.tsx'), 'utf8');
const operationalDataSource = fs.readFileSync(path.join(srcRoot, 'components', 'operationalData.ts'), 'utf8');
const authSessionSource = fs.readFileSync(path.join(srcRoot, 'lib', 'authSession.ts'), 'utf8');

test('mission analysis requests use shared authenticated fetch path', () => {
  assert.ok(missionSource.includes("import { authFetch } from '../lib/authSession';"));
  assert.ok(missionSource.includes('authFetch(`${API_BASE}/api/v2/decision-output/mission-decrease-justification`'));
  assert.ok(missionSource.includes('Mission analysis requires an authenticated session.'));
});

test('powerbi embed flow uses backend contract and supports non-configured state', () => {
  assert.ok(powerbiSource.includes('authFetch(`${API_BASE}/api/powerbi/embedToken`'));
  assert.ok(powerbiSource.includes("body?.configured === false || body?.status === 'not_configured'"));
  assert.ok(powerbiSource.includes('Power BI embedding is not configured for this environment'));
});

test('operational dataset hook retries and preserves existing data on failure', () => {
  assert.ok(operationalDataSource.includes('for (let attempt = 1; attempt <= 2; attempt += 1)'));
  assert.ok(operationalDataSource.includes('const rawData: AnyRecord = payload?.data || {};'));
  assert.ok(operationalDataSource.includes('const flatData: AnyRecord = {'));
  assert.ok(operationalDataSource.includes("...(((rawData.diagnostics as AnyRecord)?.data as AnyRecord) || {})"));
  assert.ok(operationalDataSource.includes("...(((rawData.twg as AnyRecord)?.data as AnyRecord) || {})"));
  assert.ok(operationalDataSource.includes("...(((rawData.execution as AnyRecord)?.data as AnyRecord) || {})"));
  assert.ok(!operationalDataSource.includes('setData(null);'));
});

test('shared auth session utility provides token bootstrap and auth fetch wrapper', () => {
  assert.ok(authSessionSource.includes('ensureAuthToken'));
  assert.ok(authSessionSource.includes('/api/auth/login'));
  assert.ok(authSessionSource.includes('Authorization'));
  assert.ok(authSessionSource.includes('credentials: init.credentials ||')); 
});
