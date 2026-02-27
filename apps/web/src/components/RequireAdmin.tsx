import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ADMIN_KEYS = ['system_admin','usarec_admin','sysadmin','admin','420t_admin']

export default function RequireAdmin({ children }: { children?: React.ReactNode }){
  const { roles, loading } = useAuth()
  const location = useLocation()

  if(loading) return null
  const has = roles && roles.some(r => ADMIN_KEYS.includes(r))
  if(!has) return <Navigate to="/" state={{ from: location }} replace />
  return <>{children}</>
}
