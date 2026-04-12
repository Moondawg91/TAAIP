const fs = require('fs')
const { webkit } = require('playwright')

async function run(){
  const base = process.env.BASE_URL || 'http://127.0.0.1:8001'
  const browser = await webkit.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()
  page.on('console', msg => console.log('PAGE LOG>', msg.text()))
  // capture network failures and responses >=400 for diagnostics
  const networkFailures = []
  page.on('requestfailed', request => {
    try{
      networkFailures.push({ type: 'requestfailed', url: request.url(), method: request.method(), failureText: request.failure() && request.failure().errorText ? request.failure().errorText : String(request.failure()), timestamp: Date.now() })
      console.log('NETWORK FAIL>', request.method(), request.url(), request.failure())
    }catch(e){}
  })
  page.on('response', async response => {
    try{
      const status = response.status()
      if (status >= 400){
        let postData = null
        try{ postData = response.request().postData() }catch(e){}
        let text = null
        try{ text = await response.text() }catch(e){}
        const entry = { type: 'response_error', url: response.url(), method: response.request().method(), status, postData, text: text && text.slice ? text.slice(0,2000) : text, timestamp: Date.now() }
        networkFailures.push(entry)
        console.log('NETWORK RESP>', entry.method, entry.url, entry.status)
      }
    }catch(e){}
  })

  // accept all dialogs
  page.on('dialog', async dialog => { console.log('Dialog:', dialog.message()); await dialog.accept() })

  const results = []

  async function visitAndLog(route, fn){
    const url = base + route
    console.log('\n== Visiting', url)
    await page.goto(url, { waitUntil: 'load', timeout: 60000 })
    await page.waitForTimeout(800)
    const res = { route, actions: [] }
    try{
      await fn(page, res)
    }catch(e){ res.error = String(e); console.error(e) }
    results.push(res)
  }

  async function clickDialogConfirm(page){
    try{
      const dlg = page.locator('div[role="dialog"]')
      if (await dlg.count() > 0){
        const btn = dlg.locator('button:has-text("Delete")').first()
        if (await btn.count() > 0) { await btn.click().catch(()=>{}) }
        else { const ok = dlg.locator('button:has-text("Confirm")').first(); if (await ok.count()>0) await ok.click().catch(()=>{}) }
        // attempt to wait for the DELETE response triggered by the confirm click
        try{
          await page.waitForResponse(r => (r.request().method() === 'DELETE' || r.request().method() === 'POST') && r.url().includes('/api/'), { timeout: 10000 })
        }catch(e){}
        // wait for dialog to disappear and give backend a moment to complete request
        try{ await dlg.waitFor({ state: 'detached', timeout: 6000 }) }catch(e){}
        // small pause to reduce chance of navigation cancelling in-flight requests
        await page.waitForTimeout(1200)
      }
    }catch(e){}
  }

  async function snap(name){
    const p = `./tools/e2e-snap-${name.replace(/[^a-z0-9\-]/ig,'_')}.png`
    try{ await page.screenshot({ path: p, fullPage: true }) }catch(e){}
  }

  // 1. Command TWG page (/command-center/twg)
  await visitAndLog('/command-center/twg', async (page, res) => {
    await page.getByLabel('New group name').waitFor({ timeout: 20000 })
    await page.getByLabel('New group name').fill('E2E WG')
    await page.getByRole('button', { name: 'Create Group' }).click()
    await page.waitForTimeout(900)
    // wait for items area to become available (Title input)
    await page.getByLabel('Title').waitFor({ timeout: 15000 }).catch(()=>{})
    res.actions.push('created group: E2E WG')
    await page.getByLabel('Title').fill('E2E Issue 1')
    await page.getByLabel('Owner').fill('tester')
    try{ await page.getByLabel('Due').fill(new Date().toISOString().slice(0,10)) }catch(e){}
    await page.getByRole('button', { name: 'Add' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created item: E2E Issue 1')
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Issue 1' })
    const exists = await row.count() > 0
    res.actions.push({ verify_after_create: exists })
    if (exists){
      // click the Edit button (use aria-labeled button selector scoped to the row)
      // attempt a DOM click via page.evaluate to bypass potential overlay/click issues
      await page.evaluate(() => {
        try{
          const rows = Array.from(document.querySelectorAll('table tbody tr'))
          for (const r of rows){ if (r.innerText && r.innerText.includes('E2E Issue 1')){ const btn = r.querySelector('button[aria-label="Edit"]'); if (btn) { btn.click(); return; } } }
        }catch(e){}
      })
      // debug: log whether a dialog element exists after click
      try{
        const dcount = await page.locator('div[role="dialog"]').count()
        console.log('DEBUG: dialog div count after Edit click:', dcount)
        if (dcount > 0){
          try{ const html = await page.locator('div[role="dialog"]').first().innerHTML(); console.log('DEBUG: dialog html snippet:', html.slice(0,200)) }catch(e){}
        }
      }catch(e){}
      // wait for modal dialog (or fallback to its title text) and edit via dialog inputs
      await page.getByRole('dialog').waitFor({ timeout: 15000 }).catch(async ()=>{ await page.getByText('Edit TWG Item').waitFor({ timeout: 15000 }).catch(()=>{}) })
      const dialog = page.locator('role=dialog').first()
      await dialog.locator('input').first().fill('E2E Issue 1 - edited')
      const inputs = dialog.locator('input')
      if (await inputs.count() > 1) await inputs.nth(1).fill('tester-edited')
      await dialog.locator('button:has-text("Save")').first().click().catch(()=>{})
      await page.waitForTimeout(700)
      res.actions.push('edited item title to E2E Issue 1 - edited')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    const presentAfterRefresh = await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Issue 1 - edited' }).count() > 0
    res.actions.push({ present_after_refresh: presentAfterRefresh })
    await snap('command_twg')
  })

  // 2. Ops TWG page (/working-groups)
  await visitAndLog('/working-groups', async (page, res) => {
    await page.getByLabel('New group name').waitFor({ timeout: 20000 })
    await page.getByLabel('New group name').fill('E2E WG OPS')
    await page.getByRole('button', { name: 'Create Group' }).click()
    await page.waitForTimeout(900)
    await page.getByLabel('Title').waitFor({ timeout: 15000 }).catch(()=>{})
    res.actions.push('created group: E2E WG OPS')
    await page.getByLabel('Title').fill('E2E Ops Issue')
    await page.getByRole('button', { name: 'Add' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created item: E2E Ops Issue')
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Ops Issue' })
    res.actions.push({ verify_after_create: (await row.count()) > 0 })
    if (await row.count() > 0){
      await row.getByRole('button', { name: 'Delete' }).last().click()
      await clickDialogConfirm(page)
      res.actions.push('deleted ops item')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    res.actions.push({ present_after_refresh: (await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Ops Issue' }).count()) > 0 })
    await snap('ops_twg')
  })

  // 3. Fusion page (/command-center/fusion-cell)
  await visitAndLog('/command-center/fusion-cell', async (page, res) => {
    await page.getByLabel('Fusion ID').waitFor({ timeout: 15000 })
    await page.getByLabel('Fusion ID').fill('E2E-F1')
    await page.getByLabel('Session Date').fill(new Date().toISOString().slice(0,10))
    await page.getByLabel('Participants (comma)').fill('alice,bob')
    await page.getByRole('button', { name: 'Create' }).click()
    await page.waitForTimeout(900)
    res.actions.push('created fusion: E2E-F1')
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1' })
    res.actions.push({ verify_after_create: (await row.count()) > 0 })
    if (await row.count() > 0){
      await page.evaluate(() => {
        try{
          const rows = Array.from(document.querySelectorAll('table tbody tr'))
          for (const r of rows){ if (r.innerText && r.innerText.includes('E2E-F1')){ const btn = r.querySelector('button[aria-label="Edit"]'); if (btn) { btn.click(); return; } } }
        }catch(e){}
      })
      // debug: check for dialog container
      try{
        const dcountF = await page.locator('div[role="dialog"]').count()
        console.log('DEBUG: fusion dialog div count after Edit click:', dcountF)
        if (dcountF > 0){ try{ const html = await page.locator('div[role="dialog"]').first().innerHTML(); console.log('DEBUG: fusion dialog html snippet:', html.slice(0,200)) }catch(e){} }
      }catch(e){}
      await page.getByRole('dialog').waitFor({ timeout: 15000 }).catch(async ()=>{ await page.getByText('Edit Fusion Session').waitFor({ timeout: 15000 }).catch(()=>{}) })
      const fdialog = page.locator('role=dialog').first()
      await fdialog.locator('input').first().fill('E2E-F1-EDIT')
      await fdialog.locator('button:has-text("Save")').first().click().catch(()=>{})
      await page.waitForTimeout(700)
      res.actions.push('edited fusion id to E2E-F1-EDIT')
    }
    const row2 = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1-EDIT' })
    if (await row2.count() > 0){
      await row2.getByRole('button', { name: 'Delete' }).first().click()
      await clickDialogConfirm(page)
      res.actions.push('deleted fusion')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    res.actions.push({ present_after_refresh: (await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1-EDIT' }).count()) > 0 })
    await snap('fusion')
  })

  // 4. Command Center overview (/command-center)
  await visitAndLog('/command-center', async (page, res) => {
    const progressExists = await page.locator('text=Progress').count() > 0 || await page.locator('linearprogress').count() > 0
    res.actions.push({ progress_ui_found: progressExists })
    await snap('command_center')
  })

  // 5. Lines of Effort (/command-center/lines-of-effort)
  await visitAndLog('/command-center/lines-of-effort', async (page, res) => {
  await page.getByRole('button', { name: 'Add LOE' }).click()
  // wait for the create form to render
    await page.getByLabel('Title').waitFor({ timeout: 5000 }).catch(()=>{})
    // debug: log whether Title label is present and a short page snippet when missing
    try{
      const tcnt = await page.getByLabel('Title').count()
      console.log('DEBUG: LOE Title locator count:', tcnt)
      if (tcnt === 0){ const html = await page.content(); console.log('DEBUG: LOE page snippet:', html.slice(0,2000)) }
    }catch(e){ console.log('DEBUG: LOE locator check error', String(e)) }
    try{
      await page.getByLabel('Title').fill('E2E LOE 1')
    }catch(e){
      try{ const inpx = page.locator('input[aria-label="Title"]').first(); if (await inpx.count()>0) await inpx.fill('E2E LOE 1') }catch(e2){ await page.evaluate(()=>{ const el = document.querySelector('input[aria-label="Title"]'); if (el) el.value = 'E2E LOE 1' }) }
    }
    await page.getByLabel('Description').waitFor({ timeout: 3000 }).catch(()=>{})
    try{
      await page.getByLabel('Description').fill('Automated LOE')
    }catch(e){
      try{ const inpd = page.locator('input[aria-label="Description"]').first(); if (await inpd.count()>0) await inpd.fill('Automated LOE') }catch(e2){ await page.evaluate(()=>{ const el = document.querySelector('input[aria-label="Description"]'); if (el) el.value = 'Automated LOE' }) }
    }
    const echelonSelect = page.locator('select').first()
    await echelonSelect.selectOption({ label: 'BDE' }).catch(()=>{})
    await page.waitForTimeout(400)
    const brigadeSelect = page.locator('select').filter({ hasText: 'Select Brigade' })
    if (await brigadeSelect.count() > 0){
      const opt = brigadeSelect.locator('option').nth(1)
      const val = await opt.getAttribute('value')
      if (val){ await brigadeSelect.selectOption(val) }
    }
    await page.getByRole('button', { name: 'Create' }).click().catch(()=>{})
    // attempt to capture the POST response to get the created LOE id
    let createdId = null
    try{
      const createResp = await page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/api/projects/loes'), { timeout: 5000 }).catch(()=>null)
      if (createResp){
        try{ const j = await createResp.json(); createdId = j && (j.id || j.id === 0 ? j.id : j['id']) }catch(e){}
      }
    }catch(e){}
    // fallback: if we didn't capture the POST response, query the list endpoint and find the newest item with our title
    if (!createdId){
      try{
        const items = await page.evaluate(async (baseURL) => {
          try{ const r = await fetch(baseURL + '/api/projects/loes?limit=200'); const j = await r.json(); return j }catch(e){ return null }
        }, base)
        if (items && Array.isArray(items)){
          // find items with our title and pick the highest id
          const matches = items.filter(i => i && i.name && i.name.indexOf('E2E LOE 1') !== -1)
          if (matches.length > 0){ matches.sort((a,b)=>b.id - a.id); createdId = matches[0].id }
        }
      }catch(e){ console.log('DEBUG: fallback list lookup failed', String(e)) }
    }
    await page.waitForTimeout(700)
    console.log('DEBUG: createdId captured =', createdId)
    res.actions.push('created LOE: E2E LOE 1')
    const present = await page.locator('text=E2E LOE 1').count() > 0
    res.actions.push({ present_after_create: present, createdId })
    if (present){
      let listItem = null
      if (createdId){
        try{ const editCtrl = page.locator(`[data-testid="edit-loe-${createdId}"]`).first(); if (await editCtrl.count() > 0){ await editCtrl.click().catch(()=>{}); listItem = page.locator('li').filter({ hasText: 'E2E LOE 1' }).first() } }
        catch(e){ console.log('DEBUG: clicking edit by createdId failed', String(e)) }
      }
      if (!listItem){
        listItem = page.locator('li').filter({ hasText: 'E2E LOE 1' }).first()
        await listItem.locator('button').first().click()
      }
      await page.waitForTimeout(300)
      try{ await page.getByLabel('Title').fill('E2E LOE 1 EDIT') }catch(e){ try{ const inpx2 = page.locator('input[aria-label="Title"]').first(); if (await inpx2.count()>0) await inpx2.fill('E2E LOE 1 EDIT') }catch(e2){ await page.evaluate(()=>{ const el = document.querySelector('input[aria-label="Title"]'); if (el) el.value = 'E2E LOE 1 EDIT' }) } }
      // Robust save-click logic: try row-scoped first, then global selectors, icon variant, edit->save fallback, then DOM-evaluate fallback
      let saveClicked = false
      let methodUsed = null
      // 1) Row-scoped save button (preferred)
      try{
        const rowSave = listItem.locator('button[data-testid^="save-loe-"]')
        const rc = await rowSave.count()
        console.log('DEBUG: row-scoped save count =', rc)
        if (rc > 0){
          try{ await rowSave.first().waitFor({ state: 'visible', timeout: 1200 }).catch(()=>{}) }catch(e){}
          try{
            const clicked = await listItem.evaluate(node => { try{ const b = node.querySelector('button[data-testid^="save-loe-"]'); if(!b) return false; b.click(); return true }catch(e){ return false } })
            console.log('DEBUG: row-scoped evaluate click result =', clicked)
            if (clicked) { saveClicked = true; methodUsed = 'row-scoped-evaluate' }
            else { await rowSave.first().click().catch(()=>{ console.log('DEBUG: row-scoped click failed') }) ; saveClicked = true; methodUsed = 'row-scoped-click' }
          }catch(e){ console.log('DEBUG: row-scoped click exception', String(e)) }
        }
      }catch(e){ console.log('DEBUG: row-scoped detection error', String(e)) }

      // 2) Global save button by data-testid
      if (!saveClicked){
        try{
          await page.waitForSelector('button[data-testid^="save-loe-"]', { timeout: 2500 }).catch(()=>{})
          const globalSave = page.locator('button[data-testid^="save-loe-"]')
          const gc = await globalSave.count()
          console.log('DEBUG: global save-loe- count =', gc)
          for (let i=0;i<gc && !saveClicked;i++){
            try{
              const el = globalSave.nth(i)
              const box = await el.boundingBox().catch(()=>null)
              if (box){
                await el.click().catch(async ()=>{ try{ await page.evaluate(e=>e.click(), el) }catch(e){} })
                saveClicked = true; methodUsed = 'global-save-loe'
                break
              }
            }catch(e){}
          }
        }catch(e){ console.log('DEBUG: global save-loe detection error', String(e)) }
      }

      // 3) Global icon variant
      if (!saveClicked){
        try{
          await page.waitForSelector('button[data-testid^="save-loe-icon-"]', { timeout: 2500 }).catch(()=>{})
          const icons = page.locator('button[data-testid^="save-loe-icon-"]')
          const ic = await icons.count()
          console.log('DEBUG: global save-loe-icon- count =', ic)
          for (let i=0;i<ic && !saveClicked;i++){
            try{ const el = icons.nth(i); const box = await el.boundingBox().catch(()=>null); if (box){ await el.click().catch(()=>{}); saveClicked=true; methodUsed='global-save-loe-icon'; break } }catch(e){}
          }
        }catch(e){ console.log('DEBUG: global save-loe-icon detection error', String(e)) }
      }

      // 4) Fallback: click edit icon then try Save by text
      if (!saveClicked){
        try{
          const editIcon = listItem.locator('button[data-testid^="edit-loe-"]').first()
          if ((await editIcon.count())>0){
            await editIcon.click().catch(()=>{})
            await page.waitForTimeout(300)
            try{
              await page.waitForSelector('button:has-text("Save")', { timeout: 2000 }).catch(()=>{})
              const sb = page.locator('button:has-text("Save")')
              if ((await sb.count())>0){ await sb.first().click().catch(()=>{}); saveClicked=true; methodUsed='button-text-save' }
            }catch(e){ console.log('DEBUG: button:has-text("Save") attempt failed', String(e)) }
          }
        }catch(e){ console.log('DEBUG: edit-icon fallback error', String(e)) }
      }

      // 5) Last-resort DOM evaluate click
      if (!saveClicked){
        try{
          const evalClicked = await page.evaluate(() => {
            try{
              const byData = Array.from(document.querySelectorAll('[data-testid]')).filter(e => e.getAttribute('data-testid') && e.getAttribute('data-testid').startsWith('save-loe-'))
              if (byData.length>0){ byData[0].click(); return 'eval-data-testid' }
              const buttons = Array.from(document.querySelectorAll('button')).filter(b=> b.innerText && b.innerText.trim().toLowerCase() === 'save')
              if (buttons.length>0){ buttons[0].click(); return 'eval-button-text-save' }
              return false
            }catch(e){ return false }
          })
          if (evalClicked){ saveClicked = true; methodUsed = 'eval-fallback-' + String(evalClicked) }
        }catch(e){ console.log('DEBUG: eval fallback error', String(e)) }
      }

      console.log('DEBUG: saveClicked =', saveClicked, 'method =', methodUsed)
      res.actions.push({ saveClicked, saveMethod: methodUsed })
      await page.waitForTimeout(700)
      res.actions.push('edited LOE title to E2E LOE 1 EDIT')
    }
    // After edit: reload and verify the edited LOE is present (by id when possible)
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    // capture the exact list response used by the page for debugging by fetching it directly
    try{
      const listJson = await page.evaluate(async (baseURL) => {
        try{ const r = await fetch(baseURL + '/api/projects/loes?limit=200'); return await r.json() }catch(e){ return null }
      }, base)
      if (listJson){
        const dumpPath = `./tools/e2e-loe-list-${createdId || 'unknown'}.json`
        try{ require('fs').writeFileSync(dumpPath, JSON.stringify(listJson, null, 2)) }catch(e){}
        res.actions.push({ wrote_list_dump: dumpPath })
      } else {
        res.actions.push({ wrote_list_dump: null })
      }
    }catch(e){ res.actions.push({ wrote_list_dump: null, error: String(e) }) }

    let presentAfterRefresh = false
    try{
      if (createdId){
        // wait for the specific data-testid elements the frontend now emits
        try{ await page.waitForSelector(`[data-testid="loe-item-${createdId}"], [data-testid="loe-name-${createdId}"]`, { timeout: 5000 }) }catch(e){}
        const byEditCtrl = await page.locator(`[data-testid="edit-loe-${createdId}"]`).count()
        const byItem = await page.locator(`[data-testid="loe-item-${createdId}"]`).count()
        const byName = await page.locator(`[data-testid="loe-name-${createdId}"]`).count()
        presentAfterRefresh = (byEditCtrl > 0) || (byItem > 0) || (byName > 0) || (await page.locator('text=E2E LOE 1 EDIT').count() > 0)
      } else {
        presentAfterRefresh = (await page.locator('text=E2E LOE 1 EDIT').count()) > 0
      }
    }catch(e){ presentAfterRefresh = (await page.locator('text=E2E LOE 1 EDIT').count()) > 0 }
    // Enhanced diagnostics: dump DOM and compare with API list JSON
    try{
      const domDumpPath = `./tools/e2e-dom-${createdId || 'unknown'}.html`
      const pageDumpPath = `./tools/e2e-page-${createdId || 'unknown'}.html`
      const comparePath = `./tools/e2e-compare-${createdId || 'unknown'}.json`
      // attempt to capture the LOE container HTML if present, otherwise fall back to full page
      let loeContainerHtml = null
      try{
        loeContainerHtml = await page.$eval('.loe-list-container', el => el.outerHTML).catch(()=>null)
      }catch(e){ loeContainerHtml = null }
      if (!loeContainerHtml){
        try{ loeContainerHtml = await page.$eval('#loes, .loes, .loe-list', el => el.outerHTML).catch(()=>null) }catch(e){ loeContainerHtml = null }
      }
      if (loeContainerHtml){
        try{ require('fs').writeFileSync(domDumpPath, loeContainerHtml) }catch(e){}
      } else {
        try{ const full = await page.content(); require('fs').writeFileSync(pageDumpPath, full.slice(0, 200000)) }catch(e){}
      }

      // read the API list JSON we just wrote (if any)
      let apiList = null
      try{ apiList = JSON.parse(require('fs').readFileSync(`./tools/e2e-loe-list-${createdId || 'unknown'}.json`, 'utf8')) }catch(e){ apiList = null }
      // compute comparison results
      const apiHasEdited = apiList && Array.isArray(apiList) && apiList.some(i => i && (i.id === createdId || String(i.id) === String(createdId)) && i.name && i.name.includes('E2E LOE 1 EDIT'))
      const domHasEditedName = (loeContainerHtml && loeContainerHtml.indexOf('E2E LOE 1 EDIT') !== -1) || (await page.locator('text=E2E LOE 1 EDIT').count() > 0)
      const domHasDataTestId = ((await page.locator(`[data-testid="loe-item-${createdId}"]`).count())>0) || ((await page.locator(`[data-testid="loe-name-${createdId}"]`).count())>0) || ((await page.locator(`[data-testid="edit-loe-${createdId}"]`).count())>0)
      const compare = { createdId: createdId || null, apiHasEdited, domHasEditedName, domHasDataTestId, presentAfterRefresh }
      try{ require('fs').writeFileSync(comparePath, JSON.stringify(compare, null, 2)) }catch(e){}
      res.actions.push({ present_after_refresh: presentAfterRefresh, check_method: createdId ? `id:${createdId}` : 'text', compare: comparePath })
    }catch(e){
      res.actions.push({ present_after_refresh: presentAfterRefresh, check_method: createdId ? `id:${createdId}` : 'text', compare_error: String(e) })
    }

    // Now delete the LOE (cleanup) and verify deletion persisted after reload
    let deleted = false
    try{
      let deleteClicked = false
      // Prefer clicking the id-specific delete button if we have the id
      if (createdId){
        try{
          const delBtn = page.locator(`[data-testid="delete-loe-${createdId}"]`).first()
          if ((await delBtn.count()) > 0){
            await delBtn.click().catch(()=>{})
            // wait for the DELETE request specific to this LOE id
            try{ await page.waitForResponse(r => r.request().method() === 'DELETE' && r.url().includes(`/api/projects/loes/${createdId}`), { timeout: 8000 }) }catch(e){}
            await clickDialogConfirm(page)
            res.actions.push('deleted LOE')
            deleteClicked = true
            deleted = true
          }
        }catch(e){ console.log('DEBUG: id-specific delete click failed', String(e)) }
      }
      // Fallback: click the list item's last button (older behavior)
      if (!deleteClicked){
        let itemToDelete = page.locator('li').filter({ hasText: 'E2E LOE 1 EDIT' }).first()
        if (await itemToDelete.count() > 0){ await itemToDelete.locator('button').last().click(); await clickDialogConfirm(page); res.actions.push('deleted LOE'); deleted = true }
      }
    }catch(e){ console.log('DEBUG: delete LOE error', String(e)) }
    // after delete, force a full reload and wait for network idle
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    // wait for the id-specific selector to be detached (absent) when we have an id
    let presentAfterDelete = true
    try{
      if (createdId){
        try{
          await page.waitForSelector(`[data-testid="loe-item-${createdId}"], [data-testid="loe-name-${createdId}"]`, { state: 'detached', timeout: 5000 })
          presentAfterDelete = false
        }catch(e){
          // if detached wait times out, re-check existence
          presentAfterDelete = (await page.locator(`[data-testid="loe-item-${createdId}"]`).count()) > 0 || (await page.locator(`[data-testid="loe-name-${createdId}"]`).count()) > 0
        }
      } else {
        presentAfterDelete = (await page.locator('text=E2E LOE 1 EDIT').count()) > 0
      }
    }catch(e){ presentAfterDelete = (await page.locator('text=E2E LOE 1 EDIT').count()) > 0 }

    // Also fetch the API list after delete to verify server-side deletion and write a dump
    try{
      const listAfterDelete = await page.evaluate(async (baseURL) => {
        try{ const r = await fetch(baseURL + '/api/projects/loes?limit=200'); return await r.json() }catch(e){ return null }
      }, base)
      if (listAfterDelete){
        const dumpPathAfter = `./tools/e2e-loe-list-after-delete-${createdId || 'unknown'}.json`
        try{ require('fs').writeFileSync(dumpPathAfter, JSON.stringify(listAfterDelete, null, 2)) }catch(e){}
        // compute whether API still contains the id
        let apiStillHas = false
        try{ apiStillHas = Array.isArray(listAfterDelete) && listAfterDelete.some(i => i && (i.id === createdId || String(i.id) === String(createdId))) }catch(e){}
        const deleteComparePath = `./tools/e2e-delete-compare-${createdId || 'unknown'}.json`
        try{ require('fs').writeFileSync(deleteComparePath, JSON.stringify({ createdId: createdId || null, apiStillHas, presentAfterDelete }, null, 2)) }catch(e){}
        res.actions.push({ wrote_list_after_delete: dumpPathAfter, delete_compare: deleteComparePath })
      }
    }catch(e){ res.actions.push({ list_after_delete_error: String(e) }) }
    res.actions.push({ present_after_delete: presentAfterDelete, deleted })
    await snap('loes')
  })

  // 6. Submit Ticket (/help/submit-ticket) and 7. Ticket Status
  await visitAndLog('/help/submit-ticket', async (page, res) => {
    await page.getByLabel('Title').fill('E2E Ticket')
    await page.getByRole('button', { name: 'Submit' }).click()
    await page.waitForTimeout(1000)
    res.actions.push('submitted ticket: E2E Ticket')
    await snap('submit_ticket')
  })

  await visitAndLog('/help/ticket-status', async (page, res) => {
    const found = await page.locator('text=E2E Ticket').count() > 0
    res.actions.push({ ticket_list_shows_ticket: found })
    await snap('ticket_status')
  })

  // 8. Additional org selector verification: open Projects page
  await visitAndLog('/projects', async (page, res) => {
    const selectorPresent = await page.locator('text=Apply').count() > 0 || await page.locator('select').count() > 0
    res.actions.push({ cascading_selector_present: selectorPresent })
    if (selectorPresent){
      const sel = page.locator('select').first()
      await sel.selectOption({ label: 'BDE' }).catch(()=>{})
      await page.waitForTimeout(300)
      const applyBtn = page.locator('button').filter({ hasText: 'Apply' }).first()
      if (await applyBtn.count() > 0){ await applyBtn.click(); res.actions.push('applied selector') }
    }
    await snap('projects')
  })

  await browser.close()
  fs.writeFileSync('./tools/e2e-results.json', JSON.stringify(results, null, 2))
  try{ fs.writeFileSync('./tools/e2e-network-log.json', JSON.stringify(networkFailures, null, 2)) }catch(e){ console.error('Failed writing network log', e) }
  console.log('\nE2E results saved to tools/e2e-results.json')
}

run().catch(e=>{ console.error(e); process.exit(1) })
