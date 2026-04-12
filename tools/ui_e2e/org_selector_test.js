const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const outDir = 'tools/e2e_results/org_selector';
  try { fs.mkdirSync(outDir, { recursive: true }); } catch(e){}

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // capture network requests/responses for /api/v2/org
  const apiCalls = [];
  page.on('requestfinished', async (req) => {
    try {
      const url = req.url();
      if (url.includes('/api/v2/org')) {
        const resp = await req.response();
        const text = await resp.text();
        apiCalls.push({ url, status: resp.status(), body: text });
      }
    } catch (e) {
      // ignore
    }
  });

  const base = 'http://localhost:3000';
  console.log('Opening', base);
  await page.goto(base, { waitUntil: 'networkidle' });

  // Wait for OrgUnitPicker to appear. Use generic selectors: look for select elements or dropdown labels
  await page.waitForTimeout(1000);

  // Heuristics: find visible select or button elements that look like org selectors
  // Try common MUI selector role
  const dropdowns = await page.$$('button[aria-haspopup="listbox"], select');
  console.log('Found dropdown candidate count:', dropdowns.length);

  // We'll attempt to click sequentially up to 5 times, capturing screenshot after each.
  for (let i=0;i<5;i++){
    // refresh list of visible dropdown buttons
    const buttons = await page.$$('button[aria-haspopup="listbox"]');
    if (buttons.length === 0) break;
    const btn = buttons[Math.min(i, buttons.length-1)];
    try {
      await btn.scrollIntoViewIfNeeded();
      await btn.click();
      await page.waitForTimeout(600);
      // pick first option
      const option = await page.$('ul[role="listbox"] li');
      if (option) {
        await option.click();
      }
      await page.screenshot({ path: `${outDir}/step_${i+1}.png`, fullPage: true });
      await page.waitForTimeout(600);
    } catch (e) {
      console.log('interaction error at step', i, e.message);
      break;
    }
  }

  // save captured API calls
  fs.writeFileSync(`${outDir}/api_calls.json`, JSON.stringify(apiCalls, null, 2));
  console.log('Results saved to', outDir);

  await browser.close();
})();
