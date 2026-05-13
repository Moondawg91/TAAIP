import { test, expect } from '@playwright/test';

async function gotoAndStabilize(page, path = '/') {
  await page.goto(path, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await expect(page.locator('body')).toBeVisible();
}

test.describe('visual diff', () => {
  test('home / market intelligence / school intelligence match baselines', async ({ page }) => {
    await gotoAndStabilize(page, '/?activeTab=home-page');
    await expect(page).toHaveScreenshot('home.png', { fullPage: true });

    await gotoAndStabilize(page, '/?activeTab=market-intelligence');
    await expect(page).toHaveScreenshot('market-intelligence.png', { fullPage: true });

    await gotoAndStabilize(page, '/?activeTab=school-intelligence');
    await expect(page).toHaveScreenshot('school-intelligence.png', { fullPage: true });
  });
});
