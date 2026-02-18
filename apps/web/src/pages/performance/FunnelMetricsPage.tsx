import React, { useEffect, useState } from 'react'
import { Box, Typography, Card, CardContent, List, ListItem, ListItemText } from '@mui/material'
import { getFunnelStages, getFunnelEvents } from '../../api/client'

export default function FunnelMetricsPage(){
  const [stages, setStages] = useState([])
  const [events, setEvents] = useState([])

  useEffect(()=>{ load() }, [])
  async function load(){
    try{
      const s = await getFunnelStages()
      setStages(s || [])
      const e = await getFunnelEvents()
      setEvents(e || [])
    }catch(e){ console.error('load funnel', e) }
  }

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Typography variant="h5">Funnel Metrics</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Funnel performance and conversion metrics.</Typography>
      <Card sx={{ bgcolor:'background.paper', mb:2 }}>
        <CardContent>
          <Typography variant="h6">Stages</Typography>
          <List>
            {(stages || []).map((s:any)=> <ListItem key={s.id}><ListItemText primary={s.name} secondary={`rank ${s.rank || ''}`} /></ListItem>)}
          </List>
        </CardContent>
      </Card>
      <Card sx={{ bgcolor:'background.paper' }}>
        <CardContent>
          <Typography variant="h6">Recent Funnel Events ({(events||[]).length})</Typography>
          <List>
            {(events || []).slice(0,20).map((ev:any)=> <ListItem key={ev.id}><ListItemText primary={ev.name || ev.event_type} secondary={`${ev.start_dt || ''} • ${ev.location_city || ''}`} /></ListItem>)}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}
