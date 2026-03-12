import React, { useEffect, useState } from 'react'
import { Box, Button, Paper, Typography, Grid, TextField, Table, TableBody, TableCell, TableHead, TableRow, TableContainer, Divider } from '@mui/material'
import { apiFetch } from '../../api/client'
import { loadOrgSelection } from '../../store/orgSelection'

export default function MissionAllocationPage(){
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [results, setResults] = useState(null)
  const [supportDetails, setSupportDetails] = useState(null)
  const [missionTotal, setMissionTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  function getDefaultUnit(){
    try{
      const sel = loadOrgSelection()
      const active = (sel && sel.active) ? sel.active : (sel && sel.effective_rsid ? { rsid: sel.effective_rsid } : null)
      return active && active.rsid ? active.rsid : '6L'
    }catch(e){ return '6L' }
  }

  async function fetchRuns(){
    try{
      const resp = await apiFetch('/api/v2/mission-allocation/runs', { includeUnit: true })
      setRuns((resp && resp.rows) ? resp.rows : [])
    }catch(e){ setRuns([]) }
  }

  async function fetchResults(runId){
    if(!runId) return setResults(null)
    try{
      const resp = await apiFetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(runId)}/results`, { includeUnit: true })
      setResults(resp)
    }catch(e){ setResults(null) }
  }

  async function fetchSupportDetails(runId){
    if(!runId) return setSupportDetails(null)
    try{
      const resp = await apiFetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(runId)}/details`, { includeUnit: true })
      setSupportDetails(resp)
    }catch(e){ setSupportDetails(null) }
  }

  async function handleCreateRun(){
    const unit = getDefaultUnit()
    if(!missionTotal || Number(missionTotal) <= 0){ alert('Enter a positive mission total'); return }
    setLoading(true)
    try{
      // Starter inputs: lightweight demo defaults so compute has something to work with.
      // These are UI-only convenience values and should be replaced with real inputs.
      const starterInputs = [
        { company_id: 'A', recruiter_capacity: 2, historical_production: 3, funnel_health: 0.7, dep_loss: 0, school_access: 0.5, school_population: 120 },
        { company_id: 'B', recruiter_capacity: 1, historical_production: 1, funnel_health: 0.6, dep_loss: 0, school_access: 0.3, school_population: 80 }
      ]
      const body = { unit_rsid: unit, mission_total: Number(missionTotal), notes: 'Created from UI', inputs: starterInputs }
      const resp = await apiFetch('/api/v2/mission-allocation/runs', { method: 'POST', body: JSON.stringify(body), headers: {'Content-Type':'application/json'}, includeUnit: false })
      await fetchRuns()
      if (resp && resp.run_id) {
        setSelectedRun(resp.run_id)
        setTimeout(()=> fetchResults(resp.run_id), 400)
      }
    }catch(e){ console.error(e); alert('Create run failed') }
    setLoading(false)
  }

  async function handleCompute(){
    if(!selectedRun){ alert('Select a run first'); return }
    setLoading(true)
    try{
      await apiFetch(`/api/v2/mission-allocation/runs/${encodeURIComponent(selectedRun)}/compute`, { method: 'POST', includeUnit: true })
      setTimeout(()=> fetchResults(selectedRun), 800)
    }catch(e){ console.error(e); alert('Compute failed') }
    setLoading(false)
  }

  useEffect(()=>{ fetchRuns() }, [])
  useEffect(()=>{ if(selectedRun) fetchResults(selectedRun) }, [selectedRun])
  useEffect(()=>{ if(selectedRun) fetchSupportDetails(selectedRun) }, [selectedRun])

  return (
    <Box sx={{ p:3 }}>
      <Typography variant="h4" sx={{ mb:1 }}>Mission Allocation</Typography>
      <Typography variant="body2" sx={{ color:'text.secondary', mb:2 }}>BN mission input and company-level decision table.</Typography>

      <Grid container spacing={2} sx={{ mb:2 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Unit</Typography>
            <Typography variant="h6">{getDefaultUnit()}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Mission Total</Typography>
            <TextField fullWidth type="number" value={missionTotal} onChange={e=>setMissionTotal(e.target.value)} size="small" />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2, display:'flex', gap:1, alignItems:'center', justifyContent:'flex-end' }}>
            <Button variant="contained" onClick={handleCreateRun} disabled={loading}>Create Run</Button>
            <Button variant="outlined" onClick={handleCompute} disabled={loading || !selectedRun}>Compute</Button>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Runs</Typography>
            <Box sx={{ mt:1 }}>
              {runs.length === 0 ? <Typography variant="caption" color="text.secondary">No runs yet</Typography> : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Run ID</TableCell>
                        <TableCell>Unit</TableCell>
                        <TableCell>Mission Total</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Created</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {runs.map(r => (
                        <TableRow key={r.run_id} hover selected={r.run_id === selectedRun} onClick={()=> setSelectedRun(r.run_id)} style={{ cursor: 'pointer' }}>
                          <TableCell>{r.run_id}</TableCell>
                          <TableCell>{r.unit_rsid}</TableCell>
                          <TableCell>{r.mission_total}</TableCell>
                          <TableCell>{r.status}</TableCell>
                          <TableCell>{r.created_at}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Selected Run</Typography>
            <Typography variant="body2">{selectedRun || '—'}</Typography>
            <Box sx={{ mt:1 }}>
              <Button size="small" onClick={()=> { setSelectedRun(null); setResults(null) }}>Clear</Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Company Decision Table</Typography>
            <Divider sx={{ my:1 }} />
            {(!results || !results.recommendations) ? (
              <Typography variant="caption" color="text.secondary">No results to display</Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Company</TableCell>
                      <TableCell>Recommended</TableCell>
                      <TableCell>Supportability</TableCell>
                      <TableCell>Risk</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Rationale</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {results.recommendations.map(rec => (
                      <TableRow key={rec.company}>
                        <TableCell>{rec.company}</TableCell>
                        <TableCell>{rec.recommended_allocation}</TableCell>
                        <TableCell>{rec.supportability_score}</TableCell>
                        <TableCell>{rec.risk_score}</TableCell>
                        <TableCell>{rec.confidence_score}</TableCell>
                        <TableCell style={{ maxWidth: 360, whiteSpace: 'pre-wrap' }}>{rec.rationale}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p:2 }}>
            <Typography variant="subtitle2">Supporting Details</Typography>
            <Typography variant="body2" color="text.secondary">Top drivers, limiting factors, evidence refs, and assumptions.</Typography>
            <Divider sx={{ my:1 }} />
            {supportDetails ? (
              <Box>
                <Typography variant="subtitle2">Top Drivers</Typography>
                {supportDetails.drivers && supportDetails.drivers.length>0 ? (
                  <ul>{supportDetails.drivers.map((d,i)=>(<li key={i}>{d}</li>))}</ul>
                ) : <Typography variant="caption" color="text.secondary">No drivers yet</Typography>}

                <Typography variant="subtitle2" sx={{ mt:1 }}>Limiting Factors</Typography>
                {supportDetails.limiting_factors && supportDetails.limiting_factors.length>0 ? (
                  <ul>{supportDetails.limiting_factors.map((d,i)=>(<li key={i}>{d}</li>))}</ul>
                ) : <Typography variant="caption" color="text.secondary">No limiting factors yet</Typography>}

                <Typography variant="subtitle2" sx={{ mt:1 }}>Assumptions</Typography>
                {supportDetails.assumptions && supportDetails.assumptions.length>0 ? (
                  <ul>{supportDetails.assumptions.map((a,i)=>(<li key={i}>{a}</li>))}</ul>
                ) : <Typography variant="caption" color="text.secondary">No assumptions yet</Typography>}

                <Typography variant="subtitle2" sx={{ mt:1 }}>Evidence</Typography>
                {supportDetails.evidence && supportDetails.evidence.length>0 ? (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Company</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>URI</TableCell>
                        <TableCell>Description</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {supportDetails.evidence.map(ev => (
                        <TableRow key={ev.id}>
                          <TableCell>{ev.company_id || '—'}</TableCell>
                          <TableCell>{ev.evidence_type}</TableCell>
                          <TableCell>{ev.evidence_uri}</TableCell>
                          <TableCell>{ev.description}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : <Typography variant="caption" color="text.secondary">No evidence yet</Typography>}
              </Box>
            ) : (
              <Typography variant="caption" color="text.secondary">No supporting details available</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
