const fs = require('fs')
const { webkit } = require('playwright')

async function main(){
  const base = process.env.BASE_URL || 'http://127.0.0.1:8001'
  const browser = await webkit.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()
  page.on('console', msg => console.log('PAGE>', msg.text()))

  async function fetchApi(path){
    const url = base + path
    console.log('API fetch', url)
    const res = await page.evaluate(async (u)=>{ try{ const r = await fetch(u); const j = await r.json(); return { status: r.status, json: j } }catch(e){ return { error: String(e) } } }, url)
    return res
  }

  try{
    const routeMA = '/operations/mission-analysis'
    console.log('\n== Visiting', base+routeMA)
    await page.goto(base+routeMA, { waitUntil: 'domcontentloaded', timeout: 120000 })
    await page.waitForTimeout(2000)
    const apiMA = await fetchApi('/api/performance/mission-assessment')
    try{ fs.writeFileSync('./tools/e2e-mission-analysis.json', JSON.stringify(apiMA, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-mission-analysis.png', fullPage: true }) }catch(e){}
    const pageTextMA = await page.evaluate(()=>document.body.innerText || '')
    try{ fs.writeFileSync('./tools/e2e-mission-analysis-page-text.txt', pageTextMA) }catch(e){}
    const ma = { route: routeMA, usable: false, checks: [] }
    try{
      const header = pageTextMA.indexOf('Mission Analysis') !== -1
      const apiOk = apiMA && apiMA.json
      let kpiFound = false
      try{
        if (apiMA && apiMA.json && apiMA.json.kpis){
          const kt = apiMA.json.kpis
          const vals = []
          // Collect possible fields
          if (kt.score !== undefined) vals.push(kt.score)
          if (kt.leads !== undefined) vals.push(kt.leads)
          if (kt.contracts !== undefined) vals.push(kt.contracts)
          if (kt.latest_date !== undefined) vals.push(kt.latest_date)
          if (kt.latest_total !== undefined) vals.push(kt.latest_total)
          for (const v of vals){ if (v !== undefined && v !== null && String(v) !== '' && pageTextMA.indexOf(String(v)) !== -1) { kpiFound = true; break } }
        }
      }catch(e){}
      ma.usable = header && apiOk && kpiFound
      ma.checks.push({ header, apiOk: Boolean(apiOk), kpiFound })
    }catch(e){ ma.error = String(e) }
    try{ fs.writeFileSync('./tools/e2e-mission-analysis-checks.json', JSON.stringify(ma, null, 2)) }catch(e){}
    console.log('Mission Analysis result', JSON.stringify(ma, null, 2))
    await page.reload({ waitUntil: 'load' })
    await page.waitForTimeout(600)
    try{ await page.screenshot({ path: './tools/e2e-mission-analysis-after-reload.png', fullPage: true }) }catch(e){}
  }catch(e){ console.error('Mission Analysis test error', String(e)) }

  await browser.close()
}

main().catch(e=>{ console.error(e); process.exit(2) })
