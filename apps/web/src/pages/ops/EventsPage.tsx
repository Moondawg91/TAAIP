import React, { useEffect, useState } from 'react'
import { Box, Typography, Chip, Button, Menu, MenuItem, TextField, FormControl, InputLabel, Select, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material'
import { getMissionAssessment, exportDashboard } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function OpsEventsPage(){
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [events, setEvents] = useState([])
  const [filters, setFilters] = useState({ fy:'', qtr:'', echelon_type:'', unit_value:'', funding_line:'' })

  useEffect(()=>{
    let mounted = true
    const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
    getMissionAssessment(qs).then(d=>{ if(mounted) setSummary(d) }).catch(()=>{})
    // load events list for drilldown
    exportDashboard('events-roi','json', qs).then(data=>{ if(mounted) setEvents(data || []) }).catch(()=>{})
    return ()=>{ mounted = false }
  },[filters])

  function handleExportClick(e){ setAnchorEl(e.currentTarget) }
  function handleExportClose(){ setAnchorEl(null) }

  async function doExport(type, format){
    handleExportClose()
    try{
      const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
      const text = await exportDashboard(type, format, qs)
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
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:2, flexWrap:'wrap' }}>
        <Typography variant="h4">Event Management</Typography>
        <Box sx={{ display:'flex', gap:1, alignItems:'center' }}>
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
          <Button variant="contained" color="primary" onClick={handleExportClick}>Export</Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleExportClose}>
            <MenuItem onClick={()=>doExport('events-roi','csv')}>Events ROI — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('events-roi','json')}>Events ROI — JSON</MenuItem>
          </Menu>
        </Box>
      </Box>

      <Box sx={{ mt:2 }}>
        {summary ? (
          <Box>
            <Typography variant="subtitle1">Tactical rollup (events)</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary.tactical_rollup?.events || {}, null, 2)}</pre>
          </Box>
        ) : (
          <Chip label="Loading rollup..." sx={{ mt:2 }} />
        )}

        <Box sx={{ mt:3 }}>
          <Typography variant="h6">Events (click name for ROI)</Typography>
          {events && events.length ? (
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Start</TableCell>
                    <TableCell align="right">Planned</TableCell>
                    <TableCell align="right">Actual</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {events.map(ev => (
                    <TableRow key={ev.event_id} hover>
                      <TableCell>{ev.event_id}</TableCell>
                      <TableCell>
                        <a href="#" onClick={(e)=>{ e.preventDefault(); navigate(`/ops/roi?event_id=${ev.event_id}`) }}>{ev.name}</a>
                      </TableCell>
                      <TableCell>{ev.start_date}</TableCell>
                      <TableCell align="right">{(ev.planned_cost ?? 0).toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:2})}</TableCell>
                      <TableCell align="right">{(ev.actual_cost ?? 0).toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:2})}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" sx={{ mt:1 }}>No events returned.</Typography>
          )}
        </Box>
      </Box>
    </Box>
  )
}
