const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  try{
    const browser = await pw.webkit.launch({ headless: true });
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1200);
    // find brigade combobox (first combobox that is not disabled)
    const combos = await page.$$('div[role="combobox"]');
    let target = null;
    for(const c of combos){
      const disabled = await c.getAttribute('aria-disabled')
      if (!disabled || disabled === 'false') { target = c; break }
    }
    if (!target){ console.log('No enabled combobox found'); await page.screenshot({ path: 'tools/e2e_results/inspect/after_click.png', fullPage:true }); await browser.close(); return }
    await target.click();
    await page.waitForTimeout(800);
    // collect listbox items (brigades)
    const items = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n => ({ text: n.innerText, html: n.outerHTML ? n.outerHTML.slice(0,1000) : '' })));
    fs.writeFileSync('tools/e2e_results/inspect/after_click_items.json', JSON.stringify(items, null, 2));
    await page.screenshot({ path: 'tools/e2e_results/inspect/after_click.png', fullPage:true });
    if (items.length > 1){
      // select first brigade (index 1)
      await page.$$eval('ul[role="listbox"] li', els => els[1].click());
      await page.waitForTimeout(800);
      // now find BN combobox by label
      const labels = await page.$$('label')
      let bnHandle = null
      for(const lh of labels){
        const txt = (await lh.innerText()).trim()
        if (txt.toUpperCase() === 'BN'){
          const parent = await lh.evaluateHandle(node => node.closest('.MuiFormControl-root') || node.parentElement)
          const cb = await parent.asElement().$('div[role="combobox"]')
          bnHandle = cb
          break
        }
      }
      if (bnHandle){
        await bnHandle.click();
        await page.waitForTimeout(800);
        const bns = await page.$$eval('ul[role="listbox"] li', nodes => nodes.map(n => n.innerText.trim()));
        fs.writeFileSync('tools/e2e_results/inspect/after_bde_bns.json', JSON.stringify(bns, null, 2));
        await page.screenshot({ path: 'tools/e2e_results/inspect/after_bde_bns.png', fullPage:true });
      }
    }
    await browser.close();
    console.log('OK', items.length);
  }catch(e){ console.error('ERR', e && (e.stack||e.message)); process.exit(1) }
})();
