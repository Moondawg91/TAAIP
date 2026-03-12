import ROUTE_POLICIES from './routePolicy'
import permissionMap from '../auth/permissionMap'
import routePerms from '../rbac/routePerms'

export function canAccessForPath(permissions: string[] | Record<string, boolean> | undefined, path?: string){
  const permSet: Record<string, boolean> = {}
  if(!permissions) permissions = []
  if(Array.isArray(permissions)){
    for(const p of permissions) permSet[p]=true
  } else {
    Object.assign(permSet, permissions)
  }
  const adminIndicators = ['*', 'admin.full', 'admin_full', 'master', 'owner', 'admin']
  let isAdmin = false
  for (const k of adminIndicators) {
    if (permSet[k] || permSet[k.toLowerCase()] || permSet[k.toUpperCase()]) { isAdmin = true; break }
  }

  // determine required perms for route
  let reqsAny: string[] = []
  let reqsAll: string[] | undefined = undefined
  if (path) {
    const p = (ROUTE_POLICIES || []).find(rp => rp && rp.path && path.startsWith(rp.path))
    if (p) {
      if (p.requiredAll && p.requiredAll.length) reqsAll = p.requiredAll
      if (p.requiredAny && p.requiredAny.length) reqsAny = p.requiredAny
    }
  }
  if (reqsAny.length === 0 && !reqsAll && permissionMap[path || '']) {
    const v = permissionMap[path || ''] as any
    reqsAny = Array.isArray(v) ? v : [v]
  }
  if (reqsAny.length === 0 && !reqsAll && routePerms[path || '']) {
    const v = routePerms[path || ''] as any
    reqsAny = Array.isArray(v) ? v : [v]
  }

  const missing: string[] = []
  let allowed = false
  if (isAdmin) allowed = true
  else if (reqsAll && reqsAll.length) {
    allowed = reqsAll.every(r => Boolean(permSet[r] || permSet[r.toLowerCase()] || permSet[r.toUpperCase()]))
    if(!allowed) reqsAll.forEach(r => { if(!permSet[r] && !permSet[r.toLowerCase()] && !permSet[r.toUpperCase()]) missing.push(r) })
  } else if (reqsAny && reqsAny.length) {
    allowed = reqsAny.some(r => Boolean(permSet[r] || permSet[r.toLowerCase()] || permSet[r.toUpperCase()]))
    if(!allowed) reqsAny.forEach(r => { if(!permSet[r] && !permSet[r.toLowerCase()] && !permSet[r.toUpperCase()]) missing.push(r) })
  } else {
    // no perms required
    allowed = true
  }
  return { allowed, missing }
}

export default { canAccessForPath }
