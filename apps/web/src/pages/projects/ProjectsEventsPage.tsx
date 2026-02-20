import React from 'react'
import { Box, Typography, Grid, Button } from '@mui/material'
import EmptyState from '../../components/common/EmptyState'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'
import api from '../../api/client'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'

export default function ProjectsEventsPage(){
  const [loading, setLoading] = React.useState(true)
  const [projects, setProjects] = React.useState<any[]>([])
  const [events, setEvents] = React.useState<any[]>([])

  React.useEffect(()=>{ let mounted = true; setLoading(true); Promise.all([api.getProjectsDashboard({}), api.getEventsDashboard({})]).then(([p,e])=>{ if(!mounted) return; setProjects(p && p.projects ? p.projects : []); setEvents(e && e.events ? e.events : []); }).catch(()=>{ if(mounted){ setProjects([]); setEvents([]) }}).finally(()=> mounted && setLoading(false)); return ()=>{ mounted=false }
  }, [])

  return (
    <Box sx={{ p:3, minHeight:'100vh', bgcolor:'background.default', color:'text.primary' }}>
      <Box sx={{display:'flex', alignItems:'center'}}>
        <Typography variant="h5">Projects & Events</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[...projects, ...events]} filename="projects_events" />
        </Box>
      </Box>
      <DualModeTabs />
      <DashboardFilterBar />
      <DashboardToolbar title="Event + Project Management" subtitle="Projects & events" filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
      {loading ? <Typography>Loading...</Typography> : (
        (projects.length || events.length) ? (
          <Grid container spacing={2} sx={{ mt:2 }}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6">Projects</Typography>
              {projects.length ? projects.slice(0,20).map(p=> (
                <Box key={p.project_id || p.id} sx={{ p:1, bgcolor:'#0B0B10', mb:1 }}>{p.title || p.project_id} — Planned: {p.planned_cost}</Box>
              )) : <EmptyState title="No projects" subtitle="No projects imported for your echelon." actionLabel="Go to Import Center" onAction={()=>{ window.location.href='/import-center' }} />}
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6">Events</Typography>
              {events.length ? events.slice(0,20).map(ev=> (
                <Box key={ev.event_id || ev.id} sx={{ p:1, bgcolor:'#0B0B10', mb:1 }}>{ev.name || ev.event_id} — Planned: {ev.planned_cost}</Box>
              )) : <EmptyState title="No events" subtitle="No events imported for your echelon." actionLabel="Go to Import Center" onAction={()=>{ window.location.href='/import-center' }} />}
            </Grid>
          </Grid>
        ) : <EmptyState title="No data yet" subtitle="No projects or events found. Import templates to get started." actionLabel="Go to Import Center" onAction={()=>{ window.location.href='/import-center' }} />
      )}
    </Box>
  )
}
