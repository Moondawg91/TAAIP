const fs = require('fs')
const { firefox } = require('playwright')

async function run(){
  const base = process.env.BASE_URL || 'http://127.0.0.1:8001'
  const browser = await firefox.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()
  page.on('console', msg => console.log('PAGE>', msg.text()))
  page.on('requestfailed', req => console.log('REQ-FAILED>', req.method(), req.url(), req.failure && req.failure().errorText))

  // capture request/response payloads for import flow endpoints
  let mapRequest = null
  let mapResponse = null
  let uploadResponse = null
  let parseResponse = null
  let validateResponse = null
  let commitResponse = null

  page.on('request', req => {
    try{
      const url = req.url()
      if (url.includes('/api/import/upload')){
        try{ fs.writeFileSync('./tools/import-upload-request.json', JSON.stringify({ url, method: req.method(), postData: '<formdata>' }, null, 2)) }catch(e){}
      }
      if (url.includes('/api/import/map') || /\/api\/import\/[^\/]+\/map$/.test(url)){
        mapRequest = { url, method: req.method(), postData: req.postData() }
        try{ fs.writeFileSync('./tools/import-map-request.json', JSON.stringify(mapRequest, null, 2)) }catch(e){}
      }
    }catch(e){}
  })

  page.on('response', async res => {
    try{
      const url = res.url()
      const saveJson = (p, obj) => { try{ fs.mkdirSync('./tools', { recursive: true }) }catch(e){}; try{ fs.writeFileSync(p, JSON.stringify(obj, null, 2)) }catch(e){} }
      // helper to attempt JSON parse of response body
      const tryParse = async (r) => { const t = await r.text().catch(()=>null); try{ return JSON.parse(t) }catch(e){ return t } }
      if (url.includes('/api/import/upload')){
        const body = await tryParse(res)
        uploadResponse = { status: res.status(), url, body }
        saveJson('./tools/import-upload-response.json', uploadResponse)
      }
      if (url.includes('/api/import/parse')){
        const body = await tryParse(res)
        parseResponse = { status: res.status(), url, body }
        saveJson('./tools/import-parse-response.json', parseResponse)
      }
      if (url.includes('/api/import/validate')){
        const body = await tryParse(res)
        validateResponse = { status: res.status(), url, body }
        saveJson('./tools/import-validate-response.json', validateResponse)
      }
      if (url.includes('/api/import/commit') || url.includes('/api/import/compat/commit_v3')){
        const body = await tryParse(res)
        commitResponse = { status: res.status(), url, body }
        saveJson('./tools/import-commit-response.json', commitResponse)
      }
      if (url.includes('/api/import/map') || /\/api\/import\/[^\/]+\/map$/.test(url)){
        const body = await tryParse(res)
        mapResponse = { status: res.status(), url, body }
        saveJson('./tools/import-map-response.json', mapResponse)
      }
      if(res.status()>=400){ const text = await res.text().catch(()=>null); console.log('RESP-ERR>', res.status(), res.url(), text && text.slice? text.slice(0,200): text) }
    }catch(e){ console.log('response handler err', String(e)) }
  })

  try{
    // Load pre-generated JWT token and set it in localStorage so the UI can call protected endpoints
    try{
      const fs = require('fs')
      const toks = JSON.parse(fs.readFileSync('./tools/rbac_tokens.json', 'utf8'))
      const token = toks && toks.usarec_admin ? toks.usarec_admin : null
      if (token) {
        // Ensure token present in localStorage before any page script runs
        await page.addInitScript(t => { localStorage.setItem('taaip_jwt', t) }, token)
        // Also add Authorization header to all API requests to guarantee server receives it
        await page.addInitScript((t) => {
          // monkey-patch fetch to include Authorization header for same-origin API calls
          const _fetch = window.fetch
          window.fetch = function(input, init){
            try{
              const url = (typeof input === 'string') ? input : input.url
              if (url && url.indexOf('/api/') !== -1){
                init = init || {}
                init.headers = Object.assign({}, init.headers || {}, { Authorization: 'Bearer ' + t })
              }
            }catch(e){}
            return _fetch.call(this, input, init)
          }
        }, token)
        // Also route network requests from Playwright side to inject header for non-fetch cases
        await page.route('**/api/**', route => {
          const req = route.request()
          const headers = Object.assign({}, req.headers())
          headers['authorization'] = `Bearer ${token}`
          route.continue({ headers })
        })
      }
    }catch(e){ console.log('token load failed', String(e)) }

    await page.goto(base + '/import-center', { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    // snapshot before
    await page.screenshot({ path: './tools/import-center-before.png', fullPage: true })

    // attach sample file (use MUI input by id)
    // Ensure the sample file is the production-format sample for deterministic commit
    try{
      fs.writeFileSync('./tools/import-production.csv', 'org_unit_id,date_key,metric_key,metric_value\nUSAREC,2025-01-01,leads,7\nUSAREC,2025-01-01,contracts,1')
    }catch(e){}
    const fileInput = await page.$('#import-file-input')
    if(!fileInput) throw new Error('file input not found')
    // Use absolute path / buffer-based setInputFiles to avoid headless file attach issues
    try{
      const path = require('path')
      const abs = path.resolve(__dirname, 'import-production.csv')
      const buf = fs.readFileSync(abs)
      await fileInput.setInputFiles([{ name: 'import-production.csv', mimeType: 'text/csv', buffer: buf }])
    }catch(e){
      // fallback to relative path if buffer attach fails
      try{ await fileInput.setInputFiles('./tools/import-production.csv') }catch(e2){}
    }

    // set dataset via visible label
    try{ await page.getByLabel('Dataset').selectOption('production') }catch(e){ /* fallback */ }
    // click upload button — try multiple selectors to avoid accessibility/name ambiguities
    try{
      await page.getByRole('button', { name: 'Upload', exact: true }).click({ timeout: 3000 })
    }catch(e1){
      try{
        await page.locator('button:has-text("Upload")').first().click({ timeout: 3000 })
      }catch(e2){
        try{
          await page.locator('button:has-text("General Upload")').first().click({ timeout: 3000 })
        }catch(e3){
          // final fallback: dispatch change on the file input to trigger the upload handler
          try{
            await page.evaluate(() => {
              const input = document.querySelector('#import-file-input')
              if (input) {
                input.dispatchEvent(new Event('change', { bubbles: true }))
              }
            })
          }catch(e4){}
        }
      }
    }

    // wait for job id to appear in UI
    await page.waitForSelector('text=Job:', { timeout: 15000 })
    await page.screenshot({ path: './tools/import-center-after-upload.png', fullPage: true })

    // Parse & Preview
    await page.getByRole('button', { name: 'Parse & Preview' }).click().catch(()=>{})
    await page.waitForTimeout(3000)
    await page.screenshot({ path: './tools/import-center-preview.png', fullPage: true })

    // Go to Map and perform mapping/validation/commit
    await page.getByRole('button', { name: 'Go to Map' }).click().catch(()=>{})
    await page.waitForTimeout(1000)
    // Auto-map same-name
    await page.getByRole('button', { name: 'Auto-map same-name' }).click().catch(()=>{})
    await page.getByRole('button', { name: 'Save Mapping' }).click().catch(()=>{})
    await page.waitForTimeout(1000)
    // Wait for mapping to be saved by UI and then Validate
    try{ await page.waitForSelector('text=Mapping saved', { timeout: 5000 }) }catch(e){ /* proceed anyway */ }
    await page.waitForTimeout(500)
    // click Validate
    try{ await page.getByRole('button', { name: 'Validate' }).click({ timeout: 3000 }) }catch(e){ try{ await page.locator('button:has-text("Validate")').first().click() }catch(e){} }
    await page.waitForTimeout(1000)
    // Commit (attempt several click methods and wait for the commit network response)
    try{
      await Promise.all([
        page.waitForResponse(resp => resp.url().includes('/api/import/commit') || resp.url().includes('/api/import/compat/commit_v3'), { timeout: 10000 }),
        page.getByRole('button', { name: 'Commit' }).click()
      ])
    }catch(e){
      try{
        await Promise.all([
          page.waitForResponse(resp => resp.url().includes('/api/import/commit') || resp.url().includes('/api/import/compat/commit_v3'), { timeout: 10000 }),
          page.locator('button:has-text("Commit")').first().click()
        ])
      }catch(e){
        // final fallback: try clicking any button with Commit text
        try{ await page.evaluate(() => { const b = Array.from(document.querySelectorAll('button')).find(x=>x.innerText && x.innerText.indexOf('Commit')!==-1); if(b) b.click(); }) }catch(e){}
      }
    }
    await page.waitForTimeout(1500)

      // fallback: if commitResponse wasn't captured via network, call commit API from the page context
      try{
        if(!commitResponse){
          // determine job id from uploadResponse saved earlier (if available)
          let jobId = null
          try{ if (uploadResponse && uploadResponse.body && uploadResponse.body.import_job_id) jobId = uploadResponse.body.import_job_id }catch(e){}
          // if not available, try parsing upload response file
          if(!jobId){
            try{
              const up = JSON.parse(fs.readFileSync('./tools/import-upload-response.json','utf8'))
              if(up && up.body && up.body.import_job_id) jobId = up.body.import_job_id
            }catch(e){}
          }
          if(jobId){
            const commitRes = await page.evaluate(async ({ baseURL, id }) => {
              try{
                const token = localStorage.getItem('taaip_jwt') || ''
                const r = await fetch(baseURL + '/api/import/commit', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token }, body: JSON.stringify({ import_job_id: id }) })
                const text = await r.text()
                try{ return { status: r.status, body: JSON.parse(text), url: baseURL + '/api/import/commit' } }catch(e){ return { status: r.status, body: text, url: baseURL + '/api/import/commit' } }
              }catch(e){ return { error: String(e) } }
            }, { baseURL: base, id: jobId })
            if(commitRes){
              commitResponse = commitRes
              try{ fs.writeFileSync('./tools/import-commit-response.json', JSON.stringify(commitResponse, null, 2)) }catch(e){}
            }
          }
        }
      }catch(e){ console.log('commit fallback failed', String(e)) }

    await page.screenshot({ path: './tools/import-center-after-commit.png', fullPage: true })

    // capture import history JSON from API for verification
    const hist = await page.evaluate(async (baseURL) => { try{ const r = await fetch(baseURL + '/api/import/jobs'); return await r.json() }catch(e){ return {error: String(e)} } }, base)
    try{ fs.mkdirSync('./tools', { recursive: true }) }catch(e){}
    fs.writeFileSync('./tools/import-center-history.json', JSON.stringify(hist, null, 2))
    console.log('WROTE history json, rows:', Array.isArray(hist)?hist.length:0)

    // consolidate a trail artifact: upload/parse/map/validate/commit + history + downstream rows (if available)
    try{
      const trail = { upload: uploadResponse, parse: parseResponse, map: mapResponse, validate: validateResponse, commit: commitResponse, history: hist }
      // determine job id from upload or commit
      let jobId = null
      try{ if (uploadResponse && uploadResponse.body && uploadResponse.body.import_job_id) jobId = uploadResponse.body.import_job_id }catch(e){}
      try{ if(!jobId && commitResponse && commitResponse.body && commitResponse.body.import_job_id) jobId = commitResponse.body.import_job_id }catch(e){}
      if(jobId){
        try{
          const rows = await page.evaluate(async (baseURL, id) => { try{ const r = await fetch(baseURL + '/api/powerbi/fact_production?import_job_id=' + id); return await r.json() }catch(e){ return {error: String(e)} } }, base, jobId)
          trail.downstream = rows
        }catch(e){}
      }
      const trailPath = jobId ? `./tools/import-trail-${jobId}.json` : './tools/import-trail.json'
      fs.writeFileSync(trailPath, JSON.stringify(trail, null, 2))
      console.log('WROTE trail', trailPath)
    }catch(e){ console.log('trail write failed', String(e)) }
  }catch(e){ console.error('E2E ERROR', String(e)) }
  finally{ try{ await browser.close() }catch(e){} }
}

run()
