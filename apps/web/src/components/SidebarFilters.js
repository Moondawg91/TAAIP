import React from 'react'
import {Box, Button, Divider, FormControl, InputLabel, MenuItem, Select, TextField, Typography, Switch, FormControlLabel} from '@mui/material'

const SCOPES = ['USAREC','BDE','BN','CO','STN']

export default function SidebarFilters({scope, value, onApply, onTokenSave, autoRefresh, setAutoRefresh, onRefresh, timeWindow, setTimeWindow}){
  const [localScope, setLocalScope] = React.useState(scope || 'USAREC')
  const [localValue, setLocalValue] = React.useState(value || '')
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

      <Typography variant="subtitle2">Echelon</Typography>
      <FormControl fullWidth size="small" sx={{mt:1}}>
        <InputLabel>Echelon</InputLabel>
        <Select value={localScope} label="Echelon" onChange={e=>setLocalScope(e.target.value)}>
          {SCOPES.map(s=> <MenuItem key={s} value={s}>{s}</MenuItem>)}
        </Select>
      </FormControl>
      <TextField size="small" fullWidth sx={{mt:1}} placeholder="Unit (prefix or RSID)" value={localValue} onChange={e=>setLocalValue(e.target.value)} />
      <Box sx={{display:'flex', gap:1, mt:1}}>
        <Button variant="outlined" onClick={()=>{ setLocalScope(scope); setLocalValue(value); onApply && onApply(scope, value); }}>Reset</Button>
        <Button variant="contained" onClick={()=>onApply && onApply(localScope, localValue)}>Apply</Button>
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
