import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function RequirePerm({ perm, children }: { perm: string, children: any }){
  const auth = useAuth()
  const navigate = useNavigate()
  if (auth.loading) return null
  const allowed = Boolean(auth.permissions && auth.permissions[perm]) || Boolean(auth.isAdmin)
  if (!allowed){
    navigate('/access-denied')
    return null
  }
  return children
}
