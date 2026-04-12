const fs = require('fs');
const browsers = ['chromium','webkit','firefox'];
const { devices } = require('playwright');

async function runWith(browserName){
  try{
    const pw = require('playwright');
    const browserType = pw[browserName];
    if(!browserType) throw new Error('browser not available: '+browserName);
    const browser = await browserType.launch({ headless: true, timeout: 120000 });
    const context = await browser.newContext();
    const page = await context.newPage();

    const outDir = `tools/e2e_results/org_selector_${browserName}`;
    fs.mkdirSync(outDir, { recursive: true });
    const apiCalls = [];
    page.on('requestfinished', async (req) => {
      try{
        const url = req.url();
        if(url.includes('/api/v2/org')){
          const resp = await req.response();
          const body = await resp.text();
          apiCalls.push({ url, status: resp.status(), body });
        }
      }catch(e){}
    });

    const base = 'http://localhost:3000';
    console.log('Opening', base, 'with', browserName);
    await page.goto(base, { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1200);

    // find brigade select
    // Click sequence: open brigade dropdown, pick first, then BN, CO, STN
    const steps = ['Brigade','Battalion','Company','Station'];
    for(let i=0;i<steps.length;i++){
      // find button that opens listbox which is visible and not disabled
      const buttons = await page.$$('button[aria-haspopup="listbox"]');
      if(buttons.length === 0){
        console.log('No listbox buttons found at step', steps[i]);
        break;
      }
      // heuristics: use the first unopened dropdown not yet selected
      const btn = buttons[Math.min(i, buttons.length-1)];
      await btn.click();
      await page.waitForTimeout(500);
      // try to select first li in listbox
      const option = await page.$('ul[role="listbox"] li');
      if(option){
        await option.click();
        await page.waitForTimeout(700);
      } else {
        console.log('No option found after opening dropdown at step', steps[i]);
      }
      await page.screenshot({ path: `${outDir}/step_${i+1}_${steps[i]}.png`, fullPage: true });
    }

    fs.writeFileSync(`${outDir}/api_calls.json`, JSON.stringify(apiCalls, null, 2));
    await browser.close();
    return { ok:true, browser: browserName };
  }catch(e){
    return { ok:false, browser: browserName, error: e && (e.stack || e.message) };
  }
}

(async ()=>{
  const results = [];
  for(const b of browsers){
    const r = await runWith(b);
    console.log('Result', r);
    results.push(r);
    if(r.ok) break; // stop on first success
  }
  fs.writeFileSync('tools/e2e_results/org_selector_multibrowser_results.json', JSON.stringify(results, null, 2));
  console.log('Done');
})();
