import React, { useEffect, useState } from 'react'
import { Box, Typography, Chip, Button, Menu, MenuItem, TextField, FormControl, InputLabel, Select, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
// TopFilterBar rendered centrally by shell
import { useFilters } from '../../contexts/FilterContext'
import PageFrame from '../../components/layout/PageFrame'
import Panel from '../../components/layout/Panel'
import { getMissionAssessment, exportDashboard } from '../../api/client'
import { useLocation } from 'react-router-dom'
export default function OpsRoiPage(){
  const { filters } = useFilters()
  const [summary, setSummary] = useState(null)
  const [anchorEl, setAnchorEl] = useState(null)
  const [events, setEvents] = useState([])
  const location = useLocation()

  useEffect(()=>{
    let mounted = true
    const params = new URLSearchParams(location.search)
    const eventId = params.get('event_id')
    const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
    if (eventId) qs.event_id = eventId
    getMissionAssessment(qs).then(d=>{ if(mounted) setSummary(d) }).catch(()=>{})
    exportDashboard('events-roi','json', qs).then(data=>{ if(mounted) setEvents(data || []) }).catch(()=>{})
    return ()=>{ mounted = false }
  },[filters, location.search])

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
    <PageFrame>
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

      {/* TopFilterBar rendered by shell */}
      <Box sx={{ mt:2 }}>
        {summary ? (
          <Panel>
            <Typography variant="subtitle1">Tactical rollup</Typography>
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(summary.tactical_rollup || summary, null, 2)}</pre>
          </Panel>
        ) : (
          <Chip label="Loading rollup..." sx={{ mt:2 }} />
        )}

        {events && events.length > 0 && (
          <Box sx={{ mt:3 }}>
            <Panel title="Selected event">
              <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(events[0], null, 2)}</pre>
            </Panel>
          </Box>
        )}
        <Box sx={{ mt:2 }}>
          <Accordion disableGutters elevation={0} sx={{ bgcolor: 'transparent' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: 'text.secondary' }} />}>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>Advanced Filters</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* Funding controls moved to Budget pages only */}
            </AccordionDetails>
          </Accordion>
          <Button variant="outlined" onClick={()=>{
            const qs = Object.fromEntries(Object.entries(filters).filter(([,v])=>v))
            exportDashboard('events-roi','json', qs).then(d=>setEvents(d||[])).catch(()=>{})
            getMissionAssessment(qs).then(d=>setSummary(d)).catch(()=>{})
          }}>Refresh</Button>
        </Box>
      </Box>
    </Box>
    </PageFrame>
  )
}
