import React, {useEffect, useState, useRef} from 'react'
import {Box, Chip, Typography, Button, Badge} from '@mui/material'
import {useTheme} from '@mui/material/styles'
import {getSystemFreshness, getSystemAlerts, getSystemStatus} from '../api/client'
import {useNavigate} from 'react-router-dom'

export default function SystemStrip(){
  const theme = useTheme()
  const nav = useNavigate()
  const [fresh, setFresh] = useState(null)
  const [alerts, setAlerts] = useState({alerts:{import_errors:0,api_errors:0,proposals_pending:0}, total:0})
  const [status, setStatus] = useState({mode: 'normal'})
  const timer = useRef(null)
  const lastFetched = useRef(0)
  const [fetchFailed, setFetchFailed] = useState(false)

  async function load(){
    try{
      const now = Date.now()
      if (now - lastFetched.current < 60000) return
      lastFetched.current = now
      setFetchFailed(false)
      const [f,a,s] = await Promise.all([getSystemFreshness(), getSystemAlerts(), getSystemStatus()])
      setFresh(f)
      setAlerts(a)
      setStatus(s)
    }catch(e){
      setFetchFailed(true)
    }
  }

  useEffect(()=>{
    load()
    timer.current = setInterval(load, 60000)
    return ()=> clearInterval(timer.current)
  },[])

  const bg = theme.palette.mode === 'dark' ? (theme.palette.background.paper || '#111') : '#0f1720'
  const textColor = theme.palette.text.primary || '#fff'

  const rawMode = (status && status.mode) || 'normal'
  // determine effective mode per spec
  let modeLabel = rawMode
  try{
    if (rawMode === 'maintenance') modeLabel = 'maintenance'
    else if (fetchFailed) modeLabel = 'degraded'
    else if (alerts && alerts.alerts && alerts.alerts.api_errors > 0) modeLabel = 'degraded'
    else if (fresh && fresh.data_as_of){
      const then = new Date(fresh.data_as_of)
      const ageDays = (Date.now() - then.getTime()) / (1000*60*60*24)
      if (ageDays > 7) modeLabel = 'degraded'
    }
  }catch(e){ modeLabel = 'degraded' }
  const proposalsPending = (alerts && alerts.alerts && alerts.alerts.proposals_pending) || 0
  const totalAlerts = alerts && alerts.total ? alerts.total : 0

  return (
    <Box sx={{height:44, display:'flex', alignItems:'center', px:2, gap:2, backgroundColor:bg, color:textColor, borderRadius:'4px'}}>
      <Chip size="small" label={modeLabel.charAt(0).toUpperCase()+modeLabel.slice(1)} sx={{borderRadius:'4px', bgcolor: modeLabel==='maintenance'? 'error.main' : (modeLabel==='degraded'? 'warning.main' : 'success.main'), color:'white'}} />
      <Typography variant="body2" sx={{flex:1, color:'text.secondary'}}>
        {fresh && fresh.data_as_of ? `Data as of ${fresh.data_as_of}` : 'Data not loaded'}
      </Typography>
      <Badge badgeContent={totalAlerts} color="error">
        <Button variant="outlined" size="small" onClick={()=>nav('/system/alerts')} sx={{borderRadius:'4px', color:textColor, borderColor:'rgba(255,255,255,0.08)'}}>Alerts</Button>
      </Badge>
      {proposalsPending>0 && (
        <Button variant="contained" size="small" onClick={()=>nav('/system/proposals')} sx={{ml:1, borderRadius:'4px'}}>
          Updates Ready ({proposalsPending})
        </Button>
      )}
      <Box sx={{ml:2, display:'flex', gap:1}}>
        <Button size="small" onClick={()=>nav('/system/status')} sx={{borderRadius:'4px', color:textColor}}>Status</Button>
        <Button size="small" onClick={()=>nav('/helpdesk')} sx={{borderRadius:'4px', color:textColor}}>Help Desk</Button>
      </Box>
    </Box>
  )
}
