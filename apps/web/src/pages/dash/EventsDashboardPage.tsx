import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, List, ListItem, ListItemText } from '@mui/material'
import DrillBreadcrumbs from '../../components/DrillBreadcrumbs'
import DetailDrawer from '../../components/DetailDrawer'
import api from '../../api/client'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'

export default function EventsDashboardPage(){
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerData, setDrawerData] = useState<any>(null)
  const [trail, setTrail] = useState<any[]>([])

  useEffect(()=>{ let mounted = true; api.getEventsDashboard().then(d=>{ if(mounted) setData(d) }).catch(()=>{}).finally(()=> mounted && setLoading(false)); return ()=>{ mounted=false } }, [])

  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <Typography variant="h5" sx={{ mb:2 }}>Events Dashboard</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={data && data.recent ? data.recent : []} filename="events_dashboard" />
        </Box>
      </Box>
      <DualModeTabs />
      <DashboardFilterBar />
      {loading ? <Typography>Loading...</Typography> : (
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Totals</Typography>
              <Typography variant="h6">{(data && data.totals) ? `${data.totals.count} events` : '0 events'}</Typography>
              <Typography variant="body2">Planned: ${(data && data.totals) ? data.totals.planned_cost : 0}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Recent Events</Typography>
              <List>
                {(data && data.recent && data.recent.length) ? data.recent.map((r:any)=> (
                  <ListItem key={r.event_id} button onClick={()=>{ setDrawerOpen(true); setDrawerData(r); setTrail([{label:'USAREC'},{label: r.name || r.event_id}]) }}>
                    <ListItemText primary={r.name || r.event_id} secondary={`${r.event_type || ''} • Planned: ${r.planned}`} />
                  </ListItem>
                )) : <ListItem><ListItemText primary="No events" /></ListItem>}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
      <DetailDrawer open={drawerOpen} onClose={()=>setDrawerOpen(false)} title={drawerData?.name || drawerData?.event_id}>
        <DrillBreadcrumbs trail={trail || [{label:'USAREC'},{label: drawerData?.name || drawerData?.event_id}]} />
        <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(drawerData, null, 2)}</pre>
      </DetailDrawer>
    </Box>
  )
}
