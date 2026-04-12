const fs = require('fs')
const { chromium } = require('playwright')

async function run(){
  const base = process.env.BASE_URL || 'http://127.0.0.1:8001'
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext()
  const page = await context.newPage()
  page.on('console', msg => console.log('PAGE LOG>', msg.text()))

  // accept all dialogs
  page.on('dialog', async dialog => { console.log('Dialog:', dialog.message()); await dialog.accept() })

  const results = []

  async function visitAndLog(route, fn){
    const url = base + route
    console.log('\n== Visiting', url)
    await page.goto(url, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    const res = { route, actions: [] }
    try{
      await fn(page, res)
    }catch(e){ res.error = String(e); console.error(e) }
    results.push(res)
  }

  // Helper to take screenshot for debugging
  async function snap(name){
    const p = `./tools/e2e-snap-${name.replace(/[^a-z0-9\-]/ig,'_')}.png`
    try{ await page.screenshot({ path: p, fullPage: true }) }catch(e){}
  }

  // 1. Command TWG page (/command-center/twg)
  await visitAndLog('/command-center/twg', async (page, res) => {
    // create WG
    await page.getByLabel('New group name').fill('E2E WG')
    await page.getByRole('button', { name: 'Create Group' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created group: E2E WG')
    // create item
    await page.getByLabel('Title').fill('E2E Issue 1')
    await page.getByLabel('Owner').fill('tester')
    // date input
    try{ await page.getByLabel('Due').fill(new Date().toISOString().slice(0,10)) }catch(e){}
    await page.getByRole('button', { name: 'Add' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created item: E2E Issue 1')
    // verify in table
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Issue 1' })
    const exists = await row.count() > 0
    res.actions.push({ verify_after_create: exists })
    // edit item: click edit icon in that row
    if (exists){
      await row.locator('button').filter({ hasText: '' }).first().click().catch(async ()=>{
        // fallback: click the first iconbutton in actions cell
        await row.locator('td').nth(4).locator('button').first().click()
      })
      await page.waitForTimeout(300)
      // change title
      await row.locator('input').first().fill('E2E Issue 1 - edited')
      // click save (first button with Save icon)
      await row.locator('button').filter({ hasText: '' }).first().click().catch(async ()=>{
        await row.locator('td').nth(4).locator('button').first().click()
      })
      await page.waitForTimeout(700)
      res.actions.push('edited item title to E2E Issue 1 - edited')
    }
    // delete item: find row and click Delete icon (last button)
    const row2 = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Issue 1 - edited' })
    if (await row2.count() > 0){
      // click last button in actions cell
      await row2.locator('td').nth(4).locator('button').last().click()
      await page.waitForTimeout(700)
      res.actions.push('deleted item')
    }
    // refresh and confirm item gone
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    const still = await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Issue 1 - edited' }).count()
    res.actions.push({ present_after_refresh: still > 0 })
    await snap('command_twg')
  })

  // 2. Ops TWG page (/working-groups)
  await visitAndLog('/working-groups', async (page, res) => {
    // should reuse same component
    await page.getByLabel('New group name').fill('E2E WG OPS')
    await page.getByRole('button', { name: 'Create Group' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created group: E2E WG OPS')
    // create item
    await page.getByLabel('Title').fill('E2E Ops Issue')
    await page.getByRole('button', { name: 'Add' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created item: E2E Ops Issue')
    // verify
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Ops Issue' })
    res.actions.push({ verify_after_create: (await row.count()) > 0 })
    // cleanup: delete
    if (await row.count() > 0){
      await row.locator('td').nth(4).locator('button').last().click()
      res.actions.push('deleted ops item')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    res.actions.push({ present_after_refresh: (await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E Ops Issue' }).count()) > 0 })
    await snap('ops_twg')
  })

  // 3. Fusion page (/command-center/fusion-cell)
  await visitAndLog('/command-center/fusion-cell', async (page, res) => {
    await page.getByLabel('Fusion ID').fill('E2E-F1')
    // date
    await page.getByLabel('Session Date').fill(new Date().toISOString().slice(0,10))
    await page.getByLabel('Participants (comma)').fill('alice,bob')
    await page.getByRole('button', { name: 'Create' }).click()
    await page.waitForTimeout(700)
    res.actions.push('created fusion: E2E-F1')
    // verify
    const row = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1' })
    res.actions.push({ verify_after_create: (await row.count()) > 0 })
    // edit
    if (await row.count() > 0){
      await row.locator('td').nth(3).locator('button').first().click().catch(async ()=>{ await row.locator('td').nth(3).locator('button').first().click() })
      await page.waitForTimeout(300)
      await row.locator('input').first().fill('E2E-F1-EDIT')
      // click save (first button in actions)
      await row.locator('td').nth(3).locator('button').first().click()
      await page.waitForTimeout(700)
      res.actions.push('edited fusion id to E2E-F1-EDIT')
    }
    // delete
    const row2 = page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1-EDIT' })
    if (await row2.count() > 0){
      await row2.locator('td').nth(3).locator('button').last().click()
      res.actions.push('deleted fusion')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    res.actions.push({ present_after_refresh: (await page.locator('table').locator('tbody tr').filter({ hasText: 'E2E-F1-EDIT' }).count()) > 0 })
    await snap('fusion')
  })

  // 4. Command Center overview (/command-center)
  await visitAndLog('/command-center', async (page, res) => {
    // check for LOE progress indicator and numeric progress
    const progressExists = await page.locator('text=Progress').count() > 0 || await page.locator('linearprogress').count() > 0
    res.actions.push({ progress_ui_found: progressExists })
    // snapshot
    await snap('command_center')
  })

  // 5. Lines of Effort (/command-center/lines-of-effort)
  await visitAndLog('/command-center/lines-of-effort', async (page, res) => {
    // click Add LOE
    await page.getByRole('button', { name: 'Add LOE' }).click()
    await page.getByLabel('Title').fill('E2E LOE 1')
    await page.getByLabel('Description').fill('Automated LOE')
    // interact with cascading selector: pick echelon BDE if available
    // select element
    const echelonSelect = page.locator('select').first()
    await echelonSelect.selectOption({ label: 'BDE' }).catch(()=>{})
    // wait for brigade select to populate
    await page.waitForTimeout(400)
    // find a brigade option if present
    const brigadeSelect = page.locator('select').filter({ hasText: 'Select Brigade' })
    if (await brigadeSelect.count() > 0){
      // choose first non-empty option
      const opt = brigadeSelect.locator('option').nth(1)
      const val = await opt.getAttribute('value')
      if (val){ await brigadeSelect.selectOption(val) }
    }
    // click Create
    await page.getByRole('button', { name: 'Create' }).click().catch(()=>{})
    await page.waitForTimeout(700)
    res.actions.push('created LOE: E2E LOE 1')
    // verify exists
    const present = await page.locator('text=E2E LOE 1').count() > 0
    res.actions.push({ present_after_create: present })
    // edit: click edit icon next to LOE
    if (present){
      const listItem = page.locator('li').filter({ hasText: 'E2E LOE 1' }).first()
      await listItem.locator('button').first().click()
      await page.waitForTimeout(300)
      await page.getByLabel('Title').fill('E2E LOE 1 EDIT')
      await page.getByRole('button', { name: 'Create' }).nth(0).click().catch(()=>{})
      await page.waitForTimeout(700)
      res.actions.push('edited LOE title to E2E LOE 1 EDIT')
    }
    // delete
    const item = page.locator('li').filter({ hasText: 'E2E LOE 1 EDIT' })
    if (await item.count() > 0){
      // find delete icon/button (last button)
      await item.locator('button').last().click()
      res.actions.push('deleted LOE')
    }
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(700)
    res.actions.push({ present_after_refresh: (await page.locator('text=E2E LOE 1 EDIT').count()) > 0 })
    await snap('loes')
  })

  // 6. Submit Ticket (/help/submit-ticket) and 7. Ticket Status
  await visitAndLog('/help/submit-ticket', async (page, res) => {
    await page.getByLabel('Title').fill('E2E Ticket')
    await page.getByRole('button', { name: 'Submit' }).click()
    // wait for snackbar then redirect
    await page.waitForTimeout(1000)
    res.actions.push('submitted ticket: E2E Ticket')
    await snap('submit_ticket')
  })

  // after submit, go to ticket status page
  await visitAndLog('/help/ticket-status', async (page, res) => {
    const found = await page.locator('text=E2E Ticket').count() > 0
    res.actions.push({ ticket_list_shows_ticket: found })
    await snap('ticket_status')
  })

  // 8. Additional org selector verification: open Projects page (or command center header)
  await visitAndLog('/projects', async (page, res) => {
    // check for cascading unit selector presence
    const selectorPresent = await page.locator('text=Apply').count() > 0 || await page.locator('select').count() > 0
    res.actions.push({ cascading_selector_present: selectorPresent })
    // try selecting an echelon and applying
    if (selectorPresent){
      const sel = page.locator('select').first()
      await sel.selectOption({ label: 'BDE' }).catch(()=>{})
      await page.waitForTimeout(300)
      const applyBtn = page.locator('button').filter({ hasText: 'Apply' }).first()
      if (await applyBtn.count() > 0){ await applyBtn.click(); res.actions.push('applied selector') }
    }
    await snap('projects')
  })

  // write results
  await browser.close()
  fs.writeFileSync('./tools/e2e-results.json', JSON.stringify(results, null, 2))
  console.log('\nE2E results saved to tools/e2e-results.json')
}

run().catch(e=>{ console.error(e); process.exit(1) })
