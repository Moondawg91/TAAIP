import React, { useEffect, useState } from 'react'
import { Box, Typography, Button } from '@mui/material'
import { useLocation, useNavigate } from 'react-router-dom'
import { getMe } from '../api/client'

export default function UnauthorizedPage(){
  const loc = useLocation()
  const nav = useNavigate()
  const qs = new URLSearchParams(loc.search || '')
  const queryMissing = qs.getAll('missing') || []
  const queryPath = qs.get('path')
  const stateMissing = (loc.state && loc.state.missing) || []
  const statePath = (loc.state && loc.state.path) || null
  const missing = Array.isArray(stateMissing) && stateMissing.length ? stateMissing : (queryMissing.length ? queryMissing : [])
  const requestedPath = statePath || queryPath || '/'
  const [me, setMe] = useState(null)

  useEffect(()=>{ getMe().then(m=> setMe(m && m.user ? m.user : m)).catch(()=>{}) }, [])

  function requestAccess(){
    const userEmail = (me && (me.email || me.username)) || ''
    const subject = encodeURIComponent(`Access request: ${requestedPath}`)
    const body = encodeURIComponent(`Hello,

I am requesting access to ${requestedPath}.

Missing permission(s): ${missing.join(', ')}

User: ${userEmail}

Thanks.`)
    window.location.href = `mailto:it-admin@example.com?subject=${subject}&body=${body}`
  }

  return (
    <Box sx={{ p:4 }}>
      <Typography variant="h5">Access Restricted</Typography>
      <Typography variant="body1" sx={{ mt:2 }}>You do not have the required permission(s) to view this page.</Typography>
      <Box sx={{ mt:2 }}>
        <Typography variant="subtitle2">Requested page:</Typography>
        <Typography variant="body2">{requestedPath}</Typography>
      </Box>
      {missing && missing.length>0 && (
        <Box sx={{ mt:2 }}>
          <Typography variant="subtitle2">Missing permission(s):</Typography>
          <ul>
            {missing.map((m, i) => <li key={i}><code>{m}</code></li>)}
          </ul>
        </Box>
      )}
      <Box sx={{ mt:3, display:'flex', gap:2 }}>
        <Button variant="contained" onClick={requestAccess}>Request access</Button>
        <Button onClick={()=>nav('/')}>Back to Home</Button>
      </Box>
    </Box>
  )
}
