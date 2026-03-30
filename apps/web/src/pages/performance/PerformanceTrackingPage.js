import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, List, ListItem, ListItemText } from '@mui/material'
import { getPerformanceDashboard } from '../../api/client'

export default function PerformanceTrackingPage(){
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(()=>{ let mounted = true
    async function load(){
      try{
        const res = await getPerformanceDashboard()
        if(mounted) setPayload(res)
      }catch(e){
        console.error('load performance dashboard', e)
        if(mounted) setPayload(null)
      }finally{ if(mounted) setLoading(false) }
    }
    load()
    return ()=>{ mounted = false }
  },[])

  const conversionTrend = payload && payload.conversion_trend ? payload.conversion_trend : []
  const stations = payload && payload.stations ? payload.stations : []
  const topMetrics = payload && payload.top_metrics ? payload.top_metrics : []
  const missing = payload && payload.missing_data ? payload.missing_data : []

  return (
    <Box sx={{ p:3, minHeight:'100vh' }}>
      <Typography variant="h4">Performance Tracking</Typography>
      <Typography sx={{ mt:1, color:'text.secondary' }}>Production, funnel, and station rollups from runtime aggregates.</Typography>

      { loading ? (
        <Typography variant="body2" sx={{ mt:2 }}>Loading performance data...</Typography>
      ) : ( ( (!conversionTrend || conversionTrend.length===0) && (!stations || stations.length===0) && (!topMetrics || topMetrics.length===0) ) ? (
        <Paper sx={{ p:2, mt:2 }}>
          <Typography variant="h6">No performance data</Typography>
          <Typography variant="body2" sx={{ color:'text.secondary' }}>Production/conversion/station rollups are not available for your selection. Ensure datasets are committed and post-commit processing has completed.</Typography>
          { missing && missing.length>0 ? <Typography variant="caption" sx={{ display:'block', mt:1 }}>Missing: {missing.join(', ')}</Typography> : null }
        </Paper>
      ) : (
        <Grid container spacing={2} sx={{ mt:2 }}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="h6">Top Metrics</Typography>
              <List dense>
                {topMetrics.slice(0,10).map((m,i)=>(<ListItem key={i}><ListItemText primary={`${m.metric_key} — ${m.total ?? m.metric_value ?? ''}`} /></ListItem>))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="h6">Conversion Trend</Typography>
              <List dense>
                {conversionTrend.slice(0,12).map((r,i)=>(<ListItem key={i}><ListItemText primary={`${r.period || r.date_key || i}: leads:${r.leads ?? ''}${typeof r.conversion_pct !== 'undefined' && r.conversion_pct !== null ? ` — ${r.conversion_pct}%` : ''}`} /></ListItem>))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p:2 }}>
              <Typography variant="h6">Top Stations</Typography>
              <List dense>
                {stations.slice(0,10).map((s,i)=>(<ListItem key={i}><ListItemText primary={`${s.name || s.station || s.org_id || s.org_unit_id || i} — leads:${s.leads ?? ''}${typeof s.conversion_pct !== 'undefined' && s.conversion_pct !== null ? ` — ${s.conversion_pct}%` : ''}`} /></ListItem>))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )) }
    </Box>
  )
}
