import React, { useEffect, useState } from 'react'
import { Box, Typography, Grid, Card, CardContent, CircularProgress, Table, TableBody, TableRow, TableCell } from '@mui/material'
import { useFilters } from '../../contexts/FilterContext'
import { apiFetch } from '../../api/client'

export default function MissionFeasibilityPage(){
  const { filters } = useFilters()
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState(null)
  const [scenarios, setScenarios] = useState(null)

  async function load(){
    setLoading(true)
    try{
      const qs = new URLSearchParams()
      if(filters?.unit_rsid) qs.set('unit_rsid', filters.unit_rsid)
      if(filters?.fy) qs.set('fy', filters.fy)
      // include quarter numeric and rsm_month when available
      try{
        if(filters?.qtr){ const qn = Number(String(filters.qtr).replace(/^Q/,'')); if(!isNaN(qn)) qs.set('qtr_num', qn) }
      }catch(e){}
      if(filters?.rsm_month) qs.set('rsm_month', filters.rsm_month)
      const s = await apiFetch(`/api/v2/mission-feasibility/summary?${qs.toString()}`)
      setSummary(s)
      const sc = await apiFetch(`/api/v2/mission-feasibility/scenarios?${qs.toString()}`)
      setScenarios(sc)
    }catch(e){
      console.error(e)
    }finally{ setLoading(false) }
  }

  useEffect(()=>{ load() }, [filters?.unit_rsid, filters?.fy])

  return (
    <Box sx={{p:3}}>
      <Typography variant="h5" sx={{mb:2}}>Mission Feasibility</Typography>
      <Typography variant="caption" color="text.secondary" sx={{display:'block',mb:1}}>
        Applied Scope: {filters?.unit_rsid || 'USAREC'} | {filters?.fy ? `FY${String(filters.fy).slice(-2)}` : 'FY—'} | {filters?.qtr || 'Q—'} | {filters?.rsm_month ? `RSM ${filters.rsm_month}` : 'RSM —'}
      </Typography>

      {loading ? <Box sx={{mt:4,display:'flex',justifyContent:'center'}}><CircularProgress/></Box> : (
        <Grid container spacing={2} sx={{mt:2}}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2">Status</Typography>
                <Typography variant="h6">{(summary && summary.overall_status) || 'UNKNOWN'}</Typography>
                <Typography variant="caption" color="text.secondary">Data completeness and feasibility</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2">Key Metrics</Typography>
                {summary ? (
                  <Table>
                    <TableBody>
                      <TableRow><TableCell>WR Required</TableCell><TableCell>{summary.computed?.wr_required ?? '—'}</TableCell></TableRow>
                      <TableRow><TableCell>WR Actual</TableCell><TableCell>{summary.computed?.wr_actual ?? '—'}</TableCell></TableRow>
                      <TableRow><TableCell>Recruiters Required</TableCell><TableCell>{summary.computed?.recruiters_required ?? '—'}</TableCell></TableRow>
                      <TableRow><TableCell>MSI</TableCell><TableCell>{summary.computed?.msi ?? '—'}</TableCell></TableRow>
                    </TableBody>
                  </Table>
                ) : <Typography variant="body2" color="text.secondary">No summary available.</Typography>}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2">Scenarios</Typography>
                {scenarios ? (
                  <Table>
                    <TableBody>
                      <TableRow><TableCell>Scenario A (WR=1.0)</TableCell><TableCell>{scenarios.scenario_A?.feasibility_score ?? '—'}</TableCell></TableRow>
                      <TableRow><TableCell>Scenario B (WR=0.7)</TableCell><TableCell>{scenarios.scenario_B?.feasibility_score ?? '—'}</TableCell></TableRow>
                    </TableBody>
                  </Table>
                ) : <Typography variant="body2" color="text.secondary">No scenario data.</Typography>}
              </CardContent>
            </Card>
          </Grid>

        </Grid>
      )}
    </Box>
  )
}
