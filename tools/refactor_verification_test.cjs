const fs = require('fs')
const { webkit } = require('playwright')

async function run(){
  const base = process.env.BASE_URL || 'http://127.0.0.1:8001'
  const browser = await webkit.launch({ headless: true })
  const ctx = await browser.newContext()
  const page = await ctx.newPage()
  page.on('console', m => console.log('PAGE>', m.text()))

  const routes = [
    { route: '/import-center', name: 'import-center' },
    { route: '/resources/docs', name: 'resources-docs' },
    { route: '/training/modules', name: 'training-modules' },
    { route: '/data-hub', name: 'legacy-data-hub' },
    { route: '/resources/regulations', name: 'legacy-resource-regulations' }
  ]

  const results = {}

  for(const r of routes){
    try{
      const url = base + r.route
      console.log('\nVisiting', url)
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 })
      await page.waitForTimeout(1500)
      const screenshotPath = `./tools/refactor-${r.name}.png`
      try{ await page.screenshot({ path: screenshotPath, fullPage: true }) }catch(e){ console.error('screenshot failed', e) }

      // capture final URL to detect redirects
      const finalUrl = page.url()
      const bodyText = await page.evaluate(()=>document.body.innerText || '')

      // collect nav/link texts (anchors) and unique hrefs
      const anchors = await page.evaluate(()=>{
        const a = Array.from(document.querySelectorAll('a'))
        return a.map(x=>({ text: x.innerText.trim(), href: x.getAttribute('href') }))
      })

      // try to capture a sidebar node if present
      const sidebarText = await page.evaluate(()=>{ const el = document.querySelector('[data-testid="section-sidebar"]') || document.querySelector('.sidebar') || document.querySelector('#sidebar') || document.querySelector('[role="navigation"]'); return el ? el.innerText : '' })

      results[r.name] = {
        route: r.route,
        finalUrl,
        bodyTextSample: bodyText.slice(0,400),
        anchors: anchors.slice(0,80),
        sidebarTextSample: sidebarText.slice(0,800),
        screenshot: screenshotPath,
        ok: true
      }

    }catch(e){
      console.error('visit error', r.route, e)
      results[r.name] = { route: r.route, error: String(e), ok: false }
    }
  }

  // Evaluate nav intent: expected items
  const expected = ['Import Center','Document Library','Training Modules']
  const navAnalysis = await (async ()=>{
    // go to root to read canonical sidebar
    try{
      await page.goto(base+'/', { waitUntil: 'networkidle' })
      await page.waitForTimeout(1500)
      // try expanding Resources & Training if collapsed
      try{ await page.click('button[aria-label="Resources & Training"]', { timeout: 500 }).catch(()=>{}) }catch(e){}
      await page.waitForTimeout(400)
      const sidebarText = await page.evaluate(()=>{ const el = document.querySelector('[data-testid="section-sidebar"]') || document.querySelector('.sidebar') || document.querySelector('#sidebar') || document.querySelector('[role="navigation"]'); return el ? el.innerText : '' })
      const html = await page.content()
      const found = {}
      for(const e of expected) found[e] = (sidebarText && sidebarText.indexOf(e)!==-1) || (html && html.indexOf(e)!==-1)
      // absent legacy items
      const legacy = ['Regulations','Manuals','SOPs','User Manual','Data Hub']
      const legacyFound = {}
      for(const l of legacy) legacyFound[l] = (sidebarText && sidebarText.indexOf(l)!==-1) || (html && html.indexOf(l)!==-1)
      return { sidebarTextSample: (sidebarText||'').slice(0,2000), htmlSample: html.slice(0,8000), found, legacyFound }
    }catch(e){ return { error: String(e) } }
  })()

  const out = { timestamp: new Date().toISOString(), base, results, navAnalysis }
  try{ fs.writeFileSync('./tools/refactor-checks.json', JSON.stringify(out, null, 2)) }catch(e){ console.error('write checks failed', e) }
  console.log('\nWrote ./tools/refactor-checks.json')
  await browser.close()
}

run().catch(e=>{ console.error(e); process.exit(2) })
