// Lightweight Playwright E2E script to exercise FoundationUploadPanel mapping flow.
// Usage: node apps/web/scripts/playwright_mapping_e2e.cjs --url http://localhost:5000 --csv ../test-fixtures/school_messy.csv
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright')

async function run(){
  const argv = require('minimist')(process.argv.slice(2))
  const url = argv.url || process.env.TEST_URL || 'http://127.0.0.1:5000/'
  const csv = argv.csv || 'apps/web/test-fixtures/school_messy.csv'
  const absCsv = path.resolve(csv)
  if(!fs.existsSync(absCsv)){
    console.error('CSV fixture not found:', absCsv)
    process.exit(2)
  }

  const browser = await chromium.launch()
  const page = await browser.newPage()
  const events = []
  page.on('console', m=> events.push({type:'console', text:m.text()}))
  page.on('pageerror', e=> events.push({type:'pageerror', message:String(e.stack||e)}))
  page.on('response', r=>{ if(r.status()>=400) events.push({type:'response', url:r.url(), status:r.status()}) })

  try{
    await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 })
    // find the foundation file input
    const fileInput = await page.$('input[data-testid="foundation-file-input"]')
    if(!fileInput){
      console.error('file input not found')
      process.exit(3)
    }
    await fileInput.setInputFiles(absCsv)

    // choose dataset select if present
    const datasetSelect = await page.$('select[aria-label="Dataset"]')
    if(datasetSelect){
      await datasetSelect.selectOption('school_program_fact')
    }

    // click Preview button
    const previewBtn = await page.$('button:has-text("Preview")')
    if(previewBtn) await previewBtn.click()
    await page.waitForTimeout(1500)

    // click Commit
    const commitBtn = await page.$('button:has-text("Commit")')
    if(commitBtn) await commitBtn.click()
    // wait for network response to commit endpoint
    await page.waitForTimeout(2000)

    const shot = '/tmp/playwright_mapping_e2e.png'
    await page.screenshot({ path: shot, fullPage: true }).catch(()=>{})
    fs.writeFileSync('playwright_mapping_result.json', JSON.stringify(events, null, 2))
    console.log('wrote playwright_mapping_result.json and screenshot', shot)
  }catch(e){
    console.error('error', e)
    fs.writeFileSync('playwright_mapping_result.json', JSON.stringify({error: String(e)}))
    process.exit(4)
  }finally{
    await browser.close()
  }
}

run()
