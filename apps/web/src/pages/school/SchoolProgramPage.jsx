import React, { useEffect, useState } from 'react'
import { Box, Typography, Button, Grid, Paper, List, ListItem, ListItemText } from '@mui/material'
import { exportToCsv } from '../../utils/exportCsv'
import { getSchoolProgramSummary } from '../../api/client'

export default function SchoolProgramPage(){
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    let mounted = true
    getSchoolProgramSummary().then(r=>{ if(mounted) setSummary(r) }).catch(()=>{ if(mounted) setSummary(null) }).finally(()=>{ if(mounted) setLoading(false) })
    return ()=>{ mounted = false }
  },[])

  const handleExport = ()=>{
    const cols = ['section','note']
    const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')
    exportToCsv(`program_${ts}.csv`, [], cols)
  }

  return (
    <Box sx={{ p:2 }}>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4">School Recruiting — Program</Typography>
          <Typography variant="subtitle2" sx={{ color:'text.secondary', mb:1 }}>Coverage, Engagement, Attribution, and CEP</Typography>
        </Box>
        <Button variant="outlined" size="small" onClick={handleExport}>Export CSV</Button>
      </Box>

      { loading ? (
        <Typography variant="body2" sx={{ color:'text.secondary', mt:2 }}>Loading program summary...</Typography>
      ) : (!summary || summary.status === 'partial' || (summary.missing_data && summary.missing_data.length>0)) ? (
        <Paper sx={{ p:2, mt:2 }}>
          <Typography variant="h6">Program data not available</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Required dataset `school_program_fact` is not loaded or incomplete. Import school/program datasets via Data Hub to populate this view.</Typography>
        </Paper>
      ) : (
        <Grid container spacing={2} sx={{ mt:2 }}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Population</Typography>
              <Typography variant="h6">{summary.kpis.population_total ?? '—'}</Typography>
              <Typography variant="caption">Available: {summary.kpis.available_total ?? '—'}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Attempted</Typography>
              <Typography variant="h6">{summary.kpis.attempted_total ?? '—'}</Typography>
              <Typography variant="caption">Rate: {typeof summary.kpis.attempted_rate === 'number' ? (summary.kpis.attempted_rate*100).toFixed(1)+'%' : '—'}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">Contacted</Typography>
              <Typography variant="h6">{summary.kpis.contacted_total ?? '—'}</Typography>
              <Typography variant="caption">Rate: {typeof summary.kpis.contacted_rate === 'number' ? (summary.kpis.contacted_rate*100).toFixed(1)+'%' : '—'}</Typography>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p:2 }}>
              <Typography variant="h6">Breakdown by BDE</Typography>
              { summary.breakdowns && summary.breakdowns.by_bde && summary.breakdowns.by_bde.length>0 ? (
                <List dense>
                  {summary.breakdowns.by_bde.map((b,i)=>(<ListItem key={i}><ListItemText primary={`${b.bde} — pop:${b.population} contacted:${b.contacted}`} /></ListItem>))}
                </List>
              ) : (
                <Typography variant="body2" sx={{ color:'text.secondary' }}>No breakdown data available</Typography>
              ) }
            </Paper>
          </Grid>
        </Grid>
      ) }
    </Box>
  )
}
