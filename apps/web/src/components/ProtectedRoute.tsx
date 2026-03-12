import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import accessHelper from '../auth/accessHelper'

type Props = {
  path?: string
  perm?: string
  required?: string | string[]
  children?: React.ReactNode
}

export default function ProtectedRoute({ path, perm, required, children }: Props){
  const auth = useAuth()
  if (auth.loading) return (
    <div style={{padding:24}}>Loading authorization…</div>
  )

  // If explicit `required` or `perm` props are provided, evaluate them first.
  if (required || perm) {
    const want = Array.isArray(required) ? required as string[] : (required ? [required as string] : (perm ? [perm] : []))
    if (!want || want.length===0) return <>{children}</>
    const allowed = want.some(w => (auth.hasPerm && auth.hasPerm(w)) || Boolean(auth.isAdmin))
    if (!allowed) return <Navigate to="/unauthorized" replace state={{ missing: want }} />
    return <>{children}</>
  }

  // Fallback to path-based policy checks
  const ap = accessHelper.canAccessForPath(auth.permissionsObj && Object.keys(auth.permissionsObj).length ? Object.keys(auth.permissionsObj) : auth.permissions, path)
  if (!ap.allowed && !(auth.hasPerm && ap.missing && ap.missing.some(m => auth.hasPerm(m)))) return <Navigate to="/unauthorized" replace state={{ missing: ap.missing }} />
  return <>{children}</>
}
