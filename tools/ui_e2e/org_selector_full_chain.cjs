const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  try{
    const browser = await pw.webkit.launch({ headless: true });
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const outDir = 'tools/e2e_results/org_selector_full_chain';
    fs.mkdirSync(outDir, { recursive: true });
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1200);

    // helper to open nth combobox and return li texts
      async function getComboboxByLabel(labelText){
        const labels = await page.$$('label')
        for(const lh of labels){
          const txt = (await lh.innerText()).trim()
          if (txt.toUpperCase() === labelText.toUpperCase()){
            // find combobox inside same form control
            const h = await lh.evaluateHandle(node => {
              const parent = node.closest('.MuiFormControl-root') || node.parentElement
              if (!parent) return null
              return parent.querySelector('div[role="combobox"]')
            })
            const el = h.asElement ? h.asElement() : h
            return el
          }
        }
        return null
      }

      async function openComboboxHandle(handle){
        if (!handle) return [];
        try{ await handle.scrollIntoViewIfNeeded() }catch(e){}
        // use direct DOM click to avoid Playwright "not enabled" stability checks
        await handle.evaluate(el => el.click())
        await page.waitForTimeout(600);
        const items = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n => n.innerText));
        await page.screenshot({ path: `${outDir}/after_open_${(Math.random()*100000|0)}.png`, fullPage: true });
        return items
      }

    // 0 -> Brigade, 1 -> BN, 2 -> CO, 3 -> STN (based on DOM order observed)
    const bdeHandle = await getComboboxByLabel('BDE')
    const brigades = await openComboboxHandle(bdeHandle)
    fs.writeFileSync(`${outDir}/brigades.json`, JSON.stringify(brigades, null, 2));
    if (brigades.length <= 1) { console.log('no brigades'); await browser.close(); return }
    // select first real brigade (skip 'All' at index 0)
    await page.$$eval('ul[role="listbox"] li', nodes => nodes[1].click());
    await page.waitForTimeout(800);

    const bnHandle = await getComboboxByLabel('BN')
    // wait until BN combobox exists and is enabled
    for (let i=0;i<30;i++){
      const disabled = await page.evaluate(h => h ? h.getAttribute('aria-disabled') : 'true', bnHandle)
      if (!disabled || disabled === 'false') break;
      await page.waitForTimeout(200);
    }
    const bns = await openComboboxHandle(bnHandle);
    fs.writeFileSync(`${outDir}/bns.json`, JSON.stringify(bns, null, 2));
    if (bns.length <= 1){ console.log('no bns'); await browser.close(); return }
    await page.$$eval('ul[role="listbox"] li', nodes => nodes[1].click());
    await page.waitForTimeout(800);

    const cos = await openComboboxAt(2);
    fs.writeFileSync(`${outDir}/cos.json`, JSON.stringify(cos, null, 2));
    if (cos.length <= 1){ console.log('no cos'); await browser.close(); return }
    await page.$$eval('ul[role="listbox"] li', nodes => nodes[1].click());
    await page.waitForTimeout(800);

    const stns = await openComboboxAt(3);
    fs.writeFileSync(`${outDir}/stns.json`, JSON.stringify(stns, null, 2));

    // capture network calls for /api/v2/org during the run
    const net = await page.evaluate(()=> window.__LAST_ORG_CALLS__ || null).catch(()=> null)
    fs.writeFileSync(`${outDir}/ui_net_placeholder.json`, JSON.stringify(net, null, 2));

    await browser.close();
    console.log('done')
  }catch(e){ console.error(e && (e.stack||e.message)); process.exit(1) }
})();
