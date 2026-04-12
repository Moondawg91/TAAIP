const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  try{
    const browser = await pw.webkit.launch({ headless: true });
    const sel = {
      root_rsid: 'USAREC',
      bde: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
      bn: null,
      co: null,
      stn: null,
      active: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
      effective_rsid: '1BDE'
    }
    const ctx = await browser.newContext();
    await ctx.addInitScript(s => { localStorage.setItem('taaip.unitSelection.v1', s) }, JSON.stringify(sel))
    const page = await ctx.newPage();
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1200);
    // open BN combobox
    const labels = await page.$$('label')
    let bnHandle = null
    for(const lh of labels){
      const txt = (await lh.innerText()).trim()
      if (txt.toUpperCase() === 'BN'){
        const h = await lh.evaluateHandle(node => {
          const parent = node.closest('.MuiFormControl-root') || node.parentElement
          if (!parent) return null
          return parent.querySelector('div[role="combobox"]')
        })
        bnHandle = h.asElement ? h.asElement() : h
        break
      }
    }
    if (!bnHandle){ console.log('BN combobox not found'); await page.screenshot({ path: 'tools/e2e_results/org_selector_full_chain/local_before.png', fullPage:true }); await browser.close(); return }
    await bnHandle.evaluate(el => el.click())
    await page.waitForTimeout(600)
    const bns = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n => n.innerText))
    fs.mkdirSync('tools/e2e_results/org_selector_full_chain', { recursive: true })
    fs.writeFileSync('tools/e2e_results/org_selector_full_chain/bns_from_local.json', JSON.stringify(bns, null, 2))
    await page.screenshot({ path: 'tools/e2e_results/org_selector_full_chain/local_after.png', fullPage:true })
    await browser.close()
    console.log('ok')
  }catch(e){ console.error(e && (e.stack||e.message)); process.exit(1) }
})();
