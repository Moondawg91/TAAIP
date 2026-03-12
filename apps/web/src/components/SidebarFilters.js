import React from 'react'
import {Box, Button, Divider, TextField, Typography, Switch, FormControlLabel, FormControl, InputLabel, Select, MenuItem} from '@mui/material'
import UnitCascadePicker from './UnitCascadePicker'
import { useFilters } from '../contexts/FilterContext'
import dateScopes from '../utils/dateScopes'

export default function SidebarFilters({ scope, value, onApply, onTokenSave, autoRefresh, setAutoRefresh, onRefresh, timeWindow, setTimeWindow }){
  const { filters, setUnit, setFy, setQtr, setRsmMonth } = useFilters()
  const [token, setToken] = React.useState(localStorage.getItem('taaip_jwt') || '')

  React.useEffect(()=>{ try{ setToken(localStorage.getItem('taaip_jwt') || '') }catch(e){} }, [])

  function saveToken(){
    if(token) localStorage.setItem('taaip_jwt', token)
    else localStorage.removeItem('taaip_jwt')
    onTokenSave && onTokenSave(token)
  }

  const fyOptions = (()=>{ const y = dateScopes.getCurrentFY(); return [String(y-1), String(y), String(y+1)] })()
  const qOptions = ['Q1','Q2','Q3','Q4']
  const monthsForCurrent = (()=>{
    try{ const fy = Number(filters.fy) || dateScopes.getCurrentFY(); const qn = Number(String(filters.qtr || 'Q1').replace(/^Q/,'')); return dateScopes.getQuarterMonths(fy, qn) }catch(e){ return [dateScopes.getCurrentRsmMonth()] }
  })()

  return (
    <Box sx={{width:260, p:2}}>
      <Typography variant="h6">Filters</Typography>
      <Typography variant="caption" color="text.secondary">Global filters (applies across pages)</Typography>
      <Divider sx={{my:2}} />

      <Typography variant="subtitle2">Unit (read-only)</Typography>
      <Box sx={{mt:1, mb:1}}>
        <Typography variant="body2">Command: <strong>{filters.unit_rsid || 'USAREC'}</strong></Typography>
        <Typography variant="caption" color="text.secondary">Drilldown via Unit selector on dashboards.</Typography>
      </Box>

      <Divider sx={{my:2}} />

      <Typography variant="subtitle2">Time Window</Typography>
      <Box sx={{mt:1, display:'flex', gap:1, flexDirection:'column'}}>
        <FormControl size="small" fullWidth>
          <InputLabel>FY</InputLabel>
          <Select value={String(filters.fy || '')} label="FY" onChange={(e)=> setFy(Number(e.target.value))}>
            {fyOptions.map(f=> <MenuItem key={f} value={f}>{f}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl size="small" fullWidth sx={{mt:1}}>
          <InputLabel>Quarter</InputLabel>
          <Select value={String(filters.qtr || '')} label="Quarter" onChange={(e)=> setQtr(String(e.target.value))}>
            {qOptions.map(q=> <MenuItem key={q} value={q}>{q}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl size="small" fullWidth sx={{mt:1}}>
          <InputLabel>Month</InputLabel>
          <Select value={String(filters.rsm_month || '')} label="Month" onChange={(e)=> setRsmMonth(String(e.target.value))}>
            {monthsForCurrent.map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      <Divider sx={{my:2}} />

      <Box sx={{display:'flex', gap:1, mt:1}}>
        <Button variant="contained" onClick={onRefresh}>Refresh</Button>
      </Box>

      <Divider sx={{my:2}} />

      <Typography variant="caption" color="text.secondary">Developer Token</Typography>
      <Box sx={{display:'flex', gap:1, mt:1}}>
        <TextField size="small" fullWidth value={token} onChange={e=>setToken(e.target.value)} placeholder="Paste JWT token" />
        <Button variant="contained" onClick={saveToken}>Save</Button>
      </Box>
    </Box>
  )
}
