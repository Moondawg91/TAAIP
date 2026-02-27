import { apiFetch } from './client'

export async function getOrgRoots() {
  const resp = await apiFetch('/api/v2/org/roots')
  if (!resp) return []
  return resp.roots || resp
}

// Wrapper: callers pass parent_key/unit_key; prefer resolving to parent_rsid and call v2.
export async function getOrgChildren(parent_key: string, echelon: string) {
  const parent_rsid = parent_key
  const qs = `?parent_rsid=${encodeURIComponent(parent_rsid)}&echelon=${encodeURIComponent(echelon)}`
  const resp = await apiFetch(`/api/v2/org/children${qs}`)
  if (!resp) return []
  return resp.children || resp
}

export async function getOrgPath(unit_key: string) {
  const qs = `?unit_key=${encodeURIComponent(unit_key)}`
  const resp = await apiFetch(`/api/v2/org/path${qs}`)
  return resp
}

export default { getOrgRoots, getOrgChildren, getOrgPath }
