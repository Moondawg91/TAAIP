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
      if (ct.includes('application/json')) {
        try { body = (await res.text()).slice(0, 1000); } catch(e){ body = '<<read-error:'+String(e)+'>>' }
      }
      responses.push({url: res.url(), status: res.status(), contentType: ct, bodySnippet: body});
    } catch (e) {
      responses.push({url: res.url(), status: res.status(), error: String(e)});
    }
  });

  async function visit(path, name){
    try{
      await page.goto(`https://taaip.app${path}`, {waitUntil: 'domcontentloaded', timeout: 60000});
    }catch(e){ }
    await new Promise(r => setTimeout(r, 3000));
    try { await page.screenshot({path:`tabs_${name}.png`, fullPage:true}); } catch(e){}
  }

  await visit('/projects', 'projects');
  await visit('/helpdesk', 'helpdesk');
  await visit('/resources', 'resources');

  await browser.close();
  fs.writeFileSync('tabs_console.json', JSON.stringify(logs, null, 2));
  fs.writeFileSync('tabs_requests.json', JSON.stringify(requests, null, 2));
  fs.writeFileSync('tabs_responses.json', JSON.stringify(responses, null, 2));
  console.log('tabs-capture-complete');
})();
