import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import accessHelper from './accessHelper'

export default function RequirePermission({ children }: { children?: React.ReactNode }){
  const loc = useLocation()
  const nav = useNavigate()
  const { permissionsObj, permissions, isAdmin, loading, hasPerm } = useAuth() as any

  // while loading auth, render children to avoid flicker; auth context provides baseline perms
  if (loading) return <>{children}</>

  const path = loc.pathname
  // Prefer accessHelper for path->permission mapping, but evaluate using hasPerm to avoid direct permission lookups
  const ap = accessHelper.canAccessForPath(permissionsObj && Object.keys(permissionsObj).length ? Object.keys(permissionsObj) : permissions, path)
  // If accessHelper says allowed or we have any of the missing perms via hasPerm, allow
  if (ap.allowed) return <>{children}</>
  const anyMissingGranted = (ap.missing || []).some(m => (hasPerm && hasPerm(m)))
  if (anyMissingGranted) return <>{children}</>

  // redirect to unauthorized page with missing perms info
  nav('/unauthorized', { replace: true, state: { missing: ap.missing || [], path } })
  return null
}
