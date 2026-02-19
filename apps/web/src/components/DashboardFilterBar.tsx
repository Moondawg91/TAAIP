import React from 'react'
import { Box, Grid, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material'
import { useSearchParams } from 'react-router-dom'

const FY_OPTIONS = ['2023','2024','2025']
const QUARTERS = ['Q1','Q2','Q3','Q4']
const ORG_LEVELS = ['USAREC','BDE','BN','CO','Station']
const FUNDING = ['USAREC_BDE_FUNDS','BATTALION_FUNDS','LOCAL_AMP_LAMP','DIRECT_AMP_DAMP','DIRECT_FUNDS_LOCAL','ADVERTISING_FUNDS_NATIONAL']

export default function DashboardFilterBar(){
  const [searchParams, setSearchParams] = useSearchParams()
  const fy = searchParams.get('fy') || FY_OPTIONS[0]
  const q = searchParams.get('q') || ''
  const org = searchParams.get('org') || ORG_LEVELS[0]
  const unit = searchParams.get('unit') || ''
  const station = searchParams.get('station') || ''
  const funding = searchParams.get('funding') || ''

  function updateParam(k:string, v:string){
    const sp = new URLSearchParams(searchParams.toString())
    if(!v) sp.delete(k)
    else sp.set(k,v)
    setSearchParams(sp)
  }

  return (
    <Box sx={{mb:2}}>
      <Grid container spacing={2} alignItems="center">
        <Grid item>
          <FormControl size="small" sx={{minWidth:120}}>
            <InputLabel>FY</InputLabel>
            <Select value={fy} label="FY" onChange={(e)=>updateParam('fy', e.target.value)}>
              {FY_OPTIONS.map(x=> <MenuItem key={x} value={x}>{x}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item>
          <FormControl size="small" sx={{minWidth:100}}>
            <InputLabel>Quarter</InputLabel>
            <Select value={q} label="Quarter" onChange={(e)=>updateParam('q', e.target.value)}>
              <MenuItem value="">All</MenuItem>
              {QUARTERS.map(x=> <MenuItem key={x} value={x}>{x}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item>
          <FormControl size="small" sx={{minWidth:180}}>
            <InputLabel>Org Level</InputLabel>
            <Select value={org} label="Org Level" onChange={(e)=>updateParam('org', e.target.value)}>
              {ORG_LEVELS.map(x=> <MenuItem key={x} value={x}>{x}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item>
          <FormControl size="small" sx={{minWidth:140}}>
            <InputLabel>Funding</InputLabel>
            <Select value={funding} label="Funding" onChange={(e)=>updateParam('funding', e.target.value)}>
              <MenuItem value="">Any</MenuItem>
              {FUNDING.map(x=> <MenuItem key={x} value={x}>{x}</MenuItem>)}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs>
          <Box sx={{display:'flex', gap:1, justifyContent:'flex-end'}}>
            <Button size="small" onClick={()=>{ setSearchParams({}) }}>Clear</Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}
