/* © 2025 Maroon Moon, LLC. All rights reserved. */

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
  const qs = new URLSearchParams()
  if (scope) qs.set('scope', scope)
  if (value) qs.set('value', value)
  return `?${qs.toString()}`
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

export async function getMarketPotential(scope, value){
  const qs = withScopeQs(scope, value)
  const primary = `/api/v2/coverage/market_potential${qs}`
  try { return await apiFetch(primary) } catch(e){
    const legacy = `/api/org/coverage/market_potential${qs}`
    return apiFetch(legacy)
  }
}

export default {
  getHealth, getCommandSummary, getCoverageSummary, getMarketPotential
}
