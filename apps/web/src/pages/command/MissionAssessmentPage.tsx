import React, { useState, useEffect } from 'react'
import { Box, Typography, Tabs, Tab, Card, CardContent, Grid, Chip, List, ListItem, ListItemText, TextField, Button } from '@mui/material'
import EmptyState from '../../components/common/EmptyState'
import { getAnalyticsSummary, getLatestMissionAssessment, saveMissionAssessment } from '../../api/client'
import DashboardToolbar from '../../components/dashboard/DashboardToolbar'
import DualModeTabs from '../../components/DualModeTabs'
import DashboardFilterBar from '../../components/DashboardFilterBar'
import ExportMenu from '../../components/ExportMenu'

function TabPanel({ children, value, index }: any){
  return value === index ? <Box sx={{ mt:2 }}>{children}</Box> : null
}

export default function MissionAssessmentPage(){
  const [tab, setTab] = useState(0)
  const [summary, setSummary] = useState([])
  const [assessment, setAssessment] = useState<any>(null)
  const [editing, setEditing] = useState(false)
  const [narrative, setNarrative] = useState('')
  const [periodType, setPeriodType] = useState('FY')
  const [periodValue, setPeriodValue] = useState('2026')
  const [scopeVal, setScopeVal] = useState('')

  useEffect(()=>{ load() }, [])
  async function load(){
    try{
      const s = await getAnalyticsSummary({})
      setSummary(s || [])
      const a = await getLatestMissionAssessment('FY', '')
      setAssessment(a || null)
      if(a){
        setNarrative(a.narrative || '')
        setPeriodType(a.period_type || 'FY')
        setPeriodValue(a.period_value || String(new Date().getFullYear()))
        setScopeVal(a.scope || '')
      }
    }catch(e){ console.error('load analytics summary', e) }
  }

  return (
    <Box sx={{ p:3, minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <Box sx={{display:'flex', alignItems:'center', gap:2}}>
        <DashboardToolbar title="Mission Assessment" subtitle="FY / QTR / Month assessment for recruiting missions." filters={{}} onFiltersChange={()=>{}} onExport={(t)=>{ alert(`Export ${t} coming soon`) }} />
        <Box sx={{ml:'auto'}}>
          <ExportMenu data={[] } filename="mission_assessment" />
        </Box>
      </Box>
      <DualModeTabs />
      <DashboardFilterBar />

      <Tabs value={tab} onChange={(_,v)=>setTab(v)} aria-label="assessment-tabs">
        <Tab label="FY" />
        <Tab label="Quarter" />
        <Tab label="Month" />
      </Tabs>

      <TabPanel value={tab} index={0}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor:'background.paper' }}>
              <CardContent>
                <Typography variant="h6">FY Summary</Typography>
                {summary && summary.length ? (
                  <List>
                    {(summary || []).map((r:any)=> <ListItem key={r.id || JSON.stringify(r)}><ListItemText primary={r.title || r.metric_key || JSON.stringify(r)} secondary={r.metric_value || ''} /></ListItem>)}
                  </List>
                ) : <EmptyState title="No mission data" subtitle="No analytics available for this period." actionLabel="Go to Import Center" onAction={()=>{ window.location.href='/import-center' }} />}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ bgcolor:'background.paper' }}>
              <CardContent>
                <Typography variant="h6">Standards Baseline</Typography>
                <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Baseline metrics will appear here.</Typography>
                <Box sx={{ mt:2 }}>
                  <TextField label="Period Type" size="small" value={periodType} onChange={(e)=>setPeriodType(e.target.value)} sx={{ mr:1 }} />
                  <TextField label="Period Value" size="small" value={periodValue} onChange={(e)=>setPeriodValue(e.target.value)} sx={{ mr:1 }} />
                  <TextField label="Echelon / Unit" size="small" value={scopeVal} onChange={(e)=>setScopeVal(e.target.value)} />
                </Box>
                <Box sx={{ mt:2 }}>
                  <TextField label="Narrative" multiline fullWidth minRows={4} value={narrative} onChange={(e)=>setNarrative(e.target.value)} />
                </Box>
                <Box sx={{ display:'flex', gap:1, mt:2 }}>
                  <Button variant="contained" onClick={async ()=>{
                    try{
                      const payload = { id: assessment && assessment.id, period_type: periodType, period_value: periodValue, scope: scopeVal, narrative, metrics: assessment && assessment.metrics_json };
                      const saved = await saveMissionAssessment(payload)
                      setAssessment(saved)
                      setEditing(false)
                      alert('Saved')
                    }catch(e){ console.error('save', e); alert('Save failed') }
                  }}>Save Assessment</Button>
                  <Button variant="text" onClick={()=>{ setEditing(!editing); setNarrative(assessment?.narrative || '') }}>{editing ? 'Cancel' : 'Edit'}</Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={1}>
        <Card sx={{ bgcolor:'background.paper' }}>
          <CardContent>
            <Typography variant="h6">Quarter Assessment</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Quarterly analysis.</Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tab} index={2}>
        <Card sx={{ bgcolor:'background.paper' }}>
          <CardContent>
            <Typography variant="h6">Monthly Assessment</Typography>
            <Typography variant="body2" sx={{ color:'text.secondary', mt:1 }}>Monthly performance and trends.</Typography>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  )
}
