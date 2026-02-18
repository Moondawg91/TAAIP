import React, {useEffect, useState, useRef} from 'react'
import SidebarFilters from '../components/SidebarFilters'
import CoverageCharts from '../components/CoverageCharts'
import CoverageTable from '../components/CoverageTable'
import DashboardLayout from '../components/DashboardLayout'
import api from '../api/client'
import {Box, Typography, Container, Grid, Paper} from '@mui/material'

const POLL_INTERVAL_MS = 15000

export default function CommandCenterPage(){
  const [scope, setScope] = useState('USAREC')
  const [value, setValue] = useState('')
  const [timeWindow, setTimeWindow] = useState('30')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [status, setStatus] = useState('unknown')
  const [dataAsOf, setDataAsOf] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [commandSummary, setCommandSummary] = useState(null)
  const [coverageSummary, setCoverageSummary] = useState(null)
  const [marketPotential, setMarketPotential] = useState(null)
  const [kpis, setKpis] = useState([])
  const timerRef = useRef(null)

  async function refresh(now=true){
    try{ await api.getHealth(); setStatus('online') } catch(e){ setStatus('offline') }

    try{ const cs = await api.getCommandSummary(scope, value); setCommandSummary(cs); if(cs && cs.data_as_of) setDataAsOf(cs.data_as_of) }catch(e){ setCommandSummary(null) }
    try{ const cov = await api.getCoverageSummary(scope, value); setCoverageSummary(cov); if(cov && cov.data_as_of) setDataAsOf(cov.data_as_of) }catch(e){ setCoverageSummary(null) }
    try{ const mp = await api.getMarketPotential(scope, value); setMarketPotential(mp); if(mp && mp.data_as_of) setDataAsOf(mp.data_as_of) }catch(e){ setMarketPotential(null) }
    try{ const kp = await api.getKpis(scope); setKpis(kp || []) }catch(e){ setKpis([]) }
    setLastRefresh(new Date().toISOString())
    if(now) setLastRefresh(new Date().toISOString())
  }

  useEffect(()=>{
    refresh()
    if(autoRefresh){ timerRef.current = setInterval(()=>refresh(false), POLL_INTERVAL_MS) }
    return ()=> clearInterval(timerRef.current)
  }, [scope, value, autoRefresh])

  function handleApply(s,v){ setScope(s); setValue(v); refresh() }

  function handleDrilldown(payload){
    try{
      const dim = payload.dimension
      const val = payload.value
      const filters = payload.filtersToApply || {}
      if (filters.timeWindow) setTimeWindow(filters.timeWindow)
      if (dim && filters[dim] !== undefined){ setValue(filters[dim]); handleApply(scope, filters[dim]) }
      else if (val !== undefined){ setValue(val); handleApply(scope, val) }
    }catch(e){ console.warn('drilldown handler error', e) }
  }

  const counts = coverageSummary && coverageSummary.counts ? coverageSummary.counts : null
  const totalCoverage = counts ? (Object.values(counts as any).reduce((a: number, b: any) => a + (Number(b) || 0), 0)) : null
  const mk = counts && counts.MK !== undefined ? counts.MK : null
  const mw = counts && counts.MW !== undefined ? counts.MW : null
  const mpScore = marketPotential && marketPotential.score !== undefined ? marketPotential.score : null
  const burdenRatio = commandSummary && commandSummary.burden_ratio !== undefined ? commandSummary.burden_ratio : null
  const loeStatus = commandSummary && commandSummary.loe_summary ? commandSummary.loe_summary : null
  const rows = (coverageSummary && (coverageSummary.units || coverageSummary.sub_units)) || []

  const filters = (
    <SidebarFilters
      scope={scope}
      value={value}
      onApply={handleApply}
      onTokenSave={()=>{refresh()}}
      autoRefresh={autoRefresh}
      setAutoRefresh={setAutoRefresh}
      onRefresh={()=>refresh()}
      timeWindow={timeWindow}
      setTimeWindow={setTimeWindow}
    />
  )
  return (
    <DashboardLayout filters={filters}>
      <Container maxWidth={false} disableGutters>
        <Box sx={{display:'flex', justifyContent:'space-between', alignItems:'center', mb:2}}>
          <Typography variant="h5">Command Center</Typography>
          <Typography variant="body2" color="text.secondary">API: <strong>{status}</strong> • Data as of: {dataAsOf || 'N/A'} • Last refresh: {lastRefresh || 'N/A'}</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Paper sx={{p:2}}>
              <Typography variant="subtitle1" sx={{mb:1}}>Primary: Coverage Overview</Typography>
              <CoverageCharts counts={counts || {}} onDrilldown={handleDrilldown} />
            </Paper>
            <Paper sx={{p:2, mt:2}}>
              <Typography variant="subtitle1" sx={{mb:1}}>Coverage Table</Typography>
              <CoverageTable rows={rows} />
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{p:2}}>
              <Typography variant="subtitle1">Command Summary</Typography>
              {!commandSummary ? (
                status !== 'online' ? (
                  <Typography variant="body2" color="text.secondary">API offline.</Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">No summary available for this scope/time window.</Typography>
                )
              ) : (
                <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(commandSummary, null, 2)}</pre>
              )}
            </Paper>

            <Paper sx={{p:2, mt:2}}>
              <Typography variant="subtitle1">Market Potential</Typography>
              <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(marketPotential || {}, null, 2)}</pre>
            </Paper>
          </Grid>
        </Grid>

        <Box sx={{mt:2}}>
          <footer className="footer">© 2026 TAAIP. Copyright pending.</footer>
        </Box>
      </Container>
    </DashboardLayout>
  )
}
