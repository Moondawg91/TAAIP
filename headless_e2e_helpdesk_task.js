#!/usr/bin/env node
import puppeteer from 'puppeteer';
import fs from 'fs';

const SITE = 'https://taaip.app';
const results = { timestamp: new Date().toISOString(), timings: {}, steps: [], apiCalls: [] };
const wait = async (ms) => new Promise(r => setTimeout(r, ms));

async function run() {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 900 });

  // Capture API calls
  page.on('response', async (res) => {
    const url = res.url();
    if (url.includes('/api/v2/helpdesk/requests') || url.includes('/api/v2/task_requests')) {
      try {
        const text = await res.text();
        results.apiCalls.push({ url, status: res.status(), body: text.slice(0, 500) });
      } catch (e) {}
    }
  });

  // Navigate to site and measure
  const t1 = performance.now();
  await page.goto(SITE, { waitUntil: 'networkidle2', timeout: 60000 });
  const t2 = performance.now();
  results.timings.homepage_load_ms = Math.round(t2 - t1);
  results.steps.push(`Homepage loaded in ${results.timings.homepage_load_ms}ms`);
  
  await wait(1000);

  // Try to navigate by clicking a button in the UI
  const buttons = await page.$$('button');
  let helpDeskClicked = false;
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.innerText, btn);
    if (text && text.toLowerCase().includes('help')) {
      await btn.click();
      await wait(400);
      helpDeskClicked = true;
      break;
    }
  }
  results.steps.push(helpDeskClicked ? 'Help Desk opened' : 'Help Desk button not found');

  // Navigate to static task page
  const t3 = performance.now();
  await page.goto(SITE + '/dashboard/task_requests.html', { waitUntil: 'networkidle2', timeout: 60000 });
  const t4 = performance.now();
  results.timings.task_page_load_ms = Math.round(t4 - t3);
  results.steps.push(`Task page loaded in ${results.timings.task_page_load_ms}ms`);

  await wait(500);

  // Take final screenshot
  await page.screenshot({ path: '/tmp/e2e_final.png', fullPage: true });
  results.steps.push('Screenshot captured');

  await browser.close();
  fs.writeFileSync('/tmp/headless_e2e_results.json', JSON.stringify(results, null, 2));
  console.log('E2E test completed. Results:');
  console.log(JSON.stringify(results, null, 2));
}

run().catch(e=>{console.error(e); process.exit(1)});
