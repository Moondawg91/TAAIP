import React, { useState, useEffect } from 'react'
import { AppBar, Toolbar, Typography, Box, Menu, MenuItem, IconButton, Divider, Tooltip } from '@mui/material'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import { alpha } from '@mui/material'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockIcon from '@mui/icons-material/Lock'
import { getMe } from '../api/client'

export default function TopHeader({ title }: { title?: string }){
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)
  const [isMaster, setIsMaster] = useState(false)
  const [blocked, setBlocked] = useState<string[]>([])

  useEffect(()=>{
    let canceled = false
    getMe().then(me => {
      if(canceled) return
      if(me && Array.isArray(me.permissions) && me.permissions.includes('*')) setIsMaster(true)
    }).catch(()=>{})

    // check readiness briefly to set header badge
    Promise.all([
      fetch('/api/market-intel/readiness').then(r=>r.json()).catch(()=>null),
      fetch('/api/phonetics/readiness').then(r=>r.json()).catch(()=>null),
      fetch('/api/system/status').then(r=>r.json()).catch(()=>null)
    ]).then(([mi, ph, sys])=>{
      if(canceled) return
      const bk = []
      if(mi && mi.blocking) bk.push(...mi.blocking)
      if(ph && ph.blocking) bk.push(...ph.blocking)
      if(sys && sys.blocking) bk.push(...sys.blocking)
      setBlocked(Array.from(new Set(bk)))
    }).catch(()=>{} )
    return ()=>{ canceled = true }
  },[])

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
            {isMaster && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (
              <Box sx={{ px:1, py:0.5, bgcolor: 'primary.main', color: 'primary.contrastText', borderRadius:1, mr:1, fontSize:'0.75rem' }}>MASTER MODE</Box>
            )}
            {blocked && blocked.length>0 ? (
              <Tooltip title={blocked.map(b=>b).join('\n')}>
                <Box sx={{ px:1, py:0.5, bgcolor: 'warning.main', color: 'warning.contrastText', borderRadius:1, mr:1, fontSize:'0.75rem' }}>Data not loaded</Box>
              </Tooltip>
            ) : (
              <Box sx={{ px:1, py:0.5, color:'text.secondary', borderRadius:1, mr:1, fontSize:'0.75rem' }}>Ready</Box>
            )}

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
