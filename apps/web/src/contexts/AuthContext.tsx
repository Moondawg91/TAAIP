import React, { createContext, useContext, useEffect, useState } from 'react'
import { getMe } from '../api/client'

type AuthState = {
  roles: string[]
  permissions: string[]
  permissionsObj: Record<string, boolean>
  isAdmin: boolean
  loading: boolean
}

const AuthContext = createContext<AuthState>({ roles: [], permissions: [], permissionsObj: {}, isAdmin: false, loading: true })

export function AuthProvider({ children }: { children?: React.ReactNode }){
  const [roles, setRoles] = useState<string[]>([])
  const [permissions, setPermissions] = useState<string[]>([])
  const [permissionsObj, setPermissionsObj] = useState<Record<string, boolean>>({})
  const [isAdmin, setIsAdmin] = useState<boolean>(false)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    let canceled = false
    const baseline = ['dashboards.view','export.any']
    const devExtras = ['admin.full']
    getMe().then((me: any)=>{
      if(canceled) return
      if(!me) {
        // no user object returned
        const perms = baseline.slice()
        if (process.env.NODE_ENV === 'development') perms.push(...devExtras)
        setPermissions(perms)
        setPermissionsObj(perms.reduce((acc:any,p:any)=>{ acc[p]=true; return acc }, {}))
        setLoading(false)
        return
      }
      // normalize roles and permissions shape from backend /me
      if(me.roles && Array.isArray(me.roles)) setRoles(me.roles)
      // permissions may be array or object
      let permsArr: string[] = []
      if(me.permissions) {
        if(Array.isArray(me.permissions)) permsArr = me.permissions
        else if(typeof me.permissions === 'object') permsArr = Object.keys(me.permissions).filter(k=>me.permissions[k])
      }
      if(permsArr.length===0){
        // fallback to baseline so app remains usable
        permsArr = baseline.slice()
        if (process.env.NODE_ENV === 'development') permsArr.push(...devExtras)
        console.warn('Auth: no permissions from /auth/me — applying baseline permissions')
      }
      setPermissions(permsArr)
      setPermissionsObj(permsArr.reduce((acc:any,p:any)=>{ acc[p]=true; return acc }, {}))
      // mark admin if token or perms contain wildcard/admin indicators
      const hasAdmin = permsArr.some(p => p === '*' || p.toLowerCase() === 'admin.full' || p.toLowerCase() === 'admin_full' || p.toLowerCase() === 'master' || p.toLowerCase() === 'owner' || p.toLowerCase() === 'admin')
      if (me.is_admin || hasAdmin) setIsAdmin(true)
    }).catch((err)=>{
      if(canceled) return
      // on error, keep app usable by applying baseline permissions
      const perms = baseline.slice()
      if (process.env.NODE_ENV === 'development') perms.push(...devExtras)
      setPermissions(perms)
      setPermissionsObj(perms.reduce((acc:any,p:any)=>{ acc[p]=true; return acc }, {}))
      // in development fallback, mark admin if devExtras included
      const hasAdminFallback = (process.env.NODE_ENV === 'development' && (devExtras || []).some(d => d.toLowerCase().includes('admin')))
      if (hasAdminFallback) setIsAdmin(true)
      console.warn('Auth: /auth/me failed — applying baseline permissions', err)
    }).finally(()=>{ if(!canceled) setLoading(false) })
    return ()=>{ canceled = true }
  },[])

  return (
    <AuthContext.Provider value={{ roles, permissions, permissionsObj, isAdmin, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(){
  return useContext(AuthContext)
}

export default AuthContext
