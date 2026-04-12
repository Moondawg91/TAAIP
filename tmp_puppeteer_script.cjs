
// Puppeteer script to capture console logs and network requests
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
    try{
      const ct = res.headers()['content-type'] || '';
      const text = (ct.includes('application/json') && res.status()===200) ? await res.text().then(t=>t.slice(0,2000)) : '';
      responses.push({url: res.url(), status: res.status(), contentType: ct, bodySnippet: text});
    }catch(e){responses.push({url: res.url(), status: res.status(), error: String(e)})}
  });
  // Visit app root then try /projects route
  await page.goto('https://taaip.app', {waitUntil: 'networkidle2', timeout: 60000});
  await page.waitForNavigation({waitUntil:"networkidle0"});
  // Try navigate to projects route
  try{ await page.goto('https://taaip.app/projects', {waitUntil:'networkidle2', timeout:30000}); }catch(e){}
  await page.waitForNavigation({waitUntil:"networkidle0"});
  // Take screenshot
  await page.screenshot({path:'project_management.png', fullPage:true});
  await browser.close();
  fs.writeFileSync('puppeteer_console.json', JSON.stringify(logs, null, 2));
  fs.writeFileSync('puppeteer_requests.json', JSON.stringify(requests, null, 2));
  fs.writeFileSync('puppeteer_responses.json', JSON.stringify(responses, null, 2));
  console.log('done');
})();
