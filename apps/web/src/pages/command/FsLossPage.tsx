import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Grid, List, ListItem, ListItemText, Button } from '@mui/material'
import { useFilters } from '../../contexts/FilterContext'
import { getFsLossSummary, getFsLossCodes } from '../../api/client'

export default function FsLossPage(){
  const { filters } = useFilters()
  const [summary, setSummary] = useState<any[]>([])
  const [codes, setCodes] = useState<any[]>([])

  useEffect(()=>{ load() }, [filters?.unit_rsid, filters?.fy])

  async function load(){
    try{
      const params = { unit_rsid: filters?.unit_rsid, fy: filters?.fy }
      const s = await getFsLossSummary(params)
      setSummary((s && s.summary) || [])
    }catch(e){ setSummary([]) }
    try{ const c = await getFsLossCodes(); setCodes((c && c.codes) || []) }catch(e){ setCodes([]) }
  }

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h5">Future Soldier (FS) Loss</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>Upload FS Loss events in Data Hub to populate this dashboard.</Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Loss Codes</Typography>
            <List>
              {codes.map(c=> <ListItem key={c.code}><ListItemText primary={c.code} secondary={c.label} /></ListItem>)}
              {codes.length===0 && <ListItem><ListItemText primary="No codes available" /></ListItem>}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p:2 }}>
            <Typography variant="h6">Summary</Typography>
            <List>
              {summary.map(s=> <ListItem key={s.loss_code}><ListItemText primary={s.loss_code} secondary={`Count: ${s.count}`} /></ListItem>)}
              {summary.length===0 && <ListItem><ListItemText primary="No FS Loss records found" /></ListItem>}
            </List>
            <Box sx={{ mt:2 }}>
              <Button variant="outlined" href="/data-hub">Go to Data Hub</Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
