const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async ()=>{
  const base = process.env.PLAYWRIGHT_BASE || 'http://localhost:5000';
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try{
    page.on('console', m=> console.log('PAGE_CONSOLE:', m.text()));
    page.on('pageerror', e=> console.log('PAGE_ERROR:', String(e.stack||e)));
    // navigate to site root and click the Imports Center link to ensure client-side routing loads correctly
    await page.goto(base, { waitUntil: 'networkidle' })
    // click nav link 'Imports Center' if present
    try{
      await page.click('text=Imports Center')
    }catch(e){
      // try alternate link text
      try{ await page.click('text=Import Center') }catch(e2){}
    }
    // wait for DocumentUploadPanel
    await page.waitForSelector('input[data-testid="document-file-input"]', { timeout: 20000 });
    // prepare fixture
    const fixture = path.resolve(__dirname, '../test-fixtures/test_document.txt');
    if(!fs.existsSync(fixture)){
      fs.writeFileSync(fixture, 'Playwright fixture');
    }
    const input = await page.$('input[data-testid="document-file-input"]');
    await input.setInputFiles(fixture);
    // click the nearest Upload button adjacent to the input
    await page.$eval('input[data-testid="document-file-input"]', (el)=>{ const btn = el.closest('div')?.querySelector('button'); if(btn) btn.click(); })
    // wait for the uploaded filename to appear in the table
    let found = false
    try{
      await page.waitForSelector(`text=${path.basename(fixture)}`, { timeout: 10000 })
      found = true
    }catch(e){ found = false }
    console.log('document_listed:', found);
    await browser.close();
    process.exit(found?0:2);
  }catch(e){
    console.error('e2e error', e);
    await browser.close();
    process.exit(3);
  }
})()
