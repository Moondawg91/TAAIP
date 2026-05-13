// Step 10 intelligence UI integration suite.
// Run with Playwright: npx playwright test tests/intelligence-ui.playwright.spec.mjs

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TAAIP_UI_URL || 'http://127.0.0.1:5173';

async function openMarketIntelligence(page) {
  await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Market Intelligence' }).first().click();
  await expect(page.getByText('Market Intelligence Module Hub')).toBeVisible();
}

test.describe('Intelligence IA smoke', () => {
  test('RSID selector and period selector render', async ({ page }) => {
    await openMarketIntelligence(page);
    await expect(page.getByText('Unit Scope')).toBeVisible();
    await expect(page.getByText('Period Type')).toBeVisible();
    await expect(page.getByText('Period Value')).toBeVisible();
  });

  test('Market intelligence module launcher and overview render', async ({ page }) => {
    await openMarketIntelligence(page);
    await expect(page.getByRole('button', { name: 'DoD Market Share Army vs component competitors across assigned markets.' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Segmentation PRIZM, CBSA, D3AE, and F3A analysis.' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'School Intelligence SRP and school-level recruiting intelligence.' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Market Intelligence' })).toBeVisible();
  });

  test('Intelligence section pages are navigable from sidebar', async ({ page }) => {
    await openMarketIntelligence(page);

    await page.getByRole('button', { name: 'School Intelligence' }).first().click();
    await expect(page.getByText('School Intelligence / School Recruiting Program')).toBeVisible();

    await page.getByRole('button', { name: 'DoD Market Share' }).first().click();
    await expect(page.getByText('Component-level competitive intelligence')).toBeVisible();

    await page.getByRole('button', { name: 'Segmentation' }).first().click();
    await expect(page.getByText('Segmentation Intelligence')).toBeVisible();

    await page.getByRole('button', { name: 'Reserve Alignment' }).first().click();
    await expect(page.getByText('Reserve vs Active Alignment')).toBeVisible();

    await page.getByRole('button', { name: 'Market Potential' }).first().click();
    await expect(page.getByText('Army vs DoD remaining potential and achievable capacity')).toBeVisible();

    await page.getByRole('button', { name: 'Out-of-Area Analysis' }).first().click();
    await expect(page.getByText('Out-of-Area Contract Intelligence')).toBeVisible();
  });

  test('Error banner and refresh controls appear on failed request path', async ({ page }) => {
    await page.route('**/api/v2/market-intelligence/**', (route) => route.fulfill({ status: 500, body: 'boom' }));
    await openMarketIntelligence(page);
    await expect(page.getByText('HTTP 500')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Refresh' })).toBeVisible();
  });
});
