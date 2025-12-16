const fs = require('fs');
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({args:['--no-sandbox','--disable-setuid-sandbox']});
  const page = await browser.newPage();
  const logs = [];
  page.on('console', msg => logs.push({type: msg.type(), text: msg.text()}));
  const requests = [];
  page.on('request', req => requests.push({url: req.url(), method: req.method(), resourceType: req.resourceType()}));
  const responses = [];
  page.on('response', async res => {
    try {
      const ct = res.headers()['content-type'] || '';
      let body = '';
      if (ct.includes('application/json') && res.status() === 200) {
        try { body = (await res.text()).slice(0, 2000); } catch(e){ body = '<<read-error:'+String(e)+'>>' }
      }
      responses.push({url: res.url(), status: res.status(), contentType: ct, bodySnippet: body});
    } catch (e) {
      responses.push({url: res.url(), status: res.status(), error: String(e)});
    }
  });

  try {
    await page.goto('https://taaip.app/projects', {waitUntil: 'domcontentloaded', timeout: 60000});
  } catch (e) {
    // fallback to root
    try { await page.goto('https://taaip.app', {waitUntil: 'domcontentloaded', timeout: 60000}); } catch(e){}
  }

  // Wait a bit for SPA rendering
  await new Promise(r => setTimeout(r, 3000));

  try { await page.screenshot({path:'pm_capture.png', fullPage:true}); } catch(e){}

  await browser.close();

  fs.writeFileSync('pm_console.json', JSON.stringify(logs, null, 2));
  fs.writeFileSync('pm_requests.json', JSON.stringify(requests, null, 2));
  fs.writeFileSync('pm_responses.json', JSON.stringify(responses, null, 2));
  console.log('capture-complete');
})();
