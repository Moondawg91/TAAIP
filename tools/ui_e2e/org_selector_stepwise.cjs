const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  const browser = await pw.webkit.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const out = 'tools/e2e_results/org_selector_stepwise';
  fs.mkdirSync(out, { recursive: true });
  const net = [];
  page.on('response', async r => {
    try{
      const url = r.url();
      if (url.includes('/api/v2/org')){
        const text = await r.text();
        net.push({url, status: r.status(), body: text});
      }
    }catch(e){}
  });
  try{
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1000);

    // helper to find combobox by label and return element handle
    async function findCombo(label){
      const labels = await page.$$('label');
      for(const lh of labels){
        const txt = (await lh.innerText()).trim();
        if (txt.toUpperCase() === label.toUpperCase()){
          const parent = await lh.evaluateHandle(node => node.closest('.MuiFormControl-root') || node.parentElement)
          const cb = await parent.asElement().$('div[role="combobox"]')
          return cb
        }
      }
      return null
    }

    // Step 1: open BDE
    const bde = await findCombo('BDE');
    if (!bde) { console.log('bde not found'); await page.screenshot({ path: `${out}/page_before.png`, fullPage:true }); await browser.close(); process.exit(1) }
    await bde.evaluate(el=>el.click())
    await page.waitForFunction(()=>{
      return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0
    }, { timeout: 10000 })
    const bdeItems = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/brigades.json`, JSON.stringify(bdeItems, null, 2))
    await page.screenshot({ path: `${out}/bde_open.png`, fullPage:true })
    // select first actual brigade (index 1)
    if (bdeItems.length <= 1) { console.log('no brigade items'); await browser.close(); process.exit(1) }
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // Step 2: open BN
    const bn = await findCombo('BN')
    if (!bn) { console.log('bn not found'); await browser.close(); process.exit(1) }
    // wait until enabled
    for(let i=0;i<30;i++){
      const dis = await bn.getAttribute('aria-disabled')
      if (!dis || dis === 'false') break
      await page.waitForTimeout(200)
    }
    await bn.evaluate(el=>el.click())
    await page.waitForFunction(()=>{
      return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0
    }, { timeout: 10000 })
    const bnItems = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/bns.json`, JSON.stringify(bnItems, null, 2))
    await page.screenshot({ path: `${out}/bn_open.png`, fullPage:true })
    if (bnItems.length <= 1) { console.log('no bns'); await browser.close(); process.exit(1) }
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // Step 3: open CO
    const co = await findCombo('Company') || await findCombo('CO')
    if (!co) { console.log('co not found'); await browser.close(); process.exit(1) }
    for(let i=0;i<30;i++){ const dis = await co.getAttribute('aria-disabled'); if (!dis || dis==='false') break; await page.waitForTimeout(200)}
    await co.evaluate(el=>el.click())
    await page.waitForFunction(()=>{
      return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0
    }, { timeout: 10000 })
    const coItems = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/cos.json`, JSON.stringify(coItems, null, 2))
    await page.screenshot({ path: `${out}/co_open.png`, fullPage:true })
    if (coItems.length <= 1) { console.log('no cos'); await browser.close(); process.exit(1) }
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // Step 4: open STN
    const stn = await findCombo('Station') || await findCombo('STN')
    if (!stn) { console.log('stn not found'); await browser.close(); process.exit(1) }
    for(let i=0;i<30;i++){ const dis = await stn.getAttribute('aria-disabled'); if (!dis || dis==='false') break; await page.waitForTimeout(200)}
    await stn.evaluate(el=>el.click())
    await page.waitForFunction(()=>{
      return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0
    }, { timeout: 10000 })
    const stnItems = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/stns.json`, JSON.stringify(stnItems, null, 2))
    await page.screenshot({ path: `${out}/stn_open.png`, fullPage:true })

    fs.writeFileSync(`${out}/network_calls.json`, JSON.stringify(net, null, 2))
    console.log('done')
    await browser.close()
  }catch(e){ console.error('ERR', e && (e.stack||e.message)); try{ await page.screenshot({ path: 'tools/e2e_results/org_selector_stepwise/error.png', fullPage:true }) }catch(_){}; process.exit(1) }
})();
