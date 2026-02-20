import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

type Props = { children: React.ReactNode }

const ALLOWLIST = ['/maintenance', '/help/system-status', '/admin/system-self-check']

export default function MaintenanceGuard({ children }: Props) {
  const [mode, setMode] = useState<'on' | 'off' | 'unknown'>('unknown')
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    let mounted = true
    async function check() {
      try {
        const res = await fetch('/api/system/status')
        if (!res.ok) {
          setMode('off')
          return
        }
        const j = await res.json()
        const m = (j && j.maintenance_mode) ? String(j.maintenance_mode) : 'off'
        if (!mounted) return
        setMode(m === 'on' ? 'on' : 'off')
        if (m === 'on') {
          // if current path is not allowlisted, redirect to maintenance page
          const p = location.pathname || '/'
          if (!ALLOWLIST.includes(p) && !p.startsWith('/static') && p !== '/maintenance') {
            navigate('/maintenance', { replace: true })
          }
        }
      } catch (e) {
        // network error - assume off
        setMode('off')
      }
    }
    check()
    return () => { mounted = false }
  }, [location.pathname, navigate])

  return <>{children}</>
}
