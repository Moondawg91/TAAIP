import React from 'react'
import {Box, Button, Divider, TextField, Typography, Switch, FormControlLabel} from '@mui/material'
import UnitCascadePicker from './UnitCascadePicker'
import { useFilters } from '../contexts/FilterContext'

const SCOPES = ['USAREC','BDE','BN','CO','STN']

export default function SidebarFilters({scope, value, onApply, onTokenSave, autoRefresh, setAutoRefresh, onRefresh, timeWindow, setTimeWindow}){
  const { filters, setUnit } = useFilters()
  const [localScope, setLocalScope] = React.useState(scope || 'USAREC')
  const [localValue, setLocalValue] = React.useState(value || (filters?.unit_rsid||''))
  const [token, setToken] = React.useState(localStorage.getItem('taaip_jwt') || '')

  function saveToken(){
    if(token) localStorage.setItem('taaip_jwt', token)
    else localStorage.removeItem('taaip_jwt')
    onTokenSave && onTokenSave(token)
  }

  return (
    <Box sx={{width:260, p:2}}>
      <Typography variant="h6">Command Center</Typography>
      <Typography variant="caption" color="text.secondary">Paste JWT Token</Typography>
      <Box sx={{display:'flex', gap:1, mt:1}}>
        <TextField size="small" fullWidth value={token} onChange={e=>setToken(e.target.value)} placeholder="Paste JWT token" />
        <Button variant="contained" onClick={saveToken}>Save</Button>
      </Box>

      <Divider sx={{my:2}} />

      <Typography variant="subtitle2">Echelon / Unit</Typography>
      <Box sx={{mt:1}}>
        <Typography variant="body2" color="text.secondary">Unit selection is handled in the Top filter bar on dashboard pages. Use the Top filter to change the active unit.</Typography>
      </Box>

      <Divider sx={{my:2}} />

      <Typography variant="subtitle2">Time Window</Typography>
      <Box sx={{display:'flex', gap:1, flexWrap:'wrap', mt:1}}>
        {['7','30','90','FYTD'].map(t=> (
          <Button key={t} size="small" variant={timeWindow===t? 'contained':'outlined'} onClick={()=>setTimeWindow(t)}>{t==='FYTD' ? 'FYTD' : `Last ${t}d`}</Button>
        ))}
      </Box>

      <Divider sx={{my:2}} />

      <FormControlLabel control={<Switch checked={autoRefresh} onChange={e=>setAutoRefresh(e.target.checked)} />} label="Auto-refresh (15s)" />
      <Box sx={{display:'flex', gap:1, mt:1}}>
        <Button variant="contained" onClick={onRefresh}>Refresh</Button>
      </Box>

      <Box sx={{mt:3}}>
        <Typography variant="caption" color="text.secondary">Notes</Typography>
        <Typography variant="body2" sx={{mt:1,color:'text.secondary'}}>This UI displays real data from the API. If no data is available for the selected echelon, a clear empty state will be shown. No demo data is created.</Typography>
      </Box>
    </Box>
  )
}
