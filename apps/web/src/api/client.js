/* © 2026 TAAIP. Copyright pending. */

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000'

function normalizeResponseJson(json) {
  if (!json) return null
  if (typeof json === 'object' && json.status && json.data !== undefined) return json.data
  return json
}

async function apiFetch(path, opts = {}) {
  const token = localStorage.getItem('taaip_jwt')
  const headers = Object.assign({'Accept': 'application/json'}, opts.headers || {})
  if (token) headers['Authorization'] = `Bearer ${token}`

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const res = await fetch(url, Object.assign({}, opts, {headers}))
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
  const path = `/api/powerbi/kpis?${qs.toString()}`
  try {
    return await apiFetch(path)
  } catch(e){
    return []
  }
}

export async function getHomeNews(limit = 50){
  return apiFetch(`/api/v2/home/news?limit=${limit}`)
}

export async function getHomeUpdates(limit = 50){
  return apiFetch(`/api/v2/home/updates?limit=${limit}`)
}

export async function getHomeQuickLinks(limit = 50){
  return apiFetch(`/api/v2/home/quick-links?limit=${limit}`)
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
  const res = await fetch(`${API_BASE}${url}`, { method: 'POST', body: fd, headers })
  if (!res.ok) throw new Error('upload failed')
  return res.json()
}

export async function importUpload(fd){
  const token = localStorage.getItem('taaip_jwt')
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API_BASE}/api/import/upload`, { method: 'POST', body: fd, headers })
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
  return apiFetch('/api/import/commit', { method: 'POST', body: JSON.stringify({ import_job_id, mode }), headers: {'Content-Type':'application/json'} })
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

export async function createMeeting(payload){
  return apiFetch('/api/meetings/', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function createCalendarEvent(payload){
  return apiFetch('/api/calendar/', { method: 'POST', body: JSON.stringify(payload), headers: {'Content-Type':'application/json'} })
}

export async function getMarketPotential(scope, value){
  const qs = withScopeQs(scope, value)
  const primary = `/api/v2/coverage/market_potential${qs}`
  try { return await apiFetch(primary) } catch(e){
    const legacy = `/api/org/coverage/market_potential${qs}`
    return apiFetch(legacy)
  }
}

export default {
  getHealth, getCommandSummary, getCoverageSummary, getMarketPotential, getKpis
}
