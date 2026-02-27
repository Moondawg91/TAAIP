import React, { useEffect, useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, Chip, List, ListItem, ListItemText } from '@mui/material'
import { useFilters } from '../../contexts/FilterContext'
import { getMissionFeasibilitySummary } from '../../api/client'

export default function MissionFeasibilityPage(){
  const { filters } = useFilters()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ load() }, [filters?.unit_rsid, filters?.fy])

  async function load(){
    setLoading(true)
    try{
      const params = { unit_rsid: filters?.unit_rsid, fy: filters?.fy }
      const resp = await getMissionFeasibilitySummary(params)
      setData(resp)
    }catch(e){
      console.error('feasibility load', e)
      setData(null)
    }finally{ setLoading(false) }
  }

  const statusColor = (s:any) => {
    if(!s) return 'default'
    if(s === 'GREEN') return 'success'
    if(s === 'AMBER') return 'warning'
    if(s === 'RED') return 'error'
    return 'default'
  }

  return (
    <Box sx={{ p:3, minHeight: '100vh' }}>
      

      <Box sx={{ mt:2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
                  <Typography variant="h6">Feasibility Summary</Typography>
                  {data && data.status && (
                    <Chip label={data.status.overall} color={statusColor(data.status.overall)} />
                  )}
                </Box>

                <Box sx={{ mt:2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={4}>
                      <Card variant="outlined"><CardContent>
                        <Typography variant="caption">Annual Mission</Typography>
                        <Typography variant="h6">{data?.inputs?.annual_mission_contracts ?? '—'}</Typography>
                      </CardContent></Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Card variant="outlined"><CardContent>
                        <Typography variant="caption">Recruiters Available (avg)</Typography>
                        <Typography variant="h6">{data?.inputs?.recruiters_available_avg ?? '—'}</Typography>
                      </CardContent></Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Card variant="outlined"><CardContent>
                        <Typography variant="caption">Required WR / Recruiter</Typography>
                        <Typography variant="h6">{data?.computed?.required_wr_per_recruiter ?? '—'}</Typography>
                      </CardContent></Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Card variant="outlined"><CardContent>
                        <Typography variant="caption">Market-adjusted Expected WR</Typography>
                        <Typography variant="h6">{data?.computed?.market_adjusted_expected_wr ?? '—'}</Typography>
                      </CardContent></Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Card variant="outlined"><CardContent>
                        <Typography variant="caption">Contract Gap</Typography>
                        <Typography variant="h6">{data?.computed?.contract_gap_vs_market ?? '—'}</Typography>
                      </CardContent></Card>
                    </Grid>
                  </Grid>
                </Box>

                <Box sx={{ mt:3 }}>
                  <Typography variant="subtitle1">Reasons</Typography>
                  {data?.status?.reasons && data.status.reasons.length ? (
                    <List>
                      {data.status.reasons.map((r:any, idx:number)=>(<ListItem key={idx}><ListItemText primary={r.code || r.detail} secondary={r.detail} /></ListItem>))}
                    </List>
                  ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No reasons provided.</Typography>}
                </Box>

                <Box sx={{ mt:3 }}>
                  <Typography variant="subtitle1">Recommendations</Typography>
                  {data?.recommendations && data.recommendations.length ? (
                    <List>
                      {data.recommendations.map((rec:any, idx:number)=>(<ListItem key={idx}><ListItemText primary={rec.text || rec} /></ListItem>))}
                    </List>
                  ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No recommendations.</Typography>}
                </Box>

              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6">Details</Typography>
                <Typography variant="body2">Unit: {data?.unit_display_name || data?.unit_rsid}</Typography>
                <Typography variant="body2">FY: {data?.fy}</Typography>

                <Box sx={{ mt:2 }}>
                  <Typography variant="subtitle2">Drivers</Typography>
                  {data?.drivers && data.drivers.length ? (
                    <List>
                      {data.drivers.map((d:any, i:number)=>(<ListItem key={i}><ListItemText primary={d.label || d.type} secondary={String(d.value)} /></ListItem>))}
                    </List>
                  ) : <Typography variant="body2" sx={{ color:'text.secondary' }}>No drivers detected.</Typography>}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}
