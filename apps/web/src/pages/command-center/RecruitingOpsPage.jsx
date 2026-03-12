import React from 'react'
import { Box, Typography, Grid, Paper, Button } from '@mui/material'

export default function RecruitingOps(){
  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Recruiting Ops</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>This is a scaffolded TOR page. Replace KPIs and drilldowns with real data and components.</Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric A</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric B</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">KPI: Metric C</Typography>
            <Typography variant="h5">—</Typography>
            <Typography variant="caption" sx={{ color:'text.secondary' }}>Placeholder value</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt:3 }}>
        <Typography variant="h6">Drilldowns</Typography>
        <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Add charts, tables, and filters here to explore data for this TOR.</Typography>
        <a href="/data-hub" style={{ fontSize:13 }}>Go to Data Hub</a>
      </Box>
    </Box>
  )
}
