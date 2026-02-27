/* © 2026 TAAIP. Copyright pending. */

import { loadOrgSelection } from '../store/orgSelection'

function getApiBase(){
  try{
    if (typeof process !== 'undefined' && process.env && typeof process.env.REACT_APP_API_BASE !== 'undefined'){
      return process.env.REACT_APP_API_BASE || ''
    }
  }catch(e){}
  return ''
}

function baseForUrl(){
  const b = getApiBase()
  if (b && b.length) return b
  if (typeof window !== 'undefined' && window.location && window.location.origin) return window.location.origin
  return ''
}

function normalizeResponseJson(json) {
  if (!json) return null
  if (typeof json === 'object' && json.status && json.data !== undefined) return json.data
  return json
}

function attachOrgSelectionParams(urlObj){
  try{
    // Try canonical loader first
    try{
      const sel = loadOrgSelection()
      const active = (sel && sel.active) ? sel.active : (sel && sel.effective_rsid ? { rsid: sel.effective_rsid } : null)
      if (active && active.rsid) urlObj.searchParams.set('unit_rsid', active.rsid)
      if (active && active.echelon) urlObj.searchParams.set('echelon', active.echelon)
    }catch(e){
      // fallback to reading legacy LS keys
      try{
        let raw = localStorage.getItem('taaip.unitSelection.v1')
        if (!raw) raw = localStorage.getItem('taaip_org_selection_v1')
        if (!raw) raw = localStorage.getItem('ta aip.unitSelection.v1')
        if (!raw) raw = localStorage.getItem('taaip:selected_unit')
        if (raw){
          const sel = JSON.parse(raw)
          const active = (sel && sel.active) ? sel.active : (sel && sel.effective_rsid ? { rsid: sel.effective_rsid } : null)
          if (active && active.rsid) urlObj.searchParams.set('unit_rsid', active.rsid)
          if (active && active.echelon) urlObj.searchParams.set('echelon', active.echelon)
        }
      }catch(e2){ /* ignore */ }
    }

    // attach persisted filters (fy/qtr/compare) if present
    try{
      const rawFilters = localStorage.getItem('taaip.filters.v1')
      if (rawFilters){
        const f = JSON.parse(rawFilters)
        if (f && f.fy) urlObj.searchParams.set('fy', f.fy)
        if (f && f.qtr) urlObj.searchParams.set('qtr', f.qtr)
        if (f && f.compare) urlObj.searchParams.set('compare', f.compare)
      }
    }catch(e){}
  }catch(e){}
}

// Fetch children units for a parent RSID and echelon. Falls back to units-summary if /children is unavailable.
export async function getOrgChildren(parent_rsid, echelon){
  try{
    const path = `/api/v2/org/children?parent_rsid=${encodeURIComponent(parent_rsid)}&echelon=${encodeURIComponent(echelon)}`
    const resp = await apiFetch(path, { includeUnit: false })
    // expected shape: { data: { units: [...] } }
    if (resp && resp.data && Array.isArray(resp.data.units)) return resp.data.units
    // some implementations may return { data: { children: [...] } }
    if (resp && resp.data && Array.isArray(resp.data.children)) return resp.data.children
    return []
  }catch(e){
    // fallback to units-summary and filter locally
    try{
      const summary = await apiFetch('/api/v2/org/units-summary', { includeUnit: false })
      const data = (summary && summary.data) ? summary.data : summary
      // Collect all units into a single array and filter by parent and echelon
      const all = []
      if (Array.isArray(data.brigades)) all.push(...data.brigades)
      if (Array.isArray(data.battalions)) all.push(...data.battalions)
      if (Array.isArray(data.companies)) all.push(...data.companies)
      if (Array.isArray(data.stations)) all.push(...data.stations)
      // Some older shapes may use different key names
      if (Array.isArray(data.bdes)) all.push(...data.bdes)
      if (Array.isArray(data.bns)) all.push(...data.bns)
      // Filter by parent and echelon
      const filtered = all.filter(u => {
        const matchParent = (!parent_rsid) || (u.parent_rsid === parent_rsid) || (u.parent_key === parent_rsid) || (u.parent === parent_rsid)
        const matchEchelon = (!echelon) || (u.echelon === echelon) || (u.echelon_type === echelon) || (u.echelon_type === (echelon.toLowerCase && echelon.toLowerCase()))
        return matchParent && matchEchelon
      })
      return filtered
    }catch(err){
      return []
    }
  }
}

// Safe fetch helper: returns a consistent error shape instead of throwing.
async function safeGet(path, opts = {}) {
  try {
    const token = localStorage.getItem('taaip_jwt')
    const headers = Object.assign({}, opts.headers || {})
    if (token) headers['Authorization'] = `Bearer ${token}`
    const includeUnit = opts.includeUnit !== false
    // remove internal flag before passing to fetch
    const fetchOpts = Object.assign({}, opts)
    delete fetchOpts.includeUnit
    const urlObj = path.startsWith('http') ? new URL(path) : new URL(path, baseForUrl())
    if (includeUnit) attachOrgSelectionParams(urlObj)
    const url = urlObj.toString()
    const res = await fetch(url, Object.assign({}, fetchOpts, { headers }))
    if (!res.ok) {
      return { status: 'error', http_status: res.status, path: url, message: `HTTP ${res.status}` }
    }
    const text = await res.text()
    try { return text ? JSON.parse(text) : null } catch(e){ return { status: 'error', http_status: 0, path: url, message: String(e?.message || e) } }
  } catch (e) {
    return { status: 'error', http_status: 0, path, message: String(e?.message || e) }
  }
}

export async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem('taaip_jwt')
  const headers = Object.assign({'Accept': 'application/json'}, opts.headers || {})
  if (token) headers['Authorization'] = `Bearer ${token}`
  const includeUnit = opts.includeUnit !== false
  const fetchOpts = Object.assign({}, opts)
  delete fetchOpts.includeUnit
  const urlObj = path.startsWith('http') ? new URL(path) : new URL(path, baseForUrl())
  if (includeUnit) attachOrgSelectionParams(urlObj)

  const url = urlObj.toString()
  const res = await fetch(url, Object.assign({}, fetchOpts, {headers}))
  const text = await res.text()
  let json = null
  try { json = text ? JSON.parse(text) : null } catch(e){ json = null }

  if (res.status === 401 || res.status === 403) {
    const err = new Error('unauthorized')
    err.status = res.status
    err.body = json || text
    throw err
  }
  if (!res.ok) {
    const err = new Error('request failed')
    err.status = res.status
    err.body = json || text
    throw err
  }

  return normalizeResponseJson(json) || null
}

export async function getHealth() {
  return apiFetch('/health')
}

function withScopeQs(scope, value){
  // if scope isn't provided, fall back to persisted scope in localStorage
  try { if (!scope) scope = localStorage.getItem('taaip_scope') } catch(e) { /* ignore */ }
  const qs = new URLSearchParams()
  if (scope) qs.set('scope', scope)
  if (value) qs.set('value', value)
  // include selected unit_key when available
  try{
    let raw = localStorage.getItem('taaip.unitSelection.v1')
    if (!raw) raw = localStorage.getItem('taaip_org_selection_v1')
    if (!raw) raw = localStorage.getItem('ta aip.unitSelection.v1')
    if (!raw) raw = localStorage.getItem('taaip:selected_unit')
    if (raw){
      const sel = JSON.parse(raw)
      if (sel && sel.effective_rsid) qs.set('unit_rsid', sel.effective_rsid)
    }
  }catch(e){}
  const s = qs.toString()
  return s ? `?${s}` : ''
}

export async function getCommandSummary(scope, value){
  const qs = withScopeQs(scope, value)
  const primary = `/api/v2/command/summary${qs}`
  try { return await apiFetch(primary) } catch(e){
    const legacy = `/api/org/command/summary${qs}`
    return apiFetch(legacy)
  }
}

export async function getCoverageSummary(scope, value){
  const qs = withScopeQs(scope, value)
  const primary = `/api/v2/coverage/summary${qs}`
  try { return await apiFetch(primary) } catch(e){
    const legacy = `/api/org/coverage/summary${qs}`
    return apiFetch(legacy)
  }
}

export async function getKpis(scope){
  const qs = new URLSearchParams()
  if (scope) qs.set('scope', scope)
  // append deepest selected RSID (unit_rsid) + echelon when present
  try{
    let raw = localStorage.getItem('taaip.unitSelection.v1')
    if (!raw) raw = localStorage.getItem('taaip_org_selection_v1')
    if (!raw) raw = localStorage.getItem('ta aip.unitSelection.v1')
    if (!raw) raw = localStorage.getItem('taaip:selected_unit')
    if (raw){
      const sel = JSON.parse(raw)
      const active = (sel && sel.active) ? sel.active : (sel && sel.effective_rsid ? { rsid: sel.effective_rsid, echelon: sel.echelon } : null)
      if (active && active.rsid) qs.set('unit_rsid', active.rsid)
      if (active && active.echelon) qs.set('echelon', active.echelon)
    }
  }catch(e){}
  const path = `/api/powerbi/kpis?${qs.toString()}`
  try {
    return await apiFetch(path)
  } catch(e){
    return []
  }
}

export async function getHomeNews(limit = 50){
  const resp = await safeGet(`/api/v2/home/news?limit=${limit}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

export async function getHomeUpdates(limit = 50){
  return apiFetch(`/api/v2/home/updates?limit=${limit}`)
}

export async function getHomeQuickLinks(limit = 50){
  return apiFetch(`/api/v2/home/quick-links?limit=${limit}`)
}

// Home portal clients (PHASE-12)
export async function getHomeStatusStrip(){
  const resp = await safeGet('/api/home/status-strip')
  return (resp && resp.status === 'error') ? { status: 'ok', data: [] } : resp
}

export async function getHomeAlerts(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/home/alerts?${params}`)
}

export async function ackHomeAlert(alertId){
  return apiFetch(`/api/home/alerts/${alertId}/ack`, { method: 'POST' })
}

export async function getHomeFlashes(qs = {}){
  const params = new URLSearchParams(qs).toString()
  const resp = await safeGet(`/api/home/flashes?${params}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

// New Home feed clients (Phase 15C awareness)
export async function getHomeFlash(limit = 25){
  const resp = await safeGet(`/api/home/flash?limit=${limit}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

export async function createHomeFlash(payload){
  return apiFetch('/api/home/flash', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getHomeMessages(limit = 25){
  const resp = await safeGet(`/api/home/messages?limit=${limit}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

export async function createHomeMessage(payload){
  return apiFetch('/api/home/messages', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getHomeRecognitionItems(limit = 25){
  const resp = await safeGet(`/api/home/recognition?limit=${limit}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

// Backwards-compatible aliases used elsewhere in the app
export async function getHomeRecognition(limit = 25){
  return getHomeRecognitionItems(limit)
}

export async function createHomeRecognition(payload){
  return apiFetch('/api/home/recognition', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getHomeUpcoming(limit = 25){
  const resp = await safeGet(`/api/home/upcoming?limit=${limit}`)
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

export async function createHomeUpcoming(payload){
  return apiFetch('/api/home/upcoming', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getHomeReferenceRails(){
  const resp = await safeGet('/api/home/reference-rails')
  return (resp && resp.status === 'error') ? { status: 'ok', items: [], warnings: [resp] } : resp
}

// Backwards-compatible alias
export async function getHomeReferences(){
  return getHomeReferenceRails()
}

export async function createHomeReferenceRail(payload){
  return apiFetch('/api/home/reference-rails', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getMe(){
  const resp = await safeGet('/api/me')
  if (!resp || resp.status === 'error') return null
  return resp
}

// Export API
export async function createExport(payload){
  return apiFetch('/api/v2/exports', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getExport(exportId){
  return apiFetch(`/api/v2/exports/${encodeURIComponent(exportId)}`)
}

export async function listMyExports(){
  return apiFetch('/api/v2/exports?mine=true')
}

export function downloadExportFile(exportId, fileId){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  return `${baseForUrl()}/api/v2/exports/${encodeURIComponent(exportId)}/files/${encodeURIComponent(fileId)}`
}

// Admin RBAC clients
export async function getAdminPermissionsRegistry(){
  return apiFetch('/api/v2/admin/permissions/registry')
}

export async function listAdminUsers(){
  return apiFetch('/api/v2/admin/users')
}

export async function getAdminUserPermissions(userId){
  return apiFetch(`/api/v2/admin/users/${userId}/permissions`)
}

export async function grantAdminPermission(userId, permissionKey){
  return apiFetch(`/api/v2/admin/users/${userId}/permissions/grant`, { method: 'POST', body: JSON.stringify({ permission_key: permissionKey }), headers: {'Content-Type':'application/json'} })
}

export async function revokeAdminPermission(userId, permissionKey){
  return apiFetch(`/api/v2/admin/users/${userId}/permissions/revoke`, { method: 'POST', body: JSON.stringify({ permission_key: permissionKey }), headers: {'Content-Type':'application/json'} })
}

export async function inviteAdminUser(payload){
  return apiFetch('/api/v2/admin/users/invite', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function importAdminUsers(file){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${baseForUrl()}/api/v2/admin/users/import`, { method: 'POST', body: form, headers })
  if (!res.ok) throw new Error('import failed')
  return res.json()
}

export async function setAdminUserRoles(userId, roles){
  return apiFetch(`/api/v2/admin/users/${userId}/roles`, { method: 'PUT', body: JSON.stringify({ roles }), headers: {'Content-Type':'application/json'} })
}

export async function setAdminUserStatus(userId, status){
  return apiFetch(`/api/v2/admin/users/${userId}/status`, { method: 'PUT', body: JSON.stringify({ status }), headers: {'Content-Type':'application/json'} })
}

export async function setAdminUserPermissionOverrides(userId, overrides){
  return apiFetch(`/api/v2/admin/users/${userId}/permissions`, { method: 'PUT', body: JSON.stringify({ overrides }), headers: {'Content-Type':'application/json'} })
}

// Tactical/Command Center clients
export async function getMissionAssessment(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command-center/mission-assessment?${params}`)
}

export async function exportDashboard(type, format='csv', qs = {}){
  const params = new URLSearchParams(qs)
  if (format) params.set('format', format)
  if (type) params.set('type', type)
  const path = `/api/exports/dashboard?${params.toString()}`
  // For csv we want raw text; apiFetch normalizes JSON — fetch directly for CSV
  if (format === 'csv'){
    const token = localStorage.getItem('taaip_jwt')
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const res = await fetch(`${baseForUrl()}${path}`, { headers })
    if (!res.ok) throw new Error('export failed')
    return res.text()
  }
  return apiFetch(path)
}

export async function exportCommanderTargetsCsv(qs = {}){
  const params = new URLSearchParams(qs)
  const path = `/api/market-intel/exports/commander-targets.csv?${params.toString()}`
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}${path}`, { headers })
  if (!res.ok) throw new Error('export failed')
  return res.text()
}

export async function getVirtualTechBrief(){
  return apiFetch('/api/home/virtual-tech-brief')
}

export async function getOrgUnitsSummary(){
  return apiFetch('/api/v2/org/units-summary')
}

export function getCurrentUserFromToken(){
  try{
    const token = localStorage.getItem('taaip_jwt')
    if(!token) return null
    const parts = token.split('.')
    if(parts.length<2) return null
    const payload = JSON.parse(atob(parts[1].replace(/-/g,'+').replace(/_/g,'/')))
    return { username: payload.username || payload.sub, roles: payload.roles || payload.role || [], scopes: payload.scopes || payload.scope || [] }
  }catch(e){ return null }
}

export async function uploadImport(fd){
  const url = `/api/import/upload`
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}${url}`, { method: 'POST', body: fd, headers })
  if (!res.ok) throw new Error('upload failed')
  return res.json()
}

export async function importUpload(fd){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/import/upload`, { method: 'POST', body: fd, headers })
  if (!res.ok) throw new Error('upload failed')
  return res.json()
}

export async function importParse(import_job_id){
  return apiFetch('/api/import/parse', { method: 'POST', body: JSON.stringify({ import_job_id }), headers: {'Content-Type':'application/json'} })
}

export async function importMap(import_job_id, mapping, dataset_key, source_system, scope_org_unit_id){
  return apiFetch('/api/import/map', { method: 'POST', body: JSON.stringify({ import_job_id, mapping, dataset_key, source_system, scope_org_unit_id }), headers: {'Content-Type':'application/json'} })
}

export async function importValidate(import_job_id){
  return apiFetch('/api/import/validate', { method: 'POST', body: JSON.stringify({ import_job_id }), headers: {'Content-Type':'application/json'} })
}

export async function importCommit(import_job_id, mode='append'){
  try {
    return await apiFetch('/api/import/commit', { method: 'POST', body: JSON.stringify({ import_job_id, mode }), headers: {'Content-Type':'application/json'} })
  } catch (err) {
    // If v3 commit fails (route/validation), attempt compat endpoint that invokes legacy commit
    try {
      return await apiFetch('/api/import/compat/commit_v3', { method: 'POST', body: JSON.stringify({ import_job_id, mode }), headers: {'Content-Type':'application/json'} })
    } catch (err2) {
      throw err
    }
  }
}

// Orchestrate a simple import flow for an existing v3 import job.
export async function runImportFlow(import_job_id = null, mapping = null, mode = 'append'){
  // If no import_job_id provided, pick the most recent v3 job
  try{
    if (!import_job_id){
      const jobs = await apiFetch('/api/import/jobs')
      if (Array.isArray(jobs) && jobs.length>0) import_job_id = jobs[0].id
    }
    if (!import_job_id) throw new Error('no import_job_id available')

    // parse (idempotent if already parsed)
    await importParse(import_job_id)

    // apply mapping if provided, otherwise try to reuse existing mapping by fetching job details
    if (!mapping){
      try{
        const job = await apiFetch(`/api/import/jobs/${import_job_id}`)
        const maps = job && job.mappings ? job.mappings : []
        if (maps && maps.length>0) mapping = JSON.parse(maps[0].mapping_json)
      }catch(e){}
    }

    if (mapping){
      await importMap(import_job_id, mapping, mapping.dataset_key || (mapping.dataset_key===undefined? null: mapping.dataset_key), mapping.source_system || 'ui', mapping.scope_org_unit_id || null)
    }

    await importValidate(import_job_id)
    const res = await importCommit(import_job_id, mode)
    return res
  }catch(e){
    throw e
  }
}

export async function previewMiImport(formData){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/imports/mi/preview`, { method: 'POST', body: formData, headers })
  if (!res.ok) throw new Error('preview failed')
  return res.json()
}

export async function commitMiImport(formData){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/imports/mi/commit`, { method: 'POST', body: formData, headers })
  if (!res.ok) throw new Error('commit failed')
  return res.json()
}

export async function previewFoundationImport(formData){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/imports/foundation/preview`, { method: 'POST', body: formData, headers })
  if (!res.ok) throw new Error('preview failed')
  return res.json()
}

export async function commitFoundationImport(formData){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/imports/foundation/commit`, { method: 'POST', body: formData, headers })
  if (!res.ok) throw new Error('commit failed')
  return res.json()
}

// Documents API
export async function uploadDocumentForm(formData){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/documents/upload`, { method: 'POST', body: formData, headers })
  if (!res.ok) throw new Error('upload failed')
  return res.json()
}

export async function listDocuments(){
  return apiFetch('/api/documents')
}

export function documentDownloadUrl(docId){
  return `${baseForUrl()}/api/documents/${docId}/download`
}

export async function getSchoolProgramReadiness(){
  return apiFetch('/api/school-program/readiness')
}

export async function getSchoolProgramSummary(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school-program/summary?${params}`)
}

export async function getSchoolSummary(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/summary?${params}`)
}

export async function getSchoolCoverage(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/coverage?${params}`)
}

export async function getSchoolMilestones(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/milestones?${params}`)
}

export async function postSchoolMilestone(payload){
  return apiFetch('/api/school/milestones', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getSchoolCompliance(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/compliance?${params}`)
}

export async function getSchoolLeadflow(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/leadflow?${params}`)
}

export async function getSchoolEvents(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/events?${params}`)
}

export async function postSchoolEvent(payload){
  return apiFetch('/api/school/events', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getSuggestWindow(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/school/suggest_window?${params}`)
}

export async function getRegulatoryReferences(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/resources/regulatory?${params}`)
}

export async function getRegulatoryReference(id){
  return apiFetch(`/api/resources/regulatory/${id}`)
}

export async function getTraceabilityLinks(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/regulatory/traceability?${params}`)
}

export async function getModuleRegistry(){
  return apiFetch(`/api/regulatory/modules`)
}

export async function getRegulatoryReferencesApi(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/regulatory/references?${params}`)
}

export async function importJobs(){
  return apiFetch('/api/import/jobs')
}

export async function importJobDetail(import_job_id){
  return apiFetch(`/api/import/jobs/${import_job_id}`)
}

export async function importTemplate(dataset_key){
  return apiFetch(`/api/import/templates/${dataset_key}`)
}

export async function parseImport(jobId, opts = {}){
  const qs = new URLSearchParams()
  if (opts.sheet) qs.set('sheet', opts.sheet)
  const res = await apiFetch(`/api/import/${jobId}/parse?${qs.toString()}`)
  return res
}

export async function getImport(jobId){
  return apiFetch(`/api/import/${jobId}`)
}

export async function mapImport(jobId, mapping){
  return apiFetch(`/api/import/${jobId}/map`, { method: 'POST', body: JSON.stringify(mapping), headers: {'Content-Type':'application/json'} })
}

export async function validateImport(jobId){
  return apiFetch(`/api/import/${jobId}/validate`, { method: 'POST', body: JSON.stringify({}), headers: {'Content-Type':'application/json'} })
}

export async function commitImport(jobId){
  return apiFetch(`/api/import/${jobId}/commit`, { method: 'POST' })
}

export async function getAnalyticsSummary(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/analytics/summary?${params}`)
}

export async function getBudgetDashboard(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/budget/dashboard?${params}`)
}

export async function getProjectsDashboard(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/dash/projects/dashboard?${params}`)
}

export async function getEventsDashboard(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/dash/events/dashboard?${params}`)
}

export async function getPerformanceDashboard(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/dash/performance/dashboard?${params}`)
}

export async function getAnalyticsFunnel(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/analytics/funnel?${params}`)
}

export async function getAnalyticsQBR(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/analytics/qbr?${params}`)
}

export async function getFunnelEvents(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/funnel/events?${params}`)
}

export async function postFunnelEvent(evt){
  return apiFetch('/api/funnel/events', { method: 'POST', body: JSON.stringify(evt), headers: {'Content-Type':'application/json'} })
}

export async function getFunnelStages(){
  return apiFetch('/api/funnel/stages')
}

export async function queryMetric(metric_id, params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.scope_type) qs.set('scope_type', params.scope_type)
  if (params.scope_value) qs.set('scope_value', params.scope_value)
  if (params.station_rsid) qs.set('station_rsid', params.station_rsid)
  if (params.event_id) qs.set('event_id', params.event_id)
  return apiFetch(`/api/metrics/query?metric_id=${encodeURIComponent(metric_id)}&${qs.toString()}`)
}

// PowerBI / feeds
export async function getFactProduction(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/powerbi/fact_production?${params}`)
}

export async function getFactFunnel(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/powerbi/fact_funnel?${params}`)
}

export async function getDimOrgUnit(){
  return apiFetch('/api/powerbi/dim_org_unit')
}

export async function getDimTime(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/powerbi/dim_time?${params}`)
}

// Mission Assessment client
export async function getLatestMissionAssessment(period_type, scope){
  const qs = new URLSearchParams()
  if (period_type) qs.set('period_type', period_type)
  if (scope) qs.set('scope', scope)
  return apiFetch(`/api/mission_assessments/latest?${qs.toString()}`)
}

export async function getMissionFeasibilitySummary(params = {}){
  const qs = new URLSearchParams()
  if (params.unit_rsid) qs.set('unit_rsid', params.unit_rsid)
  if (params.fy) qs.set('fy', params.fy)
  if (params.compare_mode) qs.set('compare_mode', params.compare_mode)
  return apiFetch(`/api/v2/mission-feasibility/summary?${qs.toString()}`)
}

export async function getFsLossSummary(params = {}){
  const qs = new URLSearchParams()
  if (params.unit_rsid) qs.set('unit_rsid', params.unit_rsid)
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  return apiFetch(`/api/v2/fs-loss/summary?${qs.toString()}`)
}

export async function getFsLossCodes(){
  return apiFetch(`/api/v2/fs-loss/codes`)
}

export async function saveMissionAssessment(payload){
  return apiFetch('/api/mission_assessments/', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getImportJobsList(limit=100){
  return apiFetch(`/api/powerbi/import_jobs?limit=${limit}`)
}

export async function exportFactProduction(qs = {}, format='json'){
  const params = new URLSearchParams(qs)
  if (format) params.set('format', format)
  return apiFetch(`/api/powerbi/exports/fact_production?${params.toString()}`)
}

export async function exportFactMarketing(qs = {}, format='json'){
  const params = new URLSearchParams(qs)
  if (format) params.set('format', format)
  return apiFetch(`/api/powerbi/exports/fact_marketing?${params.toString()}`)
}

// Maintenance admin endpoints
export async function runDeduplicate(tables = null){
  const body = tables ? { tables } : {}
  return apiFetch(`/api/admin/deduplicate`, { method: 'POST', body: JSON.stringify(body), headers: {'Content-Type':'application/json'} })
}

export async function runPurge(days = 90, dry_run = false, tables = null){
  const body = { days, tables, dry_run }
  return apiFetch(`/api/admin/purge_archived`, { method: 'POST', body: JSON.stringify(body), headers: {'Content-Type':'application/json'} })
}

export async function listMaintenanceRuns(limit=100){
  return apiFetch(`/api/admin/maintenance_runs?limit=${limit}`)
}

export async function listSchedules(){
  return apiFetch('/api/admin/schedules')
}

export async function createSchedule(payload){
  return apiFetch('/api/admin/schedules', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateSchedule(id, payload){
  return apiFetch(`/api/admin/schedules/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function triggerSchedule(id){
  return apiFetch(`/api/admin/schedules/${id}/trigger`, { method: 'POST', body: JSON.stringify({}) , headers: {'Content-Type':'application/json'} })
}

// System Controlled Update System (CUS) clients
export async function listSystemObservations(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/system/observations?${params}`)
}

export async function postSystemObservation(payload){
  return apiFetch('/api/system/observations', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function listProposals(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/system/proposals?${params}`)
}

export async function createProposal(payload){
  return apiFetch('/api/system/proposals', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function submitProposal(id){
  return apiFetch(`/api/system/proposals/${id}/submit`, { method: 'POST', body: JSON.stringify({}) , headers: {'Content-Type':'application/json'} })
}

export async function reviewProposal(id, payload){
  return apiFetch(`/api/system/proposals/${id}/review`, { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getSystemFreshness(){
  return apiFetch('/api/system/freshness')
}

export async function getSystemAlerts(){
  return apiFetch('/api/system/alerts')
}

export async function getSystemAlertsList(){
  return apiFetch('/api/system/alerts/list')
}

// Market Intelligence clients (Phase 13)
export async function getMarketIntelSummary(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.month) qs.set('month', params.month)
  if (params.unit_key) {
    qs.set('unit_key', params.unit_key)
    try { if (params.unit_key) qs.set('rsid_prefix', String(params.unit_key).slice(0, Math.min(4, String(params.unit_key).length))) } catch(e){}
  } else if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  return apiFetch(`/api/market-intel/summary?${qs.toString()}`)
}

export async function getMarketIntelZipRankings(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.month) qs.set('month', params.month)
  if (params.unit_key) {
    qs.set('unit_key', params.unit_key)
    try { if (params.unit_key) qs.set('rsid_prefix', String(params.unit_key).slice(0, Math.min(4, String(params.unit_key).length))) } catch(e){}
  } else if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  if (params.limit) qs.set('limit', params.limit)
  return apiFetch(`/api/market-intel/zip-rankings?${qs.toString()}`)
}

export async function getMarketIntelCbsaRollup(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.unit_key) {
    qs.set('unit_key', params.unit_key)
    try { if (params.unit_key) qs.set('rsid_prefix', String(params.unit_key).slice(0, Math.min(4, String(params.unit_key).length))) } catch(e){}
  } else if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  if (params.limit) qs.set('limit', params.limit)
  return apiFetch(`/api/market-intel/cbsa-rollup?${qs.toString()}`)
}

export async function getMarketIntelTargets(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.unit_key) {
    qs.set('unit_key', params.unit_key)
    try { if (params.unit_key) qs.set('rsid_prefix', String(params.unit_key).slice(0, Math.min(4, String(params.unit_key).length))) } catch(e){}
  } else if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  return apiFetch(`/api/market-intel/targets?${qs.toString()}`)
}

export async function getMarketIntelImportTemplates(){
  return apiFetch('/api/market-intel/import-templates')
}

// Data Hub client helpers
export async function dataHubUpload(fd, dry_run = true){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}/api/v2/datahub/uploads?dry_run=${dry_run?1:0}`, { method: 'POST', body: fd, headers })
  if (!res.ok) throw new Error('upload failed')
  return res.json()
}

export async function dataHubListImports(){
  return apiFetch('/api/v2/datahub/imports')
}

export async function dataHubListRegistry(){
  return apiFetch('/api/v2/datahub/supported')
}

// ROI client helpers
export async function getRoiKpis(params = {}){
  const qs = new URLSearchParams(params).toString()
  return apiFetch(`/api/v2/roi/kpis?${qs}`)
}

export async function getRoiBreakdown(params = {}){
  const qs = new URLSearchParams(params).toString()
  return apiFetch(`/api/v2/roi/breakdown?${qs}`)
}

export async function getRoiFunnel(params = {}){
  const qs = new URLSearchParams(params).toString()
  return apiFetch(`/api/v2/roi/funnel?${qs}`)
}

export async function getRoiEvent(eventId, params = {}){
  const qs = new URLSearchParams(params).toString()
  return apiFetch(`/api/v2/roi/event/${encodeURIComponent(eventId)}?${qs}`)
}

export async function getMarketIntelReadiness(){
  return apiFetch('/api/market-intel/readiness')
}

export async function getPhoneticsReadiness(){
  return apiFetch('/api/phonetics/readiness')
}

export async function getSystemSelfCheck(){
  return apiFetch('/api/system/self-check')
}

export async function getMarketIntelDemographics(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.unit_key) {
    qs.set('unit_key', params.unit_key)
    try { if (params.unit_key) qs.set('rsid_prefix', String(params.unit_key).slice(0, Math.min(4, String(params.unit_key).length))) } catch(e){}
  } else if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  return apiFetch(`/api/market-intel/demographics?${qs.toString()}`)
}

export async function getMarketIntelCategories(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  if (params.limit) qs.set('limit', params.limit)
  return apiFetch(`/api/market-intel/categories?${qs.toString()}`)
}

export async function exportMarketIntelTargetsCsv(params = {}){
  const qs = new URLSearchParams()
  if (params.fy) qs.set('fy', params.fy)
  if (params.qtr) qs.set('qtr', params.qtr)
  if (params.rsid_prefix) qs.set('rsid_prefix', params.rsid_prefix)
  if (params.limit) qs.set('limit', params.limit)
  const path = `/api/market-intel/export/targets.csv?${qs.toString()}`
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${baseForUrl()}${path}`, { headers })
  if (!res.ok) throw new Error('export failed')
  const text = await res.text()
  return text
}

export async function getMaintenance(){
  return apiFetch('/api/system/maintenance')
}

export async function setMaintenance(payload){
  return apiFetch('/api/system/maintenance', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function approveProposal(id){
  return apiFetch(`/api/system/proposals/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision: 'approve' }), headers: {'Content-Type':'application/json'} })
}

export async function rejectProposal(id){
  return apiFetch(`/api/system/proposals/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision: 'reject' }), headers: {'Content-Type':'application/json'} })
}

export async function getSystemStatus(){
  return apiFetch('/api/system/status')
}

export async function decideProposal(id, payload){
  return apiFetch(`/api/system/proposals/${id}/decision`, { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function markProposalApplied(id){
  return apiFetch(`/api/system/proposals/${id}/mark-applied`, { method: 'POST' })
}

// RBAC / admin
export async function listRoles(){
  return apiFetch('/api/rbac/roles')
}

export async function createRole(payload){
  return apiFetch('/api/rbac/roles', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateRole(roleId, payload){
  return apiFetch(`/api/rbac/roles/${roleId}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function createUser(payload){
  return apiFetch('/api/rbac/users', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function assignRole(payload){
  return apiFetch('/api/rbac/assign-role', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function listUsers(){
  return apiFetch('/api/rbac/users')
}
export async function getRoleUsers(roleId){
  return apiFetch(`/api/rbac/roles/${roleId}/users`)
}

export async function removeRole(payload){
  return apiFetch('/api/rbac/remove-role', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getProject(projectId){
  return apiFetch(`/api/projects/${projectId}`)
}

export async function deleteRole(roleId){
  return apiFetch(`/api/rbac/roles/${roleId}`, { method: 'DELETE' })
}
export async function deleteRoleForce(roleId){
  return apiFetch(`/api/rbac/roles/${roleId}?force=true`, { method: 'DELETE' })
}

export async function updateTask(taskId, payload){
  return apiFetch(`/api/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function assignTask(taskId, payload){
  return apiFetch(`/api/tasks/${taskId}/assign`, { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function listLOEs(){
  return apiFetch('/api/projects/loes')
}

export async function listLOEsForScope(scope){
  const qs = withScopeQs(scope)
  return apiFetch(`/api/projects/loes${qs}`)
}

export async function createLOE(payload){
  return apiFetch('/api/projects/loes', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateLOE(id, payload){
  return apiFetch(`/api/projects/loes/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function deleteLOE(id){
  return apiFetch(`/api/projects/loes/${id}`, { method: 'DELETE' })
}

// Command priorities client
export async function listCommandPriorities(scope){
  const qs = withScopeQs(scope)
  return apiFetch(`/api/projects/command_priorities${qs}`)
}

export async function getCommandBaseline(scope){
  const qs = withScopeQs(scope)
  return apiFetch(`/api/projects/command/baseline${qs}`)
}

export async function createCommandPriority(payload){
  return apiFetch('/api/projects/command_priorities', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateCommandPriority(id, payload){
  return apiFetch(`/api/projects/command_priorities/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function deleteCommandPriority(id){
  return apiFetch(`/api/projects/command_priorities/${id}`, { method: 'DELETE' })
}

export async function listPriorityLOEs(priorityId, scope){
  const qs = withScopeQs(scope)
  return apiFetch(`/api/projects/command_priorities/${priorityId}/loes${qs}`)
}

export async function assignLOEToPriority(priorityId, loeId){
  return apiFetch(`/api/projects/command_priorities/${priorityId}/loes`, { method: 'POST', body: JSON.stringify({ loe_id: loeId }), headers: {'Content-Type':'application/json'} })
}

export async function unassignLOEFromPriority(priorityId, loeId){
  return apiFetch(`/api/projects/command_priorities/${priorityId}/loes/${loeId}`, { method: 'DELETE' })
}

export async function listProjects(){
  return apiFetch('/api/projects/projects')
}

export async function listTasks(projectId){
  return apiFetch(`/api/projects/project/${projectId}/tasks`)
}

export async function createProject(payload){
  return apiFetch('/api/projects/projects', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function createTask(payload){
  return apiFetch('/api/projects/tasks', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getDomainProject(projectId){
  return apiFetch(`/api/projects/projects/${projectId}`)
}

export async function createMeeting(payload){
  return apiFetch('/api/meetings/', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function createCalendarEvent(payload){
  return apiFetch('/api/calendar/', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function listCalendarEvents(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/calendar/events?${params}`)
}

export async function updateCalendarEvent(id, payload){
  return apiFetch(`/api/calendar/events/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function deleteCalendarEvent(id){
  return apiFetch(`/api/calendar/events/${id}`, { method: 'DELETE' })
}

export async function getMarketPotential(scope, value){
  const qs = withScopeQs(scope, value)
  const primary = `/api/v2/coverage/market_potential${qs}`
  try { return await apiFetch(primary) } catch(e){
    const legacy = `/api/org/coverage/market_potential${qs}`
    return apiFetch(legacy)
  }
}

// Tactical rollup clients (PHASE-13)
export async function getBudgetRollup(qs = {}){
  return queryMetric('budget', qs)
}

export async function getEventsRollup(qs = {}){
  return queryMetric('events', qs)
}

export async function getMarketingRollup(qs = {}){
  return queryMetric('marketing', qs)
}

export async function getFunnelRollup(qs = {}){
  return queryMetric('funnel', qs)
}

export async function getCommandRollup(qs = {}){
  return queryMetric('command', qs)
}

// Command Center clients (PHASE-14)
export async function getCommandCenterOverview(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command-center/overview?${params}`)
}

export async function getCommandCenterPriorities(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command-center/priorities?${params}`)
}

export async function createCommandCenterPriority(payload){
  return apiFetch('/api/command-center/priorities', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateCommandCenterPriority(id, payload){
  return apiFetch(`/api/command-center/priorities/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function deleteCommandCenterPriority(id){
  return apiFetch(`/api/command-center/priorities/${id}`, { method: 'DELETE' })
}

export async function listCommandCenterLoes(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command-center/loes?${params}`)
}

export async function createCommandCenterLoe(payload){
  return apiFetch('/api/command-center/loes', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateCommandCenterLoe(id, payload){
  return apiFetch(`/api/command-center/loes/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function deleteCommandCenterLoe(id){
  return apiFetch(`/api/command-center/loes/${id}`, { method: 'DELETE' })
}

export async function evaluateCommandCenterLoes(){
  return apiFetch('/api/command-center/loes/evaluate')
}

export async function getCommandCenterMissionAssessment(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command-center/mission-assessment?${params}`)
}

// Operations Market Intelligence clients (PHASE-13)
export async function getMarketSummary(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/summary?${params}`)
}

export async function listMarketZips(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/zips?${params}`)
}

export async function listMarketCbsas(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/cbsa?${params}`)
}

export async function listMarketDemographics(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/demographics?${params}`)
}

export async function listGeoZones(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/geotargeting/zones?${params}`)
}

export async function createGeoZone(payload){
  return apiFetch('/api/ops/market/geotargeting/zones', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function updateGeoZone(id, payload){
  return apiFetch(`/api/ops/market/geotargeting/zones/${id}`, { method: 'PUT', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function exportTargetingList(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/targeting/export?${params}`)
}

// Market Intelligence compute + scoring clients
export async function getP2PBand(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/compute/p2p-band?${params}`)
}

export async function classifyZip(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/ops/market/compute/classify-zip?${params}`)
}

export async function getMarketCapacityScore(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command/scoring/market-capacity?${params}`)
}

export async function getMissionFeasibility(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command/scoring/mission-feasibility?${params}`)
}

export async function getCOARecommendations(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/command/coa/recommendations?${params}`)
}

// Tactical dashboards clients
export async function getEventsRoi(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/tactical/events-roi?${params}`)
}

export async function getTacticalMarketing(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/tactical/marketing?${params}`)
}

export async function getTacticalFunnel(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/tactical/funnel?${params}`)
}

const apiClient = {
  // home
  getHomeNews, getHomeUpdates, getHomeQuickLinks, getHomeStatusStrip, getHomeAlerts, ackHomeAlert, getHomeFlashes, getHomeUpcoming, getHomeRecognition, getHomeReferences,
  // health / summary
  getHealth, getCommandSummary, getCoverageSummary, getMarketPotential, getKpis, getOrgUnitsSummary,
  // auth / user
  getCurrentUserFromToken,
  // import helpers
  uploadImport, importUpload, importParse, importMap, importValidate, importCommit, importJobs, importJobDetail, importTemplate, parseImport, getImport, mapImport, validateImport, commitImport,
  // analytics
  getAnalyticsSummary, getAnalyticsFunnel, getAnalyticsQBR, getFunnelEvents, postFunnelEvent, getFunnelStages,
  // budget
  getBudgetDashboard, getProjectsDashboard, getEventsDashboard, getPerformanceDashboard,
  // powerbi
  getFactProduction, getFactFunnel, getDimOrgUnit, getDimTime,
  // mission assessment
  getLatestMissionAssessment, saveMissionAssessment,
  // imports/exports
  getImportJobsList, exportFactProduction, exportFactMarketing,
  // maintenance
  runDeduplicate, runPurge, listMaintenanceRuns, listSchedules, createSchedule, updateSchedule, triggerSchedule,
  // rbac
  listRoles, createRole, updateRole, createUser, assignRole, listUsers, getRoleUsers, removeRole, deleteRole, deleteRoleForce,
  // projects / tasks / loes
  getProject, updateTask, assignTask, listLOEs, listLOEsForScope, createLOE, updateLOE, deleteLOE,
  // legacy names
  listCommandPriorities, getCommandBaseline, createCommandPriority, updateCommandPriority, deleteCommandPriority, listPriorityLOEs, assignLOEToPriority, unassignLOEFromPriority,
  // command center (new names retained for compatibility)
  getCommandCenterPriorities, createCommandCenterPriority, updateCommandCenterPriority, deleteCommandCenterPriority,
  listCommandCenterLoes, createCommandCenterLoe, updateCommandCenterLoe, deleteCommandCenterLoe, evaluateCommandCenterLoes, getCommandCenterOverview, getCommandCenterMissionAssessment,
  listProjects, listTasks, createProject, createTask, createMeeting,
  // calendar
  createCalendarEvent, listCalendarEvents, updateCalendarEvent, deleteCalendarEvent,
  // market
  getMarketPotential, getBudgetRollup, getEventsRollup, getMarketingRollup, getFunnelRollup, getCommandRollup
  , getMarketSummary, listMarketZips, listMarketCbsas, listMarketDemographics, listGeoZones, createGeoZone, updateGeoZone, exportTargetingList
  // system CUS
  , listSystemObservations, postSystemObservation, listProposals, createProposal, submitProposal, reviewProposal
}

export default apiClient
