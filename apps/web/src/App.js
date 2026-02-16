import React, {useEffect, useState, useRef} from 'react'
import './index.css'
import SidebarFilters from './components/SidebarFilters'
import KpiTile from './components/KpiTile'
import CoverageCharts from './components/CoverageCharts'
import CoverageTable from './components/CoverageTable'
import api from './api/client'
import {Box, Grid, Typography, Container} from '@mui/material'

const POLL_INTERVAL_MS = 15000

export default function App(){
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
  const timerRef = useRef(null)

  async function refresh(now=true){
    try{ await api.getHealth(); setStatus('online') } catch(e){ setStatus('offline') }

    try{
      const cs = await api.getCommandSummary(scope, value)
      setCommandSummary(cs)
      if(cs && cs.data_as_of) setDataAsOf(cs.data_as_of)
    }catch(e){ setCommandSummary(null) }

    try{
      const cov = await api.getCoverageSummary(scope, value)
      setCoverageSummary(cov)
      if(cov && cov.data_as_of) setDataAsOf(cov.data_as_of)
    }catch(e){ setCoverageSummary(null) }

    try{
      const mp = await api.getMarketPotential(scope, value)
      setMarketPotential(mp)
      if(mp && mp.data_as_of) setDataAsOf(mp.data_as_of)
    }catch(e){ setMarketPotential(null) }

    setLastRefresh(new Date().toISOString())
    if(now) setLastRefresh(new Date().toISOString())
  }

  useEffect(()=>{
    refresh()
    if(autoRefresh){
      timerRef.current = setInterval(()=>refresh(false), POLL_INTERVAL_MS)
    }
    return ()=> clearInterval(timerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope, value, autoRefresh])

  function handleApply(s,v){ setScope(s); setValue(v); refresh() }

  // derive KPI values from coverageSummary / marketPotential
  const counts = coverageSummary && coverageSummary.counts ? coverageSummary.counts : null
  const totalCoverage = counts ? Object.values(counts).reduce((a,b)=>a+(b||0),0) : null
  const mk = counts && counts.MK !== undefined ? counts.MK : null
  const mw = counts && counts.MW !== undefined ? counts.MW : null
  const mpScore = marketPotential && marketPotential.score !== undefined ? marketPotential.score : null
  const burdenRatio = commandSummary && commandSummary.burden_ratio !== undefined ? commandSummary.burden_ratio : null
  const loeStatus = commandSummary && commandSummary.loe_summary ? commandSummary.loe_summary : null

  // table rows: coverageSummary.units or coverageSummary.sub_units
  const rows = (coverageSummary && (coverageSummary.units || coverageSummary.sub_units)) || []

  return (
    <div className="app-shell">
      <div className="left-pane">
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
      </div>

      <div className="main-pane">
        <Container maxWidth={false} disableGutters>
          <Box sx={{display:'flex', justifyContent:'space-between', alignItems:'center', mb:2}}>
            <Typography variant="h5">Command Center</Typography>
            <Typography variant="body2" color="text.secondary">API: <strong>{status}</strong> • Data as of: {dataAsOf || 'N/A'} • Last refresh: {lastRefresh || 'N/A'}</Typography>
          </Box>

          <div className="kpi-row">
            <KpiTile title="Total ZIP Coverage" value={totalCoverage} />
            <KpiTile title="MK" value={mk} />
            <KpiTile title="MW" value={mw} />
            <KpiTile title="Market Potential" value={mpScore} />
            <KpiTile title="Burden Ratio" value={burdenRatio !== undefined ? burdenRatio : 'N/A'} />
            <KpiTile title="LOE Status" value={loeStatus ? (loeStatus.met || 'N/A') : 'N/A'} />
          </div>

          <div className="charts-row">
            <div>
              <CoverageCharts counts={counts || {}} />
            </div>
            <div>
              {/* Right-side compact card: quick command summary */}
              <Box sx={{mb:2}}>
                <Box sx={{p:2, border:'1px solid #e6e9ef', borderRadius:1, background:'#fff'}}>
                  <Typography variant="subtitle1">Command Summary</Typography>
                  {!commandSummary ? (
                    <Typography variant="body2" color="text.secondary">No domain facts loaded. Ingest your real USAREC exports using Universal Ingest.</Typography>
                  ) : (
                    <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(commandSummary, null, 2)}</pre>
                  )}
                </Box>
              </Box>
            </div>
          </div>

          <div className="table-row">
            <CoverageTable rows={rows} />
          </div>

          <footer className="footer">© 2025 Maroon Moon, LLC. All rights reserved.</footer>
        </Container>
      </div>
    </div>
  )
}
