import React, { useState, useEffect } from 'react'
import { Box, Typography, Grid, Button } from '@mui/material'
import FlashBureauPanel from '../components/home/FlashBureauPanel'
import MessagesPanel from '../components/home/MessagesPanel'
import RecognitionPanel from '../components/home/RecognitionPanel'
import UpcomingPanel from '../components/home/UpcomingPanel'
import ReferenceRailsPanel from '../components/home/ReferenceRailsPanel'
import { useOrgUnitStore } from '../state/orgUnitStore'
import VirtualTechnicianBrief from '../components/home/VirtualTechnicianBrief'
import api from '../api/client'
import DashboardCard from '../components/ui/DashboardCard'
import KpiTile from '../components/ui/KpiTile'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material'

export default function HomePage(){
  // Quick Actions + System Readiness on left; Strategic + Upcoming center; Reference + Data Status right
  const quickActions = [
    { label: '420T Command Center', href: '/command-center/420t' },
    { label: 'MDMP Workspace', href: '/command-center/mdmp' },
    { label: 'Market Intelligence', href: '/operations/market-intelligence' },
    { label: 'School Recruiting', href: '/school-recruiting/program' },
    { label: 'Data Hub', href: '/data-hub' }
  ]

  const store = useOrgUnitStore()
  const activeUnitKey = store.activeUnitKey
  const activeEchelon = store.activeEchelon
  const [drillUnit, setDrillUnit] = useState<{ unit_key: string; echelon: string } | null>(null)
  const [kpis, setKpis] = useState(null)
  const [trend, setTrend] = useState([])
  const [stations, setStations] = useState([])
  const [runs, setRuns] = useState([])

  useEffect(()=>{
    let mounted = true
    ;(async ()=>{
      try{
        const [summary, perf, datahubRuns] = await Promise.all([
          api.getAnalyticsSummary().catch(()=>null),
          api.getPerformanceDashboard().catch(()=>null),
          api.dataHubListRuns().catch(()=>[])
        ])
        if(!mounted) return
        setKpis(summary || null)
        if(perf && perf.stations) setStations(perf.stations)
        if(perf && perf.conversion_trend) setTrend(perf.conversion_trend)
        setRuns(Array.isArray(datahubRuns) ? datahubRuns : (datahubRuns && datahubRuns.items) ? datahubRuns.items : [])
      }catch(e){}
    })()
    return ()=>{ mounted = false }
  }, [])

  // Executive KPI row component
  function ExecutiveKpis(){
    const activeLeads = kpis && kpis.leads ? kpis.leads.active : null
    const contracts = kpis && kpis.contracts ? kpis.contracts.total : null
    const conv = (contracts != null && activeLeads != null && activeLeads>0) ? ((contracts/activeLeads)*100).toFixed(1) : null
    const freshnessTs = kpis && kpis.freshness ? kpis.freshness.last_updated : null
    const freshnessState = kpis && kpis.freshness ? kpis.freshness.state : null
    return (
      <DashboardCard>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}><KpiTile label="Active Leads" value={activeLeads != null ? activeLeads : 'Data unavailable'} sub={''} /></Grid>
          <Grid item xs={12} sm={6} md={3}><KpiTile label="Contracts" value={contracts != null ? contracts : 'Data unavailable'} sub={''} /></Grid>
          <Grid item xs={12} sm={6} md={3}><KpiTile label="Conversion Rate" value={conv != null ? `${conv}%` : 'Data unavailable'} sub={''} /></Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box>
              <Typography sx={{ fontSize: 12, fontWeight:700, color:'text.secondary', textTransform:'uppercase' }}>Data Freshness</Typography>
              <Typography sx={{ fontSize:20, fontWeight:800 }}>{freshnessState ? freshnessState : 'Unknown'}</Typography>
              <Typography sx={{ fontSize:12, color:'text.secondary' }}>{freshnessTs ? new Date(freshnessTs).toLocaleString() : 'No recent data'}</Typography>
            </Box>
          </Grid>
        </Grid>
      </DashboardCard>
    )
  }

  function ConversionTrendPanel(){
    return (
      <DashboardCard>
        <Typography variant="subtitle2">Conversion Trend</Typography>
        <Box sx={{ height:240 }}>
          {trend && trend.length>0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="conversion_pct" stroke="#1976d2" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <Typography>No trend data available</Typography>}
        </Box>
      </DashboardCard>
    )
  }

  function TopStationsPanel(){
    return (
      <DashboardCard>
        <Typography variant="subtitle2">Top Performing Stations</Typography>
        {stations && stations.length>0 ? (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Station</TableCell>
                <TableCell>Leads</TableCell>
                <TableCell>Contracts</TableCell>
                <TableCell>Conversion</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stations.map(s => (
                <TableRow key={s.station_rsid || s.station || s.id}>
                  <TableCell>{s.name || s.station_rsid || s.station}</TableCell>
                  <TableCell>{s.leads ?? '—'}</TableCell>
                  <TableCell>{s.contracts ?? '—'}</TableCell>
                  <TableCell>{s.conversion_pct != null ? `${s.conversion_pct}%` : '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : <Typography>No station performance data</Typography>}
      </DashboardCard>
    )
  }

  function DataFreshnessPanel(){
    const recent = (runs || []).filter(r => r.status && ['success','completed','committed','done','ok'].includes(String(r.status).toLowerCase())).slice(0,3)
    return (
      <DashboardCard>
        <Typography variant="subtitle2">Data Freshness & Recent Imports</Typography>
        {recent.length>0 ? (
          <Box>
            {recent.map(r => (
              <Box key={r.run_id} sx={{ my:1 }}>
                <Typography sx={{ fontSize:13 }}>{r.dataset_key} — {r.rows_loaded ?? r.rows_in ?? 0} rows — {r.ended_at || r.finished_at || r.created_at}</Typography>
              </Box>
            ))}
          </Box>
        ) : <Typography>No recent successful imports</Typography>}
      </DashboardCard>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary', p:3 }}>
      <Box sx={{ maxWidth: 1400, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb:2 }}>
          <Typography variant="h4">Home — 420T Command Decision Support Portal</Typography>
          <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Command decision support for 420T operations</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Grid container spacing={2}>
              <Grid item xs={12}><ExecutiveKpis /></Grid>
              <Grid item xs={12} md={6}><ConversionTrendPanel /></Grid>
              <Grid item xs={12} md={6}><TopStationsPanel /></Grid>
              <Grid item xs={12}><DataFreshnessPanel /></Grid>
            </Grid>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <Box sx={{ p:0 }}>
                <Box sx={{ mb:1 }}>
                  {quickActions.map(a => (<Button key={a.href} size="small" variant="outlined" href={a.href} sx={{ mr:1, mb:1 }}>{a.label}</Button>))}
                </Box>
                <Box sx={{ mt:1 }}>
                  <Typography variant="h6">Quick Actions</Typography>
                  <Box sx={{ mt:1 }}><Typography variant="body2" sx={{ color:'text.secondary' }}>Useful links and Data Hub access.</Typography></Box>
                </Box>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <FlashBureauPanel />
              <MessagesPanel />
              <RecognitionPanel />
            </Box>
          </Grid>

          <Grid item xs={12} md={3}>
            <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
              <UpcomingPanel />
              <ReferenceRailsPanel />
            </Box>
          </Grid>
        </Grid>
        {/* drill detail panel removed for new dashboard */}
      </Box>
    </Box>
  )
}
