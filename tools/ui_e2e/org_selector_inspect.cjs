const fs = require('fs');
const pw = require('playwright');
(async ()=>{
  try{
    const browser = await pw.webkit.launch({ headless: true });
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForTimeout(1200);
    const info = await page.evaluate(()=>{
      const nodes = Array.from(document.querySelectorAll('select, button[aria-haspopup="listbox"], [role="combobox"], [role="listbox"]'));
      return nodes.map(n=>({ tag: n.tagName, role: n.getAttribute('role'), ariaHasPopup: n.getAttribute('aria-haspopup'), outer: (n.outerHTML||'').slice(0,1000) }));
    });
    fs.mkdirSync('tools/e2e_results/inspect', { recursive: true });
    fs.writeFileSync('tools/e2e_results/inspect/elements.json', JSON.stringify(info, null, 2));
    await page.screenshot({ path: 'tools/e2e_results/inspect/page.png', fullPage: true });
    await browser.close();
    console.log('OK');
  }catch(e){
    console.error('ERR', e && (e.stack||e.message));
    process.exit(1);
  }
})();
