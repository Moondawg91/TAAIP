#!/usr/bin/env node
import puppeteer from 'puppeteer';
import fs from 'fs';

const URL = 'https://taaip.app/';
const out = '/tmp/site_load_timing.json';

async function run() {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1366, height: 768 });

  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });

  // Wait a bit for any SPA navigation resources
  await new Promise(r => setTimeout(r, 2000));

  // Gather performance timing & resource entries
  const metrics = await page.evaluate(() => {
    const navEntries = performance.getEntriesByType('navigation').map(e => ({
      startTime: e.startTime, duration: e.duration, type: e.type,
      domContentLoadedEventEnd: (performance.timing || {}).domContentLoadedEventEnd || 0
    }));
    const perf = {
      timing: (() => {
        try { return Object.fromEntries(Object.keys(performance.timing).map(k=>[k, performance.timing[k]])); } catch(e){return {}};
      })(),
      navigation: navEntries,
      resources: performance.getEntries().filter(p => p.entryType === 'resource').map(r => ({name: r.name, initiatorType: r.initiatorType, duration: r.duration})),
      now: Date.now(),
      title: document.title,
      url: location.href
    };
    return perf;
  });

  // Also do 5 sequential curl-like fetch of root and API endpoints from the browser context to measure client-side fetch timing
  const endpoints = [
    '/',
    '/api/v2/standings/companies',
    '/api/v2/helpdesk/requests',
    '/api/v2/task_requests'
  ];

  const fetchResults = [];
  for (const ep of endpoints) {
    const arr = [];
    for (let i=0;i<5;i++) {
      try {
        const t0 = performance.now();
        const res = await fetch(ep, { method: 'GET', cache: 'no-store' });
        const t1 = performance.now();
        arr.push({ endpoint: ep, status: res.status, time_ms: Math.round(t1 - t0) });
      } catch (e) {
        arr.push({ endpoint: ep, error: e.message });
      }
      await new Promise(r => setTimeout(r, 200));
    }
    fetchResults.push({ endpoint: ep, samples: arr });
  }

  const result = { captured_at: new Date().toISOString(), metrics, fetchResults };
  fs.writeFileSync(out, JSON.stringify(result, null, 2));
  console.log('Saved timing to', out);

  await browser.close();
}

run().catch(err=>{console.error(err); process.exit(1);});
