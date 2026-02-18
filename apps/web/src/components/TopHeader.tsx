import React, { useEffect, useState } from 'react'
import { AppBar, Toolbar, Typography, Box, Chip, Menu, MenuItem, IconButton, Divider } from '@mui/material'
import api from '../api/client'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import { alpha } from '@mui/material'
import { useScope } from '../contexts/ScopeContext'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockIcon from '@mui/icons-material/Lock'

export default function TopHeader({ title }: { title?: string }){
  const [status, setStatus] = useState('unknown')
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)
  const [scopeAnchor, setScopeAnchor] = useState<null | HTMLElement>(null)
  const { scope, setScope } = useScope()
  const [orgs, setOrgs] = useState<any>(null)
  useEffect(()=>{
    let mounted = true
    api.getHealth().then(()=> mounted && setStatus('online')).catch(()=> mounted && setStatus('offline'))
    return ()=>{ mounted = false }
  }, [])

  return (
    <Box>
      <AppBar position="static" color="default" elevation={0} sx={{ background: (theme)=> `linear-gradient(90deg, ${alpha('#7C4DFF',0.08)}, transparent)`, borderBottom: `1px solid rgba(255,255,255,0.06)` }}>
        <Toolbar sx={{minHeight:64, px:2, bgcolor: 'background.paper'}}>
          <Box sx={{display:'flex', alignItems:'center', gap:2, flex:1}}>
            <Box>
              <Typography variant="h6" sx={{color:'text.primary', fontWeight:700}}>TAAIP</Typography>
              <Typography variant="caption" sx={{color:'text.secondary'}}>Talent Acquisition Intelligence & Analytics Platform</Typography>
            </Box>
          </Box>

          <Box sx={{display:'flex', alignItems:'center', gap:1}}>
            <Chip label={scope || 'All Scopes'} size="small" onClick={(e)=>{ setScopeAnchor(e.currentTarget);
              // lazy-load org units when opening the menu
              import('../api/client').then(m=>m.getOrgUnitsSummary()).then((d)=>{ setOrgs(d || null) }).catch(()=>{});
            }} sx={{mr:1}} />
            <Menu anchorEl={scopeAnchor} open={Boolean(scopeAnchor)} onClose={()=>setScopeAnchor(null)}>
              <MenuItem onClick={()=>{ setScope(null); setScopeAnchor(null) }}>All Scopes</MenuItem>
              <MenuItem onClick={()=>{ setScope('USAREC'); setScopeAnchor(null) }}>USAREC</MenuItem>
              {orgs && orgs.brigades && orgs.brigades.length ? [<Divider key="d1" sx={{ my: 0.5 }} />, <Typography key="h1" variant="caption" sx={{ px:1, color:'text.secondary' }}>Brigades</Typography>] : null}
              {orgs && orgs.brigades && orgs.brigades.map((b:any)=> (
                <MenuItem key={b.scope} onClick={()=>{ setScope(b.scope); setScopeAnchor(null) }}>{`Brigade: ${b.label || b.scope}`}</MenuItem>
              ))}
              {orgs && orgs.battalions && orgs.battalions.length ? [<Divider key="d2" sx={{ my: 0.5 }} />, <Typography key="h2" variant="caption" sx={{ px:1, color:'text.secondary' }}>Battalions</Typography>] : null}
              {orgs && orgs.battalions && orgs.battalions.map((b:any)=> (
                <MenuItem key={b.scope} onClick={()=>{ setScope(b.scope); setScopeAnchor(null) }}>{`Battalion: ${b.label || b.scope}`}</MenuItem>
              ))}
              {orgs && orgs.companies && orgs.companies.length ? [<Divider key="d3" sx={{ my: 0.5 }} />, <Typography key="h3" variant="caption" sx={{ px:1, color:'text.secondary' }}>Companies</Typography>] : null}
              {orgs && orgs.companies && orgs.companies.map((c:any)=> (
                <MenuItem key={c.scope} onClick={()=>{ setScope(c.scope); setScopeAnchor(null) }}>{`Company: ${c.label || c.scope}`}</MenuItem>
              ))}
              {orgs && orgs.stations && orgs.stations.length ? [<Divider key="d4" sx={{ my: 0.5 }} />, <Typography key="h4" variant="caption" sx={{ px:1, color:'text.secondary' }}>Stations</Typography>] : null}
              {orgs && orgs.stations && orgs.stations.map((s:any)=> (
                <MenuItem key={s.scope} onClick={()=>{ setScope(s.scope); setScopeAnchor(null) }}>{`Station: ${s.label || s.scope}`}</MenuItem>
              ))}
            </Menu>
            <Chip label={`API: ${status}`} size="small" color={status==='online'?'success':'default'} sx={{mr:1}} />
            <IconButton size="small" onClick={(e)=>setAnchor(e.currentTarget)} sx={{color:'text.primary'}}>
              <AccountCircleIcon />
            </IconButton>
            <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={()=>setAnchor(null)}>
              <MenuItem onClick={()=>setAnchor(null)}><LockIcon sx={{mr:1}} /> Roles</MenuItem>
              <MenuItem onClick={()=>setAnchor(null)}>Preferences</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
    </Box>
  )
}
