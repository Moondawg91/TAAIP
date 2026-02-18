#!/usr/bin/env node
/**
 * Headless browser capture for Helpdesk & Resources pages
 * Collects console logs, network requests/responses, and screenshots
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

const SITE_URL = 'https://taaip.app';
const PAGES = [
  { name: 'Helpdesk', id: 'helpdesk' },
  { name: 'Resources', id: 'resources' }
];

async function capturePageData(page, pageInfo) {
  const consoleLogs = [];
  const networkRequests = [];
  const networkResponses = {};
  const errors = [];

  // Intercept console logs
  page.on('console', (msg) => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  // Track network requests
  page.on('request', (request) => {
    networkRequests.push({
      method: request.method(),
      url: request.url(),
      resourceType: request.resourceType(),
      timestamp: new Date().toISOString()
    });
  });

  // Track network responses
  page.on('response', (response) => {
    const url = response.url();
    networkResponses[url] = {
      status: response.status(),
      statusText: response.statusText(),
      contentType: response.headers()['content-type'] || 'unknown'
    };
  });

  // Capture JS errors
  page.on('error', (err) => {
    errors.push({
      type: 'page_error',
      message: err.message,
      stack: err.stack
    });
  });

  page.on('pageerror', (err) => {
    errors.push({
      type: 'page_error',
      message: err.message,
      stack: err.stack
    });
  });

  // small helper to wait portably across puppeteer versions
  const wait = async (ms) => {
    if (typeof page.waitForTimeout === 'function') {
      return page.waitForTimeout(ms);
    }
    return new Promise((res) => setTimeout(res, ms));
  };

  // Navigate to site
  console.log(`[*] Navigating to ${SITE_URL}`);
  await page.goto(SITE_URL, { waitUntil: 'networkidle2', timeout: 30000 });

  // Wait for page to load
  await wait(2000);

  // Click the button to navigate to the page
  console.log(`[*] Navigating to ${pageInfo.name} page`);
  try {
    // The button onClick triggers onNavigate(pageId)
    await page.evaluate((pageId) => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const targetBtn = buttons.find((btn) => {
        const text = btn.innerText.toLowerCase();
        return text.includes(pageId.toLowerCase()) || text.includes(pageId.replace('_', ' '));
      });
      if (targetBtn) targetBtn.click();
      else console.warn(`Button for "${pageId}" not found`);
    }, pageInfo.id);

    // Wait for page content to load
    await wait(3000);
  } catch (e) {
    console.warn(`[!] Navigation click failed: ${e.message}`);
  }

  // Take screenshot
  const screenshotPath = `/tmp/${pageInfo.id}_verify.png`;
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`[✓] Screenshot saved: ${screenshotPath}`);

  return {
    page: pageInfo.name,
    pageId: pageInfo.id,
    consoleLogs,
    networkRequests,
    networkResponses,
    errors,
    screenshotPath,
    url: page.url(),
    title: await page.title()
  };
}

async function main() {
  console.log('[*] Starting headless browser capture for Helpdesk & Resources');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  try {
    const results = {};

    for (const pageInfo of PAGES) {
      console.log(`\n[*] Capturing ${pageInfo.name} page...`);
      const page = await browser.newPage();
      
      // Set viewport
      await page.setViewport({ width: 1920, height: 1080 });

      // Set user agent
      await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36');

      try {
        results[pageInfo.id] = await capturePageData(page, pageInfo);
        console.log(`[✓] ${pageInfo.name} page captured`);
      } catch (e) {
        console.error(`[✗] Failed to capture ${pageInfo.name}: ${e.message}`);
        results[pageInfo.id] = { error: e.message };
      } finally {
        await page.close();
      }
    }

    // Save results
    const outputPath = '/tmp/helpdesk_resources_verify.json';
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`\n[✓] Results saved to ${outputPath}`);

    // Print summary
    console.log('\n=== SUMMARY ===');
    for (const [id, data] of Object.entries(results)) {
      if (data.error) {
        console.log(`[✗] ${id}: ${data.error}`);
      } else {
        console.log(`[✓] ${data.page}:`);
        console.log(`    URL: ${data.url}`);
        console.log(`    Console logs: ${data.consoleLogs.length}`);
        console.log(`    Network requests: ${data.networkRequests.length}`);
        console.log(`    Errors: ${data.errors.length}`);
        if (data.errors.length > 0) {
          data.errors.forEach((err) => console.log(`      - ${err.type}: ${err.message}`));
        }
      }
    }

  } finally {
    await browser.close();
  }
}

main().catch(console.error);
