import React, {useEffect, useState} from 'react'
import { Box, Container, Paper, Typography, TextField, Select, MenuItem, List, ListItem, ListItemText, Collapse, IconButton } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { getTraceabilityLinks, getModuleRegistry, getRegulatoryReferencesApi } from '../../api/client'

export default function TraceabilityMatrixPage(){
  const [moduleKey, setModuleKey] = useState('')
  const [refCode, setRefCode] = useState('')
  const [metricKey, setMetricKey] = useState('')
  const [links, setLinks] = useState([])
  const [modules, setModules] = useState([])
  const [refs, setRefs] = useState([])
  const [openIds, setOpenIds] = useState({})

  async function load(){
    try{ const m = await getModuleRegistry(); setModules(m.modules || []) }catch(e){ setModules([]) }
    try{ const r = await getRegulatoryReferencesApi({}); setRefs(r.references || []) }catch(e){ setRefs([]) }
    try{
      const qs = {}
      if(moduleKey) qs.module_key = moduleKey
      if(refCode) qs.reference_code = refCode
      if(metricKey) qs.metric_key = metricKey
      const res = await getTraceabilityLinks(qs)
      setLinks(res.links || [])
    }catch(e){ setLinks([]) }
  }

  useEffect(()=>{ load() }, [])

  return (
    <Container maxWidth="lg" sx={{py:2}}>
      <Typography variant="h5" sx={{mb:2}}>Traceability Matrix</Typography>

      <Paper sx={{p:1, mb:2, display:'flex', gap:1, alignItems:'center', bgcolor:'transparent', borderRadius:'4px'}}>
        <Select value={moduleKey} size="small" onChange={e=>setModuleKey(e.target.value)} sx={{minWidth:220}}>
          <MenuItem value="">All Modules</MenuItem>
          {modules.map(m=> <MenuItem key={m.module_key} value={m.module_key}>{m.display_name}</MenuItem>)}
        </Select>
        <Select value={refCode} size="small" onChange={e=>setRefCode(e.target.value)} sx={{minWidth:220}}>
          <MenuItem value="">All References</MenuItem>
          {refs.map(r=> <MenuItem key={r.code} value={r.code}>{r.code} - {r.title}</MenuItem>)}
        </Select>
        <TextField size="small" placeholder="Metric key" value={metricKey} onChange={e=>setMetricKey(e.target.value)} sx={{minWidth:180}} />
        <Box sx={{ml:'auto'}}>
          <IconButton onClick={load} sx={{borderRadius:'4px'}}>
            <Typography variant="button">Refresh</Typography>
          </IconButton>
        </Box>
      </Paper>

      <Paper sx={{p:1, bgcolor:'transparent', borderRadius:'4px'}}>
        {links.length===0 ? (
          <Box sx={{p:2}}>
            <Typography variant="body2" sx={{color:'text.secondary'}}>No traceability links found.</Typography>
          </Box>
        ) : (
          <List>
            {links.map(l=> (
              <Box key={l.id} sx={{borderBottom:'1px solid rgba(255,255,255,0.04)', py:1}}>
                <ListItem disableGutters secondaryAction={
                  <IconButton edge="end" onClick={()=> setOpenIds(s=>({...s, [l.id]: !s[l.id]}))} sx={{color:'text.secondary'}}>
                    <ExpandMoreIcon />
                  </IconButton>
                }>
                  <ListItemText primary={`${l.module_key} — ${l.metric_key || ''}`} secondary={`${l.reference?.code || ''} ${l.tor_enclosure ? ' • ' + l.tor_enclosure : ''}`} />
                </ListItem>
                <Collapse in={!!openIds[l.id]} timeout="auto" unmountOnExit>
                  <Box sx={{p:1}}>
                    <Typography variant="body2" sx={{color:'text.secondary'}}>Decision: {l.decision_supported}</Typography>
                    <Typography variant="body2" sx={{color:'text.secondary'}}>Notes: {l.notes}</Typography>
                    <Typography variant="caption" sx={{display:'block', mt:1, color:'text.secondary'}}>Route: {l.page_route}</Typography>
                  </Box>
                </Collapse>
              </Box>
            ))}
          </List>
        )}
      </Paper>
    </Container>
  )
}
