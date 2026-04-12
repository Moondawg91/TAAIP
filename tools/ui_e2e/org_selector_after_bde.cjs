const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  const browser = await pw.webkit.launch({ headless: true });
  const page = await browser.newPage();
  const out = 'tools/e2e_results/org_selector_after_bde';
  fs.mkdirSync(out, { recursive: true });
  const net = [];
  page.on('response', async r => {
    try{ const url = r.url(); if (url.includes('/api/v2/org')) { const body = await r.text(); net.push({url, status: r.status(), body}); } }catch(e){}
  });
  try{
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1000);
    // click first enabled combobox
    const combos = await page.$$('div[role="combobox"]');
    let idx = 0; for(let i=0;i<combos.length;i++){ const d = await combos[i].getAttribute('aria-disabled'); if (!d || d === 'false') { idx = i; break } }
    await combos[idx].evaluate(el=>el.click())
    await page.waitForSelector('ul[role="listbox"] li', { timeout: 15000 })
    await page.screenshot({ path: `${out}/bde_open.png`, fullPage:true })
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(1000)
    // capture BN combobox state
    const combos2 = await page.$$('div[role="combobox"]');
    const bnInfo = []
    for(const c of combos2){ bnInfo.push({ aria_disabled: await c.getAttribute('aria-disabled'), text: (await c.innerText()).trim().slice(0,100) }) }
    fs.writeFileSync(`${out}/combos_after_bde.json`, JSON.stringify(bnInfo, null, 2))
    fs.writeFileSync(`${out}/network_after_bde.json`, JSON.stringify(net, null, 2))
    await page.screenshot({ path: `${out}/after_bde_selected.png`, fullPage:true })
    console.log('done')
    await browser.close()
  }catch(e){ console.error(e && (e.stack||e.message)); try{ await page.screenshot({ path: 'tools/e2e_results/org_selector_after_bde/error.png', fullPage:true }) }catch(_){}; process.exit(1) }
})();
