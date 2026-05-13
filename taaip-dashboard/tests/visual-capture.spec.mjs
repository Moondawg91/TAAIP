import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

async function gotoAndStabilize(page, path = '/') {
  await page.goto(path, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await expect(page.locator('body')).toBeVisible();
}

test.describe('visual capture', () => {
  test('capture home / market intelligence / school intelligence', async ({ page }) => {
    const baselineDir = path.resolve(process.cwd(), 'tests/visual-diff.spec.mjs-snapshots');
    fs.mkdirSync(baselineDir, { recursive: true });

    await gotoAndStabilize(page, '/?activeTab=home-page');
    await page.screenshot({ path: path.join(baselineDir, 'home-chromium-darwin.png'), fullPage: true });

    await gotoAndStabilize(page, '/?activeTab=market-intelligence');
    await page.screenshot({ path: path.join(baselineDir, 'market-intelligence-chromium-darwin.png'), fullPage: true });

    await gotoAndStabilize(page, '/?activeTab=school-intelligence');
    await page.screenshot({ path: path.join(baselineDir, 'school-intelligence-chromium-darwin.png'), fullPage: true });
  });
});
