import React, { useEffect, useState } from 'react'
import { AppBar, Toolbar, Typography, Box, Chip, Menu, MenuItem, IconButton } from '@mui/material'
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
            <Chip label={scope || 'All Scopes'} size="small" onClick={(e)=>setScopeAnchor(e.currentTarget)} sx={{mr:1}} />
            <Menu anchorEl={scopeAnchor} open={Boolean(scopeAnchor)} onClose={()=>setScopeAnchor(null)}>
              <MenuItem onClick={()=>{ setScope(null); setScopeAnchor(null) }}>All</MenuItem>
              <MenuItem onClick={()=>{ setScope('USAREC'); setScopeAnchor(null) }}>USAREC</MenuItem>
              <MenuItem onClick={()=>{ setScope('STATION_001'); setScopeAnchor(null) }}>Station: STATION_001</MenuItem>
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
