import React, { useEffect, useState } from 'react'
import { Box, Typography, Chip, Button, Menu, MenuItem, TextField, FormControl, InputLabel, Select, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
// Filters rendered centrally by the shell
import { useFilters } from '../../contexts/FilterContext'
import PageFrame from '../../components/layout/PageFrame'
import Panel from '../../components/layout/Panel'
import { getMissionAssessment, exportDashboard } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export default function OpsEventsPage(){
  const navigate = useNavigate()
  const { filters } = useFilters()
  const [summary, setSummary] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [events, setEvents] = useState([])

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
    <PageFrame>
    <Box>
      <Box sx={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:2, flexWrap:'wrap' }}>
        <Typography variant="h4">Event Management</Typography>
        <Box sx={{ mt:2, display:'flex', gap:1, alignItems:'center' }}>
          <Accordion disableGutters elevation={0} sx={{ bgcolor: 'transparent' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: 'text.secondary' }} />}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>Advanced Filters</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* Funding controls moved to Budget pages only */}
            </AccordionDetails>
          </Accordion>
          <Button variant="contained" color="primary" onClick={handleExportClick}>Export</Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleExportClose}>
            <MenuItem onClick={()=>doExport('events-roi','csv')}>Events ROI — CSV</MenuItem>
            <MenuItem onClick={()=>doExport('events-roi','json')}>Events ROI — JSON</MenuItem>
          </Menu>
        </Box>
      </Box>

      <Box sx={{ mt:2 }}>
        {summary ? (
          <Panel>
            <Typography variant="subtitle1">Tactical rollup (events)</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary.tactical_rollup?.events || {}, null, 2)}</pre>
          </Panel>
        ) : (
          <Chip label="Loading rollup..." sx={{ mt:2 }} />
        )}

        <Box sx={{ mt:3 }}>
          <Typography variant="h6">Events (click name for ROI)</Typography>
          {events && events.length ? (
            <Panel sx={{ mt:1 }}>
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
              </Panel>
          ) : (
            <Typography variant="body2" sx={{ mt:1 }}>No events returned.</Typography>
          )}
        </Box>
      </Box>
    </Box>
    </PageFrame>
  )
}
