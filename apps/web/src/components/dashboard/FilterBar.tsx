import React from 'react'
import { Box, FormControl, InputLabel, Select, MenuItem } from '@mui/material'

type Filters = { fy?: number | string, qtr?: string, org?: string, station?: string }

export default function FilterBar({ filters, onChange }:{ filters?: Filters, onChange:(f:Filters)=>void }){
  const nowFy = new Date().getFullYear()
  const handle = (k:keyof Filters, v:any)=>{ onChange(Object.assign({}, filters || {}, { [k]: v })) }

  const ORGS = [{ id: 'USAREC', label: 'USAREC' }, { id: 'BDE', label: 'Brigade' }]
  const STATIONS = [{ id: 'STN1', label: 'Station 1' }, { id: 'STN2', label: 'Station 2' }]

  return (
    <Box sx={{ display:'flex', gap:1, alignItems:'center', mx:2 }}>
      <FormControl size="small" sx={{ minWidth:100 }}>
        <InputLabel>FY</InputLabel>
        <Select value={filters?.fy ?? nowFy} label="FY" onChange={(e)=>handle('fy', Number(e.target.value))}>
          <MenuItem value={nowFy}>{`FY${String(nowFy).slice(2)}`}</MenuItem>
          <MenuItem value={nowFy-1}>{`FY${String(nowFy-1).slice(2)}`}</MenuItem>
          <MenuItem value={nowFy-2}>{`FY${String(nowFy-2).slice(2)}`}</MenuItem>
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:90 }}>
        <InputLabel>QTR</InputLabel>
        <Select value={filters?.qtr ?? 'Q1'} label="QTR" onChange={(e)=>handle('qtr', e.target.value)}>
          <MenuItem value={'Q1'}>Q1</MenuItem>
          <MenuItem value={'Q2'}>Q2</MenuItem>
          <MenuItem value={'Q3'}>Q3</MenuItem>
          <MenuItem value={'Q4'}>Q4</MenuItem>
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:160 }}>
        <InputLabel>Org Unit</InputLabel>
        <Select value={filters?.org ?? ''} label="Org Unit" onChange={(e)=>handle('org', e.target.value)}>
          <MenuItem value={''}>All</MenuItem>
          {ORGS.map(o=> <MenuItem key={o.id} value={o.id}>{o.label}</MenuItem>)}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth:160 }}>
        <InputLabel>Station</InputLabel>
        <Select value={filters?.station ?? ''} label="Station" onChange={(e)=>handle('station', e.target.value)}>
          <MenuItem value={''}>All</MenuItem>
          {STATIONS.map(s=> <MenuItem key={s.id} value={s.id}>{s.label}</MenuItem>)}
        </Select>
      </FormControl>
    </Box>
  )
}
