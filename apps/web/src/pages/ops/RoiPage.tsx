import React, { useEffect, useState } from 'react'
import { Box, Typography, Chip, Button, Menu, MenuItem } from '@mui/material'
import { getMissionAssessment, exportDashboard } from '../../api/client'
import { useLocation } from 'react-router-dom'
import { TextField, FormControl, InputLabel, Select } from '@mui/material'

export default function OpsRoiPage(){
  const [summary, setSummary] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [events, setEvents] = useState([])
  const [filters, setFilters] = useState({ fy:'', qtr:'', echelon_type:'', unit_value:'', funding_line:'' })

  useEffect(()=>{
    let mounted = true
    getMissionAssessment().then(d=>{ if(mounted) setSummary(d) }).catch(()=>{})
    // if event_id provided, fetch events and expose selected event
    const params = new URLSearchParams(location.search)
    const eventId = params.get('event_id')
    if (eventId){
      exportDashboard('events-roi','json',{ event_id: eventId }).then(data=>{ if(mounted) setEvents(data || []) }).catch(()=>{})
    }
    const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
    if (eventId) qs.event_id = eventId
    getMissionAssessment(qs).then(d=>{ if(mounted) setSummary(d) }).catch(()=>{})
    if (eventId){
      exportDashboard('events-roi','json', qs).then(data=>{ if(mounted) setEvents(data || []) }).catch(()=>{})
    }
    return ()=>{ mounted = false }
  },[])

  function handleExportClick(e){ setAnchorEl(e.currentTarget) }
  function handleExportClose(){ setAnchorEl(null) }

  async function doExport(type, format){
    handleExportClose()
    try{
      const text = await exportDashboard(type, format)
      const filename = `${type}.${format === 'csv' ? 'csv' : 'json'}`
      const blob = new Blob([text], { type: format === 'csv' ? 'text/csv' : 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }catch(e){ console.error('export failed', e) }
  }

  return (
    <Box>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <Typography variant="h4">Event ROI / Analytics</Typography>
        <Box>
          <Button variant="contained" color="primary" onClick={handleExportClick}>Export</Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleExportClose}>
            <MenuItem onClick={()=>doExport('events-roi','csv')}>Events ROI — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('events-roi','json')}>Events ROI — JSON</MenuItem>
            <MenuItem onClick={()=>doExport('marketing','csv')}>Marketing — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('funnel','csv')}>Funnel — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('budget','csv')}>Budget — CSV</MenuItem>
          </Menu>
        </Box>
      </Box>

      <Box sx={{ mt:2 }}>
        {summary ? (
          <Box>
            <Typography variant="subtitle1">Tactical rollup</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary.tactical_rollup || summary, null, 2)}</pre>
          </Box>
        ) : (
          <Chip label="Loading rollup..." sx={{ mt:2 }} />
        )}

        {events && events.length > 0 && (
          <Box sx={{ mt:3 }}>
            <Typography variant="h6">Selected event</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(events[0], null, 2)}</pre>
          </Box>
        )}
        <Box sx={{ mt:2, display:'flex', gap:1, alignItems:'center', flexWrap:'wrap' }}>
          <FormControl size="small" sx={{ minWidth:100 }}>
            <InputLabel>FY</InputLabel>
            <Select value={filters.fy} label="FY" onChange={(e)=>setFilters(f=>({...f, fy: e.target.value}))}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="2025">2025</MenuItem>
              <MenuItem value="2026">2026</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth:100 }}>
            <InputLabel>QTR</InputLabel>
            <Select value={filters.qtr} label="QTR" onChange={(e)=>setFilters(f=>({...f, qtr: e.target.value}))}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="Q1">Q1</MenuItem>
              <MenuItem value="Q2">Q2</MenuItem>
              <MenuItem value="Q3">Q3</MenuItem>
              <MenuItem value="Q4">Q4</MenuItem>
            </Select>
          </FormControl>
          <TextField size="small" label="Echelon" value={filters.echelon_type} onChange={(e)=>setFilters(f=>({...f, echelon_type: e.target.value}))} />
          <TextField size="small" label="Unit" value={filters.unit_value} onChange={(e)=>setFilters(f=>({...f, unit_value: e.target.value}))} />
          <TextField size="small" label="Funding Line" value={filters.funding_line} onChange={(e)=>setFilters(f=>({...f, funding_line: e.target.value}))} />
          <Button variant="outlined" onClick={()=>{
            const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
            exportDashboard('events-roi','json', qs).then(d=>setEvents(d||[])).catch(()=>{})
            getMissionAssessment(qs).then(d=>setSummary(d)).catch(()=>{})
          }}>Apply filters</Button>
        </Box>
      </Box>
    </Box>
  )
}
