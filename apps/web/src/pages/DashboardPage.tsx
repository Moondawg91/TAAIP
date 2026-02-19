import React, {useEffect, useState} from 'react'
import { Box, Typography, Grid, Paper, Button, Select, MenuItem, FormControl, InputLabel } from '@mui/material'
import { getAnalyticsSummary, getAnalyticsFunnel } from '../api/client'
import DashboardFilterBar from '../components/DashboardFilterBar'
import ExportMenu from '../components/ExportMenu'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage(){
  const [summary, setSummary] = useState(null)
  const [funnel, setFunnel] = useState([])
  const [dateRange, setDateRange] = useState('30d')
  const navigate = useNavigate()

  useEffect(()=>{ fetchSummary() }, [])

  async function fetchSummary(){
    const s = await getAnalyticsSummary({})
    setSummary(s)
    const f = await getAnalyticsFunnel({})
    setFunnel(f || [])
  }

  function handleDrill(stage){
    navigate(`/dashboard/detail?stage=${encodeURIComponent(stage)}`)
  }

  return (
    <Box sx={{p:3}}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <Typography variant="h4">Dashboard</Typography>
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={funnel} filename="dashboard_export" />
        </Box>
      </Box>
      <DashboardFilterBar />
      <Grid container spacing={2} sx={{mt:2}}>
        <Grid item xs={3}>
          <Paper sx={{p:2}}>
            <Typography variant="subtitle1">Slicers</Typography>
            <FormControl fullWidth sx={{mt:1}}>
              <InputLabel>Range</InputLabel>
              <Select value={dateRange} label="Range" onChange={(e)=>setDateRange(e.target.value)}>
                <MenuItem value={'7d'}>Last 7 days</MenuItem>
                <MenuItem value={'30d'}>Last 30 days</MenuItem>
                <MenuItem value={'90d'}>Last 90 days</MenuItem>
              </Select>
            </FormControl>
          </Paper>
        </Grid>
        <Grid item xs={9}>
          <Paper sx={{p:2}}>
            <Typography variant="subtitle1">KPIs</Typography>
            {summary ? (
              <Grid container spacing={1} sx={{mt:1}}>
                {['spend','impressions','engagements','leads','appts','contracts','accessions','CPM','CPE','CPL'].map(k=> (
                  <Grid item xs={3} key={k}><Box sx={{p:1}}><strong>{k}</strong><div>{String(summary[k] ?? '')}</div></Box></Grid>
                ))}
              </Grid>
            ) : <div>No data imported</div>}
          </Paper>

          <Paper sx={{p:2, mt:2}}>
            <Typography variant="subtitle1">Trend</Typography>
            <div style={{height:220}}>
              <ResponsiveContainer>
                <LineChart data={[]}> <XAxis dataKey="date"/> <YAxis/> <Tooltip/> <Line type="monotone" dataKey="value" stroke="#8884d8"/> </LineChart>
              </ResponsiveContainer>
            </div>
          </Paper>

          <Paper sx={{p:2, mt:2}}>
            <Typography variant="subtitle1">Funnel Stages</Typography>
            <BarChart width={800} height={200} data={funnel}>
              <XAxis dataKey="stage_key" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total_count">
                {funnel.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="#8884d8" />
                ))}
              </Bar>
            </BarChart>
            <div>
              {funnel.map((s)=> (
                <Button key={s.stage_key} onClick={()=>handleDrill(s.stage_key)}>{s.stage_key} — {s.total_count}</Button>
              ))}
            </div>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
