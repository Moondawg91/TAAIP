import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, Button, TextField } from '@mui/material'
import { useOrgUnitStore } from '../../state/orgUnitStore'

export default function RoiFunnelPanel({ dateRange, onDateRangeChange, unitSelection, kpis, funnel, breakdowns, onHoverKpi, onClickKpi, openDetail }: any){
  const [range, setRange] = useState(dateRange || { from: '', to: '' })
  return (
    <Box sx={{ display:'flex', flexDirection:'column', gap:2 }}>
      <Box sx={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <Box sx={{ display:'flex', gap:1, alignItems:'center' }}>
          <TextField size="small" label="From" value={range.from} onChange={(e)=> setRange(r=> ({...r, from: e.target.value}))} />
          <TextField size="small" label="To" value={range.to} onChange={(e)=> setRange(r=> ({...r, to: e.target.value}))} />
          <Button onClick={()=> onDateRangeChange(range)}>Apply</Button>
        </Box>
        <Box>
          <div style={{ fontWeight:600 }}>Active unit: {useOrgUnitStore().pathLabel}</div>
        </Box>
      </Box>

      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">KPIs</Typography>
              <Typography variant="body2">Leads: {kpis?.leads || 0}</Typography>
              <Typography variant="body2">Appointments: {kpis?.appts || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={8}>
          <Card>
            <CardContent>
              <Typography variant="h6">Funnel</Typography>
              {funnel && funnel.length>0 ? funnel.map((f:any)=> (
                <Box key={f.key} sx={{ display:'flex', justifyContent:'space-between' }} onClick={()=> openDetail({ title: f.label, type: 'kpi', payload: f })}>
                  <Typography>{f.label}</Typography>
                  <Typography>{f.value}</Typography>
                </Box>
              )) : <Typography>No funnel data</Typography>}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box>
        <Typography variant="subtitle2">Breakdowns</Typography>
        {breakdowns && breakdowns.length>0 ? breakdowns.map((b:any)=> (
          <Card key={b.rsid} sx={{ my:1 }}>
            <CardContent>
              <Typography variant="body2">{b.display_name} — Leads: {b.leads || 0}</Typography>
            </CardContent>
          </Card>
        )) : <Typography variant="body2">No breakdowns</Typography>}
      </Box>
    </Box>
  )
}
