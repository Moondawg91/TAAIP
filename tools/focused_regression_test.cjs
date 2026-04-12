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

  const tests = [
    { route: '/budget/roi-overview', api: '/api/v1/roi/kpis?unit_rsid=USAREC', name: 'roi-overview' },
    { route: '/performance/funnel-metrics', api: '/api/v1/roi/funnel?unit_rsid=USAREC', name: 'funnel-metrics' },
    { route: '/performance/production-dashboard', api: '/api/powerbi/fact_production?unit_rsid=USAREC', name: 'production-dashboard' },
    { route: '/data-hub', api: '/api/import/jobs', name: 'datahub' },
    { route: '/operations/mission-analysis', api: '/api/performance/mission-assessment', name: 'mission-analysis' }
  ]

  for(const t of tests){
    try{
      console.log('\n== Visiting', base + t.route)
      await page.goto(base + t.route, { waitUntil: 'domcontentloaded', timeout: 120000 })
      await page.waitForTimeout(1500)
      const apiRes = await fetchApi(t.api)
      try{ fs.writeFileSync(`./tools/e2e-${t.name}.json`, JSON.stringify(apiRes, null, 2)) }catch(e){}
      try{ await page.screenshot({ path: `./tools/e2e-${t.name}.png`, fullPage: true }) }catch(e){}
      const pageText = await page.evaluate(()=>document.body.innerText || '')
      const result = { route: t.route, usable: false, checks: [] }

      // simple checks per type
      if (t.name === 'roi-overview'){
        if (apiRes && apiRes.json && apiRes.json.kpis){
          const k = apiRes.json.kpis
          const vals = []
          if (k.spend_total !== undefined) vals.push(String(k.spend_total))
          if (k.leads_total !== undefined) vals.push(String(k.leads_total))
          if (k.contracts_total !== undefined) vals.push(String(k.contracts_total))
          const matches = vals.map(v => ({ value: v, found: pageText.indexOf(v)!==-1 }))
          result.checks = matches
          result.usable = matches.every(m=>m.found)
        }
      } else if (t.name === 'funnel-metrics'){
        if (apiRes && apiRes.json && apiRes.json.funnel){
          const f = apiRes.json.funnel
          const keys = ['leads','contacts','appointments','applicants','contracts']
          const matches = keys.map(k => ({ key: k, value: String(f[k]||''), found: String(pageText).indexOf(String(f[k]||''))!==-1 }))
          result.checks = matches
          result.usable = matches.every(m=>m.found)
        }
      } else if (t.name === 'production-dashboard'){
        let rows = 0
        if (apiRes && apiRes.json){
          if (Array.isArray(apiRes.json)) rows = apiRes.json.length
          else if (apiRes.json.data && Array.isArray(apiRes.json.data)) rows = apiRes.json.data.length
        }
        const hasHeader = pageText.indexOf('Recent Production Rows') !== -1
        const hasCount = rows ? pageText.indexOf(String(rows)) !== -1 : true
        result.checks.push({ hasHeader, hasCount, rows })
        result.usable = hasHeader && hasCount
      } else if (t.name === 'datahub'){
        const headerPresent = pageText.indexOf('Data Hub') !== -1 || pageText.indexOf('Import Center') !== -1
        result.checks.push({ headerPresent })
        result.usable = headerPresent && Boolean(apiRes)
      } else if (t.name === 'mission-analysis'){
        const header = pageText.indexOf('Mission Analysis') !== -1
        let kpiFound = false
        try{
          if (apiRes && apiRes.json && apiRes.json.kpis){
            const kt = apiRes.json.kpis
            const vals = []
            if (kt.latest_date !== undefined) vals.push(String(kt.latest_date))
            if (kt.latest_total !== undefined) vals.push(String(kt.latest_total))
            for(const v of vals){ if (v && pageText.indexOf(v)!==-1) { kpiFound = true; break } }
          }
        }catch(e){}
        result.checks.push({ header, kpiFound })
        result.usable = header && kpiFound
      }

      try{ fs.writeFileSync(`./tools/e2e-${t.name}-checks.json`, JSON.stringify(result, null, 2)) }catch(e){}
      console.log(`${t.name} result`, JSON.stringify(result, null, 2))
    }catch(e){ console.error(`${t.name} test error`, String(e)) }
  }

  await browser.close()
}

main().catch(e=>{ console.error(e); process.exit(2) })
