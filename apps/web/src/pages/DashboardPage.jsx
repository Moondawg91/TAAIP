import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Paper, List, ListItem, ListItemText } from '@mui/material'
import { getAnalyticsSummary, getKpis, getPerformanceDashboard, dataHubListRuns } from '../api/client'

export default function DashboardPage(){
  const [summary, setSummary] = useState(null)
  const [kpis, setKpis] = useState([])
  const [perf, setPerf] = useState(null)
  const [freshness, setFreshness] = useState(null)

  useEffect(()=>{
    let mounted = true
    async function load(){
      try{
        const [s, p, d] = await Promise.all([
          getAnalyticsSummary().catch(()=>null),
          getPerformanceDashboard().catch(()=>null),
          getKpis().catch(()=>[])
        ])
        if(!mounted) return
        setSummary(s)
        setPerf(p)
        setKpis(Array.isArray(d) ? d : [])

        // freshness: check latest relevant runs
        try{
          const runs = await dataHubListRuns()
          if(!mounted) return
          const watched = new Set(['school_program_fact','leads','market_intel','mission_allocation','event_roi'])
          let latest = null
          (runs || []).forEach(r => {
            try{
              const dk = r.dataset_key || r.detected_dataset_key || r.dataset
              if(!dk) return
              if(!watched.has(dk)) return
              const ts = new Date(r.ended_at || r.updated_at || r.created_at || 0).getTime() || 0
              if(!latest || ts > latest.ts) latest = { run: r, ts }
            }catch(e){}
          })
          setFreshness(latest && latest.run ? latest.run : null)
        }catch(e){ setFreshness(null) }
      }catch(e){
        // noop
      }
    }
    load()
    return ()=>{ mounted = false }
  },[])

  const kpiItems = [
    { label: 'Active leads', value: (summary && summary.leads && summary.leads.active) || (kpis && kpis.leads_active) || '—' },
    { label: 'Contracts', value: (summary && summary.contracts && summary.contracts.total) || (kpis && kpis.contracts_total) || '—' },
    { label: 'Conversion %', value: (summary && summary.conversion && summary.conversion.pct != null) ? `${(summary.conversion.pct*100).toFixed(1)}%` : (kpis && kpis.conversion_pct) || '—' }
  ]

  const conversionTrend = (perf && perf.conversion_trend) || (summary && summary.trend) || null
  const topStations = (perf && perf.top_stations) || (summary && summary.top_stations) || []

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Dashboard</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Operational dashboard showing KPIs, conversion trend, top stations and data freshness. Data sourced from runtime aggregates produced by Data Hub post-commit orchestration.</Typography>

      <Grid container spacing={2}>
        {kpiItems.map((k, idx) => (
          <Grid item xs={12} md={4} key={idx}>
            <Paper sx={{ p:2 }}>
              <Typography variant="subtitle2">{k.label}</Typography>
              <Typography variant="h5">{k.value}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2} sx={{ mt:2 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Conversion Trend</Typography>
            {conversionTrend && Array.isArray(conversionTrend) ? (
              <List dense>
                {conversionTrend.slice(0,12).map((row, i) => (
                  <ListItem key={i}><ListItemText primary={`${row.period || row.label || i}: ${typeof row.value !== 'undefined' ? row.value : JSON.stringify(row)}`} /></ListItem>
                ))}
              </List>
            ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No trend data available</Typography>}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Top Stations</Typography>
            {topStations && topStations.length>0 ? (
              <List dense>
                {topStations.slice(0,10).map((s,i) => (<ListItem key={i}><ListItemText primary={`${s.station || s.unit_rsid || s.name || s[0] || 'unknown'} — ${s.metric || s.leads || s.value || ''}`} /></ListItem>))}
              </List>
            ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No station data available</Typography>}
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt:2 }}>
        <Paper sx={{ p:2 }}>
          <Typography variant="subtitle2">Data Freshness</Typography>
          {freshness ? (
            <div>
              <div><strong>Dataset:</strong> {freshness.dataset_key || freshness.dataset || 'unknown'}</div>
              <div><strong>Run ID:</strong> {freshness.run_id || freshness.id}</div>
              <div><strong>Completed:</strong> {freshness.ended_at || freshness.updated_at || freshness.created_at || 'unknown'}</div>
            </div>
          ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No recent runs found for monitored datasets</Typography>}
        </Paper>
      </Box>
    </Box>
  )
}
