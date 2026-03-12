const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const BASE = process.env.BASE_URL || 'http://127.0.0.1:61561';
  const API_BASE = process.env.API_BASE || 'http://127.0.0.1:8000';
  const fixture = path.resolve(__dirname, '../test-fixtures/test_document.txt');
  console.log('BASE=', BASE, 'API_BASE=', API_BASE, 'fixture=', fixture);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE_CONSOLE:', msg.text()));
  page.on('pageerror', err => console.error('PAGE_ERROR:', err));

  try {
    // Navigate to the site root and open the Data Hub via the app navigation
    await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
    // Click the app nav link to trigger client-side routing to the Data Hub
    // Try multiple strategies to find the nav link
    const navByHref = await page.$('a[href="/data-hub"]');
    if (navByHref) {
      await navByHref.click();
    } else {
      // Fallback to link text
      const navByText = await page.$('text=Data Hub');
      if (navByText) await navByText.click();
    }
    // Wait for SPA to finish routing and client code to render the upload input
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('input[data-testid="document-file-input"]', { timeout: 30000 });
    const input = await page.$('input[data-testid="document-file-input"]');
    if (!input) throw new Error('file input not found');

    console.log('setting file on input...');
    await input.setInputFiles(fixture);

    // Try common upload button selectors
    let uploadButton = await page.$('button:has-text("Upload")');
    if (!uploadButton) uploadButton = await page.$('button[data-testid="document-upload-button"]');
    if (!uploadButton) {
      // fallback: find button near the file input
      uploadButton = await page.$('input[data-testid="document-file-input"] ~ button');
    }

    if (!uploadButton) throw new Error('upload button not found');
    await uploadButton.click();

    // Wait for the filename to appear in the documents list
    const filename = path.basename(fixture);
    const listed = await page.waitForSelector(`text=${filename}`, { timeout: 15000 }).then(() => true).catch(() => false);
    console.log('document_listed:', listed);

    await browser.close();
    process.exit(listed ? 0 : 2);
  } catch (err) {
    console.error('E2E error:', err);
    await browser.close();
    process.exit(3);
  }
})();
