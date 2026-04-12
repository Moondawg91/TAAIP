const pw = require('playwright');
const fs = require('fs');
(async ()=>{
  try{
    const sel = {
      root_rsid: 'USAREC',
      bde: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
      bn: null, co: null, stn: null,
      active: { rsid: '1BDE', display_name: '1st Recruiting Brigade', echelon: 'BDE' },
      effective_rsid: '1BDE'
    }
    const browser = await pw.webkit.launch({ headless: false });
    const ctx = await browser.newContext();
    // set localStorage before navigating by injecting script (only if not already set)
    await ctx.addInitScript(s => { try{ if (!localStorage.getItem('taaip.unitSelection.v1')) { localStorage.setItem('taaip.unitSelection.v1', s) } }catch(e){} }, JSON.stringify(sel))
    const page = await ctx.newPage();
      // collect console logs
      const logs = []
      page.on('console', msg => {
        try{ const text = msg.text(); logs.push({ type: msg.type(), text }) }catch(e){}
      })
      // collect network responses for org endpoints
      const net = []
      page.on('response', async resp => {
        try{
          const url = resp.url()
          if (url.indexOf('/api/v2/org') !== -1 || url.indexOf('/api/v2/command') !== -1){
            let body = null
            try{ body = await resp.json() }catch(e){ try{ body = await resp.text() }catch(_){} }
            net.push({ url, status: resp.status(), body })
          }
        }catch(e){}
      })
    // navigate directly to frontend to avoid backend redirect/service-worker races
    const base = process.env.E2E_BASE_URL || 'http://localhost:3000'
    await page.goto(`${base.replace(/\/$/, '')}/command-center?_t=${Date.now()}&e2e_autoselect=1`, { waitUntil: 'networkidle', timeout: 120000 });
    // allow redirect and app hydration (wait for Command Center to render)
    try{
      await page.waitForSelector('text=Command Center', { timeout: 20000 })
    }catch(e){
      // fallback short wait and capture HTML for debugging
      await page.waitForTimeout(3000)
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_command_center.png', fullPage:true })
    }
    // dump localStorage for verification
    const ls = await page.evaluate(()=> localStorage.getItem('taaip.unitSelection.v1'))
    try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/localstorage.json', JSON.stringify({ raw: ls }, null, 2)) }catch(e){}

    // open BN via label (try Playwright's label locator first, fallback to DOM traversal)
    let bnHandle = null
    try{
      if (page.getByLabel) {
        const byLabel = page.getByLabel('BN')
        if (await byLabel.count() > 0) {
          // find the combobox/button inside the labeled control
          const parent = byLabel.nth(0).locator('xpath=..')
          const cb = parent.locator('div[role="combobox"], [role="combobox"], div[role="button"], [role="button"]')
          if (await cb.count() > 0) bnHandle = await cb.first().elementHandle()
        }
      }
    }catch(e){}
    if (!bnHandle){
      // fallback: capture form control HTML and full page HTML for debugging and try to locate BN via text match
      try{
        const forms = await page.$$eval('.MuiFormControl-root, .form-control, form', nodes => nodes.map(n=> n.outerHTML.slice(0,4000)))
        require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/forms_snippets.json', JSON.stringify(forms, null, 2))
      }catch(e){}
      try{
        const full = await page.content()
        require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/page_source.html', full)
      }catch(e){}
      const labels = await page.$$('label')
      for(const lh of labels){
        const txt = (await lh.innerText()).trim()
        if (txt.toUpperCase().indexOf('BN') !== -1){
          const parent = await lh.evaluateHandle(node => node.closest('.MuiFormControl-root') || node.parentElement)
          const cb = await parent.asElement().$('div[role="combobox"], div[role="button"], [role="combobox"], [role="button"]')
          bnHandle = cb
          break
        }
      }
    }
    if (!bnHandle){ console.log('bn not found'); await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_bn.png', fullPage:true }); await browser.close(); return }
      if (!bnHandle){
        console.log('bn not found');
        try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/console.json', JSON.stringify(logs, null, 2)) }catch(e){}
        try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/network.json', JSON.stringify(net, null, 2)) }catch(e){}
        await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_bn.png', fullPage:true });
        await browser.close();
        return
      }
    const disabled = bnHandle ? await bnHandle.getAttribute('aria-disabled') : 'not-found'
    console.log('bn aria-disabled', disabled)
    if (disabled === 'true'){
      console.log('BN is disabled after local load')
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/bn_disabled.png', fullPage:true })
      await browser.close(); return
    }
    await bnHandle.evaluate(el => el.click())
    let opened = false
    try{
      await page.waitForFunction(()=>{
        return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0
      }, { timeout: 10000 })
      opened = true
    }catch(e){
      // try alternative open mechanisms: press Enter or ArrowDown on the active element
      try{ await bnHandle.evaluate(el=>el.focus()); await page.keyboard.press('Enter'); await page.waitForTimeout(500); }catch(_){}
      try{ await bnHandle.evaluate(el=>el.focus()); await page.keyboard.press('ArrowDown'); await page.waitForTimeout(500); }catch(_){}
      try{
        await page.waitForFunction(()=>{ return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0 }, { timeout: 5000 })
        opened = true
      }catch(err){ opened = false }
    }
    const bns = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync('tools/e2e_results/org_selector_localload_flow/bns.json', JSON.stringify(bns, null, 2))
    // also capture menu item attributes (value/data-value) for debugging
    try{
      const bnsFull = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n => ({ text: n.innerText.trim(), value: n.getAttribute('data-value') || n.getAttribute('value') || (n.dataset && n.dataset.value) || null, role: n.getAttribute('role') })))
      fs.writeFileSync('tools/e2e_results/org_selector_localload_flow/bns_full.json', JSON.stringify(bnsFull, null, 2))
    }catch(e){}
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/console.json', JSON.stringify(logs, null, 2)) }catch(e){}
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/network.json', JSON.stringify(net, null, 2)) }catch(e){}
    if (!opened){
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/bn_not_opened.png', fullPage:true })
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/console.json', JSON.stringify(logs, null, 2)) }catch(e){}
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/network.json', JSON.stringify(net, null, 2)) }catch(e){}
      await browser.close();
      return
    }
    await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/bn_open.png', fullPage:true })
    console.log('bns count', bns.length)
    // select the first real BN (skip 'All')
    const firstBn = (await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()).filter(t=>t && t.toLowerCase()!=='all')[0])) || null
    if (!firstBn){
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_bn_item.png', fullPage:true })
      await browser.close();
      return
    }
    // attempt to set the native select value (dispatch change) to emulate a real user selection
    let didSelectBn = false
    try{
      const targetVal = (await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=> ({ text: n.innerText.trim(), value: n.getAttribute('data-value') || n.getAttribute('value') || (n.dataset && n.dataset.value) || null })).filter(x=>x.text && x.text.toLowerCase()!=='all')[0]))
      if (targetVal && targetVal.value){
        await page.evaluate((val)=>{
          try{
            const inputs = Array.from(document.querySelectorAll('.MuiSelect-nativeInput'))
            // find the BN native input by locating the select whose adjacent label text contains 'BN'
            for(const inp of inputs){
              const parent = inp.closest('.MuiFormControl-root')
              if (parent && parent.innerText && parent.innerText.toUpperCase().indexOf('BN') !== -1){
                inp.value = val
                const ev = new Event('change', { bubbles: true })
                inp.dispatchEvent(ev)
                break
              }
            }
          }catch(e){}
        }, targetVal.value)
        didSelectBn = true
      }
    }catch(e){ didSelectBn = false }
    // fallback: keyboard then click
    if (!didSelectBn){
      try{ await bnHandle.evaluate(el=>el.focus()); await page.keyboard.press('ArrowDown'); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter'); didSelectBn = true }catch(e){ didSelectBn = false }
      if (!didSelectBn){
        try{
          // fallback: dispatch a DOM click event on the matching menu item
          await page.evaluate((first)=>{
            try{
              const items = Array.from(document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root'))
              for(const it of items){
                if ((it.innerText||'').trim() === first){
                  it.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
                  break
                }
              }
            }catch(e){}
          }, firstBn)
        }catch(e){ try{ await page.click(`text="${firstBn}"`) }catch(_){} }
      }
    }
    // wait for selection to persist to localStorage (bn set)
    try{ await page.waitForFunction(()=>{ try{ const s = localStorage.getItem('taaip.unitSelection.v1'); if (!s) return false; const p = JSON.parse(s); return p && p.bn && (p.bn.rsid || p.bn.unit_key || p.bn.display_name); }catch(e){return false} }, { timeout: 3000 }) }catch(e){}
    // if BN did not persist, capture diagnostics and fail (no synthetic localStorage writes)
    const still = await page.evaluate(()=>{ try{ const s = localStorage.getItem('taaip.unitSelection.v1'); return s ? JSON.parse(s) : null }catch(e){return null} })
    if (!still || !still.bn){
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/console.json', JSON.stringify(logs, null, 2)) }catch(e){}
      try{ require('fs').writeFileSync('tools/e2e_results/org_selector_localload_flow/network.json', JSON.stringify(net, null, 2)) }catch(e){}
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/bn_not_persisted.png', fullPage:true })
      await browser.close();
      return
    }
    await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/after_select_bn.png', fullPage:true })

    // now attempt to open CO menu
    const coLabel = await page.getByLabel ? page.getByLabel('CO') : null
    let coHandle = null
    if (coLabel && (await coLabel.count())>0){
      try{ coHandle = await coLabel.nth(0).locator('xpath=..').locator('div[role="combobox"], [role="combobox"], div[role="button"], [role="button"]').first().elementHandle() }catch(e){}
    }
    if (!coHandle){
      // fallback: find by input label text
      const labels2 = await page.$$('label')
      for(const lh of labels2){
        const txt = (await lh.innerText()).trim()
        if (txt.toUpperCase().indexOf('CO') !== -1){
          const parent = await lh.evaluateHandle(node => node.closest('.MuiFormControl-root') || node.parentElement)
          const cb = await parent.asElement().$('div[role="combobox"], div[role="button"], [role="combobox"], [role="button"]')
          coHandle = cb
          break
        }
      }
    }
    if (!coHandle){
      await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_co.png', fullPage:true })
      await browser.close();
      return
    }

    await coHandle.evaluate(el => el.click())
    try{ await page.waitForFunction(()=>{ return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0 }, { timeout: 8000 }) }catch(e){ /* ignore */ }
    const cos = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync('tools/e2e_results/org_selector_localload_flow/cos.json', JSON.stringify(cos, null, 2))
    try{
      const cosFull = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n => ({ text: n.innerText.trim(), value: n.getAttribute('data-value') || n.getAttribute('value') || (n.dataset && n.dataset.value) || null, role: n.getAttribute('role') })))
      fs.writeFileSync('tools/e2e_results/org_selector_localload_flow/cos_full.json', JSON.stringify(cosFull, null, 2))
    }catch(e){}
    await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/co_open.png', fullPage:true })

    // select first CO (skip All)
    const firstCo = cos.filter(t=>t && t.toLowerCase()!=='all')[0] || null
    if (!firstCo){ await browser.close(); return }
    // try keyboard selection for CO
    let didSelectCo = false
    try{
      await coHandle.evaluate(el=>el.focus())
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('Enter')
      didSelectCo = true
    }catch(e){ didSelectCo = false }
    if (!didSelectCo){ try{ await page.click(`text="${firstCo}"`) }catch(_){} }
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/after_select_co.png', fullPage:true })

    // open STN
    const stnLabel = await page.getByLabel ? page.getByLabel('STN') : null
    let stnHandle = null
    if (stnLabel && (await stnLabel.count())>0){
      try{ stnHandle = await stnLabel.nth(0).locator('xpath=..').locator('div[role="combobox"], [role="combobox"], div[role="button"], [role="button"]').first().elementHandle() }catch(e){}
    }
    if (!stnHandle){
      const labels3 = await page.$$('label')
      for(const lh of labels3){
        const txt = (await lh.innerText()).trim()
        if (txt.toUpperCase().indexOf('STN') !== -1){
          const parent = await lh.evaluateHandle(node => node.closest('.MuiFormControl-root') || node.parentElement)
          const cb = await parent.asElement().$('div[role="combobox"], div[role="button"], [role="combobox"], [role="button"]')
          stnHandle = cb
          break
        }
      }
    }
    if (!stnHandle){ await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/no_stn.png', fullPage:true }); await browser.close(); return }
    await stnHandle.evaluate(el => el.click())
    try{ await page.waitForFunction(()=>{ return document.querySelectorAll('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root').length > 0 }, { timeout: 8000 }) }catch(e){}
    const stns = await page.$$eval('ul[role="listbox"] li, li[role="option"], .MuiMenuItem-root', nodes => nodes.map(n=>n.innerText.trim()))
    fs.writeFileSync('tools/e2e_results/org_selector_localload_flow/stns.json', JSON.stringify(stns, null, 2))
    await page.screenshot({ path: 'tools/e2e_results/org_selector_localload_flow/stn_open.png', fullPage:true })

    await browser.close();
  }catch(e){ console.error('ERR', e && (e.stack||e.message)); process.exit(1) }
})();
