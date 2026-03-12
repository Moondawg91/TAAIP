export type User = { permissions?: string[]; roles?: string[] }

export function isMaster(user?: User | null): boolean {
  if (!user) return false
  const perms = user.permissions || []
  const roles = user.roles || []
  if (Array.isArray(perms) && perms.includes('*')) return true
  if (Array.isArray(roles)){
    const lows = roles.map(r => String(r).toLowerCase())
    if (lows.includes('system_admin') || lows.includes('usarec_admin') || lows.includes('420t_admin')) return true
  }
  return false
}

export function canAccess(user: User | null | undefined, navItem: any): boolean {
  // master bypass
  if (isMaster(user)) return true

  // if navItem explicitly disabled, deny
  if (navItem && navItem.disabled) return false

  // simple rules for admin paths
  const path: string = (navItem && navItem.path) || ''
  const roles = (user && user.roles) || []
  const low = Array.isArray(roles) ? roles.map((r:any)=>String(r).toLowerCase()) : []
  if (path.startsWith('/admin')) {
    return low.includes('usarec_admin') || low.includes('admin')
  }

  // default allow
  return true
}

export default { isMaster, canAccess }
