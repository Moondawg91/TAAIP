const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  try{
    const browser = await pw.webkit.launch({ headless: true });
    const page = await browser.newPage();
    const out = 'tools/e2e_results/org_selector_click_chain_simple';
    fs.mkdirSync(out, { recursive: true });
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1000);

    // get initial combobox disabled states
    const combos = await page.$$('div[role="combobox"]');
    const initialDisabled = [];
    for(const c of combos){
      const d = await c.getAttribute('aria-disabled'); initialDisabled.push(d === 'true')
    }

    // find first enabled combobox index
    let firstIdx = initialDisabled.findIndex(d => d === false)
    if (firstIdx === -1) firstIdx = 0
    const first = combos[firstIdx]
    await first.evaluate(el=>el.click())
    await page.waitForTimeout(600)
    const items = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/step0_brigades.json`, JSON.stringify(items, null, 2))
    await page.screenshot({ path: `${out}/step0_brigades.png`, fullPage:true })
    if (items.length <= 1) { console.log('no brigades'); await browser.close(); return }
    // select first brigade
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // now poll for next combobox that became enabled
    let combos2 = await page.$$('div[role="combobox"]')
    let nextIdx = -1
    for (let t=0;t<30;t++){
      combos2 = await page.$$('div[role="combobox"]')
      for(let i=0;i<combos2.length;i++){
        const wasDisabled = initialDisabled[i]
        const nowDisabled = (await combos2[i].getAttribute('aria-disabled')) === 'true'
        if (wasDisabled && !nowDisabled){ nextIdx = i; break }
      }
      if (nextIdx !== -1) break
      await page.waitForTimeout(200)
    }
    if (nextIdx === -1){ console.log('no next combobox found'); await browser.close(); return }
    const bnHandle = combos2[nextIdx]
    await bnHandle.evaluate(el=>el.click())
    await page.waitForTimeout(600)
    const bns = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/step1_bns.json`, JSON.stringify(bns, null, 2))
    await page.screenshot({ path: `${out}/step1_bns.png`, fullPage:true })
    if (bns.length <= 1){ console.log('no bns'); await browser.close(); return }
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // repeat for CO
    combos2 = await page.$$('div[role="combobox"]')
    let coIdx = -1
    for (let t=0;t<30;t++){
      combos2 = await page.$$('div[role="combobox"]')
      for(let i=0;i<combos2.length;i++){
        const wasDisabled = initialDisabled[i]
        const nowDisabled = (await combos2[i].getAttribute('aria-disabled')) === 'true'
        if (wasDisabled && !nowDisabled){ if (i !== nextIdx) { coIdx = i; break } }
      }
      if (coIdx !== -1) break
      await page.waitForTimeout(200)
    }
    if (coIdx === -1){ console.log('no co combobox found'); await browser.close(); return }
    const coHandle = combos2[coIdx]
    await coHandle.evaluate(el=>el.click())
    await page.waitForTimeout(600)
    const cos = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/step2_cos.json`, JSON.stringify(cos, null, 2))
    await page.screenshot({ path: `${out}/step2_cos.png`, fullPage:true })
    if (cos.length <= 1){ console.log('no cos'); await browser.close(); return }
    await page.$$eval('ul[role="listbox"] li', els => els[1].click())
    await page.waitForTimeout(800)

    // STN
    combos2 = await page.$$('div[role="combobox"]')
    let stnIdx = -1
    for (let t=0;t<30;t++){
      combos2 = await page.$$('div[role="combobox"]')
      for(let i=0;i<combos2.length;i++){
        const wasDisabled = initialDisabled[i]
        const nowDisabled = (await combos2[i].getAttribute('aria-disabled')) === 'true'
        if (wasDisabled && !nowDisabled){ if (i !== nextIdx && i !== coIdx) { stnIdx = i; break } }
      }
      if (stnIdx !== -1) break
      await page.waitForTimeout(200)
    }
    if (stnIdx === -1){ console.log('no stn combobox found'); await browser.close(); return }
    const stnHandle = combos2[stnIdx]
    await stnHandle.evaluate(el=>el.click())
    await page.waitForTimeout(600)
    const stns = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync(`${out}/step3_stns.json`, JSON.stringify(stns, null, 2))
    await page.screenshot({ path: `${out}/step3_stns.png`, fullPage:true })
    console.log('done')
    await browser.close()
  }catch(e){ console.error('ERR', e && (e.stack||e.message)); process.exit(1) }
})();
