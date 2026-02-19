import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, List, ListItem, ListItemText } from '@mui/material'
import api from '../../api/client'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'

export default function ProjectsDashboardPage(){
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true; api.getProjectsDashboard().then(d=>{ if(mounted) setData(d) }).catch(()=>{}).finally(()=> mounted && setLoading(false)); return ()=>{ mounted=false } }, [])

  return (
    <Box sx={{ p:3 }}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <Typography variant="h5" sx={{ mb:2 }}>Projects Dashboard</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={data && data.recent ? data.recent : []} filename="projects_dashboard" />
        </Box>
      </Box>
      <DualModeTabs />
      <DashboardFilterBar />
      {loading ? <Typography>Loading...</Typography> : (
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Totals</Typography>
              <Typography variant="h6">{(data && data.totals) ? `${data.totals.count} projects` : '0 projects'}</Typography>
              <Typography variant="body2">Planned: ${(data && data.totals) ? data.totals.planned_cost : 0}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Recent Projects</Typography>
              <List>
                {(data && data.recent && data.recent.length) ? data.recent.map((r:any)=> <ListItem key={r.project_id}><ListItemText primary={r.title || r.project_id} secondary={`Planned: ${r.planned} • ${r.percent_complete}%`} /></ListItem>) : <ListItem><ListItemText primary="No projects" /></ListItem>}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}
