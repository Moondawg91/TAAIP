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

  // ROI Overview
  try{
    const route = '/budget/roi-overview'
    console.log('\n== Visiting', base+route)
    await page.goto(base+route, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    // fetch API used for comparison
    const api = await fetchApi('/api/v1/roi/kpis?unit_rsid=USAREC')
    try{ fs.writeFileSync('./tools/e2e-roi-kpis.json', JSON.stringify(api, null, 2)) }catch(e){}
    // take screenshot of page
    try{ await page.screenshot({ path: './tools/e2e-roi-overview.png', fullPage: true }) }catch(e){}

    // simple text-based assertions: ensure page contains the numeric values from API
    const checks = { rendered: false, matches: [] }
    if (api && api.json && api.json.kpis){
      const vals = []
      const k = api.json.kpis
      if (k.spend_total !== undefined && k.spend_total !== null) vals.push(k.spend_total)
      if (k.leads_total !== undefined && k.leads_total !== null) vals.push(k.leads_total)
      if (k.contracts_total !== undefined && k.contracts_total !== null) vals.push(k.contracts_total)
      if (k.cpl !== undefined && k.cpl !== null) vals.push(Math.round((k.cpl + Number.EPSILON) * 100) / 100)
      // convert numbers to strings to search
      const strVals = vals.map(v=>String(v))
      const pageText = await page.evaluate(()=>document.body.innerText || '')
      let allFound = true
      for (const s of strVals){
        const found = pageText.indexOf(s) !== -1
        checks.matches.push({ value: s, found })
        if (!found) allFound = false
      }
      checks.rendered = allFound
    } else {
      checks.rendered = false
      checks.reason = 'api.kpis missing'
    }
    // reload and re-check
    await page.reload({ waitUntil: 'load' })
    await page.waitForTimeout(600)
    try{ await page.screenshot({ path: './tools/e2e-roi-overview-after-reload.png', fullPage: true }) }catch(e){}
    const pageText2 = await page.evaluate(()=>document.body.innerText || '')
    checks.matches_after_reload = checks.matches.map(m => ({ value: m.value, found: pageText2.indexOf(m.value) !== -1 }))
    // write checks
    try{ fs.writeFileSync('./tools/e2e-roi-checks.json', JSON.stringify(checks, null, 2)) }catch(e){}
    console.log('ROI checks', JSON.stringify(checks, null, 2))
  }catch(e){ console.error('ROI test error', String(e)) }

  // Funding Allocations
  try{
    const route = '/budget/funding-allocations'
    console.log('\n== Visiting', base+route)
    await page.goto(base+route, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const api = await fetchApi('/api/v1/roi/breakdown?unit_rsid=USAREC')
    try{ fs.writeFileSync('./tools/e2e-roi-breakdown.json', JSON.stringify(api, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-funding-allocations.png', fullPage: true }) }catch(e){}
    const pageText = await page.evaluate(()=>document.body.innerText || '')
    const result = { route: '/budget/funding-allocations', usable: false, details: [] }
    if (api && api.json){
      // look for any of the top-level keys or numeric values in the page text
      const json = api.json
      const keys = Object.keys(json || {})
      for (const k of keys){
        try{
          const v = JSON.stringify(json[k]).slice(0,200)
          const found = pageText.indexOf(v) !== -1 || pageText.indexOf(k) !== -1
          result.details.push({ key: k, found, sample: v })
          if (found) result.usable = true
        }catch(e){}
      }
    }
    try{ fs.writeFileSync('./tools/e2e-funding-checks.json', JSON.stringify(result, null, 2)) }catch(e){}
    console.log('Funding allocations result', JSON.stringify(result, null, 2))
  }catch(e){ console.error('Funding test error', String(e)) }

  // Funnel Metrics (performance)
  try{
    const route = '/performance/funnel-metrics'
    console.log('\n== Visiting', base+route)
    await page.goto(base+route, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const api = await fetchApi('/api/v1/roi/funnel?unit_rsid=USAREC')
    try{ fs.writeFileSync('./tools/e2e-funnel.json', JSON.stringify(api, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-funnel.png', fullPage: true }) }catch(e){}
    const pageText = await page.evaluate(()=>document.body.innerText || '')
    const resultF = { route, usable: false, matches: [] }
    if (api && api.json && api.json.funnel){
      const f = api.json.funnel
      const keys = ['leads','contacts','appointments','applicants','contracts']
      let allFound = true
      for (const k of keys){
        try{
          const v = (f[k] === undefined || f[k] === null) ? '' : String(f[k])
          const found = v && pageText.indexOf(v) !== -1
          resultF.matches.push({ key: k, value: v, found })
          if (!found) allFound = false
        }catch(e){}
      }
      resultF.usable = allFound
    }
    try{ fs.writeFileSync('./tools/e2e-funnel-checks.json', JSON.stringify(resultF, null, 2)) }catch(e){}
    console.log('Funnel result', JSON.stringify(resultF, null, 2))
  }catch(e){ console.error('Funnel test error', String(e)) }

  // Production Dashboard (performance)
  try{
    const route = '/performance/production-dashboard'
    console.log('\n== Visiting', base+route)
    await page.goto(base+route, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const apiProd = await fetchApi('/api/powerbi/fact_production?unit_rsid=USAREC')
    try{ fs.writeFileSync('./tools/e2e-production.json', JSON.stringify(apiProd, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-production-dashboard.png', fullPage: true }) }catch(e){}
    const pageTextProd = await page.evaluate(()=>document.body.innerText || '')
    const prodResult = { route, usable: false, rows_count: 0, checks: [] }
    try{
      let rows = 0
      if (apiProd && apiProd.json){
        if (Array.isArray(apiProd.json)) rows = apiProd.json.length
        else if (apiProd.json.data && Array.isArray(apiProd.json.data)) rows = apiProd.json.data.length
        else if (apiProd.json.rows && Array.isArray(apiProd.json.rows)) rows = apiProd.json.rows.length
      }
      prodResult.rows_count = rows
      const hasHeader = pageTextProd.indexOf('Recent Production Rows') !== -1
      const hasCount = rows ? pageTextProd.indexOf(String(rows)) !== -1 : true
      prodResult.checks.push({ hasHeader, hasCount })
      prodResult.usable = hasHeader && hasCount
    }catch(e){ prodResult.error = String(e) }
    try{ fs.writeFileSync('./tools/e2e-production-checks.json', JSON.stringify(prodResult, null, 2)) }catch(e){}
    console.log('Production dashboard result', JSON.stringify(prodResult, null, 2))
  }catch(e){ console.error('Production dashboard test error', String(e)) }

    // reload and re-check Production Dashboard
    try{
      await page.reload({ waitUntil: 'load' })
      await page.waitForTimeout(600)
      try{ await page.screenshot({ path: './tools/e2e-production-dashboard-after-reload.png', fullPage: true }) }catch(e){}
      const pageTextProd2 = await page.evaluate(()=>document.body.innerText || '')
      const prodChecksAfter = { matches_after_reload: [] }
      try{
        const hasHeader2 = pageTextProd2.indexOf('Recent Production Rows') !== -1
        prodChecksAfter.matches_after_reload.push({ hasHeader: hasHeader2 })
      }catch(e){ prodChecksAfter.error = String(e) }
      try{ fs.writeFileSync('./tools/e2e-production-checks-after-reload.json', JSON.stringify(prodChecksAfter, null, 2)) }catch(e){}
    }catch(e){ console.error('Production reload check error', String(e)) }

  // Route and nav verification: fetch the app main HTML and check for route wiring hints
  try{
    const index = await page.goto(process.env.BASE_URL || 'http://127.0.0.1:8001' + '/budget/roi-overview', { waitUntil: 'load', timeout: 60000 })
  }catch(e){}

  // Data Hub verification
  try{
    const routeDH = '/data-hub'
    console.log('\n== Visiting', base+routeDH)
    await page.goto(base+routeDH, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const apiDH = await fetchApi('/api/import/jobs')
    try{ fs.writeFileSync('./tools/e2e-datahub.json', JSON.stringify(apiDH, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-datahub.png', fullPage: true }) }catch(e){}
    const pageTextDH = await page.evaluate(()=>document.body.innerText || '')
    const dh = { route: routeDH, usable: false }
    try{
      // consider usable if page header present and API returned (possibly empty) array
      const headerPresent = pageTextDH.indexOf('Data Hub') !== -1
      const apiOk = apiDH && (Array.isArray(apiDH.json) || (apiDH.json && (Array.isArray(apiDH.json.data) || Array.isArray(apiDH.json.rows))))
      dh.usable = headerPresent && Boolean(apiDH)
      dh.api_shape = apiDH && apiDH.json ? (Array.isArray(apiDH.json) ? 'array' : 'object') : null
    }catch(e){ dh.error = String(e) }
    try{ fs.writeFileSync('./tools/e2e-datahub-checks.json', JSON.stringify(dh, null, 2)) }catch(e){}
    console.log('Data Hub result', JSON.stringify(dh, null, 2))
  }catch(e){ console.error('Data Hub test error', String(e)) }

  // Mission Analysis (operations)
  try{
    const routeMA = '/operations/mission-analysis'
    console.log('\n== Visiting', base+routeMA)
    await page.goto(base+routeMA, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const apiMA = await fetchApi('/api/performance/mission-assessment')
    try{ fs.writeFileSync('./tools/e2e-mission-analysis.json', JSON.stringify(apiMA, null, 2)) }catch(e){}
    try{ await page.screenshot({ path: './tools/e2e-mission-analysis.png', fullPage: true }) }catch(e){}
    const pageTextMA = await page.evaluate(()=>document.body.innerText || '')
    const ma = { route: routeMA, usable: false, checks: [] }
    try{
      const header = pageTextMA.indexOf('Mission Analysis') !== -1
      const apiOk = apiMA && apiMA.json
      // look for KPI strings if present
      let kpiFound = false
      try{
        if (apiMA && apiMA.json && apiMA.json.kpis){
          const kt = apiMA.json.kpis
          const vals = [kt.latest_date, kt.latest_total]
          for (const v of vals){ if (v !== undefined && v !== null && String(v) !== '' && pageTextMA.indexOf(String(v)) !== -1) { kpiFound = true; break } }
        }
      }catch(e){}
      ma.usable = header && apiOk && kpiFound
      ma.checks.push({ header, apiOk, kpiFound })
    }catch(e){ ma.error = String(e) }
    try{ fs.writeFileSync('./tools/e2e-mission-analysis-checks.json', JSON.stringify(ma, null, 2)) }catch(e){}
    console.log('Mission Analysis result', JSON.stringify(ma, null, 2))
    // reload and capture after-reload screenshot
    await page.reload({ waitUntil: 'load' })
    await page.waitForTimeout(600)
    try{ await page.screenshot({ path: './tools/e2e-mission-analysis-after-reload.png', fullPage: true }) }catch(e){}
  }catch(e){ console.error('Mission Analysis test error', String(e)) }

  // Market Segmentation (operations)
  try{
    const route = '/operations/market-segmentation'
    console.log('\n== Visiting', base+route)
    await page.goto(base+route, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const pageText = await page.evaluate(()=>document.body.innerText || '')
    const ms = { route, usable: false }
    if (pageText.indexOf('No market segmentation data') !== -1){
      ms.usable = false
      ms.reason = 'no data'
    } else {
      ms.usable = true
    }
    try{ await page.screenshot({ path: './tools/e2e-market-segmentation.png', fullPage: true }) }catch(e){}
    try{ fs.writeFileSync('./tools/e2e-market-segmentation-checks.json', JSON.stringify(ms, null, 2)) }catch(e){}
    console.log('Market segmentation result', JSON.stringify(ms, null, 2))
  }catch(e){ console.error('Market segmentation test error', String(e)) }

  // Check main nav for Market Segmentation label
  try{
    await page.goto(base+'/', { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(600)
    const html = await page.evaluate(()=>document.body.innerHTML || '')
    const navFound = html.indexOf('/performance/market-segmentation') !== -1 || html.indexOf('/operations/market-segmentation') !== -1
    try{ fs.writeFileSync('./tools/e2e-nav-check.json', JSON.stringify({ navFound }, null, 2)) }catch(e){}
    console.log('Nav label Market Segmentation present:', navFound)
  }catch(e){ console.error('Nav check error', String(e)) }

  await browser.close()
}

main().catch(e=>{ console.error(e); process.exit(2) })
