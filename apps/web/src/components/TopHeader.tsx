import React, { useState, useEffect } from 'react'
import { AppBar, Toolbar, Typography, Box, Menu, MenuItem, IconButton, Divider, Tooltip } from '@mui/material'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import { alpha } from '@mui/material'
import AccountCircleIcon from '@mui/icons-material/AccountCircle'
import LockIcon from '@mui/icons-material/Lock'
import { getMe, getMarketIntelReadiness, getPhoneticsReadiness, getSystemStatus } from '../api/client'
import AddIcon from '@mui/icons-material/Add'
import { useAuth } from '../contexts/AuthContext'
import { useLocation, useNavigate } from 'react-router-dom'
import ExportButton from './ExportButton'

export default function TopHeader({ title }: { title?: string }){
  const [anchor, setAnchor] = useState<null | HTMLElement>(null)
  const [isMaster, setIsMaster] = useState(false)
  const [blocked, setBlocked] = useState<string[]>([])
  const { roles, loading } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const p = location && location.pathname ? location.pathname : ''
  const dashboardPrefixes = [
    '/', '/dash', '/dashboards', '/command-center', '/qbr', '/market-intel', '/operations', '/ops', '/planning', '/roi', '/school', '/schools', '/budget'
  ]
  const showExport = dashboardPrefixes.some(pref => pref === '/' ? p === '/' : p.startsWith(pref))
  const showCascade = showExport

  useEffect(()=>{
    let canceled = false
    getMe().then(me => {
      if(canceled) return
      if(me && Array.isArray(me.permissions) && me.permissions.includes('*')) setIsMaster(true)
    }).catch(()=>{})

    // check readiness briefly to set header badge
    Promise.all([
      getMarketIntelReadiness().catch(()=>null),
      getPhoneticsReadiness().catch(()=>null),
      getSystemStatus().catch(()=>null)
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
            {showExport && <ExportButton />}
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

            {/* Admin-only subtle New Post action (top-right) */}
            {(!loading && roles && roles.some(r=>['system_admin','usarec_admin','sysadmin','admin','420t_admin'].includes(r)) && location.pathname.startsWith('/admin')) && (
              <IconButton size="small" color="primary" onClick={()=>navigate('/admin?new=1')} sx={{ mr:1 }} title="New Post">
                <AddIcon />
              </IconButton>
            )}
            <IconButton size="small" onClick={(e)=>setAnchor(e.currentTarget)} sx={{color:'text.primary'}}>
              <AccountCircleIcon />
            </IconButton>
            <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={()=>setAnchor(null)}>
              <MenuItem onClick={()=>setAnchor(null)}>Roles</MenuItem>
              <MenuItem onClick={()=>setAnchor(null)}>Preferences</MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
      {/* Top filter bar removed from header; filter bar moved into layout for dashboards */}
    </Box>
  )
}
