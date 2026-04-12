const pw = require('playwright');
(async ()=>{
  const browser = await pw.webkit.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/command-center', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  const combos = await page.$$('div[role="combobox"]');
  const out = [];
  for(const c of combos){
    const dis = await c.getAttribute('aria-disabled');
    const txt = await c.innerText();
    out.push({ aria_disabled: dis, text: txt.trim().slice(0,100) })
  }
  console.log(JSON.stringify(out, null, 2))
  await page.screenshot({ path: 'tools/e2e_results/inspect/combos_dump.png', fullPage:true })
  await browser.close();
})();
