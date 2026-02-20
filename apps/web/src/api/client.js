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

// Home portal clients (PHASE-12)
export async function getHomeStatusStrip(){
  return apiFetch('/api/home/status-strip')
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
  return apiFetch(`/api/home/flashes?${params}`)
}

export async function getHomeUpcoming(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/home/upcoming?${params}`)
}

export async function getHomeRecognition(){
  return apiFetch('/api/home/recognition')
}

export async function getHomeReferences(){
  return apiFetch('/api/home/references')
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
    const res = await fetch(`${API_BASE}${path}`, { headers })
    if (!res.ok) throw new Error('export failed')
    return res.text()
  }
  return apiFetch(path)
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
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/rollups/budget?${params}`)
}

export async function getEventsRollup(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/rollups/events?${params}`)
}

export async function getMarketingRollup(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/rollups/marketing?${params}`)
}

export async function getFunnelRollup(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/rollups/funnel?${params}`)
}

export async function getCommandRollup(qs = {}){
  const params = new URLSearchParams(qs).toString()
  return apiFetch(`/api/rollups/command?${params}`)
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
  getHomeNews, getHomeUpdates, getHomeQuickLinks,
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
  getMarketPotential
  // system CUS
  , listSystemObservations, postSystemObservation, listProposals, createProposal, submitProposal, reviewProposal
}

export default apiClient
